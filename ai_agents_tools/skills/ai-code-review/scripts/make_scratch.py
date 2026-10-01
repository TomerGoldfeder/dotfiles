#!/usr/bin/env python3
"""Disposable scratch copy of the code under review, for reproductions.

  make_scratch.py create      -> prints JSON {"path": ...}: a detached git worktree at HEAD
                                 with the working-tree changes (uncommitted + untracked) applied,
                                 and .venv / venv / node_modules symlinked from the repo.
  make_scratch.py remove PATH -> removes one scratch worktree
  make_scratch.py cleanup     -> removes every scratch worktree this skill created

The original checkout is never modified.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _acr_common import acr_dir, repo_root, run  # noqa: E402

PREFIX = "acr-scratch-"


def registry(root: Path) -> Path:
    d = acr_dir(root) / "scratch"
    d.mkdir(exist_ok=True)
    return d  # one file per worktree, so parallel verifiers never race on a shared file


def load_reg(root: Path) -> list:
    return [p.read_text().strip() for p in registry(root).glob("*.path")]


def reg_add(root: Path, wt: Path) -> None:
    (registry(root) / f"{wt.parent.name}.path").write_text(str(wt) + "\n")


def reg_remove(root: Path, wt: str) -> None:
    (registry(root) / f"{Path(wt).parent.name}.path").unlink(missing_ok=True)


def create(root: Path) -> int:
    parent = Path(tempfile.mkdtemp(prefix=PREFIX))
    wt = parent / "wt"
    r = run(["git", "worktree", "add", "--detach", "--quiet", str(wt), "HEAD"], cwd=root)
    if r.returncode != 0:
        print(json.dumps({"error": r.stderr.strip()}))
        return 1
    diff = run(["git", "diff", "HEAD", "--binary", "--", ".", ":(exclude).acr"], cwd=root).stdout
    if diff.strip():
        a = run(["git", "apply", "--whitespace=nowarn"], cwd=wt, input_text=diff)
        if a.returncode != 0:
            print(json.dumps({"error": "could not apply uncommitted changes: " + a.stderr.strip(), "path": str(wt)}))
            return 1
    for p in run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root).stdout.splitlines():
        if not p or p.startswith(".acr/"):
            continue
        src, dst = root / p, wt / p
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    linked = []
    for name in (".venv", "venv", "node_modules"):
        if (root / name).exists() and not (wt / name).exists():
            os.symlink(root / name, wt / name)
            linked.append(name)
    reg_add(root, wt)
    print(json.dumps({"path": str(wt), "linked": linked}))
    return 0


def remove(root: Path, path: str) -> int:
    run(["git", "worktree", "remove", "--force", path], cwd=root)
    parent = Path(path).parent
    if parent.name.startswith(PREFIX):
        shutil.rmtree(parent, ignore_errors=True)
    reg_remove(root, path)
    return 0


def cleanup(root: Path) -> int:
    for p in list(load_reg(root)):
        remove(root, p)
    run(["git", "worktree", "prune"], cwd=root)
    print("scratch worktrees removed")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("create", "remove", "cleanup"):
        print(__doc__)
        return 2
    root = repo_root()
    if sys.argv[1] == "create":
        return create(root)
    if sys.argv[1] == "remove":
        if len(sys.argv) < 3:
            print("usage: make_scratch.py remove PATH")
            return 2
        return remove(root, sys.argv[2])
    return cleanup(root)


if __name__ == "__main__":
    sys.exit(main())
