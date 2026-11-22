"""Aggregate the FP32 parity run and compare it with the BF16 run (read-only).

Public outputs hold counts, accuracies, hashes, maximum score differences and
margin distributions only: no question text, token IDs or per-item scores.
Per-item Lighteval/aligned mismatches go to report-private/ (archive only).
"""

import csv
import json
import statistics
import sys
from itertools import pairwise
from pathlib import Path

import transformers_click as tc
import transformers_fp32 as fp
from vllm_click import (
    MODELS,
    ROOT,
    compare_files,
    digest,
    file_hash,
    lines,
    read,
    require,
    write,
)

BF16_ROOT = Path("/workspace/transformers-bf16-20261120")
ROOTS = {"fp32": ROOT, "bf16": BF16_ROOT}
STRATA = {
    "all": lambda r: True,
    "four_choice": lambda r: r["num_choices"] == 4,
    "five_choice": lambda r: r["num_choices"] == 5,
    "gold_e": lambda r: r["gold"] == 4,
}


def path(root, model, condition):
    return root / "results" / model / f"full-transformers-{condition}.jsonl"


def correct(rows):
    return int(sum(r["metrics"]["acc"] for r in rows))


def pair(model, group, left, right, rows, stratum="all", same_inputs=True):
    """Compare two full result files on one stratum. left/right: (precision, condition).

    Scores are compared (and inputs required identical) only when same_inputs:
    base and #4420 prompts differ on five-choice items.
    """
    a, b = rows[left], rows[right]
    keys = sorted(k for k in a if STRATA[stratum](a[k]))
    diffs = (
        compare_files(
            path(ROOTS[left[0]], model, left[1]),
            path(ROOTS[right[0]], model, right[1]),
            keys,
        )
        if same_inputs
        else None
    )
    return {
        "model": model,
        "group": group,
        "left": ":".join(left),
        "right": ":".join(right),
        "stratum": stratum,
        "items": len(keys),
        "same_prediction": sum(a[k]["prediction"] == b[k]["prediction"] for k in keys),
        "exact_score_items": sum(d["max_abs_diff"] == 0 for d in diffs)
        if diffs
        else None,
        "max_abs_logprob_diff": max(d["max_abs_diff"] for d in diffs)
        if diffs
        else None,
        "left_correct": correct(a[k] for k in keys),
        "right_correct": correct(b[k] for k in keys),
        "prediction_changed": sum(
            a[k]["prediction"] != b[k]["prediction"] for k in keys
        ),
        "wrong_to_correct": sum(
            not a[k]["metrics"]["acc"] and bool(b[k]["metrics"]["acc"]) for k in keys
        ),
        "correct_to_wrong": sum(
            bool(a[k]["metrics"]["acc"]) and not b[k]["metrics"]["acc"] for k in keys
        ),
    }


def margin(scores):
    """Gap between the best and second-best candidate scores."""
    top = sorted(scores, reverse=True)
    return top[0] - top[1]


def mismatches(rows, precision):
    a = rows[precision, "lighteval_full"]
    b = rows[precision, "aligned_harness_full"]
    return [
        {
            "source_key": k,
            "gold": a[k]["gold"],
            "prediction_lighteval": a[k]["prediction"],
            "prediction_aligned": b[k]["prediction"],
            "margin_lighteval": margin(a[k]["scores"]),
            "margin_aligned": margin(b[k]["scores"]),
            "max_abs_diff": max(
                abs(x - y) for x, y in zip(a[k]["scores"], b[k]["scores"], strict=True)
            ),
        }
        for k in sorted(a)
        if a[k]["prediction"] != b[k]["prediction"]
    ]


def distribution(values):
    values = sorted(values)
    edges = (0, 1e-4, 1e-3, 1e-2, 1e-1, 1, float("inf"))
    return {
        "count": len(values),
        "min": values[0] if values else None,
        "median": statistics.median(values) if values else None,
        "max": values[-1] if values else None,
        "buckets": {
            f"[{lo:g},{hi:g})": sum(lo <= v < hi for v in values)
            for lo, hi in pairwise(edges)
        },
    }


def mismatch_summary(rows):
    found = {p: mismatches(rows, p) for p in ("fp32", "bf16")}
    keys = {p: {m["source_key"] for m in found[p]} for p in found}
    fp32_le = rows["fp32", "lighteval_full"]
    resolved = keys["bf16"] - keys["fp32"]
    summary = {
        p: {
            "mismatches": len(found[p]),
            **{
                field: distribution([m[field] for m in found[p]])
                for field in ("margin_lighteval", "margin_aligned", "max_abs_diff")
            },
        }
        for p in found
    }
    summary["bf16_mismatches_agreeing_in_fp32"] = len(resolved)
    summary["bf16_mismatches_agreeing_in_fp32_rate"] = (
        len(resolved) / len(keys["bf16"]) if keys["bf16"] else None
    )
    for path_name, condition in (
        ("lighteval", "lighteval_full"),
        ("aligned", "aligned_harness_full"),
    ):
        bf16 = rows["bf16", condition]
        summary[f"resolved_fp32_prediction_equals_bf16_{path_name}"] = sum(
            fp32_le[k]["prediction"] == bf16[k]["prediction"] for k in resolved
        )
    summary["fp32_mismatches_also_bf16_mismatch"] = len(keys["fp32"] & keys["bf16"])
    return summary, found


