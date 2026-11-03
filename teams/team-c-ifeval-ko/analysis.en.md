# Benchmark Analysis Report

[한국어](analysis.md) | **English**

## **1. What does it measure?**

IFEval-Ko measures how accurately an LLM follows programmatically verifiable instructions in Korean prompts.

---

## **2. Sources: paper, authors, year and official code**

| Item | Details |
| --- | --- |
| Original paper | Instruction-Following Evaluation for Large Language Models |
| Authors | Jeffrey Zhou, Tianjian Lu, Swaroop Mishra, Siddhartha Brahma, Sujoy Basu, Yi Luan, Denny Zhou, Le Hou |
| Publication | arXiv, 2023-11-14 |
| Paper | [Original paper](https://arxiv.org/abs/2311.07911) |
| **Original IFEval code** | [Google Research IFEval — the paper's English evaluation code](https://github.com/google-research/google-research/tree/master/instruction_following_eval) |
| **IFEval-Ko scoring code** | [Allganize IFEval-Ko — the Korean scoring reference](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/main/ifeval_ko) |
| **Contribution target** | [Hugging Face Lighteval — the evaluation framework for the port](https://github.com/huggingface/lighteval) |
| **Team repository** | [Hugging-Face-KREW/lighteval — the fork for implementation and team review](https://github.com/Hugging-Face-KREW/lighteval) |

---

## **3. Dataset: Hugging Face ID, config, split, size, fields and two examples**

### **3.1. Basic information**

| Item | English IFEval | IFEval-Ko |
| --- | --- | --- |
| Hugging Face ID | **`google/IFEval`** | **`allganize/IFEval-Ko`** |
| Config | **`default`** | **`default`** |
| Evaluation split | **`train`** | **`train`** |
| Prompts | 541 | 342 |
| Main storage format | JSONL | Parquet |
| Model input | **`prompt`** | **`prompt`** |
| Scoring information | **`instruction_id_list`**, **`kwargs`** | **`instruction_id_list`**, **`kwargs`** |

Prompt counts, configs and splits come from the [English dataset card](https://huggingface.co/datasets/google/IFEval) and [Ko dataset card](https://huggingface.co/datasets/allganize/IFEval-Ko). `train` is the published split name. This task uses it for evaluation; it does not train the model. Few-shot prompting during dataset construction is also distinct from the zero-shot model evaluation.

### **3.2. Fields**

| Field | Meaning |
| --- | --- |
| **`key`** | Prompt identifier, distinct from row position |
| **`prompt`** | Natural-language request presented to the model |
| **`instruction_id_list`** | Instruction types checked in the response |
| **`kwargs`** | Parameters aligned with each instruction, such as keywords, counts and comparison relations |

### **3.3. Example 1 — key 3345**

The prompt requires using ‘강도’ (robber) at least twice, writing two bullets and avoiding specified words. However, the first checker parameter still contains **`robber`**.

```json
{
  "key": 3345,
  "instruction_id_list": ["keywords:frequency", "detectable_format:number_bullet_lists", "keywords:forbidden_words"],
  "kwargs": [
    {"keyword": "robber", "frequency": 2, "relation": "at least"},
    {"num_bullets": 2},
    {"forbidden_words": ["죽이다", "도살", "점령", "침략"]}
  ]
}
```

The checker searches the strings in **`kwargs`** without translating the request's meaning again. Korean strings in source examples are preserved verbatim throughout this report.

### **3.4. Example 2 — key 3442**

This prompt asks for an answer to a riddle in fewer than 20 words, with a title enclosed in double angle brackets.

[Experiment: key 3442](evidence/checker-audit/README.en.md#representative-cases)

```json
{
  "key": 3442,
  "instruction_id_list": ["length_constraints:number_words", "detectable_format:title"],
  "kwargs": [
    {"num_words": 20, "relation": "less than"},
    {}
  ]
}
```

**`less than 20`** means strictly fewer than 20. Different word-counting rules can change the judgment at this boundary.

---

## **4. Licensing and access**

| Resource | Finding |
| --- | --- |
| English IFEval data | Apache-2.0 |
| IFEval-Ko data | Apache-2.0, following the original license |
| Ko [**`instructions.py`**](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/ifeval_ko/instructions.py) | Retains Google Research's Apache-2.0 copyright and license header |
| Contribution target, Lighteval | Repository-root [LICENSE](https://github.com/huggingface/lighteval/blob/main/LICENSE): MIT |

---

<a id="official-evaluation"></a>

## **5. Official evaluation procedure**

### **5.1. Prompts and few-shot settings**

Both the English harness and Ko task YAML use **`doc_to_text: prompt`**, **`output_type: generate_until`** and **`num_fewshot: 0`**.

The few-shot prompting described in the paper filters and rewrites prompts during dataset construction. It does not provide examples to the model under evaluation.

The reviewed [English harness YAML](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/ifeval/ifeval.yaml) and [Ko task YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/ifeval_ko/ifeval_ko.yaml) specify these generation settings:

| Setting | English harness | Ko reference |
| --- | --- | --- |
| **`do_sample`** | **`false`** | **`false`** |
| **`temperature`** | **`0.0`** | **`0.0`** |
| **`max_gen_toks`** | 1280 | 1280 |
| **`until`** | **`[]`** | **`["<end_of_turn>", "<\|im_end\|>"]`** |

1,280 limits generated tokens, a different unit from checker-counted words. Integration validation must record and align the model, chat template, generation settings and termination settings.

### **5.2. Scoring path and response extraction**

```text
Prompt → generate a response or load a stored response
→ construct checkers from instruction_id and kwargs
→ obtain strict / loose judgments for each instruction
→ aggregate at prompt and instruction levels
```

Framework response extraction and post-processing are also part of the comparison with the scoring path in [Ko `utils.py`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/main/ifeval_ko/utils.py).

### **5.3. Strict and loose**

Strict checks the response after the evaluator's standard preprocessing. IFEval-Ko applies NFC normalization before both strict and loose checks.

Loose checks eight candidates produced by removing `*`, the first line and the last line, separately or in combination. Transformations may produce duplicates, so there may be fewer than eight distinct strings. Empty candidates cannot pass. Other Markdown characters such as `#`, `>` and `-` are not all removed.

Each instruction is checked independently. Different instructions may pass on different candidates; a single candidate need not satisfy every instruction.

```text
Instruction loose = at least one candidate passes that checker
Prompt loose = every instruction's loose judgment is True
```

Lighteval must preserve this candidate generation and aggregation.

### **5.4. Four metrics**

| Metric | Meaning |
| --- | --- |
| **`prompt_level_strict_acc`** | Fraction of prompts passing every instruction under strict evaluation |
| **`inst_level_strict_acc`** | Fraction of all instruction occurrences passing strict evaluation |
| **`prompt_level_loose_acc`** | Fraction of prompts passing every instruction under loose evaluation |
| **`inst_level_loose_acc`** | Fraction of all instruction occurrences passing loose evaluation |

For $N$ prompts with $m_i$ instructions in prompt $i$, prompt accuracy divides the number of fully passing prompts by $N$. Instruction accuracy divides passing instructions by $\sum_i m_i$; it does not average per-prompt instruction accuracies. If three instructions in one prompt pass and the single instruction in another fails, instruction accuracy is $3/4=0.75$ and prompt accuracy is $1/2=0.5$. Higher values indicate greater instruction compliance for all four metrics.

### **5.5. Results reported in the paper**

These are English IFEval results from [Table 3 of the original paper](https://arxiv.org/pdf/2311.07911), in percent.

| Model | Prompt strict | Instruction strict | Prompt loose | Instruction loose |
| --- | --- | --- | --- | --- |
| GPT-4 | 76.89 | 83.57 | 79.30 | 85.37 |
| PaLM 2 S | 43.07 | 55.76 | 46.95 | 59.11 |

These English reference values use responses from November and August 2023. They are not Korean baseline scores or port acceptance criteria. Comparisons require matching models, data and settings.

Korean scores and charts on the [Allganize dataset card](https://huggingface.co/datasets/allganize/IFEval-Ko) are externally published results. Their `Strict Accuracy (%)` label does not sufficiently establish prompt versus instruction level, loose scores or execution revisions, so they are not port validation targets. Execution and attachment plans are in [design.en.md](design.en.md).

---

## **6. Existing implementations and the rationale for the Ko port**

| Implementation | Role |
| --- | --- |
| Google Research IFEval | Background on the original methodology and English code |
| lm-evaluation-harness | Pinned English evaluator used for comparison |
| Allganize IFEval-Ko | Direct reference for Korean scoring behavior |
| Hugging-Face-KREW/lighteval | Port target and existing English/French metric paths |

### **6.1. Why French reuses the metric while Ko needs adaptation**

**The French integration reused existing scoring rules, whereas Ko changes accepted phrases, length counting and normalization.** Reuse of `ifeval_metrics` is documented in French [PR #505](https://github.com/huggingface/lighteval/pull/505), its [review](https://github.com/huggingface/lighteval/pull/505#discussion_r1924874919), the [author's reply](https://github.com/huggingface/lighteval/pull/505#discussion_r1925047054) and the [pinned task code](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py#L28-L40). This was the integration's design choice; it does not guarantee that every English rule suits French.

Ko changes are supported by the [authors' documentation](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/README_Ko.md) and [utilities](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py). The following representative controls sent identical synthetic responses to the existing Lighteval metric, French adapter, English harness and original Ko evaluator. The three English-metric paths agreed; strict and loose both gave the results below.

| Case ID · condition and response | Existing English paths | Original Ko |
| --- | --- | --- |
| `word_comma_lt2` · 사과,배,포도 / fewer than 2 words | 3 words → fail | 1 word → pass |
| `sentence_no_space_ge2` · 첫 문장입니다.둘째 문장입니다. / at least 2 sentences | 1 sentence → fail | 2 sentences → pass |
| `ko_fixed_choice` · 제 답변은 예입니다. / fixed response phrase | Fail | Pass |
| `nfd_keyword` · keyword=가, response=U+1100 U+1161 | Fail | Pass after response NFC |

Changing only the dataset address can therefore change scores relative to the Ko reference. A shared scoring loop, equivalent format checks and aggregation may be reused, but Ko checkers, utilities, fixed phrases, NFC and kwargs handling must be connected. These controls demonstrate counting-rule differences, not model performance or evaluation of the entire French dataset. [Additional language controls](evidence/analysis-details.en.md#language-controls) preserve more cases and their interpretation limits.

#### **6.1.1. Bidirectional decision boundaries on identical Ko inputs**

We conducted a **156-case experiment**, passing the same Ko prompt, instruction order, effective kwargs and response to the original English harness and Ko evaluator. The [experiment results](evidence/checker-audit/results.en.md) record input and response hashes, reproduction checks, individual judgments and aggregates.

| Primary target judgment `(English, Ko)` | Strict | Loose |
| --- | ---: | ---: |
| `(T,T)` | 74 | 84 |
| `(T,F)` | 13 | 8 |
| `(F,T)` | 22 | 21 |
| `(F,F)` | 47 | 43 |

Each case contributes one primary target, giving a denominator of 156 in each phase. Raw results also retain additional targets and every instruction judgment from full evaluation. At key 349's `<40` boundary, English counts 39 words and Ko counts 40: English passes both phases and Ko fails both. At key 3442's `<20` boundary, English counts 20 and Ko counts 18, producing the reverse judgment. Line deletion can also turn strict failure into loose success, so both judgments are recorded separately.

These results support preserving Ko counting functions, fixed phrases, normalization, checker construction and execution order. Option A in [design section 1.3.1](design.en.md#131-evidence-for-option-a-from-identical-ko-inputs) is recommended for the initial implementation because it is easy to compare directly with the reference and limits changes to existing English/French code. Option B can also work if it preserves the same policies and checker lifecycle. Acceptance requires agreement between the new Ko task and the original Ko evaluator. Translation mismatches, unit mismatches and reference errors are recorded as Known Issues and preserved during the port.

### **6.2. Preservation scope and implementation handoff**

Preserve the original Ko data and scoring behavior. Translation corrections and scoring-policy improvements belong in separate Known Issues. Of the seven modified classes listed by the authors, `KeySentenceChecker` is unregistered; English-specific conditions are unused in the Ko data but remain registered. The [class and registry audit](evidence/analysis-details.en.md#ko-classes) provides the detailed counts.

Architectures A/B, Doc conversion, metric/Inspect paths and exception/fallback preservation are specified in the [design document](design.en.md#task-structure). The criterion is agreement with pinned Allganize code on the same stored responses. This does not mean that a new API or Ko task has already been implemented.

---

## **7. Duplicate checks and related prior work**

### **7.1. Search date, targets and queries**

The following 20 searches were performed on **2026-10-30 (KST)**. PR searches covered all states; issue searches covered open and closed issues, returning at most 50 records per query.

| Target and scope | Query | Searches | Findings in returned results |
| --- | --- | --- | --- |
| PRs and issues in Lighteval upstream, the team fork and harness | `"IFEval-Ko" OR "ifeval_ko" OR "allganize/IFEval-Ko"` | 6 | Zero results in each search |
| PRs and issues in Lighteval upstream and harness | `IFEval Korean` | 4 | Zero results in each search |
| PRs in Lighteval upstream and harness | `IFEval multilingual` | 2 | Prior multilingual/dependency PRs |
| All GitHub PRs/issues, and all PRs | `"IFEval-Ko"` (PRs/issues), `"ifeval_ko"` (PRs) | 3 | Team analysis PR and NeMo-Skills Ko integration, among others |
| Lighteval upstream PRs; upstream/harness PRs | `IFEval 한국어`, `IFEval Korea` | 3 | Zero results in each search |
| Issues in Lighteval upstream and harness | `"allganize"` | 2 | Zero results in each search |

The returned results contained no Lighteval/harness maintainer instruction to change Ko checkers. This does not prove the absence of duplicate implementations or relevant comments. The 20 searches and 23-prompt integration selection are separate counts.

### **7.2. Related work and limits of the cited comments**

| Reference | Finding | Interpretation limit |
| --- | --- | --- |
| [French PR #505](https://github.com/huggingface/lighteval/pull/505), [review](https://github.com/huggingface/lighteval/pull/505#discussion_r1924874919) and [author reply](https://github.com/huggingface/lighteval/pull/505#discussion_r1925047054) | Reviewer asked whether the metric could be imported from IFEval; author confirmed it was not redefined. Merged 2025-01-23 | No guarantee of linguistic correctness for all French scoring |
| [NeMo-Skills PR #1375](https://github.com/NVIDIA-NeMo/Skills/pull/1375), [review](https://github.com/NVIDIA-NeMo/Skills/pull/1375#discussion_r3189945909) and [reference reply](https://github.com/NVIDIA-NeMo/Skills/pull/1375#discussion_r3195884717) | Reused the Ko evaluator as an external package | Maintenance example from another framework, not approval of this Lighteval design |
| [Allganize Community Discussion #2](https://huggingface.co/datasets/allganize/IFEval-Ko/discussions/2) | Data-error reports involving `prompt_to_repeat`, `section_spliter`, etc., and author replies about fixes | No instruction to redesign the Ko engine, and no evidence that cases such as 3345 were fixed |

We also consulted the English IFEval [dataset relocation PR #268](https://github.com/huggingface/lighteval/pull/268), reasoning preprocessing PRs [#791](https://github.com/huggingface/lighteval/pull/791) and [#792](https://github.com/huggingface/lighteval/pull/792), and [NLTK fix PR #1013](https://github.com/huggingface/lighteval/pull/1013). These are distinct from duplicate Ko implementations.

PRs and discussions are historical references as of the analysis date. Direct evidence for Ko adaptation comes from **pinned Allganize code and observed judgment differences on identical responses**. Other projects' design choices are not Lighteval maintainer approval.

---

## **8. Implementation challenges and Known Issues**

### **8.1. Main challenges**

Direct checker calls alone cannot validate the complete evaluation path. kwargs, instruction order, NFC, loose candidates, aggregation, dependencies, randomness and exception handling must match the Ko reference. The [design input contract](design.en.md#input-contract) specifies these details and regression checks.

### **8.2. Known Issues confirmed with the actual evaluators**

Judgments are written in **strict / loose** order. Intentional Ko adaptations, prompt/checker mismatches and scoring-policy observations are distinguished. The default port preserves original conditions even where data errors are apparent.

#### **8.2.1. String consistency and fixed choices**

| Key | Issue type | Actual stored-response result | Implementation treatment |
| --- | --- | --- | --- |
| 3345 | Data: ‘강도’ (robber) versus `robber` | `robber_full`: English robber response passes/passes; Ko 강도 response fails/fails. A separate override changing only the Ko keyword to 강도 passes/passes | Preserve kwargs; explicitly identify this as a comparison using different language-specific responses |
| 1203 | Data: ‘평화’ (peace) versus `peace` | With 전쟁 8 times and 평화 10 times, index 0 passes and index 1 fails, so the prompt fails/fails. With 전쟁 8 times and peace 10 times, the Ko prompt passes/passes | Identify repeated `keywords:frequency` by index; separate original conditions from keyword overrides |
| 2142 | Data: ‘포식자’ (predator) versus `predatory` | 포식자 twice fails/fails; predatory twice passes/passes. Under a Ko keyword override, 포식자 twice passes and once fails | Preserve the keyword; report corrections separately |
| 227 | Prompt and checker disagree on accepted phrases | All three prompt phrases beginning ‘내 대답은 …’ fail/fail in Ko. All three checker phrases beginning ‘제 답변은 …’ pass/pass. All three English phrases fail/fail in Ko | Preserve Ko options and substring matching after strip; do not broaden acceptance with an OR fallback |

For 1203, 2142 and 227, 17 additional cases—14 with original dataset conditions and 3 explicit in-memory overrides—were run through actual English/Ko full and isolated strict/loose evaluation. Every predeclared expectation matched. Overrides are neither source-data edits nor author-approved solutions. Checked words, fixed phrases and judgment paths follow the Ko checker and evaluator.

#### **8.2.2. Inequality translation mismatches**

The pinned dataset contains **14 prompts: 6 word-count and 8 sentence-count cases**, where wording meaning “at most/within N” conflicts with `relation="less than"`. Stored responses of length N−1, N and N+1 gave **42 cases run on each English and Ko evaluator**. Observed counter lengths and full/isolated target strict/loose judgments matched expectations. At exactly N, the target failed for all 14 prompts; Ko prompt judgments passed at N−1 and failed at N and N+1.

| Representative key | Response length | Ko target and prompt strict / loose |
| --- | --- | --- |
| 1092 | 299 words | Pass / pass |
| 1092 | 300 words | Fail / fail |
| 1092 | 301 words | Fail / fail |
| 1268 | 5 sentences | Pass / pass |
| 1268 | 6 sentences | Fail / fail |
| 1268 | 7 sentences | Fail / fail |

This reproduces the original `<N` behavior. Whether to change the wording to “fewer than” or the checker to `≤N` is a specification decision for the dataset authors. The default port keeps `<N`. Key 3739 is excluded from these additional mismatches because “at most 3 sentences” is followed by “only 1 or 2 sentences.”

The 14 keys and target instructions are listed below. Indexes are zero-based, distinct from row numbers.

| Key | Instruction index | Ko wording, translated | Actual condition |
| --- | --- | --- | --- |
| 164 | 0 | At most 300 words | `<300` |
| 340 | 1 | At most 30 words | `<30` |
| 1092 | 0 | At most 300 words | `<300` |
| 1879 | 1 | At most 600 words | `<600` |
| 2243 | 0 | At most 150 words | `<150` |
| 3415 | 0 | At most 200 words | `<200` |
| 286 | 1 | At most 10 sentences | `<10` |
| 1268 | 0 | At most 6 sentences | `<6` |
| 1381 | 0 | At most 10 sentences | `<10` |
| 2266 | 0 | At most 7 sentences | `<7` |
| 2674 | 0 | At most 10 sentences | `<10` |
| 2780 | 0 | Within 6 sentences | `<6` |
| 3041 | 0 | At most 7 sentences | `<7` |
| 3691 | 0 | At most 10 sentences | `<10` |

Source fields were checked against pinned Ko and English data; comparison operators were checked against the original checkers.

#### **8.2.3. Word counts and Markdown policy observations**

The following representative cases come from the **156-case experiment**. The same Korean response was passed to English and Ko evaluators, with reproduction checks and judgments recorded together.

| Key · case ID | Actual target result | Observation and treatment |
| --- | --- | --- |
| 3442 · `comma_boundary_compact` | English 20 words: fail/fail; Ko 18 words: pass/pass (`<20`) | English regex versus Ko whitespace tokenization; preserve Ko |
| 349 · `markdown_quote_valid_highlights_349` | English 39 words: pass/pass; Ko 40 words: fail/fail (`<40`) | Do not add a rule removing `>` |
| 136 · `markdown_star_balanced_136` | English 99 words: pass/pass; Ko 108 words: fail/pass | `*` removal candidates and line placement affect loose evaluation |
| 136 · `markdown_dash_persistent_136` | English pass/pass; Ko fail/fail | Loose does not remove all `-` characters |

These are actual strict/loose evaluator judgments. Counts were observed from the checkers. Preserve original Ko policies, including NFC and whitespace-based word counting.

### **8.3. Rule applicability and observed judgment differences**

Denominators are **342 pinned Ko prompts and 541 English prompts**. Repeated IDs mean unique keys and instruction occurrences must be counted separately.

| Rule | Ko unique prompts | Ko instruction occurrences | English unique prompts |
| --- | --- | --- | --- |
| Word count | 34 | 36 | 50 |
| Sentence count | 28 | 31 | 46 |
| Keyword frequency | 23 | 25 | 39 |
| Bullet count | 24 | 24 | 31 |
| Highlight count | 38 | 38 | 48 |

| Intersection of prompt sets | Ko unique keys | English unique keys |
| --- | --- | --- |
| Word count ∩ bullets | 2 | 3 |
| Word count ∩ highlights | 8 | 8 |
| Word count ∩ (bullets ∪ highlights) | 10 | 11 |
| Word count ∩ bullets ∩ highlights | 0 | 0 |

We grouped instruction lists in the pinned Ko data by ID and intersected unique-key sets. Repeated IDs contribute separately to occurrence counts. Ko word count ∩ bullets contains keys `136, 2284`. Applicability counts are neither error counts nor model-score changes. Markdown can occur without an explicit format instruction, so these intersections do not measure its total impact.

Of the 156 experiment cases, 116 preserve original data conditions (`dataset`). Among them, the target strict or loose judgment differs between English and Ko on identical Ko inputs for **11 keys: 127, 136, 349, 1127, 1237, 1242, 1480, 3073, 3442, 3739, 3750**. Synthetic cases and in-memory overrides are excluded. This observation is limited to the tested stored responses. Original-input reproduction remains supporting evidence within each case. The sentence-splitting difference for 3739 is distinguished from an inequality translation error.

The frequency of judgment differences across full model responses and their effect on total scores remain unmeasured. This analysis establishes applicability, representative counterexamples and reference judgments; the next focus is Lighteval integration and parity.

---

## **9. Validation plan and available evidence**

### **9.1. Candidate models and current status**

| Role | Model | Current status |
| --- | --- | --- |
| Environment check | `HuggingFaceTB/SmolLM2-135M-Instruct` | Ran 10 ARC Easy prompts with `batch_size=1`; not an IFEval-Ko result |
| Preferred integration/full-evaluation candidate | `Qwen/Qwen2.5-1.5B-Instruct` | Reviewed Korean support and official chat template; team adoption unconfirmed |
| Lightweight alternative | `Qwen/Qwen2.5-0.5B-Instruct` | Consider if the primary candidate is too costly to run |

The 1.54B model in the [official Qwen card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) is the first proposal. The team must confirm model/tokenizer revisions, backend, dtype, environment and integration keys, currently 23 proposed prompts. [Additional candidates](evidence/analysis-details.en.md#extra-models) are in the supplementary analysis; model cards were not rechecked during this documentation update.

#### **9.1.1. Proposed validation model and 23 integration prompts**

We propose `Qwen/Qwen2.5-1.5B-Instruct`: a 1.54B instruction model with Korean support and an official chat template. It was chosen with repeated-run memory costs in mind. Freeze detailed settings after confirming model loading and generation in the actual environment. The validation objective is agreement between original Ko and new Lighteval-Ko scoring on identical responses.

The following 23 prompts are proposed from `allganize/IFEval-Ko` at revision `54199e3801116897697babf341865741dcd06fc8`. The count follows instruction-type/path coverage rules; add prompts if the rules are not satisfied.

```json
[3743, 136, 3518, 1233, 3445, 3442, 1262, 1082, 1127, 3710,
 122, 3563, 1107, 3073, 3311, 3750, 1203, 2142, 1268, 3538,
 1928, 2035, 1800]
```

The selection comprises 16 scoring-behavior prompts, 4 prompt/checker mismatch diagnostics and 3 path-coverage additions. Its 40 instruction occurrences cover all 21 data-used IDs and 25 `(ID, input path)` pairs where kwargs select different operations or regexes. Selection rules and the type mapping are in [design section 6.3](design.en.md#selection-rules).

| Selection criterion | Representative keys | What to inspect |
| --- | --- | --- |
| Length/format conditions and strict/loose differences | 136, 3442, 1262 | Count boundaries and effects of response transformations |
| Korean string handling | 1233, 3445, 3073, 3311 | Keyword frequency, attached particles, first-token matching and language detection |
| Multiple instructions and response formats | 3518, 3710, 1107 | JSON, highlighting, delimiters and partially passing instruction sets |
| Acceptance scope | 3750 | Current behavior accepting multiple fixed-choice phrases together |
| Prompt/checker mismatches | 1203, 2142, 1268, 3538 | Checked keywords, inclusive/exclusive limits, characters versus words |
| Additional input paths | 1928, 2035, 1800 | Keyword frequency `<N`, sentence count `≥N`, postscript marker `P.S.` |

This is a diagnostic selection for scoring behavior, not a sample for estimating full-dataset model performance. Preserve original prompts, instruction order and kwargs; correction proposals are separate from port validation.

### **9.2. Comparison method and acceptance criteria**

Pass the same pinned prompts and responses to original Ko and new Lighteval-Ko. Generate model responses once, save them, then compare judgments and aggregates by `(key, instruction_index, instruction_id)`. The sequence is **registered task implementation → stored-response regression → 23-prompt integration → full-split evaluation**. See the [validation plan](design.en.md#validation-plan) for execution details.

| Comparison | Proposed acceptance criterion |
| --- | --- |
| Input alignment | Preserve keys, instruction order and kwargs correspondence |
| Individual judgments | 100% agreement on instruction/prompt strict and loose Booleans |
| Aggregation | Matching numerators/denominators; absolute error ≤`1e-12` for all four metrics |
| Stability/regression | Pass/fail/boundary inputs covered; no omissions or unhandled exceptions; existing English task judgments preserved |

100% means **agreement between evaluators**, not model accuracy. Even matching exceptions leave successful scoring validation incomplete for those inputs. Actual four-metric parity results have not yet been measured.

<a id="verification-status"></a>

### **9.3. Evidence collected so far**

#### **9.3.1. Composition and execution of the existing 86 cases**

The 156-case experiment verifies case IDs, input order/hashes, correspondence to pinned sources and reproducibility. The 86 baseline cases comprise 46 original-data conditions, 2 in-memory overrides and 38 synthetic inputs. Full judgments and aggregates are in section 9.3.4 and the [experiment results](evidence/checker-audit/results.en.md). Case counts differ from unique prompt counts and model generations.

The baseline uses 11 unique keys with actual dataset conditions: `127, 136, 349, 1127, 1237, 1242, 1480, 3073, 3345, 3442, 3739`. Hashes of 21 pinned code/data files and imported modules were checked. Original `InputExample` and strict/loose functions were called directly. Results retain full evaluation of all instructions, isolated evaluation of specified targets and checker diagnostics. The complete task/model CLI and new Lighteval-Ko were not run.

The directly compared references are the [English evaluator](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/ifeval/utils.py) and [Ko evaluator](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/utils.py). See the [evidence/reproduction guide](evidence/checker-audit/README.en.md) and these files:

| Evidence | Files |
| --- | --- |
| Inputs/predeclared expectations | [cases.json](evidence/checker-audit/cases.json): 156 cases; baseline inputs and judgments retained in [baseline.json](evidence/checker-audit/baseline.json) |
| Execution code | [Input builder](evidence/checker-audit/build_cases.py), [evaluator runner](evidence/checker-audit/run_audit.py), [shared runtime](evidence/checker-audit/audit_runtime.py), [comparison](evidence/checker-audit/compare.py) |
| Raw and merged results | [156 English results](evidence/checker-audit/original_results.json), [156 Ko results](evidence/checker-audit/ko_results.json), [results.json](evidence/checker-audit/results.json); reproduction evidence for all 86 baseline cases is embedded in the corresponding cases |
| Reproduction metadata | [provenance.json](evidence/checker-audit/provenance.json), [requirements.lock.txt](evidence/checker-audit/requirements.lock.txt), [SHA256SUMS](evidence/checker-audit/SHA256SUMS) |

#### **9.3.2. Further execution and pending items**

| Evidence | Inputs/comparison path | Findings and limits |
| --- | --- | --- |
| Experiment | 156 cases × original English/Ko | Identical Ko input comparison; all individual Ko judgments match predeclared expectations; input reproduction verified |
| Normal paths, boundaries, diagnostics | 21 types/25 paths, 13 N−1/N/N+1 boundary families, four repeated-ID combinations | Dedicated pass/fail judgments, observed counts and loose recovery through line deletion, etc. |
| Compatibility/error contracts | 18 auxiliary inputs × original English/Ko | 10 normal Ko returns and 8 expected exceptions; exceptions are not successful scoring |
| Verification tools | 18 tests | Detect incorrect indexes, hashes, duplicates, aggregation and missing/tampered reproduction evidence, among other errors |
| Existing Lighteval English/French regression | Before/after new implementation | **Not run**; reference comparison does not replace it |
| 23-prompt integration | Registered new task versus original Ko | **Input coverage counted for 23 prompts/40 instructions; model integration not run** |
| New Lighteval-Ko parity | Individual judgments and four metrics | **Not run or measured** |

[results.json](evidence/checker-audit/results.json) records raw judgments, reproduction evidence, input hashes and aggregates together. Earlier investigations are in the [supplementary analysis](evidence/analysis-details.en.md#language-controls). Current execution status and figures refer to the 156-case experiment. Model generation and new-task parity remain pending.

#### **9.3.3. Attachment scope and reproduction requirements**

The attachment contains inputs, code, raw results, revisions and environment metadata for the **156-case experiment**. Results are in section 9.3.4 and `evidence/checker-audit/`. The 86 baseline inputs and expected-result provenance are also traceable. Complete console logs and source materials for earlier auxiliary experiments are excluded. A table in the supplementary document does not imply that all original execution artifacts for that experiment are attached.

The [evidence README](evidence/checker-audit/README.en.md) explains restoration and reproduction. Virtual environments, caches and downloaded sources are excluded. The [environment record](evidence/analysis-details.en.md#reference-environment) covers the earlier environment and source-preservation checks. Section 9.3.4 records the 156-case results. `evidence/sample-coverage/` counts input coverage of the 23-prompt model integration proposal; it is distinct from regression case counts.

#### **9.3.4. Dedicated stored-response regression and reference results**

The **156-case experiment** ran locally on 2026-11-03, loading original English/Ko evaluators through full-package imports. It uses 116 unchanged data conditions, 2 in-memory overrides and 38 synthetic inputs, with 247 full-evaluation instruction occurrences. Eighteen auxiliary compatibility/error inputs were also checked: 10 return normally and 8 raise expected reference exceptions. Exception inputs are excluded from normal scoring denominators. These aggregates are not model benchmark scores.

| Verification | Actual result |
| --- | --- |
| Source/environment integrity | Verified hashes of 21 provenance-listed code/data files, four imported modules and NLTK resources |
| Baseline reproduction | Both evaluators exactly match all 86/86 baseline result rows; recorded in each case's `baseline_reproduction` and the comparison table |
| Baseline preservation | `baseline.json` retains inputs, both sides' judgments and environments; extracted input LF hashes match the stored oracle |
| Behavior coverage | Explicit TT and FF responses for all 21/21 data-used types and 25/25 paths, under both strict and loose evaluation |
| Numeric boundaries | Observed checker counts and expectations agree at N−1/N/N+1 for 13 count conditions |
| Repeated ID | Both index/kwargs alignments and all four Boolean combinations confirmed for 1203 |
| Individual judgments | All 156 Ko results match predeclared expectations; full/isolated target judgments agree; zero unhandled exceptions or unresolved mismatches |
| Engine behavior | Actual traces confirm eight candidates, empty-candidate exclusion, OR/AND, NFC, `if v`, phase order and checker construction; uneven instruction aggregation also checked |
| Verification tools | All 18 tests pass, covering indexes, duplicates, source mutation, hashes, candidates, aggregation, exceptions, etc. |

| Stored-response aggregate | English evaluator | Ko evaluator |
| --- | --- | --- |
| Prompt strict | 61/156 | 71/156 |
| Instruction strict | 124/247 | 133/247 |
| Prompt loose | 66/156 | 79/156 |
| Instruction loose | 129/247 | 142/247 |

These are aggregates over diagnostic stored responses. The 25 paths count checks selected by normal kwargs, not prompts or all code branches. Previously incidental conditions were promoted to explicit targets only after their indexes and isolated judgments were checked. For 1268, 136 and 3073, strict failure recovers under loose evaluation, so both expectations are stored.

Adding 1954 and 240 to the 23-prompt proposal gives 25 collected prompts/42 instructions. Including baseline prompts gives 32 source prompts/55 instructions. **The model integration selection remains 23 prompts/40 instructions.** We preserve `peace` in 1203, `predatory` in 2142, `<6` in 1268, 600 words in 3538 and the `first_word` normalization asymmetry. Auxiliary inputs cover the four registered types absent from the data and an unregistered checker. Eight expected-exception inputs, including `capital_word_frequency` AttributeError cases, are not successful scoring.

Review/reproduction materials: [guide](evidence/checker-audit/README.en.md), [English/Ko comparison](evidence/checker-audit/results.en.md), [inputs/expectations](evidence/checker-audit/cases.json), [manifest](evidence/checker-audit/manifest.json), [coverage](evidence/checker-audit/coverage.json), [source prompts](evidence/checker-audit/source_rows.en.md). An [English draft](evidence/checker-audit/issue-1463.md) and local ZIP are prepared for a later attachment to [issue #1463](https://github.com/huggingface/lighteval/issues/1463). They have not been posted.

**Not run:** parity for the newly registered Lighteval-Ko task; before/after regression, metric-object isolation and optional-dependency loading for existing English/French paths; 23-prompt model integration; full-split model evaluation. Source/frame validation of references does not establish new-task parity.

### **9.4. Handoff to implementation and further validation**

[design.en.md](design.en.md) specifies architecture, input/output contracts, tests, generation settings and open decisions. Integration and full evaluation follow team confirmation of the model, environment and integration selection, currently 23 proposed prompts. [issue-draft.md](issue-draft.md) is the upstream proposal, separate from data-error reports to dataset authors.

---

## **10. Pinned revisions and public sources**

| Resource | Revision/public source |
| --- | --- |
| English lm-evaluation-harness | [`d6de81643928d653435c431bae19945d41d32520`](https://github.com/EleutherAI/lm-evaluation-harness/commit/d6de81643928d653435c431bae19945d41d32520) |
| English google/IFEval data | [`966cd89545d6b6acfd7638bc708b98261ca58e84`](https://huggingface.co/datasets/google/IFEval/tree/966cd89545d6b6acfd7638bc708b98261ca58e84) |
| Allganize Ko code/data | [`54199e3801116897697babf341865741dcd06fc8`](https://huggingface.co/datasets/allganize/IFEval-Ko/tree/54199e3801116897697babf341865741dcd06fc8) |
| Diagnosed Lighteval revision | [`c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14`](https://github.com/Hugging-Face-KREW/lighteval/commit/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14) |

Code links and detailed investigation tables are preserved in the [supplementary analysis](evidence/analysis-details.en.md#public-sources).
