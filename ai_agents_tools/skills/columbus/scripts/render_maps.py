#!/usr/bin/env python3
"""Render Obsidian JSON Canvas maps from typed second-brain wiki pages."""
from __future__ import annotations
import argparse, json, re, sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "second-brain" / "scripts"))
import vault as vault_mod  # noqa: E402
from vault import (  # noqa: E402
    Finding, Page, explored_percent, extract_wikilink_target, fog_targets,
    link_targets_by_kind, resolve_vault, slugify, typed_pages, validate,
)

NODE_W, NODE_H, COL_GAP, ROW_GAP = 260, 120, 360, 170
GROUP_PAD, GROUP_LABEL = 40, 40
KNOWLEDGE_COLOR: Dict[str, str] = {
    "rumored": "#6b6b6b", "seen": "5", "understood": "4", "owned": "3",
}
FOG_COLOR = MAYBE_COLOR = "#6b6b6b"
PERSON_COLOR = "6"
EDGE_KINDS: Tuple[str, ...] = ("calls", "emits", "reads", "writes")
STEP_RE = re.compile(r"^\s*(\[\[[^\]]+\]\])\s*->\s*(\[\[[^\]]+\]\])\s*:\s*(.+?)\s*$")
Node = Dict[str, object]
Edge = Dict[str, object]

def _nid(name: str) -> str:
    return f"n-{slugify(name)}"

def _eid(src: str, dst: str, kind: str) -> str:
    return f"e-{slugify(src)}-{slugify(dst)}-{slugify(kind)}"

def _persons(pages: Sequence[Page]) -> Set[str]:
    return {p.name for p in typed_pages(pages) if p.type == "person"}

def _node(name: str, knowledge: Dict[str, str], x: int, y: int, persons: Set[str]) -> Node:
    node: Node = {"id": _nid(name), "x": x, "y": y, "width": NODE_W, "height": NODE_H}
    if name not in knowledge:
        node.update({"type": "text", "text": f"? {name}", "color": FOG_COLOR})
        return node
    node.update({"type": "file", "file": f"wiki/{name}.md"})
    if name in persons:
        node["color"] = PERSON_COLOR
    else:
        color = KNOWLEDGE_COLOR.get(knowledge.get(name, "rumored"))
        if color:
            node["color"] = color
    return node

def _text_node(nid: str, text: str, x: int, y: int, w: int = 280, h: int = 120) -> Node:
    return {"id": nid, "type": "text", "text": text, "x": x, "y": y, "width": w, "height": h}

def _group_node(label: str, members: Sequence[Node]) -> Node:
    node: Node = {"id": f"n-group-{slugify(label)}", "type": "group", "label": label}
    if not members:
        node.update({"x": 0, "y": 0, "width": NODE_W + 2 * GROUP_PAD,
                     "height": NODE_H + 2 * GROUP_PAD + GROUP_LABEL})
        return node
    xs, ys = [int(n["x"]) for n in members], [int(n["y"]) for n in members]
    node.update({
        "x": min(xs) - GROUP_PAD, "y": min(ys) - GROUP_PAD - GROUP_LABEL,
        "width": max(int(n["x"]) + int(n["width"]) for n in members) - min(xs) + 2 * GROUP_PAD,
        "height": max(int(n["y"]) + int(n["height"]) for n in members) - min(ys) + 2 * GROUP_PAD + GROUP_LABEL,
    })
    return node

def _outside_group(nodes: Sequence[Node], group: Node, keep: Set[str]) -> None:
    x = int(group["x"]) + int(group["width"]) + 120
    y = int(group["y"])
    for n in nodes:
        if str(n["id"]) in keep:
            continue
        n["x"], n["y"] = x, y
        y += ROW_GAP

def _load_positions(path: Path) -> Dict[str, Tuple[int, int]]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
        return {}
    out: Dict[str, Tuple[int, int]] = {}
    for node in data["nodes"]:
        if not isinstance(node, dict) or node.get("type") == "group":
            continue
        nid = node.get("id")
        if isinstance(nid, str) and "x" in node and "y" in node:
            out[nid] = (int(node["x"]), int(node["y"]))
    return out

def _apply_positions(nodes: List[Node], prior: Dict[str, Tuple[int, int]]) -> None:
    for node in nodes:
        nid = str(node["id"])
        if node.get("type") != "group" and nid in prior:
            node["x"], node["y"] = prior[nid]

