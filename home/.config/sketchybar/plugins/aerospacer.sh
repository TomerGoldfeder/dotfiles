#!/bin/bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/plugins/icon_map.sh"

if [ -z "${FOCUSED_WORKSPACE:-}" ]; then
  FOCUSED_WORKSPACE="$(aerospace list-workspaces --focused 2>/dev/null | tr -d '[:space:]')"
fi

already_seen() {
  local name="$1"
  local s
  for s in "${seen[@]}"; do
    [ "$s" = "$name" ] && return 0
  done
  return 1
}

seen=()
glyphs=()
while IFS= read -r app; do
  [ -z "$app" ] && continue
  already_seen "$app" && continue
  seen+=("$app")
  __icon_map "$app"
  glyphs+=("$icon_result")
done < <(aerospace list-windows --workspace "$1" --format '%{app-name}' 2>/dev/null)

label=" "
if [ "${#glyphs[@]}" -gt 0 ]; then
  label="${glyphs[*]}"
fi

if [ "$1" = "$FOCUSED_WORKSPACE" ]; then
  sketchybar --set "$NAME" \
    icon.highlight=on icon.color="$HIGHLIGHT" \
    label="$label" \
    --animate tanh 20 \
    --set "$NAME" label.width=0
else
  sketchybar --set "$NAME" \
    icon.highlight=off icon.color="$ICON_COLOR_INACTIVE" \
    label="$label" \
    label.width=dynamic
fi
