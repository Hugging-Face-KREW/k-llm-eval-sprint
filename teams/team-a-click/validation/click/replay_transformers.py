"""Replay original Qwen harness history with read-only traces on diagnostic rows."""

import argparse
import collections
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

import torch
import transformers_click as scoring
from diagnose_transformers import DIAG, settings
from transformers_click import Backend, ROOT, Tasks, digest, file_hash, lines, read, verify_run, write
from vllm_run import ensure_idle

RUN = DIAG / os.environ.get("CLICK_DIAGNOSTIC_REPLAY", "replay")


def recorded_audit_class(folder, current):
    """Retain the original validation; preserve its evidence before it raises."""
    class RecordedAudit(scoring.ForwardAudit):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.observed_calls = []
            self.observed_logits = []

        def after(self, module, args, kwargs, output):
            super().after(module, args, kwargs, output)
            self.observed_calls.append({"matches": [list(m) for m in self.matches],
                "shape": list(output.logits.shape), "call_index": len(self.observed_calls)})
            if current.get("condition", "").endswith("_letter"):
                start = len(self.tokens["context"]) - 1
                longest = max(map(len, self.tokens["continuations"]))
                self.observed_logits.append(output.logits[:, start:start+longest].detach().cpu().clone())

        def finish(self, scores):
            try:
                return super().finish(scores)
            except Exception:
                folder.mkdir(parents=True, exist_ok=True)
                write(folder / "audit-failure-values.json", {**current,
                    "native_scores": scores, "values": dict(self.values),
                    "calls": self.observed_calls, "tokens": self.tokens,
                    "original_validation_preserved": True})
                torch.save(self.observed_logits, folder / "audit-failure-logits.pt")
                raise

    return RecordedAudit


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def status(state, **details):
    value = {"state": state, "updated_utc": stamp(), "diagnostic_run": True, **details}
    write(RUN / "results/status.json", value)
    print(json.dumps(value), flush=True)


def progress(phase, condition=None, done=None):
    counts = {p.stem: sum(1 for _ in p.open()) for p in (RUN / "results").glob("*.jsonl")}
    write(RUN / "results/tracking.json", {
        "updated_utc": stamp(), "phase": phase, "condition": condition,
        "done": done, "counts": counts, "completed_items": sum(counts.values()),
        "total_items": 5985, "status": read(RUN / "results/status.json"),
    })


class Capture:
    def __init__(self, model):
        self.values, self.handles, self.calls, self.active = {}, [], 0, False
        self.handles.append(model.register_forward_pre_hook(self.before, with_kwargs=True))
        for name, module in model.named_modules():
            if re.fullmatch(r"model\.language_model\.layers\.\d+", name):
                self.handles.append(module.register_forward_hook(self.layer_hook(name)))
            if name == "lm_head":
                self.handles.append(module.register_forward_pre_hook(self.head_hook))
        self.handles.append(model.register_forward_hook(self.after, with_kwargs=True))

    def before(self, module, args, kwargs):
        self.active = self.calls == 0
        if self.active:
            ids = kwargs.get("input_ids", args[0] if args else None)
            self.values["input_ids"] = ids.detach().cpu().clone()

    def layer_hook(self, name):
        def capture(module, args, output):
            if self.active:
                value = output[0] if isinstance(output, (tuple, list)) else output
                self.values[name] = value[0, -1].detach().cpu().clone()
        return capture

    def head_hook(self, module, args):
        if self.active:
            self.values["lm_head_input"] = args[0][0, -1].detach().cpu().clone()

    def after(self, module, args, kwargs, output):
        if self.active:
            self.values["logits"] = output.logits[0, -1].detach().cpu().clone()
        self.calls += 1
        self.active = False

    def close(self, path):
        for handle in self.handles:
            handle.remove()
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.values, path)


