#!/usr/bin/env bash
# Execute only in the dedicated one-GPU environment. Stop on every failed gate.
set -Eeuo pipefail
: "${MATRIX_PYTHON:=/workspace/.venv/bin/python}"
: "${MATRIX_OUTPUT:=/workspace/results-matrix}"
: "${MATRIX_OLD_OUTPUT:=/workspace/results}"
: "${MATRIX_HARNESS:=/workspace/sources/lm-evaluation-harness}"
: "${MATRIX_SNAPSHOTS:=/workspace/sources/matrix-tasks}"
: "${MATRIX_REVISIONS:=/workspace/sources/matrix-revisions}"
: "${POLYGLOT_GPU_UUID:?Set POLYGLOT_GPU_UUID to the single GPU exposed to this run}"
export POLYGLOT_GPU_UUID
export PATH="/workspace/bin:$PATH"
export NLTK_DATA="${NLTK_DATA:-/workspace/cache/nltk_data}"
export GIT_PYTHON_GIT_EXECUTABLE="${GIT_PYTHON_GIT_EXECUTABLE:-$(command -v git)}"
# Hold one exclusive lock for prepare, smoke, and BOTH model runs, including resume.
if [[ "${MATRIX_LOCK_HELD:-0}" != 1 ]]; then
  exec "$MATRIX_PYTHON" - "$MATRIX_OUTPUT" "${BASH_SOURCE[0]}" <<'PY'
import fcntl
import os
import pathlib
import subprocess
import sys
output = pathlib.Path(sys.argv[1])
output.mkdir(parents=True, exist_ok=True)
with (output / '.matrix-run.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    sys.exit(subprocess.run(['bash', sys.argv[2]], env={**os.environ, 'MATRIX_LOCK_HELD': '1'}).returncode)
PY
fi
matrix_code_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
matrix_common=(--output-dir "$MATRIX_OUTPUT" --harness-root "$MATRIX_HARNESS" --task-snapshots "$MATRIX_SNAPSHOTS" --revision-repository "$MATRIX_REVISIONS")
export NVIDIA_TF32_OVERRIDE=0 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
if [[ ! -f "$MATRIX_OUTPUT/prepared.json" ]]; then
  "$MATRIX_PYTHON" "$matrix_code_dir/polyglot_matrix.py" prepare "${matrix_common[@]}" --old-output "$MATRIX_OLD_OUTPUT"
fi
"$MATRIX_PYTHON" "$matrix_code_dir/polyglot_matrix_smoke.py" "${matrix_common[@]}" --device cuda
for matrix_size in 1.3b 12.8b; do
  "$MATRIX_PYTHON" "$matrix_code_dir/polyglot_matrix.py" run "${matrix_common[@]}" --model-size "$matrix_size"
done
