# Created by Ümit & Gökçenur
"""
Motor B / S2 — sesli sohbet durum iskeleti.

Durumlar: idle → listening → thinking → speaking → idle
Barge-in: speaking iken dinleme isteği → listening (konuşma kesilir istemci tarafında).

Takılı durum koruması (health/get/set okurken otomatik):
  listening → RUZGAR_SES_LISTENING_IDLE_SEC (varsayılan 45)
  thinking  → RUZGAR_SES_THINKING_IDLE_SEC  (varsayılan 180)
  speaking  → RUZGAR_SES_SPEAKING_IDLE_SEC  (varsayılan 300)
  0 veya negatif = o durum için koruma kapalı

Kapat: RUZGAR_SES_SOHBET_DURUM=0
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

VERSION = "ses-sohbet-durum-v1.2-2026-11-22"
_STATES = ("idle", "listening", "thinking", "speaking")
_lock = threading.Lock()
_state = "idle"
_updated = 0.0
_meta: dict[str, Any] = {}

# Durum → (env adı, varsayılan sn)
_IDLE_TIMEOUTS: dict[str, tuple[str, float]] = {
    "listening": ("RUZGAR_SES_LISTENING_IDLE_SEC", 45.0),
    "thinking": ("RUZGAR_SES_THINKING_IDLE_SEC", 180.0),
    "speaking": ("RUZGAR_SES_SPEAKING_IDLE_SEC", 300.0),
}


def enabled() -> bool:
    return os.environ.get("RUZGAR_SES_SOHBET_DURUM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def listening_idle_sec() -> float:
    """Takılı listening → idle süresi (sn). 0 veya negatif = koruma kapalı."""
    return _env_float(*_IDLE_TIMEOUTS["listening"])


def thinking_idle_sec() -> float:
    return _env_float(*_IDLE_TIMEOUTS["thinking"])


def speaking_idle_sec() -> float:
    return _env_float(*_IDLE_TIMEOUTS["speaking"])


def idle_timeout_for(state: str) -> float:
    spec = _IDLE_TIMEOUTS.get((state or "").strip().lower())
    if not spec:
        return 0.0
    return _env_float(*spec)


def _apply_stuck_idle_locked(now: float | None = None) -> bool:
    """Lock altında: non-idle durum uzun sürdüyse idle'a çek. True = sıfırlandı."""
    global _state, _updated, _meta
    if _state == "idle" or _state not in _IDLE_TIMEOUTS:
        return False
    timeout = idle_timeout_for(_state)
    if timeout <= 0:
        return False
    t = time.time() if now is None else now
    if _updated <= 0 or (t - _updated) < timeout:
        return False
    prev = _state
    prev_meta = dict(_meta)
    keep = {
        k: v
        for k, v in prev_meta.items()
        if k in ("barge_in",) and v
    }
    _meta = {
        "idle_timeout": True,
        "from": prev,
        "note": f"{prev}-idle",
        "stuck_sec": round(t - _updated, 1),
        **keep,
    }
    _state = "idle"
    _updated = t
    return True


# Geriye uyum — eski isim
_apply_listening_idle_locked = _apply_stuck_idle_locked


def public_status() -> dict[str, Any]:
    now = time.time()
    with _lock:
        reset = _apply_stuck_idle_locked(now)
        return {
            "enabled": enabled(),
            "version": VERSION,
            "state": _state,
            "updated_at": _updated,
            "meta": dict(_meta),
            "states": list(_STATES),
            "listening_idle_sec": listening_idle_sec(),
            "thinking_idle_sec": thinking_idle_sec(),
            "speaking_idle_sec": speaking_idle_sec(),
            "idle_reset": bool(reset),
            "note": (
                "STT=/api/stt · TTS=/api/tts · barge-in: speaking→listening · "
                "stuck listening/thinking/speaking→idle"
            ),
        }


def get_state() -> str:
    with _lock:
        _apply_stuck_idle_locked()
        return _state


def set_state(new_state: str, **meta: Any) -> dict[str, Any]:
    global _state, _updated, _meta
    if not enabled():
        return {"ok": False, "error": "kapalı"}
    ns = (new_state or "").strip().lower()
    if ns not in _STATES:
        return {"ok": False, "error": f"geçersiz durum: {new_state}"}
    with _lock:
        # Okumadan önce takılı durum temizliği (temiz geçiş)
        _apply_stuck_idle_locked()
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
    return set_state("idle", note="reset")
