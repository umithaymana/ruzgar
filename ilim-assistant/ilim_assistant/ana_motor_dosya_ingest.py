# Created by Ümit & Gökçenur
"""Ana Motor Faz F1 — tek tur dosya bağlamı (sürükle-bırak ingest, geçici RAG)."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_UPLOAD_ROOT = _PKG_ROOT / ".ruzgar" / "ana_motor_uploads"
_ALLOWED = {".txt", ".md", ".pdf"}
_MAX_BYTES = int(os.environ.get("RUZGAR_ANA_UPLOAD_MAX_BYTES", str(8 * 1024 * 1024)))
_TTL_SEC = int(os.environ.get("RUZGAR_ANA_UPLOAD_TTL_SEC", "7200"))
_MAX_SESSION_FILES = int(os.environ.get("RUZGAR_ANA_UPLOAD_SESSION_MAX", "6"))
_CHUNK = 900
_OVERLAP = 80

_lock = threading.Lock()
_store: dict[str, dict[str, Any]] = {}


def ingest_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_UPLOAD_INGEST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


@dataclass
class UploadRecord:
    upload_id: str
    filename: str
    chars: int
    chunks: int
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "upload_id": self.upload_id,
            "filename": self.filename,
            "chars": self.chars,
            "chunks": self.chunks,
        }


def _chunk_text(text: str, max_chars: int = _CHUNK, overlap: int = _OVERLAP) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    out: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        out.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [c for c in out if c]


def _extract_text(path: Path) -> tuple[str, str | None]:
    ext = path.suffix.lower()
    if ext in (".txt", ".md"):
        try:
            return path.read_text(encoding="utf-8", errors="replace").strip(), None
        except Exception as exc:
            return "", str(exc)
    if ext == ".pdf":
        try:
            from ilim_assistant.ilim_ve_idrak import read_pdf_text_basic

            txt = read_pdf_text_basic(path, max_pages=40)
            if not txt:
                return "", "PDF metin çıkarılamadı (taranmış sayfa olabilir)."
            return txt.strip(), None
        except Exception as exc:
            return "", str(exc)
    return "", "Desteklenmeyen uzantı."


def _purge_expired() -> None:
    now = time.time()
    dead = [k for k, v in _store.items() if now - float(v.get("created_at", 0)) > _TTL_SEC]
    for k in dead:
        _store.pop(k, None)
        meta = _UPLOAD_ROOT / f"{k}.json"
        if meta.is_file():
            try:
                meta.unlink()
            except OSError:
                pass


def _persist_record(upload_id: str, payload: dict[str, Any]) -> None:
    _UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    (_UPLOAD_ROOT / f"{upload_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def _load_disk_records() -> None:
    if not _UPLOAD_ROOT.is_dir():
        return
    for p in _UPLOAD_ROOT.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            uid = str(data.get("upload_id") or p.stem)
            if uid and uid not in _store:
                _store[uid] = data
        except Exception:
            continue


def session_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_UPLOAD_SESSION", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _session_path(session_id: str) -> Path:
    return _UPLOAD_ROOT / "sessions" / f"{session_id}.json"


def _load_session(session_id: str) -> dict[str, Any]:
    p = _session_path(session_id)
    if not p.is_file():
        return {"session_id": session_id, "upload_ids": [], "created_at": time.time()}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"session_id": session_id, "upload_ids": [], "created_at": time.time()}


def _save_session(session_id: str, payload: dict[str, Any]) -> None:
    (_UPLOAD_ROOT / "sessions").mkdir(parents=True, exist_ok=True)
    _session_path(session_id).write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def _register_upload_session_unlocked(
    session_id: str | None,
    upload_id: str,
) -> str | None:
    if not session_enabled():
        return session_id
    sid = (session_id or "").strip() or uuid.uuid4().hex[:12]
    data = _load_session(sid)
    ids = [str(x) for x in data.get("upload_ids") or []]
    if upload_id not in ids:
        if len(ids) >= _MAX_SESSION_FILES:
            raise ValueError(f"Oturumda en fazla {_MAX_SESSION_FILES} dosya.")
        ids.append(upload_id)
    data["upload_ids"] = ids
    data["updated_at"] = time.time()
    _save_session(sid, data)
    return sid


def register_upload_session(session_id: str | None, upload_id: str) -> str | None:
    """Yüklemeyi oturum paketine ekle; yeni session_id döndürür."""
    with _lock:
        return _register_upload_session_unlocked(session_id, upload_id)


def list_session_upload_ids(session_id: str | None) -> list[str]:
    sid = (session_id or "").strip()
    if not sid:
        return []
    with _lock:
        data = _load_session(sid)
    return [str(x) for x in data.get("upload_ids") or [] if str(x).strip()]


def get_upload_records(upload_ids: list[str] | None) -> list[dict[str, Any]]:
    if not upload_ids:
        return []
    with _lock:
        _purge_expired()
        if not _store:
            _load_disk_records()
        out: list[dict[str, Any]] = []
        for uid in upload_ids:
            rec = _store.get(str(uid).strip())
            if rec:
                out.append(rec)
        return out


def resolve_upload_ids(
    upload_ids: list[str] | None = None,
    session_id: str | None = None,
) -> list[str]:
    explicit = [str(x).strip() for x in (upload_ids or []) if str(x).strip()]
    if explicit:
        return explicit
    return list_session_upload_ids(session_id)


def save_upload_bytes(
    data: bytes,
    filename: str,
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Ham dosyayı kaydet, metin çıkar, göm ve upload_id döndür."""
    if not ingest_enabled():
        return {"ok": False, "error": "Dosya ingest kapalı (RUZGAR_ANA_MOTOR_UPLOAD_INGEST=0)."}
    if not data:
        return {"ok": False, "error": "Boş dosya."}
    if len(data) > _MAX_BYTES:
        return {"ok": False, "error": f"Dosya çok büyük (üst sınır {_MAX_BYTES // (1024 * 1024)} MB)."}

    name = (filename or "dosya.txt").replace("\\", "/").split("/")[-1]
    safe = re.sub(r"[^a-zA-Z0-9._\-ğüşıöçĞÜŞİÖÇ]+", "_", name).strip("._") or "dosya.txt"
    ext = Path(safe).suffix.lower()
    if ext not in _ALLOWED:
        return {"ok": False, "error": f"Desteklenen: {', '.join(sorted(_ALLOWED))}"}

    upload_id = uuid.uuid4().hex[:16]
    staging = _UPLOAD_ROOT / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    target = staging / f"{upload_id}_{safe}"
    target.write_bytes(data)

    text, err = _extract_text(target)
    try:
        target.unlink(missing_ok=True)
    except OSError:
        pass
    if err or not text:
        return {"ok": False, "error": err or "Metin çıkarılamadı."}

    chunks = _chunk_text(text)
    if not chunks:
        return {"ok": False, "error": "İçerik boş."}

    embeddings: list[list[float]] = []
    try:
        from ilim_assistant.rag_store import _get_embedder

        model = _get_embedder()
        emb = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        embeddings = [[float(v) for v in row] for row in emb]
    except Exception:
        embeddings = []

    record = {
        "upload_id": upload_id,
        "filename": safe,
        "chars": len(text),
        "chunks": len(chunks),
        "created_at": time.time(),
        "chunk_texts": chunks,
        "embeddings": embeddings,
        "source": f"upload:{safe}",
    }
    sid: str | None = None
    with _lock:
        _purge_expired()
        _store[upload_id] = record
        _persist_record(upload_id, record)
        try:
            sid = _register_upload_session_unlocked(session_id, upload_id)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

    out = UploadRecord(
        upload_id=upload_id,
        filename=safe,
        chars=len(text),
        chunks=len(chunks),
    ).to_dict()
    if sid:
        out["session_id"] = sid
        out["session_count"] = len(list_session_upload_ids(sid))
    return out


