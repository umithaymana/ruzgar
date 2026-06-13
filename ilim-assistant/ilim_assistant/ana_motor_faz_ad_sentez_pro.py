# Created by Ümit & Gökçenur
"""Ana Motor — Faz AD2: çok kaynak sentez PRO (web + yerel + kütüphane)."""

from __future__ import annotations

import os
from typing import Any

SENTEZ_PRO_VERSION = "sentez-pro-faz-ad-v1-2026-06-13"


def sentez_pro_enabled() -> bool:
    if os.environ.get("RUZGAR_SENTEZ_PRO", "1").strip().lower() in ("0", "false", "no"):
        return False
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import web_arastirma_pro_enabled

        return web_arastirma_pro_enabled()
    except Exception:
        return True


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def should_synthesize_pro_turn(
    *,
    question_plan: Any | None,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    mode_norm: str,
    kutuphane_hint: dict[str, Any] | None = None,
) -> bool:
    if not sentez_pro_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", "okuma"):
        return False
    primary = _plan_primary(question_plan)
    if primary not in ("bilgi", "bilim", "dilbilgisi"):
        return False
    has_web = bool((web_extra or "").strip()) and "WEB ARAŞTIRMA PRO" in (web_extra or "")
    has_web = has_web or bool((web_extra or "").strip()) and len((web_extra or "")) > 400
    n_local = len(hits or [])
    has_kutuphane = bool(kutuphane_hint and kutuphane_hint.get("cevap"))
    if has_web and (n_local >= 1 or has_kutuphane):
        return True
    if has_kutuphane and n_local >= 1:
        return True
    return False


def maybe_build_pro_research_summary(
    user_message: str,
    *,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
    kutuphane_hint: dict[str, Any] | None = None,
) -> str:
    """PRO sentez — web PRO + yerel + kütüphane birleşik özet."""
    if not should_synthesize_pro_turn(
        question_plan=question_plan,
        hits=hits,
        web_extra=web_extra,
        mode_norm=mode_norm,
        kutuphane_hint=kutuphane_hint,
    ):
        return ""
    try:
        from ilim_assistant.ana_motor_sentez import build_research_summary

        extra = (web_extra or "").strip()
        if kutuphane_hint and kutuphane_hint.get("cevap"):
            kc = str(kutuphane_hint.get("cevap") or "").strip()[:800]
            ks = str(kutuphane_hint.get("soru") or user_message)[:120]
            extra = (
                f"[KÜTÜPHANE — BilgiKutuphane]\nSoru: {ks}\n{kc}\n\n---\n\n{extra}"
            )
        summary = build_research_summary(
            user_message,
            hits=hits,
            web_extra=extra,
            question_plan=question_plan,
            mode_norm=mode_norm,
            skip_gate=True,
        )
        if not summary:
            return ""
        return summary.replace(
            "[ARAŞTIRMA ÖZETİ — Ana Motor Faz B1",
            "[ARAŞTIRMA ÖZETİ PRO — Faz AD2 — web+yerel+kütüphane",
            1,
        )
    except Exception:
        return ""


def sentez_pro_status() -> dict[str, Any]:
    return {
        "enabled": sentez_pro_enabled(),
        "version": SENTEZ_PRO_VERSION,
        "requires_web_pro": True,
    }
