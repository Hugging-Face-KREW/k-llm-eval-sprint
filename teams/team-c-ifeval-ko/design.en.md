# Design Document

[한국어](design.md) | **English**

<a id="task-structure"></a>

## 1. Task name and file locations

### 1.1. Purpose and support scope

| Item | Design |
| --- | --- |
| Task name | `ifeval_ko` |
| Implementation/team review repository | `Hugging-Face-KREW/lighteval` |
| Future contribution target | `huggingface/lighteval`; recheck the current API before submission |
| Registration entry point | `src/lighteval/tasks/tasks/ifeval_ko/main.py` |
| Initial support | Four metrics through the native metric/Pipeline path |
| Separate scope | Inspect scorer/backend support, data corrections and new scoring policies |

### 1.2. Choice between two architectures

**Both options require Ko checker modules.** The choice concerns whether to keep a separate scoring loop or share it.

| Aspect | A. Separate Ko package and engine | B. Ko modules with a shared metric |
| --- | --- | --- |
| Ko checkers, registry, utilities | Preserved separately | Preserved separately |
| Scoring loop | Dedicated Ko scorer | Shared engine with explicit policies |
| Existing English changes | Normally none | Extract shared loop and connect EnglishPolicy |
| Main benefit | Direct reference comparison and limited regression scope | Less duplication of helpers and aggregation integration |
| Main cost | Maintain a small duplicated scorer | Validate response preparation, both execution orders and existing paths |
| Adoption condition | Prioritize a small initial change | Agreement on the shared API and English/French regression evidence |

### 1.3. Option A: file responsibilities

