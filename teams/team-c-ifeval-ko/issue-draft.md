[Team documents](README.en.md)

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

We recommend a separate `ifeval_ko` package and scorer for the initial port (option A). This keeps Ko utilities, fixed phrases and normalization close to the reference. It also preserves the order of running all strict checks before all loose checks, with fresh checker instances in each phase. The approach limits changes to the existing English and French paths while establishing Ko parity. Option B can also work if it preserves the same policies and checker lifecycle. See the [experiment results](evidence/checker-audit/results.en.md) and [pinned sources](evidence/checker-audit/provenance.json).

## Proposed implementation and validation

- Proposed task: `ifeval_ko`, with layout subject to feedback. Follow the [Ko task protocol](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml): generative, 0-shot, no sampling, maximum 1,280 new tokens, and the declared stop strings. Record model-specific chat-template/EOS behavior.
- Proposed first target: native metric/Pipeline with `prompt_level_strict_acc`, `inst_level_strict_acc`, `prompt_level_loose_acc`, and `inst_level_loose_acc`. Inspect support is outside the initial proposal; its existing scorer returns only the two prompt-level values.
- Evaluate **identical inputs and stored responses** with the Ko reference and the registered Lighteval task. Require identical instruction-level and prompt-level judgments, matching aggregate numerators and denominators, and an absolute error of at most `1e-12` for all four metrics. Run regression checks for existing tasks if shared code changes.
- Experimental evidence: a [156-case experiment](evidence/checker-audit/results.en.md), with 18 auxiliary inputs for compatibility and error handling. Both original evaluators receive identical Ko inputs, and the raw results include input reproduction checks. Each of the 21 instruction IDs and 25 input partitions used by the dataset has dedicated pass and fail cases. For the primary targets, `(English, Ko)=(T,F)` occurs in 13 strict cases and 8 loose cases; `(F,T)` occurs in 22 strict cases and 21 loose cases. Parity testing for the new Lighteval-Ko task remains pending.
- Next: compare the new task with the stored Ko expectations, check affected English/French paths for regressions, then run model integration on the proposed 23 prompts (40 instruction occurrences, 21 IDs and 25 input partitions), followed by the full split. `Qwen/Qwen2.5-1.5B-Instruct` and the sample await team approval; backend, dtype, and model/tokenizer revisions remain to be fixed. New-task parity and model integration remain pending. See the [design proposal](design.en.md).

## Published results and known limitations

Allganize's [published Korean results](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/benchmark-score-dot-plot.png) are labeled Strict Accuracy. We have not established the prompt-/instruction-level mapping or complete execution settings, so we do not present them as a four-metric reproduction target. Our primary acceptance criterion is agreement on the same responses, not matching historical English GPT-4 scores.

We will preserve original prompts and scoring parameters. [Known Issues](analysis.en.md#82-known-issues-confirmed-with-the-actual-evaluators) include `3345` (`강도` / `robber`), `1203` (`평화` / `peace`), `2142` (`포식자` / `predatory`), fixed-choice wording in `227`, and 14 inclusive/exclusive length-limit wording mismatches. Corrections will be proposed separately to the dataset authors, not silently applied in this integration. These observations do not quantify changes in model scores.

The 2026-10-30 (KST) issue/PR searches are historical background. The proposal now exists as [huggingface/lighteval#1463](https://github.com/huggingface/lighteval/issues/1463); the [experiment results](evidence/checker-audit/results.en.md) provide the supporting evidence. Issue attachment drafts and remote publication are outside this documentation update.

## Question for maintainers

Would a separate `ifeval_ko` package and scorer, **option A**, fit the project for the initial contribution? We recommend it to establish reference parity while limiting changes to existing paths. We are also open to **option B**: a shared metric with explicit policies for registry selection, normalization, execution order and checker construction.
