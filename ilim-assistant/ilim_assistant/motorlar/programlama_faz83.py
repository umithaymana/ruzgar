# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 83: PR hazırlık (E5).

`pr hazırla:` — branch, commit mesajı, gh pr create komutu.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

FAZ83_VERSION = "programlama-faz83-v1-2026-05-26"

_PR_RE = re.compile(
    r"^\s*(?:pr\s+hazirla|pr\s+hazırla|pull\s+request|gh\s+pr)\s*:?\s*(.*)$",
    re.I | re.S,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ83", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz83_enabled() -> bool:
    return _enabled()


def wants_pr_prepare(message: str) -> bool:
    return _enabled() and bool(_PR_RE.search((message or "").strip()))


def _git(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        p = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)[:200]


def build_pr_plan(
    workspace_root: str | Path | None,
    *,
    title_hint: str = "",
    scope_rel: str | None = None,
) -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = None
    if root is None:
        return {"ok": False, "error": "repo kökü yok"}

    code, branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    _, status = _git(["status", "-sb"], root)
    _, diff_stat = _git(["diff", "--stat"], root)

    title = (title_hint or "").strip() or "feat: programlama motoru güncellemesi"
    if scope_rel:
        title = f"feat({scope_rel.split('/')[-1]}): {title_hint or 'güncelleme'}"[:72]

    commit_msg = title
    if diff_stat:
        first_files = diff_stat.splitlines()[:3]
        commit_msg = title + "\n\n" + "\n".join(f"- {ln}" for ln in first_files if ln.strip())

    branch_suggest = f"feat/ruzgar-{scope_rel.split('/')[-1] if scope_rel else 'update'}"[:48]
    branch_suggest = re.sub(r"[^\w\-/]", "-", branch_suggest)

    gh_cmd = (
        f'gh pr create --title "{title}" --body "Rüzgar programlama motoru PR (Faz 83)"'
    )
    gh_ok = shutil.which("gh") is not None

    return {
        "ok": True,
        "branch": branch.strip() if code == 0 else "?",
        "branch_suggest": branch_suggest,
        "status": status[:1500],
        "diff_stat": diff_stat[:2000],
        "commit_message": commit_msg,
        "gh_available": gh_ok,
        "gh_command": gh_cmd,
        "steps": [
            f"git checkout -b {branch_suggest}",
            "git add -A",
            f'git commit -m "{title}"',
            "git push -u origin HEAD",
            gh_cmd if gh_ok else "(gh kurulu değil — GitHub web'den PR açın)",
        ],
        "version": FAZ83_VERSION,
    }


def format_pr_plan(plan: dict[str, Any]) -> str:
    if not plan.get("ok"):
        return f"Ümit abi, PR planı oluşturulamadı: {plan.get('error')}\n({FAZ83_VERSION})"
    lines = [
        "Ümit abi, **PR hazırlık (Faz 83):**",
        "",
        f"Dal: `{plan.get('branch')}` · öneri: `{plan.get('branch_suggest')}`",
        "",
        "**Durum:**",
        "```",
        (plan.get("status") or "")[:800],
        "```",
        "",
        "**Commit mesajı önerisi:**",
        "```",
        (plan.get("commit_message") or "")[:600],
        "```",
        "",
        "**Adımlar:**",
    ]
    for i, step in enumerate(plan.get("steps") or [], 1):
        lines.append(f"{i}. `{step}`")
    if not plan.get("gh_available"):
        lines.append("")
        lines.append("_`gh` CLI yok — push sonrası GitHub'dan PR açın._")
    lines.append(f"\n({FAZ83_VERSION})")
    return "\n".join(lines)


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz83"] = faz83_enabled()
    return out


def maybe_instant_faz83(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    m = _PR_RE.search((message or "").strip())
    if not m:
        return None
    hint = (m.group(1) or "").strip()
    scope = None
    try:
        from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

        scope = resolve_scope_rel(workspace_root, message=message)
    except Exception:
        pass
    plan = build_pr_plan(workspace_root, title_hint=hint, scope_rel=scope)
    return format_pr_plan(plan)
