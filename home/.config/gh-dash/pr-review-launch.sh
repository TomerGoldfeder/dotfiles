#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: pr-review-launch.sh <repo-path> <repo-name> <pr-number>" >&2
  exit 2
fi

repo_path="$1"
repo_name="$2"
pr_number="$3"
repo_base="${repo_name##*/}"
session_name="$repo_base"
workspace_label="pr-${pr_number}"

for cmd in wezterm herdr jq cursor-agent; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "missing required command: $cmd" >&2
    exit 1
  fi
done

create_workspace_json="$(
  herdr --session "$session_name" workspace create \
    --label "$workspace_label" \
    --cwd "$repo_path" \
    --no-focus
)"

workspace_id="$(
  printf '%s\n' "$create_workspace_json" | jq -er '.result.workspace.workspace_id'
)"

pane_id="$(
  printf '%s\n' "$create_workspace_json" | jq -er '.result.root_pane.pane_id'
)"

cursor_agent_prompt="Review pull request number ${pr_number} in repository ${repo_name}. Use the ai-code-review skill and provide only actionable findings."

herdr --session "$session_name" pane run "$pane_id" \
  cursor-agent --yolo --workspace "$repo_path" "$cursor_agent_prompt"

# Make the created workspace visible when the new tab opens.
herdr --session "$session_name" workspace focus "$workspace_id" >/dev/null

# Open a tab that attaches to the same Herdr session so the running agent is visible.
wezterm cli spawn --cwd "$repo_path" -- herdr session attach "$session_name" >/dev/null
