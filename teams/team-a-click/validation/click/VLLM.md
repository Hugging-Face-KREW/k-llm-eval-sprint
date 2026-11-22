# CLIcK Qwen3.8 · Kanana2 실행 기록

Qwen3.8-27B·Kanana-2-3B-Instruct vLLM 평가 계획(개인 작업 메모, 저장소 미포함)의 후속 실행이다. 이후 평가는 [Transformers BF16](TRANSFORMERS_BF16.md)과 [FP32 parity](transformers-fp32-results/SUMMARY.md)로 진행했다.
2026-11-20 사용자 요청으로 `tailab` 1번 GPU를 사용하고, 모든 큰 파일을 `/mnt/sdb`에 저장한다.

## 실행 환경

| 항목 | 값 |
|---|---|
| SSH | `tailab` |
| GPU | 호스트 1번 RTX PRO 6000 Blackwell Max-Q 96GB, 컨테이너 내부 0번 |
| GPU UUID | `GPU-4d10fa0e-f11b-ca93-a51d-bea42af0dfaa` |
| 컨테이너 | `click-vllm-20261120` |
| 기반 이미지 | `tailab:0.0.1` / `sha256:512b50ba045fd9834c0876c06279824db294a1318c545560279b82392c9ab2cd` |
| 저장 공간 | 호스트 `/mnt/sdb/hyeongrae-click-vllm-20261120` → 컨테이너 `/workspace` |
| Python / 추론 | Python 3.12.16 / vLLM 0.34.0 / PyTorch 2.14.0+cu130 / Transformers 5.20.1 |
| 정밀도 | BF16, 비양자화, 후보별 batch 1, TP 1 |

컨테이너 루트는 읽기 전용이다. 모델, 가상환경, Python, pip/uv/HF/CUDA 캐시, 임시파일,
실행 로그와 결과는 모두 `/workspace` 아래에 있다. Docker 전역 data-root와 호스트 드라이버는 변경하지 않았다.

CUDA 실행 라이브러리는 13.0인데 최초 의존성 설치에서 컴파일러 13.5가 선택되어 FlashInfer 컴파일이 실패했다.
컨테이너 가상환경에서 `nvidia-cuda-nvcc`, `nvidia-cuda-crt`, `nvidia-nvvm`을 `13.0.88`,
`nvidia-cuda-cccl`을 `13.0.85`로 맞췄다. `CUDA_HOME`은 가상환경의 `nvidia/cu13`을 가리킨다.
같은 디렉터리 안에 `lib64 → lib`, `lib/libcudart.so → libcudart.so.13` 링크를 추가해
FlashInfer 컴파일러가 pip 패키지의 CUDA 실행 라이브러리를 찾도록 했다.
전체 패키지 목록과 실패·재검산 로그는 원격 작업 폴더에 보관한다.

## 입력 준비 결과

1,995문항, 각 문항의 정답·프롬프트·후보 문자열을 기존 Polyglot 입력과 대조했다.
Lighteval 태스크 및 두 버전의 harness 태스크를 실제 loader/request API로 구성해 비교했다.

| 모델 | 모든 조건 중 최대 길이 | Calibration | Validation |
|---|---:|---:|---:|
| Kanana-2-3B-Instruct | 1,565토큰 | 55 | 69 |
| Qwen3.8-27B | 1,955토큰 | 55 | 69 |

채점 입력 한도는 기존 2,048토큰을 유지한다. vLLM 어댑터가 내부적으로 요구하는 부가 생성 1토큰을 위해
엔진 한도만 2,049로 설정하며, 그 부가 토큰은 점수에 합산하지 않는다.
`max_num_batched_tokens`도 2,049로 고정한다. 무작위 모델은 head dimension 128로 구성했다.
입력 경계·후보 누락·잘림·점수 합산 위치를 확인하는 GPU 없는 회귀 검사 6개가 통과했다.
이 준비 결과와 작은 무작위 모델 검산은 두 실제 모델의 CLIcK 정확도 결과가 아니다.

2026-11-20 16:47 KST: 작은 모델의 4/5지선다 × 6조건 검산 12건이 통과했다.
Lighteval과 입력 정렬 harness의 점수·예측이 일치했고, 독립 Transformers 검산과의
최대 후보 logprob 차이는 0.02937794였다. 실제 모델의 허용오차는 이 값을 재사용하지 않고
각 모델의 사전 선정 calibration에서 별도로 정한다. 이후 Kanana 실제 모델 검증을 시작했다.

## 실행 파일

- `vllm_click.py`: 원본 입력 검증, 각 도구의 native vLLM 어댑터, Transformers 독립 검산, 파일럿 판정.
- `test_vllm_click.py`: 후보 토큰 경계와 실제 vLLM 요청/반환값 감사 회귀 검사.
- `vllm_smoke.py`: 무작위 작은 Qwen3 모델로 GPU 연결 검산.
- `vllm_run.py`: 모델·단계별 순차 실행. 파일럿 실패 시 전체 평가를 중단한다.
- `vllm_report.py`: 전체 12개 결과의 완전성·일치 여부를 확인하고 원문 없는 집계 보고서를 생성한다.

각 모델에서 Lighteval, 입력 정렬 harness, native harness 4조건을 실행한다.
입력 정렬 harness와 native `pr4420_full`은 별도 조건이다. 과거 Polyglot의 Transformers/FP32와
이번 vLLM/BF16은 추론 환경이 다르며 논문 방식 재현을 뜻하지 않는다.

## Kanana 파일럿 결과 — 2026-11-20 17:00 KST

124문항 × 6조건을 각 vLLM 어댑터와 별도 Transformers/BF16 forward로 실행했다.
**기존 계획의 독립 검산 조건은 미통과이며 전체 1,995문항 평가는 시작하지 않았다.**

