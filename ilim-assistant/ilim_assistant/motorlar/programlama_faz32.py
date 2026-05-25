# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 32: Görev sonrası Git akışı.

Başarılı otonom görevden sonra: durum özeti + sıradaki adımlar (commit → push → PR).
Tek komut: `iş bitir pr` / `görev kaydet` (onaylı pipeline).
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ32_VERSION = "programlama-faz32-v1-2026-05-25"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ32", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def post_task_footer_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_FAZ32_POST_TASK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def pipeline_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_FAZ32_PIPELINE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def build_post_task_summary(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    success: bool,
    verify_ok: bool = False,
    elapsed_sec: float = 0.0,
) -> dict[str, Any]:
    """Görev bitince eklenecek Git/checklist yükü."""
    steps: list[dict[str, str]] = []
    if not success:
        return {
            "ok": True,
            "markdown": (
                "Ümit abi, görev tamamlanamadı — önce pytest/verify yeşil olsun, "
                "sonra `iş akışı` ile Git adımlarına bakın.\n"
                f"({FAZ32_VERSION})"
            ),
            "steps": [],
            "version": FAZ32_VERSION,
        }

    try:
        from ilim_assistant.motorlar.programlama_faz31 import gather_pr_snapshot

        snap = gather_pr_snapshot(workspace_root)
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc)[:200],
            "version": FAZ32_VERSION,
        }

    if not snap.get("ok"):
        return {
            "ok": True,
            "markdown": (
                f"Görev bitti ({elapsed_sec:.1f}s). Git deposu yok — "
                f"`{scope_rel}` için `git init` veya workspace kökünde repo gerekir.\n"
                f"({FAZ32_VERSION})"
            ),
            "steps": [],
            "version": FAZ32_VERSION,
        }

    branch = str(snap.get("branch") or "?")
    dirty = bool(snap.get("dirty"))
    protected = bool(snap.get("protected_branch"))
    gh = bool(snap.get("gh_cli"))
    open_prs = snap.get("open_prs") or []

    lines = [
        "Ümit abi, **görev sonrası Git akışı** (Faz 32)",
        "",
        f"Proje: `{scope_rel}` · dal: **{branch}** · verify: **{'OK' if verify_ok else '—'}**",
        "",
        "**Sıradaki adımlar:**",
    ]

    if dirty:
        steps.append(
            {
                "id": "commit",
                "label": "Commit",
                "command": "commit öner",
            }
        )
        lines.append("1. `commit öner` → `git commit onayla`")
    else:
        lines.append("1. Çalışma ağacı temiz (commit gerekmez)")

    if protected:
        lines.append("2. `yeni dal: feature-adi` — main üzerinde PR açılmaz")
        steps.append(
            {
                "id": "branch",
                "label": "Feature dalı",
                "command": "yeni dal: feature-adi",
            }
        )
    elif dirty or snap.get("ahead", 0) > 0:
        steps.append({"id": "push", "label": "Push", "command": "pr gönder"})
        lines.append("2. `pr gönder` (dalı origin'e gönder)")
    else:
        lines.append("2. Push gerekmez (uzak ile uyumlu)")

    if open_prs:
        url = str(open_prs[0].get("url") or "")
        lines.append(f"3. Açık PR: {url}")
    elif gh and not protected:
        steps.append(
            {
                "id": "pr",
                "label": "PR aç",
                "command": "pr oluştur: görev tamamlandı",
            }
        )
        lines.append("3. `pr oluştur: görev tamamlandı`")
    elif not gh:
        lines.append("3. PR için: `gh auth login` sonra `pr oluştur: ...`")
    else:
        lines.append("3. Önce feature dalına geçin")

    lines.append("")
    lines.append("Tek komut (commit+push+PR): `iş bitir pr`")
    lines.append(f"({FAZ32_VERSION})")

    return {
        "ok": True,
        "markdown": "\n".join(lines),
        "steps": steps,
        "snapshot": snap,
        "version": FAZ32_VERSION,
    }


