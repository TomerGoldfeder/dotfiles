---
name: second-brain
description: >-
  Use when querying or updating the personal LLM wiki at ~/.second_brain_vault,
  ingesting sources into a second brain, linting wiki or schema, answering from
  personal notes with Obsidian wikilinks, or when the harness node is
  explorer-second-brain or worker-second-brain-writeback. Use when the user
  mentions second brain, Karpathy llm-wiki, vault index.md, durable facts that
  should persist beyond chat, or filing knowledge after a coding run.
---

# Second brain (LLM wiki)

Karpathy LLM-wiki on disk. Vault durable; chat ephemeral.

Announce once: `Using skill: second-brain`

**Root:** `$HOME/.second_brain_vault` (`~/.second_brain_vault`). Nix activation create-once-copies `vault-seed/` from this skill; agents do not mkdir the vault.

**Cheap skip:** dir missing, or `index.md` missing / stub-only (no real pages). Say so. Do not invent pages.

Read `schema/AGENTS.md` if present — **that file is the vault schema**. Schema wins vault-local conflicts.

## Layers

| Path | Owner | Rule |
|------|--------|------|
| `raw/` | ingest | Existing files **immutable**. New filename only. Never rewrite, truncate, move, delete. |
| `wiki/` | LLM | Pages + `[[Page]]`. Create/update/link. |
| `schema/` | contracts | `schema/AGENTS.md` = contracts. |
| `index.md` | catalog | Query starts here. Topics → pages. |
| `log.md` | ops | Append-only. |

Creating a **new** `raw/` path = ingest. Editing an existing `raw/` file = forbidden.

Agent writes: `wiki/`, `schema/`, `index.md`, `log.md`. `raw/` only as a new path.

## Secrets deny

Never copy into the vault: tokens, API keys, passwords, private keys, `Authorization`; env files (`.env`, `env.sh`); trees named `secrets/`; `~/.oh-my-zsh/custom/*.zsh`; credential-like strings (`sk-`, `ghp_`, `xoxb-`, `AKIA`, `BEGIN … PRIVATE KEY`).

Deny-list hit → skip that source. Do not paste secrets into wiki “for completeness.”

## Ops

One primary op per pass. Append `log.md` when the vault was actually used (query: skip log on cheap-skip).

**Query** — (1) `index.md` first (2) follow `[[wikilinks]]` / listed wiki pages; do not dump all `raw/` (3) answer with citations (`[[Page]]` or vault-relative paths) (4) cheap skip if empty. Harness explorer: stop here; **no vault writes**.

**Ingest** — secret-scan → abort on deny-list. Copy source to **new** `raw/` file (date+slug). Update entity/concept/synthesis wiki pages + `index.md` + `log.md`. Never overwrite existing raw.

**Lint** — orphans (not in index / no inbound links), missing `[[targets]]`, contradictions, stale claims. Fix `wiki/` `schema/` `index.md` `log.md` only. Never “fix” raw.

**Compile** — refresh wiki from ingested raw and/or **approved** facts (write-back). Same write targets as lint. No raw mutation. No secrets.

## Two-output rule

User-facing answer with **durable** knowledge (facts, decisions, names, lasting how-it-works) **also** files `wiki/` + `index.md` + `log.md`.

Do not file: chatter, one-off commands, secrets; harness **`explorer-second-brain`** (query-only; **`worker-second-brain-writeback`** files later); critic/QA-failed work.

No write-back node this turn → file in the same turn.

## `log.md`

Append; do not rewrite history:

```
## [YYYY-MM-DD] op | title
```

`op` ∈ `ingest` | `query` | `lint` | `compile`. Title = short noun phrase. Body: paths + 1–5 bullets. No secrets.

Write-back of approved facts → `compile`, unless a new raw file was added → `ingest`.

## Wikilinks

`[[Page]]` (`|alias` ok). Default file `wiki/Page.md` unless schema says otherwise. Link instead of duplicating. Rename both ends.

## Harness

Graph templates: `agentic-harness/graphs/coding.md`.

| Node | Vault IO |
|------|----------|
| `explorer-second-brain` (`role: explorer`) | **QUERY ONLY.** Findings → `nodes/explorer-second-brain.md`, not the vault. |
| `worker-second-brain-writeback` (`role: worker`) | After **qa** (easy) or **critic pass** (hard). File wiki/schema/index/log. Never existing-raw mutation. Never secrets. |

Do not invent `role: second-brain`. Journaler stays performance-only (`~/.jurnal_tomer/`).

## Red flags

Existing `raw/` edit · secrets/env/`secrets/`/custom `*.zsh` · explorer or critic-fail wiki write · skip `index.md` · durable chat with no file (except explorer deferral) · hand-creating the vault