Paths below are relative to `src/lighteval/tasks/tasks/`. Option A is implemented in [team code PR #2](https://github.com/Hugging-Face-KREW/lighteval/pull/2); this does not imply final upstream agreement on the architecture.

| File | Responsibility |
| --- | --- |
| `ifeval_ko/__init__.py` | Define the Ko package |
| `ifeval_ko/main.py` | Prompt function, Ko metric grouping, task config and `TASKS_TABLE` |
| `ifeval_ko/scoring.py` | Independent all-strict-then-all-loose scoring, returning four results |
| `ifeval_ko/instructions_registry.py` | Preserve the original 25-ID Ko registry |
| `ifeval_ko/instructions.py` | Preserve Ko checkers, fixed choices and ending phrases |
| `ifeval_ko/instructions_util.py` | Preserve Ko word/sentence counting and utilities |

Record structural and import changes when porting scoring functions from original `utils.py`. Do not import the English metric and then replace its global registry or utilities.

#### 1.3.1. Evidence for option A from identical Ko inputs

We conducted a **156-case experiment**, passing identical Ko prompts, instruction order, effective kwargs and responses to the original English harness and Ko evaluator. The [results](evidence/checker-audit/results.en.md) record input checks, reproduction, individual judgments and aggregates. For primary targets in `(English, Ko)` order, strict has 13 `(T,F)` and 22 `(F,T)` cases; loose has 8 and 21 respectively. These counts show scoring-rule differences on fixed responses.

For example, `markdown_quote_valid_highlights_349` counts the same response as 39 English words and 40 Ko words. Under `<40`, English passes strict/loose and Ko fails both. `comma_boundary_compact` at key 3442 counts 20 English words and 18 Ko words, reversing the result under `<20`. Results also include strict failures recovered by loose line deletion.

Option A keeps Ko counting, fixed phrases and NFC placement close to the reference. It preserves all strict checks before all loose checks, with new checker instances in each phase. It is recommended initially because it allows direct reference comparison and limits changes to existing English/French code. The cost is duplicated maintenance of part of the scoring loop. Option B can also preserve the same policies and lifecycle; the final architecture is subject to maintainer discussion.

Acceptance means **agreement between the new Ko task and original Ko judgments**. If English passes and Ko fails, the new Ko task must fail. Preserve prompt/kwargs translation mismatches and the `first_word` normalization asymmetry. These materials provide experiment evidence and a porting plan. Upstream issue drafting and publication are separate work.

### 1.4. Option B: shared engine and Ko policy

| File | Responsibility |
| --- | --- |
| `ifeval/main.py` | Preserve `IFEvalMetrics()`/`ifeval_metrics` exports and English defaults |
| `ifeval/metric_core.py` | Candidate handling, OR/AND, result helpers and both execution orders |
| `ifeval/policies.py` | Policy contract and `EnglishPolicy` |
| `ifeval_ko/main.py` | Register the Ko task and an independent metric grouping |
| `ifeval_ko/policy.py` | `KoPolicy`: response NFC, checker construction and execution order |
| Three Ko checker/registry/utility files | Preserved independently as in option A |

The proposed policy interface has these responsibilities. Names below are new API proposals.

| Proposed API | EnglishPolicy | KoPolicy |
| --- | --- | --- |
| `prepare_response(raw, phase)` | Identity | NFC at each strict/loose entry point |
| `create_checker(id, raw_kwargs, prompt)` | English registry/initialization | Ko registry/initialization |
| `loose_candidates(prepared)` | Original eight candidates | Original eight candidates from NFC response |
| `execution_order` | `interleaved` | `separate_phases` |

Registry replacement alone is insufficient. Response normalization, fixed phrases, utilities and checker construction timing must also be selectable. Create separate English/Ko metric-grouping instances. Do not change policy through existing `ifeval_metrics(sample_params=...)`, which may mutate objects and metric names.

### 1.5. Preservation scope and dependencies

The data uses 21 IDs; the Ko registry contains 25. Preserve the registry, while measuring data coverage over the 21 used types. Do not claim successful execution of all unused `keywords:letter_frequency`, `change_case:capital_word_frequency`, `change_case:english_capital` and `change_case:english_lowercase` paths. Track utility-reference problems in unused checkers separately. Do not register `KeySentenceChecker`, which is absent from the original registry.

Check `langdetect`, `immutabledict` and `packaging` against `pyproject.toml`. Follow lazy imports or existing guards so missing Ko optional dependencies do not break unrelated task discovery. Preserve source provenance, revisions, copyright and license headers.

Sources: [Lighteval Registry](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/registry.py), [English IFEval](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/ifeval/main.py), [Ko registry](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_registry.py).

## 2. Subset, evaluation split and few-shot split

| Item | Value | Meaning |
| --- | --- | --- |
| Hugging Face ID | `allganize/IFEval-Ko` | Use the pinned source revision |
| Subset/config | `default` | Evaluation data configuration |
| Evaluation split | `train` | Used for evaluation despite its name |
| Few-shot split | Nominally `train` | Follows existing IFEval convention; zero-shot means no example sampling/insertion |
| Few-shot count | `num_fewshots=0` | Also verify 0 in the actual run |
| Full prompts | 342 prompts, 342 unique keys | Full prompt-level denominator |
| Full instructions | 481 occurrences, 21 unique IDs | Full instruction-level denominator |
| Prompt identifier | Original `key` | Distinct from row index |
| Integration selection | N prompts covering types and paths; current proposal: 23 prompts/40 instructions | Count follows section 6.3 rules; add prompts if needed |

On loading, check missing/duplicate keys, instruction/kwargs list lengths and registry membership. Preserve order and multiplicity when IDs repeat. Do not collapse repeated IDs into a set or ID-keyed dictionary.

The pinned-data count confirms that the 23-prompt proposal covers all 21 IDs and 25 `(ID, input path)` pairs with 40 occurrences. Section 6 distinguishes selection rules, evidence and deeper branch checks.

<a id="input-contract"></a>

## 3. Prompt function and source-to-Doc mapping

### 3.1. Mapping contract

| Source field/constant | Doc field | Requirement |
| --- | --- | --- |
| `prompt` | `query` | Preserve text; do not apply a chat template in the prompt function |
| `instruction_id_list` | `specific["instructions_id_list"]` | Document the singular/plural key difference; preserve order and repeats |
| `kwargs` | `specific["kwargs"]` | One-to-one alignment at each instruction index |
| `key` | `specific["ifeval_ko"]["key"]` | Trace source prompt |
| Original prompt/revision | `query` and task config `hf_revision` | Preserve them at these respective locations and record both in execution artifacts |
| `choices=[""]` | `choices` | Nominal value for a generative task |
| `gold_index=0` | `gold_index` | Not an index of an answer phrase |
| `instruction=""` | `instruction` | Add no extra instruction |

### 3.2. Implemented prompt function

```python
from lighteval.tasks.requests import Doc
from lighteval.utils.imports import requires

KO_DATA_REVISION = "54199e3801116897697babf341865741dcd06fc8"


@requires("langdetect", "immutabledict")
def ifeval_ko_prompt(line, task_name=""):
    return Doc(
        task_name=task_name,
        query=line["prompt"],
        choices=[""],
        gold_index=0,
        instruction="",
        specific={
            "instructions_id_list": line["instruction_id_list"],
            "kwargs": line["kwargs"],
            "ifeval_ko": {
                "key": line["key"],
            },
        },
    )
```

Trace judgments by `(key, instruction_index, instruction_id)`. Key 1203 has two `keywords:frequency` instructions, stored separately at indexes 0 and 1.

Do not translate keywords, normalize all kwargs to NFC, remove Markdown or clean whitespace during Doc conversion. Preserve raw kwargs and apply the original filter when constructing checkers.

## 4. Scoring, generation length, stop sequences and response extraction

### 4.1. Metrics and aggregation

| Metric | Sample-level value | Corpus aggregation |
| --- | --- | --- |
| `prompt_level_strict_acc` | AND of strict flags | Mean of prompt Booleans |
| `inst_level_strict_acc` | Ordered strict Boolean list | Mean after flattening all lists |
| `prompt_level_loose_acc` | AND of loose flags | Mean of prompt Booleans |
| `inst_level_loose_acc` | Ordered loose Boolean list | Mean after flattening all lists |

Instruction accuracy is not the mean of per-prompt accuracies. `[[True, True, True], [False]]` gives 0.75 instruction accuracy and 0.5 prompt accuracy. Expose all four through `SampleLevelMetricGrouping`, with `higher_is_better=True`.

### 4.2. Generation settings and task config

| Setting | Proposed baseline |
| --- | --- |
| Output | Free-form generated response checked against instructions |
| Responses | One per prompt |
| Length | At most 1,280 new tokens |
| Sampling | Off; verify backend `do_sample=false`, `temperature=0.0` |
| Stop sequences | `<end_of_turn>`, `<\|im_end\|>` |
| Model-specific EOS | Record actual EOS token/stop handling separately |
| Chat template | Apply once and retain final rendered input |
| Model candidate | Prefer reviewing PR candidate `Qwen/Qwen2.5-1.5B-Instruct`; adoption, revisions, dtype and backend unconfirmed |

Registration example for the pinned Lighteval API follows. Freeze backend sampling settings separately.

```python
from lighteval.tasks.lighteval_task import LightevalTaskConfig

# Create ifeval_ko_metrics separately using the selected A/B architecture.
ifeval_ko = LightevalTaskConfig(
    name="ifeval_ko",
    prompt_function=ifeval_ko_prompt,
    hf_repo="allganize/IFEval-Ko",
    hf_subset="default",
    hf_revision=KO_DATA_REVISION,
    hf_avail_splits=["train"],
    evaluation_splits=["train"],
    few_shots_split="train",
    few_shots_select="random_sampling",
    num_fewshots=0,
    metrics=[ifeval_ko_metrics],
    generation_size=1280,
    stop_sequence=["<end_of_turn>", "<|im_end|>"],
    version=0,
)

TASKS_TABLE = [ifeval_ko]
```

### 4.3. Response extraction and scorer input

There is no single-answer extraction step. Each checker inspects the entire assistant response. `choices` and `gold_index` do not select a target answer string.

Use `ModelResponse.final_text[0]` as Lighteval scorer input. `final_text` selects `text_post_processed` when available, otherwise original `text`; it is not always raw model output.

Record these boundaries separately:

1. Raw model text and token IDs.
2. Extracted assistant response excluding the input, and framework post-processing.
3. Identical scoring input passed to both evaluators.
4. Response after Ko evaluator NFC normalization.

Do not apply reasoning-tag removal or stop processing to only one evaluator. Generate and store responses once, then rescore them with both evaluators. Do not generate different responses per evaluator.

### 4.4. Ko strict/loose algorithm

The original Ko execution order is:

1. NFC-normalize the response at strict entry.
2. Create fresh checkers in instruction order and run every strict check.
3. NFC-normalize the same input response again at loose entry.
4. Generate the original eight loose candidates in order.
5. Create new checkers in instruction order and OR their candidate judgments.
6. Return both flag lists and their prompt-level ANDs.

Checker construction is registry lookup → original `if v` kwargs filter → `build_description(**kwargs)` → `build_description(prompt=prompt)` when required. `if v` removes `None`, 0, False, empty strings and empty lists; do not replace it with `is not None`.

| Aspect | Existing Lighteval English | Original Ko |
| --- | --- | --- |
| Response NFC | None at metric entry | At strict and loose entry |
| Overall order | Strict→loose per instruction | All strict→all loose |
| Checker lifecycle | One shared object per instruction | Fresh objects per phase |

Option A preserves both Ko phases in a dedicated scorer. Option B supports English `interleaved` and Ko `separate_phases`. Creating two checkers but alternating strict→loose per instruction still differs from Ko's full call order.

The eight candidates are the original response, star removal, first-line removal, last-line removal, both-end-line removal, and star removal applied to the last three. Lines split on `\n`. Preserve order and duplicates; skip empty candidates using the original `r.strip()` condition. Do not additionally remove `#`, `>` or `-`. Loose is candidate OR per instruction and instruction AND per prompt. Instructions need not pass on the same candidate.

### 4.5. Exceptions, errors and execution records

Preserve results of exceptions caught internally by original checkers. For example, do not replace `ResponseLanguageChecker`'s True return after catching `LangDetectException` with an external error policy. Conversely, do not turn propagated exceptions into correct answers through a new fallback.

Record OOM, timeout and incomplete loading as execution failures. Do not substitute empty responses or silently remove failures from denominators. Genuine empty responses and normally terminated length-limited outputs are scored under original rules, with termination reasons recorded.

The manifest records keys, source/effective kwargs, scorer inputs, model/tokenizer revisions, backend, dtype, seed, chat template, actual EOS/stops, termination reasons, individual flags, numerators/denominators, four metrics, exceptions and source/input/output hashes. Distinguish expected/generated/scored counts and generation/scoring failures by stage.

Sources: [Ko YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml), [Ko scoring](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/utils.py), [ModelResponse](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/models/model_output.py), [task config](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/lighteval_task.py).

## 5. Differences from the official procedure and their rationale

The direct “official” comparison target here is pinned Allganize Ko. Distinguish English-versus-Ko differences from structural changes between the Ko reference and Lighteval port.

| Aspect | Ko reference | Lighteval port | Rationale/parity condition |
| --- | --- | --- | --- |
| Framework | lm-evaluation-harness task/YAML | Doc, TaskConfig, native metric | Framework integration changes; judgment semantics remain identical |
| Input type | `InputExample` and results list | `Doc`, `ModelResponse` | Preserve fields, order, kwargs and response boundaries |
| Scorer file | Original `utils.py` | Dedicated scorer in A or policy engine in B | Record actual file/import changes |
| Metric connection | YAML aggregation | `SampleLevelMetricGrouping` | Same metrics, Booleans, numerators/denominators and flattened aggregation |
| Revision selection | Public task dataset path | Pin with `hf_revision` | Prevent updates from changing inputs/rules |
| Model termination | YAML stops + model backend | Actual Lighteval stop/EOS behavior | Aim for matching generation conditions; record actual values |
| Initial support | Original harness path | Native metric/Pipeline first | Inspect requires a separate scorer and is outside the first scope |

Preserve Ko word/sentence counting, fixed phrases, actual NFC placement for responses/comparison strings, kwargs filtering, strict/loose candidates and combination, checker initialization/lifecycle and exception semantics. Do not substitute English utilities or add an English-failure-then-Ko OR fallback.

Keep Known Issues unchanged: `평화/peace` in 1203, `포식자/predatory` in 2142, `강도/robber` in 3345, fixed choices in 227, inclusive/exclusive limits in 1092/1268 and characters/words in 3538. Manage correction overlays as separate experiments/reports.

French currently reuses English `ifeval_metrics`. Option B must preserve that import and the English policy. The existing Inspect scorer returns only two prompt-level values; modifying a shared metric does not establish four-metric Inspect support.

Retain per-file provenance, license headers and change records. Check dataset-card licensing and imported-code notices separately.

Sources: [French task](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py), [Ko checkers](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py), [Ko utilities](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py).

<a id="validation-plan"></a>

## 6. Test plan and execution records

### 6.1. Execution order

Proceed in this order. Verify selection type/path coverage before model execution, and run existing-task regressions immediately after shared-code changes. Completion status follows the analysis report.

| Stage | Work | Completion evidence |
| --- | --- | --- |
| 1. Pin reference/environment | Record data, Ko code, harness, Lighteval and dependency revisions | Reconstructible input/source/environment manifest |
| 2. Select/load prompts | Verify section 6.3 ID/path/multiple/repeated-instruction rules, then key/prompt/kwargs alignment | Coverage counts and team-confirmed selection; no omissions, duplicates or mapping errors |
| 3. Registered task/stored-response regression | Compare original Ko/new task with section 6.2 pass/fail/boundary inputs | All target IDs/paths match judgments and aggregates without a model |
| 4. Existing-task regression | Compare English and affected French paths before/after shared-code changes | No unintended judgment changes; run immediately after common-code edits |
| 5. Selected-prompt integration | Generate, save and rescore with the agreed model/selection | Confirm assistant extraction, termination, truncation, memory, failures and individual judgment agreement |
| 6. Full-split evaluation | Generate/save/rescore all prompts under the validated settings | Every key processed; four metrics and mismatch list recorded |

See [analysis verification status](analysis.en.md#verification-status). Existing English/Ko difference analysis does not replace parity results for the new task.

<a id="fixed-response-regression"></a>

### 6.2. Registered-task and stored-response validation

These checks use stored responses without a model. Send identical scorer inputs to original Ko/new task and compare index-specific strict/loose flags, prompt judgments and aggregates. T8 runs immediately after shared-code changes and must pass before model integration.

| Test | Input | What to inspect | Acceptance |
| --- | --- | --- | --- |
| T1. Data structure | Entire pinned split | 342 unique keys, 21 IDs, 481 occurrences; ordered instruction/kwargs alignment | No missing/duplicate keys, unregistered IDs or length mismatches |
| T2. Doc conversion | Repeated/multiple-ID prompts such as `1203` | query, specific, key, source prompt and nominal choices/gold | Matching mapped fields; distinguish the two frequency instructions by index |
| T3. Every type/path | At least one pass/fail response for each of section 6.3.2's 21 IDs/25 paths; applicable N−1/N/N+1 | Trace `(key, instruction_index, ID, input path)`; catch always-True/False implementations and boundary errors | Match original Ko instruction/prompt strict/loose judgments and intended exception contracts |
| T4. Ko input handling | NFC/NFD, None/0/empty kwargs, particles and fixed phrases | Response-entry NFC, string-specific normalization, `if v` and regex boundaries | Same judgments, passed values and call traces |
| T5. Loose/lifecycle | Single/multiline text, stars, empty candidates, multiple instructions | Eight candidates in order, duplicates, empty exclusion, instruction OR/prompt AND, all strict→all loose and fresh phase checkers | Same candidates, complete call order, construction traces and flags |
| T6. Four metrics | `[[True, True, True], [False]]` and uneven instruction counts | Prompt mean versus flattened instruction mean | 0.5 and 0.75 respectively; matching four-metric numerators/denominators |
| T7. Existing 86 cases | Existing cases and stored Ko responses | Instruction/prompt strict/loose through the new registered task | 100% Boolean agreement with original Ko |
| T8. Existing paths | Pinned English inputs, French adapter and cross-language execution | Public exports, judgments, metric isolation, optional-dependency loading | Existing behavior unchanged; mandatory for B, shared-change scope checked for A too |

Additional response/parameter variants cover single/double Markdown emphasis, empty strings, whitespace, newlines, regex boundaries, first-paragraph case `3073` and last-paragraph case `1954`. Distinguish synthetic inputs from real data conditions.

For `language:response_language`, preserve the language requested by original `kwargs.language`. Check Korean, other languages, empty/short/mixed text and internal language-detection exceptions under a pinned environment. Missing/invalid kwargs, random fallbacks and other postscript markers are separate from the 25 normal-data paths.

Matching an expected exception validates the error contract, not successful scoring. Distinguish internally caught exceptions from propagated errors. Investigate nondeterminism while recording seeds, repeated runs and worker settings. Loose transformations may recover failing responses, so declare strict/loose expectations separately.

Check both checker diagnostics and the actual registered-task path. Follow [analysis section 9.2](analysis.en.md#92-comparison-method-and-acceptance-criteria) for individual judgments, denominators and tolerance. Fixtures and original-reference execution for all 21 types/25 paths are complete in sections 6.2.1–6.2.4. Subsequent **registered-task validation passed all 156 fixed-response and 18 auxiliary cases**; see [analysis section 9.3.5](analysis.en.md#935-model-free-integration-validation-of-the-registered-task). Section 6.3's sample-coverage counts measure input inclusion only.

#### 6.2.1. Stored-response implementation preserving the existing result format

`evidence/checker-audit/` contains input generation, execution, verification and results. `cases.json` and both raw result files use 156 cases. `baseline.json` preserves baseline inputs, judgments and environments for provenance. `build_cases.py` reads the pinned registry AST to locate checkers. Repeated IDs require explicit `instruction_index`. The LF hash of extracted baseline inputs must match the stored oracle's input hash.

The evidence and [reproduction commands](evidence/checker-audit/README.en.md) share one folder. The original `case/full/isolated/diagnostics` layout and English/Ko comparison columns are retained, adding `targets`, predeclared Ko expectations, input/response hashes, cache keys, revisions and phase/index call traces. `original_*` preserves English source provenance. Actual comparisons give the English evaluator **Ko inputs** too; verify equal `evaluated_input` and hashes on both sides.

| Check | Composition/denominator | Verified result |
| --- | --- | --- |
| Stored responses | 156 cases: 116 original-data conditions, 2 in-memory overrides, 38 synthetic; 247 full-evaluation occurrences | Predeclared Ko/full/isolated strict/loose agreement; zero unhandled exceptions |
| Auxiliary compatibility/errors | 18 synthetic inputs: Ko 10 normal returns/8 expected exceptions; English 16/2, in each of strict and loose | Verify independent oracles. Normal returns include F; exceptions are excluded from successful scoring and 21-type coverage |
| Baseline reproduction | 86 baseline cases checked by both evaluators within the experiment | Exact 86/86 stored-row agreement per side, in `baseline_reproduction` and the comparison table |
| Source prompt collection | Add last-paragraph key 1954 and Russian-language key 240 to the 23-prompt proposal | 25 collected prompts/42 instructions; with baseline prompts, 32 source prompts/55 instructions |

The 156-case experiment and 18 auxiliary inputs give 174 input records. The model integration proposal remains **23 prompts/40 instructions**.

#### 6.2.2. Dedicated targets and boundaries for 21 types/25 paths

[coverage.json](evidence/checker-audit/coverage.json) counts only explicit `targets` in unchanged-data cases. **All 21/21 types and 25/25 paths have a response passing strict/loose (TT) and one failing both (FF).** Incidental appearance in full evaluation is insufficient. The 25 paths count checks selected by normal kwargs, not all code branches.

For 13 count conditions, N−1/N/N+1 responses were constructed and actual checker counts observed. In 1203, index 0 checks 전쟁≥8 and index 1 checks peace≥10. Both strict and loose cover `[T,T]`, `[T,F]`, `[F,T]`, `[F,F]`. [source_rows.json](evidence/checker-audit/source_rows.json) preserves full original prompts, instruction order and all 24 kwargs fields.

| Diagnostic | Original Ko strict/loose | Behavior to preserve |
| --- | --- | --- |
| 1268: six sentences on one line / multiple lines | F/F / F/T | Actual `<6` condition; line deletion can recover loose |
| 136: ten bullets with two blank lines at each end / no padding | F/F / F/T | Distinguish strict failure from loose failure |
| 3073: five paragraphs | F/T | Removing the last line produces a four-paragraph candidate |
| 2142: 포식자 twice / predatory twice | F/F / T/T | Preserve prompt/kwargs mismatch |
| 3538: 602-character, one-word response | Frequency T, word count F in both phases | Preserve 600-character request versus 600-word kwargs |
| 1954: last paragraph / only first paragraph begins with 요약 | T/T / F/F | Check the first word of the last of seven paragraphs |
| 3750: include two fixed response phrases together | T/T | Preserve original substring acceptance |

Declare expectations separately because strict failures may recover in loose. Expectations come from the builder and stored Ko baseline, never overwritten by observations. Store all full-evaluation flags and prompt judgments even if an untargeted instruction fails.

#### 6.2.3. Original engine contracts and auxiliary error checks

Frames of executing functions were observed without modifying original `utils.py`. Traces retain actual call arguments, checker-local values after processing, counts, object construction and initialization. Checks cover response NFC, per-checker string normalization including `first_word`, original `if v`, eight loose candidates' order/duplicates/empty exclusion, instruction OR, prompt AND, all strict→all loose and fresh phase checkers. Diagnostic checkers are constructed after scoring, and RNG state is restored afterward to preserve scoring randomness.

Checks include filters for `None`, 0, empty strings/lists; Korean/Russian requirements; empty responses and short numeric input. `123` is T/T for language because the reference catches `LangDetectException`; empty response is F/F. Uneven `[[T,T,T],[F]]` gives 0.5 prompt and 0.75 instruction accuracy. Four registered but data-unused types were also checked. AttributeError from `capital_word_frequency`'s `instructions_util.nltk` reference and KeyError for unregistered `key_sentences` are recorded as error-contract observations.

Auxiliary inputs declare `expected_original` and `expected_ko` separately before execution. `compare.py` checks full/isolated strict/loose instruction and prompt Booleans or exception types on both sides without replacing expectations with observations. English has 16 normal returns/2 expected exceptions and Ko 10/8. Preserve their differences: missing keywords return F in English and raise ValueError in Ko; capital-word frequency returns an English Boolean and raises AttributeError in Ko.

All 25 [verification-tool tests](evidence/checker-audit/test_audit.py) pass. They detect incorrect indexes, duplicate `case_id`, altered source conditions, stale hashes, repeated-ID collapse, cross-phase checker sharing, candidate deduplication, incorrect candidate combination and exceptions converted to normal scores, among other errors. Distinct response hashes/cache keys prevent overwriting multiple responses for one source key.

#### 6.2.4. Reproduction materials and port completion criteria

| Evidence | Local files |
| --- | --- |
| Commands and scope | [README.en.md](evidence/checker-audit/README.en.md) |
| Inputs, expectations and comparison | [cases.json](evidence/checker-audit/cases.json), [results.en.md](evidence/checker-audit/results.en.md), [results.json](evidence/checker-audit/results.json) |
| Provenance, hashes, environment, scope | [manifest.json](evidence/checker-audit/manifest.json), [coverage.json](evidence/checker-audit/coverage.json) |
| Optional local ZIP | Generate `evidence/checker-audit/attachments/ifeval-ko-regression.zip` with `package_results.py`; issue drafts are excluded |

The original experiment verifies English/Ko judgment differences and execution behavior. The new task must receive identical inputs/responses and match every instruction/prompt strict/loose Boolean, all four numerators/denominators and metric values within absolute error ≤1e-12. Require zero omissions, unhandled exceptions and unresolved mismatches. The 8 expected Ko exceptions and 2 expected English exceptions are not successful scoring for their respective evaluators. Subsequent registered-task validation met these criteria; see [analysis section 9.3.5](analysis.en.md#935-model-free-integration-validation-of-the-registered-task). **Existing English/French regression, optional-dependency loading, 23-prompt model integration and full-split model evaluation remain pending.**

Dependencies are source/input integrity → baseline reproduction → Ko expectation confirmation → identical-response comparison with the new task → English/French, object-isolation and dependency regressions → 23-prompt model integration → all 342 prompts/481 instructions. Work is complete through identical-fixed-response comparison with the new task, with actual outputs and result files attached to team code PR #2.

<a id="selection-rules"></a>

### 6.3. Prompt selection rules and validation scope

Select prompts using these rules:

1. Include each of the **21 instruction IDs actually used in pinned data** at least once.
2. Include each of section 6.3.2's **25 normal-data `(ID, input path)` pairs** at least once. These distinguish kwargs-selected operations or regexes.
3. Include at least one **repeated-ID prompt and one multiple-instruction prompt**. Use repeats to verify index/kwargs/judgment alignment.
4. Include mismatch diagnostics `1203`, `2142`, `1268`, `3538` without editing original prompts/kwargs.

Type/path inclusion determines prompt selection; model-free stored-response regression in section 6.2 checks scoring behavior. Do not use selection scores to estimate whole-dataset model performance.

#### 6.3.1. Proposed prompts and instruction-type mapping

The proposal contains **23 prompts/40 instructions**, pending team review:

```json
[3743, 136, 3518, 1233, 3445, 3442, 1262, 1082, 1127, 3710,
 122, 3563, 1107, 3073, 3311, 3750, 1203, 2142, 1268, 3538,
 1928, 2035, 1800]
```

The comparison uses `train` at the [pinned data revision](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/54199e3801116897697babf341865741dcd06fc8). Comparing IDs across all 342 prompts/481 instructions with the selection confirms **21/21 types**. Key `1203` is the one repeated-ID prompt; 13 prompts have multiple instructions.

Occurrence counts are not prompt counts: both `keywords:frequency` instructions in 1203 count separately.

| Instruction ID | Full occurrences | Selected occurrences | Selected keys | Ko change evidence |
| --- | --- | --- | --- | --- |
| `combination:repeat_prompt` | 26 | 1 | 3563 | Author-listed modified class |
| `combination:two_responses` | 19 | 1 | 1107 | — |
| `detectable_content:number_placeholders` | 20 | 1 | 3743 | — |
| `detectable_content:postscript` | 19 | 2 | 3710, 1800 | — |
| `detectable_format:constrained_response` | 10 | 1 | 3750 | Ko fixed response phrases |
| `detectable_format:json_format` | 14 | 1 | 3518 | — |
| `detectable_format:multiple_sections` | 11 | 1 | 1127 | — |
| `detectable_format:number_bullet_lists` | 24 | 1 | 136 | — |
| `detectable_format:number_highlighted_sections` | 38 | 2 | 3710, 2035 | — |
| `detectable_format:title` | 27 | 5 | 3442, 1262, 3710, 3311, 1928 | — |
| `keywords:existence` | 22 | 2 | 3518, 3311 | Author-listed modified class |
| `keywords:forbidden_words` | 28 | 1 | 3445 | Author-listed modified class |
| `keywords:frequency` | 25 | 6 | 1233, 1203, 2142, 3538, 1928 | Author-listed modified class |
| `language:response_language` | 25 | 1 | 3311 | — |
| `length_constraints:nth_paragraph_first_word` | 2 | 1 | 3073 | Author-listed modified class |
| `length_constraints:number_paragraphs` | 19 | 1 | 1082 | — |
| `length_constraints:number_sentences` | 31 | 3 | 1262, 1268, 2035 | Ko sentence utility |
| `length_constraints:number_words` | 36 | 3 | 136, 3442, 3538 | Ko word utility |
| `punctuation:no_comma` | 42 | 2 | 1107, 1928 | — |
| `startend:end_checker` | 15 | 2 | 1233, 1127 | Author-listed modified class |
| `startend:quotation` | 28 | 2 | 122, 2035 | — |

Modified-class labels follow the [class/registry audit](evidence/analysis-details.en.md#ko-classes).

#### 6.3.2. Checker paths selected by kwargs

We examined `build_description` and `check_following` in the 21 data-used classes of the [pinned Ko checker](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py). Four types select different operations/regexes based on normal kwargs values. The counting script checks the relevant AST and actual data values.

| Instruction type | Parameter | Condition | Selected keys |
| --- | --- | --- | --- |
| `detectable_content:postscript` | `postscript_marker` | `P.P.S` | 3710 |
| `detectable_content:postscript` | `postscript_marker` | `P.S.` | 1800 |
| `keywords:frequency` | `relation` | `at least` | 1233, 1203, 2142, 3538 |
| `keywords:frequency` | `relation` | `less than` | 1928 |
| `length_constraints:number_sentences` | `relation` | `at least` | 2035 |
| `length_constraints:number_sentences` | `relation` | `less than` | 1262, 1268 |
| `length_constraints:number_words` | `relation` | `at least` | 3538 |
| `length_constraints:number_words` | `relation` | `less than` | 136, 3442 |

`relation` distinguishes `<N` and `≥N`; postscript markers select different regexes. These eight paths plus default paths for 17 other types give **25 `(ID, input path)` pairs, all covered**. [Full coverage output](evidence/sample-coverage/coverage.json) records types, path occurrences and instruction indexes.

This denominator counts paths selected by normal data. Other thresholds, words and languages are arguments to the same operations, not separate paths per value. The pinned data has no active checker argument that is missing or should be removed by original `if v` filtering.

Section 6.2 covers response-dependent success/failure, emphasis syntax, regexes, paragraph positions, NFC/NFD and numeric boundaries. Missing/invalid inputs, random fallbacks and other postscript markers absent from the data are separate stored-response checks. **25/25 is neither code-branch execution coverage nor proof that response regression has passed.**

#### 6.3.3. Diagnostic prompts and purposes

| Key | Diagnostic | Rationale |
| --- | --- | --- |
| `1203` | Prompt requests ‘평화’; checker uses `peace`; repeated ID | Preserve both frequency indexes, kwargs, judgment order and checked words |
| `2142` | Prompt requests ‘포식자’; checker uses `predatory` | Preserve judgments despite the keyword mismatch |
| `1268` | “At most 6 sentences” versus `<6` | Inspect wording/operator mismatch and exactly-six boundary |
| `3538` | “At least 600 characters” versus at least 600 words | Inspect unit mismatch and long-output termination/truncation |
| `136` | Bullets and word count | Inspect interaction and strict/loose candidates |
| `3445` | Forbidden word with attached Korean particle | Inspect regex-boundary difference between ‘컴퓨터’ and ‘컴퓨터를’ |
| `3750` | Fixed-phrase substring matching | Inspect acceptance of one or several choices in one response |

Check mismatch cases under original conditions, separately from data-correction experiments. Track the length-unit mismatch in `3538` for further review.

#### 6.3.4. Selection completion and mismatch handling

- Selection is complete when all four section 6.3 rules hold with zero missing IDs/paths. If source data/code changes, recount denominators and path definitions first.
- Before model evaluation, original Ko/new-task judgments must match on per-ID/path pass/fail responses and required boundaries. Record input inclusion and regression success separately.
- On mismatch, add the reproducing response and neighboring boundary cases for `(key, instruction_index, ID, input path)`. Fix the cause and rerun relevant regressions. If a missing path caused it, add an original prompt covering that path. Unresolved mismatches prevent completion.
- After replacing prompts, recount coverage to detect lost IDs/paths. Update selected keys, reasons and actual prompt/instruction counts in the report and run config.

### 6.4. Result comparison criteria

Follow analysis section 9.2. Generate and save responses once, then send identical prompts/responses to original Ko/new Lighteval-Ko. Compute prompt/instruction counts from the actual selected list.

| Comparison | Criterion for final selection |
| --- | --- |
| Input alignment | Loaded keys/counts match final selection; original order/kwargs preserved |
| Instruction judgments | Every selected instruction matches strict/loose Booleans |
| Prompt judgments | Every selected prompt matches strict/loose all-pass judgments |
| Aggregation | Matching four-metric numerators/denominators; absolute error ≤`1e-12` |
| Execution | All generation/scoring complete; no omissions/unhandled errors; no failures hidden as empty responses or reduced denominators |
| Existing paths | Preserve English/French judgments, public exports and metric isolation; label synthetic-adapter-only evidence accordingly |

### 6.5. Selection evidence and reproduction materials

Inputs, code and outputs for section 6.3 are attached under `evidence/sample-coverage/`.

| File | Contents |
| --- | --- |
| [README.en.md](evidence/sample-coverage/README.en.md) | Scope, denominators, environment and reproduction commands |
| [selection.json](evidence/sample-coverage/selection.json) | 23 selected keys, diagnostics and proposal status |
| [audit_coverage.py](evidence/sample-coverage/audit_coverage.py) | Pinned source hashes, registry/checker AST, ID/path/repeated/multiple-instruction counts |
| [coverage.json](evidence/sample-coverage/coverage.json) | Source URLs/revisions/hashes, script/input hashes, environment and index-specific raw counts |
| [coverage.en.md](evidence/sample-coverage/coverage.en.md) | Type and path tables for the same counts |

A [156-case experiment](evidence/checker-audit/results.en.md) used stored responses. Its scope is:

| Scope | Baseline composition | 156-case experiment result |
| --- | --- | --- |
| Cases | 46 unchanged-data, 2 overrides, 38 synthetic; 11 unique keys | 116 unchanged-data, 2 overrides, 38 synthetic; 32 unique keys; includes reproduction checks for 86 baseline cases |
| Dedicated targets | 8 IDs | Dedicated strict/loose TT and FF for 21 types/25 paths |
| Incidental full-evaluation conditions | JSON, sections, bullets, highlights, title: 5 types | Promoted to explicit targets with indexed isolated/full checks |
| Absent types | Two responses, placeholders, postscript, fixed choices, language, paragraph count, no-comma, quotation: 8 types | All supplemented with dedicated pass/fail responses |

Both references ran through full-package imports to verify reproduction and identical-Ko-input judgments. Raw results and the comparison table retain this evidence. This reference experiment does not execute the new task or generate model responses. Subsequent new-task validation is recorded separately in analysis section 9.3.5. The 156 regression cases and 23 model-integration prompts are different units.

### 6.6. Analysis-report updates and current status

Record integration execution settings, selected keys, results and artifacts in the analysis report. Include instruction-type mapping and input-condition coverage as selection evidence.

The script in section 6.5 has counted and attached coverage for 23 prompts/40 instructions. Sections 6.2.1–6.2.4 record the 156-case reference experiment and 18 auxiliary inputs. Subsequent model-free new-task validation is documented in [analysis section 9.3.5](analysis.en.md#935-model-free-integration-validation-of-the-registered-task), with code revisions, execution evidence, individual judgments and four metrics. Model integration remains pending.

## 7. Work allocation and schedule

Detailed contributions by each member are recorded under [people](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/tree/main/people) on the `main` branch.

| Week | Owner | Work | Related records |
| --- | --- | --- | --- |
| Week 1 | Entire team | Each member opened their first PR. Team members reviewed one another's PRs and opened the team's PR. | [Yejun's contribution record](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/main/people/joony0905.md) · [Junseop's contribution record](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/main/people/SubJeeLee.md) · [Hyeongjun's contribution record](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/main/people/kiimyjun.md) |
| Week 2 | [Yejun Song](https://github.com/joony0905), [Junseop Lee](https://github.com/SubJeeLee), [Hyeongjun Kim](https://github.com/kiimyjun) | Yejun wrote the IFEval-Ko benchmark report and requested review. Junseop and Hyeongjun reviewed the report and each made revisions based on their review. | [PR #18](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/18) |
| Week 3 | [Yejun Song](https://github.com/joony0905) | Revised the benchmark report in response to review feedback and drafted `design.md`. | [PR #18](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/18) |
| Week 3 | [Junseop Lee](https://github.com/SubJeeLee) | Wrote `issue-draft.md`, the draft upstream issue for Lighteval. | [PR #18](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/18) |
| Week 3 | [Hyeongjun Kim](https://github.com/kiimyjun) | Reviewed candidate comparison models and selected the model for the initial experiment. Documented the rationale for selecting validation prompts by instruction type. | [PR #18](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/18) |
| Week 4 | [Yejun Song](https://github.com/joony0905) | Documented judgment differences between the original English and Ko evaluators, expanded fixed-response regression cases **from 86 to 156**, and added English documentation. | [PR #30](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/30) |
| Week 4 | [Junseop Lee](https://github.com/SubJeeLee) | Opened an upstream issue proposing a dedicated Ko package and requesting feedback on the scope of Inspect support. | [Upstream issue #1463](https://github.com/huggingface/lighteval/issues/1463) |
| Week 4 | [Hyeongjun Kim](https://github.com/kiimyjun) | Aligned the integration validation sample in `analysis.md` and `design.md` to **23 prompts and 40 instructions**. | [PR #30](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/30) |
| Week 4 | [Yejun Song](https://github.com/joony0905) | Implement NFC normalization and strict/loose scoring in `scoring.py`. Verify 100% agreement with the original Ko evaluator for each instruction and prompt across **156 fixed-response cases**. Open a PR in the team fork `Hugging-Face-KREW/lighteval` targeting `team-c/ifeval-ko`. | [PR #30](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/30) |
| Week 4 | [Junseop Lee](https://github.com/SubJeeLee) | Port the original Ko `instructions.py`, `instructions_registry.py` and `instructions_util.py`. Preserve source attribution and license headers, and adapt import paths to the package structure. | [PR #30](https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/30) |
| Week 4 | [Hyeongjun Kim](https://github.com/kiimyjun) | Implement `Doc` conversion, dataset and zero-shot settings, and the four evaluation metrics in `main.py`; register `ifeval_ko` in `TASKS_TABLE`. Run `lighteval tasks inspect` without a model and compare the output with the original prompts. Attach the output and comparison results to the code PR. |  |
| Week 4 | Entire team | Integrate each member's implementation under `src/lighteval/tasks/tasks/ifeval_ko/` in the team fork `Hugging-Face-KREW/lighteval`, and open a code PR targeting `team-c/ifeval-ko`. | [Team branch in the fork](https://github.com/Hugging-Face-KREW/lighteval/tree/team-c/ifeval-ko) |
| Week 5 | [Hyeongjun Kim](https://github.com/kiimyjun) | Record the revision and generation settings of the comparison model selected during the session. Generate and save model responses for the 23 prompts. After integration validation passes, run all 342 prompts in the full split with the same settings. | [Design section 6](#validation-plan) |
| Week 5 | [Yejun Song](https://github.com/joony0905) | Pass the same saved responses to the original Ko evaluator and the new task. Compare strict/loose judgments for each instruction and prompt, and all four aggregate metrics. Record comparison results separately for the 23 prompts and the full 342-prompt split. For any mismatches, document a reproducible example and its cause. | — |
| Week 5 | [Junseop Lee](https://github.com/SubJeeLee) | Summarize the implementation scope, original code provenance and validation results in the PR description. Submit the code to `huggingface/lighteval` after team review and link the relevant issue. | [Upstream issue #1463](https://github.com/huggingface/lighteval/issues/1463) |
