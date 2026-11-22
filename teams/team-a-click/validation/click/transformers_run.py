"""Run both models sequentially on the isolated GPU, preserving checkpoints."""

import fcntl
import subprocess
import sys
import time

from transformers_click import ROOT, read, verify_run, write
from vllm_run import ensure_idle


def status(state, **details):
    value = {
        "state": state,
        "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **details,
    }
    write(ROOT / "results/status.json", value)
    print(value, flush=True)


def step(model, stage, engine=None):
    key = f"{model}-{stage}" + (f"-{engine}" if engine else "")
    if engine:
        ensure_idle()
    command = [sys.executable, str(ROOT / "code/transformers_click.py")]
    if engine:
        command += ["run", "--model", model, "--stage", stage, "--engine", engine]
    else:
        command += ["gate", "--model", model]
    logfile = ROOT / "logs" / f"{key}.log"
    status("RUNNING", model=model, stage=stage, engine=engine, log=str(logfile))
    with logfile.open("a") as stream:
        result = subprocess.run(
            command, stdout=stream, stderr=subprocess.STDOUT, check=False
        )
    (ROOT / "results" / f"{key}.exit").write_text(str(result.returncode) + "\n")
    if result.returncode:
        raise RuntimeError(f"{key} exited {result.returncode}; see {logfile}")
    status("STEP_COMPLETE", model=model, stage=stage, engine=engine)


def main():
    lock = (ROOT / "results/controller.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    verify_run(read(ROOT / "prepared/protocol.json"))
    for model in ("kanana2-3b", "qwen38-27b"):
        for stage in ("probe", "pilot"):
            for engine in ("lighteval", "harness"):
                step(model, stage, engine)
        step(model, "pilot-gate")
        for engine in ("lighteval", "harness"):
            step(model, "full", engine)
    status("REPORTING")
    with (ROOT / "logs/report.log").open("a") as stream:
        result = subprocess.run(
            [sys.executable, str(ROOT / "code/transformers_report.py")],
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode:
        raise RuntimeError("Report integrity checks failed; see report.log")
    report = read(ROOT / "report/results.json")
    status(
        "COMPLETE",
        report=str(ROOT / "report/README.md"),
        prediction_parity=report["prediction_parity"],
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        status("STOPPED", reason=str(error))
        raise
