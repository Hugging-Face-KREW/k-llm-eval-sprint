"""CLIcK FP32 parity run of the native Transformers adapters on two isolated GPUs.

transformers_click is reused unchanged: native Lighteval/harness adapters,
ForwardAudit, Backend.score, run(), row identities, row hashes and resume checks.
Only three things differ: the BF16 checkpoint is loaded as FP32 (lossless
upcast), Qwen is split over two GPUs, and four of the six conditions run.
"""

import argparse
import collections
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

import transformers_click as tc
from transformers_run import status
from vllm_click import CONDITIONS as ALL_CONDITIONS
from vllm_click import (
    MODELS,
    ROOT,
    compare_files,
    digest,
    file_hash,
    lines,
    read,
    require,
    write,
)

CONDITIONS = ALL_CONDITIONS[:4]  # lighteval_full + aligned/base/pr4420 harness
RUN_ID = "transformers-fp32-20261122"
GPUS = (
    {
        "cuda_index": 0,
        "host_index": 0,
        "uuid": "GPU-ce8035fc-8017-2110-4d02-346079b8ab7d",
    },
    {
        "cuda_index": 1,
        "host_index": 1,
        "uuid": "GPU-4d10fa0e-f11b-ca93-a51d-bea42af0dfaa",
    },
)
PLACEMENT = {
    "kanana2-3b": {"device": "cuda:0"},
    # Sequential fill: at most 50GiB of weights on cuda:0, the rest (lm_head
    # included) on cuda:1. Both keep headroom: logits are computed on cuda:1 and
    # accelerate copies them back to the input device (cuda:0) for log_softmax.
    "qwen38-27b": {
        "device_map": "sequential",
        "max_memory": {"0": "50GiB", "1": "70GiB"},
    },
}
RUNNER_FILES = (
    "transformers_click.py",
    "transformers_fp32.py",
    "transformers_run.py",
    "vllm_click.py",
    "vllm_run.py",
    "test_transformers_click.py",
    "test_transformers_fp32.py",
)
FP32 = "torch.float32"


def load_kwargs(placement):
    """from_pretrained placement kwargs, and the device to move to afterwards."""
    if "device" in placement:
        return {}, placement["device"]
    memory = {int(k): v for k, v in placement["max_memory"].items()}
    return {"device_map": placement["device_map"], "max_memory": memory}, None


def check_devices(gpus, uuids):
    expected = [g["uuid"] for g in sorted(gpus, key=lambda g: g["cuda_index"])]
    require(uuids == expected, f"CUDA devices differ from protocol: {uuids}")


def cuda_uuids():
    import torch

    names = (
        str(torch.cuda.get_device_properties(i).uuid)
        for i in range(torch.cuda.device_count())
    )
    return [n if n.startswith("GPU-") else "GPU-" + n for n in names]


def placement_record(model, device):
    sizes = collections.Counter()
    for p in model.parameters():
        sizes[str(p.device)] += p.numel() * p.element_size()
    require(
        all(d.startswith("cuda:") for d in sizes), f"Weights off GPU: {dict(sizes)}"
    )
    device_map = {"": device} if device else model.hf_device_map
    return {
        "device_map": {k: str(v) for k, v in device_map.items()},
        "parameter_bytes_by_device": dict(sorted(sizes.items())),
        "parameter_dtypes": dict(
            collections.Counter(str(p.dtype) for p in model.parameters())
        ),
        "buffer_dtypes": dict(
            collections.Counter(str(b.dtype) for b in model.buffers())
        ),
    }


def require_fp32(row):
    audit = row["forward_audit"]
    require(
        audit["passed"] and audit["logits_dtype"] == FP32 == audit["sum_dtype"],
        "Scored logits are not FP32",
    )


