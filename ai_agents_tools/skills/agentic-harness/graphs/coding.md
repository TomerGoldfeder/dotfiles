# Coding graph family

Parent applies this file while classifying. It picks **easy** or **hard**, then emits a task DAG using only roles from INDEX.

Fixed ids, every template:

- `explorer-second-brain` (`role: explorer`) — vault query. Parent skips the spawn when `~/.second_brain_vault/index.md` is missing or `wiki/` has no pages. Never write the vault.
- `worker-second-brain-writeback` (`role: worker`) — last worker, after the quality gate. Parent skips the spawn when the vault was skipped or the gate failed. When spawned, file approved durable facts only.

Do not invent a `second-brain` role. Do not add explorer ids other than `explorer-second-brain` and, on hard, `explorer`. One repo explorer surveys every area. A request for one subagent per folder is still that single explorer.

Implementation workers: default **one**. Split only when the pieces edit disjoint file sets and each piece has its own acceptance check. Easy max 3. Hard max 4. A rename or docs pass inside one package is one worker.

## Easy

Small surface, clear request, low regression risk, one or few files, no design fork.

Order:

1. `explorer-second-brain`
2. `planner` — 1–3 implementation workers
3. One `worker` per implementation task
4. `qa`
5. `worker-second-brain-writeback` — `depends_on` qa
6. `promoter`
7. `journaler`

No repo explorer. No critic.

## Hard

Many modules, unclear codebase, design choices, large refactor, or fragile correctness.

Order:

1. `explorer-second-brain`
2. `explorer` — `depends_on` `explorer-second-brain`
3. `planner`
4. One `worker` per implementation task, serial
5. `qa`
6. `critic`
7. `worker-second-brain-writeback` — `depends_on` critic
8. `promoter`
9. `journaler`

Planner may replace the implementation worker list only. Keep `explorer-second-brain`, `explorer` (hard), qa, critic (hard), `worker-second-brain-writeback`, promoter, and journaler. Write the updated graph to `DAG.md`.
