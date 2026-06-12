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


def _allowed_extensions() -> set[str]:
    ext = set(_ALLOWED)
    try:
        from ilim_assistant.ana_motor_gorsel_sohbet import image_extensions_enabled

        ext |= set(image_extensions_enabled())
    except Exception:
        pass
    return ext
_MAX_BYTES = int(os.environ.get("RUZGAR_ANA_UPLOAD_MAX_BYTES", str(8 * 1024 * 1024)))
_TTL_SEC = int(os.environ.get("RUZGAR_ANA_UPLOAD_TTL_SEC", "7200"))
_TTL_EXTEND_SEC = int(os.environ.get("RUZGAR_ANA_UPLOAD_TTL_EXTEND_SEC", "86400"))
_MAX_SESSION_FILES = int(os.environ.get("RUZGAR_ANA_UPLOAD_SESSION_MAX", "6"))
_ARCHIVE_ROOT = _PKG_ROOT / "arsiv" / "ana_motor_uploads"
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


def upload_virus_scan_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_UPLOAD_VIRUS_SCAN", "1").strip().lower() not in (
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


def _record_expired(rec: dict[str, Any], now: float) -> bool:
    exp = rec.get("expires_at")
    if exp is not None:
        try:
            return now > float(exp)
        except (TypeError, ValueError):
            pass
    try:
        created = float(rec.get("created_at", 0))
    except (TypeError, ValueError):
        created = 0.0
    return now - created > _TTL_SEC


def _purge_expired() -> None:
    now = time.time()
    dead = [k for k, v in _store.items() if _record_expired(v, now)]
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


def archive_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_UPLOAD_ARCHIVE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def ttl_extend_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_UPLOAD_TTL_EXTEND", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def extend_session_ttl(
    session_id: str | None = None,
    *,
    upload_ids: list[str] | None = None,
    extra_sec: int | None = None,
) -> dict[str, Any]:
    """Faz I2 — oturum dosyalarının silinme süresini uzat."""
    if not ttl_extend_enabled():
        return {"ok": False, "error": "TTL uzatma kapalı."}
    sid = (session_id or "").strip()
    ids = resolve_upload_ids(upload_ids, sid or None)
    if not ids:
        return {"ok": False, "error": "Uzatılacak dosya yok."}
    add = int(extra_sec if extra_sec is not None else _TTL_EXTEND_SEC)
    until = time.time() + max(300, add)
    with _lock:
        _purge_expired()
        if not _store:
            _load_disk_records()
        touched = 0
        for uid in ids:
            rec = _store.get(uid)
            if not rec:
                continue
            rec["expires_at"] = until
            _store[uid] = rec
            _persist_record(uid, rec)
            touched += 1
        if sid:
            data = _load_session(sid)
            data["expires_at"] = until
            data["ttl_extended_at"] = time.time()
            _save_session(sid, data)
    if touched == 0:
        return {"ok": False, "error": "Kayıtlar bulunamadı (süre dolmuş olabilir)."}
    return {
        "ok": True,
        "extended_until": until,
        "files": touched,
        "extra_sec": add,
    }


