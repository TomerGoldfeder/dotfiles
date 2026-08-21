---
name: tdd-loop
description: Phase-gated TDD development loop for building or refactoring code against user-approved acceptance tests. Use this skill whenever the user asks to build a feature, create code from scratch, do a significant refactoring, or mentions "the loop", "TDD loop", "agent loop", or wants development driven by tests with interview → tests → plan → implement → polish → QA phases. Trigger even if the user just states a coding objective and asks to "run the loop" on it.
---

# TDD Loop

A phase-gated development loop. You (the agent) are the loop engine; state lives
in files so the loop survives context loss, session restarts, and works in any
agent environment (Claude Code, Cursor, claude.ai, etc.).

## Core rules (apply to EVERY action in this skill)

1. **State file first.** Before any phase action, read the task's `STATE.md`.
   After any phase action, update it. The state file is the truth; your memory
   of the conversation is not.
2. **Show your work.** You may only mark a phase transition in STATE.md after
   pasting the required EVIDENCE (defined per phase) into the conversation in
   the current session. Never assert "tests pass" — show the actual runner
   output. No evidence = no transition.
3. **Acceptance tests are frozen after user approval.** Never edit files under
   `tests/acceptance/` after the freeze commit. QA auto-fails the task if they
   changed (checked via git diff, not trust).
4. **Budgets are hard.** When a budget is exhausted, STOP and report to the
   user. Never silently continue looping.
5. **Code standards are mandatory when available.** Phases 5 and 6 MUST follow
   the `code-standards` skill at `standards_ref` when it exists: read the
   skill → load `standards/INDEX.md` in that skill's directory → read every
   applicable rule file from `standards/` in full. Skipping this workflow when
   the skill is present is not allowed.
   **Fallback:** if `standards_ref`, `standards/INDEX.md`, or the `standards/`
   directory is missing,
   ignore code-standards and apply idiomatic best practices for the repo's
   programming language instead. This fallback MUST be written explicitly in
   STATE.md (`standards_mode`, `standards_fallback_note`) and stated in the
   conversation — never silent.

## Loop state root (cross-platform)

All task state lives under a single directory in the **current user's home folder**.
Resolve it at the start of every session (new task or resume). Do not hardcode
`~/.loop_state` — that path is Unix-oriented and wrong on Windows.

### Resolve `loop_state_root`

1. Detect the OS (`platform.system()`, `uname`, or shell hints).
2. Resolve the user home directory:
   | OS | Home directory |
   |----|----------------|
   | Linux / macOS | `$HOME` → e.g. `/home/user`, `/Users/user` |
   | Windows | `%USERPROFILE%` → e.g. `C:\Users\user` |
3. Set `loop_state_root = <home> / ".loop_state"` (use OS-native separators).

**Preferred (works on all OSes):**
```bash
python -c "import pathlib; p=pathlib.Path.home()/'.loop_state'; p.mkdir(parents=True, exist_ok=True); print(p.resolve())"
```

**Shell fallback:**
- Unix/macOS: `mkdir -p "$HOME/.loop_state" && echo "$HOME/.loop_state"`
- Windows: `mkdir "%USERPROFILE%\.loop_state" 2>nul & echo %USERPROFILE%\.loop_state`

### Create if missing

If `loop_state_root` does not exist → create it (`mkdir -p` / `mkdir` as above).
State this path once in the conversation when first created.

Record the resolved absolute path in each task's STATE.md as `loop_state_root:`.

## State layout (multi-task, versioned)

All loop state lives OUTSIDE the repo, under `<loop_state_root>/`:

```
<loop_state_root>/
└── <task-id>/                  # <YYYY-MM-DD>_<objective-slug-30ch>_<6-char-hash>
    ├── STATE.md                # phase, repo path, decisions, counters, evidence log
    ├── spec.md                 # behavioral spec from the interview
    ├── plan.md                 # implementation plan
    └── qa-verdict-<N>.json     # one per QA cycle N — never overwrite previous
```

- **New task**: resolve `loop_state_root` (create if needed), generate the task id
  (date + slugified objective + random hash), create `<loop_state_root>/<task-id>/`,
  copy `templates/STATE.md` into it, fill in `created_at` (local timestamp,
  e.g. `2026-07-30 12:00:00`), objective, repo path, and `loop_state_root`. Tell the user the task id and the resolved state path.
- **Resume**: read `loop_state_root` from STATE.md if present; otherwise resolve
  fresh. List `<loop_state_root>/*/STATE.md`, match `repo:` to the current repo,
  prefer status `in_progress`. If several match, ask the user which.
- Multiple tasks (even parallel, in different repos/worktrees) never share a
  state dir. Never write loop state inside the repo.

## Phase machine

Read ONLY the phase file for the current phase (progressive disclosure):

| Phase | File | Exit evidence required |
|---|---|---|
| 1 interview | `phases/01-interview.md` | user answered; spec.md written |
| 2 acceptance-tests | `phases/02-acceptance-tests.md` | red run output + user approval + freeze commit sha shown to user |
| 3 plan | `phases/03-plan.md` | plan.md + alignment check verdict |
| 4 implement | `phases/04-implement.md` | unit test runner output: 0 failures |
| 5 polish | `phases/05-polish.md` | standards_mode set + rule files or explicit fallback + green unit run |
| 6 qa | `phases/06-qa.md` | qa-verdict-N.json with standards_violations + test output + acceptance diff |

Routing decisions (loop-backs) are defined inside phases 3, 4, and 6. Follow
them exactly; they are the only legal back-edges.

## QA loop-back (phase 6 → 3 or → 4)

After QA writes `qa-verdict-<N>.json` with `decision: NO_SHIP`:
- **Any violation with `route: "plan"`** → phase 3. Planner triages: updates
  plan.md for structural issues, writes `## Implement checklist` in plan.md
  for `route: implement` items → phase 4 → 5 → 6.
- **All violations `route: implement` only** → phase 4 directly → 5 → 6.
- Present `standards_violations` to the user on every NO_SHIP.
- Increment `qa_cycles` before loop-back; max 3 cycles.

## Budgets (record counters in STATE.md)

- Interview: max 5 questions total (excluding user-initiated clarifications).
- Plan loop-back (phase 3 → 2 or → 1): max 1. Second misalignment → stop, report.
- Implement↔QA cycles: max 3. Exhausted → final verdict NO_SHIP, report to user.
- Any QA verdict with `confidence: "low"` → STOP and ask the user, regardless
  of decision. A low-confidence signal means the loop itself may need adjusting.

## Standards reference (phases 5 and 6)

`standards_ref` in STATE.md points to the `code-standards` skill (default:
`${DEPLOYMENT_FOR_MACHINE}/skills/code-standards/SKILL.md`). That
skill is the entry point; the actual rules are bundled in `standards/` next to
that skill (via `standards/INDEX.md`).

When the skill and rules are available, phases 5 and 6 must follow the full
workflow before reviewing or fixing code.

**When unavailable** (`standards_ref`, `standards/INDEX.md`, or `standards/`
missing):
fall back to idiomatic best practices for the repo's programming language.
Record explicitly in STATE.md:
- `standards_mode: language-default`
- `standards_fallback_note: <what was missing and which language defaults apply>`
Also state the fallback in the conversation and append to the decisions log.
Set `standards_mode: code-standards` when the full workflow was used.
