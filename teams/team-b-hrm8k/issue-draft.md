<!--
팀 메모: AI 도구로 정리한 초안이다. docs/ai-tools.md에 따라 그대로 게시하지 않는다.
10/18 세션에서 팀이 직접 다시 쓰고, 질문 1–2의 우리 의견을 정한 뒤 올린다.
수치 근거: analysis.md 5-4, 8, 9번.
-->

Title: [EVAL] Add HRM8K (Korean)

## What it measures
HRM8K is a Korean–English parallel math benchmark (8,011 problems in 5 subsets). The model solves each problem and writes a final answer, and accuracy is computed on that answer. The paper uses it to study why models score lower on Korean math problems than on the same problems in English.

- Why is this evaluation interesting? lighteval has no Korean math reasoning task. `mgsm` has no Korean split. Korean appears only in multilingual or translated sets (`openai_mmlu`, `global_mmlu`, `mkqa`, `paws_x`, `tydiqa`), and none of them is math reasoning. The KSM subset (1,428 problems) is taken from original Korean exams and olympiads.
- How used is it in the community? lm-evaluation-harness has shipped `hrm8k` and `hrm8k_en` since January 2025. The dataset owner's toolkit (HAE-RAE HRET) and the W&B Korean LLM leaderboard also include it.

## Dataset
- HF: `HAERAE-HUB/HRM8K` (configs: `GSM8K`, `MATH`, `OMNI_MATH`, `MMMLU`, `KSM`; split: `test` only; revision `c360cabf8d733a82455565358b3dc965aab9ba8d`)
- License: MIT, gated: no
- The `answer` type differs by config:
  - float64 in GSM8K and MATH (all values are integers)
  - int64 in OMNI_MATH, and in MMMLU where it is the option number 1–4
  - string in KSM, including 222 LaTeX expressions such as `-8\pi` and `\frac{1}{6}`

## Official evaluation protocol
- Paper: https://arxiv.org/abs/2501.02448 (Appendix B and G)
- Format: generative + answer extraction from `\boxed{N}`, 0-shot. English instruction plus "Respond in Korean." for the Korean setting (K2K). Sampling with temperature 0.7, top_p 0.95, up to 2,048 tokens. Metric: accuracy per subset and the unweighted mean of the five subsets.
- The paper does not specify how the answer is extracted or normalized, and no official code has been released. The lm-evaluation-harness `hrm8k` task (community contribution) is the de facto reference. It uses greedy decoding, a Korean-language instruction, and Hendrycks-MATH-style string matching.
- Reported scores (paper Table 9, K2K; GSM8K / MATH / OMNI_MATH / MMMLU / KSM → mean):
  - Qwen2.5-1.5B-Instruct: 28.13 / 20.69 / 8.64 / 18.51 / 3.78 → 15.95
  - Llama-3.2-1B-Instruct: 7.88 / 10.50 / 4.77 / 10.43 / 2.80 → 7.28
  - Qwen2.5-7B-Instruct: 66.41 / 50.36 / 18.96 / 50.00 / 11.83 → 39.52

