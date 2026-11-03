"""Verify explicit oracles and emit same-input English/Ko comparison evidence."""
import argparse
import ast
from collections import Counter, defaultdict
import copy
import importlib.util
import json
from pathlib import Path
import unicodedata

from case_utils import (ROOT, baseline_cases, baseline_cases_hash, baseline_run, read_baseline, input_hashes, ko_input, object_hash, partition, read_json,
                        sha, validate_cases, validate_source_row, verify_sources, write_json)

KINDS = ["strict", "loose"]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def tf(value):
    return "T" if value else "F"


def pair(a, b):
    return tf(a) + "," + tf(b)


def expected_candidates(response):
    lines = response.split("\n")
    first = "\n".join(lines[1:]).strip()
    last = "\n".join(lines[:-1]).strip()
    both = "\n".join(lines[1:-1]).strip()
    return [response, response.replace("*", ""), first, last, both,
            first.replace("*", ""), last.replace("*", ""), both.replace("*", "")]


def verify_phase(out, ids, kwargs, response, kind, label):
    require("error" not in out, f"Unexpected scoring error: {label}")
    flags = out["instruction_results"]
    require(len(flags) == len(ids) and all(type(x) is bool for x in flags), f"Invalid flags: {label}")
    require(out["prompt_result"] == all(flags), f"Prompt AND mismatch: {label}")
    require(out["evaluated_response"] == response, f"Wrong response preparation: {label}")
    builds, creates = out["checker_build_trace"], out["checker_creation_trace"]
    require([x["instruction_index"] for x in builds] == list(range(len(ids))), f"Build order: {label}")
    require([x["instruction_index"] for x in creates] == list(range(len(ids))), f"Creation order: {label}")
    for i, build in enumerate(builds):
        require(build["instruction_id"] == ids[i], f"Build index/ID: {label}")
        require(creates[i]["instance"] == build["instance"], f"Creation/build instance mismatch: {label}")
        require(build["filtered_kwargs"] == {k: v for k, v in kwargs[i].items() if v}, f"if-v filter changed: {label}")
    candidates = expected_candidates(response) if kind == "loose" else []
    require(out["loose_candidates_from_evaluator"] == candidates, f"Loose candidate order/duplicates: {label}")
    eligible = [r for r in candidates if r.strip()]
    for i, flag in enumerate(flags):
        calls = [x for x in out["checker_call_trace"] if x["instruction_index"] == i]
        require(all(c["instruction_id"] == ids[i] and c["instance"] == builds[i]["instance"] for c in calls), f"Checker reuse/index: {label}")
        require(all(c["value"].strip() for c in calls), f"Empty response reached checker: {label}")
        if kind == "strict":
            require(len(calls) == int(bool(response.strip())), f"Strict call count: {label}")
            require(not calls or calls[0]["value"] == response, f"Strict input: {label}")
        else:
            require([c["value"] for c in calls] == eligible[:len(calls)], f"Loose candidate call order: {label}")
            require(not any(c["result"] for c in calls[:-1]), f"Missing loose short circuit: {label}")
            require(flag or len(calls) == len(eligible), f"Loose failed without checking all nonempty candidates: {label}")
        require(flag == any(c["result"] for c in calls), f"Instruction OR mismatch: {label}")


def verify_record(case, result, side):
    label = side + "/" + case["case_id"]
    require(result["case_id"] == case["case_id"], f"Case order mismatch: {label}")
    require(result["evaluated_input"] == ko_input(case), f"Not identical Ko input: {label}")
    for key in ["input_sha256", "response_sha256", "cache_key"]:
        require(result[key] == case["hashes"][key], f"Stale {key}: {label}")
    raw_response = case["test_response_ko"]
    response = unicodedata.normalize("NFC", raw_response) if side == "ko" else raw_response
    ids = case["ko_instruction_id_list"]
    kwargs = ko_input(case)["kwargs"]
    require(result["phase_schedule"][:2] == ["full.strict", "full.loose"], f"Full phase order changed: {label}")
    for kind in KINDS:
        verify_phase(result["full"][kind], ids, kwargs, response, kind, label + "/full/" + kind)
    require(all(not s or l for s, l in zip(result["full"]["strict"]["instruction_results"], result["full"]["loose"]["instruction_results"])), f"Strict success lost in loose: {label}")
    instances = [{b["instance"] for b in result["full"][kind]["checker_build_trace"]} for kind in KINDS]
    require(instances[0].isdisjoint(instances[1]), f"Checker instance shared across phases: {label}")
    targets = result["isolated_targets"]
    require([t["instruction_index"] for t in targets] == [t["instruction_index"] for t in case["targets"]], f"Missing target: {label}")
    for target in targets:
        i = target["instruction_index"]
        require(target["instruction_id"] == ids[i], f"Isolated index/ID mismatch: {label}")
        for kind in KINDS:
            verify_phase(target[kind], [ids[i]], [kwargs[i]], response, kind, label + f"/isolated[{i}]/" + kind)
            require(target[kind]["instruction_results"][0] == result["full"][kind]["instruction_results"][i], f"Isolated/full mismatch: {label}/{i}/{kind}")
    if side == "ko":
        for kind in KINDS:
            require(result["full"][kind]["instruction_results"] == case["expected_ko"]["full"][kind], f"Predeclared Ko oracle mismatch: {label}/{kind}")


