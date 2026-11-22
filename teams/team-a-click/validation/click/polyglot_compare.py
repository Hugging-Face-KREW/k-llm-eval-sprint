"""Prepare, run and report reproducible CLIcK/Polyglot comparisons.

All raw inputs, token logs and checkpoints belong in an ignored/private output
directory. This runner uses native Python evaluation APIs, not a CLI parity claim.
"""

import argparse
import csv
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from polyglot_core import (
    DATA_REVISION,
    HARNESS_REVISION,
    LIGHTEVAL_REVISION,
    MODELS,
    SETTINGS,
    append_result,
    comparison,
    digest,
    establish_tolerance,
    file_digest,
    load_results,
    read_json,
    require,
    select_samples,
    source_records,
    token_contract,
    validate_result,
    write_json,
)

HERE = Path(__file__).resolve().parent


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def source_state(root, revision, package):
    require(git(root, "rev-parse", "HEAD") == revision, f"Wrong source HEAD: {root}")
    diff = git(root, "diff", "HEAD", "--", ".")
    if diff:
        names = git(root, "diff", "--name-only", "HEAD").splitlines()
        require(
            package == "src/lighteval"
            and names == ["src/lighteval/metrics/metrics_sample.py"],
            "Unexpected source patch",
        )
        relative = "src/lighteval/metrics/metrics_sample.py"
        original = subprocess.check_output(
            ["git", "-C", str(root), "show", f"HEAD:{relative}"], text=True
        )
        patched = original.replace(
            "api.list_models(model_name=judge_model_name)",
            "api.list_models(search=judge_model_name)",
        )
        require(
            (root / relative).read_text() == patched, "Unexpected compatibility patch"
        )
    hashes = {
        p.relative_to(root).as_posix(): file_digest(p)
        for p in sorted((root / package).rglob("*.py"))
    }
    return {
        "revision": revision,
        "patch_sha256": digest(diff),
        "python_tree_sha256": digest(hashes),
    }


def setup_sources(args):
    le, harness = args.lighteval_root.resolve(), args.harness_root.resolve()
    states = {
        "lighteval": source_state(le, LIGHTEVAL_REVISION, "src/lighteval"),
        "harness": source_state(harness, HARNESS_REVISION, "lm_eval"),
    }
    sys.path[:0] = [str(le / "src"), str(harness)]
    return states


def runner_digest():
    return digest(
        {
            name: file_digest(HERE / name)
            for name in (
                "polyglot_compare.py",
                "polyglot_core.py",
                "polyglot_backends.py",
                "polyglot_paper_reference.json",
            )
        }
    )


def environment():
    import torch

    packages = {}
    for name in (
        "torch",
        "transformers",
        "tokenizers",
        "datasets",
        "huggingface-hub",
        "accelerate",
        "numpy",
        "lighteval",
        "lm-eval",
    ):
        packages[name] = importlib.metadata.version(name)
    cuda = None
    if torch.cuda.is_available():
        prop = torch.cuda.get_device_properties(0)
        cuda = {
            "name": prop.name,
            "total_memory": prop.total_memory,
            "uuid": str(getattr(prop, "uuid", "unknown")),
            "device_count": torch.cuda.device_count(),
            "runtime": torch.version.cuda,
        }
    return {"python": platform.python_version(), "packages": packages, "cuda": cuda}


