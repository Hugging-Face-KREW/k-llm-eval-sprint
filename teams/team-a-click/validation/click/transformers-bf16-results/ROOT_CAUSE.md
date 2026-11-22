# CLIcK 불일치 원인 진단

2026-11-20. 기존 전체 평가 결과는 보존했다. 진단 역시 `tailab` GPU 1번, `tailab:0.0.1` 컨테이너, `/mnt/sdb`에서 수행했다.

## 현재 결론

1. **temperature는 원인이 아니다.** 이 평가는 `generate()`로 답변을 샘플링하지 않고, 주어진 후보의 raw logits에 `log_softmax`를 적용해 logprob 합을 비교한다. temperature·top-p·top-k 생성 설정은 이 경로에 들어가지 않는다. Qwen 문제 19문항과 대조군 4문항에서 generation temperature를 0.1 → 2.0 → 0.1로 바꿔도 모든 점수가 같았다. `generate()` 호출 시 오류를 내도록 한 검사도 통과했다. 관측한 CPU/CUDA 난수 상태도 변하지 않았다.
2. **Lighteval↔입력 정렬 harness 차이는 BF16에서 서로 다른 forward 모양으로 계산하면서 재현된다.** 같은 토큰·가중치라도 후보 배치, padding, 마지막 토큰 포함 여부가 다르다. 각 도구의 native 결과를 해당 forward 모양으로 독립 재계산했을 때 모든 진단 문항의 점수가 정확히 일치했다.
3. **Qwen의 동일한 4지선다 차이는 2차 전체 이력 재현에서 6건으로 재관측했다.** 이번에는 모두 새 모델 프로세스로 재개한 구간에서 발생했다. 기록된 사례는 최종 채점 전의 모델 내부 값부터 달랐지만, 구체적인 원인 연산과 최초 19건 전체의 원인은 아직 미확정이다. [2차 진단 완료 보고서](REPLAY_COMPLETE.md)를 확인한다.

## 첫 번째 문제: 계산 모양과 정밀도

진단 문항은 기존 불일치를 우선 선택하고 대조군 4문항을 추가했다. 아래 비율은 진단용이며 전체 데이터의 정확도가 아니다.

| 모델·연산 정밀도 | 진단 문항 | Lighteval↔harness 답 불일치 | 최대 후보 logprob 차이 |
|---|---:|---:|---:|
| Kanana BF16 | 26 | 22 | 2.125 |
| 같은 Kanana 가중치를 FP32로 연산 | 26 | 0 | 0.000333786 |
| Qwen BF16 | 22 | 17 | 3.75 |

Qwen은 이번 단일 96GB GPU에서 전체 모델 FP32 검사를 진행하지 않았다. Kanana의 FP32 결과를 Qwen 전체나 1,995문항 전체에도 보장된다고 확대하지 않는다.

다른 조건을 고정하고 한 가지씩 바꾼 BF16 실험:

| 변경 | Kanana 답 변경/26 | Qwen 답 변경/22 |
|---|---:|---:|
| 전체 후보 배치 → 후보 1개씩, 동일 padding 길이 | 15 | 7 |
| 후보 1개씩 처리에서 오른쪽 padding 제거 | 5 | 8 |
| 후보 1개씩 처리에서 마지막 target 토큰을 forward 입력에서 제외 | 10 | 8 |

마지막 target을 입력에서 제외해도 그 토큰의 확률은 직전 위치 logits로 정상 채점한다. 두 도구 모두 같은 후보 토큰을 채점하지만 forward의 텐서 모양이 달라지는 것이다. 각 변경 효과는 중첩되므로 표의 개수를 합산하지 않는다.

최종 합산만 FP32로 바꾸거나 BF16 모델의 logits에 FP32 `log_softmax`를 적용하는 것만으로는 차이가 모두 사라지지 않았다. **모델 forward 단계에서 이미 생긴 차이**도 있다. 기존 1,995문항의 토큰별 BF16 logprob를 더 높은 정밀도로 합산해도 Kanana는 240문항, Qwen은 54문항의 예측이 달랐다(원래는 각각 249, 52).

