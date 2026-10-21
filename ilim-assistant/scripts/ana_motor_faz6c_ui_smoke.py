#!/usr/bin/env python3
"""Smoke — Faz 6c UI cilası: 3 cümle orchestra + app.js paintFaz6c bağları."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz6c_tek_yuz import enrich_orchestra_faz6c
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0
    cases = [
        ("görev: health endpointine version 2.0.0 ekle pytest geçir", "faz85_fast"),
        ("şu projede app/main.py ve app/api.py refactor et", "agent_multi"),
        ("programlamada: iki dosyada auth ekle", "agent_multi"),
    ]
    for msg, hint in cases:
        orch, patch = build_genel_orchestra_preview(msg)
        ua = orch.get("ui_action") or {}
        ok = (
            ua.get("type") == "surface_handoff"
            and ua.get("motor") == "programlama"
            and bool(ua.get("task_line"))
            and ua.get("path_hint") == hint
            and patch.get("faz6c")
        )
        print(
            f"  {'OK' if ok else 'FAIL'} {msg[:48]!r} "
            f"hint={ua.get('path_hint')!r} task={bool(ua.get('task_line'))}"
        )
        if not ok:
            fails += 1

    # enrich doğrudan
    orch2 = enrich_orchestra_faz6c({}, cases[0][0])
    ok2 = orch2.get("quiet") and (orch2.get("ui_action") or {}).get("task_line")
    print(f"  {'OK' if ok2 else 'FAIL'} enrich_orchestra_faz6c quiet+task")
    if not ok2:
        fails += 1

    app_js = REPO / "ruzgar-desktop" / "app.js"
    src = app_js.read_text(encoding="utf-8", errors="replace")
    ok3 = "function paintFaz6cTekYuzPanels" in src and "paintFaz6cTekYuzPanels(a)" in src
    ok3 = ok3 and "renderProgramlamaMegaWorkbench" in src and "renderProgramlamaHandoff" in src
    print(f"  {'OK' if ok3 else 'FAIL'} app.js paintFaz6c + handoff/mega boyama")
    if not ok3:
        fails += 1

    if fails:
        print(f"FAIL {fails}")
        return 1
    print("PASS ana_motor_faz6c_ui_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
