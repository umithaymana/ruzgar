# Created by Ümit & Gökçenur
"""
Sahne Y1 meslek yan indeksi (.rag_index/sahne_y1).
Ana indekse birleşim OOM/OSError; arama buradan köprülenir.
Kapat: RUZGAR_SAHNE_Y1_RAG=0
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np

VERSION = "sahne-y1-rag-v1-2026-11-13"
_cache: dict[str, Any] = {"mtime": None, "chunks": None, "emb": None}


def enabled() -> bool:
    return os.environ.get("RUZGAR_SAHNE_Y1_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _pkg() -> Path:
    return Path(__file__).resolve().parents[1]


def index_dir() -> Path:
    return _pkg() / ".rag_index" / "sahne_y1"


def public_status() -> dict[str, Any]:
    man = index_dir() / "manifest.json"
    if not man.is_file():
        return {"enabled": enabled(), "version": VERSION, "ready": False, "chunks": 0}
    try:
        data = json.loads(man.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"enabled": enabled(), "version": VERSION, "ready": False, "chunks": 0}
    return {
        "enabled": enabled(),
        "version": VERSION,
        "ready": True,
        "chunks": int(data.get("num_chunks") or 0),
        "model": data.get("model"),
    }


def _load() -> tuple[list, Any] | tuple[None, None]:
    d = index_dir()
    man = d / "manifest.json"
    chunks_p = d / "chunks.jsonl"
    emb_p = d / "embeddings.npy"
    if not (man.is_file() and chunks_p.is_file() and emb_p.is_file()):
        return None, None
    mtime = max(man.stat().st_mtime, chunks_p.stat().st_mtime, emb_p.stat().st_mtime)
    if _cache["mtime"] == mtime and _cache["chunks"] is not None:
        return _cache["chunks"], _cache["emb"]
    chunks = []
    with chunks_p.open("rb") as f:
        for raw in f:
            try:
                row = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            chunks.append(row)
    emb = np.load(emb_p)
    if len(chunks) != len(emb):
        return None, None
    _cache["mtime"] = mtime
    _cache["chunks"] = chunks
    _cache["emb"] = emb
    return chunks, emb


def search_sahne_y1(
    query: str,
    top_k: int = 6,
    q_vec: Any = None,
) -> list[tuple[str, str, float]]:
    if not enabled():
        return []
    chunks, emb = _load()
    if not chunks or emb is None:
        return []
    if q_vec is None:
        from ilim_assistant.rag_store import _get_embedder

        q_vec = _get_embedder().encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )[0]
    sim = emb @ q_vec
    k = min(max(int(top_k), 1), len(sim))
    idx = np.argsort(-sim)[:k]
    out: list[tuple[str, str, float]] = []
    for i in idx:
        ii = int(i)
        row = chunks[ii]
        out.append((str(row.get("text") or ""), str(row.get("source") or ""), float(sim[ii])))
    return out
