#!/bin/bash

WIDTH=100
CURRENT="$(sketchybar --query volume | grep '"slider.width"' | grep -Eo '[0-9]+' | head -1)"

if [ "${CURRENT:-0}" -eq 0 ]; then
  sketchybar --animate tanh 20 --set volume slider.width="$WIDTH"
else
  sketchybar --animate tanh 20 --set volume slider.width=0
fi
