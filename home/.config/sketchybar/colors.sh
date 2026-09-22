#!/bin/bash

# Catppuccin Macchiato (FelixKratz @ e6288b3). getcolor kept for plugins.
CATPPUCCIN=(
  blue "#8aadf4"
  teal "#8bd5ca"
  cyan "#8aadf4"
  grey "#939ab7"
  green "#a6da95"
  yellow "#eed49f"
  orange "#f5a97f"
  red "#ed8796"
  purple "#c6a0f6"
  maroon "#c6a0f6"
  black "#24273a"
  trueblack "#181926"
  white "#cad3f5"
)

COLORS=("${CATPPUCCIN[@]}")

PERCENT2HEX() {
  printf "0x%02X\n" "$(( $1 * 255 / 100 ))"
}

getcolor() {
  local name="$1"
  local opacity="${2:-100}"
  local hex=""

  for ((i = 0; i < ${#COLORS[@]}; i += 2)); do
    if [[ "${COLORS[i]}" == "$name" ]]; then
      hex="${COLORS[i + 1]}"
      break
    fi
  done

  if [[ -z "$hex" ]]; then
    echo "Invalid color: $name" >&2
    return 1
  fi

  echo "$(PERCENT2HEX "$opacity")${hex:1}"
}

export BLACK=0xff181926
export WHITE=0xffcad3f5
export RED=0xffed8796
export GREEN=0xffa6da95
export BLUE=0xff8aadf4
export YELLOW=0xffeed49f
export ORANGE=0xfff5a97f
export MAGENTA=0xffc6a0f6
export GREY=0xff939ab7
export TRANSPARENT=0x00000000

export BAR_COLOR=0xa024273a
export BAR_SURFACE="$BAR_COLOR"
export BACKGROUND_1=0x903c3e4f
export BACKGROUND_2=0x90494d64
export POPUP_BACKGROUND_COLOR=0xff24273a
export POPUP_BORDER_COLOR="$WHITE"

export HIGHLIGHT="$RED"
export HIGHLIGHT_25
HIGHLIGHT_25=$(getcolor red 25)
export ICON_COLOR="$WHITE"
export ICON_COLOR_INACTIVE
ICON_COLOR_INACTIVE=$(getcolor white 25)
export LABEL_COLOR
LABEL_COLOR=$(getcolor white 75)
