# 설계 문서: KorMedMCQA를 Lighteval에 옮기기

> 팀: STP즈(D팀) · 분석 보고서: `teams/team-d-kormedmcqa/analysis.md`
>
> 기준 버전: 데이터셋 revision `79efd6f`, lm-evaluation-harness `97a5e2c`(task version 3.0), lighteval `c2af9e5f`(팀 포크 `Hugging-Face-KREW/lighteval`), 논문 arXiv 2403.01469v3
>
> 코드 맨 위 주석과 `파일 :행` 표기는 위 커밋 기준의 소스 위치다.

## 1. 태스크 이름, 파일 위치

### 1-1. 태스크 이름

`kormedmcqa:{doctor,nurse,pharm,dentist}` (직종마다 태스크 1개, 총 4개)

이름은 `<벤치마크>:<subset>` 형식이다. 이유는 셋이다.

- lighteval의 기존 관례를 따른다. `mmlu:anatomy`, `arabic_mmlu:<subset>`이 같은 형식
- 이름에서 `:` 앞부분이 같으면 lighteval이 자동으로 묶어서 `kormedmcqa:_average`를 낸다.
- 직종 하나만 실행할 수 있다(`kormedmcqa:doctor|5`). harness의 `kormedmcqa_doctor`와 구분자만 다르다.

아래는 기존 코드의 같은 패턴이다. subset 목록을 돌면서 `이름:subset` 태스크를 만들고, 같은 subset 값을 `hf_subset`으로 넘긴다. kormedmcqa도 4개 config를 이 방식으로 만든다(5장 ③).

```py
# src/lighteval/tasks/multilingual/tasks/arabic.py:109-111
ARABIC_MMLU_TASKS = [
    CustomArabicMMLUTask(name=f"arabic_mmlu:{subset}", hf_subset=subset) for subset in ARABIC_MMLU_SUBSETS
]
```

### 1-2. 파일 위치

`src/lighteval/tasks/tasks/kormedmcqa.py`로 제안한다. 파일 하나에 `extract_choice`, 프롬프트 함수, 메트릭, 태스크 4개를 모두 넣는다.

`tasks/tasks/`를 고른 이유는 이렇다.

- `tasks/tasks/`는 항상 로드된다. `multilingual/tasks/`는 `load_multilingual=True`일 때만 로드된다(`registry.py` 기본값 `False`).
- 한편 기존 한국어 관련 태스크(`global_mmlu`, `paws_x` 등)는 `multilingual/tasks/`에 있어서, 메인테이너가 그쪽을 원할 수도 있다.
- 파일 하나로 끝나는 구조라, `multilingual/tasks/`를 원하면 파일만 옮기면 되고 코드는 바뀌지 않는다. 이슈에 이렇게 적고 메인테이너에게 묻는다.

## 2. 데이터 범위

### 2-1. 원본(harness)이 하는 일

| 항목 | 원본 설정 | 근거 |
| --- | --- | --- |
| 데이터셋 | `sean0042/KorMedMCQA` | `_template_yaml` :1 |
| subset | `doctor` / `nurse` / `pharm` / `dentist` (태스크마다 하나) | `doctor.yaml` :2, `dentist.yaml` :2, `nurse.yaml` :2, `pharm.yaml` :2 |
| 평가 split | `test` | `_template_yaml` :2 |
| few-shot split | `fewshot` | `_template_yaml` :3 |
| few-shot 뽑는 방식 | `first_n` (앞에서부터 순서대로) | `_template_yaml` :5 |
| 평균 | 직종별 점수를 문항 수로 가중 평균 | `_kormedmcqa.yaml` :10 |

```yaml
# _template_yaml:1~5
dataset_path : sean0042/KorMedMCQA
test_split : test
fewshot_split : fewshot
fewshot_config:
  sampler: first_n
```

shot 수는 실행할 때 `--num_fewshot 5`로 지정한다(`_cli/run.py` :123). 지정하지 않으면 0-shot이 된다(`evaluator.py` :327-342).

### 2-2. Lighteval에서 지정할 값

