#!/bin/bash

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
export CONFIG_DIR
PLUGIN_DIR="$CONFIG_DIR/plugins"

source "$PLUGIN_DIR/window_switcher_common.sh"

action="${1:-}"
count="$(winpicker_count_selectable)"

if [ "$count" -eq 0 ]; then
  winpicker_close
  exit 0
fi

case "$action" in
  next)
    sel="$(winpicker_get_sel)"
    sel=$(( (sel + 1) % count ))
    winpicker_set_sel "$sel"
    winpicker_apply_highlight "$sel"
    ;;
  prev)
    sel="$(winpicker_get_sel)"
    sel=$(( (sel - 1 + count) % count ))
    winpicker_set_sel "$sel"
    winpicker_apply_highlight "$sel"
    ;;
  pick)
    sel="${2:-$(winpicker_get_sel)}"
    winpicker_set_sel "$sel"
    winpicker_apply_highlight "$sel"
    wid="$(sed -n "$((sel + 1))p" "$STATE_DIR/ids.txt")"
    if [ -n "$wid" ]; then
      aerospace focus --window-id "$wid" 2>/dev/null
    fi
    winpicker_close
    ;;
  focus)
    sel="$(winpicker_get_sel)"
    wid="$(sed -n "$((sel + 1))p" "$STATE_DIR/ids.txt")"
    if [ -n "$wid" ]; then
      aerospace focus --window-id "$wid" 2>/dev/null
    fi
    winpicker_close
    ;;
  close)
    winpicker_close
    ;;
esac
