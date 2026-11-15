# 문항 선정 범위 집계

**한국어** | [English](coverage.en.md)

고정 revision: `54199e3801116897697babf341865741dcd06fc8`. 데이터: 342문항·481개 지시·21종.

입력 조건을 집계한 결과이며 모델 실행·코드 분기 실행률·고정 응답 회귀 결과가 아니다. 선정안은 팀 검토 전 제안이다.

| 목록 | 문항 | 지시 | ID 포함 | 입력 경로 포함 | 반복 ID 문항 | 복수 지시 문항 |
| --- | --- | --- | --- | --- | --- | --- |
| 선정안 | 23 | 40 | 21/21 | 25/25 | [1203] | 13 |

## 유형별 대응

| instruction ID | 전체 발생 | 선정 문항 발생 | 선정 key | Ko 관련 변경 근거 |
| --- | --- | --- | --- | --- |
| `combination:repeat_prompt` | 26 | 1 | 3563 | 제작자 열거 수정 클래스 |
| `combination:two_responses` | 19 | 1 | 1107 | — |
| `detectable_content:number_placeholders` | 20 | 1 | 3743 | — |
| `detectable_content:postscript` | 19 | 2 | 3710, 1800 | — |
| `detectable_format:constrained_response` | 10 | 1 | 3750 | Ko 고정 선택 문구 |
| `detectable_format:json_format` | 14 | 1 | 3518 | — |
| `detectable_format:multiple_sections` | 11 | 1 | 1127 | — |
| `detectable_format:number_bullet_lists` | 24 | 1 | 136 | — |
| `detectable_format:number_highlighted_sections` | 38 | 2 | 3710, 2035 | — |
| `detectable_format:title` | 27 | 5 | 3442, 1262, 3710, 3311, 1928 | — |
| `keywords:existence` | 22 | 2 | 3518, 3311 | 제작자 열거 수정 클래스 |
| `keywords:forbidden_words` | 28 | 1 | 3445 | 제작자 열거 수정 클래스 |
| `keywords:frequency` | 25 | 6 | 1233, 1203, 2142, 3538, 1928 | 제작자 열거 수정 클래스 |
| `language:response_language` | 25 | 1 | 3311 | — |
| `length_constraints:nth_paragraph_first_word` | 2 | 1 | 3073 | 제작자 열거 수정 클래스 |
| `length_constraints:number_paragraphs` | 19 | 1 | 1082 | — |
| `length_constraints:number_sentences` | 31 | 3 | 1262, 1268, 2035 | Ko 문장 utility |
| `length_constraints:number_words` | 36 | 3 | 136, 3442, 3538 | Ko 단어 utility |
| `punctuation:no_comma` | 42 | 2 | 1107, 1928 | — |
| `startend:end_checker` | 15 | 2 | 1233, 1127 | 제작자 열거 수정 클래스 |
| `startend:quotation` | 28 | 2 | 122, 2035 | — |

Ko 수정 클래스 표시는 고정 제작자 문서의 열거 기준이며, ‘—’가 영어와의 완전한 동등성을 뜻하지 않는다.

## 지시 유형별 입력 경로

| instruction ID | 입력 경로 | 전체 발생 | 선정 문항 발생 |
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

`default`는 관찰된 정상 kwargs에서 값에 따른 명시적 경로 선택이 없는 유형이다. 응답별 성공·실패를 하나로 합쳐 검증했다는 뜻이 아니다.

입력 경로 집계는 check_following의 kwargs 유래 속성과 상수의 동등 비교를 AST로 확인하고 실제 데이터에 등장하는 값을 센다. 나머지 파라미터의 수치·문구·언어 값은 같은 연산의 인자이며 모든 값을 개별 경로로 세지 않는다.

데이터에 없는 누락·오류·난수 fallback, 추신의 기타 표지, 응답에 따른 분기, NFC/NFD·정규식·문장/단어 경계는 고정 응답 회귀 대상이다. 이 출력은 해당 검사를 실행하지 않는다.


[선정 안내](README.md) · [설계 문서](../../design.md#fixed-response-regression)
