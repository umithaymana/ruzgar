# Created by Ümit & Gökçenur
"""Ana Motor — sıra 5c: uzun oturum bağlamı (özet + dosya paketi + genişletilmiş geçmiş)."""

from __future__ import annotations

import os
from typing import Any

UZUN_BAGLAM_VERSION = "ana-motor-uzun-baglam-v1-2026-06-17-sira5c"


def uzun_baglam_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_UZUN_BAGLAM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def conversation_context_char_cap() -> int:
    try:
        return max(
            4000,
            min(int(os.environ.get("RUZGAR_ANA_CONV_CHARS", "12000")), 24000),
        )
    except ValueError:
        return 12000


def history_message_cap(mode_norm: str) -> int | None:
    """Genel modda uzun bağlam açıkken chat_core varsayılanını yükseltir."""
    if not uzun_baglam_enabled():
        return None
    m = (mode_norm or "genel").strip().lower()
    if m not in ("genel", "uretim", "gelisim"):
        return None
    try:
        return max(12, min(int(os.environ.get("CHAT_HISTORY_MSGS", "30")), 48))
    except ValueError:
        return 30


def history_char_cap(mode_norm: str) -> int | None:
    if not uzun_baglam_enabled():
        return None
    m = (mode_norm or "genel").strip().lower()
    if m not in ("genel", "uretim", "gelisim"):
        return None
    try:
        return max(8000, min(int(os.environ.get("CHAT_HISTORY_CHARS", "36000")), 96000))
    except ValueError:
        return 36000


def _clip(text: str, limit: int) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[: max(0, limit - 1)].rstrip() + "…"


def build_upload_session_sticky_block(
    message: str,
    upload_ids: list[str] | None,
    *,
    session_id: str | None = None,
) -> str:
    """Yüklenen dosya oturumunu her turda hatırlat (RAG isabeti zayıfsa bile)."""
    if not uzun_baglam_enabled():
        return ""
    try:
        from ilim_assistant.ana_motor_dosya_ingest import (
            ingest_enabled,
            resolve_upload_ids,
            search_upload_context,
        )
    except Exception:
        return ""
    if not ingest_enabled():
        return ""
    ids = resolve_upload_ids(upload_ids, session_id)
    if not ids:
        return ""

    with_meta: list[tuple[str, str, int]] = []
    try:
        from ilim_assistant.ana_motor_dosya_ingest import get_upload_records

        for rec in get_upload_records(ids):
            uid = str(rec.get("upload_id") or "")
            fname = str(rec.get("filename") or rec.get("source") or uid)
            chars = int(rec.get("chars") or 0)
            with_meta.append((uid, fname, chars))
    except Exception:
        with_meta = [(uid, uid, 0) for uid in ids[:8]]

    lines = [
        "[YÜKLENEN DOSYA PAKETİ — bu oturumda Mimar dosya yükledi; kullanıcıya listeyi tekrarlama]",
    ]
    if session_id:
        lines.append(f"Oturum: {str(session_id)[:16]}")
    for _uid, fname, chars in with_meta:
        extra = f" · ~{chars} karakter" if chars else ""
        lines.append(f"· {fname}{extra}")

    q = (message or "").strip() or "özet bağlam"
    try:
        hits = search_upload_context(
            q,
            upload_ids,
            session_id=session_id,
            top_k=3,
        )
        for text, src, score in hits:
            if float(score) < 0.35:
                continue
            lines.append(f"  ↳ [{_clip(src, 48)}] {_clip(text, 520)}")
    except Exception:
        pass

    lines.append(
        "Talimat: Soru yüklenen dosyayla ilgiliyse önce bu pasajları kullan; "
        "emin değilsen dosyada geçmiyor de."
    )
    lines.append("[/YÜKLENEN DOSYA PAKETİ]")
    return "\n".join(lines)


def build_ana_motor_uzun_baglam_addon(
    message: str,
    history: list | None,
    *,
    mode_norm: str = "genel",
    session_id: str | None = None,
    upload_ids: list[str] | None = None,
) -> str:
    """Ana motor LLM yoluna eklenecek uzun bağlam (özet + dosya + son turlar)."""
    if not uzun_baglam_enabled():
        return ""
    m = (mode_norm or "genel").strip().lower()
    if m not in ("genel", "uretim", "gelisim"):
        return ""

    sections: list[str] = []
    try:
        from ilim_assistant.ruzgar_tek_beyin_baglam import build_tek_beyin_baglam_addon

        # conversation_context chat_core SOHBET BAĞLAMI bloğunda — çift yazma yok
        tb = build_tek_beyin_baglam_addon(
            message,
            history,
            conversation_context=None,
            session_id=session_id,
        )
        if tb.strip():
            sections.append(tb.strip())
    except Exception:
        pass

    up = build_upload_session_sticky_block(
        message,
        upload_ids,
        session_id=session_id,
    )
    if up.strip():
        sections.append(up.strip())

    if not sections:
        return ""
    return "\n\n".join(sections) + "\n"


def uzun_baglam_status() -> dict[str, Any]:
    ozet: dict[str, Any] = {}
    try:
        from ilim_assistant.ruzgar_tek_beyin_ozet import tek_beyin_ozet_status

        ozet = tek_beyin_ozet_status()
    except Exception:
        pass
    baglam: dict[str, Any] = {}
    try:
        from ilim_assistant.ruzgar_tek_beyin_baglam import tek_beyin_baglam_status

        baglam = tek_beyin_baglam_status()
    except Exception:
        pass
    return {
        "enabled": uzun_baglam_enabled(),
        "version": UZUN_BAGLAM_VERSION,
        "conv_chars": conversation_context_char_cap(),
        "history_msgs": history_message_cap("genel"),
        "history_chars": history_char_cap("genel"),
        "tek_beyin_ozet": ozet,
        "tek_beyin_baglam": baglam,
    }
