---
name: nix-install
description: >-
  Installs CLIs, GUI apps, fonts, Homebrew formulae/casks, and editor tooling
  into this nix-darwin dotfiles repo instead of ad-hoc brew/nix-env/npm/mason.
  Use whenever the user asks to install, add, brew, cask, or put something on
  PATH; wants a Mac app, font, or SketchyBar/AeroSpace helper; or says a tool
  is missing after a rebuild. Do not use for project npm/pip/cargo deps inside
  an application repo.
---

# Install into Nix (dotfiles)

On this machine, **Nix is the install**. `brew install`, `nix-env -i`, `npm -g`,
Cargo `install`, and Mason are not durable: Homebrew `zap` on `darwin-rebuild`
removes formulae that are not listed, and PATH tools vanish on a fresh Mac.

Announce once per conversation:

```
Using skill: nix-install
```

Then edit the **repo** (via `~/.dotfiles` → clone), not the live `~/.config` copies.

## Repo map

| Path | What goes here |
|------|----------------|
| `configuration.nix` | System PATH (`environment.systemPackages`), Nix fonts, Homebrew `brews` / `casks` / `taps`, LaunchAgents |
| `home.nix` | User files (`mkOutOfStoreSymlink`), zsh, home-manager activation, Cursor/agent skill links |
| `home/.config/<app>/` | Live app config (WezTerm, nvim, tmux, AeroSpace, SketchyBar, …) |
| `ai_agents_tools/skills/<name>/` | First-party agent skills (this file's hierarchy). Upstream skills are flake inputs, not copies here. |
| `ai_agents_tools/rules/` | Always-on Cursor/agent rules (caveman rule is separate from the caveman skill). |
| `secrets/env.sh` | Tokens. Gitignored. Never commit. |

`flake.nix` is only the username, flake inputs, and `darwinConfigurations.mac`. Do not dump packages there. Flake **inputs** for third-party agent skills are allowed (see item 7).

## Where the package goes

Prefer **nixpkgs** over Homebrew when the package exists for `aarch64-darwin`.

1. **CLI on PATH** (nvim, jq, eza, node, linters) → `configuration.nix` `environment.systemPackages`.
2. **Nerd Font from nixpkgs** → `configuration.nix` `fonts.packages`.
3. **Mac GUI app / extra font cask** → `homebrew.casks`. Add a `homebrew.taps` entry if the cask is tapped (e.g. `nikitabobko/tap/aerospace`).
4. **Brew formula** (not in nixpkgs, or required as a brew binary like SketchyBar) → `homebrew.brews`. Use the `{ name = "..."; trusted = true; }` attr for `FelixKratz/formulae/*`. **Do not** `start_service` / `restart_service` — root `darwin-rebuild` cannot bootstrap user LaunchAgents (error 5). Use `launchd.user.agents` instead (see sketchybar/borders).
5. **Root-owned self-updating apps** (Chrome, Docker Desktop) → still list them in `casks` so `zap` does not try to uninstall them.
6. **App config** → files under `home/.config/<app>/`, then a `home.file` `mkOutOfStoreSymlink` in `home.nix` pointing at `${dotfiles}/home/.config/...`.
7. **New agent skill** — two sources; never copy upstream trees into this repo:
   - **First-party skill:** `ai_agents_tools/skills/<name>/SKILL.md`, then `agentSkillPaths.<name> = "skills/<name>";` in `home.nix` (out-of-store symlink into `~/.cursor/skills`, `~/.agents/skills`, and `~/.claude/skills`).
   - **Third-party / upstream skill:** add a flake input in `flake.nix` (`github:owner/repo`, plus a ref if you need a pin). `inherit` that input in `home-manager.extraSpecialArgs`. Put an absolute store path in `agentSkillStorePaths` (e.g. `"${input}/skills/<name>"`). Wire `home.file` with plain `source` + `force = true` for the three skill homes — do not wrap the store path in `mkOutOfStoreSymlink`. Bump with `nix flake update <input>`. If upstream has no `flake.nix`, set `input.flake = false` (as with `caveman`). Do **not** copy into `ai_agents_tools/third_party/` or `ai_agents_tools/skills/`.
8. **Secret / token** → `secrets/env.sh` (copy from `secrets/env.sh.example` if needed). Not Nix.

If the user wants a GUI service (SketchyBar, JankyBorders), add the formula **and** the `launchd.user.agents` block; do not `brew services start`.

## Do not

- Leave `brew install …` as the only step.
- Install into `/usr/local` or `~/.local` except for documented exceptions (SbarLua under `~/.local/share/sketchybar_lua` via `home.activation`).
- Put packages in `flake.nix` (skill **inputs** are allowed).
- Vendor upstream skills under `ai_agents_tools/third_party/` or copy them into `ai_agents_tools/skills/`.
- Edit `~/.config/...` as source of truth; edit `home/.config/...` in the repo.
- Commit `secrets/env.sh`.

## After the edit

Run these in order. Do not skip the dry-run.

**1. Point `~/.dotfiles` at the clone** (same as `rebuild.sh`):

```bash
ln -sfn <dotfiles-repo-root> ~/.dotfiles
```

Use the repo you just edited (usually `~/personal_projects/dotfiles`).

**2. Dry-run the nix-darwin system** — evaluate/plan without switching. The agent must run this and wait for a zero exit. A non-zero exit is a failed install: fix the Nix files and repeat this step. Do not run `rebuild.sh` until it passes.

```bash
nix build --dry-run --no-link ~/.dotfiles#darwinConfigurations.mac.system
```

The nix-darwin warning about `builtins.derivation` / `options.json` is harmless. Treat any other error as a blocker (missing attr, eval failure, syntax).

**3. Switch** (actually installs). Only after step 2 succeeds:

```bash
~/.dotfiles/rebuild.sh
```

That runs `darwin-rebuild switch --flake ~/.dotfiles#mac`. Do not claim the tool is installed until switch succeeds (or the user explicitly defers rebuild after a passing dry-run).

## Examples

- “Install fd” → nixpkgs `fd` in `environment.systemPackages`.
- “Install WezTerm” → already a cask; if missing, `homebrew.casks`.
- “Install a SketchyBar helper formula” → `homebrew.brews` + tap if needed; no brew services.
- “Add a Neovim plugin config” → `home/.config/nvim/...`, not a Nix package unless the plugin needs a binary on PATH.
