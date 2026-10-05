# Typed wiki pages

Contract for Columbus / second-brain map pages. Every fact lives in `wiki/<Name>.md`.
`Name` is the CamelCase file stem. Properties sit in YAML frontmatter using the subset below.
Maps, bases, and the companion brief are generated from these pages; they are never the source of truth.

## Common properties

| Property | Required | Notes |
|---|---|---|
| `type` | yes (typed) | One of the types below. Missing `type` → untyped page (kept, ignored by typed queries). |
| `knowledge` | map places + repo + concept | `rumored` → `seen` → `understood` → `owned`. Default `rumored`. |
| `sources` | when knowledge > rumored | List of strings with prefix `repo:` / `doc:` / `meeting:` / `pr:` / `chat:`. |
| `updated` | recommended | `YYYY-MM-DD`. |
| `aliases` | optional | List of alternate names. |

Link-valued properties are quoted wikilinks `"[[Name]]"` (scalar or list). Fog = a wikilink target with no page yet.

## Types

| Type | Key properties |
|---|---|
| `domain` | `owners` |
| `service` | `domain`, `owners`, `calls`, `emits`, `reads`, `writes`, `maybe` |
| `component` | `parent` (the service) plus the service edge keys |
| `datastore` | `domain`, `kind` (`db` \| `queue` \| `topic` \| `bucket` \| `cache` \| `other`) |
| `external` | `domain` (optional) |
| `flow` | `domain`, `steps` (list of `"[[A]] -> [[B]]: label"`) |
| `repo` | `implements`, `build`, `test`, `run`, `entry_points` |
| `person` | `team`, `role`, `owns`, `ask_about`, `met` |
| `concept` | `aka` |
| `question` | `status` (`open` \| `answered`), `ask`, `about`, `raised` |
| `commitment` | `status` (`open` \| `done`), `to`, `due`, `about` |

Map places: `domain`, `service`, `component`, `datastore`, `external`, `flow`.
Knowledge carriers: map places + `repo` + `concept`.

`maybe` holds relationships heard but unverified (any kind). Promotion above `rumored` needs at least one `sources` entry; `owned` needs a `pr:` source.

## YAML subset

Stdlib-only parsers accept this subset (no full YAML):

```yaml
key: scalar
key: 'quoted'
key: "quoted"
key: []
key:
  - item
  - "[[Other]]"
```

Quotes are stripped. Wikilinks may use `[[Target|alias]]` or `[[Target#heading]]`; the target is `Target`.

## Explored %

Over map places (plus fog nodes counted as rumored):

| knowledge | weight |
|---|---|
| rumored (and fog) | 0 |
| seen | 1/3 |
| understood | 2/3 |
| owned | 1 |

`explored% = 100 * sum(weights) / count(places + fog)`. Empty map → 0%.

## Company-data rule

Store paths, names, and short explanations only. Never copy source code or secrets into the vault.

## Examples

### Service

```markdown
---
type: service
knowledge: seen
domain: "[[Payments]]"
owners:
  - "[[Ada]]"
calls:
  - "[[Ledger]]"
emits: []
reads:
  - "[[OrdersDb]]"
writes: []
maybe:
  - "[[Fraud]]"
sources:
  - "repo:payments-api"
updated: 2026-10-05
---

# PaymentsApi

Deployable payments service.
```

### Person

```markdown
---
type: person
team: Platform
role: tech lead
owns:
  - "[[PaymentsApi]]"
ask_about:
  - "[[Ledger]]"
met: 2026-09-20
updated: 2026-10-05
---

# Ada
```

### Flow

```markdown
---
type: flow
knowledge: understood
domain: "[[Payments]]"
steps:
  - "[[Checkout]] -> [[PaymentsApi]]: authorize"
  - "[[PaymentsApi]] -> [[Ledger]]: post"
sources:
  - "doc:payments-trace"
  - "meeting:2026-10-01"
updated: 2026-10-05
---

# CheckoutAuthorize
```

### Question

```markdown
---
type: question
status: open
ask: "[[Ada]]"
about: "[[Fraud]]"
raised: 2026-10-02
updated: 2026-10-05
---

# WhoOwnsFraudChecks
```
