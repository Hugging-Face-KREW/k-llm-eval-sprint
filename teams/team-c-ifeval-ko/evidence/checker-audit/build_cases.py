"""Build the 156-case experiment and auxiliary inputs from pinned source rows."""
import argparse
import copy
from collections import Counter
import json
from pathlib import Path

from case_utils import (ROOT, baseline_cases, baseline_cases_hash, baseline_run, read_baseline, object_hash, input_hashes, instruction_index, partition, read_json,
                        registry_names, sha, validate_cases, validate_source_row,
                        verify_sources, write_json)


KO_TEXT = "서비스의 신뢰성을 관리하는 업무입니다. 서비스 지표를 살피고 목표를 정하며 장애의 원인을 분석합니다."
EN_TEXT = ("The reliability engineer monitors service quality and resolves operational incidents. "
           "This response is written entirely in English.")
RU_TEXT = ("Решётка представляет собой упорядоченную структуру из повторяющихся элементов. "
           "Эти элементы соединяются между собой и образуют регулярный узор.")


def words(n, token="평가"):
    return " ".join([token] * n)


def sentences(n, multiline=False):
    return ("\n" if multiline else " ").join(["평가합니다."] * n)


class Builder:
    def __init__(self, source_root):
        import pyarrow.parquet as pq
        self.provenance, self.verified = verify_sources(source_root)
        source_root = Path(source_root)
        self.rows = pq.read_table(source_root / "sources/ko/data/train-00000-of-00001.parquet").to_pylist()
        self.ko = {r["key"]: r for r in self.rows}
        self.original = {r["key"]: r for r in map(json.loads, (source_root / "sources/original_dataset/ifeval_input_data.jsonl").read_text().splitlines())}
        self.checkers = registry_names(source_root / "sources/ko/ifeval_ko/instructions_registry.py")
        self.legacy = baseline_cases()
        stored = baseline_run("ko")
        # Checkout newline conversion is recorded, never mistaken for changed JSON.
        self.legacy_lf_hash = baseline_cases_hash(read_baseline())
        if self.legacy_lf_hash != stored["environment"]["cases_sha256"]:
            raise ValueError("Archived cases differ from the stored Ko oracle")
        self.saved = {r["case_id"]: r for r in stored["results"]}
        self.cases, self.support = [], []
        for old in self.legacy:
            case = copy.deepcopy(old)
            case["instruction_index"] = instruction_index(case["ko_instruction_id_list"], case["instruction_id"])
            case["targets"] = []
            case["origin"] = "legacy_86"
            result = self.saved[case["case_id"]]
            self.finish(case, result["full"]["strict"]["instruction_results"], result["full"]["loose"]["instruction_results"], "archived_ko_results_not_current_execution")
            self.target(case, case["instruction_index"])
            self.cases.append(case)
        self.by_name = {c["case_id"]: c for c in self.cases}

    def finish(self, case, strict, loose, basis="predeclared_from_pinned_code_and_review"):
        case["comparison_input"] = "identical_ko"
        case["source_revisions"] = {name: entry["revision"] for name, entry in self.provenance.items()}
        case["expected_ko"] = {"basis": basis,
                               "full": {"strict": list(strict), "loose": list(loose)},
                               "prompt": {"strict": all(strict), "loose": all(loose)}}
        case["hashes"] = input_hashes(case)

    def target(self, case, index, boundary=None):
        iid = case["ko_instruction_id_list"][index]
        existing = next((t for t in case["targets"] if t["instruction_index"] == index), None)
        target = existing if existing is not None else {
            "instruction_index": index, "instruction_id": iid,
            "input_partition": partition(iid, case.get("ko_eval_all_kwargs", case["ko_all_kwargs"])[index]),
        }
        if boundary:
            target["boundary"] = boundary
        if existing is None:
            case["targets"].append(target)

    def add(self, name, key, indices, response, strict, loose=None, group="input_partition", reason="", boundary=None):
        loose = strict if loose is None else loose
        iid = self.ko[key]["instruction_id_list"][indices[0]]
        case = {"case_id": "expanded_" + name, "key": key, "scope": "dataset", "origin": "extension_70",
                "instruction_id": iid, "instruction_index": indices[0], "checker": self.checkers[iid],
                "group": group, "classification": "INTENTIONAL", "reason_for_test": reason or name,
                "test_response_original": response, "test_response_ko": response, "targets": []}
        for side, row in [("original", self.original[key]), ("ko", self.ko[key])]:
            case[side + "_prompt"] = row["prompt"]
            case[side + "_instruction_id_list"] = row["instruction_id_list"]
            case[side + "_all_kwargs"] = copy.deepcopy(row["kwargs"])
            case[side + "_kwargs"] = copy.deepcopy(row["kwargs"][indices[0]])
        self.finish(case, strict, loose)
        for i in indices:
            self.target(case, i, boundary if i == indices[0] else None)
        self.cases.append(case)
        return case

    def promote(self, name, index, boundary=None):
        self.target(self.by_name[name], index, boundary)

    def auxiliary(self, name, iid, kwargs, response, expected=None, error=None, group="kwargs_contract"):
        case = {"case_id": "support_" + name, "key": None, "scope": "synthetic", "origin": "support_18",
                "instruction_id": iid, "instruction_index": 0, "checker": self.checkers.get(iid, "UNREGISTERED"),
                "group": group, "classification": "NEEDS_DISCUSSION", "reason_for_test": name,
                "targets": [{"instruction_index": 0, "instruction_id": iid, "input_partition": "outside_dataset_contract"}],
                "test_response_original": response, "test_response_ko": response}
        for side in ["original", "ko"]:
            case[side + "_prompt"] = "Synthetic evaluator contract diagnostic; not a dataset row."
            case[side + "_instruction_id_list"] = [iid]
            case[side + "_all_kwargs"] = [copy.deepcopy(kwargs)]
            case[side + "_kwargs"] = copy.deepcopy(kwargs)
        if error:
            case["comparison_input"] = "identical_ko"
            case["source_revisions"] = {n: e["revision"] for n, e in self.provenance.items()}
            case["expected_ko"] = {"error_type": error, "basis": "pinned_source_error_contract"}
            case["hashes"] = input_hashes(case)
        else:
            self.finish(case, [expected], [expected])
        self.support.append(case)


