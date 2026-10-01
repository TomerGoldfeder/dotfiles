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

Parent agent is the orchestrator. It does not implement product code. Roles stay in separate subagents so one prompt does not plan, implement, and grade itself.

Speed rule: spawn a subagent only when that role produces a judgment or an edit the parent must not do. Classification and vault skips stay in the parent.

## Load order

1. Read `INDEX.md` (roles, models, id-specific files, state).
2. Read `graphs/coding.md`.
3. Read `nodes/classifier.md` and run it inline. Do not spawn a classifier.
4. Read a role file only at the moment you run that role. Id-specific file wins over the role file (`INDEX.md`). Pass that text in the spawn prompt. Tell the subagent not to read the role file, `SKILL.md`, or `INDEX.md` again.
5. Do not read every `nodes/*.md` up front. Do not also run brainstorming or writing-plans in this orchestration unless the user asked for a spec or a plan document.

## State

Resolve git root (or workspace). Create:

`~/.agentic_harness/<project-id>/<run-id>/`

- `project-id` = `<basename>_<first-8-hex-of-sha256(absolute-path)>`
- `run-id` = UTC `YYYY-MM-DDTHHMMSSZ_<slug>` where slug is the objective, max 40 chars, `[a-z0-9-]`

Write `classifier.json`, `DAG.md`, and `nodes/<id>.md` there. Create dirs if missing.

## Follow-up slice

Use this when all three are true: this chat already has a run dir for this repo; the new request corrects or extends the same behavior the last implementation worker touched; you can name that run dir.

Do not classify, explore, or re-plan. Append one implementation worker (new id, notes with `files`, `behavior`, `verify`, `standards`, `out of scope`) to that `DAG.md`. Spawn it, then `qa`, then `critic` only if `classifier.json` says `hard`, then write-back only if the gate passes, then promoter, then journaler.

A different goal is a new run. Start at Load order.

## Algorithm

1. Run **classifier inline**. Write `classifier.json` and `DAG.md`. No classifier subagent.
2. **Print the DAG** (copy of `DAG.md` or mermaid). Then execute. No confirmation gate.
3. Walk `dag.nodes` in serial topological order (`depends_on` must exist and introduce no cycles; if cycle, stop and report).
4. For each node, cheap-skip or spawn.

### Cheap skip (parent writes the node file, no subagent)

- `explorer-second-brain`: skip when `~/.second_brain_vault/index.md` is missing, or `wiki/` has no pages. Body includes `status: skipped` and the reason.
- `worker-second-brain-writeback`: skip when the vault was skipped, or the quality gate has not passed (easy: QA pass; hard: critic `verdict: pass`). Body includes `status: skipped` and the reason.

### Spawn

Prompt, in this order, and nothing else:

1. The role file text (id-specific file when INDEX has one).
2. The node record: `id`, `title`, `depends_on`, `notes`.
3. Repo root and run dir.
4. Dependency digests: the `## Output` section of each `nodes/<dep>.md`, capped at 400 words. Do not paste full node files, diffs, or other skills.

Model = the role file `model`, except the **first implementation worker** uses `cursor-grok-4.5-high`. That is the first node with `role: worker` whose `id` is not `worker-second-brain-writeback`. If the spawn path can pass a model (Cursor Task `model`, or native args after `--` when the herdr kind documents it), use this value. Do not invent a model flag.

Skill path attaches (one path, not the skill body):

- **journaler**: `performance-journaler/SKILL.md`
- **explorer-second-brain** or **worker-second-brain-writeback**, only when spawned: `second-brain/SKILL.md`
- Implementation workers, QA, critic, planner, promoter, and repo explorer: no extra skill body. The explorer brief and the worker `standards` line are the only convention inputs.

**Spawn path gate is `HERDR_ENV` only.** Treat the gate as true iff `HERDR_ENV` is exactly `1` (`test "${HERDR_ENV:-}" = 1`). Do **not** gate on “the user mentioned herdr this turn.” Mentioning herdr in chat does not attach the skill or switch spawn path if the env is unset.

- **When `HERDR_ENV` is unset, empty, or not `1`:** Cursor Task. Repo `explorer` may use an explore-style subagent; every other role uses a general-purpose subagent. **Do not attach** `herdr/SKILL.md`.
- **When `HERDR_ENV=1`:** also attach `herdr/SKILL.md`. Spawn and control that role agent with the herdr CLI. Do not invent a control plane, wrapper daemon, or extra scripts.
  - Prefer an existing available shell pane (interactive prompt, shell in foreground, no command/editor/agent). Otherwise split a sibling in the current tab: `herdr pane split --current --direction right` (or `down` if the caller pane is narrow/tall) `--cwd "$PWD" --no-focus`. Parse the new pane id from JSON `.result.pane.pane_id`. Do not create a workspace, tab, or worktree unless the user asked for that topology.
  - Start: `herdr agent start <name> --kind <kind> --pane <id>`. Default kind is **cursor** unless the original user request asked for another kind from the installed list (`herdr agent`, not guessed). Name uniquely among live agents, matching `[a-z][a-z0-9_-]{0,31}`, derived from the node id (slug of the id; shorten if needed).
  - Drive work with `herdr agent prompt <name> "…" --wait` (timeout as needed) and, if wait fails or returns `blocked`, `herdr agent get` / `herdr agent read` before sending more input. Do not blindly re-prompt on timeout.
  - Follow herdr skill safety: `--no-focus` for background work; parse IDs from JSON (do not invent them); do not close panes, tabs, or workspaces you did not create unless the user asked; never run bare `herdr` (that launches the TUI).

After the subagent finishes, it has written `nodes/<id>.md`. Report at most four lines to the user.

5. After a **critic** node with `verdict: fail`, route to `route_to` (explorer, planner, or worker). Skip **all** subsequent nodes except the reroute targets — including `worker-second-brain-writeback`. If `route_to` is `explorer` and `target_node_id` is unset, re-run the repo explorer (`id: explorer`), not `explorer-second-brain`. If `target_node_id` is set, re-run that node, then its later dependents (`qa`, `critic`; write-back only if critic later passes). The re-spawn prompt carries the critic JSON and that node's notes, not earlier node files. Increment `critic_reroutes`. After 3 reroutes, run promoter, then journaler (journaler must not persist; work was not approved); **skip write-back**. Stop and report remaining findings. Do not loop forever.
   Do not run `worker-second-brain-writeback` unless the quality gate passed (easy: QA pass; hard: critic `verdict: pass`).
6. **Promoter** is the last user-facing step. Paste its summary into the parent chat. Branch, commit, push, or open a PR only if the original user request asked for a PR or MR. Then put the URL at the end.
7. **Journaler** is last on every graph, after promoter. Persist only approved work (see `nodes/journaler.md`).

## DAG shape (coding family)

The inline classifier emits one template from `graphs/coding.md`. It may leave a single `worker-impl` placeholder. The planner replaces implementation workers and must not invent roles. Every template ends with journaler after promoter.

## Output

Printed DAG, then at most four lines per node, then the promoter text.
