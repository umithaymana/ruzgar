# Created by Ümit & Gökçenur
"""
Motor C — çift dilli ilim vitrini ölçümü (Adım 6.C).

Klasik ifade → sabit Türkçe karşılık (sözlük) yan yana kartlar.
LLM'e düşmeden doğrulanabilir mutlu yol.
"""

from __future__ import annotations

import os
from typing import Any

VERSION = "tercume-ilim-vitrin-v1-2026-11-09"

# Ölçüm seti: (gösterim_kaynak, sorgu_metni)
_VITRIN_PROBES: list[tuple[str, str]] = [
    ("بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ", "bismillahirrahmanirrahim"),
    ("Besmele (latin)", "bismillahirrahmanirrahim"),
    ("الْحَمْدُ لِلّٰهِ", "alhamdulillah"),
    ("سُبْحَانَ اللّٰهِ", "subhanallah"),
    ("اللّٰهُ أَكْبَرُ", "allahu akbar"),
    ("أَسْتَغْفِرُ اللّٰهَ", "astaghfirullah"),
    ("لَا إِلٰهَ إِلَّا اللّٰهُ", "la ilaha illallah"),
]


def enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_ILIM_VITRIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def measure_vitrin() -> dict[str, Any]:
    """Sözlük vitrini: her probe için TR karşılık + skor."""
    from ilim_assistant.ruzgar_tercume_sozluk import lookup_fixed_phrase

    cards: list[dict[str, Any]] = []
    ok_n = 0
    for display, query in _VITRIN_PROBES:
        hit = lookup_fixed_phrase(query) or lookup_fixed_phrase(
            f"{query} ifadesini türkçeye çevir"
        )
        if hit and (hit.get("tr") or "").strip():
            ok_n += 1
            cards.append(
                {
                    "ok": True,
                    "source_display": display,
                    "query": query,
                    "tr": hit.get("tr"),
                    "note": hit.get("note") or "",
                    "key": hit.get("key") or "",
                }
            )
        else:
            cards.append(
                {
                    "ok": False,
                    "source_display": display,
                    "query": query,
                    "tr": None,
                    "error": "sözlükte yok",
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
        "label_tr": "Çift dilli ilim vitrini (sabit ifade)",
    }


def atolye_mutlu_yol() -> dict[str, Any]:
    """Atölye mutlu yolu — readiness + vitrin + kritik API yolları varlık kontrolü."""
    steps: list[dict[str, Any]] = []

    # 1) vitrin
    vit = measure_vitrin()
    steps.append(
        {
            "id": "ilim_vitrin",
            "ok": bool(vit.get("ok")),
            "detail": f"score={vit.get('score_pct')}% hit={vit.get('hit')}/{vit.get('total')}",
        }
    )

    # 2) readiness yüzeyi (API toplayıcı çalışıyor; beyin soft)
    ready_ok = False
    ready_detail = ""
    try:
        from ilim_assistant.motorlar.tercume_readiness import collect_tercume_readiness

        rd = collect_tercume_readiness(need_internet=False)
        ready_ok = bool(rd.get("ok"))
        brain_ready = bool((rd.get("brain") or {}).get("ready"))
        pre_ready = bool((rd.get("preflight") or {}).get("ready"))
        ready_detail = (
            f"api_ok={rd.get('ok')} preflight={pre_ready} brain={brain_ready}"
        )
    except Exception as e:
        ready_detail = type(e).__name__
    steps.append({"id": "readiness", "ok": ready_ok, "detail": ready_detail[:200]})

    # 3) route yüzeyi — kaynak satır taraması (desktop_server import etmeden)
    routes_ok = False
    missing: list[str] = []
    try:
        from pathlib import Path

        ds = Path(__file__).resolve().parent.parent / "desktop_server.py"
        text = ds.read_text(encoding="utf-8") if ds.is_file() else ""
        core = [
            '/api/tercume/readiness',
            '/api/tercume/translate-chunk',
            '/api/tercume/config',
            '/api/tercume/ilim-vitrin',
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

    # 4) anlık sözlük komutu
    instant_ok = False
    try:
        from ilim_assistant.ruzgar_tercume_sozluk import lookup_fixed_phrase

        hit = lookup_fixed_phrase("bismillahirrahmanirrahim ifadesini türkçeye çevir")
        instant_ok = bool(hit and hit.get("tr"))
    except Exception:
        instant_ok = False
    steps.append(
        {
            "id": "anlik_sozluk",
            "ok": instant_ok,
            "detail": "besmele sabit karşılık" if instant_ok else "fail",
        }
    )

    all_ok = all(bool(s.get("ok")) for s in steps)
    return {
        "ok": all_ok,
        "version": VERSION,
        "steps": steps,
        "vitrin": vit,
        "label_tr": "Tercüme atölye mutlu yolu",
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
