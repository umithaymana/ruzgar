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
    """İlim bulut-önce.

    F2.6 (Mimar İlim-A): varsayılan **kapalı** — raftan bağlam varken yerel özet;
    Gemini stil/yedek. Eski davranış: RUZGAR_ILIM_RAG_CLOUD_FIRST=1
    """
    return os.environ.get("RUZGAR_ILIM_RAG_CLOUD_FIRST", "0").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_ilim_local_first_chain_ids() -> list[str]:
    """F2.6 — bilgi/ilim: Ollama → Gemini → Groq (ChatGPT-tarz Gemini-önce'yi ezmez)."""
    custom = (os.environ.get("RUZGAR_ILIM_LOCAL_CHAIN") or "").strip()
    if custom:
        return [x.strip() for x in custom.split(",") if x.strip()]
    out: list[str] = []
    if ollama_available():
        for p in ("denge", "hizli"):
            if p not in out:
                out.append(p)
    if not _gemini_on_cooldown():
        out.append("gemini")
    if "groq" not in out:
        out.append("groq")
    return out or ["denge", "gemini", "groq"]


def build_ilim_rag_brain_chain_ids() -> list[str]:
    """İlim/tarih/bilim turları.

    cloud_first=1 → Gemini/Groq önce; aksi halde F2.6 yerel önce.
    """
    if not ilim_rag_cloud_first_enabled():
        return build_ilim_local_first_chain_ids()
    custom = (os.environ.get("RUZGAR_ILIM_BRAIN_CHAIN") or "").strip()
    if custom:
        ids = [x.strip() for x in custom.split(",") if x.strip()]
    else:
        ids = []
        if not _gemini_on_cooldown():
            ids.append("gemini")
        if "groq" not in ids:
            ids.append("groq")
        if not ids:
            ids = ["groq", "gemini"]
    if _gemini_on_cooldown():
        ids = [x for x in ids if x != "gemini"]
        if "groq" not in ids:
            ids.insert(0, "groq")
    # Yerel yedek
    if ollama_available():
        for p in ("denge", "hizli"):
            if p not in ids:
                ids.append(p)
    return ids


def genel_hibrit_b_enabled() -> bool:
    """F4.3 — genel kültür B hibrit: doğal/yerel önce, bulut yedek (varsayılan açık)."""
    return os.environ.get("RUZGAR_GENEL_HIBRIT_B", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_genel_brain_chain_ids() -> list[str]:
    """Genel sohbet LLM zinciri — yerel öncelik; kota soğukken Gemini atlanır."""
    try:
        from ilim_assistant.config import gemini_disabled
        from ilim_assistant.prompts import sohbet_tarz_chatgpt

        if sohbet_tarz_chatgpt():
            if gemini_disabled():
                return ["denge", "hizli"]
            # F4.3 B hibrit: denge/hizli önce; Gemini yedek (eski: gemini-first)
            if genel_hibrit_b_enabled():
                ids: list[str] = []
                if ollama_available():
                    ids.extend(["denge", "hizli"])
                if not _gemini_on_cooldown():
                    ids.append("gemini")
                if "groq" not in ids:
                    ids.append("groq")
                return ids or ["denge", "gemini", "hizli"]
            ids = ["gemini", "denge", "hizli"]
            if _gemini_on_cooldown():
                ids = ["denge", "hizli"]
            return ids
    except Exception:
        pass
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
