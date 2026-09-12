"""Core data models for the DAG harness."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class TaskSize(Enum):
    TRIVIAL = "trivial"
    STANDARD = "standard"
    COMPLEX = "complex"


class TemplateHint(Enum):
    FAST_PATH = "fast-path"
    FULL_LOOP = "full-loop"
    RESEARCH_HEAVY = "research-heavy"


class NodeStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    ESCALATE = "escalate"


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionBackend(Enum):
    BB_THREAD = "bb_thread"
    SUBAGENT = "subagent"


class NodeCost(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def units(self) -> int:
        return {"low": 1, "medium": 3, "high": 5}[self.value]


@dataclass
class ClassifierOutput:
    size: TaskSize
    template_hint: TemplateHint
    reasons: str

    def to_dict(self) -> dict:
        return {
            "size": self.size.value,
            "template_hint": self.template_hint.value,
            "reasons": self.reasons,
        }


@dataclass
class NodeManifest:
    id: str
    category: str
    requires: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    when: str = "always"
    skip_if: str = ""
    cost: NodeCost = NodeCost.LOW
    retryable: bool = True
    instructions: str = ""
    max_retries: int = 3

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "requires": self.requires,
            "produces": self.produces,
            "when": self.when,
            "skip_if": self.skip_if,
            "cost": self.cost.value,
            "retryable": self.retryable,
            "max_retries": self.max_retries,
        }


@dataclass
class NodeResult:
    node_id: str
    status: NodeStatus
    confidence: Confidence
    artifacts: dict[str, str] = field(default_factory=dict)
    evidence: str = ""
    next_hint: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "confidence": self.confidence.value,
            "artifacts": self.artifacts,
            "evidence": self.evidence,
            "next_hint": self.next_hint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> NodeResult:
        return cls(
            node_id=data["node_id"],
            status=NodeStatus(data["status"]),
            confidence=Confidence(data["confidence"]),
            artifacts=data.get("artifacts", {}),
            evidence=data.get("evidence", ""),
            next_hint=data.get("next_hint"),
        )

    @classmethod
    def parse_from_output(cls, raw: str) -> NodeResult:
        """Extract JSON result block from thread/agent output."""
        # Find the last JSON block in the output
        last_json = None
        brace_depth = 0
        start_idx = None

        for i, ch in enumerate(raw):
            if ch == "{":
                if brace_depth == 0:
                    start_idx = i
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if brace_depth == 0 and start_idx is not None:
                    candidate = raw[start_idx : i + 1]
                    try:
                        parsed = json.loads(candidate)
                        if "node_id" in parsed and "status" in parsed:
                            last_json = parsed
                    except json.JSONDecodeError:
                        pass
                    start_idx = None

        if last_json is None:
            raise ValueError(
                f"No valid result JSON found in output (length={len(raw)})"
            )
        return cls.from_dict(last_json)


@dataclass
class DAGNode:
    id: str
    manifest_id: str

    def to_dict(self) -> dict:
        return {"id": self.id, "manifest_id": self.manifest_id}


@dataclass
class DAGEdge:
    from_node: str
    to_node: str
    condition: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"from": self.from_node, "to": self.to_node}
        if self.condition:
            d["condition"] = self.condition
        return d


@dataclass
class DAG:
    nodes: list[DAGNode] = field(default_factory=list)
    edges: list[DAGEdge] = field(default_factory=list)
    template_source: str = ""

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "template_source": self.template_source,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> DAG:
        nodes = [DAGNode(**n) for n in data["nodes"]]
        edges = [
            DAGEdge(
                from_node=e["from"],
                to_node=e["to"],
                condition=e.get("condition"),
            )
            for e in data["edges"]
        ]
        return cls(
            nodes=nodes,
            edges=edges,
            template_source=data.get("template_source", ""),
        )

    def successors(self, node_id: str) -> list[DAGEdge]:
        return [e for e in self.edges if e.from_node == node_id]

    def predecessors(self, node_id: str) -> list[DAGEdge]:
        return [e for e in self.edges if e.to_node == node_id]

    def node_ids(self) -> set[str]:
        return {n.id for n in self.nodes}


@dataclass
class AuditEntry:
    node_id: str
    event: str  # "dispatch", "complete", "retry", "escalate"
    timestamp: str = ""
    result_summary: Optional[dict] = None
    duration_sec: Optional[float] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        d = {
            "node_id": self.node_id,
            "event": self.event,
            "timestamp": self.timestamp,
        }
        if self.result_summary:
            d["result_summary"] = self.result_summary
        if self.duration_sec is not None:
            d["duration_sec"] = self.duration_sec
        return d


@dataclass
class RunState:
    run_id: str = ""
    task: str = ""
    classifier_output: Optional[ClassifierOutput] = None
    dag: Optional[DAG] = None
    state_dir: Path = field(default_factory=lambda: Path("."))
    completed_nodes: dict[str, NodeResult] = field(default_factory=dict)
    available_artifacts: dict[str, str] = field(default_factory=dict)
    retry_counts: dict[str, int] = field(default_factory=dict)
    budget_total: float = 30.0
    budget_spent: float = 0.0
    status: str = "pending"  # pending, running, completed, escalated, failed
    thread_ids: dict[str, str] = field(default_factory=dict)
    audit_log: list[AuditEntry] = field(default_factory=list)

    def __post_init__(self):
        if not self.run_id:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            short_id = uuid.uuid4().hex[:6]
            self.run_id = f"{ts}_{short_id}"

    @property
    def budget_remaining(self) -> float:
        return self.budget_total - self.budget_spent

    def freeze_dag(self):
        if self.dag:
            dag_path = self.state_dir / "dag.json"
            dag_path.write_text(self.dag.to_json())

    def append_audit(self, entry: AuditEntry):
        self.audit_log.append(entry)
        log_path = self.state_dir / "audit-log.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def save_artifact(self, name: str, content: str):
        self.available_artifacts[name] = content
        artifact_path = self.state_dir / f"{name}"
        artifact_path.write_text(content)

    def load_artifact(self, name: str) -> str:
        if name in self.available_artifacts:
            return self.available_artifacts[name]
        artifact_path = self.state_dir / name
        if artifact_path.exists():
            content = artifact_path.read_text()
            self.available_artifacts[name] = content
            return content
        raise FileNotFoundError(f"Artifact '{name}' not found")
