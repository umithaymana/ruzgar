# Created by Ümit & Gökçenur
"""Ana Motor — Faz AF2: araştırma kartı PRO zenginleştirme (web+yerel+kütüphane)."""

from __future__ import annotations

import os
from typing import Any

FAZ_AF_ARASTIRMA_PRO_VERSION = "arastirma-pro-faz-af-v1-2026-06-13"


def arastirma_pro_card_enabled() -> bool:
    if os.environ.get("RUZGAR_ARASTIRMA_PRO_CARD", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    try:
        from ilim_assistant.ana_motor_faz_ad_sentez_pro import sentez_pro_enabled

        return sentez_pro_enabled()
    except Exception:
        return True


def _web_pro_active(web_extra: str) -> bool:
    extra = (web_extra or "").strip()
    return bool(extra) and (
        "WEB ARAŞTIRMA PRO" in extra or "WEB ARASTIRMA PRO" in extra or len(extra) > 400
    )


def enrich_research_card_pro(
    card: dict[str, Any] | None,
    *,
    sentez_pro: bool = False,
    kutuphane_hint: dict[str, Any] | None = None,
    web_extra: str = "",
    hits: list[tuple[str, str, float]] | None = None,
) -> dict[str, Any]:
    """PRO sentez turunda araştırma kartına çok kaynak rozeti ekle."""
    if not card or not card.get("ok"):
        return card or {}
    if not arastirma_pro_card_enabled() or not sentez_pro:
        return card

    out = dict(card)
    has_kutuphane = bool(kutuphane_hint and kutuphane_hint.get("cevap"))
    n_local = len(hits or [])
    web_pro = _web_pro_active(web_extra)
    sources = {
        "web_pro": web_pro,
        "local_rag": n_local,
        "kutuphane": has_kutuphane,
    }
    active = sum(1 for v in (web_pro, n_local >= 1, has_kutuphane) if v)
    out["pro_mode"] = True
    out["pro_version"] = FAZ_AF_ARASTIRMA_PRO_VERSION
    out["pro_sources"] = sources
    out["pro_badge"] = f"PRO · {active}/3 kaynak"
    out["pro_summary_tr"] = (
        f"Web PRO: {'evet' if web_pro else 'hayır'} · "
        f"Yerel: {n_local} · "
        f"Kütüphane: {'evet' if has_kutuphane else 'hayır'}"
    )
    return out


def arastirma_pro_card_status() -> dict[str, Any]:
    return {
        "enabled": arastirma_pro_card_enabled(),
        "version": FAZ_AF_ARASTIRMA_PRO_VERSION,
    }
