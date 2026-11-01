"""Count input partitions in pinned Ko data; do not execute any checker or model.

Only finite dispatch on a kwargs-derived attribute in check_following is counted
as an input partition. Response-dependent outcomes and missing/invalid kwargs
belong to the fixed-response regression plan in design.md, not this denominator.
"""

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import urllib.request

import pyarrow
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent
SOURCE_NAMES = (
    "data/train-00000-of-00001.parquet",
    "ifeval_ko/instructions.py",
    "ifeval_ko/instructions_registry.py",
    "README_Ko.md",
)
# Mapping reviewed against the pinned source. AST checks below reject other
# literal dispatch fields or classes rather than silently assigning 'default'.
DISPATCH_FIELDS = {"_comparison_relation": "relation", "_postscript_marker": "postscript_marker"}
EXPECTED_DISPATCH = {
    "keywords:frequency": "relation",
    "length_constraints:number_sentences": "relation",
    "length_constraints:number_words": "relation",
    "detectable_content:postscript": "postscript_marker",
}
AUTHOR_CHANGED_CLASSES = {
    "KeywordChecker", "KeywordFrequencyChecker", "ParagraphFirstWordCheck",
    "ForbiddenWords", "RepeatPromptThenAnswer", "EndChecker",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def resolve(node, constants):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return constants[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return resolve(node.left, constants) + resolve(node.right, constants)
    if isinstance(node, ast.Subscript):
        return resolve(node.value, constants)[resolve(node.slice, constants)]
    raise ValueError(f"Unsupported source expression: {ast.dump(node)}")


def constants_in(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result


def source_info(blobs):
    registry = ast.parse(blobs["ifeval_ko/instructions_registry.py"])
    names = constants_in(registry)
    mapping = None
    for node in registry.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "INSTRUCTION_DICT":
            mapping = {resolve(k, names): v.attr for k, v in zip(node.value.keys, node.value.values)}
    require(mapping is not None, "INSTRUCTION_DICT not found")
    tree = ast.parse(blobs["ifeval_ko/instructions.py"])
    return mapping, {c.name: c for c in tree.body if isinstance(c, ast.ClassDef)}, constants_in(tree)


def inspect_checker(cls, constants):
    build = next(f for f in cls.body if isinstance(f, ast.FunctionDef) and f.name == "build_description")
    check = next(f for f in cls.body if isinstance(f, ast.FunctionDef) and f.name == "check_following")
    args = [a.arg for a in build.args.args + build.args.kwonlyargs if a.arg != "self"]
    dispatch = {}
    lines = []
    for node in ast.walk(check):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
            continue
        for left, right in ((test.left, test.comparators[0]), (test.comparators[0], test.left)):
            if not (isinstance(left, ast.Attribute) and isinstance(left.value, ast.Name) and left.value.id == "self"):
                continue
            try:
                value = resolve(right, constants)
            except (ValueError, KeyError):
                continue  # Comparison against a response-derived local value.
            require(left.attr in DISPATCH_FIELDS, f"Unreviewed dispatch field: {cls.name}.{left.attr}")
            field = DISPATCH_FIELDS[left.attr]
            require(field in args, f"Missing build argument: {field}")
            dispatch.setdefault(field, set()).add(value)
            lines.append(node.lineno)
    require(len(dispatch) <= 1, f"Multiple dispatch fields need review: {cls.name}")
    return {"class": cls.name, "build_args": args, "check_line": check.lineno,
            "dispatch": {k: sorted(v) for k, v in dispatch.items()}, "dispatch_lines": sorted(set(lines))}


def part_label(kw, spec):
    if not spec["dispatch"]:
        return "default"
    field, options = next(iter(spec["dispatch"].items()))
    require(kw.get(field) in options, f"Unreviewed dispatch value: {field}={kw.get(field)!r}")
    return f"{field}={kw[field]}"


def summarize(rows, specs):
    ids, partitions = Counter(), Counter()
    for row in rows:
        require(len(row["instruction_id_list"]) == len(row["kwargs"]), f"Mismatched kwargs: {row['key']}")
        for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
            spec = specs[iid]
            effective = {k: v for k, v in kw.items() if v}
            require(set(effective) == set(spec["build_args"]), f"Missing/extra checker args: {row['key']} {iid}")
            ids[iid] += 1
            partitions[(iid, part_label(kw, spec))] += 1
    return ids, partitions


def selection_summary(rows, full_ids, full_parts, specs):
    ids, parts = summarize(rows, specs)
    repeated = [r["key"] for r in rows if len(set(r["instruction_id_list"])) < len(r["instruction_id_list"])]
    multiple = [r["key"] for r in rows if len(r["instruction_id_list"]) > 1]
    return {"keys": [r["key"] for r in rows], "rows": len(rows), "instructions": sum(ids.values()),
            "ids_covered": len(ids), "ids_total": len(full_ids),
            "input_partitions_covered": len(parts), "input_partitions_total": len(full_parts),
            "missing_ids": sorted(set(full_ids) - set(ids)),
            "missing_input_partitions": [{"id": i, "case": c} for i, c in sorted(set(full_parts) - set(parts))],
            "repeated_id_keys": repeated, "multiple_instruction_keys": multiple,
            "model_execution": "not_run", "fixed_response_regression": "not_run"}


def ko_note(iid, cls):
    if cls in AUTHOR_CHANGED_CLASSES:
        return "제작자 열거 수정 클래스"
    return {"length_constraints:number_words": "Ko 단어 utility",
            "length_constraints:number_sentences": "Ko 문장 utility",
            "detectable_format:constrained_response": "Ko 고정 선택 문구"}.get(iid, "—")


def run(source_dir, out_dir):
    provenance_path = ROOT.parent / "checker-audit/provenance.json"
    provenance = json.loads(provenance_path.read_text())["ko"]
    blobs = {}
    for name in SOURCE_NAMES:
        info = provenance["files"][name]
        if source_dir:
            data = (source_dir / name).read_bytes()
        else:
            with urllib.request.urlopen(info["url"], timeout=30) as response:
                data = response.read()
        require(sha(data) == info["sha256"], f"Source hash mismatch: {name}")
        blobs[name] = data
    with tempfile.TemporaryDirectory(prefix="ifeval-ko-coverage-") as temp:
        data_path = Path(temp) / "train.parquet"
        data_path.write_bytes(blobs[SOURCE_NAMES[0]])
        rows = pq.read_table(data_path).to_pylist()
    mapping, classes, constants = source_info(blobs)
    observed = sorted({i for r in rows for i in r["instruction_id_list"]})
    specs = {i: inspect_checker(classes[mapping[i]], constants) for i in observed}
    actual_dispatch = {i: next(iter(s["dispatch"])) for i, s in specs.items() if s["dispatch"]}
    require(actual_dispatch == EXPECTED_DISPATCH, "Dispatch types changed; source review required")
    by_key = {r["key"]: r for r in rows}
    require(len(by_key) == len(rows), "Duplicate keys in source data")
    selection_path = ROOT / "selection.json"
    selection = json.loads(selection_path.read_text())
    keys = selection["keys"]
    require(len(keys) == len(set(keys)), "Duplicate selection keys")
    require(set(selection["preserved_diagnostic_keys"]) <= set(keys), "Diagnostic key missing")
    full_ids, full_parts = summarize(rows, specs)
    selected = [by_key[k] for k in keys]
    selected_ids, selected_parts = summarize(selected, specs)
    id_table, branch_table = [], []
    for iid in observed:
        id_table.append({"id": iid, "class": mapping[iid], "ko_change_note": ko_note(iid, mapping[iid]),
                         "full_occurrences": full_ids[iid], "selected_occurrences": selected_ids[iid],
                         "selected_keys": [r["key"] for r in selected if iid in r["instruction_id_list"]]})
    for (iid, case), total in sorted(full_parts.items()):
        matches = [(r["key"], idx) for r in selected for idx, (i, kw) in enumerate(zip(r["instruction_id_list"], r["kwargs"])) if i == iid and part_label(kw, specs[i]) == case]
        branch_table.append({"id": iid, "case": case, "full_occurrences": total, "check_line": specs[iid]["check_line"],
                             "selected_occurrences": selected_parts[(iid, case)],
                             "selected_matches": [{"key": k, "instruction_index": idx} for k, idx in matches]})
    summary = selection_summary(selected, full_ids, full_parts, specs)
    require(not summary["missing_ids"], "Selection misses instruction types")
    require(not summary["missing_input_partitions"], "Selection misses input partitions")
    require(summary["repeated_id_keys"], "Selection needs a repeated-ID example")
    require(summary["multiple_instruction_keys"], "Selection needs a multiple-instruction example")
    report = {"scope": "metadata input-partition coverage, not measured code-branch coverage or model evaluation",
              "status": selection["status"], "dataset": "allganize/IFEval-Ko", "revision": provenance["revision"],
              "split": "train", "full_rows": len(rows), "full_instructions": sum(full_ids.values()),
              "full_ids": len(full_ids), "full_input_partitions": len(full_parts),
              "sources": {n: {"url": provenance["files"][n]["url"], "sha256": sha(blobs[n])} for n in SOURCE_NAMES},
              "script_sha256": sha(Path(__file__).read_bytes()), "selection_sha256": sha(selection_path.read_bytes()),
              "runtime": {"python": sys.version.split()[0], "pyarrow": pyarrow.__version__},
              "checkers": specs, "selection": summary, "id_table": id_table, "input_partition_table": branch_table}
    lines = ["# 문항 선정 범위 집계", "", f"고정 revision: `{report['revision']}`. 데이터: {len(rows)}문항·{sum(full_ids.values())}개 지시·{len(full_ids)}종.",
             "", "입력 조건을 집계한 결과이며 모델 실행·코드 분기 실행률·고정 응답 회귀 결과가 아니다. 선정안은 팀 검토 전 제안이다.", "",
             "| 목록 | 문항 | 지시 | ID 포함 | 입력 경로 포함 | 반복 ID 문항 | 복수 지시 문항 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    lines.append(f"| 선정안 | {summary['rows']} | {summary['instructions']} | {summary['ids_covered']}/{summary['ids_total']} | {summary['input_partitions_covered']}/{summary['input_partitions_total']} | {summary['repeated_id_keys']} | {len(summary['multiple_instruction_keys'])} |")
    lines += ["", "## 유형별 대응", "", "| instruction ID | 전체 발생 | 선정 문항 발생 | 선정 key | Ko 관련 변경 근거 |", "| --- | --- | --- | --- | --- |"]
    for item in id_table:
        lines.append(f"| `{item['id']}` | {item['full_occurrences']} | {item['selected_occurrences']} | {', '.join(map(str,item['selected_keys']))} | {item['ko_change_note']} |")
    lines += ["", "Ko 수정 클래스 표시는 고정 제작자 문서의 열거 기준이며, ‘—’가 영어와의 완전한 동등성을 뜻하지 않는다.", "", "## 지시 유형별 입력 경로", "", "| instruction ID | 입력 경로 | 전체 발생 | 선정 문항 발생 |", "| --- | --- | --- | --- |"]
    for item in branch_table:
        lines.append(f"| `{item['id']}` | `{item['case']}` | {item['full_occurrences']} | {item['selected_occurrences']} |")
    lines += ["", "`default`는 관찰된 정상 kwargs에서 값에 따른 명시적 경로 선택이 없는 유형이다. 응답별 성공·실패를 하나로 합쳐 검증했다는 뜻이 아니다.",
              "", "입력 경로 집계는 check_following의 kwargs 유래 속성과 상수의 동등 비교를 AST로 확인하고 실제 데이터에 등장하는 값을 센다. 나머지 파라미터의 수치·문구·언어 값은 같은 연산의 인자이며 모든 값을 개별 경로로 세지 않는다.",
              "", "데이터에 없는 누락·오류·난수 fallback, 추신의 기타 표지, 응답에 따른 분기, NFC/NFD·정규식·문장/단어 경계는 고정 응답 회귀 대상이다. 이 출력은 해당 검사를 실행하지 않는다.", ""]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "coverage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (out_dir / "coverage.md").write_text("\n".join(lines))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Optional read-only cache containing data/ and ifeval_ko/ plus README_Ko.md")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    run(args.source_dir, args.output_dir)
