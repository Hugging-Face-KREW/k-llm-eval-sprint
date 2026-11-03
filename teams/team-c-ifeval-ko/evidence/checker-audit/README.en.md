# IFEval / IFEval-Ko Reference Evidence

[한국어](README.md) | **English**

This folder contains inputs, code, reproduction evidence and scoring results for a **156-case experiment**. The [comparison tables](results.en.md) and [results.json](results.json) show English/Ko judgments and aggregates. Input generation, execution, verification and attachment packaging all run from this folder.

The experiment comprises 116 unchanged dataset conditions, 2 in-memory overrides and 38 synthetic inputs, with 247 instruction occurrences in full evaluation. Eighteen auxiliary compatibility/error inputs run alongside it: 10 return normally and 8 raise expected exceptions. Auxiliary inputs are excluded from the main metric denominators. Model generation, new Lighteval-Ko parity and existing Lighteval English/French regression are pending.

## Files

| Evidence | Files and contents |
| --- | --- |
| Inputs/predeclared expectations | [cases.json](cases.json): 156 cases with source order, kwargs, responses, targets and hashes |
| English/Ko raw results | [original_results.json](original_results.json), [ko_results.json](ko_results.json): identical-Ko-input judgments and baseline reproduction |
| Complete results | [results.en.md](results.en.md), [results.json](results.json): comparison columns, individual/prompt judgments, reproduction checks and aggregates |
| Coverage/boundaries | [coverage.json](coverage.json), [manifest.json](manifest.json) |
| Source prompts | [source_rows.json](source_rows.json), [source_rows.en.md](source_rows.en.md): complete prompts, order and kwargs for 32 prompts/55 instructions |
| Baseline | [baseline.json](baseline.json): archived inputs, English/Ko judgments and environments for oracle provenance; not overwritten when regenerating results |
| Auxiliary inputs | [support_cases.json](support_cases.json), [support_original_results.json](support_original_results.json), [support_ko_results.json](support_ko_results.json) |
| Input generation/execution | [build_cases.py](build_cases.py), [run_original.py](run_original.py), [run_ko.py](run_ko.py), [run_audit.py](run_audit.py), [audit_runtime.py](audit_runtime.py) |
| Comparison/tests/packaging | [compare.py](compare.py), [test_audit.py](test_audit.py), [package_results.py](package_results.py) |
| Provenance/restoration/dependencies | [provenance.json](provenance.json), [fetch_sources.py](fetch_sources.py), [requirements.lock.txt](requirements.lock.txt), [nltk_resources.json](nltk_resources.json) |
| Verification/hashes | [validation.json](validation.json), [test_output.txt](test_output.txt), [SHA256SUMS](SHA256SUMS) |

Each `cases[i]` in `results.json` contains the input and both evaluators' results. `full` evaluates all instructions; `isolated`/`isolated_targets` evaluate specified indexes; `diagnostics` records checker observations. Baseline reproduction is embedded in the corresponding `baseline_reproduction`. Tables and four metrics use 156 identical Ko inputs; reproduction checks are not added to denominators.

`original_*` retains English source metadata. `evaluated_input` records actual comparison inputs; both evaluators use `test_response_ko`. Input/response hashes and cache keys prevent overwriting different responses with the same key. Adapt executable/cache paths to your environment.

## Representative cases

| Key | Case ID | English / Ko strict·loose on identical Ko input |
| --- | --- | --- |
| 3345 | `robber_full` | 강도 response under `keyword=robber`: both fail·fail |
| 3345 | `robber_keyword_override` | Explicit `keyword=강도` override: both pass·pass |
| 3442 | `comma_boundary_compact` | 20 words fail·fail / 18 words pass·pass |
| 349 | `markdown_quote_valid_highlights_349` | 39 words pass·pass / 40 words fail·fail |

Each case distinguishes source-input reproduction from identical-Ko-input judgment comparison. Algorithm differences are counted using identical responses. `controlled_override` and key=null `synthetic` cases remain distinct from original dataset conditions.

## Pinned revisions

