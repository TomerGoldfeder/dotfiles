#!/bin/bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/globalstyles.sh"

BT_INFO="$(system_profiler SPBluetoothDataType 2>/dev/null)"
STATE="$(echo "$BT_INFO" | awk '/Bluetooth Controller:/{p=1} p && /State:/{print $2; exit}')"
CONNECTED="$(echo "$BT_INFO" | sed -n '/^      Connected:/,/^      Not Connected:/p' | grep -c 'Address:' || true)"

if [ "$STATE" = "On" ]; then
  if [ "${CONNECTED:-0}" -gt 0 ]; then
    ICON="$ICON_BT_CONNECTED"
    COLOR="$GREEN"
  else
    ICON="$ICON_BT_ON"
    COLOR="$ICON_COLOR"
  fi
else
  ICON="$ICON_BT_OFF"
  COLOR="$ICON_COLOR_INACTIVE"
fi

sketchybar --set "$NAME" icon="$ICON" icon.font="$ICON_FONT:Regular:15.0" icon.color="$COLOR"

if [ "$SENDER" = "mouse.clicked" ]; then
  open "x-apple.systempreferences:com.apple.BluetoothSettings"
fi