def append_post_task_to_reply(
    reply_body: str,
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    success: bool,
    verify_ok: bool = False,
    elapsed_sec: float = 0.0,
) -> str:
    if not post_task_footer_enabled() or not success:
        return reply_body
    block = build_post_task_summary(
        workspace_root,
        scope_rel,
        success=success,
        verify_ok=verify_ok,
        elapsed_sec=elapsed_sec,
    )
    md = str(block.get("markdown") or "").strip()
    if not md:
        return reply_body
    return reply_body.rstrip() + "\n\n" + md


def _commit_at_cwd(cwd: Path, message: str) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz31 import _run_cmd

    add = _run_cmd(["git", "add", "-A"], cwd, timeout=120)
    if not add.get("ok"):
        return {"ok": False, "error": add.get("output") or "git add başarısız"}
    commit = _run_cmd(["git", "commit", "-m", message], cwd, timeout=120)
    return {
        "ok": bool(commit.get("ok")),
        "output": commit.get("output") or "",
        "message": message,
        "error": None if commit.get("ok") else (commit.get("output") or "commit başarısız"),
    }


def run_task_save_pipeline(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    pr_title: str = "",
    open_pr: bool = True,
) -> dict[str, Any]:
    """commit öner → onaylı commit → push → isteğe bağlı PR."""
    if not pipeline_enabled():
        return {"ok": False, "error": "Pipeline kapalı (RUZGAR_FAZ32_PIPELINE=0)."}

    from ilim_assistant.motorlar.programlama_faz17 import (
        execute_pending_commit,
        gather_git_snapshot,
        heuristic_commit_message,
        suggest_commit_message,
    )
    from ilim_assistant.motorlar.programlama_faz31 import (
        _run_cmd,
        create_pull_request,
        gather_pr_snapshot,
        push_current_branch,
    )

    snap = gather_git_snapshot(
        workspace_root,
        scope_rel=scope_rel,
        active_file=active_file,
    )
    pr_snap = gather_pr_snapshot(
        workspace_root,
        scope_rel=scope_rel,
        active_file=active_file,
    )
    if not pr_snap.get("ok"):
        return {
            "ok": False,
            "error": pr_snap.get("error") or "Git deposu yok",
            "version": FAZ32_VERSION,
        }
    git_cwd = Path(str(pr_snap["cwd"]))
    use_workspace = pr_snap.get("git_source") == "workspace_root"

    steps: list[dict[str, Any]] = []
    dirty = bool(pr_snap.get("dirty"))

    if dirty:
        commit_msg = "chore(ruzgar): görev tamamlandı"
        if use_workspace:
            diff_res = _run_cmd(["git", "diff", "--stat"], git_cwd, timeout=60)
            fake = {
                "ok": True,
                "scope_rel": scope_rel or "workspace",
                "diff_stat": {"output": diff_res.get("output") or ""},
            }
            commit_msg = heuristic_commit_message(fake)
        elif snap.get("ok") and snap.get("has_changes"):
            sug = suggest_commit_message(
                workspace_root,
                scope_rel=scope_rel,
                active_file=active_file,
            )
            if sug.get("ok") and sug.get("suggested"):
                commit_msg = str(sug["suggested"])
                steps.append({"step": "suggest", "ok": True, "message": commit_msg})
            commit_res = execute_pending_commit(workspace_root)
            steps.append({"step": "commit", **commit_res})
            if not commit_res.get("ok"):
                return {
                    "ok": False,
                    "error": commit_res.get("error") or "commit başarısız",
                    "steps": steps,
                    "version": FAZ32_VERSION,
                }
            dirty = False
        if dirty:
            steps.append({"step": "suggest", "ok": True, "message": commit_msg})
            commit_res = _commit_at_cwd(git_cwd, commit_msg)
            steps.append({"step": "commit", **commit_res})
            if not commit_res.get("ok"):
                return {
                    "ok": False,
                    "error": commit_res.get("error") or "commit başarısız",
                    "steps": steps,
                    "version": FAZ32_VERSION,
                }
    else:
        steps.append({"step": "commit", "ok": True, "skipped": True})

    push_res = push_current_branch(
        workspace_root,
        scope_rel=scope_rel,
        active_file=active_file,
    )
    steps.append({"step": "push", **push_res})
    if not push_res.get("ok"):
        return {
            "ok": False,
            "error": push_res.get("error") or "push başarısız",
            "steps": steps,
            "version": FAZ32_VERSION,
        }

    pr_res: dict[str, Any] = {"ok": True, "skipped": True}
    if open_pr:
        title = (pr_title or "").strip() or "Görev tamamlandı — Rüzgar"
        pr_res = create_pull_request(
            workspace_root,
            title=title,
            push_first=False,
            scope_rel=scope_rel,
            active_file=active_file,
        )
        steps.append({"step": "pr", **pr_res})

    return {
        "ok": bool(pr_res.get("ok")),
        "steps": steps,
        "pr_url": pr_res.get("url"),
        "git_cwd": git_cwd,
        "version": FAZ32_VERSION,
    }