def worker(phase):
    lock = (ROOT / "results/gpu.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ensure_idle()
    protocol = read(ROOT / "prepared/protocol.json")
    verify_run(protocol)
    tasks = Tasks()
    backend = Backend("qwen38-27b", "harness", protocol)
    selection = set(read(DIAG / "selection-qwen38-27b-repeat.json")["source_keys"])
    conditions = ("aligned_harness_full", "base_letter", "pr4420_letter") if phase == "before" else ("pr4420_letter",)
    write(RUN / f"environment-{phase}.json", settings(backend.model))
    current = {"phase": phase}
    if os.environ.get("CLICK_DIAGNOSTIC_AUDIT") == "1":
        scoring.ForwardAudit = recorded_audit_class(RUN, current)
    for condition in conditions:
        output = RUN / "results" / f"{condition}.jsonl"
        if phase == "before":
            assert not output.exists(), "Fresh history replay cannot skip already executed history"
        else:
            assert len(lines(output)) == 1495, "Resume boundary differs"
        indices = range(1995)
        if condition == "pr4420_letter":
            indices = range(1495) if phase == "before" else range(1495, 1995)
        write(RUN / f"settings-{phase}-{condition}-before.json", settings(backend.model))
        started = time.time()
        with output.open("a") as stream:
            for index in indices:
                row = tasks.rows[index]
                current.update(condition=condition, index=index, source_key=row["source_key"])
                capture = Capture(backend.model) if condition != "aligned_harness_full" and row["source_key"] in selection else None
                try:
                    result = backend.score(tasks, row, condition, protocol)
                except Exception:
                    write(RUN / "failure.json", {"phase": phase, "condition": condition,
                        "index": index, "source_key": row["source_key"], "traceback": traceback.format_exc(),
                        "settings": settings(backend.model)})
                    raise
                finally:
                    if capture:
                        capture.close(RUN / "traces" / condition / f"{index}.pt")
                result["row_index"] = index
                result["row_sha256"] = digest(result)
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                stream.flush()
                if (index + 1) % 20 == 0 or index == indices.stop - 1:
                    progress(phase, condition, index + 1)
                    print(json.dumps({"phase": phase, "condition": condition,
                        "done": index + 1, "elapsed_s": round(time.time() - started, 1)}), flush=True)
        write(RUN / f"settings-{phase}-{condition}-after.json", settings(backend.model))


def report():
    a = {r["source_key"]: r for r in lines(RUN / "results/base_letter.jsonl")}
    b = {r["source_key"]: r for r in lines(RUN / "results/pr4420_letter.jsonl")}
    assert len(a) == len(b) == 1995 and a.keys() == b.keys()
    comparisons = []
    for key, left in a.items():
        right = b[key]
        if left["num_choices"] != 4:
            continue
        assert left["tokens_sha256"] == right["tokens_sha256"] and left["payload_sha256"] == right["payload_sha256"]
        result = {"source_key": key, "index": left["row_index"],
                  "same_prediction": left["prediction"] == right["prediction"],
                  "max_score_diff": max(abs(x-y) for x,y in zip(left["scores"],right["scores"]))}
        ta, tb = [RUN / "traces" / c / f"{left['row_index']}.pt" for c in ("base_letter", "pr4420_letter")]
        if ta.exists() and tb.exists():
            x, y = torch.load(ta, weights_only=True), torch.load(tb, weights_only=True)
            assert torch.equal(x["input_ids"], y["input_ids"])
            result["trace_differences"] = {n: float((x[n].float()-y[n].float()).abs().max()) for n in x if n != "input_ids"}
            result["first_changed_tensor"] = next((n for n,d in result["trace_differences"].items() if d != 0), None)
        comparisons.append(result)
    result = {"diagnostic_replay": True, "complete": True,
        "items_per_condition": 1995, "total_outputs": 5985,
        "four_choice_items": len(comparisons),
        "prediction_differences": sum(not r["same_prediction"] for r in comparisons),
        "score_differences": sum(r["max_score_diff"] != 0 for r in comparisons),
        "comparisons": comparisons,
        "original_results_unchanged": True,
        "replay": "aligned_full 1995 -> base_letter 1995 -> pr4420_letter 1495 -> fresh process -> remaining 500",
        "caution": "Read-only tracing of last-token layer outputs on 19 old disagreement rows and 4 controls adds observation overhead."}
    write(RUN / "report/results.json", result)
    text = f"# Qwen 원본 실행 순서 재현\n\n전체 진단 완료: 5,985개 결과. 기존 평가 결과는 변경하지 않았다.\n\n동일 입력 4지선다 {len(comparisons)}문항 중 예측 차이 {result['prediction_differences']}개, 점수 차이 {result['score_differences']}개.\n\n레이어별 trace 차이는 results.json을 확인한다. 실행 완료가 원인 확정을 의미하지 않는다.\n"
    (RUN / "report/README.md").write_text(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("supervise", "before", "after"))
    args = parser.parse_args()
    for folder in ("results", "logs", "report", "traces"):
        (RUN / folder).mkdir(parents=True, exist_ok=True)
    if args.action != "supervise":
        worker(args.action)
        return
    lock = (RUN / "results/controller.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    write(RUN / "provenance.json", {"runner_sha256": file_hash(__file__),
        "parent_protocol_sha256": digest(read(ROOT / "prepared/protocol.json")),
        "record_audit_on_failure": os.environ.get("CLICK_DIAGNOSTIC_AUDIT") == "1",
        "started_utc": stamp(), "benchmark_code_unchanged": True})
    try:
        for phase in ("before", "after"):
            log = RUN / "logs" / f"{phase}.log"
            status("RUNNING", phase=phase, log=str(log), purpose="Qwen same-input discrepancy diagnosis")
            progress(phase)
            with log.open("a") as stream:
                subprocess.run([sys.executable, __file__, phase], stdout=stream, stderr=subprocess.STDOUT, check=True)
        status("REPORTING")
        progress("report")
        report()
        status("COMPLETE", report=str(RUN / "report/README.md"), purpose="Qwen same-input discrepancy diagnosis")
        progress("complete")
    except Exception as error:
        status("STOPPED", reason=str(error), failure=str(RUN / "failure.json"))
        progress("stopped")
        raise


if __name__ == "__main__":
    main()
