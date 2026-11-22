# CLIcK Polyglot-Ko 12.8b 검증

상태: **PASS**. Native Python API 비교이며 CLI 전체 실행 검증은 아닙니다.

| 분야 | 문항 | Lighteval | 하네스 | 예측 일치 | 논문 (%) | 논문 대비 차이 (%p) |
|---|---:|---:|---:|---:|---:|---:|
| economy | 59 | 33.8983% | 33.8983% | 59 | 45.03 | -11.1317 |
| functional | 133 | 12.0301% | 12.0301% | 133 | 19.84 | -7.8099 |
| geography | 131 | 27.4809% | 27.4809% | 131 | 30.12 | -2.6391 |
| grammar | 232 | 25.8621% | 25.8621% | 232 | 23.05 | +2.8121 |
| history | 280 | 25.7143% | 25.7143% | 280 | 24.43 | +1.2843 |
| law | 219 | 25.1142% | 25.1142% | 219 | 43.44 | -18.3258 |
| politics | 84 | 27.3810% | 27.3810% | 84 | 27.15 | +0.2310 |
| popular | 41 | 9.7561% | 9.7561% | 41 | 29.59 | -19.8339 |
| society | 309 | 30.7443% | 30.7443% | 309 | 37.37 | -6.6257 |
| textual | 285 | 21.0526% | 21.0526% | 285 | 22.96 | -1.9074 |
| tradition | 222 | 26.1261% | 26.1261% | 222 | 33.96 | -7.8339 |

## 집계

```json
{
  "all_micro": {
    "items": 1995,
    "lighteval_correct": 499,
    "harness_correct": 499,
    "lighteval_accuracy": 0.25012531328320803,
    "harness_accuracy": 0.25012531328320803,
    "same_prediction": 1995,
    "max_abs_diff": 0.00012969970703125
  },
  "culture_micro": {
    "items": 1345,
    "lighteval_correct": 363,
    "harness_correct": 363,
    "lighteval_accuracy": 0.2698884758364312,
    "harness_accuracy": 0.2698884758364312,
    "same_prediction": 1345,
    "max_abs_diff": 0.000110626220703125
  },
  "language_micro": {
    "items": 650,
    "lighteval_correct": 136,
    "harness_correct": 136,
    "lighteval_accuracy": 0.20923076923076922,
    "harness_accuracy": 0.20923076923076922,
    "same_prediction": 650,
    "max_abs_diff": 0.00012969970703125
  },
  "category_macro": {
    "lighteval_accuracy": 0.24105450040979576,
    "harness_accuracy": 0.24105450040979576
  }
}
```

설명되지 않은 예측/점수 불일치: 0건. 상세는 summary.json의 mismatches에 있습니다.

논문 출처: https://arxiv.org/html/2403.06412v2#S4.T5
논문은 지시문 3종과 보기 순환을 사용합니다. 이 실험은 0-shot·단일 지시문·원본 순서이므로 참고 비교입니다.
논문의 Average와 자체 micro/macro를 같은 산식으로 가정하지 않습니다. 수치가 다르다는 것만으로 구현 오류나 개선을 단정하지 않습니다.

실행 설정·환경·revision·허용오차·결과 해시는 summary.json에 기록했습니다. 원문 및 토큰을 포함하는 inputs.jsonl은 공개하지 않습니다.
