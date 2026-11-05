"""Construct controlled cases from pinned source rows; preserve original values."""
import copy
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent
original = {r["key"]: r for r in map(json.loads, (ROOT / "sources/original_dataset/ifeval_input_data.jsonl").read_text().splitlines())}
ko = {r["key"]: r for r in json.loads((ROOT / "sources/ko/data/rows.json").read_text())}
cases = []
NFD = lambda value: unicodedata.normalize("NFD", value)


def add(case_id, key, iid, response_original, response_ko=None, reason="", group="", classification="NEEDS_DISCUSSION",
        patch=None, fixture=None):
    if fixture is None:
        rows = {"original": original[key], "ko": ko[key]}
        scope = "dataset" if patch is None else "controlled_override"
    else:
        rows = {s: {"prompt": fixture["prompt"], "instruction_id_list": [iid], "kwargs": [fixture["kwargs"]]}
                for s in ["original", "ko"]}
        scope = "synthetic"
    case = {"case_id": case_id, "key": key, "scope": scope, "checker": {
        "length_constraints:number_words": "NumberOfWords", "length_constraints:number_sentences": "NumberOfSentences",
        "keywords:frequency": "KeywordFrequencyChecker", "keywords:existence": "KeywordChecker",
        "keywords:forbidden_words": "ForbiddenWords", "startend:end_checker": "EndChecker",
        "combination:repeat_prompt": "RepeatPromptThenAnswer",
        "length_constraints:nth_paragraph_first_word": "ParagraphFirstWordCheck"}[iid],
        "instruction_id": iid, "group": group, "classification": classification,
        "reason_for_test": reason, "test_response_original": response_original,
        "test_response_ko": response_original if response_ko is None else response_ko}
    for side, row in rows.items():
        index = row["instruction_id_list"].index(iid)
        case[side + "_prompt"] = row["prompt"]
        case[side + "_instruction_id_list"] = row["instruction_id_list"]
        case[side + "_all_kwargs"] = row["kwargs"]
        case[side + "_kwargs"] = row["kwargs"][index]
        if patch and side in patch:
            effective = copy.deepcopy(row["kwargs"])
            effective[index].update(patch[side])
            case[side + "_eval_all_kwargs"] = effective
    if patch:
        case["runtime_override"] = patch
    cases.append(case)


WORDS = "length_constraints:number_words"
SENTENCES = "length_constraints:number_sentences"
FREQ = "keywords:frequency"
FORBIDDEN = "keywords:forbidden_words"
EXIST = "keywords:existence"

add("robber_minimal", 3345, FREQ, "robber robber appears.", "강도 강도는 등장합니다.",
    "한국어 prompt는 강도 2회를 요구하지만 데이터 kwargs는 robber. 다른 bullet 제약은 의도적으로 충족하지 않는다.", "alignment", "DATA")
add("robber_full", 3345, FREQ, "* robber\n* robber", "* 강도\n* 강도",
    "동일한 최소 반례를 두 bullet로 감싸 prompt-level 차이도 격리한다.", "alignment", "DATA")
add("robber_keyword_override", 3345, FREQ, "* robber\n* robber", "* 강도\n* 강도",
    "Ko keyword만 메모리에서 강도로 교체; 데이터 및 checker 원본 파일은 변경하지 않는다.", "alignment", "DATA",
    patch={"ko": {"keyword": "강도"}})

# Same-script probes isolate tokenization from translation and semantic content.
for name, text in [("comma_compact", "사과,배,포도"), ("comma_spaced", "사과, 배, 포도"),
                   ("heading_minimal", "## 결론\n한국어 평가가 필요합니다."),
                   ("quote_minimal", "> 한국어 평가가 필요합니다."),
                   ("star_minimal", "* 사과\n* 배\n* 포도"),
                   ("dash_minimal", "- 사과\n- 배\n- 포도")]:
    add(name, 3442, WORDS, text, reason="동일한 한국어 입력을 양쪽 evaluator에 전달. 실제 <20 조건에서는 count 차이가 판정 차이를 뜻하지 않음.", group="word_minimal",
        classification="INTENTIONAL" if name.startswith("comma") else "NEEDS_DISCUSSION")
    expected_counts = {"comma_compact": (3, 1), "comma_spaced": (3, 3),
                       "heading_minimal": (4, 5), "quote_minimal": (3, 4),
                       "star_minimal": (3, 6), "dash_minimal": (3, 6)}
    expected = expected_counts[name]
    cases[-1]["expected_observation"] = {
        "original_word_count": expected[0], "ko_word_count": expected[1],
        "status": "사전 예상; 실제 관측은 results.json의 diagnostics 및 evaluator 결과 참조"}
    if name.startswith("comma"):
        add(name + "_threshold2", None, WORDS, text, reason="최소 count 반례용 합성 <2 조건; 실제 key 3442의 kwargs가 아니다.",
            group="word_synthetic", classification="INTENTIONAL", fixture={"prompt": "두 단어 미만으로 답하십시오.", "kwargs": {"num_words": 2, "relation": "less than"}})

