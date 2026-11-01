# CLIcK 평가 태스크 설계

> **팀:** A팀 · 베이직파이브  
> **상태:** 수정 초안 v0.3 — 팀·메인테이너 검토 전  
> **작성·수정일:** 2026-11-01  
> **기준 자료:** CLIcK `analysis.md`(2026-10-19 조사), 제공된 「[EVAL] CLIcK: Korean cultural and language understanding」 이슈 본문

**목표:** CLIcK의 11개 분야·1,995문항을 Lighteval에서 **0-shot·단일 한국어 프롬프트·원본 보기 순서·전체 답변 문자열의 로그 확률 비교**로 평가한다. 아래의 정확한 템플릿·추적 방식·담당·날짜는 구현을 위한 **검토 제안**이며, 이슈 승인이나 모델 검증 완료를 뜻하지 않는다. 데이터 통계는 분석 보고서의 결과를 인용한다.

## 1. 태스크 이름과 파일 위치

| 항목 | 설계 |
| --- | --- |
| 태스크 이름 | `click:<category>` — 아래 §2의 11개 이름 사용 |
| 구현 파일 | `src/lighteval/tasks/tasks/click.py` |
| Prompt function | `click_prompt(line: dict, task_name: str) -> Doc` |
| 내부 변환 함수 | `build_click_payload()` — 입력 검사와 `query`, `choices`, `gold_index` 구성 |
| 태스크 등록 | 분야별 `LightevalTaskConfig` 11개를 모듈의 `TASKS_TABLE`에 등록 |
| 단위 테스트 파일 | `tests/tasks/test_click.py` **신설 제안**. 최종 위치는 제출 브랜치의 테스트 관례에 맞춤 |
| 팀 검증 자료 | 팀 저장소의 `validation/click/` **신설 제안**. 파일 목록·실행 설정·하네스 패치·비교 결과 보관 |

Lighteval의 [태스크 추가 가이드][le-custom]에 맞춰 **데이터 연결·문항 변환·기존 로그 확률 지표 연결**을 구현한다. 공통 추론 엔진을 교체하는 작업은 아니다. 모듈 import나 prompt function 안에서 다운로드·모델 로딩을 수행하지 않는다.

첫 버전에서는 few-shot, 생성형 API 평가, 논문의 반복 프롬프트·보기 순환 평가, 원본 문항 수정·삭제를 제외한다. 비교용 하네스 수정은 팀 검증 코드이며, 하네스 업스트림에 수정 PR을 제출하는 작업과는 구분한다.

**버전 관리:** 구현 시작 시 Lighteval의 실제 제출 기준 commit SHA를 기록한다. 분석 당시 SHA `7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7`와 최신 `main`을 같은 버전으로 취급하지 않는다. 아래 API 필드는 2026-11-01 열람한 [공식 설정 문서][le-tasks]를 참고했으며, 해당 SHA에서 import·태스크 등록·지표 연결을 테스트한다.

## 2. Subset, 평가 split, few-shot split

### 2.1 데이터 설정

| 설정 | 값 | 의미 |
| --- | --- | --- |
| `hf_repo` | `EunsuKim/CLIcK` | 원본 HF 데이터셋 |
| `hf_subset` | `default` | HF config 이름. `society`, `grammar` 등으로 바꾸지 않음 |
| `hf_revision` | `d61627859645b5e6edc03fd9f835735d8226fa4e` | 분석에 사용한 데이터 버전 고정 |
| `hf_data_files` | `{"train": CATEGORY_FILES[category]}` | 해당 분야 원본 JSON의 명시적 경로 목록 |
| `hf_avail_splits` | `["train"]` | 실제 제공 split |
| `evaluation_splits` | `["train"]` | 이 split의 모든 문항을 평가에 사용 |
| `few_shots_split` | `None` | 예시 문항 출처를 지정하지 않음 |
| `few_shots_select` | `None` | 예시 선정 방식 사용하지 않음 |
| `num_fewshots` | `0` | 기준 실행에서도 0-shot을 확인. 다른 shot 수의 실행을 기준 결과와 혼합하지 않음 |
| `must_remove_duplicate_docs` | `False` | 원본 행을 자동으로 제거하지 않음 |

