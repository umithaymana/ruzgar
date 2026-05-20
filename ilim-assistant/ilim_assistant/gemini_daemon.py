# Created by Ümit & Gökçenur
"""
Gemini arka plan servisi — Rüzgar açıkken periyodik bağlantı kontrolü (daemon).

Kullanıcıya anahtar sormaz; config.py / .env GLOBAL_API_KEY kullanır.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

_lock = threading.Lock()
_thread: threading.Thread | None = None
_status: dict[str, Any] = {
    "running": False,
    "ok": False,
    "model": "",
    "last_ping_at": 0.0,
    "reason": "",
}


def _daemon_enabled() -> bool:
    return os.environ.get("RUZGAR_GEMINI_DAEMON", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _interval_sec() -> float:
    try:
        return max(30.0, float(os.environ.get("RUZGAR_GEMINI_DAEMON_INTERVAL_SEC", "90")))
    except ValueError:
        return 90.0


def _ping_once() -> dict[str, Any]:
    from ilim_assistant.config import apply_global_api_key_to_runtime, gemini_ready
    from ilim_assistant.llm_gemini import gemini_model_ping

    apply_global_api_key_to_runtime()
    if not gemini_ready():
        return {"ok": False, "reason": "global_api_key_missing", "model": ""}
    return gemini_model_ping()


def _loop() -> None:
    global _status
    while True:
        try:
            result = _ping_once()
            with _lock:
                _status = {
                    "running": True,
                    "ok": bool(result.get("ok")),
                    "model": str(result.get("model") or ""),
                    "last_ping_at": time.time(),
                    "reason": str(result.get("reason") or ""),
                    "status_code": result.get("status_code"),
                    "source": result.get("source", ""),
                }
                os.environ["RUZGAR_GEMINI_DAEMON_OK"] = "1" if _status["ok"] else "0"
        except Exception as exc:
            with _lock:
                _status = {
                    "running": True,
                    "ok": False,
                    "model": "",
                    "last_ping_at": time.time(),
                    "reason": str(exc)[:200],
                }
                os.environ["RUZGAR_GEMINI_DAEMON_OK"] = "0"
        time.sleep(_interval_sec())


def start_gemini_daemon() -> bool:
    """Arka plan ping thread'i (idempotent)."""
    global _thread
    if not _daemon_enabled():
        return False
    with _lock:
        if _thread is not None and _thread.is_alive():
            return True
        # İlk ping senkron — açılışta hemen bağlı görünsün
        try:
            result = _ping_once()
            _status.update(
                {
                    "running": True,
                    "ok": bool(result.get("ok")),
                    "model": str(result.get("model") or ""),
                    "last_ping_at": time.time(),
                    "reason": str(result.get("reason") or ""),
                }
            )
            os.environ["RUZGAR_GEMINI_DAEMON_OK"] = "1" if _status["ok"] else "0"
        except Exception as exc:
            _status.update(
                {
                    "running": False,
                    "ok": False,
                    "reason": str(exc)[:200],
                    "last_ping_at": time.time(),
                }
            )
        _thread = threading.Thread(
            target=_loop,
            name="ruzgar-gemini-daemon",
            daemon=True,
        )
        _thread.start()
    return True


def daemon_status() -> dict[str, Any]:
    with _lock:
        return dict(_status)
