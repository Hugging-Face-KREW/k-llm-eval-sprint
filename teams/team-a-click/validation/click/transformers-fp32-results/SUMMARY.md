# CLIcK Kanana-2-3B · Qwen3.8-27B Transformers FP32 parity 결과

2026-11-22 07:23 KST 완료. 모델 2개 × 4조건 × 1,995문항 = 15,960개 결과. 기존 BF16 평가(2026-11-20)와 같은 native 어댑터·입력·채점을 쓰고 **정밀도와 장치 배치만 바꿨다.** BF16 체크포인트를 FP32로 무손실 upcast했고, 모든 파라미터와 채점 logits가 `torch.float32`다. 모든 문항이 입력·채점·FP32 감사를 통과했다.

## 핵심: Lighteval ↔ 입력 정렬 harness (a)

| 모델 | 같은 예측/문항 | 최대 후보 logprob 차이 | Lighteval 정답 | aligned harness 정답 | BF16 같은 예측 |
|---|---:|---:|---:|---:|---:|
| Kanana-2-3B-Instruct | **1995/1995** | 4.73e-04 | 794 (39.80%) | 794 (39.80%) | 1746/1995 |
| Qwen3.8-27B | **1995/1995** | 9.30e-03 | 1394 (69.87%) | 1394 (69.87%) | 1943/1995 |

FP32에서는 두 모델 모두 Lighteval과 입력 정렬 harness의 예측이 모든 문항에서 같았다. pilot 124문항도 124/124로 같았다. 점수가 bitwise로 같지는 않다(최대 차이 0이 아님). 그러나 예측을 바꿀 만큼 크지 않았다.

## BF16 불일치 문항의 FP32 결과

| 모델 | BF16 불일치 | FP32에서 일치 | FP32 답 = BF16 Lighteval 답 | = BF16 harness 답 | 둘 다 아님 | FP32 불일치 |
|---|---:|---:|---:|---:|---:|---:|
| Kanana | 249 | 249 (100%) | 110 | 136 | 3 | 0 |
| Qwen | 52 | 52 (100%) | 30 | 21 | 1 | 0 |

BF16 불일치 문항은 1·2위 후보 점수 차(margin)가 작은 경우가 많았다. Kanana는 margin 중앙값이 Lighteval 0.375, harness 0.3125였고, 동점(<1e-4)이 각각 24·17건, 1 이상이 28·25건이었다. Qwen은 중앙값이 둘 다 0.125였고, 동점이 6·10건, 1 이상이 5·3건이었다. 같은 문항에서 두 경로의 최대 점수 차 중앙값은 Kanana 1.06, Qwen 0.28이었다. FP32 불일치는 0건이므로 margin 분포가 없다. 문항별 값은 비공개 archive의 `report-private/`에만 있다.

## 정확도 (FP32, 정답/1,995)

| 조건 | Kanana | Qwen |
|---|---:|---:|
| Lighteval · 보기 전체 | 794 (39.80%) | 1394 (69.87%) |
| 입력 정렬 harness · 보기 전체 | 794 (39.80%) | 1394 (69.87%) |
| 기존 harness · 알파벳 | 1051 (52.68%) | 1451 (72.73%) |
| #4420 harness · 알파벳 | 1064 (53.33%) | 1482 (74.29%) |

알파벳 조건의 `acc_norm`은 `acc`와 같았다. 입력 정렬 harness에는 `acc_norm`이 없다.

## base_letter ↔ pr4420_letter, 4지선다 1,739문항 (b)

두 모델 모두 **1,739문항의 후보 점수가 완전히 같았고 예측도 1739/1739 같았다.** BF16 Qwen에서는 19문항의 예측과 1,658문항의 점수가 달랐다. 이번 FP32에서는 조건별로 프로세스 하나가 중단 없이 끝까지 실행했다.

## FP32 ↔ 기존 BF16, 같은 조건 (c)

| 조건 | Kanana 같은 예측 | Kanana 정답 BF16→FP32 | Qwen 같은 예측 | Qwen 정답 BF16→FP32 |
|---|---:|---:|---:|---:|
| lighteval_full | 1783 | 752 → 794 | 1961 | 1396 → 1394 |
| aligned_harness_full | 1809 | 794 → 794 | 1952 | 1404 → 1394 |
| base_letter | 1885 | 1042 → 1051 | 1976 | 1449 → 1451 |
| pr4420_letter | 1879 | 1053 → 1064 | 1975 | 1481 → 1482 |

## BF16의 두 경로 중 FP32와 더 가까운 쪽 (d)

FP32 두 경로의 예측이 같으므로 FP32 Lighteval과 비교해도, aligned와 비교해도 결과가 같다. Kanana는 **BF16 harness**가 1809로 BF16 Lighteval(1783)보다 FP32와 더 많이 일치했다. Qwen은 **BF16 Lighteval**이 1961로 BF16 harness(1952)보다 더 많이 일치했다. 어느 한쪽 도구가 일관되게 FP32에 더 가깝지는 않았다.