**분야별 태스크와 HF subset은 다르다.** 예를 들어 `click:society`와 `click:grammar` 모두 HF subset은 `default`이며, 읽는 파일 목록만 달라진다. `train`이라는 이름도 이 작업에서 학습을 수행한다는 뜻은 아니다. 설정 필드는 [LightevalTaskConfig][le-tasks]를 따른다.

### 2.2 분야와 원본 파일 연결

`CATEGORY_FILES`에는 아래 폴더의 JSON 파일을 **고정 revision에서 확인한 상대 경로로 열거**한다. 목록은 경로순으로 정렬하고, 각 파일의 원본 배열 순서를 보존한다. 이 목록을 만드는 작업은 §7의 데이터 연결 산출물이다.

| 태스크 이름 | 원본 폴더 (`Dataset/` 하위) | 문항 수 | 5지선다 | 지문 있음 |
| --- | --- | ---: | ---: | ---: |
| `click:society` | `Culture/Korean Society/` | 309 | 0 | 0 |
| `click:tradition` | `Culture/Korean Tradition/` | 222 | 0 | 0 |
| `click:history` | `Culture/Korean History/` | 280 | 0 | 0 |
| `click:law` | `Culture/Korean Law/` | 219 | 0 | 0 |
| `click:politics` | `Culture/Korean Politics/` | 84 | 0 | 0 |
| `click:economy` | `Culture/Korean Economy/` | 59 | 0 | 0 |
| `click:geography` | `Culture/Korean Geography/` | 131 | 30 | 0 |
| `click:popular` | `Culture/Korean Popular/` | 41 | 0 | 0 |
| `click:textual` | `Language/Textual/` | 285 | 68 | 238 |
| `click:functional` | `Language/Functional/` | 133 | 112 | 106 |
| `click:grammar` | `Language/Grammar/` | 232 | 46 | 9 |
| **합계** | **문화 1,345 / 언어 650** | **1,995** | **256** | **353** |

출처: 팀 `analysis.md` §3 및 [고정 데이터 revision][dataset]. 최종 로딩 결과도 **26개 파일·1,995행**이어야 한다. ID 패턴으로 분야나 보기 수를 추정하지 않고, 원본 경로와 `len(choices)`를 사용한다.

### 2.3 중복 ID와 문항 추적

원본 `id`는 유일하지 않다. 검증 도구는 `데이터 revision + 원본 파일 경로 + 파일 내 0-based 행 번호`를 문항 키로 사용한다. 파일 목록에는 파일 해시와 행 수를 함께 저장한다.

HF 로딩 후 경로가 사라지는 경우, 원본 5개 필드(`id`, `paragraph`, `question`, `choices`, `answer`)를 정규화 없이 고정 JSON 형식으로 직렬화한 SHA-256과 분야를 이용해 원본 목록에 연결한다. **한 행에 유일하게 연결되는지 먼저 검사**하며, 연결이 모호하면 임의로 첫 행을 고르지 않고 파일별 로딩 단계에서 경로·행 번호를 부착한다. 태스크의 `Doc.specific`에 추적용 해시를 보존하되, 결과 로그까지 유지되는지 통합 테스트한다. 원본 ID·해시를 중복 제거 기준으로 쓰지 않는다. [Doc 메타데이터 정의][le-doc]

## 3. Prompt function: 원본 필드와 `Doc` 대응

### 3.1 필드 대응표

| 원본 필드·설정 | `Doc` 위치 | 변환·검사 규칙 |
| --- | --- | --- |
| `paragraph` | `query`의 지문 블록 | `paragraph.strip()`이 비어 있지 않을 때만 원문 전체 포함 |
| `question` | `query`의 질문 블록 | 원문·내부 보기·줄바꿈 유지. 빈 질문은 오류 |
| `choices` | `query`의 선택지 블록 | 원본 순서로 `A. 내용` … `D. 내용` 또는 `E. 내용` 표시 |
| `choices` | `choices` | `" A. 내용"`처럼 **앞 공백 1개 + 알파벳 + `. ` + 원문**을 후보로 사용 |
| `answer` | `gold_index` | `choices.index(answer)`의 0-based 위치. 정확히 일치하는 보기가 하나여야 함 |
| `id` | `specific["original_id"]` | 추적용. 모델 입력이나 유일 키로 사용하지 않음 |
| 원본 5개 필드 | `specific["raw_row_sha256"]` | §2.3의 원본 연결용 해시. 모델 입력에는 포함하지 않음 |
| 분야별 태스크 이름 | `task_name` | `click:society` 등 |
| 한국어 지시문 | `query`의 첫 블록 | 지시문을 `instruction`에 다시 넣어 중복 적용하지 않음 |

