# Created by Ümit & Gökçenur
"""Ana Motor — Faz AF1: SLO trend + son rapordan otomatik aksiyon planı."""

from __future__ import annotations

import os
from typing import Any

FAZ_AF_SLO_AKSIYON_VERSION = "slo-aksiyon-faz-af-v1-2026-06-13"

_TURN_FIXES: dict[str, list[str]] = {
    "S1": [
        "RUZGAR_ANA_CHAT_HISTORY=1 — oturum hafızası açık olsun",
        "İlk tur yavaşsa RUZGAR_SKIP_RAG_WARMUP=1 ile API açılışını hızlandırın",
    ],
    "S2": [
        "TDK/indeks RAG — ingest_cli veya RUZGAR_KUTUPHANE_ONCE=1",
        "Dilbilgisi turunda yerel indeks öncelikli kalsın",
    ],
    "S3": [
        "RUZGAR_WEB_ARASTIRMA_PRO=1 + tarih Nebula koleksiyonu",
        "RUZGAR_SENTEZ_PRO=1 ile web+yerel birleşik özet",
    ],
    "S4": [
        "RUZGAR_SLO_S4_MAX_SEC=90 — bilim turu süre sınırı",
        "Bilim turunda RUZGAR_BILGI_HYBRID=1 veya Groq yedek",
    ],
    "S5": [
        "Canlı hava — weather_live ve ENABLE_WEB_SEARCH açık",
        "Şehir adı net değilse netleştirme sorusu beklenir",
    ],
    "S6": [
        "Tercüme motoru / hub tercüme yolu — Ana Motor tercüme modu",
    ],
    "S7": [
        "Programlama hub veya kod modu — uzun yanıt için token sınırı",
    ],
    "S8": [
        "Gündelik bilgi — RUZGAR_DOGAL_SOHBET=1, kısa net yanıt",
    ],
    "S9": [
        "Hatırla komutu — hafıza motoru ve RUZGAR_ANA_SESSION_REMEMBER=1",
    ],
    "S10": [
        "Tarih derin — tarih hızlı yol + Nebula tarih_kaynak",
        "RUZGAR_TARIH_FAST=1 veya tarih özel indeks",
    ],
}

_TREND_ACTIONS: dict[str, list[str]] = {
    "down": [
        "Son koşularda skor düştü — Canlı SLO panelinden yeni koşu başlatın",
        "Zayıf turları aşağıdaki önerilere göre düzeltin, ardından gece koşusunu bekleyin",
    ],
    "stable": [
        "Skor stabil — tekrarlayan zayıf turlara odaklanın",
    ],
    "up": [
        "Skor yükseliyor — mevcut .env ayarlarını koruyun",
    ],
}


def slo_aksiyon_enabled() -> bool:
    return os.environ.get("RUZGAR_SLO_AKSIYON", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_slo_action_plan(*, limit: int = 8) -> dict[str, Any]:
    """Trend + son rapordan uygulanabilir SLO aksiyon listesi."""
    if not slo_aksiyon_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AF_SLO_AKSIYON_VERSION,
            "summary_tr": "SLO aksiyon planı kapalı",
            "actions": [],
        }

    try:
        from ilim_assistant.ana_motor_faz_ae_slo_trend import build_slo_trend_report
        from ilim_assistant.ana_motor_faz_ad_slo_gece import load_last_slo_report
        from ilim_assistant.ruzgar_canli_slo_faz_k import SLO_TURN_LABELS
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "version": FAZ_AF_SLO_AKSIYON_VERSION,
            "error": str(exc)[:120],
            "actions": [],
        }

    trend = build_slo_trend_report(limit=limit)
    last = load_last_slo_report()
    rep = last.get("weak_point_report") if isinstance(last, dict) else {}
    weak_ids: list[str] = []
    for w in rep.get("weak_turns") or []:
        if isinstance(w, dict) and w.get("id"):
            weak_ids.append(str(w["id"]))
    for rw in trend.get("recurring_weak") or []:
        if isinstance(rw, dict) and rw.get("id") and rw["id"] not in weak_ids:
            weak_ids.append(str(rw["id"]))

    actions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for wid in weak_ids:
        if wid in seen:
            continue
        seen.add(wid)
        fixes = _TURN_FIXES.get(wid, ["Genel: Web PRO + yerel RAG + RUZGAR_FREE_BRAIN=1 kontrol edin"])
        actions.append(
            {
                "id": wid,
                "label": SLO_TURN_LABELS.get(wid, wid),
                "items": fixes[:4],
                "priority": "high" if any(
                    rw.get("id") == wid and (rw.get("count") or 0) >= 2
                    for rw in (trend.get("recurring_weak") or [])
                ) else "normal",
            }
        )

    global_items: list[str] = []
    trend_key = str(trend.get("trend") or "none")
    if trend_key in _TREND_ACTIONS:
        global_items.extend(_TREND_ACTIONS[trend_key][:3])
    if not weak_ids and trend.get("count", 0) == 0:
        global_items.append("İlk SLO koşusunu başlatın — Canlı SLO paneli veya --live --slo-pack")
    elif not weak_ids and rep.get("ok"):
        global_items.append("Son koşu temiz — periyodik gece koşusu yeterli")

    if global_items:
        actions.insert(
            0,
            {
                "id": "GENEL",
                "label": "Genel eğilim",
                "items": global_items[:4],
                "priority": "info",
            },
        )

    if not actions:
        summary = "Aksiyon gerekmiyor — SLO geçti veya rapor yok"
    else:
        n_high = sum(1 for a in actions if a.get("priority") == "high")
        summary = f"{len(actions)} aksiyon"
        if n_high:
            summary += f" · {n_high} tekrarlayan zayıf tur"

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AF_SLO_AKSIYON_VERSION,
        "trend": trend_key,
        "weak_count": len(weak_ids),
        "actions": actions,
        "summary_tr": summary,
    }


def slo_aksiyon_status() -> dict[str, Any]:
    plan = build_slo_action_plan(limit=6)
    return {
        "enabled": slo_aksiyon_enabled(),
        "version": FAZ_AF_SLO_AKSIYON_VERSION,
        "summary_tr": plan.get("summary_tr"),
        "action_count": len(plan.get("actions") or []),
    }
