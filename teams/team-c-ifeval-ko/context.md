## 개인작업

- agent의 context 유지를 위한 문서
- 절대 git에 푸시하거나 커밋하지 않는다.

---
## 86건 테스트 확장

23문항 선정안은 21종 ID·25개 입력 경로를 포함하지만, 기존 86건으로 전체 동작 검증이 완료되지는 않았습니다. 보완안은 고정 응답 156건, 별도 호환성·오류 입력 18건입니다. 아래 응답 후보의 기대값은 원본 Ko에서 확인했습니다. 새 Lighteval-Ko 동등성 검증은 미수행입니다.

현재 PR #30 (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/pull/30)의 head는 **aa16a077bb4a06bf2bc92c285e4c9c98509fc240**으로, 이전 검토 이후 변경이 없습니다. PR 자체의 변경도 analysis.md, design.md 두 파일, 19줄 추가·13줄 삭제입니다. 따라서 PR 설명의 회귀테스트 확장은 실제 fixture 추가와 문서상 계획 확장을 구분해서 표현해야 합니다.

분석 기준은 다음과 같이 고정했습니다. 출처는 첨부된 provenance.json (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/checker-audit/provenance.json)입니다.

| 대상 | 고정 revision |
|---|---|
| PR 문서·첨부 증거 | aa16a077bb4a06bf2bc92c285e4c9c98509fc240 |
| Allganize Ko 데이터·평가기 | 54199e3801116897697babf341865741dcd06fc8 |
| 영어 lm-evaluation-harness | d6de81643928d653435c431bae19945d41d32520 |
| 영어 google/IFEval 데이터 | 966cd89545d6b6acfd7638bc708b98261ca58e84 |
| Lighteval 참고 구현 | c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14 |

요청한 문서·스크립트·JSON과 고정 원본 네 모듈을 읽었습니다. 보존된 21개 source 파일의 hash를 확인했고, Ko 네 모듈과 Parquet은 고정 URL에서 메모리로 다시 받아 hash도 대조했습니다. 파일 수정·커밋·푸시·GitHub 쓰기는 하지 않았습니다.

1. 기존 86건의 실제 커버리지

원본에서 독립 재확인한 수치는 다음과 같습니다.

| 구분 | 재확인 결과 |
|---|---:|
| 전체 default/train | 342문항·481개 instruction 발생·21종 ID |
| 기존 86건 | 실제 데이터 조건 46·메모리 override 2·합성 입력 38 |
| 실제 데이터 조건의 고유 key | 11개 |
| 주 검사 대상 | 8종 ID·8개 입력 경로 |
| full 평가의 등장 범위 | 13종 ID·13개 입력 경로 |
| 86건의 full instruction 판정 발생 | 121개 |
| 23문항 선정안 | 40개 instruction·21/21종·25/25개 입력 경로 |

실제 데이터 고유 key는 다음 11개입니다.

[127, 136, 349, 1127, 1237, 1242, 1480, 3073, 3345, 3442, 3739]

아래는 저장된 ko_results.json (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/checker-audit/ko_results.json) 재집계입니다. 수치는 모두 통과/실패이며, —는 해당 평가가 없다는 뜻입니다. full 열은 문항 전체 통과 수가 아니라 그 ID의 개별 instruction 판정 수입니다. 실제·override·합성을 합친 86건 기준입니다.

| instruction ID·입력 경로 | 주/full | isolated strict | isolated loose | full strict | full loose | 경계 검증 상태 |
|---|---|---:|---:|---:|---:|---|
| combination:repeat_prompt | Y/Y | 6/0 | 6/0 | 6/0 | 6/0 | 실패 없음 |
| combination:two_responses | —/— | — | — | — | — | 없음 |
| detectable_content:number_placeholders | —/— | — | — | — | — | 없음 |
| detectable_content:postscript·P.P.S | —/— | — | — | — | — | 없음 |
| detectable_content:postscript·P.S. | —/— | — | — | — | — | 없음 |
| detectable_format:constrained_response | —/— | — | — | — | — | 없음 |
| detectable_format:json_format | —/Y | — | — | 3/2 | 3/2 | 부수 조건으로만 검사 |
| detectable_format:multiple_sections | —/Y | — | — | 0/2 | 0/2 | 통과 없음 |
| detectable_format:number_bullet_lists | —/Y | — | — | 6/3 | 6/3 | 정확한 N은 있으나 N±1 세트 없음 |
| detectable_format:number_highlighted_sections | —/Y | — | — | 3/2 | 3/2 | N±1 세트 없음 |
| detectable_format:title | —/Y | — | — | 3/6 | 3/6 | 전용 검사 없음 |
| keywords:existence | Y/Y | 10/0 | 10/0 | 10/0 | 10/0 | 누락 키워드 실패 없음 |
| keywords:forbidden_words | Y/Y | 5/8 | 5/8 | 10/8 | 10/8 | 정확 일치·조사·합성어 포함 |
| keywords:frequency·at least | Y/Y | 11/2 | 11/2 | 11/2 | 11/2 | 정확한 N 있음, N±1 세트 없음 |
| keywords:frequency·less than | —/— | — | — | — | — | 없음 |
| language:response_language | —/— | — | — | — | — | 없음 |
| length_constraints:nth_paragraph_first_word | Y/Y | 4/3 | 4/3 | 4/3 | 4/3 | 문단 수 N±1·마지막 문단 없음 |
| length_constraints:number_paragraphs | —/— | — | — | — | — | 없음 |
| length_constraints:number_sentences·less than | Y/Y | 10/1 | 11/0 | 10/1 | 11/0 | <3의 2·3문장 있음, 4문장 없음 |
| length_constraints:number_sentences·at least | —/— | — | — | — | — | 없음 |
| length_constraints:number_words·less than | Y/Y | 9/11 | 14/6 | 9/11 | 14/6 | 여러 임계값 있으나 동일 조건의 N±1 세트 불완전 |
| length_constraints:number_words·at least | —/— | — | — | — | — | 없음 |
| punctuation:no_comma | —/— | — | — | — | — | 없음 |
| startend:end_checker | Y/Y | 6/0 | 6/0 | 6/0 | 6/0 | 실패 없음 |
| startend:quotation | —/— | — | — | — | — | 없음 |

특히 다음 공백이 확인됐습니다.

- 키워드 존재·끝 문구·프롬프트 반복: Ko 실패 사례가 각각 0건입니다.
- 섹션: 통과 사례가 0건입니다.
- 문장 수: strict 실패 1건도 loose에서는 복구되어, loose 실패가 0건입니다.
- 첫 문단 첫 단어: 실제 데이터 조건은 2건 모두 통과합니다. 실패 3건은 합성·override에서만 나옵니다.
- JSON·bullet·강조·제목에 양쪽 결과가 있어도, 기존에는 전용 대상이 아니므로 그대로 검증 완료로 승격하면 안 됩니다.

재집계와 별도로, 원본 소스를 import한 isolated-source 방식으로 Ko 86건과 영어 86건을 재실행했습니다. 양쪽 모두 오류 없이 저장된 isolated/full의 개별·문항 strict/loose Boolean과 86/86 일치했습니다. 이는 package 상위 namespace를 구성해 원본 모듈을 실행한 결과이며, 전체 task CLI·모델 실행·새 Lighteval-Ko 실행은 아닙니다. 영어 결과는 original_results.json (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/checker-audit/original_results.json)의 재현 확인에 사용했고, Ko와의 판정 일치를 합격 기준으로 삼지 않았습니다.

2. 수집할 원본 문항과 조건

아래 23문항을 유지하고, 마지막 문단 검사 1954와 다른 요구 언어 검사 240을 추가합니다. 수집 목록은 25문항·42개 instruction입니다. 기존 회귀의 11개 key까지 보존하면 교집합 4개를 제외해 32개 원본 key·55개 원본 instruction 조건을 사용합니다.

