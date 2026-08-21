#!/usr/bin/env bash
# Commit coverage work on a new branch: default branch -> pull -> branch -> stage changes -> commit -> push.
# Usage (from repo root):
#   bash "${DEPLOYMENT_FOR_MACHINE}/skills/pytest-coverage-incremental/scripts/commit-coverage-branch.sh" "<branch-suffix>" "commit message line 1"
set -euo pipefail

if [[ "${1:-}" == "" || "${2:-}" == "" ]]; then
  echo "Usage: $0 <branch-suffix> <commit message>" >&2
  exit 1
fi

BRANCH_SUFFIX="$1"
shift
COMMIT_MSG="$*"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Not a git repository." >&2
  exit 1
}
cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  :
else
  echo "No changes to commit." >&2
  exit 1
fi

DEFAULT_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')"
git checkout "$DEFAULT_BRANCH"
git pull --rebase origin "$DEFAULT_BRANCH"

NEW_BRANCH="coverage-${BRANCH_SUFFIX}"
if git show-ref --verify --quiet "refs/heads/${NEW_BRANCH}"; then
  echo "Branch ${NEW_BRANCH} already exists. Choose a different suffix." >&2
  exit 1
fi
git checkout -b "$NEW_BRANCH"

# Stage: modified/deleted tracked files + new untracked files (portable; no bash mapfile)
git add -u
# xargs runs nothing when there are no untracked files (BSD/GNU)
git ls-files --others --exclude-standard -z | xargs -0 git add -- 2>/dev/null || true
git commit -m "$COMMIT_MSG"
git push -u origin HEAD
