"""DagHarness — top-level orchestrator: classify → compile → execute."""

from __future__ import annotations

import os
from pathlib import Path

from dag_harness.classifier import classify_task
from dag_harness.compiler import Compiler
from dag_harness.executor import (
    BBThreadDispatcher, Executor, MockDispatcher, NodeDispatcher,
)
from dag_harness.models import (
    ClassifierOutput, DAG, ExecutionBackend, RunState,
)


DEFAULT_STATE_ROOT = Path.home() / ".harness_state"


class DagHarness:
    """End-to-end: task string in → executed DAG out.

    Modes:
      - BB_THREAD (default): each node = bb thread, visible in bb UI
      - SUBAGENT: each node = Task tool call (for non-bb IDEs)
      - Mock: for testing, no real dispatch
    """

    def __init__(
        self,
        backend: ExecutionBackend = ExecutionBackend.BB_THREAD,
        state_root: Path | None = None,
        project_id: str | None = None,
        parent_thread_id: str | None = None,
        max_budget: float = 30.0,
        thread_timeout: int = 600,
        provider: str | None = None,
        model: str | None = None,
        dispatcher: NodeDispatcher | None = None,
        extra_middleware: list | None = None,
    ):
        self.backend = backend
        self.state_root = state_root or DEFAULT_STATE_ROOT
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.max_budget = max_budget
        self.thread_timeout = thread_timeout

        self.project_id = project_id or os.environ.get("BB_PROJECT_ID", "")
        self.parent_thread_id = parent_thread_id or os.environ.get("BB_THREAD_ID", "")
        self.provider = provider
        self.model = model

        self._dispatcher = dispatcher
        self._extra_middleware = extra_middleware or []

    def run(
        self,
        task: str,
        add_nodes: set[str] | None = None,
        drop_nodes: set[str] | None = None,
    ) -> RunState:
        """Full pipeline: classify → compile → execute."""

        # 1. Classify
        classification = classify_task(task)

        # 2. Initialize run state
        run_state = RunState(
            task=task,
            classifier_output=classification,
            budget_total=self.max_budget,
        )
        run_dir = self.state_root / run_state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        run_state.state_dir = run_dir

        # 3. Compile DAG
        compiler = Compiler(max_budget=self.max_budget)
        dag = compiler.compile(classification, add_nodes, drop_nodes)
        run_state.dag = dag
        run_state.freeze_dag()

        # If trivial task, inject a synthetic plan.md so implement node can start
        if classification.size.value == "trivial":
            run_state.save_artifact(
                "plan.md",
                f"# Auto-generated plan (trivial task)\n\nTask: {task}\n\n"
                "Steps:\n1. Implement the change directly\n2. Verify\n",
            )

        # 4. Execute
        dispatcher = self._get_dispatcher()
        middleware = None
        if self._extra_middleware:
            from dag_harness.middleware import (
                AuditMiddleware, BudgetMiddleware, CheckpointMiddleware,
            )
            middleware = [
                AuditMiddleware(),
                BudgetMiddleware(),
                CheckpointMiddleware(),
            ] + list(self._extra_middleware)
        executor = Executor(
            dag=dag, run_state=run_state, dispatcher=dispatcher,
            middleware=middleware,
        )
        run_state = executor.execute(task)

        return run_state

    def _get_dispatcher(self) -> NodeDispatcher:
        if self._dispatcher:
            return self._dispatcher

        if self.backend == ExecutionBackend.BB_THREAD:
            return BBThreadDispatcher(
                project_id=self.project_id,
                parent_thread_id=self.parent_thread_id,
                timeout=self.thread_timeout,
                provider=self.provider,
                model=self.model,
            )
        else:
            return MockDispatcher()


def run_harness(
    task: str,
    backend: str = "bb_thread",
    **kwargs,
) -> RunState:
    """Convenience function for quick invocation."""
    be = ExecutionBackend(backend)
    harness = DagHarness(backend=be, **kwargs)
    return harness.run(task)
