#!/bin/bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/globalstyles.sh"

POWER="$(defaults read /Library/Preferences/com.apple.Bluetooth ControllerPowerState 2>/dev/null || echo 0)"

if [ "$POWER" = "1" ]; then
  CONNECTED="$(system_profiler SPBluetoothDataType 2>/dev/null | grep -c 'Connected: Yes' || true)"
  if [ "${CONNECTED:-0}" -gt 0 ]; then
    ICON="$ICON_BT_ON"
    COLOR="$ICON_COLOR"
  else
    ICON="$ICON_BT_ON"
    COLOR="$ICON_COLOR_INACTIVE"
  fi
else
  ICON="$ICON_BT_OFF"
  COLOR="$ICON_COLOR_INACTIVE"
fi

sketchybar --set "$NAME" icon="$ICON" icon.font="$ICON_FONT:Regular:13.0" icon.color="$COLOR"

if [ "$SENDER" = "mouse.clicked" ]; then
  open "x-apple.systempreferences:com.apple.BluetoothSettings"
fi
