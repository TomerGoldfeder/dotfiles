---
name: performance-journaler
description: Use when a development thread ends or reaches a milestone and you want a persistent, project-based journal entry for future performance review and STAR writeups.
---

# Performance Journaler

## Overview
Create a concise journal entry from the current thread and append it to a per-project text file.

Output path format:
`$HOME/.jurnal_tomer/<project>.txt` (same as `~/.jurnal_tomer/<project>.txt`)

This skill is optimized for future performance reviews and STAR drafting.

## Required Extraction
From the thread, extract:
1. `project` - the project/repo/task area you worked on
2. `category` - classify work using this fixed list only: `bug`, `feature`, `initial_project`, `refactor`, `investigation`
3. `category_confidence` - numeric confidence in the chosen category within `[0.0, 1.0]`
4. `what_was_done` - concrete implementation/debug/research actions completed
5. `what_it_solves` - user/business/engineering problem resolved

## Entry Format
Append entries in this exact structure:

```
=== ENTRY START ===
date: <YYYY-MM-DD>
project: <project>
category: <category>
category_confidence: <0.00-1.00>
thread_summary: <1-2 lines>
what_was_done:
- <bullet>
- <bullet>
what_it_solves:
- <bullet>
- <bullet>
star_hints:
- situation: <context>
- task: <responsibility>
- action: <key actions>
- result: <impact or expected impact>
=== ENTRY END ===
```

If no entry is persisted, output this exact structure:

```
status: no-entry
project: <project or unknown>
category: <best_candidate or none>
category_confidence: <0.00-1.00>
reason: <why thread does not naturally fit or is below threshold 0.1>
```

## Workflow
1. Read the current conversation/thread context.
2. Infer `project` from explicit mentions (repo names, directory names, ticket context).
3. Infer `category` from dominant intent of the thread and compute `category_confidence` in `[0.0, 1.0]`.
4. If there is no good category match or `category_confidence < 0.1`, skip persistence and return a short "no-entry" note with reason and confidence.
5. Summarize `what_was_done` and `what_it_solves` as factual bullets.
6. Build STAR hints from the same evidence. If measurable impact exists, include it.
7. Ensure target directory exists:
   - `mkdir -p "$HOME/.jurnal_tomer"`
8. Only if `category_confidence >= 0.1` and category is a good natural match in the fixed list, append entry to:
   - `"$HOME/.jurnal_tomer/<project>.txt"`
9. Return a short confirmation with:
   - target file path
   - inferred category
   - category confidence
   - first line of summary

## Decision Rules
- If multiple projects are present, choose the one with most concrete implementation actions.
- If confidence in project is low, ask exactly one clarification question before writing.
- Do not overfit category selection. If no category is a good natural match, do not write an entry.
- Never force a thread into a category just to create an entry.
- Use `0.1` as the minimum category confidence threshold for persistence.
- Never overwrite existing journal content; append only.
- Use the project name as-is for the output filename (no slugification or normalization).
- Persist only when category is in the fixed list and `category_confidence >= 0.1`.
- Keep tone factual and achievement-oriented (avoid fluff).
- Do not include secrets, tokens, passwords, or personal sensitive data.

## Quality Bar
- Entry is specific enough to reconstruct a STAR response later.
- Actions are verbs + artifacts (for example: "added validation in nimbus.py").
- Problem/impact is explicit, not implied.
- No duplicate bullets.

## Example Prompt
- "Use performance-journaler for this thread."
- "Journal this work for my performance review notes."