def metric_counts(results):
    counts = {}
    for kind in KINDS:
        flags = [r["full"][kind]["instruction_results"] for r in results]
        for level, numerator, denominator in [("prompt", sum(all(f) for f in flags), len(flags)),
                                               ("instruction", sum(sum(f) for f in flags), sum(map(len, flags)))]:
            counts[level + "_" + kind] = {"numerator": numerator, "denominator": denominator, "value": numerator / denominator}
    return counts


def verify_reproduction(case, record, archived):
    """The retained-case oracle belongs to its row in the experiment."""
    replay = record.get("baseline_reproduction")
    if case["origin"] == "legacy_86":
        require(replay is not None, "Retained case missing integrated reproduction")
        require(replay["input_contract"] == "archived_language_specific", "Reproduction input provenance was lost")
        require(replay["result"] == archived[case["case_id"]], "Integrated reproduction differs from archived result")
    else:
        require(replay is None, "A new case cannot be counted as an archived reproduction")


def verify_environment(run, cases_path, side, provenance):
    env = run["environment"]
    require(env["cases_sha256"] == sha(cases_path.read_bytes()), "Stale results input hash")
    require(env["runtime_sha256"] == sha((ROOT / "audit_runtime.py").read_bytes()), "Stale base runtime")
    require(env["runner_sha256"] == sha((ROOT / "run_audit.py").read_bytes()), "Stale audit runner")
    require(env["random_seed"] == 0 and env["langdetect_seed"] == 0, "Unrecorded seed")
    require(env["nltk_resource_sha256"] == read_json(ROOT / "nltk_resources.json")["sha256"], "NLTK resource drift")
    source = provenance["ko" if side == "ko" else "harness"]["files"]
    prefix = "ifeval_ko/" if side == "ko" else "lm_eval/tasks/ifeval/"
    require(all(h == source[prefix + n + ".py"]["sha256"] for n, h in env["module_sha256"].items()), "Wrong imported evaluator")


