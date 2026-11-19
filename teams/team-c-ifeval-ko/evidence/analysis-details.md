# IFEval-Ko 분석 보조 자료

**한국어** | [English](analysis-details.en.md)

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
| 모델 생성 환경 | 이 기준 실험 당시에는 미확정. 후속 Qwen 응답 생성과 MPS 실행은 [모델 응답 검증 안내](#model-response-parity)에 기록 |

기준 환경 최소 재실행의 영어·Ko runner는 각 3건, 종료 코드 0·오류 0이었다. 기존 86건의 주요 13개 파일 hash가 실행 전후 동일했다. 부등호·Known Issue 실행에서도 원본 보존과 양쪽 종료 코드·입력 및 결과 hash를 manifest에 남겼다.

native Lighteval metric은 기준 평가기와 분리된 Lighteval 가상환경에서 실행했다.

저장 응답을 `ModelResponse`에 넣고 `post_process`는 호출하지 않아 raw response와 final_text가 같음을 확인했다. 실제 모델 통합에서는 별도로 후처리·최종 응답 추출 범위를 고정해야 한다. NLTK는 기존 cache를 사용했다. 이 기준 실험의 저장 응답 검사는 모델 생성·GPU 가용성을 확인한 실행이 아니다. 이후 저장 모델 응답의 전체 채점과 native MPS 실행은 [분석보고서 9.3.6~9.3.7절](../analysis.md#saved-model-parity)에 구분해 기록했다. 당시 NLTK 3.10.3 기록은 보존하며, 현재 재채점 환경의 NLTK 3.10.4와 구별한다.

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

<a id="model-response-parity"></a>

## 7. 저장 모델 응답과 native MPS 검증 자료

저장 응답 채점과 native MPS 검증의 공개 자료 및 재현 경로를 정리했다. 기존 [156건 고정 응답 실험](checker-audit/README.md), [저장 모델 응답 채점](../analysis.md#saved-model-parity), [native MPS 실행](../analysis.md#native-mps-validation)의 자료를 구분해 제공한다.

### 검증 범위와 비교 기준

| 실행 | 응답 범위 | 확인 결과 |
| --- | --- | --- |
| 선정 응답 재채점 | PR #5의 23문항·40개 지시 | CPU에서 원본 Ko·이식 scorer·등록 태스크의 개별 strict/loose 판정과 네 지표 일치 |
| 전체 응답 재채점 | PR #7의 342문항·481개 지시 | 같은 세 경로에서 개별 strict/loose 판정과 네 지표 일치 |
| Native MPS 실행 | 새로 생성한 3문항·5개 지시 | native Lighteval의 생성·채점·집계·결과 저장 완료, 원본 Ko·이식 scorer와 판정 및 네 지표 일치 |

재채점 경로는 고정 원본 Ko 평가기, 이식 scorer 직접 호출, 등록 태스크의 Registry → Doc → `compute_sample` → native corpus 집계다. 원본 Ko 평가기의 실제 실행 결과를 비교 기준으로 삼는다. 저장 응답은 추가 가공 없이 전달하고 매 채점 호출 전 Python·langdetect seed를 재설정한다. key·문항 순서·kwargs·입력 체크섬·응답 해시를 확인하며, 반복 지시는 `(key, instruction_index, instruction_id)`로 구분한다.

모든 개별 판정과 네 지표의 분자·분모가 일치하고 값의 절대 오차가 `1e-12` 이하여야 한다. 입력 누락·채점 오류·미해결 불일치는 검증 실패이며 오류 문항을 제외해 분모를 줄이지 않는다. 결과에는 개별 판정·지표·불일치·재현 입력·코드 revision·패키지 버전·실행 명령을 기록한다.

전체 응답은 별도 Transformers 스크립트를 MPS·float16 환경에서 실행해 생성했다. 저장 응답 재채점에는 GPU나 모델 가중치가 필요하지 않다. native Lighteval로 새 응답을 생성한 범위는 3문항이다. 전체 342문항 결과는 저장 응답의 채점·집계 결과다.

### 공개 첨부 자료와 해시

ZIP은 해당 PR의 공개 첨부 링크에서 받고, 별도 체크섬 파일이 제공되면 함께 받는다. 압축 해제 전에 아래 표의 ZIP 해시와 대조하고 이후 내부 파일의 체크섬도 검사한다. 기존 입력·결과를 보존하고 재실행 보고서는 새 경로에 저장한다.

| 자료 | 공개 출처 | ZIP SHA-256 |
| --- | --- | --- |
| 선정 응답 | [PR #5](https://github.com/Hugging-Face-KREW/lighteval/pull/5), [ZIP](https://github.com/user-attachments/files/34706481/qwen-23-001.zip), [체크섬](https://github.com/user-attachments/files/34706603/qwen-23-001.zip.sha256.txt) | `a28e35bde3327a05efa9c255c228fa5ea2e711328e6e997c654d5f3b4f9e0e05` |
| 전체 응답 | [PR #7](https://github.com/Hugging-Face-KREW/lighteval/pull/7), [ZIP](https://github.com/user-attachments/files/34839513/qwen-342-001-public.zip), [체크섬](https://github.com/user-attachments/files/34839521/qwen-342-001-public.zip.sha256.txt) | `8d398dfbe60656daa4c9cd20bda61a91120fcea86d7e3b9fcebb7c0c91e4ddbb` |
| 전체 채점 비교 결과 | [PR #7](https://github.com/Hugging-Face-KREW/lighteval/pull/7), [ZIP](https://github.com/user-attachments/files/34839530/qwen-342-parity-001-public.zip), [체크섬](https://github.com/user-attachments/files/34839550/qwen-342-parity-001-public.zip.sha256.txt) | `81846baa55d5e64a5090ad80e26efd555727e1e15deb9e510a58d4a01405a368` |
| MPS 검증과 현재 환경의 전체 재채점 | [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8#pullrequestreview-5970474156), [ZIP](https://github.com/user-attachments/files/35070624/pr8-validation.zip) | `55c99f22f109fc2e959683208e83d96a6c5f43c9c02f4a273f12c7d71bfc1f44` |

MPS ZIP에는 native 실행 설정·로그·결과 JSON·상세 Parquet·원본 Ko 교차 검증·전체 저장 응답 재채점 결과가 있다. [PR #7](https://github.com/Hugging-Face-KREW/lighteval/pull/7#issuecomment-6877811099)의 독립 CPU 검증에서는 고정 tokenizer로 전체 342개 응답의 토큰화·디코딩 기록을 재현하고, 길이 제한에 도달한 응답 12개가 포함되었음을 확인했다. 선정 응답의 key `1127`도 제외하지 않았다.

### 코드 revision과 실행 환경

| 구분 | revision 또는 환경 |
| --- | --- |
| 원본 Ko 평가기·데이터 | `54199e3801116897697babf341865741dcd06fc8` |
| 최초 독립 CPU 재채점 | Lighteval `4cff81a2794cc7b0b7fb6bdd52f301fe887acf44`; 당시 환경 기록 보존 |
| 업스트림 제출 | [PR #1503](https://github.com/huggingface/lighteval/pull/1503), `f5feb8fe9d30000986cd9667e872ff7602022c9a` |
| Native MPS 리뷰 | 포크 `321d68bf559cc6222b42b699e3764deee3f31f0f`; Apple M5 GPU, MPS·float16, Python 3.11.18, PyTorch 2.15.0, Transformers 5.22.2, NLTK 3.10.4 |
| 재현 문서 보완 | [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8), `2d4f8c358cfae9c9ba81b4979a1a8df900e82ade` |
| 모델·tokenizer | `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |

응답 생성에는 0-shot, 공식 chat template 1회 적용, greedy decoding, batch size 1, 최대 신규 토큰 1,280개 설정을 사용했다. 저장 응답 생성 스크립트의 seed는 0이며, native Pipeline의 seed와 세부 실행 설정은 MPS ZIP에 기록했다. native 실행의 문항 key는 `2209`, `2304`, `1418`이다. strict·loose 모두 문항 점수는 `1/3`, 지시 점수는 `2/5`다.

과거 audit·응답 생성 환경에서는 NLTK 3.10.3을, 현재 재채점·native MPS 환경에서는 3.10.4를 사용했다. 과거 실행을 재현하려면 당시 lock과 메타데이터를 사용하고, 현재 환경에서 재채점하려면 최신 안내를 따른다. 두 실행은 사용한 버전이 다르므로 구분해 기록한다.

### 재현 안내

의존성 설치·NLTK tokenizer 자료 사전 준비·원본 복원·고정/선정/전체 응답 재채점 명령은 고정 revision의 [Lighteval 채점 안내](https://github.com/Hugging-Face-KREW/lighteval/blob/2d4f8c358cfae9c9ba81b4979a1a8df900e82ade/tests/ifeval_ko/README.md)를 따른다. 생성 manifest·문항 선정 근거·저장 응답 첨부 자료는 [생성 안내](https://github.com/Hugging-Face-KREW/lighteval/blob/2d4f8c358cfae9c9ba81b4979a1a8df900e82ade/scripts/ifeval_ko/README.md)에서 확인한다. 두 문서는 과거 생성 환경과 현재 채점 의존성을 구분한다.

초기 환경에서는 안내된 NLTK tokenizer 자료를 채점 전에 설치한다. 공개 ZIP의 선정·전체 응답을 각각 재채점하고 보고서는 새 경로에 저장한다. 개별 판정과 네 지표의 분자·분모를 [분석보고서 9.3.6절](../analysis.md#saved-model-parity)의 결과와 비교한다. native MPS 실행을 확인하거나 재현하려면 [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8#pullrequestreview-5970474156)의 설정과 실행 명령을 확인한다.

태스크 구현과 검증 자료를 제출한 [PR #1503](https://github.com/huggingface/lighteval/pull/1503)에 [이슈 #1463](https://github.com/huggingface/lighteval/issues/1463)을 연결했다. [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8)은 코드 스타일·재현 안내 보완과 native MPS 검증 자료를 담고 있다. 데이터셋 Known Issues와 수정 overlay는 원본 판정을 보존하는 이식 작업과 별도로 다룬다.
