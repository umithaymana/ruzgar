# Created by Ümit & Gökçenur
"""Tercüme — çok cilt / çok dosya arka plan işi (sırayla çevir + kaydet)."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

BATCH_VERSION = "tercume-batch-v1-2026-05-31"

_jobs: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def _jobs_dir() -> Path:
    d = _repo_root() / ".ruzgar" / "tercume_jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _persist(job_id: str, state: dict[str, Any]) -> None:
    path = _jobs_dir() / f"{job_id}.json"
    try:
        path.write_text(json.dumps(state, ensure_ascii=False, indent=0), encoding="utf-8")
    except OSError:
        pass


def _update(job_id: str, **fields: Any) -> None:
    with _lock:
        st = _jobs.get(job_id) or {}
        st.update(fields)
        st["updated_at"] = time.time()
        _jobs[job_id] = st
    _persist(job_id, _jobs[job_id])


def list_book_files(folder_rel: str) -> list[str]:
    from ilim_assistant.motorlar.tercume_atolye import BOOK_EXTENSIONS

    root = _repo_root()
    rel = (folder_rel or "").strip().replace("\\", "/").lstrip("/")
    if not rel.startswith("ilim-assistant/"):
        rel = f"ilim-assistant/arsiv/{rel.lstrip('/')}"
    folder = (root / rel.replace("/", os.sep)).resolve()
    if not folder.is_dir():
        return []
    allowed = {e.lower() for e in BOOK_EXTENSIONS}
    out: list[str] = []
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in allowed:
            continue
        if "tercume-output" in p.as_posix().lower():
            continue
        try:
            out.append(p.relative_to(root.resolve()).as_posix())
        except ValueError:
            continue
    return out


def _read_file_text(rel: str) -> str:
    from ilim_assistant.motorlar.tercume_atolye import extract_book_full_text

    hit = extract_book_full_text(rel)
    if not hit.get("ok"):
        return ""
    return str(hit.get("text") or "")


def _translate_full_text(
    text: str,
    *,
    rel: str,
    src_lang: str,
    tgt_lang: str,
) -> str:
    from ilim_assistant.motorlar.tercume_atolye import split_text_into_pages, translate_chunk

    pages = split_text_into_pages(text, max_chars=2800)
    parts: list[str] = []
    for p in pages:
        tr = translate_chunk(
            str(p.get("text") or ""),
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            source_file=rel,
            page_index=int(p.get("index") or 0),
        )
        if tr.get("ok"):
            parts.append(str(tr.get("text") or ""))
        else:
            parts.append(f"[HATA: {tr.get('error', '?')}]")
    return "\n\n".join(parts)


def _run_batch(job_id: str, cfg: dict[str, Any]) -> None:
    files = list(cfg.get("files") or [])
    tgt = str(cfg.get("tgt_lang") or "tr")
    src = str(cfg.get("src_lang") or "auto")
    out_dir_rel = str(cfg.get("output_dir_rel") or "ilim-assistant/arsiv/tercume-output/batch")
    root = _repo_root()
    out_dir = (root / out_dir_rel.replace("/", os.sep)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    _update(job_id, status="running", current_file="", done=0, total=len(files), outputs=[])

    outputs: list[dict[str, Any]] = []
    for i, rel in enumerate(files):
        with _lock:
            if (_jobs.get(job_id) or {}).get("cancel"):
                _update(job_id, status="cancelled", outputs=outputs)
                return

        _update(job_id, current_file=rel, done=i, label=f"{i + 1}/{len(files)}: {Path(rel).name}")

        try:
            text = _read_file_text(rel)
            if not text.strip():
                outputs.append({"rel": rel, "ok": False, "error": "Metin okunamadı"})
                continue
            translated = _translate_full_text(text, rel=rel, src_lang=src, tgt_lang=tgt)
            stem = Path(rel).stem
            safe = re.sub(r"[^a-zA-Z0-9._\-]+", "_", stem)[:80] or "cilt"
            out_rel = f"{out_dir_rel.rstrip('/')}/{safe}_{tgt}.txt"
            out_path = (root / out_rel.replace("/", os.sep)).resolve()
            out_path.write_text(translated, encoding="utf-8")
            outputs.append({"rel": rel, "ok": True, "output_rel": out_rel, "chars": len(translated)})
        except Exception as exc:
            outputs.append({"rel": rel, "ok": False, "error": str(exc)[:200]})

        _update(job_id, done=i + 1, outputs=outputs)

    _update(job_id, status="done", current_file="", outputs=outputs)


def start_batch_job(
    folder_rel: str,
    *,
    tgt_lang: str = "tr",
    src_lang: str = "auto",
    output_dir_rel: str = "ilim-assistant/arsiv/tercume-output/batch",
    file_filter: str = "",
) -> dict[str, Any]:
    files = list_book_files(folder_rel)
    if file_filter:
        fl = file_filter.lower()
        files = [f for f in files if fl in f.lower()]
    if not files:
        return {"ok": False, "error": "Klasörde çevrilecek kitap dosyası yok (pdf/txt/epub…)."}

    job_id = uuid.uuid4().hex[:12]
    cfg = {
        "folder_rel": folder_rel,
        "files": files,
        "tgt_lang": tgt_lang,
        "src_lang": src_lang,
        "output_dir_rel": output_dir_rel,
    }
    state = {
        "ok": True,
        "job_id": job_id,
        "version": BATCH_VERSION,
        "status": "queued",
        "total": len(files),
        "done": 0,
        "files": files,
        "tgt_lang": tgt_lang,
        "created_at": time.time(),
    }
    with _lock:
        _jobs[job_id] = state
    _persist(job_id, state)

    th = threading.Thread(target=_run_batch, args=(job_id, cfg), daemon=True)
    th.start()
    return {"ok": True, "job_id": job_id, "total": len(files), "files": files}


def get_batch_job(job_id: str) -> dict[str, Any]:
    jid = (job_id or "").strip()
    if not jid:
        return {"ok": False, "error": "job_id gerekli"}
    with _lock:
        st = _jobs.get(jid)
    if st:
        return {"ok": True, **st}
    path = _jobs_dir() / f"{jid}.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {"ok": True, **data}
        except Exception:
            pass
    return {"ok": False, "error": "İş bulunamadı"}


def cancel_batch_job(job_id: str) -> dict[str, Any]:
    jid = (job_id or "").strip()
    with _lock:
        if jid in _jobs:
            _jobs[jid]["cancel"] = True
            _update(jid, cancel=True)
            return {"ok": True, "job_id": jid, "status": "cancelling"}
    return {"ok": False, "error": "İş bulunamadı"}
