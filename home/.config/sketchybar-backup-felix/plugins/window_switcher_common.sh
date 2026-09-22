#!/bin/bash

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
export CONFIG_DIR
PLUGIN_DIR="$CONFIG_DIR/plugins"
STATE_DIR="/tmp/sketchybar-winpicker"

source "$CONFIG_DIR/colors.sh"

mkdir -p "$STATE_DIR"

winpicker_clear_items() {
  if [ -f "$STATE_DIR/all_items.txt" ]; then
    while IFS= read -r name; do
      [ -n "$name" ] && sketchybar --remove "$name" 2>/dev/null
    done < "$STATE_DIR/all_items.txt"
  fi

  : > "$STATE_DIR/all_items.txt"
  : > "$STATE_DIR/items.txt"
  : > "$STATE_DIR/ids.txt"
  echo 0 > "$STATE_DIR/sel"
}

winpicker_track_item() {
  printf '%s\n' "$1" >> "$STATE_DIR/all_items.txt"
}

winpicker_track_selectable() {
  printf '%s\n' "$1" >> "$STATE_DIR/items.txt"
  printf '%s\n' "$2" >> "$STATE_DIR/ids.txt"
}

winpicker_count_selectable() {
  if [ ! -f "$STATE_DIR/items.txt" ]; then
    echo 0
    return
  fi
  wc -l < "$STATE_DIR/items.txt" | tr -d ' '
}

winpicker_get_sel() {
  cat "$STATE_DIR/sel" 2>/dev/null || echo 0
}

winpicker_set_sel() {
  echo "$1" > "$STATE_DIR/sel"
}

winpicker_apply_highlight() {
  local sel="$1"
  local idx=0
  local name=""

  while IFS= read -r name; do
    if [ "$idx" = "$sel" ]; then
      sketchybar --set "$name" \
        background.drawing=on \
        background.color="$HIGHLIGHT_25" \
        background.corner_radius=6 \
        background.height=22 \
        label.color="$HIGHLIGHT"
    else
      sketchybar --set "$name" \
        background.drawing=off \
        label.color="$LABEL_COLOR"
    fi
    idx=$((idx + 1))
  done < "$STATE_DIR/items.txt"
}

winpicker_close() {
  sketchybar --set winpicker popup.drawing=off 2>/dev/null
}
