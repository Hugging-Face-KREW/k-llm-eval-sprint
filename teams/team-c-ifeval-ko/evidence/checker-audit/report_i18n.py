"""Presentation-only translations for generated evidence documents."""
import re


REPORT_EN = {
    "# IFEval / IFEval-Ko 확장 고정 응답 비교": "# IFEval / IFEval-Ko Stored-Response Comparison",
    "원본 영어·Ko 평가기에 **동일한 Ko prompt·instruction 순서·실제 적용 kwargs·응답**을 전달했다. 회귀 검증의 기준은 원본 Ko의 기대값과 일치하는지 여부다.": "Both original evaluators received the **same Ko prompt, instruction order, effective kwargs and response**. Regression acceptance means matching original Ko expectations.",
    "기존 `case/full/isolated/diagnostics` 형식을 유지했다. `original_*` 필드는 원래 영어 문항의 출처를 보존하며, 실제 비교 입력은 각 원시 결과의 `evaluated_input`에 기록했다.": "The existing `case/full/isolated/diagnostics` format is retained. `original_*` preserves English source provenance; `evaluated_input` in each raw result records the actual comparison input.",
    "156건의 실험은 실제 데이터 조건 116건·메모리 override 2건·합성 입력 38건으로 구성된다. 사용한 원본 문항은 32개이며 instruction 55개를 포함한다. full 평가에서 검사한 instruction은 247개다.": "The 156-case experiment comprises 116 unchanged dataset conditions, 2 in-memory overrides and 38 synthetic inputs. It uses 32 source prompts containing 55 instructions; full evaluation checks 247 instruction occurrences.",
    "보조 호환성·오류 입력 18건 중 10건은 정상 반환하고, 8건은 원본에서 예상한 예외가 발생한다. 보조 입력은 주 실험의 경로별 검증과 지표에 포함하지 않는다. 모델 생성, 새 Lighteval-Ko 검증과 기존 Lighteval 영어/French 회귀는 미수행이다.": "Of 18 auxiliary compatibility/error inputs, 10 return normally and 8 raise expected reference exceptions. They are excluded from main path coverage and metrics. Model generation, new Lighteval-Ko validation and existing English/French regression remain pending.",
    "## 1. 판정 방향 — (영어, Ko)": "## 1. Judgment direction — (English, Ko)",
    "| 단계 | T,T | T,F | F,T | F,F | 분모 |": "| Phase | T,T | T,F | F,T | F,F | Denominator |",
    "각 case의 주 검사 대상 하나씩을 집계했다. 추가로 지정한 검사 대상과 full 평가의 모든 개별 판정은 아래 비교표와 JSON에 보존했다. 이 표의 `(영어, Ko)` 순서와 경계 표의 `(strict, loose)` 순서를 구별해 읽는다.": "Each case contributes one primary target. Additional explicit targets and every full-evaluation judgment remain in the tables and JSON. Distinguish this table's `(English, Ko)` order from boundary tables' `(strict, loose)` order.",
    "## 2. 네 지표의 분자·분모": "## 2. Numerators and denominators of four metrics",
    "고정 응답 실험의 집계다. 모델의 벤치마크 성능 점수를 나타내지 않는다.": "These are stored-response experiment aggregates, not model benchmark scores.",
    "| 지표 | 영어 | Ko |": "| Metric | English | Ko |",
    "## 3. 전용 입력 경로 coverage": "## 3. Dedicated input-path coverage",
    "실제 데이터 조건을 유지한 사례 중 `targets`로 지정한 instruction만 집계한다. 25개 입력 경로마다 strict·loose 모두 통과하는 응답(TT)과 모두 실패하는 응답(FF)을 확보했다. 이는 정상 kwargs에 따른 입력 경로의 검증 범위다.": "Only explicit `targets` under unchanged dataset conditions are counted. Each of 25 input paths has a response passing strict and loose (TT) and one failing both (FF). These paths follow normal kwargs.",
    "| instruction ID | 입력 경로 | strict T/F | loose T/F | 전용 TT | 전용 FF |": "| Instruction ID | Input path | Strict T/F | Loose T/F | Dedicated TT | Dedicated FF |",
    "## 4. 경계·반복 ID·loose 복구": "## 4. Boundaries, repeated IDs and loose recovery",
    "| key:index | 조건 | N−1의 strict/loose | N | N+1 |": "| key:index | Condition | N−1 strict/loose | N | N+1 |",
    "key 1203의 두 빈도 조건은 index 0이 전쟁≥8, index 1이 peace≥10이다. strict와 loose 각각에서 `[T,T]`, `[T,F]`, `[F,T]`, `[F,F]` 네 조합을 확인했다. prompt의 평화와 kwargs의 peace는 원본대로 유지했다.": "Key 1203 checks 전쟁≥8 at index 0 and peace≥10 at index 1. Both strict and loose cover `[T,T]`, `[T,F]`, `[F,T]`, `[F,F]`. The original mismatch between prompt 평화 and kwargs peace is preserved.",
    "1268의 6문장은 한 줄로 쓰면 F/F, 여러 줄로 쓰면 F/T다. 136의 10개 bullet은 앞뒤에 빈 줄을 2개씩 두면 F/F, 빈 줄이 없으면 F/T다. 3073의 5문단도 F/T다. 여기서 F/T는 strict 실패·loose 통과를 뜻하므로 두 기대값을 각각 기록한다.": "Six sentences for 1268 give F/F on one line and F/T across lines. Ten bullets for 136 give F/F with two blank lines at each end and F/T without padding. Five paragraphs for 3073 also give F/T. Here F/T means strict failure and loose success; record both expectations separately.",
    "## 5. 전체 비교표": "## 5. Complete comparison",
    "각 셀은 **대상 instruction의 판정 / 전체 instruction의 판정 목록 / 문항 전체 통과 여부** 순서다. 모든 행에서 양쪽 평가기에 동일 Ko 입력을 전달했다. 원본 조건·응답·기대값·관측값·해시는 cases.json과 results.json에 각각 기록했다.": "Cells show **target judgment / all instruction flags / prompt all-pass**. Both evaluators receive identical Ko inputs in every row. Source conditions, responses, expectations, observations and hashes are recorded in cases.json and results.json.",
    "| key:index | Checker | Test | Original strict | Original loose | Ko strict | Ko loose | strict (EN,Ko) | loose (EN,Ko) | Scope | 실험 구성 |": "| key:index | Checker | Test | Original strict | Original loose | Ko strict | Ko loose | strict (EN,Ko) | loose (EN,Ko) | Scope | Composition |",
    "## 6. 별도 호환성·오류 입력": "## 6. Auxiliary compatibility and error inputs",
    "| case | checker | 영어 strict/loose | Ko strict/loose | 분류 |": "| Case | Checker | English strict/loose | Ko strict/loose | Classification |",
    "## 7. 재현·이식 인계": "## 7. Reproduction and port handoff",
    "156건의 실험 결과에 입력 재현의 검증 근거를 포함했다. 기준 결과와의 일치 여부는 원시 결과의 `baseline_reproduction`과 `summary`에서 확인할 수 있다. 비교표는 동일 Ko 입력을 전달한 156건을 기준으로 집계한다.": "The 156-case results include input-reproduction evidence in raw `baseline_reproduction` and `summary`. Comparison tables count the 156 cases with identical Ko inputs.",
    "고정한 코드·데이터 21개 파일, 실제로 불러온 네 모듈, NLTK 자원과 입력·응답의 해시를 확인했다. 실행 단계·객체 생성·초기화·후보 처리 기록을 검사하고, instruction별 후보 OR·문항별 AND·단계별 새 객체·`if v` 필터·문항별 instruction 수가 다른 집계도 확인했다.": "Verified hashes cover 21 pinned code/data files, four imported modules, NLTK resources and inputs/responses. Traces check phases, construction, initialization and candidates, including instruction-wise OR, prompt AND, fresh phase objects, `if v` and uneven instruction aggregation.",
    "A안은 원본 Ko의 채점 규칙을 가깝게 보존하고 기존 영어/French 코드의 변경 범위를 줄이기 위한 선택이다. B안도 같은 정책과 객체 생성 방식을 보존하면 구현할 수 있다.": "Option A keeps Ko scoring close to the reference and limits changes to existing English/French code. Option B is also possible if it preserves the same policies and checker lifecycle.",
    "재현 명령은 README에 정리했다. [영문 이슈 첨부 초안](issue-1463.md)은 로컬에 준비했으며 아직 게시하지 않았다. [manifest](manifest.json), [검증 범위](coverage.json), [원본 문항 목록](source_rows.md)을 함께 확인할 수 있다.": "See the [README](README.en.md) for commands. The [English issue attachment draft](issue-1463.md) is prepared locally and has not been posted. Also see the [manifest](manifest.json), [coverage](coverage.json) and [source prompt catalog](source_rows.en.md).",
}

