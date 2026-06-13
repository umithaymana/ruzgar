# Created by Ümit & Gökçenur
"""Tek beyin — konuşma akışı: meta geri bildirim, web ara, akıştan öğrenme."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional

TEK_BEYIN_KONUSMA_VERSION = "tek-beyin-konusma-v2-2026-06-13-faz-o"

_META_FEEDBACK = re.compile(
    r"(?:"
    r"saçmalama|sacmalama|saçmalıyor|sacmaliyor|"
    r"düzgün\s+cevap|duzgun\s+cevap|"
    r"yanlış\s+cevap|yanlis\s+cevap|"
    r"robot\s+gibi|"
    r"ne\s+dediğimi\s+anla|ne\s+dedigimi\s+anla|"
    r"konuşmanın\s+akış|konusmanin\s+akis|"
    r"aptal|saçma\s+soru|sacma\s+soru"
    r")",
    re.I,
)
_REFUSE_TEACH = re.compile(
    r"(?:"
    r"öğretmeyeceğim|ogretmeyecegim|"
    r"öğretmem|ogretmem|"
    r"sana\s+öğretmeyeceğim|sana\s+ogretmeyecegim|"
    r"bana\s+öğretme|bana\s+ogretme"
    r")",
    re.I,
)
_WEB_RESEARCH_CMD = re.compile(
    r"(?:"
    r"web(?:'?ten|ten)?\s+ara|"
    r"internet(?:ten)?\s+ara|"
    r"internet(?:ten)?\s+bak|"
    r"kendin\s+(?:web|internet).{0,24}(?:ara|bul|bak)|"
    r"(?:ara|bul)\s+(?:web|internet)|"
    r"araştır\s+(?:web|internet)|"
    r"arastir\s+(?:web|internet)|"
    r"öğren\s+bana\s+anlat|ogren\s+bana\s+anlat|"
    r"doğrusunu\s+anlat|dogrusunu\s+anlat|"
    r"doğru\s+cevabı\s+bul|dogru\s+cevab[iı]\s+bul"
    r")",
    re.I,
)
_FLOW_TEACH = re.compile(
    r"(?is)(?:"
    r"(?:cevab[ıi]n|cevabin)\s+(?:bu|şu|su)\b|"
    r"(?:cevab[ıi]n|cevabin)\s+şöyle(?:dir|)|"
    r"(?:cevab[ıi]n|cevabin)\s+şu\s+olmalı|"
    r"^doğru\s+cevap\s*[:\-–]|^dogru\s+cevap\s*[:\-–]|"
    r"^cevap\s+(?:bu|şu|su)\b|"
    r"^cevap\s*[:\-–]|"
    r"bunun\s+cevabı\s+(?:bu|şu|su)|"
    r"bundan\s+sonra\s+(?:böyle|soyle)|"
    r"işte\s+cevap|iste\s+cevap|"
    r"bu\s+sorunun\s+cevab[ıi]\s+(?:bu|şu|su)|"
    r"doğrusu\s+şu|dogrusu\s+su|"
    r"hatırla\s*[:\-–]|hatirla\s*[:\-–]|"
    r"hafızaya\s+al\s*[:\-–]|hafizaya\s+al\s*[:\-–]|"
    r"şöyledir|soyledir|böyledir|boyledir|"
    r"bu\s+şudur|bu\s+sudur"
    r")",
)
_SKIP_HISTORY = frozenset(
    {
        "günaydın",
        "gunaydin",
        "merhaba",
        "selam",
        "hey",
        "naber",
    }
)


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def looks_like_meta_feedback(message: str) -> bool:
    raw = (message or "").strip()
    if len(raw) < 10:
        return False
    return bool(_META_FEEDBACK.search(_norm(raw)))


def looks_like_refuse_to_teach(message: str) -> bool:
    return bool(_REFUSE_TEACH.search(_norm(message or "")))


def looks_like_web_research_command(message: str) -> bool:
    raw = (message or "").strip()
    if len(raw) < 12:
        return False
    return bool(_WEB_RESEARCH_CMD.search(_norm(raw)))


def looks_like_flow_teaching(message: str) -> bool:
    raw = (message or "").strip()
    if len(raw) < 8:
        return False
    if looks_like_refuse_to_teach(raw) or looks_like_web_research_command(raw):
        return False
    if looks_like_meta_feedback(raw):
        return False
    return bool(_FLOW_TEACH.search(raw))


def _history_user_lines(client_history: list | None) -> list[str]:
    out: list[str] = []
    if not client_history:
        return out
    for item in client_history:
        if isinstance(item, dict):
            if str(item.get("role") or "").strip().lower() == "user":
                u = str(item.get("content") or "").strip()
                if u:
                    out.append(u)
    return out


def _is_bilgi_candidate(text: str) -> bool:
    raw = (text or "").strip()
    if len(raw) < 4 or len(raw) > 500:
        return False
    if looks_like_meta_feedback(raw) or looks_like_web_research_command(raw):
        return False
    if looks_like_refuse_to_teach(raw):
        return False
    blob = _norm(raw)
    if blob in _SKIP_HISTORY:
        return False
    try:
        from ilim_assistant.ana_motor_plan import _explicit_research_intent

        if _explicit_research_intent(raw):
            return True
    except Exception:
        pass
    if re.search(r"\b(kimdir|kimdi|nedir|ne zaman|nerede|kaç|kac)\b", blob):
        return True
    if re.search(r"\batatürk\b|\bataturk\b", blob):
        return True
    if len(raw.split()) >= 2 and not looks_like_meta_feedback(raw):
        if any(w[0].isupper() for w in raw.split()[:3] if len(w) > 2):
            return True
    return False


def resolve_bilgi_target_from_history(
    message: str,
    client_history: list | None = None,
) -> str:
    """«Webten ara bul» — asıl bilgi sorusunu geçmişten çıkar."""
    try:
        from ilim_assistant.ruzgar_egitim import get_pending

        pend = get_pending()
        pending_soru = str(pend.get("soru") or "").strip()
        if pending_soru and _is_bilgi_candidate(pending_soru):
            return pending_soru
    except Exception:
        pass
    for u in reversed(_history_user_lines(client_history)):
        if u == (message or "").strip():
            continue
        if _is_bilgi_candidate(u):
            return u
    m = re.sub(
        r"(?is).*(?:web(?:'?ten|ten)?\s+ara|internet(?:ten)?\s+ara|kendin\s+web).*$",
        "",
        (message or "").strip(),
    ).strip(" .,;:")
    if m and _is_bilgi_candidate(m):
        return m
    return ""


def try_meta_feedback_reply(
    message: str,
    client_history: list | None = None,
) -> str | None:
    if not looks_like_meta_feedback(message):
        return None
    try:
        from ilim_assistant.ruzgar_egitim import clear_pending

        clear_pending()
    except Exception:
        pass
    target = resolve_bilgi_target_from_history(message, client_history)
    lines = [
        "Haklısın Ümit abi — önceki yanıt yamuk gitmiş, fark ettim.",
    ]
    if target:
        lines.append(
            f"Konu «{target[:100]}» — istersen şimdi web'den tarayıp "
            "doğru cevabı toparlayayım; «webten ara bul» demen yeterli."
        )
    else:
        lines.append(
            "Ne sorduğunu netleştirirsen veya «webten ara bul» dersen "
            "hemen araştırıp düzgün anlatırım."
        )
    return "\n".join(lines)


def try_web_research_ack(
    message: str,
    client_history: list | None = None,
) -> str | None:
    """Anında onay — asıl araştırma boru hattında yapılır."""
    if not looks_like_web_research_command(message):
        return None
    try:
        from ilim_assistant.ruzgar_egitim import clear_pending

        clear_pending()
    except Exception:
        pass
    target = resolve_bilgi_target_from_history(message, client_history)
    if not target:
        return (
            "Ümit abi, web'den arayacağım konuyu netleştiremedim — "
            "hangi sorunun cevabını bulmamı istiyorsun? Kısaca tekrar yaz."
        )
    return (
        f"Tamam Ümit abi — «{target[:110]}» için web'den araştırıyorum; "
        "kaynaklara bakıp doğru cevabı anlatacağım."
    )


def try_flow_teaching_reply(
    message: str,
    client_history: list | None = None,
) -> str | None:
    """«Cevap bu», «hatırla:», «şöyledir» — akıştan öğrenme."""
    if not looks_like_flow_teaching(message):
        return None
    raw = (message or "").strip()
    soru = ""
    cevap = ""
    try:
        from ilim_assistant.ruzgar_egitim import _last_user_question, save_teaching_pair

        soru = _last_user_question(client_history or [])
        try:
            from ilim_assistant.ruzgar_egitim import get_pending

            pend = get_pending()
            if str(pend.get("soru") or "").strip():
                soru = str(pend.get("soru") or "").strip()
        except Exception:
            pass
    except Exception:
        pass

    body = raw
    for pat in (
        r"(?is)(?:cevab[ıi]n|cevabin)\s+(?:bu|şu|su)\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)(?:cevab[ıi]n|cevabin)\s+şöyle(?:dir)?\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)(?:cevab[ıi]n|cevabin)\s+şu\s+olmalı\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)^doğru\s+cevap\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)^cevap\s+(?:bu|şu|su)\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)^cevap\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)^hat[ıi]rla\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)^haf[ıi]zaya\s+al\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)bunun\s+cevabı\s+(?:bu|şu|su)\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)bu\s+sorunun\s+cevab[ıi]\s+(?:bu|şu|su)\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)(?:doğrusu|dogrusu)\s+şu\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)(?:işte|iste)\s+cevap\s*[:\-–]?\s*(?P<a>.+)$",
        r"(?is)bundan\s+sonra\s+(?:böyle|soyle)\s+(?:cevap\s+ver\s*)?[:\-–]?\s*(?P<a>.+)$",
    ):
        m = re.search(pat, raw)
        if m:
            cevap = (m.group("a") or "").strip()
            break
    if not cevap:
        m = re.search(r"(?is)(?:şöyledir|soyledir|böyledir|boyledir)\s*[:\-]?\s*(?P<a>.+)$", raw)
        if m:
            cevap = (m.group("a") or "").strip()
    if not cevap or len(cevap) < 4:
        return None
    if not soru:
        try:
            from ilim_assistant.ruzgar_egitim import _load_durum

            soru = str(_load_durum().get("last_soru") or "").strip()
        except Exception:
            pass
    if not soru:
        soru = cevap[:80]
    try:
        from ilim_assistant.ruzgar_egitim import save_teaching_pair

        return save_teaching_pair(soru, cevap, correction=True, baglam_soru=soru)
    except Exception:
        return (
            f"Ümit abi, not aldım — «{soru[:60]}» için: {cevap[:180]}"
        )


def tek_beyin_konusma_status() -> dict[str, Any]:
    return {
        "version": TEK_BEYIN_KONUSMA_VERSION,
        "flow_teaching": True,
        "meta_feedback": True,
        "web_cmd": True,
    }
