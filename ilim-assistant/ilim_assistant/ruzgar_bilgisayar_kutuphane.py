# -*- coding: utf-8 -*-
"""Rüzgar — bilgisayar mühendisliği anlık cevap (Faz 16).

Kaynak: knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi/
Eğitim. Saldırı/exploit tarifi yok.
"""
from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_muhendisligi"
_KAV = _DIR / "kavramlar_bilgisayar.jsonl"

_CUES = (
    "bilgisayar muhendis",
    "bilgisayar mühendis",
    "sayisal mantik",
    "sayısal mantık",
    "dijital mantik",
    "dijital mantık",
    "mantik kapisi",
    "mantık kapısı",
    "islemci",
    "işlemci",
    "komut seti",
    "bellek hiyerars",
    "bellek hiyerarş",
    "onbellek",
    "önbellek",
    "veri yolu",
    "von neumann",
    "kesme",
    "cevre birimi",
    "çevre birimi",
    "saat darbesi",
    "kati hal",
    "katı hal",
    "sabit disk",
    "ayrik matematik",
    "ayrık matematik",
    "boolean cebir",
    "transistor",
    "transistör",
    "isletim cekirdegi",
    "işletim çekirdeği",
    "kernel",
    "sistem cagrisi",
    "sistem çağrısı",
    "proses",
    "sanal bellek",
    "sayfa tablosu",
    "dosya sistemi",
    "derleyici",
    "baglayici",
    "bağlayıcı",
    "ag yigini",
    "ağ yığını",
    "veri yapisi",
    "veri yapısı",
    "bagli liste",
    "bağlı liste",
    "cagri yigini",
    "çağrı yığını",
    "ikili arama",
    "hash tablosu",
    "birim testi",
    "hata ayiklama",
    "hata ayıklama",
    "surum kontrol",
    "sürüm kontrol",
    "yazilim tasarim",
    "yazılım tasarım",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_bilgisayar_question(msg: str) -> bool:
    low = _fold(msg)
    return any(_fold(c) in low for c in _CUES)


@lru_cache(maxsize=1)
def _load_kavramlar() -> list[dict[str, Any]]:
    if not _KAV.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in _KAV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def format_bilgisayar_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "bilgisayar").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


_CODE_TASK_BITS = (
    "@@",
    "pytest",
    "traceback",
    ".py",
    "refactor",
    "patch",
    "def ",
    "class ",
    "gorev:",
    "görev:",
)

_CONCEPT_ASK = (
    "nedir",
    "ne demek",
    "anlat",
    "acikla",
    "açıkla",
    "nasil",
    "nasıl",
    "farki",
    "farkı",
)


def programlama_kavram_notu(msg: str) -> str:
    """Programlama turu kavram sorusunda raf notu. Kod görevine karışmaz."""
    raw = (msg or "").strip()
    if not raw or len(raw) > 400:
        return ""
    low = _fold(raw)
    if any(bit in low for bit in _CODE_TASK_BITS):
        return ""
    if not any(p in low for p in _CONCEPT_ASK):
        return ""
    hit = try_bilgisayar_reply(raw)
    if not hit:
        return ""
    return (
        "[BİLGİSAYAR MÜHENDİSLİĞİ NOTU — dahili; kullanıcıya aynen okuma]\n"
        "Kavram notunu kendi cümlelerinle anlat. İstenirse kısa eğitim örneği yaz. "
        "Saldırı, exploit veya zararlı kod üretme.\n\n"
        + hit
    )


def try_bilgisayar_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_bilgisayar_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "nasil", "nasıl"))
    if not is_cue and not ask:
        return None
    from ilim_assistant.ruzgar_kavram_match import match_kavram_row

    row = match_kavram_row(msg, _load_kavramlar(), min_score=55 if is_cue else 70)
    if row:
        return format_bilgisayar_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "bilgisayar_muhendisligi":
                return format_bilgisayar_reply(r)
    return None
