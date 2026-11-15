We would like to contribute IFEval-Ko to Lighteval, starting with a separate `ifeval_ko` package and scorer. We plan to implement it in our team fork and adapt to your feedback.

## Evaluation short description

- **Why is this evaluation interesting?** IFEval-Ko is Allganize's Korean adaptation of IFEval. It evaluates verifiable instruction following, including keyword counts, length limits, and response formatting in Korean.
- **How used is it in the community?** Allganize publishes model results and an [lm-evaluation-harness task](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/README_Ko.md). We have not quantified broader adoption.

## Evaluation metadata

- Paper url: [Original IFEval paper](https://arxiv.org/abs/2311.07911); IFEval-Ko is its Korean adaptation.
- Github url: [Original IFEval](https://github.com/google-research/google-research/tree/master/instruction_following_eval). The [Ko reference code](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/54199e3801116897697babf341865741dcd06fc8/ifeval_ko) is hosted on Hugging Face.
- Dataset url: [allganize/IFEval-Ko](https://huggingface.co/datasets/allganize/IFEval-Ko), `default` / `train`; 342 prompts, 481 instruction occurrences, 21 instruction types at the pinned Ko revision above. The card declares Apache-2.0.

## Proposed approach

We recommend a separate Ko scorer for the first PR. Ko has different word/sentence utilities, fixed phrases, and NFC handling. It also runs all strict checks before loose checks, creating fresh checker instances for each phase. Keeping this flow close to the reference makes parity checks easier and limits changes to the existing English metric and tasks that reuse it.

This duplicates some scoring logic; we would revisit shared helpers after establishing parity. [Design and supporting analysis](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/da7053db1d4858239856695a2cfed702173234b6/teams/team-c-ifeval-ko/design.en.md).

We would preserve the [Ko protocol](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml): zero-shot, no sampling, up to 1,280 new tokens, declared stop strings, and all four prompt-/instruction-level strict/loose accuracy metrics.

Known prompt/checker mismatches, such as `3345` requesting “강도” while checking `robber`, would remain unchanged for reference compatibility and be reported separately to the dataset authors.

## Validation and current status

Compare identical stored responses through the Ko reference and the registered task, requiring matching individual judgments, aggregate numerators/denominators, and an absolute error of at most `1e-12` for all four metrics. Check affected existing tasks for regressions.

Our expanded [156 diagnostic cases](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/da7053db1d4858239856695a2cfed702173234b6/teams/team-c-ifeval-ko/evidence/checker-audit/results.en.md), plus 18 auxiliary inputs for compatibility and error handling, compare the original English and Ko evaluators on identical Ko inputs. The cases provide dedicated pass and fail examples for all 21 observed instruction types and 25 input partitions. These results support the need for Ko-specific behavior; they do not establish parity of the registered Lighteval task. [Pinned sources and execution details](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/da7053db1d4858239856695a2cfed702173234b6/teams/team-c-ifeval-ko/evidence/checker-audit/README.en.md).

We propose [23 prompts with 40 instruction occurrences](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/da7053db1d4858239856695a2cfed702173234b6/teams/team-c-ifeval-ko/evidence/sample-coverage/README.en.md) for model integration, covering all 21 observed instruction types. This is separate from the diagnostic experiment above. Model integration and full-split evaluation remain pending.

The implementation and model-free validation are available in our [team-fork PR](https://github.com/Hugging-Face-KREW/lighteval/pull/2). The [registered-task validation](https://github.com/Hugging-Face-KREW/lighteval/pull/2#issuecomment-6765647327) matched all 156 fixed-response cases and 18 auxiliary return/exception contracts against the original Ko evaluator, with zero differences across all four aggregate metrics. Doc conversion also preserved all 342 prompts and 481 instruction occurrences. These are fixed-response compatibility checks; model integration and full-split model evaluation remain pending. Our initial proposal targets native Pipeline support; Inspect scorer/backend support would be a follow-up, subject to your feedback. This is separate from the completed `lighteval tasks inspect` CLI check.

## Questions for maintainers

1. Does this separate-package approach fit the project? Any requirements for the initial PR?
2. Would native Pipeline/metric support be sufficient for the initial PR, with Inspect support as a follow-up?