def metadata_coverage(source_root):
    spec = importlib.util.spec_from_file_location("metadata_coverage", ROOT.parent / "sample-coverage/audit_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    provenance = read_json(ROOT / "provenance.json")["ko"]
    blobs = {name: (source_root / info["local_path"]).read_bytes() for name, info in provenance["files"].items()}
    mapping, classes, constants = module.source_info(blobs)
    import pyarrow.parquet as pq
    rows = pq.read_table(source_root / "sources/ko/data/train-00000-of-00001.parquet").to_pylist()
    specs = {iid: module.inspect_checker(classes[mapping[iid]], constants) for row in rows for iid in row["instruction_id_list"]}
    ids, parts = module.summarize(rows, specs)
    require((len(rows), sum(ids.values()), len(ids), len(parts), len(mapping)) == (342, 481, 21, 25, 25), "Data/registry denominator changed")
    return rows, parts, specs


def verify_baseline():
    baseline = read_baseline()
    return baseline_cases_hash(baseline)


def legacy_coverage(cases, results):
    table = defaultdict(lambda: {"isolated_strict": Counter(), "isolated_loose": Counter(), "full_strict": Counter(), "full_loose": Counter()})
    for c, r in zip(cases, results):
        i = r["instruction_index"]
        kwargs = c.get("ko_eval_all_kwargs", c["ko_all_kwargs"])
        target_key = (c["instruction_id"], partition(c["instruction_id"], kwargs[i]))
        for kind in KINDS:
            table[target_key]["isolated_" + kind][tf(r["isolated"][kind]["instruction_results"][0])] += 1
            for iid, kw, flag in zip(c["ko_instruction_id_list"], kwargs, r["full"][kind]["instruction_results"]):
                table[iid, partition(iid, kw)]["full_" + kind][tf(flag)] += 1
    return [{"instruction_id": iid, "input_partition": part, **{n: dict(v) for n, v in stats.items()}} for (iid, part), stats in sorted(table.items())]


def verify(output_dir, source_root):
    provenance, verified_sources = verify_sources(source_root)
    manifest = read_json(output_dir / "manifest.json")
    require(manifest["builder_sha256"] == sha((ROOT / "build_cases.py").read_bytes()), "Stale builder manifest")
    require(verify_baseline() == manifest["baseline_cases_lf_sha256"], "Baseline input hash mismatch")
    for field, path in [("cases_sha256", output_dir / "cases.json"), ("support_cases_sha256", output_dir / "support_cases.json"),
                        ("source_rows_sha256", output_dir / "source_rows.json"), ("baseline_sha256", ROOT / "baseline.json")]:
        require(manifest[field] == sha(path.read_bytes()), f"Changed input: {field}")
    for side in ["original", "ko"]:
        require(manifest["baseline_" + side + "_results_object_sha256"] == object_hash(baseline_run(side)), "Baseline result hash mismatch")
    cases = read_json(output_dir / "cases.json")
    validate_cases(cases)
    require(len(cases) == 156, "Incomplete normal suite")
    runs = {side: read_json(output_dir / (side + "_results.json")) for side in ["original", "ko"]}
    rows, parts, specs = metadata_coverage(source_root)
    by_key = {r["key"]: r for r in rows}
    original_rows = {r["key"]: r for r in map(json.loads, (source_root / "sources/original_dataset/ifeval_input_data.jsonl").read_text().splitlines())}
    require(read_json(output_dir / "source_rows.json") == [by_key[k] for k in manifest["source_keys"]], "Source catalog changed")
    for c in cases:
        validate_source_row(c, by_key)
        require(c["source_revisions"] == {name: info["revision"] for name, info in provenance.items()}, "Case source revision mismatch")
        if c["key"] is not None:
            source = original_rows[c["key"]]
            require(all(c["original_" + field] == source[src] for field, src in [("prompt", "prompt"), ("instruction_id_list", "instruction_id_list"), ("all_kwargs", "kwargs")]), "Archival English source metadata changed")
    for side, run in runs.items():
        verify_environment(run, output_dir / "cases.json", side, provenance)
        require(run["environment"]["comparison_input"] == "identical_ko", "Mixed language-specific comparisons")
        require(len(run["results"]) == len(cases), "Missing scored cases")
        for c, r in zip(cases, run["results"]):
            verify_record(c, r, side)
    coverage = defaultdict(lambda: {"strict": Counter(), "loose": Counter(), "pairs": Counter(), "cases": []})
    boundaries = defaultdict(list)
    primary_pairs = {kind: Counter() for kind in KINDS}
    all_pairs = {kind: Counter() for kind in KINDS}
    merged = []
    for c, a, b in zip(cases, runs["original"]["results"], runs["ko"]["results"]):
        i = c["instruction_index"]
        differences = {}
        for kind in KINDS:
            av, bv = a["full"][kind], b["full"][kind]
            differences["target_" + kind] = av["instruction_results"][i] != bv["instruction_results"][i]
            differences["prompt_" + kind] = av["prompt_result"] != bv["prompt_result"]
            primary_pairs[kind][pair(av["instruction_results"][i], bv["instruction_results"][i])] += 1
            all_pairs[kind].update(pair(x, y) for x, y in zip(av["instruction_results"], bv["instruction_results"]))
        merged.append({"case": c, "original": a, "ko": b, "differences": differences})
        if c["scope"] != "dataset":
            continue
        for target in c["targets"]:
            i, iid = target["instruction_index"], target["instruction_id"]
            key = iid, target["input_partition"]
            row = coverage[key]
            flags = [b["full"][kind]["instruction_results"][i] for kind in KINDS]
            row["pairs"][pair(*flags)] += 1
            row["cases"].append({"case_id": c["case_id"], "key": c["key"], "instruction_index": i, "strict": flags[0], "loose": flags[1]})
            for kind, flag in zip(KINDS, flags):
                row[kind][tf(flag)] += 1
            if "boundary" in target:
                edge = target["boundary"]
                group = (c["key"], i, edge["parameter"], edge["threshold"])
                calls = [x for x in b["full"]["strict"]["checker_call_trace"] if x["instruction_index"] == i]
                count_name = {"frequency": "actual_occurrences", "num_bullets": "num_bullet_lists"}.get(edge["parameter"], edge["parameter"])
                require(calls and calls[0]["counts"].get(count_name) == edge["response_count"], f"Boundary count not observed: {c['case_id']}/{i}")
                boundaries[group].append({"case_id": c["case_id"], **edge, "strict": flags[0], "loose": flags[1]})
    require(set(coverage) == set(parts), "Missing normal-data input partition")
    for key, row in coverage.items():
        require(row["pairs"]["T,T"] and row["pairs"]["F,F"], f"No dedicated TT and FF: {key}")
    require(len(boundaries) == 13, "Missing count-boundary family")
    require(all({e["offset"] for e in edges} == {-1, 0, 1} for edges in boundaries.values()), "Incomplete N-1/N/N+1")
    repeated = [r for r in merged if r["case"]["key"] == 1203]
    for kind in KINDS:
        require({tuple(r["ko"]["full"][kind]["instruction_results"]) for r in repeated} == {(True, True), (True, False), (False, True), (False, False)}, "Repeated-ID matrix incomplete")
    metrics = {side: metric_counts(run["results"]) for side, run in runs.items()}
    expected_numerators = {"prompt_strict": 71, "instruction_strict": 133, "prompt_loose": 79, "instruction_loose": 142}
    require(all(metrics["ko"][name]["numerator"] == n for name, n in expected_numerators.items()), "Ko aggregate oracle mismatch")
    require(metrics["ko"]["prompt_strict"]["denominator"] == 156 and metrics["ko"]["instruction_strict"]["denominator"] == 247, "Wrong regression denominators")

    legacy_cases = baseline_cases()
    reproduction = {}
    for side in ["original", "ko"]:
        old = baseline_run(side)
        run = runs[side]
        verify_environment(run["reproduction"], ROOT / "baseline.json", side, provenance)
        archived = {r["case_id"]: r for r in old["results"]}
        require(len(old["results"]) == run["reproduction"]["retained_cases"] == 86, "Incomplete integrated reproduction")
        for case, record in zip(cases, run["results"]):
            verify_reproduction(case, record, archived)
        require(sum("baseline_reproduction" in r for r in run["results"]) == 86, "Wrong reproduced-case count")
        require(run["reproduction"]["exact_result_rows_matched"] == 86, "Reproduction summary mismatch")
        reproduction[side] = {"retained_cases": 86, "exact_result_rows_matched": 86, "included_in_experiment": True}

    support_cases = read_json(output_dir / "support_cases.json")
    validate_cases(support_cases, require_expected=False)
    supports = {side: read_json(output_dir / ("support_" + side + "_results.json")) for side in ["original", "ko"]}
    support_rows = []
    for side, run in supports.items():
        verify_environment(run, output_dir / "support_cases.json", side, provenance)
        require([r["case_id"] for r in run["results"]] == [c["case_id"] for c in support_cases], "Missing support input")
    for c, a, b in zip(support_cases, supports["original"]["results"], supports["ko"]["results"]):
        require(a["evaluated_input"] == b["evaluated_input"] == ko_input(c), "Support inputs differ")
        for kind in KINDS:
            if "error_type" in c["expected_ko"]:
                require(b["full"][kind].get("error", {}).get("type") == c["expected_ko"]["error_type"], "Expected Ko exception not preserved")
            else:
                require("error" not in b["full"][kind] and b["full"][kind]["instruction_results"] == c["expected_ko"]["full"][kind], "Support oracle mismatch")
                verify_phase(b["full"][kind], c["ko_instruction_id_list"], ko_input(c)["kwargs"], unicodedata.normalize("NFC", c["test_response_ko"]), kind, c["case_id"])
        support_rows.append({"case": c, "original": a, "ko": b})
    require(sum("error_type" in c["expected_ko"] for c in support_cases) == 8, "Wrong exception-contract count")

    # Validate the actual original aggregation utility on uneven instructions.
    from audit_runtime import load_modules
    import os
    os.environ["IFEVAL_AUDIT_SOURCE_ROOT"] = str(source_root)
    import audit_runtime
    audit_runtime.SOURCE_ROOT = source_root
    modules = load_modules("ko", "isolated-source")
    require(modules["utils"].agg_inst_level_acc([[True, True, True], [False]]) == 0.75, "Instruction aggregation changed")
    require(sum(map(all, [[True, True, True], [False]])) / 2 == 0.5, "Prompt aggregation changed")
    star = next(r for r in merged if r["case"]["case_id"] == "markdown_star_balanced_136")
    require(star["ko"]["full"]["loose"]["prompt_result"] and not any(x["prompt_result"] for x in star["ko"]["strict_on_actual_loose_candidates"]), "Instruction-wise OR witness lost")
    by_name = {r["case"]["case_id"]: r["ko"] for r in merged}
    for name in ["expanded_sent_lt_6_multiline", "expanded_bullets_10_unpadded", "expanded_nth_paragraphs_5"]:
        require(not by_name[name]["isolated"]["strict"]["instruction_results"][0] and by_name[name]["isolated"]["loose"]["instruction_results"][0], "Loose recovery witness lost")

    coverage_rows = [{"instruction_id": iid, "input_partition": part, "check_line": specs[iid]["check_line"],
                      **{kind: dict(stats[kind]) for kind in KINDS}, "strict_loose_pairs": dict(stats["pairs"]), "cases": stats["cases"]}
                     for (iid, part), stats in sorted(coverage.items())]
    summary = {"normal_cases": 156, "support_cases": 18, "normal_full_instruction_occurrences": 247,
               "normal_scope_counts": manifest["normal_scope_counts"], "source_keys": 32, "source_instructions": 55,
               "dataset_rows": 342, "dataset_instructions": 481, "dataset_ids": 21, "dataset_input_partitions": 25,
               "explicit_ids_with_TT_and_FF": 21, "explicit_partitions_with_TT_and_FF": 25,
               "boundary_families": 13, "boundary_offsets_per_family": [-1, 0, 1],
               "primary_pairs_english_ko": {kind: dict(primary_pairs[kind]) for kind in KINDS},
               "full_instruction_pairs_english_ko": {kind: dict(all_pairs[kind]) for kind in KINDS},
               "metrics": metrics, "baseline_reproduction": reproduction,
               "experiment": {"retained_cases": 86, "added_cases": 70, "normal_cases": 156, "reproduction_integrated": True},
               "baseline_cases_hash_verified": True,
               "support_normal_returns": 10, "support_expected_exceptions": 8,
               "normal_unhandled_exceptions": 0, "unresolved_ko_oracle_mismatches": 0,
               "identical_input_hashes_verified": 156, "comparison_scope": "English reference vs Ko reference; identical Ko input",
               "model_inference_run": False, "new_lighteval_ko_parity_run": False,
               "existing_lighteval_english_french_regression_run": False}
    return {"summary": summary, "manifest": manifest, "provenance": provenance,
            "environments": {s: r["environment"] for s, r in runs.items()}, "cases": merged,
            "coverage": coverage_rows, "boundaries": [{"key": k, "instruction_index": i, "parameter": p, "threshold": n, "cases": e} for (k, i, p, n), e in sorted(boundaries.items())],
            "legacy_coverage": legacy_coverage(legacy_cases, baseline_run("ko")["results"]),
            "support": support_rows, "verifier_sha256": sha(Path(__file__).read_bytes()), "verified_sources": verified_sources}


def decision(result, kind, index):
    row = result["full"][kind]
    if "error" in row:
        return row["error"]["type"]
    return tf(row["instruction_results"][index]) + " / [" + ",".join(map(tf, row["instruction_results"])) + "] / " + tf(row["prompt_result"])


def report(result, output_dir):
    from report_i18n import catalog_en, issue_ko, report_en, with_language_link

    summary = result["summary"]
    write_json(output_dir / "results.json", result)
    write_json(output_dir / "coverage.json", {"summary": summary, "input_partitions": result["coverage"], "boundaries": result["boundaries"], "legacy_coverage": result["legacy_coverage"]})
    lines = ["# IFEval / IFEval-Ko 확장 고정 응답 비교", "",
             "원본 영어·Ko 평가기에 **동일한 Ko prompt·instruction 순서·실제 적용 kwargs·응답**을 전달했다. 회귀 검증의 기준은 원본 Ko의 기대값과 일치하는지 여부다.", "",
             "기존 `case/full/isolated/diagnostics` 형식을 유지했다. `original_*` 필드는 원래 영어 문항의 출처를 보존하며, 실제 비교 입력은 각 원시 결과의 `evaluated_input`에 기록했다.", "",
             "156건의 실험은 실제 데이터 조건 116건·메모리 override 2건·합성 입력 38건으로 구성된다. 사용한 원본 문항은 32개이며 instruction 55개를 포함한다. full 평가에서 검사한 instruction은 247개다.", "",
             "보조 호환성·오류 입력 18건 중 10건은 정상 반환하고, 8건은 원본에서 예상한 예외가 발생한다. 보조 입력은 주 실험의 경로별 검증과 지표에 포함하지 않는다. 모델 생성, 새 Lighteval-Ko 검증과 기존 Lighteval 영어/French 회귀는 미수행이다.", "",
             "## 1. 판정 방향 — (영어, Ko)", "", "| 단계 | T,T | T,F | F,T | F,F | 분모 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for kind in KINDS:
        counts = summary["primary_pairs_english_ko"][kind]
        lines.append(f"| 대상 {kind} | " + " | ".join(str(counts.get(p, 0)) for p in ["T,T", "T,F", "F,T", "F,F"]) + " | 156 |")
    lines += ["", "각 case의 주 검사 대상 하나씩을 집계했다. 추가로 지정한 검사 대상과 full 평가의 모든 개별 판정은 아래 비교표와 JSON에 보존했다. 이 표의 `(영어, Ko)` 순서와 경계 표의 `(strict, loose)` 순서를 구별해 읽는다.", "",
              "## 2. 네 지표의 분자·분모", "", "고정 응답 실험의 집계다. 모델의 벤치마크 성능 점수를 나타내지 않는다.", "", "| 지표 | 영어 | Ko |", "| --- | --- | --- |"]
    for name, stat in summary["metrics"]["ko"].items():
        en = summary["metrics"]["original"][name]
        lines.append(f"| {name} | {en['numerator']}/{en['denominator']} | {stat['numerator']}/{stat['denominator']} |")
    lines += ["", "## 3. 전용 입력 경로 coverage", "", "실제 데이터 조건을 유지한 사례 중 `targets`로 지정한 instruction만 집계한다. 25개 입력 경로마다 strict·loose 모두 통과하는 응답(TT)과 모두 실패하는 응답(FF)을 확보했다. 이는 정상 kwargs에 따른 입력 경로의 검증 범위다.", "",
              "| instruction ID | 입력 경로 | strict T/F | loose T/F | 전용 TT | 전용 FF |", "| --- | --- | --- | --- | ---: | ---: |"]
    for r in result["coverage"]:
        lines.append(f"| `{r['instruction_id']}` | `{r['input_partition']}` | {r['strict'].get('T',0)}/{r['strict'].get('F',0)} | {r['loose'].get('T',0)}/{r['loose'].get('F',0)} | {r['strict_loose_pairs']['T,T']} | {r['strict_loose_pairs']['F,F']} |")
    lines += ["", "## 4. 경계·반복 ID·loose 복구", "", "| key:index | 조건 | N−1의 strict/loose | N | N+1 |", "| --- | --- | --- | --- | --- |"]
    for b in result["boundaries"]:
        edges = {c["offset"]: c for c in b["cases"]}
        cells = [pair(edges[o]["strict"], edges[o]["loose"]) for o in [-1, 0, 1]]
        lines.append(f"| {b['key']}:{b['instruction_index']} | {b['parameter']}={b['threshold']} | " + " | ".join(cells) + " |")
    lines += ["", "key 1203의 두 빈도 조건은 index 0이 전쟁≥8, index 1이 peace≥10이다. strict와 loose 각각에서 `[T,T]`, `[T,F]`, `[F,T]`, `[F,F]` 네 조합을 확인했다. prompt의 평화와 kwargs의 peace는 원본대로 유지했다.", "",
              "1268의 6문장은 한 줄로 쓰면 F/F, 여러 줄로 쓰면 F/T다. 136의 10개 bullet은 앞뒤에 빈 줄을 2개씩 두면 F/F, 빈 줄이 없으면 F/T다. 3073의 5문단도 F/T다. 여기서 F/T는 strict 실패·loose 통과를 뜻하므로 두 기대값을 각각 기록한다.", "",
              "## 5. 전체 비교표", "", "각 셀은 **대상 instruction의 판정 / 전체 instruction의 판정 목록 / 문항 전체 통과 여부** 순서다. 모든 행에서 양쪽 평가기에 동일 Ko 입력을 전달했다. 원본 조건·응답·기대값·관측값·해시는 cases.json과 results.json에 각각 기록했다.", "",
              "| key:index | Checker | Test | Original strict | Original loose | Ko strict | Ko loose | strict (EN,Ko) | loose (EN,Ko) | Scope | 실험 구성 |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in result["cases"]:
        c, a, b = row["case"], row["original"], row["ko"]
        i = c["instruction_index"]
        cells = [decision(r, kind, i) for r, kind in [(a,"strict"),(a,"loose"),(b,"strict"),(b,"loose")]]
        pairs = [pair(a["full"][k]["instruction_results"][i], b["full"][k]["instruction_results"][i]) for k in KINDS]
        composition = "기존·양쪽 재현 일치" if c["origin"] == "legacy_86" else "신규"
        lines.append(f"| {c['key']}:{i} | {c['checker']} | `{c['case_id']}` | " + " | ".join(cells + pairs + [c["scope"], composition]) + " |")
    lines += ["", "## 6. 별도 호환성·오류 입력", "", "| case | checker | 영어 strict/loose | Ko strict/loose | 분류 |", "| --- | --- | --- | --- | --- |"]
    for r in result["support"]:
        c = r["case"]
        vals = ["; ".join(decision(r[side], k, 0) for k in KINDS) for side in ["original","ko"]]
        lines.append(f"| `{c['case_id']}` | `{c['instruction_id']}` | {vals[0]} | {vals[1]} | {'예상한 예외 확인' if 'error_type' in c['expected_ko'] else '합성 호환성'} |")
    lines += ["", "## 7. 재현·이식 인계", "", "156건의 실험 결과에 입력 재현의 검증 근거를 포함했다. 기준 결과와의 일치 여부는 원시 결과의 `baseline_reproduction`과 `summary`에서 확인할 수 있다. 비교표는 동일 Ko 입력을 전달한 156건을 기준으로 집계한다.", "",
              "고정한 코드·데이터 21개 파일, 실제로 불러온 네 모듈, NLTK 자원과 입력·응답의 해시를 확인했다. 실행 단계·객체 생성·초기화·후보 처리 기록을 검사하고, instruction별 후보 OR·문항별 AND·단계별 새 객체·`if v` 필터·문항별 instruction 수가 다른 집계도 확인했다.", "",
              "A안은 원본 Ko의 채점 규칙을 가깝게 보존하고 기존 영어/French 코드의 변경 범위를 줄이기 위한 선택이다. B안도 같은 정책과 객체 생성 방식을 보존하면 구현할 수 있다.", "",
              "재현 명령은 README에 정리했다. [영문 이슈 첨부 초안](issue-1463.md)은 로컬에 준비했으며 아직 게시하지 않았다. [manifest](manifest.json), [검증 범위](coverage.json), [원본 문항 목록](source_rows.md)을 함께 확인할 수 있다.", ""]
    (output_dir / "results.en.md").write_text("\n".join(with_language_link(report_en(lines), "results.md", "en")), encoding="utf-8")
    korean_lines = [line.replace("[영문 이슈 첨부 초안](issue-1463.md)", "[이슈 첨부 초안](issue-1463.ko.md)") for line in lines]
    (output_dir / "results.md").write_text("\n".join(with_language_link(korean_lines, "results.en.md", "ko")), encoding="utf-8")
    ko_source = result["provenance"]["ko"]
    source_base = ko_source["repository"] + "/blob/" + ko_source["revision"] + "/"
    code_lines = {c["instruction_id"]: c["check_line"] for c in result["coverage"]}
    catalog = ["# 고정 Ko 원본 문항 목록", "", "`source_rows.json`에 원본 prompt·instruction 순서·24개 kwargs 필드를 보존했다. 아래 표에서는 null 필드만 생략했다.", "",
               "고정 데이터: [train Parquet](" + source_base + "data/train-00000-of-00001.parquet). 각 ID 링크는 같은 revision의 checker 코드를 가리킨다.", ""]
    for row in read_json(output_dir / "source_rows.json"):
        catalog += [f"## key {row['key']}", "", "```text", row["prompt"], "```", "", "| index | instruction_id | kwargs (null 생략) |", "| ---: | --- | --- |"]
        for i, (iid, kw) in enumerate(zip(row["instruction_id_list"], row["kwargs"])):
            url = source_base + "ifeval_ko/instructions.py#L" + str(code_lines[iid])
            catalog.append(f"| {i} | [`{iid}`]({url}) | `{json.dumps({k:v for k,v in kw.items() if v is not None}, ensure_ascii=False)}` |")
        catalog.append("")
    (output_dir / "source_rows.en.md").write_text("\n".join(with_language_link(catalog_en(catalog), "source_rows.md", "en")), encoding="utf-8")
    (output_dir / "source_rows.md").write_text("\n".join(with_language_link(catalog, "source_rows.en.md", "ko")), encoding="utf-8")
    issue = ["# Local experiment attachment for huggingface/lighteval#1463", "",
             "This draft summarizes a reference-evaluator experiment for https://github.com/huggingface/lighteval/issues/1463. It has not been posted. The new Lighteval-Ko task and model evaluation remain pending.", "",
             "## Experiment", "",
             "We conducted a **156-case experiment** and checked **18 auxiliary inputs** for compatibility and error handling. Of the 156 cases, 116 use unchanged dataset conditions, 2 use explicit in-memory overrides, and 38 are synthetic. Full evaluation checks 247 instruction occurrences across these responses. These figures describe test results, not model benchmark accuracy.", "",
             "Both evaluators, at the pinned revisions, received the **same Ko prompt, ordered instruction IDs, effective kwargs and response**. Input and response hashes confirm this. The `original_*` fields in cases.json preserve the English source metadata; `evaluated_input` in each raw result records the Ko input used for the comparison.", "",
             "Each of the 21 instruction IDs and 25 input partitions used by the dataset has an explicitly targeted response that passes both strict and loose checks and one that fails both. Thirteen count conditions have N−1/N/N+1 checks. The two frequency instructions in key 1203 are identified by index and tested with [T,T], [T,F], [F,T] and [F,F]. The 25 partitions describe normal kwargs paths, not all source-code branches.", "",
             "## Same-input decision matrix", "", "Pairs below mean **(English, Ko)** for the primary target of each case.", "", "| Phase | T,T | T,F | F,T | F,F | Cases |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for kind in KINDS:
        counts = summary["primary_pairs_english_ko"][kind]
        issue.append(f"| {kind} | " + " | ".join(str(counts.get(p,0)) for p in ["T,T","T,F","F,T","F,F"]) + " | 156 |")
    issue += ["", "Representative results using identical responses:", "", "| Key / case | English strict/loose | Ko strict/loose | Observation |", "| --- | --- | --- | --- |"]
    witnesses = [("markdown_quote_valid_highlights_349", "word counts 39 vs 40 at <40; blockquote marker contributes a Ko whitespace token"),
                 ("comma_boundary_compact", "word counts 20 vs 18 at <20; compact comma-separated text"),
                 ("markdown_star_balanced_136", "strict difference recovers in loose; instruction-wise candidate OR"),
                 ("expanded_constrained_T", "Ko fixed response phrase is absent from the English options")]
    by_id = {r["case"]["case_id"]: r for r in result["cases"]}
    for name, observation in witnesses:
        r = by_id[name];i=r["case"]["instruction_index"]
        values = ["/".join(tf(r[side]["full"][k]["instruction_results"][i]) for k in KINDS) for side in ["original","ko"]]
        issue.append(f"| {r['case']['key']} / `{name}` | {values[0]} | {values[1]} | {observation} |")
    issue += ["", "## Interpretation and proposed implementation", "",
              "These results support a separate `ifeval_ko` package and scorer for the initial port (option A). This keeps the Ko word and sentence utilities, fixed phrases and NFC handling close to the reference. It also preserves the order of running all strict checks before all loose checks, with fresh checker instances in each phase. The approach limits changes to the existing English and French paths, at the cost of duplicating a small scoring loop. Option B can also work if it preserves the same policies and checker lifecycle.", "",
              "The port must **match the Ko reference**. If English passes a response and Ko fails it, the port must also fail it. We preserve the known prompt/kwargs mismatches in 1203, 2142, 1268 and 3538, as well as the `first_word` normalization asymmetry.", "",
              "## Verification and limitations", "",
              "- All 156 cases match the Ko expectations declared before execution, with no unhandled scoring exceptions or unresolved mismatches. Full and isolated evaluations agree for every specified target.",
              "- Input reproduction is checked against the stored reference results and recorded with the raw results. The comparison table and metrics use identical Ko inputs throughout.",
              "- Auxiliary inputs cover four registered instruction types absent from the dataset. Ko `capital_word_frequency` raises AttributeError because `instructions_util` has no `nltk` attribute; the unregistered `key_sentences` ID raises KeyError. Eight auxiliary inputs raise expected exceptions and are excluded from normal scoring.",
              "- Traces from the original functions confirm candidate order and duplicates, exclusion of empty candidates, instruction-level OR and prompt-level AND, the original `if v` filter, and checker construction. The control with unequal instruction counts yields prompt accuracy 0.5 and instruction accuracy 0.75.",
              "- Parity testing for the new Lighteval-Ko task, regression checks for the existing Lighteval English/French paths, 23-prompt model integration and full-split evaluation on 342 prompts remain pending.", "",
              "## Pinned sources", ""]
    for name, p in result["provenance"].items():
        issue.append(f"- {name}: `{p['revision']}` — {p['repository']}")
    issue += ["", "The English reference in this experiment is the pinned lm-evaluation-harness evaluator. Both evaluators ran through full-package imports after source-file hashes were verified. The Lighteval implementation was used as a design reference.", "",
              "## Attachment contents and reproduction", "",
              "The ZIP contains fixtures, predeclared Ko expectations, raw results and traces, comparison tables, provenance, checksums and reproduction scripts. Start with [README.en.md](README.en.md) and [results.en.md](results.en.md) in `team-c-ifeval-ko/evidence/checker-audit/`. Downloaded evaluator sources, dependencies and model weights are excluded; the README explains how to restore the required versions. Private context, caches and credentials are also excluded.", "",
              "The ZIP and this note are ready for a later issue attachment. Relative links refer to files inside the archive.", ""]
    (output_dir / "issue-1463.ko.md").write_text("\n".join(with_language_link(issue_ko(issue), "issue-1463.md", "ko")), encoding="utf-8")
    (output_dir / "issue-1463.md").write_text("\n".join(with_language_link(issue, "issue-1463.ko.md", "en")), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    result = verify(args.output_dir, args.source_root.resolve())
    report(result, args.output_dir)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
