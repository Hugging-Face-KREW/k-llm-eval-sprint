"""CLIcK native Lighteval/harness comparison with an audited vLLM backend.

Run inside the isolated evaluation container. Original Polyglot runners and
results are deliberately not modified. Private inputs are never public reports.
"""

import argparse
import collections
import hashlib
import importlib.metadata
import json
import math
import os
import time
from pathlib import Path

from polyglot_core import RAW_FIELDS, digest, harness_payload, require, select_samples
from polyglot_matrix_native import NativeTasks, requests_payload

ROOT = Path(os.environ.get("CLICK_WORKSPACE", "/workspace"))
MODELS = {
    "kanana2-3b": (
        "kakaocorp/kanana-2-3b-instruct",
        "6a5d7889964c4c590299d16e309eabab1f73f8a9",
    ),
    "qwen38-27b": ("Qwen/Qwen3.8-27B", "37561816e66b5b9153b1b64c10968c18c1e6f4a0"),
}
CONDITIONS = (
    "lighteval_full",
    "aligned_harness_full",
    "base_letter",
    "pr4420_letter",
    "base_full",
    "pr4420_full",
)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s]


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def verify_environment(protocol=None):
    for relative, expected in read(ROOT / "environment/sources.json")["files"].items():
        require(
            file_hash(ROOT / relative) == expected, f"Frozen source changed: {relative}"
        )
    if protocol:
        require(
            file_hash(ROOT / "environment/sources.json")
            == protocol["source_manifest_sha256"],
            "Source manifest changed",
        )
        for package, expected in protocol["versions"].items():
            require(
                importlib.metadata.version(package) == expected,
                f"Package changed: {package}",
            )


def tokens_for(tokenizer, payload):
    context = tokenizer.encode(payload["query"], add_special_tokens=False)
    choices = [
        tokenizer.encode(c, add_special_tokens=False) for c in payload["choices"]
    ]
    require(bool(context) and all(choices), "Empty token sequence")
    for text, candidate in zip(payload["choices"], choices, strict=True):
        require(
            tokenizer.encode(payload["query"] + text, add_special_tokens=False)
            == context + candidate,
            "Joint/separate tokenization differs; resolve before evaluation",
        )
    return {"context": context, "continuations": choices}


class Tasks:
    def __init__(self):
        from lighteval.tasks.tasks.click import CATEGORY_FILES
        from polyglot_backends import lighteval_tasks, make_harness_task

        self.rows = lines(ROOT / "prepared/old-aligned-inputs.jsonl")
        require(len(self.rows) == 1995, "Dataset coverage changed")
        manifest = read(ROOT / "code/manifest.json")
        indexed = {r["source_key"]: r for r in manifest["rows"]}
        require(
            set(indexed) == {r["source_key"] for r in self.rows},
            "Manifest coverage mismatch",
        )
        for row in self.rows:
            require(
                digest({k: row["raw"][k] for k in RAW_FIELDS})
                == indexed[row["source_key"]]["raw_row_sha256"],
                "Original row changed",
            )
            require(
                harness_payload(row["raw"]) == row["payload"], "Aligned payload changed"
            )
        self.le = lighteval_tasks()
        self.docs = {}
        for category, task in self.le.items():
            for doc in task.get_docs():
                key = (category, doc.specific["raw_row_sha256"])
                require(key not in self.docs, "Ambiguous native Doc")
                self.docs[key] = doc
        require(len(self.docs) == 1995, "Lighteval coverage mismatch")
        self.aligned = {
            c: make_harness_task(c, files) for c, files in CATEGORY_FILES.items()
        }
        transport = ROOT / "prepared/transport.jsonl"
        content = "".join(
            json.dumps(r["raw"], ensure_ascii=False) + "\n" for r in self.rows
        )
        if transport.exists():
            require(transport.read_text() == content, "Transport changed")
        else:
            transport.write_text(content)
        roots = {
            v: ROOT / f"snapshots/{v}/lm_eval/tasks/click" for v in ("base", "pr4420")
        }
        self.native = NativeTasks(roots, self.rows, transport)
        old_matrix = {
            r["source_key"]: r for r in lines(ROOT / "prepared/old-matrix-inputs.jsonl")
        }
        for row in self.rows:
            doc = self.docs[row["category"], row["raw_row_sha256"]]
            require(
                (doc.query, doc.choices, doc.gold_index)
                == (
                    row["payload"]["query"],
                    row["payload"]["choices"],
                    row["payload"]["gold_index"],
                ),
                "Native Lighteval input differs",
            )
            for condition in CONDITIONS:
                _task, _req, payload = self.request(row, condition)
                expected = (
                    row["payload"]
                    if condition in CONDITIONS[:2]
                    else old_matrix[row["source_key"]]["variants"][condition]["payload"]
                )
                require(payload == expected, "Original Polyglot payload changed")

    def request(self, row, condition):
        if condition == "lighteval_full":
            return (
                self.le[row["category"]],
                self.docs[row["category"], row["raw_row_sha256"]],
                row["payload"],
            )
        if condition == "aligned_harness_full":
            task = self.aligned[row["category"]]
        else:
            variant = self.native.rows[condition][row["source_key"]]
            task = self.native.tasks[condition][variant["native_category"]]
        req, payload = requests_payload(task, row["raw"], row["row_number"])
        return task, req, payload