class Backend(tc.Backend):
    """tc.Backend with FP32 weights and protocol placement; score() is inherited."""

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
        uuids = cuda_uuids()
        check_devices(protocol["gpus"], uuids)
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
        kwargs, device = load_kwargs(protocol["placement"][name])
        started = time.time()
        # Lossless BF16 -> FP32 upcast at load; no autocast or quantization.
        self.model = loader.from_pretrained(
            info["location"],
            dtype=torch.float32,
            attn_implementation="eager",
            trust_remote_code=False,
            **kwargs,
        )
        if device:
            self.model = self.model.to(device)
        self.model.eval()
        dtypes = collections.Counter(str(p.dtype) for p in self.model.parameters())
        require(set(dtypes) == {FP32}, f"Weights are not all FP32: {dtypes}")
        record = placement_record(self.model, device)
        folder = ROOT / "results" / name / "runtime"
        for previous in sorted(folder.glob("*.json")):
            require(
                read(previous)["device_map"] == record["device_map"],
                "Device placement changed between processes",
            )
        if engine == "lighteval":
            from lighteval.models.transformers.transformers_model import (
                TransformersModel,
                TransformersModelConfig,
            )

            config = TransformersModelConfig(
                model_name=info["location"],
                dtype="float32",
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
                dtype="float32",
                softmax_dtype=None,
                batch_size=1,
                max_length=protocol["context_limit"],
                add_bos_token=False,
                logits_cache=False,
                truncation=False,
            )
        now = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.runtime_path = folder / f"{now}-{engine}.json"
        self.runtime = {
            "argv": sys.argv,
            "started_utc": now,
            "load_s": round(time.time() - started, 1),
            "cuda_uuids": uuids,
            "adapter_device": str(self.adapter.device),
            **record,
            "items": {},
            "seconds": {},
        }
        write(self.runtime_path, self.runtime)

    def score(self, tasks, row, condition, protocol):
        import torch

        started = time.time()
        result = super().score(tasks, row, condition, protocol)
        require_fp32(result)
        seconds = self.runtime["seconds"]
        seconds[condition] = round(seconds.get(condition, 0) + time.time() - started, 3)
        self.runtime["items"][condition] = self.runtime["items"].get(condition, 0) + 1
        count = torch.cuda.device_count()
        self.runtime["peak_allocated_bytes"] = [
            torch.cuda.max_memory_allocated(i) for i in range(count)
        ]
        self.runtime["peak_reserved_bytes"] = [
            torch.cuda.max_memory_reserved(i) for i in range(count)
        ]
        write(self.runtime_path, self.runtime)
        return result


def run(args):
    # tc.run looks up Backend and CONDITIONS as module globals. Swapping them is
    # the whole change; prompts, batching, audits and resume checks are tc.run's.
    tc.Backend, tc.CONDITIONS = Backend, CONDITIONS
    tc.run(args)


def validated(path, protocol, expected_count=None):
    rows = tc.validate_rows(path, protocol, expected_count)
    for row in rows:
        require_fp32(row)
    return rows


def four_choice(keys):
    original = {
        r["source_key"]: r for r in lines(ROOT / "prepared/old-aligned-inputs.jsonl")
    }
    return [k for k in keys if len(original[k]["raw"]["choices"]) == 4]


def comparisons(folder, stage, keys):
    results = []
    for left, right, selected in (
        ("lighteval_full", "aligned_harness_full", keys),
        ("base_letter", "pr4420_letter", four_choice(keys)),
    ):
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
    tc.verify_run(protocol)
    samples = protocol["models"][name]["samples"]
    keys = sorted(set(samples["calibration"] + samples["validation"]))
    folder = ROOT / "results" / name
    for condition in CONDITIONS:
        rows = validated(
            folder / f"pilot-transformers-{condition}.jsonl", protocol, len(keys)
        )
        require({r["source_key"] for r in rows} == set(keys), "Wrong pilot coverage")
    checks = comparisons(folder, "pilot", keys)
    result = {
        "input_and_scoring_audit_passed": True,
        "fp32_audit_passed": True,
        "prediction_parity": all(c["prediction_parity"] for c in checks),
        "comparisons": checks,
        "protocol_sha256": digest(protocol),
        "policy": "Same as BF16: full run requires valid input, native score and FP32 audits; cross-adapter parity is measured, not required.",
    }
    write(folder / "pilot-gate.json", result)
    print(json.dumps(result, indent=2), flush=True)


def occupied(apps_csv, memory_csv, uuids):
    """nvidia-smi rows showing a process, or >1GiB used, on our GPUs."""
    busy = [r for r in apps_csv.splitlines() if r.split(",")[0].strip() in uuids]
    for r in memory_csv.splitlines():
        uuid, used = (x.strip() for x in r.split(","))
        if uuid in uuids and int(used) > 1024:
            busy.append(r)
    return busy


def wait_idle(uuids, timeout=1800):
    deadline = time.monotonic() + timeout
    while True:
        query = ["nvidia-smi", "--format=csv,noheader,nounits"]
        busy = occupied(
            subprocess.check_output(
                query + ["--query-compute-apps=gpu_uuid,pid,used_memory"], text=True
            ),
            subprocess.check_output(
                query + ["--query-gpu=uuid,memory.used"], text=True
            ),
            uuids,
        )
        if not busy:
            return
        require(
            time.monotonic() < deadline,
            f"GPUs stayed occupied; no other process is stopped: {busy}",
        )
        status("WAITING_GPU", occupied=busy)
        time.sleep(10)


