---
name: enhanced-workflow
description: >-
  Structured development workflow that loads repo-navigation and code-standards at
  startup, invokes brainstorming for the task, checks troubleshooting knowledge
  base on errors, verifies test strategy and code standards before completion,
  records new issues, and journals performance. Use for all development tasks
  involving code writing, editing, refactoring, debugging, or feature work — and
  whenever basic-rules or AGENTS.md require enhanced-workflow before coding.
---

# Enhanced Workflow

Mandatory phased workflow for development tasks. Operate like the default coding
agent but **never skip phases** — even for "quick" tasks.

Invoke sibling skills by **name** (resolved via your unified skills install /
symlink layout). If a skill is not found, note it to the user and continue with
remaining phases.

## Phase 1: STARTUP (before any work)

Before doing anything else, read and follow these skills:

1. **repo-navigation** — check for `AGENTS.md`, load repo conventions.
2. **code-standards** — load personal code standards.

Do **not** proceed to the user's task until both skills are loaded and their
setup steps are complete.

Emit once per session:

```
Using skill: enhanced-workflow (Phase 1 — startup)
```

## Phase 2: WORK (handle the user's request)

Perform the user's requested task using all available tools, with Phase 1
context guiding code decisions.

**Mandatory:** invoke **brainstorming** to work through the user request before
implementing.

**During this phase**, whenever you encounter an error, bug, unexpected
behavior, or any issue:

- Read and invoke **troubleshooting-issues-solver** to check the repo's
  `known_mistakes/` folder for prior solutions.
- If a solution exists, apply it. If not, investigate and fix normally.

## Phase 3: PRE-COMPLETION (before claiming work is done)

After main work is complete but **before** your final response:

### 3a. Test strategy

Search for `test_strategy.md` under `docs/` in the current repo:

```bash
REPO_ROOT=$(git -C <workspace_folder> rev-parse --show-toplevel 2>/dev/null)
cd "$REPO_ROOT"
find docs -type f -name test_strategy.md 2>/dev/null
```

If found, read it and verify your work complies. Add tests when the strategy
requires them.

### 3b. Code standards verification

Read and invoke **test.code-standards-verifier** to verify all code changes from
this session comply with loaded code standards. Fix violations before proceeding.

## Phase 4: END (after Phase 3 passes)

### 4a. Record new issues

If you resolved an issue in Phase 2 that was **not** already in the knowledge
base, read and invoke **troubleshooting-issues-recorder**.

### 4b. Performance journal

Read and invoke **performance-journaler**.

## Constraints

- Do **not** skip Phase 1 — even for quick tasks.
- Do **not** skip Phase 3 or Phase 4 — even if the task seems trivial.
- Do **not** claim work is complete until all phases have run.
- If a skill is not found, note it to the user and continue with remaining phases.
