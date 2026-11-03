"""Input integrity helpers; no instruction checker or scoring policy lives here."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_baseline():
    """Read the immutable archived oracle, never the current experiment output."""
    baseline = read_json(ROOT / "baseline.json")
    cases = [row["case"] for row in baseline["cases"]]
    ids = [case["case_id"] for case in cases]
    if len(ids) != 86 or len(set(ids)) != 86:
        raise ValueError("Incomplete archived baseline")
    digest = baseline_cases_hash(baseline)
    for side in ["original", "ko"]:
        if baseline["environments"][side]["cases_sha256"] != digest:
            raise ValueError("Baseline cases do not match their stored oracle hash")
        if [row[side]["case_id"] for row in baseline["cases"]] != ids:
            raise ValueError("Baseline result order does not match case order")
    return baseline


def baseline_cases_hash(baseline):
    cases = [row["case"] for row in baseline["cases"]]
    return sha((json.dumps(cases, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def baseline_cases():
    return [row["case"] for row in read_baseline()["cases"]]


def baseline_run(side):
    baseline = read_baseline()
    return {"environment": baseline["environments"][side],
            "results": [row[side] for row in baseline["cases"]]}


def object_hash(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def instruction_index(ids, iid, index=None):
    """Legacy unique IDs may omit index; repeated IDs must specify it."""
    if index is None:
        matches = [i for i, value in enumerate(ids) if value == iid]
        if len(matches) != 1:
            raise ValueError(f"Explicit instruction_index required for {iid}: {matches}")
        return matches[0]
    if type(index) is not int or not 0 <= index < len(ids) or ids[index] != iid:
        raise ValueError(f"instruction_index/ID mismatch: {index}, {iid}, {ids}")
    return index


def registry_names(path):
    """Read the pinned registry AST without importing optional dependencies."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass

    def resolve(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return constants[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return resolve(node.left) + resolve(node.right)
        raise ValueError(f"Unsupported registry expression: {ast.dump(node)}")

    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "INSTRUCTION_DICT" for t in node.targets):
            return {resolve(k): v.attr for k, v in zip(node.value.keys, node.value.values)}
    raise ValueError("INSTRUCTION_DICT not found")


def partition(iid, kwargs):
    if iid in {"keywords:frequency", "length_constraints:number_sentences", "length_constraints:number_words"}:
        return "relation=" + kwargs["relation"]
    if iid == "detectable_content:postscript":
        return "postscript_marker=" + kwargs["postscript_marker"]
    return "default"


def ko_input(case):
    return {
        "key": case["key"], "prompt": case["ko_prompt"],
        "instruction_id_list": case["ko_instruction_id_list"],
        "kwargs": case.get("ko_eval_all_kwargs", case["ko_all_kwargs"]),
    }


def input_hashes(case):
    inp = ko_input(case)
    response = case["test_response_ko"]
    return {
        "input_sha256": object_hash(inp),
        "source_row_sha256": object_hash({**inp, "kwargs": case["ko_all_kwargs"]}),
        "response_sha256": sha(response.encode("utf-8")),
        "cache_key": object_hash({"input": inp, "response": response, "source_revisions": case["source_revisions"]}),
    }


def validate_case(case, require_expected=True):
    ids, kwargs = case["ko_instruction_id_list"], case["ko_all_kwargs"]
    if not isinstance(case["case_id"], str) or not case["case_id"]:
        raise ValueError("case_id must be a nonempty string")
    if len(ids) != len(kwargs) or not ids:
        raise ValueError(f"Invalid instruction/kwargs lengths: {case['case_id']}")
    index = instruction_index(ids, case["instruction_id"], case["instruction_index"])
    if case["ko_kwargs"] != kwargs[index]:
        raise ValueError(f"Target kwargs mismatch: {case['case_id']}")
    effective = case.get("ko_eval_all_kwargs", kwargs)
    if len(effective) != len(ids):
        raise ValueError("Effective kwargs length mismatch")
    seen = set()
    for target in case["targets"]:
        i = instruction_index(ids, target["instruction_id"], target["instruction_index"])
        if i in seen:
            raise ValueError("Duplicate target instruction_index")
        seen.add(i)
        if case["scope"] == "dataset" and target["input_partition"] != partition(ids[i], effective[i]):
            raise ValueError("Input partition/kwargs mismatch")
    if not seen or case["comparison_input"] != "identical_ko":
        raise ValueError("Missing targets or identical-Ko input contract")
    if case["hashes"] != input_hashes(case):
        raise ValueError(f"Input/response hash mismatch: {case['case_id']}")
    if require_expected:
        expected = case["expected_ko"]
        for kind in ["strict", "loose"]:
            flags = expected["full"][kind]
            if len(flags) != len(ids) or any(type(v) is not bool for v in flags):
                raise ValueError("Expected flags must be ordered Boolean lists")
            if expected["prompt"][kind] != all(flags):
                raise ValueError("Expected prompt AND mismatch")


def validate_cases(cases, require_expected=True):
    ids = [c["case_id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case_id; results would overwrite each other")
    for case in cases:
        validate_case(case, require_expected)


def verify_sources(source_root):
    source_root = Path(source_root).resolve()
    provenance = read_json(ROOT / "provenance.json")
    verified = {}
    for side, entry in provenance.items():
        for name, info in entry["files"].items():
            path = source_root / info["local_path"]
            if not path.is_file() or sha(path.read_bytes()) != info["sha256"]:
                raise ValueError(f"Pinned source hash mismatch: {side}/{name}")
            verified[side + "/" + name] = info["sha256"]
    return provenance, verified


def validate_source_row(case, by_key):
    if case["key"] is not None:
        row = by_key[case["key"]]
        if any(case["ko_" + field] != row[source_field] for field, source_field in
               [("prompt", "prompt"), ("instruction_id_list", "instruction_id_list"), ("all_kwargs", "kwargs")]):
            raise ValueError(f"Ko source row changed: {case['case_id']}")
    if case["scope"] == "dataset" and "ko_eval_all_kwargs" in case:
        raise ValueError("Dataset case must not override kwargs")
    if case["scope"] == "controlled_override":
        expected = copy.deepcopy(case["ko_all_kwargs"])
        patch = case.get("runtime_override", {}).get("ko", {})
        expected[case["instruction_index"]].update(patch)
        if expected != case.get("ko_eval_all_kwargs"):
            raise ValueError("Unrecorded runtime override")
