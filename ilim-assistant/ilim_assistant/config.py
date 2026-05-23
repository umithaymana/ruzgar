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


def ollama_only_mode() -> bool:
    """Yalnızca yerel Ollama — bulut (Gemini/Groq) kapalı."""
    return os.environ.get("RUZGAR_OLLAMA_ONLY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def gemini_disabled() -> bool:
    """Gemini kapalı — Groq/Ollama öncelik (yavaşlama / kota için)."""
    if ollama_only_mode():
        return True
    return os.environ.get("RUZGAR_DISABLE_GEMINI", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def groq_disabled() -> bool:
    if ollama_only_mode():
        return True
    return os.environ.get("RUZGAR_DISABLE_GROQ", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def suppress_groq_runtime_keys() -> None:
    if not groq_disabled():
        return
    for name in ("GROQ_API_KEY", "GROQ_API_BASE", "OPENAI_COMPAT_BASE"):
        if name == "OPENAI_COMPAT_BASE":
            base = (os.environ.get(name) or "").strip()
            if "groq.com" in base:
                os.environ.pop(name, None)
            continue
        os.environ.pop(name, None)


def suppress_cloud_runtime_keys() -> None:
    """Bulut anahtarlarını kaldır (Gemini + Groq)."""
    suppress_gemini_runtime_keys()
    suppress_groq_runtime_keys()


def suppress_gemini_runtime_keys() -> None:
    """Devre dışıyken yüklü Gemini anahtarlarını ortamdan kaldırır."""
    if not gemini_disabled():
        return
    for name in _KEY_ALIASES:
        os.environ.pop(name, None)
    os.environ["RUZGAR_GEMINI_DAEMON"] = "0"


def global_api_key() -> str:
    """Kalıcı Gemini anahtarı (GLOBAL_API_KEY öncelikli)."""
    if gemini_disabled():
        return ""
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
    return not gemini_disabled() and bool(global_api_key())


def config_snapshot() -> dict[str, str | bool]:
    key = global_api_key()
    return {
        "global_api_key_set": bool(key),
        "global_api_key_source": os.environ.get("RUZGAR_ENV_LOADED_FROM", ""),
        "gemini_model": gemini_model(),
        "super_brain": os.environ.get("RUZGAR_SUPER_BRAIN", "1"),
    }