def search_upload_context(
    query: str,
    upload_ids: list[str] | None,
    *,
    session_id: str | None = None,
    top_k: int = 4,
) -> list[tuple[str, str, float]]:
    """Geçici yüklenen dosyalarda kosinüs araması."""
    if not ingest_enabled():
        return []
    ids = resolve_upload_ids(upload_ids, session_id)
    if not ids:
        return []

    with _lock:
        _purge_expired()
        if not _store:
            _load_disk_records()

    q = (query or "").strip()
    if not q:
        return []

    candidates: list[tuple[str, str, float]] = []
    try:
        from ilim_assistant.rag_store import _get_embedder
        import numpy as np

        model = _get_embedder()
        qv = model.encode([q], normalize_embeddings=True, show_progress_bar=False)[0]
    except Exception:
        qv = None

    for uid in ids:
        rec = _store.get(uid)
        if not rec:
            continue
        texts = list(rec.get("chunk_texts") or [])
        embs = rec.get("embeddings") or []
        src = str(rec.get("source") or f"upload:{uid}")
        if qv is not None and embs and len(embs) == len(texts):
            mat = np.array(embs, dtype=np.float32)
            sim = mat @ qv
            order = np.argsort(-sim)[: max(1, top_k)]
            for i in order:
                candidates.append((texts[int(i)], src, float(sim[int(i)])))
        else:
            low = q.lower()
            for t in texts:
                if low in t.lower() or any(w in t.lower() for w in low.split()[:6] if len(w) > 3):
                    candidates.append((t, src, 0.55))

    candidates.sort(key=lambda h: float(h[2]), reverse=True)
    return candidates[: max(1, top_k)]


def merge_upload_hits(
    hits: list[tuple[str, str, float]],
    query: str,
    upload_ids: list[str] | None,
    *,
    session_id: str | None = None,
    top_k: int = 4,
) -> list[tuple[str, str, float]]:
    up = search_upload_context(query, upload_ids, session_id=session_id, top_k=top_k)
    if not up:
        return hits
    boosted = [(t, s, min(1.0, float(sc) + 0.08)) for t, s, sc in up]
    seen: set[tuple[str, str]] = set()
    merged: list[tuple[str, str, float]] = []
    for h in boosted + list(hits or []):
        key = (h[1], (h[0] or "")[:160])
        if key in seen:
            continue
        seen.add(key)
        merged.append((h[0], h[1], float(h[2])))
    merged.sort(key=lambda h: float(h[2]), reverse=True)
    return merged
