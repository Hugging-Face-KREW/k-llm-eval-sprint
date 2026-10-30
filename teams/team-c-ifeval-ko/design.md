# IFEval-Ko 설계 문서

[분석보고서](analysis.md)의 구현·검증 계획을 이관한 **설계 초안**이다. 실험 결과와 Known Issues는 분석보고서를 기준으로 하며 이 문서는 구현 계약·실행 절차·미결정 사항을 다룬다. 구조·모델·backend·담당·일정은 팀 리뷰로 확정해야 하며 새 Ko task와 주입 API가 이미 구현됐다는 뜻은 아니다.

<a id="task-structure"></a>

## 1. 태스크 이름·파일 위치·구조 선택

기여 대상은 `Hugging-Face-KREW/lighteval`이다. 태스크 이름은 `ifeval_ko`, 등록·문항 변환 진입점은 `src/lighteval/tasks/tasks/ifeval_ko/main.py`를 제안한다. 파일 구성은 구조 선택 후 확정한다.

| 안 | 역할 분담 | 확정 전 확인 |
| --- | --- | --- |
| A. 별도 Ko 패키지 | `main.py`에서 등록·Doc 변환·metric 연결, Ko checker·registry·utility를 별도 모듈에 둠 | 원본 동작·라이선스 보존, 영어와 중복되는 코드의 유지보수 |
| B. 공통 metric 확장 | 공통 채점 루프에 registry·응답 normalizer·checker 구성 정책을 선택하도록 하고 Ko 특화 부분을 분리 | 기존 API의 확장이 필요하며 registry 교체만으로는 충분하지 않음 |

공통 루프 재사용을 우선 검토하되 메인테이너 선호와 팀 설계 리뷰로 결정한다. NFC 적용 위치, utility·고정 옵션, kwargs 필터·prompt 보완, checker 생성 시점·상태·난수·예외까지 같아야 한다. 기존 영어 task의 기본 동작을 유지한다.

## 2. 데이터·subset·평가 split·few-shot

| 항목 | 설계 기준 |
| --- | --- |
| 데이터 | `allganize/IFEval-Ko`, 분석보고서의 고정 revision |
| config / split | `default` / `train`; 이름이 train이어도 평가에 사용 |
| few-shot | 0-shot; few-shot 예시를 추가하지 않음 |
| 문항 식별 | `key` 사용. 실제 로딩한 key 목록·문항 수·중복·누락을 기록 |
| 원본 보존 | instruction ID·순서·kwargs와 원본 prompt 유지. 데이터 오류 수정은 별도 제안 |

전체 split의 분모는 고정 revision을 로딩해 확인한 결과로 결정한다. 데이터셋 특성과 대표 사례는 [분석보고서 3장](analysis.md)에 둔다.

<a id="input-contract"></a>

## 3. Prompt 함수와 입력·출력 계약

| 원본 데이터·생성 결과 | Lighteval 대응·검증 기준 |
| --- | --- |
| `prompt` | `Doc.query`; chat template 이전 원문도 보관 |
| `instruction_id_list` | 현재 영어 경로의 `Doc.specific["instructions_id_list"]`와 명칭 대응을 명시하고 순서·반복 ID 보존 |
| `kwargs` | 같은 index의 instruction과 연결. 원본 값과 실제 evaluator 전달 값을 각각 기록 |
| `key` | 결과 추적용 메타데이터. 행 순번과 구분 |
| `choices=[""]`, `gold_index=0` | 생성형 task의 형식상 값으로 객관식 정답을 의미하지 않음 |
| 모델 응답 | raw 응답과 실제 채점할 assistant 응답을 보관. `ModelResponse.final_text[0]` 등 추출·후처리 경계를 고정 |
| 채점 출력 | instruction 순서별 `strict_flags`, `loose_flags`, 문항별 `all(flags)`와 네 집계 지표 |

대응 키는 `(key, instruction_index, instruction_id)`다. 반복 ID를 dict key 하나로 합치지 않는다. 비교 코드에서 공백·Markdown·한국어 문자를 임의로 정리하거나 양쪽 결과를 대신 계산하지 않는다.

<a id="scoring"></a>

## 4. 채점·생성·응답 처리

### 4.1. 원본 Ko와 같아야 하는 처리

