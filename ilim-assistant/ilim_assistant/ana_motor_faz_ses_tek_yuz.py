# Created by Ümit & Gökçenur
"""
Ana Motor — Dilim 1: Ses tek yüz (sohbet → Ses quiet handoff).

6c / Faz E kalıbı. Atölye öneki veya açık panel niyeti → surface_handoff.
Profil anlığı («alim moduna geç») faz72'de kalır; burası çalmaz.
Bilgi/ilim sohbetini Ses'e çekmez.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ_SES_VERSION = "ana-motor-faz-ses-tek-yuz-v1-2026-11-17"

_ATOLYE_PREFIX_RE = re.compile(
    r"^(?:seste|ses\s*atölyesinde|ses\s*atolyesinde|ses\s*paneline|"
    r"ses\s*motorunda|ses\s*motoruna)\s*[:\-]?\s*(.*)$",
    re.I,
)
_PANEL_AC_RE = re.compile(
    r"^(?:ses\s*(?:paneli|atölyesi|atolye(?:si)?|motoru)\s*(?:aç|ac|açıl|acil)|"
    r"ses\s*motoruna\s*geç|ses\s*motoruna\s*gec|"
    r"ses\s*paneline\s*geç|ses\s*paneline\s*gec)\s*[.!]?$",
    re.I,
)
_OKU_ATOLYE_RE = re.compile(
    r"^(?:sesle\s+oku|ses\s+ile\s+oku|atölyede\s+oku|atolyede\s+oku)\s*[:\-]?\s*(.+)$",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ_SES", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz_ses_enabled() -> bool:
    return _enabled()


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def parse_ses_gorev_intent(message: str) -> dict[str, Any] | None:
    """Genel sohbetten Ses atölye handoff niyeti (TTS çalıştırmaz)."""
    if not _enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 800:
        return None

    # Bilgi / ilim kaçmasın
    if re.search(
        r"\b(?:nedir|ne\s+demek|kimdir|nerede|kaç|nasıl\s+oluş|anlat\s+bana)\b",
        raw,
        re.I,
    ):
        return None
    # Profil anlığı faz72'ye bırak
    if re.search(
        r"\b(?:alim|edip|asistan)\s+(?:moduna|profili|sesi)\b|"
        r"\b(?:moduna\s+geç|profiline\s+geç|sesi\s+aç)\b",
        raw,
        re.I,
    ):
        return None
    if re.search(r"\b(?:stt\s+durum|ses\s+ayar)", raw, re.I):
        return None

    text = ""
    action = "panel"

    if _PANEL_AC_RE.match(raw):
        return {
            "motor": "ses",
            "kind": "ses_gorev",
            "task_line": "",
            "text": "",
            "action": "panel_ac",
            "version": FAZ_SES_VERSION,
        }

    m = _ATOLYE_PREFIX_RE.match(raw)
    if m:
        text = (m.group(1) or "").strip()
        action = "doldur" if text else "panel_ac"
    else:
        m2 = _OKU_ATOLYE_RE.match(raw)
        if m2:
            text = (m2.group(1) or "").strip()
            action = "oku_doldur"
        else:
            return None

    if action == "doldur" and len(text) < 2:
        action = "panel_ac"
        text = ""

    return {
        "motor": "ses",
        "kind": "ses_gorev",
        "task_line": text[:600],
        "text": text[:600],
        "action": action,
        "version": FAZ_SES_VERSION,
    }


def enrich_orchestra_faz_ses(
    orch: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    out = dict(orch or {})
    if not _enabled():
        return out
    if isinstance(out.get("ui_action"), dict) and out["ui_action"].get("type"):
        return out
    hit = parse_ses_gorev_intent(message)
    if not hit:
        return out
    try:
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import enrich_orchestra_motor

        out = enrich_orchestra_motor(
            out,
            target="ses",
            channel="faz_ses_tek_yuz",
        )
    except Exception:
        out["active_motor"] = "ses"
    out["tek_sohbet"] = True
    out["quiet"] = True
    out["faz_ses"] = FAZ_SES_VERSION
    out["ui_action"] = {
        "type": "surface_handoff",
        "motor": "ses",
        "kind": "ses_gorev",
        "task_line": hit.get("task_line") or "",
        "text": hit.get("text") or "",
        "action": hit.get("action") or "panel",
        "version": FAZ_SES_VERSION,
    }
    return out


def faz_ses_status() -> dict[str, Any]:
    return {"enabled": _enabled(), "version": FAZ_SES_VERSION}