def step(model, stage, engine, uuids):
    key = f"{model}-{stage}" + (f"-{engine}" if engine else "")
    command = [sys.executable, str(ROOT / "code/transformers_fp32.py")]
    if engine:
        wait_idle(uuids)
        command += ["run", "--model", model, "--stage", stage, "--engine", engine]
    else:
        command += ["gate", "--model", model]
    logfile = ROOT / "logs" / f"{key}.log"
    status("RUNNING", model=model, stage=stage, engine=engine, log=str(logfile))
    started = time.time()
    with logfile.open("a") as stream:
        code = subprocess.run(
            command, stdout=stream, stderr=subprocess.STDOUT, check=False
        ).returncode
    with (ROOT / "results/steps.jsonl").open("a") as stream:
        stream.write(
            json.dumps(
                {
                    "step": key,
                    "started_utc": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)
                    ),
                    "elapsed_s": round(time.time() - started, 1),
                    "exit": code,
                }
            )
            + "\n"
        )
    require(code == 0, f"{key} exited {code}; see {logfile}")
    status("STEP_COMPLETE", model=model, stage=stage, engine=engine)


def control(through):
    lock = (ROOT / "results/controller.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = read(ROOT / "prepared/protocol.json")
    tc.verify_run(protocol)
    uuids = {g["uuid"] for g in protocol["gpus"]}
    stages = ("probe",) if through == "probe" else ("probe", "pilot")
    for model in MODELS:  # kanana2-3b, then qwen38-27b
        for stage in stages:
            for engine in ("lighteval", "harness"):
                step(model, stage, engine, uuids)
        if through == "full":
            step(model, "pilot-gate", None, uuids)
            for engine in ("lighteval", "harness"):
                step(model, "full", engine, uuids)
    status("PROBES_COMPLETE" if through == "probe" else "INFERENCE_COMPLETE")


def prepare():
    path = ROOT / "prepared/protocol.json"
    require(not path.exists(), "Protocol already frozen")
    parent_path = ROOT / "prepared/parent-bf16-protocol.json"
    parent = read(parent_path)
    require(parent["run_id"] == "transformers-bf16-20261120", "Unexpected parent")
    require(
        file_hash(ROOT / "environment/packages.txt") == parent["packages_sha256"],
        "Package list changed",
    )
    for name in MODELS:
        manifest_path = ROOT / "environment" / f"model-{name}.json"
        require(
            file_hash(manifest_path) == parent["model_manifest_sha256"][name],
            f"Model manifest changed: {name}",
        )
        location = Path(parent["models"][name]["location"])
        for relative, meta in read(manifest_path)["files"].items():
            require(
                file_hash(location / relative) == meta["sha256"],
                f"Model file changed: {name}/{relative}",
            )
    protocol = {
        k: v for k, v in parent.items() if k not in ("host_gpu_index", "gpu_uuid")
    }
    protocol.update(
        run_id=RUN_ID,
        dtype="float32",
        checkpoint_dtype="bfloat16",
        weight_loading="from_pretrained(dtype=torch.float32): lossless BF16->FP32 upcast; all parameters and scored logits FP32",
        float32_matmul_precision="highest",
        conditions=list(CONDITIONS),
        container="click-fp32-20261122",
        storage="/mnt/sdb/hyeongrae-click-vllm-20261120/" + RUN_ID,
        gpus=list(GPUS),
        placement=PLACEMENT,
        model_files_verified_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        parent_protocol_sha256=digest(parent),
        parent_protocol_file_sha256=file_hash(parent_path),
        runner_files={n: file_hash(ROOT / "code" / n) for n in RUNNER_FILES},
    )
    tc.verify_run(protocol)
    write(path, protocol)
    print(json.dumps({"protocol_sha256": digest(protocol)}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "run", "gate", "control"))
    parser.add_argument("--model", choices=MODELS)
    parser.add_argument("--engine", choices=("lighteval", "harness"))
    parser.add_argument("--stage", choices=("probe", "pilot", "full"), default="probe")
    parser.add_argument("--through", choices=("probe", "full"), default="probe")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "control":
        try:
            control(args.through)
        except Exception as error:
            status("STOPPED", reason=str(error))
            raise
    else:
        require(args.model is not None, "Choose a model")
        if args.action == "gate":
            gate(args.model)
        else:
            require(args.engine is not None, "Choose native engine")
            run(args)


if __name__ == "__main__":
    main()
