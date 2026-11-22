# CLIcK Polyglot: harness 버전 × 채점 방식 실험계획

2026-11-11 · 김형래 요청 · 기존 비교 이후의 추가 실험.

상태: **완료 — 8개 조합 PASS**, 각 native full 1,995행(합계 15,960행), 단일 실행 종료 코드 0.
실제 실행은 2026-11-11 **20:16:52.008364 KST** ~ 2026-11-12 **02:31:41.100115 KST**입니다.
원격 테스트 141개, 전 행 native 입력·토큰 감사, GPU random smoke, 여덟 조건의 파일럿,
두 모델의 동일 4지선다 점수·예측 일치 검증을 모두 통과했습니다.
원본·로그 79개를 로컬 ignored 경로로 회수하고 파일별 원격/로컬 SHA256을 대조했습니다.
실행 코드·원래 source·전체 설치 패키지와 기존 runner의 종료 후 불변성 검증도 PASS입니다.

[최종 한국어 비교 보고서](polyglot-matrix-results/README.md),
[전체 기계 요약](polyglot-matrix-results/summary.json),
[분야별 CSV](polyglot-matrix-results/categories.csv),
[실행 상태](polyglot-matrix-results/execution-status.json).
아래 계획과 시각별 기록은 실행 전 설계 및 과거 진행 관측이며, 최종 상태는 위 완료 기록을 따릅니다.

## 목적과 네 가지 조건

기존 harness CLIcK의 알파벳 채점 결과, #4420 수정의 영향, 전체 보기 문자열 채점의 영향을
구분합니다. Polyglot-Ko 1.3B와 12.8B 각각 아래 네 조건의 전체 1,995문항을 평가합니다.
총 8개 모델·조건 조합이며, 파일럿은 전체 평가 전에 별도로 수행합니다.

| 조건 ID | CLIcK 태스크 버전 | 채점 후보 | 프롬프트의 E 보기 |
| --- | --- | --- | --- |
| `base_letter` | 기존 오류 버전 | 원래 알파벳 후보 | 5지선다에서도 누락 |
| `pr4420_letter` | 김형래 #4420 적용본 | 원래 알파벳 후보 | 5지선다에서 표시 |
| `base_full` | 기존 오류 버전 | 알파벳 + `. ` + 보기 원문 | 5지선다에서도 누락 |
| `pr4420_full` | 김형래 #4420 적용본 | 알파벳 + `. ` + 보기 원문 | 5지선다에서 표시 |

`letter` 조건은 해당 revision의 실제 YAML·`get_context`·`get_choices`·`get_target`·
`process_docs`와 native 요청 생성·추론·채점 경로를 사용합니다.
고정 데이터 revision, 0-shot, 모델 실행 환경만 명시적으로 설정합니다.
태스크 의미를 바꾸지 않고 원본 task와 동등한 설정임을 전체 입력에 대해 확인합니다.

`full` 조건은 같은 버전의 태스크에서 후보 문자열만 변경한 별도 비교 태스크입니다.
원래 후보 `A`를 `A. 보기 원문`으로 바꾸고, 원래 target delimiter를 그대로 사용하여
최종 continuation이 ` A. 보기 원문`인지 검사합니다. 원래 알파벳 정답을 같은 후보의 인덱스로
대응시키는 변경도 명시합니다. 이는 후보 변경 후에도 동일한 정답을 가리키기 위한 처리입니다.
**프롬프트·보기 순서·후보 개수·분야 필터는 해당 버전 그대로 유지합니다.**

기존 버전의 버그는 단순한 ‘후보 4개’가 아닙니다. 프롬프트에는 A–D만 보이지만
원래 코드가 `CSAT` ID에 대해 채점 후보 E도 만듭니다. 이 동작을 임의로 고치지 않습니다.
`base_full`도 원래 후보 E가 있으면 보이지 않은 E의 전체 문자열을 채점하므로 그 한계를 기록합니다.

## 이전 실험과의 관계

