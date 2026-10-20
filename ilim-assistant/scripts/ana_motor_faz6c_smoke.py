#!/usr/bin/env python3
"""Smoke — Faz 6c tek yüz: sohbet → programlama görev handoff."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz6c_tek_yuz import (
        enrich_orchestra_faz6c,
        parse_programlama_gorev_intent,
    )
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    cases = [
        ("görev: projects/demo health endpointine version ekle pytest gecir", True, "faz85_fast"),
        ("şu projede app/main.py ve app/api.py refactor et", True, "agent_multi"),
        ("programlamada: iki dosyada auth ekle", True, "agent_multi"),
        ("projects/foo mega refactor 10+ dosya", True, "agent_mega"),
        ("nasılsın bugün", False, None),
        ("İslamın şartı kaçtır", False, None),
        ("kodu programlamaya gönder", False, None),  # yüzey gönder — tek sohbet yolu
    ]
    fails = 0
    for msg, want_hit, hint in cases:
        hit = parse_programlama_gorev_intent(msg)
        got = bool(hit)
        ok = got is want_hit
        if want_hit and hit:
            ok = ok and hit.get("motor") == "programlama" and bool(hit.get("task_line"))
            if hint:
                ok = ok and hit.get("path_hint") == hint
        print(
            f"  {'OK' if ok else 'FAIL'} {msg[:50]!r} hit={got} "
            f"hint={(hit or {}).get('path_hint')!r}"
        )
        if not ok:
            fails += 1

    orch = enrich_orchestra_faz6c(
        {},
        "görev: app/main.py ve app/api.py refactor et",
    )
    if not orch.get("quiet") or orch.get("ui_action", {}).get("motor") != "programlama":
        print("FAIL enrich", orch.get("ui_action"))
        fails += 1
    else:
        print("  OK enrich_orchestra_faz6c")

    orch2, patch = build_genel_orchestra_preview(
        "şu projede health endpointine version ekle pytest gecir"
    )
    ua = orch2.get("ui_action") or {}
    if ua.get("motor") != "programlama" or not ua.get("task_line"):
        print("FAIL preview", ua, patch)
        fails += 1
    else:
        print("  OK build_genel_orchestra_preview faz6c")

    if fails:
        print(f"FAIL {fails}")
        return 1
    print("PASS ana_motor_faz6c_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
