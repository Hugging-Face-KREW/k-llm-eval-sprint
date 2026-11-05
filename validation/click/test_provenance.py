"""Offline synthetic tests for D03 failure detection and the ambiguous-hash fallback."""

import copy
import hashlib
import json
from dataclasses import asdict

import pytest

from lighteval.tasks.tasks.click import click_prompt

from . import provenance
from .provenance import AmbiguousSourceError, SourceIndex, SourceRow, file_documents, inventory


@pytest.fixture
def sources():
    raw = {
        "id": "duplicate-id",
        "paragraph": "",
        "question": "합성 질문?",
        "choices": ["가", "나", "다", "라"],
        "answer": "다",
    }
    return [
        SourceRow("functional", "synthetic.json", 0, raw),
        SourceRow("functional", "synthetic.json", 1, {**raw, "question": "다른 합성 질문?"}),
    ]


def docs_for(sources):
    return [asdict(click_prompt(s.raw, f"click:{s.category}")) for s in sources]


def test_duplicate_ids_are_two_rows_even_when_log_order_changes(sources):
    index = SourceIndex(sources)
    docs = docs_for(sources)
    assert index.validate_documents("functional", docs[::-1]) == [s.key for s in sources[::-1]]


@pytest.mark.parametrize("operation", ["missing", "duplicate", "replace", "empty"])
def test_occurrence_mismatches_are_errors(sources, operation):
    docs = docs_for(sources)
    bad = {"missing": docs[:1], "duplicate": docs + docs[:1], "replace": [docs[0], docs[0]], "empty": []}[operation]
    with pytest.raises(ValueError, match="occurrence"):
        SourceIndex(sources).validate_documents("functional", bad)


@pytest.mark.parametrize(
    "field,value",
    [
        ("query", "different"),
        ("choices", [" A. 다른 보기"]),
        ("gold_index", 0),
        ("task_name", "click:grammar"),
    ],
)
def test_log_content_corruption_is_detected(sources, field, value):
    docs = docs_for(sources)
    docs[0][field] = value
    with pytest.raises(ValueError):
        SourceIndex(sources).validate_documents("functional", docs)


@pytest.mark.parametrize(
    "field,value",
    [
        ("original_id", "wrong-id"),
        ("raw_row_sha256", "0" * 64),
        ("source_key", "wrong-revision:synthetic.json#0"),
    ],
)
def test_trace_metadata_corruption_is_detected(sources, field, value):
    docs = docs_for(sources)
    docs[0]["specific"][field] = value
    with pytest.raises(ValueError):
        SourceIndex(sources).validate_documents("functional", docs)


def test_missing_trace_hash_is_detected(sources):
    docs = docs_for(sources)
    del docs[0]["specific"]["raw_row_sha256"]
    with pytest.raises(ValueError, match="No matching"):
        SourceIndex(sources).validate_documents("functional", docs)


def test_hash_lookup_is_scoped_by_category(sources):
    other = SourceRow("grammar", "grammar.json", 0, sources[0].raw)
    index = SourceIndex(sources + [other])
    doc = docs_for([other])[0]
    assert index.validate_documents("grammar", [doc]) == [other.key]
    with pytest.raises(ValueError, match="category"):
        index.validate_documents("functional", [doc])


def test_ambiguous_hash_requires_file_position_and_preserves_both_rows(sources):
    same = SourceRow("functional", "another-file.json", 0, copy.deepcopy(sources[0].raw))
    rows = [sources[0], same]
    index = SourceIndex(rows)
    with pytest.raises(AmbiguousSourceError, match="per file"):
        index.validate_documents("functional", docs_for(rows))
    # Provenance was attached at per-file loading, not guessed after concatenation.
    docs = [asdict(d) for d in file_documents(rows)]
    assert docs[0]["query"] == docs[1]["query"]
    assert index.validate_documents("functional", docs[::-1]) == [same.key, sources[0].key]
    docs[1]["specific"]["source_key"] = docs[0]["specific"]["source_key"]
    with pytest.raises(ValueError, match="occurrence"):
        index.validate_documents("functional", docs)


def test_ambiguous_rows_within_same_file_use_row_number(sources):
    rows = [sources[0], SourceRow("functional", "synthetic.json", 1, sources[0].raw)]
    docs = [asdict(d) for d in file_documents(rows)]
    assert SourceIndex(rows).validate_documents("functional", docs) == [s.key for s in rows]


def test_duplicate_source_keys_are_an_error(sources):
    with pytest.raises(ValueError, match="Duplicate source key"):
        SourceIndex([sources[0], sources[0]])


def test_inventory_preserves_order_and_contains_no_source_text(tmp_path, monkeypatch, sources):
    path = "Dataset/Language/Functional/synthetic.json"
    monkeypatch.setattr(provenance, "CATEGORY_FILES", {"functional": (path,)})
    file = tmp_path / path
    file.parent.mkdir(parents=True)
    raw = json.dumps([s.raw for s in sources], ensure_ascii=False).encode()
    file.write_bytes(raw)
    manifest, result = inventory(tmp_path)
    assert [s.raw for s in result] == [s.raw for s in sources]
    assert [s.row_number for s in result] == [0, 1]
    assert manifest["files"][0]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["files"][0]["rows"] == 2
    assert set(manifest["rows"][0]) == {
        "source_key",
        "category",
        "path",
        "row_number",
        "original_id",
        "raw_row_sha256",
    }
    assert "합성 질문" not in json.dumps(manifest, ensure_ascii=False)
    file.write_text("[]")
    changed, _ = inventory(tmp_path)
    assert changed != manifest


@pytest.mark.parametrize("extra", [False, True])
def test_inventory_rejects_missing_or_extra_files(tmp_path, monkeypatch, extra):
    path = "Dataset/Language/Functional/synthetic.json"
    monkeypatch.setattr(provenance, "CATEGORY_FILES", {"functional": (path,)})
    if extra:
        file = tmp_path / "Dataset/extra.json"
        file.parent.mkdir(parents=True)
        file.write_text("[]")
    with pytest.raises(ValueError, match="file set mismatch"):
        inventory(tmp_path)
