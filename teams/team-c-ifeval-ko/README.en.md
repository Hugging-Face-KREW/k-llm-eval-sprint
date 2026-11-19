# Team C: IFEval-Ko

[한국어](README.md) | **English**

- Team name: Strawberry Latte (딸기라떼)
- Dataset: [allganize/IFEval-Ko](https://huggingface.co/datasets/allganize/IFEval-Ko), 342 prompts and 481 instruction occurrences
- Task code: `src/lighteval/tasks/tasks/ifeval_ko/`
- Upstream submission branch: [`team-c/ifeval-ko-upstream`](https://github.com/Hugging-Face-KREW/lighteval/tree/team-c/ifeval-ko-upstream)

## Members

| Name | GitHub | Responsibility |
| --- | --- | --- |
| Junseop Lee | [@SubJeeLee](https://github.com/SubJeeLee) | Port Ko checkers, submit the upstream PR and verify artifact integrity |
| Yejun Song | [@joony0905](https://github.com/joony0905) | Implement scoring, compare judgments on identical responses, review the PR and improve reproduction guides |
| Hyeongjun Kim | [@kiimyjun](https://github.com/kiimyjun) | Register the task, generate model responses and cross-check native Lighteval execution on MPS |

## Validation results and work by PR

- Saved responses for the selected 23 prompts/40 instructions and all 342 prompts/481 instructions were scored through the original Ko evaluator, the ported scorer and the registered task. All individual strict/loose judgments and all four metrics matched.
- During the [MPS GPU validation](https://github.com/Hugging-Face-KREW/lighteval/pull/8#pullrequestreview-5970474156), native Lighteval generated fresh responses for 3 prompts/5 instructions, scored them and aggregated the metrics. Individual judgments and all four metrics matched the original Ko evaluator. The full 342-prompt result comes from replaying saved responses.
- The task implementation and validation evidence were submitted upstream in [PR #1503](https://github.com/huggingface/lighteval/pull/1503). [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8) addressed code style and clarified reproduction instructions and the MPS validation scope.
- Original prompts, kwargs and scoring rules are preserved. Dataset Known Issues are handled separately from the compatibility port.

## Documents

- [Benchmark analysis, judgment agreement and model scores](analysis.en.md)
- [Design and weekly contribution records](design.en.md)
- [Evidence and reproduction guide for saved-response scoring and MPS validation](evidence/analysis-details.en.md#model-response-parity)
- [Supplementary analysis](evidence/analysis-details.en.md)
- [Fixed-response experiment guide](evidence/checker-audit/README.en.md) and [156-case results](evidence/checker-audit/results.en.md)
- [Prompt selection rationale](evidence/sample-coverage/README.en.md) and [coverage tables](evidence/sample-coverage/coverage.en.md)

## Upstream and team-fork PRs

- Proposal issue: [huggingface/lighteval #1463](https://github.com/huggingface/lighteval/issues/1463)
- Upstream PR: [PR #1503](https://github.com/huggingface/lighteval/pull/1503)

| Team-fork PR | Work |
| --- | --- |
| [PR #2](https://github.com/Hugging-Face-KREW/lighteval/pull/2) | Task port and validation on 156 fixed responses |
| [PR #5](https://github.com/Hugging-Face-KREW/lighteval/pull/5) | Response generation and published artifacts for the selected 23 prompts |
| [PR #6](https://github.com/Hugging-Face-KREW/lighteval/pull/6) | Three-path scoring comparison on selected responses |
| [PR #7](https://github.com/Hugging-Face-KREW/lighteval/pull/7) | Response generation and scoring comparison for all 342 prompts |
| [PR #8](https://github.com/Hugging-Face-KREW/lighteval/pull/8) | Style fixes, reproduction-guide updates and native MPS validation |
