# SketchyBar Felix restyle

Date: 2026-09-22  
Status: approved 2026-09-22 (user: "let's go")  
Reference: [FelixKratz/dotfiles `.config/sketchybar` @ e6288b3](https://github.com/FelixKratz/dotfiles/tree/e6288b3f4220ca1ac64a68e60fced2d4c3e3e20b/.config/sketchybar)

## Goal

Restyle the existing SketchyBar to match FelixKratz floating Catppuccin Macchiato appearance (bar geometry, palette, grouped brackets) while keeping this machine’s AeroSpace integration and current item set.

This is an appearance restyle of `home/.config/sketchybar/`, plus `outer.top` in `home/.config/aerospace/aerospace.toml`. It is not a port of yabai.

## Locked decisions

| Topic | Decision |
|-------|----------|
| Visual source | FelixKratz @ e6288b3, not neutonfoo pills |
| Font | Keep `JetBrainsMono Nerd Font` (already casked). No SF Pro / sf-symbols cask |
| Bar | Floating: height 39, y_offset 10, margin 10, corner_radius 9, blur_radius 20, shadow on, padding 10, `display=all` |
| Palette | Catppuccin Macchiato tokens from Felix `colors.sh` (`BAR_COLOR=0xa024273a`, `BACKGROUND_1/2`, named red/green/blue/…) |
| `getcolor` | Keep the helper API so existing plugins do not break; map names to Macchiato instead of Dracula |
| Left | Apple popup + AeroSpace workspace numbers in one spaces bracket; hidden window switcher stays |
| Right | Date far right; wifi + bluetooth + battery + volume icon in one status bracket; volume slider + battery click-for-percent stay |
| WM | Keep `aerospace_workspace_change`, `aerospacer.sh`, window_switcher AeroSpace binds |
| Gaps | Bump `[gaps] outer.top` from 50 to 60 (39 + 10 + 10, plus small slack vs current stale “36” comment) |

## Out of scope

- yabai: `items/spaces.sh` `associated_space`, `plugins/space.sh`, `plugins/yabai.sh`, `items/front_app.sh` yabai item, create/destroy space chevron
- neutonfoo: flush transparent bar, powerline `front_app`, weather/spotify notch, laptop/desktop rc split
- Felix extras: CPU `helper/` C binary, brew outdated, GitHub bell, Spotify center player, calendar zen mode, front_app name
- Mixing unrelated uncommitted `home.nix` / herdr changes into this work

## Architecture

Three logical units, all under the existing SketchyBar config tree (home-manager out-of-store symlink). No new services.

1. **Tokens** — palette, fonts, bar defaults, paddings. Everything else reads these.
2. **Left cluster** — Apple menu + AeroSpace spaces bracket + hidden winpicker.
3. **Right cluster** — date + status bracket (wifi, bluetooth, battery, volume).

Data flow is unchanged: AeroSpace `exec-on-workspace-change` → `aerospace_workspace_change` → `aerospacer.sh`. Plugins still call `sketchybar --set`.

### Tokens

Replace the Dracula named list in `colors.sh` with Macchiato hex values matching Felix:

- `BAR_COLOR` / bar surface: `0xa024273a`
- `BACKGROUND_1`: `0x903c3e4f`
- `BACKGROUND_2`: `0x90494d64`
- `WHITE` `0xffcad3f5`, `BLACK` `0xff181926`, `RED` `0xffed8796`, `GREEN` `0xffa6da95`, `BLUE` `0xff8aadf4`, `YELLOW` `0xffeed49f`, `ORANGE` `0xfff5a97f`, `MAGENTA` `0xffc6a0f6`, `GREY` `0xff939ab7`
- `HIGHLIGHT=$RED` for focused AeroSpace workspace and window-switcher accent (Felix space `icon.highlight_color=$RED`). Not Dracula cyan.
- Volume slider uses `$BLUE` explicitly (`slider.highlight_color=$BLUE`). Do not reuse `HIGHLIGHT` for the slider, or spaces and volume collide.
- Keep `PERCENT2HEX` + `getcolor <name> [opacity]` so `plugins/{battery,wifi,bluetooth,volume,aerospacer}.sh` and window_switcher keep working
- Map existing `getcolor` names: `black` → Macchiato base (`#24273a`), `white` → `$WHITE`, `cyan` → `$BLUE` (leftover call sites only; workspace highlight is `$RED`), `green`/`yellow`/`red`/`orange`/`purple` → matching Macchiato

`globalstyles.sh`:

- `FONT` stays `JetBrainsMono Nerd Font`
- `PADDINGS=3` (Felix; discard uncommitted `PADDINGS=20`)
- Bar array: Felix geometry listed above; `color="$BAR_COLOR"` (or equivalent `getcolor` result)
- Item defaults: icon/label colors from new tokens; `background.height=30`, `background.corner_radius=9`; default `background.drawing=off` (brackets own the fill)
- Popup defaults: Felix-like corner 9, blur 20, border `POPUP_BORDER_COLOR`

`icons.sh`: keep Nerd Font glyphs (apple, wifi, bt, volume, battery). Do not switch to SF Symbols.

`aerospace.toml`: `outer.top = 60` and update the comment to the real bar stack (height 39 + y_offset 10 + margin 10).

### Left cluster

- Apple item: keep Settings / Sleep / Lock / Reload popup. Restyle padding/colors from tokens. No behavior change.
- Spaces: keep `aerospace list-workspaces --all` loop, `click_script="aerospace workspace $sid"`, subscribe `aerospace_workspace_change`, `plugins/aerospacer.sh $sid`.
- Add one `sketchybar --add bracket` over `/space\..*/` with `background.color=$BACKGROUND_1`, `background.border_color=$BACKGROUND_2`, `background.border_width=2`.
- Focused workspace: highlight via `icon.highlight` / `HIGHLIGHT=$RED` (Felix space `icon.highlight_color=$RED`). Inactive: dimmed white/grey.
- No app-icon labels on spaces (would need yabai `windows_on_spaces` or a new AeroSpace window query; not this spec).
- Window switcher: keep width-0 `winpicker` and AeroSpace `alt-space` scripts. They pick up new `FONT` / `PADDINGS` / highlight tokens automatically.

### Right cluster

Source order unchanged (first sourced = rightmost): date, wifi, battery, bluetooth, volume.

- Date: keep `date "+%a, %b %d  %H:%M"` and Calendar click. Restyle fonts/colors. Stays **outside** the status bracket (Felix calendar is outside `status`).
- Status bracket: `wifi`, `bluetooth`, `battery`, `volume_icon` with the same `BACKGROUND_1` / `BACKGROUND_2` border as spaces.
- Volume: keep slider + click-to-expand. Slider highlight `$BLUE`, track `$BACKGROUND_2`.
- Battery: keep click-to-toggle percent (`/tmp/sketchybar-battery-label`). Recolor thresholds with Macchiato green/yellow/red/orange. Do **not** hide until <60%.
- Wifi / bluetooth: keep popups and click behavior; icons/colors from new tokens.

## Error handling

- Missing `aerospace` CLI: spaces loop already no-ops on empty `list-workspaces`; keep that.
- Invalid `getcolor` name: keep current stderr + non-zero (do not silent-fail to black).
- SketchyBar reload: `home.nix` activation already `sketchybar --reload` after link generation; hotload stays on.
- Do not add a second SketchyBar process manager. LaunchAgent + AeroSpace `exec-and-forget sketchybar` is existing, out of scope to “fix”.

## Testing / QA

No unit tests exist for this config. Verification:

1. `bash -n` on `sketchybarrc` and every sourced `items/` + `plugins/` script.
2. `grep -R yabai home/.config/sketchybar` is empty.
3. `aerospace.toml` still triggers `aerospace_workspace_change`.
4. Window-switcher plugin paths in `aerospace.toml` unchanged.
5. After reload: bar floats with Macchiato surface; spaces grouped; right status grouped; workspace click still switches; volume click still expands slider; battery click still toggles percent.
6. Three displays: `display=all` so the bar remains on laptop + both Dells.

## Risks

- `getcolor` call sites that assumed Dracula cyan highlight will look blue/red after the map; that is intended.
- `outer.top=60` vs 50: small extra gap if blur/shadow does not consume the slack; better than overlap.
- Nerd Font + Felix geometry will not be pixel-identical to SF Pro screenshots. Accepted.

## Implementation order (for the later plan)

1. Tokens (colors, globalstyles, icons stay Nerd, aerospace gap).
2. Left bracket + highlight restyle (no event-model change).
3. Right status bracket + slider/battery colors.
4. QA as above.
