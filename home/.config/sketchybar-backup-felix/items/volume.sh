#!/bin/bash

volume_slider=(
  updates=on
  icon.drawing=off
  label.drawing=off
  padding_left=8
  slider.background.color="$BACKGROUND_2"
  slider.background.corner_radius=3
  slider.background.height=5
  slider.highlight_color="$BLUE"
  script="$PLUGIN_DIR/volume.sh"
)

volume_icon=(
  click_script="$PLUGIN_DIR/volume_click.sh"
  icon="$ICON_VOLUME_100"
  icon.font="$ICON_FONT:Regular:14.0"
  icon.padding_left="$CLUSTER_GAP"
  label.drawing=off
)

status_bracket=(
  background.color="$BACKGROUND_1"
  background.border_color="$BACKGROUND_2"
  background.border_width=2
)

sketchybar \
  --add slider volume right \
  --set volume "${volume_slider[@]}" \
  --subscribe volume volume_change mouse.clicked \
  --add item volume_icon right \
  --set volume_icon "${volume_icon[@]}"

sketchybar --add bracket status wifi bluetooth battery volume_icon \
  --set status "${status_bracket[@]}"
