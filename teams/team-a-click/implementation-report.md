# CLIcK 데이터와 프롬프트 구현 보고서

현재 PR·리뷰 상태와 남은 작업은 [2026-11-13 상태 정리](STATUS.md)를 참고하세요.
아래 날짜별 기록은 각 작업을 수행했을 당시의 범위와 결과입니다.

2026-11-12 추가 실험 완료: 기존 harness / #4420 × 알파벳 / 전체 보기 채점 네 조건을
Polyglot 1.3B·12.8B로 평가한 8개 조합이 모두 PASS했습니다(각 1,995행, 단일 실행 exit 0).
[최종 비교 보고서](validation/click/polyglot-matrix-results/README.md)와
[실험계획·실행 증빙](validation/click/POLYGLOT_MATRIX.md)에 원격 테스트 141개,
파일럿·동일 4지선다 검증 및 원본 79개 파일 SHA 회수 결과를 기록했습니다.
아래 처음 수행한 정렬 비교 결과는 보존하며, 새 실험은 native Python API 경로입니다.

2026-11-11 후속 작업: 김형래의 Polyglot-Ko 1.3B·12.8B 비교 실행기를 추가했습니다.
Lighteval·정렬한 하네스·독립 forward의 파일럿 검산, 전체 평가, 재시작과 결과 보고를 지원합니다.
단위 테스트 120개, 전체 1,995문항의 native 입력 일치, 작은 무작위 모델의 세 경로 검산을 통과했습니다.
`tailab2`의 GPU 3번과 `tailab:0.0.1` 전용 컨테이너에서 두 모델의 파일럿·전체 평가를 완료했습니다.
1.3B는 599/1,995(30.03%), 12.8B는 499/1,995(25.01%)이며,
각 모델의 Lighteval·하네스 예측은 전 문항에서 일치하고 후보 점수 차이도 사전 허용오차 이내입니다.
[최종 결과](validation/click/polyglot-results/README.md)와
[재실행 방법](validation/click/POLYGLOT.md)을 정리했습니다. 논문과 조건이 다른 참고 비교입니다.

2026-11-06 · @GeonRyoung · `docs/week5-basicfive`

[4주차 설계](design.md) §7의 담당 작업 두 개를 구현하고 검증했습니다.

| 담당 작업 | 완료한 내용 | 검증 |
| --- | --- | --- |
| 분야별 파일 목록·데이터 검사·추적 연결 | 11개 분야의 원본 26파일 고정, 파일 해시·1,995행 추적 목록, HF 로더와 Lighteval 저장 로그 연결 | D01–D03 통과, 추적 실패 테스트 20개 통과 |
| Prompt function·입력 단위 테스트 | `build_click_payload`, `click_prompt`, 4·5지선다 전체 후보, 원문 보존과 입력 오류 처리 | U01–U07에 해당하는 테스트 70개 통과 |

Lighteval 커밋은 아래처럼 구분합니다.

| 커밋 | 의미 |
| --- | --- |
| `c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14` | 팀 포크 베이스(`team-a/kmmlu`). 팀 공동 승인이나 업스트림 제출 기준 확정을 뜻하지 않음 |
| `be429ad021b199f5f0fe167e961a05180397d6af` | 이전 v2 구현(`click_paper_example_v2`) |
| `efb7e657802dd0d760473ffa9307063928ce4b41` | 현재 v3 구현(`click_harness_layout_v3`). 현재 `results.json`을 생성한 실행 커밋 |

실행 방법·검증 범위·주의할 버전 차이는 [검증 README](validation/click/README.md)에 있습니다.
[원본 목록](validation/click/manifest.json)과 [실제 검사 결과](validation/click/results.json)에는
원문 대신 경로·ID·해시·통계만 저장했습니다.

원본 고유 ID는 1,987개지만 중복 ID 행을 제거하지 않아 평가 대상 1,995행을 유지합니다.
`Functional_CSAT.json#82`도 ID 이름에 관계없이 원본 파일 기준으로 Functional에 남습니다.
Doc의 추적 해시가 실제 Parquet 저장·재읽기 후에도 유지되는 것을 전 행에서 확인했습니다.

태스크 등록(`e2c506f`)과 지표·집계·등록 테스트(`7bb0dcd`)는 이후
Lighteval에 추가됐습니다. 2026-11-06의 기존 `results.json`에는 실제 모델 검증이 포함되지 않습니다.
2026-11-11 Polyglot native API 검산 결과는 위의 별도 최종 보고서를 참고하세요.
업스트림 병합 완료를 뜻하지 않습니다.

AI 도구로 구현·테스트·문서 초안을 작성했습니다. 팀 제출 전 담당자의 코드 이해와 교차 검토가 필요합니다.



2026-11-06 프롬프트 수정: 논문 §4의 지문 유무별 지시문과 인쇄 예시의 필드·보기 표시를
적용했습니다. 스냅샷과 지문 유무 × 보기 수 검사를 갱신했습니다.
프롬프트 버전은 `click_paper_example_v2`이며, 기존 v1 결과와 구분합니다.
채점 후보는 유지했고 모델 정확도 변화는 아직 측정하지 않았습니다.

2026-11-08 프롬프트 수정: 비교 대상인 lm-evaluation-harness와 입력을 맞추기 위해
레이아웃과 한국어 필드 이름을 하네스 기준으로 바꿨습니다(Lighteval `efb7e65`).
프롬프트 버전은 `click_harness_layout_v3`이며, v2 결과와 구분합니다.
하네스와 남은 차이(라벨 뒤 공백, 5지선다의 A–E 지시문과 E 보기, 채점 후보)는
[설계 §3.2·§5.2](design.md)에 정리했습니다. 채점 후보·정답 인덱스·원본 행 해시는
바뀌지 않았고 모델 정확도 변화는 아직 측정하지 않았습니다.
