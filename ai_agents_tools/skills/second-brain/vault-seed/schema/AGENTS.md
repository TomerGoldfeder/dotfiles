# Second-brain vault contracts

Layers:
- `raw/` — immutable ingest sources; agents never mutate
- `wiki/` — LLM-owned pages (create, update, link)
- `schema/` — contracts and lint rules for ingest / query / lint

Rules:
- Query starts at `index.md`, then follow wikilinks into `wiki/`
- Append `log.md` with `## [YYYY-MM-DD] op | title`
- Never write secrets, tokens, or env files into the vault
