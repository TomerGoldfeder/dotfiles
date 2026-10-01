#!/usr/bin/env python3
"""Check that dependencies and imports introduced by the change actually exist.

1. New dependencies in manifests (requirements*.txt/.in, pyproject.toml, package.json,
   go.mod, Cargo.toml): old vs new manifest content -> names that were added ->
   registry lookup (exists / missing / unknown, plus first-publish age).
2. New imports in added lines (Python, JS/TS) that resolve neither locally, nor in the
   project environment, nor as stdlib/builtins -> "unresolved" (+ registry lookup for
   the same name, so a hallucinated package shows as missing).

Registry endpoints are templates with {name}; override them for an internal mirror:
  ACR_PYPI_URL   default https://pypi.org/pypi/{name}/json
  ACR_PYPI_SIMPLE_URL  optional PEP 503 simple page, e.g. https://mirror/simple/{name}/
  ACR_NPM_URL    default https://registry.npmjs.org/{name}
  ACR_GO_URL     default https://proxy.golang.org/{name}/@v/list
  ACR_CRATES_URL default https://crates.io/api/v1/crates/{name}

Writes .acr/deps.json.
Usage: deps_check.py [--offline] [--python PATH] [--timeout SECONDS]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _acr_common import acr_dir, added_lines, file_at, load_meta, load_patch, repo_root, run, write_json  # noqa: E402

try:
    import tomllib  # type: ignore
except ImportError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None

NODE_BUILTINS = set("""assert async_hooks buffer child_process cluster console constants crypto dgram diagnostics_channel
dns domain events fs http http2 https inspector module net os path perf_hooks process punycode querystring readline repl
stream string_decoder sys timers tls trace_events tty url util v8 vm wasi worker_threads zlib test""".split())

REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def norm_py(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# ---------- manifest parsing ----------

def deps_requirements(text: str) -> set:
    out = set()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http:", "https:", "file:", ".")):
            continue
        m = REQ_NAME.match(line)
        if m:
            out.add(norm_py(m.group(1)))
    return out


def _pep508_names(items) -> set:
    out = set()
    for it in items or []:
        if isinstance(it, str):
            m = REQ_NAME.match(it)
            if m:
                out.add(norm_py(m.group(1)))
    return out


def deps_pyproject(text: str) -> set:
    if tomllib is None:
        # fallback: quoted PEP 508 strings anywhere
        return {norm_py(m.group(1)) for m in re.finditer(r'^\s*"([A-Za-z0-9][A-Za-z0-9._-]*)[^"]*",?\s*$', text, re.M)}
    try:
        data = tomllib.loads(text)
    except Exception:
        return set()
    out = set()
    proj = data.get("project", {})
    out |= _pep508_names(proj.get("dependencies"))
    for v in (proj.get("optional-dependencies") or {}).values():
        out |= _pep508_names(v)
    for v in (data.get("dependency-groups") or {}).values():
        out |= _pep508_names([x for x in v if isinstance(x, str)])
    poetry = data.get("tool", {}).get("poetry", {})
    for key in ("dependencies", "dev-dependencies"):
        out |= {norm_py(k) for k in (poetry.get(key) or {}) if k.lower() != "python"}
    for grp in (poetry.get("group") or {}).values():
        out |= {norm_py(k) for k in (grp.get("dependencies") or {})}
    return out


def deps_package_json(text: str) -> set:
    try:
        data = json.loads(text)
    except Exception:
        return set()
    out = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        out |= set((data.get(key) or {}).keys())
    return out


def deps_go_mod(text: str) -> set:
    out, in_block = set(), False
    for line in text.splitlines():
        s = line.split("//", 1)[0].strip()
        if s.startswith("require ("):
            in_block = True
            continue
        if in_block and s == ")":
            in_block = False
            continue
        if in_block and s:
            out.add(s.split()[0])
        elif s.startswith("require "):
            parts = s.split()
            if len(parts) >= 2:
                out.add(parts[1])
    return out


def deps_cargo(text: str) -> set:
    if tomllib is None:
        return set()
    try:
        data = tomllib.loads(text)
    except Exception:
        return set()
    out = set()
    for key in ("dependencies", "dev-dependencies", "build-dependencies"):
        out |= set((data.get(key) or {}).keys())
    for tgt in (data.get("target") or {}).values():
        for key in ("dependencies", "dev-dependencies"):
            out |= set((tgt.get(key) or {}).keys())
    return out


MANIFESTS = [
    (re.compile(r"(^|/)requirements[^/]*\.(txt|in)$"), "pypi", deps_requirements),
    (re.compile(r"(^|/)pyproject\.toml$"), "pypi", deps_pyproject),
    (re.compile(r"(^|/)package\.json$"), "npm", deps_package_json),
    (re.compile(r"(^|/)go\.mod$"), "go", deps_go_mod),
    (re.compile(r"(^|/)Cargo\.toml$"), "crates", deps_cargo),
]


# ---------- registry lookups ----------

def _get(url: str, timeout: float):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-code-review-deps-check/1.0",
                                               "Accept": "application/json, text/html;q=0.9, */*;q=0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (fixed registries / user-configured mirrors)
        return r.status, r.read()


def _age_days(iso: str | None):
    if not iso:
        return None
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        return (dt.datetime.now(dt.timezone.utc) - t).days
    except ValueError:
        return None


def registry_check(eco: str, name: str, timeout: float, cache: dict) -> dict:
    key = (eco, name)
    if key in cache:
        return cache[key]
    res = {"status": "unknown", "first_published": None, "age_days": None, "url": None, "error": None}
    try:
        if eco == "pypi":
            url = os.environ.get("ACR_PYPI_URL", "https://pypi.org/pypi/{name}/json").format(name=name)
            res["url"] = url
            try:
                _, body = _get(url, timeout)
                data = json.loads(body)
                times = [f.get("upload_time_iso_8601") or f.get("upload_time")
                         for files in (data.get("releases") or {}).values() for f in files]
                times = sorted(t for t in times if t)
                res.update(status="exists", first_published=times[0] if times else None)
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
                simple = os.environ.get("ACR_PYPI_SIMPLE_URL")
                if simple:
                    try:
                        _get(simple.format(name=name), timeout)
                        res["status"] = "exists"
                    except urllib.error.HTTPError as e2:
                        res["status"] = "missing" if e2.code == 404 else "unknown"
                else:
                    res["status"] = "missing"
        elif eco == "npm":
            enc = name.replace("/", "%2F") if name.startswith("@") else urllib.parse.quote(name)
            url = os.environ.get("ACR_NPM_URL", "https://registry.npmjs.org/{name}").format(name=enc)
            res["url"] = url
            _, body = _get(url, timeout)
            data = json.loads(body)
            res.update(status="exists", first_published=(data.get("time") or {}).get("created"))
        elif eco == "go":
            esc = re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), name)
            url = os.environ.get("ACR_GO_URL", "https://proxy.golang.org/{name}/@v/list").format(name=esc)
            res["url"] = url
            _get(url, timeout)
            res["status"] = "exists"
        elif eco == "crates":
            url = os.environ.get("ACR_CRATES_URL", "https://crates.io/api/v1/crates/{name}").format(name=name)
            res["url"] = url
            _, body = _get(url, timeout)
            data = json.loads(body)
            res.update(status="exists", first_published=(data.get("crate") or {}).get("created_at"))
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            res["status"] = "missing"
        else:
            res["error"] = f"HTTP {e.code}"
    except Exception as e:  # network down, proxy, TLS, parse error
        res["error"] = f"{type(e).__name__}: {e}"[:200]
    res["age_days"] = _age_days(res["first_published"])
    if res["status"] == "exists" and res["age_days"] is not None and res["age_days"] < 30:
        res["recently_published"] = True
    cache[key] = res
    return res


# ---------- import resolution ----------

PY_IMPORT = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*(?:\s+as\s+\w+)?(?:\s*,\s*[A-Za-z_][\w.]*(?:\s+as\s+\w+)?)*)")
PY_FROM = re.compile(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\b")
JS_IMPORT = re.compile(r"""(?:\bfrom\s+|\bimport\s*\(\s*|\brequire\s*\(\s*|^\s*import\s+)['"]([^'"]+)['"]""")


def pick_python(root: Path, explicit: str | None) -> tuple:
    if explicit:
        return explicit, "explicit"
    for cand in (root / ".venv/bin/python", root / "venv/bin/python",
                 Path(os.environ.get("VIRTUAL_ENV", "/nonexistent")) / "bin/python"):
        if cand.exists():
            return str(cand), "project-venv"
    return sys.executable, "fallback-current-interpreter"


def local_python_tops(root: Path) -> set:
    tops = set()
    files = run(["git", "ls-files", "-co", "--exclude-standard", "*.py"], cwd=root).stdout.splitlines()
    for p in files:
        parts = Path(p).parts
        if not parts:
            continue
        tops.add(Path(parts[0]).stem)
        if parts[0] in ("src", "lib", "python") and len(parts) > 1:
            tops.add(Path(parts[1]).stem)
        # dirs containing the file are importable when tests run from subdirs
        for part in parts[:-1]:
            tops.add(part)
        tops.add(Path(p).stem)
    return tops


def resolve_python(py: str, names: list) -> dict:
    code = ("import importlib.util, json, sys\n"
            "names = json.loads(sys.argv[1])\n"
            "std = set(getattr(sys, 'stdlib_module_names', ())) | set(sys.builtin_module_names)\n"
            "out = {}\n"
            "for n in names:\n"
            "    try:\n"
            "        out[n] = n in std or importlib.util.find_spec(n) is not None\n"
            "    except Exception:\n"
            "        out[n] = False\n"
            "print(json.dumps(out))\n")
    r = run([py, "-c", code, json.dumps(names)])
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="skip registry lookups")
    ap.add_argument("--python", help="project interpreter used to resolve imports")
    ap.add_argument("--timeout", type=float, default=6.0)
    args = ap.parse_args()

    root = repo_root()
    out = acr_dir(root)
    meta = load_meta(root)
    files = load_patch(root)
    merge_base = meta.get("merge_base")
    cache: dict = {}
    errors = []

    # 1. manifests
    new_deps, all_new_npm = [], set()
    for f in files:
        path = f["path"]
        if not path or f["status"] == "deleted":
            continue
        for rx, eco, parser in MANIFESTS:
            if rx.search(path):
                old = file_at(root, merge_base, path) if merge_base else None
                new = file_at(root, None, path)
                added = sorted(parser(new or "") - parser(old or ""))
                if eco == "npm":
                    all_new_npm |= set(added)
                for name in added:
                    entry = {"ecosystem": eco, "name": name, "manifest": path}
                    entry["registry"] = {"status": "skipped"} if args.offline else registry_check(eco, name, args.timeout, cache)
                    new_deps.append(entry)

    # 2. imports
    py_path, py_source = pick_python(root, args.python)
    py_local = None
    py_candidates = {}  # top -> [(file, line)]
    js_candidates = {}
    for f in files:
        path = f["path"]
        if not path or f["status"] == "deleted" or f["binary"]:
            continue
        if path.endswith(".py"):
            for ln in added_lines(f):
                t = ln["text"]
                mods = []
                m = PY_FROM.match(t)
                if m:
                    mods = [m.group(1)]
                else:
                    m = PY_IMPORT.match(t)
                    if m:
                        mods = [x.strip().split()[0] for x in m.group(1).split(",")]
                for mod in mods:
                    top = mod.split(".")[0]
                    if top and top != "__future__":
                        py_candidates.setdefault(top, []).append({"file": path, "line": ln["new"], "text": t.strip()})
        elif re.search(r"\.[cm]?[jt]sx?$", path):
            for ln in added_lines(f):
                for spec in JS_IMPORT.findall(ln["text"]):
                    if spec.startswith((".", "/", "node:", "~", "#", "@/")) or spec in NODE_BUILTINS:
                        continue
                    pkg = "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
                    if pkg.split("/")[0] in NODE_BUILTINS:
                        continue
                    js_candidates.setdefault(pkg, []).append({"file": path, "line": ln["new"], "text": ln["text"].strip()})

    unresolved = []
    if py_candidates:
        py_local = local_python_tops(root)
        names = sorted(n for n in py_candidates if n not in py_local)
        found = resolve_python(py_path, names) if names else {}
        if names and not found:
            errors.append(f"could not run interpreter {py_path} to resolve imports")
        for n in names:
            if found.get(n, True):
                continue
            entry = {"lang": "python", "module": n, "occurrences": py_candidates[n][:5]}
            entry["registry"] = {"status": "skipped"} if args.offline else registry_check("pypi", norm_py(n), args.timeout, cache)
            # a real package that only fails to import because we aren't in the project's env is not a finding
            # (outside the project env we only trust a definite "missing" from the registry)
            entry["env_gap"] = py_source.startswith("fallback") and entry["registry"].get("status") != "missing"
            unresolved.append(entry)

    if js_candidates:
        declared = set()
        for pj in run(["git", "ls-files", "-co", "--exclude-standard", "package.json", "*/package.json"], cwd=root).stdout.splitlines():
            declared |= deps_package_json(file_at(root, None, pj) or "")
        for pkg, occ in sorted(js_candidates.items()):
            if pkg in declared or (root / "node_modules" / pkg).exists():
                continue
            entry = {"lang": "js", "module": pkg, "occurrences": occ[:5], "note": "not declared in any package.json",
                     "env_gap": False}
            entry["registry"] = {"status": "skipped"} if args.offline else registry_check("npm", pkg, args.timeout, cache)
            unresolved.append(entry)

    res = {
        "offline": args.offline,
        "python_interpreter": {"path": py_path, "source": py_source},
        "new_dependencies": new_deps,
        "unresolved_imports": unresolved,
        "errors": errors,
        "summary": {
            "new_dependencies": len(new_deps),
            "missing_in_registry": sum(1 for d in new_deps if d["registry"].get("status") == "missing"),
            "recently_published": sum(1 for d in new_deps if d["registry"].get("recently_published")),
            "unresolved_imports": sum(1 for u in unresolved if not u.get("env_gap")),
            "env_gaps": sum(1 for u in unresolved if u.get("env_gap")),
        },
    }
    write_json(out / "deps.json", res)
    s = res["summary"]
    print(f"new deps={s['new_dependencies']} missing={s['missing_in_registry']} "
          f"recent(<30d)={s['recently_published']} unresolved imports={s['unresolved_imports']} "
          f"(env gaps ignored={s['env_gaps']}) "
          f"interpreter={py_source}")
    if py_source.startswith("fallback") and py_candidates:
        print("NOTE: no project venv found; pass --python <project interpreter> for accurate import resolution.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
