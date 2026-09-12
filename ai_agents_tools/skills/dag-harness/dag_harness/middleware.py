"""Infrastructure middleware — wraps every node dispatch (not DAG nodes)."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dag_harness.models import AuditEntry, DAGNode, NodeCost, NodeResult, NodeStatus

if TYPE_CHECKING:
    from dag_harness.models import RunState


class Middleware(ABC):
    @abstractmethod
    def before(self, node: DAGNode, run_state: RunState) -> None: ...

    @abstractmethod
    def after(self, node: DAGNode, result: NodeResult, run_state: RunState) -> None: ...


class AuditMiddleware(Middleware):
    """Append dispatch/complete entries to audit-log.jsonl."""

    def before(self, node: DAGNode, run_state: RunState) -> None:
        run_state.append_audit(AuditEntry(node_id=node.id, event="dispatch"))

    def after(self, node: DAGNode, result: NodeResult, run_state: RunState) -> None:
        run_state.append_audit(AuditEntry(
            node_id=node.id,
            event="complete",
            result_summary={
                "status": result.status.value,
                "confidence": result.confidence.value,
            },
        ))


class BudgetMiddleware(Middleware):
    """Track cost and trigger escalation when budget exhausted."""

    def before(self, node: DAGNode, run_state: RunState) -> None:
        from dag_harness.nodes import get_manifest
        manifest = get_manifest(node.manifest_id)
        cost = manifest.cost.units
        if run_state.budget_remaining < cost:
            raise BudgetExhaustedError(
                f"Budget exhausted: need {cost}, have {run_state.budget_remaining}"
            )

    def after(self, node: DAGNode, result: NodeResult, run_state: RunState) -> None:
        from dag_harness.nodes import get_manifest
        manifest = get_manifest(node.manifest_id)
        run_state.budget_spent += manifest.cost.units


class CheckpointMiddleware(Middleware):
    """Snapshot state before medium/high cost nodes (stub — can be extended for git stash)."""

    def before(self, node: DAGNode, run_state: RunState) -> None:
        from dag_harness.nodes import get_manifest
        manifest = get_manifest(node.manifest_id)
        if manifest.cost in (NodeCost.MEDIUM, NodeCost.HIGH):
            checkpoint_path = run_state.state_dir / f"checkpoint-before-{node.id}.json"
            import json
            checkpoint_path.write_text(json.dumps({
                "node_id": node.id,
                "timestamp": time.time(),
                "completed_nodes": list(run_state.completed_nodes.keys()),
                "budget_spent": run_state.budget_spent,
            }, indent=2))

    def after(self, node: DAGNode, result: NodeResult, run_state: RunState) -> None:
        pass


class BudgetExhaustedError(Exception):
    pass
