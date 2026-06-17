# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 43: Terminal v3 (geniş whitelist + güvenli özel komut).

Faz 15 preset'lerine ek: pip, pytest, uv, npm ci.
`terminal calistir: pip install httpx` — güvenli argv (shell yok).
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ43_VERSION = "programlama-faz43-v1-2026-05-25"

_EXTRA_PRESETS: dict[str, dict[str, Any]] = {
    "pip_install": {
        "label": "pip install -r requirements.txt",
        "argv": ["pip", "install", "-r", "requirements.txt"],
        "timeout": 300,
        "needs_requirements": True,
    },
    "pip_install_deps": {
        "label": "pip install (proje)",
        "argv": ["pip", "install", "."],
        "timeout": 300,
    },
    "pytest": {
        "label": "python -m pytest",
        "argv": ["python", "-m", "pytest", "-q", "--tb=short"],
        "timeout": 300,
        "needs_pytest": True,
    },
    "npm_ci": {
        "label": "npm ci",
        "argv": ["npm", "ci"],
        "timeout": 420,
        "needs_package_json": True,
    },
    "uv_sync": {
        "label": "uv sync",
        "argv": ["uv", "sync"],
        "timeout": 300,
        "needs_uv": True,
    },
}

_EXTRA_ALIASES: dict[str, str] = {
    "pip install": "pip_install_deps",
    "python -m pytest": "pytest",
    "pytest": "pytest",
    "npm ci": "npm_ci",
    "uv sync": "uv_sync",
    "git diff --stat": "git_diff",
    "git diff stat": "git_diff",
}

