"""Inspect the stopped diagnostic replay without changing benchmark results."""

import fcntl
import json
import time
import traceback

import torch
import transformers_click as scoring
from diagnose_transformers import DIAG, settings
from replay_transformers import Capture
from vllm_run import ensure_idle


def main():
    out = DIAG / "inspect-stop-20261120T121908Z"
    out.mkdir(exist_ok=False)
    lock = (scoring.ROOT / "results/gpu.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ensure_idle()
    protocol = scoring.read(scoring.ROOT / "prepared/protocol.json")
    scoring.verify_run(protocol)
    scoring.write(out / "status.json", {"state": "RUNNING", "started": time.time()})
    backend = scoring.Backend("qwen38-27b", "harness", protocol)
    tasks = scoring.Tasks()
    scoring.write(out / "settings.json", settings(backend.model))
    comparisons = []
    # First compare the saved long-history traces against a fresh process using
    # precisely the original scoring function and the same Capture hooks.
    for saved in sorted((DIAG / "replay/traces/base_letter").glob("*.pt"), key=lambda p: int(p.stem)):
        index = int(saved.stem)
        capture = Capture(backend.model)
        item = {"index": index, "source_key": tasks.rows[index]["source_key"]}
        dest = out / "traces" / saved.name
        try:
            item["result"] = backend.score(tasks, tasks.rows[index], "base_letter", protocol)
        except Exception:
            item["error"] = traceback.format_exc()
        finally:
            capture.close(dest)
        a, b = torch.load(saved, weights_only=True), torch.load(dest, weights_only=True)
        assert a.keys() == b.keys() and torch.equal(a["input_ids"], b["input_ids"])
        item["trace_differences"] = {k: float((a[k].float() - b[k].float()).abs().max()) for k in a if k != "input_ids"}
        item["first_changed_tensor"] = next((k for k, v in item["trace_differences"].items() if v != 0), None)
        comparisons.append(item)
        scoring.write(out / "trace-comparisons.json", comparisons)
        print(json.dumps({"index": index, "first_changed_tensor": item["first_changed_tensor"], "error": item.get("error")}), flush=True)

    original_after, original_finish = scoring.ForwardAudit.after, scoring.ForwardAudit.finish
    observations = []

    def after(audit, module, args, kwargs, output):
        original_after(audit, module, args, kwargs, output)
        logits = output.logits
        full_lp = torch.log_softmax(logits, dim=-1)
        start = len(audit.tokens["context"]) - 1
        for r, matches in enumerate(audit.matches):
            for candidate in matches:
                targets = audit.tokens["continuations"][candidate]
                lp = full_lp[r, start:start + len(targets)].gather(1, torch.tensor(targets, device=logits.device)[:, None]).squeeze(1)
                audit.values[candidate][-1]["full_shape_sum"] = float(lp.sum())

    def finish(audit, scores):
        observations.append({"native_scores": scores, "audit_values": dict(audit.values), "batches": audit.batches})
        return original_finish(audit, scores)  # Retain the exact original check.

    scoring.ForwardAudit.after, scoring.ForwardAudit.finish = after, finish
    try:
        for repeat in range(3):
            for index in (1515, 1495):
                for condition in ("base_letter", "pr4420_letter"):
                    observations.clear()
                    item = {"repeat": repeat, "index": index, "condition": condition, "observations": observations}
                    try:
                        item["result"] = backend.score(tasks, tasks.rows[index], condition, protocol)
                    except Exception:
                        item["error"] = traceback.format_exc()
                    with (out / "audit-comparisons.jsonl").open("a") as stream:
                        stream.write(json.dumps(item) + "\n")
                    print(json.dumps({k: v for k, v in item.items() if k != "observations" and k != "result"}), flush=True)
    finally:
        scoring.ForwardAudit.after, scoring.ForwardAudit.finish = original_after, original_finish
    scoring.verify_run(protocol)
    scoring.write(out / "status.json", {"state": "COMPLETE", "ended": time.time(), "traces": len(comparisons)})


if __name__ == "__main__":
    main()
