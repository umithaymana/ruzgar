# Created by Ümit & Gökçenur
"""
Rüzgar — soru / STT / klavye niyet düzeltme.

Amaç (Mimar): Yanlış yazılsa, otomatik tamamlansa veya ses→metin bozulsa bile
«ne demek istedi»yi yakala; RAG + LLM + bilgi-guard düzeltilmiş niyetle çalışsın.

Kapat: RUZGAR_SORU_YAZIM=0
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any

FAZ_YAZIM_VERSION = "soru-yazim-niyet-v2-2026-11-17"

# Sık bilgi / sohbet terimleri (bilinçli liste; ekstra JSON ile büyütülür)
_CORE_TERMS: tuple[str, ...] = (
    # fen
    "fotosentez",
    "fotosentezi",
    "solunum",
    "klorofil",
    "mitokondri",
    "protein",
    "molekul",
    "molekül",
    "elektron",
    "atom",
    "dna",
    "rna",
    "yercekimi",
    "yerçekimi",
    "evren",
    "galaksi",
    "gezegen",
    "gunes",
    "güneş",
    "ay",
    "dünya",
    "dunya",
    "hubble",
    "newton",
    "einstein",
    "enerji",
    "kuvvet",
    "ivme",
    "hiz",
    "hız",
    "sicaklik",
    "sıcaklık",
    "basinc",
    "basınç",
    "elektrik",
    "manyetizma",
    "kimya",
    "fizik",
    "biyoloji",
    "matematik",
    # tarih / kültür
    "osmanli",
    "osmanlı",
    "selcuklu",
    "selçuklu",
    "byzans",
    "bizans",
    "roma",
    "istanbul",
    "ankara",
    "erzurum",
    "izmir",
    "bursa",
    "konya",
    "trabzon",
    "lale",
    "devri",
    "cumhuriyet",
    "inkilap",
    "inkılap",
    "atatürk",
    "ataturk",
    "fatih",
    "kanuni",
    "yavuz",
    # din / ilim
    "peygamber",
    "muhammed",
    "hadis",
    "kuran",
    "kur'an",
    "ayet",
    "sure",
    "sûre",
    "namaz",
    "oruç",
    "oruc",
    "zakat",
    "zekat",
    "hac",
    "iman",
    "islam",
    "müslüman",
    "musluman",
    "sahabe",
    "buhari",
    "buhârî",
    "müslim",
    "muslim",
    "tefsir",
    "meal",
    "fıkıh",
    "fikh",
    "akaid",
    "tasavvuf",
    "mevlana",
    "yunus",
    # teknoloji / asistan
    "yapay",
    "zeka",
    "bilgisayar",
    "programlama",
    "python",
    "javascript",
    "ruzgar",
    "rüzgar",
    "ollama",
    "gemini",
    "whisper",
    "mikrofon",
    "kamera",
)

# STT / klavye sık kalıplar → hedef
_PHRASE_FIXES: tuple[tuple[str, str], ...] = (
    (r"\bfoto\s*sen\s*rez\b", "fotosentez"),
    (r"\bfoto\s*sentez\b", "fotosentez"),
    (r"\bfoto\s*senrez\b", "fotosentez"),
    (r"\bfotosntez\b", "fotosentez"),
    (r"\bfotosentezı\b", "fotosentezi"),
    (r"\bosman\s*li\b", "osmanlı"),
    (r"\bosman\s*lı\b", "osmanlı"),
    (r"\bselcuk\s*lu\b", "selçuklu"),
    (r"\bpey\s*gamber\b", "peygamber"),
    (r"\byapay\s*zek[aâ]\b", "yapay zeka"),
    (r"\brüz\s*gar\b", "rüzgar"),
    (r"\bruz\s*gar\b", "rüzgar"),
    (r"\bkur\s*an\b", "kuran"),
    (r"\bata\s*türk\b", "atatürk"),
    (r"\bata\s*turk\b", "ataturk"),
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_SORU_YAZIM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("ı", "i").replace("İ", "i").lower().strip()


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _data_extra_terms() -> tuple[str, ...]:
    try:
        p = Path(__file__).resolve().parent / "data" / "soru_yazim_terimler.json"
        if not p.is_file():
            return ()
        raw = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return tuple(str(x).strip() for x in raw if str(x).strip())
        if isinstance(raw, dict):
            items = raw.get("terms") or raw.get("terimler") or []
            return tuple(str(x).strip() for x in items if str(x).strip())
    except Exception:
        return ()
    return ()


@lru_cache(maxsize=1)
def _all_terms() -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for t in _CORE_TERMS + _data_extra_terms():
        f = _fold(t)
        if f and f not in seen:
            seen.add(f)
            out.append(t)
    return tuple(out)


def _strip_word(w: str) -> str:
    return re.sub(r"^[^\wçğıöşüÇĞİÖŞÜ]+|[^\wçğıöşüÇĞİÖŞÜ]+$", "", w or "", flags=re.I)


def _apply_phrase_fixes(text: str, reps: list[dict[str, Any]]) -> str:
    s = text
    for pat, repl in _PHRASE_FIXES:
        s2, n = re.subn(pat, repl, s, flags=re.I | re.UNICODE)
        if n:
            reps.append({"from": pat, "to": repl, "n": n, "kind": "phrase"})
            s = s2
    return s


def _best_term(candidate_fold: str, *, min_ratio: float, min_len: int = 4) -> tuple[str | None, float]:
    if len(candidate_fold) < min_len:
        return None, 0.0
    best = None
    best_r = 0.0
    for term in _all_terms():
        kf = _fold(term)
        if len(kf) < min_len:
            continue
        # uzunluk çok farklıysa atla
        if abs(len(kf) - len(candidate_fold)) > max(3, len(kf) // 2):
            continue
        r = _ratio(candidate_fold, kf)
        if r > best_r:
            best_r, best = r, term
    if best and best_r >= min_ratio and _fold(best) != candidate_fold:
        return best, best_r
    return None, best_r


def rewrite_soru_yazim(message: str) -> tuple[str, dict[str, Any]]:
    """
    Yazım / STT / klavye kayması → niyet metni.
    Dönüş: (düzeltilmiş_mesaj, meta)
    """
    raw = (message or "").strip()
    meta: dict[str, Any] = {
        "changed": False,
        "replacements": [],
        "version": FAZ_YAZIM_VERSION,
    }
    if not _enabled() or len(raw) < 3:
        return raw, meta

    s = unicodedata.normalize("NFKC", raw)
    s = re.sub(r"\s+", " ", s).strip()
    reps: list[dict[str, Any]] = []

    s = _apply_phrase_fixes(s, reps)

    words = s.split()
    if not words:
        return raw, meta

    out: list[str] = []
    i = 0
    while i < len(words):
        w = words[i]
        core = _strip_word(w)
        wf = _fold(core)

        # 3 kelime birleşik (nadir STT): a b c
        if i + 2 < len(words):
            m3 = _fold(
                _strip_word(words[i]) + _strip_word(words[i + 1]) + _strip_word(words[i + 2])
            )
            term, r = _best_term(m3, min_ratio=0.80, min_len=7)
            if term:
                reps.append(
                    {
                        "from": f"{words[i]} {words[i+1]} {words[i+2]}",
                        "to": term,
                        "ratio": round(r, 3),
                        "merge": 3,
                    }
                )
                out.append(term)
                i += 3
                continue

        # 2 kelime birleşik: foto senrez
        if i + 1 < len(words):
            m2 = _fold(_strip_word(words[i]) + _strip_word(words[i + 1]))
            term, r = _best_term(m2, min_ratio=0.78, min_len=6)
            if term:
                reps.append(
                    {
                        "from": f"{words[i]} {words[i+1]}",
                        "to": term,
                        "ratio": round(r, 3),
                        "merge": 2,
                    }
                )
                out.append(term)
                i += 2
                continue

        # tek kelime
        term, r = _best_term(wf, min_ratio=0.84, min_len=4)
        if term and core:
            reps.append({"from": w, "to": term, "ratio": round(r, 3)})
            out.append(w.replace(core, term, 1))
            i += 1
            continue

        out.append(w)
        i += 1

    new_msg = " ".join(out)
    new_msg = re.sub(r"\s+", " ", new_msg).strip()
    meta["replacements"] = reps
    if _fold(new_msg) != _fold(raw):
        meta["changed"] = True
        meta["original"] = raw
        meta["rewritten"] = new_msg
        meta["niyet"] = new_msg
        return new_msg, meta
    if reps and _fold(s) != _fold(raw):
        meta["changed"] = True
        meta["original"] = raw
        meta["rewritten"] = s
        meta["niyet"] = s
        return s, meta
    return raw, meta


def search_query_with_yazim(message: str) -> str:
    fixed, meta = rewrite_soru_yazim(message)
    return fixed if meta.get("changed") else (message or "").strip()


def resolve_user_niyet(message: str) -> tuple[str, dict[str, Any]]:
    """Sohbet / STT giriş kapısı — düzeltilmiş niyet metni."""
    return rewrite_soru_yazim(message)


def apply_stt_niyet_fix(payload: dict[str, Any] | None) -> dict[str, Any]:
    """STT JSON çıktısına niyet düzeltmesi ekler (text alanını günceller)."""
    out = dict(payload or {})
    text = str(out.get("text") or out.get("transcript") or "").strip()
    if not text:
        return out
    fixed, meta = resolve_user_niyet(text)
    if meta.get("changed"):
        out["text_raw"] = text
        out["text"] = fixed
        if "transcript" in out:
            out["transcript"] = fixed
        out["soru_yazim"] = meta
    return out
