# 설계문서

## 1. 태스크 이름과 파일 위치

### 1.1. 태스크의 목적과 지원 범위

| 항목 | 설계 |
| --- | --- |
| task 이름 | `ifeval_ko` |
| 구현·팀 리뷰 대상 | `Hugging-Face-KREW/lighteval` |
| 향후 기여 대상 | `huggingface/lighteval`; 제출 시 최신 API와 재대조 |
| 등록 진입점 | `src/lighteval/tasks/tasks/ifeval_ko/main.py` |
| 초기 지원 | native metric/Pipeline의 네 지표 |
| 별도 범위 | Inspect scorer/backend 지원, 데이터 오류 수정, 새 채점 정책 |

### 1.2. 두 아키텍처의 선택 범위

**두 안 모두 Ko checker 모듈이 필요하다.** 결정할 것은 한국어 checker의 존재 여부가 아니라 채점 루프를 독립시킬지 공유할지다.

| 구분 | A. 별도 Ko 패키지·독립 엔진 | B. Ko 모듈·공통 metric 확장 |
| --- | --- | --- |
| Ko checker·registry·utility | 별도 보존 | 별도 보존 |
| 채점 루프 | Ko 전용 scorer | 정책 기반 공통 엔진 |
| 기존 영어 수정 | 원칙적으로 없음 | 공통 루프 추출·EnglishPolicy 연결 |
| 주요 이점 | 원본과 직접 대조하기 쉽고 회귀 범위가 작음 | 공통 helper·집계 연결의 중복 감소 |
| 주요 비용 | 작은 scorer의 중복 관리 | 응답 준비·두 실행 순서·기존 경로 회귀 검증 |
| 채택 조건 | 단기·최소 변경을 우선할 때 | 공유 API 합의와 영어/French 회귀 증거가 있을 때 |

### 1.3. A안: 파일별 책임

다음 경로의 기준 디렉터리는 `src/lighteval/tasks/tasks/`다. 신규 제안 파일이며 현재 구현이 존재한다는 뜻이 아니다.

| 파일 | 책임 |
| --- | --- |
| `ifeval_ko/__init__.py` | Ko 패키지 정의 |
| `ifeval_ko/main.py` | prompt 함수, Ko metric grouping, task config, `TASKS_TABLE` |
| `ifeval_ko/scoring.py` | Ko strict 전체→loose 전체의 독립 채점 흐름, 네 결과 반환 |
| `ifeval_ko/instructions_registry.py` | 원본 Ko registry 25종 보존 |
| `ifeval_ko/instructions.py` | Ko checker·고정 선택지·ending 문구 보존 |
| `ifeval_ko/instructions_util.py` | Ko 단어·문장 계산과 utility 보존 |

원본 `utils.py`의 scoring 함수를 이식할 때 구조 변경과 import 변경을 기록한다. 기존 영어 metric을 import한 뒤 전역 registry·utility를 교체하는 구현은 사용하지 않는다.

### 1.4. B안: 공통 엔진과 Ko 정책

| 파일 | 책임 |
| --- | --- |
| `ifeval/main.py` | 기존 `IFEvalMetrics()`·`ifeval_metrics` export와 영어 기본 동작 유지 |
| `ifeval/metric_core.py` | 후보 처리·OR/AND·결과 포장 helper와 두 실행 순서 지원 |
| `ifeval/policies.py` | 정책 계약과 `EnglishPolicy` |
| `ifeval_ko/main.py` | Ko task 및 독립 Ko metric grouping 등록 |
| `ifeval_ko/policy.py` | `KoPolicy`: 응답 NFC·checker 구성·실행 순서 선택 |
| Ko checker·registry·utility 3개 파일 | A안과 동일하게 독립 보존 |

새 정책 인터페이스는 다음 책임을 가져야 한다. 아래 이름은 신규 제안 API다.

| 제안 API | EnglishPolicy | KoPolicy |
| --- | --- | --- |
| `prepare_response(raw, phase)` | identity | strict·loose 각 진입점에서 NFC |
| `create_checker(id, raw_kwargs, prompt)` | 영어 registry·초기화 | Ko registry·초기화 |
| `loose_candidates(prepared)` | 고정된 8개 후보 | NFC 응답에서 고정된 8개 후보 |
| `execution_order` | `interleaved` | `separate_phases` |

registry 교체만으로는 충분하지 않다. Ko의 응답 정규화·고정 문구·utility·checker 생성 시점도 선택할 수 있어야 한다. 영어/Ko metric grouping은 별도 인스턴스로 만든다. 기존 `ifeval_metrics(sample_params=...)`로 policy를 바꾸면 객체·지표명을 변경할 수 있으므로 사용하지 않는다.

### 1.5. 보존 범위와 의존성

실제 데이터는 ID 21종을 사용하지만 Ko registry는 25종이다. registry는 원본대로 보존하고 데이터 coverage는 21종을 대상으로 한다. 미사용 `keywords:letter_frequency`, `change_case:capital_word_frequency`, `change_case:english_capital`, `change_case:english_lowercase`의 정상 실행까지 검증했다고 주장하지 않는다. 원본 미사용 checker의 utility 참조 문제도 별도 이슈로 관리한다. `KeySentenceChecker`는 원본 registry에 없으므로 신규 등록하지 않는다.

`langdetect`, `immutabledict`, `packaging` 의존성과 `pyproject.toml`의 선언을 대조한다. Ko optional dependency가 없는 상태에서 다른 task 열거까지 실패하지 않도록 lazy import 또는 기존 guard 방식을 따른다. 각 파일의 원본 출처·revision·저작권·라이선스 헤더를 보존한다.