def _layers(names: Sequence[str], edges: Sequence[Tuple[str, str]]) -> Dict[str, int]:
    name_set = set(names)
    succ: Dict[str, List[str]] = defaultdict(list)
    pred: Dict[str, int] = {n: 0 for n in names}
    for a, b in edges:
        if a in name_set and b in name_set and a != b:
            succ[a].append(b)
            pred[b] = pred.get(b, 0) + 1
    layer: Dict[str, int] = {n: 0 for n in names}
    queue: deque[str] = deque([n for n in names if pred.get(n, 0) == 0])
    seen: Set[str] = set()
    while queue:
        cur = queue.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        for nxt in succ.get(cur, []):
            layer[nxt] = max(layer.get(nxt, 0), layer[cur] + 1)
            pred[nxt] -= 1
            if pred[nxt] <= 0:
                queue.append(nxt)
    for n in names:
        layer.setdefault(n, 0)
    return layer

def _layout(
    names: Sequence[str], edges: Sequence[Tuple[str, str]],
    knowledge: Dict[str, str], persons: Set[str],
) -> List[Node]:
    layers = _layers(names, edges)
    by_layer: Dict[int, List[str]] = defaultdict(list)
    for name in names:
        by_layer[layers.get(name, 0)].append(name)
    nodes: List[Node] = []
    for layer_idx in sorted(by_layer):
        for row_idx, name in enumerate(sorted(by_layer[layer_idx])):
            nodes.append(_node(name, knowledge, layer_idx * COL_GAP, row_idx * ROW_GAP, persons))
    return nodes

def _domain_of(page: Page, by_name: Dict[str, Page]) -> Optional[str]:
    if page.type == "domain":
        return page.name
    raw = page.props.get("domain")
    if isinstance(raw, str):
        return extract_wikilink_target(raw)
    if isinstance(raw, list) and raw:
        return extract_wikilink_target(str(raw[0]))
    parent = page.props.get("parent")
    if isinstance(parent, str):
        pname = extract_wikilink_target(parent)
        if pname and pname in by_name:
            return _domain_of(by_name[pname], by_name)
    return None

def _edge_pairs(pages: Sequence[Page]) -> List[Tuple[str, str, str, bool]]:
    out: List[Tuple[str, str, str, bool]] = []
    for page in typed_pages(pages):
        by_kind = link_targets_by_kind(page)
        for kind in EDGE_KINDS:
            for dst in by_kind.get(kind, []):
                out.append((page.name, dst, kind, False))
        for dst in by_kind.get("maybe", []):
            out.append((page.name, dst, "maybe", True))
    return out

def _canvas_edges(pairs: Iterable[Tuple[str, str, str, bool]], present: Set[str]) -> List[Edge]:
    edges: List[Edge] = []
    seen: Set[str] = set()
    for src, dst, kind, is_maybe in pairs:
        if src not in present or dst not in present:
            continue
        eid = _eid(src, dst, kind)
        if eid in seen:
            continue
        seen.add(eid)
        edge: Edge = {"id": eid, "fromNode": _nid(src), "toNode": _nid(dst)}
        if is_maybe:
            edge["color"] = MAYBE_COLOR
            edge["label"] = "?" if kind == "maybe" else f"{kind}?"
        else:
            edge["label"] = kind
        edges.append(edge)
    return edges

def _write(path: Path, nodes: List[Node], edges: List[Edge]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=2) + "\n", encoding="utf-8")

def _legend_stats(explored: float, places: int, fog_n: int, x: int) -> List[Node]:
    legend = (
        "Legend\nrumored gray · seen cyan(5) · understood green(4) · owned yellow(3)\n"
        "person purple(6) · fog = ? Name · maybe edges gray with ?"
    )
    return [
        _text_node("n-legend", legend, x, 0, w=360, h=140),
        _text_node("n-stats", f"Explored {explored:.0f}% · {places} places · {fog_n} in fog", x, 160, w=360, h=80),
    ]

def _as_list(value: object) -> List[str]:
    if value is None:
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]

def _grouped_canvas(
    member_names: Sequence[str], outer_names: Sequence[str],
    pairs: Sequence[Tuple[str, str, str, bool]], knowledge: Dict[str, str],
    persons: Set[str], prior: Dict[str, Tuple[int, int]], label: str,
) -> Tuple[List[Node], List[Edge]]:
    mem_set, out_set = set(member_names), set(outer_names)
    members = _layout(member_names, [(a, b) for a, b, _k, _m in pairs if a in mem_set and b in mem_set], knowledge, persons)
    outer = _layout(outer_names, [(a, b) for a, b, _k, _m in pairs if a in out_set and b in out_set], knowledge, persons)
    _apply_positions(members, prior)
    _apply_positions(outer, prior)
    group = _group_node(label, members)
    _outside_group(outer, group, set(prior))
    return [group] + members + outer, _canvas_edges(pairs, mem_set | out_set)

