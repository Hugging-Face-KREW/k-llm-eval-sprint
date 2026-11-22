"""Sequential, resumable process supervisor for the isolated CLIcK experiment."""

import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLICK_WORKSPACE", "/workspace"))
GPU = "GPU-4d10fa0e-f11b-ca93-a51d-bea42af0dfaa"


def model_files(model):
    from huggingface_hub import snapshot_download
    from vllm_click import file_hash, read, require, write

    info = read(ROOT / "prepared/protocol.json")["models"][model]
    status("PREPARING_MODEL", model=model)
    location = Path(
        snapshot_download(
            info["repo"],
            revision=info["revision"],
            allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model", "*.jinja"],
        )
    )
    files = {
        str(p.relative_to(location)): {"size": p.stat().st_size, "sha256": file_hash(p)}
        for p in sorted(location.rglob("*"))
        if p.is_file()
    }
    manifest = {"repo": info["repo"], "revision": info["revision"], "files": files}
    destination = ROOT / "environment" / f"model-{model}.json"
    if destination.exists():
        require(read(destination) == manifest, "Model files changed on resume")
    else:
        write(destination, manifest)


def status(state, **kwargs):
    value = {
        "state": state,
        "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **kwargs,
    }
    path = ROOT / "results/status.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)
    print(json.dumps(value), flush=True)


def ensure_idle():
    for _ in range(20):
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=gpu_uuid,pid",
                "--format=csv,noheader",
            ],
            text=True,
        )
        occupied = [
            line for line in output.splitlines() if line.split(",")[0].strip() == GPU
        ]
        if not occupied:
            return
        time.sleep(1)
    raise RuntimeError("Selected GPU is occupied; no other process will be stopped")


def step(model, name, arguments, gpu=True):
    key = model + "-" + name
    receipt = ROOT / "results" / (key + ".exit")
    logfile = ROOT / "logs" / (key + ".log")
    # Always enter the runner: it validates identities/integrity before reusing rows.
    if gpu:
        ensure_idle()
    status("RUNNING", model=model, step=name, log=str(logfile))
    started = time.time()
    command = [
        sys.executable,
        str(ROOT / "code/vllm_click.py"),
        *arguments,
        "--model",
        model,
    ]
    with logfile.open("a") as stream:
        result = subprocess.run(
            command,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    receipt.write_text(str(result.returncode) + "\n")
    if result.returncode:
        raise RuntimeError(f"{key} exited {result.returncode}; see {logfile}")
    status(
        "STEP_COMPLETE",
        model=model,
        step=name,
        elapsed_s=round(time.time() - started, 1),
    )


def main():
    lock = (ROOT / "results/controller.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (ROOT / "environment/prepare.exit").read_text().strip() != "0":
        raise RuntimeError("Preparation did not pass")
    if not (ROOT / "smoke/validated.json").exists():
        status("WAITING_GPU_SMOKE")
        deadline = time.monotonic() + 1800
        receipt = ROOT / "results/smoke-rest-online.exit"
        while not receipt.exists() and time.monotonic() < deadline:
            time.sleep(5)
        if not receipt.exists() or receipt.read_text().strip() != "0":
            raise RuntimeError("GPU adapter smoke failed or timed out; see smoke logs")
    if not json.loads((ROOT / "smoke/validated.json").read_text())["passed"]:
        raise RuntimeError("GPU adapter smoke failed")
    for model in ("kanana2-3b", "qwen38-27b"):
        model_files(model)
        for stage in ("probe", "pilot"):
            step(
                model,
                stage + "-reference",
                ["run", "--stage", stage, "--reference", "--condition", "all"],
            )
            step(
                model,
                stage + "-lighteval",
                ["run", "--stage", stage, "--condition", "lighteval_full"],
            )
            step(
                model,
                stage + "-harness",
                ["run", "--stage", stage, "--condition", "harness"],
            )
        step(model, "pilot-gate", ["gate"], gpu=False)
        step(
            model,
            "full-lighteval",
            ["run", "--stage", "full", "--condition", "lighteval_full"],
        )
        step(
            model, "full-harness", ["run", "--stage", "full", "--condition", "harness"]
        )
    status("INFERENCE_COMPLETE_REPORT_PENDING")
    with (ROOT / "logs/report.log").open("a") as stream:
        result = subprocess.run(
            [sys.executable, str(ROOT / "code/vllm_report.py")],
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode:
        raise RuntimeError("Final report validation failed; see logs/report.log")
    status("COMPLETE", report=str(ROOT / "report/README.md"))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        status("STOPPED", reason=str(exc))
        raise