## 층별 정답과 FP32 #4420 효과 (e)

| 모델·조건 | 4지 1,739 | 5지 256 | 정답 E 49 |
|---|---:|---:|---:|
| Kanana Lighteval/aligned | 754 | 40 | 0 |
| Kanana base_letter → pr4420_letter | 990 → 990 | 61 → 74 | 0 → 2 |
| Qwen Lighteval/aligned | 1236 | 158 | 22 |
| Qwen base_letter → pr4420_letter | 1293 → 1293 | 158 → 189 | 0 → 43 |

#4420 효과(base→pr4420)는 모두 5지선다에서만 생겼다. Kanana는 예측 변경 45건, 틀림→맞음 19건, 맞음→틀림 6건으로 +13이었다. Qwen은 84건, 46건, 15건으로 +31이었다. 정답 E 문항 49개 중 Qwen은 43개가 틀림→맞음으로 바뀌었다. 4지선다는 입력이 같아 변경이 0건이다.

## 실행 조건

- 모델: `kakaocorp/kanana-2-3b-instruct` @ `6a5d788`, `Qwen/Qwen3.8-27B` @ `3756181`. 0-shot raw prompt, chat template 없음, 길이 정규화 없음, eager attention, TF32 off, `float32_matmul_precision("highest")`, seed 1234, batch size 1, 2,048토큰 한도와 잘림 없음. Lighteval 0.13.1.dev0, lm_eval 0.4.14.dev0, transformers 5.20.1, torch 2.14.0.
- 장치: `tailab` RTX PRO 6000 Blackwell Max-Q 96GB 2장(호스트 GPU 0·1), 컨테이너 `click-fp32-20261122`(`tailab:0.0.1`). Kanana는 `cuda:0`에 11.85GiB를 올렸다. Qwen은 `device_map="sequential"`, `max_memory={0: 50GiB, 1: 70GiB}`로 `cuda:0` 44.76GiB(visual·embed·layer 0–26)와 `cuda:1` 57.15GiB(layer 27–63·norm·lm_head)로 나눴다. CPU offload는 없었다.
- 실행 시간: probe 4분, 이어서 02:11–07:23 KST. Kanana pilot+full 36분, Qwen pilot+full 4시간 33분. full 단계 시간은 BF16의 약 2.2–4.3배였다. 중간 실패나 재시작은 없었다(`restarts=[]`).
- 메모리 peak(torch allocated, 장치별): Kanana 19.4GiB. Qwen 62.9 / 67.6GiB. caching allocator의 reserved는 Qwen 91.7 / 93.8GiB, nvidia-smi peak는 93,943 / 96,809MiB(총 97,887MiB)까지 올라갔지만 OOM은 없었다.
- protocol digest `c92b6d1d…`(BF16 parent `27e3b7c2…`). runner file hash, 모델 파일 hash, 결과 hash, 실제 device map, 단계별 시간은 [provenance.json](provenance.json)에 있다.
- 비공개 archive: `../local/qwen38-kanana2-transformers/20261122-tailab-gpu01-fp32/final-evidence-20261121T222434Z.tar.gz`(Git 제외). 원격과 로컬 SHA256은 `4c4551a2356bdfe24f27591d998562050fd27a83e7c20582772743e0e4cba264`로 일치한다.

## PR 표 형식 초안

| model | items | same prediction | Lighteval acc | input-aligned lm-eval acc | max abs log-prob diff |
|---|---:|---:|---:|---:|---:|
| Kanana-2-3B-Instruct | 1,995 | 1,995 | 0.3980 (794) | 0.3980 (794) | 4.73e-04 |
| Qwen3.8-27B | 1,995 | 1,995 | 0.6987 (1394) | 0.6987 (1394) | 9.30e-03 |

Setup: `kakaocorp/kanana-2-3b-instruct` (`6a5d788`) and `Qwen/Qwen3.8-27B` (`3756181`), BF16 checkpoints loaded as float32, 0-shot, no chat template, no length normalization, eager attention, TF32 off, batch size 1, on RTX PRO 6000 Blackwell 96GB GPUs (Qwen split across two), with Lighteval 0.13.1.dev0.

## 한계

- FP32 결과는 BF16 불일치가 정밀도 문제라는 기존 진단과 일관된다. 다만 개별 문항에서 어떤 연산이 차이를 만들었는지 특정한 것은 아니다. FP32에서도 점수 차가 0은 아니다.
- BF16 Qwen 재실행에서 생긴 base↔#4420 차이 19건의 원인은 이 실행으로 확정되지 않는다. FP32에서는 중단과 재개 없이 실행했고 차이가 0이었다.
- 가중치는 BF16 값을 FP32로 표현한 것이다. 원래 FP32로 학습·배포된 가중치와 같은 의미는 아니다. 하드웨어도 Polyglot 표의 A100과 다르다.
- 단일 지시문, 원본 보기 순서, 0-shot 조건이다. 논문의 지시문 3종 × 보기 순환 평균 재현이 아니다.
