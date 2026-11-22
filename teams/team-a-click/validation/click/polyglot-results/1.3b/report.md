# CLIcK Polyglot-Ko 1.3b 검증

상태: **PASS**. Native Python API 비교이며 CLI 전체 실행 검증은 아닙니다.

| 분야 | 문항 | Lighteval | 하네스 | 예측 일치 | 논문 (%) | 논문 대비 차이 (%p) |
|---|---:|---:|---:|---:|---:|---:|
| economy | 59 | 38.9831% | 38.9831% | 59 | 42.54 | -3.5569 |
| functional | 133 | 15.7895% | 15.7895% | 133 | 23.77 | -7.9805 |
| geography | 131 | 35.8779% | 35.8779% | 131 | 30.18 | +5.6979 |
| grammar | 232 | 21.5517% | 21.5517% | 232 | 21.87 | -0.3183 |
| history | 280 | 23.2143% | 23.2143% | 280 | 26.30 | -3.0857 |
| law | 219 | 30.5936% | 30.5936% | 219 | 38.44 | -7.8464 |
| politics | 84 | 39.2857% | 39.2857% | 84 | 30.53 | +8.7557 |
| popular | 41 | 36.5854% | 36.5854% | 41 | 29.77 | +6.8154 |
| society | 309 | 44.6602% | 44.6602% | 309 | 34.69 | +9.9702 |
| textual | 285 | 22.1053% | 22.1053% | 285 | 23.44 | -1.3347 |
| tradition | 222 | 34.6847% | 34.6847% | 222 | 32.48 | +2.2047 |

## 집계

```json
{
  "all_micro": {
    "items": 1995,
    "lighteval_correct": 599,
    "harness_correct": 599,
    "lighteval_accuracy": 0.30025062656641605,
    "harness_accuracy": 0.30025062656641605,
    "same_prediction": 1995,
    "max_abs_diff": 0.0001888275146484375
  },
  "culture_micro": {
    "items": 1345,
    "lighteval_correct": 465,
    "harness_correct": 465,
    "lighteval_accuracy": 0.34572490706319703,
    "harness_accuracy": 0.34572490706319703,
    "same_prediction": 1345,
    "max_abs_diff": 0.0001811981201171875
  },
  "language_micro": {
    "items": 650,
    "lighteval_correct": 134,
    "harness_correct": 134,
    "lighteval_accuracy": 0.20615384615384616,
    "harness_accuracy": 0.20615384615384616,
    "same_prediction": 650,
    "max_abs_diff": 0.0001888275146484375
  },
  "category_macro": {
    "lighteval_accuracy": 0.3121192967654094,
    "harness_accuracy": 0.3121192967654094
  }
}
```

설명되지 않은 예측/점수 불일치: 0건. 상세는 summary.json의 mismatches에 있습니다.

논문 출처: https://arxiv.org/html/2403.06412v2#S4.T5
논문은 지시문 3종과 보기 순환을 사용합니다. 이 실험은 0-shot·단일 지시문·원본 순서이므로 참고 비교입니다.
논문의 Average와 자체 micro/macro를 같은 산식으로 가정하지 않습니다. 수치가 다르다는 것만으로 구현 오류나 개선을 단정하지 않습니다.

실행 설정·환경·revision·허용오차·결과 해시는 summary.json에 기록했습니다. 원문 및 토큰을 포함하는 inputs.jsonl은 공개하지 않습니다.
