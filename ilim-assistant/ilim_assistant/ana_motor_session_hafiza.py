# Created by Ümit & Gökçenur
"""Ana Motor Faz H2 — oturum dosya paketini kalıcı hafızaya köprüle."""

from __future__ import annotations

import os
from typing import Any


def session_remember_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_SESSION_REMEMBER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _excerpt(text: str, cap: int = 420) -> str:
    t = (text or "").strip().replace("\r\n", "\n")
    if len(t) <= cap:
        return t
    return t[: cap - 1].rstrip() + "…"


def build_session_memory_payload(
    session_id: str | None = None,
    *,
    upload_ids: list[str] | None = None,
    topic: str = "",
) -> dict[str, Any]:
    from ilim_assistant.ana_motor_dosya_ingest import (
        get_upload_records,
        resolve_upload_ids,
    )

    ids = resolve_upload_ids(upload_ids, session_id)
    if not ids:
        return {"ok": False, "error": "Oturumda hatırlanacak dosya yok."}
    records = get_upload_records(ids)
    if not records:
        return {"ok": False, "error": "Dosya kayıtları bulunamadı (süre dolmuş olabilir)."}

    topic_clean = (topic or "").strip()[:200]
    lines: list[str] = []
    total_chars = 0
    for rec in records:
        fname = str(rec.get("filename") or "dosya")
        chunks = list(rec.get("chunk_texts") or [])
        body = "\n".join(chunks).strip()
        total_chars += int(rec.get("chars") or len(body))
        lines.append(f"· {fname} ({len(body)} karakter)\n{_excerpt(body, 380)}")

    label = topic_clean or f"{len(records)} dosyalık oturum"
    soru = f"Dosya oturumu — {label}"
    cevap = (
        f"Mimarın yüklediği dosya paketi (oturum: {session_id or '—'}).\n"
        f"Toplam {len(records)} dosya, ~{total_chars} karakter.\n\n"
        + "\n\n".join(lines)
    )
    if len(cevap) > 6000:
        cevap = cevap[:5990].rstrip() + "…"
    return {
        "ok": True,
        "session_id": session_id,
        "upload_ids": ids,
        "soru": soru,
        "cevap": cevap,
        "file_count": len(records),
        "chars": total_chars,
    }


def remember_upload_session(
    session_id: str | None = None,
    *,
    upload_ids: list[str] | None = None,
    topic: str = "",
) -> dict[str, Any]:
    """Oturum paketini `ruzgar_genel_hafiza.json` içine yazar."""
    if not session_remember_enabled():
        return {"ok": False, "error": "Oturum hatırla köprüsü kapalı."}
    payload = build_session_memory_payload(
        session_id, upload_ids=upload_ids, topic=topic
    )
    if not payload.get("ok"):
        return payload
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        get_hafiza_motor().ekle_bilgi(
            str(payload["soru"]),
            str(payload["cevap"]),
            motor_tipi="Dosya",
        )
    except Exception as exc:
        return {"ok": False, "error": f"Hafızaya yazılamadı: {exc}"}
    return {
        "ok": True,
        "remembered": True,
        "soru": payload["soru"],
        "file_count": payload["file_count"],
        "chars": payload["chars"],
        "hint": (
            f"{payload['file_count']} dosya hafızaya kaydedildi. "
            "«hatırla» ile aynı köprü — `ruzgar_genel_hafiza.json`."
        ),
    }