[이전 결과](polyglot-results/README.md)의 Lighteval과 `click_aligned_*` 하네스는 그대로 보존합니다.
이전 하네스는 채점 후보 외에도 첫 `A:` 뒤 공백과 파일 기반 분야 분류를 Lighteval에 맞췄습니다.
따라서 새로운 `pr4420_full`을 이전 정렬한 하네스 결과로 대신하지 않고 새로 평가합니다.

최종 표에는 네 조건과 기존 Lighteval·정렬한 하네스 결과를 구분해서 싣습니다.
이전 결과를 재사용하는 두 열은 실행 날짜·입력 해시·설정 차이를 명시합니다.
논문 수치는 지시문 3종 × 보기 순환 결과이므로 계속 참고값으로만 둡니다.
이번 추가 실험은 원본 순서·지시문 한 종류를 유지합니다.

## 고정 버전과 실행 환경

| 대상 | 고정 revision |
| --- | --- |
| 기존 harness | `d6de81643928d653435c431bae19945d41d32520` |
| #4420 harness | `7a7b48afa7c294a5992008053bd1ec0042906c6d` |
| 데이터 | `d61627859645b5e6edc03fd9f835735d8226fa4e` |
| Polyglot-Ko 1.3B | `557e162cf6e944fdbae05bab2e45d066a125eacb` |
| Polyglot-Ko 12.8B | `09dfc839067bf44e7f52976eca8adbc17f04e1b0` |
| 기존 Lighteval 참고값 | `efb7e657802dd0d760473ffa9307063928ce4b41` |

여기서 ‘기존’은 위 고정 commit이며, 실행 시점의 최신 main을 뜻하지 않습니다.
두 harness commit 사이 변경은 CLIcK 태스크 디렉터리에 한정됨을 실행 전 다시 검사합니다.

- `tailab2` 호스트 GPU 3 A100X 한 장만 사용합니다.
- 기존 `tailab:0.0.1` 컨테이너와 전용 venv·캐시를 재사용합니다.
- GPU UUID: `GPU-3695dff3-f973-9d01-4829-e3b3730748b6`.
- 이미지 ID: `sha256:512b50ba045fd9834c0876c06279824db294a1318c545560279b82392c9ab2cd`.
- 컨테이너: `click-polyglot-eval-0e79adb4817a`; 전용 마운트 `/workspace`.
- 호스트 전역 Python·드라이버·패키지·이미지를 변경하지 않습니다.
- 기존과 동일한 FP32, eager attention, TF32 off, batch size 1, seed 1234,
  최대 2,048토큰, 0-shot, chat template·양자화·BOS/EOS 추가 없음.
- 주 지표는 길이 정규화를 하지 않은 native `acc`입니다. 원래 YAML의 `acc_norm`도
  별도 보조 지표로 보존하며, 전체 보기 채점의 `acc`와 섞지 않습니다.

## 데이터와 사전 검증

1. 기존 manifest의 26파일·1,995행·해시를 사용합니다. ID 중복을 제거하지 않습니다.
   데이터 revision + 파일 경로 + 행 번호로 모든 결과를 추적합니다.
2. 각 버전의 실제 native loader·분야 필터로 전체 문항을 확인합니다.
   원본 파일 분야와 native task 분야를 모두 보존하고, 정확히 한 번 평가되는지 검사합니다.
   기존 harness의 Grammar 233 / Functional 132와 원본 파일의 232 / 133 차이를 기록합니다.
3. 원래 알파벳 후보와 정답 매핑, target delimiter, 실제 요청 문자열·토큰을 전 행 검증합니다.
   `letter`는 별도 직렬화한 유사 프롬프트로 대체하지 않습니다.
4. `full`은 같은 버전의 `letter`와 프롬프트·문항집합·정답 위치가 같고 채점 문자열만 다른지 검사합니다.
   5지선다 256문항, 정답 E 49문항을 별도로 확인합니다.
5. 두 버전의 4지선다 입력이 동일하고 5지선다의 E 표시·지시문만 달라지는지 대조합니다.
   기존 `CSAT` 기준 후보 수와 실제 보기 수가 다르면 숨기거나 수정하지 말고 진단을 남깁니다.
6. 두 모델 tokenizer로 실제 context/continuation 경계와 최대 길이를 검사합니다.
   문항 생략·자동 잘림·출력 파일 덮어쓰기를 금지합니다.
