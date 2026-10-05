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


def looks_like_live_web_needed(message: str) -> bool:
    """Güncel kur / haber / «şu an» — yerel hafıza yetmez, web zorunlu."""
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "güncel",
            "guncel",
            "haber",
            "bugün",
            "bugun",
            "şu an",
            "su an",
            "şimdi",
            "simdi",
            "dolar",
            "euro",
            "altın",
            "altin",
            "borsa",
            "seçim",
            "secim",
            "son dakika",
            "araştır",
            "arastir",
            "web'den",
            "webden",
            "internet",
            "kaynak bul",
        )
    )


def should_prioritize_web_research(
    message: str,
    question_plan: Any | None,
    mode_norm: str,
) -> bool:
    """
    Web PRO arama motoru kullanılsın mı?

    Yerel-önce: yalnızca güncel/araştırma niyeti veya bilgi planı + zayıf yerel
    (asıl «web aç» kapısı chat_core secondary politikasında).
    Burada True = PRO builder / çok kaynak; zorunlu web değil.
    """
    if not web_arastirma_pro_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", "okuma"):
        return False
    if os.environ.get("ENABLE_WEB_SEARCH", "1").strip() in ("0", "false", "no"):
        return False
    if looks_like_live_web_needed(message):
        return True
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
    return False


def should_force_web_despite_local(
    message: str,
    question_plan: Any | None = None,
) -> bool:
    """Güçlü yerel RAG olsa bile web açılsın (canlı kur/haber)."""
    del question_plan
    if os.environ.get("ENABLE_WEB_SEARCH", "1").strip() in ("0", "false", "no"):
        return False
    return looks_like_live_web_needed(message)


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
    live = looks_like_live_web_needed(message)
    science = False
    try:
        from ilim_assistant.ana_motor_plan import (
            looks_like_encyclopedic_fact_question,
            looks_like_science_knowledge_question,
        )

        science = looks_like_science_knowledge_question(message) or looks_like_encyclopedic_fact_question(
            message
        )
    except Exception:
        science = False
    extra = ""
    if live:
        extra = (
            "- Bu soru **canlı/güncel** (kur/haber). Yerel hafızadaki eski rakamları **yoksay**.\n"
            "- Kur sorularında sayısal değeri **ilk cümlede** ver; meta konuşma / «anlamaya çalışacağım» yasak.\n"
            "- Web raporunda «CANLI KUR ÖZETİ» varsa onu esas al.\n"
        )
    if science:
        extra += (
            "- Bu bir **sabit bilgi** sorusu. Yalnızca konuyla **doğrudan ilgili** kaynak metinlerini kullan.\n"
            "- Alakasız site/snippet (forum, burç, ürün tanıtımı, sözlük mizahı) görürsen **yoksay**.\n"
            "- Önce 1 cümlede net doğru cevap; sonra 1–3 cümle basit gerekçe. Uydurma yasak.\n"
            "- Sayı/uzaklık/tanım için Wikipedia veya güvenilir ansiklopedi metnini tercih et.\n"
            "- Kaynak yetersizse «emin değilim» de; rastgele web parçası birleştirme.\n"
        )
    return (
        "\n\n[TALİMAT — WEB ARAŞTIRMA PRO — Ümit & Gökçenur]\n"
        f"Soru: «{q}»\n"
        "- Yanıtı **web tarama raporundaki** ilgili kaynaklara dayandır; uydurma bilgi verme.\n"
        "- Mümkünse **2–4 cümlede öz** cevap (Ümit abinin anlayacağı sade Türkçe), ardından kısa kaynak notu.\n"
        "- Resmi (.gov.tr), akademik (.edu), ansiklopedi ve güvenilir haber kaynaklarına öncelik ver.\n"
        "- Çelişen kaynak varsa en güvenilirini seç ve belirsizliği dürüstçe belirt.\n"
        "- Yerel indeks parçaları ile web çelişirse: sabit bilgide tutarlı ansiklopediyi, "
        "canlı konuda **web'i** önceliklendir.\n"
        f"{extra}"
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