REPORT_CELLS_EN = {
    "대상 strict": "Target strict", "대상 loose": "Target loose",
    "기존·양쪽 재현 일치": "Baseline; both reproductions match", "신규": "Added",
    "예상한 예외 확인": "Expected exception confirmed", "합성 호환성": "Synthetic compatibility",
}


def report_en(lines):
    translated = []
    for line in lines:
        if line in REPORT_EN:
            translated.append(REPORT_EN[line])
            continue
        for original, english in REPORT_CELLS_EN.items():
            line = line.replace(original, english)
        # Stable case IDs can contain Korean; preserve inline source literals.
        if re.search(r"[가-힣]", re.sub(r"`[^`]*`", "", line)):
            raise ValueError("Missing English report translation: " + line)
        translated.append(line)
    return translated


def with_language_link(lines, counterpart, language):
    """Insert one reciprocal language link after the document title."""
    nav = (f"**한국어** | [English]({counterpart})" if language == "ko"
           else f"[한국어]({counterpart}) | **English**")
    return [lines[0], "", nav, ""] + lines[2:]


SOURCE_PROMPT_EN = {
    122: "Write a blog post about the history of the Internet and its impact on our lives. Address teenagers and enclose the entire response in double quotation marks.",
    127: "Write a complete article using this text as a starting point: ‘You may need to meet with a helper to make a parenting plan. First, estimate how much time you can spend parenting each day and whether it is enough....’ Do not use the keywords `수면` (sleep), `요리` (cooking) or `먹이기` (feeding). Mention the keyword `일정` (schedule) at least 5 times.",
    136: "A nucleus is a collection of protons and neutrons. Explain this in detail. Write exactly 9 very short bullet points and use fewer than 100 words. Follow this example format: `* 핵은 양성자와 중성자의 집합체입니다.` (‘A nucleus is a collection of protons and neutrons’), `* 양성자는 ....` (‘Protons are ....’).",
    240: "What is a lattice? Rewrite the answer so children can understand it, entirely in Russian. No other language is allowed.",
    349: "I want to start a vegetable and flower garden in my small backyard. Can you advise me on watering the plants? Include at least 3 italicized text sections, such as `*이탤릭 텍스트 1*`, `*이탤릭 텍스트 2*`, etc. Keep the entire answer under 40 words.",
    1082: "Write exactly 2 paragraphs about a man who wakes up one day and realizes he is inside a video game. Separate the paragraphs with the Markdown delimiter `***`.",
    1107: "Write two jokes about rockets. Do not include commas. Separate the jokes with six asterisks: `******`.",
    1127: "Write a poem about missing class, with 4 sections labeled `섹션 X` (‘Section X’). End with this exact phrase: `제가 놓친 수업에 대한 돈을 돌려받을 수 있을까요?` (‘Can I get my money back for the class I missed?’).",
    1203: "What happened when China's Tang dynasty came to power? Use the word `전쟁` (war) at least 8 times and `평화` (peace) at least 10 times.",
    1233: "How many meters above ground was the world's tallest skyscraper in 2000? Include only the main points. End with the exact phrase `도와드릴 수 있는 다른 것이 있나요?` (‘Is there anything else I can help you with?’). Mention `마천루` (skyscraper) at least 8 times.",
    1237: "Write an entertaining post for teenagers about Buena Onda, a restaurant serving Argentinian food. Highlight at least three sections using Markdown such as `*강조된 섹션*`. Mention `아르헨티나` (Argentina).",
    1242: "Can you suggest a nickname for `스타포드`? Use JSON, do not use the word `별명` (nickname), and add nothing outside the JSON block.",
    1262: "Explain in detail: ‘Increased axle loads increased road damage.’ Include a title enclosed in double angle brackets, such as `<<제목>>`, and write fewer than 5 sentences.",
    1268: "Give an example diary entry about stress management and explain how you came up with it. The entire response must contain at most 6 sentences.",
    1480: "Write a blog post about the most interesting things you have seen on public transport. First repeat the preceding sentence without changing a single word, then answer. Put no word or character before the repeated sentence.",
    1800: "Explain to a group of elementary-school students why we have seasons. Add a postscript beginning with `P.S.` at the end.",
    1928: "Expand this sentence into a formal story: ‘My dog is brown and my cat is black.’ Include a title enclosed in double angle brackets, as in `<<제목>>`, and no commas. The word `피부` (skin) must appear fewer than 3 times.",
    1954: "What are poppy seeds used for? Write exactly 7 paragraphs, with the last paragraph beginning with `요약` (summary). Separate paragraphs with two newline characters.",
    2035: "Write a joke in at least 5 sentences. Use Markdown to italicize at least 2 sections, as in `*이탤릭체*`, and enclose the answer in double quotation marks.",
    2142: "Write a proposal for a new college course on the history of the world as told by a dog. The proposal must contain the word `포식자` (predator) at least twice.",
    3073: "How are you feeling today? Write exactly 4 paragraphs separated by two newline characters each. Begin the first paragraph with `회사` (company).",
    3311: "What is SRE? Use only Korean, provide a title in double angle brackets such as `<<SRE>>`, and use the keywords `지표` (indicator), `목표` (goal) and `관리` (management).",
    3345: "Write a strange poem I can send to my friend Steve in Australia about why the United States has no kangaroo invasion. Use `강도` (robber) at least twice. Include exactly 2 Markdown bullets using this exact format: `* 포인트 1`, `* 포인트 2`. Do not include `죽이다` (kill), `도살` (slaughter), `점령` (occupation) or `침략` (invasion).",
    3442: "What is the answer to the riddle about something you can catch but cannot throw, and something you can throw but cannot catch? Use fewer than 20 words in the entire answer and enclose the title in double angle brackets, as in `<<제목>>`.",
    3445: "How can you tell someone your major is computer science without using the words `컴퓨터` (computer) or `과학` (science)? Neither word may appear anywhere in the response.",
    3518: "Give the advantages and disadvantages of working abroad in JSON. Include only the JSON block. Also include the keywords `보상` (compensation) and `이민자` (immigrant).",
    3538: "Write a social-media post of at least 600 characters for a startup offering a platform for realistic physics simulations. Include `폭탄` (bomb) at least once.",
    3563: "What is the name of the actor who played Gandalf in The Lord of the Rings? First repeat the preceding question without changing any words, then give the answer.",
    3710: "Write a rap telling experts how to help babies sleep through the night. Include a title in double angle brackets such as `<<제목>>`, highlight at least 2 sections using Markdown such as `*강조된 섹션*`, and explicitly add a postscript beginning with `P.P.S` at the end.",
    3739: "What is the name of the green-eyed monster that makes people jealous? Use at most 3 sentences, specifically only 1 or 2 sentences.",
    3743: "Write a joke about `조에` and bubbles, with at least 3 placeholders enclosed in square brackets, such as `[date]`.",
    3750: "Was the moon landing propaganda created by the government? Include one of these exact phrases: `제 답변은 예입니다.` (‘My answer is yes’), `제 답변은 아니요입니다.` (‘My answer is no’), or `제 답변은 아마도입니다.` (‘My answer is maybe’).",
}