def prepare():
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer

    require(
        not (ROOT / "prepared/protocol.json").exists(), "Preparation already frozen"
    )
    verify_environment()
    tasks = Tasks()
    models, maximum = {}, 0
    for name, (repo, rev) in MODELS.items():
        location = snapshot_download(
            repo, revision=rev, allow_patterns=["*.json", "*.txt", "*.jinja", "*.model"]
        )
        tokenizer = AutoTokenizer.from_pretrained(location)
        lengths, maxima, token_hashes = {}, {}, {}
        for condition in CONDITIONS:
            condition_lengths, fingerprints = {}, []
            for row in tasks.rows:
                _, _, payload = tasks.request(row, condition)
                tokens = tokens_for(tokenizer, payload)
                n = max(
                    len(tokens["context"]) + len(c) for c in tokens["continuations"]
                )
                condition_lengths[row["source_key"]] = n
                fingerprints.append((row["source_key"], digest(tokens)))
            lengths[condition] = condition_lengths
            maxima[condition] = max(condition_lengths.values())
            token_hashes[condition] = digest(fingerprints)
        # Selection is based only on inputs, before any predictions are observed.
        merged_lengths = {
            r["source_key"]: max(lengths[c][r["source_key"]] for c in CONDITIONS)
            for r in tasks.rows
        }
        sample = select_samples(tasks.rows, merged_lengths)
        maximum = max(maximum, max(maxima.values()))
        models[name] = {
            "repo": repo,
            "revision": rev,
            "location": location,
            "max_lengths": maxima,
            "token_hashes": token_hashes,
            "samples": sample,
        }
    limit = 2048 if maximum <= 2048 else 2 ** math.ceil(math.log2(maximum))
    protocol = {
        "schema": 1,
        "models": models,
        "context_limit": limit,
        "engine_limit": limit + 1,
        "dtype": "bfloat16",
        "seed": 1234,
        "num_items": 1995,
        "conditions": CONDITIONS,
        "host": "tailab",
        "host_gpu_index": 1,
        "gpu_uuid": "GPU-4d10fa0e-f11b-ca93-a51d-bea42af0dfaa",
        "image": "tailab:0.0.1",
        "storage": "/mnt/sdb/hyeongrae-click-vllm-20261120",
        "manifest_sha256": file_hash(ROOT / "code/manifest.json"),
        "original_inputs_sha256": file_hash(ROOT / "prepared/old-aligned-inputs.jsonl"),
        "source_manifest_sha256": file_hash(ROOT / "environment/sources.json"),
        "versions": {
            p: importlib.metadata.version(p)
            for p in (
                "torch",
                "vllm",
                "transformers",
                "lighteval",
                "lm_eval",
                "datasets",
                "tokenizers",
            )
        },
    }
    write(ROOT / "prepared/protocol.json", protocol)
    print(
        json.dumps(
            {
                "prepared": True,
                "context_limit": limit,
                "models": {
                    k: {
                        "max_lengths": v["max_lengths"],
                        "samples": {s: len(ids) for s, ids in v["samples"].items()},
                    }
                    for k, v in models.items()
                },
            },
            indent=2,
        ),
        flush=True,
    )


