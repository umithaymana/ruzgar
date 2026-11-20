# Created by Ümit & Gökçenur
"""
Rüzgar — Faz 90: Genel sohbet local-first (Ümit emri v2 — 2026-05-27).

Hafıza/RAG sonrası LLM: önce yerel Ollama (denge/hizli), sonra Gemini/Groq.
Kapat: RUZGAR_GENEL_LOCAL_FIRST=0
"""

from __future__ import annotations

import os
from typing import Any

FAZ90_VERSION = "ruzgar-genel-faz90-v1-2026-05-27"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_GENEL_LOCAL_FIRST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def genel_local_first_enabled() -> bool:
    return _enabled()


def ollama_available() -> bool:
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        return bool(ollama_reachable())
    except Exception:
        return False


def _gemini_on_cooldown() -> bool:
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

        return gemini_cooldown_active()
    except Exception:
        return False


def ilim_rag_cloud_first_enabled() -> bool:
    """İlim/RAG turunda bulut-önce — varsayılan KAPALI (umed local-first kazanır).

    Tek karar tablosu (Faz 4):
    | Bayrak | Sonuç |
    | RUZGAR_ILIM_RAG_CLOUD_FIRST=1 | Gemini/Groq önce (açık istek) |
    | =0 / yok (varsayılan) | Ollama denge/hızlı → Groq → Gemini (umed) |
    | RUZGAR_ILIM_BRAIN_CHAIN=... | Özel zincir (bayrağı ezer) |
    """
    return os.environ.get("RUZGAR_ILIM_RAG_CLOUD_FIRST", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def build_ilim_rag_brain_chain_ids() -> list[str]:
    """İlim/tarih/bilim turları — cloud-first yalnız açık bayrakla; değilse local-first."""
    custom = (os.environ.get("RUZGAR_ILIM_BRAIN_CHAIN") or "").strip()
    if custom:
        ids = [x.strip() for x in custom.split(",") if x.strip()]
        if _gemini_on_cooldown():
            ids = [x for x in ids if x != "gemini"]
            if "groq" not in ids:
                ids.insert(0, "groq")
        return ids
    if not ilim_rag_cloud_first_enabled():
        # umed / Faz 90 local-first — ilim turunda da aynı sıra
        return build_genel_brain_chain_ids()
    ids: list[str] = []
    if not _gemini_on_cooldown():
        ids.append("gemini")
    if "groq" not in ids:
        ids.append("groq")
    if not ids:
        ids = ["groq", "gemini"]
    # Yerel yedek sonda
    if ollama_available():
        for p in ("denge", "hizli"):
            if p not in ids:
                ids.append(p)
    if _gemini_on_cooldown():
        ids = [x for x in ids if x != "gemini"]
        if "groq" not in ids:
            ids.insert(0, "groq")
    return ids


def brain_order_decision_table() -> dict[str, Any]:
    """Smoke / health — hangi zincir neden seçilir."""
    return {
        "genel_local_first": genel_local_first_enabled(),
        "ilim_rag_cloud_first": ilim_rag_cloud_first_enabled(),
        "genel_chain": build_genel_brain_chain_ids()[:5],
        "ilim_chain": build_ilim_rag_brain_chain_ids()[:5],
        "note": "İlim turunda local-first varsayılan; cloud-first yalnız RUZGAR_ILIM_RAG_CLOUD_FIRST=1",
    }


def build_genel_brain_chain_ids() -> list[str]:
    """Genel sohbet LLM zinciri — yerel öncelik; kota soğukken Gemini atlanır.

    `RUZGAR_SOHBET_TARZ` yalnız üsluptur — zinciri Gemini-önce'ye çevirmez (Faz T2).
    """
    custom = (os.environ.get("RUZGAR_GENEL_BRAIN_CHAIN") or "").strip()
    if custom:
        ids = [x.strip() for x in custom.split(",") if x.strip()]
    else:
        out: list[str] = []
        if _enabled() and ollama_available():
            for p in ("denge", "hizli"):
                if p not in out:
                    out.append(p)
        if _gemini_on_cooldown():
            for p in ("groq", "kod"):
                if p not in out:
                    out.append(p)
        else:
            # Local-first: Ollama sonrası Groq, sonra Gemini (umed v2)
            for p in ("groq", "gemini"):
                if p not in out:
                    out.append(p)
        ids = out or ["groq", "gemini"]
        # Ollama yoksa ve Gemini açıksa bulutu öne al (erişilebilirlik)
        if not (_enabled() and ollama_available()):
            try:
                from ilim_assistant.config import gemini_disabled

                if not gemini_disabled() and not _gemini_on_cooldown():
                    ids = ["gemini"] + [x for x in ids if x != "gemini"]
            except Exception:
                pass
    if _gemini_on_cooldown():
        ids = [x for x in ids if x != "gemini"]
        if "groq" not in ids:
            ids.insert(0, "groq")
    return ids


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["genel_faz90"] = genel_local_first_enabled()
    out["genel_local_first"] = genel_local_first_enabled() and ollama_available()
    out["genel_brain_chain"] = build_genel_brain_chain_ids()[:4]
    out["ilim_rag_cloud_first"] = ilim_rag_cloud_first_enabled()
    out["ilim_brain_chain"] = build_ilim_rag_brain_chain_ids()[:4]
    out["brain_order"] = brain_order_decision_table()
    return out


def faz90_directive() -> str:
    return (
        "[Faz 90 — genel sohbet local-first]\n"
        "Zincir: Ollama denge/hizli -> Gemini -> Groq\n"
        f"Kapat: RUZGAR_GENEL_LOCAL_FIRST=0 · {FAZ90_VERSION}\n"
    )
