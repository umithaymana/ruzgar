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


def build_genel_brain_chain_ids() -> list[str]:
    """Genel sohbet LLM zinciri — yerel öncelik; kota soğukken Gemini atlanır."""
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
            for p in ("groq", "gemini"):
                if p not in out:
                    out.append(p)
        ids = out or ["groq", "gemini"]
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
    return out


def faz90_directive() -> str:
    return (
        "[Faz 90 — genel sohbet local-first]\n"
        "Zincir: Ollama denge/hizli -> Gemini -> Groq\n"
        f"Kapat: RUZGAR_GENEL_LOCAL_FIRST=0 · {FAZ90_VERSION}\n"
    )