def private_output(path):
    path = path.resolve()
    # Prevent accidentally placing raw source/logs in a tracked team directory.
    repo = HERE.parents[3]
    if path.is_relative_to(repo):
        result = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "--quiet", str(path)], check=False
        )
        require(
            result.returncode == 0,
            "Output inside repository must be ignored; use .polyglot/results",
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare(args):
    from huggingface_hub import snapshot_download
    from polyglot_backends import native_inputs
    from transformers import AutoConfig, AutoTokenizer

    sources = setup_sources(args)
    output = private_output(args.output_dir)
    require(
        not (output / "prepared.json").exists(),
        "Preparation exists; use it or select a new output directory",
    )
    manifest_path = HERE / "manifest.json"
    manifest = read_json(manifest_path)
    snapshot = args.snapshot or Path(
        snapshot_download(
            repo_id="EunsuKim/CLIcK",
            repo_type="dataset",
            revision=DATA_REVISION,
            allow_patterns=[f["path"] for f in manifest["files"]],
        )
    )
    records = source_records(snapshot, manifest_path)
    payloads = native_inputs(records)
    rows = []
    tokenizers = {}
    for size, (model, revision) in MODELS.items():
        cfg = AutoConfig.from_pretrained(
            model, revision=revision, trust_remote_code=False
        )
        require(cfg.max_position_embeddings == 2048, "Model context changed")
        tokenizers[size] = AutoTokenizer.from_pretrained(
            model, revision=revision, trust_remote_code=False
        )
    lengths = {size: {} for size in MODELS}
    for record in records:
        payload = payloads[record["source_key"]]
        row = {
            **record,
            "payload": payload,
            "payload_sha256": digest(payload),
            "gold_index": payload["gold_index"],
            "num_choices": len(payload["choices"]),
            "models": {},
        }
        for size, tokenizer in tokenizers.items():
            tokens = token_contract(tokenizer, payload)
            maximum = max(
                len(tokens["context"]) + len(c) for c in tokens["continuations"]
            )
            lengths[size][record["source_key"]] = maximum
            row["models"][size] = {
                "tokens_sha256": digest(tokens),
                "max_tokens": maximum,
            }
        rows.append(row)
    inputs_path = output / "inputs.jsonl"
    with inputs_path.open("x") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    samples = select_samples(
        records,
        {
            key: max(values[key] for values in lengths.values())
            for key in lengths["1.3b"]
        },
    )
    prepared = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_revision": DATA_REVISION,
        "manifest_sha256": file_digest(manifest_path),
        "runner_sha256": runner_digest(),
        "sources": sources,
        "settings": SETTINGS,
        "models": {
            size: {"repo": pair[0], "revision": pair[1]}
            for size, pair in MODELS.items()
        },
        "items": len(rows),
        "inputs_sha256": file_digest(inputs_path),
        "samples": samples,
        "preflight": {
            size: {
                "maximum_tokens": max(values.values()),
                "over_context": 0,
                "joint_separate_differences": 0,
            }
            for size, values in lengths.items()
        },
        "native_input_comparison": "PASS",
        "model_evaluation": "NOT_RUN",
    }
    write_json(output / "prepared.json", prepared)
    print(
        json.dumps(
            {
                "items": len(rows),
                "preflight": prepared["preflight"],
                "calibration_items": len(samples["calibration"]),
                "validation_items": len(samples["validation"]),
            }
        )
    )


def prepared_inputs(output):
    prepared = read_json(output / "prepared.json")
    require(
        prepared["runner_sha256"] == runner_digest(),
        "Runner changed; prepare a new experiment",
    )
    require(prepared["settings"] == SETTINGS, "Settings changed")
    require(
        prepared["manifest_sha256"] == file_digest(HERE / "manifest.json"),
        "Source manifest changed",
    )
    require(
        prepared["inputs_sha256"] == file_digest(output / "inputs.jsonl"),
        "Prepared inputs changed",
    )
    rows = [
        json.loads(line) for line in (output / "inputs.jsonl").read_text().splitlines()
    ]
    require(
        len(rows) == prepared["items"] == len({r["source_key"] for r in rows}),
        "Prepared rows missing/duplicated",
    )
    return prepared, rows


def expected_rows(rows, size):
    return {row["source_key"]: {**row, **row["models"][size]} for row in rows}


