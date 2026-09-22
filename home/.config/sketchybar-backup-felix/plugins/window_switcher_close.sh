#!/bin/bash

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
PLUGIN_DIR="$CONFIG_DIR/plugins"

source "$PLUGIN_DIR/window_switcher_common.sh"
winpicker_close
