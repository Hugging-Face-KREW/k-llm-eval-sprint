Title: [EVAL] Add HRM8K (Korean)

## Evaluation short description
- Why is this evaluation interesting? HRM8K is a Korean–English parallel math benchmark (8,011 problems in 5 subsets). The model solves each Korean problem and writes a final answer, and accuracy is computed on that answer. lighteval has no Korean math reasoning task yet (`mgsm` has no Korean split). The KSM subset (1,428 problems) comes from original Korean exams and olympiads.
- How used is it in the community? lm-evaluation-harness has shipped it as `hrm8k` and `hrm8k_en` since January 2025, and the dataset owner's toolkit (HAE-RAE HRET) also supports it. On the Hub the dataset has 6,357 downloads in the last 30 days and 36,675 in total (checked on 2026-10-18).

## Evaluation metadata
- Paper url: https://arxiv.org/abs/2501.02448
- Github url: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/hrm8k (reference implementation; the authors have not released evaluation code)
- Dataset url: https://huggingface.co/datasets/HAERAE-HUB/HRM8K (MIT, not gated; configs `GSM8K`, `MATH`, `OMNI_MATH`, `MMMLU`, `KSM`; split `test`; revision `c360cabf8d733a82455565358b3dc965aab9ba8d`)

## Official evaluation protocol
- Generative, 0-shot, final answer in `\boxed{N}`. Accuracy per subset and the unweighted mean of the five subsets (paper Appendix B and G).
- The paper uses an English instruction plus "Respond in Korean" and samples at temperature 0.7. It does not say how the answer is extracted.
- lm-eval `hrm8k` uses a Korean instruction, greedy decoding, and string match after MATH normalization.
- Reported scores (paper Table 9, K2K, mean of the five subsets): Qwen2.5-1.5B-Instruct 15.95, Qwen2.5-7B-Instruct 39.52, Llama-3.2-1B-Instruct 7.28.

## Proposed implementation
- File: `src/lighteval/tasks/tasks/hrm8k.py`, tasks `hrm8k:gsm8k`, `hrm8k:math`, `hrm8k:omni_math`, `hrm8k:mmmlu`, `hrm8k:ksm`. Lighteval's `hrm8k:_average` then equals the paper's unweighted mean.
- Prompt and generation follow lm-eval `hrm8k`: Korean instruction (MMMLU asks for the option number), 0-shot, greedy, `generation_size=2048`, no `"\n"` stop sequence.
- Metric: `MultilingualExtractiveMatchMetric`, `\boxed{}` first. `answer` is numeric in four configs and a string in KSM (222 LaTeX expressions such as `-8\pi`), so golds are wrapped in `$…$` and parsed as an expression or LaTeX. Values are compared with sympy at `precision=5`, so `0.5` matches `\frac{1}{2}`.
  - Fallback: if no `\boxed{}` is found, we fall back to the last number, as lm-eval does. With a 135M model the fallback picked a number copied from the question, so we will report how often it is used.
- Validation: per-item comparison with lm-eval `hrm8k` on the same model and settings, with the paper's numbers as a secondary reference.

We wrote every gold inside `\boxed{}` as a synthetic "perfect" answer and counted how often each scorer accepts it:

| Scorer | GSM8K | MATH | OMNI_MATH | MMMLU | KSM |
|---|---:|---:|---:|---:|---:|
| lm-eval `hrm8k` | 99.8% | 100% | 100% | 100% | 83.6% |
| lighteval `expr_gold_metric` | 100% | 100% | 100% | 100% | 97.1% |
| proposed | 100% | 100% | 100% | 100% | 99.9% |

Script to reproduce this table: https://github.com/dw021213/hrm8k-lighteval-experiments/blob/c994677a3a41a8e5e841f0046e26b18214ad8275/e2_perfect.py

lm-eval also runs its extractor on the gold, so `-10` becomes `10` and `\frac{1}{2}` becomes `2`, and 236 items can never match. The one KSM miss of the proposed scorer is a malformed gold.

## Questions for maintainers
1. **Prompt:** is it fine to follow lm-eval's Korean instruction rather than the paper's English one, so that the two tools can be compared item by item?
2. **Decoding:** is greedy fine as the default, like lm-eval? The paper sampled once at temperature 0.7.
3. **Data errors:** KSM rows 3, 109, 201 and 1427 have wrong or malformed golds, and rows 1254 and 1262 look wrong too (checks are in the repo above). We plan to keep the data as is with a pinned revision, list these rows in the task docstring, and report them to the dataset owners. Is that fine?
