# AeroSpace cheat sheet — implementation plan

**Goal:** Searchable top panel listing AeroSpace bindings parsed from `aerospace.toml`, toggled with Option+Shift+/.

**Architecture:** Swift accessory app + Unix socket IPC; Nix-built binary on PATH; one binding in `aerospace.toml`.

## Tasks

- [x] Task 1: `BindingParser.swift` — parse `[mode.*.binding]` from `~/.config/aerospace/aerospace.toml`
- [x] Task 2: Swift UI + panel (`PanelController`, `ContentView`, socket server, CLI `toggle`)
- [x] Task 3: `home/bin/aerospace-cheatsheet/default.nix` + wire into `configuration.nix`
- [x] Task 4: `alt-shift-slash` in `aerospace.toml`
- [x] Task 5: `nix build --dry-run` + local `swiftc` smoke test
