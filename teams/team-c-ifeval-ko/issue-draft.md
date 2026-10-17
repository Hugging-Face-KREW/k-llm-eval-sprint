Title: [EVAL] Add IFEval-Ko (Korean)

## What it measures

IFEval-Ko measures how well language models follow programmatically verifiable instructions in Korean prompts, such as keyword frequency, length constraints, and output formatting. It is Allganize's Korean adaptation of IFEval; it does not measure overall response quality or factual correctness.

## Dataset

- HF: [allganize/IFEval-Ko](https://huggingface.co/datasets/allganize/IFEval-Ko) (config: `default`, split: `train`, currently 342 examples).
- License: Apache-2.0 as declared in the dataset card; gated: no at the time of review.
- Input: `prompt`. Scoring metadata: `instruction_id_list` and the corresponding `kwargs`. The `train` split is used for evaluation, not model training.
- Reference implementation: Allganize's [IFEval-Ko task files](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/main/ifeval_ko), used with lm-evaluation-harness as described in the [official README](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/README_Ko.md).

## Official evaluation protocol

- Paper: [Instruction-Following Evaluation for Large Language Models](https://arxiv.org/abs/2311.07911) (Zhou et al., 2023). Original English code: [Google Research IFEval](https://github.com/google-research/google-research/tree/master/instruction_following_eval).
- Format: generative, 0-shot, using the dataset's `prompt`. There is no multiple-choice answer extraction; the generated response is checked against the registered instructions and their parameters.
- Ko reference settings: greedy generation (`do_sample: false`, `temperature: 0.0`), up to 1,280 new tokens, with the stop strings declared in the [task YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/ifeval_ko/ifeval_ko.yaml). Model-specific chat templates and termination settings will be recorded during validation.
- Scoring: preserve the Ko reference evaluator's NFC normalization, checker behavior, and strict/loose evaluation. Prompt-level accuracy requires all instructions in a prompt to pass; instruction-level accuracy is calculated over all individual instructions in the evaluated set.
- Reported scores: the original paper's Table 3 reports English GPT-4 results of 76.89% prompt strict, 83.57% instruction strict, 79.30% prompt loose, and 85.37% instruction loose. These are English reference results, not a Korean baseline or an acceptance target for this integration. We have not yet established a directly comparable Korean model baseline.

## Proposed implementation

- Proposed file: `src/lighteval/tasks/tasks/ifeval_ko/main.py`, with supporting checker modules as needed. The final layout is subject to maintainer feedback.
- Follow the structure of the existing [IFEval task](https://github.com/huggingface/lighteval/tree/main/src/lighteval/tasks/tasks/ifeval) where compatible, while preserving Allganize's Korean-specific scoring behavior. Reuse shared code only where it does not change reference judgments.
- Register the Korean dataset and pass each prompt's instruction IDs and corresponding parameters to the scorer.
- Metrics, all higher-is-better:
  - `prompt_level_strict_acc`
  - `inst_level_strict_acc`
  - `prompt_level_loose_acc`
  - `inst_level_loose_acc`
- Validation plan:
  1. Record dataset/code revisions, framework commits, and relevant dependencies.
  2. Compare the Ko reference evaluator and the proposed Lighteval implementation on identical prompts, parameters, and fixed responses. Cover passing, failing, and boundary cases, including empty responses, Korean text, and formatting variations.
  3. Require matching instruction-level and prompt-level strict/loose judgments, and matching aggregate metrics apart from floating-point rounding.
  4. Run a small model integration check, then evaluate the full split when resources permit. Generate and save responses once and rescore those same responses with both evaluators. The current proposal uses `Qwen/Qwen2.5-1.5B-Instruct` for a 20-prompt integration check followed by the full split; this is a candidate pending team agreement and resource checks. Model/tokenizer revisions, backend, and dtype will be recorded before execution.
  5. Check that existing English IFEval behavior remains unchanged if shared code is modified.
- Scope: reproduce the original IFEval-Ko data and evaluation rules. Record data inconsistencies and scoring concerns as Known Issues rather than silently correcting them in the integration. For example, a previously inspected `key=3345` requests the Korean word `강도` while its keyword parameter is `robber`; any dataset correction will be proposed separately to the dataset authors after review.
- This is an implementation proposal; Lighteval-Ko parity validation has not yet been completed. The English/Korean evaluator comparisons in our analysis are separate from the planned Ko-to-Lighteval parity tests.

## Questions for maintainers

- Would adding IFEval-Ko be welcome, and is there any existing or planned work we should coordinate with?
- Would you prefer a separate `ifeval_ko` task package or an extension of the existing IFEval package, given the Korean-specific checker behavior?
- Are there additional validation requirements or conventions we should follow beyond comparison with the official Ko evaluator on fixed responses?
