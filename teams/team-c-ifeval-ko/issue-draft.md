## Evaluation short description

- **Why is this evaluation interesting?**
  We would like to contribute IFEval-Ko, Allganize's Korean adaptation of IFEval, to evaluate compliance with verifiable instructions in Korean prompts. The goal is compatibility with Allganize's existing evaluator, rather than new scoring rules or a general measure of Korean response quality.
- **How used is it in the community?**
  Allganize publishes the [dataset and model-result chart](https://huggingface.co/datasets/allganize/IFEval-Ko) and an [lm-evaluation-harness task with usage instructions](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/README_Ko.md). Broader adoption is not quantified here.

## Evaluation metadata

- Paper url: [IFEval, Zhou et al. (2023)](https://arxiv.org/abs/2311.07911). IFEval-Ko is the Korean adaptation, not a separate paper.
- Github url: [original IFEval](https://github.com/google-research/google-research/tree/master/instruction_following_eval). The **Ko reference code** is hosted on [Hugging Face](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/54199e3801116897697babf341865741dcd06fc8/ifeval_ko).
- Dataset url: [allganize/IFEval-Ko](https://huggingface.co/datasets/allganize/IFEval-Ko), `default` / `train`, 342 prompts at revision `54199e3801116897697babf341865741dcd06fc8`; Apache-2.0 as declared in the card; no access gate at review time.

## Why the existing IFEval metric needs adaptation

The existing [French task](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py#L28-L40) imports the English `ifeval_metrics`. Changing only the dataset would not preserve the Ko reference: its [utility](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py) counts whitespace-delimited words, unlike the English regex tokenizer. For example, `사과,배,포도` counts as one word in Ko and three in the existing English implementation. Ko also changes sentence splitting, fixed response phrases, and NFC handling.

We propose reusing the scoring loop and compatible checkers where possible, while preserving these Ko-specific rules. A registry swap alone would not cover response normalization and checker construction behavior. The [comparison and source references](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/15a84cc426d2f19fd908c5d9a070dd522c061a3e/teams/team-c-ifeval-ko/analysis.md#61-french는-재사용하고-ko는-변경이-필요한-이유) describe the differences.

## Proposed implementation and validation

- Proposed task: `ifeval_ko`, with layout subject to feedback. Follow the [Ko task protocol](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml): generative, 0-shot, no sampling, maximum 1,280 new tokens, and the declared stop strings. Record model-specific chat-template/EOS behavior.
- Proposed first target: native metric/Pipeline with `prompt_level_strict_acc`, `inst_level_strict_acc`, `prompt_level_loose_acc`, and `inst_level_loose_acc`. Inspect support is outside the initial proposal; its existing scorer returns only the two prompt-level values.
- Compare **identical stored responses** with the Ko reference and the registered Lighteval task. Require matching instruction-level and prompt-level judgments, aggregate numerators/denominators, and all four metrics apart from floating-point rounding. Regress existing tasks if shared code changes.
- Existing evidence: [86 saved-response cases, inputs, runners, outputs, and pinned sources](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/15a84cc426d2f19fd908c5d9a070dd522c061a3e/teams/team-c-ifeval-ko/evidence/checker-audit/README.md). These compare the existing English and Ko evaluators; they are **not** validation of a new Lighteval-Ko task.
- Next: fixed-response regression, then a proposed 20-prompt integration sample covering 21 instruction types (33 instruction occurrences), followed by the full split. `Qwen/Qwen2.5-1.5B-Instruct` and the sample await team approval; backend, dtype, and model/tokenizer revisions remain to be fixed. Integration execution remains pending. See the [design proposal](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/15a84cc426d2f19fd908c5d9a070dd522c061a3e/teams/team-c-ifeval-ko/design.md).

## Published results and known limitations

Allganize's [published Korean results](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/benchmark-score-dot-plot.png) are labeled Strict Accuracy. We have not established the prompt-/instruction-level mapping or complete execution settings, so we do not present them as a four-metric reproduction target. Our primary acceptance criterion is agreement on the same responses, not matching historical English GPT-4 scores.

We will preserve original prompts and scoring parameters. [Known Issues](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/15a84cc426d2f19fd908c5d9a070dd522c061a3e/teams/team-c-ifeval-ko/analysis.md#82-실제-evaluator로-확인한-known-issues) include `3345` (`강도` / `robber`), `1203` (`평화` / `peace`), `2142` (`포식자` / `predatory`), fixed-choice wording in `227`, and 14 inclusive/exclusive length-limit wording mismatches. Corrections will be proposed separately to the dataset authors, not silently applied in this integration. These observations do not quantify changes in model scores.

On 2026-10-30 (KST), issue/PR searches for `"IFEval-Ko"` in `huggingface/lighteval`, `Hugging-Face-KREW/lighteval`, and `EleutherAI/lm-evaluation-harness` each returned zero results. We will repeat the search before posting to check for related work.

## Question for maintainers

Would a contribution in this scope be welcome? If so, would you prefer **(a)** a separate `ifeval_ko` package, or **(b)** extending the shared IFEval metric to accept a task-specific registry, response normalizer, and checker construction policy? We would first explore shared code while keeping existing English behavior unchanged.
