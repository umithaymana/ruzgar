# -*- coding: utf-8 -*-
"""Rüzgar — soru/cevap anlam koruması (kelime karıştırma kilidi).

Fuzzy SequenceMatcher ve oturum yankısı, benzer uzunluktaki «X nedir / Y nedir»
çiftlerini karıştırabiliyor. Bu modül tek kural koyar:

  Sorgudaki anlamlı içerik kelimesi aday soruda (veya cevapta) yoksa → RED.

Yama listesi değil; tüm hafıza / yankı yolları bunu kullanır.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable

_STOP = frozenset(
    {
        "ne",
        "mi",
        "mu",
        "misin",
        "musun",
        "bir",
        "bu",
        "su",
        "o",
        "ve",
        "veya",
        "ama",
        "fakat",
        "icin",
        "için",
        "de",
        "da",
        "ki",
        "ya",
        "ile",
        "den",
        "dan",
        "yi",
        "yu",
        "i",
        "u",
        "nedir",
        "nedemek",
        "kimdir",
        "kimdi",
        "kim",
        "kimi",
        "kimesne",
        "hangisi",
        "nasil",
        "nasıl",
        "neden",
        "niye",
        "abi",
        "ben",
        "sen",
        "bana",
        "sana",
        "benim",
        "senin",
        "lutfen",
        "lütfen",
        "acaba",
        "yani",
        "gibi",
        "kadar",
        "cok",
        "çok",
        "az",
        "var",
        "yok",
        "olan",
        "olarak",
        "hakkinda",
        "hakkında",
        "uzere",
        "üzere",
        "ise",
        "midir",
        "mudur",
        "anlat",
        "acikla",
        "açıkla",
        "soyle",
        "söyle",
        "ver",
        "oku",
        "bak",
    }
)

_TR = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "Ş": "s",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    }
)

_TOKEN_SIM = 0.86


def fold_ascii(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip()).casefold()
    t = t.translate(_TR)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def content_tokens(text: str, *, min_len: int = 3) -> frozenset[str]:
    """Stopword'siz içerik kelimeleri (ASCII fold)."""
    raw = fold_ascii(text)
    if not raw:
        return frozenset()
    out: set[str] = set()
    for w in raw.split():
        if len(w) < min_len or w in _STOP:
            continue
        out.add(w)
    return frozenset(out)


def _token_hit(needle: str, haystack: Iterable[str]) -> bool:
    if needle in haystack:
        return True
    for h in haystack:
        if SequenceMatcher(None, needle, h).ratio() >= _TOKEN_SIM:
            return True
        # Kısa kök: maturidi ⊂ maturidilik
        if len(needle) >= 4 and (needle in h or h in needle) and min(len(needle), len(h)) >= 4:
            if abs(len(needle) - len(h)) <= 4:
                return True
    return False


def content_overlap_count(a: str, b: str) -> int:
    ta = content_tokens(a)
    tb = content_tokens(b)
    if not ta or not tb:
        return 0
    n = 0
    for t in ta:
        if _token_hit(t, tb):
            n += 1
    return n


