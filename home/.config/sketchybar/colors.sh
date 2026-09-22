#!/bin/bash

# Pe8er palette helpers (Dracula). Bar surface at 60% opacity.
DRACULA=(
  blue "#6272A4"
  teal "#69FF94"
  cyan "#8BE9FD"
  grey "#44475A"
  green "#50FA7B"
  yellow "#F1FA8C"
  orange "#FFB86C"
  red "#FF5555"
  purple "#BD93F9"
  maroon "#FF79C6"
  black "#282A36"
  trueblack "#1c1c1c"
  white "#F8F8F2"
)

COLORS=("${DRACULA[@]}")

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

BAR_SURFACE=$(getcolor black 60)
BAR_COLOR=$(getcolor black 75)
HIGHLIGHT=$(getcolor cyan)
HIGHLIGHT_25=$(getcolor cyan 25)
ICON_COLOR=$(getcolor white)
ICON_COLOR_INACTIVE=$(getcolor white 25)
LABEL_COLOR=$(getcolor white 75)
POPUP_BACKGROUND_COLOR=$(getcolor black 75)
TRANSPARENT=$(getcolor black 0)
