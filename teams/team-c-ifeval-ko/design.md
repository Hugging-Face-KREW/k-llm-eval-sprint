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

## 6. 테스트 계획: 어떤 입력으로 무엇을 확인할지

### 6.1. 현재 증거와 앞으로의 검증 구분

| 검증 자료·범위 | 확인된 내용 | 남은 일 |
| --- | --- | --- |
| 고정 dataset·source | 342문항·481조건·21종, registry 25종, 필요한 9개 파일 hash 일치 | 구현 환경에서 로딩·등록 재확인 |
| 기존 86건 | 데이터 조건 46·override 2·합성 38, 실제 조건 고유 key 11개 | 새 task에 같은 입력·응답을 넣어 비교 |
| 동일 세션의 원본 Ko 재실행 | isolated-source 방식의 full strict/loose instruction·prompt 판정 86/86 historical 일치 | 새 LightEval-Ko 동등성이나 모델 생성 결과로 해석하지 않음 |
| 기존 86건 coverage | 주 검사 대상 8종, full의 등장 13종 | 빠진 8종과 부수 조건 5종의 전용 통과·실패 fixture 보강 |
| PR의 20문항 후보 | 21종 전체·총 33개 instruction 포함, 누락 ID 없음 | 팀의 최종 표본·모델·환경 확정 및 실행 |
| 등록 task·모델 통합·전체 split | 새 task 기준 미수행 | 구현 이후 단계적으로 실행 |

이번 문서 정리에서 새 task 구현·모델 평가를 수행한 것으로 표시하지 않는다. 기존 재실행 결과는 앞선 동일 세션 검토의 기록이다.

### 6.2. 단계별 입력과 합격 조건

| 단계 | 입력 | 확인할 내용 | 합격 조건 |
| --- | --- | --- | --- |
| T1. 데이터 구조 | 고정 split 전체 | 고유 key, 21종 ID, 481개 instruction, list/kwargs 정렬 | 누락·중복 key·미등록 ID·길이 불일치 없음 |
| T2. Doc 변환 | 실제 key 1203 등 반복 ID·복수 지시 문항 | query·specific·key·순서 보존, 형식상 gold | 원본과 대응 필드 동일, 두 frequency 유지 |
| T3. checker fixture | 전체 21종의 통과·실패·적용 가능한 N−1/N/N+1 | 항상 True/False인 구현 방지, 경계·relation 분기 | reference와 개별 판정·오류 계약 일치 |
| T4. Ko 입력 처리 | NFC/NFD, None/0/빈 kwargs, 첫 어절·고정 문구 | 응답 진입 NFC와 문자열별 처리 위치·필터 보존 | 원본과 판정·전달값·호출 trace 일치 |
| T5. loose·생명주기 | 1줄·여러 줄·별표·빈 후보·복수 instruction | 8후보 순서, 독립 OR/AND, strict 전체→loose 전체, 새 checker | 원본 후보·순서·생성 trace·flags 일치 |
| T6. 네 지표 | `[[True, True, True], [False]]` 및 비균등 instruction 수 | prompt 평균과 instruction 평탄화 | 각각 0.5와 0.75, 네 지표 분자/분모 동일 |
| T7. 기존 86건 회귀 | 기존 case·저장 Ko 응답 | 새 등록 task 경로의 개별·문항 strict/loose | 원본 Ko와 Boolean 100% 일치 |
| T8. N문항 모델 통합 | coverage를 확인한 고정 key와 모델 생성 1회 | chat template·stop/EOS·후처리·잘림·동일응답 재채점 | 입력·응답 경계 동일, 실행 오류 없음, 두 evaluator 일치 |
| T9. 전체 split | 342개 key의 저장 응답 | 481개 조건의 flags·전체 네 지표 | 정상 처리 완료·분자/분모 동일·지표 오차 기준 충족 |
| T10. 기존 경로 회귀 | 고정 영어 입력·French adapter 입력, 언어 교차 실행 | export·판정·metric 객체 격리, optional dependency 로딩 | 기존 결과 불변. B 필수, A도 공통 변경 범위 확인 |

의도한 예외 fixture에서 동일한 예외를 확인한 것은 예외 계약 검증이다. 그 입력을 정상 채점 완료로 세지 않는다. 원본에서 내부 처리되는 언어 판별 예외와 외부로 전파되는 오류도 구분한다. 비결정적 판정은 seed·반복 실행·worker 설정을 기록하고 원인을 조사한다.

### 6.3. instruction 전수 coverage와 보강 대상

아래 데이터 출현 수는 instruction 개수이며 반복 ID를 포함한다. 기존 86건 열은 “주 검사 대상 / full의 부수 조건 / 미포함”을 구분한 것이다. 테스트 통과율이나 모든 branch의 검증 완료를 뜻하지 않는다.