def render_world(
    pages: Sequence[Page], by_name: Dict[str, Page], maps_dir: Path, fog: List[str]
) -> None:
    path = maps_dir / "world.canvas"
    prior = _load_positions(path)
    knowledge = {p.name: p.knowledge for p in typed_pages(pages)}
    persons = _persons(pages)
    names: List[str] = [p.name for p in typed_pages(pages) if p.type == "domain"]
    externals = [p.name for p in typed_pages(pages) if p.type == "external"]
    names.extend(externals)
    unassigned = any(
        p.type in ("service", "datastore") and _domain_of(p, by_name) is None
        for p in typed_pages(pages)
    )
    if unassigned:
        names.append("Unassigned")
    counts: Dict[Tuple[str, str, str], int] = defaultdict(int)
    external_set = set(externals)
    for src, dst, kind, is_maybe in _edge_pairs(pages):
        if is_maybe:
            continue
        src_p, dst_p = by_name.get(src), by_name.get(dst)
        src_d = (_domain_of(src_p, by_name) if src_p else None) or "Unassigned"
        if dst_p:
            dst_d = _domain_of(dst_p, by_name) or (dst if dst in external_set else "Unassigned")
        else:
            dst_d = dst if dst in external_set else "Unassigned"
        if src_d == dst_d:
            continue
        for d in (src_d, dst_d):
            if d not in names:
                names.append(d)
        counts[(src_d, dst_d, kind)] += 1
    nodes = _layout(names, [(a, b) for (a, b, _) in counts], knowledge, persons)
    nodes = [
        _text_node(_nid("Unassigned"), "Unassigned", int(n["x"]), int(n["y"]))
        if n.get("id") == _nid("Unassigned") else n
        for n in nodes
    ]
    edges: List[Edge] = [
        {"id": _eid(s, d, k), "fromNode": _nid(s), "toNode": _nid(d), "label": f"{c} {k}"}
        for (s, d, k), c in sorted(counts.items())
    ]
    places = len([p for p in typed_pages(pages) if p.type in vault_mod.MAP_PLACE_TYPES])
    pct = explored_percent(pages, len(fog))
    max_x = max((int(n["x"]) for n in nodes), default=0) + COL_GAP
    nodes.extend(_legend_stats(pct, places, len(fog), max_x))
    _apply_positions(nodes, prior)
    _write(path, nodes, edges)

def _neighbors(core: Set[str], pairs: Sequence[Tuple[str, str, str, bool]]) -> Set[str]:
    out: Set[str] = set()
    for src, dst, _k, _m in pairs:
        if src in core:
            out.add(dst)
        if dst in core:
            out.add(src)
    return out - core

def render_domain_canvases(
    pages: Sequence[Page], by_name: Dict[str, Page], maps_dir: Path, fog: Set[str]
) -> Set[str]:
    written: Set[str] = set()
    knowledge = {p.name: p.knowledge for p in typed_pages(pages)}
    persons = _persons(pages)
    pairs = _edge_pairs(pages)
    for domain in [p for p in typed_pages(pages) if p.type == "domain"]:
        members = [
            p.name for p in typed_pages(pages)
            if p.type in ("service", "datastore", "external") and _domain_of(p, by_name) == domain.name
        ]
        neighbor_set = _neighbors(set(members) | {domain.name}, pairs)
        for n in neighbor_set:
            if n not in by_name:
                fog.add(n)
        path = maps_dir / f"domain-{slugify(domain.name)}.canvas"
        nodes, edges = _grouped_canvas(
            members, sorted(neighbor_set), pairs, knowledge, persons, _load_positions(path), domain.name,
        )
        _write(path, nodes, edges)
        written.add(path.name)
    return written

def render_service_canvases(
    pages: Sequence[Page], by_name: Dict[str, Page], maps_dir: Path, fog: Set[str]
) -> Set[str]:
    written: Set[str] = set()
    knowledge = {p.name: p.knowledge for p in typed_pages(pages)}
    persons = _persons(pages)
    pairs = _edge_pairs(pages)
    for service in [p for p in typed_pages(pages) if p.type == "service"]:
        components = [
            p.name for p in typed_pages(pages)
            if p.type == "component" and isinstance(p.props.get("parent"), str)
            and extract_wikilink_target(str(p.props.get("parent"))) == service.name
        ]
        if not components:
            continue
        neighbors = _neighbors({service.name} | set(components), pairs)
        for n in neighbors:
            if n not in by_name:
                fog.add(n)
        path = maps_dir / f"service-{slugify(service.name)}.canvas"
        nodes, edges = _grouped_canvas(
            components, [service.name] + sorted(neighbors), pairs, knowledge, persons,
            _load_positions(path), service.name,
        )
        _write(path, nodes, edges)
        written.add(path.name)
    return written

