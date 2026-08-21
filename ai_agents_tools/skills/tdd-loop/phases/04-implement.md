# Phase 4 — Implement (TDD green)

Goal: make the code real, driven by unit tests during development.

## Hard rules
- **NEVER touch `tests/acceptance/`.** Not to "fix", not to "improve", not to
  "align with the implementation". If an acceptance test seems wrong, STOP and
  tell the user — that is a contract dispute, not a code change.
- No hardcoding outputs to satisfy specific test inputs. Implement behavior.

## Procedure
1. Follow plan.md order. Write unit tests under `tests/unit/` alongside the
   components they verify (you own these; they are NOT frozen).
2. Run unit tests frequently during development (`python -m pytest tests/unit -q`
   or the repo's runner). Fix as you go — don't batch failures.
3. Finish when the unit suite is fully green.

## Re-entry (loop-back from phase 6)

### Direct route (all violations `route: implement` only)
1. Read `last_qa_verdict` from STATE.md.
2. Resolve every item in `standards_violations`.
3. Unit suite green → phase 5 → phase 6. Do not skip polish.

### After planner triage (mixed violations — planner already ran phase 3)
1. Read `## Implement checklist` in plan.md (written by planner from QA verdict).
2. Resolve every checklist item. Use `qa-verdict-<N>.json` only for extra context.
3. Unit suite green → phase 5 → phase 6. Do not skip polish.

## Exit evidence
- Pasted unit-test runner output showing 0 failures (from THIS session).
- On QA re-entry: confirmation that all checklist / verdict items are resolved.
- STATE.md: phase → polish.
