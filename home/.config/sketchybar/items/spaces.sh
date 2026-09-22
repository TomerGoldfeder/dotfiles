#!/bin/bash

FIRST=1
for sid in $(aerospace list-workspaces --all 2>/dev/null); do
  case "$sid" in
    ''|*[!0-9A-Za-z]*) continue ;;
  esac

  pad_left=8
  if [ "$FIRST" = 1 ]; then
    pad_left="$CLUSTER_GAP"
    FIRST=0
  fi

  sketchybar --add item "space.$sid" left \
    --subscribe "space.$sid" aerospace_workspace_change \
    --set "space.$sid" \
      icon="$sid" \
      icon.font="$FONT:Bold:12.0" \
      icon.highlight_color="$HIGHLIGHT" \
      icon.padding_left="$pad_left" \
      icon.padding_right=8 \
      click_script="aerospace workspace $sid" \
      script="$PLUGIN_DIR/aerospacer.sh $sid"
done

spaces_bracket=(
  background.color="$BACKGROUND_1"
  background.border_color="$BACKGROUND_2"
  background.border_width=2
  background.drawing=on
)

sketchybar --add bracket spaces '/space\..*/' \
  --set spaces "${spaces_bracket[@]}"
