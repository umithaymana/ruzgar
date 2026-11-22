# Created by Ümit & Gökçenur
"""
Madde 1 — Ezber instant kapısı (2026-11-22 Mimar mutabakatı).

Varsayılan KAPALI: selam / nezaket / görüş / oturum karşılama / mikro-gerçek
kartları LLM veya gerçek araca düşer; sabit metin okunmaz.

Acil geri aç (eski davranış): RUZGAR_EZBER_INSTANT=1
"""

from __future__ import annotations

import os

EZBER_INSTANT_VERSION = "ruzgar-ezber-instant-v1-2026-11-22"


def ezber_instant_enabled() -> bool:
    """True yalnızca açıkça istenirse — varsayılan False."""
    return os.environ.get("RUZGAR_EZBER_INSTANT", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def ezber_instant_status() -> dict[str, object]:
    return {
        "enabled": ezber_instant_enabled(),
        "version": EZBER_INSTANT_VERSION,
        "default": False,
        "env": "RUZGAR_EZBER_INSTANT",
    }
