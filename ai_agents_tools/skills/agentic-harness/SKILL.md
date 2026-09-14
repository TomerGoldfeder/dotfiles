---
name: agentic-harness
description: >
  Orchestrates multi-step coding as a task DAG of isolated subagent roles
  (classifier, explorer, planner, worker, QA, critic, promoter). Use this
  skill for features, refactors, non-trivial bugfixes, and any multi-step
  implementation unless the user explicitly names tdd-loop or
  enhanced-workflow. Use even if they never say harness, DAG, or
  agentic-harness. Do not use for trivial one-line or typo-only edits.
---

# Agentic harness

Parent agent is the orchestrator. Roles stay in separate subagents because
one prompt that plans, implements, and critiques itself mixes objectives and
produces weaker work.

Do not load `enhanced-workflow` or `tdd-loop` unless the user named them.

## Load order

1. Read `INDEX.md` in this skill directory (node table, models, state path, graph families).
2. Read `graphs/coding.md` (v1 family). Do not read every `nodes/*.md` up front.
3. When spawning a role, read only that role's file from `INDEX.md`.

## State

Resolve git root (or workspace). Create:

`~/.agentic_harness/<project-id>/<run-id>/`

- `project-id` = `<basename>_<first-8-hex-of-sha256(absolute-path)>`
- `run-id` = UTC `YYYY-MM-DDTHHMMSSZ_<slug>` where slug is the objective, max 40 chars, `[a-z0-9-]`

Write `classifier.json`, `DAG.md`, and `nodes/<id>.md` there. Create dirs if missing.

## Algorithm

1. Spawn **classifier** subagent. Attach `nodes/classifier.md` and `graphs/coding.md`. Model from classifier frontmatter. Ask it to write `classifier.json` and `DAG.md` in the run dir.
2. **Print the DAG to the user** (copy of `DAG.md` or mermaid). Then execute. No confirmation gate.
3. Walk `dag.nodes` in serial topological order (`depends_on` must exist and introduce no cycles; if cycle, stop and report).
4. For each node, spawn a subagent:
   - Prompt = that role's markdown + the node record + run-dir paths + summaries of dependency nodes.
   - Model = role frontmatter `model`, except the **first worker** in the DAG uses `cursor-grok-4.5-high`.
   - Explorer may use an explore-style subagent; other roles use a general-purpose subagent.
   - After it finishes, write `nodes/<id>.md` and report a short summary to the user.
5. After a **critic** node with `verdict: fail`, route to `route_to` (explorer, planner, or worker). If `target_node_id` is set, re-run that worker (and later dependents: qa, critic). Increment `critic_reroutes`. After 3 reroutes, stop and report remaining findings. Do not loop forever.
6. **Promoter** is last. Always write user-facing communication in the parent chat. Branch/commit/push/open PR only if the original user request asked for a PR or MR. Then put the PR URL at the end.

## DAG shape (coding family)

Classifier must emit one of the templates in `graphs/coding.md`. It may split the worker into multiple task nodes. It must not invent new roles.

## Output

Keep the user informed: printed DAG, then per-node summaries, then promoter text.
