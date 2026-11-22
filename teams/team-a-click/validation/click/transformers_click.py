"""Native CLIcK adapters with BF16 Transformers weights and read-only forward audits.

No prompt, candidate, native batching, logits, or metric is replaced. The audit
recomputes the score from each adapter's actual forward output, not another run.
"""

import argparse
import collections
import fcntl
import json
import math
import os
import time

from vllm_click import (
    CONDITIONS,
    MODELS,
    ROOT,
    Tasks,
    compare_files,
    digest,
    file_hash,
    lines,
    read,
    require,
    tokens_for,
    verify_environment,
    write,
)


class ForwardAudit:
    def __init__(self, tokens, pad, omit_last):
        self.tokens, self.pad, self.omit_last = tokens, pad, omit_last
        self.whole = [tokens["context"] + c for c in tokens["continuations"]]
        self.expected = [x[:-1] if omit_last else x for x in self.whole]
        self.values = collections.defaultdict(list)
        self.batches = []
        self.forward_rows = 0

    def before(self, module, args, kwargs):
        ids = kwargs.get("input_ids", args[0] if args else None)
        require(ids is not None and ids.ndim == 2, "Missing model input")
        self.matches = []
        for row in ids.detach().cpu().tolist():
            found = [
                i
                for i, expected in enumerate(self.expected)
                if row[: len(expected)] == expected
                and all(t == self.pad for t in row[len(expected) :])
            ]
            require(found, "Actual input changed, truncated, or gained special tokens")
            self.matches.append(found)
        self.batches.append(list(ids.shape))
        self.forward_rows += len(self.matches)

    def after(self, module, args, kwargs, output):
        import torch

        logits = output.logits
        require(
            logits.ndim == 3 and logits.shape[0] == len(self.matches),
            "Logits shape differs",
        )
        start = len(self.tokens["context"]) - 1
        for row, matches in enumerate(self.matches):
            for candidate in matches:
                targets = self.tokens["continuations"][candidate]
                selected = logits[row, start : start + len(targets)]
                require(
                    len(selected) == len(targets), "Missing first/last target position"
                )
                # Native adapters use log_softmax and sum in their logits dtype.
                lp = (
                    torch.log_softmax(selected, dim=-1)
                    .gather(1, torch.tensor(targets, device=logits.device)[:, None])
                    .squeeze(1)
                )
                require(bool(torch.isfinite(lp).all()), "Non-finite candidate logprob")
                self.values[candidate].append(
                    {
                        "sum": float(lp.sum()),
                        "tokens": lp.float().cpu().tolist(),
                        "logits_dtype": str(logits.dtype),
                        "sum_dtype": str(lp.dtype),
                    }
                )
        # A forward hook returning None leaves the model output untouched.

    def finish(self, scores):
        require(
            self.forward_rows == len(scores), "Missing/duplicate candidate forwards"
        )
        require(
            set(self.values) == set(range(len(scores))), "Candidate did not reach model"
        )
        result = []
        for i, score in enumerate(scores):
            require(math.isfinite(score), "Non-finite native score")
            require(
                all(abs(value["sum"] - score) <= 1e-5 for value in self.values[i]),
                "Native score differs from audited continuation positions",
            )
            result.append(self.values[i][0])
        return result


