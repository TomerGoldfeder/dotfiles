#!/bin/bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/globalstyles.sh"

POPUP_OFF="sketchybar --set wifi popup.drawing=off"

WIFI_DEV="$(networksetup -listallhardwareports | awk '/Wi-Fi|AirPort/{getline; print $2; exit}')"
WIFI_DEV="${WIFI_DEV:-en0}"

POWER="$(networksetup -getairportpower "$WIFI_DEV" 2>/dev/null | awk '{print tolower($NF)}')"
SSID="$(networksetup -getairportnetwork "$WIFI_DEV" 2>/dev/null | sed 's/^Current Wi-Fi Network: //')"
IP_ADDRESS="$(ipconfig getifaddr "$WIFI_DEV" 2>/dev/null || true)"

if [[ "$SSID" == *"not associated"* ]] || [[ "$SSID" == *"You are not associated"* ]]; then
  SSID=""
fi

if [[ -z "$SSID" ]]; then
  SUMMARY="$(ipconfig getsummary "$WIFI_DEV" 2>/dev/null)"
  SSID="$(echo "$SUMMARY" | grep -o 'SSID : .*' | sed 's/^SSID : //' | tail -n 1)"
fi

if [[ "$POWER" != "on" ]]; then
  ICON="$ICON_WIFI_OFF"
  COLOR="$ICON_COLOR_INACTIVE"
  HEADER="Wi-Fi Off"
  SSID="Not connected"
  IP_ADDRESS="—"
  TOGGLE_LABEL="Turn Wi-Fi On"
  TOGGLE_STATE="on"
elif [[ -n "$SSID" ]]; then
  ICON="$ICON_WIFI_ON"
  COLOR="$GREEN"
  HEADER="Connected"
  TOGGLE_LABEL="Turn Wi-Fi Off"
  TOGGLE_STATE="off"
else
  ICON="$ICON_WIFI_DISCONNECTED"
  COLOR="$YELLOW"
  HEADER="Not connected"
  SSID="No network"
  IP_ADDRESS="—"
  TOGGLE_LABEL="Turn Wi-Fi Off"
  TOGGLE_STATE="off"
fi

if [[ -z "$IP_ADDRESS" ]]; then
  IP_ADDRESS="—"
fi

COPY_IP="printf '%s' '$IP_ADDRESS' | pbcopy"
TOGGLE_CMD="networksetup -setairportpower '$WIFI_DEV' $TOGGLE_STATE; sketchybar --trigger wifi_change; $POPUP_OFF"

sketchybar --set "$NAME" \
  icon="$ICON" \
  icon.font="$ICON_FONT:Regular:15.0" \
  icon.color="$COLOR" \
  --set wifi.header icon="$ICON" icon.color="$COLOR" label="$HEADER" \
  --set wifi.ssid icon="$ICON_WIFI_ON" label="$SSID" \
  --set wifi.ip icon="$ICON_COPY" label="$IP_ADDRESS" click_script="$COPY_IP" \
  --set wifi.toggle icon="$ICON_POWER" label="$TOGGLE_LABEL" click_script="$TOGGLE_CMD"

if [ "$SENDER" = "mouse.clicked" ]; then
  sketchybar --set "$NAME" popup.drawing=toggle
fi
