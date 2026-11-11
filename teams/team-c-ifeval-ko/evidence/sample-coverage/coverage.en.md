# Prompt Selection Coverage

[한국어](coverage.md) | **English**

Pinned revision: `54199e3801116897697babf341865741dcd06fc8`. Data: 342 prompts, 481 instructions, 21 types.

This counts input conditions, not model execution, measured code-branch coverage or stored-response regression. The selection is a proposal pending team review.

| Selection | Prompts | Instructions | IDs | Input paths | Repeated-ID prompts | Multiple-instruction prompts |
| --- | --- | --- | --- | --- | --- | --- |
| Proposal | 23 | 40 | 21/21 | 25/25 | [1203] | 13 |

## Instruction-type mapping

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

Modified-class labels follow the pinned authors' documentation. A dash does not establish complete equivalence with English.

## Input paths by instruction type

| Instruction ID | Input path | Full occurrences | Selected occurrences |
| --- | --- | --- | --- |
| `combination:repeat_prompt` | `default` | 26 | 1 |
| `combination:two_responses` | `default` | 19 | 1 |
| `detectable_content:number_placeholders` | `default` | 20 | 1 |
| `detectable_content:postscript` | `postscript_marker=P.P.S` | 12 | 1 |
| `detectable_content:postscript` | `postscript_marker=P.S.` | 7 | 1 |
| `detectable_format:constrained_response` | `default` | 10 | 1 |
| `detectable_format:json_format` | `default` | 14 | 1 |
| `detectable_format:multiple_sections` | `default` | 11 | 1 |
| `detectable_format:number_bullet_lists` | `default` | 24 | 1 |
| `detectable_format:number_highlighted_sections` | `default` | 38 | 2 |
| `detectable_format:title` | `default` | 27 | 5 |
| `keywords:existence` | `default` | 22 | 2 |
| `keywords:forbidden_words` | `default` | 28 | 1 |
| `keywords:frequency` | `relation=at least` | 21 | 5 |
| `keywords:frequency` | `relation=less than` | 4 | 1 |
| `language:response_language` | `default` | 25 | 1 |
| `length_constraints:nth_paragraph_first_word` | `default` | 2 | 1 |
| `length_constraints:number_paragraphs` | `default` | 19 | 1 |
| `length_constraints:number_sentences` | `relation=at least` | 13 | 1 |
| `length_constraints:number_sentences` | `relation=less than` | 18 | 2 |
| `length_constraints:number_words` | `relation=at least` | 22 | 1 |
| `length_constraints:number_words` | `relation=less than` | 14 | 2 |
| `punctuation:no_comma` | `default` | 42 | 2 |
| `startend:end_checker` | `default` | 15 | 2 |
| `startend:quotation` | `default` | 28 | 2 |

`default` means no explicit value-dependent path selection under observed normal kwargs. It does not combine or validate all response pass/fail behavior.

Path counting checks AST equality comparisons between kwargs-derived attributes and constants in check_following, then counts values present in the data. Other numbers, phrases and language values are arguments to the same operations, not separate paths per value.

Missing/invalid inputs, random fallbacks, other postscript markers, response-dependent branches, NFC/NFD, regexes and sentence/word boundaries belong to stored-response regression. This output does not execute those checks.


[Selection guide](README.en.md) · [Design](../../design.en.md#selection-rules)
