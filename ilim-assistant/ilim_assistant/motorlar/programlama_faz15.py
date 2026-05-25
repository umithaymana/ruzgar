# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 15: Terminal v2 (yalnızca projects/<ad>/).

Onaylı preset'ler: npm install/build/test, git status/diff.
Tehlikeli kabuk komutları reddedilir.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import ExecReport, repo_root

FAZ15_VERSION = "programlama-faz15-v1-2026-05-25"

_TERMINAL_PRESETS: dict[str, dict[str, Any]] = {
    "npm_install": {
        "label": "npm install",
        "argv": ["npm", "install"],
        "timeout": 300,
        "needs_node_modules": False,
    },
    "npm_build": {
        "label": "npm run build",
        "argv": ["npm", "run", "build"],
        "timeout": 300,
        "needs_package_json": True,
    },
    "npm_test": {
        "label": "npm test",
        "argv": ["npm", "test", "--if-present"],
        "timeout": 300,
        "needs_package_json": True,
    },
    "git_status": {
        "label": "git status",
        "argv": ["git", "status", "-sb"],
        "timeout": 60,
        "needs_git": True,
    },
    "git_diff": {
        "label": "git diff",
        "argv": ["git", "diff", "--stat"],
        "timeout": 120,
        "needs_git": True,
    },
}

_DANGEROUS_RE = re.compile(
    r"(?:^|[\s;&|])(?:rm\s+-rf|del\s+/[sf]|format\s+[a-z]:|"
    r"git\s+push\s+.*--force|git\s+reset\s+--hard|shutdown|reboot|"
    r"mkfs|curl\s+.*\|\s*sh|invoke-webrequest\s+.*\|\s*iex)",
    re.I,
)

_CMD_ALIASES: dict[str, str] = {
    "npm install": "npm_install",
    "npm run build": "npm_build",
    "npm run test": "npm_test",
    "npm test": "npm_test",
    "git status": "git_status",
    "git diff": "git_diff",
    "npm build": "npm_build",
}


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ15", "1").strip().lower() not in ("0", "false", "no")


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


def list_terminal_presets() -> list[dict[str, str]]:
    return [
        {"id": k, "label": str(v.get("label") or k)}
        for k, v in _TERMINAL_PRESETS.items()
    ]


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
    if root is None:
        return None
    if not scope.startswith(f"{_projects_base()}/"):
        return None
    cwd = root / scope.replace("/", os.sep)
    return cwd if cwd.is_dir() else None


def is_dangerous_shell(text: str) -> bool:
    return bool(_DANGEROUS_RE.search(text or ""))


def parse_terminal_preset(message: str) -> str | None:
    """Mesajdan izinli terminal preset kimliği."""
    raw = (message or "").strip()
    if not raw or is_dangerous_shell(raw):
        return None
    low = _ascii_fold(raw)
    if "terminal:" in low:
        rest = raw.split(":", 1)[-1].strip().lower()
        for phrase, pid in _CMD_ALIASES.items():
            if phrase in rest:
                return pid
    for phrase, pid in sorted(_CMD_ALIASES.items(), key=lambda x: -len(x[0])):
        if phrase in low:
            return pid
    if low.strip() in _TERMINAL_PRESETS:
        return low.strip()
    return None


def wants_terminal_command(message: str) -> bool:
    if not _enabled():
        return False
    return parse_terminal_preset(message) is not None


def run_terminal_preset(
    workspace_root: str | Path | None,
    preset_id: str,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    """Tek preset çalıştır — yalnızca projects/<ad>/ içinde."""
    pid = (preset_id or "").strip().lower()
    meta = _TERMINAL_PRESETS.get(pid)
    if not meta:
        return {"ok": False, "error": f"Bilinmeyen preset: {preset_id}"}

    scope = scope_rel or resolve_scope_rel(
        workspace_root, active_file=active_file, message=message
    )
    if not scope:
        return {
            "ok": False,
            "error": "Proje kapsamı gerekli — `projects/<ad>/` açın veya yol yazın.",
        }

    cwd = _scope_cwd(workspace_root, scope)
    if cwd is None:
        return {"ok": False, "error": f"Dizin yok: {scope}", "scope_rel": scope}

    if meta.get("needs_package_json") and not (cwd / "package.json").is_file():
        return {"ok": False, "error": "package.json yok — React/Node şablonu gerekli."}

    if meta.get("needs_git"):
        import shutil

        if not shutil.which("git"):
            return {"ok": False, "error": "git PATH'te yok."}

    argv = list(meta.get("argv") or [])
    timeout = int(meta.get("timeout") or 120)
    code, out, err = run_argv(argv, timeout_sec=timeout, cwd=str(cwd))
    combined = "\n".join(x for x in (out, err) if x).strip()

    return {
        "ok": code == 0,
        "preset": pid,
        "label": meta.get("label"),
        "scope_rel": scope,
        "cwd": str(cwd),
        "exit_code": code,
        "output": combined[:12000],
        "version": FAZ15_VERSION,
    }


def format_terminal_report(result: dict[str, Any]) -> str:
    if not result.get("ok") and result.get("error"):
        return f"Ümit abi, terminal: {result.get('error')}"
    pid = result.get("preset") or "?"
    scope = result.get("scope_rel") or "?"
    code = int(result.get("exit_code") or 0)
    lines = [
        f"Ümit abi, **{result.get('label') or pid}** — `{scope}`",
        "",
        f"Çıkış kodu: **{code}**",
        "",
        "```text",
        str(result.get("output") or "(boş)")[:8000],
        "```",
        "",
        f"({FAZ15_VERSION})",
    ]
    return "\n".join(lines)


def terminal_block_for_llm(
    workspace_root: str | Path | None,
    message: str,
    *,
    active_file: str | None = None,
) -> str:
    """Sohbet turunda terminal komutu varsa çıktı bloğu."""
    pid = parse_terminal_preset(message)
    if not pid:
        return ""
    res = run_terminal_preset(
        workspace_root,
        pid,
        active_file=active_file,
        message=message,
    )
    if not res.get("ok") and res.get("error"):
        return f"[TERMINAL — Faz 15 — HATA]\n{res.get('error')}\n"
    return (
        f"[TERMINAL — Faz 15 — {res.get('label')} @ {res.get('scope_rel')}]\n"
        f"exit={res.get('exit_code')}\n"
        f"```text\n{str(res.get('output') or '')[:6000]}\n```\n"
    )


def maybe_instant_faz15(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    pid = parse_terminal_preset(message)
    if not pid:
        return None
    res = run_terminal_preset(
        workspace_root,
        pid,
        active_file=active_file,
        message=message,
    )
    return format_terminal_report(res)


def faz15_directive() -> str:
    return (
        "[TERMINAL v2 — Faz 15 — yalnızca projects/]\n"
        "Komutlar: `npm install` · `npm run build` · `npm test` · "
        "`git status` · `git diff` · veya `terminal: npm build`\n"
        "Tehlikeli komutlar (rm -rf, push --force) reddedilir.\n"
    )


def exec_report_from_terminal(result: dict[str, Any]) -> ExecReport | None:
    if "exit_code" not in result:
        return None
    return ExecReport(
        preset=str(result.get("preset") or "terminal"),
        exit_code=int(result.get("exit_code") or 1),
        output=str(result.get("output") or result.get("error") or "")[:16000],
    )
