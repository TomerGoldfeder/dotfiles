#!/bin/bash

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
export CONFIG_DIR
PLUGIN_DIR="$CONFIG_DIR/plugins"
STATE_DIR="/tmp/sketchybar-winpicker"

source "$CONFIG_DIR/globalstyles.sh"
source "$PLUGIN_DIR/window_switcher_common.sh"

winpicker_clear_items

rows_file="$STATE_DIR/rows.tsv"
: > "$rows_file"

aerospace list-windows --all \
  --format $'%{window-id}\t%{workspace}\t%{app-name}\t%{window-title}' 2>/dev/null \
  | LC_ALL=C sort -t $'\t' -k2,2n -k3,3 > "$rows_file"

if [ ! -s "$rows_file" ]; then
  sketchybar --add item winpicker.empty popup.winpicker \
    --set winpicker.empty \
      label="No windows" \
      icon.drawing=off \
      "${menu_item_defaults[@]}"
  winpicker_track_item winpicker.empty
  winpicker_set_sel 0
  sketchybar --set winpicker popup.drawing=on
  exit 0
fi

last_workspace=""
selectable_idx=0

while IFS=$'\t' read -r wid workspace app title; do
  [ -z "$wid" ] && continue

  if [ "$workspace" != "$last_workspace" ]; then
    header_name="winpicker.hdr.${workspace}"
    sketchybar --add item "$header_name" popup.winpicker \
      --set "$header_name" \
        icon.drawing=off \
        label="Workspace ${workspace}" \
        label.font="$FONT:Bold:11" \
        label.color="$(getcolor white 50)" \
        background.drawing=off \
        padding_left="$PADDINGS" \
        padding_right="$PADDINGS"
    winpicker_track_item "$header_name"
    last_workspace="$workspace"
  fi

  item_name="winpicker.item.${selectable_idx}"
  if [ "${#title}" -gt 72 ]; then
    title="${title:0:69}..."
  fi

  sketchybar --add item "$item_name" popup.winpicker \
    --set "$item_name" \
      icon.drawing=off \
      label="  ${app} — ${title}" \
      "${menu_item_defaults[@]}" \
      scroll_texts=on \
      click_script="bash '$PLUGIN_DIR/window_switcher_nav.sh' pick '$selectable_idx'"

  winpicker_track_item "$item_name"
  winpicker_track_selectable "$item_name" "$wid"
  selectable_idx=$((selectable_idx + 1))
done < "$rows_file"

winpicker_set_sel 0
winpicker_apply_highlight 0
sketchybar --set winpicker popup.drawing=on
