# Phase 3 — Plan + Alignment Check

Goal: implementation plan including internal component design and UNIT tests
(distinct from acceptance tests).

## Procedure
1. Write `<task-dir>/plan.md`:
   - Module/file layout and internal components
   - Public interfaces the acceptance tests expect (exact signatures)
   - Unit-test plan: which internal components get unit tests under
     `tests/unit/`, what each verifies
   - Implementation order: which acceptance tests turn green at each step
   - Risks / tricky parts

2. **Alignment check** — answer in writing, honestly:
   a. Does this plan, fully executed, make every acceptance test pass?
   b. Does it serve the OBJECTIVE (not just the tests)?
   c. Are there open questions that require the user?

## Routing (the only legal back-edges from alignment check)
- Open questions exist → go to **phase 1** (append-only re-entry).
- No open questions, but plan and spec/tests are misaligned → go to
  **phase 2** (revise acceptance tests; this re-triggers user approval and a
  NEW freeze commit).
- Check `plan_loopbacks` counter in STATE.md: if this would be the 2nd
  loop-back, STOP and report the misalignment to the user instead.
- Aligned and no questions → phase 4.

## Re-entry (loop-back from phase 6 — planner triage)

Triggered when QA returns NO_SHIP and any `standards_violations` item has
`route: "plan"`. Uses `qa_cycles` budget only — does not consume `plan_loopbacks`.

1. Read `last_qa_verdict` from STATE.md (or latest `qa-verdict-<N>.json`).
2. For each violation with `route: "plan"`: update plan.md — fix layout, layers,
   module boundaries, component placement. Log each change in STATE.md decisions.
3. For each violation with `route: "implement"`: append to an
   **`## Implement checklist`** section in plan.md (file, rule, detail) so the
   implementer has a filtered list without re-interpreting the full verdict.
4. Proceed to phase 4 when plan.md reflects the structural fixes and the
   checklist is complete.

Acceptance tests remain frozen — replan within the existing contract.

## Exit evidence
- plan.md + alignment answers (initial entry) OR updated plan.md + implement
  checklist (QA re-entry); STATE.md updated (phase, counters).
