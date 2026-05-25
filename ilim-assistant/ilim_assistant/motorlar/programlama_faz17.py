# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 17: Git köprüsü (projects/<ad>/).

git durum · git diff · commit öner · onaylı git commit (asla --no-verify).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ17_VERSION = "programlama-faz17-v1-2026-05-25"
_COMMIT_PENDING_FILE = "programlama_git_commit.json"

_NO_VERIFY_RE = re.compile(r"--no-verify", re.I)
_DANGEROUS_GIT_RE = re.compile(
    r"git\s+(?:push\s+.*--force|reset\s+--hard|clean\s+-fd|checkout\s+\.|stash\s+clear)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ17", "1").strip().lower() not in ("0", "false", "no")


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


def _ruzgar_dir(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    d = root / ".ruzgar"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return d


def _git_available() -> bool:
    return shutil.which("git") is not None


def _run_git(
    argv: list[str],
    cwd: Path,
    *,
    timeout: int = 120,
) -> dict[str, Any]:
    if not _git_available():
        return {"ok": False, "error": "git PATH'te yok.", "exit_code": -1, "output": ""}
    cmd = " ".join(argv)
    if _NO_VERIFY_RE.search(cmd) or _DANGEROUS_GIT_RE.search(cmd):
        return {"ok": False, "error": "Tehlikeli veya yasak git komutu.", "exit_code": -1, "output": ""}
    code, out, err = run_argv(argv, timeout_sec=timeout, cwd=str(cwd))
    combined = "\n".join(x for x in (out, err) if x).strip()
    return {
        "ok": code == 0,
        "exit_code": code,
        "output": combined[:12000],
        "argv": argv,
    }


def _is_git_repo(cwd: Path) -> bool:
    return (cwd / ".git").exists()


def gather_git_snapshot(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    scope = scope_rel or resolve_scope_rel(
        workspace_root, active_file=active_file, message=message
    )
    if not scope:
        return {"ok": False, "error": "Proje kapsamı gerekli (`projects/<ad>/`)."}
    cwd = _scope_cwd(workspace_root, scope)
    if cwd is None:
        return {"ok": False, "error": f"Dizin yok: {scope}", "scope_rel": scope}
    if not _is_git_repo(cwd):
        return {
            "ok": False,
            "error": f"Git deposu yok — `{scope}` içinde `git init` gerekir.",
            "scope_rel": scope,
            "cwd": str(cwd),
        }

    st = _run_git(["git", "status", "-sb"], cwd, timeout=60)
    diff_stat = _run_git(["git", "diff", "--stat"], cwd, timeout=120)
    diff_cached = _run_git(["git", "diff", "--cached", "--stat"], cwd, timeout=120)
    branch = ""
    for line in (st.get("output") or "").splitlines()[:3]:
        if line.startswith("##"):
            branch = line[2:].strip()
            break

    has_changes = bool(
        (diff_stat.get("output") or "").strip()
        or (diff_cached.get("output") or "").strip()
        or " M " in (st.get("output") or "")
        or "??" in (st.get("output") or "")
    )

    return {
        "ok": True,
        "scope_rel": scope,
        "cwd": str(cwd),
        "branch": branch,
        "status": st,
        "diff_stat": diff_stat,
        "diff_cached_stat": diff_cached,
        "has_changes": has_changes,
        "version": FAZ17_VERSION,
    }


def _parse_diff_files(diff_stat: str) -> list[str]:
    files: list[str] = []
    for line in (diff_stat or "").splitlines():
        line = line.strip()
        if "|" in line and not line.startswith("-"):
            name = line.split("|", 1)[0].strip()
            if name and name != "files changed":
                files.append(name.replace("\\", "/"))
    return files[:12]


def heuristic_commit_message(snapshot: dict[str, Any]) -> str:
    parts: list[str] = []
    ds = str((snapshot.get("diff_stat") or {}).get("output") or "")
    cs = str((snapshot.get("diff_cached_stat") or {}).get("output") or "")
    files = _parse_diff_files(ds) or _parse_diff_files(cs)
    scope = str(snapshot.get("scope_rel") or "")
    proj = scope.split("/")[-1] if "/" in scope else scope

    if not files:
        st = str((snapshot.get("status") or {}).get("output") or "")
        for ln in st.splitlines():
            if ln.startswith("??"):
                parts.append(ln[3:].strip().split("/")[-1])
        files = parts[:8]
        parts = []

    if not files:
        return f"chore({proj}): güncelleme"

    if len(files) == 1:
        f = files[0]
        if f.endswith(".py"):
            return f"fix({proj}): {Path(f).name} güncelle"
        return f"chore({proj}): {Path(f).name} güncelle"

    if all(f.endswith(".py") for f in files):
        return f"fix({proj}): {len(files)} Python dosyası"

    if any("test" in f.lower() for f in files):
        return f"test({proj}): test ve kaynak güncelle"

    names = ", ".join(Path(f).name for f in files[:3])
    suffix = f" (+{len(files) - 3})" if len(files) > 3 else ""
    return f"chore({proj}): {names}{suffix}"


def suggest_commit_via_llm(
    snapshot: dict[str, Any],
    *,
    user_hint: str = "",
) -> str | None:
    """Kısa LLM commit mesajı (isteğe bağlı; başarısızsa None)."""
    if os.environ.get("RUZGAR_FAZ17_LLM_SUGGEST", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return None
    if not snapshot.get("has_changes"):
        return None

    status_out = str((snapshot.get("status") or {}).get("output") or "")[:2000]
    diff_out = str((snapshot.get("diff_stat") or {}).get("output") or "")[:2500]
    cached = str((snapshot.get("diff_cached_stat") or {}).get("output") or "")[:1500]
    scope = snapshot.get("scope_rel") or "proje"

    prompt = (
        f"Git özeti ({scope}):\n"
        f"```\n{status_out}\n```\n"
        f"diff --stat:\n```\n{diff_out}\n```\n"
    )
    if cached.strip():
        prompt += f"staged:\n```\n{cached}\n```\n"
    if user_hint.strip():
        prompt += f"Kullanıcı notu: {user_hint.strip()}\n"
    prompt += (
        "\nTek satır Türkçe veya İngilizce conventional commit mesajı yaz "
        "(feat/fix/chore/test). Yalnızca mesaj, tırnak yok, açıklama yok."
    )

    try:
        from ilim_assistant.llm_brain import select_brain_chain, stream_chat_with_brain
        from ilim_assistant.prompts import pick_system

        system = pick_system(True, "programlama").strip()
        body = ""
        for piece in stream_chat_with_brain(
            system,
            prompt,
            model="",
            prior_messages=[],
            mode_norm="programlama",
            coding_mode=True,
            message="commit öner",
            question_plan=None,
        ):
            body += piece
        msg = (body or "").strip().splitlines()[0].strip()
        msg = msg.strip("\"'`")
        if len(msg) > 120:
            msg = msg[:117] + "..."
        if msg and not msg.lower().startswith("ümit abi"):
            return msg
    except Exception:
        return None
    return None


def suggest_commit_message(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    message: str = "",
    user_hint: str = "",
) -> dict[str, Any]:
    snap = gather_git_snapshot(
        workspace_root,
        scope_rel=scope_rel,
        active_file=active_file,
        message=message,
    )
    if not snap.get("ok"):
        return snap

    suggested = heuristic_commit_message(snap)
    source = "heuristic"
    llm_msg = suggest_commit_via_llm(snap, user_hint=user_hint)
    if llm_msg:
        suggested = llm_msg
        source = "llm"

    pending = {
        "scope_rel": snap.get("scope_rel"),
        "message": suggested,
        "source": source,
        "staged_at": time.time(),
        "snapshot": {
            "branch": snap.get("branch"),
            "status_snippet": str((snap.get("status") or {}).get("output") or "")[:1500],
            "diff_stat": str((snap.get("diff_stat") or {}).get("output") or "")[:2000],
        },
    }
    _save_pending_commit(workspace_root, pending)

    return {
        "ok": True,
        "suggested": suggested,
        "source": source,
        "scope_rel": snap.get("scope_rel"),
        "snapshot": snap,
        "pending": pending,
        "version": FAZ17_VERSION,
    }


def _save_pending_commit(workspace_root: str | Path | None, data: dict[str, Any]) -> None:
    rd = _ruzgar_dir(workspace_root)
    if rd is None:
        return
    try:
        (rd / _COMMIT_PENDING_FILE).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def load_pending_commit(workspace_root: str | Path | None) -> dict[str, Any]:
    rd = _ruzgar_dir(workspace_root)
    if rd is None:
        return {}
    fp = rd / _COMMIT_PENDING_FILE
    if not fp.is_file():
        return {}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def clear_pending_commit(workspace_root: str | Path | None) -> None:
    rd = _ruzgar_dir(workspace_root)
    if rd is None:
        return
    try:
        (rd / _COMMIT_PENDING_FILE).unlink(missing_ok=True)
    except OSError:
        pass


def stage_commit_message(
    workspace_root: str | Path | None,
    commit_message: str,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    msg = (commit_message or "").strip()
    if not msg or len(msg) > 500:
        return {"ok": False, "error": "Geçerli commit mesajı gerekli (max 500 karakter)."}
    if _NO_VERIFY_RE.search(msg):
        return {"ok": False, "error": "--no-verify kullanılamaz."}

    scope = scope_rel or resolve_scope_rel(
        workspace_root, active_file=active_file, message=message
    )
    if not scope:
        return {"ok": False, "error": "Proje kapsamı gerekli."}

    snap = gather_git_snapshot(workspace_root, scope_rel=scope)
    pending = {
        "scope_rel": scope,
        "message": msg,
        "source": "user",
        "staged_at": time.time(),
        "snapshot": {
            "branch": snap.get("branch") if snap.get("ok") else "",
            "diff_stat": str((snap.get("diff_stat") or {}).get("output") or "")[:2000]
            if snap.get("ok")
            else "",
        },
    }
    _save_pending_commit(workspace_root, pending)
    return {"ok": True, "pending": pending, "version": FAZ17_VERSION}


def execute_pending_commit(
    workspace_root: str | Path | None,
    *,
    commit_message: str | None = None,
) -> dict[str, Any]:
    pending = load_pending_commit(workspace_root)
    msg = (commit_message or pending.get("message") or "").strip()
    scope = str(pending.get("scope_rel") or "")
    if not msg:
        return {"ok": False, "error": "Onaylı commit mesajı yok — önce `commit öner`."}
    if _NO_VERIFY_RE.search(msg):
        return {"ok": False, "error": "--no-verify yasak."}
    if not scope:
        return {"ok": False, "error": "Bekleyen commit kapsamı yok."}

    cwd = _scope_cwd(workspace_root, scope)
    if cwd is None or not _is_git_repo(cwd):
        return {"ok": False, "error": f"Git deposu yok: {scope}"}

    add_res = _run_git(["git", "add", "-A"], cwd, timeout=120)
    if not add_res.get("ok"):
        return {
            "ok": False,
            "error": f"git add başarısız: {(add_res.get('output') or '')[:200]}",
        }

    commit_res = _run_git(["git", "commit", "-m", msg], cwd, timeout=120)
    if commit_res.get("ok"):
        clear_pending_commit(workspace_root)
    return {
        "ok": bool(commit_res.get("ok")),
        "scope_rel": scope,
        "message": msg,
        "add": add_res,
        "commit": commit_res,
        "output": str(commit_res.get("output") or ""),
        "version": FAZ17_VERSION,
    }


def format_git_status_report(snap: dict[str, Any]) -> str:
    if not snap.get("ok"):
        return f"Ümit abi, git: {snap.get('error')}"
    lines = [
        f"Ümit abi, **git durum** — `{snap.get('scope_rel')}`",
        f"Dal: `{snap.get('branch') or '?'}`",
        "",
        "```text",
        str((snap.get("status") or {}).get("output") or "(boş)")[:6000],
        "```",
    ]
    ds = str((snap.get("diff_stat") or {}).get("output") or "").strip()
    if ds:
        lines.extend(["", "**diff --stat:**", "", "```text", ds[:4000], "```"])
    lines.append(f"\n({FAZ17_VERSION})")
    return "\n".join(lines)


def format_commit_suggest_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Ümit abi, commit önerisi: {result.get('error')}"
    snap = result.get("snapshot") or {}
    lines = [
        f"Ümit abi, **önerilen commit** (`{result.get('scope_rel')}`):",
        "",
        f"```\n{result.get('suggested')}\n```",
        f"Kaynak: {result.get('source')}",
        "",
    ]
    ds = str((snap.get("diff_stat") or {}).get("output") or "").strip()
    if ds:
        lines.extend(["**Değişiklik özeti:**", "", "```text", ds[:3500], "```"])
    lines.extend(
        [
            "",
            "Onaylamak için: `git commit onayla` veya atölyeden commit onayla.",
            f"({FAZ17_VERSION})",
        ]
    )
    return "\n".join(lines)


def format_commit_done_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Ümit abi, commit yapılamadı: {result.get('error')}"
    return (
        f"Ümit abi, commit kaydedildi — `{result.get('scope_rel')}`\n\n"
        f"Mesaj: `{result.get('message')}`\n\n"
        f"```text\n{str(result.get('output') or '')[:3000]}\n```\n\n"
        f"({FAZ17_VERSION})"
    )


def wants_git_status(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "git durum",
            "git status",
            "git özeti",
            "git ozeti",
        )
    )


def wants_git_diff(message: str) -> bool:
    low = _ascii_fold(message)
    if "git diff" in low or "git fark" in low:
        return True
    return "diff --stat" in low and "git" in low


def wants_commit_suggest(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "commit öner",
            "commit oner",
            "commit mesaj",
            "commit önerisi",
            "git commit öner",
        )
    )


def wants_commit_apply(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "git commit onayla",
            "commit onayla",
            "git kaydet",
            "commit uygula",
            "commit yap",
        )
    )


def wants_commit_cancel(message: str) -> bool:
    low = _ascii_fold(message)
    return any(k in low for k in ("commit iptal", "commit sil", "commit vazgeç"))


def _extract_commit_message_inline(message: str) -> str | None:
    m = re.search(
        r"(?:commit\s*:|git\s+commit\s+)(.+)$",
        message or "",
        re.I | re.M,
    )
    if m:
        return m.group(1).strip().strip("\"'`")
    return None


def maybe_instant_faz17(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None

    if wants_commit_cancel(message):
        clear_pending_commit(workspace_root)
        return "Ümit abi, bekleyen commit mesajı silindi."

    inline_msg = _extract_commit_message_inline(message)
    if inline_msg and not wants_commit_suggest(message):
        res = stage_commit_message(
            workspace_root,
            inline_msg,
            active_file=active_file,
            message=message,
        )
        if res.get("ok"):
            return (
                f"Ümit abi, commit mesajı hazır: `{inline_msg}` — "
                "`git commit onayla` ile kaydet."
            )
        return f"Commit hazırlanamadı: {res.get('error')}"

    if wants_commit_apply(message):
        res = execute_pending_commit(workspace_root)
        return format_commit_done_report(res)

    if wants_commit_suggest(message):
        hint = ""
        if ":" in message:
            hint = message.split(":", 1)[-1].strip()
        res = suggest_commit_message(
            workspace_root,
            active_file=active_file,
            message=message,
            user_hint=hint,
        )
        return format_commit_suggest_report(res)

    if wants_git_diff(message):
        snap = gather_git_snapshot(
            workspace_root, active_file=active_file, message=message
        )
        if not snap.get("ok"):
            return f"Ümit abi, git diff: {snap.get('error')}"
        out = str((snap.get("diff_stat") or {}).get("output") or "").strip()
        cached = str((snap.get("diff_cached_stat") or {}).get("output") or "").strip()
        lines = [
            f"Ümit abi, **git diff --stat** — `{snap.get('scope_rel')}`",
            "",
            "```text",
            (out or cached or "(değişiklik yok)")[:8000],
            "```",
            f"\n({FAZ17_VERSION})",
        ]
        return "\n".join(lines)

    if wants_git_status(message):
        snap = gather_git_snapshot(
            workspace_root, active_file=active_file, message=message
        )
        return format_git_status_report(snap)

    return None


def faz17_directive() -> str:
    return (
        "[GIT KÖPRÜSÜ — Faz 17 — projects/]\n"
        "Komutlar: `git durum` · `git diff` · `commit öner` · `git commit onayla`\n"
        "Commit asla `--no-verify` ile yapılmaz; push/reset yasak.\n"
    )


def post_patch_commit_hint() -> str:
    return "\nDeğişiklikleri kaydetmek için: `commit öner` → `git commit onayla`.\n"
