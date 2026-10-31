# [EVAL] KorMedMCQA: Korean medical licensing exam MCQA

## Evaluation short description

### Why is this evaluation interesting?

[KorMedMCQA][paper] evaluates medical knowledge with **7,469 five-option questions** from the Korean national licensing exams for doctors, nurses, pharmacists and dentists (2012–2024). It also tests Korean medical terminology and Korean healthcare law. Its model rankings correlate less with MedQA (Spearman ρ = 0.763) than MedQA does with MMLU-Pro (0.928) ([paper Table 3][paper-html]). Lighteval has no benchmark built from Korean exams in the medical domain.

### How used is it in the community?

The authors added a [`kormedmcqa` task][harness-task] to lm-evaluation-harness themselves in March 2024 (PR #1530; now version 3.0 after #3842).
Reproduction status: in July 2025, lm-eval did not reproduce the paper's open-model scores (Qwen2.5-1.5B: 23.56 vs 37.92, [lm-eval #3103][harness-3103]) because answer extraction was missing. #3842 ports the Appendix B regex. Our pass criterion is agreement with lm-eval v3.0.

**I would like to implement this task with my team and submit a PR.** We would add four tasks (`doctor`, `nurse`, `pharm`, `dentist`) on the `test` split (3,009 questions in total) and report accuracy for each.

For the first version, we propose generative evaluation with 5-shot examples from the `fewshot` split, matching lm-evaluation-harness (prompt, stop sequences and `extract_choice` from paper Appendix B). CoT is out of scope.

For validation, we would run `Qwen/Qwen2.5-1.5B-Instruct` with both tools and compare the prompt, the extracted answer and the accuracy for each question and config. Pinned versions and details will be in the PR.

One open point: the dataset card says CC BY-NC 2.0 while the paper's datasheet says MIT. We will ask the authors.

**Would you be open to a PR adding KorMedMCQA with this initial scope?**

## Evaluation metadata

- **Paper url:** [KorMedMCQA (arXiv 2403.01469v3)][paper]
- **Github url:** [lm-evaluation-harness `kormedmcqa` task][harness-task]
- **Dataset url:** [sean0042/KorMedMCQA][dataset]

[paper]: https://arxiv.org/abs/2403.01469v3
[paper-html]: https://arxiv.org/html/2403.01469v3
[harness-task]: https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa
[dataset]: https://huggingface.co/datasets/sean0042/KorMedMCQA
[harness-3103]: https://github.com/EleutherAI/lm-evaluation-harness/issues/3103
