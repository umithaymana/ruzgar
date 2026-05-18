"""İstek kapsamı pazar kanalı seçimi (desktop tarama → tool zinciri)."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any

_channels_var: ContextVar[list[str] | None] = ContextVar("hizir_pazar_kanallari", default=None)


def set_pazar_kanallari(channels: list[str] | None) -> Token:
    return _channels_var.set(channels)


def reset_pazar_kanallari(token: Token) -> None:
    _channels_var.reset(token)


def get_pazar_kanallari() -> list[str] | None:
    return _channels_var.get()


def normalize_kanal_listesi(raw: Any) -> list[str] | None:
    """None → bağlam yok (tüm kanallar). Boş liste → kullanıcı hiç kanal seçmedi."""
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None
    return [str(x).strip().lower() for x in raw if str(x).strip()]
