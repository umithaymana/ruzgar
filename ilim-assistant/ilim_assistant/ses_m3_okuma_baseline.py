"""
M3 — Okuma motor baseline (kategori + arşiv anlık + hub + workspace read).
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

M3_VERSION = "ses-m3-okuma-baseline-v1-2026-11-03"


def stage_categorize() -> dict[str, Any]:
    from ilim_assistant.okuma_motoru import kategorize_metin_parcastipi

    cases = [
        ("Hadis rivayet isnad Buhari sahih radiyallahu anh ravi sened", "hadis"),
        ("Bu gazelde beyit ve aruz redif kafiye divan siiri misra", "gazel"),
        (
            "Tasavvufta zikir ve suluk ile mursid rehberliginde marifet hakikat",
            "tasavvufi_aciklama",
        ),
        ("Bugun hava guzel", "belirsiz"),
    ]
    fail = 0
    rows = []
    for text, exp in cases:
        kod, _ = kategorize_metin_parcastipi(text)
        ok = kod == exp
        if not ok:
            fail += 1
        rows.append({"ok": ok, "got": kod, "exp": exp})
    return {"ok": fail == 0, "fail": fail, "cases": rows}


def stage_instant() -> dict[str, Any]:
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import maybe_motor_instant_for_target
    from ilim_assistant.motorlar.okuma_faz73 import maybe_instant_faz73

    direct = maybe_instant_faz73("arsiv durum") or ""
    via_okuma, _ = maybe_motor_instant_for_target("arsiv durum", "okuma")
    via_mimar, _ = maybe_motor_instant_for_target("arsiv durum", "mimar")
    ok = (
        "Kültür ve İlim Hazinesi" in direct
        and via_okuma
        and "Kültür ve İlim Hazinesi" in via_okuma
        and via_mimar
        and "Kültür ve İlim Hazinesi" in via_mimar
    )
    return {
        "ok": ok,
        "direct_chars": len(direct),
        "via_okuma": bool(via_okuma),
        "via_mimar": bool(via_mimar),
    }


def stage_hub() -> dict[str, Any]:
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target
    from ilim_assistant.motorlar.programlama_faz98 import wants_umit_gate

    cases = [
        ("arsiv durum", "mimar"),
        ("bu metin hadis mi: rivayet isnad buhari sahih kutub sitte", "mimar"),
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
        rows.append({"msg": msg[:40], "ok": ok, "hub": hub, "reason": meta.get("reason")})

    # dosyayı oku → faz98 değil
    read_msg = "dosyayi oku README.md"
    gate = wants_umit_gate(read_msg)
    hub_r, meta_r = resolve_hub_target(read_msg)
    read_ok = gate is False and hub_r != "programlama"
    if not read_ok:
        fail += 1
    rows.append(
        {
            "msg": read_msg,
            "ok": read_ok,
            "gate": gate,
            "hub": hub_r,
            "reason": meta_r.get("reason"),
        }
    )
    return {"ok": fail == 0, "fail": fail, "cases": rows}


def stage_workspace_read() -> dict[str, Any]:
    """UTF-8 metin okuma (API ile aynı mantık: repo altı dosya)."""
    root = Path(__file__).resolve().parents[2]
    # kısa test dosyası ilim-assistant altında
    ilim = Path(__file__).resolve().parents[1]
    td = Path(tempfile.mkdtemp(prefix="ruzgar_m3_", dir=str(ilim)))
    f = td / "m3_okuma_test.md"
    f.write_text("# Merhaba\n\nRuzgar okuma M3.\n", encoding="utf-8")
    try:
        text = f.read_text(encoding="utf-8")
        ok = "Ruzgar okuma M3" in text and f.stat().st_size < 2_000_000
        # API route varlık
        ds = (ilim / "desktop_server.py").read_text(encoding="utf-8")
        routes_ok = all(
            r in ds
            for r in (
                "/api/workspace/read-text",
                "/api/workspace/read-pdf",
                "/api/workspace/read-ebook",
            )
        )
        return {
            "ok": ok and routes_ok,
            "chars": len(text),
            "routes_ok": routes_ok,
            "tmp": str(f.relative_to(root)) if f.is_relative_to(root) else str(f),
        }
    finally:
        try:
            f.unlink(missing_ok=True)
            td.rmdir()
        except OSError:
            pass


def stage_context() -> dict[str, Any]:
    from ilim_assistant.okuma_motoru import build_motor_context

    ctx = build_motor_context("hadis rivayet kisa ornek")
    return {
        "ok": "OKUMA MOTORU" in ctx and len(ctx) > 200,
        "chars": len(ctx),
    }


def run_m3_baseline() -> dict[str, Any]:
    report: dict[str, Any] = {"version": M3_VERSION, "ok": False, "stages": {}}
    report["stages"]["categorize"] = stage_categorize()
    report["stages"]["instant"] = stage_instant()
    report["stages"]["hub"] = stage_hub()
    report["stages"]["workspace_read"] = stage_workspace_read()
    report["stages"]["context"] = stage_context()
    report["ok"] = all(bool((s or {}).get("ok")) for s in report["stages"].values())
    return report
