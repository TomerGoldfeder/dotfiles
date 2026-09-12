"""DAG executor — dispatches nodes as bb threads or subagents, manages flow."""

from __future__ import annotations

import json
import subprocess
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dag_harness.middleware import (
    AuditMiddleware, BudgetMiddleware, BudgetExhaustedError,
    CheckpointMiddleware, Middleware,
)
from dag_harness.models import (
    AuditEntry, Confidence, DAG, DAGNode, ExecutionBackend,
    NodeResult, NodeStatus, RunState,
)
from dag_harness.nodes import get_manifest

if TYPE_CHECKING:
    pass

MAX_RETRIES_PER_NODE = 3
MAX_DEBUG_FIX_CYCLES = 3


class NodeDispatcher(ABC):
    """Abstract backend for dispatching a single node."""

    @abstractmethod
    def dispatch(self, node: DAGNode, prompt: str, run_state: RunState) -> NodeResult:
        ...


class BBThreadDispatcher(NodeDispatcher):
    """Dispatch nodes as bb threads — visible in bb UI, proper context isolation."""

    def __init__(
        self,
        project_id: str,
        parent_thread_id: str | None = None,
        timeout: int = 600,
        provider: str | None = None,
        model: str | None = None,
    ):
        self.project_id = project_id
        self.parent_thread_id = parent_thread_id
        self.timeout = timeout
        self.provider = provider
        self.model = model

    def dispatch(self, node: DAGNode, prompt: str, run_state: RunState) -> NodeResult:
        cmd = [
            "bb", "thread", "spawn",
            "--project", self.project_id,
            "--prompt", prompt,
            "--title", f"[harness:{run_state.run_id[:8]}] {node.id}",
            "--permission-mode", "full",
            "--json",
        ]
        if self.parent_thread_id:
            cmd.extend(["--parent-thread", self.parent_thread_id])
        if self.provider:
            cmd.extend(["--provider", self.provider])
        if self.model:
            cmd.extend(["--model", self.model])

        spawn_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if spawn_result.returncode != 0:
            raise RuntimeError(f"Thread spawn failed: {spawn_result.stderr}")

        spawn_data = json.loads(spawn_result.stdout)
        thread_id = spawn_data["id"]
        run_state.thread_ids[node.id] = thread_id

        wait_cmd = [
            "bb", "thread", "wait", thread_id,
            "--status", "idle",
            "--timeout", str(self.timeout),
        ]
        subprocess.run(wait_cmd, capture_output=True, text=True, timeout=self.timeout + 30)

        output_cmd = ["bb", "thread", "output", thread_id, "--json"]
        output_result = subprocess.run(output_cmd, capture_output=True, text=True, timeout=30)

        if output_result.returncode != 0:
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.FAIL,
                confidence=Confidence.LOW,
                evidence=f"Failed to get thread output: {output_result.stderr}",
            )

        try:
            output_data = json.loads(output_result.stdout)
            raw_output = output_data.get("output", output_result.stdout)
        except json.JSONDecodeError:
            raw_output = output_result.stdout

        try:
            return NodeResult.parse_from_output(str(raw_output))
        except ValueError:
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.FAIL,
                confidence=Confidence.MEDIUM,
                evidence=f"Could not parse result contract from output (length={len(str(raw_output))})",
            )


class MockDispatcher(NodeDispatcher):
    """For testing — returns configurable results without spawning real threads."""

    def __init__(self, results: dict[str, NodeResult] | None = None):
        self.results = results or {}
        self.dispatch_log: list[dict] = []

    def dispatch(self, node: DAGNode, prompt: str, run_state: RunState) -> NodeResult:
        self.dispatch_log.append({
            "node_id": node.id,
            "prompt_length": len(prompt),
            "timestamp": time.time(),
        })

        if node.id in self.results:
            return self.results[node.id]

        manifest = get_manifest(node.manifest_id)
        artifacts = {p: f"<mock content for {p}>" for p in manifest.produces}

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.PASS,
            confidence=Confidence.HIGH,
            artifacts=artifacts,
            evidence=f"Mock execution of {node.id} — all checks passed",
        )