모든 행의 데이터 출처는 같은 고정 Parquet (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/data/train-00000-of-00001.parquet)입니다. ID 링크는 같은 revision의 해당 checker 코드 위치입니다. 표의 index는 0부터 시작하며, 한 행의 전체 instruction을 원본 순서대로 표시했습니다.

kwargs는 가독성을 위해 null만 생략했습니다. 아래 24개 필드 중 각 조건에 표시하지 않은 필드는 모두 원본에서 null입니다. 따라서 표의 {}도 원본의 null 필드를 삭제하라는 뜻이 아닙니다. raw kwargs는 별도로 그대로 보존해야 합니다.

capital_frequency, capital_relation, end_phrase, first_word, forbidden_words,
frequency, keyword, keywords, language, let_frequency, let_relation, letter,
nth_paragraph, num_bullets, num_highlights, num_paragraphs, num_placeholders,
num_sections, num_sentences, num_words, postscript_marker, prompt_to_repeat,
relation, section_spliter

| key | 전체 instruction 순서와 kwargs | 원문 관련 지시·선정 이유·응답 구성 |
|---|---|---|
| 3743 | 0. detectable_content:number_placeholders (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L287) {"num_placeholders":3} | 대괄호 자리 표시자 최소 3개. 기존 미포함 유형. [항목] 2·3·4개로 경계 구성 |
| 136 | 0. detectable_format:number_bullet_lists (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L334) {"num_bullets":9}<br>1. length_constraints:number_words (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L905) {"num_words":100,"relation":"less than"} | 정확히 9개 bullet·100단어 미만. 8·9·10개 및 줄 삭제·별표 제거 상호작용 검사 |
| 3518 | 0. detectable_format:json_format (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L935)<br>1. keywords:existence (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L778) {"keywords":["보상","이민자"]} | JSON만 출력하고 두 키워드 포함. 유효 JSON·두 키워드 통과와, 비JSON·키워드 누락 실패 구성 |
| 1233 | 0. startend:end_checker (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1333) {"end_phrase":"도와드릴 수 있는 다른 것이 있나요?"}<br>1. keywords:frequency (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) {"frequency":8,"keyword":"마천루","relation":"at least"} | 지정 끝 문구와 마천루 최소 8회. 빈도 7·8·9회 및 full 순서 보존 |
| 3445 | 0. keywords:forbidden_words (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1155) {"forbidden_words":["컴퓨터","과학"]} | 두 금지어 사용 금지. 컴퓨터 실패, 컴퓨터를 통과라는 현재 정규식 경계 보존 |
| 3442 | 0. length_constraints:number_words (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L905) {"num_words":20,"relation":"less than"}<br>1. detectable_format:title (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360) | 20단어 미만·이중 꺾쇠 제목. 19·20·21단어와 기존 제목 통과·실패 응답 재사용 |
| 1262 | 0. detectable_format:title (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360)<br>1. length_constraints:number_sentences (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L237) {"num_sentences":5,"relation":"less than"} | 제목·5문장 미만. <<제목>> 뒤 4문장으로 full 통과 확인. <N 경계 전용 검사는 1268 사용 |
| 1082 | 0. length_constraints:number_paragraphs (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L593) {"num_paragraphs":2} | ***로 구분한 정확히 2단락. 1·2·3단락 구성 |
| 1127 | 0. detectable_format:multiple_sections (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L543) {"num_sections":4,"section_spliter":"섹션"}<br>1. startend:end_checker (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1333) {"end_phrase":"제가 놓친 수업에 대한 돈을 돌려받을 수 있을까요?"} | 섹션 4개·지정 끝 문구. 섹션 3·4·5개로 기존 통과 공백 보완. checker는 실제로 ≥4 |
| 3710 | 0. detectable_format:number_highlighted_sections (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L469) {"num_highlights":2}<br>1. detectable_format:title (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360)<br>2. detectable_content:postscript (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L653) {"postscript_marker":"P.P.S"} | 최소 2개 강조·제목·P.P.S 후기. 강조 1·2·3개와 해당 추신 표지 전용 통과·실패 |
| 122 | 0. startend:quotation (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1618) | 전체 응답 큰따옴표. "내용"과 내용 비교 |
| 3563 | 0. combination:repeat_prompt (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1298) {"prompt_to_repeat":"반지의 제왕에서 간달프를 연기한 배우의 이름은 무엇인가요?"} | 질문을 먼저 그대로 반복. 지정 문자열+답변과 답변만 있는 응답 비교 |
| 1107 | 0. punctuation:no_comma (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1530)<br>1. combination:two_responses (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1243) | 쉼표 금지·******로 두 농담 구분. 응답 1·2·3개, 쉼표 유무를 명시적 대상으로 검사 |
| 3073 | 0. length_constraints:nth_paragraph_first_word (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1014) {"first_word":"회사","nth_paragraph":1,"num_paragraphs":4} | 두 줄바꿈으로 4단락, 첫 단락은 회사로 시작. 3·4·5단락과 기존 NFC/NFD 재사용 |
| 3311 | 0. language:response_language (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L164) {"language":"ko"}<br>1. detectable_format:title (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360)<br>2. keywords:existence (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L778) {"keywords":["지표","목표","관리"]} | 한국어·제목·세 키워드. 긴 한국어/영어 응답, 빈 응답, 짧은 숫자 응답으로 언어 경로 확인 |
| 3750 | 0. detectable_format:constrained_response (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L373) | 지정 선택 문구 포함. 한 문구·여러 문구·문구 없음 비교 |
| 1203 | 0. keywords:frequency (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) {"frequency":8,"keyword":"전쟁","relation":"at least"}<br>1. keywords:frequency (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) {"frequency":10,"keyword":"peace","relation":"at least"} | prompt는 전쟁·평화, kwargs는 전쟁·peace. 두 index를 독립 식별해 네 Boolean 조합 구성 |
| 2142 | 0. keywords:frequency (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) {"frequency":2,"keyword":"predatory","relation":"at least"} | prompt의 포식자와 kwargs 불일치. 포식자 2회 실패·predatory 2회 통과 보존 |
| 1268 | 0. length_constraints:number_sentences (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L237) {"num_sentences":6,"relation":"less than"} | 자연어는 6문장 이하, checker는 <6. 한 줄 5·6·7문장과 여러 줄 6문장 비교 |
| 3538 | 0. keywords:frequency (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) {"frequency":1,"keyword":"폭탄","relation":"at least"}<br>1. length_constraints:number_words (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L905) {"num_words":600,"relation":"at least"} | 자연어는 600자 이상, checker는 600단어 이상. 폭탄을 포함한 599·600·601단어 및 긴 한 단어 응답 |
| 1928 | 0. detectable_format:title (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360)<br>1. punctuation:no_comma (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1530)<br>2. keywords:frequency (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) {"frequency":3,"keyword":"피부","relation":"less than"} | 제목·쉼표 금지·피부 3회 미만. 기존에 없는 빈도 <N을 2·3·4회로 검사 |
| 2035 | 0. detectable_format:number_highlighted_sections (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L469) {"num_highlights":2}<br>1. startend:quotation (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1618)<br>2. length_constraints:number_sentences (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L237) {"num_sentences":5,"relation":"at least"} | 강조·큰따옴표·최소 5문장. 기존에 없는 문장 수 ≥N을 4·5·6문장으로 검사 |
| 1800 | 0. detectable_content:postscript (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L653) {"postscript_marker":"P.S."} | P.S. 후기. P.P.S와 다른 정규식 경로의 통과·실패 확보 |
| 1954 추가 | 0. length_constraints:nth_paragraph_first_word (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1014) {"first_word":"요약","nth_paragraph":7,"num_paragraphs":7} | 정확히 7단락, 마지막이 요약으로 시작. 첫 단락 검사만으로 놓치는 위치 검증 |
| 240 추가 | 0. language:response_language (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L164) {"language":"ru"} | 어린이에게 격자를 러시아어로 설명. 원본의 다른 요구 언어를 유지해 러시아어 통과·한국어 실패 확인 |

