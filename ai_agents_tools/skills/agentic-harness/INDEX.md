# Agentic harness index

Read this after `SKILL.md`. Read a node file only when spawning that role.

## Graph families

| family | file | when |
| coding | graphs/coding.md | software change in a repo (v1, always this) |

Later families (research, etc.) get a row here and a file under `graphs/`. Do not invent a family that has no file. Every family template ends with `journaler` (after `promoter`).

## Roles

| role | file | default model | job |
| classifier | nodes/classifier.md | cursor-grok-4.6-medium | complexity, family, initial DAG |
| explorer | nodes/explorer.md | cursor-grok-4.6-medium | context only, no edits |
| planner | nodes/planner.md | cursor-grok-4.5-high | task DAG / tiny plan |
| worker | nodes/worker.md | cursor-grok-4.6-medium | implement one task |
| qa | nodes/qa.md | cursor-grok-4.6-medium | run tests |
| critic | nodes/critic.md | cursor-grok-4.5-high | simplify and question |
| promoter | nodes/promoter.md | cursor-grok-4.5-high | communicate; PR only if asked |
| journaler | nodes/journaler.md | cursor-grok-4.5-high | last; journal only approved work |

Orchestrator override: first `role: worker` node uses `cursor-grok-4.5-high`.

YAML `model:` on a node file overrides the default for that role (first-worker override still wins for the first worker).

## State

`~/.agentic_harness/<project-id>/<run-id>/` — see `SKILL.md`.
