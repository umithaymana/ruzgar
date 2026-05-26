# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 70: Ajan turunda otomatik patch (ROK).

Görev/ajan bittiğinde bekleyen patch'leri diske uygular (onay şeridi atlanır).
"""

from __future__ import annotations

import os
from typing import Any

FAZ70_VERSION = "programlama-faz70-v1-2026-05-26"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ70", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz70_enabled() -> bool:
    return _enabled()


def activate_agent_patch_mode() -> None:
    """Ajan başında — Cursor gibi doğrudan yazım."""
    if not _enabled():
        return
    os.environ["RUZGAR_FAZ10_AUTO_PATCH"] = "1"
    os.environ["RUZGAR_AGENT_AUTO_APPLY"] = "1"
    try:
        from ilim_assistant.motorlar.programlama_faz23 import enter_task_mode

        enter_task_mode()
    except Exception:
        pass


def finalize_agent_patches(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
) -> dict[str, Any]:
    """Ajan sonu — kalan pending patch'leri uygula."""
    if not _enabled():
        return {"ok": True, "skipped": True, "reason": "faz70_kapali"}
    try:
        from ilim_assistant.motorlar.programlama_faz16 import (
            apply_pending_selective,
            build_pending_bundle,
        )

        bundle = build_pending_bundle(workspace_root)
        count = int(bundle.get("count") or 0)
        if count <= 0:
            return {"ok": True, "applied": 0}
        out = apply_pending_selective(
            workspace_root,
            mode="all",
            run_verify=False,
            scope_rel=scope_rel,
        )
        out["faz70"] = True
        out["version"] = FAZ70_VERSION
        return out
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def format_finalize_report(result: dict[str, Any]) -> str:
    if result.get("skipped"):
        return ""
    if result.get("applied") == 0 and result.get("ok"):
        return ""
    applied = result.get("applied")
    n = len(applied) if isinstance(applied, list) else int(result.get("applied") or 0)
    if result.get("ok") and n > 0:
        return (
            f"Ümit abi, ajan sonunda **{n}** dosya otomatik kaydedildi (Faz 70).\n"
            f"({FAZ70_VERSION})"
        )
    if result.get("error"):
        return f"Ümit abi, otomatik patch: {result.get('error')}\n({FAZ70_VERSION})"
    return ""


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz70"] = faz70_enabled()
    return out


def faz70_directive() -> str:
    return (
        "[OTOMATİK PATCH — Faz 70]\n"
        "Kod ajanı turunda değişiklikler doğrudan diske yazılır; «patch onayla» gerekmez.\n"
        "Kapat: RUZGAR_FAZ70=0\n"
    )