25개 입력 경로는 문항 수나 전체 코드 분기 수가 아닙니다. 빈도·문장 수·단어 수의 두 relation과 추신의 두 marker를 구분한 8개 경로 + 나머지 17종 기본 경로입니다. 누락 kwargs·오류·난수 fallback·응답 문법 분기는 별도입니다. 원본 기반 집계는 audit_coverage.py (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/sample-coverage/audit_coverage.py)와 coverage.json (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/sample-coverage/coverage.json)으로도 대조했습니다.

3. 고정 응답 구성과 필요한 case 수

아래의 TT/FF/FT는 **대상 instruction의 (strict, loose)**입니다. 통과 응답이라도 다른 instruction은 실패할 수 있으며, 그 경우에도 full 전체 flags와 문항 AND를 함께 저장합니다.

응답 생성 규칙은 다음과 같습니다.

- 단어 수: 공백으로 구분한 평가를 사용합니다. 3442는 제목을 1단어로 포함하고, 3538은 폭탄을 1단어로 포함합니다.
- 문장 수: 평가합니다.를 공백으로 이어 한 줄에 배치합니다. 줄 삭제 진단만 별도로 여러 줄로 만듭니다.
- 빈도: 지정 keyword를 공백으로 구분해 반복합니다.
- 응답은 checker 검증용 최소 입력입니다. 주제에 적합한 모델 답변이라는 뜻은 아닙니다.

원본 Ko에서 확인한 개수 경계는 다음과 같습니다.

| 전용 경로·대상 | N−1 | N | N+1 | 구성상 주의 |
|---|---|---|---|---|
| 빈도 ≥8·1233:1 | 7회 FF | 8회 TT | 9회 TT | keyword=마천루 |
| 빈도 <3·1928:2 | 2회 TT | 3회 FF | 4회 FF | keyword=피부 |
| 문장 <6·1268:0 | 5문장 TT | 6문장 FF | 7문장 FF | 모두 한 줄 |
| 문장 ≥5·2035:2 | 4문장 FF | 5문장 TT | 6문장 TT | 다른 두 조건의 flags도 보존 |
| 단어 <20·3442:0 | 19단어 TT | 20단어 FF | 21단어 FF | 20단어는 기존 comma_boundary_spaced 재사용 |
| 단어 ≥600·3538:1 | 599단어 FF | 600단어 TT | 601단어 TT | 모두 폭탄 1회 포함 |
| 자리 표시자 ≥3·3743:0 | 2개 FF | 3개 TT | 4개 TT | [항목] 반복 |
| bullet =9·136:0 | 8개 FF | 9개 TT | 10개 FF | 8·10개 응답은 앞뒤에 빈 줄 2개씩 |
| 강조 ≥2·3710:0 | 1개 FF | 2개 TT | 3개 TT | 1·2개는 *강조*, 3개는 **강조** |
| 섹션 ≥4·1127:0 | 3개 FF | 4개 TT | 5개 TT | 한 줄에 섹션 1 내용 … |
| 문단 =2·1082:0 | 1개 FF | 2개 TT | 3개 FF | 한 줄에서 ***로 구분 |
| 문단·첫 단어·3073:0 | 3개 FF | 4개 TT | 5개 FT | 5개는 마지막 줄 삭제로 복구 |
| 두 응답·1107:1 | 1개 FF | 2개 TT | 3개 FF | 서로 다른 내용을 ******로 구분 |

나머지 12개 경로는 다음 통과·실패 쌍을 둡니다.

| 경로 | 전용 통과 / 실패 구성 |
|---|---|
| 반복·3563:0 | 정확한 prompt_to_repeat+답변 TT / 답변만 FF |
| P.P.S·3710:2 | 본문 P.P.S 후기 TT / 본문 FF |
| P.S.·1800:0 | 본문 P.S. 후기 TT / 본문 FF |
| 고정 선택·3750:0 | 제 답변은 예입니다. TT / 답변입니다. FF |
| JSON·3518:0 | JSON fence 안의 {"보상":"이민자"} TT / 보상 FF |
| 키워드 존재·3518:1 | 위 JSON TT / 보상 FF — JSON 쌍과 같은 응답을 명시적으로 공동 사용 |
| 제목·3442:1 | 기존 comma_boundary_compact TT / comma_compact FF |
| 금지어·3445:0 | 컴퓨터를 TT / 컴퓨터 FF — 조사 경계 동작 보존 |
| 언어·3311:0 | 긴 한국어 응답 TT / 긴 영어 응답 FF |
| 쉼표 금지·1107:0 | 두 응답 검사의 1개 응답은 쉼표 없이 TT / 3개 응답 중 첫 내용에 쉼표를 넣어 FF |
| 끝 문구·1127:1 | 기존 nfc_dataset_end_checker_nfc TT / 끝 FF |
| 큰따옴표·122:0 | "내용" TT / 내용 FF |

언어 판정에 사용한 긴 응답은 다음과 같습니다. 한국어·영어·러시아어 통과 후보는 각각 반복 확인에서도 같은 결과였습니다.

한국어:
서비스의 신뢰성을 관리하는 업무입니다. 서비스 지표를 살피고 목표를 정하며 장애의 원인을 분석합니다.

영어:
The reliability engineer monitors service quality and resolves operational incidents. This response is written entirely in English.

러시아어:
Решётка представляет собой упорядоченную структуру из повторяющихся элементов. Эти элементы соединяются между собой и образуют регулярный узор.

별도 진단 12건은 다음처럼 구성합니다. 아래 결과도 원본 Ko에서 확인했습니다.

| 진단 | 건수 | 기대값 |
|---|---:|---|
| 1203의 전쟁/peace 횟수 (8,10), (8,9), (7,10), (7,9) | 4 | strict와 loose 각각 [T,T], [T,F], [F,T], [F,F] |
| 2142의 포식자 2회 / predatory 2회 | 2 | FF / TT |
| 1268의 6문장을 줄마다 하나씩 배치 | 1 | FT. 한 줄 6문장 FF와 구분 |
| 3538의 "폭탄" + "가"*600, 공백 없음 | 1 | 두 instruction 모두 strict/loose [T,F]: 602자지만 1단어 |
| 1954의 7단락 중 마지막 / 첫 번째만 요약으로 시작 | 2 | TT / FF |
| 136의 10개 bullet, 앞뒤 빈 줄 없음 | 1 | FT. 보호용 빈 줄이 있는 10개 FF와 구분 |
| 3750에 예·아니요 선택 문구를 모두 포함 | 1 | TT. 현재 checker의 포함 검사 보존 |
| 합계 | 12 |  |

언어·엔진 입력 4건은 3311의 빈 문자열 FF, "123" TT, 240의 러시아어 TT·한국어 FF입니다. "123"의 TT는 언어 적합성이 아니라 원본이 LangDetectException을 내부에서 잡아 True를 반환하는 정책입니다.

또한 23문항 모두를 저장 응답 경로로 한 번 이상 처리하도록 1262에 <<제목>>+4문장인 full TT 1건을 둡니다.

필요량 산식은 다음과 같습니다.

| 계산 | 건수 |
|---|---:|
| 25개 경로 × 통과·실패 2개 | 50개 검증 슬롯 |
| 개수 조건 13개 경로의 세 번째 경계값 | +13 |
| JSON/키워드·두 응답/쉼표 공동 응답 | −4 |
| 실제 응답 레코드 | 59 |
| 기존 응답 그대로 재사용 | −6 |
| 경로 전용 신규 응답 | 53 |
| 1262의 선정 문항 실행 확인 | +1 |
| 진단 | +12 |
| 언어·엔진 입력 | +4 |
| 신규 응답 | 70 |
| 기존 86 + 신규 70 | 156건 |

재사용하는 6건과 대상 index는 다음과 같습니다.

