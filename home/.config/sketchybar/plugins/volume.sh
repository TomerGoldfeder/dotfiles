#!/bin/bash

source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/globalstyles.sh"

WIDTH=100

volume_change() {
  case $INFO in
    [7-9][0-9] | 100) ICON="$ICON_VOLUME_100" ;;
    [4-6][0-9]) ICON="$ICON_VOLUME_66" ;;
    [2-3][0-9]) ICON="$ICON_VOLUME_33" ;;
    [0-1][0-9]) ICON="$ICON_VOLUME_10" ;;
    [0-9]) ICON="$ICON_VOLUME_0" ;;
    *) ICON="$ICON_VOLUME_100" ;;
  esac

  sketchybar --set volume_icon icon="$ICON" icon.font="$ICON_FONT:Regular:13.0" \
    --set "$NAME" slider.percentage="$INFO" \
    --animate tanh 20 --set "$NAME" slider.width="$WIDTH"
  sleep 2
  sketchybar --animate tanh 20 --set "$NAME" slider.width=0
}

case "$SENDER" in
  volume_change) volume_change ;;
  mouse.clicked) osascript -e "set volume output volume $PERCENTAGE" ;;
esac
