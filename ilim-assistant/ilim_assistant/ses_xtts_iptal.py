# Created by Ümit & Gökçenur
"""XTTS sunucu tarafı iptal — barge / durdur / yeni istek.

Generation sayacı: iptal sonrası eski iş sonucu atılır; yeni iş eski modeli kesmez.
"""
from __future__ import annotations

import threading
import time
from typing import Any

IPTAL_VERSION = "ses-xtts-iptal-v1-2026-11-21"

_lock = threading.RLock()
_gen: int = 0
_active_gen: int | None = None
_cancel_event = threading.Event()
_LAST: dict[str, Any] = {}


class CloneCancelled(Exception):
    """Klon işi iptal edildi."""


def iptal_enabled() -> bool:
    import os

    return os.environ.get("RUZGAR_XTTS_IPTAL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def current_gen() -> int:
    with _lock:
        return _gen


def cancel_all(*, reason: str = "client") -> dict[str, Any]:
    """Tüm aktif/bekleyen klon işlerini iptal et."""
    global _gen, _LAST
    with _lock:
        _gen += 1
        _cancel_event.set()
        _LAST = {
            "action": "cancel_all",
            "gen": _gen,
            "reason": reason,
            "ts": time.time(),
        }
        return {"ok": True, "gen": _gen, "reason": reason, "version": IPTAL_VERSION}


def begin_job() -> int:
    """Yeni klon işi başlat; önceki iptal bayrağını temizle (bu gen için)."""
    global _active_gen, _LAST
    with _lock:
        token = _gen
        _active_gen = token
        _cancel_event.clear()
        _LAST = {"action": "begin", "gen": token, "ts": time.time()}
        return token


def end_job(token: int) -> None:
    global _active_gen
    with _lock:
        if _active_gen == token:
            _active_gen = None


def is_cancelled(token: int | None = None) -> bool:
    if not iptal_enabled():
        return False
    with _lock:
        if token is None:
            return _cancel_event.is_set()
        return token != _gen or _cancel_event.is_set()


def check(token: int) -> None:
    """İptalse CloneCancelled fırlat."""
    if is_cancelled(token):
        raise CloneCancelled(f"klon iptal gen={token} current={_gen}")


def snapshot() -> dict[str, Any]:
    with _lock:
        return {
            "version": IPTAL_VERSION,
            "enabled": iptal_enabled(),
            "gen": _gen,
            "active_gen": _active_gen,
            "cancel_flag": _cancel_event.is_set(),
            "last": dict(_LAST),
        }
