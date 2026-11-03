# IFEval / IFEval-Ko Stored-Response Comparison

[한국어](results.md) | **English**

Both original evaluators received the **same Ko prompt, instruction order, effective kwargs and response**. Regression acceptance means matching original Ko expectations.

The existing `case/full/isolated/diagnostics` format is retained. `original_*` preserves English source provenance; `evaluated_input` in each raw result records the actual comparison input.

The 156-case experiment comprises 116 unchanged dataset conditions, 2 in-memory overrides and 38 synthetic inputs. It uses 32 source prompts containing 55 instructions; full evaluation checks 247 instruction occurrences.

Of 18 auxiliary compatibility/error inputs, 10 return normally and 8 raise expected reference exceptions. They are excluded from main path coverage and metrics. Model generation, new Lighteval-Ko validation and existing English/French regression remain pending.

## 1. Judgment direction — (English, Ko)

| Phase | T,T | T,F | F,T | F,F | Denominator |
| --- | ---: | ---: | ---: | ---: | ---: |
| Target strict | 74 | 13 | 22 | 47 | 156 |
| Target loose | 84 | 8 | 21 | 43 | 156 |

Each case contributes one primary target. Additional explicit targets and every full-evaluation judgment remain in the tables and JSON. Distinguish this table's `(English, Ko)` order from boundary tables' `(strict, loose)` order.

## 2. Numerators and denominators of four metrics

These are stored-response experiment aggregates, not model benchmark scores.

| Metric | English | Ko |
| --- | --- | --- |
| prompt_strict | 61/156 | 71/156 |
| instruction_strict | 124/247 | 133/247 |
| prompt_loose | 66/156 | 79/156 |
| instruction_loose | 129/247 | 142/247 |

## 3. Dedicated input-path coverage

Only explicit `targets` under unchanged dataset conditions are counted. Each of 25 input paths has a response passing strict and loose (TT) and one failing both (FF). These paths follow normal kwargs.

| Instruction ID | Input path | Strict T/F | Loose T/F | Dedicated TT | Dedicated FF |
| --- | --- | --- | --- | ---: | ---: |
| `combination:repeat_prompt` | `default` | 3/1 | 3/1 | 3 | 1 |
| `combination:two_responses` | `default` | 1/2 | 1/2 | 1 | 2 |
| `detectable_content:number_placeholders` | `default` | 2/1 | 2/1 | 2 | 1 |
| `detectable_content:postscript` | `postscript_marker=P.P.S` | 1/1 | 1/1 | 1 | 1 |
| `detectable_content:postscript` | `postscript_marker=P.S.` | 1/1 | 1/1 | 1 | 1 |
| `detectable_format:constrained_response` | `default` | 2/1 | 2/1 | 2 | 1 |
| `detectable_format:json_format` | `default` | 1/1 | 1/1 | 1 | 1 |
| `detectable_format:multiple_sections` | `default` | 2/1 | 2/1 | 2 | 1 |
| `detectable_format:number_bullet_lists` | `default` | 1/3 | 2/2 | 1 | 2 |
| `detectable_format:number_highlighted_sections` | `default` | 2/1 | 2/1 | 2 | 1 |
| `detectable_format:title` | `default` | 2/1 | 2/1 | 2 | 1 |
| `keywords:existence` | `default` | 3/1 | 3/1 | 3 | 1 |
| `keywords:forbidden_words` | `default` | 3/4 | 3/4 | 3 | 4 |
| `keywords:frequency` | `relation=at least` | 10/8 | 10/8 | 10 | 8 |
| `keywords:frequency` | `relation=less than` | 1/2 | 1/2 | 1 | 2 |
| `language:response_language` | `default` | 3/3 | 3/3 | 3 | 3 |
| `length_constraints:nth_paragraph_first_word` | `default` | 3/3 | 4/2 | 3 | 2 |
| `length_constraints:number_paragraphs` | `default` | 1/2 | 1/2 | 1 | 2 |
| `length_constraints:number_sentences` | `relation=at least` | 2/1 | 2/1 | 2 | 1 |
| `length_constraints:number_sentences` | `relation=less than` | 12/4 | 14/2 | 12 | 2 |
| `length_constraints:number_words` | `relation=at least` | 2/2 | 2/2 | 2 | 2 |
| `length_constraints:number_words` | `relation=less than` | 9/11 | 14/6 | 9 | 6 |
| `punctuation:no_comma` | `default` | 1/1 | 1/1 | 1 | 1 |
| `startend:end_checker` | `default` | 2/1 | 2/1 | 2 | 1 |
| `startend:quotation` | `default` | 1/1 | 1/1 | 1 | 1 |