`answer`는 정답 위치 계산에만 사용한다. 정답을 다른 유효 보기로 바꾸어도 `query`와 후보 문자열은 바뀌지 않아야 한다. 원본 문자열의 공백·Unicode·구두점을 정답 매핑 목적으로 보정하지 않는다. `Doc`의 기본 필드는 [공식 정의][le-doc]를 따른다.

### 3.2 프롬프트 형식

프롬프트 버전은 `click_ko_single_v1`으로 기록한다. 아래 **블록 이름·배치·공백은 팀 설계안**이지, 공개되지 않은 논문 실행 코드를 복원한 결과가 아니다.

```text
주어진 질문을 천천히 읽고, 적절한 정답을 {labels} 중에 골라 알파벳 하나로 답하시오.

[지문]
{paragraph}

[질문]
{question}

[선택지]
{labeled_options}

정답:
```

`labels`는 `A, B, C, D` 또는 `A, B, C, D, E`다. 지문이 없으면 지문 블록 전체를 생략한다. 블록 사이는 줄바꿈 2개이며, 실제 `query`는 마지막 콜론으로 끝난다. 후보는 ASCII 공백 1개로 시작하므로 연결하면 `정답: E. 서울`이 된다. 원본 필드 내부의 공백·줄바꿈은 유지한다.

기본 검증은 채팅 템플릿과 별도 system prompt를 끈다. BOS 처리와 토큰화 경계를 양쪽 도구에서 맞추고, 후보 뒤 EOS를 채점에 추가하지 않는다. 문자열을 따로 토큰화한 결과를 단순 연결해도 같을 것이라 가정하지 말고, **실제 유효 토큰·후보 시작 위치·채점 마스크**를 확인한다.

### 3.3 5지선다 예시와 기대 결과

다음은 원본 데이터가 아닌 합성 테스트 문항이다. 입력의 `choices`는 `["부산", "대구", "인천", "대전", "서울"]`, `answer`는 `"서울"`, `paragraph`는 빈 문자열이다.

```text
주어진 질문을 천천히 읽고, 적절한 정답을 A, B, C, D, E 중에 골라 알파벳 하나로 답하시오.

[질문]
대한민국의 수도는 어디인가?

[선택지]
A. 부산
B. 대구
C. 인천
D. 대전
E. 서울

정답:
```

기대 `Doc.choices`는 `[" A. 부산", " B. 대구", " C. 인천", " D. 대전", " E. 서울"]`, 기대 `gold_index`는 **4**다. 입력에 E를 표시하는 것과 E 후보를 점수화하는 것을 모두 검사한다.

### 3.4 변환 함수 설계

다음 순수 함수와 얇은 `Doc` 어댑터로 분리한다. 순수 함수 테스트와 Lighteval 통합 실행은 별개다. 메타데이터는 입력에 붙이지 않는다.

<details>
<summary>입력 검사와 변환 함수 예시</summary>

```python
from collections.abc import Mapping


def build_click_payload(row: Mapping[str, object]) -> dict[str, object]:
    """click_ko_single_v1 문자열 계약. Lighteval 실행 코드 전체는 아니다."""
    fields: dict[str, str] = {}
    for key in ("id", "paragraph", "question", "answer"):
        value = row.get(key)
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        fields[key] = value

    options = row.get("choices")
    if not isinstance(options, list) or len(options) not in (4, 5):
        raise ValueError("choices must contain four or five options")
    if any(not isinstance(option, str) or not option.strip() for option in options):
        raise ValueError("each option must be a nonempty string")
    if not fields["question"].strip():
        raise ValueError("question must be nonempty")
    if options.count(fields["answer"]) != 1:
        raise ValueError("answer must match exactly one option")

    labels = "ABCDE"[:len(options)]
    instruction = (
        "주어진 질문을 천천히 읽고, 적절한 정답을 "
        + ", ".join(labels)
        + " 중에 골라 알파벳 하나로 답하시오."
    )
    blocks = [instruction]
    if fields["paragraph"].strip():
        blocks.append("[지문]\n" + fields["paragraph"])
    blocks.append("[질문]\n" + fields["question"])
    labeled_options = [
        f"{label}. {option}" for label, option in zip(labels, options)
    ]
    blocks.append("[선택지]\n" + "\n".join(labeled_options))
    blocks.append("정답:")

    return {
        "query": "\n\n".join(blocks),
        "choices": [" " + option for option in labeled_options],
        "gold_index": options.index(fields["answer"]),
    }
```

