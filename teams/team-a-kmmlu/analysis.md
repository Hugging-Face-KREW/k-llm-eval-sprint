# 벤치마크 분석 보고서 — KMMLU

> 팀: 베이직파이브 · 데이터셋: [HAERAE-HUB/KMMLU](https://huggingface.co/datasets/HAERAE-HUB/KMMLU)
> 상태: 초안 (팀 리뷰 전). 10/10 발표 글 「261011 KMMLU 논문과 데이터셋 분석」을 옮기고, 외부 링크는 2026-10-14에 확인했습니다. 10/17 자료 보완 완료

## 1. 한 줄 요약: 무엇을 측정하는가

KMMLU는 한국어로 출제된 실제 시험에서 수집한 45개 과목의 4지선다 문제를 통해 언어 모델의 전문 지식과 문제 해결 능력을 평가하는 벤치마크다.

## 2. 출처: 논문, 저자, 연도, 공식 코드

- 논문: _KMMLU: Measuring Massive Multitask Language Understanding in Korean_, arXiv [2402.11548](https://arxiv.org/abs/2402.11548) (2024)
- 저자: Guijin Son, Hanwool Lee, Sungdong Kim, Seungone Kim, Niklas Muennighoff, Taekyoon Choi, Cheonbok Park, Kang Min Yoo, Stella Biderman
- 공식 평가 코드: [EleutherAI/lm-evaluation-harness의 KMMLU 태스크](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/kmmlu). [논문 서론의 각주 2](https://arxiv.org/html/2402.11548v2#S1)에서 평가 코드로 직접 안내한다.
- 개발팀의 관련 저장소: [HAE-RAE/lm-evaluation-harness](https://github.com/HAE-RAE/lm-evaluation-harness)는 위 저장소의 포크이며, [haerae-evaluation-toolkit (HRET)](https://github.com/HAE-RAE/haerae-evaluation-toolkit)은 KMMLU를 포함한 여러 벤치마크를 지원하는 통합 평가 도구다.
- 전용 저장소 확인: 2026-10-16 기준 논문, 데이터셋 카드, [HAE-RAE의 공개 저장소 목록](https://github.com/orgs/HAE-RAE/repositories)에서 KMMLU만을 위한 독립 GitHub 저장소는 확인되지 않았다. 데이터셋은 Hugging Face의 `HAERAE-HUB`에서 제공하며, 개발팀의 GitHub 조직명은 `HAE-RAE`다.
- 비교 기반: MMLU, Hendrycks et al., [2009.03300](https://arxiv.org/abs/2009.03300)

## 3. 데이터셋: Hugging Face ID, config와 split, 문항 수, 필드, 예시 2개

- **Hugging Face ID**: `HAERAE-HUB/KMMLU`
- **Config**: 과목별 45개 (예: `Accounting`, `Korean-History`, `Math`). 과목은 HUMSS / STEM / Applied Science / Other 네 범주로 묶인다.
- **Split**: HF의 split 이름은 `train` / `dev` / `test`이다 (논문의 Validation = HF의 `dev`).

| Split | 문항 수 | 용도                                |
| ----- | ------- | ----------------------------------- |
| train | 208,522 | 학습·하이퍼파라미터 튜닝            |
| dev   | 225     | few-shot 예시 (과목당 5개 × 45과목) |
| test  | 35,030  | 평가 (과목당 최소 100문항)          |
| 합계  | 243,777 |                                     |

- **구축 과정** (논문): 자격·면허 시험, PSAT, 수능 등 533개 출처에서 371,002문항 크롤링 → 중복·파싱 오류 제거, 선택지를 4개로 정리해 243,777문항 → 6개월 공개 후 커뮤니티 피드백으로 741문항 수정 → 저작권 자료가 포함된 test 147문항 교체.
- **필드**:
  - `question` (string): 문제 본문
  - `A`, `B`, `C`, `D` (string): 선택지
  - `answer` (int, 1–4): 정답 번호 (1=A … 4=D)
  - `Category` (string): 과목 이름
  - `Human Accuracy` (float, null 가능): 실제 응시자 정답률.
- **예시 2개** (test split, datasets-server로 확인):

  ```
  # Korean-History, test 1번 행 (0부터 셈) — 정답 3 (C)
  question: (가) 국가에 대한 설명으로 옳은 것은? (가)의 사신 고제덕 등이 일본에 와서 왕이 보낸 국서를 전하였다 .
            그 국서에 이르기를 "나(대무 예 )는 큰 나라를 맡아 여러 주변국을 다스렸으며 , 고구려의 옛 땅을 회복하였고
            부여의 풍속을 이었다 ."라고 하였다 .
  A: 나 당연합군의 공격으로 멸망하였다 .
  B: 9주 5소경의 지방 행정 구역을 두었다 .
  C: 중앙 행정 기구로 3성 6부를 설치하였다 .
  D: 고구려의 수도였던 평양을 서경으로 삼았다 .
  Human Accuracy: null
  ```

  ```
  # Computer-Science, test 1번 행 — 정답 4 (D)
  question: 정보통신 시스템의 구성요소 중 데이터 처리계에 해당하는 것은?
  A: 단말장치
  B: 데이터 전송회선
  C: 통신제어장치
  D: 중앙컴퓨터
  Human Accuracy: 0.0556
  ```

  첫 예시처럼 원문에 비정상 띄어쓰기(`대무 예`, `하였다 .`)가 남아 있다.

## 4. 라이선스와 접근: 라이선스, 약관 동의 필요 여부

- **라이선스**: CC BY-ND 4.0 (HF 데이터셋 카드의 `license: cc-by-nd-4.0`)
- **접근**: gated 아님. 약관 동의나 로그인 없이 내려받을 수 있다.
- **출처 표시(BY)**: 데이터나 문항을 공유할 때는 제공된 저작자·저작권·라이선스·면책 고지를 유지하고, 원본 자료와 라이선스 링크를 표시한다 ([CC BY-ND 4.0 §3](https://creativecommons.org/licenses/by-nd/4.0/legalcode.en#s3)). 태스크 코드와 문서에도 데이터셋 출처와 라이선스를 명시한다.
- **구현 시 유의점**: ND(변경 금지) 조건이 있으므로, lighteval 태스크는 데이터를 가공해 다시 배포하지 않고 HF에서 직접 불러와 프롬프트만 구성한다.

## 5. 공식 평가 방식: 프롬프트 형식, few-shot 수와 출처, 채점 방식, 정답 추출·정규화, 지표, 논문 수치

### 프롬프트 형식 (Direct)

```
{question}
A. {A}
B. {B}
C. {C}
D. {D}
정답：
```

- 논문의 Direct 프롬프트이며, 마지막 콜론은 **전각 콜론 `：`**이다. 일반 콜론 `:`으로 바꾸지 않고 원문을 유지한다. ([논문 부록 G·Figure 12](https://arxiv.org/html/2402.11548v2#A7))
- 하네스도 같은 형식을 사용하며, `question.strip()`으로 질문 앞뒤 공백을 제거한다. `kmmlu`와 `kmmlu_direct`의 `doc_to_text`는 동일하다. ([loglikelihood 프롬프트](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/default/_default_kmmlu_yaml#L5), [Direct 프롬프트](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/direct/_direct_kmmlu_yaml#L5))

### few-shot 수와 출처

- **논문 설정**: Direct와 CoT 모두 **5-shot**으로 평가한다. ([논문 §4.1](https://arxiv.org/html/2402.11548v2#S4.SS1))
- **Direct 예시 출처**: 같은 과목의 `dev` split 5문항을 사용한다. ([논문 §3.2](https://arxiv.org/html/2402.11548v2#S3.SS2), [하네스 `fewshot_split`](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/direct/_direct_kmmlu_yaml#L1-L6))
- **CoT 예시 출처**: 풀이를 포함해 별도로 구성한 과목별 예시 5개를 사용한다. 하네스에서는 과목별 yaml의 `fewshot_config.samples`에 들어 있다. ([논문 §3.3](https://arxiv.org/html/2402.11548v2#S3.SS3), [회계학 예시 설정](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/cot_hard/kmmlu_cot_hard_accounting.yaml#L13-L26))
- **실행 시 주의**: `kmmlu`, `kmmlu_direct` yaml에는 `num_fewshot`이 없어 **별도 지정 없이 실행하면 0-shot**이다. 논문과 맞추려면 `--num_fewshot 5`를 지정해야 한다. CoT 변형에는 `num_fewshot: 5`가 명시돼 있다. ([0-shot 기본값 처리](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/evaluator.py#L342-L345), [CoT 설정](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/cot_hard/_cot_kmmlu_yaml#L18))

### 채점 방식, 정답 추출, 정규화

| 구현·근거 | `output_type` | 정답을 얻는 방식 | 정규화 |
| --- | --- | --- | --- |
| [`kmmlu`](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/default/_default_kmmlu_yaml#L2-L11) | `multiple_choice` | 선택지 `A`–`D`의 log-likelihood를 비교해 가장 큰 것을 예측으로 사용 | 해당 없음 |
| [`kmmlu_direct`](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/direct/_direct_kmmlu_yaml#L6-L22) | `generate_until` | 확률이 가장 높은 토큰을 차례로 생성한다(greedy). `Q:`, 빈 줄(`\n\n`), `</s>`, `.` 중 하나가 나오면 답변 생성을 멈추고, 정규화한 출력이 정답 문자와 일치하면 정답으로 채점한다(`exact_match`). | `ignore_case`(대소문자 무시), `ignore_punctuation`(구두점 무시), `regexes_to_ignore: [" "]`(일반 공백 제거) |
| [`kmmlu_cot_hard`](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/cot_hard/_cot_kmmlu_yaml#L5-L25) | `generate_until` | 풀이를 생성(`질문:` 출력 시 생성 중단)한 뒤 정규식 `(?<=정답은)\s*[(]?(A\|B\|C\|D)[)]?.*(?=입니다.)`로 정답 문자를 추출하고 `exact_match`로 채점 | `ignore_case`(대소문자 무시), `ignore_punctuation`(구두점 무시) |

- **정답 매핑**: Direct는 데이터의 `answer` 1–4를 정답 문자 A–D로 바꾼다. 설명에서 답만 골라내는 별도 정규식은 사용하지 않고, **정규화한 출력 전체**를 정답 문자와 비교한다. 따라서 `B.`는 정답 B와 일치하지만, `정답은 B`나 선택지 내용을 풀어 쓴 답은 오답이 된다. ([정답 매핑·정규화 설정](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/direct/_direct_kmmlu_yaml#L6-L22), [`exact_match` 구현](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/api/metrics.py#L234-L266))
- 논문의 CoT도 정규식으로 최종 답을 추출한다. 점수는 최종 답의 정답률이며, 풀이 문장을 따로 채점하지는 않는다. 위 표의 CoT 이름은 하네스의 실제 등록 이름인 `kmmlu_cot_hard`를 따른다. ([논문 §4.1](https://arxiv.org/html/2402.11548v2#S4.SS1), [CoT 그룹 설정](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/cot_hard/_kmmlu_cot_hard.yaml#L1-L9))
- 참고로 MMLU 원본(GPT-3) 평가는 `Answer:`로 끝나는 프롬프트에서 `max_tokens=1`, `logprobs=100`으로 A–D의 로그 확률을 비교한다. 하네스 README는 `kmmlu`가 MMLU 원본 구현 방식을 따른다고 설명한다. ([원본 `evaluate.py`](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/evaluate.py#L26-L88), [하네스 README](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/README.md#L24-L30))

### 지표

- **정확도(Accuracy)**: 정답으로 채점된 문항의 비율이다. **네 보기 중 하나를 같은 확률로 고르면** 기대 정확도는 25%다. 생성형 모델의 출력은 A–D로 제한되지 않으므로, 이를 생성형 평가의 하한으로 보지는 않는다. ([논문 Table 3](https://arxiv.org/html/2402.11548v2#S4.T3), [생성 방식 설명 §4.1](https://arxiv.org/html/2402.11548v2#S4.SS1))
- **집계 방식 주의**: 논문 결과표는 과목별 정확도의 **macro average**다. 하네스의 `kmmlu`와 `kmmlu_direct` 그룹은 `weight_by_size: True`로 문항 수를 가중한 **micro average**가 기본이므로, 논문과 비교할 때는 과목별 점수를 macro로 집계한다. ([논문 Table 3](https://arxiv.org/html/2402.11548v2#S4.T3), [loglikelihood 그룹 설정](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/default/_kmmlu_default.yaml#L7-L9), [Direct 그룹 설정](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/direct/_kmmlu_direct.yaml#L7-L9), [하네스 README의 주의사항](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/README.md#L9))

### 논문 수치

5-shot Direct, 전체 KMMLU의 과목별 정확도 macro 평균 (주요 모델 발췌). 출처: [논문 Table 3의 Average 열](https://arxiv.org/html/2402.11548v2#S4.T3).

| 모델              | 평균 정확도 |
| ----------------- | ----------- |
| Polyglot-Ko-12.8B | 29.26%      |
| Llama-2-13B       | 31.26%      |
| Yi-6B             | 34.70%      |
| Yi-Ko-6B          | 40.55%      |
| Yi-34B            | 43.90%      |
| Yi-Ko-34B         | 50.46%      |
| Qwen-72B          | 50.83%      |
| HyperCLOVA X      | 53.40%      |
| GPT-4             | 59.95%      |

- 수집된 인간 응시자 정답률의 평균은 62.6%이며, 저자들은 80%를 전문가 최소 수준에 대응하는 기준으로 제안한다. 다만 시험·응시자 집단이 달라 모델 점수와 직접 비교하는 데 주의가 필요하다고 설명한다. ([논문 §3.2](https://arxiv.org/html/2402.11548v2#S3.SS2))
- 한국사: GPT-4 35%, HyperCLOVA X 42%. [Table 20](https://arxiv.org/html/2402.11548v2#A10.T20)을 기준으로 하며, [서론](https://arxiv.org/html/2402.11548v2#S1)에는 HyperCLOVA X가 44%로 적혀 있어 차이가 있다.
- KMMLU-HARD, Direct → CoT 정확도(%): Qwen-72B-Chat 22.59 → 18.18, HyperCLOVA X 17.06 → 27.11, GPT-3.5-Turbo 21.10 → 20.70, GPT-4-Turbo 30.52 → 25.28. CoT가 항상 성능을 높이지는 않는다. ([논문 Table 4](https://arxiv.org/html/2402.11548v2#S6.T4))

### 이번 주 팀 결정: 기본 채점 방식

- **결론**: 기본 채점은 **생성형 Direct 방식**(하네스 `kmmlu_direct`에 대응)으로 결정한다. `dev`의 같은 과목 예시 **5개**를 사용하고, greedy로 생성한 답변을 정규화한 뒤 정답 문자 A–D와 `exact_match`로 비교한다.
- **선정 이유**:
  1. **기존 기여 보완**: 외부 기여자의 PR [#1425](https://github.com/huggingface/lighteval/pull/1425)가 loglikelihood 방식을 다루고 있어, 여기에 포함되지 않은 생성형 평가를 추가하는 방향으로 기여할 수 있다.
  2. **논문의 평가 방식 반영**: 논문의 주요 결과는 **5-shot Direct 생성 방식**이다. 같은 평가 방식을 lighteval에서도 사용할 수 있도록 한다. ([논문 §4.1](https://arxiv.org/html/2402.11548v2#S4.SS1), [Table 3](https://arxiv.org/html/2402.11548v2#S4.T3))
  3. **명확한 검증 기준**: 하네스에 이미 [`kmmlu_direct`](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/kmmlu/direct/_direct_kmmlu_yaml)가 있어, 같은 모델·문항·설정으로 실행한 결과를 문항 단위로 비교할 수 있다.
  4. **기존 생성형 평가 기능 활용**: lighteval의 [`mmlu.py`](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/tasks/tasks/mmlu.py#L46-L58)도 생성 결과를 `exact_match`로 채점한다. 기존 생성형 평가 기능을 활용해 KMMLU 태스크를 추가할 수 있다.
- **유의점**: `정답은 B`처럼 출력 형식 때문에 오답이 될 수 있다. 하네스와 동일한 중단·정규화·채점 규칙을 유지하고, 형식 오류의 발생 비율은 검증 과정에서 확인한다. 검증 기준은 같은 조건으로 실행한 하네스 결과이며, 논문 점수 자체의 재현을 목표로 하지는 않는다.

## 6. 기존 구현: 공식 코드, 다른 평가 도구

| 도구                  | 구현                                                                                                        | 비고                                                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| lm-evaluation-harness | [`lm_eval/tasks/kmmlu/`](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/kmmlu) | `default`(`kmmlu`, 확률), `direct`(`kmmlu_direct`, 생성), `hard`, `direct_hard`, `cot_hard`. 논문 저자들이 통합 |
| lighteval (`main`)    | 없음                                                                                                        | 한국어는 `global_mmlu`, `openai_mmlu` 등 번역·다국어 세트로만 평가                                              |
| lighteval (열린 PR)   | [#1425](https://github.com/huggingface/lighteval/pull/1425)                                                 | 아래 7번 참고                                                                                                   |

lighteval의 참고 구현: `src/lighteval/tasks/multilingual/tasks/cmmlu.py`, `turkish_mmlu.py`

- CMMLU와 TurkishMMLU는 영어 MMLU를 단순 번역한 것이 아니라, **각 언어권의 자료를 수집해 별도로 구축한 데이터셋**을 사용한다.
- 두 구현 모두 **log-likelihood 방식**으로 정답 후보의 확률을 비교해 채점한다.

## 7. 중복 확인과 기여 대안

### 현재 상황

`huggingface/lighteval` 저장소를 `kmmlu`, `KMMLU korean`, `HAERAE`로 검색해 외부 기여자 CY-HYUN의 이슈와 PR을 확인했다. **2026-10-17 재확인 기준, KMMLU 추가 제안은 이미 있지만 아직 병합되지 않았다.**

- 이슈 [#1424](https://github.com/huggingface/lighteval/issues/1424): KMMLU 추가를 제안하면서 **HAE-RAE Bench와 KoBEST도 추가할 의향**을 함께 밝혔다. 현재 open이며 댓글은 없다.
- PR [#1425](https://github.com/huggingface/lighteval/pull/1425): 45개 과목을 **loglikelihood 방식**으로 구현했다. 작성자는 Qwen2.5-0.5B-Instruct로 5개 과목 700문항을 0-shot 평가해 하네스와 프롬프트·예측이 일치했다고 보고했다. 현재 open이며 **생성형 평가는 포함하지 않는다.**

따라서 검토할 선택지는 **생성형 평가를 별도 이슈로 제안하기**, **기존 이슈에 코멘트로 제안하기**, **다른 벤치마크로 변경하기**다.

### 대안 1. KMMLU 생성형 평가를 별도 이슈로 제안

**언어별 벤치마크의 평가 방식**

- [CMMLU](https://github.com/huggingface/lighteval/blob/main/src/lighteval/tasks/multilingual/tasks/cmmlu.py), [TurkishMMLU](https://github.com/huggingface/lighteval/blob/main/src/lighteval/tasks/multilingual/tasks/turkish_mmlu.py), [ArabicMMLU](https://github.com/huggingface/lighteval/blob/main/src/lighteval/tasks/multilingual/tasks/arabic_mmlu.py)는 loglikelihood 방식이다.
- 아르메니아어 ArmBench-LLM은 **생성형 평가를 사용하는 PR** [#1289](https://github.com/huggingface/lighteval/pull/1289)이 열려 있다. 번역·요약·NER·품사 태깅과 객관식 평가를 함께 포함하므로, KMMLU와는 태스크 구성에 차이가 있다.
- 조사한 MMLU 계열 구현은 loglikelihood 방식이지만, 생성형 평가를 제안하는 사례도 있다.

**같은 벤치마크에 다른 평가 방식을 추가한 사례**

| 사례           | 제안 내용                                                                         | 확인된 진행 상황 (2026-10-17 기준)                                                                                                                                                                                                                                        |
| -------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GPQA           | 기존 loglikelihood 평가에 생성형 평가 추가                                        | 이슈 [#70](https://github.com/huggingface/lighteval/issues/70)에서 메인테이너가 두 방식의 공존에 동의했다. 이후 생성형 태스크를 추가한 PR [#534](https://github.com/huggingface/lighteval/pull/534)가 병합됐다.                                                           |
| HellaSwag·PIQA | 기본 태스크가 생성형으로 바뀐 뒤, 하네스와 비교할 수 있는 loglikelihood 변형 추가 | 이슈 [#1090](https://github.com/huggingface/lighteval/issues/1090)에서 기존 방식 복원을 요청했고, 외부 기여자의 PR [#1315](https://github.com/huggingface/lighteval/pull/1315)가 열려 있다. 이슈에 메인테이너 응답이 없고, PR은 제출 후 약 3개월간 리뷰 없이 대기 중이다. |

두 PR 모두 기존 태스크를 유지하면서 별도 이름의 태스크를 추가했다. 조사한 범위에서는 **같은 벤치마크의 평가 방식별로 이슈를 각각 연 선례는 찾지 못했다.** 위 사례만으로 메인테이너의 사전 동의가 병합 여부를 결정한다고 단정할 수는 없지만, 구현에 앞서 추가 방식과 범위를 확인할 필요는 있다.

### 대안 2. 기존 이슈 #1424에 생성형 평가 추가 의사를 코멘트

**KMMLU를 계속 진행한다면 우선 검토할 방향이다.** #1424에 하네스의 `kmmlu_direct`에 대응하는 생성형 평가를 추가하고 싶다는 의사를 밝히고, 메인테이너와 범위를 합의한 뒤 별도 PR을 제안한다. 기존 PR의 loglikelihood 구현과 생성형 평가의 역할을 구분해 설명할 수 있다.

### 대안 3. 다른 벤치마크로 변경

HAE-RAE Bench와 KoBEST는 #1424 작성자가 이미 추가 의향을 밝혔으므로 **기여 범위가 겹칠 가능성이 있다.** 기여 자체가 불가능한 것은 아니지만, 새로운 대안으로 CLIcK을 검토할 수 있다.

- **데이터셋**: [CLIcK](https://aclanthology.org/2024.lrec-main.296/)은 수능·TOPIK·공무원 시험 등 공식 시험과 교재를 바탕으로 구축한 한국 문화·한국어 이해 평가 벤치마크다. 역사·정치·생활문화·문법·독해 등을 포함한 **11개 분야, 1,995개 객관식 문항**으로 구성된다. 일부 문항은 KIIP 교재를 바탕으로 GPT-4가 생성한 뒤 사람이 검수했다. ([논문 §3.1–3.2](https://arxiv.org/html/2403.06412v2#S3.SS1))
- **활용 사례**: KMMLU보다 규모는 작지만, [네이버 HyperCLOVA X THINK 기술 보고서](https://clova.ai/cdn/media/2025/06/HyperCLOVA_X_THINK_Technical_Report.pdf)와 [SKT A.X 3.1 모델 카드](https://huggingface.co/skt/A.X-3.1/blob/main/README.md)에서 한국어·문화 이해 평가에 사용된 것을 확인할 수 있다.
- **선행 확인 사항**: 2026-10-17 기준 [공식 저장소](https://github.com/rladmstn1714/CLIcK)에 평가 코드가 없고, 저장소와 [HF 카드](https://huggingface.co/datasets/EunsuKim/CLIcK)에서 데이터 라이선스 표기도 확인되지 않았다. 하네스에는 5지선다 문항의 다섯 번째 보기를 프롬프트에 표시하지 않는 문제가 있어, 그대로 검증 기준으로 사용하기 어렵다. ([언어 영역 코드](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/click/click_lang/utils.py#L6-L32), [문화 영역 코드](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/click/click_cul/utils.py#L6-L32))
- **검토 방향**: CLIcK을 대안 후보로 두되, **라이선스와 평가 방식·검증 기준을 먼저 확인한 뒤 기여 가능성을 판단한다.**

**최종 기여 방향은 운영진과 상의할 필요가 있다.**

## 8. 구현하면서 어려울 것 같은 부분

하네스의 [`kmmlu_direct`](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/kmmlu/direct/_direct_kmmlu_yaml)에 맞춰 **정답 문자 A–D를 직접 생성해 채점하는 방식**을 구현할 때 예상되는 어려움은 다음과 같다.

1. **하네스와 입력을 정확히 맞추기**: 두 평가 도구의 few-shot 구성 방식이 다를 수 있어, 같은 예시를 사용해도 순서·공백·줄바꿈까지 동일하게 맞추는 데 주의가 필요하다.
2. **생성 중단과 채점 규칙 재현하기**: 중단 문자열 처리나 정규화가 조금만 달라도 같은 답변이 서로 다르게 채점될 수 있어, 하네스의 처리 방식을 정확히 재현해야 한다.
3. **결과가 다를 때 원인 구분하기**: 출력 차이가 태스크 구현 오류인지, 추론 설정이나 수치 연산의 차이인지 구분하기 어렵다. 최종 점수뿐 아니라 입력과 생성 출력, 채점 과정을 단계별로 확인해야 한다.

## 9. 검증 계획: 어떤 모델로 어떤 수치와 비교할지

- **목표**: **주 모델 1개로 전체 평가하고, 다른 계열의 보조 모델 1개로 표본을 교차 검증**한다. 각 모델에서 lighteval과 하네스 `kmmlu_direct`의 입력·출력·채점이 일치하는지 확인한다.
- **환경**: **H200 GPU**에서 두 모델을 한 개씩, 양자화 없이 **BF16**으로 실행한다. 7–8B급 모델을 사용해 전체 문항 평가와 불일치 원인 분석에 자원을 배분한다.

| 역할      | 모델                                                                                        | 선정 이유                                                                                                    | 검증 범위                                                |
| --------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| 주 모델   | [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)                      | 한국어를 지원하며 vLLM 실행 방법이 공식 문서에 제공되어, 전체 평가의 기준 모델로 사용하기 적합하다.          | 전체 45개 과목, 35,030문항의 5-shot 평가                 |
| 보조 모델 | [Kanana-1.5-8B-Instruct-2505](https://huggingface.co/kakaocorp/kanana-1.5-8b-instruct-2505) | 한국어·영어 중심의 모델이며, Qwen과 토크나이저·시작/종료 토큰이 달라 모델에 따른 처리 차이를 확인할 수 있다. | 45개 과목에서 각 20문항, 총 900문항의 0-shot·5-shot 평가 |

두 모델은 각각 vLLM이 지원하는 Qwen2·Llama 구조를 사용한다. 같은 Qwen 계열의 크기만 바꾸는 것보다 입력·종료 처리의 차이를 검증하기에 적합한 조합으로 판단했다. ([Qwen 설정](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/config.json), [Kanana 설정](https://huggingface.co/kakaocorp/kanana-1.5-8b-instruct-2505/blob/main/config.json), [vLLM 지원 목록](https://docs.vllm.ai/en/latest/models/supported_models/))

**비교 기준 수치**: 동일한 모델·문항·설정으로 하네스 `kmmlu_direct`를 실행해 얻은 정확도를 기준으로 한다. 각 모델에서 lighteval과 하네스의 **과목별 정확도 및 macro·micro 평균 차이(%p)**, **문항별 채점 불일치 건수**를 비교한다. Qwen은 전체 문항, Kanana는 동일한 900개 표본을 기준으로 비교하며, 기준 점수는 검증 실행 시 산출한다.

**비교 조건**: 모델·토크나이저·데이터셋 revision과 평가 도구·vLLM 버전을 고정한다. 각 모델에 대해 양쪽 도구의 greedy 설정, 최대 출력 길이, 중단 조건, 시작/종료 토큰 처리, few-shot 순서를 맞춘다. `repetition_penalty` 등 모델 기본 생성 설정이 반영되는지도 확인해 **실제 적용값을 양쪽에서 동일하게 지정·기록한다**. ([Qwen의 기본 생성 설정](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/generation_config.json)) **채팅 템플릿은 끄고** 하네스의 원문 프롬프트를 사용하며, 원본 문항을 임의로 제외하지 않는다.

검증은 다음 순서로 진행한다.

1. **채점 테스트**: 45개 과목 등록과 정답 매핑을 확인한다. GPU 실행에 앞서 `B`, `b`, `B.`, `(B)`, `정답은 B`, 빈 출력 등의 정규화·정오 판정이 하네스와 일치하는지 검사한다.
2. **소규모 비교**: 두 모델 모두 Korean-History·Math·Accounting의 각 20문항으로 **0-shot → 5-shot**을 실행한다. 배치 크기 1에서 입력 토큰, 생성 출력, 정규화 결과, 정오 판정을 비교한다.
3. **전체·교차 검증**: 소규모 검증 후 Qwen은 전체 35,030문항, Kanana는 과목별 표본 900문항으로 범위를 넓힌다. 표본은 고정한 seed로 뽑아 문항 목록을 저장하고, 양쪽 도구에 동일하게 사용한다. 배치는 입력이 잘리지 않고 메모리가 허용하는 범위에서 늘린다.
4. **결과 정리**: 모델·shot 설정별로 두 도구의 과목별 정확도, **macro average(과목 평균)·micro average(평가 문항 전체의 정확도)**와 점수 차이(%p)를 나란히 기록한다. 문항별 채점 불일치 건수·출력 형식 오류 사례와 재현 명령·설정을 남기고, Kanana의 표본 점수는 전체 KMMLU 점수와 구분해 표시한다.

**판정 기준**: 각 모델에서 입력 구성과 동일한 출력에 대한 채점은 완전히 일치해야 한다. 생성 결과가 다르면 배치 크기 1로 재검증해 구현·설정 오류와 추론 과정의 수치 차이를 구분하고, 설명되지 않은 불일치는 해결한다. 논문이나 모델 카드의 점수, #1425의 loglikelihood 점수는 합격 기준으로 삼지 않는다.

---

### 읽고 난 뒤 남은 질문 (발표 글에서)

- 생성형 평가에서 출력 형식 때문에 생기는 오답은 얼마나 되는가? 그 영향이 무시할 만한 수준인가?
- 분야별 벤치마크가 있는데도 MMLU·KMMLU 같은 종합 벤치마크를 쓰는 가치는 무엇인가?

### 참고 자료

- KMMLU 논문: https://arxiv.org/abs/2402.11548
- 데이터셋: https://huggingface.co/datasets/HAERAE-HUB/KMMLU
- lm-evaluation-harness KMMLU: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/kmmlu
- lighteval 이슈 #1424, PR #1425: https://github.com/huggingface/lighteval/pull/1425
- 데이터 오류 목록: [error_list.md](error_list.md)
