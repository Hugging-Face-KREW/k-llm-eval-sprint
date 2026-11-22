# CLIcK 현재 상태와 남은 작업

> **2026-11-22 추가:** 최신 모델 Kanana-2-3B-Instruct·Qwen3.8-27B를 FP32로 평가해 두 모델 모두 Lighteval ↔ 입력 정렬 harness 예측이 **1,995/1,995 일치**했다. BF16에서 생긴 불일치(Kanana 249, Qwen 52)는 FP32에서 모두 사라졌다. [FP32 결과](validation/click/transformers-fp32-results/SUMMARY.md) · [BF16 결과와 원인 진단](validation/click/transformers-bf16-results/SUMMARY.md). 아래 내용은 11/19 기준이다.

확인: **2026-11-19 16:13 KST**. 관련 Git 저장소 3개, 작업 폴더 4개, GitHub PR·리뷰와 팀 기록을 대조했다.
**Polyglot 평가·팀 PR 병합·업스트림 Draft 제출까지 완료됐다. 다음 작업은 Draft #1501의 비교표·검증 기록 정리와 리뷰 준비다.**

## Git 최신화

| 저장소 / 작업 폴더 | 반영한 기준 | 결과 |
| --- | --- | --- |
| k-llm-eval-sprint 현재 Orca 작업 폴더 | origin/main | e324bef → **8bcf16c**, 기존 브랜치 이름 유지 |
| k-llm-eval-sprint 로컬 main | origin/main | 6b8fa38 → **8bcf16c** |
| 개인 작업 폴더 docs/week3-basicfive | 같은 원격 브랜치 | 2253a39 → **c157d28**, #24 리뷰 수정까지 동기화 |
| 개인 기록 브랜치 people/hyeongrae-kim | 같은 원격 브랜치 | a77db65 → **aa3d3f1** |
| Lighteval 로컬 main | upstream/main | c2af9e5f → **b97a6533** |
| Lighteval 팀 원격 브랜치 | origin/team-a/click | **c8e6438b**까지 fetch, Draft #1501 HEAD와 일치 |
| lm-evaluation-harness 수정 브랜치 / main | origin/fix/click-five-options / upstream/main | **7a7b48af / d6de8164**, 이미 최신 |

세 저장소의 모든 설정된 원격에 `git fetch --all --prune --tags`를 실행하고 로컬 갱신은 fast-forward로만 수행했다.
추적 원격이 없는 과거 조사 브랜치와 평가용 고정 소스·결과 스냅샷은 보존했다.
현재 Orca 브랜치의 `ahead 23`은 최신 main을 가져온 결과이며 새 작업 커밋 23개를 만든 것이 아니다.
Lighteval 로컬 main이 origin/main보다 4커밋 앞선 것은 upstream/main을 반영했기 때문이다. 원격 포크에 push하지 않았다.

백업 후 기존 수정 2개와 미추적 파일 121개를 보존 검증했다. 사용자 PDF·원문·모델 캐시·원격 컨테이너는 변경하지 않았다.
이 상태 문서만 이번 정리에 맞춰 갱신했다. 새 커밋·push나 모델 재실행은 없다.

## 완료한 일

