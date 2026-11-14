# CLIcK 데이터와 프롬프트 검증

2026-11-12: **lm-evaluation-harness**로 Polyglot-Ko 1.3B·12.8B의 태스크 버전 × 채점 방식 8개 전체 평가를 완료했습니다.
[통합 비교와 조건별 상세 보고서](polyglot-matrix-results/README.md)에서 결과·평가 조건·검증 범위를 확인할 수 있습니다.
8개 결과는 모두 lm-evaluation-harness 결과이며, Lighteval 수치는 이전 실행 참고값으로 따로 표시합니다.

이전 **Lighteval ↔ 입력을 정렬한 lm-evaluation-harness** 비교도 2026-11-11 전체 평가를 통과했습니다.
[통합 보고서의 이전 실행 참고값](polyglot-matrix-results/README.md)에 두 도구의 결과를 각각 표시했습니다.
아래의 기존 `results.json`은 데이터·프롬프트 검증 결과이며 모델 정확도 결과가 아닙니다.

2026-11-06 기준으로 `@GeonRyoung` 담당인 분야별 파일 목록·데이터 검사·추적 연결과
prompt function·입력 단위 테스트를 구현했습니다. [설계 문서](../../design.md)의
U01–U07, D01–D03을 대상으로 합니다.

## 코드와 검증 자료

이하의 태스크 구현·데이터·프롬프트 검증은 **Lighteval**에 관한 설명입니다.
해당 태스크 코드는 Lighteval 커밋 `efb7e657802dd0d760473ffa9307063928ce4b41`에 있습니다.
문서와 코드 모두 `docs/week5-basicfive` 브랜치를 사용합니다.

| 산출물 | 위치와 역할 |
| --- | --- |
| 분야별 파일 목록·프롬프트 | Lighteval `src/lighteval/tasks/tasks/click.py`의 `CATEGORY_FILES`, `build_click_payload`, `click_prompt` |
| 입력 단위 테스트 | Lighteval `tests/unit/tasks/test_click.py`, 합성 문항 입력 테스트 70개(파일 전체 76개) |
| 원본 파일·행 목록 | [manifest.json](manifest.json): 파일 SHA-256·행 수, 각 행의 경로·0-based 번호·ID·내용 해시 |
| 추적 연결 | [provenance.py](provenance.py): 원본과 Doc/저장 로그의 일대일 연결 및 출현 횟수 검사 |
| 추적 오류 단위 테스트 | [test_provenance.py](test_provenance.py): 합성 데이터 20개 테스트 케이스 |
| 실제 데이터 검사 명령 | [validate.py](validate.py): 고정 원본·HF 로더·Lighteval 저장 로그 검사 |
| 실행 결과 | [results.json](results.json): 실제 버전·코드 해시·분야별 검사 결과, 원문 미포함 |

팀 포크 베이스는 `team-a/kmmlu`에 있던 `c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14`이며,
팀 공동 승인이나 업스트림 제출 기준 확정을 뜻하지 않습니다. 이전 설계의 분석 당시 SHA와 구분합니다.
현재 `results.json`은 v3 구현 커밋 `efb7e65`에서 실행한 결과이고, 이전 v2 구현은 `be429ad`입니다.
데이터는 `EunsuKim/CLIcK`의 `d61627859645b5e6edc03fd9f835735d8226fa4e`로 고정했습니다.

## 검사 결과

| 검사 | 결과 |
| --- | --- |
| U01–U07 | 70개 통과. 4·5지선다 수동 문자열 스냅샷, 모든 정답 위치, Unicode·공백 보존, 입력 오류, 정답·ID 비노출, 중복 오답·ID 유지 |
| 추적 실패 검사 | 20개 통과. 누락·중복·행 대체, 내용·정답·메타데이터 변조, 잘못된 분야, 모호한 해시, 파일 위치 fallback |
| D01 | 26파일·1,995행, 4지선다 1,739·5지선다 256·지문 353·정답 E 49. 11개 분야 통계 일치 |
| D02 | 고유 ID 1,987개·중복 ID 그룹 8개여도 1,995행 유지. `Functional_CSAT.json#82`는 Functional |
| D03 | HF repo/default loader → Doc → 실제 DetailsLogger → Parquet 저장/재읽기 → 원본 연결, 1,995행 모두 통과. 로더의 파일/배열 순서도 일치 |

