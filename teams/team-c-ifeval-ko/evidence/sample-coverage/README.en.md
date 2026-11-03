# Reproducing Prompt Selection Coverage

[한국어](README.md) | **English**

This audit compares pinned IFEval-Ko data and checker code to count the instruction IDs and input paths covered by the proposed selection. It does not generate model responses or execute checkers.

## Materials

- [selection.json](selection.json): 23 proposed prompt keys and retained diagnostic prompts, pending team review.
- [audit_coverage.py](audit_coverage.py): checks source SHA-256 hashes, analyzes registry/checker ASTs and counts selection coverage.
- [coverage.json](coverage.json): source URLs/revisions/hashes, script/selection hashes, environment, index-level mappings and aggregates.
- [coverage.en.md](coverage.en.md): type/path tables for the same result.

## Denominators and scope

The `train` split at revision `54199e3801116897697babf341865741dcd06fc8` contains 342 prompts, 481 instruction occurrences and 21 IDs. Repeated IDs in a prompt count separately by instruction index.

We examined `check_following` conditions where kwargs-derived attributes select different operations or regexes. Normal data uses two `relation` values for each of three types and two postscript markers, `P.P.S`/`P.S.`. The other 17 types have no such observed normal-input value branch and each contributes one `default` path. The total is 25 `(instruction ID, input path)` pairs. The script checks constant comparisons in the AST and stops on an unreviewed branch field, class or value.

This is not executed code-branch coverage. The 25 paths do not include all response pass/fail branches, missing/invalid kwargs, random fallbacks, other postscript markers or every numeric/phrase/language combination. These belong to the stored-response scope in [design section 6.2](../../design.en.md#fixed-response-regression). See the [156-case reference results](../checker-audit/results.en.md); new-task parity and model integration remain pending.

## Reproduction

Run from the sprint repository root. The counting environment is recorded in `runtime` in [coverage.json](coverage.json).

```bash
python -m pip install "pyarrow==26.0.0"
python teams/team-c-ifeval-ko/evidence/sample-coverage/audit_coverage.py
```

The script reuses Ko source URLs/hashes in [provenance.json](../checker-audit/provenance.json) to download pinned data, checker, registry and author documentation. It reads checker ASTs without importing or executing them. Data is read in a temporary directory, removed on exit. Outputs are `coverage.json`, `coverage.md` and `coverage.en.md` in this folder.

To reproduce without overwriting existing outputs, choose another output directory:

```bash
python teams/team-c-ifeval-ko/evidence/sample-coverage/audit_coverage.py --output-dir /tmp/ifeval-ko-coverage
```

If identical sources are already available, use `--source-dir <source-directory>` to skip downloads. It must contain `data/train-00000-of-00001.parquet`, `ifeval_ko/instructions.py`, `ifeval_ko/instructions_registry.py` and `README_Ko.md`. Source hashes are still checked.

## Confirmed result

| Selection | Prompts/instructions | IDs | Input paths | Repeated-ID/multiple-instruction prompts |
| --- | --- | --- | --- | --- |
| Proposal | 23/40 | 21/21 | 25/25 | 1/13 |

The proposal covers `less than`/`at least` for keyword frequency, sentence count and word count, plus `P.P.S`/`P.S.` postscript paths. Input inclusion and agreement of actual response judgments are separate checks.