## 4. Boundaries, repeated IDs and loose recovery

| key:index | Condition | N−1 strict/loose | N | N+1 |
| --- | --- | --- | --- | --- |
| 136:0 | num_bullets=9 | F,F | T,T | F,F |
| 1082:0 | num_paragraphs=2 | F,F | T,T | F,F |
| 1107:1 | num_responses=2 | F,F | T,T | F,F |
| 1127:0 | num_sections=4 | F,F | T,T | T,T |
| 1233:1 | frequency=8 | F,F | T,T | T,T |
| 1268:0 | num_sentences=6 | T,T | F,F | F,F |
| 1928:2 | frequency=3 | T,T | F,F | F,F |
| 2035:2 | num_sentences=5 | F,F | T,T | T,T |
| 3073:0 | num_paragraphs=4 | F,F | T,T | F,T |
| 3442:0 | num_words=20 | T,T | F,F | F,F |
| 3538:1 | num_words=600 | F,F | T,T | T,T |
| 3710:0 | num_highlights=2 | F,F | T,T | T,T |
| 3743:0 | num_placeholders=3 | F,F | T,T | T,T |

Key 1203 checks 전쟁≥8 at index 0 and peace≥10 at index 1. Both strict and loose cover `[T,T]`, `[T,F]`, `[F,T]`, `[F,F]`. The original mismatch between prompt 평화 and kwargs peace is preserved.

Six sentences for 1268 give F/F on one line and F/T across lines. Ten bullets for 136 give F/F with two blank lines at each end and F/T without padding. Five paragraphs for 3073 also give F/T. Here F/T means strict failure and loose success; record both expectations separately.

## 5. Complete comparison

Cells show **target judgment / all instruction flags / prompt all-pass**. Both evaluators receive identical Ko inputs in every row. Source conditions, responses, expectations, observations and hashes are recorded in cases.json and results.json.