def run(args):
    from polyglot_backends import Backend

    output = private_output(args.output_dir)
    prepared, rows = prepared_inputs(output)
    require(
        setup_sources(args) == prepared["sources"],
        "Evaluation source changed since preparation",
    )
    env = environment()
    require(
        env["cuda"] and env["cuda"]["device_count"] == 1,
        "Expose exactly GPU 3 to the container",
    )
    require(
        env["cuda"]["total_memory"] >= 79 * 1024**3,
        "FP32 protocol requires an 80GB-class GPU",
    )
    size, engine, stage = args.model_size, args.engine, args.stage
    model_dir = output / size
    model_dir.mkdir(exist_ok=True)
    protocol = {
        "prepared_sha256": digest(prepared),
        "environment": env,
        "model": prepared["models"][size],
    }
    protocol_path = model_dir / "protocol.json"
    if protocol_path.exists():
        require(
            read_json(protocol_path) == protocol,
            "Environment changed across engines/runs",
        )
    else:
        write_json(protocol_path, protocol)
    pilot_keys = set(
        prepared["samples"]["calibration"] + prepared["samples"]["validation"]
    )
    if stage == "pilot":
        rows = [r for r in rows if r["source_key"] in pilot_keys]
    else:
        require(
            engine != "reference", "Independent full pass is not part of this protocol"
        )
        gate = read_json(model_dir / "calibration.json")
        require(
            gate["status"] == "PASS" and gate["protocol_sha256"] == digest(protocol),
            "Pilot gate missing/failed/stale",
        )
        for name, checksum in gate["pilot_files"].items():
            require(
                file_digest(model_dir / name) == checksum,
                "Pilot evidence changed after calibration",
            )
    expected = expected_rows(rows, size)
    results_path = model_dir / f"{stage}-{engine}.jsonl"
    completed = load_results(results_path, expected)
    if len(completed) == len(rows):
        print(f"Already complete: {size} {stage} {engine}, {len(rows)} rows")
        return
    backend = Backend(engine, size, model_dir)
    status_path = model_dir / f"{stage}-{engine}-status.json"
    started = time.monotonic()
    try:
        for record in rows:
            key = record["source_key"]
            if key in completed:
                continue
            scores, correct, tokens = backend.score(record, record["payload"])
            require(
                digest(tokens) == expected[key]["tokens_sha256"],
                "Runtime tokenizer differs from preparation",
            )
            result = {
                field: expected[key][field]
                for field in (
                    "source_key",
                    "category",
                    "raw_row_sha256",
                    "payload_sha256",
                    "tokens_sha256",
                    "gold_index",
                )
            }
            result.update(
                scores=scores,
                correct=correct,
                prediction=max(range(len(scores)), key=lambda i: scores[i]),
                truncated=0,
                input_verified=True,
            )
            validate_result(result, expected[key])
            append_result(results_path, result)
            completed[key] = result
            state = {
                "status": "RUNNING",
                "completed": len(completed),
                "expected": len(rows),
                "elapsed_this_process_seconds": time.monotonic() - started,
                "last_source_key": key,
            }
            write_json(status_path, state)
            if len(completed) % 10 == 0:
                print(
                    f"{size} {stage} {engine}: {len(completed)}/{len(rows)}", flush=True
                )
        state["status"] = "COMPLETE"
        write_json(status_path, state)
    except BaseException as error:
        write_json(
            status_path,
            {
                "status": "FAILED",
                "completed": len(completed),
                "expected": len(rows),
                "error": str(error),
            },
        )
        raise


