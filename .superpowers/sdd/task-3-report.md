# Task 3 report: AGENTS.md + home.nix

## Status

DONE

## What was done

Wired always-on coding precedence to `agentic-harness` and registered the skill in Nix `agentSkillPaths`. Did not rewrite skill files. Did not run nix rebuild (Task 4). Did not commit.

Using skill: enhanced-workflow (Phase 1 — startup). Using skill: repo-navigation. Using skill: code-standards. Read enhanced-workflow. Brainstorming: design already locked in Task 1 spec + plan; this task was two-file wiring, not a new design.

## Files changed

- `ai_agents_tools/rules/AGENTS.md` — Coding section: after the existing enhanced-workflow tip, added the plan’s precedence paragraph. Caveman / execution-sequence / enhanced-workflow tip kept. `enhanced-workflow` not deleted.
- `home.nix` — added `agentic-harness = "skills/agentic-harness";` to `agentSkillPaths`. Left the pre-existing working-tree removal of `dag-harness` alone.

## Commits

none (per brief)

## Tests

n/a (markdown + one Nix attr). `docs/**/test_strategy.md` not found. `test.code-standards-verifier` skill not found; skipped. `troubleshooting-issues-recorder` skill not found; no new runtime issue to record. Did not invoke performance-journaler (out of this task’s file scope).

## Concerns

none. Rebuild / symlink check is Task 4. Cursor still sees `~/.cursor/rules/AGENTS.mdc` via the existing home.file symlink after that rebuild.

## Notes for later tasks

Task 4: `ln -sfn` repo to `~/.dotfiles`, nix dry-run, then `rebuild.sh`, then confirm `~/.cursor/skills/agentic-harness/SKILL.md` resolves into this repo.
