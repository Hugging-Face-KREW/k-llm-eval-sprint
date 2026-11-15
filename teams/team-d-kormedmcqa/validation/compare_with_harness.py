"""Compare a Lighteval KorMedMCQA run with an lm-evaluation-harness run, item by item.

Inputs are the Lighteval details file (`--save-details`) and the harness samples file
(`--log_samples`) for the same subset, model and settings. Items are matched by dataset
row index (Lighteval `doc.id`, harness `doc_id`), never by position, because Lighteval
shuffles documents before running them.

Run it with the Python environment of a Lighteval checkout that contains the KorMedMCQA task
(branch `team-d/kormedmcqa` of Hugging-Face-KREW/lighteval), because it imports `extract_choice` from there.

Usage:
    python teams/team-d-kormedmcqa/validation/compare_with_harness.py \
        --lighteval-details results/details/.../details_kormedmcqa:dentist|5_....parquet \
        --harness-samples results/.../samples_kormedmcqa_dentist_....jsonl \
        --tokenizer Qwen/Qwen2.5-1.5B-Instruct \
        --report dentist_parity.json

Exits with status 1 if any item differs.
"""

import argparse
import json
import math
import re
import sys

import pandas as pd
from transformers import AutoTokenizer

from lighteval.tasks.tasks.kormedmcqa import extract_choice


def load_harness(path: str) -> dict[int, dict]:
    with open(path, encoding="utf-8") as f:
        return {s["doc_id"]: s for s in map(json.loads, f)}


def stderr(acc: float, n: int) -> float:
    return math.sqrt(acc * (1 - acc) / (n - 1))


def letter_count(text: str) -> str:
    """Classify an output by how many distinct letters A-E it contains."""
    letters = set(re.findall(r"[A-E]", text))
    return "none" if not letters else "one" if len(letters) == 1 else "several"


def compare(details_path: str, samples_path: str, tokenizer_name: str) -> dict:
    df = pd.read_parquet(details_path)
    harness = load_harness(samples_path)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    if len(df) != len(harness):
        raise ValueError(f"Item counts differ: Lighteval {len(df)}, harness {len(harness)}")

    counts = dict.fromkeys(["prompt_text", "prompt_token_ids", "generation", "extracted", "score"], 0)
    letters = {"one": 0, "none": 0, "several": 0}
    fewshot_counts = set()
    mismatches = []

    for _, row in df.iterrows():
        doc, metric, response = row["doc"], row["metric"], row["model_response"]
        item_id = int(doc["id"])
        h = harness[item_id]

        input_ids = [int(t) for t in response["input_tokens"]]
        h_prompt = h["arguments"]["gen_args_0"]["arg_0"]
        l_text, h_text = list(response["text"])[0], h["resps"][0][0]

        checks = {
            "prompt_text": tokenizer.decode(input_ids) == h_prompt,
            "prompt_token_ids": input_ids == tokenizer(h_prompt)["input_ids"],
            "generation": l_text == h_text,
            "extracted": extract_choice(l_text) == h["filtered_resps"][0],
            "score": float(metric["em"]) == float(h["exact_match"]),
        }
        for key, ok in checks.items():
            counts[key] += ok
        if not all(checks.values()):
            mismatches.append({"id": item_id, **checks, "lighteval_text": l_text, "harness_text": h_text})

        letters[letter_count(l_text)] += 1
        fewshot_counts.add(len(doc["fewshot_samples"]))

    n = len(df)
    acc_l = sum(float(m["em"]) for m in df["metric"]) / n
    acc_h = sum(float(s["exact_match"]) for s in harness.values()) / n
    return {
        "task": df.iloc[0]["doc"]["task_name"],
        "items": n,
        "fewshot_counts": sorted(fewshot_counts),
        "same": counts,
        "accuracy": {
            "lighteval": acc_l,
            "harness": acc_h,
            "correct": round(acc_l * n),
            "stderr": stderr(acc_l, n),
        },
        "letters_in_output": letters,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lighteval-details", required=True, help="Parquet file from --save-details")
    parser.add_argument("--harness-samples", required=True, help="JSONL file from --log_samples")
    parser.add_argument("--tokenizer", required=True, help="Tokenizer of the evaluated model")
    parser.add_argument("--report", help="Optional path to write the full report as JSON")
    args = parser.parse_args()

    report = compare(args.lighteval_details, args.harness_samples, args.tokenizer)
    n, same, acc = report["items"], report["same"], report["accuracy"]

    print(f"{report['task']}: {n} items, few-shot examples per item: {report['fewshot_counts']}")
    for key, value in same.items():
        print(f"  same {key:<17} {value} / {n}")
    print(
        f"  accuracy  harness {acc['harness']:.4f}  lighteval {acc['lighteval']:.4f} "
        f"({acc['correct']}/{n}, stderr {acc['stderr']:.4f})"
    )
    print(f"  letters in output: {report['letters_in_output']}")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    if report["mismatches"]:
        print(f"  {len(report['mismatches'])} items differ, first: {report['mismatches'][0]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
