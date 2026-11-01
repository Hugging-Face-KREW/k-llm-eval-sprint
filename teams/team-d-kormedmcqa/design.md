# 설계 문서

1. 태스크 이름, 파일 위치 (src/lighteval/tasks/tasks/<name>.py)
2. subset, 평가 split, few-shot split
3. prompt function: 원본 필드와 Doc(query, choices, gold_index) 대응표
4. 채점: 지표, 생성 길이, stop sequence, 정답 추출 규칙
5. 공식 방식과 다른 점과 그 이유
6. 테스트 계획: 어떤 입력으로 무엇을 확인할지
7. 작업 나누기: 담당과 날짜
