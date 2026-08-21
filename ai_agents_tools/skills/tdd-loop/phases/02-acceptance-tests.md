# Phase 2 — Acceptance Tests (TDD red, THE CONTRACT)

Goal: black-box tests for the public API — happy path AND failure path for
every operation in spec.md. These are the task's success criteria.

## Procedure
1. Write tests under `tests/acceptance/` in the repo (pytest, `test_*.py`).
   Rules:
   - Black-box ONLY: interact exclusively through the public API in spec.md.
     Never import internals, inspect storage, or call private functions.
   - Every numbered behavioral rule → at least one test, named traceably
     (e.g. `test_rule_03_update_missing_key_upserts`).
   - Every error-semantics row and every acceptance example is covered.
   - Happy path AND failure path per operation.
   - Deterministic and independent (no ordering deps, fixed seeds).
2. Run the suite. It must be RED: failures or ImportError of the
   not-yet-existing implementation. If anything passes, the test is vacuous —
   fix it.
3. **User approval gate**: show the user the test list (names + one-line
   descriptions) and the red run summary. Ask them to approve the contract.
   It is OK if they adjust — apply, re-run red, re-ask. Do not proceed without
   an explicit yes.
4. **Freeze**: `git add tests/acceptance && git commit -m "freeze: acceptance tests <task-id>"`.
   Capture the commit sha (`git rev-parse HEAD`).
   - Record it in STATE.md as `acceptance_freeze_sha`.
   - **Present it to the user** in the conversation, e.g.:
     > Acceptance tests frozen at commit `<sha>` on branch `<branch>`.
     Do not advance to phase 3 until the sha is shown.

From this moment, tests/acceptance/ is IMMUTABLE for this task.

## Exit evidence
- Pasted red run output.
- User's approval message.
- Freeze commit sha **shown in this session** and recorded in STATE.md; phase → plan.
