# Task 4 report: Nix install verification

Work dir: `/Users/tomergo/personal_projects/dotfiles`
Skill: nix-install (repo copy at `ai_agents_tools/skills/nix-install/SKILL.md`; user copy also loaded)
No commit.

## Commands and exit codes

### 1. Point `~/.dotfiles` at clone

```bash
ln -sfn /Users/tomergo/personal_projects/dotfiles ~/.dotfiles
```

Exit: **0**

Result: `/Users/tomergo/.dotfiles` -> `/Users/tomergo/personal_projects/dotfiles`

### 2. Dry-run nix-darwin system

```bash
nix build --dry-run --no-link ~/.dotfiles#darwinConfigurations.mac.system
```

Exit: **0**

Harmless warnings:
- Git tree has uncommitted changes
- nix-darwin `builtins.derivation` / `options.json` store-context warning

Planned builds included `hm_agenticharness.drv` and `darwin-system-26.05.c3e90c8.drv`.

### 3. Switch (`rebuild.sh`)

```bash
~/.dotfiles/rebuild.sh
```

Exit: **1** (not skipped; dry-run succeeded so script ran)

Error (exact):

```
sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
sudo: a password is required
```

`rebuild.sh` execs `sudo darwin-rebuild switch --flake ~/.dotfiles#mac`. Agent shell has no TTY for sudo. Did not invent success. User must run `~/.dotfiles/rebuild.sh` in a real terminal (or grant interactive sudo).

### 4. Skill symlink check

```bash
ls -l ~/.cursor/skills/agentic-harness/SKILL.md
```

Exit: **1**

```
ls: /Users/tomergo/.cursor/skills/agentic-harness/SKILL.md: No such file or directory
```

Expected until home-manager activation from a successful switch. Source exists in repo at `ai_agents_tools/skills/agentic-harness/SKILL.md`.

## Summary

| Step | Exit | Notes |
|------|------|--------|
| ln | 0 | `~/.dotfiles` correct |
| dry-run | 0 | eval/plan OK |
| rebuild.sh | 1 | sudo needs TTY/password |
| agentic-harness live link | missing | blocked on switch |

Status: **partial** — dry-run green, live install not applied.
