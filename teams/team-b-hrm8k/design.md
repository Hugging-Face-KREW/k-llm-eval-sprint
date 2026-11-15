# 설계 문서: HRM8K를 Lighteval에 옮기기

> 팀: 최재희야(B팀) · 분석 보고서: [analysis.md](analysis.md)
>
> 기준 버전: 데이터셋 리비전 `c360cab`, lm-evaluation-harness `314f717`, Lighteval `c2af9e5`
>
> 근거 코드: [hrm8k_proto.py](https://github.com/dw021213/hrm8k-lighteval-experiments/blob/c994677a3a41a8e5e841f0046e26b18214ad8275/hrm8k_proto.py)
>
> 상태: 초안. 3번 프롬프트, 4번 대체 규칙, 4번 MMMLU 채점, 6번 검증 기준은 팀 회의에서 확정한다.

## 1. 태스크 이름, 파일 위치

- 파일: `src/lighteval/tasks/tasks/hrm8k.py`. 채점기 파일이 따로 없어서 파일 하나로 끝난다.
- 태스크: `hrm8k:gsm8k`, `hrm8k:math`, `hrm8k:omni_math`, `hrm8k:mmmlu`, `hrm8k:ksm`
- 이름을 `hrm8k:<subset>`으로 두면 Lighteval이 `hrm8k:_average`를 만든다. 이 값은 다섯 묶음의 단순 평균이라 논문의 집계와 같다.
- `hrm8k|0`로 실행하면 다섯 태스크가 모두 돈다.

파일 맨 위 설명 블록은 다음과 같다.

```text
name:
HRM8K

dataset:
HAERAE-HUB/HRM8K

abstract:
Korean math reasoning benchmark with 8,011 problems in 5 subsets.

languages:
korean

tags:
math, reasoning

paper:
https://arxiv.org/abs/2501.02448
```

## 2. subset, 평가 split, few-shot split

| subset | 문항 | 평가 split | few-shot | `answer` 자료형 |
|---|---:|---|---|---|
| `GSM8K` | 1,319 | `test` | 없음 | float64 (값은 모두 정수) |
| `MATH` | 2,885 | `test` | 없음 | float64 (값은 모두 정수) |
| `OMNI_MATH` | 1,909 | `test` | 없음 | int64 |
| `MMMLU` | 470 | `test` | 없음 | int64 (보기 번호 1-4) |
| `KSM` | 1,428 | `test` | 없음 | string (LaTeX 식 222개) |

- 데이터셋에는 `test` split만 있어서 0-shot으로 평가한다. `few_shots_split=None`, `few_shots_select=None`으로 둔다.
- `hf_revision="c360cabf8d733a82455565358b3dc965aab9ba8d"`로 데이터를 고정한다.

## 3. prompt function: 원본 필드와 `Doc` 대응표

| `Doc` 필드 | 값 | 원본 필드 |
|---|---|---|
| `query` | 지시문 + `문제: {question.strip()}\n답변:` | `question` |
| `choices` | `[_gold(answer)]` | `answer` |
| `gold_index` | `0` | 없음 |

```py
INSTRUCTION = "주어진 문제를 풀어보세요.\n문제를 푼 후, 최종 답변을 다음과 같은 형식으로 작성하세요: $\\boxed{N}$.\n\n"
INSTRUCTION_MMMLU = (
    "주어진 문제를 풀어보세요.\n문제를 푼 후, 주어진 선택지 (1, 2, 3, 4) 중 최종 선택지를 "
    "다음 형식으로 작성하세요: $\\boxed{N}$.\n\n"
)


def _gold(answer) -> str:
    if isinstance(answer, float) and answer.is_integer():
        answer = int(answer)
    return f"${answer}$"
```

- `_gold`는 `18.0`을 `$18$`로 바꾼다. `$...$`로 감싸야 KSM의 LaTeX 정답을 식으로 읽는다.
- 프롬프트는 lm-eval `hrm8k`와 같다. 프로토타입의 `query`를 lm-eval의 `doc_to_text`, `doc_to_text_mmmlu` 결과와 비교했더니 8,011문항 모두 글자 단위로 같았다(`e7_prompt_parity.py`).
- `original` 컬럼은 쓰지 않는다. 영어 입력은 이번 범위가 아니다.

## 4. 채점: 지표, 생성 길이, stop sequence, 정답 추출 규칙

| 항목 | 값 | 이유 |
|---|---|---|
| 지표 | `MultilingualExtractiveMatchMetric`을 쓴 `extractive_match` | 숫자와 LaTeX 정답을 값으로 비교한다. |
| 예측 읽기 | `ExprExtractionConfig()`, `LatexExtractionConfig(boxed_match_priority=0)` | `\boxed{}`를 먼저 찾는다. |
| 정답 읽기 | `ExprExtractionConfig()`, `LatexExtractionConfig()` | `expr_gold_metric`은 `8\pi`를 `8`로 읽는다. |
| 비교 | sympy, `precision=5` | `0.5`와 `\frac{1}{2}`를 같게 본다. |
| 언어 | 기본값(영어) | 5번 표 참고 |
| 생성 길이 | `generation_size=2048` | lm-eval과 논문의 최대 길이다. 프로토타입의 256에서 바꾼다. |
| stop sequence | `stop_sequence=[]` | 풀이가 여러 줄이라 `"\n"`을 쓰면 답 전에 끊긴다. |
| 디코딩 | greedy (Lighteval 기본 temperature 0) | lm-eval과 같다. |
| 집계 | `corpus_level_fn=np.mean` | 묶음 정확도를 내고, `_average`로 다섯 묶음의 단순 평균(macro)을 낸다. |

정답 추출 규칙은 다음 순서다.

1. `\boxed{}`를 먼저 찾는다.
2. `\boxed{}`가 없으면 "final answer is", "Answer:" 뒤의 값을 찾는다. 한국어 답에는 이 표지가 거의 없다.
3. 그것도 없으면 맨 오른쪽 숫자나 식을 쓴다. 대체 규칙이 쓰인 답의 수는 검증 때 함께 보고한다.

MMMLU도 같은 지표로 채점한다. 모델은 `\boxed{번호}`를 쓰고, 정답 `1`-`4`와 값으로 비교한다.

정답을 그대로 `\boxed{}`에 넣은 답으로 8,011문항을 채점한 결과다(E2).

| 채점기 | GSM8K | MATH | OMNI_MATH | MMMLU | KSM | 전체 8,011문항 |
|---|---:|---:|---:|---:|---:|---:|
| lm-eval `hrm8k` | 99.8% | 100% | 100% | 100% | 83.6% | 97.1% |
| lighteval `expr_gold_metric` | 100% | 100% | 100% | 100% | 97.1% | 99.5% |
| 제안 | 100% | 100% | 100% | 100% | 99.9% | 8,010/8,011 |

이 표는 모델 정확도가 아니다. 정답을 답으로 넣었을 때 채점기가 인정하는 비율이다. 제안 방식이 놓친 1문항은 정답이 `\frac[13}{20}`로 깨진 KSM 201번이다.

대표 점수는 `hrm8k:_average`의 단순 평균(macro)이다. 전체 맞힌 수를 8,011로 나눈 값(micro)과 다르므로 PR과 발표에서 구분해 적는다.

## 5. 공식 방식과 다른 점과 그 이유

| 항목 | 논문 | lm-eval `hrm8k` | 이 구현 | 이유 |
|---|---|---|---|---|
| 지시문 | 영어 + "Respond in Korean" | 한국어 | 한국어 | 한국어 벤치마크이고, lm-eval과 문항 단위로 비교할 수 있다. |
| 디코딩 | temperature 0.7, top_p 0.95 | greedy | greedy | 결과가 재현된다. |
| 정답 추출 | 적혀 있지 않음 | 마지막 `\boxed{}`, `$...$`, `=` 뒤 값, 마지막 숫자 순서 | 4번의 순서 | Lighteval 공용 지표를 쓴다. |
| 비교 | 적혀 있지 않음 | 정답에도 추출기를 돌린 뒤 문자열 비교 | sympy 값 비교 | lm-eval 방식은 `-10`, `\frac{1}{2}` 등 236문항을 맞힐 수 없다. |
| stop | 적혀 있지 않음 | 종료 문자열 4개 | 모델 EOS | 태스크에 stop을 두지 않는다. |
| 언어 설정 | 해당 없음 | 해당 없음 | 영어 기본값 | `Language.KOREAN`은 번역 문구가 비어 오류가 난다. 이 버그는 HRM8K 범위 밖이다. |
| 영어판 | 해당 없음 | `hrm8k_en` 있음 | 넣지 않음 | 한국어 평가만 이번 범위다. |

대체 규칙은 lm-eval과 완전히 같지 않다.

- lm-eval은 마지막 숫자를 보기 전에 마지막 `$...$` 값과 `=` 뒤 값을 먼저 본다.
- lm-eval은 `5개`처럼 숫자 바로 뒤에 글자가 붙으면 건너뛴다. Lighteval은 그 숫자를 집는다.
- 예를 들어 `최종 답변: 12` 다음 줄에 `사과는 5개였습니다.`가 있으면 lm-eval은 12, Lighteval은 5를 고른다.

데이터 오류는 고치지 않는다. KSM 3, 109, 201, 1427번은 정답이 틀렸거나 깨져 있고, 1254, 1262번도 틀린 것으로 보인다. 리비전을 고정하고 docstring에 행 번호를 적은 뒤 제작자에게 알린다. 자세한 내용은 analysis.md 8번에 있다.

알려진 한계는 다음과 같다.

- `\boxed{18달러}`, `\boxed{288만}`처럼 한국어 단위가 붙은 답은 어떤 채점기에서도 틀린다.
- `\boxed{}`가 없는 답은 한국어 표지를 쓰지 못한다.
- `\boxed{}`가 없는 답에서는 최종 답 뒤에 나온 방법 번호, 신뢰도, 참고 번호 같은 숫자를 답으로 집을 수 있다. 박현우가 만든 합성 답 10개(C01 ~ C10)에서 이 채점기는 `\boxed{}`를 쓴 2개만 사람 판정과 같았다. lm-eval은 4개, `expr_gold_metric`은 3개가 같았다.
- `최종 답은 19입니다. 이 답에 대한 신뢰도는 18%입니다.`(정답 18)는 정답으로 채점된다. 추출기가 `18%`에서 수식 `18*(1/100)`과 문자열 `"18"`을 함께 내고, 문자열 대체(`fallback_mode="first_match"`)에서 `"18"`이 정답 문자열과 같기 때문이다. 대체를 끄면(`no_fallback`) 이 사례는 고쳐지지만, 정답 입력 채점이 8,010에서 8,004로 줄어든다. `\pm\frac{1}{r}` 같은 KSM 정답 6개가 문자열로만 맞기 때문이다. 그래서 대체는 유지하고, `\boxed{}` 없는 답의 수를 보고한다.

## 6. 테스트 계획

| 단계 | 입력 | 확인할 것 |
|---|---|---|
| 프롬프트 | `lighteval tasks inspect "hrm8k:mmmlu\|0" --num-samples 1` | 출력을 PR에 붙인다. 다섯 태스크 모두 프롬프트가 lm-eval과 같은지 본다. |
| 등록 | `pytest tests/unit/tasks/test_registry.py` | `hrm8k:*`가 등록된다. |
| 채점 단위 테스트 | `\boxed{18}`, `\boxed{-8\pi}`, `\boxed{\frac{1}{2}}`, `\boxed{1,234}` | 같은 값의 다른 표기를 정답으로 본다. |
| 오탐 테스트 | 풀이 중간 숫자만 있는 답, `\boxed{}`가 여러 개인 답, 단위가 붙은 답, `66071772829247409`와 `66071772829247408` | 틀린 답을 정답으로 보지 않는지 확인한다. 큰 정수의 1 차이는 구분해야 한다. |
| 전체 정답 입력 | 8,011문항의 정답을 `\boxed{}`에 넣은 답 | KSM 201번만 틀리고 8,010문항을 맞힌다. |
| 스타일 | `make style && make quality` | CI 조건을 통과한다. |
| 끝까지 실행 | `SmolLM2-135M-Instruct`, 10문항, `--save-details` | 다섯 태스크와 `_average`가 끝까지 돈다. |
| lm-eval 비교 | 11/8 세션에서 고른 모델, 전체 문항 | 아래 기준을 본다. |

`--show-config`는 `c2af9e5`와 현재 upstream `main` 모두에서 `TypeError`가 나서 쓰지 않는다.

lm-eval 비교는 세 단계로 본다.

1. 같은 프롬프트에서 두 도구의 생성 결과가 문항별로 같은지 본다.
2. 같은 출력 텍스트를 lm-eval과 Lighteval 채점기에 모두 넣어 문항별 판정을 비교한다. 생성 차이와 채점 차이를 나누기 위해서다.
3. 판정이 다른 문항을 모두 원인별로 나눈다. 채점기가 달라서 점수가 정확히 같지는 않다.

비교할 때 맞출 설정은 다음과 같다.

- `--max-samples`는 시드 42로 문항을 섞으므로, 전체 문항이나 같은 문항 목록으로 비교한다.
- Lighteval은 chat template이 있는 토크나이저에서 자동으로 켠다. lm-eval은 `--apply_chat_template`을 줘야 한다. 두 도구의 설정을 같게 맞춘다.
- chat template이 켜지면 태스크의 stop sequence를 쓰지 않는다. 우리는 `stop_sequence=[]`라서 영향이 없다.

합격 기준은 결과를 보기 전에 정한다.

- 프롬프트 차이 0건
- 생성 결과가 다른 문항은 원인을 설명한다.
- 점수가 다른 문항은 5번 표의 원인으로 모두 설명한다.

논문 수치는 프롬프트와 샘플링이 달라서 보조 참고로만 쓴다.

실행마다 다음을 기록한다.

- Lighteval 커밋, 데이터 리비전, 모델과 모델 리비전
- chat template 사용 여부, 디코딩 설정, 최대 생성 토큰, stop sequence
- 문항 선택 방법, 묶음별 점수와 단순 평균
- `\boxed{}` 없는 답의 수, 생성 길이 제한으로 답이 잘린 문항 수

## 7. 작업 나누기: 담당과 날짜

| 작업 | 담당 | 날짜 |
|---|---|---|
| 팀 결정을 이 문서에 반영하고 머지 | 김동우 | |
| `[EVAL]` 이슈 게시 | 김동우 | 완료 ([#1479](https://github.com/huggingface/lighteval/issues/1479)) |
| `hrm8k.py` 이전: 정식 이름, 설명 블록, `hf_revision`, `generation_size` | 김동우 | 완료 (11/5) |
| `tasks inspect` 출력 확인과 lm-eval 프롬프트 대조 | 김동우 | 완료 (11/5) |
| 채점 단위 테스트와 등록 테스트 | 김동우 | 완료 (11/8) |
| 태스크 PR 리뷰 | 정세엽, 박현우 | 11/8 전 |
| 비교 모델 실행과 문항 단위 비교 | 정세엽, 박현우 | 11/15 전 |
