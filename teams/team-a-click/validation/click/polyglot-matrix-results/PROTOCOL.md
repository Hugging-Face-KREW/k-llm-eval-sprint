# 공통 평가 조건과 검증 범위

[8개 결과와 상세 보고서](README.md)

## 평가 도구 구분

| 구분 | 도구 | 이 보고서에서의 역할 |
|---|---|---|
| 새 8개 모델·조건 결과 | **lm-evaluation-harness** (`lm-eval`) | base/pr4420 × letter/full 전체 평가 |
| 이전 실행 참고값 | **Lighteval** | 이전에 별도로 실행한 결과를 재사용 |
| 이전 실행 참고값 | **lm-evaluation-harness (입력 정렬)** | 프롬프트·분야 분류를 Lighteval에 맞춘 이전 결과를 재사용 |
| 파일럿 검산 | 독립 forward 코드 | lm-evaluation-harness 점수와 대조하는 검산 경로; Lighteval이 아님 |

새 8개 결과는 모두 lm-evaluation-harness의 native Python API 경로입니다. Lighteval을 새 8개 조건의 평가 도구로 사용하지 않았습니다.

## 목적과 채점 정의

같은 두 모델에서 5지선다 버그 수정 효과와 후보 문자열 변경 효과를 분리합니다. 지시문은 지문 유무에 따른 원래 한 종류를 사용하며 보기 순서는 고정합니다.
`acc`는 후보 토큰의 로그확률 합이 최대인 보기를 고릅니다. `acc_norm`은 그 합을 target delimiter를 제외한 후보 문자열의 Python Unicode 문자 수로 나눈 후 보기를 고르는 별도 지표입니다. 토큰 수 정규화가 아닙니다.

## 고정 소스

| 대상 | revision |
|---|---|
| CLIcK 데이터 | `d61627859645b5e6edc03fd9f835735d8226fa4e` |
| lm-evaluation-harness base 태스크 | `d6de81643928d653435c431bae19945d41d32520` |
| lm-evaluation-harness pr4420 태스크 | `7a7b48afa7c294a5992008053bd1ec0042906c6d` |
| Polyglot-Ko 1.3B | `557e162cf6e944fdbae05bab2e45d066a125eacb` |
| Polyglot-Ko 12.8B | `09dfc839067bf44e7f52976eca8adbc17f04e1b0` |

실제 추론 core는 #4420 revision을 사용했고, 두 commit 사이의 변경이 CLIcK 하위 8파일뿐이며 core가 같음을 확인했습니다. 두 버전의 원래 태스크 파일 bytes를 각각 독립 스냅샷으로 로드했습니다.
lm-evaluation-harness native YAML의 `ConfigurableTask`·`process_docs`·`fewshot_context`·`construct_requests`·`HFLM.loglikelihood`·filter·`process_results`를 사용했습니다.
고정 원본 1,995행을 같은 필드·내용의 private JSON train split으로 전달하는 데이터 전송용 override가 있습니다. 원래 필터·프롬프트·후보·metric은 그대로 유지하고 전체 행의 원본 연결을 검증했습니다.
full 조건은 후보 문자열을 `A. 보기 원문`으로 바꾸고 정답 라벨을 원래 후보 인덱스로 바꿨습니다. 원래 delimiter가 공백 하나이므로 실제 continuation은 ` A. 보기 원문`입니다.

## 데이터와 집계

- 26파일·1,995행, 4지선다 1,739·5지선다 256·정답 E 49문항입니다.
- 데이터 revision + 원본 파일 경로 + 0-based 행 번호를 키로 삼아 중복 ID를 보존합니다.
- Native ID 필터는 Grammar 233 / Functional 132문항이며, 원본 파일은 Grammar 232 / Functional 133문항입니다. `Functional_CSAT.json#82` 한 행이 native에서는 Grammar로 분류됩니다.
- 두 분야 기준을 모두 보고합니다. 전체 micro는 정답 수/1,995, 문화/언어 micro는 각 1,345/650문항, macro는 분야 정확도 11개의 단순 평균입니다.

## 모델 실행 설정

