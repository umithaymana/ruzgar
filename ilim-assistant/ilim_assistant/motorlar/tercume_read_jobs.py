# Created by Ümit & Gökçenur
"""Tercüme Faz 3 — arka planda tam kitap okuma + kalite raporu."""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

READ_JOB_VERSION = "tercume-read-job-v3-faz3-2026-05-31"

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
    d = _repo_root() / ".ruzgar" / "tercume_read_jobs"
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


def _run_read(job_id: str, rel: str) -> None:
    from ilim_assistant.motorlar.tercume_read_pipeline import extract_source_pages

    _update(job_id, status="running", label="Sayfalar okunuyor…")
    hit = extract_source_pages(rel)
    if not hit.get("ok"):
        _update(job_id, status="failed", error=str(hit.get("error") or "okuma hatası"))
        return

    pages = list(hit.get("pages") or [])
    meta = dict(hit.get("meta") or {})
    qs = meta.get("quality_summary") or {}

    report_rel = ""
    try:
        stem = Path(rel).stem[:60] or "kitap"
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in stem)
        report_rel = f"ilim-assistant/arsiv/tercume-output/read-reports/{safe}_quality.json"
        out_path = (_repo_root() / report_rel.replace("/", "\\")).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        slim_pages = [
            {
                "index": p.get("index"),
                "label": p.get("label"),
                "quality": p.get("quality"),
                "quality_score": p.get("quality_score"),
                "quality_hint": p.get("quality_hint"),
                "chars": len(str(p.get("text") or "")),
            }
            for p in pages
        ]
        out_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "rel": rel,
                    "meta": meta,
                    "pages": slim_pages,
                    "version": READ_JOB_VERSION,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        report_rel = ""

    _update(
        job_id,
        status="done",
        rel=rel,
        total=qs.get("total") or len(pages),
        empty_pages=qs.get("empty") or 0,
        low_pages=qs.get("low") or 0,
        ok_pages=qs.get("ok") or 0,
        ocr_recommended=bool(meta.get("quality_summary", {}).get("ocr_recommended")),
        read_hint=str(meta.get("read_hint") or ""),
        report_rel=report_rel,
        label="Okuma analizi bitti",
    )


def start_read_job(rel: str) -> dict[str, Any]:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        return {"ok": False, "error": "rel gerekli"}

    job_id = uuid.uuid4().hex[:12]
    state = {
        "ok": True,
        "job_id": job_id,
        "version": READ_JOB_VERSION,
        "status": "queued",
        "rel": raw,
        "created_at": time.time(),
    }
    with _lock:
        _jobs[job_id] = state
    _persist(job_id, state)

    th = threading.Thread(target=_run_read, args=(job_id, raw), daemon=True)
    th.start()
    return {"ok": True, "job_id": job_id, "rel": raw}


def get_read_job(job_id: str) -> dict[str, Any]:
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


def cancel_read_job(job_id: str) -> dict[str, Any]:
    jid = (job_id or "").strip()
    with _lock:
        if jid in _jobs:
            _jobs[jid]["cancel"] = True
            _update(jid, status="cancelled")
            return {"ok": True, "job_id": jid}
    return {"ok": False, "error": "İş bulunamadı"}
