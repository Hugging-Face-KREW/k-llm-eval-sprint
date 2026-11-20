# C팀: IFEval-Ko

**한국어** | [English](README.en.md)

- 팀 이름: 딸기라떼
- 데이터셋: [allganize/IFEval-Ko](https://huggingface.co/datasets/allganize/IFEval-Ko), 342문항·481개 지시
- 태스크 코드: `src/lighteval/tasks/tasks/ifeval_ko/`
- 업스트림 제출 브랜치: [`team-c/ifeval-ko-upstream`](https://github.com/Hugging-Face-KREW/lighteval/tree/team-c/ifeval-ko-upstream)

## 팀원

| 이름 | GitHub | 맡은 일 |
| --- | --- | --- |
| 이준섭 | [@SubJeeLee](https://github.com/SubJeeLee) | Ko checker 이식, 업스트림 PR 게시와 검증 자료 무결성 확인 |
| 송예준 | [@joony0905](https://github.com/joony0905) | scorer 구현, 동일 응답 채점 비교, PR 검토와 재현 문서 보완 |
| 김형준 | [@kiimyjun](https://github.com/kiimyjun) | 태스크 등록, 모델 응답 생성, native Lighteval MPS 실행과 교차 검증 |

## 검증 결과와 PR별 작업

- 선정 23문항·40개 지시와 전체 342문항·481개 지시의 저장 응답을 원본 Ko, 이식 scorer, 등록 태스크의 세 경로로 채점했다. strict·loose 개별 판정과 네 지표가 모두 일치했다.
- [MPS GPU 검증](https://github.com/Hugging-Face-KREW/lighteval/pull/8#pullrequestreview-5970474156)에서는 native Lighteval로 3문항·5개 지시의 새 응답을 생성하고 채점·집계했다. 원본 Ko와 개별 판정 및 네 지표가 일치했다. 전체 342문항 결과는 저장 응답 재채점 결과다.
- 태스크 구현과 검증 자료를 업스트림 [PR #1503](https://github.com/huggingface/lighteval/pull/1503)으로 제출했다. [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8)에서는 코드 스타일을 수정하고 재현 안내와 MPS 검증 범위를 명확히 했다.
- 원본 prompt·kwargs·채점 규칙을 보존하며, 데이터셋의 Known Issues 수정은 이식 작업과 별도로 다룬다.

## 문서

- [벤치마크 분석과 판정·점수 비교](analysis.md)
- [설계와 주차별 작업 기록](design.md)
- [저장 모델 응답·MPS 검증 자료와 재현 안내](evidence/analysis-details.md#model-response-parity)
- [분석 보조 자료](evidence/analysis-details.md)
- [고정 응답 실험 안내](evidence/checker-audit/README.md)와 [156건의 실험 결과](evidence/checker-audit/results.md)
- [문항 선정 근거](evidence/sample-coverage/README.md)와 [집계표](evidence/sample-coverage/coverage.md)

## 업스트림과 팀 포크 PR

- 제안 이슈: [huggingface/lighteval #1463](https://github.com/huggingface/lighteval/issues/1463)
- 업스트림 PR: [PR #1503](https://github.com/huggingface/lighteval/pull/1503)

| 팀 포크 PR | 수행한 작업 |
| --- | --- |
| [PR #2](https://github.com/Hugging-Face-KREW/lighteval/pull/2) | 태스크 이식과 고정 응답 156건 검증 |
| [PR #5](https://github.com/Hugging-Face-KREW/lighteval/pull/5) | 선정 23문항 응답 생성과 공개 자료 |
| [PR #6](https://github.com/Hugging-Face-KREW/lighteval/pull/6) | 선정 응답의 세 경로 채점 비교 |
| [PR #7](https://github.com/Hugging-Face-KREW/lighteval/pull/7) | 전체 342문항 응답 생성과 채점 비교 |
| [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8) | 코드 스타일 수정, 재현 안내 보완과 native MPS 검증 |
