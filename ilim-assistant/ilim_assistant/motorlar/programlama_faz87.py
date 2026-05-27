# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 87: Ajan E1 — doğrulama sonrası deterministik iyileştirme.

Pytest kırmızıyken bilinen health/version/service hatalarını LLM turu olmadan düzeltir.
Tur 1 mesajına pytest sözleşmesi ipucu ekler.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ87_VERSION = "programlama-faz87-v1-2026-05-27"

_SERVICE_IN_RETURN_RE = re.compile(
    r"""(['"]service['"]\s*:\s*)['"][^'"]*['"]""",
    re.I,
)
_OK_FALSE_RE = re.compile(
    r"""(['"]ok['"]\s*:\s*)['"]false['"]""",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ87", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz87_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def goal_wants_tests(goal: str) -> bool:
    low = _ascii_fold(goal)
    return any(
        k in low
        for k in ("test", "pytest", "gecir", "geçir", "dogrula", "doğrula", "verify")
    )


def _failure_hints(verify_output: str) -> set[str]:
    out = _ascii_fold(verify_output or "")
    hints: set[str] = set()
    if "test_health_has_version" in out or (
        "version" in out and "assert" in out
    ):
        hints.add("version")
    if "test_health_ok" in out or (
        "ok" in out and ("false" in out or "true" in out)
    ):
        hints.add("ok")
    if "service" in out and "assert" in out:
        hints.add("service")
    if not hints and "failed" in out:
        hints.update({"version", "ok"})
    return hints


def inject_health_contract_hint(
    base: str,
    scope_rel: str,
    goal: str,
) -> str:
    """Tur 1 — pytest health JSON sözleşmesi (E1 yazım kalitesi)."""
    if not _enabled() or not goal_wants_tests(goal):
        return base
    try:
        from ilim_assistant.motorlar.programlama_faz85 import _service_slug_from_scope

        svc = _service_slug_from_scope(scope_rel)
    except Exception:
        svc = "app"
    return (
        base.rstrip()
        + "\n\n[Faz 87 — pytest health sözleşmesi]\n"
        f'`GET /health` JSON: ok="true" (string), service="{svc}", version="0.1.0"+\n'
        "`tests/test_health.py` bu üç alanı kontrol eder.\n"
    )


def _apply_health_repairs(
    content: str,
    *,
    service: str,
    version: str,
    hints: set[str],
) -> tuple[str, list[str]]:
    from ilim_assistant.motorlar.programlama_faz85 import patch_main_py_content

    patched = content
    notes: list[str] = []
    if "ok" in hints:
        new = _OK_FALSE_RE.sub(r'\1"true"', patched, count=1)
        new = re.sub(
            r"""(['"]ok['"]\s*:\s*)\bFalse\b""",
            r'\1"true"',
            new,
            count=1,
        )
        if new != patched:
            patched = new
            notes.append("ok→true")
    if "service" in hints and service:
        new = _SERVICE_IN_RETURN_RE.sub(rf'\1"{service}"', patched, count=1)
        if new != patched:
            patched = new
            notes.append(f"service→{service}")
    if "version" in hints or not re.search(
        r"""['"]version['"]\s*:""", patched
    ):
        patched, did = patch_main_py_content(
            patched, service=service, version=version
        )
        if did:
            notes.append(f"version→{version}")
        elif '"version"' not in patched and "'version'" not in patched:
            patched, did = patch_main_py_content(
                patched, service=service, version=version
            )
            if did:
                notes.append(f"version→{version}")
    return patched, notes


def try_post_verify_heal(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
    verify_output: str = "",
) -> dict[str, Any] | None:
    """
    Doğrulama kırmızı → bilinen health hatalarını düzelt, yeniden doğrula.
    Başarılıysa {ok, verify_ok, writes_ok, detail, source}.
    """
    if not _enabled() or not goal_wants_tests(goal):
        return None
    try:
        from ilim_assistant.motorlar.programlama_faz85 import (
            _extract_version,
            _find_main_py,
            _service_slug_from_scope,
        )
        from ilim_assistant.motorlar.programlama_faz14 import (
            ensure_pytest_bootstrap,
            run_project_verify,
        )
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari
    except Exception:
        return None

    found = _find_main_py(workspace_root, scope_rel)
    if not found:
        return None
    rel_main, path_main = found
    hints = _failure_hints(verify_output)
    if not hints:
        hints = {"version", "ok"}
    try:
        original = path_main.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    service = _service_slug_from_scope(scope_rel)
    version = _extract_version(goal)
    patched, notes = _apply_health_repairs(
        original,
        service=service,
        version=version,
        hints=hints,
    )
    if patched == original:
        return None
    wrep = ProgramlamaAraclari(workspace_root).write(rel_main, patched)
    if not wrep.ok:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "detail": wrep.detail,
            "source": "post_verify_heal_faz87",
        }
    boot = ensure_pytest_bootstrap(workspace_root, scope_rel, goal=goal)
    verify = run_project_verify(workspace_root, scope_rel, goal=goal)
    verify_ok = bool(verify and verify.ok)
    lines = [
        "[Faz 87 — doğrulama sonrası düzeltme — LLM yok]",
        f"· `{rel_main}`: " + ", ".join(notes or ["health patch"]),
    ]
    if boot:
        lines.append(f"· test iskeleti: {len(boot)} dosya.")
    if verify_ok:
        lines.append(f"· yeniden doğrulama OK ({verify.preset}).")
    else:
        code = verify.exit_code if verify else "?"
        lines.append(f"· yeniden doğrulama kırmızı (exit={code}).")
    return {
        "ok": verify_ok,
        "verify_ok": verify_ok,
        "writes_ok": 1,
        "detail": "\n".join(lines),
        "source": "post_verify_heal_faz87",
        "healed": True,
    }


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz87"] = faz87_enabled()
    return out


def faz87_directive() -> str:
    return (
        "[Faz 87 — E1 post-verify heal]\n"
        "Ajan turu kırmızı → health/version/service otomatik düzeltme.\n"
        f"Kapat: RUZGAR_FAZ87=0 · {FAZ87_VERSION}\n"
    )
