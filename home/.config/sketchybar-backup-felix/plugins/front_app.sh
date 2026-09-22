#!/bin/bash

source "$CONFIG_DIR/plugins/icon_map.sh"

__icon_map "$INFO"
sketchybar --set "$NAME" icon="$icon_result" label="$INFO"