```python
import hashlib
import json

from lighteval.tasks.requests import Doc


def click_prompt(line: dict, task_name: str) -> Doc:
    payload = build_click_payload(line)
    raw = {key: line[key] for key in
           ("id", "paragraph", "question", "choices", "answer")}
    encoded = json.dumps(
        raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return Doc(
        task_name=task_name,
        specific={
            "original_id": line["id"],
            "raw_row_sha256": hashlib.sha256(encoded).hexdigest(),
        },
        **payload,
    )
```

</details>

## 4. 채점: 지표, 생성 길이, stop sequence, 정답 추출

### 4.1 채점 설정

| 항목 | 설정·처리 |
| --- | --- |
| 평가 방식 | 전체 후보 문자열의 조건부 로그 확률 비교. 자유 답변 생성은 하지 않음 |
| 지표 | `loglikelihood_acc` 계열. 의미는 **후보 전체 로그 확률 합 → argmax → 정오 평균** |
| 지표 계산 객체 | `LoglikelihoodAcc(logprob_normalization=None)`에 해당하는 동작. 대상 SHA의 등록된 metric에 연결 |
| 길이 정규화 | 사용하지 않음. 토큰 수·문자 수로 나누지 않고 PMI 보정도 하지 않음 |
| 생성 길이 | **해당 없음.** 태스크의 `generation_size=None` |
| Stop sequence | **사용하지 않음.** 태스크의 `stop_sequence=None` |
| 정답 추출 규칙 | **생성 문장 추출 없음.** 최고 점수 후보의 인덱스를 `gold_index`와 비교 |
| 답변 텍스트 정규화 | 생성 답변이 없으므로 없음. 원본 정답 매핑도 정확한 문자열 일치 사용 |
| `temperature`, `top_p` | 사용하지 않음. 생성 설정을 평가 조건처럼 기입하지 않음 |

생성 길이를 1로 두어 알파벳을 생성하는 방식이 **아니다**. `None`은 이번 태스크에서 생성 경로를 사용하지 않는다는 의미이며, 모델 입력 길이 제한이 없다는 의미는 아니다. 지표의 의미·정규화 인자는 [공식 지표 문서][le-metrics], 생성 설정은 [태스크 설정 문서][le-tasks]를 참고한다.

### 4.2 계산과 집계

```text
score(j) = 후보 j의 모든 토큰에 대한 조건부 로그 확률의 합
predicted_index = argmax_j score(j)
correct = 1 if predicted_index == gold_index else 0
분야별 accuracy = 해당 분야의 정답 수 / 해당 분야의 전체 평가 문항 수
```

프롬프트 토큰·패딩·추가 EOS는 후보 점수에 넣지 않는다. 정확한 동점은 원본 순서의 첫 후보를 선택한다. 후보별 점수 수가 보기 수와 다르거나 `NaN`·무한대·빈 채점 구간이 발생하면 정상 예측으로 처리하지 않고 실행 오류로 기록한다.

기본 산출물은 **11개 분야별 정확도와 정답 수·문항 수**다. 검증 보고서에서 문화 문항 평균(분모 1,345), 언어 문항 평균(650), 전체 문항 평균(1,995), 11개 분야 macro 평균을 추가하되 서로 다른 이름으로 표시한다. 분모는 전체 평가 완료 시에만 사용하고, 논문 `Average`와 같은 산식이라고 전제하지 않는다.

### 4.3 긴 입력 처리

