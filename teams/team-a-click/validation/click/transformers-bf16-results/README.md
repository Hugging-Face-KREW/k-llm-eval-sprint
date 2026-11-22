# CLIcK Qwen3.8 · Kanana2 Transformers BF16 결과

12개 전체 평가 완료. 입력·채점 감사 PASS. 프레임워크 간 예측 일치 여부는 아래 비교표에 별도 표시한다.

| 모델 | 조건 | 정답/문항 | acc | acc_norm |
|---|---|---:|---:|---:|
| kanana2-3b | lighteval_full | 752/1995 | 0.376942 | — |
| kanana2-3b | aligned_harness_full | 794/1995 | 0.397995 | — |
| kanana2-3b | base_letter | 1042/1995 | 0.522306 | 0.522306 |
| kanana2-3b | pr4420_letter | 1053/1995 | 0.527820 | 0.527820 |
| kanana2-3b | base_full | 776/1995 | 0.388972 | 0.427068 |
| kanana2-3b | pr4420_full | 775/1995 | 0.388471 | 0.424561 |
| qwen38-27b | lighteval_full | 1396/1995 | 0.699749 | — |
| qwen38-27b | aligned_harness_full | 1404/1995 | 0.703759 | — |
| qwen38-27b | base_letter | 1449/1995 | 0.726316 | 0.726316 |
| qwen38-27b | pr4420_letter | 1481/1995 | 0.742356 | 0.742356 |
| qwen38-27b | base_full | 1375/1995 | 0.689223 | 0.678195 |
| qwen38-27b | pr4420_full | 1396/1995 | 0.699749 | 0.688722 |

| 모델 | 비교 | 같은 예측/문항 | 최대 logprob 차이 |
|---|---|---:|---:|
| kanana2-3b | lighteval_full_vs_aligned_harness_full | 1746/1995 | 5.875 |
| kanana2-3b | base_letter_vs_pr4420_letter | 1739/1739 | 0 |
| kanana2-3b | base_full_vs_pr4420_full | 1739/1739 | 0 |
| qwen38-27b | lighteval_full_vs_aligned_harness_full | 1943/1995 | 10.75 |
| qwen38-27b | base_letter_vs_pr4420_letter | 1720/1739 | 0.90625 |
| qwen38-27b | base_full_vs_pr4420_full | 1739/1739 | 0 |

공식 어댑터의 배치·padding·log_softmax·합산을 유지했다. BF16 수치 차이를 일치한 것으로 처리하지 않았다. 입력 정렬 harness와 native pr4420_full은 다른 조건이다. 과거 Polyglot은 Transformers/FP32이므로 정밀도까지 동일한 비교는 아니다. 논문의 지시문 3종 × 보기 순환 평균을 재현한 결과도 아니다.
