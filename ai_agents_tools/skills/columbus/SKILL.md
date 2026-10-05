---
name: columbus
description: >-
  Use when ramping up a new codebase or a new job/company, mapping a system
  (system map / fog of war), asking "what do I know about X", "how do I run/test X",
  tracing a request/flow, filing meeting notes about systems or people, or when
  the user says columbus.
---

# Columbus

Announce once: `Using skill: columbus`

**Prereq:** second-brain skill rules govern all vault writes (raw immutable, `index.md`, `log.md`, secrets deny). Typed pages follow `../second-brain/references/typed-pages.md`.

**Scripts:** resolve this skill dir from this `SKILL.md` (e.g. `~/.cursor/skills/columbus`). Render: `python3 <skill dir>/scripts/render_maps.py [--vault PATH]` and `--check`.

## survey

Ramp up a repo. Prefer breadth. State what you skipped.

1. Run repo-navigation first.
2. Find build / test / run (README, Makefile, package manifests, CI). Note entry points and top-level layout.
3. Create/update a `repo` page.
4. Create/upgrade `service` / `component` pages it implements to `seen` with `repo:` sources.
5. Add rumored pages or `maybe` edges for things it talks to (clients, env/config names, queues).
6. Create `concept` pages for domain terms.
7. Create `question` pages for unknowns; set `ask` from CODEOWNERS / git log when known (person pages rumored-style minimal).
8. Render. Report map delta.

Done when: `repo` page exists, implemented places are `seen` or explicitly skipped, rumored neighbors/questions filed, delta reported.

## chart

File observations (user pastes meeting notes or says what they learned).

1. Ingest per second-brain (new `raw/` file when pasting a source).
2. Upsert person / question / commitment / places / edges with `meeting:` or `chat:` sources.
3. Heard-only facts stay `rumored` or go in `maybe`.
4. Render. Report delta.

Done when: durable facts are on typed pages + index, heard-only not over-promoted, delta reported.

## trace

One request end to end.

1. Follow code from entry to sinks.
2. Write a `flow` page with `steps`.
3. Promote places fully proven by the trace to `understood` with `repo:` sources.
4. Optionally offer an archify `sequence` diagram if the archify skill is installed.
5. Render. Report.

Done when: `flow` exists, proven places promoted with evidence, delta reported.

## ask

Ramp-up Q&A.

1. Answer from the vault first (`index.md` → typed pages). Cite `[[Page]]`.
2. If the vault lacks it, read the code/docs, answer with evidence, then file the new durable fact (two-output rule).
3. Promote knowledge only with evidence.
4. Questions you cannot answer become `question` pages.

Done when: the user has a cited answer, and new durable facts (or open questions) are filed.

## render

`python3 <skill dir>/scripts/render_maps.py [--vault PATH]` (and `--check`). Report canvases written + explored % + what changed.

Done when: canvases written (or `--check` findings listed) and delta reported.

## Evidence & promotion

| knowledge | Needs |
|-----------|--------|
| `rumored` | none |
| `seen` | ≥1 `sources` (`repo:` / `doc:` / `meeting:` / `chat:` / `pr:`) |
| `understood` | ≥1 `sources`; code/docs actually prove the claim |
| `owned` | a `pr:` source |

`maybe` = heard, unverified. Fog = wikilink with no page yet.

## Map delta

`--check` prints findings only (silent + exit 0 if clean). Render prints `canvases written: N; deleted stale: N; explored N%`.

Capture **before** explored % by running render (or reading the last render summary) *before* writing pages. **After** = the render at the end.

Report:

- newly discovered
- promoted
- still fog
- explored % before → after

## Company data

Store paths, names, short explanations. Never copied source, secrets, or credentials. Deny-list: second-brain secrets deny.

## Existing vault (non-destructive, one-time)

Create missing only; never overwrite existing files:

- `maps/`
- `bases/` — copy from `../second-brain/vault-seed/bases/` only if absent
- append the typed-pages pointer to `schema/AGENTS.md` if missing
- add `## Maps` to `index.md` if missing

## Red flags

Overwrite existing vault files on upgrade · copy source/secrets into wiki · promote without `sources` · `owned` without `pr:` · treat maps/bases as source of truth · rewrite `raw/` · unbounded survey with no skip list · skip second-brain two-output / index / log
