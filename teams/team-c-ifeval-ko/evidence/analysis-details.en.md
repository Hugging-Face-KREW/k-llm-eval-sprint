# IFEval-Ko Supplementary Analysis

[한국어](analysis-details.md) | **English**

This document preserves detailed investigation and observation tables supporting the [analysis report](../analysis.en.md). Implementation contracts and further validation are in the [design document](../design.en.md). Moving these tables did not run a new evaluation or attach all original inputs/logs for the earlier experiments.

<a id="extra-models"></a>

## 1. Additional model candidates

The main report retains the environment check, preferred candidate and lightweight alternative. These additional candidates were considered in the earlier report; none is confirmed. Model cards were not rechecked during documentation cleanup.

| Model ID | Size | Findings | Possible use |
| --- | --- | --- | --- |
| `google/gemma-3-1b-it` | 1B | Small instruction model; Hugging Face access requires accepting usage conditions | Additional responses from another model family |
| `LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct` | 2.4B | English/Korean bilingual model; official examples use `trust_remote_code=True` and provide a recommended system prompt | Additional Korean-model response validation |
| `google/gemma-3-4b-it` | 4B | Used in the Allganize IFEval-Ko README example; check access conditions and text-generation compatibility | Additional integration based on the official example |
| `Qwen/Qwen2.5-3B-Instruct`, `Qwen/Qwen2.5-7B-Instruct` | 3B / 7B | Larger models from the same Qwen2.5 instruction family | Consider after primary validation if resources permit |
| `meta-llama/Llama-3.2-1B-Instruct` | About 1B | Korean is absent from the officially supported language list | Lower priority as the primary Korean validation model |
| `Qwen/Qwen3-0.6B` | 0.6B | Supports thinking/non-thinking modes; freeze the selected mode and final-response extraction | Deferred for the default validation |

Qwen3 requires extra checks of thinking mode/extraction; EXAONE requires remote-code/system-prompt checks. English card scores and external results under different settings are not Korean validation acceptance criteria.

<a id="ko-classes"></a>

## 2. Ko classes and registry

