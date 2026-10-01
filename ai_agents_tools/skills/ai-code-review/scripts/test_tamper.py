#!/usr/bin/env python3
"""Deterministic test-integrity signals for the change in .acr/diff.patch.

Signals (each is a fact, not a verdict; the test-integrity reviewer decides
whether the task justified it):
  - deleted test files
  - assertion lines removed from test files (and how many were added back)
  - skip / xfail / disabled markers added
  - trivial assertions added (assert True, ...)
  - tolerance / approximation changes
  - test-runner configuration changes (conftest, pytest/jest config, CI)
  - special-case hints: literals compared in new source code that also appear in tests

Writes .acr/test_tamper.json. Usage: test_tamper.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _acr_common import (acr_dir, added_lines, is_test_file, load_patch,  # noqa: E402
                         removed_lines, repo_root, run, write_json)

ASSERT_RE = re.compile(
    r"\bassert\b|\bassert[A-Z]\w*\(|\bexpect\(|\bassert\.\w+\(|\.should\b|\bt\.(Error|Errorf|Fatal|Fatalf|Fail)\b"
    r"|\brequire\.\w+\(|\bself\.fail\(|pytest\.raises|\btoThrow|\bverify\(")
SKIP_RE = re.compile(
    r"pytest\.mark\.(skip|skipif|xfail)|@unittest\.(skip|expectedFailure)|\bunittest\.skip|pytest\.skip\("
    r"|\b(it|test|describe)\.(skip|todo)\(|\bx(it|describe|test)\(|\bt\.Skip(Now|f)?\(|@Disabled\b|@Ignore\b"
    r"|\bpending\(|@pytest\.mark\.flaky")
TRIVIAL_RE = re.compile(
    r"^\s*assert\s+(True|1|not\s+False)\s*(#.*)?$|expect\(\s*true\s*\)\.toBe\(\s*true\s*\)"
    r"|assertTrue\(\s*True\s*\)|assert\s+\w+\s+(is\s+not\s+None|or\s+True)\s*$")
TOLERANCE_RE = re.compile(r"approx\(|\b(rel|abs|atol|rtol|delta|places|epsilon)\s*=|toBeCloseTo\(|InDelta\(")
CONFIG_RE = re.compile(
    r"(^|/)(conftest\.py|pytest\.ini|tox\.ini|noxfile\.py|\.coveragerc|setup\.cfg|pyproject\.toml|package\.json"
    r"|Makefile|\.gitlab-ci\.yml)$|(^|/)(jest|vitest|karma|playwright|mocha)\.config\.[cm]?[jt]s$"
    r"|(^|/)\.github/workflows/|(^|/)\.mocharc")
ALWAYS_TEST_CONFIG = re.compile(r"(^|/)(conftest\.py|pytest\.ini|noxfile\.py|\.coveragerc)$|\.config\.[cm]?[jt]s$|\.mocharc")
TEST_KEYWORDS_RE = re.compile(r"pytest|test|coverage|jest|vitest|mocha|addopts|testpaths|--ignore|--deselect|skip|omit|exclude", re.I)
SPECIAL_CASE_RE = re.compile(
    r"\b(if|elif|case|when|switch|else\s+if)\b.*?(==|===|\bis\b|\bin\b|equals\()\s*"
    r"(?P<lit>\"[^\"]{3,}\"|'[^']{3,}'|-?\d{3,}(?:\.\d+)?)")


def main() -> int:
    root = repo_root()
    out = acr_dir(root)
    files = load_patch(root)

    res = {
        "test_files_changed": [],
        "deleted_test_files": [],
        "removed_assertions": [],
        "skip_markers_added": [],
        "trivial_assertions_added": [],
        "tolerance_changes": [],
        "test_config_changes": [],
        "special_case_hints": [],
    }

    source_literals = []  # (file, line, text, literal)
    for f in files:
        path = f["path"]
        if not path or f["binary"]:
            continue
        test = is_test_file(path)
        if test:
            res["test_files_changed"].append({"path": path, "status": f["status"]})
            if f["status"] == "deleted":
                res["deleted_test_files"].append(path)
            rem = [ln for ln in removed_lines(f) if ASSERT_RE.search(ln["text"])]
            add = [ln for ln in added_lines(f) if ASSERT_RE.search(ln["text"])]
            if rem:
                res["removed_assertions"].append({
                    "file": path, "removed": len(rem), "added": len(add),
                    "net": len(add) - len(rem),
                    "lines": [{"old_line": ln["old"], "text": ln["text"].strip()} for ln in rem[:20]],
                })
            for ln in added_lines(f):
                t = ln["text"]
                if SKIP_RE.search(t):
                    res["skip_markers_added"].append({"file": path, "line": ln["new"], "text": t.strip()})
                if TRIVIAL_RE.search(t):
                    res["trivial_assertions_added"].append({"file": path, "line": ln["new"], "text": t.strip()})
            for h in f["hunks"]:
                old_tol = [ln for ln in h["lines"] if ln["tag"] == "-" and TOLERANCE_RE.search(ln["text"])]
                new_tol = [ln for ln in h["lines"] if ln["tag"] == "+" and TOLERANCE_RE.search(ln["text"])]
                if old_tol and new_tol:
                    res["tolerance_changes"].append({
                        "file": path,
                        "before": [ln["text"].strip() for ln in old_tol[:5]],
                        "after": [{"line": ln["new"], "text": ln["text"].strip()} for ln in new_tol[:5]],
                    })
        if CONFIG_RE.search(path):
            changed = [ln for h in f["hunks"] for ln in h["lines"] if ln["tag"] != " "]
            relevant = changed if ALWAYS_TEST_CONFIG.search(path) else [ln for ln in changed if TEST_KEYWORDS_RE.search(ln["text"])]
            if relevant or (ALWAYS_TEST_CONFIG.search(path) and f["status"] in ("added", "deleted")):
                res["test_config_changes"].append({
                    "file": path, "status": f["status"],
                    "lines": [{"tag": ln["tag"], "line": ln["new"] or ln["old"], "text": ln["text"].strip()} for ln in relevant[:20]],
                })
        if not test:
            for ln in added_lines(f):
                m = SPECIAL_CASE_RE.search(ln["text"])
                if m:
                    source_literals.append((path, ln["new"], ln["text"].strip(), m.group("lit").strip("\"'")))

    if source_literals:
        tracked = run(["git", "ls-files"], cwd=root).stdout.splitlines()
        tracked += [p for p in run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root).stdout.splitlines()]
        test_paths = [p for p in tracked if is_test_file(p)]
        contents = {}
        for p in test_paths:
            fp = root / p
            try:
                if fp.is_file() and fp.stat().st_size < 2_000_000:
                    contents[p] = fp.read_text(errors="replace")
            except OSError:
                pass
        for path, line, text, lit in source_literals:
            hits = [p for p, c in contents.items() if lit in c]
            if hits:
                res["special_case_hints"].append({"file": path, "line": line, "text": text, "literal": lit,
                                                  "found_in_tests": hits[:10]})

    res["signal_count"] = (len(res["deleted_test_files"]) + len(res["removed_assertions"]) + len(res["skip_markers_added"])
                           + len(res["trivial_assertions_added"]) + len(res["tolerance_changes"])
                           + len(res["test_config_changes"]) + len(res["special_case_hints"]))
    write_json(out / "test_tamper.json", res)
    print(f"test files changed={len(res['test_files_changed'])} signals={res['signal_count']} "
          f"(deleted={len(res['deleted_test_files'])} removed_assert_files={len(res['removed_assertions'])} "
          f"skips={len(res['skip_markers_added'])} trivial={len(res['trivial_assertions_added'])} "
          f"tolerance={len(res['tolerance_changes'])} config={len(res['test_config_changes'])} "
          f"special_case_hints={len(res['special_case_hints'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
