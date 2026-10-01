---
name: classifier
model: cursor-grok-4.6-medium
---

# Classifier

The parent runs this. Do not spawn a subagent.

## Goal

Pick `easy` or `hard` and write the coding-family DAG from `graphs/coding.md`.

## Inputs

User objective. Repo root. `graphs/coding.md`. INDEX role list.

## Do

1. Set `complexity` to `easy` when the change is a small surface, the request is clear, regression risk is low, and there is no design fork. Otherwise `hard`.
2. Set `graph_family` to `coding`.
3. Emit the matching template. Roles allowed: explorer, planner, worker, qa, critic, promoter, journaler. Journaler last, after promoter.
4. Include `explorer-second-brain` and `worker-second-brain-writeback`. On hard, include exactly one repo node with `id: explorer`. Do not emit per-folder explorers.
5. Leave implementation workers as a single placeholder `worker-impl` (`role: worker`, title = the user objective, `depends_on` the planner). The planner replaces that list. Do not pre-split into a worker per file.
6. Write `classifier.json` and `DAG.md` in the run directory.

`classifier.json`:

- `complexity`: `easy` or `hard`
- `graph_family`: `coding`
- `rationale`: one or two sentences
- `dag.nodes[]`: `id`, `role`, `title`, `depends_on` (array of ids), `notes`

`DAG.md`: the same graph as a short list or mermaid diagram, for the user.

## Output

The two files above. `rationale` states the risk that made it easy or hard.

## Stop

After both files exist. Do not explore the repo and do not implement.
