# KorMedMCQA 원본(lm-evaluation-harness)과 문항 단위 비교

Lighteval 포크에 머지한 `kormedmcqa:{doctor,nurse,pharm,dentist}` 태스크(포크 PR #3)가
[lm-evaluation-harness `kormedmcqa` 태스크](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/kormedmcqa)(version 3.0)와
같은 결과를 내는지 `test` 전체 3,009문항으로 확인한 기록입니다. 업스트림 이슈는 [huggingface/lighteval#1481](https://github.com/huggingface/lighteval/issues/1481)입니다.
설계는 [design.md](../design.md)를 봅니다.

## 코드와 검증 자료

| 산출물 | 위치와 역할 |
| --- | --- |
| 태스크 코드 | Lighteval 포크 `team-d/kormedmcqa`(`1f1c1d24`, 태스크 커밋 `88089039`)의 `src/lighteval/tasks/tasks/kormedmcqa.py` |
| 단위 테스트 | 같은 브랜치의 `tests/unit/tasks/test_kormedmcqa.py`, 33개 |
| 비교 스크립트 | [compare_with_harness.py](compare_with_harness.py): 두 도구의 문항별 기록을 행 번호로 맞춰 5가지를 비교 |
| 실행 결과 | [results/doctor.json](results/doctor.json), [results/dentist.json](results/dentist.json): 스크립트 `--report` 출력, 원문 미포함 |

## 비교 방법

같은 subset을 두 도구로 따로 돌리고, Lighteval `--save-details`의 parquet과 harness `--log_samples`의 jsonl을 비교합니다.

- **문항 연결**: Lighteval `doc.id`와 harness `doc_id`(데이터셋 행 번호)로 맞춥니다. Lighteval은 문항을 시드 42로 섞어서 돌리므로 줄 순서로 맞추면 다른 문항끼리 비교하게 됩니다.
- **비교 항목**: 프롬프트 텍스트(`input_tokens` 디코드 vs harness `arguments`), 프롬프트 토큰 ID(harness 프롬프트를 다시 토크나이즈), 생성 텍스트, `extract_choice`로 추출한 글자(vs harness `filtered_resps`), 문항 점수.
- 하나라도 다르면 스크립트가 첫 번째 다른 문항을 출력하고 exit 1로 끝납니다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| 모델 | `Qwen/Qwen2.5-1.5B-Instruct` |
| 설정 | 5-shot, float32, batch size 1, chat template 끔(`override_chat_template=False`), CPU |
| 데이터 | `sean0042/KorMedMCQA` `test` 전체. Lighteval은 revision `79efd6f9`로 고정, harness는 최신 |
| 범위 | `--max-samples`와 `--limit`은 고르는 문항이 달라서 쓰지 않음 |

## 결과

| 태스크 | 문항 | 프롬프트 같음 | 생성 같음 | 점수 같음 | 정확도 (harness / Lighteval) | 표준오차 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `kormedmcqa:doctor` | 435 | 435 | 435 | 435 | 0.3310 / 0.3310 (144) | 0.0226 |
| `kormedmcqa:nurse` | 878 | 878 | 878 | 878 | 0.5114 / 0.5114 (449) | 0.0169 |
| `kormedmcqa:pharm` | 885 | 885 | 885 | 885 | 0.3955 / 0.3955 (350) | 0.0164 |
| `kormedmcqa:dentist` | 811 | 811 | 811 | 811 | 0.3551 / 0.3551 (288) | 0.0168 |
| **합계** | **3,009** | **3,009** | **3,009** | **3,009** | | |

| 전체 점수 | 값 |
| --- | ---: |
| `kormedmcqa:_average` (Lighteval, 네 subset 단순 평균) | 0.3983 |
| harness 그룹 `kormedmcqa` / 논문 (문항 수 가중 평균) | 0.4091 (1,231/3,009) |

두 값이 1.1%p 다른 것은 점수가 가장 높은 nurse의 문항 수가 가장 많기 때문입니다. 업스트림 PR의 Differences 절에 들어갑니다.

생성 출력에 나온 A~E 글자 종류 수:

| 태스크 | 한 글자 | 없음 | 둘 이상 |
| --- | ---: | ---: | ---: |
| doctor | 430 | 0 | 5 |
| nurse | 859 | 0 | 19 |
| pharm | 850 | 0 | 35 |
| dentist | 803 | 0 | 8 |

글자가 없는 출력이 0개라서, 일부러 남겨 둔 harness regex의 두 빈틈(`정답` 뒤 전각 콜론, 글자 바로 뒤 한글)이 점수를 바꾼 문항은 없습니다.

### 확인 범위

- **doctor, dentist**: 이 스크립트로 다섯 항목을 모두 비교했습니다(435/435, 811/811). 결과는 `results/`에 있습니다.
- **nurse, pharm**: 이 스크립트를 만들기 전에 팀원이 각자 PC에서 프롬프트 텍스트, 생성, 점수를 비교했습니다. 토큰 ID와 추출 글자 비교는 하지 않았고, 실행 파일은 팀원 PC에 있습니다. pharm은 Windows에서 돌리느라 Lighteval에 태스크 밖 로컬 수정 4건(`list_models` 인자, 캐시·details 파일명의 `:`·`|`, `xxhash` 인코딩)을 했습니다. 프롬프트, 생성, 채점에는 닿지 않습니다.

## 재현

```bash
SUBSET=dentist

# Lighteval (포크 team-d/kormedmcqa 브랜치를 설치한 환경)
lighteval accelerate \
  "model_name=Qwen/Qwen2.5-1.5B-Instruct,override_chat_template=False,device=cpu,batch_size=1,dtype=float32" \
  "kormedmcqa:${SUBSET}|5" --save-details --output-dir results/lighteval

# lm-evaluation-harness (별도 환경)
lm_eval --model hf \
  --model_args pretrained=Qwen/Qwen2.5-1.5B-Instruct,dtype=float32 \
  --tasks kormedmcqa_${SUBSET} --num_fewshot 5 \
  --batch_size 1 --device cpu --log_samples --output_path results/harness

# 비교 (Lighteval 환경의 python)
python teams/team-d-kormedmcqa/validation/compare_with_harness.py \
  --lighteval-details results/lighteval/details/Qwen/Qwen2.5-1.5B-Instruct/*/details_kormedmcqa:${SUBSET}\|5_*.parquet \
  --harness-samples results/harness/Qwen__Qwen2.5-1.5B-Instruct/samples_kormedmcqa_${SUBSET}_*.jsonl \
  --tokenizer Qwen/Qwen2.5-1.5B-Instruct \
  --report ${SUBSET}.json
```

Apple M5 CPU에서 dentist는 Lighteval 662초, harness 1,205초가 걸렸습니다.

## 담당

| subset | 실행과 비교 |
| --- | --- |
| doctor | @kangmin04 |
| nurse | @minmin-129 |
| pharm | @naha0106-tech |
| dentist | @kangmin04 (Qwen 실행), @eotjd613 (SmolLM2-135M-Instruct로 파이프라인 확인, 811/811 일치) |
