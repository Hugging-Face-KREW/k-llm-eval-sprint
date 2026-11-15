"""Negative controls for evidence integrity and the observed scoring contract."""
import copy
import unittest

from case_utils import (ROOT, baseline_run, input_hashes, instruction_index, read_json,
                        validate_case, validate_cases, validate_source_row)
from compare import (metric_counts, verify_phase, verify_record, verify_reproduction,
                     verify_support_cases, verify_support_record)


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = read_json(ROOT / "cases.json")
        cls.inputs = {c["case_id"]: c for c in cls.cases}
        cls.results = {r["case_id"]: r for r in read_json(ROOT / "ko_results.json")["results"]}
        cls.rows = {r["key"]: r for r in read_json(ROOT / "source_rows.json")}
        cls.support_cases = read_json(ROOT / "support_cases.json")
        cls.support_inputs = {c["case_id"]: c for c in cls.support_cases}
        cls.support_runs = {side: read_json(ROOT / ("support_" + side + "_results.json")) for side in ["original", "ko"]}
        cls.support_results = {side: {r["case_id"]: r for r in run["results"]} for side, run in cls.support_runs.items()}

    def test_repeated_id_requires_index(self):
        ids = ["keywords:frequency", "keywords:frequency"]
        with self.assertRaises(ValueError):
            instruction_index(ids, ids[0])
        self.assertEqual(instruction_index(ids, ids[1], 1), 1)

    def test_index_cannot_select_another_id_or_python_bool(self):
        ids = ["keywords:frequency", "startend:end_checker"]
        for index in [1, -1, 2, True]:
            with self.subTest(index=index), self.assertRaises(ValueError):
                instruction_index(ids, ids[0], index)

    def test_duplicate_case_id_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_cases([self.cases[0], copy.deepcopy(self.cases[0])])

    def test_source_edit_is_rejected_even_with_new_hash(self):
        c = copy.deepcopy(self.inputs["expanded_predatory_literal"])
        c["ko_all_kwargs"][0]["keyword"] = "포식자"
        c["ko_kwargs"]["keyword"] = "포식자"
        c["hashes"] = input_hashes(c)
        with self.assertRaises(ValueError):
            validate_source_row(c, self.rows)

    def test_stale_response_hash_is_rejected(self):
        c = copy.deepcopy(self.cases[0])
        c["test_response_ko"] += " changed"
        with self.assertRaises(ValueError):
            validate_case(c)

    def test_same_key_variants_have_distinct_cache_keys(self):
        cases = [c for c in self.cases if c["key"] == 1203]
        self.assertEqual(len(cases), 4)
        self.assertEqual(len({c["hashes"]["cache_key"] for c in cases}), 4)

    def test_predeclared_oracle_is_not_replaced_by_observation(self):
        c = copy.deepcopy(self.inputs["expanded_predatory_literal"])
        c["expected_ko"]["full"]["strict"] = [False]
        c["expected_ko"]["prompt"]["strict"] = False
        with self.assertRaisesRegex(AssertionError, "oracle"):
            verify_record(c, self.results[c["case_id"]], "ko")

    def test_second_repeated_id_cannot_be_collapsed_to_first(self):
        name = "expanded_repeat_id_8_9"
        r = copy.deepcopy(self.results[name])
        r["isolated_targets"][1]["instruction_index"] = 0
        with self.assertRaises(AssertionError):
            verify_record(self.inputs[name], r, "ko")

    def test_ko_schedule_cannot_be_interleaved(self):
        name = "expanded_json_existence_T"
        r = copy.deepcopy(self.results[name])
        r["phase_schedule"][1] = "isolated[0].strict"
        with self.assertRaisesRegex(AssertionError, "phase order"):
            verify_record(self.inputs[name], r, "ko")

    def test_checker_objects_cannot_be_shared_between_phases(self):
        name = "expanded_json_existence_T"
        r = copy.deepcopy(self.results[name])
        for field in ["checker_build_trace", "checker_creation_trace", "checker_call_trace"]:
            for event in r["full"]["loose"][field]:
                event["instance"] = event["instance"].replace("loose", "strict")
        with self.assertRaisesRegex(AssertionError, "shared across phases"):
            verify_record(self.inputs[name], r, "ko")

    def test_loose_empty_candidates_and_duplicates_cannot_be_dropped(self):
        name = "expanded_language_empty"
        r = copy.deepcopy(self.results[name])
        self.assertEqual(r["full"]["loose"]["loose_candidates_from_evaluator"], [""] * 8)
        self.assertEqual(r["full"]["loose"]["checker_call_trace"], [])
        r["full"]["loose"]["loose_candidates_from_evaluator"].pop()
        with self.assertRaisesRegex(AssertionError, "candidate order/duplicates"):
            verify_record(self.inputs[name], r, "ko")

    def test_loose_cannot_require_one_joint_success_candidate(self):
        name = "markdown_star_balanced_136"
        r = self.results[name]
        self.assertTrue(r["full"]["loose"]["prompt_result"])
        self.assertFalse(any(x["prompt_result"] for x in r["strict_on_actual_loose_candidates"]))
        broken = copy.deepcopy(r)
        broken["full"]["loose"]["instruction_results"][1] = False
        broken["full"]["loose"]["prompt_result"] = False
        with self.assertRaises(AssertionError):
            verify_record(self.inputs[name], broken, "ko")

    def test_exception_cannot_be_counted_as_a_normal_false_or_true(self):
        with self.assertRaisesRegex(AssertionError, "scoring error"):
            verify_phase({"error": {"type": "AttributeError"}, "instruction_results": [True]}, ["x"], [{}], "text", "strict", "negative-control")

    def test_uneven_instruction_aggregation(self):
        records = [{"full": {kind: {"instruction_results": flags} for kind in ["strict", "loose"]}}
                   for flags in [[True, True, True], [False]]]
        counts = metric_counts(records)
        self.assertEqual(counts["prompt_strict"]["value"], 0.5)
        self.assertEqual(counts["instruction_strict"]["value"], 0.75)

    def test_falsey_kwargs_reach_original_random_fallback(self):
        cases = read_json(ROOT / "support_ko_results.json")["results"]
        cases = [r for r in cases if r["case_id"].startswith("support_filter_")]
        self.assertEqual(len(cases), 4)
        built = []
        for result in cases:
            args = []
            for kind in ["strict", "loose"]:
                event = result["full"][kind]["checker_build_trace"][0]
                self.assertEqual(event["filtered_kwargs"], {"relation": "less than"})
                self.assertGreater(event["built_args"]["num_words"], 0)
                args.append(event["built_args"]["num_words"])
            built.append(args)
        self.assertTrue(all(args == built[0] for args in built))

    def test_trace_keeps_call_input_before_checker_lowercases_it(self):
        name = "expanded_postscript_P.P.S_T"
        trace = next(t for t in self.results[name]["full"]["strict"]["checker_call_trace"] if t["instruction_index"] == 2)
        self.assertEqual(trace["value"], self.inputs[name]["test_response_ko"])
        self.assertNotEqual(trace["value"], trace["checker_local_value"])

    def test_retained_reproduction_is_embedded_and_must_match(self):
        case = self.cases[0]
        archived = {r["case_id"]: r for r in baseline_run("ko")["results"]}
        record = copy.deepcopy(self.results[case["case_id"]])
        verify_reproduction(case, record, archived)
        record.pop("baseline_reproduction")
        with self.assertRaisesRegex(AssertionError, "missing integrated reproduction"):
            verify_reproduction(case, record, archived)
        record = copy.deepcopy(self.results[case["case_id"]])
        record["baseline_reproduction"]["result"]["full"]["strict"]["instruction_results"][0] = True
        with self.assertRaisesRegex(AssertionError, "differs from archived"):
            verify_reproduction(case, record, archived)

    def test_new_case_cannot_inflate_retained_reproduction_count(self):
        name = "expanded_predatory_literal"
        case, record = self.inputs[name], copy.deepcopy(self.results[name])
        record["baseline_reproduction"] = {"input_contract": "archived_language_specific", "result": {}}
        with self.assertRaisesRegex(AssertionError, "new case"):
            verify_reproduction(case, record, {})

    def test_all_english_support_results_cannot_be_replaced_by_exceptions(self):
        broken = copy.deepcopy(self.support_runs)
        for result in broken["original"]["results"]:
            for kind in ["strict", "loose"]:
                result["full"][kind] = {"error": {"type": "UnexpectedSupportError"}}
        with self.assertRaisesRegex(AssertionError, "scoring error|exception"):
            verify_support_cases(self.support_cases, broken)

    def test_support_normal_return_cannot_become_exception(self):
        for side in ["original", "ko"]:
            for case in self.support_cases:
                if "error_type" in case["expected_" + side]:
                    continue
                for kind in ["strict", "loose"]:
                    for stage in ["full", "isolated"]:
                        with self.subTest(side=side, case=case["case_id"], kind=kind, stage=stage):
                            result = copy.deepcopy(self.support_results[side][case["case_id"]])
                            out = result["full"][kind] if stage == "full" else result["isolated_targets"][0][kind]
                            out.clear()
                            out["error"] = {"type": "UnexpectedSupportError"}
                            with self.assertRaisesRegex(AssertionError, "scoring error"):
                                verify_support_record(case, result, side)

    def test_support_expected_exception_cannot_be_normal_or_another_type(self):
        for side in ["original", "ko"]:
            for case in self.support_cases:
                if "error_type" not in case["expected_" + side]:
                    continue
                for kind in ["strict", "loose"]:
                    for stage in ["full", "isolated"]:
                        for substitute in [{"instruction_results": [False], "prompt_result": False}, {"error": {"type": "UnexpectedSupportError"}}]:
                            with self.subTest(side=side, case=case["case_id"], kind=kind, stage=stage, substitute=substitute):
                                result = copy.deepcopy(self.support_results[side][case["case_id"]])
                                out = result["full"][kind] if stage == "full" else result["isolated_targets"][0][kind]
                                out.clear()
                                out.update(copy.deepcopy(substitute))
                                with self.assertRaisesRegex(AssertionError, "exception not preserved"):
                                    verify_support_record(case, result, side)

    def test_support_boolean_corruption_cannot_hide_in_a_consistent_trace(self):
        name = "support_letter_a"
        for side in ["original", "ko"]:
            for kind in ["strict", "loose"]:
                for stage in ["full", "isolated"]:
                    with self.subTest(side=side, kind=kind, stage=stage):
                        case = self.support_inputs[name]
                        result = copy.deepcopy(self.support_results[side][name])
                        out = result["full"][kind] if stage == "full" else result["isolated_targets"][0][kind]
                        self.assertEqual(out["instruction_results"], [False])
                        out["instruction_results"] = [True]
                        out["prompt_result"] = True
                        out["checker_call_trace"][-1]["result"] = True
                        # A coherent trace alone must not replace the source oracle.
                        with self.assertRaisesRegex(AssertionError, "oracle mismatch"):
                            verify_support_record(case, result, side)

    def test_support_requires_independent_oracles_for_both_references(self):
        name = "support_keyword_absent"
        for side in ["original", "ko"]:
            case = copy.deepcopy(self.support_inputs[name])
            case.pop("expected_" + side)
            with self.subTest(side=side), self.assertRaisesRegex(AssertionError, "Missing support oracle"):
                verify_support_record(case, self.support_results[side][name], side)
        case = copy.deepcopy(self.support_inputs[name])
        case["expected_original"] = copy.deepcopy(case["expected_ko"])
        case["expected_original"]["source_revision"] = case["source_revisions"]["harness"]
        with self.assertRaisesRegex(AssertionError, "exception not preserved"):
            verify_support_record(case, self.support_results["original"][name], "original")

    def test_support_missing_or_reordered_english_results_are_rejected(self):
        for change in ["missing", "reordered"]:
            broken = copy.deepcopy(self.support_runs)
            if change == "missing":
                broken["original"]["results"].pop()
            else:
                broken["original"]["results"].reverse()
            with self.subTest(change=change), self.assertRaisesRegex(AssertionError, "Missing/reordered original"):
                verify_support_cases(self.support_cases, broken)

    def test_support_expected_flags_and_prompt_must_be_booleans(self):
        name = "support_filter_null"
        for side in ["original", "ko"]:
            for kind in ["strict", "loose"]:
                for field in ["full", "prompt"]:
                    case = copy.deepcopy(self.support_inputs[name])
                    case["expected_" + side][field][kind] = [1] if field == "full" else 1
                    with self.subTest(side=side, kind=kind, field=field), self.assertRaises(AssertionError):
                        verify_support_record(case, self.support_results[side][name], side)


if __name__ == "__main__":
    unittest.main(verbosity=2)
