"""Explicit D01-D03 integration check. Run with python -m validation.click.validate."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import tempfile
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from lighteval.tasks.tasks import click
from lighteval.tasks.tasks.click import CATEGORY_FILES, HF_REPO, HF_REVISION, PROMPT_VERSION, click_prompt

from .provenance import SourceIndex, SourceRow, file_documents, inventory


# (rows, five-option rows, nonblank paragraphs), copied from design.md §2.
EXPECTED = {
    "society": (309, 0, 0),
    "tradition": (222, 0, 0),
    "history": (280, 0, 0),
    "law": (219, 0, 0),
    "politics": (84, 0, 0),
    "economy": (59, 0, 0),
    "geography": (131, 30, 0),
    "popular": (41, 0, 0),
    "textual": (285, 68, 238),
    "functional": (133, 112, 106),
    "grammar": (232, 46, 9),
}


def require(condition, message):
    # These checks must still run under python -O.
    if not condition:
        raise ValueError(message)


def check_counts(sources):
    categories = {}
    for category, expected in EXPECTED.items():
        rows = [s.raw for s in sources if s.category == category]
        actual = (
            len(rows),
            sum(len(r["choices"]) == 5 for r in rows),
            sum(bool(r["paragraph"].strip()) for r in rows),
        )
        require(actual == expected, f"D01 category counts mismatch: {category}: {actual}")
        categories[category] = dict(zip(("rows", "five_options", "paragraphs"), actual))
    total = {
        "files": len({s.path for s in sources}),
        "rows": len(sources),
        "four_options": sum(len(s.raw["choices"]) == 4 for s in sources),
        "five_options": sum(len(s.raw["choices"]) == 5 for s in sources),
        "paragraphs": sum(bool(s.raw["paragraph"].strip()) for s in sources),
        "gold_e": sum(s.raw["choices"].index(s.raw["answer"]) == 4 for s in sources),
        "unique_ids": len({s.raw["id"] for s in sources}),
    }
    require(
        total
        == {
            "files": 26,
            "rows": 1995,
            "four_options": 1739,
            "five_options": 256,
            "paragraphs": 353,
            "gold_e": 49,
            "unique_ids": 1987,
        },
        "D01/D02 total mismatch",
    )
    special = [
        s for s in sources if s.path == "Dataset/Language/Functional/Functional_CSAT.json" and s.row_number == 82
    ]
    require(len(special) == 1 and special[0].category == "functional", "D02 Functional_CSAT#82 lost/misclassified")
    return categories, total, special[0].metadata()


def loaded_documents(category, snapshot, index, local_loader):
    from datasets import load_dataset

    def load(paths):
        if local_loader:
            return load_dataset("json", data_files={"train": [str(snapshot / p) for p in paths]}, split="train")
        return load_dataset(HF_REPO, "default", revision=HF_REVISION, data_files={"train": list(paths)}, split="train")

    # Check uniqueness before trying to join a combined loader result by content.
    ambiguous = any(c == category and len(rows) > 1 for (c, _), rows in index.by_digest.items())
    if ambiguous:
        sources = [
            SourceRow(category, path, i, row)
            for path in CATEGORY_FILES[category]
            for i, row in enumerate(load([path]))
        ]
        return file_documents(sources), "per-file-position"
    return [
        click_prompt(row, f"click:{category}") for row in load(CATEGORY_FILES[category])
    ], "category+raw-row-sha256"


def check_loader_and_log(snapshot, index, local_loader):
    from datasets import Dataset

    from lighteval.logging.evaluation_tracker import EvaluationTracker
    from lighteval.models.model_output import ModelResponse

    counts, datasets, modes = {}, {}, {}
    # Full text is written only to a temporary local directory, then removed.
    with tempfile.TemporaryDirectory(prefix="click-trace-") as directory:
        tracker = EvaluationTracker(output_dir=directory, push_to_hub=False)
        tracker.general_config_logger.model_name = "trace-only-no-model"
        for category in CATEGORY_FILES:
            docs, modes[category] = loaded_documents(category, snapshot, index, local_loader)
            original_keys = index.validate_documents(category, [asdict(doc) for doc in docs])
            expected_order = [s.key for s in index.by_key.values() if s.category == category]
            require(original_keys == expected_order, f"D03 loader changed file/array order: {category}")
            task = f"click:{category}"
            for doc in docs:
                # Empty model response; trace_check is a marker, not an evaluation score.
                tracker.details_logger.log(task, doc, ModelResponse(), {"trace_check": True})
            datasets[task] = Dataset.from_list([asdict(d) for d in tracker.details_logger.details[task]])
            counts[category] = {"loaded": len(docs), "linked": len(original_keys), "source_order_preserved": True}
        tracker.save_details("provenance", datasets)
        for category in CATEGORY_FILES:
            path = (
                Path(directory)
                / "details"
                / "trace-only-no-model"
                / "provenance"
                / f"details_click:{category}_provenance.parquet"
            )
            saved = Dataset.from_parquet(str(path))
            saved_keys = index.validate_documents(category, [detail["doc"] for detail in saved])
            counts[category]["saved_log_linked"] = len(saved_keys)
    return counts, modes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Local directory containing Dataset/; verified against manifest")
    parser.add_argument(
        "--local-loader", action="store_true", help="Use local JSON loader instead of the HF repo/config loader"
    )
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    parser.add_argument("--report", type=Path, required=True, help="Metadata-only JSON report output")
    args = parser.parse_args()
    if args.snapshot is None:
        from huggingface_hub import snapshot_download

        args.snapshot = Path(
            snapshot_download(
                repo_id=HF_REPO,
                repo_type="dataset",
                revision=HF_REVISION,
                allow_patterns=[p for paths in CATEGORY_FILES.values() for p in paths],
            )
        )
    manifest, sources = inventory(args.snapshot)
    require(manifest == json.loads(args.manifest.read_text()), "Source bytes/rows disagree with the pinned manifest")
    categories, totals, special = check_counts(sources)
    index = SourceIndex(sources)
    counts, modes = check_loader_and_log(args.snapshot, index, args.local_loader)
    module = Path(click.__file__)
    code_root = module.parents[4]
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": HF_REPO,
        "dataset_revision": HF_REVISION,
        "prompt_version": PROMPT_VERSION,
        "lighteval_base": "c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14",
        "lighteval_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=code_root, text=True).strip(),
        "click_module_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("datasets", "huggingface-hub", "pyarrow", "torch", "pytest")
        },
        "loader": "local-json" if args.local_loader else "HF-repo-default-config-pinned-revision",
        "D01": "PASS",
        "D02": "PASS",
        "D03": "PASS",
        "totals": totals,
        "categories": categories,
        "loader_to_saved_log": counts,
        "trace_modes": modes,
        "functional_csat_row_82": special,
        "duplicate_id_groups": sum(n > 1 for n in Counter(s.raw["id"] for s in sources).values()),
        "ambiguous_category_hash_groups": sum(len(rows) > 1 for rows in index.by_digest.values()),
        "model_evaluation": "NOT_RUN",
        "full_pipeline_registry_integration": "NOT_RUN",
        "log_check": "Real DetailsLogger and EvaluationTracker.save_details; empty ModelResponse; no accuracy measured",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"D01": "PASS", "D02": "PASS", "D03": "PASS", **totals}, ensure_ascii=False))


if __name__ == "__main__":
    main()