The [authors' documentation](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/README_Ko.md) lists seven modified classes: `KeywordChecker`, `KeywordFrequencyChecker`, `ParagraphFirstWordCheck`, `KeySentenceChecker`, `ForbiddenWords`, `RepeatPromptThenAnswer`, `EndChecker`. `KeySentenceChecker` is unregistered and unused in the pinned data; the other six are registered. Word/sentence utilities and global choice phrases also changed, so seven is not a count of all behavior changes.

Four English-specific conditions—`keywords:letter_frequency` and `change_case:capital_word_frequency`, `change_case:english_capital`, `change_case:english_lowercase`—are unused in Ko data but remain registered. English, Ko and Lighteval registries each have 25 IDs; Ko data uses 21. Do not remove registered conditions merely because data does not use them.

The following compares the seven author-listed classes with registration/data use. Prompt applicability can overlap across classes.

| Class | Ko applicable prompts | Behavior to preserve |
| --- | --- | --- |
| `KeywordChecker` | 22 | Per-keyword NFC; ValueError when missing |
| `KeywordFrequencyChecker` | 23 | Keyword strip/NFC; ValueError when missing |
| `ParagraphFirstWordCheck` | 2 | ValueError for first_word=None; do not add NFC to first_word itself |
| `KeySentenceChecker` | 0 | Sentence NFC exists in the class, but it is unregistered |
| `ForbiddenWords` | 28 | Forbidden-word NFC, missing-input errors and list handling |
| `RepeatPromptThenAnswer` | 26 | NFC for prompt_to_repeat |
| `EndChecker` | 15 | NFC for end_phrase and translated default phrases |

In pinned English data, the four English-specific IDs apply to 33 prompts (`keywords:letter_frequency`), 20 (`change_case:capital_word_frequency`), 25 (`change_case:english_capital`) and 39 (`change_case:english_lowercase`). Each has zero applications in Ko data while remaining in the Ko registry. Sources: [Ko checkers](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py), [registry](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_registry.py), [utilities](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py).

<a id="language-controls"></a>

## 3. Detailed language-specific synthetic controls

An earlier investigation ran 23 additional synthetic inputs to examine English IFEval's relationship to French and Korean. The actual English metric, French adapter and English harness agreed on all 23; all paths matched predeclared expectations.

| Case ID | Control against the English implementation | Result and interpretation |
| --- | --- | --- |
| `word_spaces_en/fr/ko` | Space-separated words: apple pear grape / pomme poire raisin / 사과 배 포도 | English counts three in all languages; Hangul itself is not unsupported |
| `word_comma_en/fr/ko` | Same words joined by commas | English counts three in every language, Ko one; the distinction is counting policy rather than language-processing failure |
| `word_contraction_fr` | `l'homme`, fewer than two words | English metric/French adapter count two and fail; Ko whitespace counting gives one and passes. French preserves the original apostrophe regex behavior |
| `sentence_no_spaces_fr` | `Bonjour.Merci.`, at least two sentences | English metric/French adapter count one and fail; Ko splits two and passes. French does not switch to a French-specific splitter |
| `fixed_fr` | French fixed phrase: Ma réponse est oui. | English choice checker fails; translated French choices would require more than the existing options |
| `keyword_nfc_fr`, `keyword_nfd_fr` | keyword=café with NFC/NFD responses | English passes NFC and fails NFD; Ko passes both. NFC concerns are not specific to Korean |
| `uppercase_en`, `uppercase_fr` | Apply english_capital to English/French uppercase responses | English passes, French fails. The checker also requires English, so it is not automatically suitable for French |

`en/fr/ko` abbreviates three case IDs sharing a prefix. French responses here are synthetic controls for actual code behavior. Ko counts are not a French correctness oracle, and these controls alone do not establish errors in actual French data.

These controls help define the changes required for Ko. Full linguistic validation of French scoring is not a prerequisite for implementing Ko.

<a id="execution-scope"></a>

## 4. Metric, French and Inspect execution scope

Every metric-reuse comparison uses a synthetic input with key=null. The French adapter received identical synthetic records to check the actual `Doc → apply_metric → IFEvalMetrics → registry` path and metric-object identity. The full French dataset, agreement with a separate French reference and model evaluation were not run. Earlier API/README access to `fr-gouv-coordination-ia/IFEval-fr`, referenced by the pinned task, returned HTTP 401. No similarly named dataset was substituted.

The native aggregation control `[[True, True, True], [False]]` yielded 0.75 instruction accuracy and mean prompt results `[1, 0]` yielded 0.5. This is an aggregation-function check, not a model score. Inspect execution used a minimal state fixture to call the native scorer, not the whole backend.

<a id="reference-environment"></a>

## 5. Reference environment and source-preservation checks

| Item | Value/scope |
| --- | --- |
| Reference environment | Separate Python virtual environment with pinned English/Ko evaluators |
| Python · lm_eval | 3.12.3 · 0.4.14.dev0 |
| langdetect · immutabledict | 1.0.9 · 4.3.1 |
| NLTK · pyarrow | 3.10.3 · 26.0.0 |
| Package lock | All 70 pinned packages matched the environment |
| Responses | Stored responses; reference-environment checks required no model generation/GPU |
| Model environment | Final model/tokenizer revisions, dtype, chat template and backend unconfirmed |

Minimal environment reruns processed three cases per English/Ko runner, with exit code 0 and zero errors. The 13 main files for the existing 86 cases had identical before/after hashes. Inequality/Known Issue runs also recorded source preservation, both exit codes and input/result hashes in manifests.

Native Lighteval metrics ran in a Lighteval virtual environment separate from the reference evaluator.

Stored responses were placed in `ModelResponse` without calling `post_process`, confirming raw response=final_text. Actual model integration must separately freeze post-processing and final-response extraction. NLTK reused its cache. These stored-response checks do not establish model generation, GPU availability or full model evaluation.

<a id="public-sources"></a>

## 6. Public code for scoring behavior

| Subject | Public source |
| --- | --- |
| Official Ko run settings | [Task YAML](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/ifeval_ko.yaml) |
| Ko response NFC, kwargs and strict/loose | [Evaluator](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/utils.py) |
| Ko checkers and fixed choices | [Instructions](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py) |
| Ko instruction registration | [Registry](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_registry.py) |
| Ko word/sentence counts | [Utilities](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py) |
| English counters/checkers | [Utilities](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/ifeval/instructions_util.py), [instructions](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/ifeval/instructions.py) |
| Lighteval input mapping, metric and Inspect scorer | [IFEval main](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/ifeval/main.py) |
| French metric reuse | [French task](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py) |
