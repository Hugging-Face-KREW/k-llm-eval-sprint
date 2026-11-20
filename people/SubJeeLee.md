# 이준섭 (@SubJeeLee)

- 팀: C팀 딸기라떼 (IFEval-Ko)
- 학과 / 학년: 컴퓨터학부 글로벌 SW융합전공 / 4학년
- 요즘 자주 쓰는 AI 도구: ChatGPT, Codex
- 8주 뒤에 해 보고 싶은 것: IFEval-Ko의 평가 방식을 이해하고 Lighteval에 동일하게 구현하는 데 기여하고 싶습니다. 브랜치 생성부터 PR, 팀 리뷰, 업스트림 리뷰 반영까지 오픈소스 협업 과정을 직접 경험하고, 제가 작성한 변경의 이유와 검증 방법을 설명할 수 있는 기여자가 되고 싶습니다.

## 기여 기록

작업과 검증에는 AI 도구를 활용했습니다. 팀에서 함께 진행한 검증 결과와 제가 맡은 작업을 구분해 기록했습니다.

| 주차 | 한 일 | 링크 |
|---|---|---|
| 1 | IFEval-Ko가 측정하는 지시 이행 능력과 채점 방식을 분석하고 글로 정리 | [분석 글](https://velog.io/@subjeelee/오픈소스-기여를-준비하며-IFEval-Ko-알아보기) |
| 1 | 자기소개 파일과 C팀 팀원 정보 추가 | [운영 저장소 PR #19](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/19) |
| 2 | 팀 벤치마크 분석 보고서를 검토하고 지시문과 검사 조건의 불일치 사례 등 확인한 내용 정리 | [팀 분석 PR #18](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/18) |
| 3 | Lighteval의 평가 태스크 요청을 위한 이슈 초안을 작성하고 팀의 분석·설계 내용 검토 | [팀 분석 PR #18](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/18) |
| 4 | 한국어 채점 방식을 유지하기 위해 원본 Ko checker·registry·utility를 Lighteval 패키지로 이식하고 출처와 라이선스 헤더, import 경로 정리 | [checker 이식 커밋](https://github.com/Hugging-Face-KREW/lighteval/commit/f9b8059f1952db78c5adbedf780ee889b364973a) · [팀 코드 PR #2](https://github.com/Hugging-Face-KREW/lighteval/pull/2) |
| 4 | 팀의 분석을 바탕으로 Ko 전용 채점 구조와 검증 계획을 담아 Lighteval 업스트림 이슈 게시 | [업스트림 이슈 #1463](https://github.com/huggingface/lighteval/issues/1463) |
| 5 | 저장된 23문항 응답의 원본 Ko·이식 scorer·등록 태스크 판정을 대조한 검증 내용을 리뷰하고, NLTK 자료 사전 설치 안내를 보완 | [PR #6 리뷰](https://github.com/Hugging-Face-KREW/lighteval/pull/6#pullrequestreview-5892533919) · [README 수정 커밋](https://github.com/Hugging-Face-KREW/lighteval/commit/9731595bb95455aa442403516114a44a39d740bd) |
| 5 | 팀이 생성한 전체 342문항 응답과 채점 자료의 무결성 및 원본 평가기와의 판정 비교 결과 검토 | [전체 검증 자료](https://github.com/Hugging-Face-KREW/lighteval/pull/7) · [독립 재실행 기록](https://github.com/Hugging-Face-KREW/lighteval/pull/7#issuecomment-6877811099) |
| 6 | IFEval-Ko 구현과 비교 결과를 담은 업스트림 Draft PR을 게시하고 이슈 및 재현 자료 연결 | [업스트림 PR #1503](https://github.com/huggingface/lighteval/pull/1503) |
| 6 | 팀의 환경 안내·코드 스타일·MPS 검증 자료 변경을 검토하고 팀 포크 PR 승인 | [PR #8 리뷰](https://github.com/Hugging-Face-KREW/lighteval/pull/8#pullrequestreview-5974636880) |
| 6 | 팀 분석 문서와 재현 자료의 수치·링크·체크섬을 검토하고 리뷰 | [운영 저장소 PR #45 리뷰](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/45#pullrequestreview-5988226336) |
