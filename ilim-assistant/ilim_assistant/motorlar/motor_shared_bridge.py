# -*- coding: utf-8 -*-
"""Minimal publish_shared köprüsü — ses/tercüme/mimar/okuma/hafıza (Faz 5).

Programlama+video seviyesinde zorunlu değil; tutarlılık için hafif not.
Kapat: RUZGAR_MOTOR_SHARED_BRIDGE=0
"""
from __future__ import annotations

import os
from typing import Optional


def bridge_enabled() -> bool:
    return os.environ.get("RUZGAR_MOTOR_SHARED_BRIDGE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def publish_motor_note(
    source_motor: str,
    key: str,
    value: str,
    *,
    priority: int = 2,
    ttl_sec: int = 86400,
) -> bool:
    if not bridge_enabled():
        return False
    text = (value or "").strip()
    if not text:
        return False
    try:
        from ilim_assistant.motorlar.merkezi_zihin_havuzu import get_havuz

        havuz = get_havuz()
        if havuz is None:
            return False
        havuz.publish_shared(
            source_motor or "sistem",
            key or "last_turn",
            text[:800],
            priority=priority,
            ttl_sec=ttl_sec,
        )
        return True
    except Exception:
        return False
