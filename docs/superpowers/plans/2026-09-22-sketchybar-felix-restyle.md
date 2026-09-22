# SketchyBar Felix Restyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle SketchyBar to FelixKratz floating Catppuccin Macchiato look while keeping AeroSpace workspaces, window switcher, wifi, bluetooth, volume slider, and battery click-for-percent.

**Architecture:** Tokens first (`colors.sh` + `globalstyles.sh` + AeroSpace `outer.top`), then left spaces bracket, then right status bracket. No yabai. No new items (no front_app, Spotify, CPU, brew, GitHub).

**Tech Stack:** SketchyBar shell config, AeroSpace, JetBrainsMono Nerd Font, home-manager out-of-store symlink at `home/.config/sketchybar/`.

## Global Constraints

- Visual source: FelixKratz/dotfiles `.config/sketchybar` @ `e6288b3`. Not neutonfoo.
- Font: `JetBrainsMono Nerd Font`. No SF Pro / sf-symbols cask.
- Keep `getcolor <name> [opacity]` API.
- `HIGHLIGHT=$RED` for spaces + window switcher. Volume slider uses `$BLUE` explicitly.
- Keep `aerospace_workspace_change`, `aerospacer.sh`, window_switcher AeroSpace binds.
- Do not port yabai. `grep -R yabai home/.config/sketchybar` must stay empty.
- Do not commit unless the user asks. Do not touch unrelated `home.nix` / herdr diffs.
- Spec: `docs/superpowers/specs/2026-09-22-sketchybar-felix-restyle-design.md`

---

### Task 1: Tokens (palette, bar geometry, gaps)

**Files:**
- Modify: `home/.config/sketchybar/colors.sh` (replace entire file)
- Modify: `home/.config/sketchybar/globalstyles.sh` (replace entire file)
- Modify: `home/.config/aerospace/aerospace.toml` (`outer.top` + comment only)
- Test: `bash -n` those two `.sh` files

**Interfaces:**
- Consumes: nothing from later tasks
- Produces: `getcolor`, `BAR_COLOR`, `BACKGROUND_1`, `BACKGROUND_2`, `HIGHLIGHT` (red), `HIGHLIGHT_25`, `ICON_COLOR`, `ICON_COLOR_INACTIVE`, `LABEL_COLOR`, `POPUP_BACKGROUND_COLOR`, `POPUP_BORDER_COLOR`, `TRANSPARENT`, `BLUE`, `RED`, `PADDINGS=3`, `FONT="JetBrainsMono Nerd Font"`, bar geometry Felix floating

- [ ] **Step 1: Write `home/.config/sketchybar/colors.sh`**

```bash
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
```

- [ ] **Step 2: Write `home/.config/sketchybar/globalstyles.sh`**

```bash
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
```

- [ ] **Step 3: In `home/.config/aerospace/aerospace.toml`, set `outer.top = 60` and comment `# Reserve space for SketchyBar (height 39 + y_offset 10 + margin 10).`**

- [ ] **Step 4: Verify**

```bash
bash -n home/.config/sketchybar/colors.sh
bash -n home/.config/sketchybar/globalstyles.sh
```

Expected: no output, exit 0. Do not commit.

---

### Task 2: Left cluster (AeroSpace spaces bracket)

**Files:**
- Modify: `home/.config/sketchybar/items/spaces.sh`
- Modify: `home/.config/sketchybar/plugins/aerospacer.sh`
- Test: `bash -n` both

**Interfaces:**
- Consumes: `HIGHLIGHT`, `BACKGROUND_1`, `BACKGROUND_2`, `CLUSTER_GAP`, `FONT`, `PLUGIN_DIR` from Task 1
- Produces: `space.$sid` items still subscribe to `aerospace_workspace_change`; bracket `spaces` wrapping `/space\..*/`

- [ ] **Step 1: Write `home/.config/sketchybar/items/spaces.sh`**

Keep the AeroSpace loop. Add Felix `icon.highlight_color`. After the loop, add the spaces bracket. Do not add a yabai create-space separator.

```bash
#!/bin/bash

FIRST=1
for sid in $(aerospace list-workspaces --all 2>/dev/null); do
  case "$sid" in
    ''|*[!0-9A-Za-z]*) continue ;;
  esac

  pad_left=8
  if [ "$FIRST" = 1 ]; then
    pad_left="$CLUSTER_GAP"
    FIRST=0
  fi

  sketchybar --add item "space.$sid" left \
    --subscribe "space.$sid" aerospace_workspace_change \
    --set "space.$sid" \
      icon="$sid" \
      icon.font="$FONT:Bold:12.0" \
      icon.highlight_color="$HIGHLIGHT" \
      icon.padding_left="$pad_left" \
      icon.padding_right=8 \
      click_script="aerospace workspace $sid" \
      script="$PLUGIN_DIR/aerospacer.sh $sid"
done

spaces_bracket=(
  background.color="$BACKGROUND_1"
  background.border_color="$BACKGROUND_2"
  background.border_width=2
  background.drawing=on
)

sketchybar --add bracket spaces '/space\..*/' \
  --set spaces "${spaces_bracket[@]}"
```

