"""Validate recorded decisions and generate the Korean audit report."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def tf(value):
    return "T" if value else "F"


def target(result, mode):
    return result["isolated"][mode]["instruction_results"][0]


def decision(result, mode):
    full = result["full"][mode]
    return f"{tf(target(result, mode))} / [{','.join(map(tf, full['instruction_results']))}] / {tf(full['prompt_result'])}"


def source_link(info):
    return f"[{info['function']}:{info['line']}]({info['path']}#L{info['line']})"


def upstream_link(provenance, group, path, line, label):
    entry = provenance[group]
    return f"[{label}]({entry['repository']}/blob/{entry['revision']}/{path}#L{line})"


def diagnostic_summary(result, form="raw"):
    diag = result["diagnostics"][form]
    if "count" in diag:
        return f"count={diag['count']}; checker={tf(diag['checker_result'])}"
    if "matches" in diag:
        return f"match={json.dumps(diag['matches'], ensure_ascii=False)}; checker={tf(diag['checker_result'])}"
    return f"checker={tf(diag['checker_result'])}"


def main():
    cases = read("cases.json")
    provenance = read("provenance.json")
    for entry in provenance.values():
        for info in entry["files"].values():
            assert hashlib.sha256((ROOT / info["local_path"]).read_bytes()).hexdigest() == info["sha256"], "source/data snapshot changed"
    import pyarrow.parquet as pq
    assert read("sources/ko/data/rows.json") == pq.read_table(
        ROOT / "sources/ko/data/train-00000-of-00001.parquet").to_pylist(), "parquet/derived JSON mismatch"
    runs = {s: read(s + "_results.json") for s in ["original", "ko"]}
    datasets = {
        "original": {r["key"]: r for r in map(json.loads, (ROOT / "sources/original_dataset/ifeval_input_data.jsonl").read_text().splitlines())},
        "ko": {r["key"]: r for r in read("sources/ko/data/rows.json")}}
    expected_case_hash = hashlib.sha256((ROOT / "cases.json").read_bytes()).hexdigest()
    for side, run in runs.items():
        assert run["environment"]["cases_sha256"] == expected_case_hash, f"stale {side} results"
        assert len(run["results"]) == len(cases)
        assert all("error" not in r for r in run["results"]), f"failed {side} cases"
        assert [r["case_id"] for r in run["results"]] == [c["case_id"] for c in cases]
        assert run["environment"]["nltk_resource_sha256"] == read("nltk_resources.json")["sha256"], "NLTK resource drift"
        expected_files = provenance["harness" if side == "original" else "ko"]["files"]
        for name, sha in run["environment"]["module_sha256"].items():
            file = ("lm_eval/tasks/ifeval/" if side == "original" else "ifeval_ko/") + name + ".py"
            assert sha == expected_files[file]["sha256"], f"upstream module modified: {side}/{file}"

    merged = []
    for i, case in enumerate(cases):
        original, ko = runs["original"]["results"][i], runs["ko"]["results"][i]
        for side, result in [("original", original), ("ko", ko)]:
            if case["key"] is not None:
                row = datasets[side][case["key"]]
                assert case[side + "_prompt"] == row["prompt"]
                assert case[side + "_instruction_id_list"] == row["instruction_id_list"]
                assert case[side + "_all_kwargs"] == row["kwargs"]
            for mode in ["strict", "loose"]:
                full = result["full"][mode]
                assert full["prompt_result"] == all(full["instruction_results"])
                assert target(result, mode) == full["instruction_results"][result["instruction_index"]]
            assert not target(result, "strict") or target(result, "loose")
        differences = {
            "target_strict": target(original, "strict") != target(ko, "strict"),
            "target_loose": target(original, "loose") != target(ko, "loose"),
            "prompt_strict": original["full"]["strict"]["prompt_result"] != ko["full"]["strict"]["prompt_result"],
            "prompt_loose": original["full"]["loose"]["prompt_result"] != ko["full"]["loose"]["prompt_result"]}
        merged.append({"case": case, "original": original, "ko": ko, "differences": differences})
    by_id = {r["case"]["case_id"]: r for r in merged}
    balanced_star = by_id["markdown_star_balanced_136"]["ko"]
    assert balanced_star["full"]["loose"]["prompt_result"]
    assert not any(r["prompt_result"] for r in balanced_star["strict_on_actual_loose_candidates"])
    persistent_dash = by_id["markdown_dash_persistent_136"]["ko"]
    assert min(r["count"] for r in persistent_dash["isolated"]["loose"]["checker_call_trace"]) == 104

    non_nfc = []
    def inspect_nfc(value, path):
        if isinstance(value, str) and unicodedata.normalize("NFC", value) != value:
            non_nfc.append(path)
        elif isinstance(value, list):
            for i, v in enumerate(value): inspect_nfc(v, path + [i])
        elif isinstance(value, dict):
            for k, v in value.items(): inspect_nfc(v, path + [k])
    for key, row in datasets["ko"].items(): inspect_nfc(row, [key])
    summary = {"cases": len(merged), "keys": sorted({c["key"] for c in cases if c["key"] is not None}),
               "scope_counts": dict(Counter(c["scope"] for c in cases)),
               "original_rows": len(datasets["original"]), "ko_rows": len(datasets["ko"]),
               "common_keys": len(datasets["original"].keys() & datasets["ko"].keys()),
               "ko_non_nfc_field_paths": non_nfc,
               "differences": {k: sum(r["differences"][k] for r in merged) for k in merged[0]["differences"]},
               "target_same_strict_and_loose": sum(not r["differences"]["target_strict"] and not r["differences"]["target_loose"] for r in merged),
               "difference_classifications": dict(Counter(r["case"]["classification"] for r in merged
                   if r["differences"]["target_strict"] or r["differences"]["target_loose"]))}
    (ROOT / "dataset_checks.json").write_text(dump({k: summary[k] for k in
        ["original_rows", "ko_rows", "common_keys", "ko_non_nfc_field_paths"]}) + "\n", encoding="utf-8")
    result = {"summary": summary, "environments": {s: run["environment"] for s, run in runs.items()},
              "provenance": provenance, "nltk_resources": read("nltk_resources.json"), "cases": merged}
    (ROOT / "results.json").write_text(dump(result) + "\n", encoding="utf-8")
    lines = ["# IFEval / IFEval-Ko checker 검증 보고서", "",
        "실제 evaluator 함수를 import해 통제한 응답을 검사했다. 모델 생성·성능 평가가 아니다. LightEval 코드는 참고용 원본으로만 저장했으며 수정·commit·PR·원격 쓰기는 하지 않았다.", "",
        "## 1. 실행 환경과 명령어", ""]
    for side, run in runs.items():
        env = run["environment"]
        lines += [f"- {side}: Python `{env['python'].splitlines()[0]}`, `{env['platform']}`, import mode `{env['import_mode']}`."]
    lines += ["", "```bash", "ifeval_checker_audit/.venv/bin/python ifeval_checker_audit/build_cases.py",
              "ifeval_checker_audit/.venv/bin/python ifeval_checker_audit/run_original.py",
              "ifeval_checker_audit/.venv/bin/python ifeval_checker_audit/run_ko.py",
              "ifeval_checker_audit/.venv/bin/python ifeval_checker_audit/compare.py", "```", "",
              "설치·재구성 명령은 [README.md](README.md)에 있다. 실제 command, module path, SHA-256, 패키지 버전은 [results.json](results.json)의 `environments`에 기록했다.", "",
              "`full-package`는 로컬에 설치한 실제 harness 패키지의 `InputExample`, `test_instruction_following_strict`, `test_instruction_following_loose` 실행을 뜻한다. Ko의 원본 파일은 `lm_eval.tasks.__path__`에 로컬 snapshot 경로를 추가해 원래 import 이름 그대로 불러온다. 함수 복제·checker 재구현·monkey patch는 없다. 모델을 연결한 `lm_eval.simple_evaluate`/CLI 전체 benchmark는 실행하지 않았다.", "",
              "설치 대기 중에는 `isolated-source`로 원본 네 모듈을 먼저 실행했다. 그 예비 결과는 최종 결과에 사용하지 않는다. `isolated-source`는 package 상위 namespace를 구성하는 명시적 fallback이며 정식 harness 전체 package 실행과 구분한다. 최종 import 실패·case 실행 실패 여부는 아래 환경 및 검증 결과를 기준으로 한다.", "",
              "NLTK English Punkt는 `punkt_tab/english` 데이터로 실행했고, [nltk_resources.json](nltk_resources.json)에 자원 hash를 고정했다. 다운로드 시 현재 WSL 경로의 group/world-writable 속성에 대한 NLTK 경고가 있었다. 실제 tokenizer 로딩 및 모든 case 실행은 성공했다. Ko 원본의 `\\s` 일반 문자열은 Python 3.12에서 SyntaxWarning을 내며, 원본을 수정하지 않았다.", "",
              "## 2. Repository / dataset revision", "", "| Source | Revision | Reference |", "| --- | --- | --- |"]
    for name, entry in provenance.items():
        title = {"harness": "EleutherAI/lm-evaluation-harness", "lighteval": "Hugging-Face-KREW/lighteval",
                 "original_dataset": "google/IFEval", "ko": "allganize/IFEval-Ko"}[name]
        lines.append(f"| {name} | `{entry['revision']}` | [{title}]({entry['repository']}) |")
    lines += ["", "모든 다운로드는 지정 revision의 read-only HTTP 요청이다. 파일별 URL/hash는 [provenance.json](provenance.json)에 있다. 영어 데이터는 JSONL, Ko는 train parquet 원본을 읽었다. Ko의 코드와 데이터는 동일 HF repository revision이다.", "",
              "## 3. 검증 key와 실제 문항 대조", "",
              f"검증 key: `{', '.join(map(str, summary['keys']))}`. 영어 {summary['original_rows']}행, Ko {summary['ko_rows']}행, 공통 {summary['common_keys']}개이며 중복 key는 없다. {summary['cases']}개 테스트: 실제 dataset 조건 {summary['scope_counts']['dataset']}개, 메모리 override {summary['scope_counts']['controlled_override']}개, 합성 fixture {summary['scope_counts']['synthetic']}개.", "",
              "`dataset`은 실제 prompt/IDs/kwargs 그대로 사용한다. `controlled_override`는 실제 행을 바탕으로 지정 kwargs만 실행 중 변경한다. `synthetic`은 key가 null인 합성 fixture이며 데이터셋 문항에 대한 판정으로 해석하면 안 된다. 원문/한국어 대응 응답과 동일 한국어 입력을 사용하는 알고리즘 격리 응답을 구분했다. 짧은 응답은 주제 적합성을 평가하지 않는다.", "",
              "Parquet kwargs에는 많은 null 필드가 있다. cases.json은 이를 원본 그대로 보존한다. 아래 표시는 null만 생략했다. evaluator는 양쪽 모두 실제 `{k:v for k,v in kwargs.items() if v}`를 사용한다. full instruction ID 순서와 모든 instruction 결과를 보존하고, 대상 instruction만 넣은 InputExample도 같은 실제 evaluator로 따로 실행했다.", ""]
    for key in summary["keys"]:
        lines += [f"### Key {key}", ""]
        for side in ["original", "ko"]:
            row = datasets[side][key]
            lines += [f"**{side} prompt**", "", "```text", row["prompt"], "```", "",
                      f"**{side} instruction_id_list / kwargs**", "", "```json",
                      dump({"instruction_id_list": row["instruction_id_list"],
                            "kwargs": [{k: v for k, v in kw.items() if v is not None} for kw in row["kwargs"]]}), "```", ""]
    lines += ["## 4. 판정이 동일했던 사례", "",
              f"대상 instruction의 strict와 loose가 모두 동일한 테스트는 {summary['target_same_strict_and_loose']}개다. 개별 결과는 전체 표와 아래 상세 기록에서 확인할 수 있다.", "",
              "- 짧은 `사과,배,포도`는 count 3/1이지만 실제 key 3442의 <20에서는 둘 다 통과한다. 공백을 넣으면 count도 3/3으로 같아진다.",
              "- punctuation 없는 두 줄은 양쪽 모두 1문장, 마침표 있는 두 줄은 2문장이다. Markdown heading은 별도 sentence를 만들지 않는다.",
              "- trailing `---`는 양쪽 모두 추가 sentence로 센다. 두 문장+divider는 strict 실패/loose 성공으로 동일하다.",
              "- 소수점 3.14/2.71과 Dr. 예시는 양쪽 모두 2문장이다.",
              "- 붙여 쓴 강조 `*사과* *배* *포도*`의 39-word case는 양쪽 strict/loose 통과한다.",
              "- 합성 사과 경계 fixture에서 양쪽 ForbiddenWords는 사과만 거부하고 사과를/사과가/사과나무는 허용한다. 양쪽 KeywordChecker/FrequencyChecker는 네 입력에서 모두 사과를 찾는다.",
              "- 실제 한국어 kwargs가 NFC인 데이터 문항에서 response를 NFD로 바꾸어도 Ko evaluator가 NFC로 복원한다. 영어 대응 응답 결과와 대상 instruction 판정이 같다.", "",
              "## 5. 판정이 달랐던 사례", "",
              f"대상 strict 차이 {summary['differences']['target_strict']}개, 대상 loose 차이 {summary['differences']['target_loose']}개, prompt strict 차이 {summary['differences']['prompt_strict']}개, prompt loose 차이 {summary['differences']['prompt_loose']}개. 합성/대조군을 포함한 audit 건수이며 benchmark accuracy가 아니다.", "",
              "### Keyword / kwargs mismatch: key 3345", "",
              "`강도 강도는 등장합니다.`에서 Ko는 kwargs의 robber를 그대로 `re.findall`로 검색해 0회로 판정한다. 영어 대응 응답은 robber 2회여서 대상 strict/loose가 T/T, Ko는 F/F다. 이 최소 응답은 bullet instruction을 실패하므로 full prompt는 둘 다 F다. `* robber\\n* robber`와 `* 강도\\n* 강도`는 bullet과 forbidden 제약도 만족해 full prompt까지 T/T 대 F/F다. Ko keyword만 강도로 메모리 override하면 2회·T/T가 되며 full prompt도 T/T로 복원된다. 이 차이는 DATA이며 검색 알고리즘 변경 근거가 아니다.", "",
              "### 단어 수: 실제 threshold와 loose", "",
              "key 3442의 `<<제목>>`+항목 16개+`사과,배,포도`는 영어 count 20으로 <20 실패, Ko 18로 통과한다. 쉼표 뒤에 공백을 넣으면 Ko도 20이 되어 strict/loose 실패한다. 한 줄이라 loose의 첫/마지막 줄 삭제 후보는 빈 문자열이며 evaluator가 제외한다.", "",
              "key 136의 99 lexical words는 heading 또는 단일 줄 `>`를 넣으면 Ko 100이 된다. heading은 첫 줄 제거로 loose가 복구되지만 단일 줄 quote는 F가 남는다. 9개 균등 bullet은 count 99/108, Ko strict F·loose T다. 같은 99 words에서 양 끝 bullet을 짧게 만들면 dash의 loose count가 최소 104로 남아 F다. star는 실제 loose `*` 제거 후보에서 99가 되어 T다. key 349에서 별도 공백으로 분리된 강조 marker는 39/45로 strict를 바꾸지만 loose star 제거로 39가 되어 복구된다.", "",
              "공백으로 둘러싼 `* 사과 *`는 실제 CommonMark italic이 아니며 위 separated-marker case는 regex/token control이다. 별도 `markdown_quote_valid_highlights_349`는 유효한 `> *사과* *배* *포도*` 형식에 39 lexical words를 넣어 강조 3개를 충족한다. Original count 39·strict/loose T, Ko count 40·strict/loose F로 full prompt 차이까지 재현한다. 유효한 자연스러운 출력 형식과 단순 matcher control을 구분한다.", "",
              "key 136의 균등 star bullet은 Ko prompt-level loose=T여도 하나의 변환 응답이 두 instruction을 함께 통과하는 것은 아니다. bullet instruction은 원본, word instruction은 star 제거/줄 제거 후보에서 각각 통과한다. 실제 loose 후보 8개 각각을 strict evaluator로 재검사한 `strict_on_actual_loose_candidates`에서도 모든 prompt가 F임을 확인했다. loose는 instruction마다 독립적으로 후보 OR를 취한다.", "",
              "word count의 공백 기준은 Ko count_words docstring에 명시된 선택(INTENTIONAL)이다. Markdown 기호를 독립 word로 포함해야 하는지와 loose 이후 잔존 차이를 허용할지는 NEEDS_DISCUSSION이다. 어느 tokenizer가 더 옳은지는 이 실행만으로 결정하지 않는다.", "",
              "### 문장 수", "",
              "실제 key 3739의 <3 조건에서 `가.`/`나.` 목록은 NLTK 4문장, Ko 2문장으로 strict F/T다. 줄을 나누면 original loose가 첫 줄 제거로 T가 되지만 한 줄이면 F/T가 그대로 남는다. e.g. 및 가.나.다. 예시도 3/2로 strict·loose F/T다. Ko 코드는 한국어 list marker·혼합 한영 abbreviation을 명시적으로 보호한다. 이 범위의 차이는 INTENTIONAL로 분류하며 올바른 문장 정책의 일반적 증명은 아니다.", "",
              "### ForbiddenWords", "",
              "양쪽 모두 `\\b + word + \\b`를 사용한다. Python Unicode regex의 word boundary는 한국어 조사나 합성어의 의미 경계가 아니다. 실제 key 1242의 JSON 응답 nickname/별명은 둘 다 금지하지만 nickname/별명을 대응시키면 영어 F, Ko T다. 구현이 다른 사례가 아니라 동일 경계 구현의 언어 적용 결과이므로 NEEDS_DISCUSSION이다. 조사를 붙인 형태까지 금지할지와 사과나무 같은 합성어까지 금지할지는 별도의 정책 선택이다.", "",
              "### NFC: evaluator와 direct checker를 구분", "",
              "합성 `가`는 U+AC00이고 분해형 `가`는 U+1100 U+1161의 두 코드 포인트다. 두 문자는 canonical equivalent이며 NFC 후 같은 문자열이다. 각 case의 unicode_response에도 전후 코드 포인트를 기록했다.", "",
              "Ko utils strict/loose는 response를 NFC로 만든 뒤 checker를 호출한다. KeywordChecker의 keywords, KeywordFrequencyChecker의 keyword, ForbiddenWords의 forbidden_words, EndChecker의 end_phrase, RepeatPromptThenAnswer의 prompt_to_repeat는 build_description에서 NFC가 된다. 따라서 direct check_following(NFD response)는 False일 수 있어도 실제 Ko evaluator는 True가 될 수 있다. ForbiddenWords에서는 통과/실패의 방향이 반대다.", "",
              "InputExample.prompt 전체나 kwargs 전체를 일괄 NFC 처리하는 코드는 없다. repeat checker는 prompt_to_repeat 인자를 비교하며 utils의 `args에 prompt가 있으면 재build` 분기를 사용하지 않는다. KeySentenceChecker는 key_sentences를 NFC 처리하지만 registry에서 비활성화되어 실제 evaluator case를 만들지 않았다.", "",
              "추가로 ParagraphFirstWordCheck는 first_word를 lower만 하고 NFC 처리하지 않는다. 합성 NFD first_word+NFD response는 original T/T, Ko F/F다. Ko가 response만 NFC로 바꾸어 대상과 불일치하는 결과다. 실제 key 3073에서도 first_word=회사를 canonical equivalent NFD로 메모리 override하면 Ko F/F, 외부에서 대상까지 NFC로 만들면 T/T다. 이는 응답/비교 대상 정규화의 비대칭 CHECKER 사례다. 현재 Ko 데이터 342행의 모든 문자열은 NFC였으므로 현 revision의 데이터에서 이 실패가 발생했다고 주장하지 않는다.", "",
              "각 NFC case에는 raw direct checker, NFC response direct checker, 실제 evaluator, 외부 NFC(response only), 외부 NFC(response+kwargs+prompt) 결과를 따로 저장했다. kwargs가 NFD인 original checker는 response만 정규화해도 실패할 수 있으며, 대상도 정규화한 control이 이를 분리한다.", "",
              "## 6. 분류와 수정 판단", "", "| Classification | 근거 | 지금 판단 가능한 범위 |", "| --- | --- | --- |",
              "| DATA | key 3345 prompt 강도 ↔ kwargs robber 불일치; override 대조군으로 복원 | 데이터 alignment 검토 필요. checker 알고리즘 수정 대상 아님 |",
              "| CHECKER | ParagraphFirstWordCheck에서 response NFC / first_word 비정규화의 비대칭 | canonical equivalence를 지원하려면 대상 정규화가 필요. 현재 dataset에 NFD first_word가 있다는 근거는 없음 |",
              "| INTENTIONAL | Ko 공백 word count docstring, 한국어 list/혼합 abbreviation 보호 코드, README의 NFC 및 sentence 변경 | 호환성 차이 재현 가능. 영어 checker를 대체해야 한다는 근거는 아님 |",
              "| NEEDS_DISCUSSION | Markdown marker word 포함 정책, forbidden 경계의 조사/합성어 의미, divider 같은 sentence 정책 | 실행 결과만으로 정책 우열·수정 여부 확정 불가 |", "",
              "분류는 관찰 원인의 분류다. 같은 결과의 control도 정책 확인 목적으로 분류가 붙어 있으며 bug 목록이 아니다. count 함수가 다르다는 사실과 instruction 판정이 다른 사실을 분리했다. 모든 차이의 count/match·source·수정 판단은 상세 기록에 있다.", "",
              "## 7. 이번 주 발표용 사례", "",
              "1. key 3345: 강도 2회인데 robber match 0 → keyword-only override로 2회/T 복원. DATA와 CHECKER 구분에 가장 분명하다.",
              "2. key 3442: 같은 쉼표 목록의 공백만 변경 → Original 20/20·F/F, Ko 18/20·T/F. 짧은 3/1 count 예시에서는 실제 threshold 판정은 둘 다 T라는 control도 함께 제시한다.",
              "3. key 136: star/dash 각각 99/108; 균등 list는 loose T지만 양 끝이 짧은 dash list는 loose F. 실제 loose 후보와 instruction별 OR를 설명하기 좋다.",
              "4. key 3739: 한 줄 가./나. 목록에서 4/2문장 → strict와 loose 모두 F/T. 명시적인 한국어 list marker 처리를 보여준다.",
              "5. NFC: 가/가 keyword에서 direct checker와 evaluator가 다름. first_word에는 대상 NFC 누락이 있어 합성 NFD/NFD가 original T, Ko F. 의도된 개선과 불완전 적용을 구분한다.", "",
              "## 8. 다음 단계 LightEval 반영 후보", "",
              "- 영어 task와 분리된 Ko task의 dataset snapshot, instruction registry, 길이 계산·NFC 정책을 명시하고 회귀 fixture를 유지한다.",
              "- key 3345는 upstream dataset issue/로컬 overlay 후보. 이번 작업에서는 원격 issue 생성이나 수정도 하지 않았다.",
              "- NFC를 도입한다면 response와 실제 비교 대상의 정규화 범위를 함께 설계하고 first_word 누락 대조군을 유지한다.",
              "- Word/sentence 정책 선택 전에 Markdown strict/loose와 한국어 list/약어의 호환성 표를 검토한다.", "",
              "LightEval 네 파일은 정적 확인만 했다. instructions_utils.count_words는 RegexpTokenizer, count_sentences는 English Punkt다. instructions의 ForbiddenWords는 word boundary, KeywordChecker/FrequencyChecker는 boundary 없는 regex이고 main.py는 동일한 8개 loose 후보와 instruction별 OR를 사용한다. 이 구조는 후속 반영 위치를 설명하지만 이 보고서의 Original 결과는 LightEval 실행 결과가 아니다.", "",
              "## 9. 근거가 부족하여 수정하면 안 되는 부분", "",
              "- 공백 단위와 regex 단위 중 하나를 일반적으로 더 옳다고 단정하거나 영어 IFEval 길이 로직을 일괄 교체하는 것.",
              "- 한국어 ForbiddenWords를 조사/합성어까지 무조건 포함하도록 변경하는 것. 의미 정책 합의 및 추가 근거가 필요하다.",
              "- heading/divider를 sentence나 word에서 일괄 제거하는 것. 여기서는 양쪽 divider가 같은 결과였으며 정책 정답을 확정하지 않았다.",
              "- first_word 합성 실패를 현 데이터셋의 실제 대량 실패·모델 성능 저하로 보고하는 것.",
              "- 최소 응답이 주제·문항 전체 의도를 충족한다고 해석하거나 테스트 차이 건수를 benchmark accuracy 차이로 제시하는 것.", "",
              "추가 데이터 관찰: key 127은 Ko prompt 5회 이상 / kwargs frequency=6이며 original은 more than 5/6으로 맞는다. key 3739는 '3문장 이하'라는 표현과 '1 또는 2문장' 설명이 함께 있고 kwargs는 <3이다. key 1268의 <6→6문장 이하 번역도 소스 탐색에서 확인했다. 이들은 데이터 문구 검토 후보이며 별도의 완전한 evaluator 반례를 구성하지 않은 것은 검증 완료 DATA 건수에 넣지 않았다.", "",
              "## 전체 판정 표", "",
              "각 셀은 **대상 instruction / 전체 instruction 리스트 / prompt-level** 순서다. I=strict 대상 차이, L=loose 대상 차이, P=strict prompt 차이, PL=loose prompt 차이. `합성`은 실제 dataset key가 없다. `override`는 실행 중 값 변경이다.", "",
              "| Key | Checker | Test | Original strict | Original loose | Ko strict | Ko loose | Difference | Classification |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in merged:
        c, a, b = row["case"], row["original"], row["ko"]
        key = "합성" if c["key"] is None else str(c["key"]) + (" override" if c["scope"] == "controlled_override" else "")
        diff = ", ".join(label for label, k in [("I", "target_strict"), ("L", "target_loose"), ("P", "prompt_strict"), ("PL", "prompt_loose")] if row["differences"][k]) or "동일"
        lines.append(f"| {key} | {c['checker']} | `{c['case_id']}` | {decision(a,'strict')} | {decision(a,'loose')} | {decision(b,'strict')} | {decision(b,'loose')} | {diff} | {c['classification']} |")
    lines += ["", "## 상세 실행 기록", "",
              "count/match는 실제 imported count 함수와 checker의 build 결과를 이용한다. `checker_call_trace`와 `loose_candidates_from_evaluator`는 실제 evaluator 실행 frame에서 수집한 것으로 loose를 재구현하지 않았다. source는 로컬 snapshot의 원래 line 번호다.", ""]
    for row in merged:
        c, a, b = row["case"], row["original"], row["ko"]
        lines += [f"### {c['case_id']}", "", f"Key={c['key']}, scope={c['scope']}, `{c['instruction_id']}`, {c['classification']}.", "", c["reason_for_test"], ""]
        if "expected_observation" in c:
            lines += ["사전 예상(실행 결과 아님): `" + json.dumps(c["expected_observation"], ensure_ascii=False) + "`.", ""]
        for side, r in [("original", a), ("ko", b)]:
            lines += [f"**{side} response**", "", "```text", c["test_response_" + side], "```", "",
                      f"Raw: {diagnostic_summary(r)}. NFC(response): {diagnostic_summary(r, 'nfc')}. strict `{decision(r,'strict')}`, loose `{decision(r,'loose')}`.", "",
                      "Code: " + ", ".join(source_link(info) for info in r["source"].values()) + ".", ""]
            diag = r["diagnostics"]["raw"]
            if "tokens" in diag or "sentences" in diag:
                field = "tokens" if "tokens" in diag else "sentences"
                lines += [f"실제 {field}: `{json.dumps(diag[field], ensure_ascii=False)}`.", ""]
            if c["group"].startswith("nfc"):
                lines += ["Built args: `" + json.dumps(diag["built_args"], ensure_ascii=False) + "`.", "",
                          "외부 NFC response only strict/loose: `" + "/".join(tf(r["isolated_nfc_response"][k]["instruction_results"][0]) for k in ["strict", "loose"]) + "`; 외부 NFC response+대상 strict/loose: `" + "/".join(tf(r["isolated_nfc_both"][k]["instruction_results"][0]) for k in ["strict", "loose"]) + "`.", ""]
            trace = r["isolated"]["loose"]["checker_call_trace"]
            if row["differences"]["target_strict"] or row["differences"]["target_loose"]:
                lines += ["실제 loose에서 호출한 대상 checker 결과: `" + json.dumps([x["result"] for x in trace]) + "`.", ""]
                if trace and "count" in trace[0]:
                    lines += ["실제 loose checker 입력의 count: `" + json.dumps([x["count"] for x in trace]) + "`.", ""]
                if c["instruction_id"] in {"length_constraints:number_words", "length_constraints:number_sentences"}:
                    # Counts are obtained from recorded actual checker inputs. For
                    # these exact fixtures word tokens are available in the raw
                    # diagnostics; full traced inputs remain in results.json.
                    witness = next((x["value"] for x in trace if x["result"]), None)
                    if witness is not None:
                        lines += ["loose 성공 후보(실제 호출값):", "", "```text", witness, "```", ""]
        if c.get("runtime_override"):
            lines += ["명시적 runtime override: `" + json.dumps(c["runtime_override"], ensure_ascii=False) + "`.", ""]
        judgment = {"DATA": "dataset alignment 문제. key 3345의 keyword correction 필요성을 대조군으로 확인했으나 원본 데이터·checker는 수정하지 않았다.",
                    "CHECKER": "응답 NFC와 first_word 대상의 비정규화 비대칭. canonical equivalence 지원 범위에서는 개선 후보지만 현 dataset에서의 발생을 의미하지 않는다.",
                    "INTENTIONAL": "Ko 코드/docstring/README에 명시된 기준 선택 또는 해당 기준의 control. 차이를 자동으로 bug라 결론내리지 않는다.",
                    "NEEDS_DISCUSSION": "정책 우열은 코드와 README만으로 확정할 수 없다. 동일 결과인 control도 포함하며 즉시 수정 근거가 아니다."}[c["classification"]]
        lines += ["수정 판단: " + judgment, ""]
    lines += ["## 핵심 소스 위치", "", "| 동작 | Original | Ko |", "| --- | --- | --- |"]
    for label, opath, oline, kpath, kline in [
        ("Word tokenizer", "instructions_util.py", 1681, "instructions_util.py", 147),
        ("Sentence count", "instructions_util.py", 1692, "instructions_util.py", 150),
        ("Keyword search", "instructions.py", 791, "instructions.py", 781),
        ("Keyword frequency search", "instructions.py", 859, "instructions.py", 850),
        ("Forbidden word boundary", "instructions.py", 1160, "instructions.py", 1158),
        ("Strict entry", "utils.py", 25, "utils.py", 30),
        ("Loose candidates", "utils.py", 63, "utils.py", 64),
        ("ParagraphFirstWordCheck build", "instructions.py", 963, "instructions.py", 955)]:
        lines.append("| " + label + " | " + upstream_link(provenance, "harness", "lm_eval/tasks/ifeval/" + opath, oline, opath + ":" + str(oline))
                     + " | " + upstream_link(provenance, "ko", "ifeval_ko/" + kpath, kline, kpath + ":" + str(kline)) + " |")
    lines += ["", "| LightEval 참고 파일 | 정적 확인 |", "| --- | --- |"]
    for label, name, line in [("count_words / count_sentences", "instructions_utils.py", 1664),
                              ("KeywordFrequencyChecker / ForbiddenWords", "instructions.py", 818),
                              ("INSTRUCTION_DICT", "instructions_registry.py", 40),
                              ("Loose preprocessing / IFEvalMetrics.compute", "main.py", 66)]:
        lines.append("| " + upstream_link(provenance, "lighteval", "src/lighteval/tasks/tasks/ifeval/" + name, line, name + ":" + str(line)) + " | " + label + " |")
    lines += ["", "## 검증 완료 조건", "",
              f"- final 양쪽 {summary['cases']}개 case 실행 성공, 기록된 실패 없음.",
              "- 실행한 네 모듈의 hash가 원격에서 고정 revision으로 받은 원본과 같음을 검증했다.",
              "- 모든 실제 key의 prompt/IDs/kwargs가 보존된 데이터 원본과 같음을 검증했다.",
              "- isolated 대상 결과와 full instruction 리스트의 대상 결과, prompt=all(instructions), strict 성공→loose 성공을 검증했다.",
              "- final case hash 일치로 오래된 실행 결과의 혼입을 막았다. NLTK 자원 hash와 dependency lock을 보존했다.", ""]
    (ROOT / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print(dump(summary))


if __name__ == "__main__":
    main()
