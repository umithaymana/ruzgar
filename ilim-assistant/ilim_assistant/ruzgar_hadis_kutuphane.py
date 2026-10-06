# -*- coding: utf-8 -*-
"""Rüzgar — hadis anlık cevap (kavram + Kutüb-i Sitte numaralı matın).

Fetva vermez. Kaynak: knowledge/ilim/din/05_hadis/
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "05_hadis"
_KAV = _DIR / "kavramlar_hadis.jsonl"
_SITTE = _DIR / "kutub_i_sitte"

_HADIS_CUES = (
    "hadis",
    "hadîs",
    "sünnet",
    "sunnet",
    "isnad",
    "isnād",
    "sened",
    "kutub",
    "kütüb",
    "kutubi sitte",
    "kütüb-i sitte",
    "sahihayn",
    "sahîhayn",
    "buhari",
    "buhârî",
    "bukhari",
    "muslim",
    "müslim",
    "ebu davud",
    "ebû dâvûd",
    "abu dawud",
    "tirmizi",
    "tirmizî",
    "tirmidhi",
    "nesai",
    "nesâî",
    "nasai",
    "ibn mace",
    "ibn mâce",
    "ibn majah",
    "cerh",
    "tadil",
    "ta'dil",
    "tedvin",
    "rihle",
    "semâ",
    "sema",
    "mustalah",
    "muhaddis",
    "ricâl",
    "rical",
    "mevzu",
    "mevzû",
    "mütevâtir",
    "mutevatir",
    "âhâd",
    "ahad",
    "musned",
    "müsned",
    "musannef",
    "ibn salah",
    "ibnü salah",
    "ibn hacer",
    "nuhbe",
    "nukhba",
    "zuhri",
    "zührî",
)

# eser_id → alias kalıpları (normalize sonrası)
_ESER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("buhari", re.compile(r"\b(buhari|buhâri|buhârî|bukhari)\b")),
    ("muslim", re.compile(r"\b(muslim|müslim|muslim)\b")),
    ("ebu_davud", re.compile(r"\b(ebu\s*davud|ebû\s*dâvûd|abu\s*dawud|ebudavud)\b")),
    ("tirmizi", re.compile(r"\b(tirmizi|tirmizî|tirmidhi)\b")),
    ("nesai", re.compile(r"\b(nesai|nesâî|nasai)\b")),
    ("ibn_mace", re.compile(r"\b(ibn\s*mace|ibn\s*mâce|ibn\s*majah|ibnmace)\b")),
]


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_hadis_question(msg: str) -> bool:
    low = _fold(msg)
    if any(c in low for c in _HADIS_CUES):
        return True
    return False


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
    low = _fold(msg)
    tokens = set(re.findall(r"[\w'’]+", low, flags=re.UNICODE))
    best: Optional[dict[str, Any]] = None
    best_score = 0
    for row in _load_kavramlar():
        keys = [_fold(row.get("baslik") or "")]
        keys.extend(_fold(a) for a in (row.get("aliases") or []))
        score = 0
        for k in keys:
            if not k:
                continue
            if k == low or low == f"{k} nedir" or low.startswith(f"{k} nedir"):
                score = max(score, 100)
            elif k in low:
                score = max(score, 60 + min(20, len(k)))
            elif k in tokens:
                score = max(score, 40)
        if score > best_score:
            best_score = score
            best = row
    if best_score >= 40:
        return best
    return None


def format_hadis_kavram_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "hadis").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


@lru_cache(maxsize=8)
def _load_eser_bundles(eser_id: str) -> tuple[dict[int, dict[str, Any]], list[dict[str, Any]]]:
    """(hadithnumber→satır, dosya sırası listesi)."""
    path = _SITTE / eser_id / "hadisler.jsonl"
    by_num: dict[int, dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    if not path.is_file():
        return by_num, ordered
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ordered.append(row)
            hn = row.get("hadithnumber")
            try:
                key = int(hn)
            except (TypeError, ValueError):
                continue
            if key not in by_num:
                by_num[key] = row
    return by_num, ordered


def _load_eser_index(eser_id: str) -> dict[int, dict[str, Any]]:
    return _load_eser_bundles(eser_id)[0]


def _detect_eser(low: str) -> Optional[str]:
    for eser_id, pat in _ESER_PATTERNS:
        if pat.search(low):
            return eser_id
    return None


def _detect_number(msg: str) -> Optional[int]:
    m = re.search(
        r"(?:hadis(?:\s*no)?|no|#)\s*[:.]?\s*(\d{1,5})\b",
        msg,
        flags=re.IGNORECASE,
    )
    if m:
        return int(m.group(1))
    m = re.search(
        r"\b(?:buhari|buhârî|bukhari|muslim|müslim|tirmizi|tirmizî|"
        r"nesai|nesâî|nasai|ebu\s*davud|ibn\s*mace|ibn\s*mâce|ibn\s*majah)"
        r"\s*[:.]?\s*(\d{1,5})\b",
        msg,
        flags=re.IGNORECASE,
    )
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{1,5})\s*\.?\s*hadis\b", msg, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def format_hadis_matn_reply(row: dict[str, Any]) -> str:
    eser = (row.get("eser_tr") or row.get("eser_id") or "").strip()
    hn = row.get("hadithnumber")
    book = row.get("book")
    section = (row.get("section") or "").strip()
    text = (row.get("text_ar") or "").strip()
    head = f"**{eser} — {hn}**"
    if book is not None:
        head += f" · kitâb {book}"
        if section:
            head += f" ({section})"
    parts = [
        head,
        "",
        text,
        "",
        "_Kaynak: Kutüb-i Sitte Arapça matın (hadith-api). Fetva değildir._",
    ]
    return "\n".join(parts).strip()


def _resolve_hadis_row(eser_id: str, num: int) -> Optional[dict[str, Any]]:
    by_num, ordered = _load_eser_bundles(eser_id)
    if num in by_num:
        return by_num[num]
    # Müslim vb. API boşluklu numaralandırma: sıradaki N. hadis
    if 1 <= num <= len(ordered):
        return ordered[num - 1]
    return None


def try_hadis_number_reply(msg: str) -> Optional[str]:
    low = _fold(msg)
    eser = _detect_eser(low)
    num = _detect_number(msg)
    if not eser or num is None:
        return None
    row = _resolve_hadis_row(eser, num)
    if not row:
        return (
            f"Ümit abi, `{eser}` raftında **{num}** numaralı hadis bulunamadı. "
            "Örnek: «buhari 1», «muslim 1» (sıradaki ilk matın)."
        )
    return format_hadis_matn_reply(row)


def try_hadis_reply(msg: str) -> Optional[str]:
    """Hadis niyeti: önce numaralı matın, sonra kavram."""
    if not (msg or "").strip():
        return None
    numbered = try_hadis_number_reply(msg)
    if numbered:
        return numbered
    low = _fold(msg)
    is_cue = looks_like_hadis_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "kimdir", "anlat", "nelerdir", "ne demektir"))
    if not is_cue and not ask:
        return None
    row = _match_kavram(msg)
    if row:
        return format_hadis_kavram_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "hadis":
                return format_hadis_kavram_reply(r)
    return None
