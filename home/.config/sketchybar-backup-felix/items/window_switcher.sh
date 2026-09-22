#!/bin/bash

winpicker=(
  icon.drawing=off
  label.drawing=off
  width=0
  padding_left=0
  padding_right=0
  popup.align=left
  popup.height=26
  popup.y_offset=8
  "${menu_defaults[@]}"
)

sketchybar --add item winpicker left --set winpicker "${winpicker[@]}"