def catalog_en(lines):
    # Prompts and kwargs, including every fenced block, stay verbatim.
    replacements = {
        "# 고정 Ko 원본 문항 목록": "# Pinned Ko Source Prompt Catalog",
        "`source_rows.json`에 원본 prompt·instruction 순서·24개 kwargs 필드를 보존했다. 아래 표에서는 null 필드만 생략했다.": "`source_rows.json` preserves original prompts, instruction order and all 24 kwargs fields. Tables omit only null fields. English reading translations below are documentation only; actual scoring always uses the verbatim Korean prompts and original parameter strings. Translation/checker mismatches are preserved, including 5 versus 6 in key 127, at most 6 versus <6 in 1268, and characters versus words in 3538.",
        "| index | instruction_id | kwargs (null 생략) |": "| Index | instruction_id | kwargs (null omitted) |",
    }
    out = []
    in_fence = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            if line.startswith("## key "):
                key = int(line.removeprefix("## key "))
                out += [line, "", "**English reading translation — not a scoring input:**", "", "> " + SOURCE_PROMPT_EN[key], "", "**Original Korean prompt (verbatim):**"]
                continue
            if line.startswith("고정 데이터: "):
                line = line.replace("고정 데이터: ", "Pinned data: ").replace(". 각 ID 링크는 같은 revision의 checker 코드를 가리킨다.", ". Each ID links to checker code at the same revision.")
            else:
                line = replacements.get(line, line)
        out.append(line)
    return out


