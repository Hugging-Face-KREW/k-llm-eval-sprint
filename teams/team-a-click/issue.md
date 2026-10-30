# [EVAL] CLIcK: Korean cultural and language understanding

## Evaluation short description

### Why is this evaluation interesting?

[CLIcK][paper] evaluates Korean cultural knowledge and language understanding with **1,995 multiple-choice questions** from Korean exams and textbooks. It covers **eight cultural and three linguistic categories**, including Korean society, history, reading comprehension, and grammar. Adding it would help Lighteval users evaluate knowledge and language skills specific to Korea.

### How used is it in the community?

CLIcK appears in official evaluations of NAVER's [HyperCLOVA X THINK][naver-report], SK Telecom's [A.X K2][skt-card], LG AI Research's [K-EXAONE][exaone-report], KT's [Mi:dm K 2.5 Pro][kt-report], and Upstage's [Solar Open 2][solar-card]. It is also available in lm-evaluation-harness through [PR #3173][harness-pr].

**I would like to implement this task with @GeonRyoung and @ojm6135 and submit a PR.** We would support all 11 categories, four or five answer options, and reading passages when present. We would evaluate all 1,995 questions from the `train` split and report accuracy for each category.

For the first version, we propose zero-shot evaluation (no example questions), one Korean prompt, and the original option order. We would compare the probabilities of complete answer strings, such as `A. option text`, following the [authors' explanation][author-scoring]. We would document the differences from the [paper's evaluation with multiple prompt wordings and option orders][paper-html].

For validation, we would make the reference implementation use the same prompts and answer strings as this proposal. We would also fix the [missing fifth option in the linked harness revision][harness-culture] before comparing results. We also still need to confirm the dataset license with the authors; we could not find an explicit license in the [dataset card][dataset-card] or [author repository][author-revision].

**Would you be open to a PR adding CLIcK with this initial scope?**

## Evaluation metadata

- **Paper url:** [CLIcK — LREC-COLING 2024][paper]
- **Github url:** [rladmstn1714/CLIcK][author-repo]
- **Dataset url:** [EunsuKim/CLIcK][dataset]

[paper]: https://aclanthology.org/2024.lrec-main.296/
[paper-html]: https://arxiv.org/html/2403.06412v2
[author-repo]: https://github.com/rladmstn1714/CLIcK
[author-revision]: https://github.com/rladmstn1714/CLIcK/tree/38373acdf73a11e9fbf3667747da61021439d7b7
[author-scoring]: https://github.com/rladmstn1714/CLIcK/issues/6#issuecomment-2132901818
[dataset]: https://huggingface.co/datasets/EunsuKim/CLIcK
[dataset-card]: https://huggingface.co/datasets/EunsuKim/CLIcK/blob/d61627859645b5e6edc03fd9f835735d8226fa4e/README.md
[naver-report]: https://arxiv.org/html/2506.22403v1
[skt-card]: https://huggingface.co/skt/A.X-K2
[exaone-report]: https://arxiv.org/html/2601.01739v1
[kt-report]: https://arxiv.org/html/2603.18788v1
[solar-card]: https://huggingface.co/upstage/Solar-Open2-250B#korean-benchmarks
[harness-pr]: https://github.com/EleutherAI/lm-evaluation-harness/pull/3173
[harness-culture]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/click/click_cul/utils.py#L6
