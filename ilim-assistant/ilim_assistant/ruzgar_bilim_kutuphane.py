# -*- coding: utf-8 -*-
"""Rüzgar — bilim anlık cevap (Faz 1+2).

Kaynak: knowledge/ortak_kaynak/alanlar/bilim/
Tıbbi teşhis değildir. Fetva yok.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilim"
_KAV = _DIR / "kavramlar_bilim.jsonl"

_CUES = (
    "bilim",
    "astronomi",
    "uzay",
    "gunes sistemi",
    "güneş sistemi",
    "galaksi",
    "samanyolu",
    "fizik",
    "kimya",
    "atom",
    "enerji",
    "elektrik",
    "biyoloji",
    "hucre",
    "hücre",
    "fotosentez",
    "ekosistem",
    "matematik",
    "geometri",
    "bilimsel yontem",
    "bilimsel yöntem",
    "hipotez",
    "islam bilim",
    "islâm bilim",
    "harizmi",
    "hârizmî",
    "ibn heysem",
    "optik",
    "kara delik",
    "karadelik",
    "dna",
    "genetik",
    "yildiz",
    "yıldız",
    "buyuk patlama",
    "büyük patlama",
    "ay evre",
    "gelgit",
    "tutulma",
    "newton",
    "kuvvet",
    "asit",
    "baz",
    "ph",
    "isi",
    "sıcaklık",
    "dalga",
    "ses",
    "solunum",
    "sindirim",
    "evrim",
    "yuzde",
    "yüzde",
    "denklem",
    "olasilik",
    "olasılık",
    "molekul",
    "periyodik",
    "atmosfer",
    "troposfer",
    "gps",
    "yapay uydu",
    "ohm",
    "direnc",
    "direnç",
    "madde halleri",
    "organeller",
    "mitokondri",
    "kalitim",
    "kalıtım",
    "mendel",
    "bagisiklik",
    "bağışıklık",
    "oran",
    "oranti",
    "orantı",
    "ortalama",
    "medyan",
    "ucgen",
    "üçgen",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_bilim_question(msg: str) -> bool:
    low = _fold(msg)
    return any(_fold(c) in low for c in _CUES)


def _norm_query(msg: str) -> str:
    low = _fold(msg)
    low = re.sub(r"[-_/]+", " ", low)
    return re.sub(r"\s+", " ", low).strip()


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


def _match_kavram(msg: str) -> Optional[dict[str, Any]]:
    from ilim_assistant.ruzgar_kavram_match import match_kavram_row

    return match_kavram_row(msg, _load_kavramlar())


def format_bilim_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "bilim").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_bilim_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_bilim_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "kimdir", "hangi", "nasil", "nasıl"))
    if not is_cue and not ask:
        return None
    # Alan ipucu yokken yalnızca güçlü eşleşme (yanlış rafa düşmeyi kes)
    from ilim_assistant.ruzgar_kavram_match import match_kavram_row

    row = match_kavram_row(msg, _load_kavramlar(), min_score=55 if is_cue else 70)
    if row:
        return format_bilim_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "bilim":
                return format_bilim_reply(r)
    return None