- NVIDIA A100X 80GB 한 장, `tailab:0.0.1` Docker와 전용 venv 사용. 호스트 전역환경 변경 없음.
- FP32, eager attention, TF32 off, 후보별 batch 1, seed 1234, 문맥 한도 2,048.
- 0-shot, chat template·양자화·BOS/EOS 추가·잘림·logits cache 없음.
- 모델 하나를 유지하며 네 조건을 순차 실행하고 모델 가중치의 변경·학습 상태·입력 토큰을 검사했습니다.
- 실행 기간: 2026-11-11 20:16:52 ~ 2026-11-12 02:31:41 KST. 종료 코드 0.

| 환경 | 버전 |
|---|---|
| Python | 3.12.16 |
| torch | 2.14.1+cu126 |
| transformers | 5.20.1 |
| tokenizers | 0.23.3 |
| datasets | 5.1.0 |
| huggingface-hub | 1.33.0 |
| accelerate | 1.15.0 |
| numpy | 2.5.4 |
| lighteval | 0.13.1.dev0 |
| lm-eval | 0.4.14.dev0 |

위 표는 설치 환경 목록입니다. `lighteval`은 이전 비교에서 사용한 패키지이며, 새 8개 결과를 계산한 평가 도구는 `lm-eval`(lm-evaluation-harness)입니다.

## 검증

1. 전체 native loader coverage·원본 해시·후보 개수·gold 매핑을 검사했습니다. 각 조건은 1,995행을 정확히 한 번 평가합니다.
2. 두 tokenizer의 context/continuation 경계 불일치가 0건입니다. 조건별 최대 길이는 base_letter 1,795 / pr4420_letter 1,844 / base_full 1,847 / pr4420_full 1,896토큰입니다.
3. 기존 120개 + 신규 21개 테스트와 GPU random GPTNeoX의 8문항 × 4조건 검산이 통과했습니다. 무작위 모델 결과는 benchmark 정확도가 아닙니다.
4. calibration 55문항, 별도 validation 72문항을 추론 전에 동결했습니다. 조건 내부 native/독립 forward의 calibration 최대 오차는 0, atol은 max(1e-6, 최대 오차 × 2)=1e-6, rtol=0입니다. validation에서 허용오차를 확대하지 않았습니다.
5. 모든 파일럿 통과 후 전체를 실행했습니다. 각 모델에서 같은 채점 방식의 기존/수정 버전 4지선다 점수·예측이 정확히 일치했습니다. 서로 다른 조건의 예측 차이는 측정 대상입니다.
6. 전체 15,960행의 완전성·정답·집계와 회수 파일 79개의 SHA256을 확인했습니다.

## 실행 및 결과 식별

- Docker 이미지 ID: `sha256:512b50ba045fd9834c0876c06279824db294a1318c545560279b82392c9ab2cd`
- 실행 코드 SHA256: `25889d47475a56f5e7d3852f364839fefe342359e32dd042c792905b67000e6b`
- 원본 통합 요약 SHA256: `523551265bdeec4bb184edb5aa631594954383c7c75f4620333347127d23b194`
- 회수 archive SHA256: `ca6d9ce2af8aa096b4bf97411e3e7a3d05c838feb4cf8ffb2e64a38c56fa6782`

조건별 원본 결과·파일럿·protocol 해시는 각 상세 보고서와 results.json에 있습니다.
당시 준비된 컨테이너에서 사용한 명령은 다음과 같습니다.

```bash
/workspace/bin/native-env bash /workspace/code/teams/team-a-click/validation/click/polyglot_matrix_run.sh
```

이는 실행 기록입니다. 이 보고서 PR에는 평가 실행기가 포함되지 않으므로 위 명령만으로 새 환경에서 재실행할 수 있는 패키지는 아닙니다. 원문·토큰·문항별 로그는 비공개 검증 자료로 보존합니다.

## 해석의 한계

- lm-evaluation-harness native Python API 경로를 검증했습니다. 전체 CLI 실행 동등성 검증은 포함하지 않습니다.
- 논문의 지시문 3종 × 보기 순환 평가를 재현하지 않았습니다.
- 원래 base의 프롬프트 E 누락을 유지합니다. base_full도 보이지 않은 E의 원문을 후보로 채점할 수 있습니다.
- 이전 Lighteval 정렬 실험은 첫 A: 공백·분야 필터가 달라 새 pr4420_full과 동일 조건이 아닙니다.
- 정확도 차이만으로 버그 수정의 타당성, 모든 문항 유형의 개선, 모델의 일반적 우열을 판단하지 않습니다.
