"""Import upstream code; collect decisions and trace actual checker calls.

No checker or loose transformation is implemented in this module. Full package
import is the default. The explicit isolated-source mode is a documented fallback.
"""
import argparse
import dataclasses
import hashlib
import importlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import platform
import random
import re
import sys
import types
import unicodedata
from case_utils import instruction_index

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = Path(os.environ.get("IFEVAL_AUDIT_SOURCE_ROOT", str(ROOT))).resolve()
os.environ.setdefault("NLTK_DATA", str(SOURCE_ROOT / ".cache/nltk_data"))
os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def location(obj):
    path = Path(inspect.getsourcefile(obj)).resolve()
    return {"path": str(path.relative_to(SOURCE_ROOT)), "line": inspect.getsourcelines(obj)[1],
            "function": obj.__qualname__}


def load_modules(side, mode):
    if mode == "full-package":
        import lm_eval
        import lm_eval.tasks
        # Ko's own README recommends placing ifeval_ko under lm_eval/tasks.
        # Extending the existing package search path accomplishes that without
        # copying over, editing, or replacing any upstream Python source.
        if side == "ko":
            lm_eval.tasks.__path__.append(str(SOURCE_ROOT / "sources/ko"))
    else:
        # Explicit fallback only: bypass top-level task-manager dependencies,
        # retaining the exact source modules and their original imports.
        for name, path in [("lm_eval", SOURCE_ROOT / "sources/harness/lm_eval"),
                           ("lm_eval.tasks", SOURCE_ROOT / "sources/harness/lm_eval/tasks")]:
            package = types.ModuleType(name)
            package.__path__ = [str(path)]
            sys.modules[name] = package
        if side == "ko":
            sys.modules["lm_eval.tasks"].__path__.append(str(SOURCE_ROOT / "sources/ko"))
    prefix = "lm_eval.tasks.ifeval" if side == "original" else "lm_eval.tasks.ifeval_ko"
    return {name: importlib.import_module(prefix + "." + name)
            for name in ["utils", "instructions", "instructions_registry", "instructions_util"]}


def make_instruction(modules, iid, kwargs, prompt):
    instruction = modules["instructions_registry"].INSTRUCTION_DICT[iid](iid)
    instruction.build_description(**{k: v for k, v in kwargs.items() if v})
    args = instruction.get_instruction_args()
    if args and "prompt" in args:
        instruction.build_description(prompt=prompt)
    return instruction


def diagnostic(modules, instruction, text):
    util = modules["instructions_util"]
    args = instruction.get_instruction_args() or {}
    result = {"text": text, "checker_result": bool(instruction.check_following(text)),
              "built_args": args}
    iid = instruction.id
    if iid == "length_constraints:number_words":
        result["count"] = util.count_words(text)
        if "nltk" in vars(util):
            result["tokens"] = util.nltk.tokenize.RegexpTokenizer(r"\w+").tokenize(text)
        else:
            result["tokens"] = text.split()
    elif iid == "length_constraints:number_sentences":
        if hasattr(util, "_get_sentence_tokenizer"):
            result["sentences"] = util._get_sentence_tokenizer().tokenize(text)
        else:
            result["sentences"] = util.split_into_sentences(text)
        result["count"] = util.count_sentences(text)
    elif iid == "keywords:frequency":
        result["pattern"] = args["keyword"]
        result["matches"] = re.findall(args["keyword"], text, flags=re.IGNORECASE)
        result["count"] = len(result["matches"])
    elif iid in {"keywords:existence", "keywords:forbidden_words"}:
        forbidden = iid == "keywords:forbidden_words"
        words = args["forbidden_words" if forbidden else "keywords"]
        result["matches"] = {word: bool(re.search(r"\b" + word + r"\b" if forbidden else word,
                                                  text, flags=re.IGNORECASE)) for word in words}
    return result


