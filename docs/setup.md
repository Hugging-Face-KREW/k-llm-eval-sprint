# 개발 환경 준비

아래 순서는 멘토가 2026-10-10에 macOS(Apple Silicon, Python 3.11)에서 처음부터 그대로 실행해 확인했습니다.
Windows는 WSL(Ubuntu)에서 같은 명령을 쓰면 됩니다. WSL과 Colab은 아직 멘토가 직접 확인하지 못했으니, 막히면 바로 알려 주세요.

## 0. 미리 확인

| 항목 | 확인 방법 | 기준 |
|---|---|---|
| Python | `python3 --version` | 3.10 이상 |
| Git | `git --version` | 설치되어 있으면 됨 |
| 디스크 | | 2GB 이상 여유 (가상환경만 약 1.6GB) |
| GitHub 초대 | github.com/notifications | 두 저장소 모두 수락 |

## 1. Git LFS 설치 (처음 한 번)

Lighteval 저장소는 `.json`, `.parquet` 파일을 Git LFS로 관리합니다. Git LFS가 없거나 설정이 꼬여 있으면 clone이 실패할 수 있습니다.

```bash
# Mac
brew install git-lfs
# WSL(Ubuntu)
sudo apt install git-lfs

git lfs install
```

## 2. 포크 받기

```bash
git clone https://github.com/Hugging-Face-KREW/lighteval.git
cd lighteval
git remote add upstream https://github.com/huggingface/lighteval.git
```

## 3. 가상환경과 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

pip install -e ".[dev]"
pip install "huggingface_hub<2"
pre-commit install
```

- 설치는 네트워크에 따라 1~10분 걸립니다. (확인 당시 81초)
- `huggingface_hub<2`는 꼭 넣어 주세요. 2026-10 기준 최신 `huggingface_hub`(2.x)에서 Lighteval 실행이 `HfApi.list_models() got an unexpected keyword argument 'model_name'` 오류로 멈춥니다.

## 4. 실행 확인

작은 모델(SmolLM2-135M)로 기존 태스크 `arc:easy`를 10문항만 돌립니다. GPU 없이 노트북에서 돌아갑니다.

```bash
lighteval accelerate \
  "model_name=HuggingFaceTB/SmolLM2-135M-Instruct" \
  "arc:easy|0" \
  --max-samples 10 \
  --output-dir ./results \
  --save-details
```

마지막에 이런 표가 나오면 성공입니다. (처음 실행은 모델과 데이터 다운로드 때문에 1~2분)

```
|   Task   |Version|Metric|Value|   |Stderr|
|----------|-------|------|----:|---|-----:|
|all       |       |acc   |  0.4|±  |0.1633|
|arc:easy:0|       |acc   |  0.4|±  |0.1633|
```

결과 파일은 `results/` 아래에 생깁니다.
- `results/results/.../results_*.json`: 전체 점수
- `results/details/.../details_*.parquet`: 문항별 질문, 선택지, 정답, 모델 점수

## 약관 동의가 필요한 데이터셋

Ko-MuSR, KMMLU-Redux처럼 약관 동의가 필요한 데이터셋은 Hugging Face에서 동의한 뒤 토큰으로 로그인합니다.

```bash
hf auth login
```

## 막혔을 때

오픈채팅방에 `[팀] 무엇을 하다 막혔는지`, 입력한 명령, 오류 마지막 줄, OS를 적고 화면 캡처를 함께 올려 주세요.
