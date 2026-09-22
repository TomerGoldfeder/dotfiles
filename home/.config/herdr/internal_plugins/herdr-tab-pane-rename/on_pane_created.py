#!/usr/bin/env python3
"""Rename newly created panes to ``{tab_label}: {slug}`` on pane.created.

Event hook only. Never fights a later manual rename (no tab.renamed listener).
Naming failures exit 0 so a broken rename cannot break herdr event delivery.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from typing import Any

NUMERIC_TAB_LABEL_RE: re.Pattern[str] = re.compile(r"^\d+$")

Runner = Callable[[list[str]], tuple[int, str, str]]


def parse_event_ids(
    event: Mapping[str, Any],
    env: Mapping[str, str],
) -> tuple[str | None, str | None]:
    """Extract pane_id and tab_id from event JSON, then env fallbacks."""
    data: Any = event.get("data")
    data_map: Mapping[str, Any] = data if isinstance(data, dict) else {}

    pane_obj: Any = data_map.get("pane")
    pane_map: Mapping[str, Any] = pane_obj if isinstance(pane_obj, dict) else {}

    pane_id: str | None = _as_nonempty_str(pane_map.get("pane_id"))
    tab_id: str | None = _as_nonempty_str(pane_map.get("tab_id"))

    if pane_id is None:
        pane_id = _as_nonempty_str(data_map.get("pane_id"))
    if tab_id is None:
        tab_id = _as_nonempty_str(data_map.get("tab_id"))

    if pane_id is None:
        pane_id = _as_nonempty_str(event.get("pane_id"))
    if tab_id is None:
        tab_id = _as_nonempty_str(event.get("tab_id"))

    if pane_id is None:
        pane_id = _as_nonempty_str(env.get("HERDR_PANE_ID"))
    if tab_id is None:
        tab_id = _as_nonempty_str(env.get("HERDR_TAB_ID"))

    return pane_id, tab_id


def is_default_numeric_tab_label(
    label: str | None,
    number: int | None,
) -> bool:
    """True when the tab still uses herdr's auto numeric display name."""
    if label is None:
        return True
    stripped: str = label.strip()
    if stripped == "":
        return True
    if NUMERIC_TAB_LABEL_RE.fullmatch(stripped) is not None:
        return True
    if number is not None and stripped == str(number):
        return True
    return False


def already_prefixed(pane_label: str | None, tab_label: str) -> bool:
    """True when pane label already starts with ``{tab_label}: ``."""
    if pane_label is None:
        return False
    prefix: str = f"{tab_label}: "
    return pane_label.startswith(prefix)


def composed_label(
    tab_label: str,
    pane_label: str | None,
    default_slug: str | None,
) -> str | None:
    """Build ``{tab_label}: {slug}``, or None if no slug is available."""
    slug: str | None = None
    if pane_label is not None and pane_label.strip() != "":
        slug = pane_label
    elif default_slug is not None and default_slug.strip() != "":
        slug = default_slug
    if slug is None:
        return None
    return f"{tab_label}: {slug}"


def decide_rename(
    *,
    tab_label: str | None,
    tab_number: int | None,
    pane_label: str | None,
    default_slug: str | None,
) -> str | None:
    """Return the new pane label, or None when rename should be skipped."""
    if is_default_numeric_tab_label(tab_label, tab_number):
        return None
    assert tab_label is not None  # narrowed by is_default_numeric_tab_label
    cleaned_tab: str = tab_label.strip()
    if already_prefixed(pane_label, cleaned_tab):
        return None
    return composed_label(cleaned_tab, pane_label, default_slug)


def _as_nonempty_str(value: Any) -> str | None:
    if value is None:
        return None
    text: str = str(value)
    if text.strip() == "":
        return None
    return text


def _unwrap_result(obj: Mapping[str, Any]) -> Mapping[str, Any]:
    result: Any = obj.get("result", obj)
    if isinstance(result, dict):
        return result
    return obj


def _default_runner(argv: list[str]) -> tuple[int, str, str]:
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def _herdr_bin() -> str:
    return os.environ.get("HERDR_BIN_PATH", "herdr")


