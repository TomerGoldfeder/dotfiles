#!/usr/bin/env python3
"""Companion brief for the second-brain vault (on-demand and sessionStart hook)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import vault as vault_mod
from vault import Page, explored_percent, fog_targets, resolve_vault, typed_pages

HOOK_INSTRUCTION: str = (
    "this is the user's second-brain companion brief; show it to the user in at most "
    "8 lines at the start of your first reply, then handle their request; do not "
    "repeat it later in the conversation."
)
CONCEPTS_TO_SHOW: int = 3
DEFAULT_LOOKBACK_DAYS: int = 7


def _state_path(vault: Path) -> Path:
    return vault / ".companion" / "state.json"


def load_state(vault: Path) -> Dict[str, object]:
    path: Path = _state_path(vault)
    if not path.is_file():
        return {"last_brief": None, "concepts_shown": {}}
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"last_brief": None, "concepts_shown": {}}
    if not isinstance(data, dict):
        return {"last_brief": None, "concepts_shown": {}}
    concepts: object = data.get("concepts_shown", {})
    if not isinstance(concepts, dict):
        concepts = {}
    return {
        "last_brief": data.get("last_brief"),
        "concepts_shown": {str(k): str(v) for k, v in concepts.items()},
    }


def save_state(vault: Path, state: Dict[str, object]) -> None:
    path: Path = _state_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_date(value: object) -> Optional[date]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _prop_str(page: Page, key: str) -> str:
    value: object = page.props.get(key)
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _open_questions(pages: Sequence[Page]) -> List[str]:
    lines: List[str] = []
    for page in typed_pages(pages):
        if page.type != "question":
            continue
        if page.props.get("status") != "open":
            continue
        ask: str = _prop_str(page, "ask")
        about: str = _prop_str(page, "about")
        lines.append(f"- [[{page.name}]] ask {ask} about {about}".rstrip())
    return lines


def _open_commitments(pages: Sequence[Page], today: date) -> List[str]:
    lines: List[str] = []
    for page in typed_pages(pages):
        if page.type != "commitment":
            continue
        if page.props.get("status") != "open":
            continue
        to_val: str = _prop_str(page, "to")
        due_raw: object = page.props.get("due")
        due: Optional[date] = _parse_date(due_raw)
        overdue: str = ""
        if due is not None and due < today:
            overdue = " (overdue)"
        due_s: str = due.isoformat() if due is not None else str(due_raw or "")
        lines.append(f"- [[{page.name}]] to {to_val} due {due_s}{overdue}".rstrip())
    return lines


def _map_updates(
    pages: Sequence[Page], last_brief: Optional[date], today: date
) -> List[str]:
    cutoff: date
    if last_brief is None:
        cutoff = today - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    else:
        cutoff = last_brief
    lines: List[str] = []
    for page in typed_pages(pages):
        updated: Optional[date] = _parse_date(page.props.get("updated"))
        if updated is None or updated <= cutoff:
            continue
        type_s: str = page.type or "untyped"
        lines.append(f"- [[{page.name}]] ({type_s}) updated {updated.isoformat()}")
    return lines


def _concepts_to_review(
    pages: Sequence[Page], concepts_shown: Dict[str, str], today: date
) -> Tuple[List[str], Dict[str, str]]:
    concepts: List[Page] = [p for p in typed_pages(pages) if p.type == "concept"]

    def sort_key(page: Page) -> Tuple[str, str]:
        shown: str = concepts_shown.get(page.name, "0000-00-00")
        return (shown, page.name)

    concepts_sorted: List[Page] = sorted(concepts, key=sort_key)
    chosen: List[Page] = concepts_sorted[:CONCEPTS_TO_SHOW]
    lines: List[str] = [f"- [[{p.name}]]" for p in chosen]
    updated_shown: Dict[str, str] = dict(concepts_shown)
    for page in chosen:
        updated_shown[page.name] = today.isoformat()
    return lines, updated_shown


def build_brief(
    pages: Sequence[Page], state: Dict[str, object], today: date
) -> Tuple[str, Dict[str, object]]:
    fog: List[str] = fog_targets(pages)
    pct: float = explored_percent(pages, len(fog))
    last_brief: Optional[date] = _parse_date(state.get("last_brief"))
    concepts_shown_raw: object = state.get("concepts_shown", {})
    concepts_shown: Dict[str, str] = {}
    if isinstance(concepts_shown_raw, dict):
        concepts_shown = {str(k): str(v) for k, v in concepts_shown_raw.items()}

    sections: List[str] = [
        f"# Companion brief — {today.isoformat()}",
        f"Explored {pct:.0f}%",
    ]
    questions: List[str] = _open_questions(pages)
    if questions:
        sections.append("## Open questions")
        sections.extend(questions)
    commitments: List[str] = _open_commitments(pages, today)
    if commitments:
        sections.append("## Open commitments")
        sections.extend(commitments)
    updates: List[str] = _map_updates(pages, last_brief, today)
    if updates:
        sections.append("## New / updated on map")
        sections.extend(updates)
    concepts_lines: List[str]
    new_shown: Dict[str, str]
    concepts_lines, new_shown = _concepts_to_review(pages, concepts_shown, today)
    if concepts_lines:
        sections.append("## Concepts to review")
        sections.extend(concepts_lines)

    new_state: Dict[str, object] = {
        "last_brief": today.isoformat(),
        "concepts_shown": new_shown,
    }
    return "\n".join(sections) + "\n", new_state


def run_brief(vault: Path, today: Optional[date] = None) -> str:
    day: date = today if today is not None else date.today()
    pages: List[Page] = vault_mod.load_pages(vault)
    state: Dict[str, object] = load_state(vault)
    text: str
    new_state: Dict[str, object]
    text, new_state = build_brief(pages, state, day)
    save_state(vault, new_state)
    return text


def run_hook(vault: Path, stdin_text: str, today: Optional[date] = None) -> str:
    day: date = today if today is not None else date.today()
    payload: Dict[str, object] = {}
    try:
        parsed: object = json.loads(stdin_text) if stdin_text.strip() else {}
        if isinstance(parsed, dict):
            payload = parsed
    except json.JSONDecodeError:
        payload = {}

    if payload.get("is_background_agent") is True:
        return "{}"
    if not vault.is_dir():
        return "{}"
    pages: List[Page] = vault_mod.load_pages(vault)
    if not typed_pages(pages):
        return "{}"
    state: Dict[str, object] = load_state(vault)
    last: Optional[date] = _parse_date(state.get("last_brief"))
    if last == day:
        return "{}"
    text: str
    new_state: Dict[str, object]
    text, new_state = build_brief(pages, state, day)
    save_state(vault, new_state)
    additional: str = HOOK_INSTRUCTION + "\n\n" + text
    return json.dumps({"additional_context": additional})


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", default=None, help="Vault path")
    parser.add_argument(
        "--hook",
        action="store_true",
        help="sessionStart hook mode (JSON on stdin, fail-open)",
    )
    args: argparse.Namespace = parser.parse_args(list(argv) if argv is not None else None)
    vault: Path = resolve_vault(args.vault)
    if args.hook:
        try:
            stdin_text: str = sys.stdin.read()
            print(run_hook(vault, stdin_text))
        except Exception:
            print("{}")
        return 0
    print(run_brief(vault), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
