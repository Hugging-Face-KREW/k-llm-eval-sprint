#!/usr/bin/env bash
# Run inside the prepared container. One process, one visible GPU, fail on any gate.
set -Eeuo pipefail

: "${POLYGLOT_PYTHON:=/workspace/.venv/bin/python}"
: "${POLYGLOT_OUTPUT:=/workspace/results}"
: "${POLYGLOT_LIGHTEVAL:=/workspace/sources/lighteval}"
: "${POLYGLOT_HARNESS:=/workspace/sources/lm-evaluation-harness}"
polyglot_code_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
polyglot_common=(--output-dir "$POLYGLOT_OUTPUT" --lighteval-root "$POLYGLOT_LIGHTEVAL" --harness-root "$POLYGLOT_HARNESS")
export NVIDIA_TF32_OVERRIDE=0
export PYTHONUNBUFFERED=1
export NLTK_DATA="${NLTK_DATA:-/workspace/cache/nltk_data}"
export PATH="/workspace/bin:$PATH"
export GIT_PYTHON_GIT_EXECUTABLE="${GIT_PYTHON_GIT_EXECUTABLE:-$(command -v git)}"

if [[ ! -f "$POLYGLOT_OUTPUT/prepared.json" ]]; then
  "$POLYGLOT_PYTHON" "$polyglot_code_dir/polyglot_compare.py" prepare "${polyglot_common[@]}"
fi
"$POLYGLOT_PYTHON" "$polyglot_code_dir/polyglot_smoke.py" "${polyglot_common[@]}" --device cuda

for polyglot_size in 1.3b 12.8b; do
  for polyglot_engine in lighteval harness reference; do
    "$POLYGLOT_PYTHON" "$polyglot_code_dir/polyglot_compare.py" run "${polyglot_common[@]}" --model-size "$polyglot_size" --engine "$polyglot_engine" --stage pilot
  done
  "$POLYGLOT_PYTHON" "$polyglot_code_dir/polyglot_compare.py" report "${polyglot_common[@]}" --model-size "$polyglot_size" --stage pilot
  for polyglot_engine in lighteval harness; do
    "$POLYGLOT_PYTHON" "$polyglot_code_dir/polyglot_compare.py" run "${polyglot_common[@]}" --model-size "$polyglot_size" --engine "$polyglot_engine" --stage full
  done
  "$POLYGLOT_PYTHON" "$polyglot_code_dir/polyglot_compare.py" report "${polyglot_common[@]}" --model-size "$polyglot_size" --stage full
done
