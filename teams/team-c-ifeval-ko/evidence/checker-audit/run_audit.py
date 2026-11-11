"""Run the 156-case audit, including the stored baseline checks."""
import argparse
import copy
import importlib.metadata
import inspect
import os
from pathlib import Path
import platform
import random
import sys
import unicodedata

from case_utils import (ROOT, baseline_cases, baseline_run, input_hashes, instruction_index, ko_input, object_hash,
                        read_json, sha, validate_cases, verify_sources, write_json)


class Trace:
    """Observe original frames without replacing a checker or loose transform."""
    def __init__(self):
        self.objects = {}  # Strong references prevent id reuse between phases.

    def evaluate(self, fn, inp, response, stage):
        calls, builds, creates, candidates = [], [], [], []
        call_inputs = {}

        def profile(frame, event, arg):
            if event == "call" and frame.f_code.co_name == "check_following":
                obj = frame.f_locals.get("self")
                if obj is not None and hasattr(obj, "id") and frame.f_back is not None and frame.f_back.f_code is fn.__code__:
                    call_inputs[id(frame)] = frame.f_locals.get("value")
                return
            if event != "return":
                return
            if frame.f_code is fn.__code__ and "all_responses" in frame.f_locals:
                candidates.extend(frame.f_locals["all_responses"])
            obj = frame.f_locals.get("self")
            parent = frame.f_back
            if obj is None or not hasattr(obj, "id") or parent is None or parent.f_code is not fn.__code__:
                return
            name = frame.f_code.co_name
            index = parent.f_locals.get("index")
            if name not in {"__init__", "build_description", "check_following"}:
                return
            if id(obj) not in self.objects:
                self.objects[id(obj)] = (obj, f"{stage}:{index}")
            token = self.objects[id(obj)][1]
            base = {"instruction_id": obj.id, "instruction_index": index, "instance": token}
            if name == "__init__":
                creates.append(base)
            elif name == "build_description":
                try:
                    args = copy.deepcopy(obj.get_instruction_args())
                except Exception as error:
                    args = {"get_args_error": type(error).__name__}
                builds.append({**base, "filtered_kwargs": copy.deepcopy(parent.f_locals.get("kwargs")), "built_args": args})
            else:
                counts = {k: frame.f_locals[k] for k in ["num_words", "num_sentences", "actual_occurrences", "num_placeholders", "num_bullet_lists", "num_highlights", "num_sections", "num_paragraphs"] if k in frame.f_locals}
                if "valid_responses" in frame.f_locals:
                    counts["num_responses"] = len(frame.f_locals["valid_responses"])
                calls.append({**base, "value": call_inputs.pop(id(frame)),
                              "checker_local_value": frame.f_locals.get("value"),
                              "result": bool(arg), "counts": counts})

        previous = sys.getprofile()
        output, error = None, None
        try:
            sys.setprofile(profile)
            output = fn(inp, response)
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
        finally:
            sys.setprofile(previous)
        result = {"checker_call_trace": calls, "checker_build_trace": builds,
                  "checker_creation_trace": creates, "loose_candidates_from_evaluator": candidates}
        if error is not None:
            result["error"] = error
        else:
            result.update(instruction_results=output.follow_instruction_list,
                          prompt_result=output.follow_all_instructions, evaluated_response=output.response)
        return result


