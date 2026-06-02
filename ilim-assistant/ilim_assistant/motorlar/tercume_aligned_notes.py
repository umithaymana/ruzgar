# Created by Umit & Gokcenur
"""CAT-lite satir notlari: dosya bazli kalici saklama."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

ALIGNED_NOTES_VERSION = "tercume-aligned-notes-v17-2026-06-02"
_LOCK = threading.Lock()
_MAX_NOTES = 600
_MAX_NOTE_LEN = 260


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def _notes_dir() -> Path:
    d = _repo_root() / ".ruzgar" / "tercume_aligned_notes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def _notes_path(rel: str) -> Path:
    key = _norm_rel(rel)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]
    return _notes_dir() / f"aligned_{digest}.json"


def load_notes(rel: str) -> dict[str, Any]:
    key = _norm_rel(rel)
    if not key:
        return {"ok": False, "error": "rel gerekli"}
    path = _notes_path(key)
    if not path.is_file():
        return {"ok": True, "rel": key, "notes": {}, "version": ALIGNED_NOTES_VERSION}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    notes = data.get("notes") if isinstance(data, dict) else {}
    if not isinstance(notes, dict):
        notes = {}
    clean: dict[str, str] = {}
    for k, v in notes.items():
        if len(clean) >= _MAX_NOTES:
            break
        kk = str(k or "").strip()[:80]
        vv = str(v or "").strip()[:_MAX_NOTE_LEN]
        if kk and vv:
            clean[kk] = vv
    return {
        "ok": True,
        "rel": key,
        "notes": clean,
        "count": len(clean),
        "version": ALIGNED_NOTES_VERSION,
    }


def save_notes(rel: str, notes: dict[str, Any]) -> dict[str, Any]:
    key = _norm_rel(rel)
    if not key:
        return {"ok": False, "error": "rel gerekli"}
    if not isinstance(notes, dict):
        return {"ok": False, "error": "notes sözlük olmalı"}
    clean: dict[str, str] = {}
    for k, v in notes.items():
        if len(clean) >= _MAX_NOTES:
            break
        kk = str(k or "").strip()[:80]
        vv = str(v or "").strip()[:_MAX_NOTE_LEN]
        if kk and vv:
            clean[kk] = vv
    payload = {
        "rel": key,
        "notes": clean,
        "updated_at": time.time(),
        "version": ALIGNED_NOTES_VERSION,
    }
    path = _notes_path(key)
    with _LOCK:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    return {
        "ok": True,
        "rel": key,
        "count": len(clean),
        "version": ALIGNED_NOTES_VERSION,
    }
