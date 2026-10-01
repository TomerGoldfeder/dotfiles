#!/usr/bin/env python3
"""Locate coding-agent session transcripts (JSONL) for this repository.

Looks in:
  Claude Code: ~/.claude/projects/<repo path with non-alphanumerics -> '-'>/*.jsonl
  Cursor:      ~/.cursor/projects/<dir derived from repo path>/agent-transcripts/**/*.jsonl
Falls back to scanning recent transcripts whose first lines mention the repo path.

Does NOT convert or normalise transcripts; the skill reads the JSONL as-is.
Writes .acr/transcripts.json (candidates, newest first) and prints a short table.

Usage: find_transcript.py [--days N] [--limit N] [--path FILE]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _acr_common import acr_dir, load_meta, repo_root, run, write_json  # noqa: E402

HOME = Path(os.path.expanduser("~"))


def alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def first_user_text(path: Path, max_lines: int = 400) -> str | None:
    """Best-effort preview of the first user message. Format-agnostic: walks the JSON."""
    def texts(obj):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, list):
            for x in obj:
                yield from texts(x)
        elif isinstance(obj, dict):
            for k in ("text", "content", "message", "prompt"):
                if k in obj:
                    yield from texts(obj[k])

    try:
        with path.open(errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    break
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(rec, dict):
                    continue
                role = rec.get("role") or rec.get("type") or (rec.get("message") or {}).get("role")
                if role not in ("user", "human"):
                    continue
                for t in texts(rec):
                    t = t.strip()
                    if t and not t.startswith(("<", "{")):
                        return re.sub(r"\s+", " ", t)[:200]
    except OSError:
        return None
    return None


def mentions(path: Path, needle: str, max_lines: int = 60) -> bool:
    try:
        with path.open(errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    return False
                if needle in line:
                    return True
    except OSError:
        return False
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14, help="lookback for the content-scan fallback (default 14)")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--path", help="use this transcript file explicitly")
    args = ap.parse_args()

    root = repo_root()
    out = acr_dir(root)
    try:
        meta = load_meta(root)
    except SystemExit:
        meta = {}
    repo = str(root)
    slug = re.sub(r"[^A-Za-z0-9]", "-", repo)

    # window start: merge-base commit time minus one day
    window_start = None
    mb = meta.get("merge_base")
    if mb:
        r = run(["git", "show", "-s", "--format=%ct", mb], cwd=root)
        if r.returncode == 0 and r.stdout.strip().isdigit():
            window_start = int(r.stdout.strip()) - 86400

    found = {}

    def add(p: Path, tool: str, how: str):
        if p.is_file() and p.suffix == ".jsonl" and str(p) not in found:
            found[str(p)] = {"tool": tool, "match": how, "path": str(p)}

    if args.path:
        add(Path(args.path).expanduser().resolve(), "explicit", "explicit")
    else:
        claude_root = HOME / ".claude" / "projects"
        d = claude_root / slug
        if d.is_dir():
            for p in d.glob("*.jsonl"):
                add(p, "claude-code", "project-dir")
        cursor_root = HOME / ".cursor" / "projects"
        if cursor_root.is_dir():
            target = alnum(repo)
            for proj in cursor_root.iterdir():
                if not proj.is_dir():
                    continue
                name = alnum(proj.name)
                if name and (target.endswith(name) or name.endswith(target)) and len(name) >= min(len(target), 8):
                    for p in proj.glob("agent-transcripts/**/*.jsonl"):
                        add(p, "cursor", "project-dir")

        # fallback: content scan of recent transcripts in both stores
        if not found:
            cutoff = dt.datetime.now().timestamp() - args.days * 86400
            pools = [(claude_root, "*/*.jsonl", "claude-code"), (cursor_root, "*/agent-transcripts/**/*.jsonl", "cursor")]
            for base, pattern, tool in pools:
                if not base.is_dir():
                    continue
                for p in base.glob(pattern):
                    try:
                        if p.stat().st_mtime >= cutoff and mentions(p, repo):
                            add(p, tool, "content-scan")
                    except OSError:
                        pass

    cands = []
    for c in found.values():
        p = Path(c["path"])
        st = p.stat()
        try:
            with p.open(errors="replace") as fh:
                n_lines = sum(1 for _ in fh)
        except OSError:
            n_lines = None
        c.update({
            "modified": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            "size_bytes": st.st_size,
            "lines": n_lines,
            "in_window": window_start is None or st.st_mtime >= window_start,
            "first_user_message": first_user_text(p),
        })
        cands.append((st.st_mtime, c))
    cands = [c for _, c in sorted(cands, key=lambda x: x[0], reverse=True)][: args.limit]
    # skip sub-agent transcripts as primary picks (they hold delegated tasks, not the user's intent)
    for c in cands:
        c["is_subagent"] = "/subagents/" in c["path"] or "subagent" in Path(c["path"]).name

    write_json(out / "transcripts.json", {"repo": repo, "candidates": cands})
    if not cands:
        print("NO TRANSCRIPT FOUND (proceed without one, or pass --path).")
        return 0
    for i, c in enumerate(cands, 1):
        flag = "*" if c["in_window"] else " "
        sub = " [subagent]" if c["is_subagent"] else ""
        print(f"{i}.{flag} {c['tool']:<11} {c['modified']}  {c['size_bytes'] / 1024:.0f}KB  "
              f"{c['lines']} lines{sub}\n    {c['path']}\n    first user msg: {c['first_user_message']!r}")
    print("* = modified after the merge-base commit (likely produced this change)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