7. 작은 무작위 GPTNeoX로 native 요청·loglikelihood·정답 처리와 독립 forward를 검산합니다.
   특히 5지선다 정답 E, 4/5지선다 × 지문 유무, 중복 ID, 분야가 다른 행을 포함합니다.

## 평가 순서와 중단 기준

1. 새 실행기와 의미 있는 회귀 테스트를 작성하고 전체 입력 감사·random smoke를 통과시킵니다.
2. 모델별로 기존 calibration 55문항과 겹치지 않는 validation 69문항을 재사용합니다.
   필요한 경계 사례가 빠지면 **추론 전에** validation에 추가하고 목록을 동결합니다.
3. 각 조건에서 native harness와 독립 forward를 대조합니다.
   calibration에서 `atol=max(1e-6, 최대 절대 점수 차이 × 2)`, `rtol=0`을 동결하고
   validation에서 점수와 예측 일치를 확인합니다. validation 실패 후 허용오차를 늘리지 않습니다.
4. 모델별 네 조건의 파일럿을 통과한 뒤 전체 1,995문항 × 네 조건을 순차 실행합니다.
   동일 모델을 메모리에 재사용해도 되지만 조건·버전 간 캐시와 태스크 상태가 섞이면 안 됩니다.
5. 각 조합의 결과는 새 디렉터리에 별도 저장합니다. 문항별 append와 설정·소스·입력 해시 검증을
   갖춘 재시작을 지원하며, 다른 코드·설정 결과에 이어 쓰지 않습니다.
6. 문항 누락, 중복 평가, 잘림, 틀린 gold 매핑, 비정상 점수, 파일럿 불일치 시 중단하고 보고합니다.
   서로 다른 실험 조건 사이의 예측 차이는 실패가 아니라 이번 실험의 측정 대상입니다.
   입력이 같은 4지선다의 버전 간 결과 차이는 구현·실행 상태를 조사합니다.

## 결과 분석과 산출물

모델·조건별로 아래를 저장합니다.

- 전체 micro, 문화/언어 micro, 11분야별 정확도와 macro, 정답 수/분모.
- 원본 파일 분야 기준 집계와 harness native 분야 기준 집계를 분리한 표.
- 4지선다 1,739문항 / 5지선다 256문항 / 정답 E 49문항의 정확도.
- A–E 예측 분포, E 예측 횟수, 문항별 후보 점수·예측·정오.
- `acc_norm`은 별도 열과 정규화 정의를 표시합니다.
- `pr4420_letter − base_letter`, `pr4420_full − base_full`: 수정의 효과.
- `base_full − base_letter`, `pr4420_full − pr4420_letter`: 채점 후보 변경의 효과.
- 각 쌍의 예측 변경 수, 오답→정답·정답→오답 수, 정확도 차이(%p).

완료 시 기존 Lighteval·정렬한 하네스·논문 참고값과 함께 해석합니다.
어떤 조건이 높다는 이유로 버그 수정의 타당성이나 모델의 일반적 우열을 단정하지 않습니다.

새 원격 출력 기본 경로는 `/workspace/results-matrix`이며 이전 `/workspace/results`는 보존합니다.
로컬 원본은 `.polyglot/remote/results-matrix` 아래 회수하고 해시를 대조합니다.
공유용 요약·코드·실행 기록은 `polyglot-matrix-results/`와 이 디렉터리의 별도 matrix 실행기에 둡니다.
원문·토큰·문항별 로그는 Git에 추가하지 않습니다.
실행 시작 증빙에는 시각·컨테이너·GPU·명령·로그·PID와 최초 완료 문항 수를 포함하고,
완료 증빙에는 8개 조합의 행 수·종료 코드·검증 상태·회수 해시를 포함합니다.

## 실행 담당

기존 Orca SSH worker에 이 계획의 구현·검증·전체 평가·결과 회수를 이어서 배정합니다.
현재 대화는 계획과 결과를 검토하며 worker의 시작·오류·완료 보고를 받습니다.
추가 사용자 승인을 기다리지 않고 검증을 통과하면 전체 평가로 진행합니다.

