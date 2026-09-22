#!/bin/bash

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
export CONFIG_DIR
source "$CONFIG_DIR/globalstyles.sh"
source "$CONFIG_DIR/icons.sh"

BT_PLUGIN="$CONFIG_DIR/plugins/bluetooth.sh"

bluetooth=(
  icon="$ICON_BT_ON"
  icon.font="$ICON_FONT:Regular:15.0"
  icon.color="$WHITE"
  icon.padding_left=8
  icon.padding_right=8
  label.drawing=off
  update_freq=15
  script="$BT_PLUGIN"
)

sketchybar \
  --add item bluetooth right \
  --set bluetooth "${bluetooth[@]}" \
  --subscribe bluetooth mouse.clicked