def main():
    protocol = read(ROOT / "prepared/protocol.json")
    tc.verify_run(protocol)
    parent = read(ROOT / "prepared/parent-bf16-protocol.json")
    require(
        digest(parent) == protocol["parent_protocol_sha256"], "Parent protocol differs"
    )
    require(
        digest(read(BF16_ROOT / "prepared/protocol.json"))
        == protocol["parent_protocol_sha256"],
        "BF16 run folder protocol differs",
    )
    original = {
        r["source_key"] for r in lines(ROOT / "prepared/old-aligned-inputs.jsonl")
    }
    results, comparisons, hashes = [], [], {}
    mismatch, private, pilot = {}, {}, {}
    for model in MODELS:
        gate = read(ROOT / "results" / model / "pilot-gate.json")
        require(
            gate["input_and_scoring_audit_passed"] and gate["fp32_audit_passed"],
            "Pilot audit missing",
        )
        pilot[model] = gate["comparisons"]
        rows = {}
        for condition in fp.CONDITIONS:
            for precision in ("fp32", "bf16"):
                file = path(ROOTS[precision], model, condition)
                loaded = (
                    fp.validated(file, protocol, 1995)
                    if precision == "fp32"
                    else tc.validate_rows(file, parent, 1995)
                )
                require(
                    {r["source_key"] for r in loaded} == original, "Coverage differs"
                )
                for r in loaded:
                    require(
                        r["prediction"]
                        == max(range(len(r["scores"])), key=r["scores"].__getitem__)
                        and r["metrics"]["acc"] == int(r["prediction"] == r["gold"]),
                        "Stored prediction/metric differs",
                    )
                rows[precision, condition] = {r["source_key"]: r for r in loaded}
                hashes[f"{precision}/{model}/{condition}"] = file_hash(file)
            fp32 = list(rows["fp32", condition].values())
            strata = {
                name: {"items": len(group), "correct": correct(group)}
                for name, test in STRATA.items()
                for group in [[r for r in fp32 if test(r)]]
            }
            require(
                [
                    strata[s]["items"]
                    for s in ("all", "four_choice", "five_choice", "gold_e")
                ]
                == [1995, 1739, 256, 49],
                "Wrong strata counts",
            )
            norm = [r["metrics"].get("acc_norm") for r in fp32]
            results.append(
                {
                    "model": model,
                    "condition": condition,
                    "dtype": "float32",
                    "items": 1995,
                    "correct": strata["all"]["correct"],
                    "acc": strata["all"]["correct"] / 1995,
                    "acc_norm": sum(norm) / 1995 if None not in norm else None,
                    "four_choice_correct": strata["four_choice"]["correct"],
                    "five_choice_correct": strata["five_choice"]["correct"],
                    "gold_e_correct": strata["gold_e"]["correct"],
                    "input_and_scoring_audit_passed": True,
                    "fp32_audit_passed": True,
                    "result_sha256": hashes[f"fp32/{model}/{condition}"],
                }
            )
        le, al = "lighteval_full", "aligned_harness_full"
        comparisons.append(pair(model, "a", ("fp32", le), ("fp32", al), rows))
        comparisons.append(  # identical inputs on four-choice items
            pair(
                model,
                "b",
                ("fp32", "base_letter"),
                ("fp32", "pr4420_letter"),
                rows,
                "four_choice",
            )
        )
        for condition in fp.CONDITIONS:
            comparisons.append(
                pair(model, "c", ("bf16", condition), ("fp32", condition), rows)
            )
        for left in (le, al):  # which BF16 path agrees more with FP32
            for right in (le, al):
                comparisons.append(
                    pair(model, "d", ("bf16", left), ("fp32", right), rows)
                )
        comparisons.append(pair(model, "d", ("bf16", le), ("bf16", al), rows))
        mismatch[model], private[model] = mismatch_summary(rows)
        for stratum in STRATA:
            comparisons.append(
                pair(
                    model,
                    "e",
                    ("fp32", "base_letter"),
                    ("fp32", "pr4420_letter"),
                    rows,
                    stratum,
                    same_inputs=stratum == "four_choice",
                )
            )
    output = ROOT / "report"
    write(
        output / "results.json",
        {
            "complete": True,
            "dtype": "float32",
            "protocol_sha256": digest(protocol),
            "prediction_parity_lighteval_vs_aligned": {
                c["model"]: c["same_prediction"] == c["items"]
                for c in comparisons
                if c["group"] == "a"
            },
            "results": results,
            "comparisons": comparisons,
            "lighteval_vs_aligned_mismatches": mismatch,
            "pilot_gate_comparisons": pilot,
        },
    )
    write(ROOT / "report-private/lighteval-vs-aligned-mismatches.json", private)
    for name, table in (("results.csv", results), ("comparisons.csv", comparisons)):
        with (output / name).open("w") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(table[0]))
            writer.writeheader()
            writer.writerows(table)
    runtime = {
        model: [
            read(p)
            for p in sorted((ROOT / "results" / model / "runtime").glob("*.json"))
        ]
        for model in MODELS
    }
    write(
        output / "provenance.json",
        {
            "protocol_sha256": digest(protocol),
            "protocol_file_sha256": file_hash(ROOT / "prepared/protocol.json"),
            "protocol": protocol,
            "report_script_sha256": file_hash(Path(__file__)),
            "packages_sha256": file_hash(ROOT / "environment/packages.txt"),
            "source_manifest_sha256": file_hash(ROOT / "environment/sources.json"),
            "models": {
                m: read(ROOT / "environment" / f"model-{m}.json") for m in MODELS
            },
            "result_sha256": hashes,
            "steps": lines(ROOT / "results/steps.jsonl"),
            "runtime": runtime,
            "container": read(ROOT / "records/container.json"),
            "restarts": read(ROOT / "restarts.json")
            if (ROOT / "restarts.json").exists()
            else [],
        },
    )
    print(
        json.dumps(
            {"results": results, "comparisons": comparisons, "mismatch": mismatch},
            indent=1,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