## Proposed implementation
- File: `src/lighteval/tasks/tasks/hrm8k.py`
- Tasks: `hrm8k:gsm8k`, `hrm8k:math`, `hrm8k:omni_math`, `hrm8k:mmmlu`, `hrm8k:ksm`. Then `hrm8k|0` runs all five, and lighteval's `hrm8k:_average` is the same unweighted mean the paper reports.
- Prompt: the Korean instruction used by lm-eval `hrm8k` (with its MMMLU-specific wording), so the two tools can be compared item by item.
- Generation: 0-shot, greedy (lighteval's default temperature 0, as in lm-eval), `generation_size=2048`, no `"\n"` stop sequence (it would cut the reasoning). The paper's sampling (temperature 0.7, top_p 0.95) can still be run through `generation_parameters`.
- Metric: the existing `MultilingualExtractiveMatchMetric`.
  - Gold: wrapped in `$…$` and parsed with `ExprExtractionConfig` + `LatexExtractionConfig`.
  - Prediction: `LatexExtractionConfig(boxed_match_priority=0)` + `ExprExtractionConfig`.
  - Comparison: `precision=5`.
  - Integer-valued float golds are written as integers. Golds are never round-tripped through `float()`, because OMNI_MATH contains 66071772829247409.
- Dataset revision pinned.
- MMMLU: scored generatively like the other four subsets, as the paper and lm-eval do. The model writes the option number in `\boxed{}` (lm-eval's MMMLU-specific instruction). We also tried option log-likelihood scoring on the same items, but it would not match the paper and would duplicate `openai_mmlu_kor_*`.

A check we ran without any model: for every item we wrote the gold itself inside `\boxed{}` and counted how often each scorer accepts this synthetic "perfect" answer.

| Scorer | GSM8K | MATH | OMNI_MATH | MMMLU | KSM |
|---|---:|---:|---:|---:|---:|
| lm-eval `hrm8k` | 99.8% | 100% | 100% | 100% | 83.6% |
| lighteval `expr_gold_metric` | 100% | 100% | 100% | 100% | 97.1% |
| proposed (gold parsed as LaTeX + expression) | 100% | 100% | 100% | 100% | 99.9% |

- This check only tests whether a scorer can read each gold. It cannot catch a gold that is readable but wrong. The one KSM item that fails is a malformed gold (`\frac[13}{20}`); the golds that are wrong are listed in question 4.
- lm-eval runs its answer extractor on the gold as well, so golds like `-10` and `\frac{1}{2}` become `10` and `2` and can never match (236 items). Our KSM numbers will therefore differ from lm-eval's by design. We plan to publish a per-item comparison of the two scorers on the same model outputs.

## Questions for maintainers
1. **Prompt:** we propose lm-eval's Korean instruction, because this is a Korean benchmark and it lets us compare with lm-eval item by item. The paper's prompt (English instruction + "Respond in Korean") would be closer to the paper's numbers. Is lm-eval's prompt fine as the default? lm-eval also ships `hrm8k_en`, separate tasks that use the English parallel text (`original` column); we plan to keep this PR Korean-only.
2. **Decoding:** we propose greedy as the default. It gives the same output on every run, so one run is enough to reproduce a score. It also matches lm-eval `hrm8k`, which allows an item-by-item comparison, and it is lighteval's default (temperature 0). The paper's numbers come from a single sampled run (temperature 0.7, top_p 0.95), so they cannot be reproduced exactly anyway, and that setting can still be run through `generation_parameters`. Is greedy fine as the default?
3. **Korean literals:** `MultilingualExtractiveMatchMetric(language=Language.KOREAN)` currently raises `AttributeError`, because the Korean `answer`, `and_word` and `or_word` literals are missing. #1179 adds some of them. Is it fine to keep `Language.ENGLISH` here, since we rely on `\boxed{}`, or would you prefer that we complete the Korean literals in a separate PR first?
4. **Data errors:** four KSM golds are wrong or malformed (rows 3, 109, 201 and 1427), two more look wrong (rows 1254 and 1262), and row 323 has a mismatched `original_answer`. Our plan is to keep the data as is with a pinned revision, list the rows in the task docstring, and report them on the dataset's Community tab. Is that acceptable?
5. **Overlap:** the MMMLU subset contains the same 470 questions as `openai_mmlu_kor` (abstract algebra, college and high school mathematics). We would like to keep it: the paper's five-subset average needs it, and here it is scored from a generated solution and `\boxed{}` answer, while `openai_mmlu_kor` compares option log-likelihoods. Is that fine? Also, at `c2af9e5` the `openai_mmlu_kor_*` tasks fail while building the prompt (`AttributeError`, because the Korean `answer` and `question_word` literals are missing; see #1179), so Korean MMMLU cannot be run in lighteval today. If log-likelihood scoring of Korean MMMLU is useful, we could instead send a small separate PR that completes the Korean literals (it overlaps with #1179) so that `openai_mmlu_kor_*` works. Would that be welcome?

## Evaluation metadata
- Paper url: https://arxiv.org/abs/2501.02448
- Github url: https://github.com/guijinSON/HRM8K (benchmark README by an author); reference implementation: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/hrm8k
- Dataset url: https://huggingface.co/datasets/HAERAE-HUB/HRM8K
