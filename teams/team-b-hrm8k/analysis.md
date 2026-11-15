# HRM8K 벤치마크 분석 보고서

## 1. 한 줄 요약: 무엇을 측정하는가

영어-한국어 병렬 수학 문제 8,011개로 한국어 수학 추론 성능과 언어 간 격차를 측정하는 벤치마크.

## 2. 출처

- 논문: Understand, Solve and Translate: Bridging the Multilingual Mathematical Reasoning Gap (arXiv 2501.02448)
- 저자: Hyunwoo Ko, Guijin Son, Dasol Choi (OneLineAI, 연세대)
- 연도: 2025 (2025.01.05 공개)
- 공식 코드: 미공개 (HF 데이터셋 카드에 "Code (Coming soon!)"로 표기)

## 3. 데이터셋

- Hugging Face ID: `HAERAE-HUB/HRM8K`
- config: `GSM8K`, `MATH`, `OMNI_MATH`, `MMMLU`, `KSM`
- split: `test` (config마다 1개)
- 문항 수: 총 8,011

| 구분 | config | 문항 수 | 설명 |
|---|---|---|---|
| Prior Sets (6,583) | GSM8K | 1,319 | 초등 수준 수학 문장제 |
| | MATH | 2,885 | 경시 수준, 숫자 정답만 포함 |
| | OMNI_MATH | 1,909 | 올림피아드 수준, 숫자 정답만 포함 |
| | MMMLU | 470 | abstract_algebra, college_mathematics, high_school_mathematics (객관식) |
| KSM (1,428) | KSM | 1,428 | KMO 730, KJMO 62, CSAT 210, KMS 82, TQ 344 |

- 필드 (GSM8K config): `question`(한국어), `answer`(float64), `original`(영어 원문)
- 예시 (GSM8K config, 요약):
  1. 로브 한 벌에 파란 섬유 2개와 그 절반의 흰 섬유가 필요할 때 총 섬유 수를 묻는 문제 (answer = 3)
  2. 오리가 낳은 알에서 아침 식사와 머핀에 쓰고 남은 것을 개당 2달러에 팔 때 하루 수입을 묻는 문제 (answer = 18)

## 4. 라이선스와 접근

- 라이선스: MIT (HF 데이터셋 카드 기준)

## 5. 공식 평가 방식

- 프롬프트 형식: 영어 지시문(문제를 풀고 최종 답을 지정 형식으로 쓰기) + 질문 + 응답 언어 지시("Respond in Korean" 또는 "Respond in English"). 풀이 생성 프롬프트(논문 Figure 9, 10)에는 예시가 포함되어 있지 않음
- 평가 설정 3가지
  - K2K: 한국어 입력, 한국어 추론
  - K2E: 한국어 입력, 영어 추론
  - E2E: 영어 입력, 영어 추론
- few-shot: 5-shot은 번역 단계(TE2E 파이프라인)에서만 사용
- 샘플링: temperature 0.7, top_p 0.95, 최소 8토큰, 최대 2,048토큰 (낮은 temperature에서는 모델이 영어나 중국어로 되돌아가는 현상이 있어 일부러 높게 설정했다고 논문에 서술)
- 지표: 정확도(%). 논문의 Avg는 5개 config 점수의 단순(macro) 평균 (Qwen2.5-7B K2K 점수로 직접 계산하면 macro 약 39.5, 문항 수 가중 micro 약 38.6이라 논문의 39.52와 macro가 일치)
- 논문 수치 (Table 3, 9)

| 모델 | 설정 | GSM8K | MATH | Omni-MATH | MMMLU | KSM | Avg |
|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | K2K | 66.41 | 50.36 | 18.96 | 50.00 | 11.83 | 39.52 |
| Qwen2.5-7B-Instruct | E2E | 81.35 | 68.87 | 27.29 | 57.02 | 21.08 | 51.12 |
| Qwen2.5-72B-Instruct | K2K | 89.46 | 74.73 | 30.07 | 69.79 | 25.35 | 57.88 |
| Qwen2.5-72B-Instruct | E2E | 94.31 | 83.33 | 37.72 | 70.00 | 31.65 | 63.40 |
| Qwen2.5-1.5B-Instruct | K2K | 28.13 | 20.69 | 8.64 | 18.51 | 3.78 | 15.95 |
| Llama-3.1-8B-Instruct | K2K | 57.47 | 31.20 | 11.73 | 32.98 | 5.25 | 27.73 |
| GPT-4o | - | 91.21 | 74.45 | 30.75 | 68.72 | 22.83 | 57.59 |

