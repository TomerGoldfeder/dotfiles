# herdr-tab-panes

Popup showing every pane in the current tab (left) with a live preview of the
selected one (right).

## Requirements

- herdr 0.7.4+ (adds popup plugin panes)
- Python 3.9+ on PATH
- Linux or macOS (curses-based UI; not declared for Windows)

## Install

Local development (this checkout):

```bash
herdr plugin link /path/to/herdr-tab-panes
```

Once pushed to GitHub, tag the repo `herdr-plugin` and others can run:

```bash
herdr plugin install <you>/herdr-tab-panes
```

## Bind a key

herdr does not bind keys for a plugin automatically. Add to
`~/.config/herdr/config.toml`:

```toml
[[keys.command]]
key = "prefix+t"
type = "plugin_action"
command = "tomer.tab-panes.open"
description = "Show panes in this tab"
```

Reload:

```bash
herdr server reload-config
```

Press `ctrl+b t` (or whatever key you bound) from inside any tab.

## Using it

| Key | Does |
|---|---|
| `↑`/`↓`, `j`/`k` | move pane selection (list focus) or scroll preview (preview focus) |
| `tab`, `→`, `l` | focus the preview pane (loads recent scrollback) |
| `←`, `h` | focus the pane list |
| `enter` | focus that pane in herdr, close the popup |
| `q`, `esc`, `ctrl+c` | close, change nothing |

The list resyncs every ~4s (new/closed panes) and the preview refreshes every
~500ms. `●` marks the pane currently focused in herdr.

## How it works

- Reads `HERDR_TAB_ID`, injected by herdr into the popup process, to know
  which tab to list.
- One `layout.export` call over herdr's local Unix socket returns
  `{type: layout_export, layout: {root, focused_pane_id, ...}}`. Leaf `pane`
  nodes under `layout.root` become the list.
- The preview polls `pane.read` (`source: recent_unwrapped`), hard-wraps to the
  preview column width, and bottom-fills the right pane.
- Enter calls `pane.focus` with the pane's id, then the popup closes because
  its process exits (herdr closes any popup when its command exits).

No CLI subprocess calls in the render loop — everything after startup goes
over the socket directly, so the refresh stays cheap. Herdr closes the socket
after each request, so the client opens a fresh connection per call.

## Known limitation

`pane.focus` (absolute focus-by-id) is used based on observed behavior of
other herdr plugins rather than the published socket method table, which
only documents the relative `pane.focus_direction`. If your herdr build
rejects it, the picker still lists and previews correctly — only the
enter-to-jump action would need a fallback (e.g. `pane.zoom` + directional
`pane.focus_direction` walk, or filing an issue against herdr itself).
