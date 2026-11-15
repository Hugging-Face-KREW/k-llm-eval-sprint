# 벤치마크 분석 보고서: KorMedMCQA

> 팀: STP즈 · 데이터셋: [sean0042/KorMedMCQA](https://huggingface.co/datasets/sean0042/KorMedMCQA)
> 기준 버전: 데이터셋 revision [`79efd6f`](https://huggingface.co/datasets/sean0042/KorMedMCQA/tree/79efd6f91edfc8036330d7a4daa88b9f2deb9a82), lm-evaluation-harness [`97a5e2c`](https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa)(task version 3.0), lighteval [`7fa19dc`](https://github.com/huggingface/lighteval/tree/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7), 논문 arXiv [2403.01469v3](https://arxiv.org/abs/2403.01469v3)

## 1. 한 줄 요약: 무엇을 측정하는가

한국 보건의료인 국가시험(의사, 간호사, 약사, 치과의사) 2012~2024년 기출 5지선다 7,469문항이다. 의학 지식뿐 아니라 한국어 의료 용어, 한국 법규·제도를 아는지도 본다.

## 2. 출처: 논문, 저자, 연도, 공식 코드

- 논문: _KorMedMCQA: Multi-Choice Question Answering Benchmark for Korean Healthcare Professional Licensing Examinations_, arXiv [2403.01469v3](https://arxiv.org/abs/2403.01469v3) (2024)
- 저자: 권선준, 최병진(공동 1저자) 외. KAIST, 아주대 의대, UNIST, 경희대 치대
- 공식 평가 코드: 따로 저장소는 없다. 논문에서 오픈소스 모델은 lm-evaluation-harness로 쟀고(A100 8장, seed 0), 상용 모델은 API로 쟀다.
- 원본 문제: 한국보건의료인국가시험원(국시원)이 공개한 기출 PDF

## 3. 데이터셋: Hugging Face ID, config와 split, 문항 수, 필드, 예시 2개

- Hugging Face ID: `sean0042/KorMedMCQA`
- Config: `doctor`, `nurse`, `pharm`, `dentist`
- Split: `train` / `dev` / `test` / `fewshot`. 연도로 나눠 놨다(train ~2020, dev 2021, test 2022~2024). `fewshot`은 config마다 5문항씩이다.

| config | train | dev | test | 합계 |
|---|---|---|---|---|
| doctor | 1,890 | 164 | 435 | 2,489 |
| nurse | 582 | 291 | 878 | 1,751 |
| pharm | 632 | 300 | 885 | 1,817 |
| dentist | 297 | 304 | 811 | 1,412 |
| 합계 | 3,401 | 1,059 | 3,009 | 7,469 |

문항 수는 HF datasets-server `/size`로 확인했다. 합계에 `fewshot` 20문항은 안 넣었다.

필드:
- `question` (string): 문제 본문
- `A`~`E` (string): 선택지
- `answer` (int, 1~5): 정답 번호 (1=A … 5=E). 0부터가 아니라 1부터라 주의.
- `cot` (string): 풀이. `fewshot` split에만 있고 나머지는 빈 문자열
- `subject`, `year`, `period`, `q_number`: 직종, 연도, 교시, 문항 번호

`fewshot` 5문항은 어디서 왔나 궁금해서 대조해 봤는데, 4개 직종 모두 질문 텍스트가 `dev`(2021년)와 5개씩 일치하고 `test`와는 안 겹친다. 정답은 직종마다 A~E가 하나씩 들어 있다(doctor: E, A, C, D, B).

예시 2개 (test split):

```
# nurse, 2022 — 정답 3 (C)
question: 고관절전치환술을 받고 절대안정 중인 환자에게 '비효과적 말초조직 관류의 위험'이라는
          간호진단을 내렸을 때 간호중재는?
A: 하지운동을 제한한다.
B: 무릎 밑에 높은 베개를 받쳐준다.
C: 항혈전스타킹을 적용한다.
D: 드레싱을 자주 교환한다.
E: 예방적 항생제를 투여한다.
```

```
# doctor, 2022 1교시 — 정답 1 (A)
question: 의사 'A'가 군지역에 의원을 개설하려고 한다. 적절한 절차는?
A: 개설신고서 → 군수
B: 개설신고서 → 도지사
C: 신고서 → 의사협회
D: 개설허가신청서 → 군수
E: 허가신청서 → 도지사
```

## 4. 라이선스와 접근: 라이선스, 약관 동의 필요 여부

- 라이선스: HF 데이터셋 카드에는 CC BY-NC 2.0(`license:cc-by-nc-2.0`, 비상업적 용도)으로 돼 있다. 그런데 [논문 부록 datasheet](https://arxiv.org/html/2403.01469v3#A5)에는 "released under MIT license"라고 적혀 있다. 둘이 다르다.
- 접근: gated 아님(HF API `gated: False`). 로그인이나 약관 동의 없이 받아진다.
- 구현할 때: lighteval 태스크는 데이터를 저장소에 넣지 않고 HF에서 바로 불러온다. docstring에는 더 엄격한 HF 카드 쪽(CC BY-NC 2.0)을 적고, 불일치는 제작자에게 알리기로 했다(8번).

## 5. 공식 평가 방식: 프롬프트 형식, few-shot 수와 출처, 채점 방식, 정답 추출, 지표, 논문 수치

기준으로 삼은 건 harness [`lm_eval/tasks/kormedmcqa`](https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa)다. 직종별 yaml(`doctor.yaml` 등)은 `_template_yaml`을 불러오고 `dataset_name`만 다르다.

### 프롬프트 형식

```
{question.strip()}
A. {A}
B. {B}
C. {C}
D. {D}
E. {E}
정답：
```

- 마지막 콜론이 전각 콜론 `：`이다. 일반 `:`으로 바꾸면 안 된다. ([`_template_yaml` L9](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L9))
- 정답 문자는 `['A','B','C','D','E'][answer-1]`로 만든다. ([L10](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L10))

### few-shot 수와 출처

- 논문은 5-shot이다(Table 1).
- 예시는 `fewshot` split 앞 5문항을 순서대로 쓴다(`sampler: first_n`). 예시에는 `정답： E\n\n`처럼 답 글자만 붙고, `cot` 풀이는 안 들어간다. ([`_template_yaml` L3-L7](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L3-L7))

### 채점 방식, 정답 추출, 정규화

| 단계 | 내용 | 근거 |
|---|---|---|
| 생성 | `generate_until`, greedy(`do_sample: false`, `temperature: 0.0`), `max_gen_toks: 1024` | [`_template_yaml` L8, L25-L34](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L25-L34) |
| 생성 중단 | `"Q:"`, `"</s>"`, `"<\|im_end\|>"`, `"."`, `"\n\n"` 중 하나가 나오면 멈춤 | 같은 곳 L26-L31 |
| 정답 추출 | 정규식 4개를 위에서부터 시도해서, 처음 걸린 패턴의 마지막 매치를 답으로 씀. 아무것도 안 걸리면 빈 문자열(오답) | [`utils.py` L14-L33](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/utils.py#L14-L33), 논문 Appendix B |
| 정규화 | `ignore_case`, `ignore_punctuation`, 공백·줄바꿈 제거 후 `exact_match` | [`_template_yaml` L16-L24](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L16-L24) |

정답 추출 정규식 (전부 `IGNORECASE`):

```python
CHOICE_PATTERNS = [
    re.compile(r"정답[:\s]*([ABCDE])", re.IGNORECASE),
    re.compile(r"정답은\s*([ABCDE])\s*입니다", re.IGNORECASE),
    re.compile(r"\b([ABCDE])\.", re.IGNORECASE),
    re.compile(r"\b([ABCDE])\b", re.IGNORECASE),
]
```

- 이 정규식은 task version 3.0에서 들어왔다([harness PR #3842](https://github.com/EleutherAI/lm-evaluation-harness/pull/3842), 2026-06-24 머지). 그 전엔 생성 결과를 통째로 `exact_match`로 비교했다.
- CoT는 harness로 재현이 안 된다. stop에 `"."`이 있어서 "차근차근 생각해봅시다."에서 첫 마침표가 나오자마자 끊긴다. 논문 CoT 점수(Table 2)는 API로 따로 잰 것이다.

### 지표

- 정확도(accuracy): 직종별 `exact_match` 평균
- 전체 점수: test 문항 수로 가중한 평균(`weight_by_size: true`). ([`_kormedmcqa.yaml` L7-L11](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_kormedmcqa.yaml#L7-L11)) 논문 GPT-4o 직종별 점수로 직접 계산해 보니 가중 평균은 85.61로 논문과 같았고, 단순 평균은 85.53이었다.

### 논문 수치

Direct 5-shot, 문항 수 가중 평균. 논문 Table 1에서 몇 개만 가져왔다.

| 모델 | 평균 |
|---|---|
| o1-preview | 92.72 |
| Claude-3.5-Sonnet | 86.51 |
| GPT-4o | 85.61 |
| Qwen2.5-72B | 78.86 |
| Llama-3.1-70B | 74.31 |
| EXAONE-3.0-7.8B | 55.73 |
| EEVE-10.8B | 54.94 |
| (참고) 응시자 평균 | 77.05 |

### 이번 주 팀 결정: 기본 채점 방식

원본처럼 생성 + 원본 정규식 추출로 가기로 했다. 예시는 `fewshot` split 5문항을 순서대로 쓰고, stop 문자열과 최대 생성 길이도 원본 그대로 둔다.

이렇게 정한 이유:
1. 원본(harness)도 논문도 이 방식이다. log-likelihood로 바꾸면 같은 모델이어도 점수가 달라져서 비교가 안 된다.
2. 5-shot이 답 형식을 잡아 준다. 예시 없이 물으면 `정답은 3번입니다` 같은 식으로 답해서 정규식이 못 잡는다. 예시 5개에 `정답： E`가 보이니까 모델도 ` C`처럼 따라 쓴다.
3. 예시를 매번 같은 5개, 같은 순서로 써야 결과가 재현된다. 랜덤으로 뽑으면 돌릴 때마다 점수가 흔들린다.

그 밖에:
- chat template은 끈다. harness 기본 실행이 안 쓰고, lighteval은 켜면 stop 문자열을 버리고 EOS에서만 멈춰서 조건이 달라진다(8번 ④). 켰을 때 점수는 나중에 따로 실험으로만 본다.
- log-likelihood 버전은 기본 태스크에 안 넣는다. 따로 만들지는 이슈에서 메인테이너한테 물어볼 생각이다.
- 범위는 Direct 5-shot, 4개 config, test split까지. CoT, KorMedMCQA-V(이미지 문항), 데이터 수정은 이번에 안 한다.

## 6. 기존 구현: 공식 코드, 다른 평가 도구

| 도구 | 구현 | 비고 |
|---|---|---|
| lm-evaluation-harness | [`lm_eval/tasks/kormedmcqa/`](https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa) | `kormedmcqa` 그룹과 `kormedmcqa_{doctor,nurse,pharm,dentist}`. 생성 + 정규식 추출(v3.0) |
| lighteval (`main`) | 없음 | 의료 태스크(`med.py` 등)는 영어고, 한국어는 번역·다국어 세트(`global_mmlu` 등)만 있다 |
| lighteval (열린 PR) | 없음 | 7번 참고 |

lighteval 쪽에서 참고하려는 코드:
- `src/lighteval/tasks/tasks/gpqa.py`: 생성하고 나서 답을 뽑는 instruct 계열 태스크
- `src/lighteval/tasks/tasks/mmlu.py`: 짧게 생성해서 `exact_match`로 비교
- `src/lighteval/tasks/tasks/musr.py`: 팀 README에 참고 코드로 적혀 있던 것. docstring 형식(`name`, `dataset`, `abstract`, `languages`, `tags`, `paper`)이랑 inspect-ai 붙이는 방법을 볼 수 있다

## 7. 중복 확인: 검색한 키워드와 결과 (이슈, PR)

2026-10-17에 `huggingface/lighteval`(main `7fa19dc`)에서 찾아봤다.

| 키워드 | 대상 | 결과 |
|---|---|---|
| `kormedmcqa` | 이슈, PR | 0건 |
| `kormedmcqa` | 코드 | 0건 |
| `medical korean` | 이슈, PR | 0건 |
| `korean` | 이슈, PR | KMMLU 이슈 [#1424](https://github.com/huggingface/lighteval/issues/1424), PR [#1425](https://github.com/huggingface/lighteval/pull/1425)(열림, A팀 범위), 번역 문구 PR #1179(열림), #356(머지). KorMedMCQA랑은 관계없음 |

찾아본 범위에서는 겹치는 게 없었다. 


## 8. 구현하면서 어려울 것 같은 부분

대부분 "원본이랑 똑같이 옮기고 싶은데 lighteval 기본값이 달라서 손봐야 하는" 부분이다.

| # | 어려운 점 | 원본 | lighteval 기본 | 대응 |
|---|---|---|---|---|
| ① | 정답 추출 | 정규식 4개 cascade | `exact_match`는 출력 전체를 통째로 비교([`metrics.py` L255-L261](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/metrics/metrics.py#L255-L261)), `extractive_match`는 규칙이 다름 | `extract_choice`를 그대로 옮긴 metric을 새로 만든다 |
| ② | 정규식 허점 | 아래 | — | 원본 그대로 두고, 영향은 따로 센다 |
| ③ | few-shot 순서 | `first_n` | `balanced`([`prompt_manager.py` L205](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/tasks/prompt_manager.py#L205)) | `few_shots_select="sequential"`(앞에서부터, [L261-L267](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/tasks/prompt_manager.py#L261-L267))로 바꾸고, 예시 사이 구분자까지 프롬프트를 글자 단위로 비교 |
| ④ | chat template | 기본 안 씀 | 토크나이저에 chat template이 있으면 자동으로 켬([`models/utils.py` L109-L132](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/models/utils.py#L109-L132)). 켜지면 stop 문자열을 버리고 EOS에서만 멈춤([transformers L693-L698](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/models/transformers/transformers_model.py#L693-L698), [vLLM L630](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/models/vllm/vllm_model.py#L630)) | `override_chat_template=False`로 끄고, 첫 실행 details에서 답 길이를 보고 stop이 먹는지 확인 |
| ⑤ | 전체 점수 집계 | 문항 수 가중 평균 | `kormedmcqa:_average`는 단순 평균([`info_loggers.py` L381-L396](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/logging/info_loggers.py#L381-L396)) | 일단 직종별 점수로 비교. 가중 평균 내는 방법은 4주차 설계 때 정한다 |
| ⑥ | 정답 인덱스 | `answer` 1~5 | `gold_index`는 0부터 | `answer - 1`. 빼먹어도 에러가 안 나고 점수만 20% 근처로 떨어지니 테스트로 잡아야 한다 |

②의 정규식 허점은 답을 못 뽑는 경우만 있는 게 아니라 다르게 뽑는 경우도 있다. 원본 `extract_choice`에 문자열을 넣어 확인했다.

| 모델 출력 | 뽑힌 답 | 이유 |
|---|---|---|
| `C가 정답` | 빈 값 | 파이썬 `re`는 한글도 단어 글자로 봐서 `C`와 `가` 사이에 `\b`가 안 생긴다. 1번 패턴도 `정답` 뒤에 글자가 없어서 안 걸린다 |
| `C번` | 빈 값 | 같은 이유 |
| `C is a correct answer` | `A` | 4번 패턴이 `C`와 관사 `a`를 둘 다 잡는다. `IGNORECASE`라 소문자 `a`도 걸리고, 마지막 매치를 쓰니까 `A`가 된다 |

못 뽑으면 빈 값이라 오답으로 남지만, 다르게 뽑으면 엉뚱한 보기가 답이 된다. 정답이 A인 문항이면 틀린 답이 맞은 걸로 채점된다. 다만 한국어 문항이라 모델이 영어로 답하는 일이 실제로 얼마나 있을지는 확인 안 한 예상이다. 실제 출력에서 세어 보고 판단한다(9번 순서 4).

일단 원본 그대로 구현한다. 고쳐 버리면 harness랑 점수가 달라지는데, 그게 일부러 고친 탓인지 우리 버그인지 구분할 수가 없다. 생성이 `.`에서 끊기니까 실제 출력은 보통 ` C`처럼 짧아서 영향은 크지 않을 수도 있다. 위 예시도 직접 만든 문자열로 돌려 본 거고 실제 모델 출력에서 본 건 아니다.

검증할 때 실제 출력에 원본 정규식이랑 고친 정규식을 둘 다 돌려서 답이 갈리는 문항이 몇 개인지 세 볼 생각이다. 그 숫자를 보고 harness에 제보할지 정하고, PR 설명에는 "알려진 문제"로 적는다.

### 이번 주 팀 결정: 찾은 데이터 문제 중 무엇부터 제보할지

| 순서 | 문제 | 제보할 곳 | 이유 |
|---|---|---|---|
| 1 | 라이선스 불일치(HF 카드 CC BY-NC 2.0 vs 논문 MIT) | HF 데이터셋 Community 탭 | 사용 조건 문제라 제일 먼저. lighteval docstring에 뭐라고 적을지도 이것에 달려 있다 |
| 2 | pharm test 2024년 271문항의 `subject`가 `pharm`이 아니라 `pharmacy` | HF 데이터셋 Community 탭 | config로 불러오면 점수엔 영향이 없다. 다만 데이터를 합쳐서 `subject`로 거르면 271문항이 빠진다. 1번이랑 같은 곳이라 같이 올린다 |
| 3 | 정규식 허점 | lm-evaluation-harness 이슈 | 실제 점수에 영향이 있는지 먼저 센다(6주차 검증). 영향이 있으면 그 문항 수를 근거로 수정을 제안한다. 정규식은 데이터셋이 아니라 harness 채점 코드에 있어서 harness로 간다 |

- lighteval 구현은 원본 데이터를 그대로 쓰고 데이터셋 revision을 고정한다. 나중에 데이터가 고쳐져도 점수가 모르게 바뀌지 않게 하려는 것이다.

## 9. 검증 계획: 어떤 모델로 어떤 수치와 비교할지

같은 모델을 harness와 lighteval로 돌려서 직종별 정확도랑 문항별로 뽑힌 답이 같은지 보는 게 목표다.

비교 기준은 같은 모델·문항·설정으로 돌린 harness 결과다. 논문 Table 1은 옆에 참고로만 적고 합격 기준으로는 안 쓴다. 논문이 정규식 추출(v3.0, 2026-06)이 들어오기 전 버전으로 쟀을 수도 있어서다.

모델은 [`Qwen/Qwen2.5-1.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) 하나로 시작한다.
- 팀에 EXAONE-3.0-7.8B를 돌릴만한 GPU가 없어서 CPU로 돌릴 수 있는 작은 모델로 골랐다. 모델 실력을 보려는 게 아니라 두 도구 채점이 같은지 보는 거라 작은 모델이면 충분하다.
- 이 모델도 논문 Table 1에 점수가 있다(Direct 5-shot): doctor 33.33 / nurse 47.72 / pharm 35.48 / dentist 32.43, 평균 37.92. 직종별 점수를 test 문항 수로 가중해서 계산해도 37.92가 나온다(단순 평균은 37.24). 결과표에 이 수치를 참고로 같이 적는다.

GPU를 쓸 수 있게 되면 EXAONE-3.0-7.8B(논문 55.73)로 한 번 더 돌린다. 토크나이저랑 종료 토큰이 Qwen과 달라서 stop 문자열, EOS 처리 차이도 같이 볼 수 있다.

CPU라서 걱정되는 건 시간이다. 5-shot 프롬프트가 문항당 2,000자 정도라 3,009문항을 두 도구로 각각 돌리면 꽤 오래 걸릴 것 같다. 소규모로 먼저 돌려서 문항당 시간을 재 보고 전체 실행 계획을 잡는다.

고정할 것: 모델·토크나이저·데이터셋 revision, 두 도구 버전, CPU·float32·배치 크기 1, greedy, `max_gen_toks` 1024, stop 문자열, few-shot 5개 순서, chat template 끔.

순서:

1. 채점 테스트 (모델 없이): `C`, ` c`, `C.`, `(C)`, `정답： C`, `정답은 C입니다`, 빈 출력, ②의 허점 사례(`C가 정답`, `C번`, `C is a correct answer`)를 넣어서 lighteval metric과 harness `extract_choice` 결과가 같은지 본다. 허점 사례는 harness에서 각각 빈 값, 빈 값, `A`가 나오므로 lighteval도 똑같이 나와야 한다. `answer - 1`도 여기서 같이 확인한다.
2. 프롬프트 비교: 직종별 test 첫 문항의 5-shot 프롬프트를 두 도구에서 뽑아서 글자 하나하나 비교한다(doctor test 1번은 harness 기준 2,145자).
3. 소규모 실행: 직종별 20문항, 배치 크기 1. 생성 결과, 뽑힌 답, 정오를 문항별로 맞춰 본다.
4. 전체 실행: test 3,009문항. 직종별 정확도, 가중 평균, 단순 평균, 두 도구 차이(%p), 문항별 불일치 건수를 적는다. 원본 정규식과 고친 정규식으로 답이 갈리는 문항 수도 같이 센다. 모델이 영어 문장으로 답한 문항 수도 세서 ②의 "다르게 뽑는" 경우가 실제로 생기는지 본다.

같은 생성 결과에 대한 채점은 무조건 똑같아야 한다. 생성 결과부터 다르면 배치 크기 1로 다시 돌려서 구현·설정 문제인지 수치 연산 차이인지 나눠 본다.

### 결과 읽는 기준

찍기 기준선부터 정해 둔다. test 정답 분포(직접 집계, revision `79efd6f`):

| config | A | B | C | D | E | 한 보기만 찍었을 때 최고 |
| --- | --- | --- | --- | --- | --- | --- |
| doctor | 99 | 77 | 85 | 92 | 82 | A 22.76% |
| nurse | 163 | 165 | 174 | 187 | 189 | E 21.53% |
| pharm | 174 | 153 | 159 | 203 | 196 | D 22.94% |
| dentist | 152 | 141 | 170 | 179 | 169 | D 22.07% |
| 합계 | 588 | 536 | 588 | **661** | 636 | D 21.97% |

직종별 점수가 무작위(20%)나 그 직종 찍기 기준선보다 낮으면, 모델이 못 푼 것보다 채점(형식) 문제를 먼저 의심한다.

논문 Table 1에도 이상한 점수가 있다. gemma-2-2b-it doctor 13.33은 무작위보다 낮고, Qwen2.5-7B-Instruct nurse 27.33은 같은 계열 1.5B(47.72)보다 낮다. 답 형식이 정규식에 안 맞아서 틀렸을 가능성이 있다(추정).

그래서 전체 실행에서 정규식 4개가 다 안 걸린 문항 비율(추출 실패율)을 직종별로 센다. 이 수치는 이슈에서 log-likelihood 변형이 필요한지 물어볼 때 근거로 쓴다.

### 선택 실험 (할지는 10/18 세션에서 정함)

- log-likelihood 비교: 추출 실패율이 높은 직종만 같은 모델로 log-likelihood 방식으로 돌려 점수 차이를 본다.
- 데이터 오염 확인: 2024-03부터 HF에 공개된 기출이고 원 시험지는 국시원에 먼저 공개돼 있어서, 모델이 학습 중에 문제와 답을 봤을 수 있다.
  - 연도별 점수: test를 2022 / 2023 / 2024로 나눠 본다(2024년 964문항: doctor 150, nurse 291, pharm 271, dentist 252). HF에는 2022–2023년 문항이 2024-03에, 2024년 문항이 2024-08에 올라왔다.
  - 보기 순서 섞기: 내용을 알고 푸는 모델은 점수가 비슷하고, 정답 위치를 외운 모델은 떨어진다.
  - 문제 이어 쓰기: 질문 앞부분만 주고 원문과 거의 같게 이어 쓰는지 본다.
  - 원본과 다른 설정이라 기본 태스크에는 넣지 않고 실험으로만 한다.

선택 실험 결과는 PR 설명에 참고로만 적는다. 차이가 크게 나오면 메인테이너나 데이터셋 제작자와 공유할지 그때 팀에서 정한다.
