---
name: dag-harness
description: >-
  Dynamic DAG harness for task-specific compilation and execution. Replaces fixed
  linear phase machines with a classify → compile → execute pipeline where each node
  runs as an isolated bb thread/subagent. Use when the user says "run the harness",
  "DAG harness", "harness this task", "dag loop", wants dynamic task routing, or asks
  to execute a development task through the DAG pipeline. Also trigger when the user
  mentions "classify and execute", "compile a DAG", or "run nodes on this task".
---

# DAG Harness

A dynamic DAG harness that sizes a task, compiles a task-specific graph from reusable
nodes, validates it, then executes it — with each node running as an isolated
thread/subagent and infrastructure concerns (checkpoint, audit, budget) as middleware.

## Quick start

When this skill triggers, follow these steps in order.

### Step 1: Locate the harness package

The harness code lives in this skill's directory:

```
<this_skill_dir>/dag_harness/
```

Add it to the Python path:

```python
import sys
sys.path.insert(0, "<this_skill_dir>")
```

Replace `<this_skill_dir>` with the resolved absolute path of this SKILL.md's parent
directory.

### Step 2: Run the harness

```python
from dag_harness.harness import DagHarness
from dag_harness.models import ExecutionBackend

harness = DagHarness(
    backend=ExecutionBackend.BB_THREAD,  # or .SUBAGENT for non-bb IDEs
    # project_id and parent_thread_id auto-resolve from BB_PROJECT_ID / BB_THREAD_ID
)

result = harness.run(task="<the user's task description>")
```

### Step 3: Report results

After the harness completes, report to the user:
- Classification result (size + template chosen)
- Nodes executed and their results
- Any escalations or failures
- Audit trail summary
- Links to spawned thread IDs (if bb threads were used)

## Architecture (4 roles)

```
Task → CLASSIFIER → COMPILER(+critic) → dag.json → EXECUTOR → [bb threads] → Result
                                                        ↕
                                              middleware wraps every dispatch
                                              (checkpoint / audit / budget)
```

1. **Classifier** — sizes task as trivial/standard/complex, picks template hint. No DAG
   modification. Rule-based by default, swappable for LLM-backed.
2. **Compiler + DAG Critic** — selects template, applies add/drop from permitted set,
   runs 4 mandatory checks (acyclic, dependency closure, budget, escalation reachability).
   Freezes validated dag.json. Retries once on failure, then escalates.
3. **Executor** — mechanical. Resolves dependency readiness, dispatches nodes as bb
   threads (or subagents), parses result contracts, routes by status. Manages bounded
   retry loops (debug-fix → qa, max 3 cycles).
4. **Nodes** — 13 types across 6 categories. Each gets only its required artifacts +
   role instructions. Must produce a machine-parseable result contract.

## Templates

| Template | When | Flow |
|---|---|---|
| fast-path | Trivial (typo, rename, one-liner) | implement → self-review → qa → promote |
| full-loop | Standard (features, bugs) | spec → acceptance-tests → plan → implement → review → critic → qa → promote |
| research-heavy | Complex/unknown (new libs, APIs) | explore ∥ research → spec → ... → qa → promote |

## Execution backends

The harness supports two backends — set at init:

- **`ExecutionBackend.BB_THREAD`** (default) — each node spawns a bb thread via
  `bb thread spawn`. Threads are parented to the current thread, visible in bb UI,
  titled `[harness:<run-id>] <node-id>`. Uses `bb thread wait` + `bb thread output`
  to collect results.

- **`ExecutionBackend.SUBAGENT`** — placeholder for non-bb IDEs. When implemented,
  would use the IDE's native subagent mechanism (e.g., Cursor's Task tool).

## Node result contract

Every node must end its output with:

```json
{
  "node_id": "<node-id>",
  "status": "pass | fail | escalate",
  "confidence": "high | medium | low",
  "artifacts": {"<name>": "<content>"},
  "evidence": "<raw output, not summary>",
  "next_hint": "<next-node-id> | null"
}
```

Rules:
- `confidence: low` → immediate escalation regardless of status
- `evidence` must be primary output (test runner stdout, git diff), not prose summary
- Artifacts referenced by name, never inlined into the result

## Recovery & escalation

- Retry loops bounded by MAX_DEBUG_FIX_CYCLES (3). Budget tracked in middleware.
- `escalate` is terminal — stops executor, surfaces audit trail to user.
- Budget exhaustion → escalate. No silent continuation.

## State storage

Per-run: `~/.harness_state/<run-id>/` containing:
- `dag.json` — frozen DAG
- `audit-log.jsonl` — append-only execution trace
- Artifact files
- Checkpoint snapshots

## Customization

### Add/drop nodes

```python
result = harness.run(
    task="...",
    add_nodes={"document", "regression-check"},
    drop_nodes={"acceptance-tests"},
)
```

Only nodes in the permitted add/drop sets are accepted. Unknown nodes silently ignored.

### Budget

```python
harness = DagHarness(max_budget=50.0)  # default is 30
```

### Thread configuration

```python
harness = DagHarness(
    provider="acp-claude",    # override bb provider per node
    model="claude-sonnet-4",  # override model
    thread_timeout=300,       # seconds to wait per node
)
```

## Constraints

- Do NOT modify the DAG after compilation (frozen artifact).
- Do NOT merge the 4 roles (classifier/compiler/executor/nodes).
- Do NOT put infrastructure concerns (audit/checkpoint/budget) into the DAG as nodes.
- Do NOT allow nodes to share conversational memory — artifacts only.
- Do NOT silently continue past budget or retry limits — always escalate.