모델별로 평가 전에 실제 토큰화·특수 토큰 정책을 적용해 **프롬프트와 모든 후보의 문맥 한도**를 검사한다. 자동 잘림·문항 제외를 기본값으로 허용하지 않는다. 한도 초과가 있으면 해당 모델은 `BLOCKED_CONTEXT`로 표시하고, 별도 잘림 조건을 합의·기록하기 전에는 전체 원문 평가 완료로 간주하지 않는다. 후보 앞 공백·템플릿·정규화·보기 순서를 바꾸면 프롬프트/태스크 버전을 갱신하고 새 결과로 저장한다.

## 5. 공식 방식과 다른 점 및 이유

### 5.1 논문·저자 설명과의 관계

| 항목 | 논문·저자 자료에서 분석한 내용 | 이번 구현과 이유 |
| --- | --- | --- |
| 지시문 표현 | 3가지 표현 사용. 정확한 전체 원문은 분석에서 확인하지 못함 | 1개를 명시적으로 고정. 임의의 세 표현을 만들어 공식 재현이라 부르지 않음 |
| 보기 순서 | 보기를 순환 배치하며 평가 | 원본 순서 고정. 첫 기여 범위를 제한하며 위치 민감도 평가까지 수행했다고 주장하지 않음 |
| 문항당 평가 | 4지선다 12회, 5지선다 15회 | 조건 1개로 정오 1개 산출. 실제 후보 채점 연산은 보기 수만큼 필요 |
| Few-shot | 실제 실험 전체의 shot 수를 명확히 확인하지 못함 | 명시적 0-shot. 별도 예시 선정·중복 관리 없이 재현 가능한 조건부터 구현 |
| 공개 모델 채점 후보 | 저자 설명은 `알파벳. 보기 내용` 전체 | 이 후보 유형을 따름. 프롬프트의 ‘알파벳 하나’ 지시와 채점 후보를 구분 |
| 길이 정규화 | 적용 여부를 확인하지 못함 | 미사용은 **팀 선택**. 긴 후보에 불리한 효과가 생길 수 있으며 정확도 개선을 보장하지 않음 |
| 입력 세부 형식 | 정확한 공백·경계·채팅 템플릿 등 미확인 사항 존재 | §3의 별도 템플릿을 버전 관리. 원문 전체 조건을 복제했다고 주장하지 않음 |
| API 모델 평가 | 생성 답변에서 정답을 판정하는 별도 절차 | 첫 버전에서 제외. 생성 전용 API 지원을 약속하지 않음 |

근거: 팀 `analysis.md` §5, [논문][paper], 보고서가 인용한 [저자 답변][author-scoring]. **이번 결과는 논문 Table 5의 완전 재현 결과가 아니라, 명시된 단일 조건의 CLIcK 평가 결과다.**

### 5.2 기존 하네스와의 차이

기존 하네스는 **공식 저자 코드가 아닌 참고 구현**이다. 아래는 분석한 revision `d6de81643928d653435c431bae19945d41d32520` 기준이며, 현재 최신 버전의 상태를 단정하지 않는다.

| 항목 | 분석한 하네스 | 비교용 하네스·새 Lighteval 설계 |
| --- | --- | --- |
| 5지선다 입력 | A–D만 표시하는 함수 | 모든 4·5개 보기 표시 |
| 채점 후보 | 알파벳만 채점 | 알파벳과 보기 내용 전체 채점 |
| 분야 선택 | ID 필터 사용. Grammar 233 / Functional 132 | 원본 파일 기준. Grammar 232 / Functional 133 |
| 비교 조건 | 이 설계와 다른 프롬프트·후보 | §3–4의 입력·후보·0-shot·정규화·집계를 동일하게 적용 |

근거: 팀 `analysis.md` §6, [문화 코드][harness-culture]·[언어 코드][harness-language]. 보완한 참고 구현은 패치·commit을 기록하고, 원래 하네스 결과와 별도로 저장한다. 차이를 단순히 ‘버그 수정으로 정답률이 개선됨’이라고 해석하지 않는다.

**데이터 이용 조건:** 분석·이슈 작성 시 명시적 데이터 라이선스를 확인하지 못했다. 이번 문서가 새로운 저자 답변을 확보했다는 뜻은 아니다. 저자에게 적용 조건을 문의하고 진행 상태를 기록한다. 데이터·원문이 포함된 로그는 별도 재배포하지 않으며, 미확인 상태에서의 공개·병합 방침은 메인테이너와 확인한다.

