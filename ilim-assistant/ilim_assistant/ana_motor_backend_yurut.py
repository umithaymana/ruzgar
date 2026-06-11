# Created by Ümit & Gökçenur
"""Ana Motor Faz W — tek sohbetten backend motor yürütme (merkezi köprü)."""

from __future__ import annotations

import os
from typing import Any

FAZ_W_VERSION = "ana-motor-backend-yurut-w1-2026-06-10"


def backend_yurut_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_BACKEND_YURUT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def resolve_motor_dispatch_kind(motor_id: str) -> str | None:
    """motor_kabiliyetleri.json dispatch alanı."""
    mid = (motor_id or "").strip().lower()
    if mid == "okuma":
        mid = "mimar"
    try:
        from ilim_assistant.motorlar.motor_kabiliyetleri import motor_capability

        spec = motor_capability(mid)
        if spec:
            return str(spec.get("dispatch") or "").strip() or None
    except Exception:
        pass
    return None


def _run_w_extensions(
    message: str,
    target: str,
    *,
    workspace_root: str | None = None,
) -> dict[str, Any] | None:
    mid = (target or "").strip().lower()
    if mid == "okuma":
        mid = "mimar"

    if mid == "tercume":
        from ilim_assistant.ana_motor_tercume_yurut import maybe_run_instant_translate

        out = maybe_run_instant_translate(message)
        if out.get("handled") and out.get("reply"):
            return out
        if out.get("error"):
            return out

    if mid == "video":
        from ilim_assistant.ana_motor_video_bilgi import maybe_video_url_info

        out = maybe_video_url_info(message)
        if out.get("handled") and out.get("reply"):
            return out
        if out.get("error"):
            return out
        try:
            from ilim_assistant.motorlar.video_faz84 import maybe_instant_faz84

            v84 = maybe_instant_faz84(message, workspace_root)
            if v84:
                return {
                    "ok": True,
                    "handled": True,
                    "reply": v84,
                    "channel": "video_faz84",
                }
        except Exception:
            pass

    return None


def execute_backend_motor(
    message: str,
    target: str,
    *,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    """Hedef motorda backend anında yürütme — panel/sekme değiştirmeden."""
    if not backend_yurut_enabled():
        return {
            "ok": True,
            "handled": False,
            "reason": "backend_yurut_disabled",
            "version": FAZ_W_VERSION,
        }

    mid = (target or "").strip().lower()
    if mid == "okuma":
        mid = "mimar"
    raw = (message or "").strip()
    if not raw or not mid or mid == "genel":
        return {"ok": True, "handled": False, "reason": "invalid_target", "version": FAZ_W_VERSION}

    dispatch = resolve_motor_dispatch_kind(mid)
    meta: dict[str, Any] = {
        "target": mid,
        "dispatch": dispatch,
        "version": FAZ_W_VERSION,
    }

    ext = _run_w_extensions(raw, mid, workspace_root=workspace_root)
    if ext and ext.get("handled") and ext.get("reply"):
        meta["channel"] = ext.get("channel")
        reply = str(ext.get("reply"))
        try:
            from ilim_assistant.ruzgar_orkestrasyon_faz_c import polish_motor_reply

            reply = polish_motor_reply(
                reply,
                target=mid,
                channel=str(ext.get("channel") or ""),
            )
        except Exception:
            pass
        return {
            "ok": True,
            "handled": True,
            "instant": True,
            "reply": reply,
            "target": mid,
            "meta": meta,
        }
    if ext and ext.get("error"):
        return {
            "ok": False,
            "handled": False,
            "error": str(ext.get("error")),
            "target": mid,
            "meta": meta,
        }

    try:
        from ilim_assistant.motorlar.ana_motor_hub_faz76 import (
            maybe_motor_instant_for_target,
            motor_label,
        )

        reply, hub_meta = maybe_motor_instant_for_target(
            raw, mid, workspace_root=workspace_root
        )
        if hub_meta:
            meta.update(hub_meta)
        if reply:
            meta["channel"] = meta.get("channel") or "hub_instant"
            try:
                from ilim_assistant.ruzgar_orkestrasyon_faz_c import polish_motor_reply

                reply = polish_motor_reply(
                    reply,
                    target=mid,
                    channel=str(meta.get("channel") or ""),
                )
            except Exception:
                pass
            return {
                "ok": True,
                "handled": True,
                "instant": True,
                "reply": reply,
                "target": mid,
                "target_label": motor_label(mid),
                "meta": meta,
            }
    except Exception as exc:
        return {
            "ok": False,
            "handled": False,
            "error": str(exc)[:200],
            "target": mid,
            "meta": meta,
        }

    return {
        "ok": True,
        "handled": False,
        "reason": "no_backend_handler",
        "target": mid,
        "meta": meta,
    }


def try_backend_before_delegate(
    message: str,
    target: str,
    *,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    """Hub delege öncesi: backend yürütme dene."""
    return execute_backend_motor(message, target, workspace_root=workspace_root)
