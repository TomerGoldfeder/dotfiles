#!/usr/bin/env zsh

# Upstream used yabai's space_change JSON. This machine uses AeroSpace;
# aerospace.toml fires aerospace_workspace_change with FOCUSED_WORKSPACE.

update_space() {
    SPACE_ID="${FOCUSED_WORKSPACE:-}"
    if [[ -z "$SPACE_ID" ]]; then
        SPACE_ID=$(aerospace list-workspaces --focused 2>/dev/null)
    fi

    case $SPACE_ID in
    1)
        ICON=󰅶
        ICON_PADDING_LEFT=7
        ICON_PADDING_RIGHT=7
        ;;
    *)
        ICON=$SPACE_ID
        ICON_PADDING_LEFT=9
        ICON_PADDING_RIGHT=10
        ;;
    esac

    sketchybar --set $NAME \
        icon=$ICON \
        icon.padding_left=$ICON_PADDING_LEFT \
        icon.padding_right=$ICON_PADDING_RIGHT
}

case "$SENDER" in
"mouse.clicked")
    # Reload sketchybar
    sketchybar --remove '/.*/'
    source $HOME/.config/sketchybar/sketchybarrc
    ;;
*)
    update_space
    ;;
esac
