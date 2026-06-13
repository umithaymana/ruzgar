# Created by Ümit & Gökçenur
"""Tek beyin Faz J — bilgi/ansiklopedik cevap doğrulama ve konu hizalaması."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

TEK_BEYIN_BILGI_GUARD_VERSION = "tek-beyin-bilgi-guard-v1-2026-06-12-faz-j"

_QUERY_STOP = frozenset(
    {
        "kimdir",
        "kimdi",
        "kim",
        "kimi",
        "nedir",
        "ne",
        "nasıl",
        "nasil",
        "nerede",
        "ne zaman",
        "hangi",
        "kaç",
        "kac",
        "mi",
        "mı",
        "mu",
        "mü",
        "bir",
        "ile",
        "ve",
        "için",
        "icin",
        "olan",
        "hakkında",
        "hakkinda",
        "anlat",
        "lütfen",
        "lutfen",
    }
)
_GUVEN_RE = re.compile(
    r"\*\*Güven:\s*(yüksek|orta|düşük|dusuk)\*\*",
    re.I,
)
_KIMDIR_PROF_HALLUCINATION = re.compile(
    r"(?:türk\s+)?(?:şair|sair|yazar|poet|writer|oyuncu|aktris|actress|sanatçı|sanatci)",
    re.I,
)


def tek_beyin_bilgi_guard_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_BILGI_GUARD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def looks_like_bilgi_guard_turn(
    message: str,
    question_plan: Any | None = None,
) -> bool:
    if not tek_beyin_bilgi_guard_enabled():
        return False
    try:
        from ilim_assistant.ruzgar_tek_beyin_izolasyon import looks_like_bilgi_isolation_turn

        return looks_like_bilgi_isolation_turn(message, question_plan)
    except Exception:
        pass
    primary = ""
    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "").strip().lower()
    return primary in ("bilgi", "bilim", "dilbilgisi")


def query_anchor_tokens(message: str) -> set[str]:
    """Sorudaki odak kelimeler — cevap bunlarla hizalanmalı."""
    raw = _norm(message)
    for cue in ("ne zaman", "ne zaman", "kimdir", "kimdi"):
        raw = raw.replace(cue, " ")
    out: set[str] = set()
    for w in re.split(r"[^\wçğıöşüÇĞİÖŞÜ]+", raw, flags=re.UNICODE):
        w = w.strip().lower()
        if len(w) >= 3 and w not in _QUERY_STOP:
            out.add(w)
        if len(w) >= 5:
            out.add(w[:5])
    return out


def assess_bilgi_topic_alignment(
    message: str,
    reply: str,
) -> tuple[bool, float, str]:
    """
    Cevap sorunun konusuna kaymış mı?
    Dönüş: (ok, overlap_skoru, neden)
    """
    body = (reply or "").strip()
    if not body or len(body) < 24:
        return True, 1.0, ""
    anchors = query_anchor_tokens(message)
    if not anchors:
        return True, 1.0, ""
    head = _norm(body[: min(420, len(body))])
    rep_tokens: set[str] = set()
    for w in re.split(r"[^\wçğıöşüÇĞİÖŞÜ]+", head, flags=re.UNICODE):
        w = w.strip().lower()
        if len(w) >= 3:
            rep_tokens.add(w)
        if len(w) >= 5:
            rep_tokens.add(w[:5])
    if not rep_tokens:
        return False, 0.0, "empty_head"
    overlap = len(anchors & rep_tokens) / max(1, len(anchors))
    try:
        min_ov = max(0.15, min(float(os.environ.get("RUZGAR_TEK_BEYIN_BILGI_MIN_OVERLAP", "0.34")), 0.8))
    except ValueError:
        min_ov = 0.34
    if overlap >= min_ov:
        return True, overlap, ""
    if overlap <= 0.0:
        return False, overlap, "topic_drift"
    if overlap < min_ov * 0.55:
        return False, overlap, "weak_alignment"
    return True, overlap, ""


def _clip_question(message: str, limit: int = 100) -> str:
    q = " ".join((message or "").split())
    return q if len(q) <= limit else q[: max(0, limit - 1)].rstrip() + "…"


def looks_like_kimdir_profession_hallucination(message: str, reply: str) -> bool:
    """«kimdir» sorusuna kaynak yokken şablon meslek uydurması."""
    mq = _norm(message)
    if not re.search(r"\bkimdir\b|\bkimdi\b", mq):
        return False
    if any(p in mq for p in ("şair", "sair", "yazar", "oyuncu", "poet", "writer")):
        return False
    return bool(_KIMDIR_PROF_HALLUCINATION.search(reply or ""))


def honest_bilgi_fallback(message: str, *, reason: str = "") -> str:
    q = _clip_question(message)
    why = ""
    if reason == "topic_drift":
        why = " Yanıt soruyla tam örtüşmüyor; önceki bağlam veya model kayması olabilir."
    elif reason == "source_mismatch":
        why = " Kaynaklarla cevap arasında uyumsuzluk var."
    elif reason == "weak_alignment":
        why = " Konu hizalaması zayıf."
    elif reason == "hallucinated_profile":
        why = " Model kaynak olmadan genel bir meslek/kişilik şablonu üretmiş olabilir."
    return (
        f"Ümit abi, «{q}» sorusuna net ve güvenilir bir yanıt veremedim.{why} "
        "Web araması açıksa tekrar deneyebilir veya soruyu biraz daha netleştirebilirsin.\n\n"
        "**Güven: düşük** — tek beyin bilgi doğrulama (Faz J)."
    )


def _ensure_low_guven(reply: str) -> str:
    body = (reply or "").strip()
    if not body:
        return body
    if _GUVEN_RE.search(body):
        return _GUVEN_RE.sub("**Güven: düşük**", body, count=1)
    return body.rstrip() + "\n\n**Güven: düşük** — kaynak/cevap uyumu zayıf."


def _append_note_if_missing(reply: str, note: str) -> str:
    body = (reply or "").strip()
    note = (note or "").strip()
    if not body or not note:
        return body
    if note.lower()[:40] in body.lower():
        return body
    return body.rstrip() + f"\n\n*Not (Faz J): {note[:360]}*"


def apply_tek_beyin_bilgi_guard(
    reply: str,
    message: str,
    *,
    hits: list | None = None,
    question_plan: Any | None = None,
    web_was_used: bool = False,
    reflection_meta: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Bilgi turu sonrası: konu hizalaması + kaynak uyumu + güven satırı.
    """
    meta: dict[str, Any] = {
        "enabled": tek_beyin_bilgi_guard_enabled(),
        "version": TEK_BEYIN_BILGI_GUARD_VERSION,
        "applied": False,
        "topic_ok": True,
        "topic_overlap": 1.0,
        "source_mismatch": False,
        "replaced": False,
    }
    if not tek_beyin_bilgi_guard_enabled():
        return (reply or "").strip(), meta
    if not looks_like_bilgi_guard_turn(message, question_plan):
        return (reply or "").strip(), meta

    body = (reply or "").strip()
    if not body:
        return body, meta

    meta["applied"] = True
    mismatch = bool((reflection_meta or {}).get("mismatch"))
    mismatch_note = str((reflection_meta or {}).get("mismatch_note") or "").strip()

    if looks_like_kimdir_profession_hallucination(message, body):
        good_hits = []
        for h in hits or []:
            try:
                score = float(h[2] if isinstance(h, (list, tuple)) and len(h) > 2 else h.get("score", 0))
            except Exception:
                score = 0.0
            if score >= 0.22:
                good_hits.append(h)
        if not good_hits:
            meta["replaced"] = True
            meta["hallucinated_profile"] = True
            return honest_bilgi_fallback(message, reason="hallucinated_profile"), meta

    try:
        from ilim_assistant.ana_motor_reflection import detect_source_answer_mismatch

        mis, mis_note = detect_source_answer_mismatch(
            body,
            hits=hits,
            web_was_used=web_was_used,
        )
        if mis:
            mismatch = True
            if mis_note:
                mismatch_note = mis_note
    except Exception:
        pass

    topic_ok, overlap, topic_reason = assess_bilgi_topic_alignment(message, body)
    meta["topic_ok"] = topic_ok
    meta["topic_overlap"] = round(float(overlap), 3)
    meta["topic_reason"] = topic_reason
    meta["source_mismatch"] = mismatch

    if not topic_ok and topic_reason in ("topic_drift", "empty_head"):
        meta["replaced"] = True
        return honest_bilgi_fallback(message, reason=topic_reason), meta

    if not topic_ok and topic_reason == "weak_alignment":
        body = _append_note_if_missing(
            body,
            f"«{_clip_question(message, 72)}» sorusuyla konu hizalaması zayıf; "
            "cevabı kaynaklarla doğrula.",
        )
        body = _ensure_low_guven(body)

    if mismatch and mismatch_note:
        body = _append_note_if_missing(body, mismatch_note)
        body = _ensure_low_guven(body)

    if not _GUVEN_RE.search(body):
        try:
            from ilim_assistant.ana_motor_reflection import _has_guven_line

            if not _has_guven_line(body):
                n_src = len(hits or [])
                level = "orta" if (n_src or web_was_used) else "düşük"
                body = body.rstrip() + (
                    f"\n\n**Güven: {level}** — tek beyin bilgi doğrulama (kaynak: {n_src})."
                )
        except Exception:
            pass

    return body, meta


def tek_beyin_bilgi_guard_status() -> dict[str, Any]:
    try:
        min_ov = float(os.environ.get("RUZGAR_TEK_BEYIN_BILGI_MIN_OVERLAP", "0.34"))
    except ValueError:
        min_ov = 0.34
    return {
        "enabled": tek_beyin_bilgi_guard_enabled(),
        "version": TEK_BEYIN_BILGI_GUARD_VERSION,
        "min_topic_overlap": min_ov,
    }
