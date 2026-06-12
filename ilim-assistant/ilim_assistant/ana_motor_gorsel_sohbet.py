# Created by Ümit & Gökçenur
"""Ana Motor — Faz H: sohbet içi görsel (Gemini Vision)."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

FAZ_H_GORSEL_VERSION = "ana-motor-gorsel-sohbet-h1-2026-06-11"
_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def gorsel_sohbet_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_GORSEL_SOHBET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def image_extensions_enabled() -> frozenset[str]:
    if not gorsel_sohbet_enabled():
        return frozenset()
    return _IMAGE_EXT


def try_gorsel_sohbet_reply(
    message: str,
    *,
    upload_ids: list[str] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Yüklenen görsel + soru → Gemini vision yanıtı."""
    if not gorsel_sohbet_enabled():
        return {"ok": True, "handled": False, "reason": "disabled"}
    msg = (message or "").strip()
    if not msg:
        return {"ok": True, "handled": False, "reason": "empty"}
    try:
        from ilim_assistant.ana_motor_dosya_ingest import get_upload_records, resolve_upload_ids
        from ilim_assistant.llm_gemini import gemini_configured

        if not gemini_configured():
            return {"ok": True, "handled": False, "reason": "no_gemini"}
        ids = resolve_upload_ids(upload_ids, session_id)
        if not ids:
            return {"ok": True, "handled": False, "reason": "no_upload"}
        records = get_upload_records(ids)
        img_path: Path | None = None
        mime = "image/jpeg"
        for rec in records:
            fname = str(rec.get("filename") or "")
            ext = Path(fname).suffix.lower()
            if ext not in _IMAGE_EXT:
                continue
            rel = str(rec.get("stored_rel") or rec.get("path") or "")
            if not rel:
                continue
            from ilim_assistant.ana_motor_dosya_ingest import _PKG_ROOT

            cand = _PKG_ROOT / rel if not Path(rel).is_absolute() else Path(rel)
            if cand.is_file():
                img_path = cand
                mime = {
                    ".png": "image/png",
                    ".webp": "image/webp",
                    ".gif": "image/gif",
                }.get(ext, "image/jpeg")
                break
        if not img_path:
            return {"ok": True, "handled": False, "reason": "no_image"}
        data = img_path.read_bytes()
        if len(data) > 6_000_000:
            return {"ok": False, "handled": False, "error": "Görsel çok büyük (max ~6MB)."}
        reply = _gemini_vision(msg, data, mime)
        if not reply:
            return {"ok": True, "handled": False, "reason": "empty_reply"}
        return {
            "ok": True,
            "handled": True,
            "reply": reply,
            "channel": "gorsel_sohbet",
            "version": FAZ_H_GORSEL_VERSION,
        }
    except Exception as exc:
        return {"ok": False, "handled": False, "error": str(exc)[:200]}


def _gemini_vision(prompt: str, image_bytes: bytes, mime: str) -> str:
    import requests

    from ilim_assistant.llm_gemini import gemini_api_key

    key = gemini_api_key()
    if not key:
        return ""
    model = os.environ.get("RUZGAR_GEMINI_VISION_MODEL", "gemini-2.0-flash").strip()
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [
            {
                "parts": [
                    {"text": f"Ümit abi soruyor (Türkçe yanıt ver):\n{prompt}"},
                    {"inline_data": {"mime_type": mime, "data": b64}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 1024},
    }
    r = requests.post(url, params={"key": key}, json=body, timeout=90)
    if r.status_code != 200:
        return ""
    data = r.json()
    parts = (
        ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
    )
    texts = [str(p.get("text") or "") for p in parts if isinstance(p, dict)]
    return "\n".join(t for t in texts if t).strip()