class Backend:
    def __init__(self, name, engine, protocol):
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoModelForImageTextToText,
            AutoTokenizer,
        )

        torch.set_grad_enabled(False)
        torch.manual_seed(1234)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.set_float32_matmul_precision("highest")
        self.engine = engine
        info = protocol["models"][name]
        self.tokenizer = AutoTokenizer.from_pretrained(info["location"])
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        loader = (
            AutoModelForImageTextToText
            if name == "qwen38-27b"
            else AutoModelForCausalLM
        )
        self.model = (
            loader.from_pretrained(
                info["location"],
                dtype=torch.bfloat16,
                attn_implementation="eager",
                trust_remote_code=False,
            )
            .to("cuda")
            .eval()
        )
        dtypes = collections.Counter(str(p.dtype) for p in self.model.parameters())
        require(
            set(dtypes) == {"torch.bfloat16"}, f"Weights are not all BF16: {dtypes}"
        )
        if engine == "lighteval":
            from lighteval.models.transformers.transformers_model import (
                TransformersModel,
                TransformersModelConfig,
            )

            config = TransformersModelConfig(
                model_name=info["location"],
                dtype="bfloat16",
                device="cuda",
                model_parallel=False,
                batch_size=1,
                max_length=protocol["context_limit"],
                override_chat_template=False,
                add_special_tokens=False,
                pairwise_tokenization=True,
                multichoice_continuations_start_space=False,
                cache_dir=str(ROOT / "cache/lighteval-transformers-unused"),
                model_loading_kwargs={"attn_implementation": "eager"},
            )
            self.adapter = TransformersModel.from_model(self.model, config)
            self.tokenizer = self.adapter.tokenizer
        else:
            from lm_eval.models.huggingface import HFLM

            self.adapter = HFLM(
                pretrained=self.model,
                tokenizer=self.tokenizer,
                backend="causal",
                device="cuda",
                dtype="bfloat16",
                softmax_dtype=None,
                batch_size=1,
                max_length=protocol["context_limit"],
                add_bos_token=False,
                logits_cache=False,
                truncation=False,
            )

    def score(self, tasks, row, condition, protocol):
        import torch

        task, request, payload = tasks.request(row, condition)
        tokens = tokens_for(self.tokenizer, payload)
        require(
            max(len(tokens["context"]) + len(c) for c in tokens["continuations"])
            <= protocol["context_limit"],
            "Input would truncate",
        )
        audit = ForwardAudit(
            tokens, self.tokenizer.pad_token_id, self.engine == "harness"
        )
        before = self.model.register_forward_pre_hook(audit.before, with_kwargs=True)
        after = self.model.register_forward_hook(audit.after, with_kwargs=True)
        try:
            with torch.inference_mode():
                if self.engine == "lighteval":
                    require(
                        self.adapter.prompt_manager.prepare_prompt(request)
                        == payload["query"],
                        "Native prompt gained content",
                    )
                    response = self.adapter._loglikelihood_tokens([request])[0]
                    scores = [float(x) for x in response.logprobs]
                    metrics = {
                        "acc": int(
                            task.metrics[0].sample_level_fn.compute(request, response)
                        )
                    }
                else:
                    responses = self.adapter.loglikelihood(request, disable_tqdm=True)
                    for req, response in zip(request, responses, strict=True):
                        req.resps = [response]
                    task._instances = request
                    task.apply_filters()
                    filtered = [req.filtered_resps["none"] for req in request]
                    require(filtered == responses, "Native filter changed responses")
                    metrics = {
                        k: float(v)
                        for k, v in task.process_results(row["raw"], filtered).items()
                    }
                    task._instances = []
                    scores = [float(r[0]) for r in filtered]
        finally:
            before.remove()
            after.remove()
        audited = audit.finish(scores)
        prediction = max(range(len(scores)), key=scores.__getitem__)
        require(
            metrics["acc"] == int(prediction == payload["gold_index"]),
            "Native acc differs",
        )
        if "acc_norm" in metrics:
            lengths = [len(c) for c in task.doc_to_choice(row["raw"])]
            pred_norm = max(range(len(scores)), key=lambda i: scores[i] / lengths[i])
            require(
                metrics["acc_norm"] == int(pred_norm == payload["gold_index"]),
                "Native acc_norm differs",
            )
        return {
            "source_key": row["source_key"],
            "category": row["category"],
            "gold": payload["gold_index"],
            "num_choices": len(scores),
            "scores": scores,
            "prediction": prediction,
            "metrics": metrics,
            "payload_sha256": digest(payload),
            "tokens_sha256": digest(tokens),
            "token_logprobs": [v["tokens"] for v in audited],
            "forward_audit": {
                "passed": True,
                "batches": audit.batches,
                "logits_dtype": audited[0]["logits_dtype"],
                "sum_dtype": audited[0]["sum_dtype"],
                "omits_last_input_token": self.engine == "harness",
            },
        }


def verify_run(protocol):
    verify_environment(protocol)
    for name, expected in protocol["runner_files"].items():
        require(file_hash(ROOT / "code" / name) == expected, f"Runner changed: {name}")
    require(
        file_hash(ROOT / "prepared/old-aligned-inputs.jsonl")
        == protocol["original_inputs_sha256"],
        "Inputs changed",
    )
    require(
        file_hash(ROOT / "prepared/old-matrix-inputs.jsonl")
        == protocol["matrix_inputs_sha256"],
        "Matrix changed",
    )


def validate_rows(path, protocol, expected_count=None):
    identity = read(path.with_suffix(".protocol.json"))
    require(identity["protocol_sha256"] == digest(protocol), "Result protocol differs")
    require(identity["runner_sha256"] == file_hash(__file__), "Result runner differs")
    rows = lines(path)
    require(len({r["source_key"] for r in rows}) == len(rows), "Duplicate rows")
    if expected_count is not None:
        require(len(rows) == expected_count, "Incomplete rows")
    for row in rows:
        require(
            row["row_sha256"]
            == digest({k: v for k, v in row.items() if k != "row_sha256"}),
            "Row integrity failure",
        )
        require(row["forward_audit"]["passed"], "Forward audit failed")
    return rows


