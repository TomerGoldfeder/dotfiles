# Lean agentic harness

Evidence from two real runs, then the process change. Implemented in `ai_agents_tools/skills/agentic-harness/`.

## What the runs actually spent

[KPI confluence tab renaming](f5a71697-6747-4a38-8a3b-b7f994a6243c) (mepy_algo) held three full DAGs in one chat. The rename alone spawned a classifier, one explorer (33 reads, 12 greps), a planner, and five workers. Each worker began by loading repo-navigation and code-standards, then re-read the same package. QA loaded those skills again (31 reads, 25 greps) and re-ran greps the workers had already done. Two follow-ups ("drop empty tables", "drop the empty expand") each started a new classifier, planner, worker, QA, promoter, and journaler. One of them also spawned a vault explorer and a write-back worker whose only result was "vault missing, skip."

[Knowledge-transfer docs](ef22d4c7-1187-4207-8638-c9f644c59011) (gtstore) used eight explorer nodes for one docs pass. QA then did 41 reads and 44 greps because its prompt said code-standards is the gold standard and every violation must be recorded. There was no test command, so QA invented a repo-wide docs audit. Critic failed, and the harness re-ran worker, QA, and critic.

Shared pattern: role files say what not to do ("do not implement", "Why separate") and leave the deliverable open. The agent fills the gap with skill startup and broad search. Spawn count, not prompt prose, is the 11–30 minute bill. Token burn is those startups plus pasting full node files into the next node.

## Process

1. Parent classifies. No classifier subagent.
2. Parent skips `explorer-second-brain` and `worker-second-brain-writeback` without a spawn when the vault index or `wiki/` pages are missing, or when the quality gate has not passed.
3. A follow-up that fixes the same behavior in the same chat adds one worker, then QA, then critic only if the run was hard, then the tail. It does not re-classify or re-explore.
4. Hard graphs have exactly one repo explorer. A request for "one subagent per section" is still that one explorer, with a read cap.
5. Default one implementation worker. Easy max 3, hard max 4. Split only when file sets are disjoint and each piece has its own acceptance check. A rename in one package is one worker.
6. Spawn prompt is the role file, the node record, repo root, run dir, and the `## Output` section of each dependency (400 words). No other role files, no skill bodies, no diffs.
7. Repo explorer records `AGENTS.md` paths and the verify command once. Later nodes use that brief. They do not re-run repo-navigation or load the code-standards index.
8. QA runs the planner's verify command only. Style and "was this the smallest change?" belong to the critic, and only the critic reads the diff for that judgment.

## Role contracts

Each role file has the same five sections: Goal, Inputs, Do, Output, Stop. Ceremony sections ("Why separate", "Phase 1: STARTUP") are gone. Id-specific work lives in its own file so a repo explorer is not pasted the vault procedure:

- `nodes/classifier.md` — parent-only rubric and `classifier.json` / `DAG.md` shape
- `nodes/explorer.md` — one repo brief, 12-read cap
- `nodes/explorer-second-brain.md` — vault query, five pages, no writes
- `nodes/planner.md` — smallest worker list; every worker note has files, behavior, verify command, standards files or `none`
- `nodes/worker.md` — edit only the listed files; run the verify command
- `nodes/worker-second-brain-writeback.md` — compile durable facts or skip
- `nodes/qa.md` — execute the verify command; verdict pass or fail
- `nodes/critic.md` — fail only for wrong behavior, a missing check, or extra scope; JSON route
- `nodes/promoter.md` — short user summary; PR only if asked
- `nodes/journaler.md` — performance journal from node outputs; no repo re-read

Critic and the first implementation worker stay on `cursor-grok-4.5-high`. Planner, promoter, and journaler move to `cursor-grok-4.6-medium` because their output is a fixed shape. The over-split plans were an instruction bug.

## Check

`ai_agents_tools/skills/agentic-harness/check_contracts.py` fails if a role file drops a required section, grows past 500 words, or regains "Why separate" / "Phase 1" / "STARTUP". It also checks the one-explorer rule, worker caps, inline classifier, and follow-up slice text.
