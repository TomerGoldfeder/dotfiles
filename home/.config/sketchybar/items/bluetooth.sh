#!/bin/bash

bluetooth=(
  icon.padding_left=8
  label.drawing=off
  update_freq=15
  script="$PLUGIN_DIR/bluetooth.sh"
)

sketchybar \
  --add item bluetooth right \
  --set bluetooth "${bluetooth[@]}" \
  --subscribe bluetooth mouse.clicked
