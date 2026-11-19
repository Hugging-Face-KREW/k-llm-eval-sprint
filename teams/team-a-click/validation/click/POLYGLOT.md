# CLIcK Polyglot 평가 재현

[완료된 결과](polyglot-matrix-results/README.md)를 재현하는 실행 코드와 환경 안내입니다.
기존 결과를 새 실행 결과로 덮어쓰지 않습니다. 실험별 상세 조건·고정 revision·해석의 한계는
[평가 조건](polyglot-matrix-results/PROTOCOL.md), 기존 정답 수는
[공개 집계](polyglot-matrix-results/results.json)에 있습니다.

## 두 평가 경로

| 경로 | 실행 명령 | 검증하는 내용 |
|---|---|---|
| 입력 정렬 비교 | `bash "$CLICK_CODE/polyglot_run.sh"` | 등록된 Lighteval 태스크와 별도로 작성한 `click_aligned_*` harness 태스크의 예측·후보 점수 일치 |
| harness 8조건 | `bash "$CLICK_CODE/polyglot_matrix_run.sh"` | 두 모델 × 기존/#4420 × 알파벳/전체 보기 채점의 결과 차이 |

입력 정렬 비교는 공백·보기 표시·채점 후보·파일별 분야 분류를 Lighteval에 맞춥니다.
원래 harness 태스크를 그대로 실행한 결과가 아닙니다. 8조건 중 `letter`는 각 revision의
원래 YAML·함수를 사용하고, `full`은 후보 문자열과 그에 필요한 정답 인덱스 대응만 바꿉니다.
8조건은 검증한 고정 원본을 로컬 JSON으로 전달하며 원래 분야 필터·요청·채점 함수를 유지합니다.
두 경로 모두 native Python API 평가이며, 전체 CLI 동등성이나 논문의 지시문 3종 × 보기 순환 재현을 뜻하지 않습니다.

| 파일 | 역할 |
|---|---|
| `polyglot_core.py`, `polyglot_backends.py`, `polyglot_compare.py` | 입력 정렬용 태스크, 실제 평가 도구 연결, 준비·실행·집계 |
| `polyglot_matrix_core.py`, `polyglot_matrix_native.py`, `polyglot_matrix.py` | 원래 태스크 스냅샷, 8조건 실행·집계 |
| `polyglot*_smoke.py`, `test_polyglot*.py` | 작은 무작위 모델 검산, 입력·정답·재시작·집계 회귀 검사 |
| `polyglot-environment.txt`, `polyglot_paper_reference.json` | 당시 설치 패키지 목록, 비교용 논문 Table 5 수치 |
| [코드 이력](polyglot-code-provenance.json) | 평가 당시와 공개 파일의 해시, 공개 과정에서 바뀐 실행 환경 설정 |

## 1. 전용 Docker 환경

Linux x86_64, NVIDIA Container Toolkit이 설정된 호스트와 **80GB급 GPU 한 장**이 필요합니다.
당시에는 `tailab:0.0.1` 이미지와 A100X 80GB를 사용했습니다. 아래 호스트 명령은 저장소 루트에서
실행합니다. `CLICK_GPU_INDEX`는 사용할 GPU로 지정하고 컨테이너 이름은 기존 실행과 겹치지 않게 합니다.

```bash
CLICK_SPRINT="$PWD"
CLICK_GPU_INDEX=3
CLICK_GPU_UUID=$(nvidia-smi -i "$CLICK_GPU_INDEX" --query-gpu=uuid --format=csv,noheader)
CLICK_WORK="$CLICK_SPRINT/teams/team-a-click/validation/click/local/polyglot-reproduction"
mkdir -p "$CLICK_WORK/tmp"
docker run -d --name click-polyglot-reproduction \
  --gpus "device=$CLICK_GPU_UUID" --user 0:0 \
  --mount "type=bind,src=$CLICK_SPRINT,dst=/workspace/code,readonly" \
  --mount "type=bind,src=$CLICK_WORK,dst=/workspace" \
  --env "POLYGLOT_GPU_UUID=$CLICK_GPU_UUID" \
  --entrypoint bash tailab:0.0.1 -lc 'exec sleep infinity'
docker exec -it click-polyglot-reproduction bash
```

이하 명령은 **컨테이너 안에서** 실행합니다. Git·uv·Python·평가 패키지는 컨테이너와 전용
마운트에 준비하며 호스트 전역 Python이나 드라이버를 변경하지 않습니다. `local/`은 이미 Git에서
제외한 경로입니다. 모델 두 개와 환경·캐시를 저장할 여유 공간을 확보합니다.

