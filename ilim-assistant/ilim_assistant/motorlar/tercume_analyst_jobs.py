# Created by Ümit & Gökçenur
"""Tercüme Faz 5 — analist pipeline arka plan işleri (indirme kuyruğu)."""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

ANALYST_JOB_VERSION = "tercume-analyst-job-v5-faz5-2026-05-31"

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
    d = _repo_root() / ".ruzgar" / "tercume_analyst_jobs"
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


def _cancelled(job_id: str) -> bool:
    with _lock:
        return bool((_jobs.get(job_id) or {}).get("cancel"))


def _run_pipeline(job_id: str, cfg: dict[str, Any]) -> None:
    from ilim_assistant.motorlar.tercume_analyst import run_tercume_pipeline

    query = str(cfg.get("query") or "").strip()
    _update(job_id, status="running", step="analyze", label="Kaynak analizi…")
    if _cancelled(job_id):
        _update(job_id, status="cancelled", label="İptal edildi")
        return

    try:
        result = run_tercume_pipeline(
            query,
            download=bool(cfg.get("download")),
            download_url=str(cfg.get("download_url") or ""),
            target_dir_rel=str(
                cfg.get("target_dir_rel") or "ilim-assistant/arsiv/tercume-imports"
            ),
            read_preview_pages=int(cfg.get("read_preview_pages") or 0),
            translate=bool(cfg.get("translate")),
            src_lang=str(cfg.get("src_lang") or "auto"),
            tgt_lang=str(cfg.get("tgt_lang") or "tr"),
            workspace_root=cfg.get("workspace_root"),
        )
    except Exception as exc:
        _update(job_id, status="failed", error=str(exc)[:240], label="Hata")
        return

    if _cancelled(job_id):
        _update(job_id, status="cancelled", label="İptal edildi")
        return

    rel = ""
    dl = result.get("download") or {}
    if isinstance(dl, dict) and dl.get("ok"):
        rel = str(dl.get("rel") or "")
    steps = list(result.get("steps") or [])
    last_step = steps[-1].get("step") if steps else "done"

    if not result.get("ok"):
        _update(
            job_id,
            status="failed",
            error=str(result.get("error") or "pipeline hatası"),
            result=result,
            rel=rel,
            step=last_step,
            label="Başarısız",
        )
        return

    _update(
        job_id,
        status="done",
        result=result,
        rel=rel,
        step=last_step,
        label="Arşive alındı" if rel else "Bitti",
        download_url=str(cfg.get("download_url") or ""),
    )


def _run_report(job_id: str, cfg: dict[str, Any]) -> None:
    from ilim_assistant.motorlar.tercume_analyst import analyze_tercume_query, prepare_import_from_search
    from ilim_assistant.motorlar.tercume_analyst_report import generate_analyst_report, save_report_file

    query = str(cfg.get("query") or "").strip()
    rel = str(cfg.get("rel") or "").strip()
    read_pages = int(cfg.get("read_pages") or 5)

    _update(job_id, status="running", step="analyze", label="Analiz raporu…")
    if _cancelled(job_id):
        _update(job_id, status="cancelled", label="İptal edildi")
        return

    if not rel and cfg.get("auto_import"):
        plan = prepare_import_from_search(query=query, download_url=str(cfg.get("download_url") or ""))
        if plan.get("mode") == "local":
            rel = str(plan.get("rel") or "")
        elif plan.get("mode") == "download" and plan.get("download_url"):
            _update(job_id, step="download", label="Kaynak indiriliyor…")
            from ilim_assistant.motorlar.tercume_analyst import run_tercume_pipeline

            pipe = run_tercume_pipeline(
                query,
                download=True,
                download_url=str(plan.get("download_url") or ""),
                target_dir_rel=str(cfg.get("target_dir_rel") or "ilim-assistant/arsiv/tercume-imports"),
            )
            dl = pipe.get("download") or {}
            if isinstance(dl, dict) and dl.get("ok"):
                rel = str(dl.get("rel") or "")

    if _cancelled(job_id):
        _update(job_id, status="cancelled", label="İptal edildi")
        return

    _update(job_id, step="report", label="Rapor oluşturuluyor…")
    report = generate_analyst_report(query, rel=rel, read_pages=read_pages)
    if not report.get("ok"):
        _update(job_id, status="failed", error=str(report.get("error") or "rapor hatası"), label="Başarısız")
        return

    saved = save_report_file(report)
    _update(
        job_id,
        status="done",
        step="done",
        label="Rapor hazır",
        rel=report.get("rel") or rel,
        report_rel=saved.get("report_rel"),
        report_json_rel=saved.get("report_json_rel"),
        quality=report.get("quality"),
        next_steps=report.get("next_steps"),
        markdown_preview=str(report.get("markdown") or "")[:1200],
        result={"report": report, "saved": saved},
    )


