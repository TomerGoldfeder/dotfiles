# Phase 5 — Polish

Goal: bring the implementation to the code standards without changing behavior.

## Procedure
1. **Load standards** at `standards_ref` in STATE.md
   (default `${DEPLOYMENT_FOR_MACHINE}/skills/code-standards/SKILL.md`):

   **Path A — code-standards available** (skill file exists):
   a. Read the skill file in full.
   b. Load `standards/INDEX.md` in the same directory as that skill file.
   c. Identify every applicable rule file; read each from `standards/` alongside
      that skill (e.g. `standards/code-structure-typing.mdc`).
   d. Set STATE.md `standards_mode: code-standards`.

   **Path B — fallback** (skill, `standards/INDEX.md`, or `standards/` missing/unreadable):
   a. Detect the repo's primary programming language.
   b. Apply idiomatic best practices for that language (e.g. PEP 8 / typing
      for Python, ecosystem conventions for JS/TS, etc.).
   c. **Write explicitly** — all three required:
      - STATE.md: `standards_mode: language-default`
      - STATE.md: `standards_fallback_note: <what was missing; which language>`
      - Conversation: state that code-standards was not found and which
        language defaults are being used.
      - Decisions log: one line recording the fallback.

2. Review ONLY implementation code and `tests/unit/` (never `tests/acceptance/`)
   against the loaded rules (Path A) or language defaults (Path B). Fix every
   violation you can without changing behavior or violating the frozen
   acceptance contract.

3. Re-run the unit suite after changes — behavior must not drift.

## Exit evidence
- `standards_mode` and rule files loaded (Path A) OR explicit fallback note (Path B).
- Concise list of violations found and fixed (file + rule/language-default + what changed).
- Pasted green unit run AFTER the polish edits.
- STATE.md: phase → qa.
