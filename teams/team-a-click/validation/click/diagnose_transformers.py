"""Read-only benchmark diagnostics; writes separate records, never benchmark rows."""

import argparse
import collections
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

import torch
from transformers_click import Backend, ForwardAudit, ROOT, Tasks, digest, lines, read, tokens_for, verify_run, write
from vllm_run import ensure_idle

DIAG = ROOT / "diagnostics/root-cause-20261120"


def tensor_hash(t):
    return hashlib.sha256(t.detach().contiguous().view(torch.uint8).cpu().numpy().tobytes()).hexdigest()


def buffers(model):
    return {n: {"dtype": str(v.dtype), "shape": list(v.shape), "sha256": tensor_hash(v)}
            for n, v in model.named_buffers()}


def settings(model):
    return {
        "training_modules": sum(m.training for m in model.modules()),
        "parameter_dtypes": dict(collections.Counter(str(p.dtype) for p in model.parameters())),
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "cudnn_enabled": torch.backends.cudnn.enabled,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
        "tf32_cudnn": torch.backends.cudnn.allow_tf32,
        "bf16_reduced_reduction": torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
        "cublas_workspace": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        "generation_temperature": model.generation_config.temperature,
        "attention": getattr(getattr(model.config, "text_config", model.config), "_attn_implementation", None),
    }


def selected(tasks, name, kind):
    folder = ROOT / "results" / name
    left, right = (("base_letter", "pr4420_letter") if kind == "repeat"
                   else ("lighteval_full", "aligned_harness_full"))
    a = {r["source_key"]: r for r in lines(folder / f"full-transformers-{left}.jsonl")}
    b = {r["source_key"]: r for r in lines(folder / f"full-transformers-{right}.jsonl")}
    differing = [r for r in tasks.rows if a[r["source_key"]]["prediction"] != b[r["source_key"]]["prediction"]
                 and (kind != "repeat" or len(r["raw"]["choices"]) == 4)]
    if kind == "shape":
        # Spread a bounded causal diagnostic across all categories with disagreement.
        counts = collections.Counter()
        subset = []
        for row in differing:
            if counts[row["category"]] < 2:
                subset.append(row)
                counts[row["category"]] += 1
        differing = subset
    controls = [r for r in tasks.rows if a[r["source_key"]]["prediction"] == b[r["source_key"]]["prediction"]
                and len(r["raw"]["choices"]) == 4][:4]
    chosen = differing + controls
    write(DIAG / f"selection-{name}-{kind}.json", {
        "source_keys": [r["source_key"] for r in chosen],
        "disagreement_items": len(differing), "controls": len(controls),
        "selection": "Previously disagreeing rows plus first four agreeing 4-choice controls; not an accuracy estimate.",
    })
    return chosen


def native(backend, tasks, row, condition):
    task, request, payload = tasks.request(row, condition)
    expected = tokens_for(backend.tokenizer, payload)
    whole = [expected["context"] + c for c in expected["continuations"]]
    omit = backend.engine == "harness"
    calls = []
    def before(module, args, kwargs):
        ids = kwargs.get("input_ids", args[0] if args else None)
        actual = ids.detach().cpu().tolist()
        for value in actual:
            matches = [c[:-1] if omit else c for c in whole]
            assert any(value[:len(c)] == c and all(t == backend.tokenizer.pad_token_id for t in value[len(c):]) for c in matches)
        calls.append({"shape": list(ids.shape), "input_sha256": digest(actual)})
    hook = backend.model.register_forward_pre_hook(before, with_kwargs=True)
    audit_hooks = []
    audit = None
    if getattr(backend, "audit_original", False):
        audit = ForwardAudit(expected, backend.tokenizer.pad_token_id, omit)
        audit_hooks = [backend.model.register_forward_pre_hook(audit.before, with_kwargs=True),
                       backend.model.register_forward_hook(audit.after, with_kwargs=True)]
    cpu_rng, cuda_rng = tensor_hash(torch.get_rng_state()), tensor_hash(torch.cuda.get_rng_state())
    try:
        with torch.inference_mode():
            if omit:
                scores = [float(x[0]) for x in backend.adapter.loglikelihood(request, disable_tqdm=True)]
            else:
                assert backend.adapter.prompt_manager.prepare_prompt(request) == payload["query"]
                scores = [float(x) for x in backend.adapter._loglikelihood_tokens([request])[0].logprobs]
    finally:
        hook.remove()
        for handle in audit_hooks:
            handle.remove()
    return {"source_key": row["source_key"], "condition": condition, "scores": scores,
            "prediction": max(range(len(scores)), key=scores.__getitem__), "calls": calls,
            "tokens_sha256": digest(expected),
            "cpu_rng_unchanged": cpu_rng == tensor_hash(torch.get_rng_state()),
            "cuda_rng_unchanged": cuda_rng == tensor_hash(torch.cuda.get_rng_state()),
            "audit_max_diff": max((abs(v["sum"]-scores[i]) for i,vs in audit.values.items() for v in vs),default=0) if audit else None}


