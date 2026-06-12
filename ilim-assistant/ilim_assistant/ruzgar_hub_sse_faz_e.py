# Created by Ümit & Gökçenur
"""
Ana Motor — Hub SSE Faz E (2026-06-11).

Tüm yardımcı motorlar sunucu SSE akışında; video sinema köprüsü (motor_action).
"""

from __future__ import annotations

import os
from typing import Any

HUB_SSE_FAZ_E_VERSION = "hub-sse-faz-e-v1-2026-06-11"

FASE_E_MOTORS: frozenset[str] = frozenset(
    {"tercume", "video", "programlama", "ses", "hafiza", "mimar", "hizir", "okuma"}
)


def hub_sse_faz_e_enabled() -> bool:
    return os.environ.get("RUZGAR_HUB_SSE_FAZ_E", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def normalize_hub_motor_id(target: str) -> str:
    mid = (target or "").strip().lower()
    if mid == "okuma":
        return "mimar"
    return mid


def get_server_stream_motors() -> frozenset[str]:
    try:
        from ilim_assistant.ruzgar_hub_sse_faz_d import (
            SERVER_STREAM_MOTORS,
            hub_sse_faz_d_enabled,
        )

        if hub_sse_faz_e_enabled():
            return FASE_E_MOTORS
        if hub_sse_faz_d_enabled():
            return SERVER_STREAM_MOTORS
    except Exception:
        pass
    return FASE_E_MOTORS if hub_sse_faz_e_enabled() else frozenset()


def should_route_via_server_stream(target: str) -> bool:
    try:
        from ilim_assistant.ruzgar_hub_sse_faz_d import hub_sse_faz_d_enabled
    except Exception:
        return False
    if not hub_sse_faz_d_enabled() and not hub_sse_faz_e_enabled():
        return False
    mid = normalize_hub_motor_id(target)
    return mid in get_server_stream_motors()


def detect_video_motor_action(
    message: str,
    hub: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Sunucu metin yanıtı yetmezse istemci Video atölyesini tetikle."""
    if not hub_sse_faz_e_enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None
    hub = hub or {}
    if hub.get("og_direct"):
        try:
            from ilim_assistant.motorlar.ana_motor_hub_faz76 import is_video_download_request

            if is_video_download_request(raw):
                return {"motor": "video", "action": "atolye", "message": raw}
        except Exception:
            pass
        return None
    target = normalize_hub_motor_id(
        str(hub.get("mode") or (hub.get("hub_meta") or {}).get("target") or "")
    )
    try:
        from ilim_assistant.motorlar.ana_motor_hub_faz76 import is_video_workflow_request

        if target == "video" or is_video_workflow_request(raw):
            return {"motor": "video", "action": "atolye", "message": raw}
    except Exception:
        if target == "video":
            return {"motor": "video", "action": "atolye", "message": raw}
    return None


def enrich_hub_orchestra(
    orch: dict[str, Any],
    *,
    message: str,
    hub: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(orch or {})
    action = detect_video_motor_action(message, hub)
    if action:
        out["motor_action"] = action
        out.setdefault("hub", {})["action"] = action.get("action")
    if hub_sse_faz_e_enabled():
        out["hub_sse_faz_e"] = True
        out["unified_face"] = True
    return out


def hub_sse_faz_e_status() -> dict[str, object]:
    return {
        "enabled": hub_sse_faz_e_enabled(),
        "version": HUB_SSE_FAZ_E_VERSION,
        "server_stream_motors": sorted(get_server_stream_motors()),
    }
