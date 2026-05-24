#!/usr/bin/env python3
"""Programlama motoru duman testi (Faz 8–11) — Ollama/API gerekmez.

Çalıştırma (ilim-assistant kökünde):
  python scripts/programlama_smoke.py

Canlı API (sunucu ayakta):
  python scripts/programlama_smoke.py --live http://127.0.0.1:8777
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent


def _ok(label: str) -> None:
    print(f"  OK  {label}")


def _fail(label: str, detail: str = "") -> None:
    msg = f"  FAIL {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def run_offline() -> int:
    fails = 0
    print("=== Faz 6 — şablonlar ===")
    from ilim_assistant.motorlar.programlama_faz6 import list_templates

    ids = {t["id"] for t in list_templates()}
    for tid in ("fastapi_api", "static_site", "react_vite", "cli_python"):
        if tid in ids:
            _ok(f"template {tid}")
        else:
            _fail(f"template {tid}")
            fails += 1

    print("=== Faz 8 — odak ===")
    from ilim_assistant.motorlar.programlama_faz8 import pick_focus_rel

    fr = pick_focus_rel(
        {
            "ok": True,
            "template_id": "react_vite",
            "base_dir": "projects/demo",
            "written": ["projects/demo/src/App.jsx"],
        }
    )
    if fr and fr.endswith("App.jsx"):
        _ok(f"focus {fr}")
    else:
        _fail("focus react", str(fr))
        fails += 1

    print("=== Faz 10 — delege & indeks ===")
    from ilim_assistant.motorlar.programlama_faz10 import (
        build_workspace_index,
        should_delegate_to_programlama,
    )

    if should_delegate_to_programlama("projects/foo/main.py duzelt", "genel"):
        _ok("delegate genel -> programlama")
    else:
        _fail("delegate")
        fails += 1
    idx = build_workspace_index(WORKSPACE, scope_rel="projects")
    if idx and "projects" in idx:
        _ok("workspace index")
    else:
        _fail("workspace index")
        fails += 1

    print("=== Faz 11 — orkestra ===")
    from ilim_assistant.motorlar.programlama_faz11 import build_programlama_orchestra_steps

    steps = build_programlama_orchestra_steps(
        "test",
        WORKSPACE,
        phase="done",
        patch_meta={"action": "applied", "applied": ["projects/x/a.py"]},
    )
    if len(steps) >= 5 and steps[0].get("id") == "plan":
        _ok(f"orchestra steps ({len(steps)})")
    else:
        _fail("orchestra steps", str(len(steps)))
        fails += 1

    print("=== Faz 12 — diff onizleme ===")
    from ilim_assistant.motorlar.programlama_faz10 import preview_writes, unified_diff_text

    diff = unified_diff_text("a=1\n", "a=2\nb=3\n", "test.py")
    if "+b=3" in diff or "b=3" in diff:
        _ok("unified_diff")
    else:
        _fail("unified_diff", diff[:80])
        fails += 1
    prev = preview_writes("@@write z.py\n```\nx=1\n```", WORKSPACE)
    if prev.get("items") and prev["items"][0].get("diff"):
        _ok("preview_writes diff")
    else:
        _fail("preview_writes diff")
        fails += 1

    print("=== Motor — rezerve komut ===")
    from ilim_assistant.motorlar.programlama_motoru import is_programlama_reserved_command

    for msg in ("patch onayla", "workspace indeks", "sablon listele"):
        if is_programlama_reserved_command(msg):
            _ok(f"reserved: {msg[:24]}")
        else:
            _fail(f"reserved: {msg}")
            fails += 1

    return fails


def run_live(base: str) -> int:
    fails = 0
    base = base.rstrip("/")
    print(f"=== Canlı API {base} ===")

    def get(path: str) -> dict:
        with urllib.request.urlopen(base + path, timeout=30) as r:
            return json.loads(r.read())

    enc = urllib.parse.quote(str(WORKSPACE), safe="")
    try:
        h = get("/api/health")
        rev = str((h.get("build") or {}).get("rev") or "")
        if "faz11" in rev or "faz10" in rev:
            _ok(f"build.rev={rev}")
        else:
            _fail("build.rev", rev)
            fails += 1
    except Exception as e:
        _fail("health", str(e)[:120])
        return fails + 1

    try:
        t = get("/api/programlama/templates")
        ids = {x["id"] for x in (t.get("templates") or [])}
        if "static_site" in ids and "react_vite" in ids:
            _ok("templates API")
        else:
            _fail("templates API", str(ids))
            fails += 1
    except Exception as e:
        _fail("templates", str(e)[:120])
        fails += 1

    try:
        w = get(f"/api/programlama/workspace-index?workspace_root={enc}")
        if w.get("ok") and w.get("index"):
            _ok("workspace-index")
        else:
            _fail("workspace-index")
            fails += 1
    except Exception as e:
        _fail("workspace-index", str(e)[:120])
        fails += 1

    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", metavar="URL", help="Örn. http://127.0.0.1:8777")
    args = ap.parse_args()
    fails = run_offline()
    if args.live:
        fails += run_live(args.live)
    print()
    if fails:
        print(f"SONUÇ: {fails} hata")
        return 1
    print("SONUÇ: tüm programlama smoke testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
