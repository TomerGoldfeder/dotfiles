#!/bin/bash

source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/colors.sh"

PADDINGS=3
FONT="JetBrainsMono Nerd Font"
ICON_FONT="$FONT"
CLUSTER_GAP=8

bar=(
  color="$BAR_COLOR"
  position=top
  topmost=off
  sticky=on
  height=39
  padding_left=10
  padding_right=10
  corner_radius=9
  blur_radius=20
  margin=10
  y_offset=10
  shadow=on
  display=all
)

item_defaults=(
  background.drawing=off
  background.corner_radius=9
  background.height=30
  background.padding_left="$PADDINGS"
  background.padding_right="$PADDINGS"
  icon.color="$ICON_COLOR"
  icon.font="$ICON_FONT:Regular:14.0"
  icon.highlight_color="$HIGHLIGHT"
  label.color="$LABEL_COLOR"
  label.font="$FONT:Semibold:13.0"
  scroll_texts=on
  updates=when_shown
)

menu_defaults=(
  popup.blur_radius=20
  popup.background.color="$POPUP_BACKGROUND_COLOR"
  popup.background.corner_radius=9
  popup.background.border_width=2
  popup.background.border_color="$POPUP_BORDER_COLOR"
)

menu_item_defaults=(
  label.font="$FONT:Regular:13.0"
  icon.font="$ICON_FONT:Regular:14.0"
  padding_left="$PADDINGS"
  padding_right="$PADDINGS"
  icon.padding_right=8
  icon.color="$HIGHLIGHT"
  background.color="$TRANSPARENT"
)