def evaluate(modules, runtime, case):
    u = modules["utils"]
    raw = ko_input(case)
    response = case["test_response_ko"]
    inp = u.InputExample(key=raw["key"] if raw["key"] is not None else -1, prompt=raw["prompt"],
                         instruction_id_list=raw["instruction_id_list"], kwargs=raw["kwargs"])
    tracer = Trace()
    random.seed(0)
    result = {"case_id": case["case_id"], "instruction_index": case["instruction_index"],
              "effective_kwargs": raw["kwargs"][case["instruction_index"]],
              "input_sha256": input_hashes(case)["input_sha256"],
              "response_sha256": sha(response.encode("utf-8")),
              "nfc_response_sha256": sha(unicodedata.normalize("NFC", response).encode("utf-8")),
              "cache_key": case["hashes"]["cache_key"],
              "evaluated_input": raw,
              "input_origin": "identical case.ko_* and test_response_ko; original_* are archival metadata",
              "full": {}, "isolated_targets": [], "phase_schedule": []}
    for kind in ["strict", "loose"]:
        result["phase_schedule"].append("full." + kind)
        result["full"][kind] = tracer.evaluate(getattr(u, "test_instruction_following_" + kind), inp, response, "full." + kind)
    for target in case["targets"]:
        i = instruction_index(raw["instruction_id_list"], target["instruction_id"], target["instruction_index"])
        isolated = u.InputExample(key=inp.key, prompt=inp.prompt, instruction_id_list=[raw["instruction_id_list"][i]], kwargs=[raw["kwargs"][i]])
        row = {"instruction_id": target["instruction_id"], "instruction_index": i}
        random.seed(0)
        for kind in ["strict", "loose"]:
            stage = f"isolated[{i}].{kind}"
            result["phase_schedule"].append(stage)
            row[kind] = tracer.evaluate(getattr(u, "test_instruction_following_" + kind), isolated, response, stage)
        result["isolated_targets"].append(row)
    primary = next(t for t in result["isolated_targets"] if t["instruction_index"] == case["instruction_index"])
    result["isolated"] = {kind: primary[kind] for kind in ["strict", "loose"]}

    # Diagnostics run AFTER scoring, with RNG state restored. They cannot alter
    # the reference's checker construction or fallback random draws.
    state = random.getstate()
    try:
        random.seed(0)
        inst = runtime.make_instruction(modules, case["instruction_id"], result["effective_kwargs"], inp.prompt)
        result["diagnostics"] = {"raw": runtime.diagnostic(modules, inst, response),
                                 "nfc": runtime.diagnostic(modules, inst, unicodedata.normalize("NFC", response))}
        result["source"] = {name: runtime.location(getattr(type(inst), name)) for name in ["build_description", "check_following"]}
    except Exception as error:
        result["diagnostic_error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        random.setstate(state)
    if case["group"] == "markdown":
        result["strict_on_actual_loose_candidates"] = [
            runtime.traced_eval(u.test_instruction_following_strict, inp, candidate)
            for candidate in result["full"]["loose"]["loose_candidates_from_evaluator"]]
    return result


def environment(side, source_root, mode, modules, input_path, verified):
    import nltk
    nltk_path = Path(str(nltk.data.find("tokenizers/punkt_tab/english")))
    return {"side": side, "python": sys.version, "platform": platform.platform(), "executable": sys.executable,
            "import_mode": mode, "command": [sys.executable] + sys.argv,
            "source_root": str(source_root), "module_paths": {n: str(Path(m.__file__).resolve()) for n, m in modules.items()},
            "module_sha256": {n: sha(Path(m.__file__).read_bytes()) for n, m in modules.items()},
            "package_versions": {n: importlib.metadata.version(n) for n in ["nltk", "langdetect", "immutabledict", "packaging", "pyarrow"]},
            "nltk_resource_sha256": {str(Path("tokenizers/punkt_tab/english") / p.name): sha(p.read_bytes()) for p in sorted(nltk_path.iterdir()) if p.is_file()},
            "verified_sources": verified, "cases_sha256": sha(input_path.read_bytes()),
            "runtime_sha256": sha((ROOT / "audit_runtime.py").read_bytes()),
            "runner_sha256": sha(Path(__file__).read_bytes()),
            "random_seed": 0, "langdetect_seed": 0, "model_inference_run": False, "new_lighteval_ko_parity_run": False}


def main(side=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--side", choices=["original", "ko"], default=side, required=side is None)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    parser.add_argument("--import-mode", choices=["full-package", "isolated-source"], default="full-package")
    parser.add_argument("--suite", choices=["normal", "support", "all"], default="all")
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    os.environ["IFEVAL_AUDIT_SOURCE_ROOT"] = str(source_root)
    os.environ["NLTK_DATA"] = str(source_root / ".cache/nltk_data")
    from langdetect import DetectorFactory
    DetectorFactory.seed = 0
    import audit_runtime as runtime
    runtime.SOURCE_ROOT = source_root
    provenance, verified = verify_sources(source_root)
    modules = runtime.load_modules(args.side, args.import_mode)
    expected = provenance["ko" if args.side == "ko" else "harness"]["files"]
    prefix = "ifeval_ko/" if args.side == "ko" else "lm_eval/tasks/ifeval/"
    for name, module in modules.items():
        if sha(Path(module.__file__).read_bytes()) != expected[prefix + name + ".py"]["sha256"]:
            raise ValueError("Imported evaluator differs from the pinned source")
    suites = ["normal", "support"] if args.suite == "all" else [args.suite]
    for suite in suites:
        path = args.output_dir / ("cases.json" if suite == "normal" else "support_cases.json")
        cases = read_json(path)
        validate_cases(cases, require_expected=suite == "normal")
        results = [evaluate(modules, runtime, case) for case in cases]
        metadata = environment(args.side, source_root, args.import_mode, modules, path, verified)
        metadata["comparison_input"] = "identical_ko"
        document = {"environment": metadata, "results": results}
        if suite == "normal":
            retained = baseline_cases()
            replay = [runtime.evaluate_case(modules, case, args.side) for case in retained]
            archived = baseline_run(args.side)["results"]
            if replay != archived:
                raise ValueError("Retained-case reproduction differs from the archived oracle")
            by_id = {r["case_id"]: r for r in replay}
            if {c["case_id"] for c in cases if c["origin"] == "legacy_86"} != set(by_id):
                raise ValueError("The 86 reproduced cases must be retained in the 156-case experiment")
            for result in results:
                if result["case_id"] in by_id:
                    result["baseline_reproduction"] = {
                        "input_contract": "archived_language_specific",
                        "result": by_id[result["case_id"]],
                    }
            document["reproduction"] = {
                "retained_cases": len(replay), "exact_result_rows_matched": len(replay),
                "environment": environment(args.side, source_root, args.import_mode, modules, ROOT / "baseline.json", verified),
            }
        filename = ("support_" if suite == "support" else "") + args.side + "_results.json"
        write_json(args.output_dir / filename, document)
        phase_errors = sum("error" in r["full"][kind] for r in results for kind in ["strict", "loose"])
        reproduction_note = "; retained 86/86 reproduced in the same records" if suite == "normal" else ""
        print(f"{args.side}/{suite}: {len(results)} cases, {phase_errors} full-phase exceptions{reproduction_note} -> {filename}")
        if suite == "normal" and phase_errors:
            raise SystemExit("Unexpected normal-case scoring errors; see raw results")


if __name__ == "__main__":
    main()
