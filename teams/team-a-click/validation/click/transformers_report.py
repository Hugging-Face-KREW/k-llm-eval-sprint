"""Aggregate native BF16 outputs; numerical parity is reported separately."""

import collections
import csv

from polyglot_core import CULTURE
from transformers_click import (
    CONDITIONS,
    MODELS,
    ROOT,
    comparisons,
    file_hash,
    lines,
    read,
    require,
    validate_rows,
    verify_run,
    write,
)


def metric(rows):
    correct = int(sum(r["metrics"]["acc"] for r in rows))
    return {"items": len(rows), "correct": correct, "acc": correct / len(rows)}


def main():
    protocol = read(ROOT / "prepared/protocol.json")
    verify_run(protocol)
    original = {
        r["source_key"]: r for r in lines(ROOT / "prepared/old-aligned-inputs.jsonl")
    }
    matrix = {
        r["source_key"]: r for r in lines(ROOT / "prepared/old-matrix-inputs.jsonl")
    }
    output = ROOT / "report"
    (output / "reports").mkdir(parents=True, exist_ok=True)
    summaries, categories, checks, effects = [], [], [], []
    for model in MODELS:
        folder = ROOT / "results" / model
        require(
            read(folder / "pilot-gate.json")["input_and_scoring_audit_passed"],
            "Missing pilot audit",
        )
        results = {}
        for condition in CONDITIONS:
            path = folder / f"full-transformers-{condition}.jsonl"
            rows = validate_rows(path, protocol, 1995)
            require(
                {r["source_key"] for r in rows} == set(original),
                "Incorrect full coverage",
            )
            for row in rows:
                key = row["source_key"]
                payload = (
                    original[key]["payload"]
                    if condition in CONDITIONS[:2]
                    else matrix[key]["variants"][condition]["payload"]
                )
                from polyglot_core import digest

                require(
                    row["payload_sha256"] == digest(payload), "Full payload changed"
                )
                require(
                    row["gold"] == payload["gold_index"]
                    and len(row["scores"]) == len(payload["choices"]),
                    "Gold/candidates differ",
                )
                pred = max(range(len(row["scores"])), key=row["scores"].__getitem__)
                require(
                    pred == row["prediction"]
                    and row["metrics"]["acc"] == int(pred == row["gold"]),
                    "Full metric differs",
                )
            results[condition] = {r["source_key"]: r for r in rows}
            summary = {
                "model": model,
                "condition": condition,
                "backend": "transformers",
                "weight_dtype": "bfloat16",
                **metric(rows),
                "acc_norm": sum(r["metrics"]["acc_norm"] for r in rows) / len(rows)
                if all("acc_norm" in r["metrics"] for r in rows)
                else None,
                "input_and_scoring_audit_passed": True,
                "result_sha256": file_hash(path),
            }
            summaries.append(summary)
            strata = {
                name: metric([r for r in rows if predicate(r)])
                for name, predicate in (
                    ("four_choice", lambda r: r["num_choices"] == 4),
                    ("five_choice", lambda r: r["num_choices"] == 5),
                    ("gold_e", lambda r: r["gold"] == 4),
                )
            }
            require(
                [strata[s]["items"] for s in ("four_choice", "five_choice", "gold_e")]
                == [1739, 256, 49],
                "Wrong strata counts",
            )
            aggregates = {}
            for basis in ("source", "native"):
                groups = collections.defaultdict(list)
                for row in rows:
                    category = (
                        row["category"]
                        if basis == "source" or condition in CONDITIONS[:2]
                        else matrix[row["source_key"]]["variants"][condition][
                            "native_category"
                        ]
                    )
                    groups[category].append(row)
                require(len(groups) == 11, "Missing categories")
                for category, group in sorted(groups.items()):
                    categories.append(
                        {
                            "model": model,
                            "condition": condition,
                            "basis": basis,
                            "category": category,
                            **metric(group),
                        }
                    )
                aggregates[basis] = {
                    "category_macro": sum(
                        metric(group)["acc"] for group in groups.values()
                    )
                    / 11
                }
                for name, included in (
                    ("culture_micro", CULTURE),
                    ("language_micro", set(groups) - CULTURE),
                ):
                    aggregates[basis][name] = metric(
                        [
                            r
                            for category, group in groups.items()
                            if category in included
                            for r in group
                        ]
                    )
            audit = {
                "logits_dtypes": dict(
                    collections.Counter(
                        r["forward_audit"]["logits_dtype"] for r in rows
                    )
                ),
                "sum_dtypes": dict(
                    collections.Counter(r["forward_audit"]["sum_dtype"] for r in rows)
                ),
                "max_native_batch_rows": max(
                    b[0] for r in rows for b in r["forward_audit"]["batches"]
                ),
                "max_native_sequence_length": max(
                    b[1] for r in rows for b in r["forward_audit"]["batches"]
                ),
            }
            write(
                output / "reports" / f"{model}-{condition}.json",
                {**summary, "strata": strata, "aggregates": aggregates, "audit": audit},
            )
            text = f"# {model} · {condition}\n\nTransformers / BF16 · 0-shot · 단일 지시문 · 원본 보기 순서\n\n정답 **{summary['correct']}/1995**, acc **{summary['acc']:.6f}**. 입력·채점 감사 PASS.\n\n"
            text += "| 구분 | 문항 | 정답 | acc |\n|---|---:|---:|---:|\n"
            for name, value in strata.items():
                text += f"| {name} | {value['items']} | {value['correct']} | {value['acc']:.6f} |\n"
            text += "\n| 분야 집계 기준 | 문화 micro | 언어 micro | 11분야 macro |\n|---|---:|---:|---:|\n"
            for basis, value in aggregates.items():
                text += f"| {basis} | {value['culture_micro']['acc']:.6f} | {value['language_micro']['acc']:.6f} | {value['category_macro']:.6f} |\n"
            (output / "reports" / f"{model}-{condition}.md").write_text(text)
        four = [k for k, r in original.items() if len(r["raw"]["choices"]) == 4]
        checks.extend(
            {"model": model, **c}
            for c in comparisons(folder, "full", sorted(original), sorted(four))
        )
        for left, right in (
            ("base_letter", "pr4420_letter"),
            ("base_full", "pr4420_full"),
            ("base_letter", "base_full"),
            ("pr4420_letter", "pr4420_full"),
        ):
            for stratum in ("all", "four_choice", "five_choice", "gold_e"):
                pairs = [(results[left][k], results[right][k]) for k in original]
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
    parity = all(c["prediction_parity"] for c in checks)
    write(
        output / "results.json",
        {
            "complete": True,
            "input_and_scoring_audit_passed": True,
            "prediction_parity": parity,
            "results": summaries,
            "comparisons": checks,
            "effects": effects,
        },
    )
    write(
        output / "provenance.json",
        {
            "protocol": protocol,
            "packages_sha256": file_hash(ROOT / "environment/packages.txt"),
            "models": {
                m: read(ROOT / "environment" / f"model-{m}.json") for m in MODELS
            },
        },
    )
    for filename, rows in (
        ("results.csv", summaries),
        ("categories.csv", categories),
        ("comparisons.csv", checks),
        ("effects.csv", effects),
    ):
        with (output / filename).open("w") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    text = "# CLIcK Qwen3.8 · Kanana2 Transformers BF16 결과\n\n12개 전체 평가 완료. 입력·채점 감사 PASS. 프레임워크 간 예측 일치 여부는 아래 비교표에 별도 표시한다.\n\n"
    text += "| 모델 | 조건 | 정답/문항 | acc | acc_norm |\n|---|---|---:|---:|---:|\n"
    for r in summaries:
        norm = f"{r['acc_norm']:.6f}" if r["acc_norm"] is not None else "—"
        text += f"| {r['model']} | {r['condition']} | {r['correct']}/{r['items']} | {r['acc']:.6f} | {norm} |\n"
    text += (
        "\n| 모델 | 비교 | 같은 예측/문항 | 최대 logprob 차이 |\n|---|---|---:|---:|\n"
    )
    for c in checks:
        text += f"| {c['model']} | {c['comparison']} | {c['same_prediction']}/{c['items']} | {c['max_abs_logprob_diff']:.8g} |\n"
    text += "\n공식 어댑터의 배치·padding·log_softmax·합산을 유지했다. BF16 수치 차이를 일치한 것으로 처리하지 않았다. 입력 정렬 harness와 native pr4420_full은 다른 조건이다. 과거 Polyglot은 Transformers/FP32이므로 정밀도까지 동일한 비교는 아니다. 논문의 지시문 3종 × 보기 순환 평균을 재현한 결과도 아니다.\n"
    (output / "README.md").write_text(text)
    print("All 23,940 native outputs verified; aggregate reports written", flush=True)


if __name__ == "__main__":
    main()