```bash
# tailab 이미지에 없는 준비 도구만 컨테이너 내부에 설치
apt-get update
apt-get install -y git ca-certificates
python3 -m pip install --target /workspace/bootstrap uv==0.13.7

cat > /workspace/repro-env.sh <<'ENV'
export PATH="/workspace/bootstrap/bin:/workspace/.venv/bin:$PATH"
export HF_HOME=/workspace/cache/huggingface
export NLTK_DATA=/workspace/cache/nltk_data
export UV_CACHE_DIR=/workspace/cache/uv
export UV_PYTHON_INSTALL_DIR=/workspace/python
export TMPDIR=/workspace/tmp
export PYTHONDONTWRITEBYTECODE=1
export GIT_LFS_SKIP_SMUDGE=1
export GIT_PYTHON_GIT_EXECUTABLE="$(command -v git)"
export CLICK_CODE=/workspace/code/teams/team-a-click/validation/click
export POLYGLOT_PYTHON=/workspace/.venv/bin/python
export POLYGLOT_LIGHTEVAL=/workspace/sources/lighteval
export POLYGLOT_HARNESS=/workspace/sources/lm-evaluation-harness
export POLYGLOT_OUTPUT=/workspace/results
export MATRIX_PYTHON="$POLYGLOT_PYTHON"
export MATRIX_HARNESS="$POLYGLOT_HARNESS"
export MATRIX_REVISIONS="$POLYGLOT_HARNESS"
export MATRIX_SNAPSHOTS=/workspace/sources/matrix-tasks
export MATRIX_OLD_OUTPUT="$POLYGLOT_OUTPUT"
export MATRIX_OUTPUT=/workspace/results-matrix
export MATRIX_TEST_HARNESS="$POLYGLOT_HARNESS"
export MATRIX_TEST_OLD="$POLYGLOT_OUTPUT"
export PYTHONPATH="$POLYGLOT_LIGHTEVAL/src:$POLYGLOT_HARNESS:$CLICK_CODE"
ENV
source /workspace/repro-env.sh
uv venv --python 3.12.16 /workspace/.venv
```

새 컨테이너 셸을 열 때마다 `source /workspace/repro-env.sh`를 실행합니다.

## 2. 소스와 설치 버전 고정

아래는 빈 `sources/` 디렉터리에서 한 번 실행합니다. 기존 checkout을 변경해서 재사용하지 않습니다.

```bash
mkdir -p /workspace/sources
git clone --no-checkout https://github.com/Hugging-Face-KREW/lighteval.git "$POLYGLOT_LIGHTEVAL"
git -C "$POLYGLOT_LIGHTEVAL" checkout --detach efb7e657802dd0d760473ffa9307063928ce4b41
git clone --no-checkout https://github.com/hyeongrae-kim/lm-evaluation-harness.git "$POLYGLOT_HARNESS"
git -C "$POLYGLOT_HARNESS" fetch origin \
  d6de81643928d653435c431bae19945d41d32520 \
  7a7b48afa7c294a5992008053bd1ec0042906c6d
git -C "$POLYGLOT_HARNESS" checkout --detach 7a7b48afa7c294a5992008053bd1ec0042906c6d

# 고정 Lighteval의 Hub API 호환성 수정: 평가 태스크·채점 로직은 변경하지 않음
python3 - <<'PY'
import os
from pathlib import Path
p = Path(os.environ['POLYGLOT_LIGHTEVAL']) / 'src/lighteval/metrics/metrics_sample.py'
s = p.read_text()
before = 'api.list_models(model_name=judge_model_name)'
assert s.count(before) == 1
p.write_text(s.replace(before, 'api.list_models(search=judge_model_name)'))
PY

uv pip install --python "$POLYGLOT_PYTHON" \
  -r "$CLICK_CODE/polyglot-environment.txt" \
  -e "$POLYGLOT_LIGHTEVAL" -e "$POLYGLOT_HARNESS[hf]"
uv pip check --python "$POLYGLOT_PYTHON"
"$POLYGLOT_PYTHON" -m nltk.downloader -d "$NLTK_DATA" punkt punkt_tab
```

`polyglot-environment.txt`는 Linux/Python 3.12/CUDA 12.6용 설치 목록으로 macOS용 requirements가 아닙니다.
모델·데이터 revision은 `polyglot_core.py`에 고정돼 있습니다. 모델 가중치는 실제 평가 시 받으며,
아래 `prepare`는 데이터·설정·토크나이저만 받습니다. Lighteval은 위 호환 패치 외의 tracked 변경을,
harness는 모든 tracked 변경을 거부합니다.

## 3. 준비와 검증 — Polyglot 가중치 추론 없음