PyTorch도 수학적으로 동일한 batch/개별 계산이 bitwise 동일함을 보장하지 않는다. 이 일반 원리와 별개로, 위 표는 실제 고정 모델에서 직접 수행한 개입 실험의 결과다. [PyTorch 2.14 numerical accuracy](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html).

## 두 번째 문제: 확인한 사항과 남은 진단

기존 Qwen `base_letter`↔`pr4420_letter`에서 4지선다 1,739문항의 입력 hash·토큰 hash·실제 배치 크기/길이·logits dtype·합산 dtype은 같았다. 그런데 19문항의 답과 1,658문항의 후보 점수가 달랐다. 19문항 중 13문항은 한쪽 실행에서 상위 점수 동점이 있었고, 두 실행의 상위 두 후보 점수 차이는 최대 0.3125였다. 작은 수치 변화에 판정이 민감한 사례들이지만, 이것만으로 차이를 만든 연산을 특정할 수는 없다.

문제 19문항 + 대조군 4문항에 대해 다음 검사를 완료했다.

- temperature 0.1/2.0/0.1, 기본 설정에서 반복: 138회 채점.
- 원래 검산 hook 유지, 긴 full 문항 12개 선행, CUDA 메모리 캐시 비우기, cuDNN deterministic 켜기, cuDNN 끄기: 230회 채점.
- 원래 `Backend.score()`와 진단 계측 경로 직접 대조 및 반복: 138회 채점.
- 새 프로세스에서 `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `torch.use_deterministic_algorithms(True)`, `cudnn.deterministic=True`: 138회 채점.

각 검사에서 같은 문항의 base/#4420 점수와 반복 점수가 모두 같았고, 관측한 난수 상태와 모델 buffer에도 변화가 없었다. strict 설정과 기본 설정의 첫 결과 23개도 정확히 같았다. 따라서 **temperature, cuDNN 또는 deterministic 미설정이 원인이라고 확정할 근거는 현재 없다.** 원래 실행은 seed를 고정했지만 결정적 연산을 강제하지 않았다는 점은 별도로 확인했다. seed 고정과 결정적 알고리즘 강제는 서로 다른 설정이다. [PyTorch 2.14 reproducibility](https://docs.pytorch.org/docs/2.14/notes/randomness.html).

## 전체 이력 재현: 1차 중단, 오류 증거 기록을 보강한 2차 완료

`replay_transformers.py`가 원래 순서를 재현한다.

1. `aligned_harness_full` 1,995문항.
2. 같은 모델 프로세스로 `base_letter` 1,995문항.
3. 같은 프로세스로 `pr4420_letter` 앞 1,495문항.
4. 원래 재개 시점처럼 모델을 새 프로세스에서 로드해 나머지 500문항.

새로운 5,985개 진단 결과를 별도 경로에 저장하며 기존 점수에 덮어쓰지 않는다. 원래 평가 함수·정밀도·검증 기준을 유지한다. 문제 19문항과 대조군 4문항은 첫 후보 forward의 입력, 각 decoder layer 마지막 위치, lm_head 입력, logits를 읽기 전용으로 보관해 차이가 처음 생긴 위치를 비교한다. 계측에 따른 관측 비용은 추가된다. 작은 CPU 모델로 hook의 입력·출력 불변성과 첫 호출만 기록하는 동작을 검증했다.

- 1차 원격 실행 폴더: `/workspace/transformers-bf16-20261120/diagnostics/root-cause-20261120/replay`
- 상태: `results/status.json`, 진행량: `results/tracking.json`.
- 완료 보고서: `report/README.md`, `report/results.json`.
- 원래 대화에 완료·오류를 전달하는 별도 Orca 알림 감시를 연결했다. Mac이 깨어 있고 Orca와 원래 세션이 열려 있어야 전달된다.

### 21:19 KST 중단과 후속 확인

1차 재현은 5,985건 중 **3,510건**을 저장한 뒤 중단됐다. 입력 정렬 harness 1,995건 완료, `base_letter` 1,515건 완료, `pr4420_letter`는 미시작이다. `base_letter`의 1,516번째 문항(`Textual_CSAT.json#27`, index 1515)에서 `Native score differs from audited continuation positions` 오류가 발생했다. 기존 검증 조건이 중단시켰으며, 당시 개별 점수·logits를 보존하지 못해 그 로그만으로 차이가 생긴 연산을 특정할 수 없다.

