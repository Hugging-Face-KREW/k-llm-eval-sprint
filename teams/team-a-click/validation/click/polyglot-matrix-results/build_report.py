"""Verify recovered private results before producing public aggregate-only reports."""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from polyglot_core import digest, file_digest, read_json, require, write_json
from polyglot_matrix import expected_rows
from polyglot_matrix_core import (
    CONDITIONS,
    condition_summary,
    load_matrix_results,
    paired_delta,
    pilot_gate,
    verify_four_choice_equivalence,
)


def kst(value):
    return datetime.fromisoformat(value).astimezone(ZoneInfo("Asia/Seoul")).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--old-results", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--retrieval", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    prepared = read_json(args.results / "prepared.json")
    execution = read_json(args.execution)
    require(
        execution["state"] == "COMPLETE" and execution["exit_code"] == 0,
        "Experiment not successfully finished",
    )
    retrieval = read_json(args.retrieval)
    require(retrieval["status"] == "PASS", "Retrieval SHA verification missing")
    require(
        prepared["inputs_sha256"] == file_digest(args.results / "inputs.jsonl"),
        "Input artifact changed",
    )
    rows = [
        json.loads(line)
        for line in (args.results / "inputs.jsonl").read_text().splitlines()
    ]
    require(
        len(rows) == len({r["source_key"] for r in rows}) == 1995,
        "Input rows incomplete",
    )
    smoke = read_json(args.results / "smoke.json")
    require(
        smoke["status"] == "PASS" and smoke["prepared_sha256"] == digest(prepared),
        "GPU smoke invalid",
    )
    pilot_keys = set(
        prepared["samples"]["calibration"] + prepared["samples"]["validation"]
    )
    models, references = {}, {}
    csv_rows = []
    for size in ("1.3b", "12.8b"):
        summary = read_json(args.results / size / "summary.json")
        require(summary["status"] == "PASS", "Model summary failed")
        protocol = read_json(args.results / size / "protocol.json")
        require(protocol["prepared_sha256"] == digest(prepared), "Stale model protocol")
        results = {}
        for condition in CONDITIONS:
            folder = args.results / size / condition
            expected = expected_rows(rows, size, condition)
            results[condition] = load_matrix_results(
                folder / "full-native.jsonl", expected
            )
            require(set(results[condition]) == set(expected), "Full results incomplete")
            expected_pilot = {k: v for k, v in expected.items() if k in pilot_keys}
            pilots = {
                engine: load_matrix_results(
                    folder / f"pilot-{engine}.jsonl", expected_pilot
                )
                for engine in ("native", "reference")
            }
            gate = pilot_gate(
                pilots["native"], pilots["reference"], prepared["samples"]
            )
            recorded = read_json(folder / "calibration.json")
            require(
                all(recorded[k] == value for k, value in gate.items()),
                "Recorded calibration does not reproduce",
            )
            require(
                gate["status"] == "PASS"
                and recorded["protocol_sha256"] == digest(protocol),
                "Invalid frozen gate",
            )
            for engine in pilots:
                require(
                    recorded[f"{engine}_sha256"]
                    == file_digest(folder / f"pilot-{engine}.jsonl"),
                    "Pilot checksum changed",
                )
            for stem, count in (
                ("pilot-native", len(pilot_keys)),
                ("pilot-reference", len(pilot_keys)),
                ("full-native", 1995),
            ):
                state = read_json(folder / f"{stem}-status.json")
                require(
                    state["status"] == "COMPLETE"
                    and state["completed"] == state["expected"] == count,
                    "Stage incomplete",
                )
                require(
                    state["output_sha256"] == file_digest(folder / f"{stem}.jsonl"),
                    "Stage checksum differs",
                )
            recomputed = condition_summary(results[condition])
            stored = summary["conditions"][condition]
            require(
                all(stored[k] == v for k, v in recomputed.items()), "Aggregate mismatch"
            )
            require(
                stored["result_sha256"] == file_digest(folder / "full-native.jsonl"),
                "Full checksum changed",
            )
            for basis in ("native_category", "source_category"):
                for category, values in stored[basis]["categories"].items():
                    csv_rows.append(
                        {
                            "model": size,
                            "condition": condition,
                            "basis": basis,
                            "category": category,
                            **{
                                k: values[k]
                                for k in (
                                    "items",
                                    "correct",
                                    "acc",
                                    "correct_norm",
                                    "acc_norm",
                                )
                            },
                            **{
                                f"pred_{k}": v
                                for k, v in values["prediction_counts"].items()
                            },
                        }
                    )
        verify_four_choice_equivalence(results)
        for a, b in (
            ("base_letter", "pr4420_letter"),
            ("base_full", "pr4420_full"),
            ("base_letter", "base_full"),
            ("pr4420_letter", "pr4420_full"),
        ):
            require(
                summary["paired_deltas"][f"{b}_minus_{a}"]["overall"]
                == paired_delta(results[a], results[b]),
                "Pair report mismatch",
            )
        summary["paired_category_deltas"] = {}
        for a, b in (
            ("base_letter", "pr4420_letter"),
            ("base_full", "pr4420_full"),
            ("base_letter", "base_full"),
            ("pr4420_letter", "pr4420_full"),
        ):
            summary["paired_category_deltas"][f"{b}_minus_{a}"] = {
                field: {
                    category: paired_delta(
                        {k: r for k, r in results[a].items() if r[field] == category},
                        {k: r for k, r in results[b].items() if r[field] == category},
                    )
                    for category in sorted({r[field] for r in results[a].values()})
                }
                for field in ("native_category", "source_category")
            }
        models[size] = summary
        old = read_json(args.old_results / size / "summary.json")
        require(
            old["status"] == "PASS" and not old["mismatches"],
            "Old reference not verified",
        )
        for filename, checksum in old["result_files"].items():
            require(
                file_digest(args.old_results / size / filename) == checksum,
                "Old raw reference changed",
            )
        references[size] = {
            "reused_run": True,
            "run_date": "2026-11-11",
            "summary_sha256": file_digest(args.old_results / size / "summary.json"),
            "prepared_sha256": old["protocol"]["prepared_sha256"],
            "settings": old["settings"],
            "overall": old["aggregates"]["all_micro"],
            "categories": old["categories"],
            "difference_from_matrix": "Lighteval-aligned first A: space and file-based category; do not substitute for pr4420_full",
        }
    args.output.mkdir(parents=True, exist_ok=True)
    paper = read_json(HERE.parent / "polyglot_paper_reference.json")
    combined = {
        "status": "PASS",
        "conditions": list(CONDITIONS),
        "models": models,
        "old_references": references,
        "paper_reference": paper,
        "settings": prepared["settings"],
        "sources": prepared["sources"],
        "preflight": prepared["preflight"],
        "code_sha256": prepared["code_sha256"],
        "samples": {k: len(v) for k, v in prepared["samples"].items()},
        "execution": execution,
        "start_kst": kst(execution["started_at"]),
        "end_kst": kst(execution["finished_at"]),
        "retrieval": retrieval,
        "report_generator_sha256": file_digest(Path(__file__)),
    }
    write_json(args.output / "summary.json", combined)
    with (args.output / "categories.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    paper = read_json(HERE.parent / "polyglot_paper_reference.json")
    lines = [
        "# CLIcK Polyglot 버전 × 채점 방식 결과",
        "",
        "상태: **8개 조합 PASS**. Native Python API 실험이며 전체 CLI 실행 동등성을 주장하지 않습니다.",
        "",
        f"실행: {combined['start_kst']} ~ {combined['end_kst']}, 종료 코드 0.",
        "",
        "`acc`는 후보의 합산 로그확률이 가장 큰 선택지를 고른 정답률입니다. `acc_norm`은 후보 문자열의 Unicode 문자 수(앞 target delimiter 제외)로 나눈 점수로 선택한 별도 보조 정답률입니다.",
        "",
        "full 조건은 원래 후보 개수·순서와 prompt/filter를 보존하고 `A` → `A. 보기 원문`으로 바꿉니다. 원래 정답 라벨을 원래 후보의 인덱스로 대응시켰습니다. 모든 조건은 첫 `A:` 뒤 공백을 추가하지 않습니다.",
        "",
        "| 모델 | 조건 | 정답/문항 | acc (%) | acc_norm (%) | E 예측 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for size, model in models.items():
        for c, value in model["conditions"].items():
            v = value["overall"]
            lines.append(
                f"| {size} | {c} | {v['correct']}/{v['items']} | {100 * v['acc']:.4f} | {100 * v['acc_norm']:.4f} | {v['prediction_counts']['E']} |"
            )
    if all(
        model["conditions"][f"{version}_full"]["overall"]["acc"]
        > model["conditions"][f"{version}_letter"]["overall"]["acc"]
        for model in models.values()
        for version in ("base", "pr4420")
    ):
        lines += [
            "",
            "이번 고정 지시문·원본 순서 실험에서는 두 모델과 두 revision 모두 full 채점의 전체 micro 정확도가 letter보다 높았습니다. 다만 아래 5지선다·정답 E 결과는 같은 방향으로 움직이지 않으므로 전체 점수 증가를 모든 문항 유형의 개선으로 해석할 수 없습니다.",
        ]
    lines += [
        "",
        "## 수정 효과와 채점 방식 효과",
        "",
        "서로 다른 조건의 예측 차이는 측정 대상입니다. 비교 이름의 `B_minus_A`는 B − A이며, 같은 평균도 문항별 변경을 숨기지 않습니다.",
        "",
        "| 모델 | 비교 | Δ acc (%p) | 예측 변경 | 오답→정답 | 정답→오답 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for size, model in models.items():
        for pair, values in model["paired_deltas"].items():
            v = values["overall"]
            lines.append(
                f"| {size} | {pair} | {v['acc_delta_percentage_points']:+.4f} | {v['prediction_switches']} | {v['wrong_to_correct']} | {v['correct_to_wrong']} |"
            )
    lines += [
        "",
        "## A–E 예측 분포",
        "",
        "주 지표 acc에 사용한 예측의 빈도이며 각 행의 합은 1,995입니다.",
        "",
        "| 모델 | 조건 | A | B | C | D | E |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for size, model in models.items():
        for condition, value in model["conditions"].items():
            counts = value["overall"]["prediction_counts"]
            require(sum(counts.values()) == 1995, "Prediction count denominator")
            lines.append(
                f"| {size} | {condition} | "
                + " | ".join(str(counts[label]) for label in "ABCDE")
                + " |"
            )
    lines += [
        "",
        "## 선택지 수와 정답 E",
        "",
        "| 모델 | 조건 | 4지선다 (1739) | 5지선다 (256) | 정답 E (49) |",
        "|---|---|---:|---:|---:|",
    ]
    for size, model in models.items():
        for c, v in model["conditions"].items():
            cells = [
                f"{v['strata'][s]['correct']}/{v['strata'][s]['items']} ({100 * v['strata'][s]['acc']:.2f}%)"
                for s in ("four_choice", "five_choice", "gold_E")
            ]
            lines.append(f"| {size} | {c} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## 분야별 집계",
        "",
        "아래 표의 수치는 acc(%)이며 n은 문항 수입니다. 분야별 정답 수와 acc_norm은 CSV 및 기계 요약에 함께 제공합니다.",
        "",
        "원본 파일 분야와 native ID 필터 분야를 분리합니다. `Functional_CSAT.json#82`(0부터 시작하는 행 인덱스)는 원본 Functional이지만 native Grammar에 들어가며, native Grammar/Functional은 233/132문항, 파일 기준은 232/133문항입니다.",
    ]
    for size, model in models.items():
        for basis in ("native_category", "source_category"):
            lines += [
                "",
                f"### {size} · {basis}",
                "",
                "| 분야 | n | base_letter | pr4420_letter | base_full | pr4420_full |",
                "|---|---:|---:|---:|---:|---:|",
            ]
            for category, v in model["conditions"]["base_letter"][basis][
                "categories"
            ].items():
                cells = [
                    f"{100 * model['conditions'][c][basis]['categories'][category]['acc']:.4f}"
                    for c in CONDITIONS
                ]
                lines.append(
                    f"| {category} | {v['items']} | " + " | ".join(cells) + " |"
                )
            for agg in ("culture", "language"):
                cells = [
                    f"{100 * model['conditions'][c][basis][agg]['acc']:.4f}"
                    for c in CONDITIONS
                ]
                lines.append(
                    f"| {agg} micro | {model['conditions']['base_letter'][basis][agg]['items']} | "
                    + " | ".join(cells)
                    + " |"
                )
            lines.append(
                "| 11분야 macro | 11분야 | "
                + " | ".join(
                    f"{100 * model['conditions'][c][basis]['macro_acc']:.4f}"
                    for c in CONDITIONS
                )
                + " |"
            )
    lines += [
        "",
        "## 이전 실행 참고값",
        "",
        "아래 두 열은 이번에 재실행한 값이 아니라 2026-11-11의 검증된 이전 실행을 재사용한 참고값입니다. 첫 A: 공백과 파일 기준 분류가 다르므로 새 pr4420_full과 동일하다고 가정하지 않습니다.",
        "",
        "| 모델 | 이전 Lighteval | 이전 정렬 harness |",
        "|---|---:|---:|",
    ]
    for size, reference in references.items():
        v = reference["overall"]
        lines.append(
            f"| {size} | {v['lighteval_correct']}/1995 ({100 * v['lighteval_accuracy']:.4f}%) | {v['harness_correct']}/1995 ({100 * v['harness_accuracy']:.4f}%) |"
        )
    lines += [
        "",
        "논문의 문화/언어 Average는 별도 참고값이며 이번 micro/macro와 산식이 같다고 가정하지 않습니다.",
        "",
        "| 모델 | 논문 문화 Average (%) | 논문 언어 Average (%) |",
        "|---|---:|---:|",
    ]
    for size, value in paper["models"].items():
        lines.append(
            f"| {size} | {value['reported_culture_average']:.2f} | {value['reported_language_average']:.2f} |"
        )
    lines += [
        "",
        f"논문 [Table 5]({paper['source']})는 지시문 3종과 보기 순환을 사용한 참고 자료입니다. 이번 단일 지시문·원본 순서 실험은 논문 재현이 아닙니다.",
        "",
        "4지선다 동일 payload의 두 revision 점수와 예측은 정확히 일치했습니다. 모든 조건의 파일럿은 조건 내부 native HFLM 대 독립 forward로 검증했고 허용오차를 검증 결과에 맞춰 늘리지 않았습니다.",
        "",
        "높은 점수만으로 버그 수정의 타당성, 모든 5지선다에서의 개선, 모델 일반 우열을 단정하지 않습니다. 원래 base는 프롬프트의 E를 누락하면서 CSAT 후보 E를 채점하며, base_full도 보이지 않는 E 원문을 채점합니다.",
        "",
        "[전체 기계 요약](summary.json)과 [두 분야 기준 CSV](categories.csv)에 A–E 예측 분포, acc_norm, 분모, strata별 paired delta, source/code/env fingerprint, 시작·종료 증빙과 회수 SHA가 있습니다. 원문·문항별 결과·토큰은 ignored private 경로에만 보관합니다.",
        "",
        "## 실행·검증 증빙",
        "",
        "설정은 FP32/eager/TF32 off, 후보별 batch 1, seed 1234, 최대 2,048토큰, 0-shot입니다. BOS/EOS·chat template·양자화·truncation·logits cache를 사용하지 않았습니다.",
        "",
        "고정된 원본 1,995행을 동일 필드의 private JSON train split으로 전달하는 transport override를 사용했습니다. 실제 native YAML 함수·ID 필터·delimiter·요청·metric 경로를 유지하고 네 조건 전 행의 loader coverage와 두 tokenizer 경계를 검증했습니다. 두 source revision의 차이는 CLIcK 하위 8개 파일뿐이며 core는 동일합니다.",
        "",
        "원격 고정 환경 테스트 141개 PASS, GPU random GPTNeoX 8문항 × 4조건 PASS. 각 모델·조건의 native/독립 파일럿은 calibration 55 + held-out 72문항이며 모두 PASS입니다. 전체 15,960행을 누락·중복 없이 검증했고 동일 4지선다 1,739행의 두 revision 점수·예측도 정확히 일치했습니다.",
        "",
        f"회수 파일 {retrieval['verified_file_count']}개의 원격/로컬 SHA256이 모두 일치합니다. 회수 archive SHA256: `{retrieval['archive_sha256']}`.",
        "",
        f"실행 코드 SHA256: `{prepared['code_sha256']}`. Source/model/data revision과 전체 환경 버전은 [기계 요약](summary.json), 설계와 시작·종료 이력은 [실험계획](../POLYGLOT_MATRIX.md)에 기록했습니다.",
        "",
        "실행 명령:",
        "",
        "```bash",
        " ".join(execution["command"]),
        "```",
        "",
        "컨테이너 `click-polyglot-eval-0e79adb4817a`, GPU `GPU-3695dff3-f973-9d01-4829-e3b3730748b6` 한 장만 사용했습니다. 로그는 `/workspace/logs/matrix-task_3ce01f897c7f/`, 원격 결과는 `/workspace/results-matrix`, 회수본은 로컬 `.polyglot/remote/results-matrix`입니다. 기존 평가 코드·결과와 사용자 PDF는 보존했습니다.",
    ]
    (args.output / "README.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "combinations": 8,
                "rows_each": 1995,
                "public_output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
