# 김형래 (@hyeongrae-kim)

- 팀: 베이직파이브
- 학과 / 학년: 컴퓨터학부 / 4학년
- 요즘 자주 쓰는 AI 도구: Codex
- 8주 뒤에 해 보고 싶은 것: 오픈소스 프로젝트 PR Merge

## 기여 기록

매주 내가 한 일을 링크와 함께 한 줄씩 적습니다. 커밋, PR, 리뷰, 이슈 댓글 모두 좋습니다.

| 주차 | 한 일 | 링크 |
| ---- | ----- | ---- |
| 1    | 자기소개 파일 추가와 A팀 팀원 목록 작성. KMMLU 데이터 구성·공식 평가 방식을 분석해 기본 채점 방식(5-shot Direct) 결정 근거를 정리하고, 기존 업스트림 KMMLU PR과의 중복을 확인해 CLIcK를 대안으로 제시 | [PR #13](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/13) · [PR #20](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/20) |
| 2    | CLIcK 분석 보고서와 Lighteval 제안 이슈 초안 작성. lm-evaluation-harness CLIcK의 5지선다 E 보기 누락 버그를 찾아 Qwen3-14B로 영향 측정(정답 E 49문항 0% → 91.8%) 후 버그 리포트와 수정 PR 제출. KMMLU 기존 확률 방식 45과목·35,030문항을 lm-eval과 GPU 전체 비교(예측 불일치 0) | [PR #24](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/24) · [harness #4418](https://github.com/EleutherAI/lm-evaluation-harness/issues/4418) · [harness #4420](https://github.com/EleutherAI/lm-evaluation-harness/pull/4420) · [KMMLU GPU 비교 결과](https://github.com/CY-HYUN/kmmlu-lighteval/blob/b67534946e9c5fc0948c201258d66a7e7336e9e5/README.md#all-45-subjects-on-a-gpu) |
| 5    | Polyglot-Ko 1.3B·12.8B로 Lighteval과 입력을 맞춘 harness의 1,995문항 예측 일치 확인, harness 기존/#4420 × 알파벳/전체 보기 8개 조건 평가와 결과 보고서 작성, 팀 코드 PR에 결과 공유, 분석 PR 리뷰 반영(정답 A 편향 제한사항) | [PR #37](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/37) · [lighteval PR #1 댓글](https://github.com/Hugging-Face-KREW/lighteval/pull/1#issuecomment-6874537065) · [c157d28](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/commit/c157d28) |
| 6    | Polyglot 재현 코드 공개, harness #4420 리뷰 요청, Kanana-2-3B·Qwen3.8-27B BF16 평가와 불일치 원인 진단, FP32에서 두 모델 모두 1,995문항 예측 일치 확인, 결과를 업스트림 CLIcK PR 비교표에 제공 | [PR #47](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/47) · [harness #4420 댓글](https://github.com/EleutherAI/lm-evaluation-harness/pull/4420#issuecomment-7010018938) · [PR #51](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/51) · [PR #52](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/52) · [lighteval #1501](https://github.com/huggingface/lighteval/pull/1501) |
