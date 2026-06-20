# Created by Ümit & Gökçenur
"""Ana Motor — sıra 6a: genel sohbet bilgi turu (hafıza → RAG → web → LLM zinciri)."""

from __future__ import annotations

import os
from typing import Any

BILGI_TURU_VERSION = "ana-motor-bilgi-turu-v1-2026-06-18-sira6a"

_BILGI_PRIMARIES = frozenset({"bilgi", "bilim", "dilbilgisi"})


def bilgi_turu_enabled() -> bool:
    return os.environ.get("RUZGAR_BILGI_TURU", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def main_only_genel_hafiza_active() -> bool:
    try:
        from ilim_assistant.chat_core import _main_chat_genel_only

        return _main_chat_genel_only()
    except Exception:
        raw = (os.environ.get("RUZGAR_MAIN_ONLY_GENEL_HAFIZA") or "").strip().lower()
        return raw in ("1", "true", "yes", "on")


def full_power_bilgi_turu() -> bool:
    """Tam güç: RAG + web + LLM açık (dar hafıza-only mod kapalı)."""
    if not bilgi_turu_enabled():
        return False
    return not main_only_genel_hafiza_active()


def local_rag_first_enabled() -> bool:
    try:
        from ilim_assistant.ana_motor_fast import fast_local_rag_first_enabled

        return fast_local_rag_first_enabled()
    except Exception:
        return os.environ.get("RUZGAR_FAST_LOCAL_RAG_FIRST", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return str(getattr(question_plan, "primary", "") or "").strip().lower()


def bilgi_primary_turn(question_plan: Any | None) -> bool:
    return _plan_primary(question_plan) in _BILGI_PRIMARIES


def should_prefetch_rag_for_bilgi_turn(
    message: str,
    mode_norm: str,
    question_plan: Any | None = None,
    *,
    history: list | None = None,
) -> bool:
    """
    Bilgi turunda yerel indeks prefetch gerekli mi?

    Yerel-RAG-önce açıkken bilgi/bilim/dilbilgisi ve ansiklopedik sorularda
    bulut hızlı yol RAG'i atlamamalı.
    """
    if not bilgi_turu_enabled():
        return False
    if not full_power_bilgi_turu():
        return False
    m = (mode_norm or "genel").strip().lower()
    if m not in ("genel", "uretim", "gelisim"):
        return False
    msg = (message or "").strip()
    if not msg:
        return False
    if not local_rag_first_enabled():
        return False
    primary = _plan_primary(question_plan)
    if primary in _BILGI_PRIMARIES:
        return True
    try:
        from ilim_assistant.ana_motor_plan import looks_like_encyclopedic_fact_question

        if looks_like_encyclopedic_fact_question(msg):
            return True
    except Exception:
        pass
    return False


def should_skip_bilgi_cloud_fast(
    message: str,
    mode_norm: str,
    question_plan: Any | None = None,
    *,
    history: list | None = None,
) -> bool:
    """Bulut hızlı yol RAG prefetch'i atlamasın (6a — yerel önce)."""
    return should_prefetch_rag_for_bilgi_turn(
        message,
        mode_norm,
        question_plan,
        history=history,
    )


def resolve_web_allow_for_bilgi_turu(
    hits: list,
    ar_hits: list,
    *,
    archive_primary: bool,
    web_pro: bool = False,
    prefer_web: bool = True,
) -> bool:
    """
    Zayıf yerel eşleşmede web açık kalsın; güçlü arşiv/RAG tek başına yeterliyse kapatılabilir.
    """
    if web_pro or prefer_web is False:
        return bool(web_pro)
    try:
        from ilim_assistant.chat_core import local_rag_strong_enough_to_skip_web

        if local_rag_strong_enough_to_skip_web(
            hits,
            ar_hits,
            archive_primary=archive_primary,
        ):
            return False
    except Exception:
        pass
    return True


def bilgi_turu_pipeline_stages() -> list[str]:
    """Bilgi turu katman sırası (Ümit emri: yerel önce)."""
    stages = ["hafiza_ipucu", "rag_indeks"]
    if os.environ.get("ENABLE_WEB_SEARCH", "1").strip() == "1":
        stages.append("web")
    stages.append("llm_zinciri")
    return stages


def expected_llm_chain_hint(question_plan: Any | None = None) -> list[str]:
    """Durum kartı için beklenen LLM profil sırası."""
    try:
        from ilim_assistant.llm_brain import free_brain_enabled

        if free_brain_enabled():
            if _plan_primary(question_plan) in _BILGI_PRIMARIES:
                return ["groq", "denge", "hizli", "gemini"]
            return ["denge", "hizli", "gemini"]
    except Exception:
        pass
    custom = (os.environ.get("RUZGAR_BILGI_BRAIN_CHAIN") or "").strip()
    if custom:
        return [x.strip() for x in custom.split(",") if x.strip()]
    return ["denge", "hizli", "gemini"]


def should_route_bilgi_turu_pipeline(
    message: str,
    question_plan: Any | None = None,
) -> bool:
    """
    Soru tam bilgi turuna (hafıza ipucu → RAG → web → LLM) gitmeli mi?

    Evrensel mikro gerçekler (kaç ay, kaç il) burada değil — anında factual yolu.
    """
    if not full_power_bilgi_turu():
        return False
    msg = (message or "").strip()
    if not msg:
        return False
    if bilgi_primary_turn(question_plan):
        return True
    try:
        from ilim_assistant.ana_motor_plan import (
            looks_like_encyclopedic_fact_question,
            should_stay_on_ana_motor_bilgi,
        )

        if looks_like_encyclopedic_fact_question(msg):
            return True
        if should_stay_on_ana_motor_bilgi(msg):
            return True
    except Exception:
        pass
    return False


def annotate_orchestra_bilgi_turu(
    orch: dict[str, Any],
    question_plan: Any | None = None,
    *,
    stage: str | None = None,
) -> None:
    """Orkestrasyon meta — UI/durum kartı için bilgi turu ipucu."""
    if not isinstance(orch, dict):
        return
    bt: dict[str, Any] = {
        "active": True,
        "version": BILGI_TURU_VERSION,
        "pipeline": bilgi_turu_pipeline_stages(),
        "llm_chain_hint": expected_llm_chain_hint(question_plan),
    }
    if stage:
        bt["stage"] = stage
    orch["bilgi_turu"] = bt


def bilgi_turu_status() -> dict[str, Any]:
    return {
        "enabled": bilgi_turu_enabled(),
        "version": BILGI_TURU_VERSION,
        "full_power": full_power_bilgi_turu(),
        "main_only_genel_hafiza": main_only_genel_hafiza_active(),
        "local_rag_first": local_rag_first_enabled(),
        "fast_local_rag_first_env": os.environ.get("RUZGAR_FAST_LOCAL_RAG_FIRST", "1"),
        "web_search": os.environ.get("ENABLE_WEB_SEARCH", "1") == "1",
        "free_brain": os.environ.get("RUZGAR_FREE_BRAIN", "1").strip().lower()
        not in ("0", "false", "no"),
        "web_suppress_rag_min": os.environ.get("RUZGAR_WEB_SUPPRESS_RAG_MIN", "0.38"),
        "pipeline": bilgi_turu_pipeline_stages(),
        "llm_chain_hint": expected_llm_chain_hint({"primary": "bilgi"}),
        "single_gate": full_power_bilgi_turu(),
    }
