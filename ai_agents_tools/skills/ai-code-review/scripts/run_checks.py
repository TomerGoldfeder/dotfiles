#!/usr/bin/env python3
"""Run the project's own linters / type checkers on the changed files (tests opt-in).

Tools are only run when present (project venv / node_modules first, then PATH) and,
where relevant, configured. Nothing here fails the review: results are context for
reviewers so they don't re-report what a tool already caught.

Writes .acr/checks/<tool>.txt and .acr/checks.json, including
"diagnostics_on_changed_lines": tool output lines that point at lines added by the diff.

Usage: run_checks.py [--tests] [--timeout SECONDS]
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _acr_common import acr_dir, added_lines, load_meta, load_patch, repo_root, run, write_json  # noqa: E402

LOC_RE = re.compile(r"^(?:\./)?(?P<path>[^\s:()]+?)[:(](?P<line>\d+)(?:[:,]\d+)?\)?[: ]")


def find_tool(root: Path, name: str):
    for cand in (root / ".venv/bin" / name, root / "venv/bin" / name, root / "node_modules/.bin" / name):
        if cand.exists():
            return str(cand)
    return shutil.which(name)


def has_any(root: Path, *names) -> bool:
    return any((root / n).exists() for n in names)


def pyproject_has(root: Path, section: str) -> bool:
    p = root / "pyproject.toml"
    return p.exists() and f"[{section}" in p.read_text(errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", action="store_true", help="also run the test suite(s)")
    ap.add_argument("--timeout", type=int, default=600, help="per-tool timeout in seconds (default 600)")
    args = ap.parse_args()

    root = repo_root()
    out = acr_dir(root)
    checks_dir = out / "checks"
    checks_dir.mkdir(exist_ok=True)
    meta = load_meta(root)

    changed = [f["path"] for f in meta["files"] if f["status"] != "deleted" and (root / f["path"]).is_file()]
    py = [p for p in changed if p.endswith(".py")]
    js = [p for p in changed if re.search(r"\.[cm]?[jt]sx?$", p)]
    go_dirs = sorted({str(Path(p).parent) for p in changed if p.endswith(".go")})
    sh = [p for p in changed if p.endswith((".sh", ".bash"))]

    plan = []  # (name, cmd)
    if py:
        ruff = find_tool(root, "ruff")
        flake8 = find_tool(root, "flake8")
        if ruff:
            plan.append(("ruff", [ruff, "check", "--output-format", "concise", "--no-fix", *py]))
        elif flake8:
            plan.append(("flake8", [flake8, *py]))
        mypy = find_tool(root, "mypy")
        if mypy and (has_any(root, "mypy.ini", ".mypy.ini") or pyproject_has(root, "tool.mypy")):
            plan.append(("mypy", [mypy, "--no-error-summary", "--show-column-numbers", *py]))
        pyright = find_tool(root, "pyright")
        if pyright and (has_any(root, "pyrightconfig.json") or pyproject_has(root, "tool.pyright")):
            plan.append(("pyright", [pyright, *py]))
    if js:
        eslint = find_tool(root, "eslint")
        if eslint and (any(root.glob("eslint.config.*")) or any(root.glob(".eslintrc*"))):
            plan.append(("eslint", [eslint, "--format", "unix", *js]))
        tsc = find_tool(root, "tsc")
        if tsc and (root / "tsconfig.json").exists() and any(p.endswith((".ts", ".tsx", ".mts", ".cts")) for p in js):
            plan.append(("tsc", [tsc, "--noEmit", "-p", "tsconfig.json"]))
    go = shutil.which("go")
    if go_dirs and go:
        plan.append(("go-vet", [go, "vet", *[f"./{d}/..." if d != "." else "./..." for d in go_dirs]]))
    shellcheck = find_tool(root, "shellcheck")
    if sh and shellcheck:
        plan.append(("shellcheck", [shellcheck, "-f", "gcc", *sh]))

    if args.tests:
        pytest = find_tool(root, "pytest")
        if pytest and (py or has_any(root, "pytest.ini", "conftest.py", "tests") or pyproject_has(root, "tool.pytest")):
            plan.append(("pytest", [pytest, "-q", "--no-header", "-p", "no:cacheprovider", "-x"]))
        pkg = root / "package.json"
        npm = shutil.which("npm")
        if npm and pkg.exists() and '"test"' in pkg.read_text(errors="replace"):
            plan.append(("npm-test", [npm, "test", "--silent"]))
        if go and go_dirs:
            plan.append(("go-test", [go, "test", *[f"./{d}/..." if d != "." else "./..." for d in go_dirs]]))

    # added line numbers per file, to separate new problems from pre-existing ones
    added = {f["path"]: {ln["new"] for ln in added_lines(f)} for f in load_patch(root) if f["path"]}

    results, on_changed = {}, []
    timeout_bin = shutil.which("timeout")
    for name, cmd in plan:
        t0 = time.time()
        full = [timeout_bin, str(args.timeout), *cmd] if timeout_bin else cmd
        r = run(full, cwd=root)
        output = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        (checks_dir / f"{name}.txt").write_text(output)
        results[name] = {
            "cmd": " ".join(cmd), "exit_code": r.returncode,
            "timed_out": r.returncode == 124 and bool(timeout_bin),
            "seconds": round(time.time() - t0, 1),
            "output_file": f".acr/checks/{name}.txt",
            "tail": output.strip().splitlines()[-15:],
        }
        for line in output.splitlines():
            m = LOC_RE.match(line.strip())
            if not m:
                continue
            p = m.group("path")
            p = str(Path(p).resolve().relative_to(root)) if Path(p).is_absolute() and str(p).startswith(str(root)) else p
            if int(m.group("line")) in added.get(p, set()):
                on_changed.append({"tool": name, "file": p, "line": int(m.group("line")), "message": line.strip()[:300]})

    skipped = []
    if py and not any(n in results for n in ("ruff", "flake8")):
        skipped.append("python linter (ruff/flake8 not found)")
    if js and "eslint" not in results:
        skipped.append("eslint (not found or not configured)")
    if not args.tests:
        skipped.append("tests (pass --tests to run)")

    write_json(out / "checks.json", {"tools": results, "skipped": skipped,
                                     "diagnostics_on_changed_lines": on_changed[:300]})
    print("ran: " + (", ".join(f"{k}(exit {v['exit_code']})" for k, v in results.items()) or "nothing"))
    print(f"diagnostics on changed lines: {len(on_changed)}")
    if skipped:
        print("skipped: " + "; ".join(skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
