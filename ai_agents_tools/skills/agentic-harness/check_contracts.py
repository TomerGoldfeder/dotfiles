"""Fail when harness role prompts drift back into ceremony or unbounded startup."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED_SECTIONS = ("## Goal", "## Inputs", "## Do", "## Output", "## Stop")
BANNED = ("Why separate", "Phase 1", "STARTUP")
WORD_CEILING = 500

ROLE_FILES = (
    "nodes/classifier.md",
    "nodes/explorer.md",
    "nodes/explorer-second-brain.md",
    "nodes/planner.md",
    "nodes/worker.md",
    "nodes/worker-second-brain-writeback.md",
    "nodes/qa.md",
    "nodes/critic.md",
    "nodes/promoter.md",
    "nodes/journaler.md",
)


def word_count(text: str) -> int:
    return len(text.split())


def check_role_file(path: Path, errors: list[str]) -> None:
    text = path.read_text()
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"{path.name}: missing {section}")
    for phrase in BANNED:
        if phrase in text:
            errors.append(f"{path.name}: contains {phrase!r}")
    count = word_count(text)
    if count > WORD_CEILING:
        errors.append(f"{path.name}: {count} words exceeds {WORD_CEILING}")


def check_orchestrator(errors: list[str]) -> None:
    skill = (ROOT / "SKILL.md").read_text()
    coding = (ROOT / "graphs" / "coding.md").read_text()
    index = (ROOT / "INDEX.md").read_text()
    if "Do not spawn a classifier" not in skill:
        errors.append("SKILL.md: classifier must stay inline")
    if "Follow-up slice" not in skill:
        errors.append("SKILL.md: missing follow-up slice")
    if "One repo explorer" not in coding:
        errors.append("coding.md: hard graph must keep a single repo explorer")
    if "Easy max 3" not in coding or "Hard max 4" not in coding:
        errors.append("coding.md: worker caps missing")
    for node_id in ("explorer-second-brain", "worker-second-brain-writeback"):
        if node_id not in index:
            errors.append(f"INDEX.md: missing id file for {node_id}")
    if "code-standards is the gold standard" in (ROOT / "nodes" / "qa.md").read_text():
        errors.append("qa.md: standards audit returned")


def main() -> None:
    errors: list[str] = []
    for relative in ROLE_FILES:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing {relative}")
            continue
        check_role_file(path, errors)
    check_orchestrator(errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"ok: {len(ROLE_FILES)} role contracts")


if __name__ == "__main__":
    main()
