#!/usr/bin/env bash
# Apply home/.config/bb/plugins.json: install missing plugins, run setup.
# Grow the JSON list; re-run bb-sync or darwin-rebuild (activation).
set -euo pipefail

MANIFEST="${BB_PLUGINS_MANIFEST:-$HOME/.config/bb/plugins.json}"
APP_BB="/Applications/bb.app/Contents/Resources/app.asar.unpacked/node_modules/bb-app/host-daemon/dist/bb"

resolve_bb() {
  if [[ -n "${BB_CLI:-}" && -x "${BB_CLI}" ]]; then
    printf '%s\n' "$BB_CLI"
    return 0
  fi
  if command -v bb >/dev/null 2>&1; then
    command -v bb
    return 0
  fi
  if [[ -x "$APP_BB" ]]; then
    printf '%s\n' "$APP_BB"
    return 0
  fi
  return 1
}

if [[ ! -f "$MANIFEST" ]]; then
  echo "bb-sync: missing $MANIFEST" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "bb-sync: jq required" >&2
  exit 1
fi

if ! BB_BIN="$(resolve_bb)"; then
  echo "bb-sync: no bb CLI. Install bb.app or run: npx --yes --allow-scripts=better-sqlite3,node-pty,@parcel/watcher bb-app@latest" >&2
  exit 0
fi

if ! "$BB_BIN" status --json >/dev/null 2>&1; then
  echo "bb-sync: bb server not reachable (start bb.app), skip plugin sync"
  exit 0
fi

LIST="$("$BB_BIN" plugin list --json)"
COUNT="$(jq '.plugins | length' "$MANIFEST")"
if [[ "$COUNT" -eq 0 ]]; then
  echo "bb-sync: empty plugin list"
  exit 0
fi

i=0
while [[ "$i" -lt "$COUNT" ]]; do
  plugin="$(jq -c --argjson i "$i" '.plugins[$i]' "$MANIFEST")"
  id="$(jq -r '.id' <<<"$plugin")"
  source="$(jq -r '.source' <<<"$plugin")"
  i=$((i + 1))

  if [[ -z "$id" || "$id" == "null" || -z "$source" || "$source" == "null" ]]; then
    echo "bb-sync: skip malformed plugin entry" >&2
    continue
  fi

  if jq -e --arg id "$id" '.plugins[] | select(.id == $id)' >/dev/null <<<"$LIST"; then
    echo "bb-sync: $id already installed"
  else
    echo "bb-sync: install $id from $source"
    "$BB_BIN" plugin install "$source" --yes
    LIST="$("$BB_BIN" plugin list --json)"
  fi

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    echo "bb-sync: $id setup: $line"
    read -r -a setup_args <<<"$line"
    "$BB_BIN" "${setup_args[@]}"
  done < <(jq -r '.setup[]?' <<<"$plugin")
done

echo "bb-sync: done"