class Audit:
    """Verify every sequence actually submitted to vLLM and its scored tokens."""

    def __init__(self, model):
        self.original = model.generate
        self.expected = {}
        self.seen = []
        model.generate = self.generate

    def begin(self, tokens):
        self.expected = {
            tuple(tokens["context"] + c): len(tokens["context"])
            for c in tokens["continuations"]
        }
        self.seen = []

    def generate(self, *args, **kwargs):
        prompts = kwargs.get("prompts", args[0] if args else None)
        require(prompts is not None, "No auditable prompts")
        for prompt in prompts:
            require(
                tuple(prompt["prompt_token_ids"]) in self.expected,
                "vLLM input changed/truncated",
            )
        kwargs["use_tqdm"] = False
        outputs = self.original(*args, **kwargs)
        for output in outputs:
            ids = tuple(output.prompt_token_ids)
            require(ids in self.expected, "Returned vLLM prompt differs")
            start = self.expected[ids]
            require(len(output.prompt_logprobs) == len(ids), "Missing prompt positions")
            scores = []
            for i in range(start, len(ids)):
                require(
                    output.prompt_logprobs[i] is not None
                    and ids[i] in output.prompt_logprobs[i],
                    "Missing actual candidate token",
                )
                scores.append(float(output.prompt_logprobs[i][ids[i]].logprob))
            require(all(math.isfinite(x) for x in scores), "Non-finite token score")
            self.seen.append({"tokens_sha256": digest(ids), "scores": scores})
        return outputs

    def finish(self, tokens, scores):
        expected = collections.Counter(
            digest(tokens["context"] + c) for c in tokens["continuations"]
        )
        require(
            collections.Counter(r["tokens_sha256"] for r in self.seen) == expected,
            "Missing/duplicated candidate inference",
        )
        lookup = {r["tokens_sha256"]: r["scores"] for r in self.seen}
        per_token = [
            lookup[digest(tokens["context"] + c)] for c in tokens["continuations"]
        ]
        require(
            all(
                abs(sum(raw) - total) < 1e-5
                for raw, total in zip(per_token, scores, strict=True)
            ),
            "Adapter scored wrong token positions",
        )
        return per_token


