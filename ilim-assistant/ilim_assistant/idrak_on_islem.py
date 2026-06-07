# Created by Ümit & Gökçenur
"""
Faz 11 — İdrak yüzey ön-işlemi (LLM yok).

Amaç: birleşik yazım ve sık yazım kaymalarında hafif düzeltme; planlama ve
RAG sorgusu daha tutarlı metin görsün.

Kapatma: RUZGAR_IDRAK_PRETREAT=0
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Any


def pretreat_enabled() -> bool:
    return os.environ.get("RUZGAR_IDRAK_PRETREAT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


# (regex pattern, replacement) — kelime sınırı + Unicode
_WORD_FIXES: tuple[tuple[str, str], ...] = (
    (r"\bbirşey\b", "bir \u015fey"),
    (r"\bbirsey\b", "bir \u015fey"),
    (r"\bhiçbirşey\b", "hi\u00e7bir \u015fey"),
    (r"\bherşey\b", "her \u015fey"),
    (r"\bherşeyi\b", "her \u015feyi"),
    (r"\bbirşekilde\b", "bir \u015fekilde"),
    (r"\bherhangibir\b", "herhangi bir"),
    (r"\bbeneksik\b", "bence eksik"),  # konuşma / yazım kayması
)

_COMPILED: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p, re.IGNORECASE | re.UNICODE), r) for p, r in _WORD_FIXES
)


@dataclass(frozen=True)
class PretreatResult:
    """Ön-işlem çıktısı (meta + düz metin)."""

    text: str
    changed: bool
    replacements: tuple[str, ...]
    continuation: bool = False


def _last_meaningful_history_text(history: list[Any] | None) -> str:
    """Son kullanıcı/asistan cümlesinden kısa bağlam al; devam komutları için."""
    for row in reversed(history or []):
        if not isinstance(row, dict):
            continue
        txt = str(row.get("content") or "").strip()
        if txt:
            return txt[:320]
    return ""


def _expand_continuation(raw: str, history: list[Any] | None) -> tuple[str, bool]:
    low = raw.strip().casefold().strip(" .,!?\t\r\n")
    exact_cues = {
        "devam",
        "devam et",
        "aynen devam",
        "aynısı",
        "aynisi",
        "öyle yap",
        "oyle yap",
        "bunu yap",
        "onu yap",
        "sunu yap",
        "şunu yap",
        "tamam devam",
        "plana devam et",
        "yukarıdaki",
        "yukardaki",
        "yukaridaki",
        "az önce",
        "az once",
        "dediğim gibi",
        "dedigim gibi",
        "sen yap",
        "hallet",
    }
    prefix_cues = (
        "yukarıdaki",
        "yukardaki",
        "yukaridaki",
        "az önce",
        "az once",
        "dediğim",
        "dedigim",
        "söylediğim",
        "soyledigim",
        "bahsettiğim",
        "bahsettigim",
        "anlattığım",
        "anlattigim",
        "bunu ",
        "onu ",
        "şunu ",
        "sunu ",
    )
    is_cont = low in exact_cues or any(low.startswith(p) for p in prefix_cues)
    if not is_cont:
        return raw, False
    ctx = _last_meaningful_history_text(history)
    if not ctx:
        return raw, False
    return (
        f"{raw}\n\n[İdrak bağlamı: Bu kısa devam ifadesi önceki bağlama bağlıdır. "
        f"Önceki bağlam özeti: {ctx}]",
        True,
    )


def pretreat_user_turn(message: str | None, history: list[Any] | None = None) -> PretreatResult:
    """
    Kullanıcı mesajını hafifçe normalize eder. `history` şimdilik rezervedir
    (Faz 11.1: devam cümlesi genişletmesi için).
    """
    raw = (message or "").strip()
    if not pretreat_enabled() or not raw:
        return PretreatResult(text=raw, changed=False, replacements=())

    s = unicodedata.normalize("NFKC", raw)
    s = re.sub(r"\s+", " ", s).strip()

    reps: list[str] = []
    for pat, repl in _COMPILED:
        s2, n = pat.subn(repl, s)
        if n:
            reps.append(f"{pat.pattern}->{repl}")
        s = s2

    s, cont = _expand_continuation(s, history)
    if cont:
        reps.append("continuation->history_context")

    changed = s != raw
    return PretreatResult(
        text=s,
        changed=changed,
        replacements=tuple(reps),
        continuation=cont,
    )