근거: [LightEval Registry](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/registry.py), [기존 영어 IFEval](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/ifeval/main.py), [Ko registry](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_registry.py).

## 2. subset, 평가 split, few-shot split

| 항목 | 값 | 의미 |
| --- | --- | --- |
| Hugging Face ID | `allganize/IFEval-Ko` | 고정 revision의 원본 사용 |
| subset/config | `default` | 평가 데이터 구성 |
| evaluation split | `train` | 이름이 train이어도 모델 학습이 아닌 평가에 사용 |
| few-shot split | `train`을 형식상 지정 | 기존 IFEval 관례에 맞춘 지정. 0-shot이므로 예시 추출·삽입 없음 |
| few-shot 수 | `num_fewshots=0` | 실제 실행 설정에서도 0 확인 |
| 전체 문항 | 342개, 고유 key 342개 | 전체 prompt-level 분모 |
| 전체 instruction | 481개 출현, 고유 ID 21종 | 전체 instruction-level 분모 |
| 문항 식별 | 원본 `key` | 행 인덱스와 구별 |
| 통합 표본 | 전체 ID를 포괄하는 고정 N문항 | N=20을 고정 요구사항으로 삼지 않음 |

로딩 시 key 중복·누락, instruction 목록과 kwargs 길이, 각 ID의 registry 존재 여부를 확인한다. 같은 ID가 한 문항에서 반복되어도 순서와 개수를 유지한다. 반복 ID를 set이나 ID별 dict로 합치지 않는다.

현재 PR의 20문항 후보는 고정 데이터 재집계 결과 21종·33개 instruction을 모두 포함한다. 후보 목록·선정 근거와 더 깊은 branch 검증은 6절에서 구분한다.

## 3. prompt function과 원본 필드–Doc 대응표

### 3.1. 대응 계약

| 원본 필드·고정값 | Doc 대응 | 확인 사항 |
| --- | --- | --- |
| `prompt` | `query` | 원문을 유지하고 chat template를 prompt 함수에서 붙이지 않음 |
| `instruction_id_list` | `specific["instructions_id_list"]` | 데이터 키와 Doc 키의 단수/복수 차이를 명시하고 순서·반복 보존 |
| `kwargs` | `specific["kwargs"]` | 같은 index의 instruction과 일대일 대응 |
| `key` | `specific["ifeval_ko"]["key"]` 제안 | 원본 문항 추적용 |
| 원본 prompt·revision | `specific["ifeval_ko"]` | 재현·재채점 메타데이터 |
| `choices=[""]` | `choices` | 생성형 task의 형식상 값 |
| `gold_index=0` | `gold_index` | 정답 문구의 index를 의미하지 않음 |
| `instruction=""` | `instruction` | 별도 지시문을 추가하지 않음 |

### 3.2. prompt 함수 제안

```python
from lighteval.tasks.requests import Doc

KO_DATA_REVISION = "54199e3801116897697babf341865741dcd06fc8"

def ifeval_ko_prompt(line, task_name=""):
    return Doc(
        task_name=task_name,
        query=line["prompt"],
        choices=[""],
        gold_index=0,
        instruction="",
        specific={
            "instructions_id_list": line["instruction_id_list"],
            "kwargs": line["kwargs"],
            "ifeval_ko": {
                "key": line["key"],
                "original_prompt": line["prompt"],
                "dataset_revision": KO_DATA_REVISION,
            },
        },
    )
```

판정 추적 키는 `(key, instruction_index, instruction_id)`다. 예를 들어 key 1203에는 `keywords:frequency`가 두 번 있으므로 각각 index 0과 1로 저장한다.

Doc 변환에서 keyword 번역, kwargs 일괄 NFC, Markdown 제거, 공백 정리를 하지 않는다. raw kwargs를 보존하고 checker 구성 시점에 원본과 같은 필터를 적용한다.

## 4. 채점, 생성 길이, stop sequence, 정답 추출 규칙

### 4.1. 지표와 집계

| 지표 | sample-level 값 | corpus 집계 |
| --- | --- | --- |
| `prompt_level_strict_acc` | strict flags의 AND | 문항별 Boolean 평균 |
| `inst_level_strict_acc` | instruction 순서의 strict Boolean list | 전체 list를 평탄화한 평균 |
| `prompt_level_loose_acc` | loose flags의 AND | 문항별 Boolean 평균 |
| `inst_level_loose_acc` | instruction 순서의 loose Boolean list | 전체 list를 평탄화한 평균 |

instruction-level은 문항별 정확도의 단순 평균이 아니다. 입력 `[[True, True, True], [False]]`의 instruction 점수는 0.75, prompt 점수는 0.5다. 네 지표는 `SampleLevelMetricGrouping`으로 제공하며 higher_is_better는 모두 True다.

### 4.2. 생성 설정과 task config

| 항목 | 제안 기준                                                                     |
| --- |---------------------------------------------------------------------------|
| 출력 | instruction 조건을 평가하는 자유 생성 응답                                             |
| 생성 수 | 문항당 1개                                                                    |
| 길이 | 최대 신규 토큰 1,280개                                                           |
| sampling | off; 실제 backend에서 `do_sample=false`, `temperature=0.0` 확인                 |
| stop sequence | `<end_of_turn>`, `<                                                       |im_end|>` |
| 모델별 EOS | 실제 EOS token/stop 처리 값을 별도 기록                                             |
| chat template | 한 번만 적용하고 최종 렌더링 입력 보관                                                    |
| 모델 후보 | PR의 `Qwen/Qwen2.5-1.5B-Instruct`를 우선 검토, 최종 채택·revision·dtype·backend 미확정 |