_SAFE_FIRST_TOKEN = frozenset(
    {"pip", "python", "npm", "uv", "pytest", "ruff", "node", "npx"}
)
_RUN_PREFIX_RE = re.compile(
    r"(?:terminal\s*calistir|terminal\s*run|calistir|çalıştır|calistir)\s*[:\"]?\s*(.+)$",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ43", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def terminal_v3_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def list_terminal_presets_v3() -> list[dict[str, str]]:
    from ilim_assistant.motorlar.programlama_faz15 import list_terminal_presets

    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for p in list_terminal_presets():
        pid = p.get("id") or ""
        if pid and pid not in seen:
            seen.add(pid)
            out.append(p)
    for k, v in _EXTRA_PRESETS.items():
        if k not in seen:
            seen.add(k)
            out.append({"id": k, "label": str(v.get("label") or k)})
    return out


def parse_safe_argv_command(message: str) -> list[str] | None:
    """Güvenli argv listesi — shell meta yok."""
    if not _enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None
    try:
        from ilim_assistant.motorlar.programlama_faz15 import is_dangerous_shell

        if is_dangerous_shell(raw):
            return None
    except Exception:
        pass
    m = _RUN_PREFIX_RE.search(raw)
    cmd = m.group(1).strip() if m else ""
    if not cmd:
        low = _ascii_fold(raw)
        if low.startswith("pip install"):
            cmd = raw.strip()
        elif "python -m pytest" in low or low.strip() == "pytest":
            cmd = "python -m pytest -q"
    if not cmd:
        return None
    if re.search(r"[;&|`$><]", cmd):
        return None
    try:
        argv = shlex.split(cmd, posix=os.name != "nt")
    except ValueError:
        return None
    if not argv:
        return None
    first = argv[0].lower()
    if first == "python" and len(argv) >= 3 and argv[1] == "-m":
        first = argv[2].lower()
    if first not in _SAFE_FIRST_TOKEN:
        return None
    if first == "pip" and len(argv) >= 2 and argv[1] not in (
        "install",
        "list",
        "show",
        "freeze",
    ):
        return None
    return argv


def extract_terminal_command_text(message: str) -> str:
    """görev: terminal çalıştır: pytest → terminal çalıştır: pytest"""
    raw = (message or "").strip()
    m = re.match(
        r"^\s*(?:görev|gorev)\s*:?\s+terminal\s+(.+)$",
        raw,
        re.I,
    )
    if m:
        rest = m.group(1).strip()
        if re.search(r"(?:calistir|çalıştır|run)\s*:", rest, re.I):
            return f"terminal calistir: {rest.split(':', 1)[-1].strip()}" if ":" in rest else f"terminal calistir: {rest}"
        return f"terminal calistir: {rest}"
    return raw


def is_misrouted_terminal_gorev(
    message: str,
    *,
    slug: str = "",
    goal: str = "",
) -> bool:
    """Terminal komutu yanlışlıkla görev/Faz85 yoluna düşmesin."""
    if wants_terminal_v3(message):
        return True
    sl = _ascii_fold(slug or "")
    if sl not in ("terminal", "term"):
        return False
    g = goal or message
    if re.search(r"(?:calistir|çalıştır|run)\s*:", g, re.I):
        return True
    low = _ascii_fold(g)
    return any(
        k in low
        for k in ("pytest", "pip install", "npm ci", "git status", "uv sync")
    )


def _scope_cwd(workspace_root: str | Path | None, scope_rel: str) -> Path | None:
    from ilim_assistant.motorlar.programlama_faz15 import _scope_cwd as _s15

    return _s15(workspace_root, scope_rel)


def _run_argv_in_scope(
    workspace_root: str | Path | None,
    scope_rel: str,
    argv: list[str],
    *,
    timeout: int = 300,
    label: str = "terminal",
) -> dict[str, Any]:
    cwd = _scope_cwd(workspace_root, scope_rel)
    if cwd is None:
        return {"ok": False, "error": f"Dizin yok: {scope_rel}", "scope_rel": scope_rel}
    code, out, err = run_argv(argv, timeout_sec=timeout, cwd=str(cwd))
    combined = "\n".join(x for x in (out, err) if x).strip()
    return {
        "ok": code == 0,
        "preset": label,
        "label": " ".join(argv)[:120],
        "scope_rel": scope_rel,
        "cwd": str(cwd),
        "exit_code": code,
        "output": combined[:16000],
        "argv": argv,
        "version": FAZ43_VERSION,
    }


def run_terminal_v3(
    workspace_root: str | Path | None,
    preset_or_message: str,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    """Faz 15 preset veya Faz 43 güvenli argv."""
    from ilim_assistant.motorlar.programlama_faz15 import (
        parse_terminal_preset,
        resolve_scope_rel,
        run_terminal_preset,
    )

    scope = scope_rel or resolve_scope_rel(
        workspace_root, active_file=active_file, message=message or preset_or_message
    )
    if not scope:
        return {"ok": False, "error": "Proje kapsamı gerekli (projects/<ad>/)."}

    pid = parse_terminal_preset(preset_or_message or message)
    if pid:
        return run_terminal_preset(
            workspace_root,
            pid,
            scope_rel=scope,
            message=message,
        )

    low = _ascii_fold(preset_or_message or message)
    for phrase, eid in sorted(_EXTRA_ALIASES.items(), key=lambda x: -len(x[0])):
        if phrase in low:
            pid = eid
            break
    else:
        pid = (preset_or_message or "").strip().lower()
    meta = _EXTRA_PRESETS.get(pid) if pid in _EXTRA_PRESETS else None
    if meta:
        cwd = _scope_cwd(workspace_root, scope)
        if cwd is None:
            return {"ok": False, "error": f"Dizin yok: {scope}"}
        if meta.get("needs_requirements") and not (cwd / "requirements.txt").is_file():
            return {"ok": False, "error": "requirements.txt yok"}
        if meta.get("needs_package_json") and not (cwd / "package.json").is_file():
            return {"ok": False, "error": "package.json yok"}
        if meta.get("needs_uv") and not shutil.which("uv"):
            return {"ok": False, "error": "uv PATH'te yok"}
        argv = list(meta.get("argv") or [])
        return _run_argv_in_scope(
            workspace_root,
            scope,
            argv,
            timeout=int(meta.get("timeout") or 300),
            label=pid,
        )

    argv = parse_safe_argv_command(preset_or_message or message)
    if argv:
        return _run_argv_in_scope(
            workspace_root,
            scope,
            argv,
            timeout=300,
            label="custom",
        )

    return {"ok": False, "error": "Tanınmayan terminal komutu (Faz 43 whitelist)."}


def format_terminal_report_v3(result: dict[str, Any]) -> str:
    if not result.get("ok") and result.get("error"):
        return f"Ümit abi, terminal v3: {result.get('error')}"
    ver = result.get("version") or FAZ43_VERSION
    lines = [
        f"Ümit abi, **terminal** — `{result.get('scope_rel')}`",
        f"Komut: `{result.get('label') or result.get('preset')}`",
        "",
        f"Çıkış: **{int(result.get('exit_code') or 0)}**",
        "",
        "```text",
        str(result.get("output") or "(boş)")[:10000],
        "```",
        "",
        f"({ver})",
    ]
    return "\n".join(lines)


def terminal_block_for_llm_v3(
    workspace_root: str | Path | None,
    message: str,
    *,
    active_file: str | None = None,
) -> str:
    from ilim_assistant.motorlar.programlama_faz15 import (
        parse_terminal_preset,
        wants_terminal_command,
    )

    if not wants_terminal_command(message) and not parse_safe_argv_command(message):
        low = _ascii_fold(message)
        if not any(
            k in low
            for k in ("pip install", "pytest", "npm ci", "uv sync", "terminal calistir")
        ):
            return ""
    res = run_terminal_v3(
        workspace_root,
        message,
        active_file=active_file,
        message=message,
    )
    if res.get("error") and not res.get("output"):
        return f"[TERMINAL v3 — HATA]\n{res.get('error')}\n"
    return (
        f"[TERMINAL v3 — {res.get('label')} @ {res.get('scope_rel')}]\n"
        f"exit={res.get('exit_code')}\n"
        f"```text\n{str(res.get('output') or '')[:8000]}\n```\n"
    )


def wants_terminal_v3(message: str) -> bool:
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz15 import wants_terminal_command

            return wants_terminal_command(message)
        except Exception:
            return False
    try:
        from ilim_assistant.motorlar.programlama_faz15 import wants_terminal_command

        if wants_terminal_command(message):
            return True
    except Exception:
        pass
    if parse_safe_argv_command(message):
        return True
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "pip install",
            "python -m pytest",
            "npm ci",
            "uv sync",
            "terminal calistir",
        )
    )


def maybe_instant_faz43(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    cmd_msg = extract_terminal_command_text(message)
    if not wants_terminal_v3(cmd_msg):
        return None
    res = run_terminal_v3(
        workspace_root,
        cmd_msg,
        active_file=active_file,
        message=cmd_msg,
    )
    return format_terminal_report_v3(res)


def sse_terminal_event(result: dict[str, Any], *, phase: str = "terminal_done") -> dict[str, Any]:
    """Atölye / SSE için terminal çıktı özeti."""
    return {
        "type": "terminal_output",
        "phase": phase,
        "ok": bool(result.get("ok")),
        "scope_rel": result.get("scope_rel"),
        "exit_code": result.get("exit_code"),
        "output_preview": str(result.get("output") or "")[:2000],
        "label": result.get("label"),
        "version": FAZ43_VERSION,
    }


def faz43_directive() -> str:
    return (
        "[TERMINAL v3 — Faz 43]\n"
        "Ek: `pip install` · `python -m pytest` · `npm ci` · `uv sync`\n"
        "Özel: `terminal calistir: pip install httpx` (whitelist, shell yok)\n"
        "Kapat: RUZGAR_FAZ43=0\n"
    )