def append(path, value):
    with path.open("a") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
    print(json.dumps({k:v for k,v in value.items() if k in ("model", "phase", "pass", "source_key", "prediction", "scores", "mode")}), flush=True)


def repeat(args, tasks, backend):
    rows = selected(tasks, args.model, "repeat")
    path = DIAG / f"repeat-{args.model}-{args.mode}.jsonl"
    assert not path.exists(), "Do not overwrite diagnostics"
    # A generation call is an error here: likelihood evaluation must never sample.
    def no_generate(*args, **kwargs):
        raise AssertionError("Unexpected generate() call in likelihood evaluation")
    backend.model.generate = no_generate
    before = buffers(backend.model)
    write(DIAG / f"settings-{args.model}-{args.mode}.json", settings(backend.model))
    for pass_index, temperature in enumerate((0.1, 2.0, 0.1)):
        backend.model.generation_config.temperature = temperature
        for row in rows:
            for condition in ("base_letter", "pr4420_letter"):
                result = native(backend, tasks, row, condition)
                append(path, {"model": args.model, "phase": "repeat", "mode": args.mode,
                              "pass": pass_index, "generation_temperature": temperature, **result})
        after = buffers(backend.model)
        write(DIAG / f"buffers-{args.model}-{args.mode}-{pass_index}.json", {
            "before": before, "after": after,
            "changed": [k for k in before if before[k] != after[k]],
        })
    print("REPEAT COMPLETE", flush=True)


def score_layout(model, tokenizer, tokenized, mode):
    context, continuations = tokenized["context"], tokenized["continuations"]
    whole = [context + c for c in continuations]
    omit = mode.endswith("omit")
    seqs = [s[:-1] if omit else s for s in whole]
    max_len = max(map(len, seqs))
    order = sorted(range(len(seqs)), key=lambda i: (-len(whole[i]), tuple(whole[i])))
    batches = [list(range(len(seqs)))] if mode.startswith("batch_") else [[i] for i in order]
    outputs = {name: [None]*len(seqs) for name in ("native", "sum_fp32", "logsoftmax_fp32")}
    calls = []
    for indices in batches:
        padded = mode.startswith("batch_") or mode == "single_padded_full"
        size = max_len if padded else len(seqs[indices[0]])
        data = [seqs[i] + [tokenizer.pad_token_id]*(size-len(seqs[i])) for i in indices]
        ids = torch.tensor(data, device="cuda")
        with torch.inference_mode():
            logits = model(ids).logits
            # Both frameworks apply native log_softmax to the full forward tensor.
            native_lp = torch.log_softmax(logits, dim=-1)
            for j, i in enumerate(indices):
                target = torch.tensor(continuations[i], device="cuda")[:, None]
                start = len(context)-1
                lp = native_lp[j, start:start+len(target)].gather(1,target).squeeze(1)
                outputs["native"][i] = float(lp.sum())
                outputs["sum_fp32"][i] = float(lp.float().sum())
            del native_lp
            for j, i in enumerate(indices):
                target = torch.tensor(continuations[i], device="cuda")[:, None]
                start = len(context)-1
                lp32 = torch.log_softmax(logits[j,start:start+len(target)].float(),dim=-1).gather(1,target).squeeze(1)
                outputs["logsoftmax_fp32"][i] = float(lp32.sum())
            calls.append({"shape":list(ids.shape),"input_sha256":digest(data),"logits_dtype":str(logits.dtype)})
            del logits, lp32
    return {"scores":outputs, "predictions":{k:max(range(len(v)),key=v.__getitem__) for k,v in outputs.items()},"calls":calls}