| instruction ID | 전체 데이터 출현 | 기존 86건에서의 위치 | 통합 후보 key |
| --- | --- | --- | --- |
| `combination:repeat_prompt` | 26 | 주 검사 대상 | 3563 |
| `combination:two_responses` | 19 | 미포함 — 보강 필요 | 1107 |
| `detectable_content:number_placeholders` | 20 | 미포함 — 보강 필요 | 3743 |
| `detectable_content:postscript` | 19 | 미포함 — 보강 필요 | 3710 |
| `detectable_format:constrained_response` | 10 | 미포함 — 보강 필요 | 3750 |
| `detectable_format:json_format` | 14 | full의 부수 조건 | 3518 |
| `detectable_format:multiple_sections` | 11 | full의 부수 조건 | 1127 |
| `detectable_format:number_bullet_lists` | 24 | full의 부수 조건 | 136 |
| `detectable_format:number_highlighted_sections` | 38 | full의 부수 조건 | 3710 |
| `detectable_format:title` | 27 | full의 부수 조건 | 3442, 1262, 3710, 3311 |
| `keywords:existence` | 22 | 주 검사 대상 | 3518, 3311 |
| `keywords:forbidden_words` | 28 | 주 검사 대상 | 3445 |
| `keywords:frequency` | 25 | 주 검사 대상 | 1233, 1203, 2142, 3538 |
| `language:response_language` | 25 | 미포함 — 보강 필요 | 3311 |
| `length_constraints:nth_paragraph_first_word` | 2 | 주 검사 대상 | 3073 |
| `length_constraints:number_paragraphs` | 19 | 미포함 — 보강 필요 | 1082 |
| `length_constraints:number_sentences` | 31 | 주 검사 대상 | 1262, 1268 |
| `length_constraints:number_words` | 36 | 주 검사 대상 | 136, 3442, 3538 |
| `punctuation:no_comma` | 42 | 미포함 — 보강 필요 | 1107 |
| `startend:end_checker` | 15 | 주 검사 대상 | 1233, 1127 |
| `startend:quotation` | 28 | 미포함 — 보강 필요 | 122 |

**보강 원칙:** 21종 모두 전용 positive/negative fixture를 갖춘다. 기존 86건에서 미포함인 8종을 우선 추가하고, 부수 조건이었던 JSON·sections·bullet·highlight·title 5종도 전용 fixture로 보강한다. 기존 주대상 8종 역시 수량·문자열·예외의 빠진 branch를 점검한다. 총 사례 수를 임의로 86건에 맞추지 않는다.

`language:response_language`는 한국어만 요구하는 검사가 아니다. 원본 `kwargs.language`가 요구하는 다른 언어도 유지한다. 빈 텍스트·짧은 텍스트·혼합 언어·언어 판별 내부 예외 경로는 고정 환경에서 별도로 확인한다.

### 6.4. N문항 선정 기준과 현재 후보

최우선 선정 조건은 전체 데이터에서 사용되는 21종 ID가 최소 한 번 등장하는 것이다. 복수 지시·Ko 문자열·Known Issue도 포함하고 `uncovered_ids=[]`를 코드로 확인한다. 재선정 시 greedy set cover를 초기 후보 생성에 사용할 수 있으나 tie-break 규칙·수동 추가 사유를 남긴다.

현재 PR 후보는 다음과 같다.

```json
[3743, 136, 3518, 1233, 3445, 3442, 1262, 1082, 1127, 3710,
 122, 3563, 1107, 3073, 3311, 3750, 1203, 2142, 1268, 3538]
```

이 목록은 **20문항·33개 instruction·21종**으로 유형 coverage를 충족한다. 유효한 통합 후보로 유지할 수 있다. 최종 N은 선정 기준과 팀 합의로 확정하며, boundary·NFD·key 227/3345 등은 별도 고정 응답 fixture로 보강할 수 있다. 이 진단 표본의 모델 점수를 전체 모델 성능의 통계적 추정값으로 사용하지 않는다.

### 6.5. 최종 합격 기준과 실패 처리

1. 같은 `(key, instruction_index, instruction_id)`, 원본 kwargs, scorer 입력을 대조한다.
2. instruction strict/loose 및 문항 AND 판정이 100% 일치한다.
3. 네 지표의 분자·분모가 동일하고 수치 절대 오차가 `1e-12` 이하다.
4. 전체 split 분모는 prompt 342·instruction 481, 현재 20문항 후보의 분모는 20·33이다.
5. 데이터 로딩·생성·채점에 미처리 오류가 없다. 오류를 빈 응답이나 축소 분모로 숨기지 않는다.
6. B안은 기존 영어·French 결과와 public export·객체 격리를 보존한다. French 실데이터에 접근하지 못했다면 합성 adapter 검증만 했다는 범위를 명시한다.
7. source·환경·입력·응답·flags·불일치·실행 command를 재현 가능하게 남긴다.

여기서 100%는 모델 정답률이 아니라 evaluator 판정 일치율이다.

근거: [기존 86건 공개 입력·결과·runner·provenance](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/tree/88c755854708cc585e60a3f0837a1faba19c8ce8/teams/team-c-ifeval-ko/evidence/checker-audit), [PR analysis의 통합 후보·현재 검증 상태](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/88c755854708cc585e60a3f0837a1faba19c8ce8/teams/team-c-ifeval-ko/analysis.md).

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