# <20 with a real title; punctuation changes the effective count around threshold.
for name, fruits in [("compact", "사과,배,포도"), ("spaced", "사과, 배, 포도")]:
    text = "<<제목>> " + " ".join(["항목"] * 16) + " " + fruits
    add("comma_boundary_" + name, 3442, WORDS, text, reason="실제 <20·제목 조건 유지. 영어 tokenizer count=20, Ko compact=18/spaced=20 여부를 실제 실행으로 확인.", group="word_boundary", classification="INTENTIONAL")

for marker, name in [("##", "heading"), (">", "quote")]:
    if name == "heading":
        text = "## 결론\n" + " ".join(["평가"] * 98)
    else:
        text = "> " + " ".join(["평가"] * 99)
    add("markdown_" + name + "_136", 136, WORDS, text,
        reason="실제 <100 조건 경계. heading은 첫 줄 제거 가능, 단일 행 quote는 제거하면 빈 문자열. bullet 제약 실패와 별개로 word 결과를 확인.", group="markdown")

for marker, name in [("*", "star"), ("-", "dash")]:
    balanced = "\n".join(marker + " " + " ".join(["평가"] * 11) for _ in range(9))
    add("markdown_" + name + "_balanced_136", 136, WORDS, balanced,
        reason="9 bullet·99 lexical words. strict는 marker 영향, loose는 star 제거 또는 줄 제거가 영향을 줄 수 있음.", group="markdown")
    lengths = [1, 14, 14, 14, 14, 14, 14, 13, 1]
    uneven = "\n".join(marker + " " + " ".join(["평가"] * n) for n in lengths)
    add("markdown_" + name + "_persistent_136", 136, WORDS, uneven,
        reason="9 bullet·99 lexical words. 양 끝 줄은 각각 1 word라 삭제 후에도 Ko dash count가 <100으로 내려가지 않도록 통제.", group="markdown")

add("markdown_heading_blank_edges", 3442, WORDS,
    "\n## <<제목>>\n" + " ".join(["평가"] * 18) + "\n",
    reason="앞뒤 빈 줄을 가진 실제 <20·제목 출력: 첫/마지막 줄 삭제가 heading token 차이를 없애지 않는 대조군.", group="markdown")

for name, highlights in [("attached", "*사과* *배* *포도*"), ("separated", "* 사과 * * 배 * * 포도 *")]:
    text = highlights + " " + " ".join(["평가"] * 36)
    add("markdown_highlights_" + name + "_349", 349, WORDS, text,
        reason="실제 <40·강조 3개 조건. 붙은 *와 공백으로 분리된 *의 count 차이 및 loose star 제거를 비교.", group="markdown")
    if name == "separated":
        cases[-1]["reason_for_test"] += " 공백으로 둘러싼 * 사과 *는 유효한 CommonMark italic이 아니므로 regex와 token 격리 control로만 해석한다."
add("markdown_quote_valid_highlights_349", 349, WORDS,
    "> *사과* *배* *포도* " + " ".join(["평가"] * 36),
    reason="유효한 blockquote와 붙은 italic 3개. 실제 <40·강조 제약 모두 검사한다. 한 줄의 >가 39/40 count 차이를 만들고 loose star 제거 후에도 남는지 확인.", group="markdown")

sentence_inputs = {
    "period_newlines": "첫 번째 문장입니다.\n두 번째 문장입니다.",
    "only_newlines": "첫 번째 문장입니다\n두 번째 문장입니다",
    "heading": "## 제목\n첫 번째 문장입니다.",
    "divider": "첫 번째 문장입니다.\n\n---",
    "divider_boundary": "첫 번째 문장입니다.\n두 번째 문장입니다.\n\n---",
    "korean_list_lines": "가. 첫 번째 문장입니다.\n나. 두 번째 문장입니다.",
    "korean_list_single_line": "가. 첫 번째 문장입니다. 나. 두 번째 문장입니다.",
    "decimal": "가격은 3.14원입니다. 다음 가격은 2.71원입니다.",
    "english_abbreviation": "Dr. Kim입니다. 다음 문장입니다.",
    "eg_abbreviation": "예시는 e.g. 사과입니다. 다음 문장입니다.",
    "korean_abbreviation": "가.나.다. 예시입니다. 다음 문장입니다.",
}
for name, text in sentence_inputs.items():
    add("sentences_" + name, 3739, SENTENCES, text, reason="실제 <3 조건·동일 한국어 문자열. 각 tokenizer의 실제 sentence list와 strict/loose를 실행한다.", group="sentences",
        classification="INTENTIONAL" if name in {"korean_list_lines", "korean_list_single_line", "eg_abbreviation", "korean_abbreviation"} else "NEEDS_DISCUSSION")

