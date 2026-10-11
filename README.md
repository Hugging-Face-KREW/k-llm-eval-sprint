# K-LLM Eval Sprint

2026 오픈소스 AI 컨트리뷰터 챌린지(경북대학교) 멘토링 저장소입니다.
네 팀이 한국어 LLM 벤치마크를 하나씩 맡아 Hugging Face [Lighteval](https://github.com/huggingface/lighteval)에 평가 태스크로 구현하고, 업스트림에 이슈와 PR을 올립니다.

이 저장소는 **운영용**입니다. 일정, 팀 문서, 개인 기여 기록, 템플릿이 여기에 있습니다.
실제 코드는 포크 저장소 [Hugging-Face-KREW/lighteval](https://github.com/Hugging-Face-KREW/lighteval)에서 작업합니다.

## 팀

| 팀 | 벤치마크 | 데이터셋 | 팀 폴더 |
|---|---|---|---|
| A 베이직파이브 | KMMLU | [HAERAE-HUB/KMMLU](https://huggingface.co/datasets/HAERAE-HUB/KMMLU) | [team-a-kmmlu](teams/team-a-kmmlu) |
| B 최재희야팀 | HRM8K | [HAERAE-HUB/HRM8K](https://huggingface.co/datasets/HAERAE-HUB/HRM8K) | [team-b-hrm8k](teams/team-b-hrm8k) |
| C 딸기라떼 | IFEval-Ko | [allganize/IFEval-Ko](https://huggingface.co/datasets/allganize/IFEval-Ko) | [team-c-ifeval-ko](teams/team-c-ifeval-ko) |
| D STP즈 | KorMedMCQA, Ko-MuSR | [sean0042/KorMedMCQA](https://huggingface.co/datasets/sean0042/KorMedMCQA) | [team-d-kormedmcqa](teams/team-d-kormedmcqa) |

팀원 명단은 각 팀 폴더의 README에 있습니다. 첫 PR에서 자기 이름을 직접 넣습니다.

멘토: 김하림 [@harheem](https://github.com/harheem) (10월 진행), 유용상 [@4n3mone](https://github.com/4n3mone) (11월 진행)

## 일정

정기 세션은 **매주 일요일 20:00–22:00**, Google Meet에서 진행합니다. 중간고사 주간(10/21–10/27)에는 세션이 없고, 커뮤니티데이 직전에 발표 리허설을 **11/25(수) 20:00–22:00**에 한 번 더 합니다.

| 주차 | 세션 | 하는 일 | 끝낼 것 |
|---|---|---|---|
| 1 | 10/11 (일) | 환경 설정 | Lighteval 설치와 실행, 첫 PR |
| 2 | 10/18 (일) | 벤치마크 분석 | 분석 보고서, 업스트림 제안 이슈 |
| 3 | 없음 | 중간고사 | 주간 기록만 |
| 4 | 11/1 (일) | 설계 리뷰 | 설계 문서, 중간보고서 |
| 5 | 11/8 (일) | 구현 | 처음부터 끝까지 실행되는 구현 |
| 6 | 11/15 (일) | 검증, PR 제출 | 결과 재현, 업스트림 PR |
| 7 | 11/22 (일) | 리뷰 반영 | 리뷰 응답, 발표 초안 |
| 8 | 11/25 (수) | 발표 리허설 | 최종 보고서, 발표자료 |
| 8 | 11/27 (금) | 커뮤니티데이 (오프라인) | 결과 발표 |

## 처음 할 일

1. 이 저장소와 포크 저장소 초대를 수락합니다. (GitHub 알림 또는 메일)
2. [docs/setup.md](docs/setup.md)를 보고 개발 환경을 준비합니다.
3. 첫 PR을 올립니다. [people/README.md](people/README.md)를 따라 하면 됩니다.

## 작업 흐름

코드는 포크 저장소의 팀 브랜치에서 작업하고, 팀 안에서 리뷰한 뒤 업스트림으로 PR을 올립니다.
자세한 규칙은 [docs/workflow.md](docs/workflow.md)에 있습니다.

```
개인 브랜치  →  팀 브랜치로 PR (팀원, 멘토 리뷰)  →  업스트림 huggingface/lighteval로 PR
```

## 무엇을 해내면 성공일까

| 단계 | 내용 |
|---|---|
| 1. 조사 | 공식 평가 방식을 알고 구현 계획을 세운다 |
| 2. 구현과 재현 | 코드가 돌아가고 논문 수치와 비교한다 |
| 3. 기여 | 이슈와 PR을 올리고 리뷰에 답한다 |
| 4. 머지 | 메인테이너가 받아 준다 |

모두의 목표는 3단계입니다. 머지는 메인테이너가 정하고, 프로그램이 끝난 뒤에 될 수도 있습니다.

## 질문과 약속

- 기술 질문은 오픈채팅방에 올립니다. 질문 앞에 `[A팀]`처럼 팀 이름을 붙여 주세요.
- 15분 막히면 팀에게, 1시간 막히면 오픈채팅방에 올립니다.
- 오류는 화면 캡처와 오류 마지막 줄을 같이 올립니다.
- AI 도구 사용 원칙은 [docs/ai-tools.md](docs/ai-tools.md)를 봐 주세요.
