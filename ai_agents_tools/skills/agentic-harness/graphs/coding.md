# Coding graph family

Classifier picks **easy** or **hard**, then emits a task DAG using only roles from INDEX.

Node ids `explorer-second-brain` and `worker-second-brain-writeback` are part of every template. Same roles as INDEX (`explorer`, `worker`). Do not invent a `second-brain` role. Planner may replace **implementation** worker tasks; it must keep these two ids, plus qa / critic (hard) / promoter / journaler.

`explorer-second-brain` (`role: explorer`): query `~/.second_brain_vault` via the second-brain skill. Read `index.md` first. Cheap skip if the vault, index, or pages are missing/empty. **Never write the vault.** Findings go to `nodes/explorer-second-brain.md` in the run dir.

`worker-second-brain-writeback` (`role: worker`): last worker, after the quality gate. File **approved** durable facts via the second-brain skill (`compile`). Write only `wiki/`, `schema/`, `index.md`, `log.md`. Never mutate existing `raw/`. Never file secrets. Skip if QA failed (easy) or critic failed / reroute budget exhausted (hard).

## Easy

Tiny plan, implement, test, tell the user. No **repo** explorer. No critic. Vault query still runs. Why: cheap path when robustness overhead would cost more than the change.

Order:

1. `explorer-second-brain` — `role: explorer`. Vault query only.
2. `planner` — 1–3 implementation worker tasks, short. Not a design novel.
3. One `worker` per planned **implementation** task (`depends_on` planner / prior tasks).
4. `qa`
5. `worker-second-brain-writeback` — `role: worker`; `depends_on` qa.
6. `promoter`
7. `journaler`

## Hard

Need exploration and a critic because the change has many moving parts or high regression risk.

Order:

1. `explorer-second-brain` — `role: explorer`. Vault query only.
2. `explorer` — repo context; `depends_on` `explorer-second-brain`.
3. `planner` — explicit task DAG (ids, depends_on, titles). Implementation worker nodes are the tasks.
4. One `worker` per implementation task, serial topo order.
5. `qa`
6. `critic`
7. `worker-second-brain-writeback` — `role: worker`; `depends_on` critic.
8. `promoter`
9. `journaler`

Planner may add extra implementation worker tasks after explorer. Classifier's initial DAG may be refined by the planner node; orchestrator then executes the **planner's** DAG for remaining work (replace implementation worker list only; keep `explorer-second-brain`, qa, critic, `worker-second-brain-writeback`, promoter, journaler unless planner has a documented reason). Write the updated graph to `DAG.md`.
