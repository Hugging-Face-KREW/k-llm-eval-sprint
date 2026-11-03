# IFEval / IFEval-Ko 확장 고정 응답 비교

**한국어** | [English](results.en.md)

원본 영어·Ko 평가기에 **동일한 Ko prompt·instruction 순서·실제 적용 kwargs·응답**을 전달했다. 회귀 검증의 기준은 원본 Ko의 기대값과 일치하는지 여부다.

기존 `case/full/isolated/diagnostics` 형식을 유지했다. `original_*` 필드는 원래 영어 문항의 출처를 보존하며, 실제 비교 입력은 각 원시 결과의 `evaluated_input`에 기록했다.

156건의 실험은 실제 데이터 조건 116건·메모리 override 2건·합성 입력 38건으로 구성된다. 사용한 원본 문항은 32개이며 instruction 55개를 포함한다. full 평가에서 검사한 instruction은 247개다.

보조 호환성·오류 입력 18건 중 10건은 정상 반환하고, 8건은 원본에서 예상한 예외가 발생한다. 보조 입력은 주 실험의 경로별 검증과 지표에 포함하지 않는다. 모델 생성, 새 Lighteval-Ko 검증과 기존 Lighteval 영어/French 회귀는 미수행이다.

## 1. 판정 방향 — (영어, Ko)

| 단계 | T,T | T,F | F,T | F,F | 분모 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 대상 strict | 74 | 13 | 22 | 47 | 156 |
| 대상 loose | 84 | 8 | 21 | 43 | 156 |

각 case의 주 검사 대상 하나씩을 집계했다. 추가로 지정한 검사 대상과 full 평가의 모든 개별 판정은 아래 비교표와 JSON에 보존했다. 이 표의 `(영어, Ko)` 순서와 경계 표의 `(strict, loose)` 순서를 구별해 읽는다.

## 2. 네 지표의 분자·분모

고정 응답 실험의 집계다. 모델의 벤치마크 성능 점수를 나타내지 않는다.

| 지표 | 영어 | Ko |
| --- | --- | --- |
| prompt_strict | 61/156 | 71/156 |
| instruction_strict | 124/247 | 133/247 |
| prompt_loose | 66/156 | 79/156 |
| instruction_loose | 129/247 | 142/247 |

## 3. 전용 입력 경로 coverage

실제 데이터 조건을 유지한 사례 중 `targets`로 지정한 instruction만 집계한다. 25개 입력 경로마다 strict·loose 모두 통과하는 응답(TT)과 모두 실패하는 응답(FF)을 확보했다. 이는 정상 kwargs에 따른 입력 경로의 검증 범위다.

| instruction ID | 입력 경로 | strict T/F | loose T/F | 전용 TT | 전용 FF |
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

## 4. 경계·반복 ID·loose 복구

| key:index | 조건 | N−1의 strict/loose | N | N+1 |
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

key 1203의 두 빈도 조건은 index 0이 전쟁≥8, index 1이 peace≥10이다. strict와 loose 각각에서 `[T,T]`, `[T,F]`, `[F,T]`, `[F,F]` 네 조합을 확인했다. prompt의 평화와 kwargs의 peace는 원본대로 유지했다.

1268의 6문장은 한 줄로 쓰면 F/F, 여러 줄로 쓰면 F/T다. 136의 10개 bullet은 앞뒤에 빈 줄을 2개씩 두면 F/F, 빈 줄이 없으면 F/T다. 3073의 5문단도 F/T다. 여기서 F/T는 strict 실패·loose 통과를 뜻하므로 두 기대값을 각각 기록한다.

## 5. 전체 비교표

각 셀은 **대상 instruction의 판정 / 전체 instruction의 판정 목록 / 문항 전체 통과 여부** 순서다. 모든 행에서 양쪽 평가기에 동일 Ko 입력을 전달했다. 원본 조건·응답·기대값·관측값·해시는 cases.json과 results.json에 각각 기록했다.

