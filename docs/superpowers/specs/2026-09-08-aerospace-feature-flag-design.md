# AeroSpace feature flag

One Nix boolean gates AeroSpace start and SketchyBar's window-manager widgets.

## Flag

- SOT: repo-root `features.nix` (`aerospace = false` by default).
- `flake.nix` imports it and passes `features` via darwin `specialArgs` and `home-manager.extraSpecialArgs`.
- Flip: edit the bool, run `rebuild.sh`.

## When false

- Homebrew cask stays (app remains on disk).
- Nix does not start AeroSpace. `aerospace.toml` has `start-at-login = false` so the app does not also login-launch.
- `home.activation` reloads config if the process is up, then `killall AeroSpace`, and boots out leftover `bobko.aerospace` LaunchAgents.
- SketchyBar LaunchAgent env `DOTFILES_WINDOW_MANAGER=macos_native`. Spaces use Mission Control. Window picker is skipped (`windows.lua` already no-ops unless aerospace).

## When true

- `launchd.user.agents.aerospace` runs `open -a AeroSpace` at load (`KeepAlive = false`).
- SketchyBar env `DOTFILES_WINDOW_MANAGER=aerospace`.

## Out of scope

JankyBorders, fonts, menu-bar hide, uninstalling the cask.