def archive_session_package(
    session_id: str | None = None,
    *,
    upload_ids: list[str] | None = None,
    topic: str = "",
) -> dict[str, Any]:
    """Faz I2 — oturumu `arsiv/ana_motor_uploads/` altına kalıcı kopyala."""
    if not archive_enabled():
        return {"ok": False, "error": "Oturum arşivi kapalı."}
    ids = resolve_upload_ids(upload_ids, session_id)
    sid = (session_id or "").strip() or uuid.uuid4().hex[:12]
    records = get_upload_records(ids)
    if not records:
        return {"ok": False, "error": "Arşivlenecek dosya yok."}

    dest = _ARCHIVE_ROOT / sid
    dest.mkdir(parents=True, exist_ok=True)
    files_dir = dest / "uploads"
    files_dir.mkdir(parents=True, exist_ok=True)

    manifest_files: list[dict[str, Any]] = []
    combined_parts: list[str] = [
        f"# Ana Motor oturum arşivi — {sid}\n",
        f"- Konu: {(topic or '').strip()[:200] or '—'}\n",
        f"- Dosya: {len(records)}\n\n",
    ]
    for rec in records:
        uid = str(rec.get("upload_id") or "")
        fname = str(rec.get("filename") or "dosya")
        src_json = _UPLOAD_ROOT / f"{uid}.json"
        if src_json.is_file():
            import shutil

            shutil.copy2(src_json, files_dir / f"{uid}.json")
        manifest_files.append(
            {
                "upload_id": uid,
                "filename": fname,
                "chars": rec.get("chars"),
                "chunks": rec.get("chunks"),
            }
        )
        body = "\n\n".join(rec.get("chunk_texts") or []).strip()
        combined_parts.append(f"## {fname}\n\n{body}\n\n")

    manifest = {
        "session_id": sid,
        "topic": (topic or "").strip()[:200],
        "archived_at": time.time(),
        "files": manifest_files,
    }
    (dest / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    combined = "".join(combined_parts)
    if len(combined) > 500_000:
        combined = combined[:499_000].rstrip() + "\n\n…\n"
    (dest / "oturum_birlesik.md").write_text(combined, encoding="utf-8")

    rel = f"arsiv/ana_motor_uploads/{sid}"
    return {
        "ok": True,
        "session_id": sid,
        "archive_path": rel,
        "file_count": len(records),
        "hint": f"Kalıcı kopya: `ilim-assistant/{rel}/`",
    }


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
    allowed = _allowed_extensions()
    if ext not in allowed:
        return {"ok": False, "error": f"Desteklenen: {', '.join(sorted(allowed))}"}

    upload_id = uuid.uuid4().hex[:16]
    staging = _UPLOAD_ROOT / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    target = staging / f"{upload_id}_{safe}"
    target.write_bytes(data)

    if upload_virus_scan_enabled():
        try:
            from ilim_assistant.motorlar.ruzgar_antivirus import ruzgar_scan_file

            verdict = ruzgar_scan_file(target, mode="quick")
            if not verdict.clean:
                try:
                    target.unlink(missing_ok=True)
                except OSError:
                    pass
                threats = ", ".join(verdict.threats[:3]) or verdict.detail or "risk"
                return {
                    "ok": False,
                    "error": f"Virüs kalkanı: dosya reddedildi ({threats}).",
                    "scan": verdict.to_dict(),
                }
        except Exception:
            pass

    try:
        from ilim_assistant.ana_motor_gorsel_sohbet import image_extensions_enabled

        if ext in image_extensions_enabled():
            img_dir = _UPLOAD_ROOT / "images"
            img_dir.mkdir(parents=True, exist_ok=True)
            final = img_dir / f"{upload_id}_{safe}"
            try:
                target.replace(final)
            except OSError:
                final.write_bytes(data)
                target.unlink(missing_ok=True)
            rel = final.relative_to(_PKG_ROOT).as_posix()
            record = {
                "upload_id": upload_id,
                "filename": safe,
                "chars": 0,
                "chunks": 0,
                "chunk_texts": [],
                "stored_rel": rel,
                "is_image": True,
                "expires_at": time.time() + _TTL_SEC,
            }
            with _lock:
                _store[upload_id] = record
                _persist_record(upload_id, record)
            if session_id:
                _register_upload_session_unlocked(session_id, upload_id)
            return {
                "ok": True,
                "upload_id": upload_id,
                "filename": safe,
                "chars": 0,
                "is_image": True,
                "session_id": session_id,
            }
    except Exception:
        pass

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


def archive_restore_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_ARCHIVE_RESTORE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def session_merge_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_SESSION_MERGE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def list_archived_sessions(*, limit: int = 30) -> list[dict[str, Any]]:
    """Faz J2 — kalıcı arşivdeki oturumları listele."""
    if not _ARCHIVE_ROOT.is_dir():
        return []
    rows: list[tuple[float, dict[str, Any]]] = []
    for d in _ARCHIVE_ROOT.iterdir():
        if not d.is_dir():
            continue
        mf = d / "manifest.json"
        if not mf.is_file():
            continue
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            archived_at = float(m.get("archived_at") or d.stat().st_mtime)
            rows.append(
                (
                    archived_at,
                    {
                        "session_id": d.name,
                        "topic": (m.get("topic") or "").strip()[:200],
                        "file_count": len(m.get("files") or []),
                        "archived_at": archived_at,
                        "archive_path": f"arsiv/ana_motor_uploads/{d.name}",
                    },
                )
            )
        except Exception:
            continue
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in rows[: max(1, limit)]]


