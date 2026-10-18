# Agentic harness index

Read this after `SKILL.md`. Read a node file only when running that role.

## Graph families

| family | file | when |
| coding | graphs/coding.md | software change in a repo (v1, always this) |

Later families get a row here and a file under `graphs/`. Do not invent a family that has no file. Every family template ends with `journaler` after `promoter`.

## Roles

| role | file | model | job |
| classifier | nodes/classifier.md | parent, no spawn | easy or hard, then the template DAG |
| explorer | nodes/explorer.md | sonnet | one bounded repo brief |
| planner | nodes/planner.md | sonnet | smallest worker list with acceptance checks |
| worker | nodes/worker.md | sonnet | implement one task |
| qa | nodes/qa.md | sonnet | run the plan's verify command |
| critic | nodes/critic.md | opus | pass or fail the diff |
| promoter | nodes/promoter.md | sonnet | user-facing summary |
| journaler | nodes/journaler.md | sonnet | journal approved work only |

Id-specific files replace the role file for that id:

| id | file |
| explorer-second-brain | nodes/explorer-second-brain.md |
| worker-second-brain-writeback | nodes/worker-second-brain-writeback.md |

Orchestrator override: the first implementation worker (`role: worker`, id not `worker-second-brain-writeback`) uses `opus`.

Spawn path: if `HERDR_ENV=1`, attach `herdr/SKILL.md` and spawn via the herdr CLI (`claude` kind). Otherwise spawn via the `cc` CLI alias (`claude --dangerously-skip-permissions`) as a headless subprocess, and do not attach herdr. Details: `SKILL.md`.

## State

`~/.agentic_harness/<project-id>/<run-id>/` — see `SKILL.md`.