def questions_share_content(sorgu: str, aday_soru: str) -> bool:
    """Fuzzy aday: sorgunun anlam kelimesi(leri) adayda olmalı.

    - Tek içerik kelime («tefsir nedir», «maturidi kimdir») → o kelime zorunlu.
    - Çok kelime → en uzun kelime + en az yarısı örtüşmeli.
    Karakter benzerliği tek başına yetmez.
    """
    toks = content_tokens(sorgu)
    if not toks:
        return False
    aday = content_tokens(aday_soru)
    if not aday:
        return False
    if len(toks) == 1:
        return _token_hit(next(iter(toks)), aday)
    hits = sum(1 for t in toks if _token_hit(t, aday))
    if hits <= 0:
        return False
    longest = max(toks, key=len)
    if len(longest) >= 4 and not _token_hit(longest, aday):
        return False
    return hits >= max(1, (len(toks) + 1) // 2)


def answer_fits_question(sorgu: str, cevap: str) -> bool:
    """Yankı / hafıza cevabı sorunun içerik kelimesini taşımalı.

    İstisna: asistan kimliği cevabı («rüzgar» + mimar).
    """
    ans = (cevap or "").strip()
    if len(ans) < 8:
        return False
    q_fold = fold_ascii(sorgu)
    a_fold = fold_ascii(ans)

    # Kimlik soruları
    if re.search(r"\b(adin|ismin|kimsin|nesin)\b", q_fold) or re.search(
        r"\bsenin\s+ad", q_fold
    ):
        return "ruzgar" in a_fold or "rüzgar" in (cevap or "").casefold()

    # «X nedir» tanım sorusu → kaynak/takip cevabı olmasın
    if re.search(r"\bnedir\b", q_fold) and not re.search(
        r"\b(kimden|hangi\s+kitap|hangi\s+eser|nereden\s+okud)\b", q_fold
    ):
        if re.search(
            r"\b(kimden\s+ald|hangi\s+kitaba|web\s+taramasi|guncellik)\b", a_fold
        ):
            return False

    toks = content_tokens(sorgu, min_len=4)
    if not toks:
        toks = content_tokens(sorgu, min_len=3)
    if not toks:
        return True  # içerik yoksa engelleme

    ans_toks = content_tokens(ans, min_len=3)
    for t in toks:
        if _token_hit(t, ans_toks):
            return True
        if len(t) >= 4 and t in a_fold:
            return True
    return False


def fuzzy_pair_allowed(sorgu: str, aday_soru: str) -> bool:
    """Hafıza fuzzy eşleşmesi için tek kapı."""
    return questions_share_content(sorgu, aday_soru)


def rag_default_score_min() -> float:
    """Bilgi RAG taban eşiği — düşük skor alakasız chunk getiriyordu."""
    import os

    raw = (os.environ.get("RAG_SCORE_MIN") or "0.32").strip()
    try:
        v = float(raw)
    except ValueError:
        v = 0.32
    return max(0.0, min(1.0, v))


def chunk_fits_query(sorgu: str, chunk_text: str) -> bool:
    """RAG parçası sorunun anlam kelimesini taşıyor mu?"""
    toks = content_tokens(sorgu, min_len=4)
    if not toks:
        toks = content_tokens(sorgu, min_len=3)
    if not toks:
        return True
    blob = fold_ascii(chunk_text or "")
    if not blob:
        return False
    ctoks = content_tokens(chunk_text or "", min_len=3)
    for t in toks:
        if _token_hit(t, ctoks):
            return True
        if len(t) >= 4 and t in blob:
            return True
    return False


def filter_rag_hits(
    sorgu: str,
    hits: list,
    *,
    min_score: float | None = None,
    soft: bool = False,
) -> list:
    """(metin, kaynak, skor) listesini skor + anlam kelimesiyle süz.

    soft=True: anlam süzgeci boşaltırsa skora göre ilk 1–2 zayıf adayı bırakır
    (eski davranışa yakın yedek). Varsayılan hard: boş liste > yanlış bağlam.
    """
    if not hits:
        return []
    floor = rag_default_score_min() if min_score is None else float(min_score)
    scored = []
    for h in hits:
        try:
            text, src, sc = h[0], h[1], float(h[2])
        except Exception:
            continue
        if sc < floor:
            continue
        scored.append((text, src, sc))
    if not scored:
        return []

    fitted = [h for h in scored if chunk_fits_query(sorgu, h[0])]
    if fitted:
        return fitted
    if soft and scored:
        return scored[:2]
    return []


def looks_like_grounded_fact_question(sorgu: str) -> bool:
    """Tanım / kimdir / ansiklopedik — cevapsız uydurma yasak sınıfı."""
    q = fold_ascii(sorgu)
    if not q:
        return False
    if re.search(r"\b(nedir|nedemek|kimdir|kimdi|hangisi|kac|kaç)\b", q):
        return True
    if re.search(r"\b(ne\s+demek|ne\s+anlama)\b", q):
        return True
    return False


def guard_assistant_reply(sorgu: str, cevap: str) -> str | None:
    """Anlam uyumsuz bilgi cevabını düşür; None = cevap kullanılamaz.

    Kimlik / selam / kısa sohbet dokunulmaz.
    """
    ans = (cevap or "").strip()
    if not ans or len(ans) < 12:
        return ans or None
    if not looks_like_grounded_fact_question(sorgu):
        return ans
    # Zaten reddedilmiş / düşük güven notu
    low = fold_ascii(ans)
    if "guven: dusuk" in low and "anlam" in low:
        return ans
    if answer_fits_question(sorgu, ans):
        return ans
    q_short = " ".join((sorgu or "").split())[:100]
    return (
        f"Ümit abi, «{q_short}» için bağladığım kaynaklar soruyla örtüşmedi; "
        "uydurmak yerine duruyorum. Soruyu biraz netleştirir veya «webten ara» "
        "dersen yeniden bakarım.\n\n"
        "**Güven: düşük** — anlam doğrulama (RAG/LLM koruma)."
    )