def parse_pipeline_title(message: str) -> str:
    m = re.search(
        r"(?:iş\s+bitir|gorev\s+kaydet|görev\s+kaydet|tamamla)\s+pr\s*[:\"]?\s*(.+)$",
        message or "",
        re.I,
    )
    if m:
        return m.group(1).strip()
    return ""


def wants_workflow_summary(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "is akisi",
            "iş akışı",
            "git akisi",
            "git akışı",
            "gorev sonu",
            "görev sonu",
            "is bitir",
            "iş bitir",
        )
    ) and "pr" not in low.split()[-1:] and "kaydet" not in low


def wants_task_save_pipeline(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "is bitir pr",
            "iş bitir pr",
            "gorev kaydet",
            "görev kaydet",
            "tamamla ve pr",
            "kaydet ve pr",
        )
    )


def format_pipeline_report(res: dict[str, Any]) -> str:
    if not res.get("ok"):
        return f"Ümit abi, kayıt akışı başarısız: {res.get('error')}\n({FAZ32_VERSION})"
    url = res.get("pr_url") or ""
    lines = [
        "Ümit abi, **görev kayıt akışı tamam** (commit → push → PR)",
        "",
    ]
    for st in res.get("steps") or []:
        name = st.get("step", "?")
        if st.get("skipped"):
            lines.append(f"- {name}: atlandı")
        elif st.get("ok"):
            lines.append(f"- {name}: OK")
        else:
            lines.append(f"- {name}: hata — {str(st.get('error') or '')[:120]}")
    if url:
        lines.append(f"\nPR: {url}")
    lines.append(f"\n({FAZ32_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz32(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None

    from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

    scope = resolve_scope_rel(
        workspace_root, active_file=active_file, message=message
    )

    if wants_task_save_pipeline(message):
        if not scope:
            return "Ümit abi, `iş bitir pr` için `projects/<proje>/` açın veya proje adı yazın."
        title = parse_pipeline_title(message)
        res = run_task_save_pipeline(
            workspace_root,
            scope_rel=scope,
            active_file=active_file,
            pr_title=title,
        )
        return format_pipeline_report(res)

    if wants_workflow_summary(message):
        if not scope:
            return "Ümit abi, Git akışı için aktif proje veya `proje sec: <ad>` gerekir."
        block = build_post_task_summary(
            workspace_root,
            scope,
            success=True,
            verify_ok=True,
        )
        return str(block.get("markdown") or "")

    return None


def faz32_directive() -> str:
    return (
        "[GÖREV SONU — Faz 32]\n"
        "Başarılı görevden sonra otomatik Git özeti eklenir.\n"
        "Komutlar: `iş akışı` · `iş bitir pr` (commit+push+PR)\n"
    )
