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


def build_genel_brain_chain_ids() -> list[str]:
    """Genel sohbet LLM zinciri — yerel öncelik."""
    custom = (os.environ.get("RUZGAR_GENEL_BRAIN_CHAIN") or "").strip()
    if custom:
        return [x.strip() for x in custom.split(",") if x.strip()]
    out: list[str] = []
    if _enabled() and ollama_available():
        for p in ("denge", "hizli"):
            if p not in out:
                out.append(p)
    for p in ("gemini", "groq"):
        if p not in out:
            out.append(p)
    return out or ["gemini", "groq"]


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
