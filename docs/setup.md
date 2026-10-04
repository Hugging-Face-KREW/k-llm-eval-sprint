# 개발 환경 준비

첫 온라인 세션에서 화면을 공유하며 같이 설치합니다. 미리 해 두면 좋은 것만 적었습니다.

## 세션 전에 확인할 것

| 항목 | 확인 방법 | 기준 |
|---|---|---|
| Python | 터미널에서 `python3 --version` | 3.10 이상 |
| Git | 터미널에서 `git --version` | 설치되어 있으면 됨 |
| GitHub 계정 | 저장소 초대 수락 | 두 저장소 모두 |
| Hugging Face 계정 | 이메일 인증 | 인증 완료 |

Windows를 쓴다면 WSL(Ubuntu)에서 작업하는 걸 권합니다. 설정은 첫 세션에서 같이 봅니다.

## 세션에서 같이 할 설치

```bash
# 포크 받기
git clone https://github.com/Hugging-Face-KREW/lighteval.git
cd lighteval
git remote add upstream https://github.com/huggingface/lighteval.git

# 가상환경 만들기
python3 -m venv .venv
source .venv/bin/activate

# 개발용 설치 (코드 검사와 테스트 도구 포함)
pip install -e ".[dev]"
pre-commit install
```

약관 동의가 필요한 데이터셋(Ko-MuSR, KMMLU-Redux 등)을 쓰는 팀은 Hugging Face 토큰으로 로그인합니다.

```bash
hf auth login
```

기존 평가를 돌려 보는 명령은 첫 세션에서 같이 실행하고 이 문서에 추가합니다.

## 막혔을 때

오픈채팅방에 `[팀] 무엇을 하다 막혔는지`, 입력한 명령, 오류 마지막 줄, OS를 적고 화면 캡처를 함께 올려 주세요.