## 6. 기존 구현

- lm-evaluation-harness
  - v0.4.8에서 추가 (PR #2627). 태스크명은 `hrm8k`(한국어 질문), `hrm8k_en`(영어 질문)
  - PR #3124 (v0.4.9.1): CoT 풀이가 잘려 exact_match가 실패하던 문제로 max_gen_toks를 논문 설정대로 2048로 조정
- HRET (haerae-evaluation-toolkit): HAE-RAE, KMMLU, KUDGE와 함께 HRM8K 통합 지원
- Ko-R1-1.5B-preview: HRM8K 서브셋으로 평가. 설정은 temperature 0.0, max_tokens 8192, repetition_penalty 1.1 (논문 설정과 다름)
- A.X K1 기술 보고서: HRM8K를 chat 형식 CoT 프롬프트로 평가하고 최종 숫자 정답의 정확성으로 채점

## 7. 중복 확인

- 검색 키워드 (웹 검색)
  - `HRM8K benchmark Korean math reasoning paper`
  - `HAERAE-HUB/HRM8K Hugging Face dataset card license configs`
  - `HRM8K lm-evaluation-harness task pull request`
  - `lm-evaluation-harness lm_eval/tasks/hrm8k README`
  - `haerae-evaluation-toolkit HRM8K`
- 결과: lm-evaluation-harness PR #2627, #3124와 HRET 통합이 확인됨. PR #2627 본문에 `resolved: #2623`이 적혀 있으나 해당 이슈는 열어보지 못함
- 대상 프레임워크의 GitHub 이슈와 PR 직접 검색은 아직 하지 않음

## 8. 구현하면서 어려울 것 같은 부분

- 생성 길이: max_gen_toks가 짧으면 정답이 잘려 점수가 크게 낮아짐 (lm-eval PR #3124 사례)
- 샘플링 변동: 논문 설정이 temperature 0.7이라 결과에 확률적 변동이 있음
- 언어 일관성: K2K 설정에서 모델이 영어로 답하는 경우의 처리 방침 필요
- 채점 규칙: 논문에 정답 추출과 매칭(정규화) 규칙이 명시되어 있지 않음
- 서브셋별 채점 차이: MMMLU는 객관식, 나머지는 숫자 정답
- 평균 방식: 논문은 macro 평균이라 구현에서 macro와 micro 중 무엇으로 보고할지 결정 필요
- 오류 문항: 번역은 사람이 검토해 부정확한 것을 제거했고 KSM OCR은 수작업으로 검증했으나, 남은 오류 문항의 처리 방침은 별도로 정해야 함
- 오염 가능성: 오염 검사는 KSM에만 수행됨 (FineWeb-2에서 정확 일치 문자열 없음). Prior Sets는 원본이 공개 벤치마크라 오염 위험이 더 큼

## 9. 검증 계획

- 모델: GPT-4o (API)
- 비교 수치: 논문 Table 3의 GPT-4o 서브셋별 점수와 macro 평균

| 모델 | GSM8K | MATH | Omni-MATH | MMMLU | KSM | Avg |
|---|---|---|---|---|---|---|
| GPT-4o | 91.21 | 74.45 | 30.75 | 68.72 | 22.83 | 57.59 |

- 설정: 논문과 동일한 프롬프트(영어 지시문 + 질문 + 응답 언어 지시), temperature 0.7, top_p 0.95, max 2,048토큰
- 교차 검증: 같은 모델을 lm-eval `hrm8k`, `hrm8k_en`(max_gen_toks 2048 이후 버전)으로도 평가해 비교
- 비교 시 유의 사항
  - 논문 Table 3의 GPT-4o 행에는 프롬프트 설정(K2K, K2E, E2E)이 표기되어 있지 않음
  - 논문에서 확인한 범위에서는 GPT-4o의 스냅샷 버전이 명시되어 있지 않아, 현재 API 모델과 동일하다고 보장할 수 없음
  - temperature 0.7 설정이라 결과에 확률적 변동이 있음
  - HRM8K의 번역과 KSM OCR에 GPT-4o가 사용되었음
- 차이가 클 경우 원인 점검 순서: 정답 추출 규칙, 생성 잘림, 언어 이탈