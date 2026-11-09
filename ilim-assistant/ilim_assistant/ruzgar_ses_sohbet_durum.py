# Created by Ümit & Gökçenur
"""
Motor B / S2 — sesli sohbet durum iskeleti.

Durumlar: idle → listening → thinking → speaking → idle
Barge-in: speaking iken dinleme isteği → listening (konuşma kesilir istemci tarafında).
Kapat: RUZGAR_SES_SOHBET_DURUM=0
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

VERSION = "ses-sohbet-durum-v1-2026-11-09"
_STATES = ("idle", "listening", "thinking", "speaking")
_lock = threading.Lock()
_state = "idle"
_updated = 0.0
_meta: dict[str, Any] = {}


def enabled() -> bool:
    return os.environ.get("RUZGAR_SES_SOHBET_DURUM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def public_status() -> dict[str, Any]:
    with _lock:
        return {
            "enabled": enabled(),
            "version": VERSION,
            "state": _state,
            "updated_at": _updated,
            "meta": dict(_meta),
            "states": list(_STATES),
            "note": "STT=/api/stt · TTS=/api/tts · barge-in: speaking→listening",
        }


def get_state() -> str:
    with _lock:
        return _state


def set_state(new_state: str, **meta: Any) -> dict[str, Any]:
    global _state, _updated, _meta
    if not enabled():
        return {"ok": False, "error": "kapalı"}
    ns = (new_state or "").strip().lower()
    if ns not in _STATES:
        return {"ok": False, "error": f"geçersiz durum: {new_state}"}
    with _lock:
        prev = _state
        # barge-in: speaking → listening serbest
        if prev == "speaking" and ns == "listening":
            _meta = {"barge_in": True, **{k: v for k, v in meta.items() if v is not None}}
        else:
            _meta = {k: v for k, v in meta.items() if v is not None}
        _state = ns
        _updated = time.time()
        return {
            "ok": True,
            "from": prev,
            "state": _state,
            "updated_at": _updated,
            "meta": dict(_meta),
        }


def reset() -> dict[str, Any]:
    return set_state("idle")
