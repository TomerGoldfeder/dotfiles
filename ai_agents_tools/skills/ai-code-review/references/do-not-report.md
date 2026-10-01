# Do not report

These are false positives for this skill. Reviewers skip them; verifiers reject them.

## General
- Problems on lines the change did not add, unless the change newly calls into them or makes them reachable.
- Formatting, naming, import order, line length, docstring style.
- Anything listed in `checks.json` → `diagnostics_on_changed_lines` (a tool already reported it).
- Issues silenced in the code (`# noqa`, `# type: ignore`, `eslint-disable`, `//nolint`) — unless the silencing comment was **added by this change**; then it is reportable.
- "Consider adding error handling / validation / logging / a try-except" without a concrete input that fails.
- Speculative performance concerns without a realistic size or hot path.
- General "missing tests" or coverage gaps. (Exceptions belong to `acr-test-integrity`: tests removed/weakened, or the task explicitly asked for tests.)
- Refactoring suggestions for code the change did not need to touch.
- Typos in comments or docs.
- Behaviour that is correct but differs from how the reviewer would have written it.
- Things the intent explicitly asked for, even if unusual.

## Project-specific
<!-- Append recurring false positives here, one line each, with a short reason. Example:
- `settings.DEBUG` checks in `app/dev_only/` — intentional, dev-only module.
-->
