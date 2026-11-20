"""Re-score lm-evaluation-harness sample files after cutting each response at the stop strings.

Why: through an API the server may ignore some stop strings, so the response keeps going
(" C\n\nnext question ... A") and the harness filter then picks the LAST letter.
This script applies the same stop strings the task config lists, then the same answer
extraction as the kormedmcqa task (utils.py), and prints both scores.

Usage:  python rescore_harness.py <folder with samples_*.jsonl> [--out result.json]
"""
import argparse
import collections
import glob
import json
import os
import re

STOP = ["Q:", "</s>", "<|im_end|>", ".", "\n\n"]  # same as _template_yaml
PATTERNS = [
    re.compile(r"\uc815\ub2f5[:\s]*([ABCDE])", re.IGNORECASE),
    re.compile(r"\uc815\ub2f5\uc740\s*([ABCDE])\s*\uc785\ub2c8\ub2e4", re.IGNORECASE),
    re.compile(r"\b([ABCDE])\.", re.IGNORECASE),
    re.compile(r"\b([ABCDE])\b", re.IGNORECASE),
]


def cut(text):
    for s in STOP:
        text = text.split(s)[0]
    return text


def extract(text):
    for p in PATTERNS:
        m = p.findall(text)
        if m:
            return m[-1].upper()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.folder, "**", "*.jsonl"), recursive=True))
    if not files:
        raise SystemExit("no jsonl files found in " + a.folder)
    st = collections.defaultdict(lambda: {"n": 0, "harness": 0, "rescored": 0, "empty": 0, "cut_changed": 0})
    for f in files:
        m = re.search(r"samples_(.+?)_\d{4}-\d{2}-\d{2}T", os.path.basename(f))
        task = m.group(1) if m else os.path.basename(f)
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                subj = task
                raw = r["resps"][0][0]
                pred = extract(cut(raw))
                s = st[subj]
                s["n"] += 1
                s["harness"] += int(r["exact_match"])
                s["rescored"] += int(pred == r["target"])
                s["empty"] += int(pred == "")
                s["cut_changed"] += int(cut(raw) != raw)

    tot = collections.Counter()
    print("%-9s %5s %9s %9s %6s %12s" % ("subject", "n", "harness", "rescored", "empty", "cut_changed"))
    for k in sorted(st):
        s = st[k]
        print("%-9s %5d %9.4f %9.4f %6d %12d" % (k, s["n"], s["harness"] / s["n"], s["rescored"] / s["n"], s["empty"], s["cut_changed"]))
        tot.update(s)
    print("%-9s %5d %9.4f %9.4f %6d %12d" % ("ALL", tot["n"], tot["harness"] / tot["n"], tot["rescored"] / tot["n"], tot["empty"], tot["cut_changed"]))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump({"per_subject": st, "total": dict(tot)}, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
