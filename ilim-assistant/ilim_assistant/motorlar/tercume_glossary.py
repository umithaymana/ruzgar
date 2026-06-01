# Created by Ümit & Gökçenur
"""Tercüme terim sözlüğü — metin/dosya adına göre çeviri talimatı."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

GLOSSARY_VERSION = "tercume-glossary-v2-faz4-2026-05-31"
_GLOSSARY_PATH = Path(__file__).with_name("tercume_glossary.json")

_LANG_COL = {
    "tr": "tr",
    "en": "en",
    "ar": "src",
    "de": "en",
    "fr": "en",
    "fa": "src",
    "ru": "en",
}


def _norm(s: str) -> str:
    t = unicodedata.normalize("NFKD", (s or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def _load() -> dict[str, Any]:
    try:
        return json.loads(_GLOSSARY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"sets": {}}


def _active_sets(text: str, source_file: str) -> list[tuple[str, dict[str, Any]]]:
    blob = _norm(f"{text} {source_file}")
    out: list[tuple[str, dict[str, Any]]] = []
    data = _load()
    for key, block in (data.get("sets") or {}).items():
        if not isinstance(block, dict):
            continue
        keys = block.get("match") or []
        if any(_norm(str(k)) in blob for k in keys):
            out.append((str(key), block))
    return out


def glossary_directive(
    text: str,
    *,
    source_file: str = "",
    tgt_lang: str = "tr",
    max_terms: int = 12,
) -> str:
    """Çeviri sistem promptuna eklenecek terim bloğu."""
    from ilim_assistant.motorlar.tercume_user_glossary import user_glossary_directive

    user_block = user_glossary_directive(
        text, source_file=source_file, tgt_lang=tgt_lang, max_terms=min(8, max_terms)
    )
    sets = _active_sets(text, source_file)
    if not sets and not user_block:
        return ""

    code = (tgt_lang or "tr").strip().lower()[:2] or "tr"
    col = _LANG_COL.get(code, "en")
    lines: list[str] = []
    if user_block:
        lines.append(user_block.strip())
    if sets:
        lines.append("TERİM SÖZLÜĞÜ (bu metin için — tutarlı çevir):")
    shown = 0
    if user_block:
        shown += user_block.count("→")
    for set_name, block in sets:
        rules = block.get("rules") or []
        for r in rules[:4]:
            lines.append(f"- {r}")
        for term in block.get("terms") or []:
            if shown >= max_terms:
                break
            if not isinstance(term, dict):
                continue
            src = str(term.get("src") or "").strip()
            if not src:
                continue
            hint = str(term.get(col) or term.get("tr") or term.get("en") or "").strip()
            if hint:
                lines.append(f"- «{src}» → {hint}")
            shown += 1
        if shown >= max_terms:
            break

    if not lines:
        return ""
    if sets:
        lines.append(f"({GLOSSARY_VERSION} · {', '.join(s[0] for s in sets[:3])})")
    return "\n".join(lines)


def glossary_term_pairs(
    text: str,
    *,
    source_file: str = "",
    tgt_lang: str = "tr",
    max_terms: int = 16,
) -> list[tuple[str, str]]:
    """Bellek/RAG için (kaynak → hedef ipucu) çiftleri."""
    from ilim_assistant.motorlar.tercume_user_glossary import matching_user_terms

    user_pairs = matching_user_terms(
        text, source_file=source_file, tgt_lang=tgt_lang, max_terms=max_terms
    )
    sets = _active_sets(text, source_file)
    if not sets and not user_pairs:
        return []
    code = (tgt_lang or "tr").strip().lower()[:2] or "tr"
    col = _LANG_COL.get(code, "en")
    blob = _norm(f"{text} {source_file}")
    out: list[tuple[str, str]] = list(user_pairs)
    existing = {_norm(a) for a, _ in out}
    for _name, block in sets:
        for term in block.get("terms") or []:
            if len(out) >= max_terms:
                break
            if not isinstance(term, dict):
                continue
            src = str(term.get("src") or "").strip()
            if not src or _norm(src) not in blob:
                continue
            sl = _norm(src)
            if sl in existing:
                continue
            hint = str(term.get(col) or term.get("tr") or term.get("en") or "").strip()
            if hint:
                out.append((src, hint))
                existing.add(sl)
            if len(out) >= max_terms:
                break
    return out[:max_terms]


def active_glossary_sets(text: str, source_file: str = "") -> list[str]:
    return [name for name, _ in _active_sets(text, source_file)]
