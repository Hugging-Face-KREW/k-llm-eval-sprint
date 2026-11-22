# CLIcK Qwen3.8·Kanana2 Transformers BF16 실행

**2026-11-20 20:10:34 KST 전체 12개 평가 완료.** [최종 결과 요약](transformers-bf16-results/SUMMARY.md)과 상세 보고서·원본을 로컬에 보관하고 23,940개 결과의 무결성과 집계를 확인했다. 두 모델 모두 공식 Transformers BF16 어댑터로 평가했으며 기존 vLLM 결과도 보존한다. 평가 완료와 예측 일치는 별개로, `prediction_parity=false`다. Lighteval↔입력 정렬 harness는 Kanana 1,746/1,995, Qwen 1,943/1,995 예측이 같았다. Qwen letter의 입력이 동일한 4지선다에서도 19문항의 예측 차이가 있어 원인 검토가 필요하다.

완료 알림은 원래 대화에 전달되어 turn 시작까지 확인됐고, 알림 감시 프로세스는 종료됐다. 평가 GPU 메모리도 반환됐다. 이하 시간별 기록은 실행 이력이다.

17:48 KST 확인: Kanana의 6조건 × 124문항 파일럿에서 입력·채점 검증이 통과하여 전체 평가에 진입했다. Lighteval↔입력 정렬 harness 예측은 **116/124 일치**, 최대 후보 logprob 차이는 **2.5**였다. 두 도구 모두 Transformers BF16이어도 완전히 일치한 결과는 아니다. 4지선다 78문항의 base↔#4420은 letter/full 모두 점수·예측이 정확히 같았다. Qwen은 Kanana 전체 평가 뒤 자동 실행 대기 중이다. 이 수치는 전체 평가 점수가 아니다.

19:26 KST 후속 확인: Kanana 6조건과 Qwen 3조건의 전체 평가가 완료됐다. Qwen `pr4420_letter`는 1,495문항 저장 후 19:25에 읽기 전용 점수 재검산 단계에서 중단됐다. 실패 대상 `Textual_CSAT.json#7`을 별도 프로세스에서 재현했을 때는 native 점수·부분 logits 검산·전체 logits 검산이 모두 정확히 같아 통과했다. 원인은 아직 확정되지 않았다. frozen 평가 코드·정밀도·검증 허용오차는 변경하지 않고 미완료 문항부터 재개했다. 실패 로그와 별도 검산 결과는 `diagnostics/`에 보존한다.

재개 실행기는 `diagnostics/resume_with_tracking.py`이며, 30초마다 `results/tracking.json`에 단계·조건별 문항 수·총 진행량을 갱신한다. 완료/오류 시 마지막 상태를 기록한다. 원격 추적 파일 생성과 아래 로컬 알림 감시는 별도 기능이다.

## 완료·오류 알림

19:33 KST 사용자 요청으로 `watch_transformers.py`를 별도 Orca 터미널에서 시작했다. 원격 상태를 30초 간격으로 확인하며, `COMPLETE` 또는 `STOPPED`일 때 원래 Codex 대화로 결과 보고 요청을 보낸다. 연결 확인이 3회 연속 실패하거나 추적 heartbeat가 3분 이상 멈춘 경우도 알린다. 같은 이벤트는 한 번만 전송하며 완료 이벤트 처리 후 감시를 종료한다.

완료 알림은 원격 보고서를 재확인해 결과를 요약하도록 요청하고, 오류 알림은 중단 단계·완료량·오류를 보고하도록 요청한다. 평가 코드와 결과 파일은 수정하지 않는다. 감시 프로세스는 에이전트가 아니라 로컬 Python 프로세스다. **Mac이 깨어 있고 Orca와 원래 Codex 세션이 열려 있어야** 확인·대화 전달이 가능하다. 전송 확인이 불명확한 경우 중복 입력을 막기 위해 임의 재전송하지 않고 receipt에 기록한다.

- 감시 터미널: `term_56697064-58bd-41de-86da-a1d598aeb2c0` (현재 Orca runtime에서만 유효)
- 로컬 상태·전송 기록: `local/qwen38-kanana2-transformers/20261120-tailab-gpu1/notifications/`
- `watcher-status.json`: 마지막 확인 시각과 원격 상태
- `events/<event hash>/delivery-receipt.json`: 실제 Orca 전달 응답. 프롬프트 수신은 결과 보고 완료와 구분한다.

## 범위

