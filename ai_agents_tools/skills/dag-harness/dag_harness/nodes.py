"""Node manifest registry — declares every available node type."""

from dag_harness.models import NodeManifest, NodeCost

NODE_MANIFESTS: dict[str, NodeManifest] = {}


def _register(m: NodeManifest):
    NODE_MANIFESTS[m.id] = m


# ── 2.2 Context-gathering ──────────────────────────────────────────────

_register(NodeManifest(
    id="explore",
    category="context-gathering",
    requires=[],
    produces=["context-notes"],
    when="task touches unfamiliar/large parts of the codebase",
    skip_if="codebase already well-understood",
    cost=NodeCost.MEDIUM,
    instructions=(
        "Explore the codebase to understand relevant files, structure, and patterns. "
        "Produce a context-notes artifact summarizing what you found: key files, "
        "architecture patterns, dependencies, and anything the implementation needs to know."
    ),
))

_register(NodeManifest(
    id="research",
    category="context-gathering",
    requires=[],
    produces=["research-notes"],
    when="task needs an external library/API not already understood",
    skip_if="all APIs/libraries already known",
    cost=NodeCost.MEDIUM,
    instructions=(
        "Research the external library/API needed for this task. "
        "Produce research-notes covering: API surface, usage patterns, gotchas, "
        "version constraints, and example snippets."
    ),
))

_register(NodeManifest(
    id="interview",
    category="context-gathering",
    requires=[],
    produces=["spec-seed"],
    when="task under-specified by the user",
    skip_if="task is fully specified",
    cost=NodeCost.LOW,
    instructions=(
        "The task description is under-specified. Generate a spec-seed document that: "
        "1) Lists assumptions being made, 2) Identifies ambiguities, "
        "3) Proposes default choices for each ambiguity with rationale. "
        "This becomes input to the spec node."
    ),
))

# ── 2.3 Definition ─────────────────────────────────────────────────────

_register(NodeManifest(
    id="spec",
    category="definition",
    requires=[],
    produces=["spec.md"],
    when="always, unless classifier marks task trivial",
    skip_if="task is trivial one-liner",
    cost=NodeCost.MEDIUM,
    instructions=(
        "Write a behavioral specification for the task. Include: "
        "1) What the code should do (functional requirements), "
        "2) Edge cases and error handling, "
        "3) Acceptance criteria. Output as spec.md artifact."
    ),
))

_register(NodeManifest(
    id="acceptance-tests",
    category="definition",
    requires=["spec.md"],
    produces=["frozen-tests"],
    when="task changes user-observable behavior",
    skip_if="task is a one-line fix or pure refactor",
    cost=NodeCost.MEDIUM,
    retryable=False,
    instructions=(
        "Given the spec, write acceptance tests that verify the specified behavior. "
        "Tests must be concrete and runnable. Once written, they are frozen — "
        "no modifications allowed after this node completes."
    ),
))

_register(NodeManifest(
    id="plan",
    category="definition",
    requires=["spec.md"],
    produces=["plan.md", "alignment-verdict"],
    when="always except trivial fixes",
    skip_if="trivial task",
    cost=NodeCost.MEDIUM,
    instructions=(
        "Create an implementation plan covering: "
        "1) Files to create/modify, 2) Implementation steps in order, "
        "3) Risk areas, 4) Testing approach. "
        "Also produce an alignment-verdict confirming the plan matches the spec."
    ),
))

# ── 2.4 Execution ──────────────────────────────────────────────────────

_register(NodeManifest(
    id="implement",
    category="execution",
    requires=["plan.md"],
    produces=["diff", "unit-test-output"],
    when="always",
    cost=NodeCost.HIGH,
    instructions=(
        "Implement the changes described in plan.md. "
        "Produce: 1) A diff artifact showing all changes made, "
        "2) unit-test-output showing test results. "
        "Follow the plan step by step. Run tests after implementation."
    ),
))

# ── 2.5 Verification ───────────────────────────────────────────────────