def report(args):
    output = args.output_dir.resolve()
    prepared, rows = prepared_inputs(output)
    size = args.model_size
    model_dir = output / size
    protocol = read_json(model_dir / "protocol.json")
    require(protocol["prepared_sha256"] == digest(prepared), "Stale model protocol")
    expected = expected_rows(rows, size)
    if args.stage == "pilot":
        keys = set(
            prepared["samples"]["calibration"] + prepared["samples"]["validation"]
        )
        expected = {k: v for k, v in expected.items() if k in keys}
        engines = {
            engine: load_results(model_dir / f"pilot-{engine}.jsonl", expected)
            for engine in ("lighteval", "harness", "reference")
        }
        result = establish_tolerance(engines, prepared["samples"])
        result.update(
            protocol_sha256=digest(protocol),
            pilot_files={
                f"pilot-{engine}.jsonl": file_digest(
                    model_dir / f"pilot-{engine}.jsonl"
                )
                for engine in engines
            },
        )
        gate_path = model_dir / "calibration.json"
        if gate_path.exists():
            require(
                read_json(gate_path) == result,
                "Frozen calibration cannot be replaced; create a new experiment",
            )
        else:
            write_json(gate_path, result)
        print(json.dumps(result, ensure_ascii=False))
        require(
            result["status"] == "PASS",
            "Held-out pilot failed; investigate without widening tolerance",
        )
        return
    gate = read_json(model_dir / "calibration.json")
    require(
        gate["status"] == "PASS" and gate["protocol_sha256"] == digest(protocol),
        "Missing/stale pilot gate",
    )
    for name, checksum in gate["pilot_files"].items():
        require(
            file_digest(model_dir / name) == checksum,
            "Pilot evidence changed after calibration",
        )
    engines = {
        engine: load_results(model_dir / f"full-{engine}.jsonl", expected)
        for engine in ("lighteval", "harness")
    }
    require(
        all(set(values) == set(expected) for values in engines.values()),
        "Full comparison incomplete",
    )
    result = comparison(engines["lighteval"], engines["harness"], gate["atol"])
    result.update(
        model=prepared["models"][size],
        dataset_revision=prepared["dataset_revision"],
        settings=prepared["settings"],
        sources=prepared["sources"],
        runner_sha256=prepared["runner_sha256"],
        preflight=prepared["preflight"][size],
        protocol=protocol,
        tolerance=gate,
        result_files={
            f"full-{engine}.jsonl": file_digest(model_dir / f"full-{engine}.jsonl")
            for engine in engines
        },
    )
    write_json(model_dir / "summary.json", result)
    columns = [
        "category",
        "items",
        "lighteval_correct",
        "harness_correct",
        "lighteval_accuracy",
        "harness_accuracy",
        "same_prediction",
        "max_abs_diff",
    ]
    with (model_dir / "categories.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(
            {"category": name, **values}
            for name, values in result["categories"].items()
        )
    paper = read_json(HERE / "polyglot_paper_reference.json")
    lines = [
        f"# CLIcK Polyglot-Ko {size} 검증",
        "",
        f"상태: **{result['status']}**. Native Python API 비교이며 CLI 전체 실행 검증은 아닙니다.",
        "",
        "| 분야 | 문항 | Lighteval | 하네스 | 예측 일치 | 논문 (%) | 논문 대비 차이 (%p) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for category, values in result["categories"].items():
        baseline = paper["models"][size]["categories"][category]
        score = values["lighteval_accuracy"] * 100
        lines.append(
            f"| {category} | {values['items']} | {score:.4f}% | {values['harness_accuracy'] * 100:.4f}% | {values['same_prediction']} | {baseline:.2f} | {score - baseline:+.4f} |"
        )
    lines += [
        "",
        "## 집계",
        "",
        "```json",
        json.dumps(result["aggregates"], indent=2),
        "```",
        "",
        f"설명되지 않은 예측/점수 불일치: {len(result['mismatches'])}건. 상세는 summary.json의 mismatches에 있습니다.",
        "",
        f"논문 출처: {paper['source']}",
        "논문은 지시문 3종과 보기 순환을 사용합니다. 이 실험은 0-shot·단일 지시문·원본 순서이므로 참고 비교입니다.",
        "논문의 Average와 자체 micro/macro를 같은 산식으로 가정하지 않습니다. 수치가 다르다는 것만으로 구현 오류나 개선을 단정하지 않습니다.",
        "",
        "실행 설정·환경·revision·허용오차·결과 해시는 summary.json에 기록했습니다. 원문 및 토큰을 포함하는 inputs.jsonl은 공개하지 않습니다.",
    ]
    (model_dir / "report.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "model": size,
                "status": result["status"],
                "mismatches": len(result["mismatches"]),
            }
        )
    )
    require(
        result["status"] == "PASS", "Unexplained mismatches remain; see summary.json"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "report"))
    parser.add_argument("--output-dir", type=Path, default=Path(".polyglot/results"))
    parser.add_argument(
        "--lighteval-root", type=Path, default=Path(".polyglot/sources/lighteval")
    )
    parser.add_argument(
        "--harness-root",
        type=Path,
        default=Path(".polyglot/sources/lm-evaluation-harness"),
    )
    parser.add_argument(
        "--snapshot", type=Path, help="Optional local pinned dataset snapshot"
    )
    parser.add_argument("--model-size", choices=tuple(MODELS))
    parser.add_argument("--engine", choices=("lighteval", "harness", "reference"))
    parser.add_argument("--stage", choices=("pilot", "full"), default="pilot")
    args = parser.parse_args()
    if args.command != "prepare":
        parser.error("--model-size is required") if args.model_size is None else None
    if args.command == "run" and args.engine is None:
        parser.error("--engine is required")
    {"prepare": prepare, "run": run, "report": report}[args.command](args)


if __name__ == "__main__":
    main()