def build_node_prompt(
    node: DAGNode,
    task: str,
    run_state: RunState,
) -> str:
    """Construct the prompt injected into a node's bb thread."""
    manifest = get_manifest(node.manifest_id)

    artifact_section = ""
    for req in manifest.requires:
        if req in run_state.available_artifacts:
            content = run_state.available_artifacts[req]
            artifact_section += f"\n### Artifact: {req}\n```\n{content}\n```\n"
        else:
            artifact_section += f"\n### Artifact: {req}\n(not available — was optional)\n"

    return f"""You are executing the **{node.id}** node in a DAG harness run.

## Your Role
{manifest.instructions}

## Task
{task}

## Required Artifacts (injected from upstream nodes)
{artifact_section if artifact_section else "(none — this node has no dependencies)"}

## Output Contract (MANDATORY)
You MUST end your response with a JSON block in EXACTLY this format.
The executor parses this programmatically — do not omit any field.

```json
{{
  "node_id": "{node.id}",
  "status": "pass",
  "confidence": "high",
  "artifacts": {json.dumps({p: f"<your {p} content>" for p in manifest.produces})},
  "evidence": "<raw command output or test results — never a summary>",
  "next_hint": null
}}
```

Valid `status` values: "pass", "fail", "escalate"
Valid `confidence` values: "high", "medium", "low"

If you encounter issues, set status to "fail" and describe what went wrong in evidence.
If you believe the task should be escalated to a human, set status to "escalate".
"""


