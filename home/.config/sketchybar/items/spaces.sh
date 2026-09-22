#!/bin/bash

SPACE_PLUGIN="${PLUGIN_SHARED_DIR:-$HOME/.config/sketchybar/plugins}"
FONT_FACE="${FONT_FACE:-JetBrainsMono Nerd Font}"

for sid in $(aerospace list-workspaces --all 2>/dev/null); do
  case "$sid" in
    ''|*[!0-9A-Za-z]*) continue ;;
  esac

  sketchybar --add item "space.$sid" left \
    --subscribe "space.$sid" aerospace_workspace_change front_app_switched \
    --set "space.$sid" \
      icon="$sid" \
      icon.font="$FONT_FACE:Bold:12.0" \
      icon.padding_left=8 \
      icon.padding_right=8 \
      label.font="sketchybar-app-font:Regular:16.0" \
      label.y_offset=-1 \
      label.padding_right=8 \
      label.drawing=on \
      update_freq=5 \
      click_script="aerospace workspace $sid" \
      script="$SPACE_PLUGIN/aerospacer.sh $sid"
done
