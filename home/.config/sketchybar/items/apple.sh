#!/bin/bash

POPUP_OFF='sketchybar --set logo popup.drawing=off'

logo=(
  "${menu_defaults[@]}"
  icon="$ICON_APPLE"
  icon.font="$ICON_FONT:Regular:14.0"
  label.drawing=off
  popup.align=left
  click_script='sketchybar --set logo popup.drawing=toggle'
)

sketchybar \
  --add item logo left \
  --set logo "${logo[@]}" \
  --add item logo.settings popup.logo \
  --set logo.settings icon=􀍟 label="System Settings" \
    "${menu_item_defaults[@]}" \
    click_script="open -a 'System Settings'; $POPUP_OFF" \
  --add item logo.sleep popup.logo \
  --set logo.sleep icon=􀜚 label="Sleep" \
    "${menu_item_defaults[@]}" \
    click_script="pmset sleepnow; $POPUP_OFF" \
  --add item logo.lock popup.logo \
  --set logo.lock icon=􀼑 label="Lock Screen" \
    "${menu_item_defaults[@]}" \
    click_script="osascript -e 'tell application \"System Events\" to keystroke \"q\" using {command down,control down}'; $POPUP_OFF" \
  --add item logo.refresh popup.logo \
  --set logo.refresh icon=􀅈 label="Refresh SketchyBar" \
    "${menu_item_defaults[@]}" \
    click_script="$POPUP_OFF; sketchybar --reload"
