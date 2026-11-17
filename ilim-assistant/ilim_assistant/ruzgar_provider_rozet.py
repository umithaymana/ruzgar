# Created by Ümit & Gökçenur
"""F4.2 — tur provider rozeti (yerel / bulut / raftan). LLM bağımlılığı yok."""

from __future__ import annotations

import contextvars

_last_brain_profile: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ruzgar_last_brain_profile", default=""
)
_last_brain_kind: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ruzgar_last_brain_kind", default=""
)


def note_brain_used(profile_id: str, *, provider: str = "") -> None:
    """Son başarılı beyin profilini tur bağlamına yaz."""
    pid = (profile_id or "").strip()
    if not pid:
        return
    _last_brain_profile.set(pid)
    kind = (provider or "").strip().lower()
    if not kind:
        if pid in ("gemini",):
            kind = "gemini"
        elif pid in ("groq",):
            kind = "groq"
        elif pid in ("denge", "hizli", "denge_yeni", "kod", "denge70"):
            kind = "ollama"
        elif pid in ("raftan", "kutuphane_extractive", "kutuphane"):
            kind = "library"
        else:
            kind = "other"
    _last_brain_kind.set(kind)


def last_brain_profile() -> str:
    return (_last_brain_profile.get() or "").strip()


def last_brain_kind() -> str:
    return (_last_brain_kind.get() or "").strip()


def provider_rozet_label(
    profile_or_provider: str = "",
    *,
    raftan: bool = False,
    extractive: bool = False,
) -> str:
    """«Bu tur yerel / bulut / raftan» rozeti."""
    if extractive or raftan:
        return "raftan"
    p = (profile_or_provider or last_brain_profile() or "").strip().lower()
    if p in (
        "kutuphane_extractive",
        "kutuphane",
        "raftan",
        "library",
        "rag",
        "miss_kutuphane",
    ):
        return "raftan"
    if p in ("denge", "hizli", "denge_yeni", "kod", "denge70", "ollama", "yerel", "local"):
        return "yerel"
    if p in ("gemini", "groq", "bulut", "cloud"):
        return "bulut"
    kind = last_brain_kind()
    if kind == "ollama":
        return "yerel"
    if kind in ("gemini", "groq"):
        return "bulut"
    if kind == "library":
        return "raftan"
    return p or "bilinmiyor"
