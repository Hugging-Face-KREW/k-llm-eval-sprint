"""Random GPTNeoX native HFLM versus independent forward; never benchmark accuracy."""

import argparse
from collections import Counter
from pathlib import Path

from polyglot_core import MODELS, digest, require, write_json
from polyglot_matrix import inputs
from polyglot_matrix_core import CONDITIONS
from polyglot_matrix_native import MatrixBackend


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--harness-root", type=Path, required=True)
    parser.add_argument("--task-snapshots", type=Path, required=True)
    parser.add_argument("--revision-repository", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    prepared, rows, tasks = inputs(args)
    import torch
    from polyglot_backends import configure_torch
    from transformers import AutoTokenizer, GPTNeoXConfig, GPTNeoXForCausalLM

    configure_torch()
    torch.set_num_threads(4)
    counts = Counter(r["original_id"] for r in rows)
    predicates = [
        (
            lambda r, n=n, ctx=ctx: (
                len(r["raw"]["choices"]) == n and bool(r["raw"]["paragraph"]) == ctx
            )
        )
        for n in (4, 5)
        for ctx in (False, True)
    ]
    predicates += [
        lambda r: r["raw"]["choices"].index(r["raw"]["answer"]) == 4,
        lambda r: counts[r["original_id"]] > 1,
        lambda r: r["variants"]["base_letter"]["native_category"] != r["category"],
    ]
    selected = {}
    for predicate in predicates:
        candidates = [r for r in rows if predicate(r)]
        require(candidates, "Missing smoke stratum")
        row = min(
            candidates,
            key=lambda r: r["variants"]["pr4420_full"]["models"]["1.3b"]["max_tokens"],
        )
        selected[row["source_key"]] = row
    duplicate_ids = {
        r["original_id"] for r in selected.values() if counts[r["original_id"]] > 1
    }
    for row in rows:
        if row["original_id"] in duplicate_ids:
            selected[row["source_key"]] = row
    repo, revision = MODELS["1.3b"]
    tokenizer = AutoTokenizer.from_pretrained(
        repo, revision=revision, trust_remote_code=False
    )
    cfg = GPTNeoXConfig(
        vocab_size=len(tokenizer),
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=1,
        num_attention_heads=4,
        max_position_embeddings=2048,
        rotary_pct=0.5,
        attention_dropout=0.0,
        hidden_dropout=0.0,
    )
    cfg._attn_implementation = "eager"
    backend = MatrixBackend(
        "1.3b",
        tasks,
        model=GPTNeoXForCausalLM(cfg).float(),
        tokenizer=tokenizer,
        device=args.device,
    )
    maximum = 0.0
    evidence = []
    for condition in CONDITIONS:
        for row in selected.values():
            native, metrics, tokens = backend.score(row, condition)
            reference, reference_metrics, reference_tokens = backend.score(
                row, condition, reference=True
            )
            require(
                digest(tokens)
                == digest(reference_tokens)
                == row["variants"][condition]["models"]["1.3b"]["tokens_sha256"],
                "Smoke token trace differs",
            )
            delta = max(abs(a - b) for a, b in zip(native, reference, strict=True))
            require(
                metrics == reference_metrics
                and max(range(len(native)), key=lambda i: native[i])
                == max(range(len(reference)), key=lambda i: reference[i]),
                "Smoke prediction/metric differs",
            )
            maximum = max(maximum, delta)
            evidence.append(
                {
                    "condition": condition,
                    "source_key": row["source_key"],
                    "max_abs_diff": delta,
                }
            )
    require(maximum <= 1e-4, "Random model native score mismatch")
    result = {
        "status": "PASS",
        "purpose": "random-model adapter check, not model accuracy or model calibration",
        "device": args.device,
        "items_per_condition": len(selected),
        "conditions": 4,
        "max_abs_diff": maximum,
        "prepared_sha256": digest(prepared),
        "evidence": evidence,
    }
    write_json(args.output_dir / "smoke.json", result)
    print(result, flush=True)


if __name__ == "__main__":
    main()
