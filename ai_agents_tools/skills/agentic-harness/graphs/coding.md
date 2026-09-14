# Coding graph family

Classifier picks **easy** or **hard**, then emits a task DAG using only roles from INDEX.

## Easy

Tiny plan, implement, test, tell the user. No explorer. No critic. Why: cheap path when robustness overhead would cost more than the change.

Order:

1. `planner` — 1–3 worker tasks, short. Not a design novel.
2. One `worker` per planned task.
3. `qa`
4. `promoter`
5. `journaler`

## Hard

Need exploration and a critic because the change has many moving parts or high regression risk.

Order:

1. `explorer`
2. `planner` — explicit task DAG (ids, depends_on, titles). Worker nodes are the tasks.
3. One `worker` per task, serial topo order.
4. `qa`
5. `critic`
6. `promoter`
7. `journaler`

Planner may add extra worker tasks after explorer. Classifier's initial DAG may be refined by the planner node; orchestrator then executes the **planner's** DAG for remaining work (replace worker list, keep qa/critic/promoter/journaler unless planner says otherwise). Write the updated graph to `DAG.md`.