def shape(args, tasks, backend, protocol):
    from lighteval.models.transformers.transformers_model import TransformersModel, TransformersModelConfig
    rows = selected(tasks, args.model, "shape")
    path = DIAG / f"shape-{args.model}-{args.mode}.jsonl"
    assert not path.exists(), "Do not overwrite diagnostics"
    config = TransformersModelConfig(model_name=protocol["models"][args.model]["location"],
        dtype="bfloat16",device="cuda",model_parallel=False,batch_size=1,max_length=2048,
        override_chat_template=False,add_special_tokens=False,pairwise_tokenization=True,
        multichoice_continuations_start_space=False,
        cache_dir=str(DIAG/"unused-cache"),model_loading_kwargs={"attn_implementation":"eager"})
    le = object.__new__(Backend)
    le.engine, le.model = "lighteval", backend.model
    le.adapter = TransformersModel.from_model(backend.model,config)
    le.tokenizer = le.adapter.tokenizer
    if args.mode == "fp32":
        assert args.model == "kanana2-3b", "27B full FP32 exceeds isolated GPU memory"
        backend.model.float()
    write(DIAG/f"settings-{args.model}-shape-{args.mode}.json",settings(backend.model))
    for row in rows:
        payload = tasks.request(row,"lighteval_full")[2]
        tokenized = tokens_for(backend.tokenizer,payload)
        result = {"model":args.model,"phase":"shape","mode":args.mode,"source_key":row["source_key"],
                  "tokens_sha256":digest(tokenized),"native_lighteval":native(le,tasks,row,"lighteval_full"),
                  "native_harness":native(backend,tasks,row,"aligned_harness_full"),"layouts":{}}
        for layout in ("batch_full","single_padded_full","single_full","single_omit","batch_omit"):
            result["layouts"][layout]=score_layout(backend.model,backend.tokenizer,tokenized,layout)
        append(path,result)
    print("SHAPE COMPLETE",flush=True)


def stress(args, tasks, backend):
    rows = selected(tasks, args.model, "repeat")
    path = DIAG / f"stress-{args.model}-{args.mode}.jsonl"
    assert not path.exists()
    backend.audit_original = True
    initial = buffers(backend.model)
    warmups = sorted(tasks.rows, key=lambda r: len(r["payload"]["query"]), reverse=True)[:12]
    for index, phase in enumerate(("cold_audited", "after_long_full", "after_empty_cache", "cudnn_deterministic", "cudnn_off")):
        if phase == "after_long_full":
            for row in warmups:
                native(backend,tasks,row,"aligned_harness_full")
        if phase == "after_empty_cache": torch.cuda.empty_cache()
        if phase == "cudnn_deterministic": torch.backends.cudnn.deterministic=True
        if phase == "cudnn_off": torch.backends.cudnn.enabled=False
        write(DIAG/f"stress-settings-{args.model}-{phase}.json",settings(backend.model))
        for row in rows:
            for condition in ("base_letter", "pr4420_letter"):
                result=native(backend,tasks,row,condition)
                append(path,{"model":args.model,"phase":phase,"pass":index,**result})
        after=buffers(backend.model)
        write(DIAG/f"stress-buffers-{args.model}-{phase}.json",{"changed":[k for k in initial if initial[k]!=after[k]]})
    print("STRESS COMPLETE",flush=True)


def exact_repeat(args, tasks, backend):
    rows=selected(tasks,args.model,"repeat")
    path=DIAG/f"exact-{args.model}-{args.mode}.jsonl"
    assert not path.exists()
    for index, phase in enumerate(("original_runner_first", "instrumented", "original_runner_second")):
        for row in rows:
            for condition in ("base_letter","pr4420_letter"):
                try:
                    result=(native(backend,tasks,row,condition) if phase=="instrumented"
                            else backend.score(tasks,row,condition,read(ROOT/"prepared/protocol.json")))
                    result={k:v for k,v in result.items() if k in ("scores","prediction","forward_audit","calls")}
                except Exception as error:
                    result={"error":repr(error)}
                append(path,{"model":args.model,"phase":phase,"pass":index,"source_key":row["source_key"],"condition":condition,**result})
        write(DIAG/f"exact-settings-{args.model}-{phase}.json",settings(backend.model))
    print("EXACT COMPLETE",flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("phase",choices=("repeat","shape","stress","exact"))
    parser.add_argument("--model",choices=("kanana2-3b","qwen38-27b"),required=True)
    parser.add_argument("--mode",choices=("default","cudnn_deterministic","cudnn_off","strict","no_reduced","fp32"),default="default")
    args=parser.parse_args()
    DIAG.mkdir(parents=True,exist_ok=True)
    lock=(ROOT/"results/gpu.lock").open("w");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ensure_idle()
    protocol=read(ROOT/"prepared/protocol.json");verify_run(protocol)
    tasks=Tasks();backend=Backend(args.model,"harness",protocol)
    if args.mode=="cudnn_deterministic":torch.backends.cudnn.deterministic=True
    if args.mode=="cudnn_off":torch.backends.cudnn.enabled=False
    if args.mode=="no_reduced":torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
    if args.mode=="strict":
        assert os.environ.get("CUBLAS_WORKSPACE_CONFIG")==":4096:8"
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic=True
    if args.phase=="repeat":repeat(args,tasks,backend)
    elif args.phase=="stress":stress(args,tasks,backend)
    elif args.phase=="exact":exact_repeat(args,tasks,backend)
    else:
        shape(args,tasks,backend,protocol)
        if args.model=="qwen38-27b" and args.mode=="default":exact_repeat(args,tasks,backend)


if __name__=="__main__":main()
