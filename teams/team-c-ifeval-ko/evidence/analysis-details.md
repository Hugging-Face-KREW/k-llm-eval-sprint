# IFEval-Ko 분석 보조 자료

[분석보고서](../analysis.md)의 상세 조사·관찰 표를 보존한 문서다. 구현 계약·후속 검증 절차는 [설계 문서](../design.md)에 둔다. 이 분리 작업에서 새 평가를 실행하지 않았으며 아래 표를 옮긴 것이 후속 실험의 원본 입력·로그 추가 첨부를 뜻하지 않는다.

<a id="extra-models"></a>

## 1. 추가 모델 후보 조사

본문에는 환경 점검·우선 후보·경량 대안만 남겼다. 아래는 기존 보고서에서 함께 검토한 추가 후보이며 채택을 확정하지 않았다. 모델 카드는 이번 문서 정리에서 재조회하지 않았다.

| 모델 ID | 규모 | 조사 내용 | 이번 검증에서의 용도 |
| --- | --- | --- | --- |
| `google/gemma-3-1b-it` | 1B | 소형 instruction 모델로, Hugging Face에서 사용 조건 동의가 필요하다. | 다른 모델 계열의 응답으로 확인할 때 사용할 보조 후보 |
| `LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct` | 2.4B | 영어·한국어 bilingual 모델이다. 공식 예제는 `trust_remote_code=True`를 사용하며, 권장 system prompt도 제시한다. | 한국어 모델의 응답을 추가 검증할 때 사용할 후보 |
| `google/gemma-3-4b-it` | 4B | Allganize의 IFEval-Ko README에 실행 예시 모델로 등장한다. 모델 접근 조건과 텍스트 생성 경로의 호환성을 확인해야 한다. | 공식 실행 예시를 참고한 추가 통합 검증 |
| `Qwen/Qwen2.5-3B-Instruct`, `Qwen/Qwen2.5-7B-Instruct` | 3B / 7B | 같은 Qwen2.5 instruction 계열의 더 큰 모델이다. | 주 모델 검증 이후 자원이 확보되면 검토 |
| `meta-llama/Llama-3.2-1B-Instruct` | 1B급 | 공식 지원 언어 목록에 한국어가 포함되어 있지 않다. | 한국어 주 검증 모델로는 우선순위를 낮춤 |
| `Qwen/Qwen3-0.6B` | 0.6B | thinking / non-thinking 전환을 지원한다. 사용 시 해당 모드와 최종 응답 추출 범위를 추가로 고정해야 한다. | 이번 기본 검증에서는 보류 |

Qwen3는 thinking·응답 추출 범위, EXAONE은 remote code·system prompt를 추가로 확인해야 한다. 공식 카드의 영어 점수나 실행 조건이 다른 외부 점수는 한국어 검증의 합격 기준으로 삼지 않는다.

<a id="ko-classes"></a>

## 2. Ko 클래스·registry 조사

[제작자 문서](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/README_Ko.md)의 수정 클래스 7개는 `KeywordChecker`, `KeywordFrequencyChecker`, `ParagraphFirstWordCheck`, `KeySentenceChecker`, `ForbiddenWords`, `RepeatPromptThenAnswer`, `EndChecker`다. 이 중 `KeySentenceChecker`는 고정 registry에 미등록이고 데이터에도 사용되지 않는다. 나머지 6개가 등록되어 있다. 단어·문장 utility와 전역 선택 문구의 변경도 따로 있으므로 7개를 전체 동작 변경 수로 해석하지 않는다.

영어 전용 조건 4종인 keywords:letter_frequency와 change_case의 capital_word_frequency·english_capital·english_lowercase는 Ko 데이터에서 사용되지 않지만 registry에는 유지돼 있다. 영어·Ko·Lighteval registry는 모두 25개 ID이고 Ko 데이터에서 실제 사용하는 유형은 21개다. 데이터 미사용을 registry 삭제로 해석해 조건을 임의로 제거하지 않는다.

