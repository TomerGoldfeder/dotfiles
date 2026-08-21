# Phase 1 — Interview

Goal: turn the user's objective into a behavioral spec precise enough to derive
black-box acceptance tests.

## Procedure
1. If a structured question tool is available in this environment, use it;
   otherwise ask in plain chat. Max 5 questions TOTAL for the task (budget in
   STATE.md — count them). Ask the most valuable first; batch, don't drip.
2. Question #1 is MANDATORY:
   **"Are there any user-facing APIs/interfaces? If so — what are they
   (operations, arguments, return values)?"**
3. Choose the remaining ≤4 from this taxonomy, ONLY where the answer changes
   observable behavior:
   - Not-found/empty semantics (what does a miss return?)
   - Error semantics (invalid input → which exception/error value?)
   - Mutation semantics (upsert vs error, partial updates, idempotency,
     last-write-wins)
   - Validation rules (types, ranges, nullability, uniqueness)
   - Acceptance examples (concrete input → output pairs)
   - Test seeding (how tests may arrange preconditions)
   Never ask about implementation choices (storage, frameworks, file layout).
4. Write `<task-dir>/spec.md`:
   - Restated objective (one paragraph)
   - Public API: each operation with signature and return type
   - Numbered behavioral rules as Given / When / Then
   - Error semantics table: condition → exact expected outcome
   - Acceptance examples from the interview
   - Out of scope + explicit assumptions for anything unanswered
   Every rule must be verifiable through the public API alone.

## Re-entry (loop-back from phase 3)
Append-only: ask ONLY the new open questions (they still count against the
5-question budget), update spec.md sections in place, log the change in STATE.md.

## Exit evidence
- spec.md exists and every interview answer maps to at least one numbered rule.
- Update STATE.md: phase → acceptance-tests, questions_used counter.
