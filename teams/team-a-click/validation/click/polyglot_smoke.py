"""Exercise all native adapters with a tiny random model, never a benchmark score."""

import argparse
from pathlib import Path

from polyglot_compare import prepared_inputs, setup_sources
from polyglot_core import MODELS, digest, require, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(".polyglot/results"))
    parser.add_argument(
        "--lighteval-root", type=Path, default=Path(".polyglot/sources/lighteval")
    )
    parser.add_argument(
        "--harness-root",
        type=Path,
        default=Path(".polyglot/sources/lm-evaluation-harness"),
    )
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    setup_sources(args)
    prepared, records = prepared_inputs(args.output_dir)

    import torch
    from polyglot_backends import Backend, configure_torch
    from transformers import AutoTokenizer, GPTNeoXConfig, GPTNeoXForCausalLM

    configure_torch()
    torch.set_num_threads(4)
    repo, revision = MODELS["1.3b"]
    tokenizer = AutoTokenizer.from_pretrained(
        repo, revision=revision, trust_remote_code=False
    )
    selected = []
    for count, has_context in ((4, False), (4, True), (5, False), (5, True)):
        candidates = [
            r
            for r in records
            if r["num_choices"] == count
            and bool(r["raw"]["paragraph"].strip()) == has_context
        ]
        selected.append(
            min(candidates, key=lambda r: r["models"]["1.3b"]["max_tokens"])
        )
    selected.append(
        min(
            (r for r in records if r["gold_index"] == 4),
            key=lambda r: r["models"]["1.3b"]["max_tokens"],
        )
    )
    selected = list({r["source_key"]: r for r in selected}.values())
    engines = {}
    for engine in ("reference", "lighteval", "harness"):
        torch.manual_seed(1234)
        config = GPTNeoXConfig(
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
        config._attn_implementation = "eager"
        model = GPTNeoXForCausalLM(config).float()
        backend = Backend(
            engine,
            "1.3b",
            args.output_dir,
            model=model,
            tokenizer=tokenizer,
            device=args.device,
        )
        values = {}
        for row in selected:
            scores, correct, tokens = backend.score(row, row["payload"])
            require(
                digest(tokens) == row["models"]["1.3b"]["tokens_sha256"],
                "Smoke tokenization differs",
            )
            values[row["source_key"]] = {
                "scores": scores,
                "correct": correct,
                "prediction": max(range(len(scores)), key=lambda i: scores[i]),
            }
        engines[engine] = values
        del backend, model
        if args.device == "cuda":
            torch.cuda.empty_cache()
    maximum = 0.0
    for row in selected:
        values = [engine[row["source_key"]] for engine in engines.values()]
        require(
            len({(v["correct"], v["prediction"]) for v in values}) == 1,
            "Smoke prediction/metric mismatch",
        )
        maximum = max(
            maximum, max(max(s) - min(s) for s in zip(*(v["scores"] for v in values)))
        )
    require(maximum <= 1e-4, "Random-model native score mismatch")
    result = {
        "status": "PASS",
        "purpose": "Random tiny GPTNeoX adapter smoke; not Polyglot accuracy or a calibration gate",
        "device": args.device,
        "items": len(selected),
        "max_abs_diff": maximum,
        "prepared_sha256": digest(prepared),
    }
    write_json(args.output_dir / "smoke.json", result)
    print(result)


if __name__ == "__main__":
    main()
