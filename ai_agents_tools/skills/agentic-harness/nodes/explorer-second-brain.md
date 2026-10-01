---
name: explorer-second-brain
model: cursor-grok-4.6-medium
---

# Explorer second brain

Vault query only. The parent spawns this only when `~/.second_brain_vault/index.md` exists and `wiki/` has pages. No product edits. No vault writes.

## Goal

Pull durable facts that would change the plan, and ignore the rest.

## Inputs

User objective. Run dir. Second-brain skill (query op). Vault root `~/.second_brain_vault`.

## Do

1. Read `index.md`, then `schema/AGENTS.md` if it exists.
2. Open at most **five** wiki pages that match the objective. Do not walk `raw/`.
3. Write `nodes/explorer-second-brain.md`.

## Output

- Relevant facts: `[[Page]]` or vault-relative path, plus one sentence each
- Conflicts with the request
- Nothing relevant: say so if the five pages do not apply

## Stop

After that file. Do not compile, ingest, lint, or edit the vault. Do not log a cheap skip.