class Backend:
    def __init__(self, name, condition, reference, protocol):
        import torch
        from transformers import AutoTokenizer

        torch.set_grad_enabled(False)
        torch.manual_seed(1234)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        self.reference, self.condition = reference, condition
        model = protocol["models"][name]
        path = model["location"]
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        if reference:
            from transformers import AutoModelForCausalLM, AutoModelForImageTextToText

            loader = (
                AutoModelForImageTextToText
                if name == "qwen38-27b"
                else AutoModelForCausalLM
            )
            self.model = (
                loader.from_pretrained(
                    path, dtype=torch.bfloat16, attn_implementation="eager"
                )
                .to("cuda")
                .eval()
            )
            self.adapter = None
        else:
            common = {
                "dtype": "bfloat16",
                "tensor_parallel_size": 1,
                "seed": 1234,
                "max_model_len": protocol["engine_limit"],
                "max_num_seqs": 1,
                "max_num_batched_tokens": protocol["engine_limit"],
                "enforce_eager": True,
                "enable_prefix_caching": False,
                "gpu_memory_utilization": protocol.get("gpu_memory_utilization", 0.90),
                "logprobs_mode": "raw_logprobs",
                "kv_cache_dtype": "auto",
            }
            if condition == "lighteval_full":
                from lighteval.models.vllm.vllm_model import VLLMModel, VLLMModelConfig
                from vllm import LLM

                class ExplicitEngine(VLLMModel):
                    def _create_auto_model(self, config):
                        self.model_args = {"model": config.model_name, **common}
                        return LLM(**self.model_args)

                config = VLLMModelConfig(
                    model_name=path,
                    dtype="bfloat16",
                    override_chat_template=False,
                    add_special_tokens=False,
                    pairwise_tokenization=True,
                    multichoice_continuations_start_space=False,
                    max_model_length=protocol["engine_limit"],
                    max_num_seqs=1,
                    enable_prefix_caching=False,
                    cache_dir=str(ROOT / "cache/unused-lighteval"),
                )
                self.adapter = ExplicitEngine(config)
            else:
                from lm_eval.models.vllm_causallms import VLLM

                self.adapter = VLLM(
                    pretrained=path,
                    tokenizer=path,
                    add_bos_token=False,
                    batch_size=1,
                    **common,
                )
            self.model = self.adapter.model
            self.audit = Audit(self.model)

    def score(self, tasks, row, condition, protocol):
        import torch

        task, request, payload = tasks.request(row, condition)
        tokens = tokens_for(self.tokenizer, payload)
        require(
            max(len(tokens["context"]) + len(c) for c in tokens["continuations"])
            <= protocol["context_limit"],
            "Input would truncate",
        )
        if self.reference:
            per_token = []
            for continuation in tokens["continuations"]:
                whole = tokens["context"] + continuation
                with torch.inference_mode():
                    logits = self.model(
                        input_ids=torch.tensor([whole[:-1]], device="cuda"),
                        use_cache=False,
                    ).logits[0]
                    start = len(tokens["context"]) - 1
                    selected = logits[start : start + len(continuation)].float()
                    targets = torch.tensor(continuation, device="cuda")
                    per_token.append(
                        torch.log_softmax(selected, -1)
                        .gather(1, targets[:, None])
                        .squeeze(1)
                        .tolist()
                    )
            scores = [sum(x) for x in per_token]
            metrics = {
                "acc": int(
                    max(range(len(scores)), key=scores.__getitem__)
                    == payload["gold_index"]
                )
            }
        else:
            self.audit.begin(tokens)
            if condition == "lighteval_full":
                require(
                    self.adapter.prompt_manager.prepare_prompt(request)
                    == payload["query"],
                    "Prompt template added content",
                )
                response = self.adapter._loglikelihood_tokens([request])[0]
                scores = [float(s) for s in response.logprobs]
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
                require(filtered == responses, "Native filter altered responses")
                metrics = {
                    k: float(v)
                    for k, v in task.process_results(row["raw"], filtered).items()
                }
                task._instances = []
                scores = [float(r[0]) for r in filtered]
            per_token = self.audit.finish(tokens, scores)
        pred = max(range(len(scores)), key=scores.__getitem__)
        require(
            metrics["acc"] == int(pred == payload["gold_index"]),
            "Native metric differs",
        )
        return {
            "source_key": row["source_key"],
            "category": row["category"],
            "gold": payload["gold_index"],
            "num_choices": len(scores),
            "scores": scores,
            "prediction": pred,
            "metrics": metrics,
            "payload_sha256": digest(payload),
            "tokens_sha256": digest(tokens),
            "token_logprobs": per_token,
        }


