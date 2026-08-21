# Reference: incremental coverage workflow

## Target coverage

- **Default minimum: 90%** per file unless the user specifies another value in the conversation.

## Finding gaps

- Use `--cov-report=term-missing` (and optionally `html`/`xml` for large trees).
- Eligible “first” gap: first non-excluded file (alphabetically under source tree), first missing block.

## Excluded patterns (quick check)

| Category   | Typical signals |
|-----------|------------------|
| MCP       | Path contains `/mcp/`, or `@mcp.tool`, FastMCP server modules |
| `__init__`| Filename `__init__.py` |
| CLI       | Console entry module, argparse main, `gtstore/cli.py` |
| Constants | `constants.py`, `*_constants.py`, or only `NAME = ...` lines |

## Commit script

See [scripts/commit-coverage-branch.sh](scripts/commit-coverage-branch.sh). It:

1. Resolves the remote default branch (`origin/HEAD`).
2. Checks it out and pulls with rebase.
3. Creates `coverage-<suffix>` (fails if branch exists).
4. Stages changes with `git add -u` plus untracked files from `git ls-files --others --exclude-standard` (broader and safer than only `git diff --name-only`, so new test files are included).
5. Commits with the provided message and pushes `-u origin HEAD`.

Requires a clean intention: run from repository root; resolve conflicts after `git pull` before retrying.

## When to bump `__version__`

- Bump patch when shipping or when project policy ties version to test milestones.
- Skip if tests-only and maintainers do not version-bump for that.