| 기존 case_id | 명시할 대상 |
|---|---|
| comma_boundary_spaced | 3442:0 단어 수 |
| markdown_star_balanced_136 | 136:0 bullet |
| nfc_dataset_first_word_nfc | 3073:0 첫 문단 |
| comma_boundary_compact | 3442:1 제목 |
| comma_compact | 3442:1 제목 |
| nfc_dataset_end_checker_nfc | 1127:1 끝 문구 |

제목·bullet은 이번에 그 index의 isolated 평가까지 따로 실행하여 전용 대상으로 승격 가능한 것을 확인했습니다. 단순 full 등장만으로 재사용한 것이 아닙니다.

따라서 이전 86+61+10=157은 고정 목표로 채택하지 않습니다. 이번에 구체화한 안은 156건 = 실제 데이터 조건 116 + override 2 + 합성 38입니다. 응답 레코드의 full instruction 발생 분모는 247입니다.

이 156건 구성에 대한 원본 Ko 기준 집계는 아래와 같습니다. 이는 회귀 fixture 집계이며 모델 벤치마크 점수가 아닙니다.

| 지표 | 원본 Ko 기준 분자/분모 |
|---|---:|
| prompt strict | 71/156 |
| instruction strict | 133/247 |
| prompt loose | 79/156 |
| instruction loose | 142/247 |

신규·재사용 후보 76개 응답 레코드를 원본 Ko에서 검사했고, 모든 명시적 대상의 isolated/full 결과가 일치했습니다. 그 안에서 25/25개 경로 모두 TT·FF가 존재함을 확인했습니다. 아직 fixture 파일이나 새 task 테스트로 작성한 상태는 아닙니다.

4. 테스트 도구·문서 보완 계획

