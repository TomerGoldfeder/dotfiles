#!/bin/bash

POPUP_OFF="sketchybar --set wifi popup.drawing=off"

wifi=(
  "${menu_defaults[@]}"
  icon.padding_left=8
  label.drawing=off
  popup.align=right
  update_freq=10
  script="$PLUGIN_DIR/wifi.sh"
)

sketchybar \
  --add item wifi right \
  --set wifi "${wifi[@]}" \
  --subscribe wifi wifi_change mouse.clicked \
  --add item wifi.ssid popup.wifi \
  --set wifi.ssid icon=󰖩 label="SSID" "${menu_item_defaults[@]}" \
    click_script="open 'x-apple.systempreferences:com.apple.preference.network?Wi-Fi'; $POPUP_OFF" \
  --add item wifi.ip popup.wifi \
  --set wifi.ip icon=󰩠 label="IP" "${menu_item_defaults[@]}"
