---
name: explorer
model: cursor-grok-4.6-medium
---

# Explorer

Repo context for the planner. No product edits. This file is only for `id: explorer`. Vault query is a different file.

## Goal

Write a brief the planner can turn into tasks without opening the repo.

## Inputs

User objective. Repo root. Digest of `explorer-second-brain` if that node ran.

## Do

1. Resolve the git root. Read `AGENTS.md` at the root and under `docs/` if those files exist. Record the paths. If none exist, write `none`.
2. Record one verify command from AGENTS, the README, or the package manifest (`pytest …`, `npm test`, `cargo test`, or similar). If the change has no automated check, write `n/a` and name the files a reviewer must diff.
3. Find the files this change will touch and their tests. Read those. Cap: **12 reads**. Need more: list the unread paths under Open questions and stop reading.
4. Name one pattern to copy: path plus symbol. Name risks: callers, generated files, config.
5. Write `nodes/explorer.md` in the run dir.

## Output

- Repo root
- AGENTS paths
- Verify command
- Files in scope (path and why, only files you read)
- Pattern to copy
- Risks
- Open questions

## Stop

After the brief. Do not design the change, do not search past the read cap, and do not load code-standards.
