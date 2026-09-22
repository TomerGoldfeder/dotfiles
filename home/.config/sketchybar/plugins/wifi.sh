#!/bin/bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/globalstyles.sh"

SUMMARY="$(ipconfig getsummary en0 2>/dev/null)"
SSID="$(echo "$SUMMARY" | grep -o 'SSID : .*' | sed 's/^SSID : //' | tail -n 1)"
IP_ADDRESS="$(echo "$SUMMARY" | grep -o 'ciaddr = .*' | sed 's/^ciaddr = //')"

if [[ -n "$SSID" ]]; then
  ICON="$ICON_WIFI_ON"
  COLOR="$ICON_COLOR"
else
  ICON="$ICON_WIFI_OFF"
  COLOR="$ICON_COLOR_INACTIVE"
  SSID="Not connected"
  IP_ADDRESS="—"
fi

sketchybar --set "$NAME" icon="$ICON" icon.font="$ICON_FONT:Regular:13.0" icon.color="$COLOR"

if [ "$SENDER" = "mouse.clicked" ]; then
  sketchybar --set "$NAME" popup.drawing=toggle \
    --set wifi.ssid label="$SSID" \
    --set wifi.ip label="$IP_ADDRESS"
fi
