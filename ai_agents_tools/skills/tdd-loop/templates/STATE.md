# Loop State — <task-id>

created_at: <YYYY-MM-DD HH:MM:SS>   # local time when task was created
task_id: <YYYY-MM-DD>_<slug>_<hash6>
objective: <verbatim user objective>
repo: <absolute path to the repo this task works on>
loop_state_root: <absolute path to .loop_state in user home; OS-resolved>
branch: <git branch, if one was created for the task>
status: in_progress        # in_progress | done | halted
phase: interview           # interview | acceptance-tests | plan | implement | polish | qa
standards_ref: ${DEPLOYMENT_FOR_MACHINE}/skills/code-standards/SKILL.md
standards_mode: code-standards       # code-standards | language-default
standards_fallback_note:             # required when standards_mode is language-default

## Budgets
questions_used: 0/5
plan_loopbacks: 0/1
qa_cycles: 0/3

## Contract
acceptance_freeze_sha: <set in phase 2>
last_qa_verdict: <set after each QA cycle, e.g. qa-verdict-1.json>

## Decisions log
<!-- append-only: one line per key decision / interview answer / loop-back, with date -->

## Evidence log
<!-- append-only: phase transitions with a pointer to the evidence shown
     e.g. "2026-07-29 implement→polish: unit run green (23 passed) shown in session" -->
