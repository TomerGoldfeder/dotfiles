# Third-party agent skills (vendored)

Skills from external repos, vendored here so **home-manager / nix** can symlink them
into `~/.agents/skills/` on a fresh machine without `npx` or network at deploy time.

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
