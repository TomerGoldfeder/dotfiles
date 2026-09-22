#!/bin/bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/globalstyles.sh"

STATE_FILE="/tmp/sketchybar-battery-label"
PERCENTAGE="$(pmset -g batt | grep -Eo '[0-9]+%' | head -1 | tr -d '%')"
CHARGING="$(pmset -g batt | grep 'AC Power')"
LABEL_DRAWING="$(cat "$STATE_FILE" 2>/dev/null || echo off)"
COLOR="$ICON_COLOR"

case "$PERCENTAGE" in
9[0-9] | 100) ICON="$ICON_BATTERY_100" ;;
[6-8][0-9]) ICON="$ICON_BATTERY_75" ;;
[3-5][0-9]) ICON="$ICON_BATTERY_50" ;;
[1-2][0-9])
  ICON="$ICON_BATTERY_25"
  COLOR="$(getcolor yellow)"
  ;;
*)
  ICON="$ICON_BATTERY_0"
  COLOR="$(getcolor red)"
  ;;
esac

if [[ -n "$CHARGING" ]]; then
  ICON="$ICON_BATTERY_CHARGING"
  COLOR="$(getcolor green)"
fi

sketchybar --set "$NAME" \
  icon="$ICON" icon.font="$ICON_FONT:Regular:14.0" icon.color="$COLOR" \
  label="${PERCENTAGE}%" label.color="$COLOR" label.drawing="$LABEL_DRAWING"

if [ "$SENDER" = "mouse.clicked" ]; then
  if [ "$LABEL_DRAWING" = "on" ]; then
    echo off >"$STATE_FILE"
    sketchybar --set "$NAME" label.drawing=off
  else
    echo on >"$STATE_FILE"
    sketchybar --set "$NAME" label.drawing=on
  fi
fi