고정 LightEval API에 맞춘 등록 예시는 다음과 같다. 생성 backend의 sampling 설정은 별도로 고정한다.

```python
from lighteval.tasks.lighteval_task import LightevalTaskConfig

# ifeval_ko_metrics는 선택한 A/B 구조로 별도 생성한다.
ifeval_ko = LightevalTaskConfig(
    name="ifeval_ko",
    prompt_function=ifeval_ko_prompt,
    hf_repo="allganize/IFEval-Ko",
    hf_subset="default",
    hf_revision=KO_DATA_REVISION,
    hf_avail_splits=["train"],
    evaluation_splits=["train"],
    few_shots_split="train",
    few_shots_select="random_sampling",
    num_fewshots=0,
    metrics=[ifeval_ko_metrics],
    generation_size=1280,
    stop_sequence=["<end_of_turn>", "<|im_end|>"],
    version=0,
)

TASKS_TABLE = [ifeval_ko]
```

### 4.3. 정답 추출과 scorer 입력

이 task에는 단일 정답 문구를 추출하는 절차가 없다. 모델의 assistant 응답 전체를 각 checker가 검사한다. `choices`·`gold_index`를 이용해 정답 문자열을 비교하지 않는다.

LightEval scorer 입력은 `ModelResponse.final_text[0]`을 기준으로 한다. `final_text`는 `text_post_processed`가 있으면 그것을, 없으면 원본 `text`를 선택하므로 raw 모델 출력과 항상 같지 않다.

다음 경계를 구분해 저장한다.

1. raw 모델 text·token ID
2. 입력 구간을 제외하고 추출한 assistant 응답과 framework 후처리 결과
3. 두 evaluator에 동일하게 전달한 채점 입력
4. Ko evaluator의 NFC 처리 후 응답

reasoning tag 제거·stop 처리 등은 한쪽에만 적용하지 않는다. 저장 응답을 한 번 생성해 양쪽 evaluator에서 재채점한다. evaluator마다 다른 응답을 생성해 비교하지 않는다.

### 4.4. Ko strict/loose 알고리즘

Ko 원본의 실행 순서는 다음과 같다.

1. strict 함수 진입에서 응답 NFC 정규화.
2. instruction 순서대로 새 checker를 만들고 strict 전체를 검사.
3. loose 함수 진입에서 같은 입력 응답을 다시 NFC 정규화.
4. 원본 순서의 8개 loose 후보 생성.
5. instruction 순서대로 checker를 다시 새로 만들고 각 후보의 OR 판정.
6. 두 flags list와 문항별 AND를 반환.

checker 구성은 registry 조회 → 원본 `if v` kwargs 필터 → `build_description(**kwargs)` → 필요 시 `build_description(prompt=prompt)` 순서다. `if v`는 None뿐 아니라 0·False·빈 문자열·빈 list도 제거하므로 `is not None`으로 바꾸지 않는다.

| 항목 | 기존 LightEval 영어 | Ko 원본 |
| --- | --- | --- |
| 응답 NFC | metric 진입에서 없음 | strict·loose 각 진입에서 적용 |
| 전체 실행 순서 | instruction별 strict→loose | strict 전체→loose 전체 |
| checker 생명주기 | instruction당 한 객체 공유 | 각 phase마다 새 객체 |

A안은 Ko의 두 phase를 전용 scorer로 보존한다. B안은 영어 `interleaved`와 Ko `separate_phases`를 모두 지원한다. Ko에서 checker만 두 개 만들고 instruction마다 strict→loose를 번갈아 실행하는 것도 원본의 전체 호출 순서와 다르다.

loose 후보는 원본, 별표 제거, 첫 줄 제거, 마지막 줄 제거, 첫·마지막 줄 제거, 마지막 세 후보에서 각각 별표를 제거한 결과의 총 8개다. 줄 구분은 `\n`이다. 후보의 순서·중복을 유지하고 빈 후보는 원본의 `r.strip()` 검사로 배제한다. `#`, `>`, `-`까지 임의로 제거하지 않는다. 각 instruction의 loose는 후보 OR이며 prompt는 instruction AND다. 모든 instruction이 같은 후보에서 통과할 필요는 없다.

### 4.5. 예외, 오류, 실행 기록

원본 checker가 내부에서 처리한 예외의 결과를 보존한다. 예를 들어 `ResponseLanguageChecker`가 `LangDetectException`을 잡아 True로 반환하는 경로를 외부 오류 정책으로 바꾸지 않는다. 반대로 밖으로 전파되는 예외를 새 fallback으로 정답 처리하지 않는다.

OOM·timeout·불완전 로딩은 실행 오류로 기록한다. 실패를 빈 응답으로 바꾸거나 정상 분모에서 조용히 제외하지 않는다. 실제 빈 응답과 길이 상한에서 정상 종료된 응답은 원본 규칙으로 채점하고 종료 사유를 기록한다.

manifest에는 key·원본/전달 kwargs·scorer 입력·model/tokenizer revision·backend·dtype·seed·chat template·실제 EOS/stop·종료 사유·개별 flags·분자/분모·네 지표·예외·source/입출력 hash를 담는다. expected/generated/scored 및 생성 실패/채점 실패 건수를 stage별로 구분한다.

