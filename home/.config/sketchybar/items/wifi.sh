#!/bin/bash

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
export CONFIG_DIR
source "$CONFIG_DIR/globalstyles.sh"
source "$CONFIG_DIR/icons.sh"

POPUP_OFF="sketchybar --set wifi popup.drawing=off"
WIFI_PLUGIN="$CONFIG_DIR/plugins/wifi.sh"

wifi=(
  "${menu_defaults[@]}"
  icon="$ICON_WIFI_ON"
  icon.font="$ICON_FONT:Regular:15.0"
  icon.color="$WHITE"
  icon.padding_left=8
  icon.padding_right=8
  label.drawing=off
  popup.align=right
  popup.height=32
  update_freq=10
  script="$WIFI_PLUGIN"
)

row() {
  local name="$1"
  sketchybar --add item "$name" popup.wifi --set "$name" "${menu_item_defaults[@]}"
}

sketchybar \
  --add item wifi right \
  --set wifi "${wifi[@]}" \
  --subscribe wifi wifi_change mouse.clicked

row wifi.header
sketchybar --set wifi.header \
  icon="$ICON_WIFI_ON" \
  label="Wi-Fi" \
  label.font="$FONT:Bold:13.0" \
  click_script=""

row wifi.ssid
sketchybar --set wifi.ssid \
  icon="$ICON_WIFI_ON" \
  label="Network"

row wifi.ip
sketchybar --set wifi.ip \
  icon="$ICON_WIFI_IP" \
  label="IP"

sketchybar --add item wifi.sep popup.wifi --set wifi.sep "${popup_separator[@]}"

row wifi.toggle
sketchybar --set wifi.toggle \
  icon="$ICON_POWER" \
  label="Turn Wi-Fi Off"

row wifi.settings
sketchybar --set wifi.settings \
  icon="$ICON_WIFI_SETTINGS" \
  label="Wi-Fi Settings" \
  click_script="open 'x-apple.systempreferences:com.apple.wifi-settings-extension'; $POPUP_OFF"
