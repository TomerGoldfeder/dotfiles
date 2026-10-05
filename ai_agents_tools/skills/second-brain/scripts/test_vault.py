#!/usr/bin/env python3
"""Tests for vault.py typed-page loader and validator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import vault
from vault import (
    explored_percent,
    extract_wikilink_target,
    fog_targets,
    load_pages,
    parse_frontmatter,
    resolve_vault,
    validate,
)


def _write_wiki(vault_dir: Path, name: str, body: str) -> None:
    wiki: Path = vault_dir / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)
    (wiki / f"{name}.md").write_text(body, encoding="utf-8")


class TestFrontmatter(unittest.TestCase):
    def test_lists_quotes_empty_and_wikilink_alias(self) -> None:
        text: str = (
            "---\n"
            "type: service\n"
            "domain: \"[[Payments]]\"\n"
            "owners:\n"
            "  - '[[Ada|A]]'\n"
            "  - \"[[Bea#bio]]\"\n"
            "calls: []\n"
            "maybe:\n"
            "  - [[FogTarget]]\n"
            "---\n"
            "\n# X\n"
        )
        props, errors = parse_frontmatter(text)
        self.assertEqual(errors, [])
        self.assertEqual(props["type"], "service")
        self.assertEqual(props["domain"], "[[Payments]]")
        self.assertEqual(props["owners"], ["[[Ada|A]]", "[[Bea#bio]]"])
        self.assertEqual(props["calls"], [])
        self.assertEqual(extract_wikilink_target("[[Ada|A]]"), "Ada")
        self.assertEqual(extract_wikilink_target("[[Bea#bio]]"), "Bea")


class TestValidate(unittest.TestCase):
    def test_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root: Path = Path(tmp)
            _write_wiki(
                root,
                "BadType",
                "---\ntype: spaceship\n---\n",
            )
            _write_wiki(
                root,
                "BadKnowledge",
                "---\ntype: service\nknowledge: legendary\n---\n",
            )
            _write_wiki(
                root,
                "SeenNoSources",
                "---\ntype: service\nknowledge: seen\nsources: []\n---\n",
            )
            _write_wiki(
                root,
                "OwnedNoPr",
                "---\ntype: service\nknowledge: owned\nsources:\n  - repo:x\n---\n",
            )
            _write_wiki(
                root,
                "BadStatus",
                "---\ntype: question\nstatus: maybe\n---\n",
            )
            pages = load_pages(root)
            messages = {(f.page, f.message) for f in validate(pages)}
            self.assertIn(("BadType", "unknown type: spaceship"), messages)
            self.assertTrue(any(p == "BadKnowledge" and "invalid knowledge" in m for p, m in messages))
            self.assertTrue(
                any(p == "SeenNoSources" and "sources" in m for p, m in messages)
            )
            self.assertTrue(any(p == "OwnedNoPr" and "pr:" in m for p, m in messages))
            self.assertTrue(any(p == "BadStatus" and "invalid status" in m for p, m in messages))


class TestExploredAndFog(unittest.TestCase):
    def test_explored_and_fog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root: Path = Path(tmp)
            _write_wiki(
                root,
                "PaymentsApi",
                "---\n"
                "type: service\n"
                "knowledge: owned\n"
                "domain: \"[[Payments]]\"\n"
                "calls:\n"
                "  - \"[[MissingSvc]]\"\n"
                "sources:\n"
                "  - pr:1\n"
                "---\n",
            )
            _write_wiki(
                root,
                "Payments",
                "---\ntype: domain\nknowledge: rumored\n---\n",
            )
            pages = load_pages(root)
            fog = fog_targets(pages)
            self.assertEqual(fog, ["MissingSvc"])
            # 2 places (PaymentsApi owned=1, Payments rumored=0) + 1 fog=0 → 100/3
            pct = explored_percent(pages, len(fog))
            self.assertAlmostEqual(pct, 100.0 / 3.0, places=5)

    def test_empty_typed_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root: Path = Path(tmp)
            (root / "wiki").mkdir(parents=True)
            _write_wiki(root, "Note", "# just a note\n")
            pages = load_pages(root)
            self.assertEqual(validate(pages), [])
            self.assertEqual(explored_percent(pages, 0), 0.0)


class TestResolveVault(unittest.TestCase):
    def test_explicit_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = resolve_vault(tmp)
            self.assertEqual(path, Path(tmp).resolve())


if __name__ == "__main__":
    unittest.main()