- [ ] **Step 2: Write `home/.config/sketchybar/plugins/aerospacer.sh`**

```bash
#!/bin/bash

source "$CONFIG_DIR/colors.sh"

if [ "$1" = "$FOCUSED_WORKSPACE" ]; then
  sketchybar --set "$NAME" icon.highlight=on icon.color="$HIGHLIGHT"
else
  sketchybar --set "$NAME" icon.highlight=off icon.color="$ICON_COLOR_INACTIVE"
fi
```

- [ ] **Step 3: Verify**

```bash
bash -n home/.config/sketchybar/items/spaces.sh
bash -n home/.config/sketchybar/plugins/aerospacer.sh
grep -R yabai home/.config/sketchybar || true
```

Expected: `bash -n` silent; no `yabai` matches. Apple item and window_switcher files unchanged. Do not commit.

---

### Task 3: Right cluster (status bracket, slider blue)

**Files:**
- Modify: `home/.config/sketchybar/items/volume.sh` (slider colors + status bracket)
- Modify: `home/.config/sketchybar/items/date.sh` (font to Semibold 13, padding from tokens)
- Test: `bash -n` both

**Interfaces:**
- Consumes: `BLUE`, `BACKGROUND_1`, `BACKGROUND_2`, `CLUSTER_GAP`, `FONT` from Task 1. Wifi/bluetooth/battery items already exist when `volume.sh` is sourced last among right items.
- Produces: status bracket over `wifi` `bluetooth` `battery` `volume_icon`; volume slider highlight `$BLUE`

- [ ] **Step 1: Write `home/.config/sketchybar/items/volume.sh`**

```bash
#!/bin/bash

volume_slider=(
  updates=on
  icon.drawing=off
  label.drawing=off
  padding_left=8
  slider.background.color="$BACKGROUND_2"
  slider.background.corner_radius=3
  slider.background.height=5
  slider.highlight_color="$BLUE"
  script="$PLUGIN_DIR/volume.sh"
)

volume_icon=(
  click_script="$PLUGIN_DIR/volume_click.sh"
  icon="$ICON_VOLUME_100"
  icon.font="$ICON_FONT:Regular:14.0"
  icon.padding_left="$CLUSTER_GAP"
  label.drawing=off
)

status_bracket=(
  background.color="$BACKGROUND_1"
  background.border_color="$BACKGROUND_2"
  background.border_width=2
)

sketchybar \
  --add slider volume right \
  --set volume "${volume_slider[@]}" \
  --subscribe volume volume_change mouse.clicked \
  --add item volume_icon right \
  --set volume_icon "${volume_icon[@]}"

sketchybar --add bracket status wifi bluetooth battery volume_icon \
  --set status "${status_bracket[@]}"
```

- [ ] **Step 2: Write `home/.config/sketchybar/items/date.sh`**

```bash
#!/bin/bash

date=(
  icon.drawing=off
  label.font="$FONT:Semibold:13.0"
  label.padding_left=8
  label.padding_right=8
  update_freq=30
  script='sketchybar --set $NAME label="$(date "+%a, %b %d  %H:%M")"'
  click_script="open -a Calendar"
)

sketchybar \
  --add item date right \
  --set date "${date[@]}" \
  --subscribe date system_woke
```

Leave `items/wifi.sh`, `items/battery.sh`, `items/bluetooth.sh`, and battery/wifi/bluetooth plugins as-is except they pick up Macchiato via `getcolor` / `ICON_COLOR` from Task 1.

- [ ] **Step 3: Verify**

```bash
bash -n home/.config/sketchybar/items/volume.sh
bash -n home/.config/sketchybar/items/date.sh
bash -n home/.config/sketchybar/sketchybarrc
```

Expected: exit 0. Do not commit.

---

### Task 4: QA

**Files:** none (verify only)

- [ ] **Step 1:** `bash -n` every `home/.config/sketchybar/**/*.sh` and `sketchybarrc`
- [ ] **Step 2:** `grep -R yabai home/.config/sketchybar` empty
- [ ] **Step 3:** Confirm `aerospace.toml` still has `aerospace_workspace_change` and window_switcher plugin paths; `outer.top = 60`
- [ ] **Step 4:** If `sketchybar` is on PATH, `sketchybar --reload` then `--trigger aerospace_workspace_change` with focused workspace