def render_flow_canvases(
    pages: Sequence[Page], maps_dir: Path, fog: Set[str], summary: List[str]
) -> Set[str]:
    written: Set[str] = set()
    knowledge = {p.name: p.knowledge for p in typed_pages(pages)}
    persons = _persons(pages)
    for flow in [p for p in typed_pages(pages) if p.type == "flow"]:
        ordered: List[str] = []
        edges: List[Edge] = []
        step_num = 0
        for raw in _as_list(flow.props.get("steps")):
            match = STEP_RE.match(raw)
            if match is None:
                summary.append(f"invalid flow step on {flow.name}: {raw!r}")
                continue
            a = extract_wikilink_target(match.group(1))
            b = extract_wikilink_target(match.group(2))
            if not a or not b:
                summary.append(f"invalid flow step on {flow.name}: {raw!r}")
                continue
            step_num += 1
            for name in (a, b):
                if name not in ordered:
                    ordered.append(name)
                if name not in knowledge:
                    fog.add(name)
            edges.append({
                "id": _eid(a, b, f"step{step_num}"), "fromNode": _nid(a), "toNode": _nid(b),
                "label": f"{step_num}. {match.group(3).strip()}",
            })
        path = maps_dir / f"flow-{slugify(flow.name)}.canvas"
        prior = _load_positions(path)
        nodes = [_node(name, knowledge, idx * COL_GAP, 0, persons) for idx, name in enumerate(ordered)]
        _apply_positions(nodes, prior)
        _write(path, nodes, edges)
        written.add(path.name)
    return written

def render_people(pages: Sequence[Page], maps_dir: Path, fog: Set[str]) -> None:
    path = maps_dir / "people.canvas"
    prior = _load_positions(path)
    persons_pages = sorted([p for p in typed_pages(pages) if p.type == "person"], key=lambda p: p.name)
    knowledge = {p.name: p.knowledge for p in typed_pages(pages)}
    persons = {p.name for p in persons_pages}
    targets: List[str] = []
    edges: List[Edge] = []
    for person in persons_pages:
        for kind, label in (("owns", "owns"), ("ask_about", "ask")):
            for item in _as_list(person.props.get(kind)):
                dst = extract_wikilink_target(item)
                if not dst:
                    continue
                if dst not in targets:
                    targets.append(dst)
                if dst not in knowledge:
                    fog.add(dst)
                edges.append({
                    "id": _eid(person.name, dst, kind),
                    "fromNode": _nid(person.name), "toNode": _nid(dst), "label": label,
                })
    nodes: List[Node] = [
        _node(p.name, knowledge, 0, i * ROW_GAP, persons) for i, p in enumerate(persons_pages)
    ]
    for i, name in enumerate(targets):
        nodes.append(_node(name, knowledge, COL_GAP, i * ROW_GAP, persons))
    _apply_positions(nodes, prior)
    _write(path, nodes, edges)

def delete_stale(maps_dir: Path, keep: Set[str]) -> List[str]:
    deleted: List[str] = []
    if not maps_dir.is_dir():
        return deleted
    for path in maps_dir.glob("*.canvas"):
        if path.name.startswith(("domain-", "service-", "flow-")) and path.name not in keep:
            path.unlink()
            deleted.append(path.name)
    return deleted

def render_all(vault: Path) -> Tuple[List[str], List[str], float, List[Finding]]:
    pages = vault_mod.load_pages(vault)
    findings = validate(pages)
    maps_dir = vault / "maps"
    fog_list = fog_targets(pages)
    fog = set(fog_list)
    by_name = {p.name: p for p in pages}
    summary: List[str] = []
    render_world(pages, by_name, maps_dir, fog_list)
    keep: Set[str] = set()
    keep |= render_domain_canvases(pages, by_name, maps_dir, fog)
    keep |= render_service_canvases(pages, by_name, maps_dir, fog)
    keep |= render_flow_canvases(pages, maps_dir, fog, summary)
    render_people(pages, maps_dir, fog)
    deleted = delete_stale(maps_dir, keep)
    written = ["world.canvas", "people.canvas"] + sorted(keep)
    pct = explored_percent(pages, len(fog_list))
    for line in summary:
        print(f"warning: {line}", file=sys.stderr)
    return written, deleted, pct, findings

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    vault = resolve_vault(args.vault)
    pages = vault_mod.load_pages(vault)
    findings = validate(pages)
    if args.check:
        for f in findings:
            print(f"{f.page}: {f.message}")
        return 1 if findings else 0
    for f in findings:
        print(f"warning: {f.page}: {f.message}", file=sys.stderr)
    written, deleted, pct, _ = render_all(vault)
    print(f"canvases written: {len(written)}; deleted stale: {len(deleted)}; explored {pct:.0f}%")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
