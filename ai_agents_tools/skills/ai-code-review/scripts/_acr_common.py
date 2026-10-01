"""Shared helpers for the ai-code-review scripts (stdlib only, Python 3.9+)."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

TEST_FILE_PATTERNS = [
    r"(^|/)tests?/",
    r"(^|/)__tests__/",
    r"(^|/)spec/",
    r"(^|/)test_[^/]*\.py$",
    r"_test\.(py|go)$",
    r"\.(test|spec)\.[cm]?[jt]sx?$",
    r"(^|/)conftest\.py$",
    r"Tests?\.(java|kt|cs)$",
    r"_spec\.rb$",
]
_TEST_RE = re.compile("|".join(TEST_FILE_PATTERNS))


def is_test_file(path: str) -> bool:
    return bool(_TEST_RE.search(path))


def run(cmd: List[str], cwd: Optional[Path] = None, check: bool = False,
        input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, input=input_text)
    if check and r.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(cmd)}\n{r.stderr.strip()}")
    return r


def repo_root() -> Path:
    r = run(["git", "rev-parse", "--show-toplevel"])
    if r.returncode != 0:
        raise SystemExit("not inside a git repository")
    return Path(r.stdout.strip())


def acr_dir(root: Optional[Path] = None) -> Path:
    d = (root or repo_root()) / ".acr"
    d.mkdir(parents=True, exist_ok=True)
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n")  # keep review artifacts out of git without touching the repo's .gitignore
    return d


def load_meta(root: Optional[Path] = None) -> Dict:
    p = acr_dir(root) / "meta.json"
    if not p.exists():
        raise SystemExit("missing .acr/meta.json: run scripts/collect_diff.py first")
    return json.loads(p.read_text())


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _strip_prefix(p: str) -> str:
    p = p.strip()
    if p.startswith('"') and p.endswith('"'):
        p = p[1:-1]
    for pref in ("a/", "b/"):
        if p.startswith(pref):
            return p[len(pref):]
    return p


def parse_patch(text: str) -> List[Dict]:
    """Parse a unified git diff into files -> hunks -> lines.

    Each line is a dict: {"tag": "+"|"-"|" ", "text": str, "old": int|None, "new": int|None}.
    """
    files: List[Dict] = []
    cur: Optional[Dict] = None
    hunk: Optional[Dict] = None
    o = n = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            cur = {"old_path": None, "new_path": None, "status": "modified",
                   "binary": False, "hunks": []}
            files.append(cur)
            hunk = None
            m = re.match(r"^diff --git (\S+) (\S+)$", raw)
            if m:
                cur["old_path"], cur["new_path"] = _strip_prefix(m.group(1)), _strip_prefix(m.group(2))
            continue
        if cur is None:
            continue
        if hunk is None:
            if raw.startswith("new file mode"):
                cur["status"] = "added"
                continue
            if raw.startswith("deleted file mode"):
                cur["status"] = "deleted"
                continue
            if raw.startswith("rename from "):
                cur["status"] = "renamed"
                cur["old_path"] = raw[len("rename from "):]
                continue
            if raw.startswith("rename to "):
                cur["new_path"] = raw[len("rename to "):]
                continue
            if raw.startswith("Binary files"):
                cur["binary"] = True
                continue
            if raw.startswith("--- "):
                p = raw[4:]
                if p.strip() == "/dev/null":
                    cur["status"] = "added"
                else:
                    cur["old_path"] = _strip_prefix(p)
                continue
            if raw.startswith("+++ "):
                p = raw[4:]
                if p.strip() == "/dev/null":
                    cur["status"] = "deleted"
                else:
                    cur["new_path"] = _strip_prefix(p)
                continue
        m = HUNK_RE.match(raw)
        if m:
            o, n = int(m.group(1)), int(m.group(3))
            hunk = {"old_start": o, "new_start": n, "header": raw, "lines": []}
            cur["hunks"].append(hunk)
            continue
        if hunk is None:
            continue
        if raw.startswith("+"):
            hunk["lines"].append({"tag": "+", "text": raw[1:], "old": None, "new": n})
            n += 1
        elif raw.startswith("-"):
            hunk["lines"].append({"tag": "-", "text": raw[1:], "old": o, "new": None})
            o += 1
        elif raw.startswith("\\"):
            continue  # "\ No newline at end of file"
        else:
            hunk["lines"].append({"tag": " ", "text": raw[1:], "old": o, "new": n})
            o += 1
            n += 1
    for f in files:
        f["path"] = f["old_path"] if f["status"] == "deleted" else (f["new_path"] or f["old_path"])
    return files


def load_patch(root: Optional[Path] = None) -> List[Dict]:
    p = acr_dir(root) / "diff.patch"
    if not p.exists():
        raise SystemExit("missing .acr/diff.patch: run scripts/collect_diff.py first")
    return parse_patch(p.read_text(errors="replace"))


def added_lines(f: Dict) -> List[Dict]:
    return [ln for h in f["hunks"] for ln in h["lines"] if ln["tag"] == "+"]


def removed_lines(f: Dict) -> List[Dict]:
    return [ln for h in f["hunks"] for ln in h["lines"] if ln["tag"] == "-"]


def file_at(root: Path, rev: Optional[str], path: str) -> Optional[str]:
    """Content of `path` at git `rev`, or in the working tree when rev is None."""
    if rev is None:
        p = root / path
        return p.read_text(errors="replace") if p.is_file() else None
    r = run(["git", "show", f"{rev}:{path}"], cwd=root)
    return r.stdout if r.returncode == 0 else None
