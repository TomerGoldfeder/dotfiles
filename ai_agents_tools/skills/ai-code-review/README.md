# ai-code-review — advisory review for agent-written code

One skill + 7 subagents. In this dotfiles repo the source-of-truth is:
- skill: `ai_agents_tools/skills/ai-code-review`
- agents: `ai_agents_tools/agents`

`home.nix` symlinks these into each runtime (`.cursor`, `.agents`, `.claude`), so all harnesses consume the same files.

```text
ai_agents_tools/
├── skills/
│   └── ai-code-review/
│       ├── SKILL.md                 # orchestration: collect → intent → reviewers → verify → report
│       ├── references/
│       │   ├── reviewer-common.md   # rules every reviewer follows (bar, severity, confidence)
│       │   ├── findings-contract.md # finding + verdict format
│       │   ├── findings.schema.json
│       │   ├── do-not-report.md     # false-positive list (append project-specific lines)
│       │   └── transcript.md        # how to read a raw JSONL transcript
│       └── scripts/                 # stdlib Python 3.9+, no installs
│           ├── collect_diff.py      # diff vs merge-base (+uncommitted +untracked), wide context
│           ├── test_tamper.py       # removed asserts, skips, tolerance, test config, special-case hints
│           ├── deps_check.py        # new deps → registry; new imports → resolvable?
│           ├── run_checks.py        # project linters/type checker on changed files (--tests opt-in)
│           ├── find_transcript.py   # locate Claude Code / Cursor session JSONL for this repo
│           ├── make_scratch.py      # disposable worktree for reproductions
│           └── merge_findings.py    # dedupe → candidates; verdicts → report.json / report.md
└── agents/                          # model: claude-sonnet-5-5 in each file
    ├── acr-intent.md  acr-correctness.md  acr-test-integrity.md
    ├── acr-codebase-fit.md  acr-standards.md  acr-security.md
    └── acr-verifier.md
```

## Install

In this repo: keep files under `ai_agents_tools/skills/ai-code-review` and `ai_agents_tools/agents`, then run the Nix rebuild. `home.nix` links them into `.cursor`, `.agents`, and `.claude`.

## Run

Claude Code or Cursor: `/ai-code-review`, or "review what the agent did on this branch". Optional things to say:

- the base: "against `release/2.3`"
- the task: paste it or point to a file — strongest intent source
- a transcript: "use transcript `<path>`" (otherwise the newest matching one is used if found)
- "run the tests too"

Output: `.acr/report.md` (human) and `.acr/report.json` (machine). `.acr/` ignores itself in git.

## Change the model

Edit the `model:` line in each `ai_agents_tools/agents/acr-*.md`. In Cursor an ID your plan or admin blocks silently falls back to another model.

## Internal registries (on-prem)

`deps_check.py` reads `ACR_PYPI_URL`, `ACR_PYPI_SIMPLE_URL`, `ACR_NPM_URL`, `ACR_GO_URL`, `ACR_CRATES_URL` (templates with `{name}`); `--offline` skips lookups.
