# Created by Ümit & Gökçenur
"""Ana Motor — cevap sonrası hafif kalite geçidi (kural tabanlı, ek LLM yok)."""

from __future__ import annotations

import os
import re
from typing import Any


def reflection_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_REFLECTION", "1").strip().lower() not in (
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


def _looks_factual_question(msg: str) -> bool:
    low = (msg or "").strip().lower()
    if len(low) < 6:
        return False
    cues = (
        "nedir",
        "kimdir",
        "kim ",
        "ne zaman",
        "kaç",
        "kac",
        "nerede",
        "nasıl",
        "nasil",
        "neden",
        "niçin",
        "hangi",
        "kurdu",
        "tarih",
        "anlam",
        "fark",
    )
    return any(c in low for c in cues) or "?" in low


def _has_guven_line(text: str) -> bool:
    return bool(re.search(r"\*\*Güven:\s*(yüksek|orta|düşük|dusuk)", text, re.I))


def apply_answer_quality_pass(
    reply: str,
    user_message: str,
    *,
    hits: list | None = None,
    question_plan: Any | None = None,
    web_was_used: bool = False,
) -> str:
    """
    Streaming bittikten sonra: eksik güven satırı, kaynaksız factual uyarısı.
    """
    if not reflection_enabled():
        return reply
    body = (reply or "").strip()
    if not body or body.startswith("["):
        return reply

    primary = _plan_primary(question_plan)
    factual = _looks_factual_question(user_message)
    n_src = len(hits or [])
    extras: list[str] = []

    if factual and primary in ("bilgi", "bilim", "dilbilgisi") and n_src == 0 and not web_was_used:
        if "yerel kaynak" not in body.lower() and "genel bilgi" not in body.lower():
            extras.append(
                "\n\n*Not: Bu yanıt için yerel indeks veya web özeti bağlama eklenmedi; "
                "genel model bilgisine dayanıyor olabilir.*"
            )

    if factual and primary in ("bilgi", "bilim") and not _has_guven_line(body):
        level = "orta" if n_src or web_was_used else "düşük"
        extras.append(f"\n\n**Güven: {level}** — otomatik kalite geçidi (kaynak sayısı: {n_src}).")

    if factual and len(body) < 80 and n_src >= 2:
        extras.append(
            "\n\n*Not: Soru derin görünüyor; kaynaklar bağlamda — gerekirse «daha detaylı anlat» diyebilirsin.*"
        )

    if not extras:
        return reply
    return body + "".join(extras)
