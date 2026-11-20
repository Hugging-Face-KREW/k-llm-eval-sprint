# KorMedMCQA 모델 평가 기록: lm-evaluation-harness, OpenRouter

논문(Kweon et al., [arXiv 2403.01469v3](https://arxiv.org/abs/2403.01469)) 표 1에 나온 모델 2개(gpt-4o-mini, Llama-3.1-8B-Instruct)를 OpenRouter API와 lm-evaluation-harness 0.4.13으로 KorMedMCQA test 3,009문항에 5-shot 평가한 기록입니다. 이 문서는 Lighteval 태스크의 검증이 아니라, 원본 harness로 모델을 평가한 결과와 그 조건을 남기는 문서입니다. Lighteval과 harness의 문항 단위 비교는 상위 폴더의 `../README.md`를 봅니다. 설계는 `../../design.md`를 봅니다.

## 요약

같은 조건에서 **원본 `kormedmcqa` 태스크**와 **정답 추출 전에 응답을 중단 문자열로 자르는 단계만 추가한 수정 태스크**를 둘 다 돌렸습니다. 이유는 "원본 태스크가 API에서 낮게 나오는 이유"에 있습니다.

| 모델 (가중 평균) | 원본 태스크 | 수정 태스크 | 논문 | 수정 − 논문 |
|---|---|---|---|---|
| gpt-4o-mini | 71.69% | 70.79% | 70.29% | +0.50%p |
| Llama-3.1-8B-Instruct | **30.91%** | 44.70% | 50.85% | -6.15%p |

- Llama의 원본 태스크 점수가 낮은 것은 API 서버가 중단 문자열을 적용하지 않아 응답이 정답 뒤로 이어지기 때문이며, 응답의 98%(2,959/3,009)가 잘려서 달라졌습니다. 모델 능력을 반영한 값이 아닙니다.
- Llama의 논문 대비 격차(수정 태스크 기준 -6.15%p)의 원인은 확인하지 못했습니다.

## 코드와 검증 자료

| 산출물 | 역할 |
|---|---|
| `results.json` | 두 모델의 결과(원본·수정 태스크), 설정, 비용 추정 |
| `make_original_task.py` | 설치된 harness의 `kormedmcqa`를 복사하고 **태스크 이름과 DeepInfra 고정만** 바꾼 `kormedmcqa_orig_*`를 만듦(Llama 원본 실행용) |
| `make_stop_task.py` | 위 복사본에 정답 추출 전 중단 문자열 자르기를 추가한 `kormedmcqa_stop_*`를 만듦 |
| `pin_provider.py` | `kormedmcqa_stop_*`에 OpenRouter 제공 업체(DeepInfra) 고정을 추가(Llama 수정 실행용) |
| `rescore_harness.py` | 검증용. 저장된 샘플을 중단 문자열로 자르고 같은 추출 규칙으로 다시 채점해 harness 점수와 비교 |
| `estimate_cost.py` | 저장된 샘플의 토큰 수 × 공시 단가로 비용을 추정(청구액 아님) |
| `requirements-harness.txt` | 실행 당시 설치된 패키지 목록(`pip freeze`) |

실행 로그, `--log_samples` 폴더(문항 원문·모델 응답 포함), 생성되는 `custom_tasks/`는 올리지 않았습니다. `custom_tasks/`는 만드는 스크립트로 대신합니다.

## 실행 기록

| 항목 | gpt-4o-mini | Llama-3.1-8B-Instruct |
|---|---|---|
| 모델 (OpenRouter) | `openai/gpt-4o-mini` | `meta-llama/llama-3.1-8b-instruct` |
| provider | 고정하지 않음. 실제 제공 업체는 기록하지 못함 | DeepInfra로 고정(`provider.order=[DeepInfra]`, `allow_fallbacks=false`). 양자화는 확인하지 못함 |
| 실행 날짜 | 수정 태스크: 2026-11-20 (07:54 UTC 시작, harness 결과 파일 기록). 원본 태스크: 2026-11-20 | 수정 태스크, 원본 태스크 모두 2026-11-20 (한국 시간). 원본 태스크는 19:51~20:48 사이에 4과목 실행 |
| harness 모델 방식 | `local-chat-completions`, `--apply_chat_template` | `local-completions` (채팅 템플릿 미적용), `tokenized_requests=False` |
| 토크나이저 | 사용 안 함 | `unsloth/Llama-3.1-8B-Instruct` (제3자 복제본, 공식 `meta-llama` 저장소는 승인이 필요해 쓰지 않음). 스냅샷 `4699cc75b550f9c6f3173fb80f4703b62d946aa5` |
| 생성 설정 | 5-shot, temperature 0, `max_gen_toks` 1024, 중단 문자열 `Q:` `</s>` `<\|im_end\|>` `.` 빈 줄 | 같음 |
| 동시 요청 수 | 4 | 4. 단, 원본 태스크 dentist는 연결 끊김으로 한 번 실패해 2로 다시 실행 |
| 문항 | 두 태스크 모두 3,009문항 채점 | 두 태스크 모두 3,009문항 채점 |
| 소요 시간 | 수정 태스크 825초(약 14분, harness 결과 파일의 `total_evaluation_time_seconds`) | 수정 태스크는 과목별 약 4~21분(터미널 로그 기준, DeepInfra의 429 재시도 영향으로 변동). 원본 태스크는 doctor 약 4분만 기록 |
| 비용 (토큰 수 × 공시 단가로 계산한 추정값, 청구액 아님) | 수정 태스크 약 $0.37, 원본 태스크 약 $0.37 | 수정 태스크 약 $0.06, 원본 태스크 약 $0.06 |
| harness | lm-evaluation-harness 0.4.13, 태스크 version 3.0 | 같음 |
| 데이터 | `sean0042/KorMedMCQA` test, revision `79efd6f91edfc8036330d7a4daa88b9f2deb9a82` | 같음 |
| 환경 | Windows 11 Home, Python 3.13.12, CPU(GPU 미사용). 패키지는 `requirements-harness.txt` | 같음 |

- 데이터 revision은 `lm_eval` 옵션으로 고정하지 않았습니다. 실행 시점의 최신본을 받았고, 로컬 Hugging Face 캐시에 스냅샷이 이것 하나뿐이며, `design.md`의 기준 revision과 같습니다. 태스크 version 3.0은 gpt-4o-mini 수정 태스크 실행의 `results_*.json`에서 확인했고 `design.md`의 기준(harness `97a5e2c`, task version 3.0)과 같습니다. 태스크 파일 내용이 `97a5e2c`와 완전히 같은지는 비교하지 않았습니다.

## 결과

정확도(%)와 정답 수입니다. 수정 태스크의 표준오차는 harness가 낸 값(%p), 논문 값은 표 1입니다. 가중 평균은 맞힌 수 합계 / 3,009이며 harness의 그룹 평균(문항 수 가중)과 같은 방식입니다. 원본 태스크의 정답 수는 harness가 낸 정확도에 문항 수를 곱해 구했습니다.

### gpt-4o-mini

| 과목 | 문항 수 | 원본 태스크 | 수정 태스크 | 표준오차(%p) | 논문(%) | 수정 − 논문(%p) | 추출 실패(수정) |
|---|---|---|---|---|---|---|---|
| doctor | 435 | 67.59 (294) | 67.36 (293) | 2.25 | 63.22 | +4.14 | 24 |
| nurse | 878 | 82.23 (722) | 79.73 (700) | 1.36 | 83.14 | -3.41 | 57 |
| pharm | 885 | 70.96 (628) | 70.40 (623) | 1.54 | 71.30 | -0.90 | 102 |
| dentist | 811 | 63.26 (513) | 63.38 (514) | 1.69 | 59.06 | +4.32 | 24 |
| **가중 평균** | 3,009 | **71.69 (2,157)** | **70.79 (2,130)** | 0.83 | 70.29 | +0.50 | 207 |

### Llama-3.1-8B-Instruct

| 과목 | 문항 수 | 원본 태스크 | 수정 태스크 | 표준오차(%p) | 논문(%) | 수정 − 논문(%p) | 추출 실패(수정) |
|---|---|---|---|---|---|---|---|
| doctor | 435 | 37.70 (164) | 34.94 (152) | 2.29 | 40.69 | -5.75 | 0 |
| nurse | 878 | 37.36 (328) | 51.94 (456) | 1.69 | 59.57 | -7.63 | 0 |
| pharm | 885 | 31.41 (278) | 47.91 (424) | 1.68 | 55.25 | -7.34 | 0 |
| dentist | 811 | 19.73 (160) | 38.59 (313) | 1.71 | 42.05 | -3.46 | 0 |
| **가중 평균** | 3,009 | **30.91 (930)** | **44.70 (1,345)** | 0.91 | 50.85 | -6.15 | 0 |

## 해석

- gpt-4o-mini: 가중 평균은 논문과 비슷합니다. 과목별로는 doctor(+4.14)와 dentist(+4.32)가 높고 nurse(-3.41)가 낮으며, 표준오차의 약 2배 수준입니다. 원인은 확인하지 못했습니다. 원본 태스크의 점수(71.69)가 수정 태스크(70.79)보다 높은 것은, 빈 줄 뒤에 정답을 쓴 응답이 원본에서는 인정되기 때문으로 보입니다(추정).
- Llama-3.1-8B-Instruct(수정 태스크): 네 과목 모두 논문보다 3.5~7.6%p 낮고, 평균의 표준오차(0.91%p)로는 설명되지 않습니다. 원인은 확인하지 못했습니다.
- 추출 실패(정답 글자를 찾지 못한 응답)는 오답으로 처리됩니다. gpt-4o-mini 수정 태스크는 207건(6.9%)이었습니다. 대표 유형은 `E입니다`처럼 글자 바로 뒤에 한글이 붙은 응답(정규식의 단어 경계가 인식하지 못함), 정답 글자 없이 설명만 쓴 응답, 설명 뒤에 빈 줄을 두고 글자를 쓴 응답입니다. 207건 전체를 분류하지는 않았습니다. 앞의 한 유형은 팀이 `../README.md`에 적은 harness 정규식의 빈틈(글자 바로 뒤 한글)과 같은 종류입니다.

### Llama 원본 태스크가 낮은 이유

OpenRouter와 DeepInfra는 태스크의 중단 문자열을 적용하지 않았고, harness도 받은 응답을 자르지 않습니다. 모델은 정답 뒤에 다음 문제를 이어서 쓰고, 추출 필터는 처음 일치한 정규식의 **마지막 매치**를 고르므로 정답을 맞혀도 뒤쪽 글자가 선택됩니다. 같은 실행의 응답을 중단 문자열로 자른 뒤 오프라인으로 다시 채점한 결과입니다(`rescore_harness.py results-harness-llama-orig`).

| 과목 | 원본 태스크(harness) | 자른 뒤 재채점 | 자르기로 응답이 달라진 문항 |
|---|---|---|---|
| doctor | 37.70% | 37.70% | 432/435 |
| nurse | 37.36% | 53.08% | 870/878 |
| pharm | 31.41% | 46.55% | 855/885 |
| dentist | 19.73% | 38.96% | 802/811 |
| 전체 | 30.91% | 45.13% | 2,959/3,009 |

pharm은 데이터의 `subject` 라벨이 `pharm`(614)과 `pharmacy`(271)로 나뉘어 있어 합친 값입니다.

### 같은 설정으로 다시 실행했을 때의 차이

원본 태스크 실행의 응답을 수정 태스크와 같은 규칙(자르기 + 같은 추출)으로 채점한 결과는, 최종 수정 태스크 실행과 같은 설정(DeepInfra 고정, 1,024토큰)인데도 문항 수준에서 다릅니다.

| 과목 | 재채점 정답 수(원본 실행의 응답) | 수정 태스크 정답 수(최종) | 차이 |
|---|---|---|---|
| doctor | 164 | 152 | +12 |
| nurse | 466 | 456 | +10 |
| pharm | 412 | 424 | -12 |
| dentist | 316 | 313 | +3 |
| 전체 | 1,358 (45.13%) | 1,345 (44.70%) | +13 |

temperature 0이어도 실행마다 응답이 달라지고, 과목 단위로는 10문항 이상 차이가 납니다. doctor만 원본 태스크가 수정 태스크보다 높게 나온 것도 이 실행 간 차이 때문으로 보입니다(같은 자르기 규칙을 적용하면 두 실행의 doctor 점수는 37.70%와 34.94%로, 자르기가 원인은 아님). 이 차이의 원인(제공 업체 내부 변동 등)은 확인하지 못했습니다.

## 원본 harness와 다른 점

설치된 harness의 `kormedmcqa`와 다른 점입니다.

1. **수정 태스크는 정답 추출 전에 중단 문자열로 자르는 단계를 추가했습니다**(이유는 위 "Llama 원본 태스크가 낮은 이유"). 설치된 harness 코드 기준으로, 채팅 방식은 중단 문자열 앞 4개만 서버로 보내고 빈 줄(`\n\n`)은 보내지 않으며, 두 방식 모두 harness 쪽에서 응답을 자르지 않습니다.
2. Llama는 요청 본문에 `provider`(DeepInfra, 대체 업체 금지)를 넣었습니다. 수정 태스크는 `pin_provider.py`, 원본 태스크는 `make_original_task.py`가 넣습니다. 이 외에 원본 태스크의 파일은 설치된 원본과 같습니다(`diff`로 확인: 태스크 이름과 `provider` 설정만 다름).
3. gpt-4o-mini는 채팅 API라서 채팅 템플릿을 적용했습니다. 팀의 Qwen 비교 실행(채팅 템플릿 끔)과 조건이 다릅니다. harness 기본값(`fewshot_as_multiturn`)으로 few-shot 예시 5개와 문제가 user 메시지 6개로 전달되었습니다(저장된 샘플에서 확인).

## 확인 범위

- 확인한 것: 두 모델 모두 두 태스크에서 네 과목의 문항 수가 435 / 878 / 885 / 811로 맞고 합계가 3,009입니다. 수정 태스크의 harness 점수와 `rescore_harness.py`의 재채점 점수가 모든 과목에서 일치합니다(같은 자르기·추출 규칙을 독립적으로 적용). 원본 태스크 복사본(`kormedmcqa_orig_*`)은 설치된 원본과 `diff`로 비교해 차이가 태스크 이름과 `provider` 설정뿐임을 확인했습니다.
- 하지 않은 것: 중단 문자열이 적용되는 환경(로컬 모델)에서 수정 태스크가 원본 태스크와 같은 점수를 내는지(원본과 수정의 차이가 자르기 단계 하나뿐이라는 점에서 같을 것으로 추정하지만 실행으로 확인하지 못함), gpt-4o-mini 추출 실패 207건의 전체 분류, 다른 제공 업체나 반복 실행, DeepInfra 모델의 정밀도와 논문 시점 모델 버전이 같은지, 토크나이저 복제본이 점수에 주는 영향(`tokenized_requests=False`라 작을 것으로 추정하지만 확인되지 않음).

## 재현

PowerShell 기준입니다. 키는 환경 변수로만 넘기고 코드, 파일, 로그에 남기지 않습니다. **harness는 요청 실패(429 등) 시 오류 로그에 `Authorization` 헤더(키)를 그대로 출력하므로, 터미널 로그를 공유하거나 저장소에 올리지 않습니다.** 이 폴더의 스크립트는 현재 폴더에 `custom_tasks\`를 만들므로, 레포 밖에 작업 폴더를 따로 만들어 실행합니다.

```powershell
# 1. 작업 폴더, 스크립트 복사, 설치 (requirements-harness.txt는 실행 당시 환경의 기록이며, 아래 설치만으로도 실행됨)
mkdir work; cd work
copy <레포 경로>\teams\team-d-kormedmcqa\validation\openrouter-harness\*.py .
pip install lm-eval==0.4.13 tenacity aiohttp tqdm requests
$env:OPENAI_API_KEY = "<OpenRouter 키>"

# 2. 태스크 복사본 만들기 (설치된 kormedmcqa를 복사해 custom_tasks 아래에 생성)
python make_stop_task.py       # custom_tasks\kormedmcqa_stop (수정 태스크)
python make_original_task.py   # custom_tasks\kormedmcqa_orig (원본 + DeepInfra 고정)

# 3. gpt-4o-mini, 수정 태스크 (제공 업체를 고정하지 않으므로 4번보다 먼저 실행)
lm_eval --model local-chat-completions --model_args model=openai/gpt-4o-mini,base_url=https://openrouter.ai/api/v1/chat/completions,num_concurrent=4 --apply_chat_template --include_path custom_tasks\kormedmcqa_stop --tasks kormedmcqa_stop_doctor,kormedmcqa_stop_nurse,kormedmcqa_stop_pharm,kormedmcqa_stop_dentist --num_fewshot 5 --log_samples --output_path results-harness-gpt-stop

# 3b. gpt-4o-mini, 원본 태스크 (설치된 내장 태스크 그대로)
lm_eval --model local-chat-completions --model_args model=openai/gpt-4o-mini,base_url=https://openrouter.ai/api/v1/chat/completions,num_concurrent=4 --apply_chat_template --tasks kormedmcqa_doctor,kormedmcqa_nurse,kormedmcqa_pharm,kormedmcqa_dentist --num_fewshot 5 --log_samples --output_path results-harness-gpt-full

# 4. Llama용 제공 업체 고정 (수정 태스크 전체에 적용되므로 gpt 수정 태스크 실행 뒤에)
python pin_provider.py

# 5. Llama-3.1-8B-Instruct, 수정 태스크 (과목별로 나누어 실행했고, 한 번에 네 과목을 --tasks에 넣어도 됨)
lm_eval --model local-completions --model_args model=meta-llama/llama-3.1-8b-instruct,base_url=https://openrouter.ai/api/v1/completions,num_concurrent=4,tokenized_requests=False,tokenizer=unsloth/Llama-3.1-8B-Instruct --include_path custom_tasks\kormedmcqa_stop --tasks kormedmcqa_stop_doctor --num_fewshot 5 --log_samples --output_path results-harness-llama-final
# --tasks를 kormedmcqa_stop_nurse, kormedmcqa_stop_pharm, kormedmcqa_stop_dentist로 바꿔 같은 방식으로 실행

# 5b. Llama-3.1-8B-Instruct, 원본 태스크 (제공 업체 고정은 make_original_task.py가 넣어 둠)
lm_eval --model local-completions --model_args model=meta-llama/llama-3.1-8b-instruct,base_url=https://openrouter.ai/api/v1/completions,num_concurrent=4,tokenized_requests=False,tokenizer=unsloth/Llama-3.1-8B-Instruct --include_path custom_tasks\kormedmcqa_orig --tasks kormedmcqa_orig_doctor --num_fewshot 5 --log_samples --output_path results-harness-llama-orig
# --tasks를 kormedmcqa_orig_nurse, kormedmcqa_orig_pharm, kormedmcqa_orig_dentist로 바꿔 같은 방식으로 실행

# 6. 검증 (문항 수, 추출 실패 수, harness 점수와 자른 뒤 재채점 점수 비교)
python rescore_harness.py results-harness-gpt-stop
python rescore_harness.py results-harness-llama-final
python rescore_harness.py results-harness-llama-orig

# 7. 비용 추정 (pip install tiktoken 필요, 추정값이며 청구액이 아님)
python estimate_cost.py --gpt results-harness-gpt-stop --llama results-harness-llama-final
python estimate_cost.py --gpt results-harness-gpt-full --llama results-harness-llama-orig
```

`<레포 경로>`와 `<OpenRouter 키>`는 자리 표시자이므로 실제 값으로 바꿔 입력합니다.
