# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 62: Git commit önerisi v2 (görev sonrası + atölye şeridi).

Faz 17 üzerine: otonom görev bitince otomatik öneri, git-changes API zenginleştirme.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

FAZ62_VERSION = "programlama-faz62-v1-2026-05-26"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ62", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz62_enabled() -> bool:
    return _enabled()


def maybe_auto_suggest_commit_after_task(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str = "",
    success: bool = False,
) -> dict[str, Any]:
    """Görev başarılı ve git değişikliği varsa commit mesajı öner (pending kayıt)."""
    if not _enabled() or not success:
        return {"ok": False, "skipped": True}
    if os.environ.get("RUZGAR_FAZ62_AUTO_SUGGEST", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return {"ok": False, "skipped": True}
    try:
        from ilim_assistant.motorlar.programlama_faz58 import gather_scope_git

        snap = gather_scope_git(workspace_root, scope_rel=scope_rel)
        if not snap.get("ok") or not snap.get("has_changes"):
            return {"ok": False, "skipped": True, "reason": "no_changes"}
        from ilim_assistant.motorlar.programlama_faz17 import suggest_commit_message

        hint = (goal or "").strip()[:400]
        return suggest_commit_message(
            workspace_root,
            scope_rel=scope_rel,
            user_hint=hint,
            message=hint,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def format_commit_strip_line(suggest: dict[str, Any]) -> str:
    if not suggest.get("ok"):
        return ""
    msg = str(suggest.get("suggested") or "").strip()
    if not msg:
        return ""
    src = str(suggest.get("source") or "heuristic")
    return f"Önerilen commit ({src}): {msg[:120]}"


def append_commit_footer_to_reply(
    reply: str,
    suggest: dict[str, Any],
) -> str:
    if not _enabled() or not suggest.get("ok"):
        return reply
    msg = str(suggest.get("suggested") or "").strip()
    if not msg:
        return reply
    block = (
        f"\n\n**Git commit önerisi (Faz 62)**\n"
        f"```\n{msg}\n```\n"
        "Onay: atölyede **Commit onayla** veya sohbette `git commit onayla`.\n"
        f"({FAZ62_VERSION})"
    )
    return (reply or "").rstrip() + block


def enrich_git_changes_api_payload(
    payload: dict[str, Any],
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    auto_suggest: bool = True,
) -> dict[str, Any]:
    """git-changes yanıtına pending / öneri ekle."""
    if not _enabled():
        payload["faz62"] = False
        return payload
    out = dict(payload)
    out["faz62"] = True
    try:
        from ilim_assistant.motorlar.programlama_faz17 import load_pending_commit

        pending = load_pending_commit(workspace_root)
        if pending.get("message"):
            out["pending_commit"] = {
                "scope_rel": pending.get("scope_rel"),
                "message": pending.get("message"),
                "source": pending.get("source"),
            }
    except Exception:
        pass
    strip = out.get("strip") if isinstance(out.get("strip"), dict) else {}
    if (
        auto_suggest
        and out.get("ok")
        and strip.get("has_changes")
        and not out.get("pending_commit")
        and scope_rel
    ):
        sug = maybe_auto_suggest_commit_after_task(
            workspace_root,
            scope_rel=str(scope_rel),
            goal="",
            success=True,
        )
        if sug.get("ok"):
            out["commit_suggest"] = {
                "message": sug.get("suggested"),
                "source": sug.get("source"),
                "scope_rel": sug.get("scope_rel"),
            }
            out["pending_commit"] = {
                "scope_rel": sug.get("scope_rel"),
                "message": sug.get("suggested"),
                "source": sug.get("source"),
            }
    return out


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz62"] = faz62_enabled()
    out["faz62_auto_suggest"] = faz62_enabled()
    return out


def faz62_directive() -> str:
    return (
        "[GIT COMMIT — Faz 62]\n"
        "Görev sonrası otomatik commit mesajı önerisi; git şeridinde pending görünür.\n"
        "Kapat: RUZGAR_FAZ62=0 · otomatik öneri: RUZGAR_FAZ62_AUTO_SUGGEST=0\n"
    )
