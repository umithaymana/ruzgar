# Created by Ümit & Gökçenur
"""Ana Motor Faz F2 — düşük Güven turunda Nebula koleksiyon önerisi."""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent


def oneri_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_NEBULA_ONERI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm_token(s: str) -> str:
    t = unicodedata.normalize("NFKD", (s or "").strip()).casefold()
    return re.sub(r"[^\w]+", "", t, flags=re.UNICODE)


def _list_nebula_collections() -> list[dict[str, str]]:
    try:
        from ilim_assistant.rag_store import _knowledge_root

        root = _knowledge_root() / "nebula"
    except Exception:
        root = _PKG_ROOT / "knowledge" / "nebula"
    if not root.is_dir():
        return []
    out: list[dict[str, str]] = []
    for p in sorted(root.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        title = p.name.replace("_", " ").replace("-", " ")
        meta = p / "meta.json"
        if meta.is_file():
            try:
                import json

                data = json.loads(meta.read_text(encoding="utf-8"))
                title = str(data.get("title") or data.get("collection") or title)
            except Exception:
                pass
        out.append({"slug": p.name, "title": title})
    return out


def _infer_guven_level(
    reply: str,
    *,
    hits: list | None,
    web_was_used: bool,
) -> str:
    body = reply or ""
    m = re.search(r"\*\*Güven:\s*(yüksek|orta|düşük|dusuk)", body, re.I)
    if m:
        g = m.group(1).lower()
        return "düşük" if g == "dusuk" else g
    n_src = len(hits or [])
    if n_src >= 2 or web_was_used:
        return "orta"
    if n_src == 0 and not web_was_used:
        return "düşük"
    return "orta"


def _score_collection(slug: str, title: str, tokens: set[str]) -> float:
    if not tokens:
        return 0.0
    parts = set()
    for raw in (slug, title):
        for w in re.split(r"[\s_\-]+", raw.lower()):
            n = _norm_token(w)
            if len(n) >= 3:
                parts.add(n)
    overlap = tokens & parts
    if not overlap:
        return 0.0
    return len(overlap) / max(1, len(tokens))


def suggest_nebula_collection(
    user_message: str,
    *,
    hits: list | None = None,
    guven: str | None = None,
    web_was_used: bool = False,
) -> dict[str, Any] | None:
    if not oneri_enabled():
        return None
    msg = (user_message or "").strip()
    if len(msg) < 8:
        return None
    level = (guven or "").strip().lower() or _infer_guven_level(
        "", hits=hits, web_was_used=web_was_used
    )
    if level not in ("düşük", "dusuk"):
        return None
    if hits and len(hits) >= 2:
        return None

    tokens = {
        _norm_token(w)
        for w in re.split(r"\W+", msg.lower())
        if len(_norm_token(w)) >= 4
    }
    cols = _list_nebula_collections()
    if not cols:
        return None

    ranked = sorted(
        (
            {
                "slug": c["slug"],
                "title": c["title"],
                "score": _score_collection(c["slug"], c["title"], tokens),
            }
            for c in cols
        ),
        key=lambda x: float(x["score"]),
        reverse=True,
    )
    best = ranked[0] if ranked else None
    if not best or float(best["score"]) < 0.15:
        best = cols[0]
        best = {"slug": best["slug"], "title": best["title"], "score": 0.1}

    cmd = (
        f"knowledge/nebula/{best['slug']}/ kaynağını Nebula'ya ekle — "
        f"«{msg[:120]}» konusu için ansiklopedi paketi oluştur."
    )
    return {
        "ok": True,
        "guven": "düşük",
        "collection": best["slug"],
        "collection_title": best["title"],
        "topic": msg[:240],
        "hint": (
            "Yerel külliyatta güçlü eşleşme bulunamadı. "
            "İlgili kaynağı Nebula koleksiyonuna ekleyerek kaliteyi artırabilirsin."
        ),
        "suggested_command": cmd,
    }


def build_nebula_oneri_card(
    reply: str,
    user_message: str,
    *,
    hits: list | None = None,
    web_was_used: bool = False,
) -> dict[str, Any] | None:
    guven = _infer_guven_level(reply, hits=hits, web_was_used=web_was_used)
    sug = suggest_nebula_collection(
        user_message,
        hits=hits,
        guven=guven,
        web_was_used=web_was_used,
    )
    if not sug:
        return None
    return sug


def session_nebula_oneri_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_SESSION_NEBULA_ONERI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_session_nebula_card(
    *,
    session_id: str | None = None,
    upload_ids: list[str] | None = None,
    topic: str = "",
) -> dict[str, Any] | None:
    """Faz K2 — birleşik/çoklu dosya oturumundan tek Nebula koleksiyon önerisi."""
    if not oneri_enabled() or not session_nebula_oneri_enabled():
        return None
    try:
        from ilim_assistant.ana_motor_dosya_ingest import (
            get_upload_records,
            resolve_upload_ids,
        )
    except Exception:
        return None

    ids = resolve_upload_ids(upload_ids, session_id)
    if not ids:
        return None
    records = get_upload_records(ids)
    if not records:
        return None

    msg = (topic or "").strip()
    tokens: set[str] = set()
    for w in re.split(r"\W+", msg.lower()):
        n = _norm_token(w)
        if len(n) >= 4:
            tokens.add(n)
    for rec in records:
        fname = str(rec.get("filename") or "")
        for w in re.split(r"[\W_.]+", fname.lower()):
            n = _norm_token(w)
            if len(n) >= 4:
                tokens.add(n)
        chunks = list(rec.get("chunk_texts") or [])
        if chunks:
            for w in re.split(r"\W+", str(chunks[0])[:500].lower()):
                n = _norm_token(w)
                if len(n) >= 5:
                    tokens.add(n)

    cols = _list_nebula_collections()
    if not cols:
        return None

    ranked = sorted(
        (
            {
                "slug": c["slug"],
                "title": c["title"],
                "score": _score_collection(c["slug"], c["title"], tokens),
            }
            for c in cols
        ),
        key=lambda x: float(x["score"]),
        reverse=True,
    )
    best = ranked[0] if ranked else None
    if not best or float(best["score"]) < 0.08:
        best = {"slug": cols[0]["slug"], "title": cols[0]["title"], "score": 0.1}

    label = msg[:120] or f"{len(records)} dosyalık oturum"
    cmd = (
        f"knowledge/nebula/{best['slug']}/ — oturum paketi "
        f"({len(records)} dosya) Nebula'ya ekle: «{label}»"
    )
    merged = len(ids) >= 2 or bool((session_id or "").strip())
    return {
        "ok": True,
        "guven": "orta",
        "merged_session": merged,
        "file_count": len(records),
        "session_id": session_id,
        "upload_ids": ids,
        "collection": best["slug"],
        "collection_title": best["title"],
        "topic": (msg or label)[:240],
        "hint": (
            f"{len(records)} dosyalı oturum için önerilen Nebula koleksiyonu: "
            f"«{best['title']}». Tek tıkla kaynak ekle."
        ),
        "suggested_command": cmd,
    }


def maybe_append_nebula_oneri_note(
    reply: str,
    user_message: str,
    *,
    hits: list | None = None,
    web_was_used: bool = False,
) -> str:
    """Kısa metin notu (kart yanında)."""
    card = build_nebula_oneri_card(
        reply,
        user_message,
        hits=hits,
        web_was_used=web_was_used,
    )
    if not card:
        return reply
    note = (
        f"\n\n*Nebula öneri:* `{card['collection']}` koleksiyonuna kaynak eklemek "
        f"bu konuda güveni artırabilir. Komut: «{card['suggested_command'][:160]}…»*"
    )
    if "nebula öneri" in (reply or "").lower():
        return reply
    return (reply or "").rstrip() + note
