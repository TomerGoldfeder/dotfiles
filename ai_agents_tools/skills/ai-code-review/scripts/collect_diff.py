#!/usr/bin/env python3
"""Collect the change under review into .acr/.

Diff = working tree (committed + uncommitted + untracked) vs merge-base(base, HEAD).

Writes:
  .acr/diff.patch    unified diff with wide context (default 15 lines)
  .acr/meta.json     base, merge-base, head, changed files with +/- counts
  .acr/commits.txt   commit subjects/bodies in merge-base..HEAD

Usage: collect_diff.py [--base REF] [--context N]
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _acr_common import acr_dir, repo_root, run, write_json  # noqa: E402

EXCLUDE = ":(exclude).acr"


def ref_exists(root: Path, ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd=root).returncode == 0


def detect_base(root: Path) -> str | None:
    cands = []
    r = run(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd=root)
    if r.returncode == 0:
        cands.append(r.stdout.strip().replace("refs/remotes/", ""))
    cands += ["origin/main", "origin/master", "main", "master"]
    for c in cands:
        if ref_exists(root, c):
            return c
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="base ref to diff against (default: origin/HEAD, origin/main, main, master)")
    ap.add_argument("--context", type=int, default=15, help="context lines around each change (default 15)")
    args = ap.parse_args()

    root = repo_root()
    out = acr_dir(root)
    has_head = ref_exists(root, "HEAD")

    base = args.base or (detect_base(root) if has_head else None)
    if args.base and not ref_exists(root, args.base):
        print(f"error: base ref '{args.base}' not found", file=sys.stderr)
        return 2

    if not has_head:
        merge_base = None  # empty repo: everything is new
    elif base:
        r = run(["git", "merge-base", base, "HEAD"], cwd=root)
        merge_base = r.stdout.strip() if r.returncode == 0 else None
        if not merge_base:
            print(f"warning: no merge-base between {base} and HEAD; using HEAD", file=sys.stderr)
            merge_base = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    else:
        merge_base = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()

    ctx = f"-U{args.context}"
    diff_target = [merge_base] if merge_base else ["--cached"]  # empty repo fallback
    tracked = run(["git", "diff", ctx, "--no-color", "--find-renames", *diff_target, "--", ".", EXCLUDE], cwd=root).stdout
    numstat = run(["git", "diff", "--numstat", "--find-renames", *diff_target, "--", ".", EXCLUDE], cwd=root).stdout
    namestat = run(["git", "diff", "--name-status", "--find-renames", *diff_target, "--", ".", EXCLUDE], cwd=root).stdout

    files = {}
    for line in namestat.splitlines():
        parts = line.split("\t")
        code = parts[0][0]
        path = parts[-1]
        status = {"A": "added", "D": "deleted", "M": "modified", "R": "renamed", "C": "copied", "T": "modified"}.get(code, "modified")
        files[path] = {"path": path, "status": status, "added": 0, "deleted": 0, "untracked": False}
        if code == "R":
            files[path]["old_path"] = parts[1]
    for line in numstat.splitlines():
        a, d, *rest = line.split("\t")
        path = rest[-1]
        if " => " in path:  # rename shorthand "dir/{a => b}.py"
            continue
        if path in files:
            files[path]["added"] = int(a) if a.isdigit() else 0
            files[path]["deleted"] = int(d) if d.isdigit() else 0

    untracked = [p for p in run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root).stdout.splitlines()
                 if p and not p.startswith(".acr/")]
    untracked_diff = []
    for p in untracked:
        r = run(["git", "diff", "--no-index", ctx, "--no-color", "--", "/dev/null", p], cwd=root)
        untracked_diff.append(r.stdout)
        try:
            n = sum(1 for _ in (root / p).open(errors="replace"))
        except (OSError, UnicodeDecodeError):
            n = 0
        files[p] = {"path": p, "status": "added", "added": n, "deleted": 0, "untracked": True}

    patch = tracked + "".join(untracked_diff)
    (out / "diff.patch").write_text(patch)

    commits = ""
    if merge_base and has_head:
        commits = run(["git", "log", "--format=### %h %s%n%b", f"{merge_base}..HEAD"], cwd=root).stdout
    (out / "commits.txt").write_text(commits)

    total_add = sum(f["added"] for f in files.values())
    total_del = sum(f["deleted"] for f in files.values())
    meta = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "repo_root": str(root),
        "base_ref": base,
        "merge_base": merge_base,
        "head": run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip() if has_head else None,
        "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip() if has_head else None,
        "context_lines": args.context,
        "files": sorted(files.values(), key=lambda f: f["path"]),
        "totals": {"files": len(files), "added": total_add, "deleted": total_del},
        "artifacts": {"diff": ".acr/diff.patch", "commits": ".acr/commits.txt"},
    }
    write_json(out / "meta.json", meta)

    if not files:
        print("EMPTY: no changes between working tree and merge-base "
              f"({base or 'HEAD'}). Pass --base <ref> to choose another base.")
        return 3
    print(f"base={base} merge_base={(merge_base or '')[:12]} files={len(files)} +{total_add} -{total_del}")
    if total_add + total_del > 3000:
        print("WARNING: large change (>3000 lines); reviewers should prioritise non-generated, non-test source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
