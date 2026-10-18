Title: [EVAL] Add KorMedMCQA (Korean medical licensing exam MCQA): would a PR be welcome?

## What it measures

KorMedMCQA is a Korean multiple-choice QA benchmark built from the Korean national licensing exams for doctors, nurses, pharmacists and dentists (2012–2024): 7,469 five-option questions. Besides medical knowledge, it tests Korean medical terminology and Korean healthcare law and regulations. In the paper, model rankings on KorMedMCQA correlate less with MedQA (Spearman ρ = 0.763) than MedQA does with MMLU-Pro (0.928), so it measures something MedQA does not.

lighteval has medical benchmarks (`med.py`) and Korean tasks that are translated or multilingual, but no Korean-native medical benchmark.

## Dataset

- HF: [`sean0042/KorMedMCQA`](https://huggingface.co/datasets/sean0042/KorMedMCQA) (revision `79efd6f`)
- Configs: `doctor`, `nurse`, `pharm`, `dentist`
- Splits: `train`, `dev`, `test`, `fewshot` (5 questions per config). Split by exam year: train up to 2020, dev 2021, test 2022–2024.
- Test size: doctor 435, nurse 878, pharm 885, dentist 811 (3,009 in total)
- Fields: `question`, `A`–`E`, `answer` (integer 1–5), plus `subject`, `year`, `period`, `q_number`, `cot`
- License: CC BY-NC 2.0 on the dataset card, but the paper's datasheet ([Appendix](https://arxiv.org/html/2403.01469v3#A5)) says it is released under the MIT license. We plan to ask the authors on the dataset's Community tab which one applies. Gated: no.

## Official evaluation protocol

- Paper: [KorMedMCQA: Multi-Choice Question Answering Benchmark for Korean Healthcare Professional Licensing Examinations](https://arxiv.org/abs/2403.01469v3) (Kweon, Choi et al., 2024). Open models in the paper were evaluated with lm-evaluation-harness.
- Reference implementation: lm-evaluation-harness [`lm_eval/tasks/kormedmcqa`](https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa) (commit `97a5e2c`, task version 3.0; regex extraction added in EleutherAI/lm-evaluation-harness#3842)
- Format: generative + answer extraction, 5-shot
  - Prompt: `{question}\nA. {A}\nB. {B}\nC. {C}\nD. {D}\nE. {E}\n정답：` (full-width colon)
  - Few-shot: the first 5 rows of the `fewshot` split, in order (`sampler: first_n`). The harness yaml has no `num_fewshot`, so `--num_fewshot 5` is needed to match the paper.
  - Generation: greedy, `max_gen_toks: 1024`, stop sequences `["Q:", "</s>", "<|im_end|>", ".", "\n\n"]`
  - Answer extraction (`utils.py`, paper Appendix B): four regex patterns tried in order, case-insensitive. The last match of the first pattern that matches is the answer, and no match counts as wrong.
  - Metric: `exact_match` per config. The overall score is the average weighted by test size (`weight_by_size: true`).
- Reported scores (paper Table 1, Direct 5-shot, weighted average): GPT-4o 85.61, Qwen2.5-72B 78.86, Llama-3.1-70B 74.31, EXAONE-3.0-7.8B 55.73, EEVE-10.8B 54.94

## Proposed implementation

- File: `src/lighteval/tasks/tasks/kormedmcqa.py`
- Tasks: `kormedmcqa:doctor`, `kormedmcqa:nurse`, `kormedmcqa:pharm`, `kormedmcqa:dentist` on the test split
- Goal: match lm-eval's `kormedmcqa` so scores from the two tools can be compared
  - Same prompt string, gold `answer - 1`
  - Few-shot from the `fewshot` split with `few_shots_select="sequential"`, since the default (`balanced`) differs from `first_n`
  - Same stop sequences and generation length
- Metrics: a metric that ports lm-eval's `extract_choice` as is, then exact match. The built-in `exact_match` and `extractive_match` follow different extraction rules, so they would give different scores.
- Validation plan: run `Qwen/Qwen2.5-1.5B-Instruct` (CPU, float32, batch size 1) with lm-eval and lighteval, chat template off on both, and compare per-config accuracy and the extracted answer for each question. The paper reports this model at 37.92 (Table 1, Direct 5-shot); we will list it for reference, but the pass criterion is agreement with lm-eval. If we get GPU access, we will repeat it with EXAONE-3.0-7.8B.

## Prior work check

On 2026-10-17 we searched this repo for `kormedmcqa` (issues, PRs, code) and found nothing. `main` is at `7fa19dc`. The only other Korean benchmark proposal we found is KMMLU (#1424, #1425), which does not overlap with this one.

## Questions for maintainers

1. Would you take this as a new task? If so, should it go in `src/lighteval/tasks/tasks/` (like the KMMLU PR) or `src/lighteval/tasks/multilingual/tasks/`?
2. The default task would be generative to match the paper and lm-eval. Do you also want a loglikelihood variant? Some small models in the paper score below chance (gemma-2-2b-it: 13.33 on `doctor`, Table 1), which suggests the generative score partly measures whether the answer format can be extracted. A loglikelihood variant would not depend on the output format.
3. The original regex has known gaps. Case-insensitive matching can read the English article "a" as option A, and `\b` does not match before Korean particles (for example `C가`). We plan to copy it as is so scores match lm-eval, and note the gaps in the PR. Is that OK?
4. `kormedmcqa:_average` in lighteval would be a plain mean, while the paper and lm-eval weight by test size (GPT-4o: 85.53 vs 85.61). Is there a preferred way to report the weighted average?
5. Should new tasks also define the inspect-ai fields (`sample_fields`, `solver`, `scorer`) like `gpqa.py` does, or is the `prompt_function` + `metrics` config enough?
6. The dataset card and the paper give different licenses (CC BY-NC 2.0 vs MIT). Is a non-commercial dataset fine for lighteval, and should the task docstring state the license?
