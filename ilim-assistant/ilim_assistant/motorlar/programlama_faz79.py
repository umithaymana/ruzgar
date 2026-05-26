# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 79: Ana Motor handoff v3 (E4).

Faz 55 paketine git özeti, hub meta, son başarısız görevler, aktif dosya.
"""

from __future__ import annotations

import os
from typing import Any

FAZ79_VERSION = "programlama-faz79-v1-2026-05-26"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ79", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz79_enabled() -> bool:
    return _enabled()


def _git_summary(workspace_root: str | None, scope_rel: str | None) -> str:
    if not scope_rel:
        return ""
    try:
        from ilim_assistant.motorlar.programlama_faz58 import format_git_changes_for_llm

        block = format_git_changes_for_llm(workspace_root, scope_rel=scope_rel)
        if block and len(block) > 40:
            return block[:2000]
    except Exception:
        pass
    return ""


def enrich_handoff_v3(
    packet: dict[str, Any],
    message: str,
    workspace_root: str | None,
    *,
    active_file: str | None = None,
    hub_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not _enabled() or not packet.get("ok"):
        return packet
    parts: list[str] = [str(packet.get("packet_text") or "")]
    scope = packet.get("scope_rel")

    if active_file:
        parts.append(f"Aktif dosya: `{active_file}`")

    if hub_meta:
        winner = hub_meta.get("winner") or hub_meta.get("reason")
        if winner:
            parts.append(f"Hub yönlendirme: `{winner}` ({hub_meta.get('reason', '')})")

    git_blk = _git_summary(workspace_root, scope)
    if git_blk:
        parts.append("**Git (son değişiklikler):**\n" + git_blk)

    try:
        from ilim_assistant.motorlar.programlama_faz78 import (
            wants_core_scope,
            core_scope_directive,
            resolve_core_scope_rel,
        )

        if wants_core_scope(message):
            cs = core_scope_directive(message)
            if cs:
                parts.append(cs)
            packet["scope_rel"] = resolve_core_scope_rel(message)
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz55 import compute_task_stats

        stats = compute_task_stats(workspace_root, window_days=7)
        fails = [
            r
            for r in (stats.get("recent") or [])
            if not r.get("success")
        ][-3:]
        if fails:
            lines = ["**Son başarısız görevler (7 gün):**"]
            for r in fails:
                lines.append(
                    f"· `{r.get('scope_rel')}` — {str(r.get('detail') or 'verify')[:80]}"
                )
            parts.append("\n".join(lines))
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz80 import mega_refactor_directive

        mr = mega_refactor_directive(message)
        if mr:
            parts.append(mr)
    except Exception:
        pass

    packet["packet_text"] = "\n\n".join(p for p in parts if p.strip())
    packet["handoff_v3"] = True
    packet["version_v3"] = FAZ79_VERSION
    return packet


def build_handoff_packet_v3(
    message: str,
    workspace_root: str | None,
    *,
    active_file: str | None = None,
    hub_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz55 import build_handoff_packet

    base = build_handoff_packet(
        message, workspace_root, active_file=active_file
    )
    return enrich_handoff_v3(
        base,
        message,
        workspace_root,
        active_file=active_file,
        hub_meta=hub_meta,
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz79"] = faz79_enabled()
    return out
