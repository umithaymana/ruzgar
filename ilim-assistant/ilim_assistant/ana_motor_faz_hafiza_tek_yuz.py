# Created by Ümit & Gökçenur
"""
Ana Motor — Dilim 2: Hafıza tek yüz (sohbet → Hafıza quiet handoff).

Atölye öneki → panel doldur. Otomatik kart yazmaz (zehir kapısı).
«hatırla:» / öğren komutları faz75 / learn_trust yolunda kalır — burası çalmaz.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ_HAFIZA_VERSION = "ana-motor-faz-hafiza-tek-yuz-v1-2026-11-17"

_ATOLYE_PREFIX_RE = re.compile(
    r"^(?:haf[ıi]zada|haf[ıi]za\s*atölyesinde|hafiza\s*atolyesinde|"
    r"haf[ıi]za\s*paneline|haf[ıi]za\s*motorunda|haf[ıi]za\s*motoruna)\s*[:\-]?\s*(.*)$",
    re.I,
)
_PANEL_AC_RE = re.compile(
    r"^(?:haf[ıi]za\s*(?:paneli|atölyesi|atolye(?:si)?|motoru)\s*(?:aç|ac|açıl|acil)|"
    r"haf[ıi]za\s*motoruna\s*geç|hafiza\s*motoruna\s*gec|"
    r"haf[ıi]za\s*paneline\s*geç|hafiza\s*paneline\s*gec)\s*[.!]?$",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ_HAFIZA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz_hafiza_enabled() -> bool:
    return _enabled()


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def parse_hafiza_gorev_intent(message: str) -> dict[str, Any] | None:
    """Panel handoff niyeti — kayıt yazmaz."""
    if not _enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 800:
        return None

    # Otomatik öğren / hatırla komutları mevcut kapılarda kalsın
    if re.match(
        r"^(?:hat[ıi]rla|unut|bunu\s+hat[ıi]rla|sana\s+[öo]ğret|"
        r"görev\s+oluştur|gorev\s+olustur|hat[ıi]rlat)\b",
        raw,
        re.I,
    ):
        return None
    if re.search(r"\b(?:nedir|ne\s+demek|kimdir)\b", raw, re.I):
        return None
    if re.search(r"\bhaf[ıi]za\s+(?:durum|özet|ozet|komut)", raw, re.I):
        return None

    text = ""
    action = "panel"

    if _PANEL_AC_RE.match(raw):
        return {
            "motor": "hafiza",
            "kind": "hafiza_gorev",
            "task_line": "",
            "text": "",
            "action": "panel_ac",
            "version": FAZ_HAFIZA_VERSION,
        }

    m = _ATOLYE_PREFIX_RE.match(raw)
    if not m:
        return None
    text = (m.group(1) or "").strip()
    action = "doldur" if len(text) >= 2 else "panel_ac"
    if action == "panel_ac":
        text = ""

    return {
        "motor": "hafiza",
        "kind": "hafiza_gorev",
        "task_line": text[:600],
        "text": text[:600],
        "action": action,
        "version": FAZ_HAFIZA_VERSION,
    }


def enrich_orchestra_faz_hafiza(
    orch: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    out = dict(orch or {})
    if not _enabled():
        return out
    if isinstance(out.get("ui_action"), dict) and out["ui_action"].get("type"):
        return out
    hit = parse_hafiza_gorev_intent(message)
    if not hit:
        return out
    try:
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import enrich_orchestra_motor

        out = enrich_orchestra_motor(
            out,
            target="hafiza",
            channel="faz_hafiza_tek_yuz",
        )
    except Exception:
        out["active_motor"] = "hafiza"
    out["tek_sohbet"] = True
    out["quiet"] = True
    out["faz_hafiza"] = FAZ_HAFIZA_VERSION
    out["ui_action"] = {
        "type": "surface_handoff",
        "motor": "hafiza",
        "kind": "hafiza_gorev",
        "task_line": hit.get("task_line") or "",
        "text": hit.get("text") or "",
        "action": hit.get("action") or "panel",
        "version": FAZ_HAFIZA_VERSION,
    }
    return out


def faz_hafiza_status() -> dict[str, Any]:
    return {"enabled": _enabled(), "version": FAZ_HAFIZA_VERSION}