| 필드 | 값 | 원본의 대응 | Lighteval 기본값 | 근거 |
| --- | --- | --- | --- | --- |
| `hf_repo` | `sean0042/KorMedMCQA` | `dataset_path` | (필수 필드) | `lighteval_task.py` :115 |
| `hf_subset` | 직종 4개 중 하나 | `dataset_name` | (필수 필드) | `lighteval_task.py` :116 |
| `hf_revision` | `79efd6f` | (원본은 고정하지 않음) | `None`(최신) | `lighteval_task.py` :128 |
| `evaluation_splits` | `["test"]` | `test_split` | `["validation"]` | `lighteval_task.py` :133 |
| `few_shots_split` | `"fewshot"` | `fewshot_split` | `None` | `lighteval_task.py` :134 |
| `few_shots_select` | `"sequential"` | `sampler: first_n` | `None` → `balanced` | `prompt_manager.py` :203-205 |
| shot 수 | 설정 파일에 쓰지 않고 실행 문자열 `kormedmcqa:doctor\|5`로 지정 | (실행 시 지정) | 설정 파일 기본값 0, 실행 문자열이 덮어씀 | `lighteval_task.py` :148, `registry.py` :203-204, 229 |

### 2-3. 지정하지 않으면 생기는 일

| 지정 안 한 필드 | Lighteval 동작 | 생기는 일 |
| --- | --- | --- |
| `evaluation_splits` | `validation`을 채점 | 이 데이터셋의 split은 `train`/`dev`/`test`/`fewshot`이라 `validation`이 없다. 에러가 나거나 엉뚱한 구간이 채점될 수 있다(**추정**, 실행으로 확인 필요) |
| `few_shots_split` | 후보 목록(`hf_avail_splits`, 기본값 `train`/`validation`/`test`)에서 평가 구간을 뺀 뒤, 이름에 `train`, `dev`, `valid`, `default`가 든 것을 이 순서로 찾아 첫 번째를 쓴다(`lighteval_task.py` :234-236, :256-279) | 후보에 `train`이 있으므로 `train`에서 뽑힌다. `fewshot`은 후보 목록에 없어 선택되지 않는다. 예시가 원본과 달라져 프롬프트가 달라진다 |
| `few_shots_select` | `balanced`(정답 분포가 고르게 되도록 뽑음) | 직종마다 정답이 A~E로 하나씩이라 5-shot에서는 같은 5개가 뽑히지만 순서가 바뀐다 |

`few_shots_split`을 지정하면 `hf_avail_splits`는 쓰이지 않는다.

```py
# src/lighteval/tasks/prompt_manager.py:203-205
few_shots_select = task.fewshot_selection
if few_shots_select is None:
    few_shots_select = "balanced"
```

`sequential`은 원본의 `first_n`과 같은 동작이라고 판단했다. `variance_seed`가 0으로 들어가므로(`lighteval_task.py` :397-399) 아래 반복이 실행되지 않아, `fewshot` split의 앞 5개가 순서 그대로 예시가 된다.

```py
# src/lighteval/tasks/prompt_manager.py:261-266
def _init_fewshot_sampling_sequential(self, num_fewshot: int, variance_seed: int):
    # No balancing of the few-shot examples, we take the first items of the set
    # We rotate by num_fewshot * seed (seed >= 0) to be able to have different series of sequential few-shots
    fewshotpool = self.task.fewshot_docs()
    for _ in range(num_fewshot * variance_seed):
        fewshotpool.append(fewshotpool.pop(0))
```

### 2-4. 태스크 4개 구성

| 태스크 이름 | `hf_subset` | test 문항 수 | few-shot 문항 수 |
| --- | --- | --- | --- |
| `kormedmcqa:doctor` | `doctor` | 435 | 5 |
| `kormedmcqa:nurse` | `nurse` | 878 | 5 |
| `kormedmcqa:pharm` | `pharm` | 885 | 5 |
| `kormedmcqa:dentist` | `dentist` | 811 | 5 |
| 합계 |  | 3,009 |  |

합계에 `fewshot` 20문항은 넣지 않았다.

## 3. prompt function: 원본 필드와 `Doc(query, choices, gold_index)` 대응표

harness 프롬프트 형식 ([`_template_yaml` L9](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L9)):

