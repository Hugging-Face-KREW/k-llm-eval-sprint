# A팀: KMMLU

- 팀 이름: 베이직파이브
- 데이터셋: [HAERAE-HUB/KMMLU](https://huggingface.co/datasets/HAERAE-HUB/KMMLU)
- 참고할 Lighteval 코드: src/lighteval/tasks/multilingual/tasks/cmmlu.py, turkish_mmlu.py
- 작업 브랜치: [`team-a/kmmlu`](https://github.com/Hugging-Face-KREW/lighteval/tree/team-a/kmmlu)

## 팀원

첫 PR에서 자기 이름을 한 줄씩 추가합니다.

| 이름 | GitHub | 맡은 일 |
| --- | --- | --- |
| 김형래 | [hyeongrae-kim](https://github.com/hyeongrae-kim) | |
| 박건령 | GeonRyoung |     |
| 오재민 | ojm6135 | |

## 이번 주 팀 과제 (10/17 토까지)

결과물은 팀 PR 1건입니다. 누가 PR을 올릴지는 팀에서 정합니다.

1. [analysis.md](analysis.md)의 9개 항목을 모두 채웁니다. 10/10에 공유한 팀 글을 옮기면 대부분 채워집니다.
2. 5번 공식 평가 방식에는 프롬프트, few-shot, 정답 추출, 정규화를 각각 어디서 확인했는지 링크와 함께 적습니다.
3. 아래 팀 결정의 결론과 근거를 해당 번호 항목에 적습니다.
4. 같은 PR에 `issue-draft.md`를 추가합니다. [templates/upstream-issue.md](../../templates/upstream-issue.md)를 복사해 영어로 채웁니다. 업스트림 게시는 10/18 세션에서 함께 다듬은 뒤에 합니다.
5. 팀원 모두 읽고, 1명 이상 승인하면 머지합니다.

| 이번 주 팀 결정 | 적을 곳 |
|---|---|
| 기본 채점을 선택지 확률 방식과 생성 방식 중 무엇으로 할지. 근거는 논문의 5-shot Direct 설정과 lm-evaluation-harness의 두 구현(kmmlu, kmmlu_direct) | analysis.md 5번 |

## 문서

- [벤치마크 분석 보고서](analysis.md) (2주차)
- [설계 문서](design.md) (4주차)

## 업스트림 링크

- 제안 이슈:
- PR:
