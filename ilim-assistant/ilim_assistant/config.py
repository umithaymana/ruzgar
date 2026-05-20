# Created by Ümit & Gökçenur
"""
Rüzgar kalıcı yapılandırma — GLOBAL_API_KEY (Gemini) tek kaynak.

`.env` veya ortamdan yüklenir; tüm Gemini alias'larına senkron edilir.
"""

from __future__ import annotations

import os

from ilim_assistant.defaults import DEFAULT_GEMINI_MODEL

_KEY_ALIASES = (
    "GLOBAL_API_KEY",
    "GOOGLE_GEMINI_API_KEY",
    "GEMINI_API_KEY",
    "RUZGAR_GEMINI_API_KEY",
)


def _bootstrap() -> None:
    try:
        from ilim_assistant.env_bootstrap import ensure_ruzgar_env, sync_global_api_key_aliases

        ensure_ruzgar_env()
        sync_global_api_key_aliases()
    except Exception:
        pass


_bootstrap()


def global_api_key() -> str:
    """Kalıcı Gemini anahtarı (GLOBAL_API_KEY öncelikli)."""
    for name in _KEY_ALIASES:
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return ""


def apply_global_api_key_to_runtime() -> bool:
    """Anahtarı tüm runtime alias'larına yazar; başarılıysa True."""
    key = global_api_key()
    if not key:
        return False
    for name in _KEY_ALIASES:
        os.environ[name] = key
    return True


def gemini_model() -> str:
    return (os.environ.get("RUZGAR_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip()


def gemini_ready() -> bool:
    return bool(global_api_key())


def config_snapshot() -> dict[str, str | bool]:
    key = global_api_key()
    return {
        "global_api_key_set": bool(key),
        "global_api_key_source": os.environ.get("RUZGAR_ENV_LOADED_FROM", ""),
        "gemini_model": gemini_model(),
        "super_brain": os.environ.get("RUZGAR_SUPER_BRAIN", "1"),
    }