제작자 소개의 7개 클래스와 실제 등록·데이터 사용을 대조한 결과는 다음과 같다. 문항 수는 클래스별 적용 수이므로 서로 겹칠 수 있다.

| 클래스 | Ko 적용 문항 수 | 보존할 동작 |
| --- | --- | --- |
| `KeywordChecker` | 22 | keywords별 NFC, 누락 시 ValueError |
| `KeywordFrequencyChecker` | 23 | keyword의 strip·NFC, 누락 시 ValueError |
| `ParagraphFirstWordCheck` | 2 | first_word=None이면 ValueError. first_word 자체의 NFC는 추가하지 않음 |
| `KeySentenceChecker` | 0 | 클래스에는 문장 NFC가 있으나 registry 미등록 |
| `ForbiddenWords` | 28 | 금지어 NFC·누락 오류·목록 처리 |
| `RepeatPromptThenAnswer` | 26 | prompt_to_repeat의 NFC |
| `EndChecker` | 15 | end_phrase의 NFC와 번역된 기본 문구 |

영어 전용 4종의 고정 영어 데이터 적용 문항 수는 `keywords:letter_frequency` 33, `change_case:capital_word_frequency` 20, `change_case:english_capital` 25, `change_case:english_lowercase` 39다. 네 ID는 Ko registry에도 남아 있고 Ko 데이터에서의 적용 수만 각각 0이다. 출처: [Ko checker](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py), [Ko registry](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_registry.py), [Ko utility](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py).

<a id="language-controls"></a>

## 3. 언어별 합성 대조군의 상세 결과

영어 IFEval과 프랑스어·한국어의 관계를 더 확인하기 위해 별도 합성 입력 23건을 추가로 실행했다. 실제 영어 metric·French 어댑터·영어 harness의 판정은 23건 모두 같았으며, 모든 경로의 결과가 사전 예상과 일치했다.

| case ID | 영어 구현을 기준으로 한 대조 | 실제 결과와 해석 |
| --- | --- | --- |
| `word_spaces_en/fr/ko` | 공백 단어: apple pear grape / pomme poire raisin / 사과 배 포도 | 영어 checker도 세 언어 모두 3개로 계산한다. 한글 자체가 처리 불가인 것은 아님 |
| `word_comma_en/fr/ko` | 쉼표 단어: 위 세 언어의 단어를 쉼표로 연결 | 영어 checker는 세 언어 모두 3개, Ko는 모두 1개. 차이는 특정 언어의 처리 실패보다 계산 규칙의 차이임 |
| `word_contraction_fr` | `l'homme`, 2단어 미만 | 영어 metric과 French 어댑터는 2개로 세어 실패하고, Ko 공백 기준은 1개로 세어 통과. French 경로가 아포스트로피도 원본 정규식대로 처리함을 확인 |
| `sentence_no_spaces_fr` | `Bonjour.Merci.`, 2문장 이상 | 영어 metric과 French 어댑터는 1문장으로 세어 실패하고, Ko 분리기는 2문장으로 세어 통과. French 전용 문장 분리기로 바꾸지 않았음을 확인 |
| `fixed_fr` | 프랑스어 고정 문구 Ma réponse est oui. | 영어 선택지 checker에서 실패. French 데이터가 문구까지 번역한다면 기존 옵션만으로 부족함 |
| `keyword_nfc_fr`, `keyword_nfd_fr` | 프랑스어 keyword=café, NFC·NFD 응답 | 영어 경로는 NFC 통과·NFD 실패, Ko는 둘 다 통과. NFC 문제는 한국어에만 생기는 현상이 아님 |
| `uppercase_en`, `uppercase_fr` | 영어·프랑스어 대문자 응답에 english_capital 적용 | 영어 통과·프랑스어 실패. 기존 checker는 대문자뿐 아니라 영어 사용도 요구하므로 French에 무조건 적용 가능한 조건이 아님 |

