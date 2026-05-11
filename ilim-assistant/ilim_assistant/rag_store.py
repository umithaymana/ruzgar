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


def build_index(
    knowledge_root: Path | None = None,
    force: bool = False,
    incremental: bool = False,
) -> dict:
    root = knowledge_root or _KNOWLEDGE_ROOT
    root = Path(root)
    manifest_path = _INDEX_DIR / "manifest.json"
    chunks_path = _INDEX_DIR / "chunks.jsonl"
    emb_path = _INDEX_DIR / "embeddings.npy"

    _INDEX_DIR.mkdir(parents=True, exist_ok=True)

    files_payload = _load_markdown_files(root)
    payload_map = {rel: body for rel, body in files_payload}

    # Dosya bazlı hash: incremental (kademeli) gömme güncellemeleri için.
    file_digests: dict[str, str] = {}
    overall_h = hashlib.sha256()
    for rel, body in files_payload:
        one_h = hashlib.sha256()
        one_h.update(rel.encode("utf-8"))
        one_h.update(b"\0")
        one_h.update(body.encode("utf-8"))
        fd = one_h.hexdigest()
        file_digests[rel] = fd
        overall_h.update(rel.encode("utf-8"))
        overall_h.update(fd.encode("utf-8"))
    digest = overall_h.hexdigest()

    if (
        not force
        and manifest_path.is_file()
        and chunks_path.is_file()
        and emb_path.is_file()
    ):
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        old_digest = old.get("digest")
        if not incremental and old_digest == digest:
            return {
                "status": "cached",
                "chunks": old.get("num_chunks", 0),
                "digest": digest,
            }

        # Incremental: sadece değişen/eklenen/çıkarılan md dosyalarının chunk'larını yeniden gömecek.
        if incremental and old.get("model") == _MODEL_NAME and isinstance(old.get("file_digests"), dict):
            old_file_digests: dict[str, str] = old.get("file_digests") or {}
            changed_rels = [rel for rel, fd in file_digests.items() if old_file_digests.get(rel) != fd]
            removed_rels = [rel for rel in old_file_digests.keys() if rel not in file_digests]

            if not changed_rels and not removed_rels:
                return {
                    "status": "cached",
                    "chunks": old.get("num_chunks", 0),
                    "digest": digest,
                }

            try:
                old_chunks = _load_chunks()
                old_emb = _load_embeddings()
            except Exception:
                old_chunks, old_emb = [], None

            if not old_chunks or old_emb is None or len(old_chunks) != len(old_emb):
                # Eski indeks bozuksa veya uyumsuzsa tam rebuild yap.
                force = True
            else:
                changed_set = set(changed_rels)
                removed_set = set(removed_rels)

                keep_indices: list[int] = []
                kept_chunks: List[Chunk] = []
                for i, c in enumerate(old_chunks):
                    if c.source in removed_set:
                        continue
                    if c.source in changed_set:
                        continue
                    # Kaynak hâlâ mevcutsa tut.
                    if c.source in file_digests:
                        keep_indices.append(i)
                        kept_chunks.append(c)

                texts_kept = None  # sadece emtpy tutucu
                keep_emb = old_emb[keep_indices] if keep_indices else old_emb[:0]

                # Değişen kaynakların chunk'larını yeniden üret + embed et.
                changed_payload = [(rel, payload_map[rel]) for rel in sorted(changed_rels) if rel in payload_map]
                new_chunks: List[Chunk] = []
                for rel, body in changed_payload:
                    for piece in _split_text(body):
                        new_chunks.append(Chunk(text=piece, source=rel))

                if new_chunks:
                    model = _get_embedder()
                    texts_new = [c.text for c in new_chunks]
                    emb_new = model.encode(texts_new, normalize_embeddings=True, show_progress_bar=True)
                    emb_out = np.vstack([keep_emb, emb_new]) if len(keep_indices) else emb_new
                else:
                    emb_out = keep_emb

                chunks_out = kept_chunks + new_chunks
                # Persist
                np.save(str(emb_path), emb_out)
                with chunks_path.open("w", encoding="utf-8") as f:
                    for c in chunks_out:
                        f.write(
                            json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False)
                            + "\n"
                        )

                manifest_path.write_text(
                    json.dumps(
                        {
                            "digest": digest,
                            "num_chunks": len(chunks_out),
                            "model": _MODEL_NAME,
                            "file_digests": file_digests,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                return {
                    "status": "incremental",
                    "chunks": len(chunks_out),
                    "digest": digest,
                    "changed_files": len(changed_rels),
                    "removed_files": len(removed_rels),
                }

    # Tam rebuild (cached / incremental koşulları dışında kalır).
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
            {
                "digest": digest,
                "num_chunks": len(chunks),
                "model": _MODEL_NAME,
                "file_digests": file_digests,
            },
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


def _source_is_archive(rel: str) -> bool:
    """İndeks kaynağı `ilim-assistant/arsiv/...` altında mı? (Windows / POSIX yolu)."""
    p = (rel or "").replace("\\", "/").lower()
    return "/arsiv/" in p or p.startswith("arsiv/")


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


def search_arsiv(query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """Yalnızca arşiv külliyatı kaynakları; geniş aday kümeden süzülür (tek gömme sorgusu)."""
    tk = max(1, top_k)
    pool = max(tk * 4, 16)
    wide = search(query, top_k=min(pool, 48))
    out = [(t, s, sc) for t, s, sc in wide if _source_is_archive(s)]
    return out[:tk]