# Real translated forbidden-word intent; ASCII suffix and Korean particle controls.
for name, en, kr in [("exact", "nickname", "별명"), ("particle", "nickname", "별명을"),
                     ("compound", "nicknames", "별명표")]:
    add("forbidden_dataset_" + name, 1242, FORBIDDEN, json.dumps({"value": en}), json.dumps({"value": kr}, ensure_ascii=False),
        "실제 JSON+금지어 조건. exact/한국어 조사/합성어에 대한 경계 match를 비교.", "forbidden", "NEEDS_DISCUSSION")
for word in ["사과", "사과를", "사과가", "사과나무"]:
    for iid, kw in [(FORBIDDEN, {"forbidden_words": ["사과"]}), (EXIST, {"keywords": ["사과"]}),
                    (FREQ, {"keyword": "사과", "frequency": 1, "relation": "at least"})]:
        add("boundary_" + iid.split(":")[1] + "_" + word, None, iid, word,
            reason="합성 한국어 사과 fixture로 동일 input/kwargs 사용. ForbiddenWords와 keyword checker의 경계 의미를 격리.",
            group="forbidden_synthetic", fixture={"prompt": "사과 keyword 경계 검사", "kwargs": kw})

# Dataset-level composed/decomposed Korean counterparts (English reference remains English).
dataset_nfc = [(1237, EXIST, "keywords"), (127, FREQ, "keyword"), (1242, FORBIDDEN, "forbidden_words"),
               (1127, "startend:end_checker", "end_phrase"), (1480, "combination:repeat_prompt", "prompt_to_repeat")]
for key, iid, arg in dataset_nfc:
    index = original[key]["instruction_id_list"].index(iid)
    okw = original[key]["kwargs"][index]
    kkw = ko[key]["kwargs"][index]
    def target_response(kw):
        value = kw[arg]
        if isinstance(value, list):
            return " ".join(value)
        return " ".join([value] * kw["frequency"]) if iid == FREQ else value
    en, kr = target_response(okw), target_response(kkw)
    for form in ["NFC", "NFD"]:
        add("nfc_dataset_" + iid.split(":")[1] + "_" + form.lower(), key, iid, en,
            unicodedata.normalize(form, kr), "실제 비교 대상 유지. 한국어 response의 canonical equivalent 형태만 변경한다. 나머지 instruction은 충족하지 않을 수 있음.",
            "nfc_dataset", "INTENTIONAL")

# Same Korean target in English checker is explicitly synthetic; no invented dataset value.
for iid, arg in [(EXIST, "keywords"), (FREQ, "keyword"), (FORBIDDEN, "forbidden_words"),
                 ("startend:end_checker", "end_phrase"), ("combination:repeat_prompt", "prompt_to_repeat"),
                 ("length_constraints:nth_paragraph_first_word", "first_word")]:
    for target_form, response_form in [("NFC", "NFC"), ("NFC", "NFD"), ("NFD", "NFC"), ("NFD", "NFD")]:
        target = unicodedata.normalize(target_form, "가")
        response = unicodedata.normalize(response_form, "가")
        kw = {arg: [target] if arg in {"keywords", "forbidden_words"} else target}
        if iid == FREQ:
            kw.update(frequency=1, relation="at least")
        if arg == "first_word":
            kw.update(num_paragraphs=1, nth_paragraph=1)
        add("nfc_matrix_" + iid.split(":")[1] + "_" + target_form.lower() + "_" + response_form.lower(), None, iid, response,
            reason="합성 가/U+1100 U+1161 matrix: 비교 대상과 response의 정규화 경로를 분리. raw checker와 evaluator를 함께 검사.",
            group="nfc_synthetic", classification="INTENTIONAL", fixture={"prompt": "가 canonical equivalence 검사", "kwargs": kw})
        if arg == "first_word":
            cases[-1]["classification"] = "CHECKER" if target_form == "NFD" else "INTENTIONAL"

first_iid = "length_constraints:nth_paragraph_first_word"
for form in ["NFC", "NFD"]:
    en_kw = original[3073]["kwargs"][original[3073]["instruction_id_list"].index(first_iid)]
    ko_kw = ko[3073]["kwargs"][ko[3073]["instruction_id_list"].index(first_iid)]
    en = "\n\n".join([en_kw["first_word"] + " text", "second", "third", "fourth"])
    kr = "\n\n".join([ko_kw["first_word"] + " 내용", "둘째", "셋째", "넷째"])
    add("nfc_dataset_first_word_" + form.lower(), 3073, first_iid, en, unicodedata.normalize(form, kr),
        "실제 4문단·첫 단어 조건. response-only NFD는 evaluator 진입 NFC로 복원되는지 확인.", "nfc_dataset", "INTENTIONAL")
add("nfc_first_word_target_override", 3073, first_iid, en, kr,
    "실제 first_word의 canonical equivalent NFD만 메모리에서 적용. first_word 인자의 NFC 누락과 response NFC 사이의 비대칭 검사; 원본 데이터 변경 없음.",
    "nfc_target_override", "CHECKER", patch={"ko": {"first_word": NFD(ko_kw["first_word"])}})

(ROOT / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"{len(cases)} cases; dataset keys={sorted({c['key'] for c in cases if c['key'] is not None})}")
