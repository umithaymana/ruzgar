"""
M4 — Mimar motor baseline (atölye niyet + hub + API + alt modüller).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

M4_VERSION = "ses-m4-mimar-baseline-v1-2026-11-03"


def stage_atolye_parse() -> dict[str, Any]:
    from ilim_assistant.motorlar.mimar_faz5 import parse_atolye_action

    cases = [
        ("ev plani ciz", "tasarim", "sketch_from_chat"),
        ("eseri tani", "resim-sanat", "identify"),
        ("foto restore et", "fotograf", "restore"),
        ("eski foto duzelt", "fotograf", "restore"),
        ("kopya cikar poster", "resim-sanat", "copy"),
        ("tasarla: modern villa", "tasarim", "sketch_from_text"),
        ("sanat galerisi", "resim-sanat", "open_tab"),
        ("fotograf nedir", None, None),
    ]
    fail = 0
    rows = []
    for msg, etab, eact in cases:
        p = parse_atolye_action(msg)
        if etab is None:
            ok = p is None
        else:
            ok = bool(p) and p.get("tab") == etab and p.get("action") == eact
        if not ok:
            fail += 1
        rows.append({"msg": msg[:36], "ok": ok, "got": p})
    return {"ok": fail == 0, "fail": fail, "cases": rows}


def stage_instant() -> dict[str, Any]:
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import maybe_motor_instant_for_target
    from ilim_assistant.motorlar.mimar_faz5 import maybe_instant_faz5

    help_txt = maybe_instant_faz5("mimar yardim") or ""
    tab_txt = maybe_instant_faz5("sanat galerisi") or ""
    via, _ = maybe_motor_instant_for_target("sanat galerisi", "mimar")
    ok = (
        "Mimar atölye" in help_txt
        and "Sanat" in tab_txt
        and bool(via)
        and "Sanat" in (via or "")
    )
    return {
        "ok": ok,
        "help_chars": len(help_txt),
        "tab_chars": len(tab_txt),
        "via_hub": bool(via),
    }


def stage_hub() -> dict[str, Any]:
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target

    cases = [
        ("ev plani ciz", "mimar"),
        ("foto restore et", "mimar"),
        ("eseri tani", "mimar"),
        ("fotograf nedir", "genel"),
        ("fotosentez nedir", "genel"),
        ("nasilsin", "genel"),
    ]
    fail = 0
    rows = []
    for msg, exp in cases:
        hub, meta = resolve_hub_target(msg)
        ok = hub == exp
        if not ok:
            fail += 1
        rows.append(
            {"msg": msg[:40], "ok": ok, "hub": hub, "reason": meta.get("reason")}
        )
    return {"ok": fail == 0, "fail": fail, "cases": rows}


def stage_modules() -> dict[str, Any]:
    from ilim_assistant.motorlar import mimar_fotograf, mimar_sanat, mimar_tasarim

    foto = mimar_fotograf.capabilities()
    sanat = mimar_sanat.capabilities()
    tasarim = mimar_tasarim.capabilities()
    lst = mimar_tasarim.list_projects()
    ok = (
        bool(foto.get("ok"))
        and bool(sanat.get("ok"))
        and bool(tasarim.get("ok"))
        and isinstance(lst.get("items"), list)
    )
    return {
        "ok": ok,
        "foto_pillow": bool(foto.get("pillow")),
        "sanat_ok": bool(sanat.get("ok")),
        "tasarim_projects": len(lst.get("items") or []),
    }


def stage_api_routes() -> dict[str, Any]:
    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    needed = [
        "/api/mimar/atolye/parse",
        "/api/mimar/fotograf/capabilities",
        "/api/mimar/fotograf/restoration/preview",
        "/api/mimar/sanat/identify",
        "/api/mimar/sanat/copy",
        "/api/mimar/tasarim/project/list",
        "/api/mimar/tasarim/sketch/from-text",
        "/api/mimar/tasarim/sketch/from-chat-handoff",
    ]
    missing = [p for p in needed if p not in paths]
    return {"ok": not missing, "missing": missing, "mimar_route_count": sum(1 for p in paths if "/mimar/" in p)}


def stage_context() -> dict[str, Any]:
    from ilim_assistant.mimar_motoru import build_motor_context

    ctx = build_motor_context("ev ciz")
    ok = (
        ("MİMAR MOTORU" in ctx or "MIMAR MOTORU" in ctx)
        and "mimar-fotograf" in ctx
        and "mimar-sanat" in ctx
        and "okuma_motoru" in ctx
    )
    return {"ok": ok, "chars": len(ctx)}


def run_m4_baseline() -> dict[str, Any]:
    stages = {
        "atolye_parse": stage_atolye_parse(),
        "instant": stage_instant(),
        "hub": stage_hub(),
        "modules": stage_modules(),
        "api_routes": stage_api_routes(),
        "context": stage_context(),
    }
    ok = all(bool(s.get("ok")) for s in stages.values())
    return {"ok": ok, "version": M4_VERSION, "stages": stages}


def baseline_doc_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "M4_MIMAR_BASELINE_2026-11-03.md"