build_cases.py:23–33 (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/checker-audit/build_cases.py#L23)의 checker 매핑은 요청한 대로 8종으로 제한돼 있습니다. instruction_id_list.index(iid)도 사용하므로, 1203을 추가하면 기본적으로 첫 번째 전쟁 조건만 선택합니다.

audit_runtime.py:133 (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/checker-audit/audit_runtime.py#L124)에는 instruction_index를 받는 경로가 있지만 기본값은 여전히 .index(iid)입니다. builder에서 index를 확정하고 runtime에서 검증하도록 바꿔야 합니다.

| 대상 | 필요한 보완 |
|---|---|
| 대상 식별 | instruction_index 필수화. ids[index] == instruction_id, 목록 길이, 해당 kwargs 대응 검증 |
| checker 매핑 | registry에서 클래스명·코드 위치를 얻도록 일반화. 미등록 ID를 임의 checker로 대체하지 않음 |
| 반복 ID | 1203:0, 1203:1을 별도 대상으로 저장. trace도 ID만으로 식별하지 않음 |
| 고유 ID | 응답 레코드별 case_id와 명시적 targets 목록. 중복 ID는 저장 전 오류 처리 |
| 입력 무결성 | 원본 prompt·전체 IDs·raw kwargs·source revision·원본 파일 hash 보존 |
| 응답 무결성 | raw UTF-8 응답 hash와 NFC 후 응답 hash를 구분 |
| 기대값 | 의도한 사전 기대값, 원본 Ko 관측값, 새 task 관측값을 별도 필드로 저장 |
| 결과 저장 | case_id 기준 list/레코드 저장. key 하나를 dict 키로 사용하지 않음 |
| 캐시 | dataset/checker revision·입력 hash·응답 hash를 포함. 같은 key의 여러 응답이 덮어써지지 않도록 독립 sample ID 사용 |
| 실행 trace | phase·index·checker 생성/빌드·필터 전후 kwargs·후보 번호·판정 기록 |
| 난수 진단 | 채점 전에 진단용 checker를 추가 생성해 RNG를 소비하지 않음. 진단은 별도 RNG 상태나 프로세스 사용 |
| 비교기 | 개별 flags 길이·순서·타입, prompt AND, 고유 case_id, 누락·오류, 네 지표 분자/분모 검증 |

현재 runtime은 결과를 list로 저장하므로 곧바로 key 덮어쓰기가 발생하는 구조는 아닙니다. 다만 확장 도구·새 task 캐시는 같은 보장을 명시해야 합니다.

문서는 다음 항목을 보완해야 합니다.

- analysis.md (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/analysis.md)와 design.md (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/blob/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/design.md)에서 선정 범위·원본 기대값 확인·새 task 동등성·모델 통합 상태를 분리합니다.
- 기존 86건의 위 커버리지 표와 새 응답별 index·기대값을 연결합니다.
- 23문항·40조건, 수집 25문항·42조건, 전체 원본 pool 32 key·55조건, 회귀 156 case·247판정 발생을 구분합니다.
- 번역 불일치·단위 불일치·정규화 비대칭을 Known Issue로 유지하고 이식 중 수정하지 않습니다.
- PR에서 실제 fixture가 추가됐다는 표현은 변경 파일·실행 증거와 맞춰 정리합니다.

5. 엔진·집계·기존 경로 회귀의 별도 범위

| 항목 | 보존·검증 계획 |
|---|---|
| NFC/NFD | strict·loose 각 진입점에서 응답 NFC. prompt·kwargs 전체를 Doc 변환 시 일괄 정규화하지 않음 |
| 문자열 kwargs | keywords, keyword, forbidden_words, end_phrase, prompt_to_repeat의 checker별 NFC 위치 보존. first_word는 lower만 하는 비대칭도 보존 |
| if v | None뿐 아니라 0, False, "", []가 제거되는 원본 동작 유지. is not None으로 바꾸지 않음 |
| loose 8후보 | 원본, 별표 제거, 첫 줄·마지막 줄·양 끝 줄 제거, 마지막 세 후보의 별표 제거. 순서·중복 유지, 빈 후보 제외 |
| 결합 | instruction별 후보 OR, prompt별 instruction AND. 모든 instruction이 같은 후보에서 통과할 필요 없음 |
| 실행 순서 | Ko는 strict 전체→loose 전체. 각 phase에서 새 checker 생성. 현재 영어의 instruction별 strict→loose·객체 공유와 구분 |
| 언어 | 한국어·실제 다른 요구 언어·빈/짧은 입력·내부 예외 확인. 밖으로 전파된 오류를 True로 바꾸지 않음 |
| 집계 | [[T,T,T],[F]]에서 prompt 0.5, instruction 0.75. 문항별 instruction 비율의 평균 금지 |
| 영어/French | 고정 영어 metric과 French adapter의 변경 전후 판정 비교. 기존 public export·기존 공유 관계 보존 |
| metric 격리 | Ko가 기존 ifeval_metrics 객체·registry·utility·설정을 변경하지 않도록 E→Ko→Fr→Ko→E 순서 검사 |
| optional dependency | 정상 환경과 Ko 의존성 부재 환경에서 관련 없는 task 로딩·열거가 보존되는지 검사 |

근거는 Ko utils.py (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/utils.py#L25), 정규화·길이 utility (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions_util.py#L74), 고정 Lighteval main.py (https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/tasks/ifeval/main.py#L92)입니다. French가 기존 ifeval_metrics를 재사용하는 사실도 고정 French task (https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/multilingual/tasks/french.py#L28)에서 확인했습니다. 이번에는 Lighteval 영어/French 변경 전후 회귀를 실행하지 않았습니다.

데이터 사용 21종과 registry 등록 25종은 분리합니다. 나머지 4종은 다음 합성 호환성 검사 대상입니다.

| 데이터 미사용 registry ID | 입력 2건 | 원본 Ko 확인 결과 |
|---|---|---|
| keywords:letter_frequency | letter=a, frequency=2, at least, 응답 a/aa | FF / TT |
| change_case:english_capital | 긴 영어 대문자/일반 문장 | TT / FF |
| change_case:english_lowercase | 긴 영어 소문자/일반 문장 | TT / FF |
| change_case:capital_word_frequency | 명시적 빈도 조건, HELLO/hello | 두 건 모두 AttributeError |

마지막 checker는 instructions.py:1590 (https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1590)에서 원본 Ko utility에 없는 nltk를 참조합니다. 이를 고치거나 정상 채점 성공으로 계산하지 않습니다.

별도 합성·오류 입력 18건의 구성은 다음과 같습니다.

| 범위 | 건수 | 원본 결과·분류 |
|---|---:|---|
| NumberOfWords의 num_words=None/0/""/[], relation 고정 | 4 | 필터 후 fallback 실행. 정상 결과와 빌드값·RNG trace 비교 대상 |
| KeywordChecker의 kwargs 부재/None/빈 문자열/빈 리스트 | 4 | ValueError |
| 잘못된 relation | 1 | ValueError |
| 위 registry 미사용 4종 × 2 | 8 | 6건 정상 판정·2건 AttributeError |
| 미등록 keywords:key_sentences | 1 | KeyError |
| 합계 | 18 | 정상 반환 10·의도한 외부 예외 8 |

KeySentenceChecker는 클래스가 있어도 registry에 등록돼 있지 않습니다. 신규 등록하지 않으며, 미등록 경로의 오류 계약으로만 취급합니다.

따라서 전체 fixture 목록은 156+18=174개 입력 레코드입니다. 18건은 정상 데이터 25개 경로의 분모에 넣지 않고, 특히 예외 8건을 채점 성공으로 세지 않습니다. 엔진 호출 순서·집계·캐시·의존성 검사는 이 입력들을 활용하는 별도 assertion/scenario로 관리합니다.

6. 실행 순서와 완료 기준

| 순서 | 작업·의존 관계 | 현재 상태 |
|---|---|---|
| 1 | PR head·source revision·hash·전체 데이터 구조·kwargs 대응 확인 | 완료 |
| 2 | 기존 86건 저장 결과 재집계 → 원본 evaluator 재현 | 완료. 영어·Ko 각각 isolated-source 86/86 일치 |
| 3 | 신규 응답을 원본 Ko에서 검사해 strict/loose 기대값 확정 | 이 대화의 후보 기준 완료. fixture·manifest 작성은 후속 작업 |
| 4 | 새 등록 Lighteval-Ko에 동일한 Ko 문항·응답 전달 → index별·문항별·집계 비교 | 미수행. 이 PR에는 새 구현이 없음 |
| 5 | 기존 영어/French 회귀, metric 격리·optional dependency 검사 | 미수행. 공통 코드 변경 전 기준값을 먼저 고정 |
| 6 | 원래 23문항 모델 통합: 응답 한 번 생성·저장 후 양쪽 재채점 | 미수행. 23문항·40조건 유지 |
| 7 | 통합 통과 후 전체 train split 동일 방식 평가 | 미수행. 342문항·481조건 처리 |

모델 단계에서는 모델·tokenizer revision, backend·dtype·seed, chat template, 생성 길이·stop/EOS, 응답 추출·후처리 경계를 고정합니다. 생성 실패를 빈 응답으로 바꾸거나 실패 문항을 분모에서 빼지 않습니다.

완료 기준은 다음과 같습니다.

- 21/21종·25/25개 입력 경로에 명시적 전용 통과·실패 확보. 필요한 개수 경계와 반복 ID 네 조합 포함.
- 원본과 새 task의 개별 instruction·문항 strict/loose Boolean 100% 일치.
- 네 지표의 분자·분모 일치, 절대 오차 1e-12 이하.
- 입력·응답 누락, 미처리 예외, 미해결 불일치 없음. 의도한 예외는 별도 오류 계약으로 일치 확인.
- 영어/French 판정·metric 객체 상태·optional dependency 동작 보존.
- 23문항 통합과 전체 split 평가를 실제 수행한 뒤 각각 별도 완료 표시.

이번에 완료한 범위는 근거 수집, 기존 결과 재집계·원본 재현, 신규 응답의 원본 Ko 기대값 확인, 보완 계획 작성입니다. 새 Lighteval-Ko 동등성·모델 통합·전체 split 평가는 완료하지 않았습니다.

---


해당 부분 테스트를 확장하면 IFEval ko와 원본 IFeval의 판단 경계 구분이 되고, 원본은 T지만 Ko는 F인경우 또는 그 역 (F,T)을 확실히 구분할수있고 메인테이너에게 design.md의 A안으로 가는 이유를 확실히 어필가능하며, Lighteval에 옮길때 반영 가능한가? 에 대해 답변

가능합니다. 테스트를 확장하면 영어 IFEval과 Ko의 판정 차이를 재현 가능한 근거로 제시하고, A안의 설계 근거와 Lighteval 이식 회귀테스트로 사용할 수 있습니다. 다만 두 가지 검증을 분리해야 합니다.

첫째, 영어와 Ko의 판정 경계를 비교합니다.

같은 Ko 문항·kwargs·응답을 두 evaluator에 전달하고, instruction index별로 (영어, Ko) 결과를 기록해야 합니다. strict와 loose도 각각 비교합니다.

이미 기존 사례에서 양방향 차이를 확인했습니다.

| 동일 응답 사례 | 영어 IFEval | 원본 Ko | 차이 원인 |
|---|---|---|---|
| 349·markdown_quote_valid_highlights_349 | 39단어 → T/T | 40단어 → F/F | Ko의 공백 기준에서 >도 단어로 계산 |
| 3442·comma_boundary_compact | 20단어 → F/F | 18단어 → T/T | 쉼표로 붙은 문자열의 단어 분리 차이 |

여기서 T/T는 strict·loose 모두 통과라는 뜻입니다. 입력과 저장 결과는 기존 증거 자료 (https://github.com/Hugging-Face-KREW/k-llm-eval-sprint/tree/aa16a077bb4a06bf2bc92c285e4c9c98509fc240/teams/team-c-ifeval-ko/evidence/checker-audit)에 있습니다.

확장할 때는 다음을 지켜야 합니다.

- (T,T), (T,F), (F,T), (F,F)를 비교 결과로 분류하고, 차이가 발생하는 임계값 전후 응답을 확보합니다.
- strict 차이가 loose에서도 유지되는지 확인합니다. 예를 들어 줄 삭제로 Ko 실패가 복구되면 strict에서만 차이가 남을 수 있습니다.
- 번역된 keyword 불일치 같은 데이터 문제와 checker 알고리즘 차이를 분리합니다. 서로 다른 언어별 응답을 비교한 사례만으로 checker 차이를 주장하면 안 됩니다.

따라서 고정 revision과 검사한 응답 범위에서는 경계를 명확히 구분할 수 있습니다. 다만 25개 입력 경로를 검사했다고 모든 가능한 응답의 차이까지 증명하는 것은 아닙니다.

둘째, 이 근거는 A안을 선택하는 이유를 강화합니다.

메인테이너에게 설명할 핵심은 다음과 같습니다.

> 동일한 입력에서도 영어와 Ko reference의 판정이 양방향으로 달라진다. Ko는 단어·문장 계산, NFC 적용 위치, 고정 문구뿐 아니라 strict 전체→loose 전체의 실행 순서와 checker 생성 방식도 보존해야 한다. 따라서 별도 Ko 패키지와 scorer를 두어 원본 동작을 직접 재현하고, 기존 영어·French 경로에 미치는 변경 범위를 줄이려 한다.

이 주장은 실행 결과로 뒷받침할 수 있습니다. 다만 테스트가 A안만 가능함을 증명하지는 않습니다. B안도 정책과 실행 순서를 정확히 분리하면 구현 가능합니다. A안은 원본과 대조하기 쉽고 기존 경로의 회귀 부담을 줄이는 선택으로 설명하는 것이 설득력 있습니다. 작은 채점 루프를 중복 관리하는 비용도 함께 밝히면 됩니다.

Lighteval 이식에도 그대로 반영할 수 있습니다.

이식 시 합격 기준은 다음처럼 나눕니다.

| 검증 목적 | 기준 |
|---|---|
| 영어와 Ko의 차이 설명 | 동일 입력에서 두 reference의 판정 차이를 재현 |
| 새 Lighteval-Ko 검증 | 원본 Ko와 동일한 개별·문항 strict/loose 판정 및 네 지표 |
| 기존 기능 보존 | 기존 Lighteval 영어·French 판정과 metric 상태 유지 |

즉, 영어가 T이고 Ko가 F인 fixture는 새 Lighteval-Ko에서도 F가 나와야 통과합니다. 영어 결과에 맞추는 것이 목표가 아닙니다.

앞서 구성한 156건은 주로 원본 Ko→새 Lighteval-Ko 동등성을 위한 안입니다. 여기에 같은 Ko 입력을 영어 evaluator에도 전달하는 비교 열을 추가하면, 동일 fixture를 A안의 근거와 이식 검증에 함께 활용할 수 있습니다. 현재 확보한 것은 원본 판정과 계획이며, 새 구현의 동등성은 구현 후 별도로 검증해야 합니다.



## 2026-11-03 로컬 구현 진행 기록

- 사용자 승인 범위: 테스트 확장 구현, analysis.md/design.md의 기존 소제목 안에 하위 절 추가, issue #1463용 로컬 첨부 자료. 커밋/푸시/원격 작성 금지.
- 기존 worktree 변경은 CRLF 차이였으며 작업 전 의미 있는 diff는 없었음. private context.md는 보존하고 첨부 archive에서 제외.
- 현재 HEAD aa16a077bb4a06bf2bc92c285e4c9c98509fc240. 원본 고정 revision은 checker-audit/provenance.json 그대로 유지.
- 구현 방침: 기존 86건 JSON/저장 결과는 보존. checker-audit/expanded/에 156건(86+70)과 별도 18건, 동일 Ko 입력을 영어/Ko에 전달한 비교 결과, coverage/영문 이슈 첨부 초안을 생성.
- 기존 case/full/isolated/diagnostics 형태 유지. 명시 index/targets/기대값·입력·응답 hash/오류 계약만 추가. legacy 입력은 별도로 재현하고 identical-Ko 비교와 혼합하지 않음.
- source/venv 재사용 후보: /mnt/c/testifeval/ifevaltest/ifeval_checker_audit/{sources,.venv,.cache/nltk_data}. hash 확인 후 사용.
- issue #1463 read-only 확인: separate ifeval_ko package/scorer 제안, 아직 maintainer 댓글 없음. 게시하지 않음.
- 진행 전 hash와 기존 문서 heading 목록: evidence/checker-audit/.cache/expansion-baseline.json. 완료 시 heading 순서·텍스트 보존 및 범위 밖 파일 hash 불변 검증 필요.
- 다음: 공통 index/source 검증 helper와 확장 builder/runner/verifier 구현 → 원본 실행 → 실제 결과 기반 문서·첨부 보고서 반영.


### 구현 체크포인트 (source 실행 완료)

- case_utils.py: registry AST, 반복 ID index 검증, hash/cache ID/source 무결성. 기존 build_cases.py/audit_runtime.py는 helper 및 외부 source root 사용만 추가; 과거 cases/results는 변경하지 않음.
- build_expanded_cases.py가 expanded/{cases.json=156,support_cases.json=18,source_rows.json=32key55조건,manifest.json} 생성. 기대값은 builder에 사전 선언; 실제 evaluator를 호출하지 않음.
- run_expanded.py: 양쪽 evaluator에 identical Ko 입력; 기존 full/isolated/diagnostics 형식+index별 targets, source frame 생성/build/count trace 추가. 별도 legacy replay도 실행.
- full-package 실행 완료: 영어·Ko 각각 정상156개 오류0; support18은 Ko8개(phase별16회) 의도 예외, 영어는2개(phase별4회); legacy86도 양쪽 실행 완료. Ko156 사전 flags 불일치0 확인.
- compare_expanded.py 검증/결과 생성 실행 중 또는 결과 확인 필요. CLI의 --source-root는 /mnt/c/testifeval/ifevaltest/ifeval_checker_audit 사용.
- 남은 작업: verifier 오류 수정/반례 단위검사, 문서 기존 heading 보존하며 추가·상태 갱신, README·첨부 ZIP·해시, 출력/아카이브/범위 밖 파일 불변 최종 검증. 새 Lighteval-Ko 및 모델 평가는 범위 밖으로 계속 미수행 표기.


### 로컬 구현 완료 및 최종 검증 (2026-11-03)

- 실행·검증 완료: 원본 full-package 양쪽156건 정상 오류0, Ko 사전기대값 불일치0. 별도18건 중 Ko정상10·예외8. 기존 언어별86건 전체 결과 행이 영어/Ko 각각86/86 정확 일치; 일반화한 기존 builder도 archived LF 바이트 재현.
- 전용 실제-data targets:21/21종·25/25경로에 strict/loose TT와 FF;13개 경계군 N−1/N/N+1,1203네조합,loose복구,NFC/if-v/phase/객체/OR/AND/집계검증. negative control16개 통과.
- 같은 Ko 입력의 주대상 비교:strict (EN,Ko) TT74/TF13/FT22/FF47;loose TT84/TF8/FT21/FF43. Ko 지표 분자/분모=71/156,133/247,79/156,142/247. 모델 점수 아님.
- design: 기존 제목 모두 유지,1.3.1 및6.2.1~6.2.4 추가. analysis:6.1.1 및9.3.4 추가. 기존 23문항·40조건 모델선정안 유지.
- 산출물: checker-audit/expanded/에cases/support/source_rows/원시양쪽결과/historical replay/coverage/results.md/issue-1463.md/manifest/validation/test_output. 공통case_utils 및build/run/compare/package_expanded.py,도구test 구현.
- 로컬 첨부: checker-audit/attachments/ifeval-ko-regression.zip (51파일, 약909KB), sha256파일 및manifest. context/source/cache/venv 제외. 압축해제본에서checksum→builder→양쪽runner(all)→compare→16tests→package 전7단계 재현 성공. 증거 .cache/attachment-reproduction.json.
- 범위 밖 파일·원본86건 JSON은 작업 시작 hash와 동일. HEAD aa16a077bb4a06bf2bc92c285e4c9c98509fc240 불변, staged변경0. commit/push/원격 issue·댓글·첨부 작성 전혀 없음.
- 완료 감사: .cache/completion-audit.json. 현재 공개 파일 hash는 audit/SHA256SUMS, 문서 구조 보존은 expanded/validation.json. context는 private로 계속 커밋/첨부 금지.
- 미수행으로 명시: 새 Lighteval-Ko 구현/동등성,현재 Lighteval 영어·French 회귀 및 optional dependency,23문항 모델통합/전체 split모델평가. 이번 목표는 테스트확장·원본 실험·문서·로컬첨부 준비까지 완료.


### 사용자 후속 지시: 기존86 재현·확장156 실험 결과 통합

- 이전 분리 서술을 폐기하고 하나의156건확장실험으로 통합하도록 요청받음. 기존 heading은 계속 유지.
- run_expanded.py가 기존86재현을 normal 결과 각 case의 baseline_reproduction에 포함하고 reproduction 환경/개수를 같은 JSON에 기록. historical_* 생성파일은 동일행 보존 확인 후 제거.
- compare_expanded.py는 통합 재현을 필수검증하고 comparison표에 기존/신규 구성을 표시. 두 입력 계약의 provenance는 유지하되 같은156분모로 동일Ko 비교, 재현86을 중복집계하지 않음.
- design/analysis/양쪽README/생성report·영문이슈초안·ZIP에 반영 진행중. 통합누락·신규case재현중복을 거부하는2개tests를 추가하여 총18개.
- 현재 양쪽 full-package runner 재실행 중. 다음: root README 통합, package로재검증/해시ZIP재생성, 압축해제 재현과문서최종검사. 원격작성/commit/push 금지.


### 사용자 후속 통합 수정 완료

- 사용자 지시에 따라 기존86 재현과 신규70 검증을 하나의156건 확장실험·결과로 통합 완료. 이전 '별도 재현/분리' 지침은 이 항목으로 대체.
- raw original_results.json/ko_results.json은 각각156행이며 기존86행 내부 baseline_reproduction에 원래 입력의 정확재현결과 포함. top-level reproduction에 환경/개수; summary.baseline_reproduction과experiment.reproduction_integrated=true로 검증. historical_*_results.json 생성/첨부 제거.
- 동일Ko 입력 비교의156분모·247instruction·TF/FT수치와원본고정revision 유지; 원래입력재현의provenance는case검증근거로 보존하며분모중복가산안함.
- design/analysis/감사README/expandedREADME/results.md/영문첨부초안/로컬issue-draft.md 모두 통합 서술. analysis8.3도현재동일Ko의dataset116건에서차이11key로갱신. 기존소제목문자열·순서보존.
- 통합재현누락/오염 및신규case의재현중복을검출하는2tests추가,총18개통과. 양쪽full-package156판정+86포함재현+보조18재실행정상.
- 최신ZIP은49파일이며context/source/cache/venv제외. 해시/CRC검증통과, 압축해제본에서원본무결성→builder→양쪽runner→package(verify+18tests)5단계전부성공. 로그 .cache/unified-attachment-reproduction.json.
- 최신ZIP SHA256: 7967d8ab6c724507b59bf03c7e73dddecee2ac7af0f8e06048e8de52abb7ceb9
- HEAD aa16a077bb4a06bf2bc92c285e4c9c98509fc240 및기존86기준JSON불변,staged0,commit/push/원격작성없음. 새Lighteval-Ko/모델평가는계속미수행.


### 대표 표현 변경 요청

- 사용자는 대표 표현을 단순히 “156건의 실험”으로 쓰도록 요청함. “기존86재현+신규70통합/확장실험”을 소개 문구로 반복하지 않는다.
- 문서·생성 보고서·영문 초안은 같은 표현으로 통일한다. 원본 추적용 기술 메타데이터와 기존 소제목은 유지한다.

- 대표 표현을 “156건의 실험”으로 변경 완료. design/analysis/README/영문 초안 및 보고서 생성 코드에 반영하고 첨부 ZIP·해시를 갱신. 기존 소제목·판정·입력과 기술적 provenance는 유지.


### 문서 표현 검토 완료

- analysis/design/양쪽README/로컬issue-draft와자동생성결과·영문첨부문구를 검토·수정. 주술관계,불필요한영어혼용,중복설명,수치단위·검증범위설명을 자연스럽게 정리함. 대표표현 “156건의 실험” 유지.
- 기존모든소제목문자열·순서(8개문서),입력·원시결과파일해시,판정·집계summary,compare_expanded.py의report외검증함수AST불변 확인. 원본문항prompt/kwargs는수정하지않음.
- package_expanded.py로보고서·ZIP·해시갱신,검증테스트18개통과. 평가기재실행이나새모델평가는하지않음. .cache/editorial-baseline.json 및editorial-audit.json에근거기록. 커밋·푸시·원격작성없음.
- 최신ZIP SHA256: 742f8daaa8f677c1ce9784f0c23395c221ee824559e2c03ae04c4d5f10bfa7b9


### 현재 작업: expanded 폴더 제거·단일 실험 구조로 정리

- 사용자가 expanded 패키지 필요성을 묻고 실험을 하나로 통일 요청. checker-audit/ 자체가156건실험이 되도록 구현 진행. expanded/ 및 *_expanded* 실행파일 분리 제거, canonical build_cases/run_original/run_ko/compare/package_results/test_audit 사용.
- 기존root results.json은86건의입력/양쪽원시행/환경을모두포함함을원본3JSON과대조하여확인. byte그대로 baseline.json으로보존하고 원본추적용으로만사용. 상위cases/results/ko/original_results는156건으로전환.
- 변경전복사: evidence/checker-audit/.cache/pre-flatten/ (현재code+자료+문서). 기준검증snapshot .cache/flatten-baseline.json.
- 필요한수정: baseline공통읽기와hash검증, builder/runner/verifier/test 경로·import통합, package파일목록·baseline보존검사,문서링크·명령정리,양쪽원본재실행·18tests·ZIP재현.
- 이전 '기존root86JSON불변'은이제 baseline.json의동일byte및기준record검증으로대체. 원본데이터/평가기revision·판정·문항순서/kwargs는유지. 문서소제목변경금지. commit/push/원격작성금지.


### 단일 실험 구조 정리 완료

- `expanded/` 폴더와 `*_expanded*` 실행 파일을 제거했다. `evidence/checker-audit/`에서 156건의 실험 입력 생성, 양쪽 원본 실행, 비교, 검증, 로컬 첨부 생성을 모두 수행한다.
- 기존 86건의 입력·양쪽 저장 판정·환경은 기존 `results.json`의 바이트 그대로 `baseline.json`에 보존했다. 현재 `cases.json`, `original_results.json`, `ko_results.json`, `results.json`은 모두 156건 기준이다. 기준 입력 재현 근거는 해당 case 안에 포함하며 지표 분모에 중복 가산하지 않는다.
- 실행 경로: `build_cases.py` → `run_original.py` / `run_ko.py` → `compare.py` → `test_audit.py` → `package_results.py`. 공통 실행은 `run_audit.py`가 담당한다. 문서·재현 명령·링크·첨부 구조를 함께 갱신했다. 기존 소제목은 모두 보존했다.
- 양쪽 원본을 재실행했다. 통합 전후 156건의 모든 원시 결과 행, 입력·보조 입력·원본 문항, 판정 쌍과 네 지표가 동일하다. 정상 156건의 미처리 예외 0건, 보조 입력의 예상 예외 계약 유지, 검증 도구 테스트 18개 통과.
- ZIP 압축 해제본에서 해시 검사 → 입력 생성 → 양쪽 원본 실행 → 검증·18개 테스트·첨부 생성 → 재생성 해시 검사를 통과했다. 추출본의 156건 원시 결과와 집계도 현재 결과와 동일하다. 공개 로컬 파일 링크 112개가 모두 유효하다.
- 첨부 ZIP은 43개 파일이며 SHA256은 `fe9386a06762055a8b7375f1b6d80a30617001d2f7354ea0f8be92eeb0847aa8`. private context, source, cache, 가상환경은 제외했다. 재현 로그는 `.cache/flat-attachment-reproduction.json`, 완료 감사는 `.cache/flatten-completion-audit.json`.
- 원본 revision·HEAD·범위 밖 파일은 그대로이며 staged 변경 0건이다. 커밋·푸시·원격 작성은 하지 않았다. 새 Lighteval-Ko 동등성과 모델 평가는 계속 미수행이다.


### 영어판과 언어별 문서 이동 정리 완료

- 사용자 요청: analysis/design 및 연결 문서의 영어판을 만들고, 각 문서 상단에 언어 전환 링크를 두며 본문은 같은 언어끼리 연결한다. 커밋·푸시·원격 작성 금지는 유지한다.
- 영어판 추가: `analysis.en.md`, `design.en.md`, 팀 `README.en.md`, `evidence/analysis-details.en.md`, 실험 `README.en.md`·`results.en.md`·`source_rows.en.md`, 문항 선정 `README.en.md`·`coverage.en.md`. 원래 영어인 이슈 문서의 경로는 유지하고 `issue-draft.ko.md`, `evidence/checker-audit/issue-1463.ko.md`를 추가했다. 총 11쌍·22문서다. private context는 번역·첨부하지 않는다.
- 원문 제목·소제목을 모두 유지했다. 영어 분석/설계의 모든 번호 절·표 행·외부 출처 URL·JSON/Python 예제를 대조했다. 원본 32문항의 한국어 prompt와 55개 instruction/kwargs 행은 양쪽 문서에 그대로 보존하고 영어판에 읽기용 번역을 추가했다. 이 번역은 실제 채점 입력이 아니다.
- `compare.py`와 `report_i18n.py`, `audit_coverage.py`와 `coverage_i18n.py`가 보고서 양쪽 언어판을 함께 생성한다. `package_results.py`는 양쪽 문서를 첨부하고, 상단 전환 링크·로컬 파일/절 링크·같은 언어 이동을 검증한다. 본문 링크 253개 유효, 예상하지 않은 언어 전환 0개.
- 선정 안내의 과거 미수행 표현은 원본 156건 실험 완료/새 task·모델 통합 미수행으로 명확히 했다. 선정 집계는 원본 소스를 읽기 전용으로 재집계했으며 수치는 동일하다. 새 코드 hash·실제 CRLF selection 바이트 hash·실행 환경 정보만 갱신했다. 한국어 설계 표의 stop 문자열 파이프도 Markdown escape로 표시를 바로잡았다.
- 기존 156건 입력·응답·양쪽 원시 판정·기준 자료·원본 revision·모든 실험 집계는 작업 시작 시점과 동일하다. 전체 평가기/모델은 재실행하지 않았다. 저장 결과 검증과 검증 도구 테스트 18개가 통과했다.
- 최신 ZIP은 56파일·SHA256 `61f8f04bbeeba7c352e5b0c2de425242084a0a89b2ce021a7c7e01c6f18b5e05`. 새 압축 해제본에서 checksum → 문항 선정 문서 재생성 → 실험 문서 재생성/검증/18개 테스트/재포장 → checksum 검사를 통과했고 22문서가 현재 파일과 byte 단위로 동일하다. 로그 `.cache/bilingual-final-reproduction.json`, 완료 감사 `.cache/translation-completion-audit.json`.
- HEAD·범위 밖 파일 불변, staged 변경 0건. 커밋·푸시·원격 작성 없음. 새 Lighteval-Ko 동등성과 모델 평가는 계속 미수행이다.


### 이슈 초안 제외 범위 반영 완료

- 사용자는 `issue-1463.md`·`issue-1463.ko.md`·`issue-draft.ko.md`를 담당 범위가 아니므로 푸시하지 않는다고 명시했다. 해당 3개 로컬 파일은 수정·삭제하지 않고 보존했다. 이슈 초안 전체를 공개 실험 문서의 필수 자료·링크·자동 생성·첨부 ZIP 범위에서 제외했다.
- analysis/design/팀 README/실험 README/생성 결과의 한·영 양쪽에서 초안 준비·제공·첨부 완료 표현과 로컬 초안 링크를 제거했다. 이슈 작성·원격 게시는 별도 범위로 설명하고, 실제 실험 파일과 선택적 로컬 ZIP 생성 방법으로 연결했다. 기존 영어 `issue-draft.md`는 미포함 파일 링크와 첨부 표현만 실험 결과·출처 링크로 바꿨다.
- `compare.py`의 issue-1463 양쪽 언어 자동 생성을 제거하고 `report_i18n.py`의 미사용 이슈 번역을 정리했다. `package_results.py`는 이슈 초안 4파일을 ZIP/언어별 문서 검사 목록에서 제외하고 ZIP 유입도 검사한다. 공개 실험 문서는 9쌍·18문서이며 본문 링크 224개 유효, 끊어진 링크·불필요한 언어 전환 0개다.
- 사용자가 이전 작업을 커밋하여 현재 HEAD가 `54a9fa53ac8f716fb79eec716db90ec1fd5bbd70`임을 확인했다. 이번 작업 시작 파일 해시·HEAD를 `.cache/issue-scope-baseline.json`과 `.cache/active-worktree-baseline.json`에 기록하고 현재 작업 기준으로 범위 밖 파일·HEAD 보존을 검사했다. 이전 source/기준 판정의 고정 검사는 유지했다.
- 검증 도구 테스트 18개 통과. 초안이 없는 ZIP 압축 해제본에서 checksum → 보고서 재생성·검증·18개 테스트·재포장 → checksum 검사가 성공했고 초안 파일이 다시 생성되지 않았다. 입력·원시 판정·실험 집계·문서 제목은 그대로다. 전체 평가기나 모델은 재실행하지 않았다.
- ZIP은 52파일·SHA256 `fb586736297eb5349cd5cd779a5c1916be9d23e08809a133d3f28f215dd2173c`. 재현 로그 `.cache/issue-scope-final-reproduction.json`, 완료 감사 `.cache/issue-scope-completion-audit.json`. 커밋·푸시·원격 작성 없으며 staged 변경 0건이다.


### 영어 보조 기대값 누락·평가기별 건수 설명 보완 완료 (2026-11-04)

- 사용자 승인: 리뷰의 두 P2를 보완한다. 추가 지시로 영어/Ko checker·NFC·예외 처리에서 생기는 차이는 그대로 유지해야 함을 확인했다. 원본 code/data 수정이나 판정 일치는 목표가 아니다. 커밋·푸시·원격 작성 금지는 유지한다.
- `build_cases.py`는 보조 18건 모두에 영어의 `expected_original`을 명시적으로 사전 선언하며, Ko 기대값을 기본 복사하지 않는다. 영어 source revision과 seed 0 근거를 기록했다. 기존 보조 입력은 해당 필드만 추가됐고 Ko 기대값·prompt·kwargs·응답·해시는 그대로다. manifest schema는 3이며 양쪽 oracle 필수임을 표시했다.
- `compare.py`의 `verify_support_record`/`verify_support_cases`가 양쪽 full·isolated의 strict·loose Boolean·문항 AND·trace 또는 예상 예외 유형, 입력/해시/순서를 검사한다. summary의 모호한 정상10·예외8 필드를 `support_outcomes_by_evaluator`로 교체해 양쪽 단계별로 기록한다. Ko는 10/8, 영어는 16/2이며 F도 정상 반환에 포함한다. 보조 18건은 본156 지표 분모에서 계속 제외한다.
- 원본 고정 영어/Ko 보조18건을 full-package로 각각 재실행했다. 양쪽 모든 원시 결과 행(판정·예외·호출 기록 포함)이 작업 전과 정확히 동일하다. 본156건은 저장 결과를 재검증했으며 입력·양쪽 원시 파일·네 지표·양방향 판정 쌍·21종/25경로/13경계군이 모두 그대로다. 원본 checker·utility·NFC·예외 동작은 전혀 수정하지 않았다.
- 검증 도구 테스트는 기존18+추가7=25개 통과. 전체 영어 보조 결과를 예외로 바꾸기, full/isolated 각 단계의 정상→예외·예외→정상/다른유형·Boolean과trace 동시변조·기대값누락/Ko복사·결과누락/재정렬·비Boolean 기대값을 검사한다. 전체 `verify()`에도 영어18건 모두를 메모리에서 예상 밖 예외로 바꾸어 전달했고 검증이 거부됨을 확인했다. 원시 결과 파일은 변조하지 않았다.
- analysis/design/실험README/생성report의 양쪽 언어판에 평가기별 건수·입력 기준·독립기대값·원본차이보존·25개 테스트를 반영했다. 기존 제목은 보존했다. 과거17/42/언어별합성23의 재현 자료 제한과 새 Ko task/모델평가 미수행 상태는 유지한다.
- 최신 ZIP은 52파일·SHA256 `9eccbae292342ec4957b7787c6c80cb1ec7fa40d95ed7db927c34bc6c7f0ae59`. 압축 해제본에서 checksum → builder → 영어 보조18 → Ko 보조18 → 검증/25테스트/재포장 → checksum이 모두 통과했다. 입력·생성문서·결과행·summary가 현재 자료와 같고 이슈 초안은 생성/첨부되지 않는다. 로그 `.cache/support-oracle-reproduction.json`, 변조 거부 증거 `.cache/support-oracle-mutation-check.json`, 완료 감사 `.cache/support-oracle-completion-audit.json`.
- 현재 HEAD 불변, staged 변경0, 범위 밖 파일 불변. 로컬 이슈 초안4파일은 이번에 수정하지 않았다. 커밋·푸시·원격 작성 없음. 새 Lighteval-Ko나 모델 평가 완료로 표현하지 않는다.
