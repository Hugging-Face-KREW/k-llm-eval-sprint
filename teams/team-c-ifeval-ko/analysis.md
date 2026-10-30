# 벤치마크 분석 보고서

## **1. 한 줄 요약: 무엇을 측정하는가**

IFEval-Ko는 한국어 프롬프트에 포함된 지시사항 중 프로그램으로 검증 가능한 조건(verifiable instructions)을 LLM이 얼마나 정확하게 준수하는지 측정하는 벤치마크입니다.

---

## **2. 출처: 논문, 저자, 연도, 공식 코드**

| 구분 | 내용 |
| --- | --- |
| 원본 논문 | Instruction-Following Evaluation for Large Language Models |
| 저자 | Jeffrey Zhou, Tianjian Lu, Swaroop Mishra, Siddhartha Brahma, Sujoy Basu, Yi Luan, Denny Zhou, Le Hou |
| 발표 연도 | arXiv. 2023-11-14 |
| 논문 | [원본 논문](https://arxiv.org/abs/2311.07911) |
| **원본 IFEval 코드** | [Google Research IFEval — 논문의 영어 평가 코드](https://github.com/google-research/google-research/tree/master/instruction_following_eval) |
| **IFEval-Ko 채점 코드** | [Allganize IFEval-Ko — 한국어 채점 기준 구현](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/main/ifeval_ko) |
| **기여 대상** | [Hugging Face Lighteval — IFEval-Ko를 연결할 평가 도구](https://github.com/huggingface/lighteval) |
| **팀 작업 저장소** | [Hugging-Face-KREW/lighteval — 구현과 팀 리뷰를 진행할 포크](https://github.com/Hugging-Face-KREW/lighteval) |

---

## **3. 데이터셋: Hugging Face ID, config와 split, 문항 수, 필드, 예시 2개**

### **3.1. 기본 정보**

| 항목 | 영어 IFEval | IFEval-Ko |
| --- | --- | --- |
| Hugging Face ID | **`google/IFEval`** | **`allganize/IFEval-Ko`** |
| Config | **`default`** | **`default`** |
| 평가에 사용하는 split | **`train`** | **`train`** |
| 문항 수 | 541 | 342 |
| 주요 저장 형식 | JSONL | Parquet |
| 모델 입력 | **`prompt`** | **`prompt`** |
| 채점 정보 | **`instruction_id_list`**, **`kwargs`** | **`instruction_id_list`**, **`kwargs`** |

문항 수와 config·split의 출처는 [영어 데이터셋 카드](https://huggingface.co/datasets/google/IFEval)와 [Ko 데이터셋 카드](https://huggingface.co/datasets/allganize/IFEval-Ko)다. `train`은 공개 데이터의 split 이름이다. 이번 task에서는 이 split의 문항을 평가에 사용하며 모델을 학습시키는 설정을 의미하지 않는다. 데이터 제작 과정의 few-shot과 실제 모델 평가의 0-shot도 구분한다.

### **3.2. 필드**

| 필드 | 의미 |
| --- | --- |
| **`key`** | 문항 식별자. 행 순서와 구분한다. |
| **`prompt`** | 모델에게 제시하는 자연어 요청 |
| **`instruction_id_list`** | 해당 응답에서 검사할 instruction 유형의 목록 |
| **`kwargs`** | 각 instruction에 대응하는 키워드, 횟수, 비교 조건 등의 파라미터 |

### **3.3. 예시 1 — key 3345**

프롬프트의 핵심 조건은 ‘강도’를 최소 두 번 사용하고, bullet 두 개를 작성하며, 지정 금지어를 사용하지 않는 것이다. 그러나 첫 번째 검사 파라미터에는 **`robber`**가 남아 있었다.

```json
{
  "key": 3345,
  "instruction_id_list": ["keywords:frequency", "detectable_format:number_bullet_lists", "keywords:forbidden_words"],
  "kwargs": [
    {"keyword": "robber", "frequency": 2, "relation": "at least"},
    {"num_bullets": 2},
    {"forbidden_words": ["죽이다", "도살", "점령", "침략"]}
  ]
}
```

검사기는 요청의 의미를 다시 번역하지 않고 **`kwargs`**의 문자열을 검색한다.

### **3.4. 예시 2 — key 3442**

수수께끼에 답하되 20단어 미만으로 작성하고 이중 꺾쇠괄호 제목을 포함하도록 요구하는 문항이다.

[실험: key 3442](evidence/checker-audit/README.md#확인할-대표-사례)

```json
{
  "key": 3442,
  "instruction_id_list": ["length_constraints:number_words", "detectable_format:title"],
  "kwargs": [
    {"num_words": 20, "relation": "less than"},
    {}
  ]
}
```

**`less than 20`**은 20개 이하가 아니라 20개 미만이다. 단어 수의 계산 단위가 달라지면 이 경계에서 판정이 달라질 수 있다.

---

## **4. 라이선스와 접근: 라이선스, 약관 동의 필요 여부**

| 대상 | 확인 내용 |
| --- | --- |
| 영어 IFEval 데이터 | Apache-2.0 |
| IFEval-Ko 데이터 | Apache-2.0, 원본 라이선스를 따름 |
| Ko [**`instructions.py`**](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/ifeval_ko/instructions.py) | Google Research의 Apache-2.0 저작권·라이선스 헤더 유지 |
| 기여 대상 LightEval | 저장소 최상위 [LICENSE](https://github.com/huggingface/lighteval/blob/main/LICENSE): MIT |

---

<a id="official-evaluation"></a>

## **5. 공식 평가 방식**

### **5.1. 프롬프트와 few-shot**

영어 Harness와 Ko task YAML 모두  **`doc_to_text: prompt`**, **`output_type: generate_until`**, **`num_fewshot: 0`**을 사용한다.

논문에서 등장하는 few-shot prompting은 평가 대상 모델에게 예시를 주는 설정이 아닌 데이터 제작 중 프롬프트를 필터링하고 재작성하는 과정이다.

확인한 [영어 Harness YAML](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/ifeval/ifeval.yaml)과 [Ko task YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/ifeval_ko/ifeval_ko.yaml)의 생성 설정은 아래와 같다. 이는 실행 구현의 설정이다.

| 항목 | 영어 Harness | Ko reference |
| --- | --- | --- |
| **`do_sample`** | **`false`** | **`false`** |
| **`temperature`** | **`0.0`** | **`0.0`** |
| **`max_gen_toks`** | 1280 | 1280 |
| **`until`** | **`[]`** | **`["<end_of_turn>", "<\|im_end\|>"]`** |

1,280은 생성 토큰 수 제한이며 checker가 세는 단어 수와는 다른 단위다. 실제 통합 검증에서는 같은 모델·chat template·생성 및 종료 설정을 기록하고 맞춘다.

### **5.2. 채점 경로와 정답 추출**

```
문항의 prompt → 응답 생성 또는 저장된 응답 입력
→ instruction_id와 kwargs로 checker 구성
→ 각 instruction의 strict / loose 판정
→ prompt-level / instruction-level 집계
```

프레임워크의 답변 추출·후처리도 [Ko `utils.py`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/ifeval_ko/utils.py)의 채점 경로와 비교할 평가 범위에 포함한다.

### **5.3. Strict와 loose**

Strict는 evaluator의 기본 전처리를 거친 응답을 대상으로 검사한다.

IFEval-Ko에서는 strict와 loose 모두 검사 전에 NFC 정규화를 적용한다.

Loose는 원본 응답에 `*` 제거, 첫 줄 제거, 마지막 줄 제거를 개별적으로 적용하거나 조합하여 총 8가지 후보를 검사한다. 다만 변환 결과가 중복될 수 있어 실제로 생성되는 서로 다른 문자열은 8개보다 적을 수 있다. 빈 문자열은 통과로 인정하지 않으며, `#`, `>`, `-` 등 다른 Markdown 기호까지 모두 제거하는 방식은 사용하지 않는다.

각 instruction은 독립적으로 검사하므로 서로 다른 후보에서 조건을 충족하더라도 통과로 인정된다. 즉, 모든 조건을 하나의 후보 문자열에서 동시에 만족할 필요는 없다.

```
instruction별 loose = 후보 중 하나라도 해당 checker를 통과
prompt-level loose = 모든 instruction의 loose가 True
```

이 후보 생성과 집계 방식 자체를 Lighteval에서도 유지해야 한다.

### **5.4. 네 가지 지표**

| 지표 | 의미 |
| --- | --- |
| **`prompt_level_strict_acc`** | 모든 instruction을 strict로 통과한 문항의 비율 |
| **`inst_level_strict_acc`** | 전체 개별 instruction 중 strict 통과 비율 |
| **`prompt_level_loose_acc`** | 모든 instruction을 loose로 통과한 문항의 비율 |
| **`inst_level_loose_acc`** | 전체 개별 instruction 중 loose 통과 비율 |

전체 문항 수를 $N$, 문항 $i$의 instruction 수를 $m_i$라고 할 때, prompt-level은 모든 instruction을 통과한 문항 수를 $N$으로 나눈다. instruction-level은 통과한 instruction 수를 $\sum_i m_i$로 나눈다. 문항별 instruction 통과율을 단순 평균하지 않는다. 예를 들어 한 문항의 3개 조건은 모두 통과하고 다른 문항의 1개 조건은 실패하면 instruction 점수는 $3/4=0.75$, prompt 점수는 $1/2=0.5$다. 네 지표 모두 값이 높을수록 지시 준수율이 높다.

### **5.5. 논문 보고 수치**

[원본 논문 Table 3](https://arxiv.org/pdf/2311.07911)의 영어 IFEval 결과이며 단위는 %다.

| 모델 | Prompt strict | Instruction strict | Prompt loose | Instruction loose |
| --- | --- | --- | --- | --- |
| GPT-4 | 76.89 | 83.57 | 79.30 | 85.37 |
| PaLM 2 S | 43.07 | 55.76 | 46.95 | 59.11 |

위 수치는 2023년 11월·8월 응답으로 산출한 영어 IFEval 참고값이다. 한국어 기준 점수나 이식의 합격 기준으로 사용하지 않으며 동일 모델·데이터·설정의 별도 결과가 필요하다.

[Allganize 데이터셋 카드](https://huggingface.co/datasets/allganize/IFEval-Ko)의 한국어 점수·그래프는 제작자의 외부 결과다. `Strict Accuracy (%)`의 prompt/instruction 구분, loose 점수·실행 revision이 충분히 공개되지 않아 이식 검증값으로 쓰지 않는다. 실제 실행·첨부 계획은 [design.md](design.md)에 둔다.

---

## **6. 기존 구현과 Ko 이식의 근거**

| 구현 | 역할 |
| --- | --- |
| Google Research IFEval | 원본 방법론·영어 코드의 배경 |
| lm-evaluation-harness | 고정한 영어 evaluator 비교 기준 |
| Allganize IFEval-Ko | 한국어 채점 동작의 직접적인 reference |
| Hugging-Face-KREW/lighteval | 이식 대상과 기존 영어·French metric 경로 |

### **6.1. French는 재사용하고 Ko는 변경이 필요한 이유**

**French 통합은 기존 채점 규칙을 재사용했고, Ko는 한국어 허용 문구·길이 계산·정규화 규칙을 변경했다.** French [PR #505](https://github.com/huggingface/lighteval/pull/505)의 [리뷰](https://github.com/huggingface/lighteval/pull/505#discussion_r1924874919)와 [작성자 답변](https://github.com/huggingface/lighteval/pull/505#discussion_r1925047054), [고정 task 코드](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py#L28-L40)에서 기존 `ifeval_metrics` 재사용을 확인했다. 이는 해당 통합의 선택이며 모든 영어 규칙이 프랑스어에 적합하다는 보증은 아니다.

Ko의 변경은 [제작자 설명](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/README_Ko.md)과 [utility](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py)에 근거한다. 아래는 같은 합성 응답을 기존 Lighteval metric·French 어댑터·영어 harness·원본 Ko에 전달한 대표 결과다. 영어 metric을 쓰는 세 경로의 판정은 같았고 strict·loose 모두 아래와 같았다.

| case ID · 조건·응답 | 기존 영어 경로 | 원본 Ko |
| --- | --- | --- |
| `word_comma_lt2` · 사과,배,포도 / 2단어 미만 | 3단어 → 실패 | 1단어 → 통과 |
| `sentence_no_space_ge2` · 첫 문장입니다.둘째 문장입니다. / 2문장 이상 | 1문장 → 실패 | 2문장 → 통과 |
| `ko_fixed_choice` · 제 답변은 예입니다. / 고정 선택 문구 | 실패 | 통과 |
| `nfd_keyword` · keyword=가, 응답=U+1100 U+1161 | 실패 | 응답 NFC 후 통과 |

따라서 데이터 주소만 Ko로 바꾸면 원본과 다른 점수가 나올 수 있다. 공통 채점 루프·동일한 형식 검사·집계는 재사용하되 Ko의 checker·utility·고정 문구·NFC·kwargs 처리를 연결해야 한다. 이는 계산 규칙의 차이를 확인한 것으로 모델 성능이나 실제 French 데이터 전체의 평가 결과가 아니다. [언어별 상세 대조군](evidence/analysis-details.md#language-controls)에 추가 사례와 해석 범위를 보존했다.

### **6.2. 보존 범위와 구현 인계**

원본 Ko의 데이터·채점 동작을 보존하고, 번역 오류·채점 정책 개선은 별도 Known Issues로 다룬다. 제작자가 열거한 수정 클래스 7개 중 `KeySentenceChecker`는 registry에 미등록이며, 영어 전용 조건도 데이터에서 미사용일 뿐 registry에는 남아 있다. [클래스별 조사와 등록 현황](evidence/analysis-details.md#ko-classes)에 상세 수치를 정리했다.

구조 A/B, Doc 변환, metric·Inspect 경로, 예외와 fallback 보존 방식은 [설계 문서](design.md#task-structure)로 이관했다. 이식의 판단 기준은 고정 Allganize 코드와 같은 저장 응답의 판정 일치이며, 새 API나 Ko task가 이미 구현됐다는 뜻은 아니다.

---

## **7. 중복 확인과 관련 선행 작업**

### **7.1. 검색 일자·대상·검색어**

**2026-10-30(KST)**에 아래 20개 조회를 수행했다. PR은 all, issue는 open·closed 범위이며 조회당 최대 50개를 반환했다.

| 대상·범위 | 검색어 | 조회 수 | 해당 조회에서 확인한 결과 |
| --- | --- | --- | --- |
| Lighteval upstream·팀 포크·harness의 PR 및 issue | `"IFEval-Ko" OR "ifeval_ko" OR "allganize/IFEval-Ko"` | 6 | 각 조회에서 결과 0건 |
| Lighteval upstream·harness의 PR 및 issue | `IFEval Korean` | 4 | 각 조회에서 결과 0건 |
| Lighteval upstream·harness의 PR | `IFEval multilingual` | 2 | 다국어·의존성 관련 선행 PR 확인 |
| GitHub 전체 PR·issue, 전체 PR | `"IFEval-Ko"`(PR·issue), `"ifeval_ko"`(PR) | 3 | 팀 분석 PR과 NeMo-Skills의 Ko 통합 등 확인 |
| Lighteval upstream PR, Lighteval upstream·harness PR | `IFEval 한국어`, `IFEval Korea` | 3 | 각 조회에서 결과 0건 |
| Lighteval upstream·harness의 issue | `"allganize"` | 2 | 각 조회에서 결과 0건 |

반환 범위에서는 Lighteval·harness 메인테이너의 Ko checker 변경 지시를 찾지 못했다. 중복 구현·관련 발언의 완전한 부재를 증명하는 결과는 아니며, 조회 20회와 통합 점검 20문항은 별개다.

### **7.2. 관련 선행 작업과 발언의 범위**

| 참고 기록 | 확인한 내용 | 해석의 한계 |
| --- | --- | --- |
| [Lighteval French PR #505](https://github.com/huggingface/lighteval/pull/505)의 [리뷰](https://github.com/huggingface/lighteval/pull/505#discussion_r1924874919) 및 [작성자 답변](https://github.com/huggingface/lighteval/pull/505#discussion_r1925047054) | 중복 metric을 기존 IFEval에서 import할 수 있는지 질문했고 작성자가 재정의가 없다고 확인. 2025-01-23 병합 | French 전체 채점의 언어적 정확성 보증이 아님 |
| [NeMo-Skills PR #1375](https://github.com/NVIDIA-NeMo/Skills/pull/1375)의 [리뷰](https://github.com/NVIDIA-NeMo/Skills/pull/1375#discussion_r3189945909) | Ko 평가기를 외부 패키지로 분리해 재사용한 [참고 사례](https://github.com/NVIDIA-NeMo/Skills/pull/1375#discussion_r3195884717) | 다른 프레임워크의 유지보수 사례이며 이번 Lighteval 설계의 승인 근거는 아님 |
| [Allganize Community Discussion #2](https://huggingface.co/datasets/allganize/IFEval-Ko/discussions/2) | `prompt_to_repeat`, `section_spliter` 등의 데이터 오류 제보와 제작자 수정 답변 | Ko engine 구조 변경의 지시가 아님. key 3345 등 이번 사례가 수정됐다는 뜻도 아님 |

영어 IFEval의 [데이터 저장소 변경 PR #268](https://github.com/huggingface/lighteval/pull/268), [reasoning 전처리 PR #791](https://github.com/huggingface/lighteval/pull/791)·[#792](https://github.com/huggingface/lighteval/pull/792), [NLTK 수정 PR #1013](https://github.com/huggingface/lighteval/pull/1013)도 참고했다. Ko 중복 구현 사례와는 구분한다.

PR·discussion은 분석 기준일의 참고 기록이다. Ko 변경의 직접 근거는 **고정 Allganize 코드와 동일 응답의 실제 판정 차이**이며 다른 프로젝트의 설계 사례를 Lighteval 메인테이너의 승인으로 해석하지 않는다.

---

## **8. 구현상 어려운 점과 Known Issues**

### **8.1. 핵심 난점**

checker 직접 호출만으로는 실제 평가 경로를 검증할 수 없다. kwargs·instruction 순서, NFC·loose 후보, 집계, 의존성·난수·예외 처리까지 원본 Ko와 맞춰야 한다. 세부 입력 계약과 회귀 테스트는 [설계 문서](design.md#input-contract)에 정리했다.

### **8.2. 실제 evaluator로 확인한 Known Issues**

판정 표기는 **strict / loose** 순서다. 원본 Ko 구현의 의도된 adaptation, 지시문·검사 조건 불일치, 채점 정책에 관한 관찰을 구분한다. 데이터 오류가 보여도 기본 이식에서는 원본 조건을 유지한다.

#### **8.2.1. 문자열 정합성과 고정 선택지**

| key | 문제 유형 | 고정 응답의 실제 결과 | 구현에서의 처리 |
| --- | --- | --- | --- |
| 3345 | 데이터: ‘강도’와 `robber` | `robber_full`: 영어 robber 응답 통과/통과, Ko 강도 응답 실패/실패. Ko keyword만 강도로 바꾼 별도 override는 통과/통과 | 원본 kwargs 보존. 언어별 서로 다른 응답을 사용한 사례임을 명시 |
| 1203 | 데이터: ‘평화’와 `peace` | 전쟁 8회·평화 10회 응답에서 index 0은 통과, index 1은 실패해 전체 실패/실패. 전쟁 8회·peace 10회는 Ko 전체 통과/통과 | 반복 `keywords:frequency`를 index로 구별. 원본과 keyword override 대조군 분리 |
| 2142 | 데이터: ‘포식자’와 `predatory` | 포식자 2회는 실패/실패, predatory 2회는 통과/통과. Ko keyword override에서 포식자 2회 통과·1회 실패 | 원본 keyword 보존. 제보는 별도 초안 |
| 227 | 데이터·checker 허용 문구 불일치 | prompt의 ‘내 대답은 …’ 3종 모두 Ko 실패/실패. checker의 ‘제 답변은 …’ 3종 모두 Ko 통과/통과. 영어 3종은 Ko 실패/실패 | Ko 허용 옵션과 strip 후 포함 검사를 보존. OR fallback으로 허용 범위를 확대하지 않음 |

1203·2142·227은 신규 17건(원본 데이터 조건 14건·명시적 메모리 override 3건)으로 실제 영어·Ko evaluator의 full·isolated strict/loose를 실행했다. 모든 사전 기대값과 일치했다. override는 원본 데이터 수정이나 제작자가 승인한 해결책이 아니다. 검사 단어·고정 선택 문구와 판정 경로는 Ko checker와 Ko evaluator를 기준으로 했다.

#### **8.2.2. 부등호 번역 불일치**

고정 데이터에서 **14문항(단어 수 6개·문장 수 8개)**의 ‘N 이하/이내’와 `relation="less than"`의 불일치를 확인했다. 각 문항에 N−1·N·N+1 길이의 저장 응답을 넣은 **42건을 영어·Ko 각각 실행**했다. 양쪽 counter의 실측 길이와 대상 instruction의 full·isolated strict/loose 판정이 모두 기대값과 일치했다. 정확히 N에서 14문항 모두 대상 조건이 실패했고 Ko 전체 판정도 N−1 통과, N·N+1 실패였다.

| 대표 key | 응답 길이 | Ko 대상·문항 전체 strict / loose |
| --- | --- | --- |
| 1092 | 299단어 | 통과 / 통과 |
| 1092 | 300단어 | 실패 / 실패 |
| 1092 | 301단어 | 실패 / 실패 |
| 1268 | 5문장 | 통과 / 통과 |
| 1268 | 6문장 | 실패 / 실패 |
| 1268 | 7문장 | 실패 / 실패 |

이는 `<N`의 원본 동작을 재현한 결과다. 지시문을 ‘미만’으로 고칠지 검사 조건을 `≤N`으로 바꿀지는 제작자가 의도한 명세의 결정이며, 기본 이식에서는 `<N`을 유지한다. key 3739는 ‘3문장 이하’ 뒤에 ‘단 1문장 또는 2문장’이라는 보충 조건이 있어 추가 불일치에서 제외했다.

14문항의 key와 대상 instruction은 다음과 같다. index는 0부터 세며, 행 순번과 구분한다.

| key | instruction index | Ko 지시문 표현 | 실제 조건 |
| --- | --- | --- | --- |
| 164 | 0 | 300단어 이하 | `<300` |
| 340 | 1 | 30단어 이하 | `<30` |
| 1092 | 0 | 300단어 이하 | `<300` |
| 1879 | 1 | 600단어 이하 | `<600` |
| 2243 | 0 | 150단어 이하 | `<150` |
| 3415 | 0 | 200단어 이하 | `<200` |
| 286 | 1 | 10문장 이하 | `<10` |
| 1268 | 0 | 6문장 이하 | `<6` |
| 1381 | 0 | 10문장 이하 | `<10` |
| 2266 | 0 | 7문장 이하 | `<7` |
| 2674 | 0 | 10문장 이하 | `<10` |
| 2780 | 0 | 6문장 이내 | `<6` |
| 3041 | 0 | 7문장 이하 | `<7` |
| 3691 | 0 | 10문장 이하 | `<10` |

문항의 원본 필드는 고정 Ko 데이터와 고정 영어 데이터, 실제 비교 연산은 원본 checker를 기준으로 대조했다.

#### **8.2.3. 단어 수·Markdown 정책에 관한 관찰**

다음은 같은 한국어 응답을 영어·Ko에 전달한 사례다. 원본 86건 중 아래 4개 입력을 포함해, 3345의 원본·override까지 **6개 입력을 양쪽에 재실행했고 과거 결과 행 전체와 일치**했다.

| key · case ID | 대상 조건의 실제 결과 | 관찰과 처리 |
| --- | --- | --- |
| 3442 · `comma_boundary_compact` | 영어 20단어: 실패/실패, Ko 18단어: 통과/통과 (`<20`) | 영어 정규식·Ko 공백 분리의 차이. 원본 Ko 유지 |
| 349 · `markdown_quote_valid_highlights_349` | 영어 39단어: 통과/통과, Ko 40단어: 실패/실패 (`<40`) | `>`를 임의로 제거하는 규칙을 추가하지 않음 |
| 136 · `markdown_star_balanced_136` | 영어 99단어: 통과/통과, Ko 108단어: 실패/통과 | `*` 제거 후보와 줄 배치 때문에 loose가 달라짐 |
| 136 · `markdown_dash_persistent_136` | 영어 통과/통과, Ko 실패/실패 | `-`는 loose에서 일괄 제거하지 않음 |

위 판정은 실제 evaluator의 strict/loose 결과다. 실측 단어 수는 checker의 counter 진단으로 별도 확인했으며 두 종류의 확인을 구분했다. NFC나 한국어 공백 기준처럼 원본 Ko에 이미 있는 adaptation 자체를 새 데이터 오류로 분류하지 않는다.

### **8.3. 규칙 적용 범위와 확인한 판정 차이**

분모는 **고정 Ko 342문항, 영어 541문항**이다. 같은 ID가 한 문항에 반복될 수 있어 고유 key 수와 instruction 발생 횟수를 구분했다.

| 규칙 | Ko 고유 문항 수 | Ko instruction 발생 횟수 | 영어 고유 문항 수 |
| --- | --- | --- | --- |
| 단어 수 | 34 | 36 | 50 |
| 문장 수 | 28 | 31 | 46 |
| 키워드 빈도 | 23 | 25 | 39 |
| bullet 수 | 24 | 24 | 31 |
| 강조 수 | 38 | 38 | 48 |

| 문항 집합의 교집합 | Ko 고유 key 수 | 영어 고유 key 수 |
| --- | --- | --- |
| 단어 수 ∩ bullet | 2 | 3 |
| 단어 수 ∩ 강조 | 8 | 8 |
| 단어 수 ∩ (bullet ∪ 강조) | 10 | 11 |
| 단어 수 ∩ bullet ∩ 강조 | 0 | 0 |

고정 Ko 데이터의 instruction 목록을 ID별로 집계하고, 고유 key 집합의 교집합을 계산했다. 반복 instruction ID도 발생 횟수에는 각각 포함했다. Ko 단어 수∩bullet은 key `136, 2284`다. 적용 문항 수는 오류 수나 모델 점수 변화량이 아니다. Markdown은 별도 형식 지시가 없어도 응답에 포함될 수 있어 교집합만으로 전체 영향을 판단할 수 없다.

기존 86건 중 `dataset` 범주 46건에서 대상 strict 또는 loose 판정이 영어·Ko 사이에서 달랐던 고유 key는 **6개: 136, 349, 1242, 3345, 3442, 3739**다. 이는 저장된 테스트 입력에 한정한 집계이며 합성·override를 제외했다. 3345처럼 언어별 응답이 다른 사례도 포함하므로, 동일 문자열에 대한 순수 checker 차이 6개라고 해석하지 않는다. key 3739의 문장 분리 차이와 부등호 번역 오류 제외 판단도 서로 다른 내용이다.

전체 모델 응답에서 판정이 얼마나 달라지는지, 총점에 얼마나 영향을 주는지는 미측정이다. 이번 분석은 적용 범위·대표 반례·원본 판정 근거를 확보한 범위에서 마무리하고 Lighteval 연결과 동등성 검증에 집중한다.

---

## **9. 검증 계획과 현재 확보한 자료**

### **9.1. 모델 후보와 현재 상태**

| 역할 | 모델 | 현재 상태 |
| --- | --- | --- |
| 환경 점검 | `HuggingFaceTB/SmolLM2-135M-Instruct` | `batch_size=1`로 ARC Easy 10문항 실행. IFEval-Ko 결과는 아님 |
| 통합·전체 평가 우선 후보 | `Qwen/Qwen2.5-1.5B-Instruct` | 한국어 지원·공식 chat template를 검토한 후보. 팀 채택 미확정 |
| 경량 대안 | `Qwen/Qwen2.5-0.5B-Instruct` | 주 후보의 실행 부담이 클 때 검토 |

[Qwen 공식 모델 카드](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)의 1.54B 모델을 우선 제안하되 모델·tokenizer revision·backend·dtype·실행 환경·20개 key는 팀 확정이 필요하다. [추가 후보 조사](evidence/analysis-details.md#extra-models)는 보조 자료로 옮겼으며 이번 문서 정리에서 모델 카드를 재조회하지 않았다.

#### **9.1.1. 검증 모델 및 고정 20문항 선정안**

주 검증 모델로 `Qwen/Qwen2.5-1.5B-Instruct`를 제안한다. 한국어를 지원하는 1.54B instruction 모델이며 공식 chat template를 제공한다. 반복 실행 시 메모리 부담을 고려하여 선정했으며, 실제 실행 환경에서 모델 로딩과 응답 생성을 확인한 뒤 세부 설정을 고정한다. 이번 검증의 목적은 동일한 응답에 대한 원본 Ko와 새 Lighteval-Ko의 채점 일치 여부를 확인하는 것이다.

고정 데이터 revision `54199e3801116897697babf341865741dcd06fc8`의 `allganize/IFEval-Ko`에서 다음 20문항을 선정안으로 구성했다.

```json
[3743, 136, 3518, 1233, 3445, 3442, 1262, 1082, 1127, 3710,
 122, 3563, 1107, 3073, 3311, 3750, 1203, 2142, 1268, 3538]
```

채점 특성 확인 16문항과 요청문·검사 설정 불일치 확인 4문항으로 구성했으며, 데이터에 등장하는 instruction ID 21종을 모두 포함한다. 개별 instruction은 총 33개다.

| 선정 기준 | 대표 key | 확인할 내용 |
| --- | --- | --- |
| 길이·형식 조건과 strict/loose 차이 | 136, 3442, 1262 | 단어·문장 수의 경계와 응답 변환이 판정에 미치는 영향 |
| 한국어 문자열 처리 | 1233, 3445, 3073, 3311 | 키워드 횟수, 조사 결합, 첫 어절 일치, 언어 판별 |
| 복수 지시와 응답 형식 | 3518, 3710, 1107 | JSON·강조·구분자 등의 검사와 일부 조건만 통과하는 경우 |
| 채점 범위 확인 | 3750 | 여러 선택 문구를 함께 포함해도 통과하는 현재 동작 |
| 요청문·검사 설정 불일치 | 1203, 2142, 1268, 3538 | 검사 키워드, 이하/미만, 글자 수/단어 수의 차이 |

이 목록은 채점 동작을 확인하기 위한 진단용 표본이며 전체 데이터셋의 모델 성능을 추정하는 표본으로 사용하지 않는다. 원본 prompt·instruction 순서·kwargs를 유지하고, 데이터 불일치의 수정 제안은 이식 검증과 별도로 다룬다.

### **9.2. 비교 방법과 합격 기준**

같은 고정 문항·응답을 원본 Ko와 새 Lighteval-Ko에 전달한다. 모델 응답은 한 번 생성해 저장하고 `(key, instruction_index, instruction_id)`별 판정과 집계를 비교한다. **등록 task 구현 → 저장 응답 회귀 → 고정 20문항 통합 → 전체 split 평가** 순으로 진행하며 상세 실행 절차는 [설계 문서](design.md#validation-plan)에 둔다.

| 비교 항목 | 제안하는 합격 기준 |
| --- | --- |
| 입력 대응 | key·instruction 순서·kwargs 대응 유지 |
| 개별 판정 | instruction별·prompt별 strict/loose Boolean 일치율 100% |
| 집계 | 분자·분모 일치, 네 지표 절대 오차 `1e-12` 이하 |
| 안정성·회귀 | 정상·실패·경계 입력 충족, 누락·미처리 예외 없음, 기존 영어 task 판정 유지 |

100%는 모델 정답률이 아닌 **두 evaluator의 판정 일치율**이다. 같은 예외가 나와도 해당 입력의 채점 검증은 미완료로 기록한다. 네 지표의 실제 비교 점수는 아직 미측정이다.

<a id="verification-status"></a>

### **9.3. 현재까지 확보한 검증 자료**

#### **9.3.1. 기존 86건의 구성과 실행 방식**

기존 입력·양쪽 결과의 case ID·순서·입력 hash와 고정 source 대응을 확인했다. 실제 데이터 조건 46건, 메모리 override 2건, 합성 fixture 38건으로 **각 evaluator당 86건**이며 고유 데이터 86문항이나 모델 생성 86회를 뜻하지 않는다.

실제 조건의 고유 key는 11개다: `127, 136, 349, 1127, 1237, 1242, 1480, 3073, 3345, 3442, 3739`. 고정 source·데이터 21개 파일과 실제 import module hash를 대조했고, 원본 `InputExample`과 strict/loose 함수를 직접 호출했다. 전체 instruction의 full, 대상 조건의 isolated, checker 진단을 구분했으며 전체 task/model CLI나 새 Lighteval-Ko 실행은 아니다.

직접 비교한 reference는 [영어 evaluator](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/ifeval/utils.py)와 [Ko evaluator](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/utils.py)다. [자료 안내·재현 방법](evidence/checker-audit/README.md)과 아래 원본 파일을 함께 확인할 수 있다.

| 자료 | 파일 |
| --- | --- |
| 86건의 입력·저장 응답 | [cases.json](evidence/checker-audit/cases.json) |
| 실행 코드 | [영어 runner](evidence/checker-audit/run_original.py), [Ko runner](evidence/checker-audit/run_ko.py), [공통 runtime](evidence/checker-audit/audit_runtime.py), [비교 스크립트](evidence/checker-audit/compare.py) |
| 원시·비교 결과 | [영어 86건](evidence/checker-audit/original_results.json), [Ko 86건](evidence/checker-audit/ko_results.json), [results.json](evidence/checker-audit/results.json) |
| 재현 정보 | [provenance.json](evidence/checker-audit/provenance.json), [requirements.lock.txt](evidence/checker-audit/requirements.lock.txt), [SHA256SUMS](evidence/checker-audit/SHA256SUMS) |

#### **9.3.2. 후속 실행과 미완료 항목**

| 자료 | 입력 수·비교 경로 | 확인한 결과·제한 |
| --- | --- | --- |
| 기준 환경 최소 재실행 | 3건 × 영어·Ko | 양쪽 6개 결과가 같은 쪽의 과거 전체 결과 행과 일치. 86건 전체 재실행 아님 |
| 부등호 경계값 | 14문항 × 3길이 = 42건 × 영어·Ko | 실측 길이·full/isolated 대상 판정·Ko 전체 판정 모두 기대값 일치 |
| Known Issue | 신규 17건＋과거 재실행 6건 = 23건 × 영어·Ko | 신규 기대값·과거 전체 결과 행 일치. 고유 key 7개 |
| metric 재사용 첫 비교 | 합성 11건 × 기존 영어 metric·French 어댑터·harness·Ko | 기대값 충족. 영어 계열과 Ko 차이 5건·4유형 |
| 언어별 추가 대조 | 별도 합성 23건 × 위 네 경로 | 기대값 충족. 영어 계열과 Ko 차이 10건 |
| 통합 20문항 | 새 등록 task와 원본 Ko | **20문항 선정안 작성완료·팀 확정 및 실행 대기** |
| 새 Lighteval-Ko 동등성 | 개별 판정·네 지표 비교 | **미수행·미측정** |

부등호·Known Issue 실행은 evaluator당 65건, 양쪽 합계 **130개 case 실행**이며 실제 함수 호출 수는 더 많다. Known Issue 23건과 언어별 합성 23건은 별도 입력 집합이다. French 어댑터는 합성 입력으로만 확인했으며 실제 French 데이터 전체나 별도 French reference와의 동등성을 검증한 것은 아니다. [상세 대조군·실행 범위](evidence/analysis-details.md#language-controls)에 기록을 보존했다.

#### **9.3.3. 첨부 범위와 재현 조건**

이번 첨부는 **기존 86건**의 입력·코드·원시 결과·revision·환경 정보다. 콘솔 로그 전체와 후속 42건·Known Issue 23건·metric 재사용 11건·언어 대조군 23건의 원본 자료는 포함하지 않았다. 보조 문서의 상세 표도 원본 실행 파일의 추가 첨부를 뜻하지 않는다.

[자료 README](evidence/checker-audit/README.md)에 복원·재현 명령을 정리했고 가상환경·캐시·source 전체는 제외했다. 기존 실행 환경과 원본 보존 확인은 [보조 기록](evidence/analysis-details.md#reference-environment)에 둔다. 이번 문서 정리에서는 평가를 재실행하지 않았다.

### **9.4. 구현·후속 검증으로의 인계**

구현 구조·입출력·테스트·생성 설정·미결정 사항은 [design.md](design.md)에 정리했다. 팀이 모델·환경·고정 20개 key를 확정한 뒤 통합 점검과 전체 평가를 진행한다. 업스트림 제안 초안은 [issue-draft.md](issue-draft.md)이며 데이터셋 제작자에게 보내는 오류 제보와 구분한다.

---

## **10. 고정 revision과 공개 출처**

| 대상 | revision·공개 출처 |
| --- | --- |
| 영어 lm-evaluation-harness | [`d6de81643928d653435c431bae19945d41d32520`](https://github.com/EleutherAI/lm-evaluation-harness/commit/d6de81643928d653435c431bae19945d41d32520) |
| 영어 google/IFEval 데이터 | [`966cd89545d6b6acfd7638bc708b98261ca58e84`](https://huggingface.co/datasets/google/IFEval/tree/966cd89545d6b6acfd7638bc708b98261ca58e84) |
| Allganize Ko 코드·데이터 | [`54199e3801116897697babf341865741dcd06fc8`](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/54199e3801116897697babf341865741dcd06fc8) |
| 진단한 Lighteval | [`c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14`](https://github.com/Hugging-Face-KREW/lighteval/commit/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14) |

공개 코드별 링크와 상세 조사 표는 [분석 보조 자료](evidence/analysis-details.md#public-sources)에 보존했다.
