"""Markdown bilgi dosyalarından basit RAG: çok dilli gömme + kosinüs araması."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np

_KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent / "knowledge"
_INDEX_DIR = Path(__file__).resolve().parent.parent / ".rag_index"
_MODEL_NAME = os.environ.get(
    "RAG_EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)


@dataclass
class Chunk:
    text: str
    source: str


def _split_text(text: str, max_chars: int = 900, overlap: int = 80) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end].strip()
        if chunk:
            parts.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return parts


def _load_markdown_files(root: Path) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        try:
            out.append((str(path.relative_to(root)), path.read_text(encoding="utf-8")))
        except OSError:
            continue
    return out


def _embed_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_MODEL_NAME)


_cached_embedder = None


def _get_embedder():
    """Arama başına model yükleme yapmaz (ilk çağrıda bir kez bellekte tutulur)."""
    global _cached_embedder
    if _cached_embedder is None:
        _cached_embedder = _embed_model()
    return _cached_embedder


def build_index(knowledge_root: Path | None = None, force: bool = False) -> dict:
    root = knowledge_root or _KNOWLEDGE_ROOT
    root = Path(root)
    manifest_path = _INDEX_DIR / "manifest.json"
    chunks_path = _INDEX_DIR / "chunks.jsonl"
    emb_path = _INDEX_DIR / "embeddings.npy"

    _INDEX_DIR.mkdir(parents=True, exist_ok=True)

    files_payload = _load_markdown_files(root)
    h = hashlib.sha256()
    for rel, body in files_payload:
        h.update(rel.encode("utf-8"))
        h.update(body.encode("utf-8"))
    digest = h.hexdigest()

    if (
        not force
        and manifest_path.is_file()
        and chunks_path.is_file()
        and emb_path.is_file()
    ):
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("digest") == digest:
            return {"status": "cached", "chunks": old.get("num_chunks", 0), "digest": digest}

    chunks: List[Chunk] = []
    for rel, body in files_payload:
        for piece in _split_text(body):
            chunks.append(Chunk(text=piece, source=rel))

    model = _get_embedder()
    texts = [c.text for c in chunks]
    emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    np.save(str(emb_path), emb)

    with chunks_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False) + "\n")

    manifest_path.write_text(
        json.dumps(
            {"digest": digest, "num_chunks": len(chunks), "model": _MODEL_NAME},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"status": "built", "chunks": len(chunks), "digest": digest}


def _load_chunks() -> List[Chunk]:
    chunks_path = _INDEX_DIR / "chunks.jsonl"
    if not chunks_path.is_file():
        return []
    rows: List[Chunk] = []
    with chunks_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            rows.append(Chunk(text=o["text"], source=o["source"]))
    return rows


def _load_embeddings() -> np.ndarray | None:
    emb_path = _INDEX_DIR / "embeddings.npy"
    if not emb_path.is_file():
        return None
    return np.load(str(emb_path))


_index_mtime_ns: int | None = None
_cached_chunks_list: List[Chunk] | None = None
_cached_emb_arr: np.ndarray | None = None


def _rag_cache_enabled() -> bool:
    return os.environ.get("RAG_INDEX_CACHE", "1").strip() not in ("0", "false", "no")


def _get_cached_index() -> tuple[List[Chunk], np.ndarray | None]:
    """İndeks dosyalarını her aramada diskten okumaz; embeddings.npy değişince yeniler."""
    global _index_mtime_ns, _cached_chunks_list, _cached_emb_arr
    emb_path = _INDEX_DIR / "embeddings.npy"
    chunks_path = _INDEX_DIR / "chunks.jsonl"
    if not emb_path.is_file() or not chunks_path.is_file():
        return [], None

    if not _rag_cache_enabled():
        chunks = _load_chunks()
        emb = _load_embeddings()
        if not chunks or emb is None or len(chunks) != len(emb):
            return [], None
        return chunks, emb

    try:
        mtime = emb_path.stat().st_mtime_ns
    except OSError:
        return [], None

    if (
        _cached_emb_arr is not None
        and _cached_chunks_list is not None
        and _index_mtime_ns == mtime
    ):
        return _cached_chunks_list, _cached_emb_arr

    chunks = _load_chunks()
    emb = _load_embeddings()
    if chunks and emb is not None and len(chunks) == len(emb):
        _cached_chunks_list = chunks
        _cached_emb_arr = emb
        _index_mtime_ns = mtime
    else:
        _cached_chunks_list = None
        _cached_emb_arr = None
        _index_mtime_ns = None
    return chunks, emb


def warmup_index() -> None:
    """API / Gradio başlarken indeksi ve gömme modelini önceden yükle (ilk mesaj gecikmesini azaltır)."""
    if not _rag_cache_enabled():
        return
    _get_embedder()
    _get_cached_index()


def search(query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """Dönüş: (metin, kaynak, skor) — skor yaklaşık uyum."""
    chunks, emb = _get_cached_index()
    if not chunks or emb is None or len(chunks) != len(emb):
        return []

    model = _get_embedder()
    q = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    sim = emb @ q
    idx = np.argsort(-sim)[:top_k]
    out: List[Tuple[str, str, float]] = []
    for i in idx:
        out.append((chunks[int(i)].text, chunks[int(i)].source, float(sim[int(i)])))
    return out
