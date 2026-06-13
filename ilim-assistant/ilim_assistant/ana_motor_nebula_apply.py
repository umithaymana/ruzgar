# Created by Ümit & Gökçenur
"""Ana Motor Faz G2/H1 — Nebula öneri kartından tek tık kaynak ekleme (+ arka plan indeks)."""

from __future__ import annotations

import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_job_lock = threading.Lock()
_bg_job: dict[str, Any] = {"running": False}


def nebula_apply_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_NEBULA_APPLY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def nebula_apply_bg_enabled() -> bool:
    return os.environ.get("RUZGAR_NEBULA_APPLY_BG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def get_nebula_apply_job_status() -> dict[str, Any]:
    with _job_lock:
        return dict(_bg_job)


def _batch_markdown(
    entries: list[tuple[str, str]],
    batch_index: int,
    collection: str,
    source_name: str,
) -> str:
    head = (
        f"# Nebula — {collection}\n\n"
        f"- Paket: `{batch_index:05d}`\n"
        f"- Kayıt: **{len(entries)}**\n"
        f"- Kaynak: `{source_name}`\n"
        f"- Yükleme (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n"
        "---\n\n"
    )
    parts = [head]
    for title, body in entries:
        safe_title = title.replace("\n", " ").strip()[:500]
        parts.append(f"## {safe_title}\n{body.strip()}\n\n")
    return "".join(parts)


def _slug(s: str, max_len: int = 48) -> str:
    t = (s or "").strip().casefold()
    t = re.sub(r"[^\w\s\-]", "", t)
    t = re.sub(r"[\s\-]+", "-", t).strip("-")
    return (t[:max_len] or "konu")[:max_len]


def _collect_upload_texts(upload_ids: list[str] | None) -> list[tuple[str, str]]:
    if not upload_ids:
        return []
    try:
        from ilim_assistant.ana_motor_dosya_ingest import get_upload_records
    except Exception:
        return []
    rows: list[tuple[str, str]] = []
    for rec in get_upload_records(upload_ids):
        fname = str(rec.get("filename") or "dosya")
        chunks = list(rec.get("chunk_texts") or [])
        if not chunks:
            continue
        body = "\n\n".join(chunks).strip()
        if body:
            rows.append((fname, body))
    return rows


def write_nebula_batch(
    collection: str,
    topic: str,
    *,
    upload_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Paketi diske yazar; indeks güncellemez (H1 arka plan için)."""
    slug = _slug(collection)
    if not slug:
        return {"ok": False, "error": "Geçersiz koleksiyon."}
    topic_clean = (topic or "").strip()[:500] or "Genel konu"
    uploads = _collect_upload_texts(upload_ids)

    try:
        from ilim_assistant.rag_store import _knowledge_root
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    nebula_root = _knowledge_root() / "nebula"
    out_dir = nebula_root / slug / "incremental"
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(out_dir.glob("nebula_batch_*.md"))
    batch_no = len(existing)

    entries: list[tuple[str, str]] = []
    if uploads:
        for fname, body in uploads:
            title = f"{topic_clean} — {fname}"[:500]
            entries.append((title, body[:12000]))
    else:
        entries.append(
            (
                topic_clean,
                (
                    "(Mimar — bu konu için Nebula öneri kartından otomatik stub oluşturuldu. "
                    "İlgili kaynak dosyasını sürükleyip tekrar «Kaynağı ekle» kullanabilir "
                    "veya `knowledge/nebula/` altında düzenleyebilirsin.)"
                ),
            )
        )

    path = out_dir / f"nebula_batch_{batch_no:05d}.md"
    src_name = "ana_motor_oneri_apply"
    if uploads:
        src_name = ", ".join(u[0] for u in uploads)[:120]
    path.write_text(
        _batch_markdown(entries, batch_no, slug, src_name),
        encoding="utf-8",
    )

    meta_path = nebula_root / slug / "meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    if not meta_path.is_file():
        meta_path.write_text(
            (
                "{\n"
                f'  "collection": "{slug}",\n'
                f'  "title": "{slug.replace("-", " ")}",\n'
                f'  "created_via": "ana_motor_nebula_apply",\n'
                f'  "updated_at": "{datetime.now(timezone.utc).isoformat(timespec="seconds")}"\n'
                "}\n"
            ),
            encoding="utf-8",
        )

    rel = f"nebula/{slug}/incremental/{path.name}"
    return {
        "ok": True,
        "collection": slug,
        "batch_path": rel,
        "entries": len(entries),
        "from_uploads": bool(uploads),
    }


def write_nebula_qa_batch(
    collection: str,
    question: str,
    answer: str,
    *,
    source: str = "otomatik_ogrenme",
) -> dict[str, Any]:
    """Faz AC4 — otomatik öğrenme soru/cevap paketi."""
    slug = _slug(collection)
    if not slug:
        return {"ok": False, "error": "Geçersiz koleksiyon."}
    q = (question or "").strip()
    a = (answer or "").strip()
    if not q or len(q) < 4:
        return {"ok": False, "error": "Soru boş."}
    if not a or len(a) < 20:
        return {"ok": False, "error": "Cevap çok kısa."}

    try:
        from ilim_assistant.rag_store import _knowledge_root
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    nebula_root = _knowledge_root() / "nebula"
    out_dir = nebula_root / slug / "incremental"
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(out_dir.glob("nebula_batch_*.md"))
    batch_no = len(existing)

    title = q[:500]
    body = (
        f"Kaynak: **{source}** (Ana Motor otomatik öğrenme — Ümit & Gökçenur)\n\n"
        f"**Soru:** {q}\n\n"
        f"**Cevap:**\n{a}\n"
    )
    entries = [(title, body[:12000])]
    path = out_dir / f"nebula_batch_{batch_no:05d}.md"
    path.write_text(
        _batch_markdown(entries, batch_no, slug, source),
        encoding="utf-8",
    )

    meta_path = nebula_root / slug / "meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    if not meta_path.is_file():
        meta_path.write_text(
            (
                "{\n"
                f'  "collection": "{slug}",\n'
                f'  "title": "{slug.replace("_", " ")}",\n'
                f'  "created_via": "{source}",\n'
                f'  "updated_at": "{datetime.now(timezone.utc).isoformat(timespec="seconds")}"\n'
                "}\n"
            ),
            encoding="utf-8",
        )

    rel = f"nebula/{slug}/incremental/{path.name}"
    return {
        "ok": True,
        "collection": slug,
        "batch_path": rel,
        "entries": len(entries),
        "from_uploads": False,
        "qa": True,
    }


def _start_index_after_batch(batch: dict[str, Any]) -> dict[str, Any]:
    with _job_lock:
        if _bg_job.get("running"):
            return {
                "ok": False,
                "error": "Arka plan indeksleme sürüyor.",
                "job": dict(_bg_job),
            }
        _bg_job.clear()
        _bg_job.update(
            running=True,
            collection=batch.get("collection"),
            batch_path=batch.get("batch_path"),
            entries=batch.get("entries"),
            progress="Paket yazıldı — indeks kuyruğa alındı…",
            started_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            error=None,
        )

    threading.Thread(
        target=_run_index_worker,
        args=(batch,),
        daemon=True,
        name="nebula-apply-index",
    ).start()

    return {
        "ok": True,
        "async": True,
        "collection": batch["collection"],
        "batch_path": batch["batch_path"],
        "entries": batch["entries"],
        "from_uploads": batch.get("from_uploads"),
        "hint": (
            f"`knowledge/{batch['batch_path']}` yazıldı. "
            "İndeks arka planda güncelleniyor."
        ),
        "job": get_nebula_apply_job_status(),
    }


def start_nebula_qa_apply_background(
    collection: str,
    question: str,
    answer: str,
    *,
    source: str = "otomatik_ogrenme",
) -> dict[str, Any]:
    """Faz AC4 — öğrenilen QA → Nebula + arka plan indeks."""
    if not nebula_apply_enabled():
        return {"ok": False, "error": "Nebula tek tık ekleme kapalı."}
    batch = write_nebula_qa_batch(collection, question, answer, source=source)
    if not batch.get("ok"):
        return batch
    out = _start_index_after_batch(batch)
    out["qa"] = True
    return out


def _run_index_worker(batch_meta: dict[str, Any]) -> None:
    global _bg_job
    try:
        with _job_lock:
            _bg_job["progress"] = "Vektör indeksi güncelleniyor…"
        from ilim_assistant.rag_store import build_index

        idx_info = build_index(force=False, incremental=True)
        with _job_lock:
            _bg_job.update(
                running=False,
                progress="Tamamlandı",
                index=idx_info.get("status") or "ok",
                chunks=idx_info.get("chunks"),
                finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
    except Exception as exc:
        with _job_lock:
            _bg_job.update(
                running=False,
                progress="Hata",
                error=str(exc),
            )


def start_nebula_apply_background(
    collection: str,
    topic: str,
    *,
    upload_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Paketi yaz, indeksi arka planda güncelle (Faz H1)."""
    if not nebula_apply_enabled():
        return {"ok": False, "error": "Nebula tek tık ekleme kapalı."}
    with _job_lock:
        if _bg_job.get("running"):
            return {
                "ok": False,
                "error": "Arka plan indeksleme sürüyor.",
                "job": dict(_bg_job),
            }
    batch = write_nebula_batch(collection, topic, upload_ids=upload_ids)
    if not batch.get("ok"):
        return batch

    out = _start_index_after_batch(batch)
    out["from_uploads"] = batch.get("from_uploads")
    return out


def apply_nebula_oneri(
    collection: str,
    topic: str,
    *,
    upload_ids: list[str] | None = None,
    background: bool | None = None,
) -> dict[str, Any]:
    """
    Önerilen koleksiyona konu paketi yazar.
    Varsayılan: arka plan indeks (API); smoke/test için senkron yol.
    """
    use_bg = nebula_apply_bg_enabled() if background is None else bool(background)
    if use_bg:
        return start_nebula_apply_background(collection, topic, upload_ids=upload_ids)

    if not nebula_apply_enabled():
        return {"ok": False, "error": "Nebula tek tık ekleme kapalı."}
    batch = write_nebula_batch(collection, topic, upload_ids=upload_ids)
    if not batch.get("ok"):
        return batch
    try:
        from ilim_assistant.rag_store import build_index

        idx_info = build_index(force=False, incremental=True)
    except Exception as exc:
        return {
            "ok": True,
            "warning": f"Paket yazıldı; indeks güncellenemedi: {exc}",
            **batch,
        }
    rel = batch["batch_path"]
    return {
        **batch,
        "index": idx_info.get("status") or "ok",
        "hint": (
            f"`knowledge/{rel}` yazıldı. "
            f"{'Yüklenen dosya içeriği' if batch.get('from_uploads') else 'Konu stub'} "
            "Nebula koleksiyonuna eklendi."
        ),
    }