근거: [Ko YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml), [Ko scoring](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/utils.py), [ModelResponse](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/models/model_output.py), [task config](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/lighteval_task.py).

## 5. 공식 방식과 다른 점 및 그 이유

여기서 직접 비교 기준인 “공식 방식”은 고정 Allganize Ko reference다. 원본 영어 IFEval과 Ko의 차이, Ko reference와 LightEval 이식의 구조 차이를 구분한다.

| 항목 | Ko reference | LightEval 이식 | 이유·동등성 조건 |
| --- | --- | --- | --- |
| 실행 framework | lm-evaluation-harness task/YAML | Doc·TaskConfig·native metric | 프레임워크 연결 변경. 판정 의미는 동일 |
| 입력 자료형 | `InputExample`·results list | `Doc`·`ModelResponse` | 필드·instruction 순서·kwargs·응답 경계 보존 |
| scorer 파일 | 원본 `utils.py` | A의 전용 scorer 또는 B의 정책 엔진 | 실제 파일명 변경과 import 변경을 기록 |
| 지표 연결 | YAML aggregation | `SampleLevelMetricGrouping` | 네 지표·Boolean·분자/분모·평탄화 집계 동일 |
| revision 지정 | 공개 task의 dataset 경로 | `hf_revision`으로 고정 | 업데이트로 입력·규칙이 달라지는 것 방지 |
| 모델별 종료 처리 | YAML stop + 모델 backend | LightEval backend의 실제 stop/EOS | 동일 생성 조건을 목표로 하며 실제 값 기록 |
| 최초 지원 | 원본 harness 경로 | native metric/Pipeline 우선 | Inspect는 별도 scorer가 필요하므로 첫 범위와 구분 |

변경하면 안 되는 것은 Ko 단어·문장 계산, 고정 문구, 응답/비교 문자열 NFC의 실제 위치, kwargs 필터, strict/loose 후보와 결합, checker 초기화·생명주기·예외 의미다. Ko utility를 영어 utility로 대체하거나 영어 실패 후 Ko로 재시도하는 OR fallback은 도입하지 않는다.

Known Issues는 원본 조건을 그대로 유지한다. 예를 들어 key 1203의 `평화/peace`, 2142의 `포식자/predatory`, 3345의 `강도/robber`, 227의 고정 선택 문구, 1092·1268의 이하/미만 조건, 3538의 글자 수/단어 수 차이를 이식 과정에서 자동 수정하지 않는다. 수정 overlay는 별도 실험·제보로 관리한다.

French는 현재 영어 `ifeval_metrics`를 재사용한다. B안을 선택하면 이 import와 기존 영어 정책을 유지한다. 기존 Inspect scorer는 두 prompt-level 값만 반환하므로 공통 metric을 수정했다고 Inspect의 네 지표 지원까지 완료된 것으로 표시하지 않는다.

파일별 출처·라이선스 헤더·수정 내역을 남긴다. 데이터셋 카드의 라이선스 표기와 가져오는 코드의 고지를 각각 확인한다.

근거: [French task](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py), [Ko checker](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py), [Ko utility](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py).

<a id="validation-plan"></a>

## 6. 테스트 계획과 실행 기록

### 6.1. 실행 순서

검증은 아래 순서로 진행한다. 모델 실행 전에 문항의 유형·입력 경로 포함 조건을 확인하고, 공통 코드를 변경하면 기존 task 회귀를 즉시 실행한다. 실행 완료 여부는 분석보고서의 검증 상태를 따른다.

| 단계 | 작업 | 완료 확인 |
| --- | --- | --- |
| 1. reference·환경 고정 | 데이터·Ko 코드·harness·Lighteval·의존성 revision 기록 | 입력·source·환경 manifest로 재구성 가능 |
| 2. 문항 선정·로딩 확인 | 6.3절의 ID·입력 경로·복수/반복 지시 기준 확인 후 key·prompt·kwargs 대응 점검 | 기준 충족 집계와 팀이 확정한 선정안 확보, 누락·중복·연결 오류 없음 |
| 3. 등록 task·유형별 고정 응답 회귀 | 6.2절의 유형별 통과·실패·경계 입력으로 원본 Ko와 새 task 비교 | 모델 없이 모든 대상 ID·입력 경로의 판정과 집계 일치 |
| 4. 기존 task 회귀 | 공통 코드 변경 전후 영어 및 영향을 받는 French 경로 비교 | 의도하지 않은 기존 판정 변화 없음. 공통 코드 수정 직후 실행 |
| 5. 선정안 통합 평가 | 팀이 확정한 모델·선정안으로 생성·저장·양쪽 재채점 | 실제 assistant 응답 추출·종료·잘림·메모리·실행 오류와 개별 판정 일치 확인 |
| 6. 전체 split 평가 | 통합 검증 후 같은 조건으로 전체 응답 생성·저장·재채점 | 모든 key 처리, 네 지표와 불일치 목록 확보 |

