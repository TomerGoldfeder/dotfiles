"""Pre-shaped DAG templates — the compiler picks one and optionally adds/drops nodes."""

from dag_harness.models import DAG, DAGNode, DAGEdge


def fast_path() -> DAG:
    """Trivial tasks: implement → self-review → qa → promote. Minimal overhead."""
    return DAG(
        nodes=[
            DAGNode(id="implement", manifest_id="implement"),
            DAGNode(id="self-review", manifest_id="self-review"),
            DAGNode(id="qa", manifest_id="qa"),
            DAGNode(id="promote", manifest_id="promote"),
            DAGNode(id="debug-fix", manifest_id="debug-fix"),
            DAGNode(id="escalate", manifest_id="escalate"),
        ],
        edges=[
            DAGEdge(from_node="implement", to_node="self-review"),
            DAGEdge(from_node="self-review", to_node="qa"),
            DAGEdge(from_node="qa", to_node="promote", condition="on_pass"),
            DAGEdge(from_node="qa", to_node="debug-fix", condition="on_fail"),
            DAGEdge(from_node="qa", to_node="escalate", condition="on_escalate"),
            DAGEdge(from_node="debug-fix", to_node="escalate", condition="on_escalate"),
        ],
        template_source="fast-path",
    )


def full_loop() -> DAG:
    """Standard tasks: spec → acceptance-tests → plan → implement → self-review → critic → qa → promote."""
    return DAG(
        nodes=[
            DAGNode(id="spec", manifest_id="spec"),
            DAGNode(id="acceptance-tests", manifest_id="acceptance-tests"),
            DAGNode(id="plan", manifest_id="plan"),
            DAGNode(id="implement", manifest_id="implement"),
            DAGNode(id="self-review", manifest_id="self-review"),
            DAGNode(id="critic", manifest_id="critic"),
            DAGNode(id="qa", manifest_id="qa"),
            DAGNode(id="promote", manifest_id="promote"),
            DAGNode(id="debug-fix", manifest_id="debug-fix"),
            DAGNode(id="escalate", manifest_id="escalate"),
        ],
        edges=[
            DAGEdge(from_node="spec", to_node="acceptance-tests"),
            DAGEdge(from_node="spec", to_node="plan"),
            DAGEdge(from_node="acceptance-tests", to_node="plan"),
            DAGEdge(from_node="plan", to_node="implement"),
            DAGEdge(from_node="implement", to_node="self-review"),
            DAGEdge(from_node="self-review", to_node="critic"),
            DAGEdge(from_node="critic", to_node="qa", condition="on_pass"),
            DAGEdge(from_node="critic", to_node="debug-fix", condition="on_fail"),
            DAGEdge(from_node="qa", to_node="promote", condition="on_pass"),
            DAGEdge(from_node="qa", to_node="debug-fix", condition="on_fail"),
            DAGEdge(from_node="qa", to_node="escalate", condition="on_escalate"),
            DAGEdge(from_node="critic", to_node="escalate", condition="on_escalate"),
            DAGEdge(from_node="debug-fix", to_node="escalate", condition="on_escalate"),
        ],
        template_source="full-loop",
    )


def research_heavy() -> DAG:
    """Complex tasks with unknowns: explore + research → spec → plan → implement → critic → qa → promote."""
    return DAG(
        nodes=[
            DAGNode(id="explore", manifest_id="explore"),
            DAGNode(id="research", manifest_id="research"),
            DAGNode(id="spec", manifest_id="spec"),
            DAGNode(id="acceptance-tests", manifest_id="acceptance-tests"),
            DAGNode(id="plan", manifest_id="plan"),
            DAGNode(id="implement", manifest_id="implement"),
            DAGNode(id="self-review", manifest_id="self-review"),
            DAGNode(id="critic", manifest_id="critic"),
            DAGNode(id="qa", manifest_id="qa"),
            DAGNode(id="promote", manifest_id="promote"),
            DAGNode(id="debug-fix", manifest_id="debug-fix"),
            DAGNode(id="escalate", manifest_id="escalate"),
        ],
        edges=[
            # Explore and research run in parallel (no deps between them)
            DAGEdge(from_node="explore", to_node="spec"),
            DAGEdge(from_node="research", to_node="spec"),
            DAGEdge(from_node="spec", to_node="acceptance-tests"),
            DAGEdge(from_node="spec", to_node="plan"),
            DAGEdge(from_node="acceptance-tests", to_node="plan"),
            DAGEdge(from_node="plan", to_node="implement"),
            DAGEdge(from_node="implement", to_node="self-review"),
            DAGEdge(from_node="self-review", to_node="critic"),
            DAGEdge(from_node="critic", to_node="qa", condition="on_pass"),
            DAGEdge(from_node="critic", to_node="debug-fix", condition="on_fail"),
            DAGEdge(from_node="qa", to_node="promote", condition="on_pass"),
            DAGEdge(from_node="qa", to_node="debug-fix", condition="on_fail"),
            DAGEdge(from_node="qa", to_node="escalate", condition="on_escalate"),
            DAGEdge(from_node="critic", to_node="escalate", condition="on_escalate"),
            DAGEdge(from_node="debug-fix", to_node="escalate", condition="on_escalate"),
        ],
        template_source="research-heavy",
    )


TEMPLATES = {
    "fast-path": fast_path,
    "full-loop": full_loop,
    "research-heavy": research_heavy,
}


def get_template(name: str) -> DAG:
    if name not in TEMPLATES:
        raise KeyError(f"Unknown template: {name}. Available: {list(TEMPLATES.keys())}")
    return TEMPLATES[name]()
