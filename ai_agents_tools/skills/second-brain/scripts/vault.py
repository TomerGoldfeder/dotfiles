#!/usr/bin/env python3
"""Load and validate typed second-brain wiki pages (stdlib-only, Python 3.9)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

KNOWN_TYPES: frozenset[str] = frozenset(
    {
        "domain",
        "service",
        "component",
        "datastore",
        "external",
        "flow",
        "repo",
        "person",
        "concept",
        "question",
        "commitment",
    }
)
MAP_PLACE_TYPES: frozenset[str] = frozenset(
    {"domain", "service", "component", "datastore", "external", "flow"}
)
KNOWLEDGE_TYPES: frozenset[str] = MAP_PLACE_TYPES | frozenset({"repo", "concept"})
KNOWLEDGE_VALUES: frozenset[str] = frozenset(
    {"rumored", "seen", "understood", "owned"}
)
KNOWLEDGE_WEIGHTS: Dict[str, float] = {
    "rumored": 0.0,
    "seen": 1.0 / 3.0,
    "understood": 2.0 / 3.0,
    "owned": 1.0,
}
STATUS_BY_TYPE: Dict[str, frozenset[str]] = {
    "question": frozenset({"open", "answered"}),
    "commitment": frozenset({"open", "done"}),
}
DATASTORE_KINDS: frozenset[str] = frozenset(
    {"db", "queue", "topic", "bucket", "cache", "other"}
)
SOURCE_PREFIXES: Tuple[str, ...] = ("repo:", "doc:", "meeting:", "pr:", "chat:")
EDGE_LINK_KEYS: frozenset[str] = frozenset(
    {
        "owners",
        "domain",
        "calls",
        "emits",
        "reads",
        "writes",
        "maybe",
        "parent",
        "implements",
        "owns",
        "ask_about",
        "ask",
        "about",
        "to",
    }
)
WIKILINK_RE: re.Pattern[str] = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
DEFAULT_VAULT: Path = Path.home() / ".second_brain_vault"


@dataclass
class Page:
    name: str
    type: Optional[str]
    knowledge: str
    props: Dict[str, object]
    path: Path
    frontmatter_errors: List[str] = field(default_factory=list)

    @property
    def is_typed(self) -> bool:
        return self.type is not None


@dataclass
class Finding:
    page: str
    message: str


def resolve_vault(explicit: Optional[str] = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env: Optional[str] = os.environ.get("SECOND_BRAIN_VAULT")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_VAULT.resolve()


def extract_wikilink_target(text: str) -> Optional[str]:
    match: Optional[re.Match[str]] = WIKILINK_RE.search(text)
    if match is None:
        return None
    return match.group(1).strip()


def extract_all_wikilink_targets(text: str) -> List[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def _strip_quotes(value: str) -> str:
    text: str = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def parse_frontmatter(text: str) -> Tuple[Dict[str, object], List[str]]:
    """Parse YAML-subset frontmatter. Returns (props, malformed_line_messages)."""
    props: Dict[str, object] = {}
    errors: List[str] = []
    if not text.startswith("---"):
        return props, errors
    end: int = text.find("\n---", 3)
    if end < 0:
        errors.append("unclosed frontmatter")
        return props, errors
    body: str = text[3:end].lstrip("\n")
    lines: List[str] = body.splitlines()
    idx: int = 0
    while idx < len(lines):
        line: str = lines[idx]
        if not line.strip() or line.strip().startswith("#"):
            idx += 1
            continue
        if line.startswith(" ") or line.startswith("\t"):
            errors.append(f"malformed frontmatter line: {line!r}")
            idx += 1
            continue
        if ":" not in line:
            errors.append(f"malformed frontmatter line: {line!r}")
            idx += 1
            continue
        key: str
        rest: str
        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        if rest == "[]":
            props[key] = []
            idx += 1
            continue
        if rest == "":
            items: List[str] = []
            idx += 1
            while idx < len(lines):
                item_line: str = lines[idx]
                stripped: str = item_line.strip()
                if not stripped:
                    idx += 1
                    continue
                if stripped.startswith("- ") or stripped.startswith("-"):
                    raw: str = stripped[1:].strip()
                    if raw.startswith(" "):
                        raw = raw.strip()
                    if stripped.startswith("- "):
                        raw = stripped[2:].strip()
                    items.append(_strip_quotes(raw))
                    idx += 1
                    continue
                if item_line.startswith(" ") or item_line.startswith("\t"):
                    errors.append(f"malformed frontmatter line: {item_line!r}")
                    idx += 1
                    continue
                break
            props[key] = items
            continue
        props[key] = _strip_quotes(rest)
        idx += 1
    return props, errors


def load_page(path: Path) -> Page:
    text: str = path.read_text(encoding="utf-8")
    props: Dict[str, object]
    errors: List[str]
    props, errors = parse_frontmatter(text)
    raw_type: object = props.get("type")
    page_type: Optional[str] = str(raw_type) if isinstance(raw_type, str) and raw_type else None
    raw_knowledge: object = props.get("knowledge", "rumored")
    knowledge: str = (
        str(raw_knowledge) if isinstance(raw_knowledge, str) and raw_knowledge else "rumored"
    )
    return Page(
        name=path.stem,
        type=page_type,
        knowledge=knowledge,
        props=props,
        path=path,
        frontmatter_errors=errors,
    )


def load_pages(vault: Path) -> List[Page]:
    wiki: Path = vault / "wiki"
    if not wiki.is_dir():
        return []
    pages: List[Page] = []
    for path in sorted(wiki.glob("*.md")):
        pages.append(load_page(path))
    return pages


def typed_pages(pages: Sequence[Page]) -> List[Page]:
    return [p for p in pages if p.is_typed]


def _as_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _sources_ok(sources: List[str]) -> bool:
    return any(any(s.startswith(prefix) for prefix in SOURCE_PREFIXES) for s in sources)


def _has_pr_source(sources: List[str]) -> bool:
    return any(s.startswith("pr:") for s in sources)


def validate(pages: Sequence[Page]) -> List[Finding]:
    findings: List[Finding] = []
    for page in pages:
        for err in page.frontmatter_errors:
            findings.append(Finding(page=page.name, message=err))
        if not page.is_typed:
            continue
        assert page.type is not None
        if page.type not in KNOWN_TYPES:
            findings.append(Finding(page=page.name, message=f"unknown type: {page.type}"))
            continue
        if page.type in KNOWLEDGE_TYPES:
            if page.knowledge not in KNOWLEDGE_VALUES:
                findings.append(
                    Finding(
                        page=page.name,
                        message=f"invalid knowledge value: {page.knowledge}",
                    )
                )
            sources: List[str] = _as_list(page.props.get("sources"))
            if page.knowledge != "rumored" and page.knowledge in KNOWLEDGE_VALUES:
                if not sources or not _sources_ok(sources):
                    findings.append(
                        Finding(
                            page=page.name,
                            message="knowledge above rumored requires sources",
                        )
                    )
            if page.knowledge == "owned" and not _has_pr_source(sources):
                findings.append(
                    Finding(page=page.name, message="owned requires a pr: source")
                )
        if page.type in STATUS_BY_TYPE:
            status: object = page.props.get("status")
            allowed: frozenset[str] = STATUS_BY_TYPE[page.type]
            if not isinstance(status, str) or status not in allowed:
                findings.append(
                    Finding(
                        page=page.name,
                        message=f"invalid status value: {status!r}",
                    )
                )
        if page.type == "datastore":
            kind: object = page.props.get("kind")
            if kind is not None and (
                not isinstance(kind, str) or kind not in DATASTORE_KINDS
            ):
                findings.append(
                    Finding(page=page.name, message=f"invalid datastore kind: {kind!r}")
                )
    return findings


def link_targets_for_page(page: Page) -> List[str]:
    targets: List[str] = []
    for key in EDGE_LINK_KEYS:
        if key not in page.props:
            continue
        for item in _as_list(page.props.get(key)):
            targets.extend(extract_all_wikilink_targets(item))
    for step in _as_list(page.props.get("steps")):
        targets.extend(extract_all_wikilink_targets(step))
    # preserve order, unique
    seen: set[str] = set()
    ordered: List[str] = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


def link_targets_by_kind(page: Page) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for key in EDGE_LINK_KEYS:
        if key not in page.props:
            continue
        links: List[str] = []
        for item in _as_list(page.props.get(key)):
            links.extend(extract_all_wikilink_targets(item))
        if links:
            result[key] = links
    return result


def fog_targets(pages: Sequence[Page]) -> List[str]:
    names: set[str] = {p.name for p in pages}
    fog: List[str] = []
    seen: set[str] = set()
    for page in typed_pages(pages):
        for target in link_targets_for_page(page):
            if target not in names and target not in seen:
                seen.add(target)
                fog.append(target)
    return fog


def explored_percent(pages: Sequence[Page], fog_count: int) -> float:
    places: List[Page] = [
        p for p in typed_pages(pages) if p.type in MAP_PLACE_TYPES
    ]
    total: int = len(places) + fog_count
    if total == 0:
        return 0.0
    weight_sum: float = 0.0
    for page in places:
        weight_sum += KNOWLEDGE_WEIGHTS.get(page.knowledge, 0.0)
    # fog counts as rumored (weight 0)
    return 100.0 * weight_sum / float(total)


def slugify(name: str) -> str:
    out: List[str] = []
    prev_dash: bool = False
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    text: str = "".join(out).strip("-")
    return text or "unnamed"