```bash
"$POLYGLOT_PYTHON" "$CLICK_CODE/polyglot_compare.py" prepare \
  --output-dir "$POLYGLOT_OUTPUT" \
  --lighteval-root "$POLYGLOT_LIGHTEVAL" --harness-root "$POLYGLOT_HARNESS"
"$POLYGLOT_PYTHON" "$CLICK_CODE/polyglot_matrix.py" prepare \
  --output-dir "$MATRIX_OUTPUT" --old-output "$POLYGLOT_OUTPUT" \
  --harness-root "$MATRIX_HARNESS" --task-snapshots "$MATRIX_SNAPSHOTS" \
  --revision-repository "$MATRIX_REVISIONS"

"$POLYGLOT_PYTHON" -m pytest -q -o cache_dir=/workspace/cache/pytest \
  "$POLYGLOT_LIGHTEVAL/tests/unit/tasks/test_click.py" \
  "$CLICK_CODE/test_provenance.py" "$CLICK_CODE/test_polyglot.py" \
  "$CLICK_CODE/test_polyglot_matrix.py"
"$POLYGLOT_PYTHON" "$CLICK_CODE/polyglot_smoke.py" \
  --output-dir "$POLYGLOT_OUTPUT" --lighteval-root "$POLYGLOT_LIGHTEVAL" \
  --harness-root "$POLYGLOT_HARNESS" --device cpu
"$POLYGLOT_PYTHON" "$CLICK_CODE/polyglot_matrix_smoke.py" \
  --output-dir "$MATRIX_OUTPUT" --harness-root "$MATRIX_HARNESS" \
  --task-snapshots "$MATRIX_SNAPSHOTS" --revision-repository "$MATRIX_REVISIONS" --device cpu
```

`prepare`는 26파일·1,995행·중복 ID 보존·프롬프트·정답·토큰 경계·길이를 검사합니다.
두 번째 준비 단계는 첫 번째의 `prepared.json`·`inputs.jsonl`을 사용합니다.
8조건 평가만 재현할 때도 이 준비는 필요하지만, 첫 실험의 GPU 전체 평가까지 실행할 필요는 없습니다.
이미 준비한 폴더에서는 `prepare`를 반복하지 않습니다. 작은 무작위 모델의 smoke 점수는 benchmark 정확도가 아닙니다.

## 4. GPU 평가

필요한 경로를 하나씩 실행합니다. 두 명령을 동시에 실행하지 않습니다.

```bash
# A. Lighteval ↔ 입력 정렬용 harness: 두 모델의 파일럿과 전체 비교
bash "$CLICK_CODE/polyglot_run.sh"

# B. 원래 harness 태스크의 두 버전 × 두 채점 방식 × 두 모델
bash "$CLICK_CODE/polyglot_matrix_run.sh"
```

각 실행기는 GPU smoke → 모델별 파일럿 → 전체 평가 순서를 지킵니다.
파일럿은 calibration으로 허용오차를 정하고 겹치지 않는 validation으로 검증합니다.
예측·점수 검산 실패, 문항 누락·중복, 입력 잘림, 소스·환경 변경은 실행을 중단합니다.
8조건의 서로 다른 조건 사이 예측 차이는 측정 대상이며, 같은 입력인 4지선다의 버전 간 점수는 일치해야 합니다.

같은 코드·소스·환경에서 같은 명령을 다시 실행하면 검증된 행을 건너뜁니다.
잘린 JSON 행이나 변경된 결과는 자동 삭제하지 않습니다. 설정이나 코드가 바뀌면 **새 출력 디렉터리**에서
다시 준비해야 합니다. matrix 실행기는 같은 출력 폴더의 중복 실행을 잠금으로 차단합니다.

## 5. 산출물과 기존 결과 확인

| 출력 | 내용 |
|---|---|
| `results/<모델>/summary.json`, `categories.csv`, `report.md` | 입력 정렬 비교의 전체·분야별 정확도, 예측 일치, 점수 차이 |
| `results-matrix/<모델>/<조건>/summary.json` | 각 조건의 정확도·분야·4/5지선다·정답 E·예측 분포 |
| `results-matrix/<모델>/summary.json` | 조건별 집계와 조건 간 변화, 4지선다 일치 검사 |
| 각 출력의 `prepared.json`, 모델별 `protocol.json` | 입력·실행 코드·소스 해시, 환경·모델 revision |
| `inputs.jsonl`, `transport.jsonl`, `pilot-*.jsonl`, `full-*.jsonl` | 로컬 검증용 입력·문항별 결과. 출력 디렉터리 전체를 Git에 추가하지 않음 |

기존 결과는 아래와 같습니다. 주 지표는 길이 정규화 없는 `acc`, 분모는 모두 1,995입니다.

| 모델 | Lighteval / 입력 정렬 harness 각각 | base_letter | pr4420_letter | base_full | pr4420_full |
|---|---:|---:|---:|---:|---:|
| 1.3B | 599 | 573 | 568 | 596 | 595 |
| 12.8B | 499 | 477 | 478 | 488 | 487 |

하드웨어·라이브러리·코드 해시가 다르면 기존 실행과 동일한 기록으로 취급하지 않습니다.
이 공개본은 GPU UUID를 환경 변수로 받고 Git/NLTK 경로 설정을 정리했습니다.
태스크·점수 계산·파일럿·집계 코드는 그대로이며, 변경 파일의 전후 해시는
[코드 이력](polyglot-code-provenance.json)에 있습니다. 새 코드 해시로 생성한 출력은 과거 실행 폴더에 이어 쓸 수 없습니다.
