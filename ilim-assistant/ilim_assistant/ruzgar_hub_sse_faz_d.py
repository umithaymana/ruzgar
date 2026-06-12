# Created by Ümit & Gökçenur
"""
Ana Motor — Hub SSE Faz D (2026-06-11).

Tercüme / video / programlama: istemci motor-dispatch kısayolu yerine
sunucu SSE akışı (Tek Ses + orchestra meta).
Not: Super Brain «Faz D» (bilim derin) ile karıştırılmaz.
"""

from __future__ import annotations

import os
from typing import Any

HUB_SSE_FAZ_D_VERSION = "hub-sse-faz-d-v1-2026-06-11"

SERVER_STREAM_MOTORS: frozenset[str] = frozenset({"tercume", "video", "programlama"})


def hub_sse_faz_d_enabled() -> bool:
    return os.environ.get("RUZGAR_HUB_SSE_FAZ_D", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def should_route_via_server_stream(target: str) -> bool:
    try:
        from ilim_assistant.ruzgar_hub_sse_faz_e import should_route_via_server_stream as _e

        return _e(target)
    except Exception:
        pass
    if not hub_sse_faz_d_enabled():
        return False
    return (target or "").strip().lower() in SERVER_STREAM_MOTORS


def try_hub_sse_instant(
    message: str,
    *,
    motor_flags: dict[str, bool] | None = None,
    workspace_root: str | None = None,
    orchestration_out: dict[str, Any] | None = None,
    question_plan: Any | None = None,
) -> tuple[str | None, dict[str, Any]]:
    """
    apply_genel_hub_routing + Faz C polish/enrich.
    Dönüş: (og_direct, orchestra) — og_direct yoksa (None, orch).
    """
    orch = dict(orchestration_out or {})
    if not hub_sse_faz_d_enabled():
        return None, orch
    raw = (message or "").strip()
    if not raw:
        return None, orch
    try:
        from ilim_assistant.motorlar.ana_motor_hub_faz76 import apply_genel_hub_routing
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import (
            enrich_orchestra_motor,
            polish_motor_reply,
        )

        hub = apply_genel_hub_routing(
            raw,
            motor_flags=motor_flags,
            workspace_root=workspace_root,
        )
        og = hub.get("og_direct")
        if not og:
            return None, orch

        _hm = dict(hub.get("hub_meta") or {})
        orch["hub_delegate"] = _hm
        _tgt = str(orch.get("hub_target") or _hm.get("target") or hub.get("mode") or "").strip()
        if _tgt:
            orch["hub_target"] = _tgt
        _ch = str(_hm.get("channel") or "").strip()
        og_out = polish_motor_reply(str(og), target=_tgt or "genel", channel=_ch)
        if _tgt:
            orch = enrich_orchestra_motor(
                orch,
                target=_tgt,
                channel=_ch,
                plan=question_plan,
            )
        try:
            from ilim_assistant.ruzgar_hub_sse_faz_e import enrich_hub_orchestra

            orch = enrich_hub_orchestra(orch, message=raw, hub=hub)
        except Exception:
            pass
        return og_out, orch
    except Exception:
        return None, orch


def hub_sse_status() -> dict[str, object]:
    motors = sorted(SERVER_STREAM_MOTORS)
    out: dict[str, object] = {
        "enabled": hub_sse_faz_d_enabled(),
        "version": HUB_SSE_FAZ_D_VERSION,
        "server_stream_motors": motors,
    }
    try:
        from ilim_assistant.ruzgar_hub_sse_faz_e import hub_sse_faz_e_status

        out["faz_e"] = hub_sse_faz_e_status()
        fe = hub_sse_faz_e_status()
        if fe.get("enabled"):
            out["server_stream_motors"] = fe.get("server_stream_motors")
    except Exception:
        pass
    return out
