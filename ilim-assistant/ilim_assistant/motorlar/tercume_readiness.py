"""
Tercüme Faz 13 — birleşik hazırlık özeti (config + UI şeridi).
"""

from __future__ import annotations

from typing import Any

READINESS_VERSION = "tercume-readiness-v13-2026-06-01"


def collect_tercume_readiness(*, need_internet: bool = False) -> dict[str, Any]:
    from ilim_assistant.motorlar.tercume_llm import translation_brain_status
    from ilim_assistant.motorlar.tercume_preflight import run_tercume_preflight

    brain = translation_brain_status()
    pre = run_tercume_preflight(need_internet=need_internet)

    from ilim_assistant.motorlar.tercume_eser_arama import duckduckgo_search_available

    search_ok, search_detail = duckduckgo_search_available()

    blockers: list[str] = []
    if not brain.get("ready"):
        blockers.append(
            "Çeviri beyni hazır değil — Ollama veya API anahtarı gerekli."
            if not brain.get("ollama_only")
            else "Ollama çalışmıyor — ollama serve + model pull."
        )
    if need_internet and not search_ok:
        blockers.append(f"İnternet araması için: {search_detail}")

    hints = list(pre.get("hints") or [])
    if brain.get("ollama_only") and brain.get("ollama"):
        hints.insert(0, f"Ollama-only: {brain.get('ollama_model')}")

    ready = bool(pre.get("ready")) and bool(brain.get("ready"))
    if need_internet:
        ready = ready and search_ok

    return {
        "ok": True,
        "version": READINESS_VERSION,
        "ready": ready,
        "brain": brain,
        "preflight": pre,
        "search": {"ok": search_ok, "detail": search_detail},
        "blockers": blockers,
        "hints": hints[:6],
    }
