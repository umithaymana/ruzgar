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

BATCH_VERSION = "tercume-batch-v3-faz14a-2026-05-29"
_PARTIAL_TEXT_MAX = 420_000

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


def _load_job_into_memory(jid: str) -> dict[str, Any] | None:
    path = _jobs_dir() / f"{jid}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict):
        with _lock:
            _jobs[jid] = data
        return data
    return None


def get_batch_job(job_id: str) -> dict[str, Any]:
    jid = (job_id or "").strip()
    if not jid:
        return {"ok": False, "error": "job_id gerekli"}
    with _lock:
        st = _jobs.get(jid)
    if st:
        return {"ok": True, **st}
    data = _load_job_into_memory(jid)
    if data:
        return {"ok": True, **data}
    return {"ok": False, "error": "İş bulunamadı"}


def list_batch_jobs(*, limit: int = 20) -> dict[str, Any]:
    lim = max(1, min(50, int(limit)))
    items: list[dict[str, Any]] = []
    d = _jobs_dir()
    paths = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths[: lim * 2]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        jid = str(data.get("job_id") or path.stem)
        items.append(
            {
                "job_id": jid,
                "job_type": data.get("job_type") or "batch",
                "status": data.get("status") or "unknown",
                "rel": data.get("rel") or data.get("current_file") or "",
                "done": data.get("done"),
                "total": data.get("total"),
                "label": data.get("label") or "",
                "output_rel": data.get("output_rel") or "",
                "updated_at": data.get("updated_at") or data.get("created_at"),
                "created_at": data.get("created_at"),
            }
        )
        if len(items) >= lim:
            break
    return {"ok": True, "items": items, "version": BATCH_VERSION, "limit": lim}


def cancel_batch_job(job_id: str) -> dict[str, Any]:
    jid = (job_id or "").strip()
    if not jid:
        return {"ok": False, "error": "job_id gerekli"}
    with _lock:
        st = _jobs.get(jid)
    if not st:
        st = _load_job_into_memory(jid)
    if not st:
        return {"ok": False, "error": "İş bulunamadı"}
    if st.get("status") in ("done", "failed", "cancelled"):
        return {"ok": True, "job_id": jid, "status": st.get("status"), "already_finished": True}
    _update(jid, cancel=True, status="cancelling", label="İptal istendi…")
    return {"ok": True, "job_id": jid, "status": "cancelling"}


