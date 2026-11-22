"""Private matrix input/result integrity and public aggregate helpers."""

from collections import Counter, defaultdict
from pathlib import Path

from polyglot_core import (
    CULTURE,
    DATA_REVISION,
    RAW_FIELDS,
    digest,
    file_digest,
    read_json,
    require,
    validate_result,
)

BASE_REVISION = "d6de81643928d653435c431bae19945d41d32520"
PR_REVISION = "7a7b48afa7c294a5992008053bd1ec0042906c6d"
CONDITIONS = ("base_letter", "pr4420_letter", "base_full", "pr4420_full")
SETTINGS = {
    "dtype": "float32",
    "attention": "eager",
    "tf32": False,
    "batch_size": 1,
    "batch_unit": "one candidate per forward",
    "seed": 1234,
    "max_length": 2048,
    "fewshots": 0,
    "quantization": None,
    "add_bos_token": False,
    "add_eos_token": False,
    "chat_template": False,
    "truncation": False,
    "logits_cache": False,
    "primary_metric": "acc",
    "secondary_metric": "acc_norm",
    "acc_norm_definition": "argmax(sum log probability / len(candidate string)); Python Unicode character count, excluding target delimiter",
    "target_adapter_full": "original_choices.index(original_doc_to_target(raw)); preserves original correct answer while candidates become label + '. ' + original option",
    "scope": "native YAML / Python API / HFLM / filters / process_results; not full CLI parity",
}


def original_records(old_output, manifest_path):
    old = read_json(old_output / "prepared.json")
    require(old["dataset_revision"] == DATA_REVISION, "Old dataset revision differs")
    require(old["manifest_sha256"] == file_digest(manifest_path), "Manifest changed")
    require(
        old["inputs_sha256"] == file_digest(old_output / "inputs.jsonl"),
        "Old inputs changed",
    )
    import json

    rows = [
        json.loads(line)
        for line in (old_output / "inputs.jsonl").read_text().splitlines()
    ]
    manifest = read_json(manifest_path)
    expected = {r["source_key"]: r for r in manifest["rows"]}
    require(len(rows) == len(expected) == 1995, "Missing original rows")
    require(len({r["source_key"] for r in rows}) == 1995, "Duplicate provenance")
    records = []
    for row in rows:
        meta = expected[row["source_key"]]
        require(all(row[k] == meta[k] for k in meta), "Original provenance changed")
        require(
            digest({k: row["raw"][k] for k in RAW_FIELDS}) == meta["raw_row_sha256"],
            "Original raw hash changed",
        )
        records.append({**meta, "raw": row["raw"]})
    require(
        len({r["raw_row_sha256"] for r in records}) == 1995,
        "Ambiguous raw hashes require file-position transport",
    )
    return old, records


def native_gold(labels, target):
    require(
        isinstance(target, str) and target in labels,
        "Native string target missing from native choices",
    )
    return labels.index(target)


def candidate_diagnostics(raw, labels, version):
    result = []
    if len(labels) != len(raw["choices"]):
        result.append(
            {
                "id": raw["id"],
                "version": version,
                "native_candidates": len(labels),
                "raw_choices": len(raw["choices"]),
                "csat_in_id": "CSAT" in raw["id"],
            }
        )
    return result


def validate_matrix_result(row, expected):
    validate_result(row, expected)
    for key in (
        "condition",
        "native_category",
        "native_task",
        "source_category",
        "config_sha256",
    ):
        require(row.get(key) == expected[key], f"Matrix result {key} mismatch")
    lengths = expected["choice_char_lengths"]
    pred_norm = max(range(len(lengths)), key=lambda i: row["scores"][i] / lengths[i])
    require(row.get("prediction_norm") == pred_norm, "Wrong native acc_norm argmax")
    require(
        row.get("acc_norm") == int(pred_norm == row["gold_index"]),
        "Wrong native acc_norm",
    )


def load_matrix_results(path, expected):
    import json

    result = {}
    if not Path(path).exists():
        return result
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        key = row["source_key"]
        require(
            key in expected and key not in result, "Unexpected/duplicate matrix result"
        )
        validate_matrix_result(row, expected[key])
        result[key] = row
    return result


