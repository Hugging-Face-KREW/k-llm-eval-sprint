# KMMLU 평가 태스크 설계와 협업 결과

> **팀:** 베이직파이브 · @GeonRyoung, @ojm6135, @hyeongrae-kim
> **작성일:** 2026-11-05
> **상태:** 협업 구현·검증 완료 내용을 정리한 사후 설계 문서

KMMLU의 기존 선택지 로그 확률 평가(`kmmlu`)를 유지하면서, 정답 문자를 생성하는
`kmmlu_direct` 45개 태스크를 추가했다. 같은 모델과 설정에서 Lighteval과
lm-evaluation-harness의 입력·출력·채점을 문항별로 비교하는 것을 완료 기준으로 삼았다.

협업 PR [CY-HYUN/lighteval#1][collab-pr]은 **2026-10-28 병합 완료**됐으며,
변경 사항은 [huggingface/lighteval#1425][upstream-pr]의 제출 브랜치에 반영됐다.
**2026-11-05 확인 시 업스트림 PR은 OPEN**이다. 협업 종료와 업스트림 병합 완료는 구분한다.

## 1. 태스크 이름과 파일 위치

| 항목 | 최종 구현 |
| --- | --- |
| 구현 파일 | `src/lighteval/tasks/tasks/kmmlu.py` |
| 기존 태스크 | `kmmlu:<subject>` 45개, 예: `kmmlu:accounting` |
| 추가 태스크 | `kmmlu_direct:<subject>` 45개, 예: `kmmlu_direct:accounting` |
| 등록 | `TASKS_TABLE = KMMLU_TASKS + KMMLU_DIRECT_TASKS`, 총 90개 |
| 과목 이름 변환 | HF config를 소문자로 바꾸고 `-`를 `_`로 치환 |
| 기존 prompt function | `kmmlu_prompt` |
| 추가 prompt function | `kmmlu_direct_prompt` |
| 추가 구성 요소 | `KMMLUDirectDoc`, `_kmmlu_direct_fewshot_order`, `kmmlu_direct_normalize`, `kmmlu_direct_exact_match` |

구현 기준은 협업 커밋 `5bd752883e6456d0ecb5ffffaec2d88480481b90`이다.
업스트림 PR의 제출 HEAD `76d6194c53f9a418cfa383bc74d750f82614c723`에 있는
[최종 kmmlu.py][final-code]와 해당 파일의 내용이 같음을 문서 작성 시 확인했다.
공통 추론 엔진이나 공통 few-shot sampler는 수정하지 않고 태스크 파일 안에서 구현했다.

## 2. Subset과 평가 및 few-shot split

| 설정 | 값 |
| --- | --- |
| `hf_repo` | `HAERAE-HUB/KMMLU` |
| `hf_revision` | `d61b3f19e552c576bf5960dd24289763edc36a88` |
| `hf_subset` | `KMMLU_SUBSETS`의 과목별 HF config 45개 |
| `hf_avail_splits` | `train`, `dev`, `test` |
| `evaluation_splits` | `test` |
| `few_shots_split` | `dev` |
| Direct `few_shots_select` | `sequential` |
| 검증 실행의 shot 수 | 기존 `kmmlu`는 0-shot, 추가 `kmmlu_direct`는 5-shot |

평가 대상은 test **35,030문항**, dev는 과목당 5문항씩 **225문항**이다.
train은 이번 평가의 예시나 평가 문항으로 사용하지 않는다.
전체 과목명은 구현의 `KMMLU_SUBSETS`를 기준으로 하며,
`Korean-History` → `korean_history`, `Political-Science-and-Sociology` →
`political_science_and_sociology`처럼 변환한다. 데이터 구성의 배경은 [analysis.md](analysis.md) §3에 있다.

**5-shot은 실행 시 명시해야 한다.** `few_shots_split="dev"`만으로 5-shot이 되지는 않는다.
Lighteval의 태스크 선택은 `kmmlu_direct:accounting|5`, 기존 비교는 `kmmlu:accounting|0`처럼
shot 수까지 구분한다. Direct 문서는 빈 예시와 5개 예시를 지원하고 1–4개 등 다른 개수의
예시가 할당되면 오류를 낸다. 실제 생성 결과의 동등성은 5-shot에서 검증했다.

### 문항별 few-shot 순서

하네스 0.4.13은 기본 few-shot seed **1234**를 사용해 원본 test 순서대로 각 문항의
예시 순서를 뽑는다. Lighteval은 평가 문항을 섞으므로 단순히 같은 dev 5개를 넣는 것만으로는
문항별 입력이 같아지지 않는다.

`KMMLUDirectDoc`은 예시가 할당될 때 다음과 같이 순서를 맞춘다.

1. dev 예시의 `Doc.id`로 원본 dev 순서를 복원한다.
2. 원본 test 행 번호에 해당하는 난수 추출 순서를 `random.Random(1234)`로 재생한다.
3. 해당 순서로 5개 예시를 배치한다. 계산한 순서는 캐시한다.

따라서 평가 순서를 뒤집거나 예시를 다시 할당해도 같은 test 문항에는 같은 문맥이 붙는다.
이 방식은 하네스의 기본 seed와 원본 test 순회에 맞춘 것이다. 사용자 지정 seed나
하네스의 임의 부분집합 순회까지 일반화한 sampler는 아니다.

## 3. Prompt function과 Doc 필드 대응

| 원본 필드 | `Doc` 위치 | 처리 |
| --- | --- | --- |
| `question` | `query` 첫 줄 | `strip()`으로 질문 앞뒤 공백 제거 |
| `A`, `B`, `C`, `D` | `query` 선택지 네 줄 | A–D 순서로 표시, 보기 내용은 그대로 사용 |
| `answer` | `gold_index` | 원본 1–4에서 1을 빼 0–3으로 변환 |
| 과목별 태스크 이름 | `task_name` | `kmmlu:<subject>` 또는 `kmmlu_direct:<subject>` |
| 정답 문자 후보 | `choices` | 기존은 `[" A", " B", " C", " D"]`, Direct는 `["A", "B", "C", "D"]` |
| `Category`, `Human Accuracy` | 사용하지 않음 | 모델 입력과 정답 판정에 넣지 않음 |

두 변형의 단일 문항 query는 같다.

```text
{question.strip()}
A. {A}
B. {B}
C. {C}
D. {D}
정답：
```

마지막 문자는 **전각 콜론 `：`(U+FF1A)**이다. ASCII 콜론으로 바꾸면 하네스와 입력이 달라진다.
Direct의 정답 B는 `choices[1]`로 얻으며, 평가 문항의 정답은 query에 넣지 않는다.
5-shot 문맥에는 dev 문항과 그 정답 예시가 포함된다.

기존 로그 확률 방식은 공백을 포함한 **정답 문자**를 채점한다. CLIcK 구현처럼
` A. 보기 내용` 전체를 채점하는 계약과 다르다. Direct는 생성 결과를 정답 문자와 비교한다.
두 방식 모두 이번 비교에서는 채팅 템플릿을 껐다.

## 4. 채점과 생성 설정

| 항목 | 기존 `kmmlu` | 추가 `kmmlu_direct` |
| --- | --- | --- |
| 방식 | 정답 문자 후보의 조건부 로그 확률 비교 | greedy 생성 |
| 지표 | `Metrics.loglikelihood_acc` | `exact_match` |
| 문항 판정 | 로그 확률이 가장 높은 후보의 인덱스와 gold 비교 | 정규화한 출력 전체와 정답 문자 비교 |
| 길이 정규화 | 사용하지 않음 | 해당 없음 |
| 생성 길이 | 해당 없음 | `generation_size=256` |
| 중단 문자열 | 생성하지 않음 | `Q:`, `\n\n`, `</s>`, `.` |
| 과목 내 집계 | 정답률 | 문항별 exact match의 `numpy.mean` |

Direct 정규화 함수는 **ASCII 공백 제거 → 소문자 변환 → `string.punctuation`의 ASCII
구두점 제거** 순서다. 탭·개행과 전각 문자를 임의로 정리하지 않는다. 정답 문자를
설명문에서 찾는 정규식도 사용하지 않는다.

정답이 B일 때, 아래는 **생성 종료 처리를 마친 문자열을 metric에 전달했을 때**의 예다.

| 출력 | 정규화 결과 | 판정 |
| --- | --- | --- |
| `B`, `b`, ` B `, `B.`, `(B)` | `b` | 정답 |
| `정답은 B` | `정답은b` | 오답 |
| `B\n` 또는 `\tB` | 개행·탭이 남음 | 오답 |
| 빈 문자열 | 빈 문자열 | 오답 |

출력에 처음 등장하는 A–D만 뽑아 맞히는 방식으로 완화하지 않는다.
생성 중단 문자열이 적용되는 단계와 metric의 문자열 정규화 단계도 구분한다.

전체 결과는 **micro**(전체 정답 수/전체 문항 수)와 **macro**(45개 과목 정답률 평균)를
별도로 계산한다. 하네스 그룹 기본 집계와 논문 집계의 차이를 숨기지 않는다.
논문 비교는 [analysis.md](analysis.md) §5에 정리한 macro 기준을 따른다.

## 5. 공식 방식과의 관계 및 범위

구현 기준은 lm-evaluation-harness **0.4.13**의 `kmmlu`와 `kmmlu_direct`이다.
한국어 원문 프롬프트, 전각 콜론, dev 5문항, 생성 중단과 exact-match 정규화를 맞췄다.

| 구분 | 이번 협업에서 적용한 범위와 이유 |
| --- | --- |
| 0-shot 로그 확률 비교 | 기존 기여의 동작을 보존하고 하네스와의 동등성을 검사 |
| 5-shot Direct 생성 | 팀이 추가한 범위. 논문의 Direct 설정과 관련된 생성형 평가 경로 제공 |
| 검증 모델 | `Qwen/Qwen2.5-0.5B-Instruct` 한 모델. 논문 모델의 수치 재현보다 두 도구의 동일 동작 검증에 집중 |
| few-shot 순서 | 기본 seed 1234와 원본 test 행 순회에 한정해 재현 |
| Hard·CoT | 구현 범위에서 제외 |
| API 모델 평가 | 별도 프로토콜이므로 이번 두 도구 비교 결과에 포함하지 않음 |
| 원본 문항과 결과 로그 | 원문 포함 파일은 로컬 검증용으로 보존하고 새 문서에 재배포하지 않음 |

초기 [analysis.md](analysis.md) §9의 Qwen 7B·Kanana 8B·H200 계획은 **당시 계획**이다.
아래 완료 결과는 Qwen 0.5B와 RTX 4070 Ti SUPER에서 얻은 결과이며,
초기 계획을 모두 실행한 것으로 표시하지 않는다.

## 6. 검증 방법과 완료 결과

### 입력과 설정 검사

협업 PR에 기록된 검사는 다음과 같다.

| 검사 | 확인 내용 | 결과 |
| --- | --- | --- |
| 등록·기존 동작 | 기존 45개 설정과 prompt 보존, Direct 45개 추가 | 통과 |
| 레지스트리 | `kmmlu:accounting|0`, `kmmlu_direct:accounting|5` 해석 | 통과 |
| few-shot | 평가 순서 역전·반복 할당 시 같은 문항의 예시 순서 유지 | 통과 |
| 정규화 | 공백·대소문자·구두점·탭·개행 등의 판정이 하네스 metric과 일치 | 통과 |
| 문자열·토큰 | 모델 로딩 전 전체 prompt를 문자 단위로 비교하고 입력 token ID도 비교 | 전체 일치 |
| 코드 형식 | Ruff 검사·포맷과 `git diff --check` | 통과 |

이는 협업 당시 실행 기록이다. 이번 문서 작성에서 모델 평가를 다시 실행하지는 않았다.
Direct 비교 스크립트와 문항별 증빙은 로컬 `compare/`에 있으며,
Lighteval PR에는 해당 스크립트나 영구 단위 테스트 파일이 포함되지 않았다.
따라서 검증 기록과 저장소 CI에 등록된 테스트를 동일하게 취급하지 않는다.

### 실제 모델과 실행 환경

| 항목 | 기존 로그 확률 전체 비교 | Direct 전체 비교 |
| --- | --- | --- |
| 모델 | `Qwen/Qwen2.5-0.5B-Instruct` | 동일 |
| 모델 revision | `7ae557604adf67be50417f59c2c2f167def9a775` | 동일 |
| 데이터 | 고정 revision의 45과목·35,030문항 | 동일 |
| GPU | RTX 4070 Ti SUPER | 동일 |
| 정밀도 | float32 | float32 |
| batch size | 1 | 8 |
| shots | 0 | 5, few-shot seed 1234 |
| Lighteval | 0.13.0 + `kmmlu_task.py` custom task | 0.13.1.dev0 editable source |
| lm-eval | 0.4.13 | 0.4.13 |
| 채팅 템플릿 | 끔 | 끔 |

Direct 실행의 transformers는 5.19.0, torch는 2.14.1, datasets는 5.1.0이다.
문맥 한도는 양쪽 모두 32,768토큰, 최대 생성 길이는 256토큰으로 설정했다.
실측 최대 prompt는 2,312토큰으로 입력 잘림이 필요하지 않았다.
`LightevalTask.get_docs()`·`PromptManager`, `HFLM.generate_until()`,
`TransformersModel.greedy_until()`과 각 도구의 실제 metric을 호출했다.
비교 중 별도로 예시 순서를 고치는 보정은 사용하지 않았으며 원본 test 행 번호로 결과를 연결했다.

### 결과

| 비교 | 문항 수 | Lighteval | lm-eval | 문항별 차이 |
| --- | ---: | ---: | ---: | --- |
| 기존 `kmmlu` 0-shot, micro | 35,030 | 0.3245 | 0.3245 | prompt·입력 토큰·예측 불일치 0 |
| 기존 `kmmlu` 0-shot, macro | 45과목 | 0.3157 | 0.3157 | 모든 과목의 정확도 일치 |
| `kmmlu_direct` 5-shot, micro | 35,030 | 10,623/35,030 = 0.303254 | 동일 | 생성 문자열·정규화 답·문항별 점수 불일치 0 |

기존 방식의 수치는 [공개된 GPU 전체 비교 결과][gpu-results]에 근거한다.
Direct 수치는 [협업 PR의 과목별 결과][collab-pr]와 로컬 `all_direct_native/summary.csv`에
근거하며, 문서 작성 시 CSV의 45개 과목·35,030행·정답 10,623개와 불일치 합계 0을 재확인했다.
두 행의 정확도 차이는 **0-shot 로그 확률 방식과 5-shot 생성 방식의 조건 차이**를 포함하므로
한 구현이 다른 구현보다 우수하다는 근거로 사용하지 않는다.

기존 방식의 로그 확률은 완전히 같지 않았다. GPU에서 최대 절댓값 차이가 약 `3.48e-03`이었지만
문항별 예측은 모두 같았다. 이를 모든 모델·GPU에서 수치적으로 동등하다는 보장이나
확인되지 않은 반올림 원인으로 일반화하지 않는다.

### 재현과 남는 한계

기존 로그 확률 비교는 [비교 저장소][comparison-repo]에서 실행한다.
당시 전체 GPU 실행 코드는 `c731c1e`, 공개 결과 문서는 `b67534946e9c5fc0948c201258d66a7e7336e9e5` 기준이다.

```bash
uv sync --frozen
uv run python reproduce.py --subjects all --device cuda
```

Direct 비교는 로컬 `compare/run_all_direct.py`가 구현 소스를 import해 수행했다.
스크립트는 출력 폴더가 이미 있으면 멈추므로 재실행 전에 별도 출력 위치를 정해야 한다.
외부 검토자가 PR만으로 이 비교를 재실행할 수 있게 하려면 비교 도구와 원문 없는 결과 요약을
추가로 정리할 수 있다. 원문이 포함된 CSV/JSON을 그대로 올리는 작업은 포함하지 않는다.

검증은 한 모델·한 GPU·기본 seed의 5-shot Direct에 한정된다.
다른 토크나이저의 경계 처리, custom seed와 부분집합 순회, Direct 0-shot 생성 동등성은
같은 수준으로 확인하지 않았다. Direct 비교는 native Python API 경로이며 CLI 전체 실행 검증은 아니다.

## 7. 협업 담당과 완료 이력

협업이 끝난 상태이므로 미래 역할 배정 대신 공개 기록으로 확인되는 수행 내용과 완료 시점을 정리한다.

| 작업 | 수행 주체 | 확인되는 시점 | 산출물·상태 |
| --- | --- | --- | --- |
| 기존 `kmmlu` 구현과 초기 CPU 비교 | @CY-HYUN | 2026-10-10 업스트림 제안 | 45개 로그 확률 태스크, 이슈 #1424·PR #1425, 5과목 700문항 비교 |
| Direct 추가 구현 | @GeonRyoung, 베이직파이브 협업 | 커밋 작성 2026-10-23, 병합 2026-10-28 | `5bd7528`, 협업 PR #1 |
| 기존 방식 전체 GPU 비교 | @GeonRyoung·@ojm6135·@hyeongrae-kim | 2026-10-28 공개 기록 | 45과목·35,030문항, 예측 불일치 0 |
| Direct 전체 비교·검증 보고 | 협업 PR #1의 @GeonRyoung 기여 | 2026-10-28 병합 시 보고 | 45과목·35,030문항, 문자열·점수 불일치 0 |
| 협업 결과 통합 | @CY-HYUN | 2026-10-28 | 협업 PR 병합, 업스트림 제출 브랜치에 반영 |
| 사후 설계 문서 정리 | @GeonRyoung 작업 기록 | 2026-11-05 | 현재 문서, 구현·검증·병합 범위 구분 |

업스트림 리뷰 대응과 병합은 별도 후속 단계다. 이 문서 작성으로 새 PR을 만들거나
업스트림 승인 상태를 변경하지 않는다.

## 근거 자료

- [기존 분석 보고서](analysis.md): 데이터 구성과 공식 평가 방식 조사.
- [협업 PR #1][collab-pr]: Direct 구현 설명, 전체 검증 결과, 병합 이력.
- [업스트림 PR #1425][upstream-pr]: 기존 태스크와 협업 변경의 통합 상태.
- [고정 커밋의 최종 태스크 코드][final-code]: 설정·prompt·few-shot·metric의 구현 기준.
- [GPU 전체 비교 기록][gpu-results]: 기존 로그 확률 방식의 45과목 검증 결과.

[collab-pr]: https://github.com/CY-HYUN/lighteval/pull/1
[upstream-pr]: https://github.com/huggingface/lighteval/pull/1425
[final-code]: https://github.com/CY-HYUN/lighteval/blob/76d6194c53f9a418cfa383bc74d750f82614c723/src/lighteval/tasks/tasks/kmmlu.py
[gpu-results]: https://github.com/CY-HYUN/kmmlu-lighteval/blob/b67534946e9c5fc0948c201258d66a7e7336e9e5/README.md#all-45-subjects-on-a-gpu
[comparison-repo]: https://github.com/CY-HYUN/kmmlu-lighteval
