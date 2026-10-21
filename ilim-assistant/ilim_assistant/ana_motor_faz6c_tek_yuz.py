# Created by Ümit & Gökçenur
"""
Ana Motor — Faz 6c: tek yüz pilot (sohbet → programlama görev handoff).

Genel sohbette kod görevi niyetini tanır; quiet handoff ile programlama
paneline `görev:` + path_hint taşır. Serbest kod çalıştırma yok.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ6C_VERSION = "ana-motor-faz6c-tek-yuz-v1-2026-10-21"

# «şu projede … yap», «projects/foo …», «görev: …», «programlamada: …»
_GOREV_PREFIX_RE = re.compile(
    r"^(?:görev|gorev|iş|is|yap)\s*:\s*(.+)$",
    re.I,
)
_PROG_ATOLYE_RE = re.compile(
    r"^(?:programlamada|kodda|atölyede|atolyede)\s*[:\-]?\s*(.+)$",
    re.I,
)
_SU_PROJEDE_RE = re.compile(
    r"^(?:şu|su|bu)\s+proje(?:de|yi)?\s+(.+)$",
    re.I,
)
_PROJECTS_PATH_RE = re.compile(
    r"(?:^|\s)(projects/[\w.\-]+(?:/[\w.\-]+)*)\b",
    re.I,
)
_ACTION_RE = re.compile(
    r"(?:pytest|health|endpoint|version|refactor|düzelt|duzelt|ekle|yaz|"
    r"geçir|gecir|oluştur|olustur|patch|dosya|multi\s*file|mega)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ6C", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz6c_enabled() -> bool:
    return _enabled()


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def parse_programlama_gorev_intent(message: str) -> dict[str, Any] | None:
    """Genel sohbetten programlama görev niyeti (yazım yok — yalnız çıkarım)."""
    if not _enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 600:
        return None
    # Yüzey gönder kalıbı «kodu programlamaya gönder» — tek sohbet zaten yakalar
    if re.search(r"programlamaya\s+g[öo]nder", raw, re.I):
        return None

    goal = ""
    m = _GOREV_PREFIX_RE.match(raw)
    if m:
        goal = (m.group(1) or "").strip()
    if not goal:
        m = _PROG_ATOLYE_RE.match(raw)
        if m:
            goal = (m.group(1) or "").strip()
    if not goal:
        m = _SU_PROJEDE_RE.match(raw)
        if m:
            goal = (m.group(1) or "").strip()
    if not goal:
        pm = _PROJECTS_PATH_RE.search(raw)
        if pm and _ACTION_RE.search(raw):
            goal = raw
    if not goal:
        return None
    if not _ACTION_RE.search(goal) and "projects/" not in goal.lower():
        # Saf sohbet / bilgi sorusu değil — eylem veya proje yolu şart
        if len(goal.split()) < 4:
            return None
        if not re.search(r"(?:yap|et|geçir|gecir|düzelt|duzelt|ekle)", goal, re.I):
            return None

    task_line = goal if goal.lower().startswith(("görev:", "gorev:")) else f"görev: {goal}"
    task_line = task_line[:600]
    path_hint = "agent"
    named: list[str] = []
    try:
        from ilim_assistant.motorlar.programlama_yuzey_bridge import (
            build_surface_handoff_payload,
        )

        payload = build_surface_handoff_payload(task_line)
        path_hint = str(payload.get("path_hint") or "agent")
        named = list(payload.get("named_paths") or [])
        if payload.get("task_line"):
            task_line = str(payload["task_line"])[:600]
    except Exception:
        pass

    return {
        "motor": "programlama",
        "kind": "programlama_gorev",
        "goal": goal[:500],
        "task_line": task_line,
        "path_hint": path_hint,
        "named_paths": named[:12],
        "version": FAZ6C_VERSION,
    }


def enrich_orchestra_faz6c(
    orch: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    """Tek yüz: görev niyeti → quiet programlama handoff (yüzey gönder’den önce bakılmaz)."""
    out = dict(orch or {})
    if not _enabled():
        return out
    # Yüzey gönder zaten ui_action doldurduysa dokunma
    if isinstance(out.get("ui_action"), dict) and out["ui_action"].get("type"):
        return out
    hit = parse_programlama_gorev_intent(message)
    if not hit:
        return out
    mid = "programlama"
    try:
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import enrich_orchestra_motor

        out = enrich_orchestra_motor(
            out,
            target=mid,
            channel="faz6c_tek_yuz",
        )
    except Exception:
        out["active_motor"] = mid
    out["tek_sohbet"] = True
    out["quiet"] = True
    out["faz6c"] = FAZ6C_VERSION
    out["ui_action"] = {
        "type": "surface_handoff",
        "motor": mid,
        "kind": "programlama_gorev",
        "task_line": hit["task_line"],
        "goal": hit["goal"],
        "path_hint": hit["path_hint"],
        "named_paths": hit.get("named_paths") or [],
        "version": FAZ6C_VERSION,
    }
    return out


def faz6c_status() -> dict[str, Any]:
    return {"enabled": _enabled(), "version": FAZ6C_VERSION}
