# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 27: editör satır içi diff.

Bekleyen patch için eski/yeni metin + unified diff (atölye API + UI).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari, repo_root

FAZ27_VERSION = "programlama-faz27-v1-2026-05-25"
_MAX_INLINE_CHARS = 14_000


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ27", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def build_inline_diff_for_path(
    workspace_root: str | Path | None,
    rel_path: str,
    *,
    new_content: str | None = None,
) -> dict[str, Any]:
    """Tek dosya için editör diff yükü."""
    if not _enabled():
        return {"ok": False, "error": "Faz 27 kapalı"}
    from ilim_assistant.motorlar.programlama_faz10 import unified_diff_text

    rel = _norm_rel(rel_path)
    if not rel:
        return {"ok": False, "error": "Dosya yolu gerekli"}

    tools = ProgramlamaAraclari(workspace_root)
    old = ""
    if tools.root is not None:
        rep = tools.read(rel, max_chars=_MAX_INLINE_CHARS)
        old = rep.content if rep.ok else ""

    new = new_content
    if new is None:
        try:
            from ilim_assistant.motorlar.programlama_faz10 import load_pending

            for j in load_pending(workspace_root).get("jobs") or []:
                if _norm_rel(str(j.get("path") or "")) == rel:
                    new = str(j.get("content") or "")
                    break
        except Exception:
            pass
    if new is None:
        new = ""

    diff = unified_diff_text(old, new, rel)
    return {
        "ok": True,
        "path": rel,
        "old_text": old[:_MAX_INLINE_CHARS],
        "new_text": new[:_MAX_INLINE_CHARS],
        "diff": diff[:_MAX_INLINE_CHARS],
        "is_new_file": not (old or "").strip(),
        "old_lines": len(old.splitlines()),
        "new_lines": len(new.splitlines()),
        "version": FAZ27_VERSION,
    }


def enrich_pending_with_inline(
    workspace_root: str | Path | None,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Pending liste öğelerine kısa inline önizleme alanları."""
    if not _enabled() or not items:
        return items
    out: list[dict[str, Any]] = []
    for it in items:
        row = dict(it)
        rel = _norm_rel(str(row.get("path") or ""))
        if rel:
            payload = build_inline_diff_for_path(
                workspace_root,
                rel,
                new_content=str(row.get("content") or ""),
            )
            if payload.get("ok"):
                row["old_preview"] = str(payload.get("old_text") or "")[:2000]
                row["new_preview"] = str(payload.get("new_text") or "")[:2000]
        out.append(row)
    return out


def faz27_directive() -> str:
    return (
        "[EDİTÖR DİFF — Faz 27]\n"
        "Patch şeridinde dosyaya tıklayınca editör üstünde eski/yeni yan yana görünür.\n"
    )