| key:index | Checker | Test | Original strict | Original loose | Ko strict | Ko loose | strict (EN,Ko) | loose (EN,Ko) | Scope | Composition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3345:0 | KeywordFrequencyChecker | `robber_minimal` | F / [F,F,T] / F | F / [F,F,T] / F | F / [F,F,T] / F | F / [F,F,T] / F | F,F | F,F | dataset | Baseline; both reproductions match |
| 3345:0 | KeywordFrequencyChecker | `robber_full` | F / [F,T,T] / F | F / [F,T,T] / F | F / [F,T,T] / F | F / [F,T,T] / F | F,F | F,F | dataset | Baseline; both reproductions match |
| 3345:0 | KeywordFrequencyChecker | `robber_keyword_override` | T / [T,T,T] / T | T / [T,T,T] / T | T / [T,T,T] / T | T / [T,T,T] / T | T,T | T,T | controlled_override | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `comma_compact` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| None:0 | NumberOfWords | `comma_compact_threshold2` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `comma_spaced` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| None:0 | NumberOfWords | `comma_spaced_threshold2` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `heading_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `quote_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `star_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `dash_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `comma_boundary_compact` | F / [F,T] / F | F / [F,T] / F | T / [T,T] / T | T / [T,T] / T | F,T | F,T | dataset | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `comma_boundary_spaced` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | Baseline; both reproductions match |
| 136:1 | NumberOfWords | `markdown_heading_136` | T / [F,T] / F | T / [F,T] / F | F / [F,F] / F | T / [F,T] / F | T,F | T,T | dataset | Baseline; both reproductions match |
| 136:1 | NumberOfWords | `markdown_quote_136` | T / [F,T] / F | T / [F,T] / F | F / [F,F] / F | F / [F,F] / F | T,F | T,F | dataset | Baseline; both reproductions match |
| 136:1 | NumberOfWords | `markdown_star_balanced_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | Baseline; both reproductions match |
| 136:1 | NumberOfWords | `markdown_star_persistent_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | Baseline; both reproductions match |
| 136:1 | NumberOfWords | `markdown_dash_balanced_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | Baseline; both reproductions match |
| 136:1 | NumberOfWords | `markdown_dash_persistent_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | F / [T,F] / F | T,F | T,F | dataset | Baseline; both reproductions match |
| 3442:0 | NumberOfWords | `markdown_heading_blank_edges` | T / [T,T] / T | T / [T,T] / T | F / [F,T] / F | F / [F,T] / F | T,F | T,F | dataset | Baseline; both reproductions match |
| 349:1 | NumberOfWords | `markdown_highlights_attached_349` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 349:1 | NumberOfWords | `markdown_highlights_separated_349` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | Baseline; both reproductions match |
| 349:1 | NumberOfWords | `markdown_quote_valid_highlights_349` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | F / [T,F] / F | T,F | T,F | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_period_newlines` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_only_newlines` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_heading` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_divider` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_divider_boundary` | F / [F] / F | T / [T] / T | F / [F] / F | T / [T] / T | F,F | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_korean_list_lines` | F / [F] / F | T / [T] / T | T / [T] / T | T / [T] / T | F,T | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_korean_list_single_line` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_decimal` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_english_abbreviation` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_eg_abbreviation` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | Baseline; both reproductions match |
| 3739:0 | NumberOfSentences | `sentences_korean_abbreviation` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | Baseline; both reproductions match |
| 1242:1 | ForbiddenWords | `forbidden_dataset_exact` | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F,F | F,F | dataset | Baseline; both reproductions match |
| 1242:1 | ForbiddenWords | `forbidden_dataset_particle` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 1242:1 | ForbiddenWords | `forbidden_dataset_compound` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | Baseline; both reproductions match |
| None:0 | KeywordChecker | `boundary_existence_사과` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과를` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordChecker | `boundary_existence_사과를` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과를` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과가` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordChecker | `boundary_existence_사과가` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과가` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과나무` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordChecker | `boundary_existence_사과나무` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과나무` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| 1237:1 | KeywordChecker | `nfc_dataset_existence_nfc` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| 1237:1 | KeywordChecker | `nfc_dataset_existence_nfd` | F / [F,F] / F | F / [F,F] / F | T / [F,T] / F | T / [F,T] / F | F,T | F,T | dataset | Baseline; both reproductions match |
| 127:1 | KeywordFrequencyChecker | `nfc_dataset_frequency_nfc` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 127:1 | KeywordFrequencyChecker | `nfc_dataset_frequency_nfd` | F / [T,F] / F | F / [T,F] / F | T / [T,T] / T | T / [T,T] / T | F,T | F,T | dataset | Baseline; both reproductions match |
| 1242:1 | ForbiddenWords | `nfc_dataset_forbidden_words_nfc` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | Baseline; both reproductions match |
| 1242:1 | ForbiddenWords | `nfc_dataset_forbidden_words_nfd` | T / [F,T] / F | T / [F,T] / F | F / [F,F] / F | F / [F,F] / F | T,F | T,F | dataset | Baseline; both reproductions match |
| 1127:1 | EndChecker | `nfc_dataset_end_checker_nfc` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | Baseline; both reproductions match |
| 1127:1 | EndChecker | `nfc_dataset_end_checker_nfd` | F / [F,F] / F | F / [F,F] / F | T / [F,T] / F | T / [F,T] / F | F,T | F,T | dataset | Baseline; both reproductions match |
| 1480:0 | RepeatPromptThenAnswer | `nfc_dataset_repeat_prompt_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 1480:0 | RepeatPromptThenAnswer | `nfc_dataset_repeat_prompt_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | Baseline; both reproductions match |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfc_nfc` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfc_nfd` | T / [T] / T | T / [T] / T | F / [F] / F | F / [F] / F | T,F | T,F | synthetic | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfd_nfc` | T / [T] / T | T / [T] / T | F / [F] / F | F / [F] / F | T,F | T,F | synthetic | Baseline; both reproductions match |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfd_nfd` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | Baseline; both reproductions match |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | Baseline; both reproductions match |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | Baseline; both reproductions match |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfd_nfc` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | Baseline; both reproductions match |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfd_nfd` | T / [T] / T | T / [T] / T | F / [F] / F | F / [F] / F | T,F | T,F | synthetic | Baseline; both reproductions match |
| 3073:0 | ParagraphFirstWordCheck | `nfc_dataset_first_word_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Baseline; both reproductions match |
| 3073:0 | ParagraphFirstWordCheck | `nfc_dataset_first_word_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | Baseline; both reproductions match |
| 3073:0 | ParagraphFirstWordCheck | `nfc_first_word_target_override` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | controlled_override | Baseline; both reproductions match |
| 1233:1 | KeywordFrequencyChecker | `expanded_freq_ge_7` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | Added |
| 1233:1 | KeywordFrequencyChecker | `expanded_freq_ge_8` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | Added |
| 1233:1 | KeywordFrequencyChecker | `expanded_freq_ge_9` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | Added |
| 1928:2 | KeywordFrequencyChecker | `expanded_freq_lt_2` | T / [F,T,T] / F | T / [F,T,T] / F | T / [F,T,T] / F | T / [F,T,T] / F | T,T | T,T | dataset | Added |
| 1928:2 | KeywordFrequencyChecker | `expanded_freq_lt_3` | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F,F | F,F | dataset | Added |
| 1928:2 | KeywordFrequencyChecker | `expanded_freq_lt_4` | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F,F | F,F | dataset | Added |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_5` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_6` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_7` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 2035:2 | NumberOfSentences | `expanded_sent_ge_4` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | Added |
| 2035:2 | NumberOfSentences | `expanded_sent_ge_5` | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T,T | T,T | dataset | Added |
| 2035:2 | NumberOfSentences | `expanded_sent_ge_6` | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T,T | T,T | dataset | Added |
| 3442:0 | NumberOfWords | `expanded_words_lt_19` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Added |
| 3442:0 | NumberOfWords | `expanded_words_lt_21` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | Added |
| 3538:1 | NumberOfWords | `expanded_words_ge_599` | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F,F | F,F | dataset | Added |
| 3538:1 | NumberOfWords | `expanded_words_ge_600` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Added |
| 3538:1 | NumberOfWords | `expanded_words_ge_601` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Added |
| 3743:0 | PlaceholderChecker | `expanded_placeholders_2` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 3743:0 | PlaceholderChecker | `expanded_placeholders_3` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 3743:0 | PlaceholderChecker | `expanded_placeholders_4` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 136:0 | BulletListChecker | `expanded_bullets_8` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | Added |
| 136:0 | BulletListChecker | `expanded_bullets_10` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | Added |
| 3710:0 | HighlightSectionChecker | `expanded_highlights_1` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | Added |
| 3710:0 | HighlightSectionChecker | `expanded_highlights_2` | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T,T | T,T | dataset | Added |
| 3710:0 | HighlightSectionChecker | `expanded_highlights_3` | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T,T | T,T | dataset | Added |
| 1127:0 | SectionChecker | `expanded_sections_3` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | Added |
| 1127:0 | SectionChecker | `expanded_sections_4` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Added |
| 1127:0 | SectionChecker | `expanded_sections_5` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Added |
| 1082:0 | ParagraphChecker | `expanded_paragraphs_1` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 1082:0 | ParagraphChecker | `expanded_paragraphs_2` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 1082:0 | ParagraphChecker | `expanded_paragraphs_3` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 3073:0 | ParagraphFirstWordCheck | `expanded_nth_paragraphs_3` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 3073:0 | ParagraphFirstWordCheck | `expanded_nth_paragraphs_5` | F / [F] / F | T / [T] / T | F / [F] / F | T / [T] / T | F,F | T,T | dataset | Added |
| 1107:0 | CommaChecker | `expanded_two_responses_1` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Added |
| 1107:1 | TwoResponsesChecker | `expanded_two_responses_2` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Added |
| 1107:0 | CommaChecker | `expanded_two_responses_3` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | Added |
| 3710:2 | PostscriptChecker | `expanded_postscript_P.P.S_T` | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T,T | T,T | dataset | Added |
| 3710:2 | PostscriptChecker | `expanded_postscript_P.P.S_F` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | Added |
| 1800:0 | PostscriptChecker | `expanded_postscript_P.S._T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 1800:0 | PostscriptChecker | `expanded_postscript_P.S._F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 3750:0 | ConstrainedResponseChecker | `expanded_constrained_T` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | Added |
| 3750:0 | ConstrainedResponseChecker | `expanded_constrained_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 3518:0 | JsonFormat | `expanded_json_existence_T` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Added |
| 3518:0 | JsonFormat | `expanded_json_existence_F` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | Added |
| 3445:0 | ForbiddenWords | `expanded_forbidden_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 3445:0 | ForbiddenWords | `expanded_forbidden_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 3311:0 | ResponseLanguageChecker | `expanded_language_ko_T` | T / [T,F,T] / F | T / [T,F,T] / F | T / [T,F,T] / F | T / [T,F,T] / F | T,T | T,T | dataset | Added |
| 3311:0 | ResponseLanguageChecker | `expanded_language_ko_F` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | Added |
| 1127:1 | EndChecker | `expanded_end_F` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | Added |
| 122:0 | QuotationChecker | `expanded_quotation_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 122:0 | QuotationChecker | `expanded_quotation_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 3563:0 | RepeatPromptThenAnswer | `expanded_repeat_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 3563:0 | RepeatPromptThenAnswer | `expanded_repeat_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_8_10` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Added |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_8_9` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Added |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_7_10` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | Added |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_7_9` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | Added |
| 2142:0 | KeywordFrequencyChecker | `expanded_predatory_ko` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 2142:0 | KeywordFrequencyChecker | `expanded_predatory_literal` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_6_multiline` | F / [F] / F | T / [T] / T | F / [F] / F | T / [T] / T | F,F | T,T | dataset | Added |
| 3538:0 | KeywordFrequencyChecker | `expanded_characters_600_not_words` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | Added |
| 1954:0 | ParagraphFirstWordCheck | `expanded_last_paragraph_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 1954:0 | ParagraphFirstWordCheck | `expanded_last_paragraph_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 136:0 | BulletListChecker | `expanded_bullets_10_unpadded` | F / [F,T] / F | T / [T,T] / T | F / [F,T] / F | T / [T,T] / T | F,F | T,T | dataset | Added |
| 3750:0 | ConstrainedResponseChecker | `expanded_constrained_multi` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | Added |
| 3311:0 | ResponseLanguageChecker | `expanded_language_empty` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | Added |
| 3311:0 | ResponseLanguageChecker | `expanded_language_short_exception` | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T,T | T,T | dataset | Added |
| 240:0 | ResponseLanguageChecker | `expanded_language_ru_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | Added |
| 240:0 | ResponseLanguageChecker | `expanded_language_ru_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | Added |
| 1262:0 | TitleChecker | `expanded_selected_1262_smoke` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | Added |

## 6. Auxiliary compatibility and error inputs

| Case | Checker | English strict/loose | Ko strict/loose | Classification |
| --- | --- | --- | --- | --- |
| `support_filter_null` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | Synthetic compatibility |
| `support_filter_zero` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | Synthetic compatibility |
| `support_filter_empty_string` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | Synthetic compatibility |
| `support_filter_empty_list` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | Synthetic compatibility |
| `support_keyword_absent` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | Expected exception confirmed |
| `support_keyword_null` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | Expected exception confirmed |
| `support_keyword_empty_string` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | Expected exception confirmed |
| `support_keyword_empty_list` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | Expected exception confirmed |
| `support_bad_relation` | `length_constraints:number_words` | ValueError; ValueError | ValueError; ValueError | Expected exception confirmed |
| `support_letter_a` | `keywords:letter_frequency` | F / [F] / F; F / [F] / F | F / [F] / F; F / [F] / F | Synthetic compatibility |
| `support_letter_aa` | `keywords:letter_frequency` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | Synthetic compatibility |
| `support_capital_T` | `change_case:english_capital` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | Synthetic compatibility |
| `support_capital_F` | `change_case:english_capital` | F / [F] / F; F / [F] / F | F / [F] / F; F / [F] / F | Synthetic compatibility |
| `support_lowercase_T` | `change_case:english_lowercase` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | Synthetic compatibility |
| `support_lowercase_F` | `change_case:english_lowercase` | F / [F] / F; F / [F] / F | F / [F] / F; F / [F] / F | Synthetic compatibility |
| `support_capital_words_HELLO` | `change_case:capital_word_frequency` | T / [T] / T; T / [T] / T | AttributeError; AttributeError | Expected exception confirmed |
| `support_capital_words_hello` | `change_case:capital_word_frequency` | F / [F] / F; F / [F] / F | AttributeError; AttributeError | Expected exception confirmed |
| `support_unregistered` | `keywords:key_sentences` | KeyError; KeyError | KeyError; KeyError | Expected exception confirmed |

## 7. Reproduction and port handoff

The 156-case results include input-reproduction evidence in raw `baseline_reproduction` and `summary`. Comparison tables count the 156 cases with identical Ko inputs.

Verified hashes cover 21 pinned code/data files, four imported modules, NLTK resources and inputs/responses. Traces check phases, construction, initialization and candidates, including instruction-wise OR, prompt AND, fresh phase objects, `if v` and uneven instruction aggregation.

Option A keeps Ko scoring close to the reference and limits changes to existing English/French code. Option B is also possible if it preserves the same policies and checker lifecycle.

See the [README](README.en.md) for commands. The [English issue attachment draft](issue-1463.md) is prepared locally and has not been posted. Also see the [manifest](manifest.json), [coverage](coverage.json) and [source prompt catalog](source_rows.en.md).