| key:index | Checker | Test | Original strict | Original loose | Ko strict | Ko loose | strict (EN,Ko) | loose (EN,Ko) | Scope | 실험 구성 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3345:0 | KeywordFrequencyChecker | `robber_minimal` | F / [F,F,T] / F | F / [F,F,T] / F | F / [F,F,T] / F | F / [F,F,T] / F | F,F | F,F | dataset | 기존·양쪽 재현 일치 |
| 3345:0 | KeywordFrequencyChecker | `robber_full` | F / [F,T,T] / F | F / [F,T,T] / F | F / [F,T,T] / F | F / [F,T,T] / F | F,F | F,F | dataset | 기존·양쪽 재현 일치 |
| 3345:0 | KeywordFrequencyChecker | `robber_keyword_override` | T / [T,T,T] / T | T / [T,T,T] / T | T / [T,T,T] / T | T / [T,T,T] / T | T,T | T,T | controlled_override | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `comma_compact` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| None:0 | NumberOfWords | `comma_compact_threshold2` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `comma_spaced` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| None:0 | NumberOfWords | `comma_spaced_threshold2` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `heading_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `quote_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `star_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `dash_minimal` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `comma_boundary_compact` | F / [F,T] / F | F / [F,T] / F | T / [T,T] / T | T / [T,T] / T | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `comma_boundary_spaced` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | 기존·양쪽 재현 일치 |
| 136:1 | NumberOfWords | `markdown_heading_136` | T / [F,T] / F | T / [F,T] / F | F / [F,F] / F | T / [F,T] / F | T,F | T,T | dataset | 기존·양쪽 재현 일치 |
| 136:1 | NumberOfWords | `markdown_quote_136` | T / [F,T] / F | T / [F,T] / F | F / [F,F] / F | F / [F,F] / F | T,F | T,F | dataset | 기존·양쪽 재현 일치 |
| 136:1 | NumberOfWords | `markdown_star_balanced_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | 기존·양쪽 재현 일치 |
| 136:1 | NumberOfWords | `markdown_star_persistent_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | 기존·양쪽 재현 일치 |
| 136:1 | NumberOfWords | `markdown_dash_balanced_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | 기존·양쪽 재현 일치 |
| 136:1 | NumberOfWords | `markdown_dash_persistent_136` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | F / [T,F] / F | T,F | T,F | dataset | 기존·양쪽 재현 일치 |
| 3442:0 | NumberOfWords | `markdown_heading_blank_edges` | T / [T,T] / T | T / [T,T] / T | F / [F,T] / F | F / [F,T] / F | T,F | T,F | dataset | 기존·양쪽 재현 일치 |
| 349:1 | NumberOfWords | `markdown_highlights_attached_349` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 349:1 | NumberOfWords | `markdown_highlights_separated_349` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | T / [T,T] / T | T,F | T,T | dataset | 기존·양쪽 재현 일치 |
| 349:1 | NumberOfWords | `markdown_quote_valid_highlights_349` | T / [T,T] / T | T / [T,T] / T | F / [T,F] / F | F / [T,F] / F | T,F | T,F | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_period_newlines` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_only_newlines` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_heading` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_divider` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_divider_boundary` | F / [F] / F | T / [T] / T | F / [F] / F | T / [T] / T | F,F | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_korean_list_lines` | F / [F] / F | T / [T] / T | T / [T] / T | T / [T] / T | F,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_korean_list_single_line` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_decimal` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_english_abbreviation` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_eg_abbreviation` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 3739:0 | NumberOfSentences | `sentences_korean_abbreviation` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 1242:1 | ForbiddenWords | `forbidden_dataset_exact` | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F,F | F,F | dataset | 기존·양쪽 재현 일치 |
| 1242:1 | ForbiddenWords | `forbidden_dataset_particle` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 1242:1 | ForbiddenWords | `forbidden_dataset_compound` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `boundary_existence_사과` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과를` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `boundary_existence_사과를` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과를` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과가` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `boundary_existence_사과가` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과가` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `boundary_forbidden_words_사과나무` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `boundary_existence_사과나무` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `boundary_frequency_사과나무` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| 1237:1 | KeywordChecker | `nfc_dataset_existence_nfc` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 1237:1 | KeywordChecker | `nfc_dataset_existence_nfd` | F / [F,F] / F | F / [F,F] / F | T / [F,T] / F | T / [F,T] / F | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 127:1 | KeywordFrequencyChecker | `nfc_dataset_frequency_nfc` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 127:1 | KeywordFrequencyChecker | `nfc_dataset_frequency_nfd` | F / [T,F] / F | F / [T,F] / F | T / [T,T] / T | T / [T,T] / T | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 1242:1 | ForbiddenWords | `nfc_dataset_forbidden_words_nfc` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | 기존·양쪽 재현 일치 |
| 1242:1 | ForbiddenWords | `nfc_dataset_forbidden_words_nfd` | T / [F,T] / F | T / [F,T] / F | F / [F,F] / F | F / [F,F] / F | T,F | T,F | dataset | 기존·양쪽 재현 일치 |
| 1127:1 | EndChecker | `nfc_dataset_end_checker_nfc` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 1127:1 | EndChecker | `nfc_dataset_end_checker_nfd` | F / [F,F] / F | F / [F,F] / F | T / [F,T] / F | T / [F,T] / F | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 1480:0 | RepeatPromptThenAnswer | `nfc_dataset_repeat_prompt_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 1480:0 | RepeatPromptThenAnswer | `nfc_dataset_repeat_prompt_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordChecker | `nfc_matrix_existence_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | KeywordFrequencyChecker | `nfc_matrix_frequency_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfc_nfc` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfc_nfd` | T / [T] / T | T / [T] / T | F / [F] / F | F / [F] / F | T,F | T,F | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfd_nfc` | T / [T] / T | T / [T] / T | F / [F] / F | F / [F] / F | T,F | T,F | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ForbiddenWords | `nfc_matrix_forbidden_words_nfd_nfd` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | 기존·양쪽 재현 일치 |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | EndChecker | `nfc_matrix_end_checker_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfd_nfc` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | RepeatPromptThenAnswer | `nfc_matrix_repeat_prompt_nfd_nfd` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfc_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfc_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfd_nfc` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | synthetic | 기존·양쪽 재현 일치 |
| None:0 | ParagraphFirstWordCheck | `nfc_matrix_nth_paragraph_first_word_nfd_nfd` | T / [T] / T | T / [T] / T | F / [F] / F | F / [F] / F | T,F | T,F | synthetic | 기존·양쪽 재현 일치 |
| 3073:0 | ParagraphFirstWordCheck | `nfc_dataset_first_word_nfc` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 기존·양쪽 재현 일치 |
| 3073:0 | ParagraphFirstWordCheck | `nfc_dataset_first_word_nfd` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | 기존·양쪽 재현 일치 |
| 3073:0 | ParagraphFirstWordCheck | `nfc_first_word_target_override` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | controlled_override | 기존·양쪽 재현 일치 |
| 1233:1 | KeywordFrequencyChecker | `expanded_freq_ge_7` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | 신규 |
| 1233:1 | KeywordFrequencyChecker | `expanded_freq_ge_8` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | 신규 |
| 1233:1 | KeywordFrequencyChecker | `expanded_freq_ge_9` | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T / [F,T] / F | T,T | T,T | dataset | 신규 |
| 1928:2 | KeywordFrequencyChecker | `expanded_freq_lt_2` | T / [F,T,T] / F | T / [F,T,T] / F | T / [F,T,T] / F | T / [F,T,T] / F | T,T | T,T | dataset | 신규 |
| 1928:2 | KeywordFrequencyChecker | `expanded_freq_lt_3` | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F,F | F,F | dataset | 신규 |
| 1928:2 | KeywordFrequencyChecker | `expanded_freq_lt_4` | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F / [F,T,F] / F | F,F | F,F | dataset | 신규 |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_5` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_6` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_7` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 2035:2 | NumberOfSentences | `expanded_sent_ge_4` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | 신규 |
| 2035:2 | NumberOfSentences | `expanded_sent_ge_5` | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T,T | T,T | dataset | 신규 |
| 2035:2 | NumberOfSentences | `expanded_sent_ge_6` | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T,T | T,T | dataset | 신규 |
| 3442:0 | NumberOfWords | `expanded_words_lt_19` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 신규 |
| 3442:0 | NumberOfWords | `expanded_words_lt_21` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | 신규 |
| 3538:1 | NumberOfWords | `expanded_words_ge_599` | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F / [T,F] / F | F,F | F,F | dataset | 신규 |
| 3538:1 | NumberOfWords | `expanded_words_ge_600` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 신규 |
| 3538:1 | NumberOfWords | `expanded_words_ge_601` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 신규 |
| 3743:0 | PlaceholderChecker | `expanded_placeholders_2` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 3743:0 | PlaceholderChecker | `expanded_placeholders_3` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 3743:0 | PlaceholderChecker | `expanded_placeholders_4` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 136:0 | BulletListChecker | `expanded_bullets_8` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | 신규 |
| 136:0 | BulletListChecker | `expanded_bullets_10` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | 신규 |
| 3710:0 | HighlightSectionChecker | `expanded_highlights_1` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | 신규 |
| 3710:0 | HighlightSectionChecker | `expanded_highlights_2` | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T,T | T,T | dataset | 신규 |
| 3710:0 | HighlightSectionChecker | `expanded_highlights_3` | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T,T | T,T | dataset | 신규 |
| 1127:0 | SectionChecker | `expanded_sections_3` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | 신규 |
| 1127:0 | SectionChecker | `expanded_sections_4` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 신규 |
| 1127:0 | SectionChecker | `expanded_sections_5` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 신규 |
| 1082:0 | ParagraphChecker | `expanded_paragraphs_1` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 1082:0 | ParagraphChecker | `expanded_paragraphs_2` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 1082:0 | ParagraphChecker | `expanded_paragraphs_3` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 3073:0 | ParagraphFirstWordCheck | `expanded_nth_paragraphs_3` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 3073:0 | ParagraphFirstWordCheck | `expanded_nth_paragraphs_5` | F / [F] / F | T / [T] / T | F / [F] / F | T / [T] / T | F,F | T,T | dataset | 신규 |
| 1107:0 | CommaChecker | `expanded_two_responses_1` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 신규 |
| 1107:1 | TwoResponsesChecker | `expanded_two_responses_2` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 신규 |
| 1107:0 | CommaChecker | `expanded_two_responses_3` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | 신규 |
| 3710:2 | PostscriptChecker | `expanded_postscript_P.P.S_T` | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T / [F,F,T] / F | T,T | T,T | dataset | 신규 |
| 3710:2 | PostscriptChecker | `expanded_postscript_P.P.S_F` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | 신규 |
| 1800:0 | PostscriptChecker | `expanded_postscript_P.S._T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 1800:0 | PostscriptChecker | `expanded_postscript_P.S._F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 3750:0 | ConstrainedResponseChecker | `expanded_constrained_T` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | 신규 |
| 3750:0 | ConstrainedResponseChecker | `expanded_constrained_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 3518:0 | JsonFormat | `expanded_json_existence_T` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 신규 |
| 3518:0 | JsonFormat | `expanded_json_existence_F` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | 신규 |
| 3445:0 | ForbiddenWords | `expanded_forbidden_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 3445:0 | ForbiddenWords | `expanded_forbidden_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 3311:0 | ResponseLanguageChecker | `expanded_language_ko_T` | T / [T,F,T] / F | T / [T,F,T] / F | T / [T,F,T] / F | T / [T,F,T] / F | T,T | T,T | dataset | 신규 |
| 3311:0 | ResponseLanguageChecker | `expanded_language_ko_F` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | 신규 |
| 1127:1 | EndChecker | `expanded_end_F` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | 신규 |
| 122:0 | QuotationChecker | `expanded_quotation_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 122:0 | QuotationChecker | `expanded_quotation_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 3563:0 | RepeatPromptThenAnswer | `expanded_repeat_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 3563:0 | RepeatPromptThenAnswer | `expanded_repeat_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_8_10` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 신규 |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_8_9` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 신규 |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_7_10` | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F / [F,T] / F | F,F | F,F | dataset | 신규 |
| 1203:0 | KeywordFrequencyChecker | `expanded_repeat_id_7_9` | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F / [F,F] / F | F,F | F,F | dataset | 신규 |
| 2142:0 | KeywordFrequencyChecker | `expanded_predatory_ko` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 2142:0 | KeywordFrequencyChecker | `expanded_predatory_literal` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 1268:0 | NumberOfSentences | `expanded_sent_lt_6_multiline` | F / [F] / F | T / [T] / T | F / [F] / F | T / [T] / T | F,F | T,T | dataset | 신규 |
| 3538:0 | KeywordFrequencyChecker | `expanded_characters_600_not_words` | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T / [T,F] / F | T,T | T,T | dataset | 신규 |
| 1954:0 | ParagraphFirstWordCheck | `expanded_last_paragraph_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 1954:0 | ParagraphFirstWordCheck | `expanded_last_paragraph_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 136:0 | BulletListChecker | `expanded_bullets_10_unpadded` | F / [F,T] / F | T / [T,T] / T | F / [F,T] / F | T / [T,T] / T | F,F | T,T | dataset | 신규 |
| 3750:0 | ConstrainedResponseChecker | `expanded_constrained_multi` | F / [F] / F | F / [F] / F | T / [T] / T | T / [T] / T | F,T | F,T | dataset | 신규 |
| 3311:0 | ResponseLanguageChecker | `expanded_language_empty` | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F / [F,F,F] / F | F,F | F,F | dataset | 신규 |
| 3311:0 | ResponseLanguageChecker | `expanded_language_short_exception` | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T / [T,F,F] / F | T,T | T,T | dataset | 신규 |
| 240:0 | ResponseLanguageChecker | `expanded_language_ru_T` | T / [T] / T | T / [T] / T | T / [T] / T | T / [T] / T | T,T | T,T | dataset | 신규 |
| 240:0 | ResponseLanguageChecker | `expanded_language_ru_F` | F / [F] / F | F / [F] / F | F / [F] / F | F / [F] / F | F,F | F,F | dataset | 신규 |
| 1262:0 | TitleChecker | `expanded_selected_1262_smoke` | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T / [T,T] / T | T,T | T,T | dataset | 신규 |

## 6. 별도 호환성·오류 입력

| case | checker | 영어 strict/loose | Ko strict/loose | 분류 |
| --- | --- | --- | --- | --- |
| `support_filter_null` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | 합성 호환성 |
| `support_filter_zero` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | 합성 호환성 |
| `support_filter_empty_string` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | 합성 호환성 |
| `support_filter_empty_list` | `length_constraints:number_words` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | 합성 호환성 |
| `support_keyword_absent` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | 예상한 예외 확인 |
| `support_keyword_null` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | 예상한 예외 확인 |
| `support_keyword_empty_string` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | 예상한 예외 확인 |
| `support_keyword_empty_list` | `keywords:existence` | F / [F] / F; F / [F] / F | ValueError; ValueError | 예상한 예외 확인 |
| `support_bad_relation` | `length_constraints:number_words` | ValueError; ValueError | ValueError; ValueError | 예상한 예외 확인 |
| `support_letter_a` | `keywords:letter_frequency` | F / [F] / F; F / [F] / F | F / [F] / F; F / [F] / F | 합성 호환성 |
| `support_letter_aa` | `keywords:letter_frequency` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | 합성 호환성 |
| `support_capital_T` | `change_case:english_capital` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | 합성 호환성 |
| `support_capital_F` | `change_case:english_capital` | F / [F] / F; F / [F] / F | F / [F] / F; F / [F] / F | 합성 호환성 |
| `support_lowercase_T` | `change_case:english_lowercase` | T / [T] / T; T / [T] / T | T / [T] / T; T / [T] / T | 합성 호환성 |
| `support_lowercase_F` | `change_case:english_lowercase` | F / [F] / F; F / [F] / F | F / [F] / F; F / [F] / F | 합성 호환성 |
| `support_capital_words_HELLO` | `change_case:capital_word_frequency` | T / [T] / T; T / [T] / T | AttributeError; AttributeError | 예상한 예외 확인 |
| `support_capital_words_hello` | `change_case:capital_word_frequency` | F / [F] / F; F / [F] / F | AttributeError; AttributeError | 예상한 예외 확인 |
| `support_unregistered` | `keywords:key_sentences` | KeyError; KeyError | KeyError; KeyError | 예상한 예외 확인 |

## 7. 재현·이식 인계

156건의 실험 결과에 입력 재현의 검증 근거를 포함했다. 기준 결과와의 일치 여부는 원시 결과의 `baseline_reproduction`과 `summary`에서 확인할 수 있다. 비교표는 동일 Ko 입력을 전달한 156건을 기준으로 집계한다.

고정한 코드·데이터 21개 파일, 실제로 불러온 네 모듈, NLTK 자원과 입력·응답의 해시를 확인했다. 실행 단계·객체 생성·초기화·후보 처리 기록을 검사하고, instruction별 후보 OR·문항별 AND·단계별 새 객체·`if v` 필터·문항별 instruction 수가 다른 집계도 확인했다.

A안은 원본 Ko의 채점 규칙을 가깝게 보존하고 기존 영어/French 코드의 변경 범위를 줄이기 위한 선택이다. B안도 같은 정책과 객체 생성 방식을 보존하면 구현할 수 있다.

재현 명령은 README에 정리했다. [이슈 첨부 초안](issue-1463.ko.md)은 로컬에 준비했으며 아직 게시하지 않았다. [manifest](manifest.json), [검증 범위](coverage.json), [원본 문항 목록](source_rows.md)을 함께 확인할 수 있다.
