"""Native CLIcK version x candidate-scoring experiment; private output only."""

import argparse
import importlib.metadata
import json
import os
import traceback
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from polyglot_compare import environment, private_output
from polyglot_core import (
    MODELS,
    RAW_FIELDS,
    append_result,
    canonical,
    digest,
    file_digest,
    read_json,
    require,
    token_contract,
    write_json,
)
from polyglot_matrix_core import (
    CONDITIONS,
    SETTINGS,
    condition_summary,
    load_matrix_results,
    original_records,
    paired_delta,
    pilot_gate,
    validate_matrix_result,
    verify_four_choice_equivalence,
)
from polyglot_matrix_native import MatrixBackend, NativeTasks, task_snapshots

HERE = Path(__file__).resolve().parent
GPU_UUID = os.environ.get("POLYGLOT_GPU_UUID", "")


def now():
    return datetime.now(UTC).isoformat()


def code_fingerprint():
    paths = list(HERE.glob("polyglot_matrix*.py")) + [
        HERE / name
        for name in (
            "polyglot_core.py",
            "polyglot_backends.py",
            "polyglot_compare.py",
            "polyglot_matrix_run.sh",
        )
    ]
    return digest({p.name: file_digest(p) for p in sorted(paths)})


def setup(args):
    roots, sources = task_snapshots(
        args.harness_root.resolve(),
        args.task_snapshots.resolve(),
        args.revision_repository,
    )
    return roots, sources


def frozen(path, value):
    if path.exists():
        require(
            read_json(path) == value,
            f"Frozen artifact differs: {path}; use a clean experiment directory",
        )
    else:
        write_json(path, value)


