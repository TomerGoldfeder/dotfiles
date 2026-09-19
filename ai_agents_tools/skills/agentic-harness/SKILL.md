---
name: agentic-harness
description: >
  Orchestrates multi-step coding as a task DAG of isolated subagent roles
  (classifier, explorer, planner, worker, QA, critic, promoter, journaler). Use this
  skill for features, refactors, and any multi-step
  implementation. Use even
  if they never say harness, DAG, or agentic-harness.
---

# Agentic harness

Parent agent is the orchestrator. Roles stay in separate subagents because
one prompt that plans, implements, and critiques itself mixes objectives and
produces weaker work.

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
4. For each node, spawn a role agent. Prompt, model, and extra skill attaches are the same on either spawn path:
   - Prompt = that role's markdown + the node record + run-dir paths + summaries of dependency nodes.
   - Model = role frontmatter `model`, except the **first implementation worker** uses `cursor-grok-4.5-high`. That is the first node with `role: worker` whose `id` is **not** `worker-second-brain-writeback`. Write-back is last among workers and must not steal this override. If the spawn path can pass a model (Cursor Task `model`, or native args after `--` when the herdr kind documents it), use this value. Do not invent a model flag.
   - **journaler**: also attach `performance-journaler/SKILL.md`.
   - **explorer-second-brain** or **worker-second-brain-writeback**: also attach `second-brain/SKILL.md` (same pattern as journaler + performance-journaler).
   - **Spawn path gate is `HERDR_ENV` only.** Treat the gate as true iff `HERDR_ENV` is exactly `1` (`test "${HERDR_ENV:-}" = 1`). Do **not** gate on “the user mentioned herdr this turn.” The user already asked this harness to use the herdr CLI whenever the orchestrator is inside Herdr (`HERDR_ENV=1`). Mentioning herdr in chat does not attach the skill or switch spawn path if the env is unset.
   - **When `HERDR_ENV` is unset, empty, or not `1`:** keep current Cursor Task spawn **exactly as today**. Explorer may use an explore-style subagent; other roles use a general-purpose (or equivalent Task) subagent. **Do not attach** `herdr/SKILL.md`. The upstream herdr skill STOPs unless `HERDR_ENV=1`; attaching it outside Herdr would poison every node.
   - **When `HERDR_ENV=1`:** also attach `herdr/SKILL.md` from the agent skill homes (same attach pattern as journaler → `performance-journaler/SKILL.md`). Spawn and control that role agent with the herdr CLI from that skill. Do not invent a control plane, wrapper daemon, or extra scripts.
     - Prefer an existing available shell pane (interactive prompt, shell in foreground, no command/editor/agent). Otherwise split a sibling in the current tab: `herdr pane split --current --direction right` (or `down` if the caller pane is narrow/tall) `--cwd "$PWD" --no-focus`. Parse the new pane id from JSON `.result.pane.pane_id`. Do not create a workspace, tab, or worktree unless the user asked for that topology.
     - Start: `herdr agent start <name> --kind <kind> --pane <id>`. Default kind is **cursor** unless the original user request asked for another kind from the installed list (`herdr agent`, not guessed). Name uniquely among live agents, matching `[a-z][a-z0-9_-]{0,31}`, derived from the node id (slug of the id; shorten if needed).
     - Drive work with `herdr agent prompt <name> "…" --wait` (timeout as needed) and, if wait fails or returns `blocked`, `herdr agent get` / `herdr agent read` before sending more input. Do not blindly re-prompt on timeout.
     - Follow herdr skill safety: `--no-focus` for background work; parse IDs from JSON (do not invent them); do not close panes, tabs, or workspaces you did not create unless the user asked; never run bare `herdr` (that launches the TUI).
   - After it finishes, write `nodes/<id>.md` and report a short summary to the user.
5. After a **critic** node with `verdict: fail`, route to `route_to` (explorer, planner, or worker). Skip **all** subsequent nodes except the reroute targets — not only promoter and journaler. That includes `worker-second-brain-writeback` (no vault persist on fail). If `route_to` is `explorer` and `target_node_id` is unset, re-run the **repo** explorer (`id: explorer`), not `explorer-second-brain`. If `target_node_id` is set, re-run that node (and later dependents: qa, critic; write-back only if critic later passes). Increment `critic_reroutes`. After 3 reroutes, run promoter, then journaler (journaler must not persist; work was not approved); **skip write-back**. Stop and report remaining findings. Do not loop forever.
   Do not run `worker-second-brain-writeback` unless the quality gate passed (easy: QA pass; hard: critic `verdict: pass`).
6. **Promoter** is last user-facing step. Always write user-facing communication in the parent chat. Branch/commit/push/open PR only if the original user request asked for a PR or MR. Then put the PR URL at the end.
7. **Journaler** is last on every graph, after promoter. Persist only approved work (see `nodes/journaler.md`).

## DAG shape (coding family)

Classifier must emit one of the templates in `graphs/coding.md`. It may split the worker into multiple task nodes. It must not invent new roles. Every template (this family and later ones) ends with journaler after promoter.

## Output

Keep the user informed: printed DAG, then per-node summaries, then promoter text.