def start_report_job(
    *,
    query: str = "",
    rel: str = "",
    read_pages: int = 5,
    auto_import: bool = False,
    download_url: str = "",
    target_dir_rel: str = "ilim-assistant/arsiv/tercume-imports",
) -> dict[str, Any]:
    q = (query or "").strip()
    if not q and not (rel or "").strip():
        return {"ok": False, "error": "query veya rel gerekli"}

    job_id = uuid.uuid4().hex[:12]
    cfg = {
        "query": q or Path(rel).stem,
        "rel": (rel or "").strip(),
        "read_pages": max(1, min(25, int(read_pages or 5))),
        "auto_import": bool(auto_import),
        "download_url": (download_url or "").strip(),
        "target_dir_rel": (target_dir_rel or "ilim-assistant/arsiv/tercume-imports").strip(),
    }
    state = {
        "ok": True,
        "job_id": job_id,
        "job_type": "analyst_report",
        "version": ANALYST_JOB_VERSION,
        "status": "queued",
        "step": "queued",
        "label": "Rapor kuyruğunda…",
        "query": cfg["query"],
        "rel": cfg["rel"],
        "created_at": time.time(),
    }
    with _lock:
        _jobs[job_id] = state
    _persist(job_id, state)

    th = threading.Thread(target=_run_report, args=(job_id, cfg), daemon=True)
    th.start()
    return {"ok": True, "job_id": job_id, "job_type": "analyst_report", "status": "queued"}


def start_analyst_job(
    *,
    query: str = "",
    download: bool = True,
    download_url: str = "",
    target_dir_rel: str = "ilim-assistant/arsiv/tercume-imports",
    read_preview_pages: int = 0,
    translate: bool = False,
    src_lang: str = "auto",
    tgt_lang: str = "tr",
    workspace_root: str | None = None,
    title: str = "",
) -> dict[str, Any]:
    q = (query or "").strip()
    url = (download_url or "").strip()
    if not q and not url:
        return {"ok": False, "error": "query veya download_url gerekli"}

    job_id = uuid.uuid4().hex[:12]
    cfg = {
        "query": q or (title or "import"),
        "download": download,
        "download_url": url,
        "target_dir_rel": (target_dir_rel or "ilim-assistant/arsiv/tercume-imports").strip(),
        "read_preview_pages": max(0, min(25, int(read_preview_pages or 0))),
        "translate": translate,
        "src_lang": (src_lang or "auto").strip(),
        "tgt_lang": (tgt_lang or "tr").strip(),
        "workspace_root": workspace_root,
        "title": (title or "").strip(),
    }
    state = {
        "ok": True,
        "job_id": job_id,
        "job_type": "analyst_pipeline",
        "version": ANALYST_JOB_VERSION,
        "status": "queued",
        "step": "queued",
        "label": "Kuyrukta…",
        "query": cfg["query"],
        "download_url": url,
        "title": cfg["title"],
        "created_at": time.time(),
    }
    with _lock:
        _jobs[job_id] = state
    _persist(job_id, state)

    th = threading.Thread(target=_run_pipeline, args=(job_id, cfg), daemon=True)
    th.start()
    return {"ok": True, "job_id": job_id, "job_type": "analyst_pipeline", "status": "queued"}


def get_analyst_job(job_id: str) -> dict[str, Any]:
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


def cancel_analyst_job(job_id: str) -> dict[str, Any]:
    jid = (job_id or "").strip()
    if not jid:
        return {"ok": False, "error": "job_id gerekli"}
    with _lock:
        if jid in _jobs:
            _jobs[jid]["cancel"] = True
    _update(jid, status="cancelling", label="İptal ediliyor…")
    return {"ok": True, "job_id": jid, "status": "cancelling"}


def resolve_tercume_job(job_id: str) -> dict[str, Any]:
    """Faz 5 — analyst / read / batch işlerini tek uçtan çöz."""
    jid = (job_id or "").strip()
    if not jid:
        return {"ok": False, "error": "job_id gerekli"}

    hit = get_analyst_job(jid)
    if hit.get("ok"):
        hit.setdefault("job_type", hit.get("job_type") or "analyst_pipeline")
        return hit

    from ilim_assistant.motorlar.tercume_read_jobs import get_read_job

    hit = get_read_job(jid)
    if hit.get("ok"):
        hit.setdefault("job_type", "read")
        return hit

    from ilim_assistant.motorlar.tercume_batch_jobs import get_batch_job

    hit = get_batch_job(jid)
    if hit.get("ok"):
        hit.setdefault("job_type", "batch")
        return hit

    return {"ok": False, "error": "İş bulunamadı"}
