"""Pure validation/report helpers; no model or evaluation-library imports."""

import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path

LIGHTEVAL_REVISION = "efb7e657802dd0d760473ffa9307063928ce4b41"
HARNESS_REVISION = "7a7b48afa7c294a5992008053bd1ec0042906c6d"
DATA_REVISION = "d61627859645b5e6edc03fd9f835735d8226fa4e"
MODELS = {
    "1.3b": ("EleutherAI/polyglot-ko-1.3b", "557e162cf6e944fdbae05bab2e45d066a125eacb"),
    "12.8b": (
        "EleutherAI/polyglot-ko-12.8b",
        "09dfc839067bf44e7f52976eca8adbc17f04e1b0",
    ),
}
CULTURE = {
    "society",
    "tradition",
    "history",
    "law",
    "politics",
    "economy",
    "geography",
    "popular",
}
RAW_FIELDS = ("id", "paragraph", "question", "choices", "answer")
SETTINGS = {
    "dtype": "float32",
    "batch_size": 1,
    "batch_unit": "native configuration: Lighteval 1 document (4/5 candidates), harness/reference 1 candidate",
    "attention": "eager",
    "tf32": False,
    "max_length": 2048,
    "chat_template": False,
    "add_special_tokens": False,
    "fewshots": 0,
    "length_normalization": False,
    "seed": 1234,
    "prompt_version": "click_harness_layout_v3",
    "quantization": None,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def harness_payload(row):
    """Independent reference serializer, not a call to Lighteval's prompt function."""
    for field in ("id", "paragraph", "question", "answer"):
        require(isinstance(row.get(field), str), f"Invalid {field}")
    choices = row.get("choices")
    require(
        isinstance(choices, list) and len(choices) in (4, 5),
        "Expected four or five choices",
    )
    require(
        all(isinstance(c, str) and c.strip() for c in choices), "Empty/invalid choice"
    )
    require(bool(row["question"].strip()), "Empty question")
    require(choices.count(row["answer"]) == 1, "Answer must match one choice")
    labels = list("ABCDE"[: len(choices)])
    has_context = bool(row["paragraph"].strip())
    instruction = (
        "주어진 맥락을 천천히 읽고, 질문에 대한 적절한 정답을 "
        if has_context
        else "주어진 질문을 천천히 읽고, 적절한 정답을 "
    )
    instruction += ", ".join(labels) + " 중에 골라 알파벳 하나로 답하시오.\n\n"
    context = "맥락: " + row["paragraph"] + "\n" if has_context else ""
    options = ", ".join(label + ": " + choice for label, choice in zip(labels, choices))
    return {
        "query": instruction
        + context
        + "질문: "
        + row["question"]
        + "\n보기:\n"
        + options
        + "\n정답:",
        "choices": [
            " " + label + ". " + choice for label, choice in zip(labels, choices)
        ],
        "gold_index": choices.index(row["answer"]),
    }


def source_records(snapshot, manifest_path):
    """Require the existing source manifest, including every file and row hash."""
    manifest = read_json(manifest_path)
    require(manifest["revision"] == DATA_REVISION, "Dataset revision mismatch")
    expected = {entry["path"] for entry in manifest["files"]}
    actual = {
        p.relative_to(snapshot).as_posix()
        for p in (snapshot / "Dataset").rglob("*.json")
    }
    require(actual == expected, "Source file set mismatch")
    indexed = {r["source_key"]: r for r in manifest["rows"]}
    records = []
    for entry in manifest["files"]:
        path = snapshot / entry["path"]
        require(file_digest(path) == entry["sha256"], f"Changed file: {entry['path']}")
        rows = read_json(path)
        require(len(rows) == entry["rows"], "File row count changed")
        for i, raw in enumerate(rows):
            key = f"{DATA_REVISION}:{entry['path']}#{i}"
            meta = indexed[key]
            raw_hash = digest({k: raw[k] for k in RAW_FIELDS})
            require(raw_hash == meta["raw_row_sha256"], f"Changed source row: {key}")
            require(
                meta["category"] == entry["category"]
                and meta["original_id"] == raw["id"],
                "Source metadata mismatch",
            )
            records.append({**meta, "raw": raw})
    require(len(records) == len(indexed) == 1995, "Expected all 1,995 rows")
    return sorted(records, key=lambda r: (r["category"], r["path"], r["row_number"]))


def token_contract(tokenizer, payload):
    """Untruncated semantic inputs and scored tokens, without BOS/EOS."""
    context = tokenizer.encode(payload["query"], add_special_tokens=False)
    require(context, "Empty context tokens")
    continuations = []
    for choice in payload["choices"]:
        suffix = tokenizer.encode(choice, add_special_tokens=False)
        whole = tokenizer.encode(payload["query"] + choice, add_special_tokens=False)
        require(
            whole == context + suffix, "Joint/separate tokenization boundary differs"
        )
        require(suffix, "Empty scored continuation")
        require(
            len(whole) <= SETTINGS["max_length"],
            "BLOCKED_CONTEXT: would truncate input",
        )
        continuations.append(suffix)
    return {"context": context, "continuations": continuations}


def select_samples(records, lengths):
    groups = defaultdict(list)
    for r in records:
        groups[r["category"]].append(r)
    calibration, validation = set(), set()
    for group in groups.values():
        calibration.update(r["source_key"] for r in group[:5])
        validation.update(r["source_key"] for r in group[5:10])
    remaining = [r for r in records if r["source_key"] not in calibration]
    counts = Counter(r["original_id"] for r in records)
    predicates = [
        lambda r: r["raw"]["choices"].index(r["raw"]["answer"]) == 4,
        lambda r: counts[r["original_id"]] > 1,
        lambda r: r["path"].endswith("Functional_CSAT.json") and r["row_number"] == 82,
    ]
    for n in (4, 5):
        for context in (False, True):
            predicates.append(
                lambda r, n=n, context=context: (
                    len(r["raw"]["choices"]) == n
                    and bool(r["raw"]["paragraph"].strip()) == context
                )
            )
    for predicate in predicates:
        candidates = [r for r in remaining if predicate(r)]
        require(candidates, "Missing required pilot stratum")
        validation.add(candidates[0]["source_key"])
    for category in groups:
        candidates = [r for r in remaining if r["category"] == category]
        validation.add(
            max(candidates, key=lambda r: lengths[r["source_key"]])["source_key"]
        )
    require(not calibration & validation, "Pilot sets overlap")
    return {"calibration": sorted(calibration), "validation": sorted(validation)}


def validate_result(row, expected):
    for key in (
        "source_key",
        "category",
        "raw_row_sha256",
        "payload_sha256",
        "tokens_sha256",
        "gold_index",
    ):
        require(row.get(key) == expected[key], f"Result {key} mismatch")
    scores = row.get("scores", [])
    require(
        len(scores) == expected["num_choices"]
        and all(isinstance(s, (float, int)) and math.isfinite(s) for s in scores),
        "Missing/non-finite scores",
    )
    prediction = max(range(len(scores)), key=lambda i: scores[i])
    require(row.get("prediction") == prediction, "Wrong argmax/tie handling")
    require(
        row.get("correct") == int(prediction == row["gold_index"]), "Wrong sample score"
    )
    require(
        row.get("truncated") == 0 and row.get("input_verified") is True,
        "Input trace missing or truncated",
    )


def load_results(path, expected):
    result = {}
    if not Path(path).exists():
        return result
    for line in Path(path).read_text().splitlines():
        row = json.loads(
            line
        )  # An interrupted partial line is an error, never silently discarded.
        key = row["source_key"]
        require(
            key in expected and key not in result, "Unexpected or duplicate result key"
        )
        validate_result(row, expected[key])
        result[key] = row
    return result


def append_result(path, row):
    with Path(path).open("a") as stream:
        stream.write(canonical(row) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def establish_tolerance(engines, samples):
    """Freeze calibration-derived tolerance; validation cannot increase it."""
    keys = set(samples["calibration"]) | set(samples["validation"])
    require(
        set(engines) == {"lighteval", "harness", "reference"},
        "All three pilot engines required",
    )
    require(
        all(set(rows) == keys for rows in engines.values()), "Incomplete pilot evidence"
    )
    max_delta = 0.0
    for key in samples["calibration"]:
        rows = [rows[key] for rows in engines.values()]
        require(
            len({r["prediction"] for r in rows}) == 1,
            f"Calibration prediction disagreement: {key}",
        )
        for scores in zip(*(r["scores"] for r in rows)):
            max_delta = max(max_delta, max(scores) - min(scores))
    atol = max(1e-6, max_delta * 2)
    failures = []
    for key in samples["validation"]:
        rows = [rows[key] for rows in engines.values()]
        delta = max(max(s) - min(s) for s in zip(*(r["scores"] for r in rows)))
        if len({r["prediction"] for r in rows}) != 1 or delta > atol:
            failures.append({"source_key": key, "max_abs_diff": delta})
    return {
        "status": "PASS" if not failures else "FAIL",
        "atol": atol,
        "rtol": 0,
        "calibration_max_abs_diff": max_delta,
        "validation_failures": failures,
    }


def comparison(left, right, atol):
    require(set(left) == set(right), "Different evaluated item sets")
    groups = defaultdict(list)
    mismatches = []
    for key, a in left.items():
        b = right[key]
        for field in ("category", "gold_index", "payload_sha256", "tokens_sha256"):
            require(a[field] == b[field], f"Comparison {field} differs: {key}")
        delta = max(abs(x - y) for x, y in zip(a["scores"], b["scores"]))
        same = a["prediction"] == b["prediction"]
        item = (a["correct"], b["correct"], same, delta)
        groups[a["category"]].append(item)
        if not same or delta > atol:
            mismatches.append(
                {
                    "source_key": key,
                    "prediction_same": same,
                    "max_abs_diff": delta,
                    "lighteval_prediction": a["prediction"],
                    "harness_prediction": b["prediction"],
                }
            )

    def summarize(items):
        n = len(items)
        return {
            "items": n,
            "lighteval_correct": sum(i[0] for i in items),
            "harness_correct": sum(i[1] for i in items),
            "lighteval_accuracy": sum(i[0] for i in items) / n,
            "harness_accuracy": sum(i[1] for i in items) / n,
            "same_prediction": sum(i[2] for i in items),
            "max_abs_diff": max(i[3] for i in items),
        }

    categories = {
        category: summarize(items) for category, items in sorted(groups.items())
    }
    all_items = [item for items in groups.values() for item in items]
    aggregates = {"all_micro": summarize(all_items)}
    for name, included in (
        ("culture_micro", CULTURE),
        ("language_micro", set(groups) - CULTURE),
    ):
        items = [i for c, items in groups.items() if c in included for i in items]
        if items:
            aggregates[name] = summarize(items)
    aggregates["category_macro"] = {
        engine + "_accuracy": sum(c[engine + "_accuracy"] for c in categories.values())
        / len(categories)
        for engine in ("lighteval", "harness")
    }
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "categories": categories,
        "aggregates": aggregates,
        "mismatches": mismatches,
    }
