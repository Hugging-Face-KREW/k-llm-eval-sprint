"""Random tiny Qwen3 GPU adapter smoke; never benchmark accuracy."""

import argparse
import json

from vllm_click import CONDITIONS, ROOT, Backend, Tasks, digest, read, require, write


def validate():
    reference = read(ROOT / "smoke/reference.json")
    measured = {
        **read(ROOT / "smoke/lighteval.json"),
        **read(ROOT / "smoke/harness.json"),
    }
    checks = []
    for condition in CONDITIONS:
        require(
            len(measured[condition]) == len(reference[condition]) == 2, "Smoke coverage"
        )
        for left, right in zip(measured[condition], reference[condition], strict=True):
            require(
                all(
                    left[k] == right[k]
                    for k in ("source_key", "payload_sha256", "tokens_sha256")
                ),
                "Smoke inputs differ",
            )
            delta = max(
                abs(a - b) for a, b in zip(left["scores"], right["scores"], strict=True)
            )
            # A small randomly initialized model checks adapter plumbing; the real
            # model has a separate calibration/validation tolerance and gate.
            require(
                delta < 0.1 and left["prediction"] == right["prediction"],
                "Smoke reference mismatch",
            )
            checks.append(
                {
                    "condition": condition,
                    "source_key": left["source_key"],
                    "max_abs_diff": delta,
                }
            )
    for left, right in zip(
        measured["lighteval_full"], measured["aligned_harness_full"], strict=True
    ):
        require(
            left["tokens_sha256"] == right["tokens_sha256"]
            and left["prediction"] == right["prediction"],
            "Smoke aligned mismatch",
        )
        require(
            max(
                abs(a - b) for a, b in zip(left["scores"], right["scores"], strict=True)
            )
            <= 1e-6,
            "Smoke adapter score mismatch",
        )
    write(
        ROOT / "smoke/validated.json",
        {
            "passed": True,
            "checks": checks,
            "outputs_sha256": digest(measured),
            "reference_sha256": digest(reference),
        },
    )
    print("Random-model GPU adapter smoke passed; no benchmark score", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "engine", choices=("create", "reference", "lighteval", "harness", "validate")
    )
    args = parser.parse_args()
    if args.engine == "validate":
        validate()
        return
    protocol = read(ROOT / "prepared/protocol.json")
    location = ROOT / "smoke/model"
    if args.engine == "create":
        import torch
        from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM

        torch.manual_seed(1234)
        tokenizer = AutoTokenizer.from_pretrained(
            protocol["models"]["kanana2-3b"]["location"]
        )
        config = Qwen3Config(
            vocab_size=len(tokenizer),
            hidden_size=512,
            intermediate_size=1024,
            num_hidden_layers=2,
            num_attention_heads=4,
            num_key_value_heads=2,
            head_dim=128,
            max_position_embeddings=2049,
            bos_token_id=tokenizer.bos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
        model = Qwen3ForCausalLM(config).to(torch.bfloat16).eval()
        model.save_pretrained(location)
        tokenizer.save_pretrained(location)
        print("Created random tiny Qwen3", flush=True)
        return
    protocol["models"]["smoke"] = {"location": str(location)}
    protocol["gpu_memory_utilization"] = 0.10
    condition = "lighteval_full" if args.engine == "lighteval" else "harness"
    backend = Backend("smoke", condition, args.engine == "reference", protocol)
    tasks = Tasks()
    rows = [
        next(r for r in tasks.rows if len(r["raw"]["choices"]) == n) for n in (4, 5)
    ]
    conditions = (
        CONDITIONS
        if args.engine == "reference"
        else CONDITIONS[:1]
        if args.engine == "lighteval"
        else CONDITIONS[1:]
    )
    outputs = {}
    for c in conditions:
        outputs[c] = [backend.score(tasks, r, c, protocol) for r in rows]
    write(ROOT / f"smoke/{args.engine}.json", outputs)
    print(
        json.dumps(
            {
                "smoke_engine": args.engine,
                "conditions": list(conditions),
                "items_each": 2,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
