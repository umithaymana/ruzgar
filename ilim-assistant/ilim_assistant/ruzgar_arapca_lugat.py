# -*- coding: utf-8 -*-
"""Rüzgar — Arapça lügat / kök-müştak / nahiv-sarf anlık cevap."""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "03_arapca_lugat"
_KOK = _DIR / "kuran_kok_lugat.jsonl"
_KLASIK = _DIR / "klasik_kok_lugat.jsonl"
_NAHIV = _DIR / "nahiv_sarf_temel.jsonl"
_LOOKUP = _DIR / "lookup_index.json"


def _fold_ar(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in t if not unicodedata.combining(c))


def _fold_tr(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def looks_like_arapca_lugat_question(msg: str) -> bool:
    low = _fold_tr(msg)
    if not low:
        return False
    cues = (
        "lugat", "lügat", "sozluk", "sözlük", "kok", "kök", "mushtaq", "mushtak",
        "mustak", "nahiv", "sarf", "irab", "i'rab", "vezin", "masdar", "ism-i fail",
        "ism-i meful", "arapca ne demek", "arapça ne demek", "kelimesinin koku",
        "kelimenin koku", "lane", "morpholog", "morfoloji", "bab nedir",
        "harf-i cer", "mubteda", "mübteda", "fail nedir", "turev", "türev",
    )
    if any(_fold_tr(c) in low for c in cues):
        return True
    if re.search(r"[\u0600-\u06FF]{2,}", msg or "") and any(
        x in low for x in ("nedir", "ne demek", "anlam", "kok", "kök", "mana")
    ):
        return True
    return False


@lru_cache(maxsize=1)
def _load_roots() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not _KOK.is_file():
        return out
    try:
        for line in _KOK.open(encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            root = (r.get("root") or "").strip()
            if root:
                out[root] = r
    except Exception:
        pass
    return out


@lru_cache(maxsize=1)
def _load_klasik() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    if not _KLASIK.is_file():
        return out
    try:
        for line in _KLASIK.open(encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            root = (r.get("root") or "").strip()
            if root:
                out.setdefault(root, []).append(r)
    except Exception:
        pass
    return out


@lru_cache(maxsize=1)
def _load_lookup() -> dict[str, str]:
    if not _LOOKUP.is_file():
        return {}
    try:
        return json.loads(_LOOKUP.read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _load_nahiv() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not _NAHIV.is_file():
        return rows
    try:
        for line in _NAHIV.open(encoding="utf-8"):
            if not line.strip():
                continue
            rows.append(json.loads(line))
    except Exception:
        pass
    return rows


def _extract_arabic_token(msg: str) -> Optional[str]:
    m = re.search(r"([\u0600-\u06FF]{2,}(?:\s+[\u0600-\u06FF]{2,}){0,2})", msg or "")
    if not m:
        return None
    return m.group(1).strip()


def lookup_root(token: str) -> Optional[dict[str, Any]]:
    if not token:
        return None
    roots = _load_roots()
    lookup = _load_lookup()
    klasik = _load_klasik()
    bare = _fold_ar(token).replace(" ", "")

    def _pack_klasik(root: str) -> dict[str, Any]:
        k0 = (klasik.get(root) or [{}])[0]
        return {
            "root": root,
            "meaning_en": k0.get("definition") if k0.get("lang") == "en" else "",
            "meaning_tr": "",
            "forms": [],
            "verse_keys": [],
            "frequency": 0,
        }

    if token in roots:
        return roots[token]
    if bare in roots:
        return roots[bare]
    root = lookup.get(token) or lookup.get(bare)
    if root and root in roots:
        return roots[root]
    if root and root in klasik:
        return _pack_klasik(root)
    if bare in klasik:
        return _pack_klasik(bare)
    for k, r in roots.items():
        if k in bare or bare in k:
            return r
    return None


def format_root_reply(row: dict[str, Any]) -> str:
    root = row.get("root") or ""
    en = (row.get("meaning_en") or "").strip()
    tr = (row.get("meaning_tr") or "").strip()
    forms = row.get("forms") or []
    verses = row.get("verse_keys") or []
    parts = [f"Ümit abi, kök **{root}**:"]
    if tr:
        parts.append(f"**TR (kısa):** {tr}")
    if en:
        parts.append(f"**EN (Lane / Kur'an kök):** {en}")
    for k in (_load_klasik().get(root) or [])[:2]:
        book = (k.get("book_name") or "")[:60]
        definition = (k.get("definition") or "").strip()
        if not definition:
            continue
        label = "EN (klasik sözlük)" if k.get("lang") == "en" else "AR (klasik lügat)"
        parts.append(f"**{label} — {book}:** {definition[:500]}")
    if forms:
        parts.append("**Müştak / formlar:** " + ", ".join(forms[:12]))
    if verses:
        parts.append("**Kur'an örnekleri:** " + ", ".join(verses[:8]))
    parts.append("(Kaynak: yerel Kur'an kök lügati + klasik Arapça sözlükler)")
    return "\n".join(parts)


def _score_nahiv(low: str, row: dict[str, Any]) -> float:
    sc = 0.0
    keys = [_fold_tr(str(row.get("id") or "")), _fold_tr(str(row.get("baslik") or ""))]
    keys += [_fold_tr(a) for a in (row.get("aliases") or [])]
    for k in keys:
        if not k:
            continue
        if k in low:
            sc = max(sc, 5.0 + min(len(k), 12) * 0.1)
    return sc


def try_nahiv_reply(msg: str) -> Optional[str]:
    low = _fold_tr(msg)
    best = None
    best_sc = 0.0
    for row in _load_nahiv():
        sc = _score_nahiv(low, row)
        if sc > best_sc:
            best_sc = sc
            best = row
    if best and best_sc >= 4.0:
        return f"Ümit abi, {best.get('metin')}"
    return None


def try_arapca_lugat_reply(message: str) -> Optional[str]:
    msg = (message or "").strip()
    if not msg or not looks_like_arapca_lugat_question(msg):
        return None

    tok = _extract_arabic_token(msg)
    if tok:
        row = lookup_root(tok)
        if row:
            return format_root_reply(row)

    nah = try_nahiv_reply(msg)
    if nah:
        return nah
    return None


def build_arapca_lugat_context(msg: str, *, max_chars: int = 4000) -> str:
    if not looks_like_arapca_lugat_question(msg):
        return ""
    parts = ["【Arapça lügat / nahiv — yerel】", ""]
    tok = _extract_arabic_token(msg)
    if tok:
        row = lookup_root(tok)
        if row:
            parts.append(format_root_reply(row))
            parts.append("")
    nah = try_nahiv_reply(msg)
    if nah:
        parts.append(nah)
    text = "\n".join(parts).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "…"
    return text if len(parts) > 2 else ""
