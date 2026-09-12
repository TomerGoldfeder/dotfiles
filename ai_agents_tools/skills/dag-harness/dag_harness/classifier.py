"""Task classifier — sizes task and picks a template hint."""

from dag_harness.models import ClassifierOutput, TaskSize, TemplateHint

TRIVIAL_SIGNALS = [
    "one-line", "typo", "rename", "bump version", "fix import",
    "add comment", "remove unused", "simple fix", "trivial",
    "update readme", "fix whitespace",
]

COMPLEX_SIGNALS = [
    "architecture", "redesign", "migration", "new service",
    "integrate", "api", "database schema", "multi-module",
    "performance optimization", "security audit", "refactor entire",
]

RESEARCH_SIGNALS = [
    "new library", "unfamiliar", "evaluate options", "research",
    "investigate", "learn", "unknown api", "external service",
    "third-party", "poc", "proof of concept", "spike",
]


def classify_task(task: str) -> ClassifierOutput:
    """Rule-based classifier. Fast, deterministic, no LLM needed.

    For production use, swap with an LLM-backed classifier that runs as a
    single cheap bb thread call.
    """
    task_lower = task.lower()
    word_count = len(task.split())

    trivial_hits = sum(1 for s in TRIVIAL_SIGNALS if s in task_lower)
    complex_hits = sum(1 for s in COMPLEX_SIGNALS if s in task_lower)
    research_hits = sum(1 for s in RESEARCH_SIGNALS if s in task_lower)

    if research_hits >= 2 or (research_hits >= 1 and complex_hits >= 1):
        return ClassifierOutput(
            size=TaskSize.COMPLEX,
            template_hint=TemplateHint.RESEARCH_HEAVY,
            reasons=f"Research signals ({research_hits}) + complexity ({complex_hits}) → research-heavy",
        )

    if complex_hits >= 2 or word_count > 100:
        return ClassifierOutput(
            size=TaskSize.COMPLEX,
            template_hint=TemplateHint.FULL_LOOP,
            reasons=f"Complexity signals ({complex_hits}), word count ({word_count}) → full-loop",
        )

    if trivial_hits >= 1 and complex_hits == 0 and word_count < 30:
        return ClassifierOutput(
            size=TaskSize.TRIVIAL,
            template_hint=TemplateHint.FAST_PATH,
            reasons=f"Trivial signals ({trivial_hits}), short ({word_count} words) → fast-path",
        )

    return ClassifierOutput(
        size=TaskSize.STANDARD,
        template_hint=TemplateHint.FULL_LOOP,
        reasons=f"No strong signals either way, word count ({word_count}) → default full-loop",
    )
