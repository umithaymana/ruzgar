# Created by Ümit & Gökçenur
"""
Adım 5 — seçili ayıklama md için yan indeks (ana RAG MemoryError kaçınır).

Kaynak: knowledge/ortak_kaynak/alanlar/ruzgar_indir_secim/
İndeks: .rag_index_ayiklama/
Kapat: RUZGAR_AYIKLAMA_RAG=0
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

VERSION = "ayiklama-rag-v1-2026-11-09"


def enabled() -> bool:
    return os.environ.get("RUZGAR_AYIKLAMA_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _pkg() -> Path:
    return Path(__file__).resolve().parents[1]


def source_root() -> Path:
    return _pkg() / "knowledge" / "ortak_kaynak" / "alanlar" / "ruzgar_indir_secim"


def index_dir() -> Path:
    d = _pkg() / ".rag_index_ayiklama"
    d.mkdir(parents=True, exist_ok=True)
    return d


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
        "built_at": data.get("built_at"),
    }


def build_ayiklama_index(*, batch: int = 64) -> dict[str, Any]:
    """Yalnız seçili md → göm. Ana indeksi dokunmaz."""
    from ilim_assistant.rag_store import Chunk, _get_embedder, _MODEL_NAME, _split_text

    root = source_root()
    if not root.is_dir():
        return {"ok": False, "error": f"kaynak yok: {root}"}

    files = sorted(root.rglob("*.md"))
    chunks: list[Chunk] = []
    for path in files:
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            rel = str(path.relative_to(_pkg() / "knowledge")).replace("\\", "/")
        except ValueError:
            rel = str(path).replace("\\", "/")
        for piece in _split_text(body):
            chunks.append(Chunk(text=piece, source=rel))

    if not chunks:
        return {"ok": False, "error": "chunk yok", "files": len(files)}

    model = _get_embedder()
    texts = [c.text for c in chunks]
    parts: list[np.ndarray] = []
    for i in range(0, len(texts), max(8, batch)):
        batch_texts = texts[i : i + batch]
        emb = model.encode(
            batch_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        parts.append(np.asarray(emb, dtype=np.float32))
    emb_out = np.vstack(parts)

    out = index_dir()
    chunks_path = out / "chunks.jsonl"
    emb_path = out / "embeddings.npy"
    man_path = out / "manifest.json"

    with chunks_path.open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(
                json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False)
                + "\n"
            )
    np.save(str(emb_path), emb_out)
    payload = {
        "version": VERSION,
        "num_chunks": len(chunks),
        "num_files": len(files),
        "model": _MODEL_NAME,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": str(root),
    }
    man_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"ok": True, **payload}


_cache: tuple[list[Any], np.ndarray] | None = None


def _load_index() -> tuple[list[Any], np.ndarray] | None:
    global _cache
    if _cache is not None:
        return _cache
    from ilim_assistant.rag_store import Chunk

    out = index_dir()
    chunks_path = out / "chunks.jsonl"
    emb_path = out / "embeddings.npy"
    if not chunks_path.is_file() or not emb_path.is_file():
        return None
    chunks: list[Any] = []
    with chunks_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            chunks.append(Chunk(text=str(row.get("text") or ""), source=str(row.get("source") or "")))
    emb = np.load(str(emb_path), mmap_mode="r")
    if len(chunks) != len(emb):
        return None
    _cache = (chunks, emb)
    return _cache


def search_ayiklama(
    query: str,
    top_k: int = 5,
    *,
    q_vec: np.ndarray | None = None,
) -> list[tuple[str, str, float]]:
    if not enabled():
        return []
    loaded = _load_index()
    if not loaded:
        return []
    chunks, emb = loaded
    if q_vec is None:
        from ilim_assistant.rag_store import _get_embedder

        q_vec = _get_embedder().encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )[0]
    sim = np.asarray(emb) @ np.asarray(q_vec)
    take = min(max(int(top_k), 1), len(sim))
    idx = np.argsort(-sim)[:take]
    return [
        (chunks[int(i)].text, chunks[int(i)].source, float(sim[int(i)])) for i in idx
    ]
