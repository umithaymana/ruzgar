# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 67: Özgür shell (onaylı, projects/ kapsamı).

Faz 43 whitelist argv üzerine: kullanıcı onayı ile shell=True komut.
İki adım: `shell istek:` → `shell onayla` · tek adım: `shell onay: komut`
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ67_VERSION = "programlama-faz67-v1-2026-05-26"
_PENDING_FILE = "shell_pending.json"
_PENDING_TTL_SEC = 600

_SHELL_ONAY_RE = re.compile(
    r"^\s*(?:shell|ozgur-shell|özgür\s*shell|ozgur\s*shell)\s+onay\s*:\s*(.+)$",
    re.I | re.S,
)
_SHELL_ISTEK_RE = re.compile(
    r"^\s*(?:shell|ozgur-shell|özgür\s*shell)\s+istek\s*:\s*(.+)$",
    re.I | re.S,
)
_SHELL_ONAYLA_RE = re.compile(
    r"^\s*shell\s+onayla(?:\s*:\s*([a-f0-9]{6,12}))?\s*$",
    re.I,
)
_SHELL_IPTAL_RE = re.compile(r"^\s*shell\s+iptal\s*$", re.I)
_SHELL_LISTE_RE = re.compile(r"^\s*shell\s+liste\s*$", re.I)

_BLOCK_META_RE = re.compile(r"[;&|`$><]")


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ67", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz67_enabled() -> bool:
    return _enabled()


def shell_timeout_sec() -> int:
    try:
        return max(15, min(600, int(os.environ.get("RUZGAR_FAZ67_TIMEOUT", "180"))))
    except ValueError:
        return 180


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _pending_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        d = root / ".ruzgar"
        d.mkdir(parents=True, exist_ok=True)
        return d / _PENDING_FILE
    except Exception:
        return None


def _token_for(scope_rel: str, command: str) -> str:
    raw = f"{scope_rel}\n{command}\n{int(time.time() // 60)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def load_pending(workspace_root: str | Path | None) -> dict[str, Any] | None:
    path = _pending_path(workspace_root)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    exp = float(data.get("expires_at") or 0)
    if exp and time.time() > exp:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    return data


def save_pending(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    command: str,
) -> dict[str, Any]:
    token = _token_for(scope_rel, command)
    now = time.time()
    payload = {
        "token": token,
        "scope_rel": scope_rel,
        "command": command,
        "created_at": now,
        "expires_at": now + _PENDING_TTL_SEC,
        "version": FAZ67_VERSION,
    }
    path = _pending_path(workspace_root)
    if path is None:
        return {"ok": False, "error": "workspace"}
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"ok": True, **payload}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:120]}


def clear_pending(workspace_root: str | Path | None) -> bool:
    path = _pending_path(workspace_root)
    if path is None:
        return False
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def validate_shell_command(command: str) -> tuple[bool, str]:
    cmd = (command or "").strip()
    if not cmd:
        return False, "boş komut"
    if len(cmd) > 2000:
        return False, "komut çok uzun (max 2000)"
    try:
        from ilim_assistant.motorlar.programlama_faz15 import is_dangerous_shell

        if is_dangerous_shell(cmd):
            return False, "tehlikeli komut (politika)"
    except Exception:
        pass
    if _BLOCK_META_RE.search(cmd):
        return False, "shell meta karakter yasak (; | & > < ` $)"
    low = _ascii_fold(cmd)
    if re.search(r"\bcd\s+\.\.", low) or " cd .." in low:
        return False, "üst dizine çıkış yasak"
    return True, ""


def wants_free_shell(message: str) -> bool:
    if not _enabled():
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    if (
        _SHELL_ONAY_RE.match(raw)
        or _SHELL_ISTEK_RE.match(raw)
        or _SHELL_ONAYLA_RE.match(raw)
        or _SHELL_IPTAL_RE.match(raw)
        or _SHELL_LISTE_RE.match(raw)
    ):
        return True
    low = _ascii_fold(raw)
    return any(
        k in low
        for k in (
            "shell onay:",
            "shell istek:",
            "shell onayla",
            "shell iptal",
            "ozgur-shell",
            "özgür shell",
        )
    )


def parse_shell_onay_command(message: str) -> str | None:
    m = _SHELL_ONAY_RE.match((message or "").strip())
    return m.group(1).strip() if m else None


def parse_shell_istek_command(message: str) -> str | None:
    m = _SHELL_ISTEK_RE.match((message or "").strip())
    return m.group(1).strip() if m else None


def run_free_shell(
    workspace_root: str | Path | None,
    scope_rel: str,
    command: str,
) -> dict[str, Any]:
    scope = (scope_rel or "").strip().replace("\\", "/")
    if not scope.startswith("projects/"):
        return {"ok": False, "error": "yalnızca projects/<ad>/ kapsamı"}
    ok_cmd, err = validate_shell_command(command)
    if not ok_cmd:
        return {"ok": False, "error": err, "scope_rel": scope}

    try:
        from ilim_assistant.motorlar.programlama_faz15 import _scope_cwd
    except Exception:
        return {"ok": False, "error": "scope cwd"}

    cwd = _scope_cwd(workspace_root, scope)
    if cwd is None:
        return {"ok": False, "error": f"dizin yok: {scope}", "scope_rel": scope}

    try:
        from ilim_assistant.approved_executor import run_argv

        code, out, err_s = run_argv(
            [command],
            timeout_sec=shell_timeout_sec(),
            shell=True,
            cwd=str(cwd),
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "scope_rel": scope}

    combined = "\n".join(x for x in (out, err_s) if x).strip()
    return {
        "ok": code == 0,
        "scope_rel": scope,
        "cwd": str(cwd),
        "command": command,
        "exit_code": code,
        "output": combined[:20000],
        "version": FAZ67_VERSION,
    }


