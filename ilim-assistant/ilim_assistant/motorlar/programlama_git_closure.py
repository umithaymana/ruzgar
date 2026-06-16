# Created by Ümit & Gökçenur
"""
Programlama motoru — Adım 8: Git kapanış döngüsü.

Görev başarılı -> diff özeti -> commit mesajı -> pending -> «commit onayla».
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

GIT_CLOSURE_VERSION = "programlama-git-closure-v1-2026-06-16"


def git_closure_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_GIT_CLOSURE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def ensure_scope_git_repo(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, Any]:
    """Proje dizininde git yoksa güvenli init."""
    try:
        from ilim_assistant.motorlar.programlama_faz17 import (
            _is_git_repo,
            _run_git,
            _scope_cwd,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}

    cwd = _scope_cwd(workspace_root, scope_rel)
    if cwd is None:
        return {"ok": False, "error": f"kapsam yok: {scope_rel}"}
    if _is_git_repo(cwd):
        return {"ok": True, "scope_rel": scope_rel, "initialized": False}
    init = _run_git(["git", "init"], cwd, timeout=30)
    if not init.get("ok"):
        return {
            "ok": False,
            "error": f"git init: {(init.get('output') or '')[:120]}",
        }
    return {"ok": True, "scope_rel": scope_rel, "initialized": True}


def gather_closure_snapshot(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
) -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_faz58 import gather_scope_git
        from ilim_assistant.motorlar.programlama_faz17 import gather_git_snapshot

        snap58 = gather_scope_git(workspace_root, scope_rel=scope_rel)
        snap17 = gather_git_snapshot(workspace_root, scope_rel=scope_rel)
        return {
            "ok": bool(snap17.get("ok")),
            "scope_rel": scope_rel,
            "has_changes": bool(snap58.get("has_changes") or snap17.get("has_changes")),
            "branch": snap17.get("branch") or snap58.get("branch"),
            "diff_stat": str(
                (snap17.get("diff_stat") or {}).get("output")
                or snap58.get("diff_stat")
                or ""
            )[:3000],
            "status_snippet": str((snap17.get("status") or {}).get("output") or "")[:1500],
            "snap17": snap17,
            "snap58": snap58,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def run_git_closure_after_task(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str = "",
    success: bool = False,
) -> dict[str, Any]:
    """Başarılı görev sonrası git kapanış paketi."""
    if not git_closure_enabled() or not success:
        return {"ok": False, "skipped": True}
    scope = (scope_rel or "").replace("\\", "/").strip("/")
    if not scope:
        return {"ok": False, "error": "scope yok"}

    repo_rep = ensure_scope_git_repo(workspace_root, scope)
    if not repo_rep.get("ok"):
        return repo_rep

    snap = gather_closure_snapshot(workspace_root, scope_rel=scope)
    if not snap.get("ok"):
        return snap
    if not snap.get("has_changes"):
        return {
            "ok": True,
            "skipped": True,
            "reason": "no_changes",
            "scope_rel": scope,
            "version": GIT_CLOSURE_VERSION,
        }

    try:
        from ilim_assistant.motorlar.programlama_faz17 import suggest_commit_message

        sug = suggest_commit_message(
            workspace_root,
            scope_rel=scope,
            user_hint=(goal or "")[:400],
            message=goal or "",
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}

    if not sug.get("ok"):
        return sug

    return {
        "ok": True,
        "scope_rel": scope,
        "suggested": sug.get("suggested"),
        "source": sug.get("source"),
        "snapshot": snap,
        "pending": sug.get("pending"),
        "version": GIT_CLOSURE_VERSION,
    }


def format_git_closure_footer(closure: dict[str, Any]) -> str:
    if not closure.get("ok") or closure.get("skipped"):
        return ""
    msg = str(closure.get("suggested") or "").strip()
    if not msg:
        return ""
    scope = closure.get("scope_rel") or "?"
    diff = str((closure.get("snapshot") or {}).get("diff_stat") or "").strip()
    lines = [
        "",
        f"**Git kapanış ({GIT_CLOSURE_VERSION})**",
        f"Kapsam: `{scope}`",
    ]
    if diff:
        lines.extend(["", "```text", diff[:2000], "```"])
    lines.extend(
        [
            "",
            f"Önerilen commit: `{msg}`",
            "Onay için: `commit onayla` · iptal: `commit iptal`",
        ]
    )
    return "\n".join(lines)


def append_git_closure_to_reply(reply: str, closure: dict[str, Any]) -> str:
    foot = format_git_closure_footer(closure)
    if not foot:
        return reply
    return (reply or "").rstrip() + foot


def run_git_closure_smoke(
    workspace_root: str | Path | None,
    *,
    scope_rel: str = "projects/smoke-live-test",
) -> dict[str, Any]:
    """Bench: init -> öneri -> onaylı commit."""
    if not git_closure_enabled():
        return {"ok": False, "error": "RUZGAR_PROG_GIT_CLOSURE=0"}

    os.environ.setdefault("RUZGAR_FAZ17_LLM_SUGGEST", "0")

    repo_rep = ensure_scope_git_repo(workspace_root, scope_rel)
    if not repo_rep.get("ok"):
        return {"ok": False, "repo": repo_rep}

    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return {"ok": False, "error": "workspace_root yok"}
        marker = root / scope_rel.replace("/", os.sep) / ".ruzgar_git_closure_smoke"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(f"smoke-{time.time():.3f}\n", encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:120]}

    closure = run_git_closure_after_task(
        workspace_root,
        scope_rel=scope_rel,
        goal="git closure smoke test",
        success=True,
    )
    if not closure.get("ok") or not closure.get("suggested"):
        return {
            "ok": False,
            "closure": closure,
            "version": GIT_CLOSURE_VERSION,
        }

    try:
        from ilim_assistant.motorlar.programlama_faz17 import execute_pending_commit

        commit_rep = execute_pending_commit(workspace_root)
    except Exception as exc:
        commit_rep = {"ok": False, "error": str(exc)[:120]}

    ok = bool(commit_rep.get("ok"))
    return {
        "ok": ok,
        "repo": repo_rep,
        "closure": {
            "suggested": closure.get("suggested"),
            "source": closure.get("source"),
        },
        "commit": {
            "ok": commit_rep.get("ok"),
            "message": commit_rep.get("message"),
            "output": str(commit_rep.get("output") or "")[:300],
        },
        "version": GIT_CLOSURE_VERSION,
    }
