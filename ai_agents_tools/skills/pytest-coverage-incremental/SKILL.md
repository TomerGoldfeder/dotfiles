---
name: pytest-coverage-incremental
description: Runs pytest with coverage, raises coverage toward a minimum (default 90%), adds tests iteratively, optionally bumps package version, and commits each increment on a dedicated branch via scripts/commit-coverage-branch.sh. Use when improving test coverage, running pytest-cov, filling coverage gaps, or when the user asks for incremental coverage work.
---

# Pytest coverage (incremental)

## Start: target coverage

**Default minimum: 90%** per file (fail the goal if reported total is below this).

Use **90** unless the user explicitly asks for a different minimum in this conversation
(e.g. "aim for 75%" or "get to 92%"). Store the chosen number for the rest of the workflow.

## Exclusions (do not add tests for these)

When choosing the next gap, **skip** any untested code that falls only under:

1. **MCP** — Code under an `mcp/` package directory, or files that exist to register MCP tools (e.g. `FastMCP`, `@mcp.tool()`), or MCP-only wiring.
2. **`__init__.py`** — Any package `__init__.py` (re-exports and package markers only).
3. **CLI** — The project CLI entry module.
4. **Constants** — Modules whose primary purpose is constants (typical names: `constants.py`, `*_constants.py`, or any files without any functions/classes), or lines that are only module-level constant bindings with no meaningful behavior to assert.

If the only remaining gaps are in excluded categories, **stop** and report that the minimum target cannot be reached without covering excluded areas (or suggest raising `pragma: no cover` / omit patterns in team review).

## Loop until coverage ≥ minimum (or no eligible gaps)

### 1. Run coverage

- Prefer the project’s existing command if present (e.g. `run_coverage.sh` or `pytest` from `pyproject.toml` or from `setup.py`).
- Typical pattern: `python -m pytest <tests> -v --cov=<package> --cov-report=term-missing --cov-report=xml` so **missing lines** are visible.
- Respect `[tool.coverage.run]` / `[tool.coverage.report]` in `pyproject.toml` when present.

Read the **TOTAL** coverage line and per-file missing sections.

### 2. Select the first eligible untested code

- Order files in a stable, predictable way (e.g. alphabetical path under the main package).
- Pick the **first file** that still has missing lines **and** is not excluded by the list above.
- Within that file, pick the **first missing line range** that is not only excluded constructs (e.g. pure constant lines in a constants module).

### 3. Add tests

- Place tests next to existing tests (same layout and style as the repo).
- Cover the selected behavior with focused tests; avoid broad refactors.
- Run pytest again to confirm green tests.

### 4. Version bump (if applicable)

If the change is **user-visible** or **release-worthy** (new behavior covered, API surface tested, or project convention expects a bump for test-only milestones—use judgment), bump the patch version:

- Search for `__version__ = "` (or `__version__ = '`) in the package’s main `__init__.py` (for example in gtstore package: `gtstore/__init__.py`).
- Increment the **patch** segment only unless the repo uses another policy documented elsewhere.

If the work is **tests-only** and the team does not bump for that, **skip** the version bump.

### 5. Commit on a new branch (script)

Run the helper script from the repo root (arguments: branch suffix, commit message; see [scripts/commit-coverage-branch.sh](scripts/commit-coverage-branch.sh)):

```bash
bash "${DEPLOYMENT_FOR_MACHINE}/skills/pytest-coverage-incremental/scripts/commit-coverage-branch.sh" \
  "<short-name-for-the-tested-area>" \
  "test(<area>): add coverage for <what was missing>

Explain what behavior is now covered."
```

The script performs: checkout default branch → pull → create `coverage-<suffix>` → stage changed/untracked project files → commit → push.

### 6. Repeat

Go to **step 1**. Stop when either: 
1. coverage of each file ≥ **minimum**
2. there are **no eligible** missing lines left to cover.
3. you have already done 10 iterations


## Project notes (gtstore)

- Package: `gtstore`; tests often under `tests/`.
- Optional: `run_coverage.sh` wraps venv init and pytest with `--cov=gtstore`.
- CLI: `gtstore/cli.py`; MCP: `gtstore/metadata_store/stores_operations/mcp/`.

## Additional resources

- Script usage and edge cases: [reference.md](reference.md)


## Checklist
- [ ] Adding tests where needed
- [ ] Bump __version__ if applicable
- [ ] commit and push the changes into a new branch