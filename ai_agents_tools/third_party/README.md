# Third-party agent skills (vendored)

Skills from external repos, vendored here so **home-manager / nix** can symlink them
into `~/.agents/skills/` on a fresh machine without `npx` or network at deploy time.

## caveman

- **Source:** [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) (`skills/caveman`, pinned `v2.3.1`)
- **Always-on rule body:** `skills/caveman/caveman-activate.md` (upstream `src/rules/caveman-activate.md`); live copy with Cursor `alwaysApply` is `ai_agents_tools/rules/caveman.md`
- **Lock metadata:** `skill-lock.json`

Cursor has no skill `alwaysApply` / env var. Native always-on is a user-level rule
(`~/.cursor/rules/caveman.mdc`), same as `npx skills add … -a cursor -g` plus
`--with-init`. The skill itself still lands in `~/.cursor/skills/caveman` so
`/caveman` and intensity switches work.

To upgrade on a dev machine:

```bash
# Prefer a release tag over main.
git clone --depth 1 --branch vX.Y.Z --filter=blob:none --sparse https://github.com/JuliusBrussee/caveman.git /tmp/caveman
git -C /tmp/caveman sparse-checkout set skills/caveman src/rules
cp -R /tmp/caveman/skills/caveman/. ai_agents_tools/third_party/skills/caveman/
cp /tmp/caveman/src/rules/caveman-activate.md ai_agents_tools/third_party/skills/caveman/caveman-activate.md
# Refresh ai_agents_tools/rules/caveman.md from caveman-activate.md; keep the alwaysApply frontmatter.
```

Then commit the updated vendored copy.

## skill-creator

- **Source:** [anthropics/skills](https://github.com/anthropics/skills) (`skills/skill-creator`)
- **Lock metadata:** `skill-lock.json` (used by `npx skills` when you upgrade)

To upgrade on a dev machine:

```bash
npx skills add anthropics/skills --skill skill-creator -g -a opencode -y
cp -R ~/.agents/skills/skill-creator ai_agents_tools/third_party/skills/skill-creator
cp ~/.agents/.skill-lock.json ai_agents_tools/third_party/skill-lock.json
```

Then commit the updated vendored copy.
