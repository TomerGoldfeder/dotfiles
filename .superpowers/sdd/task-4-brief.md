# Task 4 brief

Follow nix-install skill: /Users/tomergo/personal_projects/dotfiles/ai_agents_tools/skills/nix-install/SKILL.md

Work from: /Users/tomergo/personal_projects/dotfiles

1. `ln -sfn /Users/tomergo/personal_projects/dotfiles ~/.dotfiles`
2. `nix build --dry-run --no-link ~/.dotfiles#darwinConfigurations.mac.system` — must exit 0. nix-darwin options.json warning is OK.
3. Only if step 2 succeeds: `~/.dotfiles/rebuild.sh`
4. Confirm `ls -l ~/.cursor/skills/agentic-harness/SKILL.md` points at the repo skill.

Do not commit. If dry-run fails, do not rebuild; report the error.

Report: `/Users/tomergo/personal_projects/dotfiles/.superpowers/sdd/task-4-report.md` with commands, exit codes, symlink result.
