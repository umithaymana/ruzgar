# Created by Ümit & Gökçenur
"""Faz E3 — Ana Motor → programlama delege: çok dosya patch onay kartı."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def patch_approval_bridge_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_PATCH_APPROVAL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def should_force_patch_staging(
    *,
    delegated_from_genel: bool = False,
    wants_debug: bool = False,
    message: str = "",
) -> bool:
    """Delege / otonom debug turunda otomatik yazım yerine onay."""
    if not patch_approval_bridge_enabled():
        return False
    if delegated_from_genel or wants_debug:
        return True
    try:
        from ilim_assistant.ana_motor_otonom_debug import detect_otonom_debug_intent

        if detect_otonom_debug_intent(message):
            return True
    except Exception:
        pass
    return False


def process_turn_patches(
    reply_body: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    skip_if_debug_loop: bool = False,
    delegated_from_genel: bool = False,
    wants_debug: bool = False,
    message: str = "",
) -> dict[str, Any]:
    """Tur sonu patch — delege/debug'ta zorunlu staging + zengin kart verisi."""
    if skip_if_debug_loop:
        return {"action": "skip"}
    try:
        from ilim_assistant.motorlar.programlama_faz10 import extract_write_jobs

        if not extract_write_jobs(reply_body):
            return {"action": "none"}
    except Exception:
        return {"action": "none"}

    force_stage = should_force_patch_staging(
        delegated_from_genel=delegated_from_genel,
        wants_debug=wants_debug,
        message=message,
    )
    if force_stage:
        try:
            from ilim_assistant.motorlar.programlama_faz16 import (
                build_pending_bundle,
                stage_pending_enriched,
            )

            staged = stage_pending_enriched(
                reply_body, workspace_root, source="ana_motor_delegate"
            )
            bundle = build_pending_bundle(workspace_root)
            items = list(bundle.get("items") or staged.get("items") or [])
            counts = bundle.get("counts") or {}
            return {
                "action": "staged",
                "count": staged.get("count", len(items)),
                "items": items,
                "counts": counts,
                "paths": bundle.get("paths") or staged.get("paths") or [],
                "approval_required": True,
                "footer": (
                    "\n\n---\n**Faz E3 — Patch onay:** "
                    f"**{len(items)} dosya** atölyede bekliyor. "
                    "Dashboard kartından **Kabul/Red** veya `patch onayla`.\n"
                ),
            }
        except Exception:
            pass

    from ilim_assistant.motorlar.programlama_faz10 import process_assistant_reply_patches

    return process_assistant_reply_patches(
        reply_body,
        workspace_root,
        scope_rel=scope_rel,
        skip_if_debug_loop=skip_if_debug_loop,
    )


def build_patch_approval_card(meta: dict[str, Any]) -> dict[str, Any]:
    """UI kartı — genel modda görünür patch onay özeti."""
    if not meta or meta.get("action") not in ("staged", "applied"):
        return {"ok": False, "has_pending": False}
    items = list(meta.get("items") or [])
    applied = list(meta.get("applied") or [])
    counts = meta.get("counts") or {}
    if not items and not applied:
        return {"ok": False, "has_pending": False}
    paths = [str(it.get("path") or "") for it in items if it.get("path")]
    return {
        "ok": True,
        "has_pending": meta.get("action") == "staged" and bool(items),
        "action": meta.get("action"),
        "count": meta.get("count") or len(items) or len(applied),
        "paths_preview": paths[:12],
        "counts": counts,
        "approval_required": bool(meta.get("approval_required")),
        "hint": (
            "Dosya bazlı Kabul/Red — sonra «Uygula» veya patch onayla"
            if meta.get("action") == "staged"
            else "Patch uygulandı"
        ),
    }
