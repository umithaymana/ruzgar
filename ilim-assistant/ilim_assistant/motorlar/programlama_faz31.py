# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 31: Git PR köprüsü (gh CLI).

Komutlar: pr durum · pr gönder · pr oluştur: başlık
Önce workspace kökü git deposu; yoksa projects/<ad>/.
"""

from __future__ import annotations

import os
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ31_VERSION = "programlama-faz31-v1-2026-05-25"
_PROTECTED_BRANCHES = frozenset({"main", "master", "develop"})
_PUSH_BLOCK_RE = re.compile(
    r"push\s+.*--force|push\s+-f\b|push\s+--force-with-lease",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ31", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _git_available() -> bool:
    return shutil.which("git") is not None


def _run_cmd(
    argv: list[str],
    cwd: Path,
    *,
    timeout: int = 180,
) -> dict[str, Any]:
    if not argv:
        return {"ok": False, "error": "boş komut", "exit_code": -1, "output": ""}
    cmd = " ".join(argv)
    if _PUSH_BLOCK_RE.search(cmd):
        return {
            "ok": False,
            "error": "Force push yasak.",
            "exit_code": -1,
            "output": "",
        }
    code, out, err = run_argv(argv, timeout_sec=timeout, cwd=str(cwd))
    combined = "\n".join(x for x in (out, err) if x).strip()
    return {
        "ok": code == 0,
        "exit_code": code,
        "output": combined[:12000],
        "argv": argv,
    }


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def resolve_git_cwd(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    message: str = "",
) -> tuple[Path | None, str]:
    """Önce workspace kökü, sonra projects/<proje> git deposu."""
    root = repo_root(workspace_root)
    if root is not None and _is_git_repo(root):
        return root, "workspace_root"

    from ilim_assistant.motorlar.programlama_faz17 import resolve_scope_rel

    scope = (scope_rel or "").strip() or resolve_scope_rel(
        workspace_root, active_file=active_file, message=message
    )
    if scope:
        from ilim_assistant.motorlar.programlama_faz17 import _scope_cwd

        cwd = _scope_cwd(workspace_root, scope)
        if cwd is not None and _is_git_repo(cwd):
            return cwd, "project_scope"

    return None, ""


def _current_branch(cwd: Path) -> str:
    res = _run_cmd(["git", "branch", "--show-current"], cwd, timeout=30)
    if res.get("ok"):
        return (res.get("output") or "").strip()
    return ""


def _upstream_branch(cwd: Path) -> str:
    res = _run_cmd(["git", "rev-parse", "--abbrev-ref", "@{u}"], cwd, timeout=30)
    if res.get("ok"):
        return (res.get("output") or "").strip()
    return ""


def _ahead_behind(cwd: Path) -> tuple[int, int]:
    up = _upstream_branch(cwd)
    if not up:
        return 0, 0
    res = _run_cmd(
        ["git", "rev-list", "--left-right", "--count", f"{up}...HEAD"],
        cwd,
        timeout=60,
    )
    if not res.get("ok"):
        return 0, 0
    parts = (res.get("output") or "").strip().split()
    if len(parts) >= 2:
        try:
            behind = int(parts[0])
            ahead = int(parts[1])
            return ahead, behind
        except ValueError:
            pass
    return 0, 0


def _default_base_branch(cwd: Path) -> str:
    if _gh_available():
        res = _run_cmd(
            ["gh", "repo", "view", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"],
            cwd,
            timeout=60,
        )
        if res.get("ok"):
            b = (res.get("output") or "").strip()
            if b:
                return b
    res = _run_cmd(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd,
        timeout=30,
    )
    if res.get("ok"):
        ref = (res.get("output") or "").strip()
        if ref.endswith("/main"):
            return "main"
        if "/" in ref:
            return ref.rsplit("/", 1)[-1]
    return "main"


def _list_head_prs(cwd: Path, branch: str) -> list[dict[str, Any]]:
    if not _gh_available() or not branch:
        return []
    res = _run_cmd(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--json",
            "number,title,url,state",
            "--limit",
            "5",
        ],
        cwd,
        timeout=90,
    )
    if not res.get("ok"):
        return []
    try:
        import json

        data = json.loads(res.get("output") or "[]")
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []


def gather_pr_snapshot(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    cwd, source = resolve_git_cwd(
        workspace_root,
        scope_rel=scope_rel,
        active_file=active_file,
        message=message,
    )
    if cwd is None:
        return {
            "ok": False,
            "error": "Git deposu bulunamadı (workspace kökü veya projects/<ad>).",
        }

    branch = _current_branch(cwd)
    upstream = _upstream_branch(cwd)
    ahead, behind = _ahead_behind(cwd)
    base = _default_base_branch(cwd)
    remote_res = _run_cmd(["git", "remote", "get-url", "origin"], cwd, timeout=30)
    remote_url = (remote_res.get("output") or "").strip() if remote_res.get("ok") else ""

    st = _run_cmd(["git", "status", "-sb"], cwd, timeout=60)
    dirty = " M " in (st.get("output") or "") or "??" in (st.get("output") or "")

    return {
        "ok": True,
        "cwd": str(cwd),
        "git_source": source,
        "branch": branch,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "base_branch": base,
        "remote_url": remote_url,
        "dirty": dirty,
        "gh_cli": _gh_available(),
        "protected_branch": branch in _PROTECTED_BRANCHES,
        "open_prs": _list_head_prs(cwd, branch),
        "version": FAZ31_VERSION,
    }


def push_current_branch(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
) -> dict[str, Any]:
    if os.environ.get("RUZGAR_FAZ31_PUSH", "1").strip().lower() in ("0", "false", "no"):
        return {"ok": False, "error": "Push kapalı (RUZGAR_FAZ31_PUSH=0)."}

    snap = gather_pr_snapshot(workspace_root, scope_rel=scope_rel, active_file=active_file)
    if not snap.get("ok"):
        return snap
    cwd = Path(str(snap["cwd"]))
    branch = str(snap.get("branch") or "")
    if not branch:
        return {"ok": False, "error": "Aktif dal okunamadı."}
    if snap.get("protected_branch"):
        return {
            "ok": False,
            "error": f"`{branch}` korumalı dal — feature dalında push yapın.",
        }

    push = _run_cmd(["git", "push", "-u", "origin", "HEAD"], cwd, timeout=300)
    return {
        "ok": bool(push.get("ok")),
        "branch": branch,
        "push": push,
        "output": str(push.get("output") or ""),
        "version": FAZ31_VERSION,
    }


def create_pull_request(
    workspace_root: str | Path | None,
    *,
    title: str = "",
    body: str = "",
    push_first: bool = True,
    scope_rel: str | None = None,
    active_file: str | None = None,
) -> dict[str, Any]:
    if not _gh_available():
        return {
            "ok": False,
            "error": "GitHub CLI (`gh`) PATH'te yok — PR için gh auth login gerekir.",
        }

    snap = gather_pr_snapshot(workspace_root, scope_rel=scope_rel, active_file=active_file)
    if not snap.get("ok"):
        return snap

    cwd = Path(str(snap["cwd"]))
    branch = str(snap.get("branch") or "")
    base = str(snap.get("base_branch") or "main")

    if snap.get("protected_branch"):
        return {
            "ok": False,
            "error": f"`{branch}` üzerinde PR açılamaz — önce feature dalı oluşturun.",
        }

    existing = snap.get("open_prs") or []
    if existing:
        pr0 = existing[0]
        return {
            "ok": True,
            "already_exists": True,
            "pr": pr0,
            "url": pr0.get("url"),
            "version": FAZ31_VERSION,
        }

    push_res: dict[str, Any] | None = None
    if push_first:
        push_res = push_current_branch(workspace_root, scope_rel=scope_rel)
        if not push_res.get("ok"):
            return {
                "ok": False,
                "error": f"Push başarısız: {push_res.get('error') or push_res.get('output', '')[:200]}",
                "push": push_res,
            }

    tit = (title or "").strip()
    if not tit:
        log_res = _run_cmd(["git", "log", "-1", "--pretty=%s"], cwd, timeout=30)
        tit = (log_res.get("output") or "").strip() or f"Programlama: {branch}"

    bod = (body or "").strip() or (
        f"Rüzgar Programlama Motoru — Faz 31 otomatik PR.\n\nDal: `{branch}` → `{base}`"
    )

    argv = [
        "gh",
        "pr",
        "create",
        "--base",
        base,
        "--head",
        branch,
        "--title",
        tit,
        "--body",
        bod,
    ]
    pr_res = _run_cmd(argv, cwd, timeout=180)
    url = ""
    for line in (pr_res.get("output") or "").splitlines():
        if line.startswith("http"):
            url = line.strip()
            break

    return {
        "ok": bool(pr_res.get("ok")),
        "branch": branch,
        "base": base,
        "title": tit,
        "url": url,
        "push": push_res,
        "gh": pr_res,
        "output": str(pr_res.get("output") or ""),
        "version": FAZ31_VERSION,
    }


def parse_pr_create(message: str) -> tuple[str, str]:
    m = re.search(
        r"(?:pr\s+olustur|pr\s+oluştur|pr\s+ac|pull\s+request)\s*[:\"]?\s*(.+)$",
        message or "",
        re.I | re.M,
    )
    if m:
        rest = m.group(1).strip()
        if "\n" in rest:
            title, body = rest.split("\n", 1)
            return title.strip(), body.strip()
        return rest, ""
    return "", ""


def wants_pr_status(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "pr durum",
            "pr özeti",
            "pr ozeti",
            "pull request",
            "pr listesi",
            "acik pr",
            "açık pr",
        )
    ) and "olustur" not in low and "oluştur" not in low and "ac " not in low


def wants_pr_push(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "pr gonder",
            "pr gönder",
            "dal gonder",
            "dal gönder",
            "push pr",
            "origin push",
        )
    )


def wants_pr_create(message: str) -> bool:
    low = _ascii_fold(message)
    if parse_pr_create(message)[0] or parse_pr_create(message)[1]:
        return True
    return any(
        k in low
        for k in (
            "pr olustur",
            "pr oluştur",
            "pr ac",
            "pr aç",
            "gh pr create",
        )
    )


def format_pr_status_report(snap: dict[str, Any]) -> str:
    if not snap.get("ok"):
        return f"Ümit abi, PR: {snap.get('error')}"
    lines = [
        "Ümit abi, **PR durumu** (Faz 31)",
        "",
        f"Depo: `{snap.get('cwd')}` ({snap.get('git_source')})",
        f"Dal: **{snap.get('branch')}** → taban `{snap.get('base_branch')}`",
        f"Uzak: `{snap.get('upstream') or '(yok)'}` · ileri **{snap.get('ahead')}** · geri **{snap.get('behind')}**",
        f"GitHub CLI: **{'var' if snap.get('gh_cli') else 'yok'}**",
    ]
    if snap.get("dirty"):
        lines.append("Uyarı: commit edilmemiş değişiklik var.")
    if snap.get("protected_branch"):
        lines.append("Uyarı: korumalı dal — PR için feature dalı kullanın.")
    prs = snap.get("open_prs") or []
    if prs:
        lines.append("")
        lines.append("**Açık PR:**")
        for p in prs:
            lines.append(f"- #{p.get('number')} {p.get('title')} — {p.get('url')}")
    else:
        lines.append("")
        lines.append("_Bu dal için açık PR yok._")
    lines.append(f"\n({FAZ31_VERSION})")
    return "\n".join(lines)


def format_pr_create_report(res: dict[str, Any]) -> str:
    if not res.get("ok"):
        err = res.get("error") or str(res.get("output") or "")[:400]
        return f"Ümit abi, PR oluşturulamadı: {err}\n({FAZ31_VERSION})"
    if res.get("already_exists"):
        url = res.get("url") or (res.get("pr") or {}).get("url") or ""
        return f"Ümit abi, bu dal için PR zaten var: {url}\n({FAZ31_VERSION})"
    url = res.get("url") or ""
    return (
        f"Ümit abi, PR hazır — **`{res.get('title')}`**\n\n"
        f"Dal: `{res.get('branch')}` → `{res.get('base')}`\n"
        f"{url or res.get('output', '')}\n"
        f"({FAZ31_VERSION})"
    )


def maybe_instant_faz31(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None

    if wants_pr_create(message):
        title, body = parse_pr_create(message)
        res = create_pull_request(
            workspace_root,
            title=title,
            body=body,
            active_file=active_file,
        )
        return format_pr_create_report(res)

    if wants_pr_push(message):
        res = push_current_branch(workspace_root, active_file=active_file)
        if res.get("ok"):
            return (
                f"Ümit abi, dal gönderildi: **{res.get('branch')}**\n"
                f"```text\n{str(res.get('output') or '')[:2000]}\n```\n({FAZ31_VERSION})"
            )
        return f"Push başarısız: {res.get('error')}\n({FAZ31_VERSION})"

    if wants_pr_status(message):
        snap = gather_pr_snapshot(workspace_root, active_file=active_file, message=message)
        return format_pr_status_report(snap)

    return None


def faz31_directive() -> str:
    return (
        "[GIT PR — Faz 31]\n"
        "Komutlar: `pr durum` · `pr gönder` · `pr oluştur: başlık`\n"
        "Gereksinim: `gh auth login` · force push yasak.\n"
    )
