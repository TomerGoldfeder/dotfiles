#!/bin/bash

volume_slider=(
  updates=on
  icon.drawing=off
  label.drawing=off
  padding_left=8
  slider.background.color="$(getcolor white 25)"
  slider.background.corner_radius=8
  slider.background.height=6
  slider.highlight_color="$HIGHLIGHT"
  script="$PLUGIN_DIR/volume.sh"
)

volume_icon=(
  click_script="$PLUGIN_DIR/volume_click.sh"
  icon="$ICON_VOLUME_100"
  icon.font="$ICON_FONT:Regular:13.0"
  icon.padding_left="$CLUSTER_GAP"
  label.drawing=off
)

sketchybar \
  --add slider volume right \
  --set volume "${volume_slider[@]}" \
  --subscribe volume volume_change mouse.clicked \
  --add item volume_icon right \
  --set volume_icon "${volume_icon[@]}"
