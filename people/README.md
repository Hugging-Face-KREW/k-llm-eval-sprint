# 첫 PR: 나를 소개하는 파일 올리기

이 폴더의 파일은 8주 동안 개인 기여 기록으로 씁니다.

1. 저장소를 받고 브랜치를 만듭니다.

   ```bash
   git clone https://github.com/Hugging-Face-KREW/k-llm-eval-sprint.git
   cd k-llm-eval-sprint
   git switch -c people/<github-id>
   ```

2. `people/_template.md`를 복사해 `people/<github-id>.md`를 만들고 채웁니다.
3. 우리 팀 폴더의 `README.md` 팀원 목록에 내 이름과 GitHub ID를 한 줄 추가합니다.
4. 커밋하고 올립니다.

   ```bash
   git add people/<github-id>.md teams/
   git commit -m "Add <github-id> profile"
   git push -u origin people/<github-id>
   ```

5. GitHub에서 PR을 열고, 같은 팀원 한 명에게 리뷰를 요청합니다. 승인을 받으면 병합합니다.