def prepare(args):
    roots, sources = setup(args)
    output = private_output(args.output_dir)
    require(
        not (output / "prepared.json").exists(), "Already prepared; do not overwrite"
    )
    old, records = original_records(args.old_output, HERE / "manifest.json")
    transport = output / "transport.jsonl"
    with transport.open("x") as stream:
        for row in records:
            stream.write(canonical({k: row["raw"][k] for k in RAW_FIELDS}) + "\n")
    tasks = NativeTasks(roots, records, transport)
    from lm_eval.api.model import TemplateLM
    from lm_eval.models.huggingface import HFLM
    from transformers import AutoConfig, AutoTokenizer

    tokenizers = {}
    for size, (repo, revision) in MODELS.items():
        require(
            AutoConfig.from_pretrained(repo, revision=revision).max_position_embeddings
            == 2048,
            "Context size changed",
        )
        tokenizer = AutoTokenizer.from_pretrained(
            repo, revision=revision, trust_remote_code=False
        )
        proxy = SimpleNamespace(
            tokenizer=tokenizer,
            backend="causal",
            add_bos_token=False,
            prefix_token_id=tokenizer.eos_token_id,
        )
        proxy.tok_encode = lambda text, _proxy=proxy, **kwargs: HFLM.tok_encode(
            _proxy, text, **kwargs
        )
        tokenizers[size] = tokenizer, proxy
    maxima = {size: {condition: 0 for condition in CONDITIONS} for size in MODELS}
    rows = []
    for record in records:
        variants = {}
        for condition in CONDITIONS:
            variant = {
                **tasks.rows[condition][record["source_key"]],
                "condition": condition,
                "models": {},
            }
            payload = variant["payload"]
            variant.update(
                payload_sha256=digest(payload),
                gold_index=payload["gold_index"],
                num_choices=len(payload["choices"]),
            )
            for size, (tokenizer, proxy) in tokenizers.items():
                tokens = token_contract(tokenizer, payload)
                for continuation, expected in zip(
                    payload["choices"], tokens["continuations"], strict=True
                ):
                    ctx, suffix = TemplateLM._encode_pair(
                        proxy, payload["query"], continuation
                    )
                    require(
                        ctx == tokens["context"] and suffix == expected,
                        "Native tokenizer boundary differs",
                    )
                maximum = max(
                    len(tokens["context"]) + len(c) for c in tokens["continuations"]
                )
                variant["models"][size] = {
                    "tokens_sha256": digest(tokens),
                    "max_tokens": maximum,
                }
                maxima[size][condition] = max(maxima[size][condition], maximum)
            variants[condition] = variant
        rows.append({**record, "variants": variants})
    samples = {key: list(value) for key, value in old["samples"].items()}
    # Keep the original 55/69 and add any newly longest boundary BEFORE inference.
    additions = set()
    remaining = [r for r in rows if r["source_key"] not in samples["calibration"]]
    for size in MODELS:
        for condition in CONDITIONS:
            for category in sorted({r["category"] for r in rows}):
                group = [r for r in remaining if r["category"] == category]
                additions.add(
                    max(
                        group,
                        key=lambda r: r["variants"][condition]["models"][size][
                            "max_tokens"
                        ],
                    )["source_key"]
                )
    samples["validation"] = sorted(set(samples["validation"]) | additions)
    require(
        len(samples["calibration"]) == 55
        and not set(samples["calibration"]) & set(samples["validation"]),
        "Pilot split invalid",
    )
    inputs = output / "inputs.jsonl"
    with inputs.open("x") as stream:
        for row in rows:
            stream.write(canonical(row) + "\n")
    count4 = sum(len(r["raw"]["choices"]) == 4 for r in rows)
    count5 = sum(len(r["raw"]["choices"]) == 5 for r in rows)
    gold_e = sum(r["raw"]["choices"].index(r["raw"]["answer"]) == 4 for r in rows)
    require((count4, count5, gold_e) == (1739, 256, 49), "Unexpected strata")
    native_counts = {
        c: dict(Counter(v["native_category"] for v in tasks.rows[c].values()))
        for c in CONDITIONS
    }
    mismatches = [
        {
            "source_key": r["source_key"],
            "source_category": r["category"],
            "native_category": r["variants"]["base_letter"]["native_category"],
        }
        for r in rows
        if r["category"] != r["variants"]["base_letter"]["native_category"]
    ]
    prepared = {
        "schema_version": 1,
        "created_at": now(),
        "items": len(rows),
        "settings": SETTINGS,
        "code_sha256": code_fingerprint(),
        "sources": sources,
        "configs": tasks.configs,
        "dataset_revision": old["dataset_revision"],
        "manifest_sha256": file_digest(HERE / "manifest.json"),
        "old_prepared_sha256": digest(old),
        "old_inputs_sha256": old["inputs_sha256"],
        "inputs_sha256": file_digest(inputs),
        "transport_sha256": file_digest(transport),
        "transport_override": "JSON loader over the 1995 verified old raw records; identical fields/content; original native process_docs and requests preserved; no dataset logic/row deduplication",
        "samples": samples,
        "validation_additions": sorted(
            set(samples["validation"]) - set(old["samples"]["validation"])
        ),
        "models": {
            size: {"repo": p[0], "revision": p[1]} for size, p in MODELS.items()
        },
        "preflight": {
            "status": "PASS",
            "native_loader_coverage": {c: 1995 for c in CONDITIONS},
            "native_counts": native_counts,
            "source_counts": dict(Counter(r["category"] for r in rows)),
            "category_mismatches": mismatches,
            "candidate_diagnostics": tasks.diagnostics,
            "four_choice": count4,
            "five_choice": count5,
            "gold_E": gold_e,
            "max_tokens": maxima,
            "native_joint_separate_boundary_mismatches": 0,
        },
    }
    write_json(output / "prepared.json", prepared)
    print(
        canonical(
            {
                "event": "PREPARED",
                "items": len(rows),
                "samples": {k: len(v) for k, v in samples.items()},
                "preflight": prepared["preflight"],
            }
        ),
        flush=True,
    )


def inputs(args):
    roots, sources = setup(args)
    prepared = read_json(args.output_dir / "prepared.json")
    require(prepared["code_sha256"] == code_fingerprint(), "Matrix code changed")
    require(
        prepared["sources"] == sources and prepared["settings"] == SETTINGS,
        "Sources/settings changed",
    )
    require(
        prepared["manifest_sha256"] == file_digest(HERE / "manifest.json"),
        "Manifest changed",
    )
    require(
        prepared["inputs_sha256"] == file_digest(args.output_dir / "inputs.jsonl"),
        "Inputs changed",
    )
    require(
        prepared["transport_sha256"]
        == file_digest(args.output_dir / "transport.jsonl"),
        "Transport changed",
    )
    rows = [
        json.loads(line)
        for line in (args.output_dir / "inputs.jsonl").read_text().splitlines()
    ]
    require(
        len(rows) == len({r["source_key"] for r in rows}) == 1995,
        "Missing/duplicate inputs",
    )
    tasks = NativeTasks(roots, rows, args.output_dir / "transport.jsonl")
    require(tasks.configs == prepared["configs"], "Native config changed")
    return prepared, rows, tasks


