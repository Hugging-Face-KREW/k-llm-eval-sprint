# 벤치마크 분석 보고서: HRM8K

- 작성: B팀 최재희야 (정세엽, 김동우, 박현우)
- 기준: 2026-10-16. 데이터 `HAERAE-HUB/HRM8K` 리비전 [`c360cab`](https://huggingface.co/datasets/HAERAE-HUB/HRM8K/tree/c360cabf8d733a82455565358b3dc965aab9ba8d), Lighteval [`c2af9e5`](https://github.com/huggingface/lighteval/tree/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14)
- 10/10 팀 글을 바탕으로 원문, 코드, 데이터를 다시 확인해 고쳤다. 아래 실험 수치는 모델 없이 채점기만 돌려 얻었고, 재현 코드는 https://github.com/dw021213/hrm8k-lighteval-experiments (커밋 `c994677`)에 있다.

## 1. 한 줄 요약

같은 수학 문제를 한국어와 영어로 병렬 제공해, 모델이 한국어로 주어진 수학 문제를 풀고 최종 답을 맞히는지 측정한다. 논문의 관심사는 영어 입력 대비 한국어 입력에서 생기는 성능 격차다.

## 2. 출처

| 항목 | 내용 |
|---|---|
| 논문 | Hyunwoo Ko, Guijin Son, Dasol Choi. *Understand, Solve and Translate: Bridging the Multilingual Mathematical Reasoning Gap*. [arXiv 2501.02448](https://arxiv.org/abs/2501.02448) (2025-01, v2), MRL 2025 ([ACL Anthology](https://aclanthology.org/2025.mrl-main.6/)) |
| 데이터 소유 | HAERAE-HUB (HAE-RAE) |
| 공식 코드 | 없다. 데이터셋 카드는 평가 코드를 "Coming soon!"으로만 표시한다. 2저자 저장소 [guijinSON/HRM8K](https://github.com/guijinSON/HRM8K/blob/201024633c9ff92529dc73b2b3a99a135a21ffc6/README.md)에는 README와 리더보드만 있다 |
| 대신 쓰이는 구현 | lm-evaluation-harness `hrm8k` (커뮤니티 기여, 2025-01), HAE-RAE의 HRET. 6번에서 비교한다 |

논문은 HRM8K(벤치마크)와 UST(한국어 수학 성능을 올리는 파인튜닝 방법)를 함께 제안한다. 우리 구현 대상은 HRM8K의 평가 방식이다. UST는 모델 학습 방법이라 범위 밖이다.

## 3. 데이터셋

- Hugging Face ID: `HAERAE-HUB/HRM8K`
- config: `GSM8K`, `MATH`, `OMNI_MATH`, `MMMLU`, `KSM`
- split: `test` 하나뿐이다. train과 validation이 없어서 few-shot 예시를 뽑을 곳이 없고, 0-shot이 전제다.
- 문항 수: 8,011

| config | 문항 | 출처와 번역 | `answer` 자료형 | 추가 컬럼과 범주 |
|---|---:|---|---|---|
| `GSM8K` | 1,319 | GSM8K test 전체. 영→한, GPT-4o 번역과 사람 검수 | float64. 값은 모두 정수(`18.0`), 음수 2개, 최대 2,880,000 | `original` |
| `MATH` | 2,885 | MATH test 중 숫자 답만. 영→한, GPT-4o | float64. 값은 모두 정수 | `original`, `question-initial`, `level` 1–5, `type` 7개(대수 752, 예비대수 585, 정수론 469 등) |
| `OMNI_MATH` | 1,909 | Omni-MATH 중 숫자 답만. 영→한, GPT-4o | int64. 최대 66071772829247409 | `original`, `question-initial`, `difficulty` 1.0–9.5 |
| `MMMLU` | 470 | MMLU 수학 3과목 전체. 번역은 OpenAI의 사람 번역본 `openai/MMMLU` KO_KR을 쓴 것으로 보인다(아래 표) | int64. 보기 번호 1–4 | `original`, `subject`(고등학교 수학 270, 대학 수학 100, 추상대수 100) |
| `KSM` | 1,428 | 한국 시험·경시대회 원문. 한→영 번역이 `original`에 들어 있다 | string | `original`, `original_answer`, `category`(KMO 730, 전공수학 344, 수능/모의고사 210, KMS 82, KJMO 62), `difficulty`(KJMO 62개는 비어 있음) |

주요 필드:
- `question`: 한국어 문제. MMMLU는 보기 `1.`–`4.`가 문제 안에 들어 있다.
- `answer`: 정답.
- `original`: 영어 문제. GSM8K, MATH, OMNI_MATH, MMMLU에서는 영어 원문이고, KSM에서는 영어 번역본이다.

예시 2개:

```text
[KSM, 5번 행]
question: 좌표평면에서 원 \(x^2+y^2=4\) 위를 반시계방향으로 한 바퀴 도는 곡선을 \( C \)라 할 때,
          선적분 \[ \int_C (3+yx^2)dx+(2-xy^2)dy \] 의 값을 구하시오.
answer:   "-8\pi"   (string, 그린 정리로 -8π 확인)

[GSM8K, 0번 행]
question: Janet의 오리는 하루에 16개의 알을 낳습니다. ... 그녀는 매일 농산물 시장에서 얼마를 버나요?
answer:   18.0      (float64)
original: Janet’s ducks lay 16 eggs per day. ...
```

KSM 정답 1,428개를 정규식으로 나누면 이렇다.

| 형태 | 개수 |
|---|---:|
| 정수 | 1,199 |
| 소수 | 7 |
| 숫자 분수 | 90 |
| π·√·e·i가 들어간 식(집합 `{1}`, `{0}` 2개 포함) | 94 |
| 변수·집합·기호식(`e^x(x+1)`, `Z_6`, `\emptyset`, `160\pmod{275}` 등) | 38 |

KSM에는 보기 번호가 정답인 객관식이 약 76문항(대부분 전공수학), "…임을 보이고 … 구하시오" 꼴의 증명형 문항이 6개(10, 13, 26, 28, 110, 1381번 행) 있다.

문서끼리 서로 다른 점:

| 항목 | 논문 | 데이터셋 카드 | 2저자 README | 우리가 확인한 것 |
|---|---|---|---|---|
| MMMLU 번역 | 전부 GPT-4o 번역 | 같음 | OpenAI 사람 번역(MMMLU) | 문제 앞부분(정규화한 80자)이 `openai/MMMLU` KO_KR과 470/470 일치하고, 정답 번호도 A–D 순서와 470/470 일치. 문제 전문 비교는 하지 않았다 |
| OMNI_MATH 출처 | Omni-MATH | Omni-MATH | "Numina-Math" | config 이름과 `difficulty`(1–10 척도) 컬럼이 Omni-MATH와 맞음 |
| KSM OCR | GPT-4o | GPT-4 API | GPT-4o, 2인 교차 검수 | 확인 불가 |
| `answer` 자료형 | 숫자 답 | float64로 표시 | 없음 | config마다 다름(위 표) |

## 4. 라이선스와 접근

- 라이선스: MIT (데이터셋 카드 메타데이터)
- 약관 동의: 필요 없다(gated 아님). 토큰 없이 `load_dataset("HAERAE-HUB/HRM8K", "KSM", split="test")`로 받아지는 것을 확인했다.

## 5. 공식 평가 방식

### 5-1. 논문이 적은 것

| 항목 | 내용 | 확인한 곳 |
|---|---|---|
| 프롬프트 | 영어 지시문 "Solve the given question. After solving the problem, state your final answer in the following format: $\boxed{N}$." + 문제 + "Respond in Korean."(K2K) 또는 "Respond in English."(K2E, E2E) | 논문 부록 G, Figure 9·10 ([HTML v2](https://arxiv.org/html/2501.02448v2)) |
| 평가 조건 | K2K(한국어 문제, 한국어 풀이), K2E(한국어 문제, 영어 풀이), E2E(영어 문제, 영어 풀이). E2K는 영어 입력에서 한국어 풀이를 유지하지 못해 제외 | 논문 4.1절 |
| few-shot | 0-shot. 풀이 프롬프트에 예시가 없다. 5-shot은 번역 단계(TE) 프롬프트에만 쓴다 | 부록 G Figure 9·10, 4.3절 |
| 디코딩 | temperature 0.7, top_p 0.95, 출력 8–2,048 토큰. 낮은 temperature에서 영어·중국어로 넘어가는 현상 때문이라고 설명 | 부록 B |
| 정답 추출과 정규화 | **적혀 있지 않다.** 본문과 부록에서 `boxed`, `extract`, `exact`, `match`, `parse`를 검색해도 규칙 설명이 없다. 부록 E "Evaluation Methods"는 ELO와 토큰 비용만 다룬다 | 본문, 부록 A–G |
| 채점 원칙 | 증명형·식 답은 LLM 심판이 필요해서 빼고 숫자 답만 남겨 기계 검증한다(Prior Sets 기준) | 3.1절 |
| 지표 | 묶음별 정확도(%)와 5개 묶음의 단순 평균. Table 3의 7B K2K를 직접 계산하면 단순 평균 39.51(표 39.52), 문항 수 가중 평균 38.63 | Table 3, Table 9 |

논문 수치(Table 9, K2K):

| 모델 | GSM8K | MATH | OMNI_MATH | MMMLU | KSM | 평균 |
|---|---:|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B-Instruct | 28.13 | 20.69 | 8.64 | 18.51 | 3.78 | 15.95 |
| Qwen2.5-7B-Instruct | 66.41 | 50.36 | 18.96 | 50.00 | 11.83 | 39.52 |
| Qwen2.5-72B-Instruct | 89.46 | 74.73 | 30.07 | 69.79 | 25.35 | 57.88 |
| Llama-3.2-1B-Instruct | 7.88 | 10.50 | 4.77 | 10.43 | 2.80 | 7.28 |
| Llama-3.1-8B-Instruct | 57.47 | 31.20 | 11.73 | 32.98 | 5.25 | 27.73 |
| Llama-3.1-70B-Instruct | 78.62 | 56.12 | 20.38 | 57.87 | 11.83 | 44.96 |

같은 모델이라도 출처마다 수치가 다르다. 8번 9항목에 정리했다.

### 5-2. 가장 널리 쓰이는 구현: lm-evaluation-harness `hrm8k`

논문 대신 사실상의 기준 구현이다. [PR #2627](https://github.com/EleutherAI/lm-evaluation-harness/pull/2627)로 2025-01-20에 커뮤니티 기여자가 추가했고, 이슈에 "Hendrycks Math처럼 추가하고 싶다"고 적었다. 저자의 공식 구현은 아니다.

| 항목 | 내용 | 확인한 곳 |
|---|---|---|
| 프롬프트 | 한국어 지시문 "주어진 문제를 풀어보세요.\n문제를 푼 후, 최종 답변을 다음과 같은 형식으로 작성하세요: $\boxed{N}$.\n\n문제: {question}\n답변:". MMMLU는 "주어진 선택지 (1, 2, 3, 4) 중 최종 선택지를"로 바꾼 전용 문구. `hrm8k_en`은 영어 지시문과 `original` 사용 | [`default/utils.py`](https://github.com/EleutherAI/lm-evaluation-harness/blob/314f717677d4aa0c706fc1c6bbd3c801d321384a/lm_eval/tasks/hrm8k/default/utils.py), [`en/utils.py`](https://github.com/EleutherAI/lm-evaluation-harness/blob/314f717677d4aa0c706fc1c6bbd3c801d321384a/lm_eval/tasks/hrm8k/en/utils.py) |
| few-shot | 0 | [`default/_hrm8k_yaml`](https://github.com/EleutherAI/lm-evaluation-harness/blob/314f717677d4aa0c706fc1c6bbd3c801d321384a/lm_eval/tasks/hrm8k/default/_hrm8k_yaml) |
| 디코딩 | greedy(temperature 0), 최대 2,048 토큰, 종료 토큰만 stop. README에 "We default to greedy decoding"으로 논문과 다르다고 밝힘 | 같은 yaml, [README](https://github.com/EleutherAI/lm-evaluation-harness/blob/314f717677d4aa0c706fc1c6bbd3c801d321384a/lm_eval/tasks/hrm8k/README.md) |
| 정답 추출 | 마지막 `\boxed{}` → 없으면 마지막 `$…$` → 없으면 마지막 숫자. boxed 안에 `=`가 있으면 오른쪽만 | `utils.py` `parse_math_answer` |
| 정규화 | Hendrycks MATH의 `_strip_string`(공백·`\left`·`\$`·단위 제거, `0.5`→`\frac{1}{2}` 등) 뒤에 숫자는 `float`→정수 문자열 | `utils.py` `is_equiv`, `postprocess` |
| 지표 | `exact_match`: 정규화한 문자열이 같으면 1 | 같은 파일 |

### 5-3. 원본 벤치마크의 공식 채점

| 원본 | 공식 채점 | 근거 |
|---|---|---|
| GSM8K | 풀이 끝의 `#### 숫자`를 정규식으로 뽑아 쉼표를 지우고 문자열 비교 | [openai/grade-school-math `dataset.py`](https://github.com/openai/grade-school-math/blob/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/dataset.py) |
| MATH | 마지막 `\boxed{}`를 꺼내 `_strip_string`으로 정규화하고 문자열 비교 | [hendrycks/math `math_equivalence.py`](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/modeling/math_equivalence.py) |
| Omni-MATH | 규칙이 아니라 GPT-4o 심판(리더보드 전부), 대안으로 Omni-Judge 모델 | [KbsdJames/omni-math README](https://github.com/KbsdJames/omni-math/blob/23be225c8e268df51990f6c5c1448f34d3b56911/README.md) |
| MMMLU | "Answer: $LETTER"로 답하게 한 뒤 정규식 추출. 한국어 "정답:", "답:", "답변:"도 인식 | [openai/simple-evals `common.py`](https://github.com/openai/simple-evals/blob/5e623c2b400af62a1278e23595f95b0853d7fe8a/common.py) |
| KSM | 원본이 시험 문제라 공식 채점 코드가 없음 | - |

HRM8K는 이 다섯 가지를 "`\boxed{N}`에 쓴 최종 답 하나를 기계적으로 비교"하는 한 방식으로 통일했다. Omni-MATH는 원래 LLM 심판이 필요한 데이터인데, 숫자 답만 남겨 규칙 채점이 가능해졌다. MMMLU는 원래 A–D 글자로 답하지만 HRM8K에서는 보기 번호 1–4를 `\boxed{}`에 쓴다.

### 5-4. 팀 결정: 서브셋별 정답 비교 기준과 정규화 (제안, 팀 확인 필요)

모델 없이 "정답을 그대로 `\boxed{}`에 쓴 완벽한 답"을 8,011문항 전부 만들어 채점기마다 몇 %를 정답으로 인정하는지 쟀다.

| 묶음 | lm-eval `hrm8k` | Lighteval `expr_gold_metric` (gsm8k 태스크 지표) | 제안: 정답을 `$…$`로 감싸 Expr·LaTeX로 읽기 |
|---|---:|---:|---:|
| GSM8K | 99.8% | 100% | 100% |
| MATH | 100% | 100% | 100% |
| OMNI_MATH | 100% | 100% | 100% |
| MMMLU | 100% | 100% | 100% |
| KSM | 83.6% | 97.1% | 99.9% |
| 전체 | 97.1% (7,775) | 99.5% (7,970) | 100.0% (8,010) |

제안하는 규칙:

1. **정답(gold)**: float인 정수값은 정수 문자열로 바꾼다(`18.0`→`18`). int는 그대로 문자열로, KSM은 문자열 그대로 둔다. `float()`로 다시 바꾸지 않는다. `66071772829247409`가 `float`을 거치면 `…408`로 바뀐다.
2. **정답 읽기**: 모든 정답을 `$…$`로 감싸 Lighteval의 `ExprExtractionConfig`와 `LatexExtractionConfig`로 읽는다. 이렇게 하면 KSM의 `-8\pi`, `\frac{1}{6}`, `e^2`까지 sympy 식이 된다.
3. **예측 읽기**: `LatexExtractionConfig(boxed_match_priority=0)`로 `\boxed{}`를 가장 먼저 찾고, `ExprExtractionConfig`를 함께 쓴다(gsm8k 태스크와 같은 구성). `\boxed{}`가 없으면 lm-eval처럼 마지막 숫자로 대체한다(10/18 세션 결정, 8번 8항).
4. **비교**: Lighteval `compare_gold_target`(sympy 동치, `precision=5`)을 쓴다. 표기가 달라도 값이 같으면 맞고, 근사값은 틀린다.
5. **MMMLU**: 보기 번호가 정수라 같은 지표를 쓴다. 프롬프트만 MMMLU 전용 문구로 한다.

같은 정답을 다르게 쓴 경우의 실험 결과다(일부).

| 정답 | 모델이 쓴 답 | lm-eval | Lighteval 기존 | 제안 |
|---|---|:-:|:-:|:-:|
| `-8\pi` | `\boxed{-8\pi}`, `\boxed{-8 \pi}`, `\boxed{-8π}` | X | X | O |
| `-8\pi` | `\boxed{-25.13}` (근사값) | X | X | X |
| `\frac{1}{2}` | `\boxed{0.5}`, `\boxed{1/2}`, `\boxed{\frac12}` | X | O | O |
| `-10` | `\boxed{-10}` | X | O | O |
| `2880000` | `\boxed{2,880,000}`, `\boxed{\$2,880,000}` | X | O | O |
| `18` | `\boxed{18달러}` | X | X | X |
| `4` (MMMLU) | `\boxed{4번}`, `\boxed{④}` | X | X | X |
| `2880000` | `\boxed{288만}` | X | X | X |

한국어 단위와 표기(`달러`, `번`, `④`, `만`)는 어느 방식도 인정하지 않는다. 이걸 정규화에 넣을지는 공식 방식과 달라지는 선택이라 멘토와 정한다.

### 5-5. 팀 제안: 프롬프트와 디코딩 (팀 확인 필요)

1. **프롬프트: lm-eval `hrm8k`의 한국어 지시문을 그대로 쓴다.** MMMLU는 lm-eval의 선택지 전용 문구를 쓴다.
   - 이유: 한국어 벤치마크라 지시문도 한국어가 자연스럽다. 같은 프롬프트를 쓰면 lm-eval 결과와 문항 단위로 비교할 수 있다.
   - 대가: 논문 K2K(영어 지시문 + "Respond in Korean")와 조건이 달라서, 논문 Table 9과의 비교는 근사치가 된다.
2. **디코딩: greedy(temperature 0)로 한다.**
   - Lighteval 기본값이라 태스크에 따로 쓰지 않는다. `model_input.py` L42에서 `temperature=0`이고, `transformers_model.py` L817에서 `do_sample=False`가 된다.
   - 논문 설정은 실행 옵션으로 보조 실행한다: `"model_name=…,generation_parameters={temperature:0.7,top_p:0.95}"`
3. **풀이 언어는 강제하지 않는다.** lm-eval도 "한국어로 답하라"는 문장이 없다.
   - 논문 Table 9에서 풀이 언어의 효과(K2K→K2E)는 작고 방향도 일정하지 않다: Qwen2.5-1.5B +5.2, 7B +1.8, Llama-3.2-1B 0.0, Llama-3.1-8B −1.7.
   - 반면 입력 언어의 효과(K2E→E2E)는 Qwen2.5-1.5B에서 +16.0이다. 한국어 벤치마크에서 핵심은 문제를 한국어로 주는 것이다.
   - 검증 실행에서 답안의 한글 비율로 풀이 언어 분포를 기록한다.
4. **"숫자만 적으시오" 같은 문구는 넣지 않는다.** 한국어 단위를 줄이려는 문구지만, KSM 정답 222개가 수식이라 역효과가 난다.
   - 제안 채점기로 확인하면 `-8\pi`, `e^2`, `\frac{32}{15}\pi`는 소수로 쓰면 자릿수와 상관없이 오답이다.
   - `\frac{1}{6}`도 소수점 아래 5자리 이상(0.16667)을 써야 정답이다.
   - 한국어 단위가 실제로 얼마나 나오는지는 검증 실행의 details에서 먼저 센다.

### 5-6. 객관식(MMMLU) 채점: 생성형으로 한다 (팀 제안, 팀 확인 필요)

MMMLU도 다른 네 묶음처럼 풀이를 생성하게 하고, 보기 번호를 `\boxed{N}`에 쓴 것으로 채점한다. 프롬프트는 lm-eval의 MMMLU 전용 문구("주어진 선택지 (1, 2, 3, 4) 중 최종 선택지를 다음 형식으로 작성하세요: $\boxed{N}$.")를 쓴다.

- **이유**: 논문과 lm-eval `hrm8k`가 MMMLU를 이렇게 채점했다. 논문의 MMMLU 열과 5개 묶음 평균을 비교하려면 같은 방식이어야 한다(멘토 안내 "원본 기준").
- **검토했지만 쓰지 않는 방법: 선택지 확률(log-likelihood).**
  - KMMLU(A팀)와 Lighteval `openai_mmlu`가 쓰는 방식이다. KMMLU는 전부 4지선다다(45개 과목, test 35,030, train 208,522, dev 225).
  - 연습 태스크로 HRM8K MMMLU에도 적용해 봤다(SmolLM2-135M, 20문항, acc 0.45 ± 0.11). 구성은 보기 포함 문제 + `"\n정답:"`, `choices = [" 1", " 2", " 3", " 4"]`, `LogLikelihoodAccMetric`이다.
  - 그래도 세 가지 이유로 쓰지 않는다.
    1. 논문 수치와 비교할 수 없다.
    2. 같은 470문항을 같은 방식으로 채점하는 `openai_mmlu_kor_*`와 완전히 겹친다.
    3. 보기 라벨이 숫자라서, 보기 내용이 숫자인 87문항에서 라벨과 보기 값이 헷갈린다.
- **확률 방식의 한국어 MMMLU가 필요하면** 기존 `openai_mmlu_kor_*`가 그 역할을 한다. 지금은 한국어 단어장 문제로 실행되지 않으므로, 단어장을 채우는 작은 PR(#1179와 겹침)을 메인테이너에게 제안한다.
- **생성형에서 남는 주의점**: 보기 내용이 숫자인 87문항은 모델이 번호 대신 보기 값을 `\boxed{}`에 쓰면 다른 번호로 채점될 수 있다(Known Issues).
- KSM 안의 객관식 약 76문항도 생성형으로 채점한다. 다른 문항과 섞여 있고 보기 수도 4–5개로 다르다.

## 6. 기존 구현

| 구현 | 프롬프트 | 디코딩 | 정답 추출 | 비교 | 비고 |
|---|---|---|---|---|---|
| 논문 | 영어 지시문 + "Respond in Korean/English" | T 0.7, top_p 0.95 | 공개 안 됨 | 공개 안 됨 | 단일 실행으로 보임 |
| [lm-eval `hrm8k`](https://github.com/EleutherAI/lm-evaluation-harness/tree/314f717677d4aa0c706fc1c6bbd3c801d321384a/lm_eval/tasks/hrm8k) | 한국어 지시문(논문 프롬프트의 번역이 아님) | greedy, 2,048 | 마지막 boxed → `$…$` → 마지막 숫자 | MATH 정규화 + 문자열 일치 | 정답 쪽에도 `parse_math_answer`를 적용해 `-10`→`10`, `\frac{1}{2}`→`2`가 된다. 236문항(GSM8K 2, KSM 234)은 완벽한 답도 정답 처리되지 않는다 |
| [HRET (HAE-RAE)](https://github.com/HAE-RAE/haerae-evaluation-toolkit/blob/5af1d3fbc2a6c78bfb22f7cce26cec67e7219f86/llm_eval/datasets/hrm8k.py) | 영어 "put your final answer within \boxed{}.\nQuestion: {question}" | 설정 파일에 따름 | [math_verify](https://github.com/HAE-RAE/haerae-evaluation-toolkit/blob/be92b652568c29d2c96f797ea04be1b7d90a0fb4/llm_eval/evaluation/math_eval.py) `parse` | math_verify `verify`(sympy) | 데이터 소유 조직의 도구. math_verify는 Lighteval 추출 엔진과 같은 계열 |
| wandb llm-leaderboard-korean, daekeun-ml/evaluate-llm-on-korean-dataset | - | - | - | - | 코드 검색으로 HRM8K 구현이 있는 것만 확인했다(내용 미검토) |
| Lighteval | HRM8K 없음 | | | | 관련 태스크는 아래 |

Lighteval의 관련 태스크:
- [`gsm8k`](https://github.com/huggingface/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/gsm8k.py#L58-L86): `lighteval accelerate` 경로의 `prompt_function`은 `Question: …\nAnswer:` 형식이고, inspect-ai 경로의 solver만 `ANSWER: $ANSWER` 형식을 쓴다. 지표는 `expr_gold_metric`, 생성 256토큰, stop `Question:`
- [`math`](https://github.com/huggingface/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/math.py): `maj@4`, stop `"\n"`. 이 stop을 그대로 쓰면 풀이가 첫 줄에서 잘린다
- `math_500`: 생성 32,768토큰
- `mgsm`: 한국어가 없다
- `openai_mmlu_kor_*`: HRM8K MMMLU 470문항과 **같은 문항**이다. 다만 선택지 확률(loglikelihood) 방식이라 채점 방식이 다르다 그리고 `c2af9e5` 기준으로 이 태스크는 실행되지 않는다. 한국어 단어장에 `answer`와 `question_word`가 없어서 문제 카드를 만드는 단계에서 `AttributeError`가 난다(PR #1179가 고치려는 문제). 다국어 태스크는 `lighteval[multilingual]` 추가 설치도 필요하다.

## 7. 중복 확인

검색일 2026-10-16. 저장소 `huggingface/lighteval`의 이슈와 PR을 `gh search`로 찾았다.

| 키워드 | 결과 |
|---|---|
| `HRM8K` | 0건 (이슈, PR 모두) |
| `korean` | [#1424](https://github.com/huggingface/lighteval/issues/1424) KMMLU 제안 이슈(열림), [#1425](https://github.com/huggingface/lighteval/pull/1425) KMMLU PR(열림), [#1179](https://github.com/huggingface/lighteval/pull/1179) 한국어 번역 문구 보완 PR(열림, 2026-03 이후 리뷰 없음), #356 Translation literals(머지) |
| `haerae`, `KMMLU` | #1424, #1425 |
| 소스 코드 | `src/lighteval`에 `hrm8k`, `HAERAE` 없음 |

HRM8K 자체는 중복이 없다. MMMLU 묶음만 기존 `openai_mmlu_kor`와 문항이 겹친다.

## 8. 구현하면서 어려울 것 같은 부분

1. **정답 형식이 config마다 다르다.** float64, int64, string이 섞여 있고, KSM에는 수식 222개(변수·집합 38개 포함)가 있다. 5-4의 규칙으로 해결 가능해 보이지만, 문항별 판정을 lm-eval과 비교해 차이를 설명해야 한다.
2. **lm-eval과 수치가 체계적으로 다를 수 있다.** lm-eval은 완벽한 답도 236문항에서 오답 처리한다. 그래서 같은 모델 출력이라도 우리 쪽 KSM 점수가 더 높게 나올 수 있다. 이 차이가 버그가 아니라는 근거를 남겨야 한다.
3. **어느 프롬프트를 쓸지.** 논문 K2K 프롬프트는 영어 지시문 + "Respond in Korean"이고, lm-eval `hrm8k`는 지시문 전체가 한국어다. 제안은 lm-eval 쪽이다(5-5). 대가로 논문 수치와는 근사 비교가 된다.
4. **디코딩.** 논문은 T 0.7 샘플링, lm-eval은 greedy다. 제안은 greedy다(5-5). greedy에서는 모델이 풀이를 영어나 중국어로 바꾸거나(논문 부록 B), 작은 모델이 같은 문장을 반복해 2,048토큰을 다 채울 수 있다.
5. **채팅 템플릿.** Lighteval은 instruct 모델이면 채팅 템플릿을 자동으로 켜고, lm-eval은 기본이 꺼져 있다. 비교할 때 어느 쪽인지 적어야 한다.
6. **생성 길이와 stop.** 2,048토큰이 필요하고, `math` 태스크처럼 `"\n"`을 stop으로 쓰면 풀이가 잘린다.
7. **`Language.KOREAN`을 쓰면 지표가 바로 죽는다.** Lighteval의 한국어 번역 문구에 `answer`(그리고 `and_word`, `or_word`)가 없어서 `MultilingualExtractiveMatchMetric(language=Language.KOREAN)`이 `AttributeError`를 낸다. PR #1179가 일부를 채우지만 머지되지 않았고 `and_word`는 빠져 있다. 당장은 English 설정으로 `\boxed{}` 위주 추출을 하게 되고, "정답:" 같은 한국어 앵커는 인식되지 않는다. 이 문제는 HRM8K 이슈와 분리해 별도 이슈 초안(`issue-draft-korean-literals.md`)으로 올린다.
8. **`\boxed{}`가 없을 때 숫자를 줍는 대체 규칙.** 10/18 세션에서 lm-eval처럼 **마지막 숫자로 대체**하기로 정했다. 연습 태스크를 SmolLM2-135M으로 돌렸을 때 모델이 문제 문장("하루에 5번")을 반복했는데 채점기가 그 숫자를 뽑아 정답(5)과 맞은 사례가 있었다(가짜 정답). 그래서 검증 실행에서 대체 규칙이 쓰인 답의 수를 세어 함께 보고한다.
9. **기준 수치가 출처마다 다르다.** 같은 모델이라도 논문 Table 3 상단, 논문 Table 9 K2K, 2저자 README 리더보드의 수치가 다르다.

   | 모델 | Table 9 K2K | Table 3 상단 / README | 차이 |
   |---|---:|---:|---|
   | Qwen2.5-1.5B-Instruct | 15.95 | README 15.95 | 같음 |
   | Llama-3.2-1B-Instruct | 7.28 | README 7.28 | 같음 |
   | Qwen2.5-7B-Instruct | 39.52 | README 37.00 | 다름 |
   | Llama-3.1-8B-Instruct | 27.73 | README 39.39 | 크게 다름 |
   | Qwen2.5-72B-Instruct | 57.88 | Table 3·README 56.63 | 다름 |
   | Llama-3.1-70B-Instruct | 44.96 | Table 3·README 45.61 | 다름 |

10. **객관식과 증명형.**
    - KSM 객관식 약 76문항은 보기 번호가 정답인데, 일반 문제 프롬프트를 쓴다.
    - KSM 증명형 6문항은 "보이고 … 구하시오"의 마지막 값만 채점한다.
    - MMMLU 87문항은 보기 내용 자체가 정수다(예: 10번 행의 3번 보기가 "1"). 모델이 번호 대신 보기 값을 `\boxed{}`에 쓰면 다른 보기 번호로 채점될 수 있다.

### Known Issues (팀 결정: 오류 문항을 제외할지 그대로 둘지)

C팀 질문에 대한 멘토 답변 형식(`문항 key / 문제 유형 / 영향`)으로 정리했다. HRM8K에는 문항 ID 컬럼이 없어서, 문항 key는 리비전 `c360cab` 기준 `config` + 0부터 센 행 번호 + 문제 앞부분으로 적었다.

| 문항 key | 문제 유형 | 영향 | 근거 |
|---|---|---|---|
| `KSM` 3번 행 · "함수 f(x, y) = x²/(√(x²+y²))³에 대하여 다음 적분의 값을…" | 정답 오류. `answer`와 `original_answer`가 모두 `\frac{x-3}{4}`(π→x 오타로 추정) | 맞는 답 (π−3)/4를 써도 오답. KSM 최대 정확도가 1문항(0.07%p) 낮아짐 | 극좌표에서 (π/8 − 1/4) − (1/2 − π/8) = (π−3)/4. 수치 적분 0.035398 |
| `KSM` 201번 행 · "5개의 숫자 1, 2, 3, 4, 5를 일렬로 나열할 때…" | 정답 형식 깨짐. 두 정답 컬럼 모두 `\frac[13}{20}` | 어떤 채점기도 정답을 읽지 못해 맞는 답 13/20도 오답(1문항) | 포함배제: 120 − (24 + 24 − 6) = 78, 78/120 = 13/20 |
| `KSM` 109번 행 · "3차원 유클리드 공간 ℝ³에서 비틀림률…곡선 β" | 정답 기호 오타. 두 정답 컬럼 모두 `\sqrt{1+r^2}`(τ→r) | sympy가 r과 τ를 다른 기호로 봐서 `\sqrt{1+\tau^2}`도 오답(1문항) | β′ = N, β″ = −T + τB라 κ_β = √(1+τ²). β‴ ∥ N이라 τ_β = 0 |
| `KSM` 323번 행 · "실수 전체의 집합을 ℝ, 유리수 전체의 집합을 ℚ라 하자…" | 영어 정답 불일치. `answer`는 1, `original_answer`는 4 | `answer` 컬럼으로 채점하면 영향 없음(lm-eval도 `answer` 사용). `original_answer`를 쓸 때만 영향 | ㄱ(포함사상은 연속) 참, ㄴ(부분공간 위상의 성질) 참 → 1번 |
| `KSM` 1427번 행 · "A와 B가 바닥에서 출발하여 단의 개수가 12개인 계단을…" | 정답 오류. 두 정답 컬럼 모두 `\frac{6}{(1-x)^4}`(확률인데 x가 들어 있음) | 맞는 답 40/81을 써도 오답(1문항) | A는 확률 1/4로 3번, B는 확률 1/6으로 2번 성공해야 이긴다. 급수 합과 상태 전이 방정식 두 방법 모두 40/81 |
| `KSM` 1262번 행 · "네 문자 A, B, C, D를 일렬로 나열하여 만든 문자열…" | 정답이 섞인 것으로 보임. 두 정답 컬럼 모두 `3\times4^p`(문제에 p가 없고, 1258번 행의 정답과 같음) | 어떤 답도 정답 처리되지 않음(1문항) | 각 문자를 n개씩 쓸 때의 최댓값을 n = 1, 2, 3에서 전수 조사하면 3n²(3, 12, 27). n = 2020이면 12,241,200으로 추정 |
| `KSM` 1254번 행 · "양의 정수 n(≥ 2)에 대하여 다음 세 조건을 모두 만족하는…" | 확인 필요. 정답 `C_n`은 문제에 정의되지 않은 기호 | 모델이 같은 기호를 쓸 수 없어 사실상 채점 불가 | 풀이는 확인하지 못함 |
| `KSM` 1396, 1420번 행 | 정답의 변수 이름(t)이 문제에 없음. 값은 맞음 | 모델이 λ나 x로 쓰면 sympy가 다른 식으로 판정 | 1396: x⁴을 곱하는 사상의 고윳값이 모두 1이라 (t−1)⁴. 1420: u = y²로 두면 u″ − 4u′ + 3u = 0이라 y = 2e^{3t/2} |
| `KSM` 82번 행 · "실수값을 갖는 두 함수 u(x, y), v(x, y)…" | 오류 아님. 약분하지 않은 정답 `\frac{3}{3}` | 문자열 비교 채점기는 `1`을 오답 처리. sympy 비교는 정답 처리 | 문제가 "f(0)을 분자, u의 상수항을 분모로" 요구. 평균값 성질로 u(0,0) = 3, f(0) = 3 |
| 데이터셋 카드·논문 | 문서 불일치(MMMLU 번역 출처, OMNI_MATH 출처 표기, KSM OCR 모델, `answer` 자료형) | 점수에는 영향 없음. 재현 문서의 정확성 문제 | 3번 표 |
| `MMMLU` 87문항, `KSM` 객관식 약 76문항 | 보기 번호와 보기 값의 혼동 | 모델이 값을 쓰면 오답이거나 다른 번호로 채점 | 10번 항목 |
| 전 묶음 | 한국어 단위·표기(`달러`, `번`, `④`, `만`) | 비교한 세 채점기 모두 오답 처리 | 5-4 사례표 |

정답이 틀리거나 깨진 문항은 확정 4개(3, 109, 201, 1427번 행)와 의심 2개(1254, 1262번 행)다. 확정분만 빼도, 모든 문제를 맞힌 모델이 KSM에서 받을 수 있는 최대 점수는 1,424/1,428(99.72%)이다.

찾은 범위의 한계: 변수 문자가 들어간 정답 30개는 모두 문제와 대조했다(문제에 없는 문자 8개 중 6개는 정상이거나 변수 이름 문제). 정답이 숫자인 문항의 오류는 문제를 직접 풀어야 알 수 있어서 확인하지 못했다.

처리 방침. C팀 질문에 대한 멘토 답변을 B팀에도 적용했다(팀 확인 필요).
1. **Lighteval 구현은 원본 데이터 그대로 한다.** `hf_revision`을 `c360cab`로 고정해서, 나중에 데이터가 고쳐져도 점수가 조용히 바뀌지 않게 한다. 논문이 비워 둔 부분(답 추출과 비교)은 5-4의 규칙을 쓰고, lm-eval과 달라지는 점은 Known Issues로 문서화한다.
2. **데이터 오류(3, 109, 201, 323, 1427번 행)와 의심 문항(1254, 1262번 행)은 제작자에게 제보한다.** 제보처는 [HAERAE-HUB/HRM8K Community](https://huggingface.co/datasets/HAERAE-HUB/HRM8K/discussions)다. 2026-10-16 기준 봇 글 1건 외에 제보가 없다. 게시 전에 초안을 멘토님께 공유해 검토받는다.
3. **채점 기준 개선은 분석과 제안까지만 한다.** 한국어 단위, 원문자, 보기 값 혼동이 대상이다. 영향받는 문항 수와 판정이 달라지는 사례를 이 표로 정리한다.
4. **우선순위는 Lighteval 구현이다.** 이슈 분석에 시간을 너무 쓰지 않는다.

## 9. 검증 계획

1. **채점기 일치 검증 (모델 없이)**
   - 같은 모델 출력에 lm-eval 채점기와 우리 채점기를 둘 다 돌려 문항별로 비교한다.
   - 판정이 다른 문항을 모두 목록으로 만들고, 차이마다 이유(5-4의 규칙)를 붙인다.
   - 5-4 사례표의 입력은 단위 테스트로 옮긴다.
2. **종단 검증 (모델로 실행)**
   - 기준 모델은 Qwen2.5-1.5B-Instruct, K2K 조건, 5개 묶음 전체(8,011문항)다.
   - 1차 비교 대상은 **같은 모델을 같은 설정(한국어 프롬프트, greedy, 채팅 템플릿)으로 lm-eval `hrm8k`에 돌린 결과**다(10/18 멘토 피드백). 논문 수치는 영어 지시문과 temperature 0.7로 낸 결과라 우리 설정과 다르다. lm-eval은 `--apply_chat_template`으로 돌려 Lighteval과 조건을 맞춘다.
   - 논문 Table 9 K2K(28.13 / 20.69 / 8.64 / 18.51 / 3.78, 평균 15.95)는 보조 참고로 본다. 2저자 README 리더보드와 값이 같은 몇 안 되는 모델이고 크기도 작다.
   - 보조로 Llama-3.2-1B-Instruct(7.28)를 돌린다.
   - 고정할 설정:
     - 프롬프트: lm-eval 한국어 지시문(5-5 제안)
     - 최대 2,048토큰, stop 없음
     - 채팅 템플릿 켬
     - greedy를 기본으로, 논문 설정(T 0.7, top_p 0.95)은 1회 추가
     - `hf_revision` `c360cab`, Lighteval 커밋
   - 함께 기록할 것: 답안의 한글 비율로 본 풀이 언어 분포, `\boxed{}` 안에 한국어 단위가 들어간 답의 수, `\boxed{}`가 없는 답의 수
   - 판단 기준: lm-eval과는 같은 모델 출력에 두 채점기를 돌렸을 때, 채점 규칙 차이로 설명되는 문항(정답 파싱 236문항, 쉼표 등)을 빼면 판정이 모두 같아야 한다. 논문과는 설정이 달라 근사 비교만 하고, 묶음별 표준오차(GSM8K ±1.2%p, MATH ±0.8%p, OMNI_MATH ±0.6%p, MMMLU ±1.8%p, KSM ±0.5%p)의 2배를 넘으면 원인을 기록한다.
   - 1.5B 모델로도 8,011문항 × 최대 2,048토큰은 노트북 CPU로 오래 걸린다. GPU(vLLM 백엔드) 환경을 멘토와 확인한다.
3. **집계 구조 검증**
   - 태스크 이름을 `hrm8k:gsm8k`처럼 붙이면 Lighteval이 `hrm8k:_average`로 묶음 단순 평균을 자동으로 낸다. 연습 태스크로 확인했다.
   - 이 값이 논문 평균 정의(5개 단순 평균)와 같은지 실제 결과로 한 번 더 확인한다.