| 비교 | 문항 | 예측 불일치 | 최대 후보 logprob 차이 |
|---|---:|---:|---:|
| Lighteval ↔ 입력 정렬 harness, 모두 vLLM | 124 | 0 | 0 |
| Lighteval vLLM ↔ Transformers | 124 | 5 | 3.036299 |
| 입력 정렬 harness vLLM ↔ Transformers | 124 | 5 | 3.036299 |
| base_letter vLLM ↔ Transformers | 124 | 9 | 1.123440 |
| pr4420_letter vLLM ↔ Transformers | 124 | 12 | 1.123440 |
| base_full vLLM ↔ Transformers | 124 | 10 | 9.831754 |
| pr4420_full vLLM ↔ Transformers | 124 | 8 | 2.932659 |

파일럿 중 4지선다 78문항은 base↔#4420의 입력·점수·예측이 letter/full 각각 모두 동일했다.
입력 token IDs, 후보 경계, 잘림 여부, 점수 합산 위치 검사도 통과했다.
위의 Transformers 비교는 calibration/validation에서 정한 오차 안에 들었지만, 예측 완전 일치 조건에서 실패했다.
허용오차를 키우거나 기존 실패 기록을 PASS로 바꾸지 않았다.

추가 진단은 불일치 5문항과 최초 probe 2문항, 총 7문항만 대상으로 했다.
Transformers의 입력 끝 토큰 포함 여부와 BF16/FP32 계산을 비교했고,
vLLM/FP32(TRITON_ATTN)와 Transformers/FP32는 7문항 모두 같은 답을 골랐다
(최대 후보 점수 차이 0.174923). 이는 정밀도·계산 커널 차이가 영향을 준다는 근거지만
전체 파일럿 문제가 해결됐다는 증거는 아니다. 본 평가의 BF16 설정은 바꾸지 않았다.
두 구현의 YaRN inverse frequency 및 attention scaling 값도 동일함을 별도 확인했다.

### 전체 평가 재개안 — 아직 적용하지 않음

기존 계획 7-B/C는 독립 Transformers 검산까지 통과해야 전체 평가를 시작하도록 정했다.
다음 기준으로 변경하면 vLLM 비교 실험 자체를 진행할 수 있으나, 사용자 확인 전에는 적용하지 않는다.

1. 입력·토큰·후보 합산 검사는 기존대로 모두 통과해야 한다.
2. Lighteval↔입력 정렬 harness의 예측 완전 일치와 후보 점수 차이 ≤ 1e-6을 요구한다.
3. 4지선다 base↔#4420도 letter/full 각각 같은 입력·예측, 점수 차이 ≤ 1e-6을 요구한다.
4. Transformers 독립 검산 결과와 실패 상태는 그대로 보존하고 별도 표에 공개한다.
   이를 통과한 것처럼 표기하지 않으며, 모델·BF16·6조건·1,995문항·raw prompt는 유지한다.
5. 전체 결과에도 2~3의 비교를 적용하고, 미달 시 완료 보고서에 검증 실패를 명시한다.

이는 수치 검산의 합격 조건을 바꾸는 안이며 단순한 재시작이 아니다.

Kanana의 probe/pilot 1,512행은 코드·protocol·행 해시와 문항 수를 검증해
ignored 로컬 폴더의 `kanana-pilot-evidence.tar.gz`로 회수했다.
기존 순차 실행기는 파일럿 실패로 종료됐다. Qwen은 별도 `qwen_validation.py` 프로세스에서
다운로드 완료 → 파일 해시 확인 → probe/pilot을 진행한다. 이 프로세스는 전체 평가를 시작하지 않는다.

## 진행 확인

순차 실행기는 SSH 연결과 별개로 컨테이너에서 실행한다. 다음은 읽기 전용 진행 확인 명령이다.

```bash
ssh tailab 'docker exec click-vllm-20261120 cat /workspace/results/status.json'
ssh tailab 'docker exec click-vllm-20261120 tail -n 30 /workspace/logs/controller.log'
ssh tailab 'docker exec click-vllm-20261120 tail -n 30 /workspace/logs/qwen-validation.log'
ssh tailab 'docker exec click-vllm-20261120 tail -n 15 /workspace/logs/download.log'
ssh tailab 'nvidia-smi -i 1'
```

`WAITING_GPU_SMOKE`는 사전 GPU 검산 대기, `PREPARING_MODEL`은 모델 다운로드·파일 해시 확인,
`RUNNING`은 해당 단계 실행 중, `STOPPED`는 로그 확인이 필요한 중단,
`COMPLETE`는 12개 결과와 최종 비교 검증·보고서 생성이 완료됐다는 뜻이다.
`STEP_COMPLETE`는 개별 단계 완료이며 전체 실험 완료와 다르다.

## 원격 산출물

```text
/workspace/
  environment/           # 소스 해시, 패키지 목록, 준비·설치 종료 상태
  prepared/protocol.json # 모델 revision, 입력 길이, 파일럿 목록, 환경
  cache/huggingface/     # 두 모델 가중치 및 원본 데이터
  smoke/                # 무작위 모델과 GPU 검산 결과
  results/<model>/      # probe/pilot/full 문항별 결과와 고정 실행 정보
  results/status.json   # 순차 실행 상태
  logs/                 # 단계별 로그
  report/               # 완료 후 집계 표·분야별 CSV·상세 보고서
```

완료 결과를 로컬로 회수할 때는 새 `local/qwen38-kanana2-vllm/` 경로를 사용한다.
기존 Polyglot 결과에 덮어쓰지 않고, 원문과 문항별 로그는 Git에 추가하지 않는다.
이 실행으로 upstream PR을 수정하거나 새 PR을 자동 게시하지 않는다.
