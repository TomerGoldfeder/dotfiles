# Second-brain vault contracts

Layers:
- `raw/` — immutable ingest sources; agents never mutate
- `wiki/` — LLM-owned pages (create, update, link)
- `schema/` — contracts and lint rules for ingest / query / lint

Rules:
- Query starts at `index.md`, then follow wikilinks into `wiki/`
- Append `log.md` with `## [YYYY-MM-DD] op | title`
- Never write secrets, tokens, or env files into the vault
- Typed pages follow `~/.cursor/skills/second-brain/references/typed-pages.md` (versioned with dotfiles)
- `maps/` and `bases/` views are generated from typed pages — only canvas node positions may be hand-edited
- Never store copied source code