| 처리 | 구현 계약 |
| --- | --- |
| checker 구성 | Ko의 `if v` kwargs 필터, 필요 시 prompt 보완, 클래스별 누락 필드·fallback·예외 보존 |
| 길이·고정 문구 | Ko 단어·문장 utility와 허용 선택·ending 옵션 사용 |
| NFC | 원본 Ko가 적용하는 응답·비교 문자열과 처리 순서를 보존. 모든 kwargs에 일괄 NFC를 새로 적용하지 않음 |
| strict / loose | 실제 strict 진입, 원본 loose 후보 생성, 빈 후보 배제, instruction별 후보 OR와 문항별 AND 보존 |
| 상태·난수 | checker 생성 시점·상태·언어 판별 의존성·난수 사용을 기록하고 반복 판정 차이 조사 |
| Known Issues | 기본 구현에서 keyword나 부등호를 임의 수정하지 않고 별도 제보·개선 제안으로 관리 |

고정 선택지를 재사용할 때는 태스크별 허용 옵션을 선택한다. 영어 검사 실패 후 Ko도 검사하는 OR fallback은 영어 문구만으로도 통과시킬 수 있어 원본 Ko와 다르다. 원본의 strip 후 포함 검사도 보존한다. 클래스별 변경·등록 현황은 [분석 보조 자료](evidence/analysis-details.md#ko-classes)에 둔다.

### 4.2. 실행 경로와 집계

첫 구현은 native metric/Pipeline 경로와 네 지표 제공을 기준으로 제안한다. instruction-level은 모든 instruction 판정을 합친 분모로 계산하고 문항별 통과율을 평균하지 않는다. 공식 정의·loose 규칙은 [분석보고서 5장](analysis.md#official-evaluation)을 따른다.

[고정 IFEval 코드](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/ifeval/main.py)의 Inspect scorer는 prompt-level strict·loose 두 값만 반환한다. French task에는 Inspect sample_fields·scorer가 없고 [get_inspect_ai_task guard](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/main_inspect.py#L48-L59)에 걸린다. Inspect 지원 범위는 메인테이너 질문·팀 결정으로 남기며 전체 Inspect backend 검증 완료로 표시하지 않는다.

### 4.3. 생성·종료·응답 추출

출발점은 고정 [Ko task YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml)의 sampling 비활성화, `temperature=0.0`, `max_gen_toks=1280`, stop 문자열 `<end_of_turn>`·`<|im_end|>`다. 최종 backend에 전달된 실제 값과 모델별 EOS 처리를 별도로 기록한다.

chat template는 한 번만 적용하고 생성 토큰에서 입력 구간을 제외하는 등 assistant 응답 경계를 확인한다. backend의 EOS·stop 처리와 evaluator 전처리를 구분한다. 같은 저장 응답을 양쪽에서 재채점하며 후처리 범위 변경은 별도 설정으로 관리한다.

길이 상한에 도달한 응답은 잘림·종료 사유를 표시해 동일하게 채점한다. OOM·timeout 등 생성 실패를 가짜 응답으로 치환하거나 분모에서 제외하지 않고 실행 오류로 기록한다.

## 5. 공식 방식과의 차이·보존 범위

Lighteval 등록·자료형·실행 경로에 맞춘 구조 변환을 수행하되 Ko 데이터·checker·정규화·strict/loose·집계 동작을 보존한다. French와 Ko의 차이 및 이미 확인한 반례는 [분석보고서 6·8장](analysis.md)에만 정리하고 설계에서 중복 서술하지 않는다.

원본 Ko와 다른 판정이 이식 과정에서 생기면 수정한다. 원본 자체의 번역 불일치·채점 정책 개선은 기본 구현과 분리한다. 정책 우열에 대한 결론은 원본 재현과 별도 근거·검토가 필요하다.

<a id="validation-plan"></a>

## 6. 테스트 계획과 실행 기록

### 6.1. 실행 순서

| 단계 | 작업 | 완료 확인 |
| --- | --- | --- |
| 1. reference·환경 고정 | 데이터·Ko 코드·harness·Lighteval·의존성 revision 기록 | 입력·source·환경 manifest로 재구성 가능 |
| 2. 로딩·구조 확인 | key·prompt·instruction 순서·kwargs 대응·필수 필드 확인 | 누락·중복·연결 오류 상태 기록 |
| 3. 등록 task·고정 응답 회귀 | 문항 변환·scorer 연결·집계까지 원본 Ko와 비교 | 정상·실패·경계 기대값과 개별·문항 판정 일치 |
| 4. 고정 20문항 통합 | 팀이 확정한 모델로 생성·저장·양쪽 재채점 | chat template·종료·잘림·메모리·실행 오류 확인 |
| 5. 전체 split 평가 | 같은 조건으로 전체 응답 생성·저장·재채점 | 모든 key 처리, 네 지표와 불일치 목록 확보 |
| 6. 영어 task 회귀 | 공통 코드 변경 전후 고정 입력 비교 | 의도하지 않은 기존 판정 변화 없음 |

현재 완료 여부는 [분석보고서의 검증 상태](analysis.md#verification-status)를 기준으로 한다. 기존 영어·Ko 차이 분석을 새 Ko task의 동등성 결과로 대체하지 않는다.

### 6.2. 고정 응답 회귀 항목

| 항목 | 입력·기대 결과 |
| --- | --- |
| 통과·실패 대조군 | 조건 충족·위반을 함께 넣어 항상 True/False인 잘못된 구현도 실패시킴 |
| 경계값 | 길이·빈도의 N−1, N, N+1; 의도한 길이와 실제 checker counter를 함께 저장 |
| 빈 응답 | 빈 문자열·공백·줄바꿈만 있는 응답과 변환 후 빈 loose 후보 |
| 한국어 처리 | NFC/NFD, 조사·띄어쓰기, Ko 고정 선택·ending 문구 |
| loose 조합 | `*`, 첫·마지막 줄, 한 줄 응답; 서로 다른 후보에서 instruction별로 통과하는 경우 |
| instruction 대응 | 같은 ID의 반복, 원본 순서·index와 kwargs 대응, 원본·명시적 override 분리 |
| 집계 | `[[True, True, True], [False]]`의 instruction 점수 0.75, prompt 평균 0.5 |
| 오류·비결정성 | 원본 예외, 누락 필드, 반복 실행·의존성·난수·상태 차이를 숨기지 않고 기록 |

checker 단독 진단과 실제 등록 task 경로를 모두 확인한다. 합격 기준은 [분석보고서 9.2절](analysis.md)에 정의한 판정·분모 일치와 네 지표 허용 오차를 따른다. 양쪽에서 같은 예외가 발생해도 해당 입력의 채점 검증은 미완료다.

### 6.3. 고정 20문항과 재현 manifest

20문항은 통합 점검 표본이며 기존 86건·부등호 42건·Known Issue 23건의 다른 이름이 아니다. 길이·키워드·형식·복수 instruction 사례를 포함해 key 목록을 고정하고 선정 이유를 기록한다. 최종 목록과 모델·실행 환경은 팀에서 확정한다.

| 범주 | 저장할 정보 |
| --- | --- |
| 데이터·코드 | 데이터 ID·revision·config·split·key 목록, Ko 코드·harness·Lighteval commit, 변경 파일 |
| 모델·실행 환경 | 모델·tokenizer revision, dtype·양자화, CPU/GPU·메모리·backend·관련 패키지 버전 |
| 입력 프롬프트 | 원본 prompt·kwargs·instruction 순서, system prompt·few-shot·chat template·최종 렌더링 입력 |
| 생성·응답 | sampling·seed·최대 토큰·EOS·stop, 생성 token ID·raw 응답·채점 응답·길이·종료 사유 |
| 결과·재현 | instruction/prompt strict·loose, 분자·분모·네 지표, 입력·출력 hash·명령·설정·로그·예외·불일치 목록 |

소규모 실행의 메모리·시간으로 전체 평가 가능 여부를 판단한다. 모델·backend·길이 상한을 바꾸면 사유와 설정을 기록하고 응답 파일을 분리한다. 전체 평가 완료 여부는 실제 로딩한 분모와 생성·채점 오류 처리 상태로 결정한다.

<a id="decisions"></a>

## 7. 작업 분담·일정·미결정 사항

| 확정할 항목 | 현재 상태 |
| --- | --- |
| 구조 A/B·최종 파일 구성·선택 API | 제안 단계. 팀 설계 리뷰·메인테이너 선호 확인 필요 |
| metric/Pipeline·Inspect 지원 범위 | native metric 우선 제안. Inspect는 질문·확인 필요 |
| 모델·revision·backend·dtype·생성 설정 | Qwen2.5-1.5B 우선 후보이며 최종 채택 미확정 |
| 고정 20개 key·선정 기준·실행 환경 | 선정·확정 대기 |
| 등록 task 구현·회귀·20문항 실행·리뷰 담당과 기한 | 팀에서 확정 후 기입. 이 문서에서 임의 배정하지 않음 |

분석 결과·공개 범위는 [분석보고서](analysis.md), 추가 조사 표·source 목록은 [보조 자료](evidence/analysis-details.md), 기존 86건 재현 명령은 [자료 README](evidence/checker-audit/README.md)를 참조한다.
