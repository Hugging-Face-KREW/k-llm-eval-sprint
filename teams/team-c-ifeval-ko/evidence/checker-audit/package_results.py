"""Create a verified local attachment; never publish or run a git mutation."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from urllib.parse import unquote, urlsplit

from case_utils import ROOT, read_json, sha, write_json
from compare import report, require, verify

TEAM = ROOT.parent.parent
REPO = TEAM.parent.parent
AUDIT_FILES = [
    ".gitignore", "README.md", "README.en.md", "SHA256SUMS", "audit_runtime.py", "build_cases.py", "case_utils.py", "report_i18n.py",
    "run_audit.py", "run_original.py", "run_ko.py", "compare.py", "test_audit.py", "package_results.py",
    "fetch_sources.py", "provenance.json", "requirements.lock.txt", "nltk_resources.json", "baseline.json",
    "cases.json", "support_cases.json", "source_rows.json", "source_rows.md", "manifest.json",
    "original_results.json", "ko_results.json", "support_original_results.json", "support_ko_results.json",
    "results.json", "results.md", "results.en.md", "source_rows.en.md", "coverage.json", "validation.json", "test_output.txt",
]
TEAM_FILES = ["README.md", "README.en.md", "analysis.md", "analysis.en.md", "design.md", "design.en.md", "evidence/analysis-details.md", "evidence/analysis-details.en.md"]
SAMPLE_FILES = ["README.md", "README.en.md", "audit_coverage.py", "coverage_i18n.py", "selection.json", "coverage.json", "coverage.md", "coverage.en.md"]
EXCLUDED_DRAFT_NAMES = {"issue-draft.md", "issue-draft.ko.md", "issue-1463.md", "issue-1463.ko.md"}
DOCUMENT_PAIRS = [
    ("README.md", "README.en.md"), ("analysis.md", "analysis.en.md"), ("design.md", "design.en.md"),
    ("evidence/analysis-details.md", "evidence/analysis-details.en.md"),
    ("evidence/checker-audit/README.md", "evidence/checker-audit/README.en.md"),
    ("evidence/checker-audit/results.md", "evidence/checker-audit/results.en.md"),
    ("evidence/checker-audit/source_rows.md", "evidence/checker-audit/source_rows.en.md"),
    ("evidence/sample-coverage/README.md", "evidence/sample-coverage/README.en.md"),
    ("evidence/sample-coverage/coverage.md", "evidence/sample-coverage/coverage.en.md"),
]


def headings(path):
    return re.findall(r"^#{1,6} .+$", path.read_text(encoding="utf-8"), re.M)


def verify_document_languages():
    languages, counterparts = {}, {}
    for ko, en in DOCUMENT_PAIRS:
        for name, language, other in [(ko, "ko", en), (en, "en", ko)]:
            path = (TEAM / name).resolve()
            require(path.is_file(), f"Missing language version: {name}")
            languages[path], counterparts[path] = language, (TEAM / other).resolve()

    def prose(path):
        return re.sub(r"^```[^\n]*\n.*?^```[^\n]*$", "", path.read_text(encoding="utf-8"), flags=re.M | re.S)

    def anchors(path):
        content = prose(path)
        values = set(re.findall(r'<a\s+id="([^"]+)"', content))
        for title in re.findall(r"^#{1,6} (.+)$", content, re.M):
            title = re.sub(r"<[^>]+>", "", title)
            values.add(re.sub(r"[^\w -]", "", title.lower()).replace(" ", "-"))
        return values

    checked, switches = 0, 0
    for path, language in languages.items():
        content = prose(path)
        nav = next((line for line in content.splitlines()[:6] if "한국어" in line and "English" in line), None)
        require(nav is not None, f"Missing top language link: {path}")
        nav_targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", nav)
        require(len(nav_targets) == 1 and (path.parent / nav_targets[0]).resolve() == counterparts[path], f"Incorrect language counterpart: {path}")
        switches += 1
        for line in content.splitlines():
            if line == nav:
                continue
            for url in re.findall(r"\[[^\]\n]*\]\(([^\s)]+)\)", line):
                parsed = urlsplit(url.strip("<>"))
                if parsed.scheme or parsed.netloc:
                    continue
                target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                require(target.is_file(), f"Broken local link in {path}: {url}")
                checked += 1
                if target.suffix == ".md":
                    require(target in languages, f"Linked document has no language pair: {target}")
                    require(languages[target] == language, f"Unexpected language switch in {path}: {url}")
                    if parsed.fragment:
                        require(unquote(parsed.fragment) in anchors(target), f"Broken heading link in {path}: {url}")
    return {"pairs": len(DOCUMENT_PAIRS), "documents": len(languages), "top_language_links": switches,
            "local_body_links_checked": checked, "broken_links": 0, "unexpected_language_switches": 0}


def verify_document_structure():
    baseline_path = ROOT / ".cache/expansion-baseline.json"
    previous = ROOT / "validation.json"
    baseline = read_json(baseline_path) if baseline_path.exists() else None
    expected = baseline["headings"] if baseline else read_json(previous)["document_structure"]["expected_headings"]
    result = {"expected_headings": expected, "files": {}}
    for name, old in expected.items():
        current = headings(TEAM / name)
        old_iter = iter(current)
        require(all(any(candidate == value for candidate in old_iter) for value in old), f"An existing heading was renamed/removed/reordered: {name}")
        require([x for x in old if x.startswith("## ")] == [x for x in current if x.startswith("## ")], f"Top-level numbered sections changed: {name}")
        additions = [x for x in current if x not in old]
        require(all(x.startswith("#### ") for x in additions), f"Only numbered sub-subsections may be added: {name}")
        result["files"][name] = {"existing_headings_preserved": True, "top_level_sections_preserved": True,
                                 "added_headings": additions, "file_sha256": sha((TEAM / name).read_bytes())}
    if baseline:
        # A new local task may start after the user has committed earlier work.
        active_path = ROOT / ".cache/active-worktree-baseline.json"
        worktree_baseline = read_json(active_path) if active_path.exists() else baseline
        # The follow-up request authorizes bilingual documentation and its renderers.
        # Fix links in the existing English proposal without bundling issue drafts.
        allowed_names = TEAM_FILES + ["context.md", "issue-draft.md"] + ["evidence/sample-coverage/" + n for n in SAMPLE_FILES if n != "selection.json"]
        allowed = {str((TEAM / n).relative_to(REPO)) for n in allowed_names}
        audit_prefix = str(ROOT.relative_to(REPO)) + "/"
        for relative, digest in worktree_baseline["files"].items():
            if relative in allowed or relative.startswith(audit_prefix):
                continue
            require((REPO / relative).is_file() and sha((REPO / relative).read_bytes()) == digest, f"File outside authorized scope changed: {relative}")
        frozen = ["provenance.json", "nltk_resources.json", "requirements.lock.txt", "fetch_sources.py"]
        for name in frozen:
            path = ROOT / name
            require(sha(path.read_bytes()) == baseline["files"][str(path.relative_to(REPO))], f"Pinned provenance/dependency record was modified: {name}")
        original_results = str((ROOT / "results.json").relative_to(REPO))
        require(sha((ROOT / "baseline.json").read_bytes()) == baseline["files"][original_results], "Archived baseline bundle was modified")
        current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        require(current_head == worktree_baseline["head"], "HEAD changed during local task")
        require(not subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=REPO, text=True).strip(), "Unexpected staged changes")
        result["local_worktree_checks"] = {"head_unchanged": current_head, "index_has_no_staged_changes": True,
                                            "outside_scope_files_unchanged": True, "baseline_bundle_bytes_unchanged": True}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    output = ROOT
    evidence = verify(output, args.source_root.resolve())
    report(evidence, output)
    process = subprocess.run([sys.executable, "-B", str(ROOT / "test_audit.py")], cwd=ROOT, text=True, capture_output=True)
    test_log = process.stdout + process.stderr
    (output / "test_output.txt").write_text(test_log, encoding="utf-8")
    match = re.search(r"Ran (\d+) tests? in", test_log)
    require(process.returncode == 0 and match and int(match.group(1)) > 0, "Evidence negative-control tests failed; inspect test_output.txt")
    structure = verify_document_structure()
    document_languages = verify_document_languages()
    validation = {"validated_at_utc": datetime.now(timezone.utc).isoformat(),
                  "unit_tests_run": int(match.group(1)), "unit_test_failures": 0,
                  "verifier_sha256": evidence["verifier_sha256"], "test_code_sha256": sha((ROOT / "test_audit.py").read_bytes()),
                  "packager_sha256": sha(Path(__file__).read_bytes()), "summary": evidence["summary"],
                  "document_structure": structure, "document_languages": document_languages, "remote_publication_performed": False,
                  "new_lighteval_ko_parity_run": False, "model_inference_run": False}
    write_json(output / "validation.json", validation)
    audit_payload = [ROOT / n for n in AUDIT_FILES if n != "SHA256SUMS"]
    checksum_text = "".join(f"{sha(p.read_bytes())}  {p.relative_to(ROOT).as_posix()}\n" for p in sorted(audit_payload))
    (ROOT / "SHA256SUMS").write_text(checksum_text, encoding="utf-8")
    payload = audit_payload + [ROOT / "SHA256SUMS"] + [TEAM / n for n in TEAM_FILES] + [ROOT.parent / "sample-coverage" / n for n in SAMPLE_FILES]
    payload = sorted(set(payload))
    files = {"team-c-ifeval-ko/" + p.relative_to(TEAM).as_posix(): p.read_bytes() for p in payload}
    files["SHA256SUMS"] = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items())).encode("utf-8")
    attachments = ROOT / "attachments"
    attachments.mkdir(exist_ok=True)
    destination = attachments / "ifeval-ko-regression.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(destination) as archive:
        require(archive.testzip() is None, "ZIP CRC failure")
        forbidden = {"context.md", ".cache", ".venv", "sources", "__pycache__", ".git"} | EXCLUDED_DRAFT_NAMES
        require(not any(set(Path(name).parts) & forbidden for name in archive.namelist()), "Private, downloaded or excluded issue-draft files entered ZIP")
        for line in archive.read("SHA256SUMS").decode().splitlines():
            digest, name = line.split("  ", 1)
            require(sha(archive.read(name)) == digest, f"ZIP checksum mismatch: {name}")
    digest = sha(destination.read_bytes())
    (attachments / "ifeval-ko-regression.zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    write_json(attachments / "manifest.json", {"zip": destination.name, "bytes": destination.stat().st_size,
                                               "sha256": digest, "files": len(files), "crc_and_all_checksums_verified": True,
                                               "private_context_excluded": True, "issue_drafts_excluded": True, "remote_publication_performed": False})
    print(json.dumps({"archive": str(destination), "bytes": destination.stat().st_size, "sha256": digest,
                      "files": len(files), "tests": validation["unit_tests_run"], "existing_document_headings_preserved": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
