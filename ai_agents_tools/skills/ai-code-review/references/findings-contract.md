# Findings contract

Reviewers return a JSON array of finding objects. The orchestrator adds `id`, `status`, `verification` and `also_flagged_by`; reviewers never set them.

| Field | Type | Rule |
|---|---|---|
| `reviewer` | string | Your subagent name without the `acr-` prefix: `intent`, `correctness`, `test-integrity`, `codebase-fit`, `standards`, `security`. |
| `category` | enum | `intent`, `scope`, `logic`, `edge-case`, `error-handling`, `concurrency`, `test-integrity`, `dependency`, `api-misuse`, `duplication`, `blast-radius`, `convention`, `standards`, `security`. |
| `severity` | enum | `critical`, `high`, `medium`, `low` (rubric in reviewer-common.md). |
| `confidence` | int 0-100 | Rubric in reviewer-common.md. |
| `file` | string | Repo-relative path of the line to look at. |
| `line_start`, `line_end` | int | Line numbers in the **new** file (the `+` side). For a deleted file or removed lines, use the old line numbers and say so in `evidence`. |
| `title` | string | ≤ 90 chars, states the problem, not the fix. |
| `mechanism` | string | One sentence: trigger → wrong outcome. |
| `evidence` | string | Short code quote, quoted rule, intent line, or tool output that supports it. Name any unverified assumption. |
| `suggested_fix` | string | One or two sentences. May be empty. |

Example:
```json
[
  {
    "reviewer": "correctness",
    "category": "edge-case",
    "severity": "high",
    "confidence": 88,
    "file": "src/billing/invoice.py",
    "line_start": 142,
    "line_end": 147,
    "title": "Empty line_items list raises ZeroDivisionError in average_price",
    "mechanism": "An invoice with no line items (allowed by InvoiceSchema) reaches sum(...)/len(items) with len 0 and crashes.",
    "evidence": "L145: `return sum(p.price for p in items) / len(items)`; InvoiceSchema.line_items has min_length=0 (schemas.py:31).",
    "suggested_fix": "Return Decimal(0) (or None) when items is empty, matching total_price()."
  }
]
```

## Verifier verdict (returned by `acr-verifier`)
```json
{
  "id": "F003",
  "status": "confirmed",
  "confidence": 95,
  "severity": "high",
  "method": "test",
  "repro": "<test code or command that demonstrates it>",
  "result": "<≤20 lines of the relevant output>",
  "notes": "<why the status was chosen; what was assumed>"
}
```
- `status`: `confirmed` (reproduced, or deterministic evidence), `plausible` (premise holds, not reproduced within budget), `rejected` (premise false, behaviour is correct, or on the do-not-report list).
- `method`: `test`, `command`, `trace` (code reading only), `registry`.
- `severity` / `confidence`: may be adjusted up or down from the candidate.