def traced_eval(fn, inp, response):
    calls = []
    candidates = []
    def profile(frame, event, arg):
        if event == "return" and frame.f_code is fn.__code__ and "all_responses" in frame.f_locals:
            candidates.extend(frame.f_locals["all_responses"])
        if event == "return" and frame.f_code.co_name == "check_following":
            instruction = frame.f_locals.get("self")
            if instruction is not None and hasattr(instruction, "id"):
                calls.append({"instruction_id": instruction.id,
                              "value": frame.f_locals.get("value"), "result": bool(arg)})
    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        output = fn(inp, response)
    finally:
        sys.setprofile(previous)
    return {"instruction_results": output.follow_instruction_list,
            "prompt_result": output.follow_all_instructions,
            "evaluated_response": output.response, "checker_call_trace": calls,
            "loose_candidates_from_evaluator": candidates}


def evaluate_case(modules, case, side):
    utils = modules["utils"]
    iid = case["instruction_id"]
    ids = case[side + "_instruction_id_list"]
    kwargs = case.get(side + "_eval_all_kwargs", case[side + "_all_kwargs"])
    prompt = case[side + "_prompt"]
    response = case["test_response_" + side]
    inp = utils.InputExample(key=case["key"] if case["key"] is not None else -1,
                             instruction_id_list=ids, prompt=prompt, kwargs=kwargs)
    index = instruction_index(ids, iid, case.get("instruction_index"))
    isolated = utils.InputExample(key=inp.key, instruction_id_list=[iid], prompt=prompt,
                                  kwargs=[kwargs[index]])
    random.seed(0)
    instruction = make_instruction(modules, iid, kwargs[index], prompt)
    result = {"case_id": case["case_id"], "instruction_index": index,
              "effective_kwargs": kwargs[index],
              "full": {"strict": traced_eval(utils.test_instruction_following_strict, inp, response),
                       "loose": traced_eval(utils.test_instruction_following_loose, inp, response)},
              "isolated": {"strict": traced_eval(utils.test_instruction_following_strict, isolated, response),
                           "loose": traced_eval(utils.test_instruction_following_loose, isolated, response)},
              "diagnostics": {"raw": diagnostic(modules, instruction, response),
                              "nfc": diagnostic(modules, instruction, unicodedata.normalize("NFC", response))},
              "source": {"build_description": location(type(instruction).build_description),
                         "check_following": location(type(instruction).check_following)}}
    if iid in {"length_constraints:number_words", "length_constraints:number_sentences"}:
        name = "count_words" if iid.endswith("number_words") else "count_sentences"
        result["source"][name] = location(getattr(modules["instructions_util"], name))
        counter = getattr(modules["instructions_util"], name)
        for trace in result["isolated"]["loose"]["checker_call_trace"]:
            trace["count"] = counter(trace["value"])
    if case["group"].startswith("nfc"):
        result["unicode_response"] = {
            "raw_codepoints": [f"U+{ord(c):04X}" for c in response],
            "nfc_codepoints": [f"U+{ord(c):04X}" for c in unicodedata.normalize("NFC", response)]}
        result["isolated_nfc_response"] = {
            kind: traced_eval(getattr(utils, "test_instruction_following_" + kind), isolated,
                              unicodedata.normalize("NFC", response)) for kind in ["strict", "loose"]}
        def normalize(value):
            if isinstance(value, str):
                return unicodedata.normalize("NFC", value)
            if isinstance(value, list):
                return [normalize(v) for v in value]
            if isinstance(value, dict):
                return {k: normalize(v) for k, v in value.items()}
            return value
        normalized_input = dataclasses.replace(isolated, prompt=normalize(isolated.prompt),
                                                kwargs=normalize(isolated.kwargs))
        result["isolated_nfc_both"] = {
            kind: traced_eval(getattr(utils, "test_instruction_following_" + kind), normalized_input,
                              unicodedata.normalize("NFC", response)) for kind in ["strict", "loose"]}
    if case["group"] == "markdown":
        # A separate control: run the actual strict evaluator on each candidate
        # produced by the actual loose evaluator. This does not define loose.
        result["strict_on_actual_loose_candidates"] = [
            traced_eval(utils.test_instruction_following_strict, inp, candidate)
            for candidate in result["full"]["loose"]["loose_candidates_from_evaluator"]]
    return result


def main(side):
    """Compatibility entry point for the single audit runner."""
    from run_audit import main as run_main
    return run_main(side)
