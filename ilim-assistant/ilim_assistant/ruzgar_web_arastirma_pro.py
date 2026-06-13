# Created by Ümit & Gökçenur
"""
Ana Motor — Web araştırma PRO (Faz AC).

Hedef: Bilgi/bilim sorularında web taraması birincil; çok sorgu, kaynak sıralama,
sayfa derinliği, haber modu, profesyonel LLM talimatı.
"""

from __future__ import annotations

import os
from typing import Any, Callable

WEB_ARASTIRMA_PRO_VERSION = "web-arastirma-pro-v1-2026-06-13-faz-ac"


def web_arastirma_pro_enabled() -> bool:
    return os.environ.get("RUZGAR_WEB_ARASTIRMA_PRO", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def should_prioritize_web_research(
    message: str,
    question_plan: Any | None,
    mode_norm: str,
) -> bool:
    """Web PRO — bilgi/bilim/güncellik sorularında web her zaman açık."""
    if not web_arastirma_pro_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", "okuma"):
        return False
    if os.environ.get("ENABLE_WEB_SEARCH", "1").strip() in ("0", "false", "no"):
        return False
    primary = _plan_primary(question_plan)
    if primary in ("bilgi", "bilim", "dilbilgisi", "hava"):
        return True
    try:
        from ilim_assistant.ana_motor_plan import (
            _explicit_research_intent,
            looks_like_encyclopedic_fact_question,
        )

        if _explicit_research_intent(message) or looks_like_encyclopedic_fact_question(message):
            return True
    except Exception:
        pass
    low = (message or "").lower()
    if any(
        x in low
        for x in (
            "güncel",
            "guncel",
            "haber",
            "araştır",
            "arastir",
            "web",
            "internet",
            "kaynak",
        )
    ):
        return True
    return False


def apply_web_pro_plan_overrides(plan: Any, message: str) -> Any:
    if plan is None or not web_arastirma_pro_enabled():
        return plan
    if not should_prioritize_web_research(message, plan, "genel"):
        primary = _plan_primary(plan)
        if primary not in ("bilgi", "bilim", "dilbilgisi"):
            return plan
    try:
        from ilim_assistant.ana_motor_plan import rewrite_web_search_query

        plan.prefer_web = True
        wq = rewrite_web_search_query(
            message,
            _plan_primary(plan) or "bilgi",
            "genel",
        )
        if wq:
            plan.web_query = wq
        plan.status_text = "Profesyonel web araştırması — çok kaynak tarama"
    except Exception:
        pass
    return plan


def resolve_pro_fetch_pages(fetch_pages: float) -> int:
    base = int(min(max(fetch_pages, 0), 8))
    if not web_arastirma_pro_enabled():
        return min(base, 5)
    try:
        cap = int(os.environ.get("RUZGAR_WEB_PRO_FETCH_URLS", "6"))
    except ValueError:
        cap = 6
    return max(base, min(cap, 8))


def pick_web_context_builder(
    message: str,
    question_plan: Any | None,
    mode_norm: str,
) -> Callable[..., str]:
    if should_prioritize_web_research(message, question_plan, mode_norm):
        from ilim_assistant.web_tools import build_web_context_pro

        primary = _plan_primary(question_plan) or "bilgi"

        def _pro(q: str, max_results: int = 10, fetch_first_n_urls: int = 0) -> str:
            return build_web_context_pro(
                q,
                primary=primary,
                max_results=max_results,
                fetch_first_n_urls=fetch_first_n_urls,
            )

        return _pro
    from ilim_assistant.web_tools import build_web_context, build_web_context_fast, web_fast_mode_enabled

    if web_fast_mode_enabled():
        return build_web_context_fast
    return build_web_context


def resolve_pro_max_results(default: int) -> int:
    if not web_arastirma_pro_enabled():
        return default
    try:
        return max(default, int(os.environ.get("RUZGAR_WEB_PRO_MAX_RESULTS", "14")))
    except ValueError:
        return max(default, 14)


def build_web_pro_system_addon(message: str) -> str:
    q = (message or "").strip()[:180]
    return (
        "\n\n[TALİMAT — WEB ARAŞTIRMA PRO — Ümit & Gökçenur]\n"
        f"Soru: «{q}»\n"
        "- Yanıtı **web tarama raporundaki** kaynaklara dayandır; uydurma bilgi verme.\n"
        "- Mümkünse **2–4 cümlede öz** cevap, ardından kısa kaynak notu (site/ad).\n"
        "- Resmi (.gov.tr), akademik (.edu), ansiklopedi ve güvenilir haber kaynaklarına öncelik ver.\n"
        "- Çelişen kaynak varsa en güvenilirini seç ve belirsizliği dürüstçe belirt.\n"
        "- Yerel indeks parçaları ile web çelişirse ikisini kıyasla.\n"
    )


def should_defer_web_for_pro(
    message: str,
    question_plan: Any | None,
    mode_norm: str,
) -> bool:
    """PRO modda web ikincil değil — yerel RAG varken de tara."""
    if should_prioritize_web_research(message, question_plan, mode_norm):
        return False
    try:
        from ilim_assistant.ruzgar_umed_cevap_emri import should_defer_web_to_rest

        return should_defer_web_to_rest()
    except Exception:
        return False


def web_arastirma_pro_status() -> dict[str, Any]:
    return {
        "ok": True,
        "enabled": web_arastirma_pro_enabled(),
        "version": WEB_ARASTIRMA_PRO_VERSION,
        "secondary_only_off": os.environ.get(
            "RUZGAR_WEB_SECONDARY_ONLY_ON_EMPTY", "0"
        ).strip()
        in ("0", "false", "no"),
        "max_results": os.environ.get("RUZGAR_WEB_PRO_MAX_RESULTS", "14"),
        "fetch_urls": os.environ.get("RUZGAR_WEB_PRO_FETCH_URLS", "6"),
    }