def restore_archive_session(session_id: str) -> dict[str, Any]:
    """Faz J2 — arşivden geçici upload RAG kayıtlarını geri yükle."""
    if not archive_restore_enabled():
        return {"ok": False, "error": "Arşiv geri yükleme kapalı."}
    sid = (session_id or "").strip()
    if not sid:
        return {"ok": False, "error": "session_id gerekli."}
    dest = _ARCHIVE_ROOT / sid
    manifest_path = dest / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "error": f"Arşiv bulunamadı: {sid}"}

    uploads_dir = dest / "uploads"
    restored: list[str] = []
    until = time.time() + max(300, _TTL_EXTEND_SEC)
    with _lock:
        _purge_expired()
        if not _store:
            _load_disk_records()
        if uploads_dir.is_dir():
            for p in sorted(uploads_dir.glob("*.json")):
                try:
                    rec = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                uid = str(rec.get("upload_id") or p.stem).strip()
                if not uid:
                    continue
                rec["expires_at"] = until
                rec["restored_from_archive"] = sid
                _store[uid] = rec
                _persist_record(uid, rec)
                restored.append(uid)
        if not restored:
            combined = dest / "oturum_birlesik.md"
            if combined.is_file():
                text = combined.read_text(encoding="utf-8", errors="replace").strip()
                chunks = _chunk_text(text)
                if chunks:
                    uid = uuid.uuid4().hex[:16]
                    rec = {
                        "upload_id": uid,
                        "filename": "oturum_birlesik.md",
                        "chars": len(text),
                        "chunks": len(chunks),
                        "created_at": time.time(),
                        "expires_at": until,
                        "chunk_texts": chunks,
                        "embeddings": [],
                        "source": f"archive:{sid}",
                        "restored_from_archive": sid,
                    }
                    _store[uid] = rec
                    _persist_record(uid, rec)
                    restored.append(uid)
        if not restored:
            return {"ok": False, "error": "Arşivde geri yüklenecek içerik yok."}
        data = _load_session(sid)
        data["upload_ids"] = restored
        data["restored_at"] = time.time()
        data["expires_at"] = until
        _save_session(sid, data)

    return {
        "ok": True,
        "session_id": sid,
        "upload_ids": restored,
        "file_count": len(restored),
        "hint": f"Arşivden {len(restored)} dosya RAG bağlamına geri yüklendi.",
    }


def merge_upload_sessions(
    session_ids: list[str],
    *,
    target_session_id: str | None = None,
    restore_missing: bool = True,
) -> dict[str, Any]:
    """Faz J3 — birden fazla oturumdaki dosyaları tek pakette birleştir."""
    if not session_merge_enabled():
        return {"ok": False, "error": "Oturum birleştirme kapalı."}
    if not session_enabled():
        return {"ok": False, "error": "Upload oturumu kapalı."}
    sids = [str(s).strip() for s in (session_ids or []) if str(s).strip()]
    if len(sids) < 2:
        return {"ok": False, "error": "En az 2 oturum kimliği gerekli."}

    all_ids: list[str] = []
    for sid in sids:
        ids = list_session_upload_ids(sid)
        if not ids and restore_missing and archive_restore_enabled():
            rr = restore_archive_session(sid)
            if rr.get("ok"):
                ids = list(rr.get("upload_ids") or [])
        all_ids.extend(ids)

    seen: set[str] = set()
    unique: list[str] = []
    for uid in all_ids:
        if uid in seen:
            continue
        seen.add(uid)
        unique.append(uid)
    if not unique:
        return {"ok": False, "error": "Birleştirilecek dosya bulunamadı."}
    if len(unique) > _MAX_SESSION_FILES:
        return {
            "ok": False,
            "error": f"Birleşik oturum en fazla {_MAX_SESSION_FILES} dosya (şu an {len(unique)}).",
        }

    target = (target_session_id or "").strip() or uuid.uuid4().hex[:12]
    with _lock:
        payload = {
            "session_id": target,
            "upload_ids": unique,
            "merged_from": sids,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        _save_session(target, payload)
    out: dict[str, Any] = {
        "ok": True,
        "session_id": target,
        "upload_ids": unique,
        "merged_from": sids,
        "file_count": len(unique),
        "hint": f"{len(sids)} oturum → {len(unique)} dosya birleştirildi.",
    }
    try:
        from ilim_assistant.ana_motor_nebula_oneri import build_session_nebula_card

        nb = build_session_nebula_card(session_id=target, upload_ids=unique)
        if nb:
            out["nebula_card"] = nb
    except Exception:
        pass
    return out