`en/fr/ko`는 같은 접두사에 붙는 세 case ID의 축약 표기다. 위 프랑스어 응답은 기존 코드가 실제로 어떻게 처리하는지 확인한 합성 대조군이다. Ko의 계산 결과를 프랑스어 정답 기준으로 삼거나, 이 결과만으로 실제 French 데이터에 오류가 있다고 판정하지 않는다.

이 대조는 Ko에 필요한 변경 범위를 좁히기 위한 자료다. 프랑스어 전체 데이터의 채점 적합성 검증을 Ko 구현의 선행 과제로 삼지 않는다.

<a id="execution-scope"></a>

## 4. metric·French·Inspect 실행 범위

metric 재사용 비교의 모든 key는 null인 합성 입력이다. French 어댑터에는 동일한 합성 레코드를 전달해 실제 `Doc → apply_metric → IFEvalMetrics → registry` 경로와 metric 객체의 동일성을 확인했다. 실제 French 데이터 전체·별도 French reference와의 동등성·모델 평가는 하지 않았다. 고정 French 태스크가 가리킨 `fr-gouv-coordination-ia/IFEval-fr`의 기존 API·README 조회는 HTTP 401이었고, 이름이 유사한 다른 데이터로 대체하지 않았다.

native 집계 함수의 별도 입력 `[[True, True, True], [False]]`는 instruction-level 0.75, prompt 평균 `[1, 0]`은 0.5로 확인했다. 모델 점수가 아닌 집계 함수 검사다. Inspect는 최소 상태 fixture로 native scorer 함수를 호출한 범위이며 전체 backend 실행이 아니다.

<a id="reference-environment"></a>

## 5. 기준 실행 환경과 원본 보존 확인

| 항목 | 확인 값과 범위 |
| --- | --- |
| 기준 환경 | 고정 영어·Ko evaluator를 설치한 별도 Python 가상환경 |
| Python · lm_eval | 3.12.3 · 0.4.14.dev0 |
| langdetect · immutabledict | 1.0.9 · 4.3.1 |
| NLTK · pyarrow | 3.10.3 · 26.0.0 |
| 패키지 lock | 고정 70개 패키지가 현재 환경과 일치한 것을 확인 |
| 실행 응답 | 저장 응답. 기준 환경 점검에는 모델 생성·GPU가 필요하지 않았음 |
| 모델 생성 환경 | 최종 모델·tokenizer revision·dtype·chat template·backend 미확정 |

기준 환경 최소 재실행의 영어·Ko runner는 각 3건, 종료 코드 0·오류 0이었다. 기존 86건의 주요 13개 파일 hash가 실행 전후 동일했다. 부등호·Known Issue 실행에서도 원본 보존과 양쪽 종료 코드·입력 및 결과 hash를 manifest에 남겼다.

native Lighteval metric은 기준 평가기와 분리된 Lighteval 가상환경에서 실행했다.

저장 응답을 `ModelResponse`에 넣고 `post_process`는 호출하지 않아 raw response와 final_text가 같음을 확인했다. 실제 모델 통합에서는 별도로 후처리·최종 응답 추출 범위를 고정해야 한다. NLTK는 기존 cache를 사용했다. 이 저장 응답 검사는 모델 생성·GPU 가용성이나 전체 모델 평가 완료를 뜻하지 않는다.

<a id="public-sources"></a>

## 6. 채점 동작을 확인할 공개 코드

| 확인 대상 | 공개 source |
| --- | --- |
| Ko 공식 실행 설정 | [task YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml) |
| Ko 응답 NFC·kwargs 처리·strict/loose | [evaluator](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/utils.py) |
| Ko 개별 checker·고정 선택 문구 | [instructions](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py) |
| Ko instruction ID 등록 | [registry](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_registry.py) |
| Ko 단어·문장 수 | [utility](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py) |
| 영어 counter·checker 대조 | [utility](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/ifeval/instructions_util.py), [instructions](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/ifeval/instructions.py) |
| Lighteval 입력 변환·metric·Inspect scorer | [IFEval main](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/ifeval/main.py) |
| French의 기존 metric 재사용 | [French task](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py) |
