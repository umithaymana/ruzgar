"""Markdown bilgi dosyalarından basit RAG: çok dilli gömme + kosinüs araması."""

from __future__ import annotations

import hashlib
import json
import os
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple

import numpy as np

_PKG_ROOT = Path(__file__).resolve().parent.parent
_MODEL_NAME = os.environ.get(
    "RAG_EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)


def _knowledge_root() -> Path:
    try:
        from ilim_assistant.ruzgar_public_mode import shared_knowledge_root

        return shared_knowledge_root()
    except Exception:
        return _PKG_ROOT / "knowledge"


# Eski importlar: `from rag_store import _KNOWLEDGE_ROOT`
_KNOWLEDGE_ROOT = _knowledge_root()


def _index_dir() -> Path:
    try:
        from ilim_assistant.ruzgar_public_mode import shared_rag_index_dir

        return shared_rag_index_dir()
    except Exception:
        p = _PKG_ROOT / ".rag_index"
        p.mkdir(parents=True, exist_ok=True)
        return p



def _atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Windows'ta büyük jsonl yeniden yazımında Errno 22 / kilit riskine karşı."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding=encoding)
    os.replace(tmp, path)


def _atomic_save_npy(path: Path, arr: np.ndarray) -> None:
    """Windows'ta açık/kilitli embeddings.npy üzerine doğrudan yazmayı önler."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f"{path.stem}_write.tmp.npy"
    if tmp.is_file():
        try:
            tmp.unlink()
        except OSError:
            pass
    np.save(str(tmp), arr)
    last_err: Exception | None = None
    for attempt in range(8):
        try:
            os.replace(tmp, path)
            return
        except OSError as e:
            last_err = e
            import time

            time.sleep(0.35 * (attempt + 1))
            try:
                if path.is_file():
                    path.unlink()
                os.replace(tmp, path)
                return
            except Exception as e2:
                last_err = e2
    if last_err:
        raise last_err


def _atomic_write_chunks_jsonl(path: Path, chunks: List["Chunk"]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(
                json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False)
                + "\n"
            )
    # Windows: antivirüs / indeksleyici kilitlerse os.replace bir kez düşebiliyor
    last_err: Exception | None = None
    for attempt in range(8):
        try:
            os.replace(tmp, path)
            return
        except PermissionError as e:
            last_err = e
            import time

            time.sleep(0.35 * (attempt + 1))
            try:
                if path.is_file():
                    path.unlink()
                os.replace(tmp, path)
                return
            except Exception as e2:
                last_err = e2
    if last_err:
        raise last_err
    raise PermissionError(f"chunks.jsonl yazılamadı: {path}")


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


def _is_dokunma_markdown(path: Path, text: str | None = None) -> bool:
    """F3.5 — «dokunma» etiketi: indeks/ingest dışı bırak.

    Kurallar (herhangi biri yeterli):
    - yan dosya: ``name.md.dokunma`` veya aynı klasörde ``.dokunma``
    - dosya adı ``_DOKUNMA_`` ile başlar
    - içerik başında ``dokunma: true`` / ``<!-- dokunma -->``
    """
    name = path.name
    if name.upper().startswith("_DOKUNMA_"):
        return True
    try:
        if path.with_suffix(path.suffix + ".dokunma").is_file():
            return True
        if (path.parent / ".dokunma").is_file():
            return True
    except OSError:
        pass
    head = (text if text is not None else "")[:400].lower()
    if not head and text is None:
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:400].lower()
        except OSError:
            return False
    if "<!-- dokunma -->" in head or "dokunma: true" in head or "dokunma:true" in head:
        return True
    return False


def _norm_rel(rel: str) -> str:
    return (rel or "").replace("\\", "/").strip()


def _is_shamela_main_skip(rel: str) -> bool:
    """Şamile ana indekse çekilmez — shard indeksi sahibidir."""
    r = _norm_rel(rel).lower()
    return r == "ilim/din/shamela" or r.startswith("ilim/din/shamela/")


def _is_thin_auto_ingest_rel(rel: str) -> bool:
    """Otomatik ince yol: yalnız learned/ (kör ortak/Şamile yutma yok)."""
    return _norm_rel(rel).lower().startswith("learned/")


def _allow_new_main_rel(rel: str) -> bool:
    if _is_shamela_main_skip(rel):
        return False
    flag = os.environ.get("RUZGAR_RAG_ALLOW_NEW_MAIN", "0").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    return _is_thin_auto_ingest_rel(rel)


def _rel_known(rel: str, known_norm: set[str]) -> bool:
    return _norm_rel(rel) in known_norm


def _load_markdown_files(
    root: Path,
    *,
    known_norm: set[str] | None = None,
    restrict_new: bool = False,
) -> List[Tuple[str, str]]:
    """knowledge altı md yükle.

    - Şamile her zaman atlanır (ana indeks / shard ayrımı).
    - ``restrict_new``: bilinen (manifest) + ince yol (learned) dışında yeni dosya yüklenmez.
      Böylece incremental 66k ortak / 298k Şamile'yi ana indekse çekmez.
    """
    out: List[Tuple[str, str]] = []
    known = known_norm or set()
    for path in sorted(root.rglob("*.md")):
        try:
            rel = str(path.relative_to(root))
            if _is_shamela_main_skip(rel):
                continue
            if restrict_new and known:
                if not _rel_known(rel, known) and not _allow_new_main_rel(rel):
                    continue
            raw = path.read_text(encoding="utf-8")
            if _is_dokunma_markdown(path, raw):
                continue
            out.append((rel, raw))
        except OSError:
            continue
    return out


def invalidate_rag_cache() -> None:
    """Disk indeksi değişince bellek önbelleğini düşür."""
    global _index_mtime_ns, _cached_chunks_list, _cached_emb_arr
    global _tarih_chunk_row_indices, _tdk_chunk_row_indices, _nebula_chunk_row_indices
    _index_mtime_ns = None
    _cached_chunks_list = None
    _cached_emb_arr = None
    _tarih_chunk_row_indices = None
    _tdk_chunk_row_indices = None
    _nebula_chunk_row_indices = None


def index_health_report(knowledge_root: Path | None = None) -> dict:
    """İndeks vs disk ölçümü — kör rebuild yok, yalnız rapor."""
    root = Path(knowledge_root or _knowledge_root())
    man_path = _index_dir() / "manifest.json"
    out: dict = {
        "ok": True,
        "knowledge_root": str(root),
        "index_dir": str(_index_dir()),
        "manifest_present": man_path.is_file(),
        "manifest_mtime": None,
        "manifest_files": 0,
        "manifest_chunks": 0,
        "learned_disk": 0,
        "learned_in_index": 0,
        "learned_missing": 0,
        "learned_missing_sample": [],
        "shamela_policy": "main_index_skip_shards_own",
        "hint": "learned eksikse upsert_learned_into_main_index; Şamile ana indekse çekilmez.",
    }
    if not man_path.is_file():
        out["ok"] = False
        out["hint"] = "manifest yok — önce güvenli indeks kurulumu gerekir."
        return out
    try:
        out["manifest_mtime"] = man_path.stat().st_mtime
        man = json.loads(man_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        out["ok"] = False
        out["error"] = str(exc)[:200]
        return out
    fd = man.get("file_digests") or {}
    known = {_norm_rel(k) for k in fd}
    out["manifest_files"] = len(fd)
    out["manifest_chunks"] = int(man.get("num_chunks") or 0)
    out["model"] = man.get("model")
    learned_dir = root / "learned"
    missing: list[str] = []
    if learned_dir.is_dir():
        for p in sorted(learned_dir.glob("*.md")):
            try:
                if _is_dokunma_markdown(p):
                    continue
            except OSError:
                continue
            rel = str(p.relative_to(root))
            out["learned_disk"] += 1
            if _norm_rel(rel) in known:
                out["learned_in_index"] += 1
            else:
                missing.append(_norm_rel(rel))
    out["learned_missing"] = len(missing)
    out["learned_missing_sample"] = missing[:12]
    sham_in = sum(1 for k in known if _is_shamela_main_skip(k))
    out["shamela_frozen_in_main"] = sham_in
    return out


def nebula_dokunma_inventory(nebula_root: Path | None = None) -> dict:
    """F3.5 — nebula incremental: dokunma / aday sayımı (karar görünürlüğü)."""
    root = nebula_root
    if root is None:
        root = _PKG_ROOT / "knowledge" / "nebula"
    tagged: list[str] = []
    open_md: list[str] = []
    if not root.is_dir():
        return {"ok": True, "root": str(root), "dokunma": 0, "aday": 0, "tagged": [], "open": []}
    for path in sorted(root.rglob("*.md")):
        rel = str(path.relative_to(root)).replace("\\", "/")
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _is_dokunma_markdown(path, raw):
            tagged.append(rel)
        else:
            open_md.append(rel)
    return {
        "ok": True,
        "root": str(root),
        "policy": "dokunma_etiketi_veya_ingest",
        "hint": "İndekslenmesin istenen paketlere «dokunma: true» veya .dokunma koyun; diğerleri ingest adayı.",
        "dokunma": len(tagged),
        "aday": len(open_md),
        "tagged": tagged[:40],
        "open": open_md[:40],
    }


def _embed_model():
    import os

    from sentence_transformers import SentenceTransformer

    # Ollama GPU VRAM kullanırken gömme CUDA'ya binmesin (8GB kartlarda kilitlenme).
    # RUZGAR_EMBED_DEVICE=cuda ile zorla GPU.
    device = (os.environ.get("RUZGAR_EMBED_DEVICE") or "cpu").strip() or "cpu"
    return SentenceTransformer(_MODEL_NAME, device=device)


_cached_embedder = None


def _get_embedder():
    """Arama başına model yükleme yapmaz (ilk çağrıda bir kez bellekte tutulur)."""
    global _cached_embedder
    if _cached_embedder is None:
        _cached_embedder = _embed_model()
    return _cached_embedder


def _file_digest(rel: str, body: str) -> str:
    one_h = hashlib.sha256()
    one_h.update(rel.encode("utf-8"))
    one_h.update(b"\0")
    one_h.update(body.encode("utf-8"))
    return one_h.hexdigest()


def _overall_digest(file_digests: dict[str, str]) -> str:
    overall_h = hashlib.sha256()
    for rel in sorted(file_digests.keys(), key=_norm_rel):
        overall_h.update(rel.encode("utf-8"))
        overall_h.update(file_digests[rel].encode("utf-8"))
    return overall_h.hexdigest()


def build_index(
    knowledge_root: Path | None = None,
    force: bool = False,
    incremental: bool = False,
) -> dict:
    root = knowledge_root or _knowledge_root()
    root = Path(root)
    manifest_path = _index_dir() / "manifest.json"
    chunks_path = _index_dir() / "chunks.jsonl"
    emb_path = _index_dir() / "embeddings.npy"

    _index_dir().mkdir(parents=True, exist_ok=True)

    old: dict = {}
    old_file_digests: dict[str, str] = {}
    if manifest_path.is_file():
        try:
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(old.get("file_digests"), dict):
                old_file_digests = dict(old.get("file_digests") or {})
        except (OSError, json.JSONDecodeError):
            old, old_file_digests = {}, {}

    known_norm = {_norm_rel(k) for k in old_file_digests}
    # force=True: Şamile hariç tüm md (bilinçli tam rebuild).
    # aksi: yalnız bilinen + ince yol (learned) — kör yutma yok.
    files_payload = _load_markdown_files(
        root,
        known_norm=known_norm if (old_file_digests and not force) else None,
        restrict_new=bool(old_file_digests and not force),
    )
    payload_map = {rel: body for rel, body in files_payload}

    # Dosya bazlı hash: incremental (kademeli) gömme güncellemeleri için.
    file_digests: dict[str, str] = {}
    for rel, body in files_payload:
        file_digests[rel] = _file_digest(rel, body)

    # Şamile: diskten yüklenmez; incremental'da eski manifest girdilerini dondur.
    if not force:
        frozen_norm = {_norm_rel(k) for k in file_digests}
        for rel, fd in old_file_digests.items():
            if _is_shamela_main_skip(rel) and _norm_rel(rel) not in frozen_norm:
                file_digests[rel] = fd

    digest = _overall_digest(file_digests)

    if (
        not force
        and manifest_path.is_file()
        and chunks_path.is_file()
        and emb_path.is_file()
    ):
        old_digest = old.get("digest")
        if not incremental and old_digest == digest:
            return {
                "status": "cached",
                "chunks": old.get("num_chunks", 0),
                "digest": digest,
            }

        # Incremental: sadece değişen/eklenen/çıkarılan md.
        # Kör full rebuild koruması: digest kaymış + force yok → incremental.
        use_inc = incremental or (
            not force
            and old.get("model") == _MODEL_NAME
            and bool(old_file_digests)
        )
        if use_inc and old.get("model") == _MODEL_NAME and old_file_digests:
            new_norm = {_norm_rel(k) for k in file_digests}
            changed_rels = [
                rel
                for rel, fd in file_digests.items()
                if old_file_digests.get(rel) != fd and not _is_shamela_main_skip(rel)
            ]
            removed_rels = [
                rel
                for rel in old_file_digests.keys()
                if _norm_rel(rel) not in new_norm and not _is_shamela_main_skip(rel)
            ]

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
                return {
                    "status": "index_corrupt",
                    "hint": "İndeks bozuk; kör full rebuild yok. Bilinçli: build_index(force=True).",
                    "chunks": int(old.get("num_chunks") or 0),
                }

            changed_set = set(changed_rels)
            removed_set = set(removed_rels)

            keep_indices: list[int] = []
            kept_chunks: List[Chunk] = []
            for i, c in enumerate(old_chunks):
                if c.source in removed_set:
                    continue
                if c.source in changed_set:
                    continue
                # Kaynak hâlâ mevcutsa veya Şamile dondurulmuşsa tut.
                if c.source in file_digests or _is_shamela_main_skip(c.source):
                    keep_indices.append(i)
                    kept_chunks.append(c)

            keep_emb = old_emb[keep_indices] if keep_indices else old_emb[:0]

            changed_payload = [
                (rel, payload_map[rel]) for rel in sorted(changed_rels) if rel in payload_map
            ]
            new_chunks: List[Chunk] = []
            for rel, body in changed_payload:
                for piece in _split_text(body):
                    new_chunks.append(Chunk(text=piece, source=rel))

            if new_chunks:
                model = _get_embedder()
                texts_new = [c.text for c in new_chunks]
                emb_new = model.encode(
                    texts_new, normalize_embeddings=True, show_progress_bar=True
                )
                emb_out = np.vstack([keep_emb, emb_new]) if len(keep_indices) else emb_new
            else:
                emb_out = keep_emb

            chunks_out = kept_chunks + new_chunks
            _atomic_save_npy(emb_path, emb_out)
            _atomic_write_chunks_jsonl(chunks_path, chunks_out)
            _atomic_write_text(
                manifest_path,
                json.dumps(
                    {
                        "digest": digest,
                        "num_chunks": len(chunks_out),
                        "model": _MODEL_NAME,
                        "file_digests": file_digests,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
            )
            invalidate_rag_cache()
            return {
                "status": "incremental",
                "chunks": len(chunks_out),
                "digest": digest,
                "changed_files": len(changed_rels),
                "removed_files": len(removed_rels),
            }

    # Tam rebuild yalnız force=True ile (kör yutma engeli).
    if not force:
        return {
            "status": "refused_full_rebuild",
            "hint": (
                "Kör full rebuild engellendi. Learned için upsert_learned_into_main_index; "
                "bilinçli tam rebuild: build_index(force=True)."
            ),
            "chunks": int(old.get("num_chunks") or 0),
            "digest": digest,
        }

    chunks: List[Chunk] = []
    for rel, body in files_payload:
        for piece in _split_text(body):
            chunks.append(Chunk(text=piece, source=rel))

    model = _get_embedder()
    texts = [c.text for c in chunks]
    emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    _atomic_save_npy(emb_path, emb)
    _atomic_write_chunks_jsonl(chunks_path, chunks)
    _atomic_write_text(
        manifest_path,
        json.dumps(
            {
                "digest": digest,
                "num_chunks": len(chunks),
                "model": _MODEL_NAME,
                "file_digests": file_digests,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    invalidate_rag_cache()
    return {"status": "built", "chunks": len(chunks), "digest": digest}


def upsert_sources_into_main_index(
    rels: list[str],
    *,
    knowledge_root: Path | None = None,
) -> dict:
    """İnce yol: yalnız verilen relative md yollarını ana indekse ekle/güncelle.

    Full knowledge taraması yok. Şamile yolları reddedilir.
    """
    root = Path(knowledge_root or _knowledge_root())
    manifest_path = _index_dir() / "manifest.json"
    chunks_path = _index_dir() / "chunks.jsonl"
    emb_path = _index_dir() / "embeddings.npy"
    if not (manifest_path.is_file() and chunks_path.is_file() and emb_path.is_file()):
        return {
            "status": "no_base_index",
            "hint": "Ana indeks yok; ince yol taban ister.",
            "changed_files": 0,
        }

    try:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "manifest_error", "error": str(exc)[:200], "changed_files": 0}

    file_digests: dict[str, str] = dict(man.get("file_digests") or {})
    known_by_norm = {_norm_rel(k): k for k in file_digests}

    try:
        old_chunks = _load_chunks()
        old_emb = _load_embeddings()
    except Exception as exc:
        return {"status": "index_corrupt", "error": str(exc)[:200], "changed_files": 0}
    if not old_chunks or old_emb is None or len(old_chunks) != len(old_emb):
        return {
            "status": "index_corrupt",
            "hint": "chunk/emb uyumsuz; ince yol durdu.",
            "changed_files": 0,
        }

    changed: list[tuple[str, str, str]] = []  # key, body, digest
    skipped_shamela = 0
    for raw_rel in rels:
        rel = str(raw_rel).strip()
        if not rel:
            continue
        if _is_shamela_main_skip(rel):
            skipped_shamela += 1
            continue
        path = root / rel
        if not path.is_file():
            # OS ayırıcı dene
            path = root / _norm_rel(rel)
            if not path.is_file():
                continue
            rel = str(path.relative_to(root))
        try:
            body = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _is_dokunma_markdown(path, body):
            continue
        # Manifest anahtarı: varsa eski anahtarı koru (slash tutarlılığı)
        key = known_by_norm.get(_norm_rel(rel), rel)
        fd = _file_digest(key, body)
        if file_digests.get(key) == fd:
            continue
        changed.append((key, body, fd))

    if not changed:
        return {
            "status": "cached",
            "chunks": int(man.get("num_chunks") or len(old_chunks)),
            "changed_files": 0,
            "skipped_shamela": skipped_shamela,
        }

    drop_norm = {_norm_rel(k) for k, _, _ in changed}
    keep_indices: list[int] = []
    kept_chunks: List[Chunk] = []
    for i, c in enumerate(old_chunks):
        if _norm_rel(c.source) in drop_norm:
            continue
        keep_indices.append(i)
        kept_chunks.append(c)
    keep_emb = old_emb[keep_indices] if keep_indices else old_emb[:0]

    new_chunks: List[Chunk] = []
    for key, body, fd in changed:
        for piece in _split_text(body):
            new_chunks.append(Chunk(text=piece, source=key))
        file_digests[key] = fd

    model = _get_embedder()
    emb_new = model.encode(
        [c.text for c in new_chunks],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    emb_out = np.vstack([keep_emb, emb_new]) if len(keep_indices) else emb_new
    chunks_out = kept_chunks + new_chunks
    digest = _overall_digest(file_digests)

    _atomic_save_npy(emb_path, emb_out)
    _atomic_write_chunks_jsonl(chunks_path, chunks_out)
    _atomic_write_text(
        manifest_path,
        json.dumps(
            {
                "digest": digest,
                "num_chunks": len(chunks_out),
                "model": _MODEL_NAME,
                "file_digests": file_digests,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    invalidate_rag_cache()
    return {
        "status": "learned_upsert" if all(_is_thin_auto_ingest_rel(k) for k, _, _ in changed) else "upsert",
        "chunks": len(chunks_out),
        "digest": digest,
        "changed_files": len(changed),
        "skipped_shamela": skipped_shamela,
    }


def upsert_learned_into_main_index(*, knowledge_root: Path | None = None) -> dict:
    """learned/*.md ince yol — sohbet öğrenmesi ana indekse girsin, Şamile/ortak yutulmasın."""
    root = Path(knowledge_root or _knowledge_root())
    learned = root / "learned"
    if not learned.is_dir():
        return {"status": "empty", "changed_files": 0, "chunks": 0}
    rels: list[str] = []
    for p in sorted(learned.glob("*.md")):
        try:
            if _is_dokunma_markdown(p):
                continue
            rels.append(str(p.relative_to(root)))
        except OSError:
            continue
    out = upsert_sources_into_main_index(rels, knowledge_root=root)
    out["learned_scanned"] = len(rels)
    return out


def index_knowledge_files(
    rels: list[str] | str,
    *,
    knowledge_root: Path | None = None,
) -> dict:
    """Nebula / TDK / Tarih / learned ince yol — `build_index(restrict_new)` yerine.

    ``rels`` knowledge köküne göre relative (örn. ``nebula/x/incremental/batch.md``).
    Şamile yolları reddedilir. Kör full rebuild yok.
    """
    if isinstance(rels, str):
        rels = [rels]
    cleaned: list[str] = []
    for raw in rels:
        r = str(raw or "").strip().replace("\\", "/")
        if not r:
            continue
        if r.startswith("knowledge/"):
            r = r[len("knowledge/") :]
        cleaned.append(r)
    if not cleaned:
        return {"status": "empty", "changed_files": 0}
    return upsert_sources_into_main_index(cleaned, knowledge_root=knowledge_root)


def _load_chunks() -> List[Chunk]:
    chunks_path = _index_dir() / "chunks.jsonl"
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
    emb_path = _index_dir() / "embeddings.npy"
    if not emb_path.is_file():
        return None
    return np.load(str(emb_path))


_index_mtime_ns: int | None = None
_cached_chunks_list: List[Chunk] | None = None
_cached_emb_arr: np.ndarray | None = None
# `search_tarih_hafiza` / `search_tdk_hafiza` / `search_nebula_hafiza` için alt küme indeksleri.
_tarih_chunk_row_indices: np.ndarray | None = None
_tdk_chunk_row_indices: np.ndarray | None = None
_nebula_chunk_row_indices: np.ndarray | None = None


def _rag_cache_enabled() -> bool:
    return os.environ.get("RAG_INDEX_CACHE", "1").strip() not in ("0", "false", "no")


def _get_cached_index() -> tuple[List[Chunk], np.ndarray | None]:
    """İndeks dosyalarını her aramada diskten okumaz; embeddings.npy değişince yeniler."""
    global _index_mtime_ns, _cached_chunks_list, _cached_emb_arr
    global _tarih_chunk_row_indices, _tdk_chunk_row_indices, _nebula_chunk_row_indices
    emb_path = _index_dir() / "embeddings.npy"
    chunks_path = _index_dir() / "chunks.jsonl"
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
        _tarih_chunk_row_indices = np.array(
            [i for i, c in enumerate(chunks) if _source_is_tarih_hafiza(c.source)],
            dtype=np.int64,
        )
        _tdk_chunk_row_indices = np.array(
            [i for i, c in enumerate(chunks) if source_is_tdk(c.source)],
            dtype=np.int64,
        )
        _nebula_chunk_row_indices = np.array(
            [i for i, c in enumerate(chunks) if _source_is_nebula(c.source)],
            dtype=np.int64,
        )
    else:
        _cached_chunks_list = None
        _cached_emb_arr = None
        _index_mtime_ns = None
        _tarih_chunk_row_indices = None
        _tdk_chunk_row_indices = None
        _nebula_chunk_row_indices = None
    return chunks, emb


def warmup_index() -> None:
    """API / Gradio başlarken indeksi ve gömme modelini önceden yükle (ilk mesaj gecikmesini azaltır)."""
    if not _rag_cache_enabled():
        return
    _get_embedder()
    _get_cached_index()
    try:
        from ilim_assistant.ruzgar_tur_teshis_f0 import mark_warmup

        mark_warmup("rag", True)
    except Exception:
        pass


def _source_is_archive(rel: str) -> bool:
    """İndeks kaynağı `ilim-assistant/arsiv/...` altında mı? (Windows / POSIX yolu)."""
    p = (rel or "").replace("\\", "/").lower()
    return "/arsiv/" in p or p.startswith("arsiv/")


def _source_is_tarih_hafiza(rel: str) -> bool:
    """`knowledge/TARIH_VE_KULTUR/...` altındaki Tarih Hafızası kaynakları."""
    p = (rel or "").replace("\\", "/").lower()
    return "tarih_ve_kultur" in p or "tarh_ve_kultur" in p


def source_is_tarih_hafiza(rel: str) -> bool:
    """Dışarıdan: kaynak yolu Tarih Hafızası mı?"""
    return _source_is_tarih_hafiza(rel)


def source_is_tdk(rel: str) -> bool:
    """TDK sözlük / kademeli paket kaynakları (`knowledge/tdk/...`)."""
    p = (rel or "").replace("\\", "/").lower()
    return "/tdk/" in p or p.startswith("tdk/")


def _source_is_nebula(rel: str) -> bool:
    p = (rel or "").replace("\\", "/").lower()
    return "/nebula/" in p or p.startswith("nebula/")


def source_is_nebula(rel: str) -> bool:
    return _source_is_nebula(rel)


def source_is_din(rel: str) -> bool:
    """Dini ilimler külliyatı (`knowledge/ilim/din/...`). Silme değil; arama hijyeni için."""
    p = (rel or "").replace("\\", "/").lower()
    return "/ilim/din/" in f"/{p}" or p.startswith("ilim/din/")


def _din_hygiene_enabled() -> bool:
    return os.environ.get("RUZGAR_RAG_DIN_HYGIENE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _lemma_norm(s: str) -> str:
    t = unicodedata.normalize("NFKD", (s or "").strip()).casefold()
    return " ".join(t.split())


def _tdk_chunk_has_exact_lemma(text: str, lemma: str) -> bool:
    """Chunk 900 karakter dilimlerine bölünebildiği için tüm `##` başlıkları taranır."""
    want = _lemma_norm(lemma)
    if not want:
        return False
    for line in (text or "").splitlines():
        s = line.strip()
        if s.startswith("## "):
            if _lemma_norm(s[3:].strip()) == want:
                return True
    return False


def search_tdk_exact_lemma(lemma: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """
    TDK paketlerinde madde başlığı (## satırı) ile tam eşleşme — vektör benzerliği yok, skor sabit 1.0.
    Yakın ses/yazım eşlemesi yapmaz (Hayalet / Haya karışması riskini azaltır).
    """
    want = _lemma_norm(lemma)
    if not want:
        return []
    tk = max(1, top_k)
    chunks, emb = _get_cached_index()
    if not chunks or emb is None:
        return []

    out: List[Tuple[str, str, float]] = []
    for c in chunks:
        if not source_is_tdk(c.source):
            continue
        if not _tdk_chunk_has_exact_lemma(c.text, lemma):
            continue
        out.append((c.text, c.source, 1.0))
        if len(out) >= tk:
            break
    return out


# Ortak alan / fen rafları — din külliyatı altında ezilmesin diye sorgu ipucu → yol öneği.
_ORTAK_DOMAIN_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        (
            "bilim",
            "astronomi",
            "fotosentez",
            "atom",
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "hipotez",
            "bilimsel",
            "galaksi",
            "newton",
            "dna",
            "geometri",
            "atmosfer",
            "troposfer",
            "ohm",
            "organel",
            "mitokondri",
            "kalitim",
            "kalıtım",
            "bagisiklik",
            "bağışıklık",
            "oranti",
            "orantı",
            "medyan",
            "gps",
        ),
        (
            "ortak_kaynak/alanlar/bilim",
            "kutuphane/raflar/01_",
            "kutuphane/raflar/02_",
            "kutuphane/raflar/03_",
            "kutuphane/raflar/06_",
        ),
    ),
    (
        (
            "cografya",
            "coğrafya",
            "karadeniz",
            "marmara",
            "akdeniz",
            "anadolu",
            "iklim",
            "harita",
            "kita",
            "kıta",
            "okyanus",
            "enlem",
            "boylam",
        ),
        ("ortak_kaynak/alanlar/cografya", "kutuphane/raflar/04_"),
    ),
    (
        (
            "edebiyat",
            "divan",
            "kelile",
            "makamat",
            "maqamat",
            "tanzimat",
            "fuzuli",
            "shakespeare",
            "maarri",
            "buhturi",
        ),
        ("ortak_kaynak/alanlar/edebiyat_sanat",),
    ),
    (
        (
            "felsefe",
            "meşşai",
            "messai",
            "metafizik",
            "tahafut",
            "tehafut",
            "farabi",
            "ibn sina",
            "avicenna",
        ),
        ("ortak_kaynak/alanlar/felsefe",),
    ),
    (
        (
            "psikoloji",
            "nefs",
            "nefis",
            "idrak",
            "mizan amal",
            "nefs gucler",
            "nefis güç",
        ),
        ("ortak_kaynak/alanlar/psikoloji",),
    ),
    (
        (
            "turev",
            "türev",
            "integral",
            "lineer cebir",
            "olasilik",
            "olasılık",
            "kirchhoff",
            "paralaks",
            "levha tekton",
            "sera etkisi",
            "dolasim sistemi",
            "dolaşım sistemi",
            "sesbilim",
            "makam",
            "tabakalasma",
            "tabakalaşma",
            "kuvvetler ayril",
            "firsat maliyeti",
            "fırsat maliyeti",
            "hukuk devleti",
            "mufredat",
            "müfredat",
        ),
        (
            "ortak_kaynak/alanlar/matematik_derin",
            "ortak_kaynak/alanlar/istatistik_olasilik",
            "ortak_kaynak/alanlar/elektrik_elektronik",
            "ortak_kaynak/alanlar/astronomi_derin",
            "ortak_kaynak/alanlar/jeoloji",
            "ortak_kaynak/alanlar/cevre_bilimleri",
            "ortak_kaynak/alanlar/anatomi_fizyoloji",
            "ortak_kaynak/alanlar/dilbilim",
            "ortak_kaynak/alanlar/muzik",
            "ortak_kaynak/alanlar/sosyoloji",
            "ortak_kaynak/alanlar/siyaset",
            "ortak_kaynak/alanlar/ekonomi",
            "ortak_kaynak/alanlar/hukuk",
            "ortak_kaynak/alanlar/egitim_bilimleri",
        ),
    ),
    (
        (
            "islemci",
            "işlemci",
            "komut seti",
            "sanal bellek",
            "derleyici",
            "veri yapisi",
            "veri yapısı",
            "bellek hiyerars",
            "bellek hiyerarş",
            "kernel",
            "dosya sistemi",
            "saat darbesi",
            "hash tablosu",
            "birim testi",
        ),
        (
            "ortak_kaynak/alanlar/bilgisayar_muhendisligi",
            "ortak_kaynak/alanlar/bilgisayar_eserleri",
        ),
    ),
    (
        (
            "teknoloji",
            "bilgisayar",
            "internet",
            "yapay zeka",
            "yapay zekâ",
            "şifre",
            "sifre",
            "programlama",
            "https",
        ),
        ("ortak_kaynak/alanlar/teknoloji", "kutuphane/raflar/08_"),
    ),
)

_ortak_path_row_cache: dict[tuple[str, ...], np.ndarray] = {}
_ortak_path_cache_chunks_id: int | None = None


def _fold_q(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower()


def _ortak_path_prefixes_for_query(query: str) -> tuple[str, ...]:
    if os.environ.get("RUZGAR_RAG_ORTAK_BOOST", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return ()
    low = _fold_q(query)
    found: list[str] = []
    for cues, paths in _ORTAK_DOMAIN_HINTS:
        if any(_fold_q(c) in low for c in cues):
            found.extend(paths)
    # benzersiz, sıra korunur
    out: list[str] = []
    for p in found:
        if p not in out:
            out.append(p)
    return tuple(out)


def _ortak_domain_row_indices(chunks: List[Chunk], prefixes: tuple[str, ...]) -> np.ndarray:
    global _ortak_path_row_cache, _ortak_path_cache_chunks_id
    cid = id(chunks)
    if _ortak_path_cache_chunks_id != cid:
        _ortak_path_row_cache = {}
        _ortak_path_cache_chunks_id = cid
    cached = _ortak_path_row_cache.get(prefixes)
    if cached is not None:
        return cached
    prefs = tuple(p.replace("\\", "/") for p in prefixes)

    def _ok(src: str) -> bool:
        s = (src or "").replace("\\", "/")
        return any(p in s for p in prefs)

    arr = np.array([i for i, c in enumerate(chunks) if _ok(c.source)], dtype=np.int64)
    _ortak_path_row_cache[prefixes] = arr
    return arr


def search(query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """Dönüş: (metin, kaynak, skor) — skor yaklaşık uyum.

    Anlam kilidi: içerik kelimesi taşımayan chunk'lar elenir (yanlış raftan
    cevap karışmasını keser). Kapat: ``RUZGAR_RAG_CONTENT_FILTER=0``.

    Ortak alan ipucu varsa (`RUZGAR_RAG_ORTAK_BOOST`, varsayılan açık) ilgili
    yollar alt kümeden aday çekilip hafifçe öne alınır — din külliyatı baskınlığını azaltır.

    Ortak/fen ipucu açıkken `RUZGAR_RAG_DIN_HYGIENE=1` (varsayılan) global doldurmada
    `ilim/din` kaynaklarını atlar (külliyat silinmez).
    """
    chunks, emb = _get_cached_index()
    if not chunks or emb is None or len(chunks) != len(emb):
        return []

    model = _get_embedder()
    q = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    sim = emb @ q
    # Geniş havuz al, sonra skor+anlam süz
    pool = max(int(top_k) * 4, 16)
    idx = np.argsort(-sim)[: min(pool, len(sim))]
    best: dict[tuple[str, str], Tuple[str, str, float]] = {}

    def _put(text: str, source: str, score: float) -> None:
        key = (source, (text or "")[:96])
        prev = best.get(key)
        if prev is None or score > prev[2]:
            best[key] = (text, source, score)

    for i in idx:
        ii = int(i)
        _put(chunks[ii].text, chunks[ii].source, float(sim[ii]))

    # Şamile kategori shard'ları (ana indeksi şişirmeden). Ortak/fen hijyeninde eklenmez.
    if os.environ.get("RUZGAR_SHAMELA_SHARDS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        try:
            ortak_prefixes = _ortak_path_prefixes_for_query(query)
            skip_shamela = bool(ortak_prefixes) and _din_hygiene_enabled()
            if not skip_shamela:
                from ilim_assistant.shamela_rag_shards import (
                    pick_shamela_cats_for_query,
                    search_shamela_shards,
                )
                from ilim_assistant.shamela_rag_shards import load_registry as _sam_reg

                _ready = dict((_sam_reg().get("ready") or {}))
                # K3: soru dilinden kaynak diline (Arapça) terim/sorgu genişletme (veri sözlüğü; kapat RUZGAR_K3_DIN_SORGU=0)
                _k3 = None
                try:
                    from ilim_assistant.ruzgar_k3_sorgu import plan_for_query as _k3_plan
                    from ilim_assistant.ruzgar_tur_teshis_f0 import note_k3 as _note_k3

                    _note_k3(None)
                    _k3 = _k3_plan(query)
                    if _k3 is not None and not _k3.aktif:
                        _k3 = None
                except Exception:
                    _k3 = None
                _cats = pick_shamela_cats_for_query(
                    query, _ready, prefer=(_k3.kategoriler if _k3 is not None else None)
                )
                try:
                    from ilim_assistant.ruzgar_tur_teshis_f0 import note_shamela_cats

                    note_shamela_cats(list(_cats or []))
                except Exception:
                    pass
                _sham1 = list(
                    search_shamela_shards(
                        query,
                        top_k=max(int(top_k), 8),
                        q_vec=q,
                        cats=_cats,
                        k3=_k3,
                    )
                )
                for text, source, score in _sham1:
                    _put(text, source, float(score))
                # F2.2 kademe-2: zayıf ilk geçiş + süre varsa derin Şamile
                try:
                    from ilim_assistant.ruzgar_umed_cevap_emri import remaining_sec

                    _rem = float(remaining_sec())
                except Exception:
                    _rem = 0.0
                try:
                    _min_rem = float(
                        os.environ.get("RUZGAR_SHAMELA_DEEP_MIN_REMAIN_SEC", "7") or "7"
                    )
                except ValueError:
                    _min_rem = 7.0
                _deep_on = os.environ.get("RUZGAR_SHAMELA_DEEP", "1").strip().lower() not in (
                    "0",
                    "false",
                    "no",
                )
                if (
                    _deep_on
                    and _rem >= _min_rem
                    and len(_sham1) < max(2, int(top_k) // 2 + 1)
                    and _cats is not None
                ):
                    _deep_cats = pick_shamela_cats_for_query(
                        query, _ready, deep=True, exclude=_cats,
                        prefer=(_k3.kategoriler if _k3 is not None else None),
                    )
                    if _deep_cats:
                        try:
                            from ilim_assistant.ruzgar_tur_teshis_f0 import note_shamela_cats

                            note_shamela_cats(list(_cats) + list(_deep_cats))
                        except Exception:
                            pass
                        for text, source, score in search_shamela_shards(
                            query,
                            top_k=max(int(top_k), 8),
                            q_vec=q,
                            cats=_deep_cats,
                            deep=True,
                            exclude_cats=_cats,
                            k3=_k3,
                        ):
                            _put(text, source, float(score))
        except Exception:
            pass

    # Din / Şamile sorusunda bilgisayar RAG yükleme (870MB+) sohbeti öldürür
    _din_q = False
    try:
        _ql = _fold_q(query)
        _din_q = any(
            k in _ql
            for k in (
                "samile",
                "samil",
                "shamel",
                "hadis",
                "buhari",
                "muslim",
                "muslim",
                "tefsir",
                "fikih",
                "ayet",
                "kuran",
                "kur'an",
                "akaid",
                "siyer",
                "sahih",
                "niyet",
                "mezhep",
                "fetva",
                "kimdir",
                "sahabe",
                "sahabi",
                "peygamber",
                "muhammed",
                "ebubekir",
                "resulullah",
                "teracim",
                "tabakat",
            )
        ) or (
            (" hz " in f" {_ql} " or _ql.startswith("hz "))
            and any(k in _ql for k in ("omer", "osman", "ali", "hatice", "aise", "ayse", "hamza"))
        )
    except Exception:
        _din_q = False

    # Adım 5 — seçili ayıklama yan indeksi (ana RAG MemoryError kaçınır)
    if os.environ.get("RUZGAR_AYIKLAMA_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        try:
            from ilim_assistant.ruzgar_ayiklama_rag import search_ayiklama

            for text, source, score in search_ayiklama(
                query, top_k=max(int(top_k), 6), q_vec=q
            ):
                _put(text, source, float(score))
        except Exception:
            pass

    # Sahne Y1 meslek yan indeksi (9147 chunk sidecar)
    if os.environ.get("RUZGAR_SAHNE_Y1_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        try:
            from ilim_assistant.ruzgar_sahne_y1_rag import search_sahne_y1

            for text, source, score in search_sahne_y1(
                query, top_k=max(int(top_k), 6), q_vec=q
            ):
                _put(text, source, float(score))
        except Exception:
            pass

    # Adım 4 — bilgisayar eserleri yan indeksi (Dalga A omurga)
    if (
        not _din_q
        and os.environ.get("RUZGAR_BILGISAYAR_RAG", "1").strip().lower()
        not in (
            "0",
            "false",
            "no",
        )
    ):
        try:
            from ilim_assistant.ruzgar_bilgisayar_rag import search_bilgisayar

            for text, source, score in search_bilgisayar(
                query, top_k=max(int(top_k), 6), q_vec=q
            ):
                _put(text, source, float(score))
        except Exception:
            pass

    # Ortak alan / fen rafı boost (+ yol ipucu; düşük skorlu kavram md kaçmasın)
    try:
        boost = float(os.environ.get("RUZGAR_RAG_ORTAK_BOOST_SCORE", "0.10") or "0.10")
    except ValueError:
        boost = 0.10
    boost = max(0.0, min(0.25, boost))
    prefixes = _ortak_path_prefixes_for_query(query)
    domain_hits: List[Tuple[str, str, float]] = []
    if prefixes:
        row_idx = _ortak_domain_row_indices(chunks, prefixes)
        if row_idx.size:
            sub = emb[row_idx]
            sub_sim = sub @ q
            try:
                take_n = int(os.environ.get("RUZGAR_RAG_ORTAK_SCAN", "256") or "256")
            except ValueError:
                take_n = 256
            take = min(max(pool, int(top_k) * 8, take_n), int(row_idx.size))
            order = np.argsort(-sub_sim)[:take]
            path_toks = [
                t
                for t in _fold_q(query).replace("ı", "i").split()
                if len(t) >= 4 and t not in {"nedir", "nasil", "nasildir", "hakkinda", "neden"}
            ]
            seen_gi: set[int] = set()
            for j in order:
                ji = int(j)
                gi = int(row_idx[ji])
                seen_gi.add(gi)
                sc = float(sub_sim[ji]) + boost
                _put(chunks[gi].text, chunks[gi].source, sc)
                domain_hits.append((chunks[gi].text, chunks[gi].source, sc))
            # Yol adında sorgu ipucu (nefs_gucleri, bilimsel_yontem, …)
            # Erken kesme yok: tek token çok dosyaya uyuyor; çoklu token + skor ile seç.
            if path_toks:
                path_extra: list[tuple[int, float, int]] = []
                for gi0 in row_idx.tolist():
                    gi = int(gi0)
                    src_fold = _fold_q(chunks[gi].source or "").replace("\\", "/")
                    n_hit = sum(1 for t in path_toks if t.replace("ı", "i") in src_fold)
                    if n_hit <= 0:
                        continue
                    sc = float(emb[gi] @ q) + boost + 0.04 * n_hit
                    path_extra.append((n_hit, sc, gi))
                path_extra.sort(key=lambda x: (x[0], x[1]), reverse=True)
                for _n, sc, gi in path_extra[:96]:
                    _put(chunks[gi].text, chunks[gi].source, sc)
                    domain_hits.append((chunks[gi].text, chunks[gi].source, sc))

    raw = sorted(best.values(), key=lambda h: h[2], reverse=True)
    tk = max(1, int(top_k))

    def _in_domain(src: str) -> bool:
        if not prefixes:
            return False
        s = (src or "").replace("\\", "/")
        return any(p.replace("\\", "/") in s for p in prefixes)

    def _merge_domain_first(
        dom: List[Tuple[str, str, float]],
        glob: List[Tuple[str, str, float]],
    ) -> List[Tuple[str, str, float]]:
        """Ortak/fen adayları önce; global doldurmada din külliyatı (hijyen açıkken) atlanır."""
        out: List[Tuple[str, str, float]] = []
        seen: set[tuple[str, str]] = set()
        skip_din = bool(prefixes) and _din_hygiene_enabled()

        def _take(h: Tuple[str, str, float], *, allow_din: bool) -> bool:
            if skip_din and not allow_din and source_is_din(h[1]):
                return False
            key = (h[1], (h[0] or "")[:96])
            if key in seen:
                return False
            out.append(h)
            seen.add(key)
            return True

        for h in dom:
            _take(h, allow_din=True)
            if len(out) >= tk:
                return out[:tk]
        # Global: önce din dışı, yetmezse (hijyen kapalıysa) din
        for h in glob:
            _take(h, allow_din=False)
            if len(out) >= tk:
                return out[:tk]
        if not skip_din:
            for h in glob:
                _take(h, allow_din=True)
                if len(out) >= tk:
                    break
        return out[:tk]

    # İçerik filtresi kapalı olsa bile ortak/fen rafı din altında ezilmesin
    domain_preferred: List[Tuple[str, str, float]] | None = None
    if prefixes and domain_hits:
        dom_sorted = sorted(domain_hits, key=lambda h: h[2], reverse=True)
        try:
            from ilim_assistant.ruzgar_anlam_koruma import (
                chunk_fits_query,
                filter_rag_hits,
                rag_default_score_min,
            )

            floor = rag_default_score_min()
            dom_fit = filter_rag_hits(
                query,
                dom_sorted,
                min_score=max(0.18, floor - 0.12),
                soft=False,
            )
            if not dom_fit:
                dom_fit = [
                    h
                    for h in dom_sorted
                    if h[2] >= max(0.15, floor - 0.16)
                    and chunk_fits_query(query, h[0], source=str(h[1] or ""))
                ][: max(tk * 2, 8)]
            if not dom_fit:
                dom_fit = [h for h in dom_sorted if h[2] >= 0.28][:tk]
            if dom_fit:
                domain_preferred = _merge_domain_first(dom_fit, raw)
        except Exception:
            domain_preferred = _merge_domain_first(
                [h for h in dom_sorted if h[2] >= 0.28][:tk],
                raw,
            )

    try:
        if os.environ.get("RUZGAR_RAG_CONTENT_FILTER", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        ):
            from ilim_assistant.ruzgar_anlam_koruma import filter_rag_hits, rag_default_score_min

            soft = os.environ.get("RUZGAR_RAG_CONTENT_SOFT", "0").strip().lower() in (
                "1",
                "true",
                "yes",
            )
            floor = rag_default_score_min()
            base = domain_preferred if domain_preferred else raw
            filtered = filter_rag_hits(
                query,
                base,
                min_score=floor if not domain_preferred else max(0.18, floor - 0.12),
                soft=soft,
            )
            if filtered:
                if domain_preferred and prefixes:
                    dom_f = [h for h in filtered if _in_domain(h[1])]
                    glob_f = [h for h in filtered if not _in_domain(h[1])]
                    if _din_hygiene_enabled():
                        glob_f = [h for h in glob_f if not source_is_din(h[1])]
                    if dom_f:
                        return _merge_domain_first(dom_f, glob_f)
                if prefixes and _din_hygiene_enabled():
                    filtered = [h for h in filtered if not source_is_din(h[1])] or filtered
                return filtered[:tk]
            if domain_preferred:
                return domain_preferred[:tk]
            if not soft:
                return []
    except Exception:
        pass
    if domain_preferred:
        return domain_preferred[:tk]
    return raw[:tk]


def _arsiv_root() -> Path | None:
    try:
        from ilim_assistant.ruzgar_public_mode import shared_arsiv_root

        p = shared_arsiv_root()
        if p is not None and p.is_dir():
            return p
    except Exception:
        pass
    p = _PKG_ROOT / "arsiv"
    return p if p.is_dir() else None


def _arsiv_disk_search_enabled() -> bool:
    return os.environ.get("RUZGAR_ARSIV_DISK_SEARCH", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


_ARSIV_SKIP_DIR_NAMES = frozenset(
    {
        "klon-sesler",
        "klon-sesler-umit-ozel",
        "ses-referans",
        "mimar-fotograf",
        "mimar-sanat",
        "mimar-tasarim",
        "ana_motor_uploads",
        "hafiza_karantina",
    }
)

# Dosya listesi mtime önbelleği — her aramada full rglob maliyetini keser (M4).
_arsiv_file_list_cache: dict[str, Any] = {
    "root": None,
    "sig": None,
    "files": None,
    "built_at": 0.0,
}
_arsiv_disk_last_meta: dict[str, Any] = {
    "scanned": 0,
    "cap": 0,
    "truncated": False,
    "deadline_hit": False,
    "cache_hit": False,
}


def arsiv_disk_last_meta() -> dict[str, Any]:
    return dict(_arsiv_disk_last_meta)


def _arsiv_root_mtime_sig(root: Path) -> str:
    """Üst dizin mtime imzası — liste tazeliği için ucuz kontrol."""
    try:
        parts = [f"{root.stat().st_mtime_ns}"]
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower())[:48]:
            try:
                parts.append(f"{child.name}:{child.stat().st_mtime_ns}")
            except OSError:
                continue
        return "|".join(parts)
    except OSError:
        return str(time.time())


def _arsiv_list_searchable_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    """md/txt listesi — mtime imzası ile önbellek; (paths, cache_hit)."""
    global _arsiv_file_list_cache
    sig = _arsiv_root_mtime_sig(root)
    root_s = str(root.resolve()) if root.exists() else str(root)
    cached = _arsiv_file_list_cache
    if (
        cached.get("root") == root_s
        and cached.get("sig") == sig
        and isinstance(cached.get("files"), list)
    ):
        files = list(cached["files"])
        return files[:max_files], True

    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (".md", ".txt"):
            continue
        try:
            parts_l = [p.lower() for p in path.relative_to(root).parts]
        except ValueError:
            continue
        if any(
            p.startswith("_backup") or p.startswith("_virus") or p.startswith("_legacy")
            for p in parts_l
        ):
            continue
        if parts_l and parts_l[0] in _ARSIV_SKIP_DIR_NAMES:
            continue
        out.append(path)
        if len(out) >= max_files:
            break
    _arsiv_file_list_cache = {
        "root": root_s,
        "sig": sig,
        "files": out,
        "built_at": time.time(),
    }
    return list(out), False


def arsiv_search_status() -> dict:
    """Dürüst durum: ana vektör indeksinde arsiv/ yok; disk ince arama ayrı."""
    root = _arsiv_root()
    man = _index_dir() / "manifest.json"
    vec_n = 0
    if man.is_file():
        try:
            fd = (json.loads(man.read_text(encoding="utf-8")).get("file_digests") or {})
            vec_n = sum(1 for k in fd if _source_is_archive(str(k)))
        except (OSError, json.JSONDecodeError, TypeError):
            vec_n = 0
    md_n = 0
    if root is not None:
        try:
            md_n = sum(1 for _ in root.rglob("*.md"))
        except OSError:
            md_n = 0
    return {
        "ok": True,
        "arsiv_root": str(root) if root else None,
        "vector_in_main_index": vec_n,
        "disk_md_approx": md_n,
        "disk_search_enabled": _arsiv_disk_search_enabled() and root is not None,
        "mode": "disk_keyword" if _arsiv_disk_search_enabled() else "off",
        "last_disk_meta": arsiv_disk_last_meta(),
        "hint": (
            "arsiv/ ana RAG indeksinde değil; sohbet md/txt disk aramasıyla bakar "
            "(Şamile/knowledge ayrı). Kapat: RUZGAR_ARSIV_DISK_SEARCH=0"
        ),
    }


def _arsiv_query_tokens(query: str) -> list[str]:
    try:
        from ilim_assistant.ruzgar_anlam_koruma import content_tokens

        toks = list(content_tokens(query, min_len=3))
        if toks:
            return toks[:12]
    except Exception:
        pass
    import re as _re

    raw = _re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9]{3,}", (query or "").lower())
    return raw[:12]


def search_arsiv_disk(query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """İnce yol: arsiv/ altı md/txt — gömme/full rebuild yok.

    Dosya listesi mtime önbellekli; tur deadline varsa erken keser (M4).
    """
    global _arsiv_disk_last_meta
    if not _arsiv_disk_search_enabled():
        _arsiv_disk_last_meta = {
            "scanned": 0,
            "cap": 0,
            "truncated": False,
            "deadline_hit": False,
            "cache_hit": False,
        }
        return []
    root = _arsiv_root()
    if root is None:
        return []
    toks = _arsiv_query_tokens(query)
    if not toks:
        return []
    tk = max(1, int(top_k))
    try:
        max_files = max(50, int(os.environ.get("RUZGAR_ARSIV_DISK_MAX_FILES", "600") or "600"))
    except ValueError:
        max_files = 600
    try:
        max_bytes = max(8_000, int(os.environ.get("RUZGAR_ARSIV_DISK_MAX_BYTES", "120000") or "120000"))
    except ValueError:
        max_bytes = 120_000

    files, cache_hit = _arsiv_list_searchable_files(root, max_files)
    remaining_fn = None
    try:
        from ilim_assistant.ruzgar_umed_cevap_emri import remaining_sec as _rem

        remaining_fn = _rem
    except Exception:
        remaining_fn = None

    scored: list[tuple[float, str, str]] = []
    seen = 0
    truncated = False
    deadline_hit = False
    for path in files:
        if remaining_fn is not None:
            try:
                if float(remaining_fn()) < 0.35:
                    deadline_hit = True
                    truncated = True
                    break
            except Exception:
                pass
        seen += 1
        if seen > max_files:
            truncated = True
            break
        rel = "arsiv/" + str(path.relative_to(root)).replace("\\", "/")
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
        except OSError:
            continue
        # Token'lar fold_ascii; ad/gövde de katlanmalı (ş→s) — aksi Türkçe isabet kaçıyor.
        try:
            from ilim_assistant.ruzgar_anlam_koruma import fold_ascii

            name_f = fold_ascii(path.name)
            body_f = fold_ascii(raw)
        except Exception:
            name_f = path.name.lower()
            body_f = raw.lower()
        hit_name = sum(1 for t in toks if t in name_f)
        hit_body = sum(1 for t in toks if t in body_f)
        if hit_name == 0 and hit_body == 0:
            continue
        cov = (hit_name * 2 + hit_body) / float(len(toks) * 3)
        score = min(0.82, 0.18 + 0.64 * cov)
        if hit_name:
            score = min(0.85, score + 0.08)
        # kısa pasaj
        snippet = raw.strip().replace("\r\n", "\n")
        if len(snippet) > 900:
            pos = -1
            for t in toks:
                pos = body_f.find(t)
                if pos >= 0:
                    break
            if pos < 0:
                pos = 0
            # fold boyutu ≈ ham boyuta yakın; ham dilimde kes
            start = max(0, min(pos - 120, max(0, len(snippet) - 900)))
            snippet = snippet[start : start + 900]
        scored.append((score, snippet, rel))

    if len(files) >= max_files:
        truncated = True
    _arsiv_disk_last_meta = {
        "scanned": seen,
        "cap": max_files,
        "truncated": truncated,
        "deadline_hit": deadline_hit,
        "cache_hit": cache_hit,
        "hits": len(scored),
    }
    scored.sort(key=lambda x: -x[0])
    return [(text, src, float(sc)) for sc, text, src in scored[:tk]]


def _arsiv_vector_count_cached() -> int:
    """Ana indekste arsiv/ satırı var mı — gömme yüklemeden."""
    man = _index_dir() / "manifest.json"
    if not man.is_file():
        return 0
    try:
        fd = json.loads(man.read_text(encoding="utf-8")).get("file_digests") or {}
        return sum(1 for k in fd if _source_is_archive(str(k)))
    except (OSError, json.JSONDecodeError, TypeError):
        return 0


def search_arsiv(query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """Arşiv araması: önce (nadiren) ana indeksteki arsiv/ satırları; yoksa disk ince yol.

    Not: `arsiv/` bilinçli olarak ana RAG gömmesine alınmaz (Şamile/knowledge ayrımı).
    """
    tk = max(1, top_k)
    # Ana indekste arsiv yoksa gömme modelini boşuna yükleme.
    if _arsiv_vector_count_cached() <= 0:
        return search_arsiv_disk(query, top_k=tk)
    pool = max(tk * 4, 16)
    try:
        wide = search(query, top_k=min(pool, 48))
        vec = [(t, s, sc) for t, s, sc in wide if _source_is_archive(s)]
        if vec:
            return vec[:tk]
    except Exception:
        pass
    return search_arsiv_disk(query, top_k=tk)


def _tarih_row_indices(chunks: List[Chunk]) -> np.ndarray:
    """TARIH_VE_KULTUR satırları — önbellekli indeksle aynı liste ise tek seferlik dizi."""
    global _cached_chunks_list, _tarih_chunk_row_indices
    if (
        _rag_cache_enabled()
        and _cached_chunks_list is not None
        and _tarih_chunk_row_indices is not None
        and chunks is _cached_chunks_list
    ):
        return _tarih_chunk_row_indices
    return np.array(
        [i for i, c in enumerate(chunks) if _source_is_tarih_hafiza(c.source)],
        dtype=np.int64,
    )


def search_tarih_hafiza(
    query: str, top_k: int = 5, scan_cap: int = 96
) -> List[Tuple[str, str, float]]:
    """
    Yalnızca `TARIH_VE_KULTUR/` kaynakları; gömme kosinüsü **yalnız bu alt küme** üzerinde
    (tüm indekste argsort + süzme yok — TTK/tarih havuzu için daha hızlı).
    """
    chunks, emb = _get_cached_index()
    if not chunks or emb is None or len(chunks) != len(emb):
        return []

    row_idx = _tarih_row_indices(chunks)
    if row_idx.size == 0:
        return []

    tk = max(1, top_k)
    try:
        cap = int(scan_cap)
    except ValueError:
        cap = 96
    cap = max(tk, min(cap, int(row_idx.size)))

    model = _get_embedder()
    q = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    sub = emb[row_idx]
    sim = sub @ q
    order = np.argsort(-sim)[:cap]

    out: List[Tuple[str, str, float]] = []
    for j in order:
        ji = int(j)
        gi = int(row_idx[ji])
        out.append((chunks[gi].text, chunks[gi].source, float(sim[ji])))
        if len(out) >= tk:
            break
    return out


def _subset_row_indices(
    chunks: List[Chunk],
    predicate,
    *,
    cache_attr: str,
) -> np.ndarray:
    global _cached_chunks_list, _tarih_chunk_row_indices, _tdk_chunk_row_indices, _nebula_chunk_row_indices
    cached = {
        "tarih": _tarih_chunk_row_indices,
        "tdk": _tdk_chunk_row_indices,
        "nebula": _nebula_chunk_row_indices,
    }.get(cache_attr)
    if (
        _rag_cache_enabled()
        and _cached_chunks_list is not None
        and cached is not None
        and chunks is _cached_chunks_list
    ):
        return cached
    return np.array([i for i, c in enumerate(chunks) if predicate(c.source)], dtype=np.int64)


def _search_source_subset(
    query: str,
    *,
    row_idx: np.ndarray,
    top_k: int,
    scan_cap: int,
    chunks: List[Chunk],
    emb: np.ndarray,
) -> List[Tuple[str, str, float]]:
    if row_idx.size == 0:
        return []
    tk = max(1, top_k)
    try:
        cap = int(scan_cap)
    except ValueError:
        cap = 96
    cap = max(tk, min(cap, int(row_idx.size)))
    model = _get_embedder()
    q = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    sub = emb[row_idx]
    sim = sub @ q
    order = np.argsort(-sim)[:cap]
    out: List[Tuple[str, str, float]] = []
    for j in order:
        ji = int(j)
        gi = int(row_idx[ji])
        out.append((chunks[gi].text, chunks[gi].source, float(sim[ji])))
        if len(out) >= tk:
            break
    return out


def search_tdk_hafiza(
    query: str, top_k: int = 5, scan_cap: int = 96
) -> List[Tuple[str, str, float]]:
    """Yalnızca `knowledge/tdk/...` kaynakları."""
    chunks, emb = _get_cached_index()
    if not chunks or emb is None or len(chunks) != len(emb):
        return []
    row_idx = _subset_row_indices(chunks, source_is_tdk, cache_attr="tdk")
    return _search_source_subset(
        query,
        row_idx=row_idx,
        top_k=top_k,
        scan_cap=scan_cap,
        chunks=chunks,
        emb=emb,
    )


def search_nebula_hafiza(
    query: str, top_k: int = 5, scan_cap: int = 96
) -> List[Tuple[str, str, float]]:
    """Yalnızca `knowledge/nebula/...` kaynakları."""
    chunks, emb = _get_cached_index()
    if not chunks or emb is None or len(chunks) != len(emb):
        return []
    row_idx = _subset_row_indices(chunks, source_is_nebula, cache_attr="nebula")
    return _search_source_subset(
        query,
        row_idx=row_idx,
        top_k=top_k,
        scan_cap=scan_cap,
        chunks=chunks,
        emb=emb,
    )