D03은 실제 `EvaluationTracker.save_details`를 사용합니다. 모델을 호출하지 않고 빈
`ModelResponse`와 `trace_check=True` 표시를 저장하므로 모델 정확도나 전체 평가 파이프라인
검증 결과로 해석하면 안 됩니다. 저장된 각 Doc의 query·choices·gold_index·분야·추적 메타데이터와
행별 출현 횟수를 원본에 대조합니다. 결과 로그의 행 순서가 바뀌어도 연결할 수 있습니다.

최초 원본 목록 작성 시 고정 revision의 HF 파일 트리에 있는 Git blob ID와 다운로드한
26개 파일의 바이트를 대조했습니다. 이후 실행은 `manifest.json`의 파일 SHA-256과 모든 행 메타데이터를
그대로 비교하며, 원본이 달라지면 실패합니다. 검사 실패 시 manifest를 자동으로 갱신하지 않습니다.

## 입력과 추적 계약

프롬프트 버전은 `click_harness_layout_v3`입니다. 지문 유무별 지시문을 선택하고,
lm-evaluation-harness와 같이 지시문 뒤에 빈 줄을 두고 `맥락:`·`질문:`·`보기:`·`정답:`
한국어 필드 이름과 콜론·쉼표로 보기를 표시합니다. 하네스와 달리 모든 보기 라벨 뒤에 공백을 두고,
5지선다는 지시문과 보기에 E까지 표시합니다.
원본 공백·Unicode·줄바꿈과 보기 순서는 보존합니다. 세부 규칙은 [설계 §3](../../design.md)에 있습니다.
query는 `정답:`으로 끝나며, 채점 후보는 기존 ` A. 원문` 형식을 유지합니다.
이번 변경은 단일 예시 형식에 맞춘 것으로, 지시문 3종·보기 순환 평가와 실제 모델의
변경 전후 정확도 비교는 포함하지 않습니다.

정답은 정확히 한 보기에 일치해야 합니다. 누락된 필드, 잘못된 타입, 3/6지선다,
빈 질문/보기, 없는 정답·중복 정답은 `ValueError`를 발생시킵니다. 중복된 **오답**은 유지합니다.
정답만 바꾸면 gold_index만 달라지고, ID를 바꿔도 모델 입력은 달라지지 않습니다.

추적 키는 `revision:상대파일경로#0-based행번호`입니다. 원본 5개 필드를
`ensure_ascii=False, sort_keys=True, separators=(",", ":")`로 JSON 직렬화해 UTF-8 SHA-256을
계산합니다. `Doc.specific`에는 `original_id`와 `raw_row_sha256`이 들어갑니다.

현재 고정 원본의 내용 해시는 1,995개 모두 고유하므로 분야+해시로 연결합니다.
동일 분야에 내용까지 같은 행이 생기면 `AmbiguousSourceError`로 멈춥니다. 이 경우
파일별 로딩 시점에 `source_key`를 부착하는 fallback을 사용하며, 합쳐진 데이터의
순서나 ID로 임의의 원본을 고르지 않습니다. fallback은 서로 다른 파일과 같은 파일 내
동일 행을 포함한 합성 데이터로 검증했습니다.

원본 질문·지문·보기·정답과 원문이 포함된 로그는 Git에 넣지 않습니다.
`manifest.json`과 `results.json`에는 경로·ID·해시·통계만 있습니다.
검사 중 Parquet는 임시 로컬 디렉터리에 저장한 후 지웁니다. HF 캐시는 로컬에 남을 수 있습니다.

## 재실행

두 저장소의 `docs/week5-basicfive`를 체크아웃합니다. 아래는 Bash 기준입니다.
Lighteval 의존성이 설치된 Python 환경이 이미 있다면 그 Python을 사용해도 됩니다.

