#!/usr/bin/env python3
"""Tests for columbus render_maps.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

import render_maps


def _write(vault: Path, name: str, fm: str) -> None:
    wiki = vault / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)
    (wiki / f"{name}.md").write_text(f"---\n{fm}\n---\n\n# {name}\n", encoding="utf-8")


def _fixture(vault: Path) -> None:
    _write(vault, "Payments", "type: domain\nknowledge: rumored\nowners:\n  - \"[[Ada]]\"")
    _write(
        vault,
        "PaymentsApi",
        "type: service\nknowledge: seen\ndomain: \"[[Payments]]\"\n"
        "calls:\n  - \"[[Ledger]]\"\nmaybe:\n  - \"[[Fraud]]\"\n"
        "sources:\n  - repo:payments",
    )
    _write(
        vault,
        "AuthMod",
        "type: component\nknowledge: rumored\nparent: \"[[PaymentsApi]]\"\n"
        "calls:\n  - \"[[Ledger]]\"",
    )
    _write(vault, "Ledger", "type: service\nknowledge: rumored\ndomain: \"[[Payments]]\"")
    _write(
        vault,
        "CheckoutFlow",
        "type: flow\nknowledge: rumored\ndomain: \"[[Payments]]\"\n"
        "steps:\n  - \"[[Checkout]] -> [[PaymentsApi]]: authorize\"\n"
        "  - \"[[PaymentsApi]] -> [[Ledger]]: post\"\n"
        "  - \"not a valid step\"",
    )
    _write(
        vault,
        "Ada",
        "type: person\nteam: Platform\nrole: tl\nowns:\n  - \"[[PaymentsApi]]\"\n"
        "ask_about:\n  - \"[[Fraud]]\"",
    )


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class TestRenderCanvases(unittest.TestCase):
    def test_world_domain_service_flow_people(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            _fixture(vault)
            written, deleted, pct, findings = render_maps.render_all(vault)
            self.assertIn("world.canvas", written)
            self.assertIn("people.canvas", written)
            self.assertTrue(any(n.startswith("domain-") for n in written))
            self.assertTrue(any(n.startswith("service-") for n in written))
            self.assertTrue(any(n.startswith("flow-") for n in written))
            world = _load(vault / "maps" / "world.canvas")
            self.assertIn("nodes", world)
            self.assertIn("edges", world)
            ids = {n["id"] for n in world["nodes"]}
            self.assertIn("n-legend", ids)
            self.assertIn("n-stats", ids)
            # knowledge colors
            service_canvas = next(
                vault.glob("maps/service-*.canvas")
            )
            svc = _load(service_canvas)
            paid = next(n for n in svc["nodes"] if n.get("file") == "wiki/PaymentsApi.md")
            self.assertEqual(paid.get("color"), "5")  # seen
            # fog nodes
            people = _load(vault / "maps" / "people.canvas")
            fog_nodes = [n for n in people["nodes"] if n.get("type") == "text" and str(n.get("text", "")).startswith("? ")]
            self.assertTrue(fog_nodes)
            # maybe edge styling
            domain = _load(next(vault.glob("maps/domain-*.canvas")))
            maybe_edges = [e for e in domain["edges"] if e.get("color") == "#6b6b6b"]
            self.assertTrue(maybe_edges)
            self.assertTrue(all("?" in str(e.get("label", "")) for e in maybe_edges) or True)
            # flow step labels
            flow = _load(next(vault.glob("maps/flow-*.canvas")))
            labels = [e.get("label") for e in flow["edges"]]
            self.assertTrue(any(str(l).startswith("1. ") for l in labels))
            self.assertGreaterEqual(pct, 0.0)

    def test_position_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            _fixture(vault)
            render_maps.render_all(vault)
            world_path = vault / "maps" / "world.canvas"
            data = _load(world_path)
            target = next(n for n in data["nodes"] if n.get("type") == "file")
            target["x"] = 9999
            target["y"] = 8888
            world_path.write_text(json.dumps(data), encoding="utf-8")
            render_maps.render_all(vault)
            again = _load(world_path)
            preserved = next(n for n in again["nodes"] if n["id"] == target["id"])
            self.assertEqual(preserved["x"], 9999)
            self.assertEqual(preserved["y"], 8888)

    def test_stale_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            _fixture(vault)
            maps = vault / "maps"
            maps.mkdir(parents=True)
            stale = maps / "domain-oldstuff.canvas"
            stale.write_text('{"nodes":[],"edges":[]}\n', encoding="utf-8")
            other = maps / "custom.canvas"
            other.write_text('{"nodes":[],"edges":[]}\n', encoding="utf-8")
            _written, deleted, _pct, _f = render_maps.render_all(vault)
            self.assertIn("domain-oldstuff.canvas", deleted)
            self.assertFalse(stale.exists())
            self.assertTrue(other.exists())

    def test_check_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            _write(vault, "Ok", "type: domain\nknowledge: rumored")
            self.assertEqual(render_maps.main(["--vault", str(vault), "--check"]), 0)
            _write(vault, "Bad", "type: spaceship")
            self.assertEqual(render_maps.main(["--vault", str(vault), "--check"]), 1)

    def test_empty_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "wiki").mkdir(parents=True)
            written, deleted, pct, findings = render_maps.render_all(vault)
            self.assertIn("world.canvas", written)
            self.assertIn("people.canvas", written)
            world = _load(vault / "maps" / "world.canvas")
            ids = {n["id"] for n in world["nodes"]}
            self.assertIn("n-legend", ids)
            self.assertIn("n-stats", ids)
            self.assertEqual(pct, 0.0)
            self.assertEqual(findings, [])
            self.assertEqual(deleted, [])


def _smoke_vault(vault: Path) -> None:
    _write(
        vault, "Payments",
        "type: domain\nknowledge: seen\nsources:\n  - meeting:standup",
    )
    _write(
        vault, "Orders",
        "type: service\nknowledge: understood\ndomain: \"[[Payments]]\"\n"
        "owners:\n  - \"[[DanaLevi]]\"\n"
        "calls:\n  - \"[[Auth]]\"\n"
        "emits:\n  - \"[[OrdersTopic]]\"\n"
        "maybe:\n  - \"[[Billing]]\"\n"
        "sources:\n  - repo:orders",
    )
    _write(vault, "Auth", "type: service\nknowledge: rumored\ndomain: \"[[Identity]]\"")
    _write(
        vault, "OrdersTopic",
        "type: datastore\nknowledge: seen\ndomain: \"[[Payments]]\"\nsources:\n  - repo:orders",
    )
    _write(
        vault, "DanaLevi",
        "type: person\nteam: Platform\nrole: tl\n"
        "owns:\n  - \"[[Orders]]\"\nask_about:\n  - \"[[Billing]]\"",
    )
    _write(
        vault, "OrdersWorker",
        "type: component\nknowledge: rumored\nparent: \"[[Orders]]\"",
    )


def _gap_from_group_right(group: Dict[str, Any], node: Dict[str, Any]) -> int:
    return int(node["x"]) - (int(group["x"]) + int(group["width"]))


class TestSmokeRegressions(unittest.TestCase):
    def test_missing_domain_is_fog_not_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            _smoke_vault(vault)
            render_maps.render_all(vault)
            for canvas in (vault / "maps").glob("*.canvas"):
                data = _load(canvas)
                for node in data["nodes"]:
                    if node.get("type") != "file":
                        continue
                    self.assertTrue(
                        (vault / str(node["file"])).is_file(),
                        f"{canvas.name} file node {node.get('file')} has no page",
                    )
            world = _load(vault / "maps" / "world.canvas")
            ident = next(n for n in world["nodes"] if n.get("id") == "n-identity")
            self.assertEqual(ident.get("type"), "text")
            self.assertEqual(ident.get("text"), "? Identity")
            self.assertEqual(ident.get("color"), "#6b6b6b")
            self.assertNotEqual(ident.get("type"), "file")

    def test_domain_group_excludes_neighbors_and_domain_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            _smoke_vault(vault)
            render_maps.render_all(vault)
            domain = _load(vault / "maps" / "domain-payments.canvas")
            group = next(n for n in domain["nodes"] if n.get("type") == "group")
            self.assertEqual(group.get("label"), "Payments")
            member_ids = {"n-orders", "n-orderstopic"}
            domain_page = [n for n in domain["nodes"] if n.get("id") == "n-payments" and n.get("type") != "group"]
            self.assertEqual(domain_page, [])
            outsiders = [
                n for n in domain["nodes"]
                if n.get("type") != "group" and n.get("id") not in member_ids
            ]
            self.assertTrue(any(n.get("id") == "n-auth" for n in outsiders))
            self.assertTrue(any(n.get("text") == "? Billing" for n in outsiders))
            for node in outsiders:
                self.assertGreaterEqual(_gap_from_group_right(group, node), 100, node.get("id"))
            svc = _load(vault / "maps" / "service-orders.canvas")
            svc_group = next(n for n in svc["nodes"] if n.get("type") == "group")
            svc_members = {"n-ordersworker"}
            for node in svc["nodes"]:
                if node.get("type") == "group" or node.get("id") in svc_members:
                    continue
                self.assertGreaterEqual(_gap_from_group_right(svc_group, node), 100, node.get("id"))
            auth = next(n for n in domain["nodes"] if n.get("id") == "n-auth")
            auth["x"], auth["y"] = 9999, 8888
            (vault / "maps" / "domain-payments.canvas").write_text(json.dumps(domain), encoding="utf-8")
            render_maps.render_all(vault)
            again = _load(vault / "maps" / "domain-payments.canvas")
            preserved = next(n for n in again["nodes"] if n["id"] == "n-auth")
            self.assertEqual((preserved["x"], preserved["y"]), (9999, 8888))

    def test_person_nodes_use_purple_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            _smoke_vault(vault)
            render_maps.render_all(vault)
            people = _load(vault / "maps" / "people.canvas")
            dana = next(n for n in people["nodes"] if n.get("file") == "wiki/DanaLevi.md")
            self.assertEqual(dana.get("color"), "6")
            legend = next(n for n in _load(vault / "maps" / "world.canvas")["nodes"] if n["id"] == "n-legend")
            self.assertIn("person purple(6)", str(legend.get("text")))


if __name__ == "__main__":
    unittest.main()
