"""DAG compiler + critic — selects template, applies add/drop, validates."""

from __future__ import annotations

from dag_harness.models import (
    ClassifierOutput, DAG, DAGEdge, DAGNode, TaskSize, TemplateHint,
)
from dag_harness.nodes import (
    NODE_MANIFESTS, OPTIONAL_ADDABLE, OPTIONAL_DROPPABLE, get_manifest,
)
from dag_harness.templates import get_template


class DAGValidationError(Exception):
    pass


class Compiler:
    def __init__(self, max_budget: float = 30.0):
        self.max_budget = max_budget

    def compile(
        self,
        classifier_output: ClassifierOutput,
        add_nodes: set[str] | None = None,
        drop_nodes: set[str] | None = None,
        initial_artifacts: set[str] | None = None,
    ) -> DAG:
        """Compile a validated DAG from classifier output + optional modifications.

        Returns a frozen DAG that passed all critic checks.
        Raises DAGValidationError on second failure (first failure retries once).

        initial_artifacts: artifacts available at run start (e.g. synthetic plan.md
        for trivial tasks). These satisfy dependency closure without a producing node.
        """
        add_nodes = (add_nodes or set()) & OPTIONAL_ADDABLE
        drop_nodes = (drop_nodes or set()) & OPTIONAL_DROPPABLE
        initial = initial_artifacts or set()

        if classifier_output.size == TaskSize.TRIVIAL:
            drop_nodes |= {"acceptance-tests", "spec", "critic"}
            initial |= {"plan.md"}

        dag = self._build(classifier_output.template_hint, add_nodes, drop_nodes)

        errors = self._validate(dag, initial)
        if errors:
            dag = self._build(classifier_output.template_hint, add_nodes, drop_nodes)
            errors = self._validate(dag, initial)
            if errors:
                raise DAGValidationError(
                    f"DAG validation failed after retry: {'; '.join(errors)}"
                )

        return dag

    def _build(
        self,
        template_hint: TemplateHint,
        add_nodes: set[str],
        drop_nodes: set[str],
    ) -> DAG:
        dag = get_template(template_hint.value)

        existing_ids = dag.node_ids()

        for nid in drop_nodes:
            if nid in existing_ids and nid not in ("escalate",):
                dag.nodes = [n for n in dag.nodes if n.id != nid]
                dag.edges = [
                    e for e in dag.edges
                    if e.from_node != nid and e.to_node != nid
                ]

        for nid in add_nodes:
            if nid not in existing_ids and nid in NODE_MANIFESTS:
                manifest = get_manifest(nid)
                dag.nodes.append(DAGNode(id=nid, manifest_id=nid))
                for req in manifest.requires:
                    producers = [
                        n.id for n in dag.nodes
                        if req in get_manifest(n.manifest_id).produces
                    ]
                    for pid in producers:
                        dag.edges.append(DAGEdge(from_node=pid, to_node=nid))

        return dag

    def _validate(self, dag: DAG, initial_artifacts: set[str] | None = None) -> list[str]:
        errors: list[str] = []
        errors.extend(self._check_acyclic(dag))
        errors.extend(self._check_dependency_closure(dag, initial_artifacts or set()))
        errors.extend(self._check_budget(dag))
        errors.extend(self._check_escalation_reachability(dag))
        return errors

    def _check_acyclic(self, dag: DAG) -> list[str]:
        """Detect cycles via DFS. Conditional edges (on_fail, on_escalate) are
        bounded recovery loops managed by the executor's retry limits — exclude
        them from structural cycle detection."""
        RECOVERY_CONDITIONS = {"on_fail", "on_escalate"}
        adj: dict[str, list[str]] = {n.id: [] for n in dag.nodes}
        for e in dag.edges:
            if e.condition in RECOVERY_CONDITIONS:
                continue
            if e.from_node in adj:
                adj[e.from_node].append(e.to_node)

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {nid: WHITE for nid in adj}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in adj.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    return True
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        for nid in adj:
            if color[nid] == WHITE:
                if dfs(nid):
                    return [f"Cycle detected involving node '{nid}'"]
        return []

    def _check_dependency_closure(
        self, dag: DAG, initial_artifacts: set[str],
    ) -> list[str]:
        """Every node's requires must be satisfiable by upstream produces or initial artifacts."""
        errors = []

        all_producible: set[str] = set(initial_artifacts)
        for n in dag.nodes:
            m = get_manifest(n.manifest_id)
            all_producible.update(m.produces)

        for node in dag.nodes:
            manifest = get_manifest(node.manifest_id)
            for req in manifest.requires:
                if req not in all_producible:
                    errors.append(
                        f"Node '{node.id}' requires '{req}' but nothing in the DAG "
                        f"or initial artifacts produces it"
                    )
        return errors

    def _check_budget(self, dag: DAG) -> list[str]:
        total = sum(get_manifest(n.manifest_id).cost.units for n in dag.nodes)
        if total > self.max_budget:
            return [f"DAG cost ({total}) exceeds budget ({self.max_budget})"]
        return []

    def _check_escalation_reachability(self, dag: DAG) -> list[str]:
        """Every failure-capable node must have a path to 'escalate'."""
        if "escalate" not in dag.node_ids():
            return ["No 'escalate' node in DAG"]

        failure_nodes = {"qa", "critic", "debug-fix"}
        present_failure_nodes = failure_nodes & dag.node_ids()

        adj: dict[str, set[str]] = {n.id: set() for n in dag.nodes}
        for e in dag.edges:
            if e.from_node in adj:
                adj[e.from_node].add(e.to_node)

        def can_reach_escalate(start: str) -> bool:
            visited = set()
            stack = [start]
            while stack:
                current = stack.pop()
                if current == "escalate":
                    return True
                if current in visited:
                    continue
                visited.add(current)
                stack.extend(adj.get(current, set()))
            return False

        errors = []
        for nid in present_failure_nodes:
            if not can_reach_escalate(nid):
                errors.append(f"Node '{nid}' has no path to 'escalate'")
        return errors
