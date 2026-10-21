#!/usr/bin/env python3
"""Faz88 E1 — yüzey → görev satırı köprüsü smoke."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
WORKSPACE = _ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_yuzey_bridge import (
        build_surface_handoff_payload,
        extract_surface_goal,
        build_surface_task_line,
    )

    sample = (
        "# Yüzey → Programlama (Faz85 güvenli yol; serbest çalıştırma kapalı)\n"
        "# Kaynak yetenek: belge\n\n"
        "health endpointine version ekle pytest geçir\n"
    )
    goal = extract_surface_goal(sample)
    if "version" not in goal.lower() or "health" not in goal.lower():
        print("FAIL goal extract", goal)
        return 1

    explicit = extract_surface_goal("# başlık\n\ngörev: benim-api auth ekle\n")
    if "auth" not in explicit.lower():
        print("FAIL explicit görev", explicit)
        return 1

    complex_goal = extract_surface_goal(
        "# Yüzeyden görev\n\nlogin modülünü servislere refactor et ve pytest geçir\n"
    )
    if "refactor" not in complex_goal.lower():
        print("FAIL complex goal", complex_goal)
        return 1

    line = build_surface_task_line(sample, WORKSPACE)
    if not line.lower().startswith(("görev:", "gorev:")):
        print("FAIL task_line prefix", line)
        return 1

    payload = build_surface_handoff_payload(sample, WORKSPACE)
    if not payload.get("ok") or not payload.get("task_line"):
        print("FAIL payload", payload)
        return 1
    wb = payload.get("handoff_workbench") or {}
    if not wb.get("ok"):
        print("FAIL nested workbench", wb)
        return 1
    _agentish = ("agent", "agent_multi", "agent_mega")
    if payload.get("path_hint") not in ("faz85_fast", *_agentish):
        print("FAIL path_hint", payload.get("path_hint"))
        return 1

    complex_payload = build_surface_handoff_payload(
        "# Yüzey\n\nlogin modülünü servislere refactor et\n",
        WORKSPACE,
    )
    if complex_payload.get("path_hint") not in _agentish:
        print("FAIL complex should be agent*", complex_payload.get("path_hint"))
        return 1

    # D: Belge / Tablo → programlama
    belge = (
        "# Yüzeyden görev (çalıştırma kapalı — güvenli atölye)\n"
        "# Kaynak yetenek: belge\n\n"
        "görev: health endpointine version 2.0.0 ekle pytest geçir\n"
    )
    belge_p = build_surface_handoff_payload(belge, WORKSPACE)
    if "version" not in (belge_p.get("goal") or "").lower():
        print("FAIL belge goal", belge_p.get("goal"))
        return 1
    bt = (belge_p.get("task_line") or "").lower()
    if not bt.startswith(("görev:", "gorev:")):
        print("FAIL belge task_line", belge_p.get("task_line"))
        return 1
    if "smoke-" in bt or "e2-bat-" in bt:
        print("FAIL belge got ephemeral project slug", belge_p.get("task_line"))
        return 1

    tablo = (
        "# Kaynak yetenek: tablo\n"
        "A1\thealth endpointine version ekle pytest geçir\n"
        "B1\t2.0.0\n"
    )
    tablo_p = build_surface_handoff_payload(tablo, WORKSPACE)
    tg = (tablo_p.get("goal") or "").lower()
    if "health" not in tg and "version" not in tg and "pytest" not in tg:
        print("FAIL tablo goal", tablo_p.get("goal"))
        return 1
    if not tablo_p.get("ok"):
        print("FAIL tablo payload", tablo_p)
        return 1
    tt = (tablo_p.get("task_line") or "").lower()
    if "smoke-" in tt or "e2-bat-" in tt:
        print("FAIL tablo got ephemeral project slug", tablo_p.get("task_line"))
        return 1

    # D+: Çizim / Sunum → programlama
    sunum = (
        "# Kaynak yetenek: sunum\n"
        "Slayt 1: Plan\n"
        "görev: health endpointine version 2.0.0 ekle pytest geçir\n"
    )
    sunum_p = build_surface_handoff_payload(sunum, WORKSPACE)
    if "version" not in (sunum_p.get("goal") or "").lower():
        print("FAIL sunum goal", sunum_p.get("goal"))
        return 1
    if not (sunum_p.get("task_line") or "").lower().startswith(("görev:", "gorev:")):
        print("FAIL sunum task_line", sunum_p.get("task_line"))
        return 1

    cizim = (
        "# Kaynak yetenek: cizim\n"
        "çizim durumu: dolu (kalem izi var)\n"
    )
    cizim_p = build_surface_handoff_payload(cizim, WORKSPACE)
    cg = (cizim_p.get("goal") or "").lower()
    if "çizim" not in cg and "cizim" not in cg and "özet" not in cg and "ozet" not in cg:
        print("FAIL cizim goal", cizim_p.get("goal"))
        return 1
    if not cizim_p.get("ok"):
        print("FAIL cizim payload", cizim_p)
        return 1

    print(
        f"OK yuzey-bridge — goal={goal[:40]!r} "
        f"path={payload.get('path_hint')} "
        f"complex={complex_payload.get('path_hint')} "
        f"belge={belge_p.get('path_hint')} tablo={tablo_p.get('path_hint')} "
        f"sunum={sunum_p.get('path_hint')} cizim={cizim_p.get('path_hint')} "
        f"task={belge_p.get('task_line')!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