def _cli_json(runner: Runner, argv: list[str]) -> Mapping[str, Any] | None:
    try:
        code: int
        stdout: str
        _stderr: str
        code, stdout, _stderr = runner(argv)
    except Exception:
        return None
    if code != 0:
        return None
    try:
        parsed: Any = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None
    return _unwrap_result(parsed)


def _fetch_tab(
    runner: Runner,
    tab_id: str,
) -> tuple[str | None, int | None]:
    payload: Mapping[str, Any] | None = _cli_json(
        runner,
        [_herdr_bin(), "tab", "get", tab_id],
    )
    if payload is None:
        return None, None
    tab_obj: Any = payload.get("tab", payload)
    if not isinstance(tab_obj, dict):
        return None, None
    number_raw: Any = tab_obj.get("number")
    number: int | None
    if isinstance(number_raw, int):
        number = number_raw
    elif isinstance(number_raw, str) and number_raw.strip().isdigit():
        number = int(number_raw.strip())
    else:
        number = None
    # Keep raw label (including "1") for is_default_numeric_tab_label.
    raw_label: Any = tab_obj.get("label")
    label_str: str | None
    if raw_label is None:
        label_str = None
    else:
        label_str = str(raw_label)
    return label_str, number


def _fetch_pane(
    runner: Runner,
    pane_id: str,
) -> tuple[str | None, str | None]:
    payload: Mapping[str, Any] | None = _cli_json(
        runner,
        [_herdr_bin(), "pane", "get", pane_id],
    )
    if payload is None:
        return None, None
    pane_obj: Any = payload.get("pane", payload)
    if not isinstance(pane_obj, dict):
        return None, None
    raw_label: Any = pane_obj.get("label")
    label: str | None
    if raw_label is None:
        label = None
    else:
        text: str = str(raw_label)
        label = text if text.strip() != "" else None
    resolved_pane_id: str | None = _as_nonempty_str(pane_obj.get("pane_id")) or pane_id
    return label, resolved_pane_id


def _foreground_process_slug(runner: Runner, pane_id: str) -> str | None:
    payload: Mapping[str, Any] | None = _cli_json(
        runner,
        [_herdr_bin(), "pane", "process-info", "--pane", pane_id],
    )
    if payload is None:
        return None
    process_info: Any = payload.get("process_info", payload)
    if not isinstance(process_info, dict):
        return None
    foreground: Any = process_info.get("foreground_processes")
    if not isinstance(foreground, list) or len(foreground) == 0:
        return None
    first: Any = foreground[0]
    if not isinstance(first, dict):
        return None
    name: str | None = _as_nonempty_str(first.get("name"))
    return name


def _rename_pane(runner: Runner, pane_id: str, new_label: str) -> None:
    _cli_json(
        runner,
        [_herdr_bin(), "pane", "rename", pane_id, new_label],
    )


def _load_event(env: Mapping[str, str]) -> Mapping[str, Any] | None:
    raw: str | None = env.get("HERDR_PLUGIN_EVENT_JSON")
    if raw is None or raw.strip() == "":
        return None
    try:
        parsed: Any = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def run_hook(env: Mapping[str, str], runner: Runner) -> None:
    event: Mapping[str, Any] | None = _load_event(env)
    if event is None:
        return

    pane_id: str | None
    tab_id: str | None
    pane_id, tab_id = parse_event_ids(event, env)
    if pane_id is None or tab_id is None:
        return

    tab_label: str | None
    tab_number: int | None
    tab_label, tab_number = _fetch_tab(runner, tab_id)
    if tab_label is None and tab_number is None:
        # tab.get failed (race) — exit quietly
        return

    pane_label: str | None
    _resolved_pane: str | None
    pane_label, _resolved_pane = _fetch_pane(runner, pane_id)

    default_slug: str | None = None
    if pane_label is None:
        default_slug = _foreground_process_slug(runner, pane_id)

    new_label: str | None = decide_rename(
        tab_label=tab_label,
        tab_number=tab_number,
        pane_label=pane_label,
        default_slug=default_slug,
    )
    if new_label is None:
        return

    _rename_pane(runner, pane_id, new_label)


def main(runner: Runner | None = None) -> int:
    active_runner: Runner = runner if runner is not None else _default_runner
    try:
        run_hook(os.environ, active_runner)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
