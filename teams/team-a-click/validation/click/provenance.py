"""Join source rows, HF-loaded rows and saved Lighteval details without ID deduplication."""

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from lighteval.tasks.tasks.click import CATEGORY_FILES, HF_REVISION, build_click_payload, click_prompt, raw_row_sha256


@dataclass(frozen=True)
class SourceRow:
    category: str
    path: str
    row_number: int
    raw: dict

    @property
    def key(self):
        return f"{HF_REVISION}:{self.path}#{self.row_number}"

    def metadata(self):
        return {
            "source_key": self.key,
            "category": self.category,
            "path": self.path,
            "row_number": self.row_number,
            "original_id": self.raw["id"],
            "raw_row_sha256": raw_row_sha256(self.raw),
        }


def inventory(snapshot: Path):
    """Read original arrays in file order; return metadata only plus in-memory rows."""
    expected = {path for files in CATEGORY_FILES.values() for path in files}
    actual = {p.relative_to(snapshot).as_posix() for p in (snapshot / "Dataset").rglob("*.json")}
    if actual != expected:
        raise ValueError(
            f"Source file set mismatch: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )
    files, sources = [], []
    for category, paths in CATEGORY_FILES.items():
        for path in paths:
            data = (snapshot / path).read_bytes()
            rows = json.loads(data)
            if not isinstance(rows, list):
                raise ValueError(f"Source is not an array: {path}")
            for row_number, row in enumerate(rows):
                build_click_payload(row)  # Fail at the source; do not skip invalid rows.
                sources.append(SourceRow(category, path, row_number, row))
            files.append(
                {"category": category, "path": path, "sha256": hashlib.sha256(data).hexdigest(), "rows": len(rows)}
            )
    return {"revision": HF_REVISION, "files": files, "rows": [source.metadata() for source in sources]}, sources


class AmbiguousSourceError(ValueError):
    pass


class SourceIndex:
    def __init__(self, sources):
        self.by_key = {}
        self.by_digest = defaultdict(list)
        for source in sources:
            if source.key in self.by_key:
                raise ValueError("Duplicate source key")
            self.by_key[source.key] = source
            self.by_digest[(source.category, raw_row_sha256(source.raw))].append(source)

    def resolve(self, category, specific):
        candidates = self.by_digest.get((category, specific.get("raw_row_sha256")), [])
        if "source_key" in specific:
            candidates = [source for source in candidates if source.key == specific["source_key"]]
        if not candidates:
            raise ValueError("No matching source row in this category/revision")
        if len(candidates) != 1:
            raise AmbiguousSourceError("Hash is ambiguous; load per file and attach source_key before formatting")
        source = candidates[0]
        if source.raw["id"] != specific.get("original_id"):
            raise ValueError("Original ID disagrees with source")
        return source

    def validate_documents(self, category, documents):
        """Check content, category and occurrence counts, including after Parquet round trips."""
        keys = []
        for doc in documents:
            if doc["task_name"].split("|")[0] != f"click:{category}":
                raise ValueError("Document task/category mismatch")
            source = self.resolve(category, doc["specific"])
            expected = build_click_payload(source.raw)
            if any(doc[field] != value for field, value in expected.items()):
                raise ValueError("Document content/gold disagrees with source")
            keys.append(source.key)
        expected_keys = [source.key for source in self.by_key.values() if source.category == category]
        if Counter(keys) != Counter(expected_keys):
            raise ValueError("Source/document occurrence mismatch: missing, repeated or extra rows")
        return keys


def file_documents(sources):
    """Fallback for identical raw rows: provenance is attached while file position is known.

    Use this on SourceRow objects made directly from per-file loading, never by
    guessing source positions from the order of a combined/shuffled dataset.
    """
    docs = []
    for source in sources:
        doc = click_prompt(source.raw, f"click:{source.category}")
        doc.specific["source_key"] = source.key
        docs.append(doc)
    return docs