def format_shell_report(result: dict[str, Any]) -> str:
    if result.get("pending"):
        return (
            f"Ümit abi, **shell isteği** kaydedildi (Faz 67).\n\n"
            f"Kapsam: `{result.get('scope_rel')}`\n"
            f"Komut: `{result.get('command')}`\n"
            f"Onay: `shell onayla` veya `shell onayla: {result.get('token')}`\n"
            f"İptal: `shell iptal` · süre: {_PENDING_TTL_SEC // 60} dk\n"
            f"({FAZ67_VERSION})"
        )
    if not result.get("ok") and result.get("error") and not result.get("output"):
        return (
            f"Ümit abi, özgür shell başarısız: {result.get('error')}\n"
            f"({FAZ67_VERSION})"
        )
    lines = [
        f"Ümit abi, **özgür shell** — `{result.get('scope_rel')}`",
        f"Komut: `{result.get('command')}`",
        "",
        f"Çıkış: **{int(result.get('exit_code') or 0)}**",
        "",
        "```text",
        str(result.get("output") or "(boş)")[:12000],
        "```",
        "",
        f"({FAZ67_VERSION})",
    ]
    return "\n".join(lines)


def stage_shell_request(
    workspace_root: str | Path | None,
    scope_rel: str,
    command: str,
) -> dict[str, Any]:
    ok_cmd, err = validate_shell_command(command)
    if not ok_cmd:
        return {"ok": False, "error": err}
    saved = save_pending(workspace_root, scope_rel=scope_rel, command=command)
    if not saved.get("ok"):
        return saved
    return {
        "ok": True,
        "pending": True,
        "scope_rel": scope_rel,
        "command": command,
        "token": saved.get("token"),
    }


def approve_and_run_shell(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    pending = load_pending(workspace_root)
    if not pending:
        return {"ok": False, "error": "bekleyen shell isteği yok"}
    if token and str(pending.get("token") or "") != token.strip().lower():
        return {"ok": False, "error": "token eşleşmedi"}
    scope = str(pending.get("scope_rel") or "")
    if scope_rel and scope_rel.replace("\\", "/") != scope:
        return {"ok": False, "error": "kapsam farklı — önce doğru projede onaylayın"}
    cmd = str(pending.get("command") or "")
    clear_pending(workspace_root)
    res = run_free_shell(workspace_root, scope, cmd)
    res["approved"] = True
    res["token"] = pending.get("token")
    return res


def maybe_instant_faz67(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None

    if _SHELL_IPTAL_RE.match(raw):
        clear_pending(workspace_root)
        return f"Ümit abi, bekleyen shell isteği iptal edildi.\n({FAZ67_VERSION})"

    if _SHELL_LISTE_RE.match(raw):
        p = load_pending(workspace_root)
        if not p:
            return f"Ümit abi, bekleyen shell yok.\n({FAZ67_VERSION})"
        return (
            f"Ümit abi, bekleyen shell:\n"
            f"  token: `{p.get('token')}`\n"
            f"  kapsam: `{p.get('scope_rel')}`\n"
            f"  komut: `{p.get('command')}`\n"
            f"Onay: `shell onayla`\n({FAZ67_VERSION})"
        )

    try:
        from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

        scope = resolve_scope_rel(
            workspace_root, active_file=active_file, message=message
        )
    except Exception:
        scope = None

    if _SHELL_ONAYLA_RE.match(raw):
        m = _SHELL_ONAYLA_RE.match(raw)
        tok = (m.group(1) or "").strip().lower() if m else None
        res = approve_and_run_shell(workspace_root, scope_rel=scope, token=tok)
        return format_shell_report(res)

    cmd_onay = parse_shell_onay_command(raw)
    if cmd_onay:
        if not scope:
            return "Ümit abi, proje kapsamı seçin (`projects/<ad>/`)."
        res = run_free_shell(workspace_root, scope, cmd_onay)
        return format_shell_report(res)

    cmd_istek = parse_shell_istek_command(raw)
    if cmd_istek:
        if not scope:
            return "Ümit abi, proje kapsamı seçin (`projects/<ad>/`)."
        staged = stage_shell_request(workspace_root, scope, cmd_istek)
        return format_shell_report(staged)

    return None


def execute_free_shell_tool(
    workspace_root: str | Path | None,
    scope_rel: str,
    command: str,
    *,
    approved: bool = False,
) -> dict[str, Any]:
    if not approved:
        staged = stage_shell_request(workspace_root, scope_rel, command)
        return {
            "ok": bool(staged.get("ok")),
            "tool": "free_shell",
            "output": format_shell_report(staged)[:8000],
            "pending": True,
        }
    res = run_free_shell(workspace_root, scope_rel, command)
    return {
        "ok": bool(res.get("ok")),
        "tool": "free_shell",
        "output": format_shell_report(res)[:8000],
        "exit_code": res.get("exit_code"),
    }


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz67"] = faz67_enabled()
    out["free_shell_timeout_sec"] = shell_timeout_sec()
    return out


def enrich_health_build_for_workspace(
    build: dict[str, Any] | None,
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    out = enrich_health_build(build)
    p = load_pending(workspace_root)
    out["shell_pending"] = bool(p)
    if p:
        out["shell_pending_token"] = p.get("token")
    return out


def faz67_directive() -> str:
    return (
        "[ÖZGÜR SHELL — Faz 67]\n"
        "Tek onay: `shell onay: git status` · İki adım: `shell istek: make build` → `shell onayla`\n"
        "Liste/iptal: `shell liste` · `shell iptal` · Yalnızca `projects/<ad>/` · Kapat: RUZGAR_FAZ67=0\n"
    )