| Resource | Revision |
| --- | --- |
| lm-evaluation-harness | `d6de81643928d653435c431bae19945d41d32520` |
| google/IFEval | `966cd89545d6b6acfd7638bc708b98261ca58e84` |
| Allganize IFEval-Ko code/data | `54199e3801116897697babf341865741dcd06fc8` |
| Lighteval design reference | `c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14` |

[provenance.json](provenance.json) preserves URLs and per-file hashes. Execution calls actual pinned `InputExample` and strict/loose functions without modifying checkers, tokenizers or loose transformations.

## Reproduction

Work in this `checker-audit/` directory. Inputs/results are generated here; `baseline.json` is read-only. Installation and public-source restoration need network access.

```bash
sha256sum --check SHA256SUMS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python fetch_sources.py
python -m pip install --no-deps --no-build-isolation -e sources/harness_full
python -c 'import nltk; assert nltk.download("punkt_tab", download_dir=".cache/nltk_data", quiet=True)'
python build_cases.py
python run_original.py
python run_ko.py
python compare.py
python test_audit.py
python package_results.py
sha256sum --check SHA256SUMS
```

To reuse restored sources read-only, give the builder, runners, comparator and packager the same `--source-root /absolute/path/to/ifeval_checker_audit`. It must contain `sources/` and `.cache/nltk_data/`. Raw results record actual paths, commands, versions, seeds and module hashes.

The default import mode is `full-package`. `--import-mode isolated-source` runs original evaluation modules without importing the parent harness dependencies; the selected mode is recorded. Both sides of the recorded experiment use full-package imports. Python `random` and `langdetect.DetectorFactory` seeds are 0. Source/NLTK hash mismatches stop verification.

`run_original.py` and `run_ko.py` share `run_audit.py`. Per evaluator, the default processes 156 comparison cases, 86 baseline reproductions and 18 auxiliary inputs: 260 case evaluations, distinct from 174 input records. Reproduction is not added to metric denominators. Use `--suite normal|support` to select a subset.

Expectations are declared before execution and never overwritten by observations. Baseline input LF hashes are checked against the stored oracle. Actual JSON byte hashes are distinguished from LF hashes to detect checkout CRLF conversion. `build_cases.py` preserves complete original prompts, instruction order and kwargs; repeated IDs are identified by `instruction_index`.

## Attachment scope

The attachment includes inputs, raw results, tables, code, documents, provenance and `baseline.json`. It excludes downloaded sources, virtual environments, caches, models, private settings and `context.md`. After verification, `package_results.py` creates `attachments/ifeval-ko-regression.zip` and its `.sha256`. Run `sha256sum --check SHA256SUMS` at the extraction root to verify it.

The [English issue attachment draft](issue-1463.md) and ZIP use the same experiment results. Both are prepared locally; no remote publication, commits or pushes were performed.

## Stored-response regression expansion (2026-11-03)

Counting only explicitly targeted instructions under original data conditions gives **all 21 types/25 paths a strict-and-loose pass (TT) and fail (FF)**. Incidental ID appearance is insufficient. The 25 paths follow normal kwargs, not all code branches.

Checks cover 13 N−1/N/N+1 count families, four Boolean combinations for both indexes in 1203, and strict failures recovered in loose. Baseline objects, inputs and judgments are also checked. Verified contracts include `if v`, NFC placement, eight candidates' order/duplicates/empty exclusion, instruction OR/prompt AND, all strict→all loose, fresh phase objects and uneven instruction aggregation.

Comparison `(EN,Ko)` pairs differ from boundary `(strict,loose)` pairs. Original translation/unit mismatches, normalization asymmetry and internal exception behavior are preserved. Eight expected-exception auxiliary inputs are not successful scoring.

The new Ko task must match every instruction/prompt strict/loose Boolean, all four numerators/denominators and values within absolute error ≤1e-12, with zero omissions, unhandled exceptions or unresolved mismatches. The integration proposal remains 23 prompts/40 instructions. New-task validation, existing English/French regression/object isolation/optional dependencies, model integration and full-split evaluation remain pending.
