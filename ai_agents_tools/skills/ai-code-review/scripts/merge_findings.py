#!/usr/bin/env python3
"""Merge reviewer output into candidates, then apply verifier verdicts into the final report.

  merge_findings.py candidates [--verify-cap N]
      reads  .acr/findings/raw/<reviewer>.json   (JSON arrays returned by reviewers)
             .acr/deps.json                      (deterministic dependency facts)
      writes .acr/findings/candidates.json       (validated, deduplicated, with ids)
             .acr/findings/to_verify.json        (ids to send to verifiers, highest risk first)

  merge_findings.py report [--threshold N]
      reads  candidates.json + .acr/findings/verdicts/<id>.json
      writes .acr/report.json and .acr/report.md

Stdlib only. Validation follows references/findings.schema.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _acr_common import acr_dir, load_meta, repo_root, write_json  # noqa: E402

SEVERITIES = ["critical", "high", "medium", "low"]
SEV_RANK = {s: i for i, s in enumerate(SEVERITIES)}
STATUSES = {"unverified", "confirmed", "plausible", "rejected"}
REQUIRED = ["reviewer", "category", "severity", "confidence", "file", "line_start", "title", "mechanism", "evidence"]
CATEGORIES = {"intent", "scope", "logic", "edge-case", "error-handling", "concurrency", "test-integrity",
              "dependency", "api-misuse", "duplication", "blast-radius", "convention", "standards", "security"}


def tokens(s: str) -> set:
    return {t for t in re.findall(r"[a-z0-9_]{3,}", s.lower())}


def validate(f: dict, src: str) -> tuple:
    errs = [k for k in REQUIRED if f.get(k) in (None, "")]
    if errs:
        return None, f"{src}: missing {errs}"
    f = dict(f)
    f["severity"] = str(f["severity"]).lower()
    if f["severity"] not in SEV_RANK:
        return None, f"{src}: bad severity {f['severity']!r}"
    try:
        f["confidence"] = max(0, min(100, int(f["confidence"])))
        f["line_start"] = int(f["line_start"])
        f["line_end"] = int(f.get("line_end") or f["line_start"])
    except (TypeError, ValueError):
        return None, f"{src}: non-integer confidence/line"
    if f["category"] not in CATEGORIES:
        f.setdefault("notes", f"category '{f['category']}' normalised to 'logic'")
        f["category"] = "logic"
    f.setdefault("suggested_fix", "")
    f["status"] = f.get("status") if f.get("status") in STATUSES else "unverified"
    f.setdefault("verification", {"method": "none"})
    return f, None


def same_issue(a: dict, b: dict) -> bool:
    if a["file"] != b["file"]:
        return False
    if a["line_start"] > b["line_end"] + 3 or b["line_start"] > a["line_end"] + 3:
        return False
    ta, tb = tokens(a["title"] + " " + a["mechanism"]), tokens(b["title"] + " " + b["mechanism"])
    jacc = len(ta & tb) / max(1, len(ta | tb))
    return a["category"] == b["category"] or jacc >= 0.35


def deps_findings(out: Path) -> list:
    p = out / "deps.json"
    if not p.exists():
        return []
    deps = json.loads(p.read_text())
    res = []
    for d in deps.get("new_dependencies", []):
        reg = d.get("registry", {})
        if reg.get("status") == "missing":
            res.append({
                "reviewer": "deps-check", "category": "dependency", "severity": "high", "confidence": 97,
                "file": d["manifest"], "line_start": 1, "line_end": 1,
                "title": f"New dependency '{d['name']}' does not exist in the {d['ecosystem']} registry",
                "mechanism": "Install fails, or an attacker who registers this name gets code execution (slopsquatting).",
                "evidence": f"registry lookup {reg.get('url')} returned not found",
                "suggested_fix": "Replace with the intended real package, or remove the dependency.",
                "status": "confirmed",
                "verification": {"method": "registry", "result": "not found"},
            })
        elif reg.get("recently_published"):
            res.append({
                "reviewer": "deps-check", "category": "dependency", "severity": "medium", "confidence": 80,
                "file": d["manifest"], "line_start": 1, "line_end": 1,
                "title": f"New dependency '{d['name']}' was first published {reg.get('age_days')} days ago",
                "mechanism": "A very new package matching an AI-suggested name is a known slopsquatting pattern.",
                "evidence": f"first published {reg.get('first_published')}",
                "suggested_fix": "Confirm this is the intended package and its maintainer before keeping it.",
                "status": "plausible",
                "verification": {"method": "registry", "result": f"age {reg.get('age_days')} days"},
            })
    for u in deps.get("unresolved_imports", []):
        if u.get("env_gap"):
            continue
        occ = (u.get("occurrences") or [{}])[0]
        reg = (u.get("registry") or {}).get("status")
        missing = reg == "missing"
        res.append({
            "reviewer": "deps-check", "category": "dependency", "severity": "high",
            "confidence": 92 if missing else 75,
            "file": occ.get("file", "?"), "line_start": occ.get("line") or 1, "line_end": occ.get("line") or 1,
            "title": f"Import '{u['module']}' does not resolve" + (" and no package of that name exists" if missing else ""),
            "mechanism": "Module import fails at runtime (ImportError / module not found).",
            "evidence": f"{occ.get('text', '')} | registry: {reg}",
            "suggested_fix": "Use the real module name, or declare and install the dependency.",
            "status": "confirmed" if missing else "unverified",
            "verification": {"method": "registry", "result": "no package with this name in the registry"} if missing
                            else {"method": "none"},
        })
    return res


def cmd_candidates(args) -> int:
    root = repo_root()
    out = acr_dir(root)
    fdir = out / "findings"
    raw_dir = fdir / "raw"
    items, problems = [], []
    for p in sorted(raw_dir.glob("*.json")) if raw_dir.exists() else []:
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{p.name}: invalid JSON ({e})")
            continue
        if isinstance(data, dict):
            data = data.get("findings", [])
        for i, f in enumerate(data):
            v, err = validate(f, f"{p.name}[{i}]")
            if err:
                problems.append(err)
            else:
                items.append(v)
    for f in deps_findings(out):
        v, err = validate(f, "deps.json")
        if v:
            items.append(v)

    # dedupe: keep the strongest, remember who else flagged it
    items.sort(key=lambda f: (SEV_RANK[f["severity"]], -f["confidence"]))
    merged = []
    for f in items:
        dup = next((m for m in merged if same_issue(m, f)), None)
        if dup is None:
            f["also_flagged_by"] = []
            merged.append(f)
        elif f["reviewer"] != dup["reviewer"] and f["reviewer"] not in dup["also_flagged_by"]:
            dup["also_flagged_by"].append(f["reviewer"])
            dup["confidence"] = min(100, dup["confidence"] + 5)  # independent agreement
    for i, f in enumerate(merged, 1):
        f["id"] = f"F{i:03d}"

    to_verify = [f for f in merged if f["status"] == "unverified" and SEV_RANK[f["severity"]] <= SEV_RANK["medium"]]
    to_verify.sort(key=lambda f: (SEV_RANK[f["severity"]], -f["confidence"]))
    capped = to_verify[: args.verify_cap]
    write_json(fdir / "candidates.json", {"findings": merged, "problems": problems})
    write_json(fdir / "to_verify.json", {"ids": [f["id"] for f in capped],
                                         "over_cap": [f["id"] for f in to_verify[args.verify_cap:]]})
    print(f"candidates={len(merged)} (raw={len(items)}) to_verify={len(capped)} over_cap={len(to_verify) - len(capped)}")
    for f in merged:
        mark = "V" if f["id"] in {c["id"] for c in capped} else " "
        print(f"  {mark} {f['id']} {f['severity']:<8} {f['confidence']:>3} {f['status']:<10} "
              f"{f['file']}:{f['line_start']} [{f['reviewer']}] {f['title'][:80]}")
    for pr in problems:
        print(f"  ! {pr}")
    return 0


def cmd_report(args) -> int:
    root = repo_root()
    out = acr_dir(root)
    fdir = out / "findings"
    cand = json.loads((fdir / "candidates.json").read_text())
    findings = cand["findings"]
    vdir = fdir / "verdicts"
    verdicts = {}
    for p in vdir.glob("*.json") if vdir.exists() else []:
        try:
            v = json.loads(p.read_text())
            verdicts[v.get("id") or p.stem] = v
        except json.JSONDecodeError:
            pass

    for f in findings:
        v = verdicts.get(f["id"])
        if not v:
            continue
        if v.get("status") in STATUSES:
            f["status"] = v["status"]
        if isinstance(v.get("confidence"), (int, float)):
            f["confidence"] = max(0, min(100, int(v["confidence"])))
        if v.get("severity") in SEV_RANK:
            f["severity"] = v["severity"]
        f["verification"] = {k: v.get(k) for k in ("method", "repro", "result", "notes") if v.get(k)}

    th = args.threshold
    confirmed, questions, unverified, dropped = [], [], [], []
    for f in findings:
        st, c, sev = f["status"], f["confidence"], f["severity"]
        if st == "rejected":
            dropped.append((f, "rejected by verifier"))
        elif st == "confirmed" and c >= th:
            confirmed.append(f)
        elif st == "plausible" and c >= th:
            questions.append(f)
        elif st == "unverified" and (c >= 90 or (sev == "low" and c >= th)):
            unverified.append(f)
        else:
            dropped.append((f, f"below threshold ({c} < {th})" if c < th else f"status {st}"))
    key = lambda f: (SEV_RANK[f["severity"]], -f["confidence"])  # noqa: E731
    confirmed.sort(key=key)
    questions.sort(key=key)
    unverified.sort(key=key)

    meta = load_meta(root)
    tamper = json.loads((out / "test_tamper.json").read_text()) if (out / "test_tamper.json").exists() else {}
    checks = json.loads((out / "checks.json").read_text()) if (out / "checks.json").exists() else {}
    intent_src = ""
    if (out / "intent.md").exists():
        m = re.search(r"(?im)^##\s*Sources.*?\n(.+?)(?:\n##|\Z)", (out / "intent.md").read_text(), re.S)
        intent_src = m.group(1).strip() if m else ""

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "mode": "advisory",
        "base_ref": meta.get("base_ref"), "merge_base": meta.get("merge_base"), "head": meta.get("head"),
        "threshold": th,
        "summary": {"confirmed": len(confirmed), "questions": len(questions), "unverified": len(unverified),
                    "dropped": len(dropped), "by_severity": {s: sum(1 for f in confirmed + questions if f["severity"] == s)
                                                             for s in SEVERITIES}},
        "findings": confirmed, "questions": questions, "unverified": unverified,
        "dropped": [{"id": f["id"], "title": f["title"], "reason": r} for f, r in dropped],
        "signals": {
            "test_tamper_signals": tamper.get("signal_count", 0),
            "tool_diagnostics_on_changed_lines": len(checks.get("diagnostics_on_changed_lines", [])),
            "tools_ran": {k: v.get("exit_code") for k, v in (checks.get("tools") or {}).items()},
        },
        "intent_sources": intent_src,
    }
    write_json(out / "report.json", report)

    def block(f):
        loc = f"{f['file']}:{f['line_start']}" + (f"-{f['line_end']}" if f.get("line_end", f["line_start"]) != f["line_start"] else "")
        lines = [f"### {f['id']} · {f['severity'].upper()} · {f['title']}",
                 f"`{loc}` · confidence {f['confidence']} · {f['category']} · found by {f['reviewer']}"
                 + (f" (+{', '.join(f['also_flagged_by'])})" if f.get("also_flagged_by") else ""),
                 "", f"**Mechanism:** {f['mechanism']}", "", f"**Evidence:** {f['evidence']}"]
        ver = f.get("verification") or {}
        if ver.get("method") and ver.get("method") != "none":
            detail = ver.get("result") or ver.get("notes") or ""
            lines += ["", f"**Verification ({ver.get('method')}):** {detail}" if detail else f"**Verification:** {ver.get('method')}"]
            if ver.get("repro"):
                lines += ["", "```", str(ver["repro"]).strip()[:1500], "```"]
        if f.get("suggested_fix"):
            lines += ["", f"**Suggested fix:** {f['suggested_fix']}"]
        return "\n".join(lines) + "\n"

    s = report["summary"]
    md = [f"# AI code review (advisory)",
          f"Base `{meta.get('base_ref')}` @ `{(meta.get('merge_base') or '')[:10]}` → `{(meta.get('head') or '')[:10]}` · "
          f"{meta['totals']['files']} files, +{meta['totals']['added']} −{meta['totals']['deleted']} · threshold {th}",
          "",
          f"**{s['confirmed']} confirmed · {s['questions']} questions · {s['unverified']} unverified · {s['dropped']} dropped**",
          ""]
    if intent_src:
        md += [f"Intent sources: {intent_src}", ""]
    md += ["## Confirmed findings", ""] + ([block(f) for f in confirmed] or ["None.", ""])
    md += ["## Questions (plausible, not reproduced)", ""] + ([block(f) for f in questions] or ["None.", ""])
    if unverified:
        md += ["## Unverified", ""] + [block(f) for f in unverified]
    md += ["## Signals", "",
           f"- Test-integrity signals from scripts: {report['signals']['test_tamper_signals']}",
           f"- Tool diagnostics on changed lines: {report['signals']['tool_diagnostics_on_changed_lines']}",
           f"- Tools run: {report['signals']['tools_ran'] or 'none'}", ""]
    if dropped:
        md += ["<details><summary>Dropped</summary>", ""] + [f"- {f['id']} {f['title']} — {r}" for f, r in dropped] + ["", "</details>"]
    (out / "report.md").write_text("\n".join(md) + "\n")
    print(f"report: {s['confirmed']} confirmed, {s['questions']} questions, {s['unverified']} unverified, "
          f"{s['dropped']} dropped -> .acr/report.md")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("candidates")
    c.add_argument("--verify-cap", type=int, default=12)
    r = sub.add_parser("report")
    r.add_argument("--threshold", type=int, default=80)
    args = ap.parse_args()
    return cmd_candidates(args) if args.cmd == "candidates" else cmd_report(args)


if __name__ == "__main__":
    sys.exit(main())