## 구현 및 로컬 검증 기록

- 실행 파일: `polyglot_matrix.py`, `polyglot_matrix_native.py`, `polyglot_matrix_core.py`,
  `polyglot_matrix_smoke.py`, `polyglot_matrix_run.sh`; 기존 실행기 코드는 변경하지 않았습니다.
- native `load_yaml(resolve_func=True)` → `ConfigurableTask` → `test_docs`/`fewshot_context`/
  `construct_requests` → `HFLM.loglikelihood` → 원래 `take_first` filter → `process_results`를 사용합니다.
- 원래 PR 소스는 그대로 두고 두 commit의 객체는 별도 `/workspace/sources/matrix-revisions`에서 읽습니다.
  YAML·함수의 원본 bytes를 버전별 외부 경로에 읽기 전용 스냅샷으로 두어 Python module cache 혼합도 피합니다.
- 데이터 전송용 override는 검증된 기존 raw 1,995행의 동일 필드·내용을 private JSON loader의 `train`으로
  매핑합니다. 원래 `process_docs`, prompt, target delimiter, metric/filter 설정을 유지합니다.
- full 조건의 변경은 후보 문자열과 원래 label→후보 index target adapter뿐입니다.
  각 결과에 `source_category`, `native_category`, 실제 `native_task` 이름을 보존합니다.
- 전 행 검증: 네 조건 모두 1,995행 한 번씩, CSAT 후보 개수 불일치 0건,
  4지선다 1,739 / 5지선다 256 / E 정답 49행; `Functional_CSAT.json#82`(0부터 시작하는 행 인덱스)의 native Grammar 이동 1건.
- 두 tokenizer의 native/joint/separate 경계 불일치 0건; 최대 길이는 base_letter 1,795,
  pr4420_letter 1,844, base_full 1,847, pr4420_full 1,896토큰입니다.
- calibration 55개와 기존 validation 69개를 보존하고 새로운 최장 입력 경계 3개를 추가하여 **55/72**를
  실제 모델 추론 전에 동결했습니다. validation 결과로 허용오차를 바꾸지 않습니다.
- 로컬 새 테스트 21 + 기존 120 = 141 PASS; 최종 provenance metadata 변경 뒤 관련 새 테스트 21개 재검증 PASS.
  random GPTNeoX CPU smoke는 조건별 8문항, native/독립 점수 차이 0, 예측·acc·acc_norm 일치입니다.
- 로컬 검증은 Python 3.14.8 / torch 2.14.1 CPU / transformers 5.20.0입니다. 실제 원격 고정 환경의
  검사·새 GPU smoke·파일럿은 별도로 수행하며, CPU smoke를 실제 Polyglot 결과로 해석하지 않습니다.
- 재시작은 source/code/전체 설치 패키지/model/data/config hash를 확인하고, 부분 JSON·중복·비유한 점수를 거부합니다.
  한 모델의 네 파일럿이 모두 PASS한 뒤 네 full을 수행하며, 같은 출력 디렉터리의 동시 전체 실행은 file lock으로 막습니다.
- [새 결과 상태 문서](polyglot-matrix-results/README.md)에 실제 시작 및 최종 결과를 갱신합니다.

원격 실행 명령(인증·GPU 상태 및 원격 테스트 확인 완료):

```bash
/workspace/bin/native-env bash /workspace/code/teams/team-a-click/validation/click/polyglot_matrix_run.sh
```

원격 로그 경로는 `/workspace/logs/matrix-task_3ce01f897c7f/`이며, 실제 GPU 추론 시작·완료 및 각 파일럿/full 판정은 해당 로그와 최종 기계 요약에 보존했습니다.
입력 감사·smoke·파일럿·전체 평가는 하나의 작업에서 순차 실행됐습니다.

## 실행 중 관측 기록 (과거 상태)

1.3B 네 조건 full 1,995행과 동일 4지선다 revision 간 점수·예측 일치 검증이 PASS했습니다.
정답 수: base_letter 573, pr4420_letter 568, base_full 596, pr4420_full 595.
**12.8B 실제 시작: 20:58:45.704184 KST, base_letter/native pilot 최초 1/127행 완료, PID 6727.**
12.8B 파일럿과 네 전체 평가가 진행 중입니다.

