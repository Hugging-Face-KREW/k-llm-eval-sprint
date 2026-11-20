"""Regression tests for scientific validity and restart/report integrity."""

import copy
import json

import pytest
from polyglot_core import (
    append_result,
    comparison,
    digest,
    establish_tolerance,
    harness_payload,
    load_results,
    token_contract,
    validate_result,
)


@pytest.fixture
def raw():
    return {
        "id": "not-CSAT",
        "paragraph": "",
        "question": "질문?",
        "choices": ["가", "나", "다", "라", "마"],
        "answer": "마",
    }


def test_manual_five_option_snapshot(raw):
    payload = harness_payload(raw)
    assert payload == {
        "query": "주어진 질문을 천천히 읽고, 적절한 정답을 A, B, C, D, E 중에 골라 알파벳 하나로 답하시오.\n\n질문: 질문?\n보기:\nA: 가, B: 나, C: 다, D: 라, E: 마\n정답:",
        "choices": [" A. 가", " B. 나", " C. 다", " D. 라", " E. 마"],
        "gold_index": 4,
    }


@pytest.mark.parametrize("count", [4, 5])
@pytest.mark.parametrize("paragraph", ["", " \n", "가가\n 지문 "])
def test_native_and_independent_serializer_agree(raw, count, paragraph):
    from lighteval.tasks.tasks.click import build_click_payload

    raw.update(
        choices=raw["choices"][:count],
        answer=raw["choices"][count - 1],
        paragraph=paragraph,
    )
    assert harness_payload(raw) == build_click_payload(raw)


def result(key="one", scores=None, category="society", gold=0):
    scores = scores or [-1.0, -2.0, -3.0, -4.0]
    pred = max(range(len(scores)), key=lambda i: scores[i])
    return {
        "source_key": key,
        "category": category,
        "raw_row_sha256": key,
        "payload_sha256": key,
        "tokens_sha256": key,
        "gold_index": gold,
        "scores": scores,
        "prediction": pred,
        "correct": int(pred == gold),
        "input_verified": True,
        "truncated": 0,
    }


def test_equal_aggregate_accuracy_does_not_hide_prediction_disagreement():
    left = {"a": result("a"), "b": result("b", gold=1)}
    right = {
        "a": result("a", scores=[-2, -1, -3, -4]),
        "b": result("b", scores=[-2, -1, -3, -4], gold=1),
    }
    report = comparison(left, right, 0.001)
    assert report["status"] == "FAIL"
    assert len(report["mismatches"]) == 2
    assert (
        report["aggregates"]["all_micro"]["lighteval_accuracy"]
        == report["aggregates"]["all_micro"]["harness_accuracy"]
    )


def test_weighted_micro_and_category_macro_are_distinct():
    rows = {
        "a": result("a"),
        "b": result("b"),
        "c": result("c", category="grammar", gold=1),
    }
    report = comparison(rows, rows, 1e-6)
    assert report["aggregates"]["all_micro"]["lighteval_accuracy"] == pytest.approx(
        2 / 3
    )
    assert report["aggregates"]["category_macro"]["lighteval_accuracy"] == 0.5


@pytest.mark.parametrize(
    "change",
    [
        {"scores": [float("nan"), 0, 0, 0]},
        {"scores": [-1]},
        {"prediction": 2},
        {"correct": 0},
        {"input_verified": False},
        {"truncated": 1},
        {"gold_index": 1},
    ],
)
def test_invalid_or_unverified_result_is_rejected(change):
    row = result()
    expected = {**row, "num_choices": 4}
    row.update(change)
    with pytest.raises(ValueError):
        validate_result(row, expected)


def test_tie_picks_first_option():
    row = result(scores=[-1, -1, -3, -4])
    validate_result(row, {**row, "num_choices": 4})
    assert row["prediction"] == 0


def test_resume_rejects_duplicate_and_partial_json(tmp_path):
    path = tmp_path / "rows.jsonl"
    row = result()
    expected = {"one": {**row, "num_choices": 4}}
    append_result(path, row)
    assert load_results(path, expected) == {"one": row}
    append_result(path, row)
    with pytest.raises(ValueError, match="duplicate"):
        load_results(path, expected)
    path.write_text('{"source_key":')
    with pytest.raises(json.JSONDecodeError):
        load_results(path, expected)


def test_incomplete_item_sets_are_rejected():
    with pytest.raises(ValueError):
        comparison({"a": result("a")}, {}, 1e-6)


def test_validation_cannot_inflate_calibrated_tolerance():
    samples = {"calibration": ["a"], "validation": ["b"]}
    rows = {"a": result("a"), "b": result("b")}
    engines = {
        name: copy.deepcopy(rows) for name in ("lighteval", "harness", "reference")
    }
    engines["harness"]["a"]["scores"][0] += 0.001
    engines["harness"]["b"]["scores"][0] += 0.05
    tolerance = establish_tolerance(engines, samples)
    assert tolerance["atol"] == pytest.approx(0.002)
    assert tolerance["status"] == "FAIL"
    del engines["reference"]["b"]
    with pytest.raises(ValueError, match="Incomplete"):
        establish_tolerance(engines, samples)


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        assert not add_special_tokens
        return [ord(c) for c in text]


def test_context_overflow_stops_before_scoring():
    with pytest.raises(ValueError, match="BLOCKED_CONTEXT"):
        token_contract(CharacterTokenizer(), {"query": "a" * 2047, "choices": [" bc"]})


def test_tokenization_boundary_mismatch_stops():
    class BadTokenizer(CharacterTokenizer):
        def encode(self, text, add_special_tokens=False):
            return [1] if text == "ab" else super().encode(text, add_special_tokens)

    with pytest.raises(ValueError, match="boundary"):
        token_contract(BadTokenizer(), {"query": "a", "choices": ["b"]})


def test_actual_input_audit_rejects_truncation_and_requires_all_choices():
    import torch
    from polyglot_backends import InputAudit

    audit = InputAudit(
        {"context": [1, 2], "continuations": [[3, 4], [5]]}, 0, omit_last=False
    )
    audit(None, (), {"input_ids": torch.tensor([[1, 2, 3, 4]])})
    with pytest.raises(ValueError, match="every continuation"):
        audit.complete()
    with pytest.raises(ValueError, match="Actual model input"):
        audit(None, (), {"input_ids": torch.tensor([[2, 5]])})
    audit(None, (), {"input_ids": torch.tensor([[1, 2, 5, 0]])})
    audit.complete()


def test_digest_is_order_independent_but_preserves_unicode_and_spaces():
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})
    assert digest("가") != digest("가") != digest(" 가")
