# Created by Ümit & Gökçenur
"""
Ana Motor — Dilim 3: Mimar tek yüz (sohbet → Mimar quiet handoff).

Yalnız görsel/atölye niyeti. İlim «nedir» / bilim / okuma buraya düşmez (F5).
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ_MIMAR_VERSION = "ana-motor-faz-mimar-tek-yuz-v1-2026-11-17"

_ATOLYE_PREFIX_RE = re.compile(
    r"^(?:mimarda|mimar\s*atölyesinde|mimar\s*atolyesinde|"
    r"mimar\s*paneline|mimar\s*motorunda|mimar\s*motoruna|"
    r"tasarımda|tasarimda|fotoğrafta|fotografta)\s*[:\-]?\s*(.*)$",
    re.I,
)
_PANEL_AC_RE = re.compile(
    r"^(?:(?:mimar|fotoğraf|fotograf|tasarım|tasarim)\s*"
    r"(?:paneli|atölyesi|atolye(?:si)?|motoru)\s*(?:aç|ac|açıl|acil)|"
    r"mimar\s*motoruna\s*geç|mimar\s*motoruna\s*gec|"
    r"mimar\s*paneline\s*geç|mimar\s*paneline\s*gec|"
    r"fotoğraf\s*paneli\s*aç|fotograf\s*paneli\s*ac)\s*[.!]?$",
    re.I,
)
_GORSEL_ACTION_RE = re.compile(
    r"\b(?:tasarla|çiz|ciz|görsel|gorsel|afiş|afis|logo|kapak|"
    r"fotoğraf|fotograf|render|mockup)\b",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ_MIMAR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz_mimar_enabled() -> bool:
    return _enabled()


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def parse_mimar_gorev_intent(message: str) -> dict[str, Any] | None:
    if not _enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 800:
        return None

    # İlim / bilgi Ana Motor'da kalsın
    if re.search(
        r"\b(?:nedir|ne\s+demek|kimdir|nerede|kaç\s+yıl|tarihinde|"
        r"anlat\s+bana|ilim|bilim|okuma\s+arsiv)\b",
        raw,
        re.I,
    ):
        return None

    text = ""
    action = "panel"

    if _PANEL_AC_RE.match(raw):
        return {
            "motor": "mimar",
            "kind": "mimar_gorev",
            "task_line": "",
            "text": "",
            "action": "panel_ac",
            "version": FAZ_MIMAR_VERSION,
        }

    m = _ATOLYE_PREFIX_RE.match(raw)
    if m:
        text = (m.group(1) or "").strip()
        action = "doldur" if len(text) >= 2 else "panel_ac"
        if action == "panel_ac":
            text = ""
    elif _GORSEL_ACTION_RE.search(raw) and re.search(
        r"\b(?:mimar|atölye|atolye|panel)\b", raw, re.I
    ):
        text = raw[:600]
        action = "doldur"
    else:
        return None

    return {
        "motor": "mimar",
        "kind": "mimar_gorev",
        "task_line": text[:600],
        "text": text[:600],
        "action": action,
        "version": FAZ_MIMAR_VERSION,
    }


def enrich_orchestra_faz_mimar(
    orch: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    out = dict(orch or {})
    if not _enabled():
        return out
    if isinstance(out.get("ui_action"), dict) and out["ui_action"].get("type"):
        return out
    hit = parse_mimar_gorev_intent(message)
    if not hit:
        return out
    try:
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import enrich_orchestra_motor

        out = enrich_orchestra_motor(
            out,
            target="mimar",
            channel="faz_mimar_tek_yuz",
        )
    except Exception:
        out["active_motor"] = "mimar"
    out["tek_sohbet"] = True
    out["quiet"] = True
    out["faz_mimar"] = FAZ_MIMAR_VERSION
    out["ui_action"] = {
        "type": "surface_handoff",
        "motor": "mimar",
        "kind": "mimar_gorev",
        "task_line": hit.get("task_line") or "",
        "text": hit.get("text") or "",
        "action": hit.get("action") or "panel",
        "version": FAZ_MIMAR_VERSION,
    }
    return out


def faz_mimar_status() -> dict[str, Any]:
    return {"enabled": _enabled(), "version": FAZ_MIMAR_VERSION}