## 6. 테스트 계획: 입력, 확인 사항, 기대 결과

### 6.1 모델 없이 수행하는 단위·데이터 테스트

| ID | 테스트 입력 | 확인할 사항·기대 결과 |
| --- | --- | --- |
| U01 | 4지선다·지문 없음·정답 C인 합성 문항 | A–D 모두 표시, E 없음, 후보 4개, `gold_index=2`, 지문 블록 생략 |
| U02 | 5지선다·지문 있음·정답 E인 합성 문항 | 지문 원문과 E 표시, 후보 5개, `gold_index=4` |
| U03 | 4·5지선다 각각에서 모든 정답 위치 순회 | 0-based 인덱스와 A–D/E 대응 정확. ID 내용이 보기 수를 바꾸지 않음 |
| U04 | 한글·한자·분해형 Unicode·앞뒤 공백·줄바꿈을 포함한 원문 | 원문 보존. 공백만 있는 지문만 생략. §3의 문자열 스냅샷과 일치 |
| U05 | 정답만 다른 유효 보기로 바꾼 문항, ID만 바꾼 문항 | 정답 변경은 `gold_index`만 바꿈. ID는 모델 입력에 영향 없음 |
| U06 | 필드 누락·잘못된 타입·3/6지선다·빈 보기·정답 없음·정답 중복 | `ValueError`. 자동 수정·skip으로 평가를 계속하지 않음 |
| U07 | 중복 ID를 가진 서로 다른 문항·중복 오답 보기 | 행·보기 수와 순서를 유지. 추적 키가 원본 행에 정확히 연결됨 |
| U08 | 가상 후보 점수 `[-2,-3,-8,-9]`, 길이 `[4,12,4,4]` | 원시 합 기준 A 선택. 길이로 나누면 B가 되는 사례로 정규화 혼입 검출 |
| U09 | 가상 동점·`NaN`·무한대·누락된 후보 점수 | 동점은 첫 후보. 비정상 점수·후보 수 불일치는 오류 |
| U10 | 정오 `[1,0,1]` 등 사전 계산한 결과 | 정답 수 2·분모 3·정확도 `2/3`. 분야 macro와 문항 평균을 구분 |
| D01 | 고정 revision의 전체 26개 파일 | 1,995행, 4지선다 1,739·5지선다 256·지문 353·정답 E 49행, §2의 분야별 수 일치 |
| D02 | `Functional_CSAT.json#82` 및 중복 ID 사례 | Functional 분류 유지, 고유 ID 1,987개여도 평가 행은 1,995개 유지 |
| D03 | 로더 결과·원본 목록·결과 로그를 연결한 데이터 | 분야·행 내용·출현 횟수·추적 키가 일치. 일대일 연결 실패를 검출 |

단위 테스트는 네트워크·GPU 없이 합성 데이터로 실행한다. 원본 전체를 읽는 D01–D03은 **별도 통합 검사**이며 네트워크 의존성을 기본 단위 테스트에 섞지 않는다. 원본 데이터 파일을 테스트 fixture로 복사해 배포하지 않는다.

### 6.2 Lighteval 통합·실제 모델 테스트

| ID | 입력·환경 | 확인할 사항·기대 결과 |
| --- | --- | --- |
| I01 | 대상 commit의 태스크 레지스트리·11개 설정 | 태스크 이름 중복 없음, 모두 등록됨. split·revision·중복 제거 OFF가 실제 적용됨 |
| I02 | 4·5지선다 샘플의 실제 평가 요청 | 전체 후보 4/5개를 loglikelihood로 채점. 생성·few-shot·채팅 템플릿이 섞이지 않음 |
| M01 | 짧은 4·5지선다 및 지문 문항, 동일 모델 | 별도 forward 계산으로 후보 토큰의 log-softmax 합 검산. 첫 토큰 이후 본문도 합산하며 프롬프트·패딩·추가 EOS 제외 |
| M02 | 문맥 한도 경계·초과 문항 | 실제 길이와 잘림 여부 확인. 초과는 `BLOCKED_CONTEXT`; 몰래 제외한 점수를 전체 점수로 보고하지 않음 |
| M03 | 동일 샘플을 보완한 하네스와 Lighteval에 입력 | 실제 프롬프트·후보·정답·유효 토큰·채점 구간 일치. 후보별 점수와 예측까지 비교 |
| M04 | 같은 모델로 전체 1,995문항 | 분야별·전체 집계 대조, 예측 불일치 전수 조사. 같은 정확도만으로 통과시키지 않음 |

