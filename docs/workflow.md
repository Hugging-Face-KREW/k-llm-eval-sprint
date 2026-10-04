# 작업 흐름

## 저장소 두 개

| 저장소 | 쓰는 곳 |
|---|---|
| [Hugging-Face-KREW/k-llm-eval-sprint](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint) | 문서. 분석 보고서, 설계 문서, 개인 기여 기록 |
| [Hugging-Face-KREW/lighteval](https://github.com/Hugging-Face-KREW/lighteval) | 코드. 평가 태스크 구현 |

포크 저장소의 `main`은 원본 [huggingface/lighteval](https://github.com/huggingface/lighteval)과 똑같이 유지합니다. `main`에는 아무도 직접 커밋하지 않습니다.

## 브랜치

| 브랜치 | 용도 | 누가 |
|---|---|---|
| `main` | 원본과 같은 상태 | 멘토만 동기화 |
| `team-a/kmmlu` | A팀 공동 작업 | 팀원 PR로만 병합 |
| `team-b/hrm8k` | B팀 공동 작업 | 〃 |
| `team-c/ifeval-ko` | C팀 공동 작업 | 〃 |
| `team-d/kormedmcqa` | D팀 공동 작업 | 〃 |
| `team-a/<github-id>-<작업>` | 개인 작업 | 본인 |

팀 브랜치에는 직접 push할 수 없고, PR에서 한 명 이상 승인을 받아야 병합됩니다.

## 한 번의 작업 순서

```bash
# 1. 포크를 받는다 (처음 한 번)
git clone https://github.com/Hugging-Face-KREW/lighteval.git
cd lighteval
git remote add upstream https://github.com/huggingface/lighteval.git

# 2. 팀 브랜치 최신 상태에서 개인 브랜치를 만든다
git fetch origin
git switch -c team-a/ojm6135-prompt origin/team-a/kmmlu

# 3. 작업하고 커밋한다
git add -p
git commit -m "Add prompt function for KMMLU"

# 4. 올리고, GitHub에서 팀 브랜치로 PR을 연다
git push -u origin team-a/ojm6135-prompt
```

PR을 열 때 **base가 팀 브랜치인지** 꼭 확인합니다. 기본값이 `main`으로 잡혀 있을 수 있습니다.

## 커밋과 PR

- 커밋 메시지는 영어로, 무엇을 했는지 한 줄로 씁니다. 예: `Add KMMLU task config`
- 올리기 전에 스타일 검사를 돌립니다.

  ```bash
  pre-commit run --all-files
  ```

- 업스트림 PR에는 팀원 전원을 공동 작성자로 넣습니다. 커밋 메시지 끝에 한 줄씩 추가합니다.

  ```
  Co-authored-by: 이름 <github-id+숫자@users.noreply.github.com>
  ```

  noreply 주소는 GitHub 설정의 Emails 메뉴에서 확인할 수 있습니다.

## 업스트림으로 PR 올리기

팀 브랜치가 완성되면 멘토와 함께 `huggingface/lighteval`의 `main`으로 PR을 엽니다.
PR 설명 틀은 [templates/upstream-pr.md](../templates/upstream-pr.md)를 씁니다.