def pilot_gate(native, reference, samples):
    keys = set(samples["calibration"]) | set(samples["validation"])
    require(set(native) == set(reference) == keys, "Incomplete matrix pilot")
    require(
        not set(samples["calibration"]) & set(samples["validation"]),
        "Overlapping pilot sets",
    )
    maximum = 0.0
    for key in samples["calibration"]:
        a, b = native[key], reference[key]
        require(
            a["prediction"] == b["prediction"]
            and a["prediction_norm"] == b["prediction_norm"],
            f"Calibration prediction mismatch: {key}",
        )
        maximum = max(
            maximum,
            max(abs(x - y) for x, y in zip(a["scores"], b["scores"], strict=True)),
        )
    atol = max(1e-6, 2 * maximum)
    failures = []
    for key in samples["validation"]:
        a, b = native[key], reference[key]
        delta = max(abs(x - y) for x, y in zip(a["scores"], b["scores"], strict=True))
        if (
            delta > atol
            or a["prediction"] != b["prediction"]
            or a["prediction_norm"] != b["prediction_norm"]
        ):
            failures.append({"source_key": key, "max_abs_diff": delta})
    return {
        "status": "FAIL" if failures else "PASS",
        "atol": atol,
        "rtol": 0,
        "calibration_max_abs_diff": maximum,
        "validation_failures": failures,
    }


def aggregate(rows):
    rows = list(rows)
    require(rows, "Empty aggregate")
    counts = Counter("ABCDE"[r["prediction"]] for r in rows)
    return {
        "items": len(rows),
        "correct": sum(r["correct"] for r in rows),
        "acc": sum(r["correct"] for r in rows) / len(rows),
        "correct_norm": sum(r["acc_norm"] for r in rows),
        "acc_norm": sum(r["acc_norm"] for r in rows) / len(rows),
        "prediction_counts": {label: counts[label] for label in "ABCDE"},
    }


def condition_summary(rows):
    rows = list(rows.values())
    result = {"overall": aggregate(rows)}
    for field in ("native_category", "source_category"):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row[field]].append(row)
        categories = {c: aggregate(group) for c, group in sorted(grouped.items())}
        require(
            len(categories) == 11
            and sum(v["items"] for v in categories.values()) == 1995,
            "Category denominators differ",
        )
        result[field] = {
            "categories": categories,
            "macro_acc": sum(v["acc"] for v in categories.values()) / 11,
            "macro_acc_norm": sum(v["acc_norm"] for v in categories.values()) / 11,
            "culture": aggregate(r for r in rows if r[field] in CULTURE),
            "language": aggregate(r for r in rows if r[field] not in CULTURE),
        }
    result["strata"] = {
        "four_choice": aggregate(r for r in rows if r["num_choices"] == 4),
        "five_choice": aggregate(r for r in rows if r["num_choices"] == 5),
        "gold_E": aggregate(r for r in rows if r["gold_index"] == 4),
    }
    require(
        [result["strata"][k]["items"] for k in ("four_choice", "five_choice", "gold_E")]
        == [1739, 256, 49],
        "Stratum denominators changed",
    )
    return result


def paired_delta(left, right):
    require(set(left) == set(right), "Pair item coverage differs")
    switches = sum(left[k]["prediction"] != right[k]["prediction"] for k in left)
    wrong_right = sum(not left[k]["correct"] and right[k]["correct"] for k in left)
    right_wrong = sum(left[k]["correct"] and not right[k]["correct"] for k in left)
    require(
        sum(right[k]["correct"] - left[k]["correct"] for k in left)
        == wrong_right - right_wrong,
        "Delta denominator inconsistency",
    )
    return {
        "items": len(left),
        "prediction_switches": switches,
        "wrong_to_correct": wrong_right,
        "correct_to_wrong": right_wrong,
        "acc_delta_percentage_points": 100 * (wrong_right - right_wrong) / len(left),
        "acc_norm_delta_percentage_points": 100
        * sum(right[k]["acc_norm"] - left[k]["acc_norm"] for k in left)
        / len(left),
    }


def verify_four_choice_equivalence(results):
    for mode in ("letter", "full"):
        left, right = results[f"base_{mode}"], results[f"pr4420_{mode}"]
        require(set(left) == set(right), "Revision coverage differs")
        for key, row in left.items():
            if row["num_choices"] == 4:
                other = right[key]
                require(
                    row["payload_sha256"] == other["payload_sha256"]
                    and row["tokens_sha256"] == other["tokens_sha256"],
                    "Four-choice inputs differ",
                )
                require(
                    row["scores"] == other["scores"]
                    and row["prediction"] == other["prediction"]
                    and row["prediction_norm"] == other["prediction_norm"],
                    f"Identical four-choice execution differs: {key}",
                )