M01은 두 도구의 채점 함수를 복사해 호출하지 않고, 모델 출력으로 독립 계산한다. 양쪽 프롬프트 구현도 동일한 명세와 **수동 기대 문자열**로 검증하여 공통 오류를 놓치지 않는다. 패딩 배열 자체의 동일성 대신 유효 입력·후보 토큰과 채점 구간을 비교한다.

### 6.3 사용할 모델과 실행 순서

| 모델 | 검증 목적 |
| --- | --- |
| `Qwen/Qwen2.5-7B-Instruct` | 주 비교 모델: 보완 하네스 ↔ Lighteval |
| `kakaocorp/kanana-1.5-8b-instruct-2505` | 다른 모델·토크나이저에서 같은 조건 확인 |
| `EleutherAI/polyglot-ko-1.3b` | 도구 간 비교 및 논문과 조건 차이가 있는 참고 비교 |
| `EleutherAI/polyglot-ko-12.8b` | 다른 크기에서도 같은 검증·논문 참고 비교 |

이는 `analysis.md` §9의 네 모델 계획을 유지한 것이며 실행 결과가 아니다. H200·양자화 없는 BF16은 해당 보고서의 환경 제안이고 확보 여부는 미확인이다. 모델별로 **길이 검사 → 소규모 검산·배치 1 비교 → 수치 허용 범위 고정 → 전체 비교** 순으로 진행한다. 샘플은 분야별 경로·행 번호순 최대 10행에 경계 사례를 보충하고 실제 키 목록을 고정한다.

`atol`, `rtol`은 독립 검산을 통과한 교정 샘플에서 결정하고 별도 확인 샘플에도 적용한 뒤 본평가 전에 고정한다. 현재는 측정하지 않은 수치를 임의로 적지 않는다. 비교식은 `abs(s_le - s_ref) <= atol + rtol * abs(s_ref)`이며, 사후에 결과에 맞춰 기준을 넓히지 않는다.

### 6.4 기록과 완료 조건

실행 기록에는 데이터·모델·토크나이저·두 도구의 revision, 패치 해시, 실제 명령·설정, 프롬프트 버전, 특수 토큰·정밀도·백엔드·배치·문맥 한도·seed·캐시 사용 여부를 남긴다. 문항별로 키·정답·후보 점수·예측·정오·잘림 여부를 보존하고, 토큰·입력 로그는 로컬 검증용으로 관리한다. 설정이 다른 실행 간 캐시가 재사용되지 않게 구분한다.

**합격 조건:** 문항 집합·입력·정답·채점·집계가 정확하고, 전체 평가에서 설명되지 않은 점수·예측 불일치가 0건이어야 한다. 예측 100% 일치를 목표로 하되, 재계산으로 확인된 수치 차이의 예외는 건수·영향·근거를 별도로 보고한다. 점수가 가깝다는 이유만으로 수치 오차라고 판단하지 않는다.

상태는 **미실행 / 보류 / 실패 / 통과(수치 예외가 있으면 명시)**로 구분한다. 길이·환경 때문에 막힌 모델을 통과로 표시하거나 임의의 다른 모델로 대체하지 않는다. 단위 테스트 완료, 모델별 전체 검증 완료, 논문 참고 비교 완료를 각각 기록하며, 네 모델 중 보류가 있으면 전체 검증 계획은 부분 완료다.

## 7. 작업 나누기: 담당과 날짜

**아래는 합의 전 역할 배정·목표일 제안이며 실제 프로그램 마감일이 아니다.** 참여자 표기는 `@hyeongrae-kim`, `@GeonRyoung`, `@ojm6135`로 통일한다. `@hyeongrae-kim`은 [GitHub PR 작성자 목록](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pulls?q=is%3Apr+state%3Aopen+author%3Ahyeongrae-kim)에서 사용자가 지정한 계정이다. 역할과 목표일은 팀이 검토 후 확정한다. 날짜는 한국 시간 기준이다.

