#!/usr/bin/env python3
"""Unit tests for herdr-tab-pane-rename pure helpers and main() exit contract."""
from __future__ import annotations

import json
import os
import unittest
from typing import Any
from unittest import mock

from on_pane_created import (
    already_prefixed,
    composed_label,
    decide_rename,
    is_default_numeric_tab_label,
    main,
    parse_event_ids,
)


class TestIsDefaultNumericTabLabel(unittest.TestCase):
    def test_skip_blank_tab_label(self) -> None:
        self.assertTrue(is_default_numeric_tab_label(None, None))
        self.assertTrue(is_default_numeric_tab_label("", None))
        self.assertTrue(is_default_numeric_tab_label("   ", 3))

    def test_skip_numeric_tab_label_one_and_two(self) -> None:
        self.assertTrue(is_default_numeric_tab_label("1", None))
        self.assertTrue(is_default_numeric_tab_label("2", 2))
        self.assertTrue(is_default_numeric_tab_label("42", 99))

    def test_skip_when_label_equals_tab_number(self) -> None:
        self.assertTrue(is_default_numeric_tab_label("7", 7))

    def test_custom_label_is_not_default(self) -> None:
        self.assertFalse(is_default_numeric_tab_label("work", 1))
        self.assertFalse(is_default_numeric_tab_label("tab-1", 1))


class TestAlreadyPrefixed(unittest.TestCase):
    def test_skip_when_already_prefixed(self) -> None:
        self.assertTrue(already_prefixed("work: shell", "work"))
        self.assertTrue(already_prefixed("work: ", "work"))

    def test_not_prefixed_when_different_tab(self) -> None:
        self.assertFalse(already_prefixed("other: shell", "work"))
        self.assertFalse(already_prefixed("workshell", "work"))
        self.assertFalse(already_prefixed(None, "work"))
        self.assertFalse(already_prefixed("shell", "work"))


class TestComposedLabel(unittest.TestCase):
    def test_compose_with_pane_label(self) -> None:
        result: str | None = composed_label("work", "shell", "zsh")
        self.assertEqual(result, "work: shell")

    def test_compose_with_process_slug_when_pane_unlabeled(self) -> None:
        result: str | None = composed_label("work", None, "zsh")
        self.assertEqual(result, "work: zsh")
        result_empty: str | None = composed_label("work", "", "nvim")
        self.assertEqual(result_empty, "work: nvim")

    def test_skip_when_neither_pane_label_nor_slug(self) -> None:
        self.assertIsNone(composed_label("work", None, None))
        self.assertIsNone(composed_label("work", "", ""))
        self.assertIsNone(composed_label("work", None, ""))


class TestDecideRename(unittest.TestCase):
    def test_skip_blank_tab(self) -> None:
        self.assertIsNone(
            decide_rename(
                tab_label="  ",
                tab_number=1,
                pane_label="shell",
                default_slug="zsh",
            )
        )

    def test_skip_numeric_tab(self) -> None:
        self.assertIsNone(
            decide_rename(
                tab_label="1",
                tab_number=1,
                pane_label="shell",
                default_slug="zsh",
            )
        )

    def test_skip_already_prefixed(self) -> None:
        self.assertIsNone(
            decide_rename(
                tab_label="work",
                tab_number=1,
                pane_label="work: shell",
                default_slug="zsh",
            )
        )

    def test_compose_happy_path(self) -> None:
        self.assertEqual(
            decide_rename(
                tab_label="work",
                tab_number=1,
                pane_label="shell",
                default_slug=None,
            ),
            "work: shell",
        )

    def test_compose_from_slug(self) -> None:
        self.assertEqual(
            decide_rename(
                tab_label="work",
                tab_number=1,
                pane_label=None,
                default_slug="zsh",
            ),
            "work: zsh",
        )

    def test_skip_no_slug(self) -> None:
        self.assertIsNone(
            decide_rename(
                tab_label="work",
                tab_number=1,
                pane_label=None,
                default_slug=None,
            )
        )


class TestParseEventIds(unittest.TestCase):
    def test_extract_ids_from_nested_event_json(self) -> None:
        event: dict[str, Any] = {
            "event": "pane.created",
            "data": {
                "type": "pane_created",
                "pane": {"pane_id": "w1:p2", "tab_id": "w1:t1", "label": None},
            },
        }
        pane_id: str | None
        tab_id: str | None
        pane_id, tab_id = parse_event_ids(event, {})
        self.assertEqual(pane_id, "w1:p2")
        self.assertEqual(tab_id, "w1:t1")

    def test_extract_ids_from_data_flat(self) -> None:
        event: dict[str, Any] = {
            "event": "pane.created",
            "data": {"pane_id": "w1:p9", "tab_id": "w1:t3"},
        }
        pane_id: str | None
        tab_id: str | None
        pane_id, tab_id = parse_event_ids(event, {})
        self.assertEqual(pane_id, "w1:p9")
        self.assertEqual(tab_id, "w1:t3")

    def test_extract_ids_from_top_level(self) -> None:
        event: dict[str, Any] = {"pane_id": "w2:p1", "tab_id": "w2:t1"}
        pane_id: str | None
        tab_id: str | None
        pane_id, tab_id = parse_event_ids(event, {})
        self.assertEqual(pane_id, "w2:p1")
        self.assertEqual(tab_id, "w2:t1")

    def test_extract_ids_from_env_fallback(self) -> None:
        event: dict[str, Any] = {"event": "pane.created", "data": {}}
        env: dict[str, str] = {
            "HERDR_PANE_ID": "env:p1",
            "HERDR_TAB_ID": "env:t1",
        }
        pane_id: str | None
        tab_id: str | None
        pane_id, tab_id = parse_event_ids(event, env)
        self.assertEqual(pane_id, "env:p1")
        self.assertEqual(tab_id, "env:t1")

    def test_nested_wins_over_env(self) -> None:
        event: dict[str, Any] = {
            "data": {"pane": {"pane_id": "nested:p", "tab_id": "nested:t"}},
        }
        env: dict[str, str] = {
            "HERDR_PANE_ID": "env:p1",
            "HERDR_TAB_ID": "env:t1",
        }
        pane_id: str | None
        tab_id: str | None
        pane_id, tab_id = parse_event_ids(event, env)
        self.assertEqual(pane_id, "nested:p")
        self.assertEqual(tab_id, "nested:t")


class TestMainAlwaysExitsZero(unittest.TestCase):
    def test_main_exits_zero_when_cli_would_fail(self) -> None:
        event: dict[str, Any] = {
            "event": "pane.created",
            "data": {
                "type": "pane_created",
                "pane": {"pane_id": "w1:p2", "tab_id": "w1:t1", "label": None},
            },
        }

        def boom_runner(argv: list[str]) -> tuple[int, str, str]:
            raise RuntimeError("simulated cli failure")

        with mock.patch.dict(
            os.environ,
            {"HERDR_PLUGIN_EVENT_JSON": json.dumps(event)},
            clear=False,
        ):
            code: int = main(runner=boom_runner)
        self.assertEqual(code, 0)

    def test_main_exits_zero_when_event_json_missing(self) -> None:
        env_without_event: dict[str, str] = {
            k: v for k, v in os.environ.items() if k != "HERDR_PLUGIN_EVENT_JSON"
        }
        with mock.patch.dict(os.environ, env_without_event, clear=True):
            code: int = main(runner=lambda argv: (1, "", "fail"))
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