def _filter_pages(
    pages: list[dict[str, Any]],
    *,
    skip_empty: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in pages:
        if not isinstance(p, dict):
            continue
        text = str(p.get("text") or "").strip()
        quality = str(p.get("quality") or "")
        if skip_empty and (not text or quality == "empty"):
            continue
        if not text and skip_empty:
            continue
        out.append(p)
    return out


def _run_page_range(job_id: str, cfg: dict[str, Any]) -> None:
    from ilim_assistant.motorlar.tercume_atolye import translate_chunk
    from ilim_assistant.motorlar.tercume_read_pipeline import extract_source_pages

    rel = str(cfg.get("rel") or "").strip().replace("\\", "/").lstrip("/")
    page_from = cfg.get("page_from")
    page_to = cfg.get("page_to")
    skip_empty = bool(cfg.get("skip_empty", True))
    tgt = str(cfg.get("tgt_lang") or "tr")
    src = str(cfg.get("src_lang") or "auto")
    out_dir_rel = str(cfg.get("output_dir_rel") or "ilim-assistant/arsiv/tercume-output/page-range")
    root = _repo_root()

    _update(job_id, status="running", current_file=rel, done=0, total=0, label="Sayfalar okunuyor…")

    hit = extract_source_pages(rel, page_from=page_from, page_to=page_to)
    if not hit.get("ok"):
        _update(job_id, status="failed", error=str(hit.get("error") or "Okuma hatası"))
        return

    pages = _filter_pages(list(hit.get("pages") or []), skip_empty=skip_empty)
    if not pages:
        _update(job_id, status="failed", error="Seçilen aralıkta çevrilecek sayfa yok.")
        return

    out_dir = (root / out_dir_rel.replace("/", os.sep)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    _update(
        job_id,
        status="running",
        total=len(pages),
        done=0,
        outputs=[],
        partial_text="",
        ok_count=0,
        error_count=0,
    )

    parts: list[str] = []
    outputs: list[dict[str, Any]] = []
    ok_count = 0
    error_count = 0

    def _push_partial() -> None:
        from ilim_assistant.motorlar.tercume_translate_quality import summarize_chunk_qualities

        body = "\n\n".join(parts)
        if len(body) > _PARTIAL_TEXT_MAX:
            body = "…\n\n" + body[-_PARTIAL_TEXT_MAX:]
        qsum = summarize_chunk_qualities(outputs)
        _update(
            job_id,
            partial_text=body,
            ok_count=ok_count,
            error_count=error_count,
            quality_summary=qsum,
        )

    for i, p in enumerate(pages):
        with _lock:
            if (_jobs.get(job_id) or {}).get("cancel"):
                _push_partial()
                _update(
                    job_id,
                    status="cancelled",
                    outputs=outputs,
                    label="İptal edildi",
                )
                return

        label = str(p.get("label") or p.get("index") or i + 1)
        _update(job_id, done=i, label=f"{i + 1}/{len(pages)}: {label}")

        try:
            tr = translate_chunk(
                str(p.get("text") or ""),
                src_lang=src,
                tgt_lang=tgt,
                source_file=rel,
                page_index=int(p.get("index") if p.get("index") is not None else i),
            )
            if tr.get("ok"):
                chunk = str(tr.get("text") or "")
                parts.append(chunk)
                q = tr.get("quality") if isinstance(tr.get("quality"), dict) else {}
                pidx = int(p.get("index") if p.get("index") is not None else i)
                outputs.append(
                    {
                        "page": label,
                        "page_index": pidx,
                        "ok": True,
                        "quality_score": q.get("score"),
                        "quality_ok": q.get("ok"),
                        "quality_issues": q.get("issues") if isinstance(q.get("issues"), list) else [],
                    }
                )
                ok_count += 1
            else:
                err = str(tr.get("error") or "?")
                parts.append(f"[HATA sayfa {label}: {err}]")
                pidx = int(p.get("index") if p.get("index") is not None else i)
                outputs.append(
                    {"page": label, "page_index": pidx, "ok": False, "error": err}
                )
                error_count += 1
        except Exception as exc:
            parts.append(f"[HATA sayfa {label}: {str(exc)[:120]}]")
            pidx = int(p.get("index") if p.get("index") is not None else i)
            outputs.append(
                {
                    "page": label,
                    "page_index": pidx,
                    "ok": False,
                    "error": str(exc)[:120],
                }
            )
            error_count += 1

        _update(job_id, done=i + 1, outputs=outputs)
        _push_partial()

    stem = Path(rel).stem
    safe = re.sub(r"[^a-zA-Z0-9._\-]+", "_", stem)[:72] or "sayfa"
    pf = int(page_from) if page_from is not None else 0
    pt = int(page_to) if page_to is not None else pf + len(pages) - 1
    out_rel = f"{out_dir_rel.rstrip('/')}/{safe}_p{pf}-{pt}_{tgt}.txt"
    out_path = (root / out_rel.replace("/", os.sep)).resolve()
    body = "\n\n".join(parts)
    out_path.write_text(body, encoding="utf-8")

    _update(
        job_id,
        status="done",
        current_file="",
        output_rel=out_rel,
        partial_text=body,
        chars=len(body),
        page_from=pf,
        page_to=pt,
        pages_translated=len(pages),
        outputs=outputs,
        ok_count=ok_count,
        error_count=error_count,
        label=f"{ok_count}/{len(pages)} sayfa — kaydedildi",
    )


def start_page_range_job(
    rel: str,
    *,
    page_from: int | None = None,
    page_to: int | None = None,
    skip_empty: bool = True,
    tgt_lang: str = "tr",
    src_lang: str = "auto",
    output_dir_rel: str = "ilim-assistant/arsiv/tercume-output/page-range",
) -> dict[str, Any]:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        return {"ok": False, "error": "rel gerekli"}

    pf = int(page_from) if page_from is not None else None
    pt = int(page_to) if page_to is not None else None
    if pf is not None and pt is not None and pt < pf:
        return {"ok": False, "error": "page_to, page_from'dan küçük olamaz."}

    job_id = uuid.uuid4().hex[:12]
    cfg = {
        "rel": raw,
        "page_from": pf,
        "page_to": pt,
        "skip_empty": bool(skip_empty),
        "tgt_lang": (tgt_lang or "tr").strip(),
        "src_lang": (src_lang or "auto").strip(),
        "output_dir_rel": (output_dir_rel or "ilim-assistant/arsiv/tercume-output/page-range").strip(),
    }
    state = {
        "ok": True,
        "job_id": job_id,
        "job_type": "page_range",
        "version": BATCH_VERSION,
        "status": "queued",
        "rel": raw,
        "page_from": pf,
        "page_to": pt,
        "skip_empty": bool(skip_empty),
        "total": 0,
        "done": 0,
        "created_at": time.time(),
    }
    with _lock:
        _jobs[job_id] = state
    _persist(job_id, state)

    th = threading.Thread(target=_run_page_range, args=(job_id, cfg), daemon=True)
    th.start()
    return {
        "ok": True,
        "job_id": job_id,
        "job_type": "page_range",
        "rel": raw,
        "page_from": pf,
        "page_to": pt,
    }
