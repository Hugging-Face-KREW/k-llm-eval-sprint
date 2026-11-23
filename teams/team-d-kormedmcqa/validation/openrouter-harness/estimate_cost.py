"""Estimate the token cost of the FINAL harness runs from the saved --log_samples files.

This is an ESTIMATE (token counts x list price), not the billed amount:
  - input tokens = tokenized prompt text (gpt: tiktoken o200k_base, message text only, no per-message overhead;
                   Llama: the unsloth Llama-3.1 tokenizer + 1 BOS token)
  - output tokens = tokenized stored response text
  - retries (e.g. DeepInfra 429 errors) and any provider-side token accounting differences are not included
Prices are the OpenRouter model-page list prices read on 2026-11-20 (USD per 1M tokens); edit PRICES if they changed.

Usage (needs:  pip install tiktoken):
  python estimate_cost.py --gpt results-harness-gpt-stop --llama results-harness-llama-final [--out cost.json]
"""
import argparse
import glob
import json
import os
import re

PRICES = {  # USD per 1M tokens: (input, output)
    "gpt": (0.15, 0.60),    # openai/gpt-4o-mini (OpenAI / Azure list price on OpenRouter)
    "llama": (0.02, 0.04),  # meta-llama/llama-3.1-8b-instruct, DeepInfra list price on OpenRouter
}


def latest_per_task(folder):
    files = glob.glob(os.path.join(folder, "**", "samples_*.jsonl"), recursive=True)
    best = {}
    for f in files:
        m = re.search(r"samples_(.+?)_(\d{4}-\d{2}-\d{2}T[\d\-\.]+)\.jsonl$", os.path.basename(f))
        if not m:
            continue
        task, ts = m.group(1), m.group(2)
        if task not in best or ts > best[task][0]:
            best[task] = (ts, f)
    return {t: f for t, (ts, f) in best.items()}, len(files)


def prompt_text(arg0):
    """arg_0 can be a plain string, a JSON string of chat messages, or a list of such items."""
    if isinstance(arg0, str):
        try:
            v = json.loads(arg0)
        except ValueError:
            return arg0
        if isinstance(v, (list, dict)):
            return prompt_text(v)
        return arg0
    if isinstance(arg0, dict):
        c = arg0.get("content", "")
        return c if isinstance(c, str) else prompt_text(c)
    if isinstance(arg0, list):
        return "\n".join(prompt_text(x) for x in arg0)
    return str(arg0)


def read_samples(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            try:
                arg0 = r["arguments"]["gen_args_0"]["arg_0"]
            except (KeyError, TypeError):
                raise SystemExit("unexpected sample format, keys: %s / arguments: %s" % (list(r), str(r.get("arguments"))[:200]))
            yield prompt_text(arg0), r["resps"][0][0]


def run(folder, count, label):
    tasks, nfiles = latest_per_task(folder)
    if not tasks:
        raise SystemExit("no samples_*.jsonl in " + folder)
    tin = tout = n = 0
    per = {}
    for task, f in sorted(tasks.items()):
        i = o = c = 0
        for p, resp in read_samples(f):
            i += count(p, True)
            o += count(resp, False)
            c += 1
        per[task] = {"file": os.path.basename(f), "n": c, "input_tokens": i, "output_tokens": o}
        tin += i
        tout += o
        n += c
    pi, po = PRICES[label]
    cost = tin / 1e6 * pi + tout / 1e6 * po
    print("%s: files found %d, used %d (newest per task)" % (label, nfiles, len(tasks)))
    for t, v in per.items():
        print("  %-26s n=%4d in=%9d out=%9d" % (t, v["n"], v["input_tokens"], v["output_tokens"]))
    print("  TOTAL n=%d input=%d output=%d  -> estimated USD %.4f (price in/out per 1M: %s/%s)" % (n, tin, tout, cost, pi, po))
    return {"n": n, "input_tokens": tin, "output_tokens": tout, "price_usd_per_1m": {"input": pi, "output": po},
            "estimated_usd": round(cost, 4), "per_task": per}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpt", required=True)
    ap.add_argument("--llama", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("unsloth/Llama-3.1-8B-Instruct")

    res = {
        "gpt-4o-mini": run(a.gpt, lambda t, is_in: len(enc.encode(t, disallowed_special=())), "gpt"),
        "llama-3.1-8b-instruct": run(a.llama, lambda t, is_in: len(tok.encode(t, add_special_tokens=is_in)), "llama"),
    }
    print("\nESTIMATE ONLY (token counts x list price). Total: USD %.4f" % sum(v["estimated_usd"] for v in res.values()))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)


if __name__ == "__main__":
    main()