def build(source_root, output_dir):
    b = Builder(source_root)

    def boundary(parameter, threshold, count):
        return {"parameter": parameter, "threshold": threshold, "response_count": count, "offset": count - threshold}

    # 13 count paths, each with N-1/N/N+1. Expectations are declared here,
    # before any evaluator runs, and never regenerated from observed decisions.
    for n in [7, 8, 9]:
        b.add(f"freq_ge_{n}", 1233, [1], words(n, "마천루"), [False, n >= 8], boundary=boundary("frequency", 8, n))
    for n in [2, 3, 4]:
        b.add(f"freq_lt_{n}", 1928, [2], words(n, "피부"), [False, True, n < 3], boundary=boundary("frequency", 3, n))
    for n in [5, 6, 7]:
        b.add(f"sent_lt_{n}", 1268, [0], sentences(n), [n < 6], boundary=boundary("num_sentences", 6, n))
    for n in [4, 5, 6]:
        b.add(f"sent_ge_{n}", 2035, [2], sentences(n), [False, False, n >= 5], boundary=boundary("num_sentences", 5, n))
    for n in [19, 20, 21]:
        edge = boundary("num_words", 20, n)
        if n == 20:
            b.promote("comma_boundary_spaced", 0, edge)
        else:
            b.add(f"words_lt_{n}", 3442, [0], "<<제목>> " + words(n - 1), [n < 20, True], boundary=edge)
    for n in [599, 600, 601]:
        b.add(f"words_ge_{n}", 3538, [1], "폭탄 " + words(n - 1), [True, n >= 600], boundary=boundary("num_words", 600, n))
    for n in [2, 3, 4]:
        b.add(f"placeholders_{n}", 3743, [0], " ".join(["[항목]"] * n), [n >= 3], boundary=boundary("num_placeholders", 3, n))
    for n in [8, 9, 10]:
        edge = boundary("num_bullets", 9, n)
        if n == 9:
            b.promote("markdown_star_balanced_136", 0, edge)
        else:
            text = "\n\n" + "\n".join(["- 항목"] * n) + "\n\n"
            b.add(f"bullets_{n}", 136, [0], text, [False, True], boundary=edge)
    for n in [1, 2, 3]:
        text = " ".join(["**강조**" if n == 3 else "*강조*"] * n)
        b.add(f"highlights_{n}", 3710, [0], text, [n >= 2, False, False], boundary=boundary("num_highlights", 2, n))
    for n in [3, 4, 5]:
        text = " ".join(f"섹션 {i} 내용" for i in range(1, n + 1))
        b.add(f"sections_{n}", 1127, [0], text, [n >= 4, False], boundary=boundary("num_sections", 4, n))
    for n in [1, 2, 3]:
        b.add(f"paragraphs_{n}", 1082, [0], "***".join(["내용"] * n), [n == 2], boundary=boundary("num_paragraphs", 2, n))
    for n in [3, 4, 5]:
        edge = boundary("num_paragraphs", 4, n)
        if n == 4:
            b.promote("nfc_dataset_first_word_nfc", 0, edge)
        else:
            text = "\n\n".join(["회사 내용"] + ["다음"] * (n - 1))
            b.add(f"nth_paragraphs_{n}", 3073, [0], text, [False], [n == 5], boundary=edge)
    for n in [1, 2, 3]:
        text = "******".join(["첫,농담" if n == 3 else "첫 농담", "둘 농담", "셋 농담"][:n])
        b.add(f"two_responses_{n}", 1107, [0, 1] if n != 2 else [1], text, [n != 3, n == 2])
        b.target(b.cases[-1], 1, boundary("num_responses", 2, n))
    for key, marker in [(3710, "P.P.S"), (1800, "P.S.")]:
        index = 2 if key == 3710 else 0
        for ok in [True, False]:
            flags = [False, False, ok] if key == 3710 else [ok]
            b.add("postscript_" + marker + ("_T" if ok else "_F"), key, [index], "본문 " + marker + " 후기" if ok else "본문", flags)
    b.add("constrained_T", 3750, [0], "제 답변은 예입니다.", [True])
    b.add("constrained_F", 3750, [0], "답변입니다.", [False])
    b.add("json_existence_T", 3518, [0, 1], '```json\n{"보상":"이민자"}\n```', [True, True])
    b.add("json_existence_F", 3518, [0, 1], "보상", [False, False])
    b.promote("comma_boundary_compact", 1)
    b.promote("comma_compact", 1)
    b.add("forbidden_T", 3445, [0], "컴퓨터를", [True])
    b.add("forbidden_F", 3445, [0], "컴퓨터", [False])
    b.add("language_ko_T", 3311, [0], KO_TEXT, [True, False, True])
    b.add("language_ko_F", 3311, [0], EN_TEXT, [False, False, False])
    b.promote("nfc_dataset_end_checker_nfc", 1)
    b.add("end_F", 1127, [1], "끝", [False, False])
    b.add("quotation_T", 122, [0], '"내용"', [True])
    b.add("quotation_F", 122, [0], "내용", [False])
    query = b.ko[3563]["kwargs"][0]["prompt_to_repeat"]
    b.add("repeat_T", 3563, [0], query + " 이언 매켈런입니다.", [True])
    b.add("repeat_F", 3563, [0], "이언 매켈런입니다.", [False])
    for x, y in [(8, 10), (8, 9), (7, 10), (7, 9)]:
        b.add(f"repeat_id_{x}_{y}", 1203, [0, 1], words(x, "전쟁") + " " + words(y, "peace"), [x >= 8, y >= 10], group="diagnostic")
    b.add("predatory_ko", 2142, [0], words(2, "포식자"), [False], group="diagnostic")
    b.add("predatory_literal", 2142, [0], words(2, "predatory"), [True], group="diagnostic")
    b.add("sent_lt_6_multiline", 1268, [0], sentences(6, True), [False], [True], group="diagnostic")
    b.add("characters_600_not_words", 3538, [0, 1], "폭탄" + "가" * 600, [True, False], group="diagnostic")
    b.add("last_paragraph_T", 1954, [0], "\n\n".join(["내용"] * 6 + ["요약 내용"]), [True], group="diagnostic")
    b.add("last_paragraph_F", 1954, [0], "\n\n".join(["요약 내용"] + ["내용"] * 6), [False], group="diagnostic")
    b.add("bullets_10_unpadded", 136, [0], "\n".join(["- 항목"] * 10), [False, True], [True, True], group="diagnostic")
    b.add("constrained_multi", 3750, [0], "제 답변은 예입니다. 제 답변은 아니요입니다.", [True], group="diagnostic")
    b.add("language_empty", 3311, [0], "", [False, False, False], group="language_engine")
    b.add("language_short_exception", 3311, [0], "123", [True, False, False], group="language_engine")
    b.add("language_ru_T", 240, [0], RU_TEXT, [True], group="language_engine")
    b.add("language_ru_F", 240, [0], KO_TEXT, [False], group="language_engine")
    b.add("selected_1262_smoke", 1262, [0, 1], "<<제목>> " + sentences(4), [True, True], group="selection_smoke")

    for label, value in [("null", None), ("zero", 0), ("empty_string", ""), ("empty_list", [])]:
        b.auxiliary("filter_" + label, "length_constraints:number_words", {"num_words": value, "relation": "less than"}, "평가", True)
    for label, kwargs in [("absent", {}), ("null", {"keywords": None}), ("empty_string", {"keywords": ""}), ("empty_list", {"keywords": []})]:
        b.auxiliary("keyword_" + label, "keywords:existence", kwargs, "평가", error="ValueError")
    b.auxiliary("bad_relation", "length_constraints:number_words", {"num_words": 2, "relation": "invalid"}, "평가", error="ValueError")
    for text, ok in [("a", False), ("aa", True)]:
        b.auxiliary("letter_" + text, "keywords:letter_frequency", {"letter": "a", "let_frequency": 2, "let_relation": "at least"}, text, ok, group="registry_unused")
    for suffix, text, ok in [("T", "THIS IS A CLEAR ENGLISH SENTENCE ABOUT SCIENCE AND NATURE.", True),
                             ("F", "This is a clear English sentence about science and nature.", False)]:
        b.auxiliary("capital_" + suffix, "change_case:english_capital", {}, text, ok, group="registry_unused")
    for suffix, text, ok in [("T", "this is a clear english sentence about science and nature.", True),
                             ("F", "This is a clear English sentence about science and nature.", False)]:
        b.auxiliary("lowercase_" + suffix, "change_case:english_lowercase", {}, text, ok, group="registry_unused")
    for text in ["HELLO", "hello"]:
        b.auxiliary("capital_words_" + text, "change_case:capital_word_frequency", {"capital_frequency": 1, "capital_relation": "at least"}, text, error="AttributeError", group="registry_unused")
    b.auxiliary("unregistered", "keywords:key_sentences", {"key_sentences": ["평가합니다."], "num_sentences": 1}, "평가합니다.", error="KeyError", group="unregistered")

    validate_cases(b.cases)
    validate_cases(b.support, require_expected=False)
    for case in b.cases:
        validate_source_row(case, b.ko)
    assert len(b.cases) == 156 and len(b.support) == 18
    assert len({c["hashes"]["cache_key"] for c in b.cases}) == 156, "Duplicate response record"
    selected = read_json(ROOT.parent / "sample-coverage/selection.json")["keys"]
    source_keys = sorted({c["key"] for c in b.cases if c["key"] is not None})
    assert set(selected) <= set(source_keys) and len(source_keys) == 32
    output_dir = Path(output_dir)
    write_json(output_dir / "cases.json", b.cases)
    write_json(output_dir / "support_cases.json", b.support)
    write_json(output_dir / "source_rows.json", [b.ko[k] for k in source_keys])
    manifest = {
        "schema_version": 2, "scope": "original English evaluator vs original Ko evaluator on identical Ko inputs",
        "source_revisions": {n: e["revision"] for n, e in b.provenance.items()}, "verified_sources": b.verified,
        "baseline_sha256": sha((ROOT / "baseline.json").read_bytes()), "baseline_cases_lf_sha256": b.legacy_lf_hash,
        "baseline_original_results_object_sha256": object_hash(baseline_run("original")),
        "baseline_ko_results_object_sha256": object_hash(baseline_run("ko")),
        "cases_sha256": sha((output_dir / "cases.json").read_bytes()),
        "support_cases_sha256": sha((output_dir / "support_cases.json").read_bytes()),
        "source_rows_sha256": sha((output_dir / "source_rows.json").read_bytes()),
        "builder_sha256": sha(Path(__file__).read_bytes()), "normal_cases": 156, "support_cases": 18,
        "normal_scope_counts": dict(Counter(c["scope"] for c in b.cases)),
        "extension_groups": dict(Counter(c["group"] for c in b.cases if c["origin"] == "extension_70")),
        "normal_full_instruction_occurrences": sum(len(c["ko_instruction_id_list"]) for c in b.cases),
        "source_keys": source_keys, "source_instructions": sum(len(b.ko[k]["kwargs"]) for k in source_keys),
        "integration_selection_keys": selected, "integration_selection_changed": False,
        "model_inference_run": False, "new_lighteval_ko_parity_run": False,
        "count_formula": "86 + (25*2 + 13 - 4 shared slots - 6 reused responses) + 1 selection smoke + 12 diagnostics + 4 language = 156; support=18",
    }
    write_json(output_dir / "manifest.json", manifest)
    print(json.dumps({k: manifest[k] for k in ["normal_cases", "support_cases", "normal_scope_counts", "extension_groups", "normal_full_instruction_occurrences"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    options = parser.parse_args()
    build(options.source_root, options.output_dir)
