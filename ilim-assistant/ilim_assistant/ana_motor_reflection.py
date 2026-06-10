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
        "kuruldu",
        "tarih",
        "anlam",
        "fark",
    )
    return any(c in low for c in cues) or "?" in low


def _looks_factual_claim(text: str) -> bool:
    """Soru veya kesin iddia — B2 kaynak uyumu için."""
    if _looks_factual_question(text):
        return True
    low = (text or "").strip().lower()
    if len(low) < 10:
        return False
    if _extract_years(low):
        return True
    return any(
        x in low
        for x in (
            "kesinlikle",
            "suphesiz",
            "şüphesiz",
            "yilinda",
            "yılında",
            "dogdu",
            "doğdu",
        )
    )


def _has_guven_line(text: str) -> bool:
    return bool(re.search(r"\*\*Güven:\s*(yüksek|orta|düşük|dusuk)", text, re.I))


def _extract_years(text: str) -> set[str]:
    return set(re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", text or ""))


def _extract_numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d{2,5}\b", text or ""))


def _source_corpus(hits: list | None) -> str:
    parts: list[str] = []
    for item in hits or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            parts.append(str(item[0] or ""))
            parts.append(str(item[1] or ""))
    return " ".join(parts).lower()


def detect_source_answer_mismatch(
    reply: str,
    *,
    hits: list | None = None,
    web_was_used: bool = False,
) -> tuple[bool, str]:
    """
    Faz B2 — kural tabanlı kaynak ↔ cevap uyumu.
    Çelişki veya kaynaksız kesin iddia → (True, kısa not).
    """
    body = (reply or "").strip()
    if not body or not _looks_factual_claim(body):
        return False, ""
    corpus = _source_corpus(hits)
    if not corpus and not web_was_used:
        return False, ""

    reply_years = _extract_years(body)
    src_years = _extract_years(corpus)
    if reply_years and src_years and not (reply_years & src_years):
        return True, (
            "Cevaptaki tarih bilgisi yerel kaynak parçalarıyla örtüşmüyor; "
            "**emin değilim** — lütfen kaynakları veya «daha detaylı anlat» ile doğrula."
        )

    reply_nums = _extract_numbers(body)
    src_nums = _extract_numbers(corpus)
    orphan_nums = {n for n in reply_nums if n not in src_nums and len(n) >= 3}
    if orphan_nums and hits and len(hits) >= 2 and not web_was_used:
        if len(orphan_nums) >= 2:
            return True, (
                "Yanıttaki sayısal bilgiler bağlamdaki kaynaklarda net görünmüyor; "
                "**emin değilim** — genel bilgi veya eksik kaynak olabilir."
            )

    low = body.lower()
    overconfident = any(
        x in low for x in ("kesinlikle", "şüphesiz", "suphesiz", "kuşkusuz", "kusku")
    )
    if overconfident and hits and len(hits) >= 2:
        scores = []
        for item in hits:
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                try:
                    scores.append(float(item[2]))
                except (TypeError, ValueError):
                    pass
        if scores and max(scores) - min(scores) > 0.18:
            return True, (
                "Kaynak parçaları birbiriyle tam uyumlu görünmüyor; "
                "**emin değilim** — çelişen noktaları açıkça belirttim."
            )

    if corpus and reply_years and len(src_years) >= 2 and len(reply_years) == 1:
        if reply_years.pop() not in src_years:
            yr = next(iter(_extract_years(body)), "")
            if yr and yr in _extract_years(corpus):
                pass
            elif yr:
                return True, (
                    f"Kaynaklarda farklı tarih ipuçları var; «{yr}» için **emin değilim** — "
                    "özet kaynaklara dayanmalı."
                )

    return False, ""


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

    mismatch, mismatch_note = detect_source_answer_mismatch(
        body,
        hits=hits,
        web_was_used=web_was_used,
    )
    if mismatch and mismatch_note and mismatch_note.lower() not in body.lower():
        extras.append(f"\n\n*Not (Faz B2): {mismatch_note}*")
        if _has_guven_line(body) and "**Güven: yüksek**" in body:
            body = re.sub(
                r"\*\*Güven:\s*yüksek\*\*[^.\n]*",
                "**Güven: orta** — kaynak uyumu tam değil",
                body,
                count=1,
                flags=re.I,
            )

    try:
        from ilim_assistant.ana_motor_guncellik import append_reply_freshness_stamp

        stamped = append_reply_freshness_stamp(
            body + "".join(extras),
            web_was_used=web_was_used,
            user_message=user_message,
        )
        if stamped != body + "".join(extras):
            return stamped
    except Exception:
        pass

    if not extras:
        return reply
    return body + "".join(extras)
