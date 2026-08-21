---
name: repo-navigation
description: >-
  Use this skill whenever writing, editing, or adding code inside a repository
  (any task involving files in a git repo, a project directory, or anywhere with
  package manifests like package.json, pyproject.toml, Cargo.toml, go.mod, etc.).
  Checks for a repo-level AGENTS.md file that documents where code lives, how the
  codebase is organized, and how to add new code in this specific repo. If
  AGENTS.md exists, load it and follow its guidance for placement, structure, and
  repo-specific conventions. If it does not exist, exit silently and proceed with
  normal code-writing; its absence is not an error. This skill complements
  code-standards: AGENTS.md tells you WHERE code goes in this repo; code-standards
  tells you HOW the code itself should be written.
---

# Repo Navigation

This skill ensures that repo-specific conventions are loaded before you write or modify code in a repository.

## When this skill is active

Classify the intent of the user's request — or the intent of any other skill that's currently driving the task. If that intent involves **producing code** (writing new code, editing existing code, refactoring, generating snippets, etc.), this skill is active.

This applies regardless of whether the request comes directly from the user or indirectly through another skill that needs code as a sub-step.

## What to do

### Step 0: Announce activation

Before doing anything else, emit a one-line user-visible message so the user can see this skill was activated:

```
Using skill: repo-navigation
```

Do this once per conversation (the first time the skill is activated). Do not repeat it on subsequent code-writing turns in the same conversation.

### Step 1: Check for AGENTS.md

Check whether a file named exactly `AGENTS.md` exists at the repo root, **and** anywhere under a `docs/` directory in the repo (it may live one or more levels deep, e.g. `docs/AGENTS.md`, `docs/agent-onboarding/AGENTS.md`, `docs/some/nested/path/AGENTS.md`).
The `AGENTS.md` can also live under the package main folder (e.g: gtstore/docs/..).

First, resolve the repo root from the workspace folder being worked on (use `git rev-parse --show-toplevel` or the workspace path provided by the IDE). Then search within that directory:

```bash
REPO_ROOT=$(git -C <workspace_folder> rev-parse --show-toplevel 2>/dev/null)
cd "$REPO_ROOT"
ls **/AGENTS.md 2>/dev/null
find "docs" -type f -name AGENTS.md 2>/dev/null
```

Collect every match. All of them are in scope — a repo may have a root `AGENTS.md` plus more focused ones under `docs/`.

### Step 2a: If one or more AGENTS.md files exist

1. **Read each of them in full** before writing any code. If multiple exist, the more specific one (deeper in `docs/`, closer to the area being modified) takes precedence on conflicts; the root `AGENTS.md` provides the broader baseline.
2. **Treat it as authoritative** for this repo regarding:
   - Where new files should live (directory structure, module boundaries)
   - Naming conventions specific to this codebase
   - How to register new components (routes, handlers, models, migrations, etc.)
   - Which abstractions to use vs. avoid
   - Build/test/lint commands
   - Any other repo-specific rules it documents
3. **Cross-reference your plan** with AGENTS.md before emitting code. If the user asks for "a new service," AGENTS.md likely tells you which directory, which base class, and which registration step to use.
4. **If AGENTS.md links to other docs** (e.g., "see `docs/architecture.md` for X"), follow those links when relevant to the current task.

### Step 2b: If no AGENTS.md is found

Proceed normally. Do not warn the user, do not suggest creating one, do not mention it. Its absence is the expected default for most repos. (The Step 0 activation line should still have been emitted.)

## Composition with code-standards

These two skills work together:

- **`repo-navigation.md` (this skill)** — repo-specific: *where* code goes, *which* patterns this codebase uses, *how* to register things in this project.
- **`code-standards`** — universal: *how* the code itself is written (naming, typing, error handling, structure).

Both apply simultaneously when writing code in a repo. If they ever conflict on a specific point, AGENTS.md wins for that repo (it's the local override), but `code-standards` still governs everything AGENTS.md doesn't address.

## Composition with other skills

If another skill is driving the task (e.g., a feature-implementation skill, a refactor skill), still run this check first when code is being produced. The other skill handles *what* to build; AGENTS.md tells you *where and how* it fits into this specific codebase.

## Quick checklist

Before writing code:
- [ ] Did I emit the `Using skill: repo-navigation` activation line (once per conversation)?
- [ ] Did I check for `AGENTS.md` at the repo root **and** anywhere under `docs/`?
- [ ] If any are present, did I read them before planning the change?
- [ ] Does my plan match the file placement and conventions they describe (most specific wins)?
- [ ] Am I also applying `code-standards` for the code itself?
