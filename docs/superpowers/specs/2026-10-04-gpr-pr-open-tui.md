# gpr — PR-open TUI

Date: 2026-10-04  
Status: approved for implementation (harness planner)

## Goal

Ship a first-party PATH binary `gpr` that opens a Tokyo Night midnight Bubble Tea form in the current git repo, then runs `gh pr create` with the fields the form exposes. Durable install is nix-darwin `callPackage` into `environment.systemPackages`, not Homebrew.

## Locked decisions

| Topic | Decision |
|-------|----------|
| PATH binary | `gpr` (never `pr` — `/usr/bin/pr` exists) |
| Tree | New Go module `home/bin/gpr/` (module path `gpr`). Do not import `hs/internal`. Duplicate Theme slots + Tokyo Night midnight only. |
| Theme | `theme.Default = TokyoNightMidnight`. Views read theme slots, never raw hex. Not classic night `#1a1b26`, not Catppuccin. |
| Stack | Bubble Tea v1.3.x + Lip Gloss v1.1.x (match `hs` pins). Shell out to `gh` and `git`. No Cobra. Glamour only for title/body markdown preview. Delta optional if on PATH for diff preview; never required. |
| Create path | Assemble `gh pr create` flags. No GitHub HTTP API. Tests use a fake runner / `--dry-run` — never create a real PR. |
| Install | Copy `home/bin/hs/default.nix` shape (`buildGoModule`, `vendorHash`, `mainProgram = "gpr"`). Wire `gpr = pkgs.callPackage ./home/bin/gpr { };` and append `gpr` next to `h` in `configuration.nix`. |
| Cwd | Current git repo only. No `--repo` / `-R` in v1. |

## Theme schema (Tokyo Night midnight slots)

| Slot | Hex |
|------|-----|
| Bg | `#0C0E14` |
| Surface | `#16161e` |
| SurfaceStrong | `#1f2335` |
| Border | `#3b4261` |
| BorderStrong | `#7aa2f7` |
| Text | `#c0caf5` |
| TextMuted | `#565f89` |
| TextInverse | `#0C0E14` |
| Primary | `#7aa2f7` |
| PrimaryStrong | `#89ddff` |
| Accent | `#bb9af7` |
| Success | `#9ece6a` |
| Warning | `#e0af68` |
| Error | `#f7768e` |
| Info | `#7dcfff` |

## Out of scope

- `home/bin/hs/**` edits or imports
- `flake.nix`, `home.nix` (no `sessionPath` wrapper)
- Homebrew install path
- `gh-dash` changes
- Commits / push / creating a real GitHub PR during verify
- `--web`, `--editor`, `--body-file`, `--recover`, `--repo` / `-R`

## Architecture

Four logical units under `home/bin/gpr/`:

1. **Theme** — slot struct + `TokyoNightMidnight` / `Default`. All views read slots.
2. **Repo + create services** — detect git context; list PR templates; fill title/body from commits; assemble and run `gh pr create` (injectable runner).
3. **TUI** — Bubble Tea form: edit fields, toggles, preview diff/body, dry-run, submit, quit.
4. **Nix packaging** — `default.nix` + `configuration.nix` `callPackage` / `systemPackages` wiring.

### Data flow

```
cwd → gitctx.Detect → tui.New(form defaults)
user ↓
user edits / fill / template / toggles
      ↓
create.BuildArgs → gh pr create [--dry-run]
      ↓
show PR URL (submit) or preview text (dry-run)
```

### `gh pr create` fields exposed

title, body, base (default: `gh-merge-base` if set, else repo default branch), head (default: current branch), draft, assignee (incl. `@me`), reviewer (users and `org/team`), label, milestone, project, no-maintainer-edit, template (list + pick as starting body), fill / fill-first / fill-verbose (populate form), dry-run preview before submit.