| 작업 | 담당 제안 | 교차 검토 | 목표일 제안 | 완료 산출물 |
| --- | --- | --- | --- | --- |
| 설계 검토·기준 Lighteval SHA 고정 | 팀 공동 | 팀 공동 | 2026-11-02 | 이 문서의 결정 항목, 실제 API 확인 기록 |
| 라이선스·초기 범위 확인 요청 | `@hyeongrae-kim` | 팀 공동 | 2026-11-02 | 저자·메인테이너 문의 기록. **답변 도착일의 약속이 아님** |
| 분야별 파일 목록·데이터 검사·추적 연결 | `@GeonRyoung` | `@ojm6135` | 2026-11-03 | `CATEGORY_FILES`, 원본 목록, D01–D03 검사 결과 |
| Prompt function·입력 단위 테스트 | `@GeonRyoung` | `@hyeongrae-kim` | 2026-11-04 | `click_prompt`, 스냅샷, U01–U07 |
| 태스크 등록·지표·집계 연결 | `@hyeongrae-kim` | `@GeonRyoung` | 2026-11-04 | 11개 설정, U08–U10, I01 |
| 비교용 하네스 보완 | `@ojm6135` | `@hyeongrae-kim` | 2026-11-05 | 모든 보기·분야·프롬프트·후보를 맞춘 패치 |
| 소규모 모델 검산·허용 오차 결정 | `@ojm6135` | `@GeonRyoung` | 2026-11-06 | I02·M01–M03, 고정 샘플·허용 범위 |
| Qwen·Kanana 전체 비교 | `@ojm6135` | `@GeonRyoung` | 2026-11-09 | 모델별 1,995문항 결과·불일치 분석 |
| Polyglot 두 모델 비교·논문 참고 비교 | `@hyeongrae-kim` | `@ojm6135` | 2026-11-11 | 모델별 결과 또는 구체적인 보류 사유 |
| 결과 문서·테스트 교차 검토 | 팀 공동 | 팀 공동 | 2026-11-12 | 실행 방법·범위 차이·모델별 상태·오류 수정 기록 |
| 업스트림 PR 준비·제출 판단 | `@hyeongrae-kim` | 팀 공동 | 2026-11-13 | 코드·테스트·재현 기록. 미해결 조건은 명시 |

**제출 전 확인:** 파일·필드 매핑과 4·5지선다 테스트 통과, 모델별 실제 검증 범위 공개, 모든 불일치 원인 기록, 공식 평가와의 차이 명시, 데이터 이용 조건·메인테이너 의견 상태 확인. 조건이 충족되지 않으면 날짜에 맞추기 위해 완료로 바꾸지 않고 보류 사유와 다음 확인 항목을 기록한다. 메인테이너 승인·병합일은 팀이 보장할 수 있는 일정에 포함하지 않는다.

---

**근거 자료:** 팀의 CLIcK `analysis.md` §3–9, 제공된 이슈 본문, [관련 팀 PR #24][team-pr], [논문][paper], [데이터][dataset], [저자 답변][author-scoring], [Lighteval 태스크 가이드][le-custom]·[설정 API][le-tasks]·[Doc][le-doc]·[지표 API][le-metrics]. 이슈·PR 댓글의 실시간 승인 상태와 실제 모델 검증 결과는 이번 수정에 포함하지 않았다.

[team-pr]: https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/24
[paper]: https://aclanthology.org/2024.lrec-main.296/
[dataset]: https://huggingface.co/datasets/EunsuKim/CLIcK/tree/d61627859645b5e6edc03fd9f835735d8226fa4e
[author-scoring]: https://github.com/rladmstn1714/CLIcK/issues/6#issuecomment-2132901818
[harness-culture]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/click/click_cul/utils.py
[harness-language]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/click/click_lang/utils.py
[le-custom]: https://huggingface.co/docs/lighteval/main/en/adding-a-custom-task
[le-tasks]: https://huggingface.co/docs/lighteval/main/en/package_reference/tasks
[le-doc]: https://huggingface.co/docs/lighteval/main/en/package_reference/doc
[le-metrics]: https://huggingface.co/docs/lighteval/main/en/package_reference/metrics
