#!/bin/bash

front_app=(
  script="$PLUGIN_DIR/front_app.sh"
  icon.font="sketchybar-app-font:Regular:16.0"
  label.font="$FONT:Black:12.0"
  icon.padding_left="$PADDINGS"
  icon.padding_right=8
  label.padding_right="$PADDINGS"
  padding_left="$PADDINGS"
  padding_right="$PADDINGS"
)

sketchybar --add item front_app left \
  --set front_app "${front_app[@]}" \
  --subscribe front_app front_app_switched