def run(args):
    protocol = read(ROOT / "prepared/protocol.json")
    verify_run(protocol)
    folder = ROOT / "results" / args.model
    folder.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / "results/gpu.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.stage == "full":
        gate = read(folder / "pilot-gate.json")
        require(
            gate["input_and_scoring_audit_passed"]
            and gate["protocol_sha256"] == digest(protocol),
            "Pilot audit not passed",
        )
    tasks = Tasks()
    samples = protocol["models"][args.model]["samples"]
    selected = set(samples["calibration"] + samples["validation"])
    rows = (
        tasks.rows
        if args.stage == "full"
        else [r for r in tasks.rows if r["source_key"] in selected]
    )
    if args.stage == "probe":
        rows = [
            next(r for r in tasks.rows if len(r["raw"]["choices"]) == n) for n in (4, 5)
        ]
    conditions = CONDITIONS[:1] if args.engine == "lighteval" else CONDITIONS[1:]
    pending = []
    for condition in conditions:
        output = folder / f"{args.stage}-transformers-{condition}.jsonl"
        identity_path = output.with_suffix(".protocol.json")
        identity = {
            "protocol_sha256": digest(protocol),
            "runner_sha256": file_hash(__file__),
            "model": args.model,
            "condition": condition,
            "stage": args.stage,
            "engine": args.engine,
        }
        if identity_path.exists():
            require(read(identity_path) == identity, "Cannot resume changed run")
        else:
            require(not output.exists(), "Results without identity")
            write(identity_path, identity)
        previous = validate_rows(output, protocol) if output.exists() else []
        done = {r["source_key"] for r in previous}
        require(done <= {r["source_key"] for r in rows}, "Unexpected resumed rows")
        if len(done) < len(rows):
            pending.append((condition, output, done))
    if not pending:
        print("All rows already complete and verified", flush=True)
        return
    backend = Backend(args.model, args.engine, protocol)
    for condition, output, done in pending:
        started, processed = time.time(), 0
        with output.open("a") as stream:
            for i, row in enumerate(rows):
                if row["source_key"] in done:
                    continue
                result = backend.score(tasks, row, condition, protocol)
                result["row_sha256"] = digest(result)
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                stream.flush()
                processed += 1
                if (i + 1) % 20 == 0 or i + 1 == len(rows):
                    os.fsync(stream.fileno())
                    print(
                        json.dumps(
                            {
                                "model": args.model,
                                "condition": condition,
                                "stage": args.stage,
                                "done": i + 1,
                                "total": len(rows),
                                "elapsed_s": round(time.time() - started, 1),
                                "remaining_s_estimate": round(
                                    (time.time() - started)
                                    / processed
                                    * (len(rows) - i - 1),
                                    1,
                                ),
                            }
                        ),
                        flush=True,
                    )


def comparisons(folder, stage, keys, four_keys):
    results = []
    pairs = [("lighteval_full", "aligned_harness_full", keys)]
    pairs.extend(
        ("base_" + mode, "pr4420_" + mode, four_keys) for mode in ("letter", "full")
    )
    for left, right, selected in pairs:
        rows = compare_files(
            folder / f"{stage}-transformers-{left}.jsonl",
            folder / f"{stage}-transformers-{right}.jsonl",
            selected,
        )
        results.append(
            {
                "comparison": left + "_vs_" + right,
                "items": len(rows),
                "same_prediction": sum(r["same_prediction"] for r in rows),
                "max_abs_logprob_diff": max(r["max_abs_diff"] for r in rows),
                "exact_scores": all(r["max_abs_diff"] == 0 for r in rows),
                "prediction_parity": all(r["same_prediction"] for r in rows),
            }
        )
    return results


def gate(name):
    protocol = read(ROOT / "prepared/protocol.json")
    verify_run(protocol)
    samples = protocol["models"][name]["samples"]
    keys = set(samples["calibration"] + samples["validation"])
    folder = ROOT / "results" / name
    for condition in CONDITIONS:
        rows = validate_rows(
            folder / f"pilot-transformers-{condition}.jsonl", protocol, len(keys)
        )
        require({r["source_key"] for r in rows} == keys, "Wrong pilot coverage")
    original = {
        r["source_key"]: r for r in lines(ROOT / "prepared/old-aligned-inputs.jsonl")
    }
    four = [k for k in keys if len(original[k]["raw"]["choices"]) == 4]
    checks = comparisons(folder, "pilot", sorted(keys), sorted(four))
    result = {
        "input_and_scoring_audit_passed": True,
        "prediction_parity": all(c["prediction_parity"] for c in checks),
        "comparisons": checks,
        "protocol_sha256": digest(protocol),
        "policy": "Native adapter numerical differences are measured, not silently corrected. Full run requires valid input and native score audits.",
    }
    write(folder / "pilot-gate.json", result)
    print(json.dumps(result, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("run", "gate"))
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--engine", choices=("lighteval", "harness"))
    parser.add_argument("--stage", choices=("probe", "pilot", "full"), default="probe")
    args = parser.parse_args()
    if args.action == "gate":
        gate(args.model)
    else:
        require(args.engine is not None, "Choose native engine")
        run(args)


if __name__ == "__main__":
    main()
