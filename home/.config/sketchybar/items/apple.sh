#!/bin/bash

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
export CONFIG_DIR
source "$CONFIG_DIR/globalstyles.sh"
source "$CONFIG_DIR/icons.sh"

POPUP_OFF='sketchybar --set logo popup.drawing=off'

logo=(
  "${menu_defaults[@]}"
  icon="$ICON_APPLE"
  icon.font="$ICON_FONT:Regular:16.0"
  icon.color="$WHITE"
  icon.padding_left=8
  icon.padding_right=8
  label.drawing=off
  popup.align=left
  popup.height=32
  click_script='sketchybar --set logo popup.drawing=toggle'
)

row() {
  local name="$1"
  sketchybar --add item "$name" popup.logo --set "$name" "${menu_item_defaults[@]}"
}

sep() {
  local name="$1"
  sketchybar --add item "$name" popup.logo --set "$name" "${popup_separator[@]}"
}

sketchybar \
  --add item logo left \
  --set logo "${logo[@]}"

row logo.about
sketchybar --set logo.about \
  icon="$ICON_INFO" \
  label="About This Mac" \
  click_script="open 'x-apple.systempreferences:com.apple.About-Settings.extension'; $POPUP_OFF"

row logo.settings
sketchybar --set logo.settings \
  icon="$ICON_SETTINGS" \
  label="System Settings" \
  click_script="open -a 'System Settings'; $POPUP_OFF"

sep logo.sep.power

row logo.sleep
sketchybar --set logo.sleep \
  icon="$ICON_SLEEP" \
  label="Sleep" \
  click_script="pmset sleepnow; $POPUP_OFF"

row logo.lock
sketchybar --set logo.lock \
  icon="$ICON_LOCK" \
  label="Lock Screen" \
  click_script="osascript -e 'tell application \"System Events\" to keystroke \"q\" using {command down,control down}'; $POPUP_OFF"

sep logo.sep.bar

row logo.refresh
sketchybar --set logo.refresh \
  icon="$ICON_REFRESH" \
  label="Refresh SketchyBar" \
  click_script="$POPUP_OFF; sketchybar --reload"
