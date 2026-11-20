"""Regression evidence for native semantics, target adaptation, and experiment gates."""

import copy
import json
import os
from collections import Counter
from pathlib import Path

import pytest
from polyglot_core import append_result, canonical
from polyglot_matrix_core import (
    CONDITIONS,
    candidate_diagnostics,
    load_matrix_results,
    native_gold,
    original_records,
    paired_delta,
    pilot_gate,
    validate_matrix_result,
)
from polyglot_matrix_native import (
    NativeTasks,
    full_choices,
    requests_payload,
    task_snapshots,
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


@pytest.fixture(scope="module")
def native(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("matrix-native")
    harness = Path(
        os.environ.get(
            "MATRIX_TEST_HARNESS", str(REPO / ".polyglot/sources/lm-evaluation-harness")
        )
    )
    old = Path(os.environ.get("MATRIX_TEST_OLD", str(REPO / ".polyglot/results")))
    _, rows = original_records(old, HERE / "manifest.json")
    roots, state = task_snapshots(harness, tmp / "snapshots")
    transport = tmp / "raw.jsonl"
    transport.write_text("".join(canonical(r["raw"]) + "\n" for r in rows))
    return NativeTasks(roots, rows, transport), rows, state


def test_exact_core_and_native_loader_coverage(native):
    tasks, rows, state = native
    assert state["core_identical"] and len(state["changed_files"]) == 8
    for condition in CONDITIONS:
        assert set(tasks.rows[condition]) == {r["source_key"] for r in rows}
        assert len(tasks.rows[condition]) == 1995
    assert not tasks.diagnostics


def test_native_category_diff_and_duplicate_ids_preserved(native):
    tasks, rows, _ = native
    native_counts = Counter(
        v["native_category"] for v in tasks.rows["base_letter"].values()
    )
    source_counts = Counter(r["category"] for r in rows)
    assert (native_counts["grammar"], native_counts["functional"]) == (233, 132)
    assert (source_counts["grammar"], source_counts["functional"]) == (232, 133)
    duplicate_ids = {
        k for k, n in Counter(r["original_id"] for r in rows).items() if n > 1
    }
    assert duplicate_ids
    selected = [r for r in rows if r["original_id"] in duplicate_ids]
    assert len({r["source_key"] for r in selected}) == len(selected)


@pytest.mark.parametrize("condition", CONDITIONS)
def test_every_row_native_requests_target_and_delimiter(native, condition):
    tasks, rows, _ = native
    for row in rows:
        value = tasks.rows[condition][row["source_key"]]
        task = tasks.tasks[condition][value["native_category"]]
        assert value["native_task"] == task.config.task
        requests, payload = requests_payload(task, row["raw"])
        assert payload == value["payload"]
        assert payload["gold_index"] == row["raw"]["choices"].index(
            row["raw"]["answer"]
        )
        assert all(
            r.args[1].startswith(" ") and not r.args[1].startswith("  ")
            for r in requests
        )
        if condition.endswith("_letter"):
            assert [r.args[1] for r in requests] == [
                " " + label for label in value["native_labels"]
            ]
            assert task.doc_to_target(row["raw"]) == value["native_target"]
        else:
            assert task.doc_to_target(row["raw"]) == payload["gold_index"]
            assert [r.args[1] for r in requests] == [
                f" {label}. {option}"
                for label, option in zip(
                    value["native_labels"], row["raw"]["choices"], strict=True
                )
            ]


@pytest.mark.parametrize("paragraph", ["", "본문", " \n"])
@pytest.mark.parametrize("count", [4, 5])
def test_prompt_E_bug_first_A_spacing_and_goldE(native, paragraph, count):
    tasks, _, _ = native
    raw = {
        "id": "CSAT_sample" if count == 5 else "sample",
        "paragraph": paragraph,
        "question": "질문?",
        "choices": list("가나다라마"[:count]),
        "answer": "마" if count == 5 else "라",
    }
    contexts = {}
    for condition in CONDITIONS:
        task = tasks.tasks[condition]["society"]
        _, payload = requests_payload(task, raw)
        contexts[condition] = payload["query"]
        assert "A:가, B: 나, C: 다, D: 라" in payload["query"]
        assert "A: 가" not in payload["query"]
        assert len(payload["choices"]) == count
        assert payload["gold_index"] == count - 1
        scores = [(-2.0, False)] * count
        scores[-1] = (-0.01, True)
        assert task.process_results(raw, scores) == {"acc": 1.0, "acc_norm": 1.0}
    assert ("E: 마" in contexts["pr4420_letter"]) == (count == 5)
    assert "E: 마" not in contexts["base_letter"]
    if count == 4:
        assert len(set(contexts.values())) == 1


def test_candidate_mismatch_is_diagnostic_not_repaired():
    raw = {"id": "CSAT_four", "choices": ["a", "b", "c", "d"]}
    labels = lambda _: list("ABCDE")
    assert candidate_diagnostics(raw, labels(raw), "base")[0]["native_candidates"] == 5
    with pytest.raises(ValueError, match="candidate mismatch"):
        full_choices(labels, raw)
    with pytest.raises(ValueError, match="target missing"):
        native_gold(list("ABCD"), "E")


def result(key="one", gold=0):
    return {
        "source_key": key,
        "category": "society",
        "native_category": "society",
        "native_task": "click_cul_society",
        "source_category": "society",
        "condition": "base_full",
        "raw_row_sha256": key,
        "payload_sha256": key,
        "tokens_sha256": key,
        "config_sha256": key,
        "gold_index": gold,
        "num_choices": 4,
        "choice_char_lengths": [2, 4, 2, 2],
        "scores": [-1.0, -1.5, -3.0, -4.0],
        "prediction": 0,
        "correct": int(gold == 0),
        "prediction_norm": 1,
        "acc_norm": int(gold == 1),
        "input_verified": True,
        "truncated": 0,
    }


@pytest.mark.parametrize(
    "change",
    [
        {"acc_norm": 1},
        {"native_category": "grammar"},
        {"scores": [float("nan")] * 4},
        {"prediction_norm": 0},
        {"condition": "pr4420_full"},
    ],
)
def test_invalid_matrix_result_rejected(change):
    expected = result()
    changed = {**expected, **change}
    with pytest.raises(ValueError):
        validate_matrix_result(changed, expected)


def test_resume_rejects_partial_duplicate_and_changed_payload(tmp_path):
    path, row = tmp_path / "rows.jsonl", result()
    append_result(path, row)
    assert len(load_matrix_results(path, {"one": row})) == 1
    with pytest.raises(ValueError, match="payload"):
        load_matrix_results(path, {"one": {**row, "payload_sha256": "changed"}})
    append_result(path, row)
    with pytest.raises(ValueError, match="duplicate"):
        load_matrix_results(path, {"one": row})
    path.write_text('{"source_key":')
    with pytest.raises(json.JSONDecodeError):
        load_matrix_results(path, {"one": row})


def test_frozen_tolerance_validation_cannot_expand():
    a = {"cal": result("cal"), "val": result("val")}
    b = copy.deepcopy(a)
    b["cal"]["scores"][0] += 0.001
    b["val"]["scores"][0] += 0.01
    gate = pilot_gate(a, b, {"calibration": ["cal"], "validation": ["val"]})
    assert gate["status"] == "FAIL" and gate["atol"] == pytest.approx(0.002)
    with pytest.raises(ValueError, match="Incomplete"):
        pilot_gate(
            a, {"cal": b["cal"]}, {"calibration": ["cal"], "validation": ["val"]}
        )


def test_scientific_condition_changes_are_measured_not_gated():
    left = {"a": result("a"), "b": result("b", gold=1)}
    right = copy.deepcopy(left)
    for row in right.values():
        row.update(prediction=1, correct=int(row["gold_index"] == 1))
    delta = paired_delta(left, right)
    assert delta["prediction_switches"] == 2
    assert delta["wrong_to_correct"] == delta["correct_to_wrong"] == 1
    assert delta["acc_delta_percentage_points"] == 0
