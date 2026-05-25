# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 28: Git branch (projects/<ad>/).

git branch · git dal · yeni dal: feature-x
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ28_VERSION = "programlama-faz28-v1-2026-05-25"
_BRANCH_NAME_RE = re.compile(r"^[\w.\-/]{1,80}$")


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ28", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def resolve_scope_rel(
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
    message: str = "",
) -> str | None:
    from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel as _r13

    return _r13(workspace_root, active_file=active_file, message=message)


def _scope_cwd(workspace_root: str | Path | None, scope_rel: str) -> Path | None:
    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    if root is None or not scope.startswith(f"{_projects_base()}/"):
        return None
    cwd = root / scope.replace("/", os.sep)
    return cwd if cwd.is_dir() else None


def gather_branch_snapshot(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, Any]:
    cwd = _scope_cwd(workspace_root, scope_rel)
    if cwd is None:
        return {"ok": False, "error": "Proje dizini yok"}
    if not (cwd / ".git").exists():
        return {"ok": False, "error": "Git deposu yok — önce git init"}

    current = ""
    code, out = run_argv(["git", "branch", "--show-current"], cwd=cwd)
    if code == 0:
        current = (out or "").strip()

    branches: list[str] = []
    code2, out2 = run_argv(["git", "branch", "--format=%(refname:short)"], cwd=cwd)
    if code2 == 0:
        branches = [ln.strip() for ln in (out2 or "").splitlines() if ln.strip()]

    return {
        "ok": True,
        "scope_rel": scope_rel,
        "current": current or "(detached)",
        "branches": branches[:40],
        "version": FAZ28_VERSION,
    }


def create_branch(
    workspace_root: str | Path | None,
    scope_rel: str,
    branch_name: str,
) -> dict[str, Any]:
    name = (branch_name or "").strip()
    if not name or not _BRANCH_NAME_RE.match(name):
        return {"ok": False, "error": "Geçersiz dal adı"}
    cwd = _scope_cwd(workspace_root, scope_rel)
    if cwd is None:
        return {"ok": False, "error": "Proje dizini yok"}
    code, out = run_argv(["git", "checkout", "-b", name], cwd=cwd)
    return {
        "ok": code == 0,
        "branch": name,
        "output": (out or "")[:2000],
        "version": FAZ28_VERSION,
    }


def parse_branch_create(message: str) -> str | None:
    m = re.search(
        r"(?:yeni\s+dal|git\s+branch\s+create|dal\s+olustur|dal\s+oluştur)\s*[:\"]?\s*([\w.\-/]+)",
        message or "",
        re.I,
    )
    if m:
        return m.group(1).strip()
    low = _ascii_fold(message)
    if low.startswith("git branch ") and "status" not in low:
        parts = message.strip().split(None, 2)
        if len(parts) >= 3 and parts[2]:
            return parts[2].strip()
    return None


def wants_git_branch_list(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "git branch",
            "git dal",
            "hangi dal",
            "aktif dal",
            "branch list",
        )
    ) and "create" not in low and "olustur" not in low and "oluştur" not in low


def wants_git_branch_create(message: str) -> bool:
    return bool(parse_branch_create(message))


def format_branch_report(snap: dict[str, Any]) -> str:
    if not snap.get("ok"):
        return f"Git dal: {snap.get('error')}"
    lines = [
        f"Ümit abi, **`{snap.get('scope_rel')}`** — Git dalları (Faz 28)",
        "",
        f"Aktif: **{snap.get('current')}**",
        "",
    ]
    for b in snap.get("branches") or []:
        mark = "→ " if b == snap.get("current") else "  "
        lines.append(f"{mark}`{b}`")
    lines.append(f"\n({FAZ28_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz28(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None
    scope = resolve_scope_rel(workspace_root, active_file=active_file, message=message)
    if not scope:
        if wants_git_branch_list(message) or wants_git_branch_create(message):
            return "Ümit abi, dal komutu için `projects/<proje>/` açın."
        return None

    if wants_git_branch_create(message):
        name = parse_branch_create(message)
        if not name:
            return "Ümit abi, `yeni dal: feature-adi` veya `git branch create feature-adi` yaz."
        res = create_branch(workspace_root, scope, name)
        if res.get("ok"):
            return f"Ümit abi, dal oluşturuldu: **`{name}`** (`{scope}`)\n({FAZ28_VERSION})"
        return f"Dal oluşturulamadı: {res.get('error')}\n{res.get('output', '')[:400]}"

    if wants_git_branch_list(message):
        return format_branch_report(gather_branch_snapshot(workspace_root, scope))

    return None


def faz28_directive() -> str:
    return (
        "[GİT DAL — Faz 28]\n"
        "Komutlar: `git branch` · `git dal` · `yeni dal: feature-x`\n"
    )