- 완료한 입력 정렬 harness 1,995건은 최초 실행 대비 **5건의 답이 달랐다**. 정답 수는 1,404 → 1,402, 후보 점수가 완전히 같은 문항은 1,497개였다. 실행 간 수치 차이를 재관측한 진단 결과이며 기존 평가 점수를 대체하지 않는다.
- 저장된 15문항(문제 사례 11개와 대조군 4개)의 첫 후보 forward에서 입력, 모든 관측 레이어, lm_head 입력, logits를 새 프로세스와 비교했으며 전부 같았다. native 점수도 모두 같았다.
- 최초 중단 문항(index 1495)과 이번 중단 문항(index 1515)을 base/#4420 각각 3회, 총 12회 검사했으나 검산 오류는 재현되지 않았다. 같은 logits의 sliced/full-shaped log_softmax도 정확히 같았다.
- 따라서 아직 **19건 불일치의 원인이나 이번 검산 실패의 원인이 확정된 것은 아니다.** 두 현상이 같은 원인인지도 미확정이다.

2차 진단은 `/workspace/transformers-bf16-20261120/diagnostics/root-cause-20261120/replay-recorded`에 별도 저장한다. 오류 순간의 native 점수·검산값·각 후보 forward의 raw logits를 보존하도록 관측만 추가했다. 기존 모델·native 채점 함수·검증 허용오차를 유지하며, 실패 검사를 우회하지 않는다. 작은 CPU 검사로 기존 pass/fail 유지, 모델 출력 불변, 실패 증거 저장을 확인했다. 2차 실행의 완료·오류 알림도 연결했다.

**2차 완료:** 2026-11-20 22:18:07 KST, 5,985/5,985개 결과를 저장했다. 4지선다 동일 프로세스 구간 1,300개는 점수까지 같았고, 재개 구간 439개에서는 답 6개·후보 점수 416개가 달랐다. 추적한 재개 구간 8개에서는 마지막 토큰 위치의 layer 18/19(0부터 세는 번호)부터 관측 차이가 있었고 raw logits도 달랐다. 모델 forward 내부 차이는 확인했지만, 전체 토큰 위치를 저장한 것은 아니므로 최초 원인 레이어/커널을 특정한 것은 아니다. 이번에는 검산 오류가 재현되지 않았다. 세부 결과와 한계는 [2차 완료 보고서](REPLAY_COMPLETE.md)에 정리했다. 알림 감시는 완료 알림 전달 후 종료됐다.

1차 중단 원본 archive SHA256: `6f9786766d42338a934ada963a34b582153f7df28cba1be7a07065815d0977f1` (`../local/qwen38-kanana2-transformers/20261120-tailab-gpu1/root-cause/replay-stopped-20261120T121908Z.tar.gz`, Git 제외). 중단 집계: [REPLAY_STOPPED.json](REPLAY_STOPPED.json).

후속 15문항 trace 비교·12회 검산·중단 보고서도 `replay-stop-inspection-20261120T1224Z.tar.gz`로 같은 로컬 폴더에 보관했다. SHA256 `75fc8b77e84158c973aadce5e8efc074b9117f0a34bc9d5c4eb0ff27a75f6385`. 두 archive 모두 원격/로컬 해시 일치를 확인했다.

초기 진단 원본: `../local/qwen38-kanana2-transformers/20261120-tailab-gpu1/root-cause/initial-diagnostics.tar.gz` (Git 제외). SHA256 `13508202cbcb8bfb8fc181c244de607e92c38f9bcabe834a69620765db1e8578`. 기계 판독 요약: [ROOT_CAUSE_INITIAL.json](ROOT_CAUSE_INITIAL.json).

## 2026-11-21 웹 사례 대조와 원인 후보

공식 문서와 upstream 이슈의 후속 분석까지 확인했다. 이번에는 웹 조사와 고정 실행 환경의 읽기 전용 코드 점검만 했으며 모델 평가를 추가 실행하거나 패키지·평가 설정을 변경하지 않았다.

