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
    if payload.get("path_hint") not in ("faz85_fast", "agent"):
        print("FAIL path_hint", payload.get("path_hint"))
        return 1

    complex_payload = build_surface_handoff_payload(
        "# Yüzey\n\nlogin modülünü servislere refactor et\n",
        WORKSPACE,
    )
    if complex_payload.get("path_hint") != "agent":
        print("FAIL complex should be agent", complex_payload.get("path_hint"))
        return 1

    print(
        f"OK yuzey-bridge — goal={goal[:40]!r} "
        f"path={payload.get('path_hint')} "
        f"complex={complex_payload.get('path_hint')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