```txt
{question.strip()}
A. {A}
B. {B}
C. {C}
D. {D}
E. {E}
정답：
```

| 원본 필드 | Doc의 어디로 | 변환 규칙 |
| --- | --- | --- |
| `question` | `query` 첫 줄 | `.strip()` 적용 (보기에는 strip 안 함. 원본도 같음) |
| `A`~`E` | `query`의 `A. ...` ~ `E. ...` 줄 | 줄바꿈으로 이어 붙임 |
| (고정 문구) | `query` 마지막 줄 | `정답：` (**전각 콜론 `：`**, 일반 `:` 금지) |
| `answer` (1~5) | `gold_index` | **`answer - 1`** (Lighteval은 0부터. 빼먹어도 에러가 없고 점수만 20% 근처로 떨어짐) |
| (A~E 글자) | `choices` | `[" A", " B", " C", " D", " E"]`. 앞 공백은 프롬프트와 채점에 영향 없음 (3-1 ①) |
| `cot`, `subject`, `year`, `period`, `q_number` | 사용 안 함 |  |

```py
def kormedmcqa_prompt(line, task_name: str = None):
    query = f"{line['question'].strip()}\n"
    query += "".join(f"{l}. {line[l]}\n" for l in ["A", "B", "C", "D", "E"])
    query += "정답："
    return Doc(
        task_name=task_name,
        query=query,
        choices=[" A", " B", " C", " D", " E"],
        gold_index=line["answer"] - 1,
    )
```