### 1. 배치 차이에 따른 오차: 직접 부합하는 사례

[PyTorch 2.14 numerical accuracy](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html)는 batch/개별 계산이 수학적으로 같아도 bitwise 동일하지 않을 수 있다고 명시한다. [PyTorch #151658](https://github.com/pytorch/pytorch/issues/151658)에서도 같은 입력·가중치의 `Linear`를 묶거나 나눠 계산했을 때 달라졌으며, 유지보수자는 shape별 커널과 덧셈 순서 차이를 설명했다. 해당 이슈는 FP16 사례이며 우리 BF16 실험과 dtype이 동일한 것은 아니다.

우리에게는 이 일반 설명에 더해 통제 실험 근거가 있다. 같은 가중치에서 배치/패딩/마지막 입력 토큰만 바꾸어 native 결과 차이를 재현했고, Kanana 진단 26문항의 BF16 불일치 22건은 FP32 연산에서 0건이 됐다. 첫 번째 문제의 설명은 강하게 뒷받침된다.

### 2. Qwen GatedDeltaNet: 작은 오차가 커지는 과정에 부합

[Transformers #46190의 후속 분석](https://github.com/huggingface/transformers/issues/46190#issuecomment-4637480226)은 Qwen3.5에서 full forward와 cache를 사용한 prefill/decode가 달라지는 사례를 조사했다. 실제 FP32 연산에서는 차이가 작아졌고, FP32 내부 연산 순서의 작은 차이가 BF16 반올림 경계를 넘으며 여러 레이어를 거쳐 커지는 현상을 보고했다. 최초 게시물의 ‘FP32에서도 동일’ 주장은 실제로 BF16으로 로드된 별도 dtype 버그 때문에 잘못된 대조군이었다. 이 이슈를 단순한 GDN 구현 오류 확정 사례로 인용하지 않는다.

우리 고정 체크포인트는 `Qwen3_5ForConditionalGeneration`을 사용한다. 읽기 전용 확인에서 0부터 세는 layer 18은 `linear_attention`(GDN), layer 19는 `full_attention`이었다. 설치된 `transformers==5.20.1`의 GDN 경로는 `F.conv1d`, FP32로 올린 q/k/v·누적 decay·행렬곱·`solve_triangular`, BF16 출력 복귀를 포함한다. 따라서 가중치가 BF16이라고 모든 중간 연산까지 BF16인 것은 아니다.

우리 trace의 작은 차이가 뒤쪽 레이어와 logits에서 커지는 현상은 위 설명과 일관된다. **다만 외부 사례는 서로 다른 처리 경로의 비교이고, 우리는 같은 입력/shape의 재실행도 달랐다.** 오차 증폭 과정의 유사성이 최초 오차의 원인까지 증명하지는 않는다. 또한 마지막 토큰만 기록했으므로 layer 18이 모든 토큰에서 최초 발생 지점이라고 단정할 수 없다.

### 3. 실행별 차이를 만드는 후보: 결정적 연산과 실제 내부 상태

[PyTorch 재현성 문서](https://docs.pytorch.org/docs/2.14/notes/randomness.html)는 seed 고정, cuDNN benchmark 비활성화, 결정적 연산 강제가 서로 다르다고 설명한다. `cudnn.benchmark=False`만으로 선택한 합성곱 알고리즘 자체의 결정성을 보장하지 않는다.

기존 실행은 seed와 TF32 설정을 고정했지만 `cudnn.deterministic=False`, `deterministic_algorithms=False`, `CUBLAS_WORKSPACE_CONFIG` 미설정이었고 BF16 reduced-precision reduction은 켜져 있었다. 따라서 수치/결정성 설정은 검사 대상이다. 그러나 짧은 기존 진단에서는 기본 설정도 일치했고 strict 설정도 일치했으므로, strict 설정이 문제를 해결했다고 주장할 수 없다.

[cuBLAS 13.0 재현성 문서](https://docs.nvidia.com/cuda/archive/13.0.0/cublas/index.html#results-reproducibility)는 같은 toolkit·GPU 조건에서 단일 CUDA stream 실행의 재현성을 명시하고 다중 stream 등의 예외를 설명한다. **따라서 ‘GPU는 원래 매번 랜덤하게 계산한다’거나 ‘프로세스 재시작 자체가 원인’이라고 설명하는 것은 부정확하다.** 다중 stream 사용, 실제 연산 선택, 내부 tensor의 값·stride·dtype, 로드된 파라미터/상태 중 무엇이 달랐는지 확인해야 한다.

추가로 [PyTorch #88147](https://github.com/pytorch/pytorch/issues/88147)은 값이 같아도 tensor stride가 다르면 deterministic 설정 아래에서 합성곱 결과가 달라질 수 있는 사례다. 구형 PyTorch의 Conv2d 사례이므로 우리 Conv1d에 같은 버그가 있다고 보지는 않지만, 입력 token hash만으로 내부 tensor layout까지 같다고 가정하면 안 된다는 점을 뒷받침한다.

### 4. 비슷하지만 현재 실행에 바로 적용할 수 없는 사례

- [SGLang #46446](https://github.com/sgl-project/sglang/issues/46446): Qwen3.5·RTX PRO 6000 Blackwell·BF16 환경에서 deterministic 설정에도 실행 경로에 따라 출력이 달라졌고, 후속 조사에는 별도의 DeepGEMM shared-memory 순서 버그도 등장했다. 우리는 SGLang/DeepGEMM 실행 경로가 아니라 native PyTorch 및 GDN reference fallback을 사용했다. 현재 model source에 DeepGEMM 호출이 없고 별도 읽기 전용 프로세스의 BLAS 선호도도 cuBLAS였다. 동일 GPU라는 이유로 해당 버그나 패치를 우리 원인/해결책으로 채택할 수 없다.
- [Transformers #46459](https://github.com/huggingface/transformers/issues/46459): `AutoModelForCausalLM`에서 dtype 요청이 무시된 과거 문제. 우리는 Qwen에 `AutoModelForImageTextToText`를 사용했고 실제 파라미터 dtype도 검사했다. Kanana FP32 대조군은 로드 후 `.float()`와 실제 dtype 확인을 거쳤다. 이 버그가 현재 대조군을 무효화한다는 근거는 없다.
- cache decode, FlashAttention backward, MoE routing, 양자화 모델 등의 사례는 현재 dense·eager·likelihood 실행과 구분해야 한다. `generate()`의 temperature 조절은 현재 계산 경로에 영향을 주지 않는다.

### 현재 판단과 다음 검증 순서

**가장 타당한 설명:** 첫 번째 문제는 shape에 따른 수치 차이이며, Qwen 재실행 문제는 아직 확인되지 않은 실행/상태 차이가 모델 forward의 작은 차이를 만들고 BF16 변환과 후속 레이어에서 커지는 과정으로 추정한다. GDN의 합성곱·행렬곱·누적 계산은 우선 관측할 위치이지 원인 확정 연산이 아니다.

1. 기본 설정에서 재시작 차이가 실제로 발생하는 최소 조건을 먼저 확보한다. 기본 설정에서도 차이가 없는 짧은 검사만으로 해결을 판정하지 않는다.
2. 두 프로세스의 실제 파라미터·buffer hash와 GDN 입출력 전체 토큰의 값/shape/stride/dtype을 비교한다. 기존 checkpoint hash와 마지막 토큰 trace만으로는 이 부분이 완전히 검증되지 않았다.
3. 같은 재현 조건에서 결정성 설정, cuDNN 경로, BF16 reduced-precision reduction을 각각 하나씩 바꿔 최초 차이가 사라지는지 확인한다. reduced-precision reduction은 오차 크기 후보이며 그 자체로 비결정성의 증거는 아니다.
4. 차이가 생기는 연산을 분리한 뒤 그 연산만 FP32/FP64로 대조한다. 전체 27B 모델을 FP32로 올리거나 fast-path 패키지를 설치하는 것은 현재의 첫 조치가 아니다.

이 순서는 후속 진단 제안이다. 이번 조사에서 새로운 GPU 실험은 시작하지 않았다.