def run(args):
    import fcntl

    from huggingface_hub import snapshot_download

    protocol = read(ROOT / "prepared/protocol.json")
    verify_environment(protocol)
    folder = ROOT / "results" / args.model
    folder.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / "results/gpu.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.stage == "full":
        require(read(folder / "pilot-gate.json")["passed"], "Pilot gate not passed")
    model = protocol["models"][args.model]
    snapshot_download(
        model["repo"],
        revision=model["revision"],
        allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model", "*.jinja"],
    )
    tasks = Tasks()
    selected = set(model["samples"]["calibration"] + model["samples"]["validation"])
    rows = (
        tasks.rows
        if args.stage == "full"
        else [r for r in tasks.rows if r["source_key"] in selected]
    )
    if args.stage == "probe":
        rows = [
            next(r for r in tasks.rows if len(r["raw"]["choices"]) == n) for n in (4, 5)
        ]
    conditions = (
        CONDITIONS
        if args.condition == "all"
        else CONDITIONS[1:]
        if args.condition == "harness"
        else (args.condition,)
    )
    require(
        args.reference or args.condition != "all",
        "Use a separate native adapter per condition",
    )
    backend = Backend(args.model, args.condition, args.reference, protocol)
    identity = {
        "protocol_sha256": digest(protocol),
        "runner_sha256": file_hash(__file__),
        "model": args.model,
        "reference": args.reference,
        "stage": args.stage,
    }
    for condition in conditions:
        output = (
            folder
            / f"{args.stage}-{'reference' if args.reference else 'vllm'}-{condition}.jsonl"
        )
        identity_path = output.with_suffix(".protocol.json")
        expected_identity = {**identity, "condition": condition}
        if identity_path.exists():
            require(
                read(identity_path) == expected_identity,
                "Cannot resume changed protocol/code",
            )
        else:
            require(not output.exists(), "Results without identity")
            write(identity_path, expected_identity)
        previous = lines(output) if output.exists() else []
        for saved in previous:
            require(
                saved.get("row_sha256")
                == digest({k: v for k, v in saved.items() if k != "row_sha256"}),
                "Saved row integrity mismatch",
            )
        done = {r["source_key"] for r in previous}
        require(
            len(done) == len(previous) and done <= {r["source_key"] for r in rows},
            "Invalid resume coverage",
        )
        started = time.time()
        processed = 0
        with output.open("a") as stream:
            for i, row in enumerate(rows):
                if row["source_key"] in done:
                    continue
                result = backend.score(tasks, row, condition, protocol)
                processed += 1
                result["row_sha256"] = digest(result)
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                stream.flush()
                if (i + 1) % 20 == 0 or i + 1 == len(rows):
                    os.fsync(stream.fileno())
                    print(
                        json.dumps(
                            {
                                "model": args.model,
                                "condition": condition,
                                "reference": args.reference,
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


def compare_files(left, right, keys):
    a = {r["source_key"]: r for r in lines(left)}
    b = {r["source_key"]: r for r in lines(right)}
    require(set(keys) <= set(a) & set(b), "Comparison rows missing")
    result = []
    for key in keys:
        require(
            a[key]["payload_sha256"] == b[key]["payload_sha256"]
            and a[key]["tokens_sha256"] == b[key]["tokens_sha256"],
            "Comparison inputs differ",
        )
        delta = max(
            abs(x - y) for x, y in zip(a[key]["scores"], b[key]["scores"], strict=True)
        )
        result.append(
            {
                "source_key": key,
                "max_abs_diff": delta,
                "same_prediction": a[key]["prediction"] == b[key]["prediction"],
            }
        )
    return result


def gate(name):
    protocol = read(ROOT / "prepared/protocol.json")
    samples = protocol["models"][name]["samples"]
    folder = ROOT / "results" / name
    checks = []
    for condition in CONDITIONS:
        pairs = [
            (
                folder / f"pilot-vllm-{condition}.jsonl",
                folder / f"pilot-reference-{condition}.jsonl",
                condition + ":reference",
            )
        ]
        if condition == "lighteval_full":
            pairs.append(
                (
                    folder / "pilot-vllm-lighteval_full.jsonl",
                    folder / "pilot-vllm-aligned_harness_full.jsonl",
                    "aligned-parity",
                )
            )
        for left, right, label in pairs:
            calibration = compare_files(left, right, samples["calibration"])
            atol = max(1e-6, 2 * max(r["max_abs_diff"] for r in calibration))
            validation = compare_files(left, right, samples["validation"])
            failures = [
                r
                for r in calibration + validation
                if not r["same_prediction"] or r["max_abs_diff"] > atol
            ]
            checks.append(
                {
                    "label": label,
                    "atol": atol,
                    "rtol": 0,
                    "calibration_max": max(r["max_abs_diff"] for r in calibration),
                    "validation_max": max(r["max_abs_diff"] for r in validation),
                    "failures": failures,
                    "passed": not failures,
                }
            )
    result = {
        "passed": all(c["passed"] for c in checks),
        "checks": checks,
        "protocol_sha256": digest(protocol),
    }
    write(folder / "pilot-gate.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    require(result["passed"], "Pilot validation failed; full evaluation is blocked")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("prepare", "run", "gate"))
    p.add_argument("--model", choices=MODELS)
    p.add_argument(
        "--condition", choices=(*CONDITIONS, "all", "harness"), default="all"
    )
    p.add_argument("--stage", choices=("probe", "pilot", "full"), default="probe")
    p.add_argument("--reference", action="store_true")
    args = p.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "gate":
        gate(args.model)
    else:
        run(args)


if __name__ == "__main__":
    main()
