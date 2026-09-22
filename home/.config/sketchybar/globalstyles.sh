#!/bin/bash

source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/colors.sh"

PADDINGS=6
FONT="JetBrainsMono Nerd Font"
ICON_FONT="$FONT"
CLUSTER_GAP=20

bar=(
  color="$BAR_SURFACE"
  position=top
  topmost=off
  sticky=on
  height=32
  padding_left=8
  padding_right=8
  corner_radius=12
  blur_radius=24
  margin=8
  y_offset=6
  display=all
)

item_defaults=(
  background.drawing=off
  background.corner_radius=6
  background.height=20
  background.padding_left=$((PADDINGS / 2))
  background.padding_right=$((PADDINGS / 2))
  icon.color="$ICON_COLOR"
  icon.font="$ICON_FONT:Regular:13.0"
  icon.highlight_color="$HIGHLIGHT"
  label.color="$LABEL_COLOR"
  label.font="$FONT:Regular:11"
  scroll_texts=on
  updates=when_shown
)

menu_defaults=(
  popup.blur_radius=24
  popup.background.color="$POPUP_BACKGROUND_COLOR"
  popup.background.corner_radius=8
)

menu_item_defaults=(
  label.font="$FONT:Regular:12"
  icon.font="$ICON_FONT:Regular:13.0"
  padding_left="$PADDINGS"
  padding_right="$PADDINGS"
  icon.padding_right=4
  icon.color="$HIGHLIGHT"
  background.color="$TRANSPARENT"
)