_register(NodeManifest(
    id="self-review",
    category="verification",
    requires=["diff"],
    produces=["review-notes"],
    when="always",
    cost=NodeCost.LOW,
    instructions=(
        "Review the diff for: 1) Correctness, 2) Edge cases missed, "
        "3) Code quality issues, 4) Security concerns. "
        "Produce review-notes with findings and severity ratings."
    ),
))

_register(NodeManifest(
    id="critic",
    category="verification",
    requires=["diff", "review-notes"],
    produces=["critic-verdict"],
    when="non-trivial task",
    skip_if="task is trivial",
    cost=NodeCost.MEDIUM,
    instructions=(
        "Act as a critical reviewer. Given the diff and review-notes, "
        "evaluate: 1) Does the implementation match the plan? "
        "2) Are there bugs or logical errors? 3) Is the code production-ready? "
        "Produce a critic-verdict with pass/fail and detailed findings."
    ),
))

_register(NodeManifest(
    id="qa",
    category="verification",
    requires=["diff"],
    produces=["qa-verdict"],
    when="always",
    cost=NodeCost.MEDIUM,
    instructions=(
        "Run all tests and verify the implementation. "
        "Check: 1) All tests pass, 2) Acceptance tests pass (if they exist), "
        "3) No regressions detected. "
        "Produce qa-verdict with pass/fail, test output, and confidence level."
    ),
))

_register(NodeManifest(
    id="regression-check",
    category="verification",
    requires=["diff"],
    produces=["regression-report"],
    when="task touches shared/high-blast-radius code",
    skip_if="change is isolated",
    cost=NodeCost.MEDIUM,
    instructions=(
        "Check for regressions in areas affected by the diff. "
        "Run broader test suites, check dependent modules, verify API contracts. "
        "Produce regression-report with findings."
    ),
))

# ── 2.6 Recovery ───────────────────────────────────────────────────────

_register(NodeManifest(
    id="debug-fix",
    category="recovery",
    requires=["qa-verdict"],
    produces=["diff", "unit-test-output"],
    when="triggered by qa or critic failure",
    cost=NodeCost.HIGH,
    instructions=(
        "The previous QA/critic check failed. Analyze the failing verdict, "
        "identify root cause, fix the code, and re-run tests. "
        "Produce updated diff and unit-test-output artifacts."
    ),
))

_register(NodeManifest(
    id="escalate",
    category="recovery",
    requires=[],
    produces=["escalation-report"],
    when="any node hits retry budget or emits confidence: low",
    cost=NodeCost.LOW,
    retryable=False,
    instructions=(
        "The harness is escalating to the user. Compile a report: "
        "1) What was attempted, 2) What failed and why, "
        "3) The full audit trail, 4) Recommended next steps for a human."
    ),
))

# ── 2.7 Communication ──────────────────────────────────────────────────

_register(NodeManifest(
    id="promote",
    category="communication",
    requires=["qa-verdict"],
    produces=["pr-description"],
    when="task is shippable",
    cost=NodeCost.LOW,
    instructions=(
        "The task passed QA. Produce a PR description / changelog entry: "
        "1) Summary of changes, 2) Testing done, 3) Breaking changes if any."
    ),
))

_register(NodeManifest(
    id="document",
    category="communication",
    requires=["qa-verdict"],
    produces=["doc-updates"],
    when="change is user-facing",
    skip_if="change is internal-only",
    cost=NodeCost.LOW,
    instructions=(
        "The task passed QA and is user-facing. "
        "Produce documentation updates covering the new/changed behavior."
    ),
))


def get_manifest(node_id: str) -> NodeManifest:
    if node_id not in NODE_MANIFESTS:
        raise KeyError(f"Unknown node: {node_id}")
    return NODE_MANIFESTS[node_id]


OPTIONAL_ADDABLE = {"explore", "research", "interview", "regression-check", "promote", "document"}
OPTIONAL_DROPPABLE = {"acceptance-tests", "spec", "self-review", "critic", "regression-check"}