21:49:46 KST: 12.8B 네 조건의 파일럿도 모두 PASS(native/독립 각127, calibration55/validation72, 최대오차0, atol1e-6/rtol0). base_letter full 59/1,995행을 완료한 상태이며 나머지 세 full을 이어서 수행합니다.

22:09:25 KST 마지막 정상 관측: 12.8B base_letter full 358/1,995, 실행 RUNNING. 이후 SSH network unreachable/ControlMaster 소멸로 모니터가 종료255였으며, 단일 재확인에서는 서버 연결 후 인증 거절(Permission denied)이 확인되었습니다. 원격 평가에 종료 신호는 보내지 않았고 현재 원격 상태는 재로그인 후 확인해야 합니다. 코디네이터에 기존 전용 SSH 터미널의 직접 로그인을 요청하며 완료로 판정하지 않습니다.

2026-11-12 00:28:36 KST: 로그인된 전용 SSH 터미널에서 기존 작업 생존을 확인했습니다. supervisor5522/runner5528/model6727 모두 같은 명령으로 실행 중이고 두 single-run lock은 HELD입니다. 6/8 full 완료: 12.8B base_letter477/1995, pr4420_letter478/1995; base_full362/1995 진행 중. 사용자의 일반 ssh 로그인은 공유 ControlPath를 만들지 않아 비대화형 조회·회수 연결은 아직 복구가 필요합니다. 기존 평가 재시작이나 중단은 하지 않았습니다.

2026-11-12 00:50:41 KST: 공유 ControlPath가 복구되어 비대화형 snapshot exit0을 확인했습니다. 기존 supervisor5522/runner5528/model6727과 두 lock HELD를 재확인했고 평가 재시작은 없었습니다. 6/8 완료, 12.8B base_full1,218/1,995행에서 자동 모니터링을 재개했습니다.

2026-11-12 01:18:44.923760 KST: 12.8B base_full 1,995행 COMPLETE, primary488/1995 및 acc_norm633/1995. 7/8 full을 완료했으며 마지막 pr4420_full을 동일 PID6727로 이어서 수행 중입니다.

## 최종 완료 증빙

- 종료: 2026-11-12 02:31:41.100115 KST, supervisor PID 5522 / runner PID 5528, exit 0.
- 최초 실제 추론: 1.3B/base_letter/native pilot 1행, 2026-11-11 20:18:27.701316 KST, PID 5899;
  12.8B는 20:58:45.704184 KST, PID 6727. 관찰용 SSH 단절 동안에도 동일 원격 작업이 계속 실행됐으며 재시작은 없었습니다.
- 조건 순서 base_letter / pr4420_letter / base_full / pr4420_full의 primary 정답 수:
  1.3B **573 / 568 / 596 / 595**, 12.8B **477 / 478 / 488 / 487**, 분모는 모두 1,995.
- 여덟 파일럿 모두 native127 + independent127, calibration55/validation72 PASS,
  calibration 최대 절대오차 0, 동결 atol1e-6/rtol0. 두 모델 모두 동일 4지선다 점수·예측 일치 PASS.
- 실행 code SHA256: `25889d47475a56f5e7d3852f364839fefe342359e32dd042c792905b67000e6b`.
- 기존 runner SHA256: `0824359c8bbe2f9943bf92d5059990a4b92c8d0e58451b1f174eccc8aef99f57`, 변경 없음.
- 결과 archive SHA256: `ca6d9ce2af8aa096b4bf97411e3e7a3d05c838feb4cf8ffb2e64a38c56fa6782`, 79개 파일 대조 PASS.
- GPU3 종료 후 10MiB / 0%이며 평가 프로세스는 종료됐고 전용 컨테이너의 sleep infinity만 남았습니다.
- 원본 회수 경로 `.polyglot/remote/results-matrix`, 상세 실행 증빙 `.polyglot/remote/matrix-evaluation-report.json`.
- Native Python API 평가이며 전체 CLI 동등성이나 논문 재현을 주장하지 않습니다. 남은 실행 작업은 없습니다.
