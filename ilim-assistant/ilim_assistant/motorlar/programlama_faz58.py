# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 58: Git entegrasyonu (read-only+).

- git status / git diff --stat preset (Faz 15/43)
- Patch öncesi/sonrası diff özeti → LLM bağlamı
- Atölye «Son değişiklikler» şeridi (API)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

FAZ58_VERSION = "programlama-faz58-v1-2026-05-26"
_LAST_SNAP_KEY = "faz58_last_git"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ58", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz58_enabled() -> bool:
    return _enabled()


def gather_scope_git(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
) -> dict[str, Any]:
    """Faz 17 snapshot — kapsam bazlı."""
    try:
        from ilim_assistant.motorlar.programlama_faz17 import gather_git_snapshot

        return gather_git_snapshot(workspace_root, scope_rel=scope_rel)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120], "scope_rel": scope_rel}


def run_git_preset(
    workspace_root: str | Path | None,
    preset: str,
    *,
    scope_rel: str,
) -> dict[str, Any]:
    """git_status | git_diff | git_diff_stat preset."""
    pid = (preset or "").strip().lower()
    if pid == "git_diff_stat":
        pid = "git_diff"
    try:
        from ilim_assistant.motorlar.programlama_faz43 import run_terminal_v3

        return run_terminal_v3(
            workspace_root,
            pid,
            scope_rel=scope_rel,
            message=pid,
        )
    except Exception:
        try:
            from ilim_assistant.motorlar.programlama_faz15 import run_terminal_preset

            return run_terminal_preset(workspace_root, pid, scope_rel=scope_rel)
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:120]}


def _short_diff_lines(snap: dict[str, Any], *, limit: int = 8) -> list[str]:
    ds = str((snap.get("diff_stat") or {}).get("output") or "").strip()
    if not ds:
        ds = str((snap.get("diff_cached_stat") or {}).get("output") or "").strip()
    lines = [ln.strip() for ln in ds.splitlines() if ln.strip()]
    return lines[:limit]


def build_git_strip_summary(snap: dict[str, Any]) -> dict[str, Any]:
    """Atölye şeridi — kısa özet."""
    if not snap.get("ok"):
        return {
            "ok": False,
            "error": snap.get("error") or "git yok",
            "scope_rel": snap.get("scope_rel") or "",
        }
    files = _short_diff_lines(snap)
    st_out = str((snap.get("status") or {}).get("output") or "").strip()
    untracked = sum(1 for ln in st_out.splitlines() if ln.startswith("??"))
    modified = sum(
        1
        for ln in st_out.splitlines()
        if ln and not ln.startswith("##") and not ln.startswith("??")
    )
    return {
        "ok": True,
        "scope_rel": snap.get("scope_rel") or "",
        "branch": snap.get("branch") or "",
        "has_changes": bool(snap.get("has_changes")),
        "file_lines": files,
        "modified_count": modified,
        "untracked_count": untracked,
        "summary": (
            f"{len(files)} dosya özeti"
            if files
            else ("değişiklik yok" if not snap.get("has_changes") else "değişiklik var")
        ),
        "version": FAZ58_VERSION,
    }


def build_llm_git_context_block(
    snap: dict[str, Any],
    *,
    phase: str = "before",
    prior_snap: dict[str, Any] | None = None,
) -> str:
    """Patch öncesi/sonrası LLM bloğu."""
    if not _enabled() or not snap.get("ok"):
        return ""
    phase_l = (phase or "before").strip().lower()
    title = "PATCH ÖNCESİ" if phase_l == "before" else "PATCH SONRASI"
    lines = [
        f"[GIT ÖZET — Faz 58 — {title}]",
        f"Kapsam: `{snap.get('scope_rel')}` · dal: `{snap.get('branch') or '?'}`",
    ]
    for ln in _short_diff_lines(snap, limit=10):
        lines.append(f"  · {ln}")
    st = str((snap.get("status") or {}).get("output") or "").strip()
    if st and not _short_diff_lines(snap):
        for ln in st.splitlines()[:6]:
            if ln.strip() and not ln.startswith("##"):
                lines.append(f"  · {ln.strip()[:100]}")
    if prior_snap and prior_snap.get("ok") and phase_l == "after":
        before = set(_short_diff_lines(prior_snap, limit=20))
        after = set(_short_diff_lines(snap, limit=20))
        new_lines = sorted(after - before)
        if new_lines:
            lines.append("Bu turda yeni diff satırları:")
            for ln in new_lines[:6]:
                lines.append(f"  + {ln}")
    lines.append(f"({FAZ58_VERSION})")
    return "\n".join(lines)


def augment_turn_with_git_context(
    base_message: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
) -> str:
    if not _enabled():
        return base_message
    snap = gather_scope_git(workspace_root, scope_rel=scope_rel)
    block = build_llm_git_context_block(snap, phase="before")
    if not block:
        return base_message
    return base_message.rstrip() + "\n\n" + block


def record_patch_git_delta(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    pre_snap: dict[str, Any] | None,
) -> dict[str, Any]:
    """Patch sonrası snapshot + agent state."""
    post = gather_scope_git(workspace_root, scope_rel=scope_rel)
    delta = {
        "ok": bool(post.get("ok")),
        "scope_rel": scope_rel,
        "pre": pre_snap,
        "post": post,
        "strip": build_git_strip_summary(post),
        "llm_block": build_llm_git_context_block(
            post, phase="after", prior_snap=pre_snap
        ),
        "ts": time.time(),
        "version": FAZ58_VERSION,
    }
    try:
        from ilim_assistant.motorlar.programlama_faz14 import (
            load_agent_state,
            save_agent_state,
        )

        st = load_agent_state(workspace_root)
        save_agent_state(
            workspace_root,
            {**st, _LAST_SNAP_KEY: delta},
        )
    except Exception:
        pass
    return delta


def load_last_git_delta(
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    try:
        from ilim_assistant.motorlar.programlama_faz14 import load_agent_state

        st = load_agent_state(workspace_root)
        raw = st.get(_LAST_SNAP_KEY)
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None


def build_git_changes_api_payload(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
) -> dict[str, Any]:
    scope = scope_rel
    if not scope:
        try:
            from ilim_assistant.motorlar.programlama_motoru import resolve_scope_rel

            scope = resolve_scope_rel(
                workspace_root, active_file=active_file, message=""
            )
        except Exception:
            scope = None
    if not scope:
        return {"ok": False, "error": "scope gerekli", "version": FAZ58_VERSION}
    snap = gather_scope_git(workspace_root, scope_rel=scope)
    strip = build_git_strip_summary(snap)
    last = load_last_git_delta(workspace_root)
    return {
        "ok": bool(snap.get("ok")),
        "scope_rel": scope,
        "snapshot": {
            "branch": snap.get("branch"),
            "has_changes": snap.get("has_changes"),
            "status_preview": str((snap.get("status") or {}).get("output") or "")[:800],
            "diff_stat_preview": str((snap.get("diff_stat") or {}).get("output") or "")[:1200],
        },
        "strip": strip,
        "last_patch_delta": last,
        "version": FAZ58_VERSION,
    }


def faz58_directive() -> str:
    return (
        "[GIT — Faz 58]\n"
        "read-only: git status · git diff --stat · patch öncesi/sonrası özet LLM'e.\n"
        "Kapat: RUZGAR_FAZ58=0\n"
    )