| 항목 | 확인된 완료 범위 |
| --- | --- |
| [분석 PR #24][analysis-pr] | 11/15 병합. 정답 A 편향 제한사항·재현 집계 추가 및 리뷰 스레드 해결 |
| [결과 PR #37][results-pr] | 11/15 병합. 평가 도구를 구분한 표·상세 보고서·JSON·CSV 반영 |
| [Lighteval 팀 코드 PR #1][code-pr] | 11/15 team-a/click에 병합 |
| Polyglot 두 모델 검증 | 이전 Lighteval/입력 정렬 harness 비교 완료. 새 harness 8조건도 각각 1,995행, 총 15,960행 PASS |
| Lighteval 팀 PR 결과 공유 | [댓글][result-comment]에서 Lighteval 결과와 harness의 기존 오류/수정 버전 **알파벳 채점** 구분 |
| [CLIcK 업스트림 Draft #1501][upstream-pr] | **@ojm6135가 11/15 제출**, HEAD c8e6438b, OPEN / Draft |

#1501의 `click.py`와 `test_click.py`는 기존 검증 SHA efb7e65의 두 파일과 Git blob이 동일하다.
새 구현이나 동일 Polyglot 실험의 재실행이 자동으로 필요한 상태는 아니다.

## 남은 작업: 우선순위

| 순서 | 작업 | 현재 근거 | 완료 기준 |
| --- | --- | --- | --- |
| 1 | **Draft #1501 결과 비교표 정리** | 본문은 전체 보기로 입력을 맞춘 harness의 동일 입력 검증 표가 중심. 원래 알파벳 채점의 기존/수정 버전은 별도 표로 제시되지 않음 | Lighteval / harness 기존 오류·알파벳 / harness #4420·알파벳 3열로 제시. 동일 입력 검증은 별도 근거로 분리 |
| 2 | **Draft 교차 검토 후 Ready 전환 준비** | 리뷰 댓글 0개, REVIEW_REQUIRED, 표시된 check 0개. 코드·테스트는 기존 검증본과 같음 | 작성자·팀이 SHA·검증 범위·입력 차이·76개 테스트/Ruff 및 필요한 CI 상태를 확인하고 Draft 해제·리뷰 요청 |
| 3 | **11/22 발표 초안·최종 보고서 구성** | 다음 세션은 리뷰 반영·발표 초안. 저장소에서 CLIcK 발표 산출물을 확인하지 못함 | 문제 발견 → 구현 → 검증 → Polyglot 결과 → 기여·한계 순서로 근거 링크와 발표 초안 작성 |
| 4 | **개인 기여 기록·팀 현황 갱신** | [개인 기록](../../people/hyeongrae-kim.md)은 1주차 한 줄. 설계·구현 보고서의 완료 기록과 STATUS는 로컬 변경 | 실제 작업의 PR·커밋 링크 추가, 최신 제출·병합 상태 반영. 재민님 기여 기록 #35와 담당·기여 구분 |
| 5 | **재현 자료 공유 준비** | #37은 보고서·집계만 포함. POLYGLOT 문서, 실행기·테스트, 이전 비교 결과 요약은 로컬 미추적 파일 | 재현 코드·설정·원문 없는 요약을 제출 단위로 정리하고 raw/log/cache는 비공개로 유지 |
| 6 | **Qwen·Kanana 검증 상태 확정** | 최신 팀 문서·Draft·재민님 공개 기록에서 Qwen2.5-7B·Kanana-8B 완료 증빙을 찾지 못함 | 담당자의 완료 증빙 또는 보류·범위 제외 상태 확인. 미확인을 미실행으로 단정하거나 네 모델 전체 완료로 표시하지 않음 |

이 순서는 다음 작업 제안이다. 이번 요청에서는 Git 최신화와 상태 정리를 수행했으며 #1501 본문·Draft 상태와 다른 PR은 변경하지 않았다.
표시된 check가 없다는 사실을 CI 실패나 통과로 단정하지 않는다.

### #1501에 제시할 결과 범위

각 값은 고정된 원본 1,995문항 기준이다. harness에는 기존 CLIcK의 **알파벳 후보 채점**만 제시한다.

| 모델 | Lighteval: 전체 보기 채점 | harness: 기존 오류·알파벳 | harness: #4420·알파벳 |
| --- | ---: | ---: | ---: |
| Polyglot-Ko 1.3B | 599/1995 (30.0251%) | 573/1995 (28.7218%) | 568/1995 (28.4712%) |
| Polyglot-Ko 12.8B | 499/1995 (25.0125%) | 477/1995 (23.9098%) | 478/1995 (23.9599%) |

Lighteval과 harness의 채점 방식이 다르므로 위 세 열에 예측·점수 일치를 주장하지 않는다.
전체 보기로 정렬한 harness의 599/499 정답은 별도의 도구 검산 결과이며 원래 harness 결과로 대체하지 않는다.
현재 Draft의 정렬 비교는 유효한 별도 검증 자료지만, 위의 원래 방법 비교와 구분해야 한다.

## 이어서 볼 외부 리뷰

| 대상 | 11/19 상태 | 남은 일 |
| --- | --- | --- |
| [harness #4420][harness-pr] | OPEN, REVIEW_REQUIRED / BLOCKED. 기존 승인 1건, CLA 성공만 표시 | 메인테이너 리뷰·필수 검사 대응. 기존 승인과 병합 가능 상태 구분 |
| [KMMLU Lighteval #1425][kmmlu-pr] | OPEN, REVIEW_REQUIRED / BLOCKED, 표시된 check 0개. HEAD 531f69c | 작성자·팀과 후속 리뷰 확인. 설계 문서의 과거 HEAD와 현재 제출 HEAD 구분 |
| [재민님 기여 기록 #35][jaemin-pr] | OPEN, 1–5주차 기록과 CLIcK Draft 제출 링크 포함 | 팀 기여 기록 교차 검토 시 함께 확인. 이번 작업에서 리뷰·병합하지 않음 |

## 일정과 범위

[프로그램 일정](../../README.md): **11/22 리뷰 반영·발표 초안 → 11/25 최종 보고서·리허설 → 11/27 결과 발표**.

Polyglot 평가와 #24·#37·팀 코드 #1 병합은 완료다.
논문 지시문 3종·보기 순환 재현, 전체 CLI 동등성, 합성 문항의 GPU 문맥 경계 실험은 현재 완료 범위 밖이다.
추가 평가 여부는 필요성이 확인된 작업으로 정하며 이번 최신화 과정에서는 실행하지 않았다.

[analysis-pr]: https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/24
[results-pr]: https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/37
[code-pr]: https://github.com/Hugging-Face-KREW/lighteval/pull/1
[upstream-pr]: https://github.com/huggingface/lighteval/pull/1501
[result-comment]: https://github.com/Hugging-Face-KREW/lighteval/pull/1#issuecomment-6874537065
[harness-pr]: https://github.com/EleutherAI/lm-evaluation-harness/pull/4420
[kmmlu-pr]: https://github.com/huggingface/lighteval/pull/1425
[jaemin-pr]: https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/35