- `Qwen/Qwen3.8-27B` @ `37561816e66b5b9153b1b64c10968c18c1e6f4a0`
- `kakaocorp/kanana-2-3b-instruct` @ `6a5d7889964c4c590299d16e309eabab1f73f8a9`
- 모델별 `lighteval_full`, `aligned_harness_full`, `base_letter`, `pr4420_letter`, `base_full`, `pr4420_full` 총 6조건. 전체 12결과 × 1,995문항.
- frozen 데이터·소스·raw prompt·0-shot·원본 보기 순서·단일 지시문 조건 유지. chat template와 추가 BOS/EOS 없음. 입력 정렬 harness는 native harness와 구분한다.
- 두 모델의 배포 가중치와 로드한 모든 파라미터 BF16, 양자화·autocast 없음. attention `eager`, TF32 비활성화, seed 1234, 최대 2,048토큰, 잘림 금지.
- 공식 Lighteval `TransformersModel.from_model` / harness `HFLM(pretrained=model)` 사용. Qwen의 텍스트·비전 architecture는 `AutoModelForImageTextToText`로 로드하고 텍스트만 입력한다.

## 실행·검증

`transformers_run.py`가 Kanana → Qwen 순으로 4/5지선다 2문항 probe → 고정 124문항 파일럿 → 입력·채점 검증 → 1,995문항 전체 평가 → 12개 상세 보고서와 종합표 생성을 수행한다. 프로세스 실패 시 중단하며 다른 GPU 작업을 종료하지 않는다. 문항별 결과와 코드·프로토콜 해시를 저장하여 같은 코드·조건으로 재개할 수 있다.

`transformers_click.py`는 공식 어댑터가 실제로 받은 token IDs와 후보 경계를 확인하고, 실제 forward logits에서 채점 위치를 재계산해 반환 점수와 대조한다. hook은 입력·출력을 수정하지 않는다. 실제 logits·합산 dtype, 배치 모양, 토큰별 logprob를 문항별 기록한다. 관련 CPU 검증 테스트 4개가 통과했다.

공식 배치·padding·log_softmax·합산을 유지한다. `batch_size=1`은 Lighteval에서 한 문항의 4/5개 후보, harness에서 후보 하나를 뜻한다. harness는 마지막 target 토큰을 forward 입력에서 제외하고 Lighteval은 포함한다. 이 차이에 따른 BF16 수치·예측 일치 여부는 **별도 측정**하며, 입력과 채점이 검증되면 전체 평가를 진행한다. 기존 vLLM↔독립 Transformers 검산 불일치를 해결했다고 간주하지 않는다.

## 위치와 확인 방법

- 서버: `tailab`, 호스트 GPU 1번만 노출 (`GPU-4d10fa0e-f11b-ca93-a51d-bea42af0dfaa`). 컨테이너 내부 GPU 0번.
- 이미지/컨테이너: `tailab:0.0.1` / `click-vllm-20261120` (이름만 기존 것 재사용).
- 호스트 실행 폴더: `/mnt/sdb/hyeongrae-click-vllm-20261120/transformers-bf16-20261120`
- 컨테이너 실행 폴더: `/workspace/transformers-bf16-20261120`
- 모델·Python·가상환경·캐시는 상위 `/workspace`의 기존 파일을 재사용하며 실제 저장 장치는 `/mnt/sdb`다. 호스트 전역환경 변경 없음.

```bash
# 현재 단계
ssh tailab 'docker exec click-vllm-20261120 cat /workspace/transformers-bf16-20261120/results/status.json'

# 30초마다 갱신되는 전체 진행량 (재개 실행기)
ssh tailab 'docker exec click-vllm-20261120 cat /workspace/transformers-bf16-20261120/results/tracking.json'

# 단계별 진행 / 실패 원인
ssh tailab 'docker exec click-vllm-20261120 tail -n 20 /workspace/transformers-bf16-20261120/logs/controller.log'

# 19:25 중단 후 재개 실행기의 진행 / 실패 원인
ssh tailab 'docker exec click-vllm-20261120 tail -n 20 /workspace/transformers-bf16-20261120/logs/recovery-controller.log'

# 중단 후 동일 조건 재개 (실행 중에는 다시 시작하지 않음)
ssh tailab 'docker exec -d click-vllm-20261120 bash -lc "source /workspace/transformers-bf16-20261120/eval-env.sh && exec python -u /workspace/transformers-bf16-20261120/code/transformers_run.py >> /workspace/transformers-bf16-20261120/logs/controller.log 2>&1"'
```

완료 시 `report/README.md`, `results.csv`, `categories.csv`, `comparisons.csv`, `effects.csv`, `reports/` 상세 12건과 provenance를 생성한다. `status=COMPLETE`와 `prediction_parity`는 구분한다. 완료가 반드시 모든 예측의 일치를 뜻하지 않는다.

기존 Polyglot은 Transformers/FP32였다. 이번 결과는 BF16이므로 정밀도까지 동일한 비교라고 표현하지 않는다. 논문의 지시문 3종 × 보기 순환 평균도 아니다. 공개 PR 생성·수정은 이번 실행에 포함하지 않는다.
