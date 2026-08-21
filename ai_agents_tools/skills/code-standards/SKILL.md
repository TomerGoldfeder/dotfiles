---
name: code-standards
description: Use this skill whenever writing, editing, refactoring, generating, or reviewing code in any language or context. Loads the user's personal code standards from standards/INDEX.md (bundled with this skill), then loads the specific rule files relevant to the current task. Apply for ALL code generation tasks, including code produced as a side effect of other skills (e.g., when a data-analysis, docx, pptx, or any other skill writes Python, JavaScript, shell, SQL, etc., these standards still apply). This skill composes with other skills rather than replacing them — follow the other skill's domain instructions AND the loaded rules together.
---

# Code Standards

This skill points you to the user's personal code standards. The rules are **bundled in this skill's `standards/` directory** (not in `~/.cursor/rules/`), organized via `standards/INDEX.md`.

**Paths (relative to this skill's directory):**

- Index: `standards/INDEX.md`
- Rule files: `standards/code-structure-*.mdc` (names listed in the index)

On this machine the skill root is:

`${DEPLOYMENT_FOR_MACHINE}/skills/code-standards/`

(`DEPLOYMENT_FOR_MACHINE` is set by `terminal-stack/shell/env.sh`.)

## When this skill is active

You are active any time code is being produced. This includes:
- Direct requests ("write me a script", "fix this bug", "refactor this function")
- Indirect code generation, where another skill needs code as a sub-step (data analysis writing Python, document generation writing a snippet, etc.)
- Code in any language: Python, JavaScript/TypeScript, Go, Rust, shell, SQL, etc.

If another skill instructs you to write code, follow that skill's domain guidance **and** the rules loaded via this skill. They are not mutually exclusive.

## What to do

### Step 0: Announce activation

Before doing anything else, emit a one-line user-visible message so the user can see this skill was activated:

```
Using skill: code-standards
```

Do this once per conversation (the first time the skill is activated). Do not repeat it on subsequent code-writing turns in the same conversation.

### Step 1: Load the index

Read `standards/INDEX.md` first (in the `standards/` folder next to this `SKILL.md`). It is the navigation file that tells you which rule files exist and when each one applies.

```bash
cat "${DEPLOYMENT_FOR_MACHINE}/skills/code-standards/standards/INDEX.md"
```

If `standards/INDEX.md` is missing or unreadable, fall back to listing `standards/` and reading what's there directly:

```bash
ls "${DEPLOYMENT_FOR_MACHINE}/skills/code-standards/standards/"
```

If the `standards/` directory itself doesn't exist, tell the user once that standards weren't found alongside the code-standards skill and proceed with sensible defaults — don't keep mentioning it on subsequent turns.

### Step 2: Identify which rules apply

Based on what `standards/INDEX.md` says about each rule file and what you're about to write, decide which specific rule files are relevant to the current task. Examples of how relevance might break down (the actual structure depends on what's in INDEX.md):

- Language-specific rules (e.g., Python rules when writing Python)
- Domain-specific rules (e.g., testing rules when writing tests, API rules when writing endpoints)
- Universal rules that always apply

Be inclusive when in doubt — loading a rule file that turns out to be marginally relevant is cheap; missing one that mattered is the failure mode to avoid.

### Step 3: Load the relevant rule files

Read each rule file you identified in step 2 from `standards/`. Read them **in full** before writing any code — don't skim, and don't load them lazily mid-generation.

```bash
cat "${DEPLOYMENT_FOR_MACHINE}/skills/code-standards/standards/<rule-file>.mdc"
```

### Step 4: Apply them

Write the code following the loaded rules. If multiple rules touch the same concern, follow the more specific one (e.g., a Python-specific rule overrides a generic one for Python code).

## Composition with other skills

When another skill (data analysis, document generation, repo navigation, etc.) is active alongside this one:

1. The other skill governs **what** the code accomplishes (its domain logic, output format, etc.).
2. This skill — via the loaded rules — governs **how** the code is written (style, structure, conventions).
3. If `repo-navigation` loaded an `AGENTS.md`, that file governs repo-specific placement and conventions. The loaded personal rules still apply on top, except where AGENTS.md explicitly overrides them for that repo.

Order of precedence when conflicts arise (rare):
1. Repo-specific `AGENTS.md` (most specific)
2. Personal rules from `standards/` (loaded via this skill)
3. Language/ecosystem idiomatic defaults (least specific)

## Caching across a conversation

Once you've loaded the index and the relevant rule files in a conversation, you don't need to re-read them on every code-writing turn within the same conversation — they're in your context. Re-load only if:
- The task shifts to a different language or domain that needs different rules
- The user mentions they've updated their rules
- A long conversation may have pushed earlier reads out of working memory

## Quick checklist before emitting code

- [ ] Did I emit the `Using skill: code-standards` activation line (once per conversation)?
- [ ] Did I read `standards/INDEX.md` (at least once this conversation)?
- [ ] Did I identify which specific rule files apply to this task?
- [ ] Did I load those rule files in full from `standards/`?
- [ ] Am I about to write code that follows them?
- [ ] If another skill or `AGENTS.md` is also active, am I composing them correctly?
- [ ] Did i check whether i need to bump the version of the repo? under name_of_the_repo/__init__.py
