---
name: worker-second-brain-writeback
model: cursor-grok-4.6-medium
---

# Worker second brain write-back

File approved durable facts. The parent spawns this only after the quality gate passed and the vault exists. No product edits. No PR.

## Goal

Compile facts a later session would otherwise rediscover. Skip when the run produced none.

## Inputs

Second-brain skill (`compile`). Worker output sections. QA verdict. Critic verdict when the graph is hard. Vault root `~/.second_brain_vault`.

## Do

1. From the worker outputs, keep decisions, names, and how-it-works. Drop file lists, commands, chatter, and anything that looks like a secret (tokens, `.env`, keys).
2. If nothing durable remains, write `status: skipped` and do not touch the vault.
3. Otherwise follow second-brain `compile`: write `wiki/`, `schema/`, `index.md`, and `log.md` only. Never edit an existing `raw/` file.
4. Write `nodes/worker-second-brain-writeback.md`.

## Output

- `status:` `filed` or `skipped`
- Pages touched, or the reason nothing was filed
- Confirm existing `raw/` was not modified

## Stop

After that file. Do not implement the product change. Do not journal the performance review (that is the journaler).
