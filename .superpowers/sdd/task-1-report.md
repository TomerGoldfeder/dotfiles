# Task 1 report: Design spec file

## Status

DONE

## What was done

Created `docs/superpowers/specs/2026-09-13-agentic-harness-design.md` from the plan’s Spec (locked interview) and Global Constraints.

Coverage includes: purpose and isolation rationale, trigger/precedence (vs `tdd-loop` only), skill identity + Nix install path, layout and progressive INDEX load, coding-only graph family + INDEX extension hook, easy/hard templates, roles, full orchestrator algorithm, state path formula, classifier/critic JSON shapes, critic routing with cap 3, QA scope, model table + first-worker strong override, promoter PR rule, implementation process constraints, and non-goals.

## Self-review vs Global Constraints

Checked each Global Constraint appears in the spec (skill identity, markdown-only / no Python / no dag-harness revival, serial topo, models + first-worker, no tdd-loop unless named, print DAG before workers, per-node summaries, line limits, omit disable-model-invocation, pushy third-person description, promoter PR rule, critic cap 3, QA scope, easy/hard shapes, classifier emits DAG, state path, role jobs, invalid model → INDEX default, normal prose, process: no commit/push/git-config/--no-verify, current checkout / no worktrees, ignore unrelated dirt, no science graph).

No TBD placeholders found.

## Files

- Created: `docs/superpowers/specs/2026-09-13-agentic-harness-design.md`
- Not modified: skill files, `home.nix`, `AGENTS.md`

## Commits

none (per brief)

## Tests

n/a (markdown design spec)

## Concerns

none

## Notes for later tasks

Task 2 should treat this spec as canonical for behavior when chat memory conflicts; plan Global Constraints still win on process. Task 2 file bodies are already specified verbatim in the plan.
