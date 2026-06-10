# Created by Ümit & Gökçenur
"""Ana Motor Faz G2 — Nebula öneri kartından tek tık kaynak ekleme."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def nebula_apply_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_NEBULA_APPLY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


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


def apply_nebula_oneri(
    collection: str,
    topic: str,
    *,
    upload_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Önerilen koleksiyona konu paketi yazar ve indeksi günceller.
    upload_ids varsa dosya içeriği; yoksa konu stub'ı.
    """
    if not nebula_apply_enabled():
        return {"ok": False, "error": "Nebula tek tık ekleme kapalı."}
    slug = _slug(collection)
    if not slug:
        return {"ok": False, "error": "Geçersiz koleksiyon."}
    topic_clean = (topic or "").strip()[:500] or "Genel konu"
    uploads = _collect_upload_texts(upload_ids)

    try:
        from ilim_assistant.rag_store import _knowledge_root, build_index
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

    idx_info: dict[str, Any] = {"status": "skipped"}
    try:
        idx_info = build_index(force=False, incremental=True)
    except Exception as exc:
        return {
            "ok": True,
            "warning": f"Paket yazıldı; indeks güncellenemedi: {exc}",
            "collection": slug,
            "batch_path": f"nebula/{slug}/incremental/{path.name}",
            "entries": len(entries),
            "from_uploads": bool(uploads),
        }

    rel = f"nebula/{slug}/incremental/{path.name}"
    return {
        "ok": True,
        "collection": slug,
        "batch_path": rel,
        "entries": len(entries),
        "from_uploads": bool(uploads),
        "index": idx_info.get("status") or "ok",
        "hint": (
            f"`knowledge/{rel}` yazıldı. "
            f"{'Yüklenen dosya içeriği' if uploads else 'Konu stub'} Nebula koleksiyonuna eklendi."
        ),
    }
