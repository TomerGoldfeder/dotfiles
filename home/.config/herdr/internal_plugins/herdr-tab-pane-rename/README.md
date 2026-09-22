# Tab Pane Rename

On `pane.created`, rename the new pane to `{tab_label}: {slug}` when the
tab has a custom (non-numeric) name.

- `slug` is the pane's existing label, or the first foreground process
  name from `herdr pane process-info` when the pane is unlabeled.
- Skips auto-named tabs whose label is blank or numeric (`"1"`, `"2"`, …).
- Skips when the pane label already starts with `{tab_label}: `.
- Does **not** listen to `tab.renamed` — manual pane renames stay put.

## Install

This repo links internal plugins from `home/.config/herdr/int_plugins.list`
on every `darwin-rebuild`. Ensure the list contains:

```
internal_plugins/herdr-tab-pane-rename
```

For a one-off local link without rebuild:

```bash
herdr plugin link ~/.config/herdr/internal_plugins/herdr-tab-pane-rename
herdr server reload-config
```

## Test plan

1. Rename a tab to a custom name (e.g. `work`).
2. Split a new pane in that tab.
3. Confirm the new pane label is prefixed, e.g. `work: zsh` (or `work: <existing-label>`).
4. Manually rename a pane; create another pane — the manual rename must stay unchanged.
5. In an auto-named tab (`1`, `2`, …), new panes must not get a prefix.

## Known limitation

If the tab is renamed **after** panes were created, those panes keep the
stale prefix. Fixing that needs a `tab.renamed` hook; out of scope for
this plugin (avoids fighting intentional manual renames).

## Unit tests

```bash
cd ~/.config/herdr/internal_plugins/herdr-tab-pane-rename
python3 -m unittest test_on_pane_created
```