class Executor:
    """Walks the DAG, resolves dependencies, dispatches ready nodes."""

    def __init__(
        self,
        dag: DAG,
        run_state: RunState,
        dispatcher: NodeDispatcher,
        middleware: list[Middleware] | None = None,
    ):
        self.dag = dag
        self.run_state = run_state
        self.dispatcher = dispatcher
        self.middleware = middleware or [
            AuditMiddleware(),
            BudgetMiddleware(),
            CheckpointMiddleware(),
        ]
        self._debug_fix_cycles: dict[str, int] = {}
        self._pending_retry_node: str | None = None

    def execute(self, task: str) -> RunState:
        self.run_state.status = "running"

        while True:
            ready = self._get_ready_nodes()

            if not ready:
                if self._is_terminal():
                    if self.run_state.status == "running":
                        self.run_state.status = "completed"
                    break
                else:
                    self.run_state.status = "failed"
                    self.run_state.append_audit(AuditEntry(
                        node_id="executor",
                        event="stuck",
                        result_summary={"reason": "no ready nodes and not terminal"},
                    ))
                    break

            for node in ready:
                result = self._dispatch_with_middleware(node, task)
                self._process_result(node, result)

                if self.run_state.status in ("escalated", "failed"):
                    return self.run_state

        return self.run_state

    def _get_ready_nodes(self) -> list[DAGNode]:
        """Determine which nodes are ready for dispatch.

        Semantics:
        - If a node has unconditional incoming edges: ALL must be from completed
          predecessors. Conditional edges are ignored for gating (they're alternative
          triggers, not structural prerequisites).
        - If a node has ONLY conditional incoming edges: at least one must match
          (these are nodes gated purely on upstream status, like promote/debug-fix).
        - Artifact requires must all be satisfied in either case.
        """
        ready = []
        for node in self.dag.nodes:
            if node.id in self.run_state.completed_nodes:
                continue
            if node.id == "escalate":
                continue

            manifest = get_manifest(node.manifest_id)
            predecessors = self.dag.predecessors(node.id)

            if not predecessors:
                if all(r in self.run_state.available_artifacts for r in manifest.requires):
                    ready.append(node)
                continue

            unconditional = [e for e in predecessors if not e.condition]
            conditional = [e for e in predecessors if e.condition]

            if unconditional:
                all_done = all(
                    e.from_node in self.run_state.completed_nodes
                    for e in unconditional
                )
                if not all_done:
                    continue
            elif conditional:
                any_match = any(
                    self._edge_condition_met(e) for e in conditional
                )
                if not any_match:
                    continue

            if all(r in self.run_state.available_artifacts for r in manifest.requires):
                ready.append(node)

        return ready

    def _edge_condition_met(self, edge: DAGEdge) -> bool:
        if edge.from_node not in self.run_state.completed_nodes:
            return False
        if not edge.condition:
            return True
        pred_result = self.run_state.completed_nodes[edge.from_node]
        cond_map = {
            "on_pass": NodeStatus.PASS,
            "on_fail": NodeStatus.FAIL,
            "on_escalate": NodeStatus.ESCALATE,
        }
        expected = cond_map.get(edge.condition)
        return pred_result.status == expected if expected else True

    def _dispatch_with_middleware(self, node: DAGNode, task: str) -> NodeResult:
        try:
            for mw in self.middleware:
                mw.before(node, self.run_state)
        except BudgetExhaustedError as e:
            self.run_state.append_audit(AuditEntry(
                node_id=node.id,
                event="budget_exhausted",
                result_summary={"error": str(e)},
            ))
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.ESCALATE,
                confidence=Confidence.HIGH,
                evidence=str(e),
                next_hint="escalate",
            )

        prompt = build_node_prompt(node, task, self.run_state)
        result = self.dispatcher.dispatch(node, prompt, self.run_state)

        for mw in self.middleware:
            mw.after(node, result, self.run_state)

        return result

    def _process_result(self, node: DAGNode, result: NodeResult):
        if result.confidence == Confidence.LOW:
            result.status = NodeStatus.ESCALATE
            result.next_hint = "escalate"

        self.run_state.completed_nodes[node.id] = result

        for name, content in result.artifacts.items():
            self.run_state.save_artifact(name, content)

        if result.status == NodeStatus.ESCALATE:
            self._handle_escalation(node, result)
            return

        if result.status == NodeStatus.FAIL:
            self._handle_failure(node, result)
            return

        # After debug-fix passes, re-enable the node that originally failed
        if node.id == "debug-fix" and self._pending_retry_node:
            retry_node = self._pending_retry_node
            self._pending_retry_node = None
            if retry_node in self.run_state.completed_nodes:
                del self.run_state.completed_nodes[retry_node]

    def _handle_escalation(self, node: DAGNode, result: NodeResult):
        self.run_state.status = "escalated"
        self.run_state.append_audit(AuditEntry(
            node_id=node.id,
            event="escalate",
            result_summary={"reason": result.evidence[:200]},
        ))

    def _handle_failure(self, node: DAGNode, result: NodeResult):
        cycle_key = f"{node.id}_debug_fix"
        current_cycles = self._debug_fix_cycles.get(cycle_key, 0)

        if current_cycles >= MAX_DEBUG_FIX_CYCLES:
            self.run_state.status = "escalated"
            self.run_state.append_audit(AuditEntry(
                node_id=node.id,
                event="retry_budget_exhausted",
                result_summary={"cycles": current_cycles},
            ))
            return

        has_debug_fix_edge = any(
            e.to_node == "debug-fix" and e.from_node == node.id
            for e in self.dag.edges
        )
        if has_debug_fix_edge and "debug-fix" in self.dag.node_ids():
            self._debug_fix_cycles[cycle_key] = current_cycles + 1
            # Clear debug-fix so it can be dispatched (its condition: failed node on_fail is met)
            if "debug-fix" in self.run_state.completed_nodes:
                del self.run_state.completed_nodes["debug-fix"]
            # Track which node to re-enable after debug-fix completes
            self._pending_retry_node = node.id
            self.run_state.append_audit(AuditEntry(
                node_id=node.id,
                event="retry",
                result_summary={"cycle": current_cycles + 1},
            ))
        else:
            self.run_state.status = "escalated"
            self.run_state.append_audit(AuditEntry(
                node_id=node.id,
                event="escalate_no_recovery_path",
                result_summary={"reason": "No debug-fix edge"},
            ))

    def _is_terminal(self) -> bool:
        completed_ids = set(self.run_state.completed_nodes.keys())
        terminal_nodes = {"promote", "document"}
        if completed_ids & terminal_nodes:
            return True
        # Also terminal if all dispatchable nodes are done
        active_nodes = {n.id for n in self.dag.nodes if n.id != "escalate"}
        non_recovery = {nid for nid in active_nodes
                        if nid not in ("debug-fix",)}
        return non_recovery.issubset(completed_ids)
