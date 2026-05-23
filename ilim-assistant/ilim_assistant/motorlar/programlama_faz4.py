# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 4: güvenlik denetimi, içerik filtresi, derin ortam kontrolü.
"""

from __future__ import annotations

import os
import re
import socket
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root
from ilim_assistant.motorlar.programlama_faz3 import (
    programlama_write_allowed,
    run_windows_env_scan,
)

FAZ4_VERSION = "programlama-faz4-v1-2026-05-20"

_DANGEROUS_CODE: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bos\.system\s*\(", re.I), "os.system"),
    (re.compile(r"subprocess\.[^(]+\([^)]*shell\s*=\s*True", re.I), "subprocess shell=True"),
    (re.compile(r"\beval\s*\(", re.I), "eval()"),
    (re.compile(r"\bexec\s*\(", re.I), "exec()"),
    (re.compile(r"__import__\s*\(\s*['\"]os['\"]", re.I), "__import__('os')"),
    (re.compile(r"Remove-Item\s+.*-Recurse\s+.*[Cc]:\\", re.I), "PowerShell toplu silme"),
    (re.compile(r"format\s+[a-z]:", re.I), "disk format"),
]


def write_guard_directive() -> str:
    return (
        "[YAZIM GÜVENLİĞİ — Faz 4]\n"
        "@@write ile .env, hafiza/, *.db, hafıza JSON dosyalarına yazma — reddedilir.\n"
        "Patch içinde os.system, eval, subprocess shell=True kullanma.\n"
        "«güvenlik tara» ile tam güvenlik raporu al.\n"
    )


def content_guard_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_CONTENT_GUARD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def validate_write_content(content: str) -> tuple[bool, str]:
    """@@write gövdesinde tehlikeli desenleri reddet."""
    if not content_guard_enabled():
        return True, ""
    body = content or ""
    for pat, label in _DANGEROUS_CODE:
        if pat.search(body):
            return False, f"Güvenlik: patch içinde yasak desen ({label})."
    return True, ""


def wants_security_scan(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "güvenlik tara",
            "guvenlik tara",
            "güvenlik kontrol",
            "guvenlik kontrol",
            "security audit",
            "güvenlik denetim",
        )
    )


def _port_listening(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def run_security_audit(workspace_root: str | Path | None = None) -> dict[str, Any]:
    """Yazım politikası + API portu + ortam (Faz 4)."""
    tests: list[dict[str, Any]] = []
    root = repo_root(workspace_root)

    def add(name: str, ok: bool, detail: str = "") -> None:
        tests.append({"name": name, "ok": bool(ok), "detail": detail})

    guard_on = os.environ.get("RUZGAR_PROG_WRITE_GUARD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )
    add("write_guard_enabled", guard_on, "RUZGAR_PROG_WRITE_GUARD")

    if root is not None:
        blocked, msg = programlama_write_allowed(root, "ilim-assistant/.env")
        add("write_blocks_env", not blocked and "Güvenlik" in msg, msg[:80])
        ok_py, _ = programlama_write_allowed(
            root, "ilim-assistant/ilim_assistant/chat_core.py"
        )
        add("write_allows_code", ok_py, "chat_core.py")
    else:
        add("write_blocks_env", False, "kök yok")
        add("write_allows_code", False, "kök yok")

    bad_code, creason = validate_write_content("import os\nos.system('x')")
    add("content_blocks_os_system", not bad_code, creason[:60])
    good_code, _ = validate_write_content("def hello():\n    return 1\n")
    add("content_allows_safe_code", good_code, "basit fonksiyon")

    port = 8779
    try:
        port = int(os.environ.get("RUZGAR_API_PORT", "8779"))
    except ValueError:
        pass
    add("api_port_listen", _port_listening(port), f"127.0.0.1:{port}")

    ia = root / "ilim-assistant" if root else None
    if ia and ia.is_dir():
        add("requirements_txt", (ia / "requirements.txt").is_file(), "requirements.txt")
        venv = ia / ".venv" / "Scripts" / "python.exe"
        add("venv_optional", venv.is_file(), str(venv) if venv.is_file() else "yok (isteğe bağlı)")
    else:
        add("requirements_txt", False, "ilim-assistant yok")

    env_root = (
        os.environ.get("LOCAL_TOOLS_ROOT", "").strip()
        or os.environ.get("RUZGAR_EXEC_CWD", "").strip()
    )
    if root is not None:
        add("workspace_resolved", True, str(root))
    else:
        add("workspace_resolved", False, "workspace_root / LOCAL_TOOLS_ROOT gerekir")
        add("local_tools_root_env", bool(env_root), env_root or "boş")

    failures = [
        t["name"]
        for t in tests
        if not t.get("ok") and t["name"] not in ("venv_optional",)
    ]
    return {
        "ok": len(failures) == 0,
        "version": FAZ4_VERSION,
        "tests": tests,
        "failures": failures,
    }


def append_faz4_self_scan_tests(
    tests: list[dict[str, Any]],
    workspace_root: str | Path | None = None,
) -> None:
    """kendini tara raporuna Faz 4 maddelerini ekle."""
    sec = run_security_audit(workspace_root)
    for t in sec.get("tests") or []:
        if t.get("name") == "venv_optional":
            continue
        tests.append(t)


def format_security_scan_report(workspace_root: str | Path | None = None) -> str:
    data = run_security_audit(workspace_root)
    lines = [
        "Ümit abi, Programlama güvenlik denetimi (Faz 4):",
        f"Genel: {'GEÇTİ' if data.get('ok') else 'UYARI'}",
        "",
    ]
    for t in data.get("tests") or []:
        mark = "✓" if t.get("ok") else "✗"
        name = t.get("name", "?")
        detail = (t.get("detail") or "").strip()
        note = " (isteğe bağlı)" if name == "venv_optional" else ""
        lines.append(f"{mark} {name}{note}" + (f" — {detail[:90]}" if detail else ""))
    if not data.get("ok"):
        lines.extend(
            [
                "",
                "Kritik maddeler için patch değil ortam/ayar düzeltmesi gerekir.",
            ]
        )
    return "\n".join(lines)
