# Created by Ümit & Gökçenur
"""
Programlama motoru → Merkezi Zihin Havuzu köprüsü.

Başarılı yazma/patch ve verify sonuçlarını motor_kv + shared_context'e kaydeder.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

PROG_HAVUZ_BRIDGE_VERSION = "programlama-havuz-bridge-v1-2026-06-15"
_MOTOR = "programlama"


def havuz_bridge_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_HAVUZ_BRIDGE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _get_havuz():
    try:
        from ilim_assistant.motorlar.merkezi_zihin_havuzu import get_havuz

        return get_havuz()
    except Exception:
        return None


def record_tool_outcome(
    workspace_root: str | Path | None,
    *,
    writes: list[str] | None = None,
    patches: list[str] | None = None,
    pytest_ok: bool | None = None,
    goal: str = "",
    scope_rel: str = "",
) -> None:
    """Başarılı araç çıktısını havuza yaz."""
    if not havuz_bridge_enabled():
        return
    havuz = _get_havuz()
    if havuz is None:
        return
    payload: dict[str, Any] = {
        "ts": time.time(),
        "writes": list(writes or [])[:20],
        "patches": list(patches or [])[:20],
        "pytest_ok": pytest_ok,
        "goal": (goal or "")[:500],
        "scope_rel": (scope_rel or "")[:200],
        "version": PROG_HAVUZ_BRIDGE_VERSION,
    }
    try:
        havuz.motor_set(_MOTOR, "last_tool_outcome", payload)
        if writes or patches:
            havuz.motor_set(_MOTOR, f"patch:{int(time.time())}", payload)
        if goal and scope_rel:
            havuz.publish_shared(
                "programlama",
                f"task:{scope_rel.replace('/', ':')[:100]}",
                (
                    f"Hedef: {goal[:300]} · yazılan: {len(writes or [])} · "
                    f"patch: {len(patches or [])}"
                ),
                priority=5,
                ttl_sec=86400 * 7,
            )
    except Exception:
        pass


def record_root_cause_hint(
    workspace_root: str | Path | None,
    *,
    label: str,
    scope_rel: str = "",
    snippet: str = "",
) -> None:
    if not havuz_bridge_enabled():
        return
    havuz = _get_havuz()
    if havuz is None:
        return
    try:
        havuz.motor_set(
            _MOTOR,
            f"root_cause:{label[:40]}",
            {
                "label": label[:80],
                "scope_rel": scope_rel[:200],
                "snippet": (snippet or "")[:2000],
                "ts": time.time(),
            },
        )
    except Exception:
        pass


def compact_havuz_context_block(workspace_root: str | Path | None) -> str:
    """LLM bağlamına kısa son işlem özeti (Ana motor aktif okumaya delege)."""
    try:
        from ilim_assistant.ana_motor_programlama_havuz import (
            build_programlama_havuz_context_block,
        )

        return build_programlama_havuz_context_block(
            mode_norm="programlama",
            workspace_root=str(workspace_root) if workspace_root is not None else None,
            compact=True,
        )
    except Exception:
        return ""