```bash
CLICK_LIGHTEVAL=/path/to/lighteval
CLICK_SPRINT=/path/to/k-llm-eval-sprint

# 최초 환경 설치
uv venv "$CLICK_LIGHTEVAL/.venv"
CLICK_PYTHON="$CLICK_LIGHTEVAL/.venv/bin/python"
uv pip install --python "$CLICK_PYTHON" -e "$CLICK_LIGHTEVAL[dev]"

# 이 경로의 소스가 기존 설치본보다 먼저 import되도록 지정
export PYTHONPATH="$CLICK_LIGHTEVAL/src"

cd "$CLICK_LIGHTEVAL"
HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 "$CLICK_PYTHON" -m pytest tests/unit/tasks/test_click.py -q

cd "$CLICK_SPRINT"
HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 "$CLICK_PYTHON" -m pytest teams/team-a-click/validation/click/test_provenance.py -q

# 별도 통합 검사: 고정 HF 원본을 다운로드하고 실제 repo/default 로더를 사용
"$CLICK_PYTHON" teams/team-a-click/validation/click/validate.py --report /tmp/click-results.json
```

기존 스냅샷 폴더에 `Dataset/`가 있으면 `--snapshot /path/to/snapshot`을 추가합니다.
`--local-loader`도 지정하면 원격 repo/config 로더 대신 로컬 JSON 로더를 사용합니다.
이 경우 결과의 `loader`는 `local-json`이므로 원격 경로를 시험한 결과와 구분하세요.
잘못된 원본이나 추적 연결은 0이 아닌 종료 코드로 실패하며 성공 결과 파일을 새로 쓰지 않습니다.
기존 결과 파일은 실패 시 남아 있을 수 있으므로 종료 코드와 `checked_at_utc`를 함께 확인합니다.

실제 검증은 Python 3.14.4, datasets 5.1.0, huggingface-hub 1.33.0, pyarrow 26.0.0,
torch 2.14.1, pytest 9.1.1 환경에서 수행했습니다. 모델 다운로드나 GPU 연산은 하지 않았습니다.

## 스타일 검사와 다음 연결

Lighteval 변경 파일의 pre-commit 검사는 모두 통과했습니다. 저장소 전체
`pre-commit run --all-files`도 실행했지만 기존 LFS 기준 결과 파일 두 개
(`SmolLM2-1.7B-Instruct-results-accelerate.json`, `SmolLM2-1.7B-Instruct-results-vllm.json`)의
마지막 개행 검사에서 변경이 발생했습니다. 해당 변경은 복원해 이번 커밋에서 제외했습니다.
검증 Python 코드의 Ruff 검사·포맷 검사도 통과했습니다.

태스크 등록은 Lighteval `e2c506f`에서 완료됐습니다. `TASKS_TABLE`에 `click:<category>`
11개 설정이 있으며, 각 설정은 `CATEGORY_FILES[category]`, `HF_REPO`, `HF_REVISION`,
`click_prompt`를 사용합니다. HF subset은 `default`, `hf_data_files`는
`{"train": list(CATEGORY_FILES[category])}`, 평가 split은 `train`, 지표는
`Metrics.loglikelihood_acc`(길이 정규화 없음)이고 `must_remove_duplicate_docs=False`와 0-shot입니다.
지표·집계·등록 테스트 6개는 `7bb0dcd`에서 추가돼 `test_click.py`는 입력 테스트 70개를 포함해
모두 76개입니다(`efb7e65` 기준 76개 통과).
2026-11-11에는 Polyglot 두 모델의 native 요청·독립 forward 파일럿·전체 비교를 추가로 완료했습니다.
I02·M01·M03·M04의 전체 비교 결과는 [통합 보고서의 이전 실행 참고값](polyglot-matrix-results/README.md)에,
두 도구의 정답 수·예측 일치·점수 차이는 [기계 판독용 집계](polyglot-matrix-results/results.json)의 `previous_run_references`에 있습니다.
M02는 전체 실제 입력의 길이·잘림 검사와 초과 차단 단위 테스트 범위이며,
합성 문항의 GPU 문맥 한도 경계 실험과 CLI 전체 실행 검증은 포함하지 않습니다.