- `task_name`은 prompt function 인자로 받아 Doc에 넘긴다(`med.py`와 같은 구조). lighteval이 데이터 한 행마다 `self.formatter(item, self.name)`으로 부른다([`lighteval_task.py` L309](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/lighteval_task.py#L309)). `test`와 `fewshot` 모두 이 함수로 Doc이 된다([L345-348](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/lighteval_task.py#L345-L348)).

### 3-1. 프롬프트 한계와 해결 결과

분석 보고서 8절 ③의 프롬프트 항목과 설계 중에 나온 확인 항목을 다룬다. 확인 방법은 두 가지다.

- 두 도구의 실제 코드를 읽었다.
- doctor test 435문항의 실행 기록을 대조했다. harness 기록의 프롬프트와, lighteval 기록의 `doc`을 아래 조립 규칙대로 합친 프롬프트가 **435문항 모두 글자 단위로 같았다.** doctor test 1번은 양쪽 모두 2,145자다.

| # | 한계 (출처) | harness 코드 | Lighteval 코드 | 결과 |
| --- | --- | --- | --- | --- |
| ① | `choices` 앞 공백 포함 여부 | — | few-shot 정답은 `get_golds()[0].strip()`으로 공백 제거 후 붙음 ([`prompt_manager.py` L159](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L159)) | **해결.** 공백이 있든 없든 프롬프트가 같다. 채점에서도 `strip_strings=True`가 gold의 공백을 지운다 |
| ② | 예시 사이 구분자까지 글자 단위로 같아야 함 (분석 8절 ③, 6-2) | few-shot 전용 `doc_to_text`가 예시 끝에 `정답： {답}\n\n`을 직접 넣고 `doc_to_target: ""` ([`_template_yaml` L4-7](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L4-L7)). 답이 비어 있어 구분자를 더 붙이지 않고 `"".join`으로 연결 ([`task.py` L1078-1088, L1040](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/api/task.py#L1078-L1088)) | 예시 = `query + " " + 정답`, 조각 사이 `"\n\n".join` ([`prompt_manager.py` L157-165](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L157-L165)) | **같은 문자열.** 만드는 방식은 다르지만 결과는 `…정답： E\n\n…정답： A\n\n…\n\n{문제}\n정답：`로 같다 |
| ③ | few-shot 순서 `first_n` vs `balanced` (분석 8절 ③) | `first_n` = `fewshot` split 앞 n개를 순서대로 ([`samplers.py` L95-104](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/api/samplers.py#L95-L104)) | `sequential` = 풀을 순서대로, 앞 n개 ([`prompt_manager.py` L261-267](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L261-L267), L231 `[:num_fewshot]`) | **해결.** `few_shots_select="sequential"`이면 같은 5문항이 같은 순서로 붙는다 |
| ④ | 전각 콜론 `：` | U+FF1A (L6, L9) | 우리 함수도 U+FF1A | **일치** |

lighteval의 조립 코드는 다음과 같다. harness는 평가용과 few-shot용 템플릿이 따로 있고, lighteval은 `prompt_function` 하나만 쓴다.

```py
# src/lighteval/tasks/prompt_manager.py:156-165  (_prepare_plain_text)
for fewshot_sample in doc.fewshot_samples:
    query = self._extract_query(fewshot_sample.query, fewshot_sample.instruction)
    parts.append(query + " " + fewshot_sample.get_golds()[0].strip())

query = self._extract_query(doc.query, doc.instruction)
parts.append(query)

return "\n\n".join(parts)
```

**같은 프롬프트가 나오는 조건** (하나라도 어기면 프롬프트가 달라진다):

- `Doc`에 `instruction`을 넣지 않는다. 넣으면 맨 앞에 붙는다([L153-154](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L153-L154)).
- 모델 설정에 `system_prompt`를 주지 않는다. 주면 맨 앞에 붙는다([L150-151](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L150-L151)).
- chat template을 끈다(`override_chat_template=False`). 켜면 위 평문 조립을 타지 않는다([L54-57](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L54-L57)).

## 4. 채점: 지표, 생성 길이, stop sequence, 정답 추출 규칙

KorMedMCQA는 모델이 답변을 생성한 후, 정규식을 사용해 정답 선택지를 추출하고 실제 정답과 비교하여 평가한다. 기존 lm-evaluation-harness의 평가 방식을 재현하기 위해 다음 설정을 적용한다.

### 4-1. 생성 설정

| 항목 | 설정 | 근거 |
| --- | --- | --- |
| 최대 생성 길이 | `generation_size=1024` | harness의 `max_gen_toks: 1024` |
| 샘플링 | Greedy Decoding. 태스크에 지정할 필드가 없고 모델 기본값(temperature 0)을 따른다 | harness의 `do_sample: false`, `temperature: 0.0` |
| Stop Sequence | `["Q:", "</s>", "<\|im_end\|>", ".", "\n\n"]` | 기존 KorMedMCQA 평가 설정 |
| Chat Template | `override_chat_template=False` | 기존 harness의 `apply_chat_template=False`와 동일하게 Chat Template 미적용 |

### 4-2. 정답 추출

모델이 생성한 답변에서 정규표현식을 사용하여 객관식 정답 A~E를 추출한다.

| 순서 | 정규식 | 예시 |
| --- | --- | --- |
| 1 | `정답[:\s]*([ABCDE])` | 정답: c |
| 2 | `정답은\s*([ABCDE])\s*입니다` | 정답은 c 입니다 |
| 3 | `\b([ABCDE])\.` | c. |
| 4 | `\b([ABCDE])\b` | c |

- `IGNORECASE`를 적용하고 정규식을 순서대로 실행한다.<br>**IGNORECASE : 대소문자를 구분하지 않도록 하는 설정**
- 처음 일치한 정규식에서 마지막 매치를 정답으로 선택한다.
- 추출한 정답은 대문자로 변형한다(`.upper()` 적용)
- 추출에 실패하면 빈 문자열(`""`)을 반환하고 오답으로 처리한다.
- 기존 harness의 `utils.py`에 구현된 `extract_choice`를 기준으로 동일하게 구현한다.

### 4-3. 정답 변환 및 평가 지표

데이터셋의 실제 정답 1~5를 3장의 `gold_index`로 바꿔 A~E 글자로 모델의 예측 정답과 비교한다.

- **평가 지표:** Lighteval의 `ExactMatches` 사용
- **예측값 정규화:** `normalize_pred`에 `extract_choice` 연결
- **실제 정답:** `Doc`의 `gold_index`를 활용하여 A~E 형식으로 관리
- **채점 기준:** 정답 일치 시 1점, 불일치 및 추출 실패 시 0점

참고 구현: `src/lighteval/tasks/tasks/tiny_benchmarks.py`의 GSM8K `ExactMatches` 설정

### 4-4. 점수 집계

Doctor, Nurse, Pharm, Dentist 네 가지 하위 데이터셋의 정확도를 각각 산출한다. 전체 점수 및 가중 평균은 5장에서 다룬다.

Accuracy = {(정답 문항 수)/(전체 평가 문항 수) }\*100(%)

## 5. 원본과 다른 점, 그 이유

> 목표는 같은 입력에 harness와 같은 점수를 내는 것이다. Qwen2.5-1.5B-Instruct, doctor 435문항, 5-shot에서 실험용 커스텀 태스크는 harness와 문항별 출력과 채점이 doctor 태스크에 한해선, 모두 일치했다(정확도 둘 다 0.3310, 시간 : cpu 25-30분). 나머지 범위는 8장에 적었다.

### 5-1. 요약

| # | 항목 | 원본(harness) | Lighteval | 대응 | 이유 |
| --- | --- | --- | --- | --- | --- |
| ① | 정답 추출 | `ExtractChoiceFilter` + `take_first` 필터 | 필터 단계가 없다. 기본 `exact_match`는 출력 전체를 비교 | `ExactMatches`의 `normalize_pred`에 원본 `extract_choice`를 넣는다 | 원본과 같은 채점을 하려고 |
| ② | 전체 점수 | 문항 수 **가중 평균**(`weight_by_size: true`) | `kormedmcqa:_average`는 **단순 평균** | 일단 직종별 점수로 비교. 방법은 **미정**(5-3) | GPT-4o 기준 가중 85.61, 단순 85.53 |
| ③ | 직종 묶기 | group yaml | 이름의 `:` 앞부분이 같으면 superset으로 묶인다 | `kormedmcqa:<직종>` 4개를 만든다 | `kormedmcqa\|5`로 네 직종을 함께 실행할 수 있다 |
| ④ | few-shot 선택 | `sampler: first_n` | 기본 `balanced` | `few_shots_select="sequential"` | 기본값이면 예시 순서가 바뀌어 프롬프트가 달라진다 |
| ⑤ | few-shot 개수 | CLI `--num_fewshot 5` | 실행 문자열 `kormedmcqa:doctor\|5` | 실행할 때 `\|5`를 반드시 쓴다 | `\|` 없이 쓰면 0-shot으로 덮어쓴다 |
| ⑥ | few-shot split | `fewshot_split: fewshot` | 지정하지 않으면 `train`이 먼저 선택된다 | `few_shots_split="fewshot"` | 원본 예시와 같은 split을 쓰려고 |
| ⑦ | 평가 split | `test_split: test` | 기본이 `validation` | `evaluation_splits=["test"]` | 기본값이 원본과 다르다 |
| ⑧ | 정답 표현 | `answer` 1~5를 글자로 변환 | `gold_index` 0~4 | `answer - 1` | 인덱스 기준이 다르다 |
| ⑨ | 메트릭 정규화 | `ignore_case`, `ignore_punctuation`, 공백·줄바꿈 제거 | 옵션을 쓰지 않는다 | `strip_strings=True`만 쓴다 | 추출 결과가 대문자 한 글자라 점수에 영향이 없다 |
| ⑩ | 생성 설정 | `until`, `max_gen_toks`, `temperature: 0.0` | `stop_sequence`, `generation_size`, 모델 기본값 | 값을 그대로 옮기고 temperature는 지정하지 않는다 | 이름만 다르고 기본이 greedy다 |
| ⑪ | chat template | 기본으로 쓰지 않음 | 토크나이저에 있으면 자동으로 켬 | 실행할 때 `override_chat_template=False` | 켜면 stop 문자열이 무시된다 |
| ⑫ | 정규식 허점 | 있음 |  | **고치지 않고 원본 그대로** 구현 | 고치면 의도한 수정인지 우리 버그인지 구분이 안 된다 |

### 5-2. 정답 추출: 필터에서 메트릭으로

harness는 생성 결과를 필터로 가공한 뒤 `exact_match`를 낸다.

```yaml
# lm_eval/tasks/kormedmcqa/_template_yaml
filter_list:
  - name: "extract_answer"
    filter:
      - function: !function utils.ExtractChoiceFilter
      - function: "take_first"
```

lighteval에는 필터 단계가 없어서 메트릭 쪽에서 추출한다. `CHOICE_PATTERNS`와 `extract_choice`는 그대로 옮기고 호출 위치만 바뀐다.

```py
# 설계안 (의사코드)
kormedmcqa_metric = SampleLevelMetric(
    metric_name="exact_match",
    sample_level_fn=ExactMatches(strip_strings=True, normalize_pred=extract_choice),
    category=SamplingMethod.GENERATIVE,
    corpus_level_fn=np.mean,
    higher_is_better=True,
)
```

- `extract_choice`가 `.upper()`로 A~E 한 글자만 돌려주므로 harness의 대소문자, 구두점, 공백 무시 옵션은 필요 없다.
- 추출에 실패하면 빈 문자열이 되어 오답이다. harness와 같다.

### 5-3. 전체 점수: 가중 평균 (미정)

harness는 문항 수로 가중한다.

```yaml
# lm_eval/tasks/kormedmcqa/_kormedmcqa.yaml:7~11
aggregate_metric_list:
  - metric: exact_match
    aggregation: mean
    weight_by_size: true
    filter_list: extract_answer
```

lighteval의 `_average`는 어떤 벤치마크든 단순 평균이다.

```py
# src/lighteval/logging/info_loggers.py:382-384, 391-396
if "|" in k:
    task, fewshot = k.split("|")
    grouped_tasks[f"{task.split(':')[0]}:_average|{fewshot}"].append(k)
...
if len(list_of_subtasks) > 1:
    metrics = list(self.metric_aggregated[list_of_subtasks[0]].keys())
    self.metric_aggregated[average_task] = {
        metric: sum(self.metric_aggregated[k][metric] for k in list_of_subtasks) / len(list_of_subtasks)
        for metric in metrics
    }
```

| 후보 | 방법 | 5-shot에서 harness와 같은 계산인가 | 비고 |
| --- | --- | --- | --- |
| 1 | 사후 계산. 직종별 점수와 문항 수로 직접 가중한다 | **같다** | 태스크 코드에 손대지 않는다. docstring이나 문서로 계산법을 안내한다 |
| 2 | 통합 태스크. 네 직종을 이어 붙인 태스크를 추가한다 | **다르다** | 0-shot에서만 같다. `download_dataset_worker`를 가로채야 한다 |
| 3 | lighteval 집계 코드에 가중 평균을 넣는다 | 구현에 따라 다르다 | `_average` 관례를 바꾸는 일이라 메인테이너에게 물어야 한다 |

**후보 2가 5-shot에서 다른 이유**: `fewshot` split도 네 직종을 이어 붙이면 풀은 doctor 5개가 맨 앞에 오는 20개가 된다. `sequential`은 앞의 5개만 쓰므로 nurse, pharm, dentist 문항도 doctor 예시를 받는다. harness는 직종마다 자기 예시를 쓴다.

```py
# src/lighteval/tasks/prompt_manager.py:230-231
# get rid of the doc that's the one we're evaluating, if it's in the fewshot
return [x for x in samples if x != formatted_doc][:num_fewshot]
```

후보 1의 계산 예시는 다음과 같다.

```py
rows = []
for task, scores in results.items():
    # "kormedmcqa:doctor|5" 같은 직종 태스크만 고른다 (all, _average 제외)
    name = task.split("|")[0]
    if not name.startswith(f"{prefix}:") or "_average" in name:
        continue
    details = sorted(run.glob(f"details/**/details_{task}_*.parquet"))[-1]
    rows.append((name, scores[metric], len(pd.read_parquet(details))))

total_n = sum(n for _, _, n in rows)
weighted = sum(score * n for _, score, n in rows) / total_n
```

**선례**: `mmlu`는 과목별 문항 수가 달라도 `mmlu:_average` 단순 평균을 낸다. 한편 `bbq`, `lsat_qa`, `bold`는 서브태스크 옆에 전체를 합친 태스크를 함께 둔다. 다만 이 셋은 데이터셋의 `all` config를 그대로 읽는다. KorMedMCQA처럼 네 config를 코드로 이어 붙이는 선례는 아니다.

```py
# src/lighteval/tasks/tasks/bbq.py:53, 55-56, 71
name="bbq",
hf_repo="lighteval/bbq_helm",
hf_subset="all",
...
name="bbq:Age",
```

### 5-4. few-shot 개수

`LightevalTaskConfig.num_fewshots=5`로 적어도 실행 문자열이 값을 덮어쓴다. `|` 없이 `kormedmcqa:doctor`로 실행하면 0-shot이 된다. 태스크에 고정할 수 없으므로 실행 예시와 docstring에 `|5`를 명시해야 한다.

```py
# src/lighteval/tasks/registry.py:204-207, 229
    task_name, few_shot = tuple(task.split("|"))
else:
    task_name = task
    few_shot = 0
...
config.num_fewshots = few_shot
```

few-shot 선택과 split은 2-3, 문자열 조립은 3-1을 본다.

### 5-5. 생성 설정과 chat template

`do_sample`과 `temperature`는 태스크에 없는 필드다. 기본 temperature가 0이면 lighteval이 `do_sample=False`로 둔다.

```py
# src/lighteval/models/transformers/transformers_model.py:817-818
if num_samples == 1 and generation_config["temperature"] == 0:
    generation_config["do_sample"] = False
```

chat template을 켜면 stop 문자열이 EOS 하나로 줄어든다. 그래서 `override_chat_template=False`를 준다. 이 값은 모델 인자라서 태스크 파일이 아니라 실행 명령에 적는다.

```py
# src/lighteval/models/transformers/transformers_model.py:694-700
if self.use_chat_template:
    stop_tokens = [self.tokenizer.eos_token]
else:
    # NOTE: we are assuming all items in a batch behave similarly (same
    # stop_tokens and max_tokens genrated) which is not necessarily
    # the case! Because of that we only use batch size of 1
    stop_tokens = [self.tokenizer.eos_token] + batch[0].stop_sequences
```

### 5-6. 정규식 허점의 실제 영향

Qwen2.5-1.5B-Instruct, doctor 435문항, 5-shot 출력을 집계한 결과 허점 사례는 나오지 않았다. stop 문자열 `.`과 `\n\n` 때문에 출력이 거의 한 글자로 끝난다. 그래서 ⑫번은 재현성을 위해 그대로 두되, 이 조건에서 점수에 주는 영향은 없다고 볼 수 있다.

| 확인 항목 | 435문항 결과 |
| --- | --- |
| 한 글자로만 답함 | 430개 |
| 추출 실패(빈 값) | 0개 |
| 소문자 관사 문제(`a`가 A로 잡힘) | 0개 |
| 조사가 붙은 답(`C가`, `C번`) | 0개 |
| 복수 답(`A, D, E` 등) | 5개 |
| 원본과 수정 정규식(6-4)의 답이 갈린 문항 | 0개 |

- 복수 답 5개는 마지막 글자로 채점된다. 모델이 답을 여러 개 낸 경우라 정규식을 고쳐도 정답이 되는 것은 아니다.
- 이 결과는 한 모델, doctor, 5-shot 조건에 한정된다. 설명식으로 답하는 큰 모델과 0-shot은 따로 봐야 한다. 0-shot 100문항에서는 `C\n해설: ...` 같은 출력이 보였다.
- 수정안이 임시안이라, 이 값은 제보 여부를 판단할 근거로는 아직 부족하다.

### 5-7. 검증할 때 주의할 점

구현 차이는 아니지만 harness와 비교할 때 결과가 달라지는 지점이다.

| 항목 | harness | Lighteval | 주의 |
| --- | --- | --- | --- |
| 일부 문항 실행 | `--limit N`: 앞에서부터 N개 | `--max-samples N`: 시드 42로 섞은 뒤 N개 | doctor 100문항에서 겹치는 문항이 26개뿐이었다. 전체 문항으로 비교한다 |
| 추론 태그 | KorMedMCQA 설정에 처리 없음 | `remove_reasoning_tags` 기본값 `True` | `<think>` 태그를 내는 모델을 비교할 때 확인한다 |

```py
# src/lighteval/tasks/lighteval_task.py:387-390  (get_docs)
n_samples = min(max_samples, len(eval_docs)) if max_samples else len(eval_docs)
rnd = random.Random()
rnd.seed(42)
rnd.shuffle(eval_docs)
```

## 6. 테스트 계획

### 6-1. 단위 테스트

`extract_choice`:

```py
@pytest.mark.parametrize("output, expected", [
    ("정답: B", "B"),
    ("정답 : B", "B"),
    ("정답은 C입니다", "C"),
    ("정답은 C 입니다.", "C"),
    ("A와 B 중 B", "B"),
    ("(C)", "C"),
    ("", ""),
    ("C가 정답", ""),
    ("C is a correct answer", "A"),   # 알려진 허점
])
def test_extract_choice(output, expected):
    assert extract_choice(output) == expected
```

프롬프트 함수:

- `answer = 1`, `answer = 5`이면 gold A, E

메트릭:

- pred `C`, gold `C`이면 1
- pred 빈 문자열, gold `C`이면 0

### 6-2. harness와 lighteval의 프롬프트 글자 대조

- 4개 subset 전부를 대조한다.
- doctor는 435문항 모두 일치했고, test 1번은 양쪽 모두 2,145자다(3-1).

### 6-3. 전체 문항 대조

nurse, pharm, dentist를 포함한 전체 3,009문항을 harness와 문항별로 대조한다. doctor 435문항은 일치를 확인했다(5장).

### 6-4. 정규식 허점 영향 집계

원본과 수정 정규식으로 뽑은 답이 갈리는 문항을 센다. 수정안은 소문자 관사를 잡지 않도록 대소문자를 구분하는 임시안이다. 결과는 5-6에 적었다.

```py
FIXED = [re.compile(p) for p in [
    r"정답[:：\s]*([ABCDE])",
    r"정답은\s*([ABCDE])\s*입니다",
    r"(?<![A-Za-z])([ABCDE])\.",
    r"(?<![A-Za-z])([ABCDE])(?![A-Za-z])",
]]
diff = [r for r in rows if ext(ORIG, out(r)) != ext(FIXED, out(r))]
```

### 6-5. EXAONE 모델에서 검증

EXAONE(LG가 만든 한국어 특화 모델)으로 추가로 돌리면 다음 두 가지를 더 검증할 수 있다.

1. 토크나이저 종료 처리: EXAONE은 토크나이저와 종료 토큰이 Qwen과 다르다. Qwen에서 드러나지 않은 stop 문자열이나 EOS 처리 차이가 나타날 수 있다.
2. 논문 점수와 비교: 논문 점수는 55.73이다.

NVIDIA GPU로 테스트하지 못하면 그 사실을 PR 검증 범위에 적는다.

## 7. 작업 나누기

| 작업 | 내용 | 산출물 | 담당 | 기한 |
| --- | --- | --- | --- | --- |
| 데이터 스플릿, few-shot | 태스크 정의 4개의 데이터 설정(`hf_subset`, `hf_revision`, `evaluation_splits`, `few_shots_split`, `few_shots_select`) | `kormedmcqa.py`의 `make_task` | 정민채 | 11/7 |
| 프롬프트 | 프롬프트 함수와 단위 테스트, nurse, pharm, dentist 프롬프트 글자 대조 | `kormedmcqa_prompt`, 대조 스크립트 | 김대성 | 11/7 |
| 채점 | `extract_choice`, 메트릭, 생성 설정, 단위 테스트 | `extract_choice`, `SampleLevelMetric`, `test_kormedmcqa.py` | 나하윤 | 11/7 |
| 전체 실행, 대조 | nurse, pharm, dentist를 포함한 전체 3,009문항 harness 대조, 정규식 영향 집계 | `scripts/`, `results/` | 김강민 | 11/7 |
| PR, 이슈 | 이슈 질문 정리, PR 작성 | PR, 이슈 | 김강민 | 11/7 |

## 8. 아직 확인하지 않은 것

- `validation` split이 없을 때 `evaluation_splits`를 지정하지 않은 경우의 실제 동작
- nurse, pharm, dentist 서브셋의 harness 일치 여부
- 0-shot 전체 실행. 답 뒤에 해설이 붙는 출력과 복수 답의 채점 경로
