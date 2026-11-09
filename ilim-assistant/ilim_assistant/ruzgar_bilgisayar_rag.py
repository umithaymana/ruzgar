# Created by Ümit & Gökçenur
"""
Adım 4 — bilgisayar eserleri yan indeksi (ana RAG MemoryError kaçınır).

Kaynak: knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/
İndeks: .rag_index_bilgisayar/
Kapat: RUZGAR_BILGISAYAR_RAG=0
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

VERSION = "bilgisayar-rag-v1-2026-11-09"

# Dalga A omurga + programlama
_DAL_PREFIXES = (
    "01_",
    "02_",
    "03_",
    "04_",
    "05_",
    "06_",
    "11_",
)


def enabled() -> bool:
    return os.environ.get("RUZGAR_BILGISAYAR_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _pkg() -> Path:
    return Path(__file__).resolve().parents[1]


def source_root() -> Path:
    return _pkg() / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_eserleri"


def index_dir() -> Path:
    d = _pkg() / ".rag_index_bilgisayar"
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
        "dals": data.get("dals") or [],
    }


def _iter_md_files() -> list[Path]:
    root = source_root()
    if not root.is_dir():
        return []
    out: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not child.name.startswith(_DAL_PREFIXES):
            continue
        metin = child / "metin"
        if not metin.is_dir():
            continue
        out.extend(sorted(metin.rglob("*.md")))
    return out


def build_bilgisayar_index(*, batch: int = 64, max_files: int = 0) -> dict[str, Any]:
    from ilim_assistant.rag_store import Chunk, _MODEL_NAME, _get_embedder, _split_text

    files = _iter_md_files()
    if max_files > 0:
        files = files[:max_files]
    if not files:
        return {"ok": False, "error": "md yok", "root": str(source_root())}

    chunks: list[Chunk] = []
    dals: set[str] = set()
    for path in files:
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            rel = str(path.relative_to(_pkg() / "knowledge")).replace("\\", "/")
        except ValueError:
            rel = str(path).replace("\\", "/")
        # dal adı
        parts = Path(rel).parts
        if len(parts) >= 3:
            dals.add(parts[2] if parts[0] == "ortak_kaynak" else parts[0])
        for piece in _split_text(body):
            chunks.append(Chunk(text=piece, source=rel))

    if not chunks:
        return {"ok": False, "error": "chunk yok", "files": len(files)}

    model = _get_embedder()
    texts = [c.text for c in chunks]
    parts_emb: list[np.ndarray] = []
    for i in range(0, len(texts), max(8, batch)):
        emb = model.encode(
            texts[i : i + batch],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        parts_emb.append(np.asarray(emb, dtype=np.float32))
    emb_out = np.vstack(parts_emb)

    out = index_dir()
    with (out / "chunks.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(
                json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False)
                + "\n"
            )
    np.save(str(out / "embeddings.npy"), emb_out)
    payload = {
        "version": VERSION,
        "num_chunks": len(chunks),
        "num_files": len(files),
        "model": _MODEL_NAME,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": str(source_root()),
        "dals": sorted(dals),
    }
    (out / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    global _cache
    _cache = None
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
            chunks.append(
                Chunk(text=str(row.get("text") or ""), source=str(row.get("source") or ""))
            )
    emb = np.load(str(emb_path), mmap_mode="r")
    if len(chunks) != len(emb):
        return None
    _cache = (chunks, emb)
    return _cache


def search_bilgisayar(
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
