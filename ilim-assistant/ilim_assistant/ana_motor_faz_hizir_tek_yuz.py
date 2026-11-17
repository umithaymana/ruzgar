# Created by Ümit & Gökçenur
"""
Ana Motor — Dilim 8: Hızır tek yüz (sohbet → Hızır quiet handoff).

Panel doldurur; canlı pazar API uydurmaz. «pazar tara» anlığı faz84'te kalabilir.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ_HIZIR_VERSION = "ana-motor-faz-hizir-tek-yuz-v1-2026-11-17"

_ATOLYE_PREFIX_RE = re.compile(
    r"^(?:hizirda|hızırda|hizir\s*atölyesinde|hizir\s*atolyesinde|"
    r"hızır\s*atölyesinde|hizir\s*paneline|hızır\s*paneline|"
    r"hizir\s*motorunda|hızır\s*motoruna)\s*[:\-]?\s*(.*)$",
    re.I,
)
_PANEL_AC_RE = re.compile(
    r"^(?:(?:hizir|hızır)\s*(?:paneli|atölyesi|atolye(?:si)?|motoru)\s*(?:aç|ac|açıl|acil)|"
    r"(?:hizir|hızır)\s*motoruna\s*geç|(?:hizir|hızır)\s*motoruna\s*gec|"
    r"(?:hizir|hızır)\s*paneline\s*geç|(?:hizir|hızır)\s*paneline\s*gec)\s*[.!]?$",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ_HIZIR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz_hizir_enabled() -> bool:
    return _enabled()


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def parse_hizir_gorev_intent(message: str) -> dict[str, Any] | None:
    if not _enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 800:
        return None

    # Saf ticaret anlığı / durum — faz84 / hub'da kalsın
    if re.match(r"^(?:pazar\s+tara|ürün\s+tara|urun\s+tara)\b", raw, re.I):
        return None
    if re.search(r"\b(?:hizir|hızır)\s+durum\b", raw, re.I):
        return None
    if re.search(r"\b(?:nedir|ne\s+demek|kimdir)\b", raw, re.I):
        return None

    text = ""
    action = "panel"

    if _PANEL_AC_RE.match(raw):
        return {
            "motor": "hizir",
            "kind": "hizir_gorev",
            "task_line": "",
            "text": "",
            "action": "panel_ac",
            "version": FAZ_HIZIR_VERSION,
        }

    m = _ATOLYE_PREFIX_RE.match(raw)
    if not m:
        return None
    text = (m.group(1) or "").strip()
    action = "doldur" if len(text) >= 2 else "panel_ac"
    if action == "panel_ac":
        text = ""

    return {
        "motor": "hizir",
        "kind": "hizir_gorev",
        "task_line": text[:600],
        "text": text[:600],
        "action": action,
        "version": FAZ_HIZIR_VERSION,
    }


def enrich_orchestra_faz_hizir(
    orch: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    out = dict(orch or {})
    if not _enabled():
        return out
    if isinstance(out.get("ui_action"), dict) and out["ui_action"].get("type"):
        return out
    hit = parse_hizir_gorev_intent(message)
    if not hit:
        return out
    try:
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import enrich_orchestra_motor

        out = enrich_orchestra_motor(
            out,
            target="hizir",
            channel="faz_hizir_tek_yuz",
        )
    except Exception:
        out["active_motor"] = "hizir"
    out["tek_sohbet"] = True
    out["quiet"] = True
    out["faz_hizir"] = FAZ_HIZIR_VERSION
    out["ui_action"] = {
        "type": "surface_handoff",
        "motor": "hizir",
        "kind": "hizir_gorev",
        "task_line": hit.get("task_line") or "",
        "text": hit.get("text") or "",
        "action": hit.get("action") or "panel",
        "version": FAZ_HIZIR_VERSION,
    }
    return out


def faz_hizir_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "version": FAZ_HIZIR_VERSION,
        "pazar_api": False,
        "note": "panel handoff; canlı pazar API yok",
    }