def expected_rows(rows, size, condition):
    return {
        r["source_key"]: {
            **r,
            **r["variants"][condition],
            **r["variants"][condition]["models"][size],
        }
        for r in rows
    }


def run_stage(backend, rows, size, condition, stage, reference, folder, protocol):
    engine = "reference" if reference else "native"
    name = f"{stage}-{engine}"
    expected = expected_rows(rows, size, condition)
    path = folder / f"{name}.jsonl"
    completed = load_matrix_results(path, expected)
    status_path = folder / f"{name}-status.json"
    start = now()
    versions = tuple(p._version for p in backend.model.parameters())
    try:
        for row in rows:
            key = row["source_key"]
            if key in completed:
                continue
            scores, metrics, tokens = backend.score(row, condition, reference)
            exp = expected[key]
            require(
                digest(tokens) == exp["tokens_sha256"], "Runtime tokenizer mismatch"
            )
            result = {
                field: exp[field]
                for field in (
                    "source_key",
                    "category",
                    "native_category",
                    "native_task",
                    "source_category",
                    "condition",
                    "raw_row_sha256",
                    "payload_sha256",
                    "tokens_sha256",
                    "gold_index",
                    "num_choices",
                    "config_sha256",
                )
            }
            result.update(
                scores=scores,
                prediction=max(range(len(scores)), key=lambda i: scores[i]),
                prediction_norm=max(
                    range(len(scores)),
                    key=lambda i: scores[i] / exp["choice_char_lengths"][i],
                ),
                correct=int(metrics["acc"]),
                acc_norm=int(metrics["acc_norm"]),
                input_verified=True,
                truncated=0,
            )
            validate_matrix_result(result, exp)
            append_result(path, result)
            completed[key] = result
            state = {
                "status": "RUNNING",
                "model": size,
                "condition": condition,
                "stage": stage,
                "engine": engine,
                "completed": len(completed),
                "expected": len(rows),
                "started_at": start,
                "updated_at": now(),
                "pid": os.getpid(),
                "protocol_sha256": digest(protocol),
            }
            write_json(status_path, state)
            if len(completed) == 1 or len(completed) % 10 == 0:
                print(canonical(state), flush=True)
        require(
            versions == tuple(p._version for p in backend.model.parameters())
            and not backend.model.training,
            "Shared model state mutated",
        )
        require(set(completed) == set(expected), "Incomplete stage")
        write_json(
            status_path,
            {
                "status": "COMPLETE",
                "model": size,
                "condition": condition,
                "stage": stage,
                "engine": engine,
                "completed": len(completed),
                "expected": len(rows),
                "started_at": start,
                "finished_at": now(),
                "pid": os.getpid(),
                "protocol_sha256": digest(protocol),
                "output_sha256": file_digest(path),
            },
        )
    except BaseException:
        write_json(
            status_path,
            {
                "status": "FAILED",
                "completed": len(completed),
                "expected": len(rows),
                "failed_at": now(),
                "traceback": traceback.format_exc(),
            },
        )
        raise
    return completed


