#!/usr/bin/env python3
"""Tests for brief.py companion brief and hook mode."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from unittest import mock

import brief
import vault


def _page(vault_dir: Path, name: str, frontmatter: str) -> None:
    wiki: Path = vault_dir / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)
    (wiki / f"{name}.md").write_text(f"---\n{frontmatter}\n---\n\n# {name}\n", encoding="utf-8")


def _sample_vault(root: Path, today: date) -> None:
    _page(
        root,
        "Q1",
        "type: question\nstatus: open\nask: \"[[Ada]]\"\nabout: \"[[Ledger]]\"\n"
        f"updated: {today.isoformat()}",
    )
    _page(
        root,
        "C1",
        "type: commitment\nstatus: open\nto: \"[[Ada]]\"\n"
        f"due: {(today - timedelta(days=1)).isoformat()}\nabout: ship\n"
        f"updated: {today.isoformat()}",
    )
    _page(
        root,
        "PaymentsApi",
        "type: service\nknowledge: rumored\n"
        f"updated: {today.isoformat()}",
    )
    _page(root, "Alpha", "type: concept\naka: A\n")
    _page(root, "Beta", "type: concept\naka: B\n")
    _page(root, "Gamma", "type: concept\naka: C\n")
    _page(root, "Delta", "type: concept\naka: D\n")


class TestBriefSections(unittest.TestCase):
    def test_sections_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root: Path = Path(tmp)
            today: date = date(2026, 10, 5)
            _sample_vault(root, today)
            text: str = brief.run_brief(root, today=today)
            self.assertIn("# Companion brief — 2026-10-05", text)
            self.assertIn("## Open questions", text)
            self.assertIn("[[Q1]]", text)
            self.assertIn("## Open commitments", text)
            self.assertIn("(overdue)", text)
            self.assertIn("## New / updated on map", text)
            self.assertIn("## Concepts to review", text)
            state = brief.load_state(root)
            self.assertEqual(state["last_brief"], "2026-10-05")
            shown = state["concepts_shown"]
            assert isinstance(shown, dict)
            self.assertEqual(len(shown), 3)


class TestHook(unittest.TestCase):
    def test_once_per_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root: Path = Path(tmp)
            today: date = date(2026, 10, 5)
            _sample_vault(root, today)
            first: str = brief.run_hook(root, "{}", today=today)
            self.assertIn("additional_context", first)
            second: str = brief.run_hook(root, "{}", today=today)
            self.assertEqual(second, "{}")

    def test_background_agent_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root: Path = Path(tmp)
            today: date = date(2026, 10, 5)
            _sample_vault(root, today)
            out: str = brief.run_hook(
                root, json.dumps({"is_background_agent": True}), today=today
            )
            self.assertEqual(out, "{}")

    def test_missing_vault(self) -> None:
        missing: Path = Path("/tmp/definitely-missing-second-brain-vault-xyz")
        out: str = brief.run_hook(missing, "{}", today=date(2026, 10, 5))
        self.assertEqual(out, "{}")

    def test_no_typed_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root: Path = Path(tmp)
            (root / "wiki").mkdir(parents=True)
            (root / "wiki" / "Note.md").write_text("# hi\n", encoding="utf-8")
            out: str = brief.run_hook(root, "{}", today=date(2026, 10, 5))
            self.assertEqual(out, "{}")


class TestMainAlwaysExitsZero(unittest.TestCase):
    def test_hook_exception_prints_empty_and_exits_zero(self) -> None:
        with mock.patch.object(brief, "run_hook", side_effect=RuntimeError("boom")):
            with mock.patch.object(brief.sys, "stdin", io.StringIO("{}")):
                with mock.patch("builtins.print") as printed:
                    code: int = brief.main(["--hook", "--vault", "/tmp"])
        self.assertEqual(code, 0)
        printed.assert_called_with("{}")


if __name__ == "__main__":
    unittest.main()
