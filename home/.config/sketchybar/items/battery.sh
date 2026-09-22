#!/bin/bash

battery=(
  icon.padding_left=8
  icon.font="$ICON_FONT:Regular:14.0"
  update_freq=60
  popup.align=right
  script="$PLUGIN_DIR/battery.sh"
)

sketchybar \
  --add item battery right \
  --set battery "${battery[@]}" \
  --subscribe battery power_source_change mouse.clicked