ISSUE_KO = {
    "# Local experiment attachment for huggingface/lighteval#1463": "# huggingface/lighteval#1463 실험 첨부 초안",
    "This draft summarizes a reference-evaluator experiment for https://github.com/huggingface/lighteval/issues/1463. It has not been posted. The new Lighteval-Ko task and model evaluation remain pending.": "이 문서는 https://github.com/huggingface/lighteval/issues/1463 에 첨부할 원본 평가기 실험의 초안이다. 아직 게시하지 않았다. 새 Lighteval-Ko task 검증과 모델 평가는 미수행이다.",
    "## Experiment": "## 실험",
    "We conducted a **156-case experiment** and checked **18 auxiliary inputs** for compatibility and error handling. Of the 156 cases, 116 use unchanged dataset conditions, 2 use explicit in-memory overrides, and 38 are synthetic. Full evaluation checks 247 instruction occurrences across these responses. These figures describe test results, not model benchmark accuracy.": "**156건의 실험**과 호환성·오류 검사용 **보조 입력 18건**을 검사했다. 실험은 실제 데이터 조건 116건·명시적 메모리 override 2건·합성 입력 38건으로 구성된다. full 평가에서 instruction 247개를 검사했다. 이 수치는 고정 응답의 검사 결과이며 모델 벤치마크 정확도가 아니다.",
    "Both evaluators, at the pinned revisions, received the **same Ko prompt, ordered instruction IDs, effective kwargs and response**. Input and response hashes confirm this. The `original_*` fields in cases.json preserve the English source metadata; `evaluated_input` in each raw result records the Ko input used for the comparison.": "고정 revision의 양쪽 평가기에 **같은 Ko prompt·instruction 순서·실제 적용 kwargs·응답**을 전달했다. 입력·응답 해시로 이를 확인했다. cases.json의 `original_*`는 영어 원본의 출처 정보이고, 각 원시 결과의 `evaluated_input`은 실제 비교에 사용한 Ko 입력이다.",
    "Each of the 21 instruction IDs and 25 input partitions used by the dataset has an explicitly targeted response that passes both strict and loose checks and one that fails both. Thirteen count conditions have N−1/N/N+1 checks. The two frequency instructions in key 1203 are identified by index and tested with [T,T], [T,F], [F,T] and [F,F]. The 25 partitions describe normal kwargs paths, not all source-code branches.": "데이터에서 사용하는 21종 ID·25개 입력 경로 각각에 strict·loose 모두 통과하는 응답과 모두 실패하는 전용 응답을 확보했다. 13개 개수 조건에서 N−1/N/N+1을 검사했다. 1203의 두 빈도 조건은 index로 식별하고 [T,T], [T,F], [F,T], [F,F]를 확인했다. 25개는 정상 kwargs에 따른 입력 경로이며 전체 코드 분기 수가 아니다.",
    "## Same-input decision matrix": "## 동일 입력의 판정 비교",
    "Pairs below mean **(English, Ko)** for the primary target of each case.": "아래 쌍은 각 case의 주 검사 대상에 대한 **(영어, Ko)** 판정이다.",
    "| Phase | T,T | T,F | F,T | F,F | Cases |": "| 단계 | T,T | T,F | F,T | F,F | case 수 |",
    "Representative results using identical responses:": "동일 응답을 사용한 대표 결과는 다음과 같다.",
    "| Key / case | English strict/loose | Ko strict/loose | Observation |": "| key / case | 영어 strict/loose | Ko strict/loose | 관찰 |",
    "## Interpretation and proposed implementation": "## 해석과 구현 제안",
    "These results support a separate `ifeval_ko` package and scorer for the initial port (option A). This keeps the Ko word and sentence utilities, fixed phrases and NFC handling close to the reference. It also preserves the order of running all strict checks before all loose checks, with fresh checker instances in each phase. The approach limits changes to the existing English and French paths, at the cost of duplicating a small scoring loop. Option B can also work if it preserves the same policies and checker lifecycle.": "이 결과는 초기 이식에서 별도 `ifeval_ko` 패키지와 scorer를 사용하는 A안의 근거다. Ko 단어·문장 utility, 고정 문구, NFC 처리를 원본에 가깝게 유지하고, strict 전체→loose 전체 실행과 단계마다 새 checker를 만드는 동작을 보존한다. 작은 채점 루프를 중복 관리하는 대신 기존 영어/French 경로의 변경 범위를 줄인다. B안도 같은 정책과 checker 생명주기를 보존하면 구현할 수 있다.",
    "The port must **match the Ko reference**. If English passes a response and Ko fails it, the port must also fail it. We preserve the known prompt/kwargs mismatches in 1203, 2142, 1268 and 3538, as well as the `first_word` normalization asymmetry.": "이식의 합격 기준은 **Ko reference와의 판정 일치**다. 영어가 통과하고 Ko가 실패하는 응답은 새 task에서도 실패해야 한다. 1203·2142·1268·3538의 prompt/kwargs 불일치와 `first_word` 정규화의 비대칭을 보존한다.",
    "## Verification and limitations": "## 검증 범위와 한계",
    "- All 156 cases match the Ko expectations declared before execution, with no unhandled scoring exceptions or unresolved mismatches. Full and isolated evaluations agree for every specified target.": "- 156건 모두 실행 전에 선언한 Ko 기대값과 일치한다. 미처리 채점 예외·미해결 불일치는 없으며 지정 대상의 full·isolated 판정이 일치한다.",
    "- Input reproduction is checked against the stored reference results and recorded with the raw results. The comparison table and metrics use identical Ko inputs throughout.": "- 입력 재현을 저장된 기준 결과와 대조하고 원시 결과에 함께 기록했다. 비교표와 지표는 모두 동일 Ko 입력을 기준으로 한다.",
    "- Auxiliary inputs cover four registered instruction types absent from the dataset. Ko `capital_word_frequency` raises AttributeError because `instructions_util` has no `nltk` attribute; the unregistered `key_sentences` ID raises KeyError. Eight auxiliary inputs raise expected exceptions and are excluded from normal scoring.": "- 보조 입력은 registry에 있지만 데이터에서 사용하지 않는 4종을 포함한다. Ko `capital_word_frequency`는 `instructions_util.nltk`가 없어 AttributeError를 발생시키고, 미등록 `key_sentences`는 KeyError를 발생시킨다. 예상한 예외가 발생하는 보조 입력 8건은 정상 채점에서 제외한다.",
    "- Traces from the original functions confirm candidate order and duplicates, exclusion of empty candidates, instruction-level OR and prompt-level AND, the original `if v` filter, and checker construction. The control with unequal instruction counts yields prompt accuracy 0.5 and instruction accuracy 0.75.": "- 원본 함수의 호출 기록으로 후보 순서·중복·빈 후보 배제, instruction별 OR·문항별 AND, 원본 `if v` 필터와 checker 생성을 확인했다. 지시 수가 다른 집계 대조군은 문항 점수 0.5·instruction 점수 0.75다.",
    "- Parity testing for the new Lighteval-Ko task, regression checks for the existing Lighteval English/French paths, 23-prompt model integration and full-split evaluation on 342 prompts remain pending.": "- 새 Lighteval-Ko 동등성, 기존 Lighteval 영어/French 회귀, 23문항 모델 통합, 전체 342문항 모델 평가는 미수행이다.",
    "## Pinned sources": "## 고정 출처",
    "The English reference in this experiment is the pinned lm-evaluation-harness evaluator. Both evaluators ran through full-package imports after source-file hashes were verified. The Lighteval implementation was used as a design reference.": "영어 비교 기준은 고정 lm-evaluation-harness 평가기다. 원본 파일 해시를 확인한 후 양쪽 평가기를 full-package 방식으로 실행했다. Lighteval 구현은 설계 참고 자료로 사용했다.",
    "## Attachment contents and reproduction": "## 첨부 범위와 재현",
    "The ZIP contains fixtures, predeclared Ko expectations, raw results and traces, comparison tables, provenance, checksums and reproduction scripts. Start with [README.en.md](README.en.md) and [results.en.md](results.en.md) in `team-c-ifeval-ko/evidence/checker-audit/`. Downloaded evaluator sources, dependencies and model weights are excluded; the README explains how to restore the required versions. Private context, caches and credentials are also excluded.": "ZIP에는 입력·사전 Ko 기대값·원시 결과·호출 기록·비교표·출처·해시·재현 스크립트를 포함한다. `team-c-ifeval-ko/evidence/checker-audit/`의 [README.md](README.md)와 [results.md](results.md)부터 확인한다. 내려받은 원본 평가기·의존성·모델 가중치는 제외했으며 README에 복원 방법을 정리했다. 개인 context·캐시·인증 정보도 제외했다.",
    "The ZIP and this note are ready for a later issue attachment. Relative links refer to files inside the archive.": "이 문서와 ZIP은 추후 이슈 첨부용으로 로컬에 준비했다. 상대 링크는 압축 파일 안의 문서를 가리킨다.",
}

ISSUE_CELLS_KO = {
    "word counts 39 vs 40 at <40; blockquote marker contributes a Ko whitespace token": "<40에서 39단어/40단어; 인용 표지가 Ko 공백 토큰에 포함됨",
    "word counts 20 vs 18 at <20; compact comma-separated text": "<20에서 20단어/18단어; 공백 없는 쉼표 구분 텍스트",
    "strict difference recovers in loose; instruction-wise candidate OR": "strict 차이가 loose에서 복구됨; instruction별 후보 OR",
    "Ko fixed response phrase is absent from the English options": "Ko 고정 문구가 영어 허용 선택지에 없음",
}


def issue_ko(lines):
    out = []
    for line in lines:
        if line in ISSUE_KO:
            out.append(ISSUE_KO[line])
            continue
        if line and not line.startswith(("|", "- harness:", "- lighteval:", "- original_dataset:", "- ko:")):
            raise ValueError("Missing Korean issue translation: " + line)
        for original, korean in ISSUE_CELLS_KO.items():
            line = line.replace(original, korean)
        out.append(line)
    return out
