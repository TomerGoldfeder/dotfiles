#!/usr/bin/env bash
# Takes a fresh Mac from nothing to a built nix-darwin config.
# Run this once. After it finishes, use ./rebuild.sh for every later change.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
NIX_DAEMON_PROFILE="/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh"
DETERMINATE_DAEMON="system/systems.determinate.nix-daemon"

load_nix() {
  if [[ -f "$NIX_DAEMON_PROFILE" ]]; then
    # shellcheck disable=SC1091
    . "$NIX_DAEMON_PROFILE"
  fi
}

ensure_nix_daemon() {
  if pgrep -q determinate-nixd || pgrep -q nix-daemon; then
    echo "    nix daemon already running"
    return
  fi
  echo "    starting Determinate nix daemon"
  if launchctl print "$DETERMINATE_DAEMON" >/dev/null 2>&1; then
    sudo launchctl kickstart -k "$DETERMINATE_DAEMON"
  elif [[ -f /Library/LaunchDaemons/systems.determinate.nix-daemon.plist ]]; then
    sudo launchctl bootstrap system /Library/LaunchDaemons/systems.determinate.nix-daemon.plist
  else
    echo "    Could not find systems.determinate.nix-daemon. Re-run the Determinate installer."
    exit 1
  fi
}

echo "==> Step 1: Determinate Nix + daemon"
if command -v nix >/dev/null 2>&1; then
  echo "    nix already installed, skipping installer"
else
  curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix \
    | sh -s -- install --no-confirm
fi
load_nix
ensure_nix_daemon
if ! command -v nix >/dev/null 2>&1; then
  echo "    nix is still not on PATH. Open a new terminal and re-run ./bootstrap.sh."
  exit 1
fi

echo "==> Step 2: symlink this repo to ~/.dotfiles"
# This is not the same as the ~/.config/* links.
# home-manager mkOutOfStoreSymlink makes ~/.config/wezterm (and nvim, tmux, …)
# point at files inside the repo so edits apply without a rebuild.
# Those targets are all ${home}/.dotfiles/home/.config/..., so this stable
# alias must exist regardless of where the clone lives
# (e.g. ~/personal_projects/dotfiles vs ~/code/dotfiles).
# rebuild.sh refreshes the same link before every switch.
ln -sfn "$DIR" ~/.dotfiles

echo "==> Step 3: personalize the configured username"
# flake.nix has a single `user = "tomergo";`. That value is passed into
# configuration.nix and home.nix (home path /Users/$user, primaryUser,
# home-manager.users.$user). The flake host label "mac" is not the Mac's
# computer name — leave it unless you also rename it in rebuild.sh.
# Do this before any sudo call: sudo resets $USER to root, so whoami has
# to run as the real interactive user first.
REAL_USER="$(whoami)"
FLAKE_USER="$(sed -nE 's/^[[:space:]]*user = "([^"]+)";.*/\1/p' "$DIR/flake.nix" | head -n1)"
if [[ -z "$FLAKE_USER" ]]; then
  echo "    Could not find the single \"user = \" line in flake.nix."
  echo "    Edit flake.nix yourself before continuing."
  exit 1
elif [[ "$FLAKE_USER" != "$REAL_USER" ]]; then
  echo "    flake.nix is configured for user \"$FLAKE_USER\", but you are \"$REAL_USER\"."
  read -r -p "    Rewrite flake.nix's \"user = \" line to \"$REAL_USER\"? [y/N] " REPLY
  if [[ "$REPLY" == "y" || "$REPLY" == "Y" ]]; then
    sed -i '' -E "s/^([[:space:]]*user = \")[^\"]+(\";.*)/\1${REAL_USER}\2/" "$DIR/flake.nix"
    echo "    Updated. Review the change with: git diff flake.nix"
  else
    echo "    Skipped. Edit the single \"user = \" line in flake.nix yourself before continuing."
    exit 1
  fi
else
  echo "    flake.nix already matches \"$REAL_USER\", nothing to do."
fi

echo "==> Step 4: first darwin-rebuild switch (pinned to nix-darwin-26.05)"
# darwin-rebuild doesn't exist yet on a fresh machine, so run it straight
# from the flake this once. After this, rebuild.sh works normally.
# This fetches the darwin-rebuild tool from the nix-darwin-26.05 release branch,
# not the exact flake.lock revision. The system config it applies is still pinned
# by this repo's flake.lock.
# sudo resets PATH to a secure default that excludes /nix/.../bin, so a
# freshly installed `nix` would not be found under sudo even though it's
# on PATH here. Resolve the absolute path first and invoke that instead.
NIX_BIN="$(command -v nix)"
# "mac" is the flake host label — if you renamed it, change it in flake.nix
# and rebuild.sh too.
sudo "$NIX_BIN" run github:nix-darwin/nix-darwin/nix-darwin-26.05#darwin-rebuild -- \
  switch --flake ~/.dotfiles#mac

if [[ ! -f "$DIR/secrets/env.sh" && -f "$DIR/secrets/env.sh.example" ]]; then
  echo "==> Copied secrets/env.sh.example → secrets/env.sh (fill in tokens locally; do not commit)"
  cp "$DIR/secrets/env.sh.example" "$DIR/secrets/env.sh"
fi

echo "==> Done. Use ./rebuild.sh for future changes."
