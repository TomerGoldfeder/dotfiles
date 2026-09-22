#!/bin/bash

source "$CONFIG_DIR/colors.sh"

if [ "$1" = "$FOCUSED_WORKSPACE" ]; then
  sketchybar --set "$NAME" icon.color="$HIGHLIGHT"
else
  sketchybar --set "$NAME" icon.color="$ICON_COLOR_INACTIVE"
fi
