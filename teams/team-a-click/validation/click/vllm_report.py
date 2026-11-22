"""Validate all twelve completed results and publish aggregate-only reports."""

import csv
from collections import defaultdict

from polyglot_core import CULTURE
from vllm_click import (
    CONDITIONS,
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


def main():
    protocol = read(ROOT / "prepared/protocol.json")
    original = {
        r["source_key"]: r for r in lines(ROOT / "prepared/old-aligned-inputs.jsonl")
    }
    matrix = {
        r["source_key"]: r for r in lines(ROOT / "prepared/old-matrix-inputs.jsonl")
    }
    output = ROOT / "report"
    output.mkdir(exist_ok=True)
    (output / "reports").mkdir(exist_ok=True)
    summaries, category_rows, comparisons, effects = [], [], [], []
    passed = True
    for model in MODELS:
        folder = ROOT / "results" / model
        gate = read(folder / "pilot-gate.json")
        require(
            gate["passed"] and gate["protocol_sha256"] == digest(protocol),
            "Pilot gate invalid",
        )
        checks = {c["label"]: c for c in gate["checks"]}
        results = {}
        for condition in CONDITIONS:
            path = folder / f"full-vllm-{condition}.jsonl"
            identity = read(path.with_suffix(".protocol.json"))
            require(
                identity["protocol_sha256"] == digest(protocol)
                and identity["runner_sha256"] == file_hash(ROOT / "code/vllm_click.py"),
                "Result provenance differs",
            )
            rows = lines(path)
            require(
                len(rows) == 1995 and {r["source_key"] for r in rows} == set(original),
                "Incomplete or duplicated full result",
            )
            for row in rows:
                require(
                    row["row_sha256"]
                    == digest({k: v for k, v in row.items() if k != "row_sha256"}),
                    "Result integrity failure",
                )
                require(
                    row["prediction"]
                    == max(range(len(row["scores"])), key=row["scores"].__getitem__),
                    "Prediction mismatch",
                )
                require(
                    row["metrics"]["acc"] == int(row["prediction"] == row["gold"]),
                    "Metric mismatch",
                )
                require(
                    row["gold"] == original[row["source_key"]]["gold_index"],
                    "Gold differs from frozen input",
                )
            results[condition] = {r["source_key"]: r for r in rows}
            correct = sum(r["metrics"]["acc"] for r in rows)
            norm = (
                sum(r["metrics"]["acc_norm"] for r in rows) / len(rows)
                if all("acc_norm" in r["metrics"] for r in rows)
                else None
            )
            summary = {
                "model": model,
                "condition": condition,
                "backend": "vllm",
                "dtype": "bfloat16",
                "items": len(rows),
                "correct": int(correct),
                "acc": correct / len(rows),
                "acc_norm": norm,
                "full_result_sha256": file_hash(path),
                "pilot_passed": True,
            }
            summaries.append(summary)
            strata = {}
            for label, subset in [
                ("four_choice", [r for r in rows if r["num_choices"] == 4]),
                ("five_choice", [r for r in rows if r["num_choices"] == 5]),
                ("gold_e", [r for r in rows if r["gold"] == 4]),
            ]:
                strata[label] = {
                    "items": len(subset),
                    "correct": sum(r["metrics"]["acc"] for r in subset),
                }
            aggregates = {}
            for basis in ("source", "native"):
                groups = defaultdict(list)
                for row in rows:
                    category = row["category"]
                    if basis == "native" and condition not in CONDITIONS[:2]:
                        category = matrix[row["source_key"]]["variants"][condition][
                            "native_category"
                        ]
                    groups[category].append(row)
                for category, group in sorted(groups.items()):
                    category_rows.append(
                        {
                            "model": model,
                            "condition": condition,
                            "basis": basis,
                            "category": category,
                            "items": len(group),
                            "correct": int(sum(r["metrics"]["acc"] for r in group)),
                            "acc": sum(r["metrics"]["acc"] for r in group) / len(group),
                        }
                    )
                require(len(groups) == 11, "Category coverage differs")
                aggregates[basis] = {
                    "category_macro": sum(
                        sum(r["metrics"]["acc"] for r in group) / len(group)
                        for group in groups.values()
                    )
                    / len(groups)
                }
                for label, included in (
                    ("culture_micro", CULTURE),
                    ("language_micro", set(groups) - CULTURE),
                ):
                    subset = [
                        r
                        for category, group in groups.items()
                        if category in included
                        for r in group
                    ]
                    aggregates[basis][label] = {
                        "items": len(subset),
                        "correct": int(sum(r["metrics"]["acc"] for r in subset)),
                        "acc": sum(r["metrics"]["acc"] for r in subset) / len(subset),
                    }
            write(
                output / "reports" / f"{model}-{condition}.json",
                {**summary, "strata": strata, "aggregates": aggregates},
            )
            text = f"# {model} · {condition}\n\nvLLM / BF16 · 0-shot · 단일 지시문 · 원본 보기 순서\n\n정답 **{int(correct)}/1995**, acc **{100 * summary['acc']:.4f}%**.\n\n"
            text += "| 구분 | 문항 | 정답 |\n|---|---:|---:|\n"
            for label, value in strata.items():
                text += f"| {label} | {value['items']} | {int(value['correct'])} |\n"
            (output / "reports" / f"{model}-{condition}.md").write_text(text)
        aligned = compare_files(
            folder / "full-vllm-lighteval_full.jsonl",
            folder / "full-vllm-aligned_harness_full.jsonl",
            original,
        )
        atol = checks["aligned-parity"]["atol"]
        item = {
            "model": model,
            "comparison": "lighteval_vs_aligned_harness",
            "items": 1995,
            "same_prediction": sum(r["same_prediction"] for r in aligned),
            "max_abs_logprob_diff": max(r["max_abs_diff"] for r in aligned),
            "atol": atol,
            "passed": all(
                r["same_prediction"] and r["max_abs_diff"] <= atol for r in aligned
            ),
        }
        comparisons.append(item)
        passed &= item["passed"]
        four = [k for k, r in original.items() if len(r["raw"]["choices"]) == 4]
        for mode in ("letter", "full"):
            a, b = "base_" + mode, "pr4420_" + mode
            same = compare_files(
                folder / f"full-vllm-{a}.jsonl", folder / f"full-vllm-{b}.jsonl", four
            )
            atol = min(
                checks[a + ":reference"]["atol"], checks[b + ":reference"]["atol"]
            )
            ok = all(r["same_prediction"] and r["max_abs_diff"] <= atol for r in same)
            passed &= ok
            comparisons.append(
                {
                    "model": model,
                    "comparison": "four_choice_base_vs_pr4420_" + mode,
                    "items": len(four),
                    "same_prediction": sum(r["same_prediction"] for r in same),
                    "max_abs_logprob_diff": max(r["max_abs_diff"] for r in same),
                    "atol": atol,
                    "passed": ok,
                }
            )
        for left, right in (
            ("base_letter", "pr4420_letter"),
            ("base_full", "pr4420_full"),
            ("base_letter", "base_full"),
            ("pr4420_letter", "pr4420_full"),
        ):
            for stratum in ("all", "four_choice", "five_choice", "gold_e"):
                pairs = [(results[left][key], results[right][key]) for key in original]
                if stratum != "all":
                    pairs = [
                        (a, b)
                        for a, b in pairs
                        if (
                            a["gold"] == 4
                            if stratum == "gold_e"
                            else a["num_choices"]
                            == (4 if stratum == "four_choice" else 5)
                        )
                    ]
                effects.append(
                    {
                        "model": model,
                        "from": left,
                        "to": right,
                        "stratum": stratum,
                        "items": len(pairs),
                        "prediction_changed": sum(
                            a["prediction"] != b["prediction"] for a, b in pairs
                        ),
                        "wrong_to_correct": sum(
                            not a["metrics"]["acc"] and bool(b["metrics"]["acc"])
                            for a, b in pairs
                        ),
                        "correct_to_wrong": sum(
                            bool(a["metrics"]["acc"]) and not b["metrics"]["acc"]
                            for a, b in pairs
                        ),
                    }
                )
    write(
        output / "results.json",
        {
            "complete": True,
            "validation_passed": passed,
            "results": summaries,
            "comparisons": comparisons,
            "effects": effects,
        },
    )
    write(
        output / "provenance.json",
        {
            "protocol": protocol,
            "models": {
                model: read(ROOT / "environment" / f"model-{model}.json")
                for model in MODELS
            },
            "packages_sha256": file_hash(ROOT / "environment/packages.txt"),
            "code_sha256": {
                p.name: file_hash(p) for p in sorted((ROOT / "code").glob("vllm*.py"))
            },
        },
    )
    for filename, rows in [
        ("results.csv", summaries),
        ("categories.csv", category_rows),
        ("comparisons.csv", comparisons),
        ("effects.csv", effects),
    ]:
        with (output / filename).open("w") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    text = "# CLIcK Qwen3.8 · Kanana2 vLLM 평가 결과\n\n"
    text += f"전체 12개 결과 완료. 비교 검증: {'PASS' if passed else 'FAIL — 불일치 조사 필요'}.\n\n"
    text += "| 모델 | 조건 | 정답/문항 | acc | acc_norm |\n|---|---|---:|---:|---:|\n"
    for row in summaries:
        norm = f"{100 * row['acc_norm']:.4f}%" if row["acc_norm"] is not None else "—"
        text += f"| {row['model']} | {row['condition']} | {row['correct']}/{row['items']} | {100 * row['acc']:.4f}% | {norm} |\n"
    text += "\n입력 정렬 harness와 native pr4420_full은 서로 다른 조건이다. 과거 Polyglot은 Transformers/FP32이며 이번 vLLM/BF16과 실행 환경이 다르다. 논문의 지시문 3종 × 보기 순환 평균을 재현한 결과가 아니다.\n"
    (output / "README.md").write_text(text)
    require(
        passed, "Full result validation failed; reports retain explicit FAIL status"
    )
    print("All twelve results validated and aggregate reports written", flush=True)


if __name__ == "__main__":
    main()