def model_run(args):
    import torch

    require(GPU_UUID, "Set POLYGLOT_GPU_UUID to the single GPU exposed to this run")
    prepared, rows, tasks = inputs(args)
    env = environment()
    env["installed_packages"] = dict(
        sorted(
            (d.metadata["Name"].lower(), d.version)
            for d in importlib.metadata.distributions()
        )
    )
    require(
        env["cuda"]
        and env["cuda"]["device_count"] == 1
        and env["cuda"]["uuid"].removeprefix("GPU-") == GPU_UUID.removeprefix("GPU-"),
        "Wrong GPU exposure",
    )
    require(env["cuda"]["total_memory"] >= 79 * 1024**3, "GPU memory too small")
    pins = {
        "torch": "2.14.1+cu126",
        "transformers": "5.20.1",
        "datasets": "5.1.0",
        "huggingface-hub": "1.33.0",
        "tokenizers": "0.23.3",
    }
    require(
        all(env["packages"][k] == v for k, v in pins.items()), "Environment pins differ"
    )
    size = args.model_size
    folder = args.output_dir / size
    folder.mkdir(exist_ok=True)
    protocol = {
        "prepared_sha256": digest(prepared),
        "environment": env,
        "model": prepared["models"][size],
        "settings": SETTINGS,
    }
    frozen(folder / "protocol.json", protocol)
    smoke = read_json(args.output_dir / "smoke.json")
    require(
        smoke["status"] == "PASS" and smoke["prepared_sha256"] == digest(prepared),
        "Smoke missing/stale",
    )
    backend = MatrixBackend(size, tasks)
    pilot_keys = set(
        prepared["samples"]["calibration"] + prepared["samples"]["validation"]
    )
    pilot_rows = [r for r in rows if r["source_key"] in pilot_keys]
    for condition in CONDITIONS:
        sub = folder / condition
        sub.mkdir(exist_ok=True)
        native = run_stage(
            backend, pilot_rows, size, condition, "pilot", False, sub, protocol
        )
        reference = run_stage(
            backend, pilot_rows, size, condition, "pilot", True, sub, protocol
        )
        gate = pilot_gate(native, reference, prepared["samples"])
        gate.update(
            protocol_sha256=digest(protocol),
            native_sha256=file_digest(sub / "pilot-native.jsonl"),
            reference_sha256=file_digest(sub / "pilot-reference.jsonl"),
        )
        frozen(sub / "calibration.json", gate)
        print(
            canonical(
                {"event": "PILOT_GATE", "model": size, "condition": condition, **gate}
            ),
            flush=True,
        )
        require(
            gate["status"] == "PASS", "Held-out gate failed; do not widen tolerance"
        )
    results = {}
    for condition in CONDITIONS:
        sub = folder / condition
        gate = read_json(sub / "calibration.json")
        require(
            gate["status"] == "PASS" and gate["protocol_sha256"] == digest(protocol),
            "Stale pilot gate",
        )
        require(
            file_digest(sub / "pilot-native.jsonl") == gate["native_sha256"]
            and file_digest(sub / "pilot-reference.jsonl") == gate["reference_sha256"],
            "Pilot changed",
        )
        results[condition] = run_stage(
            backend, rows, size, condition, "full", False, sub, protocol
        )
        write_json(
            sub / "summary.json",
            {
                "status": "PASS",
                "model": size,
                "condition": condition,
                "protocol_sha256": digest(protocol),
                "calibration": gate,
                "result_sha256": file_digest(sub / "full-native.jsonl"),
                **condition_summary(results[condition]),
            },
        )
        print(
            canonical(
                {
                    "event": "FULL_COMPLETE",
                    "model": size,
                    "condition": condition,
                    "rows": 1995,
                }
            ),
            flush=True,
        )
    verify_four_choice_equivalence(results)
    pairs = [
        ("base_letter", "pr4420_letter"),
        ("base_full", "pr4420_full"),
        ("base_letter", "base_full"),
        ("pr4420_letter", "pr4420_full"),
    ]
    deltas = {
        f"{b}_minus_{a}": {
            "overall": paired_delta(results[a], results[b]),
            "strata": {
                name: paired_delta(
                    {k: r for k, r in results[a].items() if predicate(r)},
                    {k: r for k, r in results[b].items() if predicate(r)},
                )
                for name, predicate in (
                    ("four_choice", lambda r: r["num_choices"] == 4),
                    ("five_choice", lambda r: r["num_choices"] == 5),
                    ("gold_E", lambda r: r["gold_index"] == 4),
                )
            },
        }
        for a, b in pairs
    }
    write_json(
        folder / "summary.json",
        {
            "status": "PASS",
            "model": size,
            "protocol": protocol,
            "four_choice_exact_score_and_prediction_equality": "PASS",
            "conditions": {
                c: read_json(folder / c / "summary.json") for c in CONDITIONS
            },
            "paired_deltas": deltas,
        },
    )
    del backend
    torch.cuda.empty_cache()
    print(
        canonical(
            {"event": "MODEL_COMPLETE", "model": size, "status": "PASS", "at": now()}
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("/workspace/results-matrix")
    )
    parser.add_argument("--old-output", type=Path, default=Path("/workspace/results"))
    parser.add_argument(
        "--harness-root",
        type=Path,
        default=Path("/workspace/sources/lm-evaluation-harness"),
    )
    parser.add_argument(
        "--task-snapshots", type=Path, default=Path("/workspace/sources/matrix-tasks")
    )
    parser.add_argument("--model-size", choices=tuple(MODELS))
    parser.add_argument(
        "--revision-repository",
        type=Path,
        help="Private git object repository containing both revisions; original installed PR source stays untouched",
    )
    args = parser.parse_args()
    require(
        args.output_dir.resolve() != args.old_output.resolve(),
        "Must preserve old results",
    )
    if args.command == "prepare":
        prepare(args)
    else:
        require(args.model_size is not None, "Model required")
        model_run(args)


if __name__ == "__main__":
    main()
