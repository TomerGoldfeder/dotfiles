#!/bin/bash

date=(
  icon.drawing=off
  label.font="$FONT:Semibold:13.0"
  label.padding_left=8
  label.padding_right=8
  update_freq=30
  script='sketchybar --set $NAME label="$(date "+%a, %b %d  %H:%M")"'
  click_script="open -a Calendar"
)

sketchybar \
  --add item date right \
  --set date "${date[@]}" \
  --subscribe date system_woke