현재 완료 여부는 [분석보고서의 검증 상태](analysis.md#verification-status)를 기준으로 한다. 기존 영어·Ko 차이 분석을 새 Ko task의 동등성 결과로 대체하지 않는다.

<a id="fixed-response-regression"></a>

### 6.2. 등록 task·고정 응답 검증

다음 검사는 모델 없이 저장 응답으로 수행한다. 원본 Ko와 새 task에 같은 scorer 입력을 전달하고 지시 index별 strict/loose·문항 판정·집계를 비교한다. T8의 기존 경로 회귀는 공통 코드 수정 직후 실행하며 모델 통합 평가보다 먼저 통과해야 한다.

| 검사 | 입력 | 확인할 내용 | 합격 조건 |
| --- | --- | --- | --- |
| T1. 데이터 구조 | 고정 split 전체 | 342개 고유 key·21종 ID·481개 지시, instruction/kwargs 순서·대응 | 누락·중복 key·미등록 ID·목록 길이 불일치 없음 |
| T2. Doc 변환 | `1203` 등 반복 ID·복수 지시 문항 | query·specific·key·원본 prompt 보존, 형식상 choices/gold | 원본과 대응 필드 동일, 두 frequency를 index로 구별 |
| T3. 유형·입력 경로 전수 점검 | 6.3.2절의 21종 ID·25개 `(ID, 입력 경로)` 각각에 통과·실패 고정 응답 최소 1건씩, 적용 가능한 N−1/N/N+1 | `(key, instruction_index, ID, 입력 경로)`로 연결. 항상 True/False인 잘못된 구현 방지와 경계 확인 | 원본 Ko와 개별 strict/loose·문항 판정 일치, 의도한 예외 계약 보존 |
| T4. Ko 입력 처리 | NFC/NFD, None/0/빈 kwargs, 조사 결합·고정 문구 | 응답 진입 NFC·문자열별 처리 위치·`if v` 필터·정규식 경계 | 원본과 판정·전달값·호출 trace 일치 |
| T5. loose·생명주기 | 한 줄·여러 줄·별표·빈 후보·복수 지시 | 8후보 순서·중복·빈 후보 배제, 지시별 OR/문항 AND, Ko strict 전체→loose 전체, phase별 새 checker | 원본 후보·전체 호출 순서·checker 생성 trace·flags 일치 |
| T6. 네 지표 | `[[True, True, True], [False]]` 및 비균등 지시 수 | prompt 평균과 instruction 평탄화 | 각각 0.5와 0.75, 네 지표의 분자/분모 동일 |
| T7. 기존 86건 회귀 | 기존 case와 저장 Ko 응답 | 새 등록 task 경로의 개별·문항 strict/loose | 원본 Ko와 Boolean 100% 일치 |
| T8. 기존 경로 회귀 | 고정 영어 입력·French adapter·언어 교차 실행 | public export·판정·metric 객체 격리·optional dependency 로딩 | 기존 결과 불변. B안 필수이며 A안도 공통 변경 범위 확인 |

별도의 응답·파라미터 변형으로 Markdown 단일/이중 강조, 빈 문자열·공백·줄바꿈, 정규식 경계, 첫 단락 `3073`과 마지막 단락 `1954` 등을 확인한다. 필요한 합성 입력은 실제 데이터 조건과 구분한다.

`language:response_language`는 원본 `kwargs.language`가 요구하는 언어를 유지한다. 한국어·다른 언어·빈/짧은/혼합 텍스트와 언어 판별 내부 예외를 고정 환경에서 확인한다. 누락·잘못된 kwargs·난수 fallback·데이터에 없는 추신 표지의 일반 경로는 정상 데이터의 25개 입력 경로와 별도로 검사한다.

의도한 예외 fixture에서 같은 예외가 발생한 것은 예외 계약 검증이며 정상 채점 완료로 세지 않는다. 원본이 내부 처리하는 예외와 밖으로 전파되는 오류를 구분한다. 비결정적 판정은 seed·반복 실행·worker 설정을 기록하고 조사한다. loose 변환으로 실패 응답이 통과할 수 있으므로 strict/loose 기대값은 각각 명시한다.

checker 단독 진단과 실제 등록 task 경로를 모두 확인한다. 합격 기준은 [분석보고서 9.2절](analysis.md)의 개별 판정·분모 일치와 네 지표 허용 오차를 따른다. 21종·25개 입력 경로의 통과·실패 fixture 작성과 새 task 회귀는 **미수행**이다. 첨부 집계는 입력 포함 범위에 대한 결과다.

### 6.3. 문항 선정 규칙과 검증 범위

검증 문항은 다음 규칙으로 선정한다.

1. 고정 데이터에 실제 등장하는 **21종 instruction ID를 각각 최소 1회** 포함한다.
2. 6.3.2절에서 정의한 **정상 데이터의 25개 `(ID, 입력 경로)`를 각각 최소 1회** 포함한다. 이 경로는 kwargs 값에 따라 검사 연산·정규식이 바뀌는 경우를 구분한 것이다.
3. **같은 ID가 반복되는 문항과 복수 지시 문항을 각각 최소 1건** 포함한다. 반복 ID는 index별 kwargs·판정 대응을 확인하는 데 사용한다.
4. 지시문·검사 설정의 불일치를 확인하는 `1203`, `2142`, `1268`, `3538`을 포함하고 원본 prompt·kwargs를 수정하지 않는다.

유형·입력 경로 포함은 문항 선정의 조건이며, checker의 판정 정확성은 6.2절의 모델 없는 고정 응답 회귀로 확인한다. 이 표본의 점수를 전체 데이터셋의 모델 성능 추정치로 사용하지 않는다.

#### 6.3.1. 검증 문항과 지시 유형별 대응

검증 문항 선정안은 **23문항·40개 지시**이며 팀 검토 전 제안이다. 문항 목록은 다음과 같다.

```json
[3743, 136, 3518, 1233, 3445, 3442, 1262, 1082, 1127, 3710,
 122, 3563, 1107, 3073, 3311, 3750, 1203, 2142, 1268, 3538,
 1928, 2035, 1800]
```

비교 범위는 [고정 데이터 revision](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/54199e3801116897697babf341865741dcd06fc8)의 `train` split이다. 전체 342문항·481개 지시에 등장하는 ID 집합과 선정 문항의 집합을 대조했으며 **21/21종**을 포함한다. 반복 ID 문항은 `1203` 한 건이며 복수 지시 문항은 13건이다.

발생 수는 문항 수가 아니라 지시의 발생 횟수다. key `1203`에 두 번 나오는 `keywords:frequency`도 각각 센다.

| instruction ID | 전체 발생 | 선정 문항 발생 | 선정 key | Ko 관련 변경 근거 |
| --- | --- | --- | --- | --- |
| `combination:repeat_prompt` | 26 | 1 | 3563 | 제작자 열거 수정 클래스 |
| `combination:two_responses` | 19 | 1 | 1107 | — |
| `detectable_content:number_placeholders` | 20 | 1 | 3743 | — |
| `detectable_content:postscript` | 19 | 2 | 3710, 1800 | — |
| `detectable_format:constrained_response` | 10 | 1 | 3750 | Ko 고정 선택 문구 |
| `detectable_format:json_format` | 14 | 1 | 3518 | — |
| `detectable_format:multiple_sections` | 11 | 1 | 1127 | — |
| `detectable_format:number_bullet_lists` | 24 | 1 | 136 | — |
| `detectable_format:number_highlighted_sections` | 38 | 2 | 3710, 2035 | — |
| `detectable_format:title` | 27 | 5 | 3442, 1262, 3710, 3311, 1928 | — |
| `keywords:existence` | 22 | 2 | 3518, 3311 | 제작자 열거 수정 클래스 |
| `keywords:forbidden_words` | 28 | 1 | 3445 | 제작자 열거 수정 클래스 |
| `keywords:frequency` | 25 | 6 | 1233, 1203, 2142, 3538, 1928 | 제작자 열거 수정 클래스 |
| `language:response_language` | 25 | 1 | 3311 | — |
| `length_constraints:nth_paragraph_first_word` | 2 | 1 | 3073 | 제작자 열거 수정 클래스 |
| `length_constraints:number_paragraphs` | 19 | 1 | 1082 | — |
| `length_constraints:number_sentences` | 31 | 3 | 1262, 1268, 2035 | Ko 문장 utility |
| `length_constraints:number_words` | 36 | 3 | 136, 3442, 3538 | Ko 단어 utility |
| `punctuation:no_comma` | 42 | 2 | 1107, 1928 | — |
| `startend:end_checker` | 15 | 2 | 1233, 1127 | 제작자 열거 수정 클래스 |
| `startend:quotation` | 28 | 2 | 122, 2035 | — |

Ko 수정 클래스 표시는 [기존에 열거된 수정 클래스와 등록 현황](evidence/analysis-details.md#ko-classes)을 따른다.

#### 6.3.2. kwargs 값에 따른 검사 경로

원본 Ko [checker](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py)의 데이터 사용 21개 클래스에서 `build_description`과 `check_following`을 확인했다. 정상 kwargs의 값에 따라 서로 다른 연산·정규식을 선택하는 유형은 다음 네 가지다. 집계 스크립트는 이 조건의 AST와 실제 데이터 값을 확인한다.

| 지시 유형 | 파라미터 | 검사 조건 | 선정 key |
| --- | --- | --- | --- |
| `detectable_content:postscript` | `postscript_marker` | `P.P.S` | 3710 |
| `detectable_content:postscript` | `postscript_marker` | `P.S.` | 1800 |
| `keywords:frequency` | `relation` | `at least` | 1233, 1203, 2142, 3538 |
| `keywords:frequency` | `relation` | `less than` | 1928 |
| `length_constraints:number_sentences` | `relation` | `at least` | 2035 |
| `length_constraints:number_sentences` | `relation` | `less than` | 1262, 1268 |
| `length_constraints:number_words` | `relation` | `at least` | 3538 |
| `length_constraints:number_words` | `relation` | `less than` | 136, 3442 |

`relation`은 `<N`과 `≥N`으로 나뉘며 두 추신 표지는 서로 다른 정규식을 사용한다. 네 유형의 8개 경로와 나머지 17종의 기본 경로를 합친 **25개 `(ID, 입력 경로)`를 모두 포함**한다. 지시 유형별 대응과 경로별 발생·지시 index는 [전체 집계 결과](evidence/sample-coverage/coverage.json)에 기록했다.

이 분모는 정상 데이터에서 선택되는 검사 경로의 집계다. 나머지 유형의 임계값·단어·언어 값은 같은 연산에 전달하는 인자이므로 모든 값을 개별 경로로 세지 않는다. 고정 데이터에는 checker 인자가 누락되거나 원본의 `if v` 필터로 제거되어야 하는 활성 인자가 없음을 확인했다.

응답에 따라 갈리는 성공·실패, 강조 문법·정규식·단락 위치·NFC/NFD와 숫자의 경계값은 6.2절에서 검사한다. 데이터에 없는 누락·오류·난수 fallback과 추신의 기타 표지 경로도 고정 응답 회귀에서 별도로 다룬다. **25/25는 코드 분기 실행률이나 고정 응답 검사 완료를 뜻하지 않는다.**

#### 6.3.3. 진단 문항과 확인 대상

| key | 확인 대상 | 선정 근거 |
| --- | --- | --- |
| `1203` | ‘평화’ 요청과 `peace` 검사, 반복 ID | 두 `keywords:frequency`의 index·kwargs·판정 순서와 원본 검사 단어 보존 |
| `2142` | ‘포식자’ 요청과 `predatory` 검사 | 지시문과 검사 키워드가 다른 문항의 원본 판정 보존 |
| `1268` | ‘6문장 이하’ 요청과 `<6` 검사 | 요청문·검사 부등호 차이와 정확히 6문장인 경계 확인 |
| `3538` | ‘600자 이상’ 요청과 600단어 이상 검사 | 길이 단위 차이와 긴 출력의 종료·잘림 확인 |
| `136` | 글머리 기호와 단어 수 | 두 조건의 상호작용과 strict/loose 후보 처리 확인 |
| `3445` | 금지어와 조사 결합 | 정규식 단어 경계에 따른 ‘컴퓨터’·‘컴퓨터를’ 판정 차이 확인 |
| `3750` | 고정 선택 문구 포함 검사 | 선택 문구 하나 또는 여러 개를 포함하는 응답의 허용 범위 확인 |

지시문과 검사 설정의 불일치는 데이터 수정 실험과 구분하여 원본 조건으로 검사한다. `3538`의 길이 단위 불일치는 추가 검토 대상으로 관리한다.

#### 6.3.4. 선정 완료 조건과 불일치 처리

- 문항 선정은 6.3절의 네 규칙을 모두 충족하고 ID·입력 경로 누락이 0일 때 완료한다. 원본 데이터·코드를 바꾸면 분모와 경로 정의부터 다시 집계한다.
- 모델 평가 전에는 6.2절의 ID·경로별 통과·실패 고정 응답과 필요한 경계값에서 원본 Ko·새 task의 판정이 일치해야 한다. 입력 포함 조건의 충족과 회귀 통과를 각각 기록한다.
- 비교 불일치가 나오면 해당 `(key, instruction_index, ID, 입력 경로)`의 재현 응답과 인접 경계 사례를 추가한다. 원인을 수정하고 관련 회귀를 재실행한다. 빠진 입력 경로가 원인이면 해당 경로의 원본 문항도 포함한다. 미해결 불일치는 검증 완료로 처리하지 않는다.
- 문항을 교체하면 다른 ID·경로가 빠지지 않는지 재집계한다. 선정한 key·선정 이유·실제 문항 수·지시 수를 보고서와 실행 설정에 함께 반영한다.

### 6.4. 결과 비교 기준

분석보고서 9.2절에 기록된 비교 방법과 합격 기준을 따른다. 모델 응답을 한 번 생성해 저장하고 동일한 문항·응답을 원본 Ko와 새 Lighteval-Ko에 전달하여 판정과 집계를 비교한다. 문항 수·지시 수는 평가에 사용한 선정 목록에서 계산한다.

| 비교 항목 | 최종 선정 문항에 적용할 비교 기준 |
| --- | --- |
| 입력 대응 | 최종 선정 key·지시 수와 실제 로딩 결과 일치, 원본 순서·kwargs 일치 |
| 지시 판정 | 선정한 모든 지시 각각의 strict·loose Boolean 일치 |
| 문항 판정 | 선정한 모든 문항 각각의 strict·loose 전체 통과 여부 일치 |
| 집계 | 네 지표의 분자·분모 일치, 절대 오차 `1e-12` 이하 |
| 실행 상태 | 모든 문항 생성·채점 완료, 누락·미처리 오류 없음. 생성/채점 실패를 빈 응답이나 축소 분모로 숨기지 않음 |
| 기존 경로 | 영어/French 판정·public export·metric 객체 격리 보존. 합성 adapter만 확인했다면 그 범위를 표시 |


### 6.5. 문항 선정 근거와 재현 자료

6.3절 집계에 사용한 입력·코드·출력을 `evidence/sample-coverage/`에 첨부했다.

| 파일 | 내용 |
| --- | --- |
| [README.md](evidence/sample-coverage/README.md) | 집계 범위·분모·실행 환경·재현 명령 |
| [selection.json](evidence/sample-coverage/selection.json) | 검증 문항 23개 key·진단 문항 목록·제안 상태 |
| [audit_coverage.py](evidence/sample-coverage/audit_coverage.py) | 고정 원본의 hash 확인, registry·checker AST 확인, ID·입력 경로·반복/복수 지시 집계 |
| [coverage.json](evidence/sample-coverage/coverage.json) | 원본 URL·revision·hash, 스크립트·입력 hash, 환경과 지시 index별 원시 집계 |
| [coverage.md](evidence/sample-coverage/coverage.md) | 같은 집계의 유형별·입력 경로별 표 |

기존 고정 응답 검사는 [checker-audit 자료 안내](evidence/checker-audit/README.md)와 [cases.json](evidence/checker-audit/cases.json)을 참조한다. 입력 메타데이터를 재집계한 범위는 다음과 같다.

| 기존 검사 범위 | 확인한 구성 | 새 task 검증에서의 사용 |
| --- | --- | --- |
| 86개 case | 실제 데이터 조건 46건·메모리 override 2건·합성 fixture 38건. 실제 조건의 고유 key 11개 | 같은 입력·응답으로 등록 task 회귀 |
| 주 검사 대상 | 8종 ID | 유형 안의 조건·경계·예외 보강 |
| full 평가의 등장 유형 | 13종 ID. 주 대상 외 JSON·sections·bullet·highlight·title 5종은 부수 조건 | 각 유형 전용 통과·실패 fixture 구성 |
| 미포함 유형 | 두 응답·자리 표시자·추신·고정 선택 문구·언어·단락 수·쉼표 금지·큰따옴표의 8종 | T3의 전수 고정 응답 검사에 포함 |

원본 Ko의 [재실행 기록](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/3f6e86e52887c1ad1c4455928623f565b2be5640/teams/team-c-ifeval-ko/design.md#61-현재-증거와-앞으로의-검증-구분)에는 isolated-source 방식의 full strict/loose 지시·문항 판정이 과거 저장 결과와 86/86 일치한 것으로 보고되어 있다. 이 결과는 새 task 동등성 검증이나 모델 생성을 포함하지 않는다. 기존 86건의 사례 수와 문항 선정 집계의 23문항은 서로 다른 단위다.

### 6.6. 분석보고서 반영 항목과 현재 상태

통합 평가의 실행 조건·선정안의 key 목록·결과·관련 실행 자료를 분석보고서에 기록한다. 문항 선정 근거로 지시 유형별 대응표와 검사 조건의 포함 범위를 제시한다.

선정한 23문항·40개 지시의 입력 범위 집계는 6.5절의 스크립트로 실행하여 첨부하였다.

## 7. 작업 나누기: 담당과 날짜

### 7.1. 배정·일정의 상태

아래는 2026년 11월 1일을 설계 확정일 D0로 가정한 **제안 일정**이다. 기존 기한을 이미 지켰거나 팀원이 이 배정을 수락했다는 뜻이 아니다. 구조·구현 담당·환경이 늦게 확정되면 의존 작업을 순연한다.

기존 PR 기록에서 `joony0905`는 분석·설계·검증 자료 연결, `SubJeeLee`는 issue draft 작성·검토 흐름에 등장한다. `kiimyjun`에게는 모델·환경·표본 확정 후 통합 실행을 요청한 댓글이 있다. 구현 담당의 이름과 확정 기한은 확인되지 않아 미정으로 둔다. 아래 GitHub 식별자는 업무 제안의 근거이며 실제 Notion 담당자 할당이나 알림을 만들지 않는다.

| 작업 | 담당·협업 제안 | 목표 날짜 KST | 산출물·완료 조건 |
| --- | --- | --- | --- |
| 설계 기준·A/B 결정·지원 범위 확정 | `joony0905` 정리, 팀 리뷰·메인테이너 의견 확인 |  | 선택 구조, 파일 목록, API·검증 범위 기록 |
| Ko checker·registry·utility 이식 | 구현 담당 A — 미정 |  | 원본 출처·헤더 유지, 필수 source hash·import 확인 |
| scorer·task·metric 연결 | 구현 담당 B — 미정; A와 계약 조율 |  | A: 전용 scorer / B: 공통 core·policy, Registry 발견·Doc·네 지표 연결 |
| 21종 fixture 보강·86건 회귀 | 검증 담당 — 미정; `joony0905`의 근거 검토 협업 제안 |  | 8종 누락·5종 부수 조건 보강, 반복 ID·NFC·schedule·집계 검증 |
| B 선택 시 영어/French 회귀 | 구현 담당 B·검증 담당 — 미정 |  | 기존 판정·export·교차 언어 상태 격리 불변 |
| 모델·환경·N문항 확정과 통합 평가 | `kiimyjun` — 기존 요청 기준의 제안, 확정 필요 |  | revision·dtype·backend·template·실제 생성 설정·응답·재채점 결과 |
| 전체 split 생성·동일응답 재채점 | `kiimyjun`·검증 담당 협업 제안 |  | 342개 key·481개 조건 정상 처리, 네 지표·불일치 목록 |
| analysis·design·issue draft 동기화 | `joony0905` 분석·설계, `SubJeeLee` issue draft 흐름 기준의 제안 |  | 같은 구조·범위·실행 상태·증빙 링크로 정리 |
| 상호 리뷰와 제출 준비 | 팀 공동; 리뷰 담당 확정 필요 |  | 합격 기준, 미완료 항목, source·라이선스·재현 자료 검토 |

B안의 영어/French 리팩터링 범위가 늘거나 모델 실행 자원이 부족하면 실제 측정 후 일정을 다시 산정한다. 구조 미확정 상태에서 구현 완료일이나 전체 모델 평가 완료를 확약하지 않는다.

### 7.2. 선행 의존성과 결정 목록

- 구조 A/B 확정 → scorer·policy 계약 확정 → 등록 task·고정 응답 회귀 → N문항 통합 → 전체 split 평가.
- fixture 보강과 모델 환경 준비는 구조 확정 후 독립적으로 진행할 수 있다.
- B안은 기존 영어 결과 고정 → 동작을 유지한 공통화 → 영어/French 회귀 통과 → Ko 연결 순서로 검토한다.

| 결정할 항목 | 현재 상태 | 결정 기준 |
| --- | --- | --- |
| 최종 구조 | A 기본 권고·B 대안, 팀/메인테이너 합의 전 | 최소 변경과 공통화 비용, 두 schedule·회귀 증거 |
| 구현·검증 담당 | 미정 | 팀의 실제 참여·시간 확인 |
| 모델·revision·backend·dtype | 후보 단계 | 로딩·생성 자원 점검과 재현성 |
| 최종 N·key 목록 | 20문항 후보의 전수 coverage 확인 | 21종 포함과 진단 목적 충족 |
| Inspect | 초기 범위에서 분리 제안 | 별도 요구와 scorer 계약 |
| 데이터 오류 수정 | 기본 이식과 분리 | 제작자 제보·명시적 overlay·별도 검증 |