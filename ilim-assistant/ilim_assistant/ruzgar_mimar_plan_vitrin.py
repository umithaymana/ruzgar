# Created by Ümit & Gökçenur
"""
Motor E — büyük plan + fantastik sahne binası vitrin ölçümü (Adım 6.E).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

VERSION = "mimar-plan-vitrin-v1-2026-11-09"

_VITRIN_PROBES: list[tuple[str, str]] = [
    ("ev_ciz", "ev planı çiz"),
    ("eser_tani", "eseri tanı"),
    ("sanat_galeri", "sanat galerisi"),
    ("foto_restore", "eski foto restorasyon"),
    ("kroki", "mimari kroki tasarla"),
]


def enabled() -> bool:
    return os.environ.get("RUZGAR_MIMAR_PLAN_VITRIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def measure_vitrin() -> dict[str, Any]:
    from ilim_assistant.motorlar.mimar_faz5 import ensure_kernel_registered, parse_atolye_action

    ensure_kernel_registered()
    cards: list[dict[str, Any]] = []
    ok_n = 0
    for key, msg in _VITRIN_PROBES:
        hit = parse_atolye_action(msg)
        good = bool(hit and (hit.get("action") or hit.get("tab")))
        if good:
            ok_n += 1
        cards.append(
            {
                "ok": good,
                "id": key,
                "query": msg,
                "action": (hit or {}).get("action"),
                "tab": (hit or {}).get("tab"),
            }
        )
    total = len(_VITRIN_PROBES)
    score = round(100.0 * ok_n / total, 1) if total else 0.0
    return {
        "ok": ok_n == total,
        "version": VERSION,
        "enabled": enabled(),
        "total": total,
        "hit": ok_n,
        "miss": total - ok_n,
        "score_pct": score,
        "cards": cards,
        "label_tr": "Mimar plan/sahne vitrini (niyet)",
    }


def atolye_mutlu_yol() -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    vit = measure_vitrin()
    steps.append(
        {
            "id": "plan_vitrin",
            "ok": bool(vit.get("ok")),
            "detail": f"score={vit.get('score_pct')}% hit={vit.get('hit')}/{vit.get('total')}",
        }
    )

    # Büyük Plan Excel omurgası
    buyuk_ok = False
    buyuk_detail = ""
    try:
        desk = Path(r"C:\Users\hayma\Desktop\RÜZGAR") / "RÜZGAR_BUYUK_PLAN.xlsx"
        root_xlsx = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "RÜZGAR_BUYUK_PLAN.xlsx"
        )
        path = desk if desk.is_file() else root_xlsx
        if path.is_file():
            from openpyxl import load_workbook

            wb = load_workbook(path, read_only=True, data_only=True)
            names = list(wb.sheetnames)
            buyuk_ok = "1_Ana_Sıra" in names or any("Ana" in n for n in names)
            buyuk_detail = f"sheets={len(names)} ana={'1_Ana_Sıra' in names}"
        else:
            buyuk_detail = "xlsx yok"
    except Exception as e:
        buyuk_detail = type(e).__name__
    steps.append({"id": "buyuk_plan", "ok": buyuk_ok, "detail": buyuk_detail})

    # motor context banner
    ctx_ok = False
    try:
        from ilim_assistant.mimar_motoru import build_motor_context

        ctx = build_motor_context("ev çiz") or ""
        ctx_ok = "mimar" in ctx.lower() and len(ctx) > 40
    except Exception as e:
        steps.append({"id": "motor_context", "ok": False, "detail": type(e).__name__})
    else:
        steps.append({"id": "motor_context", "ok": ctx_ok, "detail": f"len={len(ctx)}"})

    routes_ok = False
    missing: list[str] = []
    try:
        ds = Path(__file__).resolve().parent.parent / "desktop_server.py"
        text = ds.read_text(encoding="utf-8") if ds.is_file() else ""
        core = [
            "/api/mimar/atolye/parse",
            "/api/mimar/tasarim/capabilities",
            "/api/mimar/fotograf/capabilities",
            "/api/mimar/sanat/capabilities",
            "/api/mimar/plan-vitrin",
        ]
        missing = [p for p in core if p not in text]
        routes_ok = len(missing) == 0
    except Exception as e:
        missing = [type(e).__name__]
    steps.append(
        {
            "id": "atolye_routes",
            "ok": routes_ok,
            "detail": "ok" if routes_ok else f"eksik={missing}",
        }
    )

    all_ok = all(bool(s.get("ok")) for s in steps)
    return {
        "ok": all_ok,
        "version": VERSION,
        "steps": steps,
        "vitrin": vit,
        "label_tr": "Mimar atölye mutlu yolu",
    }


def public_status() -> dict[str, Any]:
    if not enabled():
        return {"enabled": False, "version": VERSION}
    vit = measure_vitrin()
    return {
        "enabled": True,
        "version": VERSION,
        "vitrin_ok": bool(vit.get("ok")),
        "vitrin_score_pct": vit.get("score_pct"),
        "vitrin_hit": vit.get("hit"),
        "vitrin_total": vit.get("total"),
    }
