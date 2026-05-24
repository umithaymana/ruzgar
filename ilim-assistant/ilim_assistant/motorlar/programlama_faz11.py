# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 11: orkestra adımları (atölye + dashboard).

Akış: Plan → İndeks → Oku → LLM → Patch → Doğrula
"""

from __future__ import annotations

import os
from typing import Any

FAZ11_VERSION = "programlama-faz11-v1-2026-05-24"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ11", "1").strip().lower() not in ("0", "false", "no")


def _step(sid: str, label: str, status: str, detail: str = "") -> dict[str, str]:
    return {"id": sid, "label": label, "status": status, "detail": detail}


def build_programlama_orchestra_steps(
    message: str,
    workspace_root: str | None = None,
    *,
    active_file: str | None = None,
    phase: str = "prepare",
    patch_meta: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Faz 11 — programlama turu için ajan adım listesi."""
    if not _enabled():
        return []
    msg = (message or "").strip()
    steps: list[dict[str, str]] = [
        _step("plan", "İstek analizi", "done", "Programlama motoru"),
    ]
    scope = ""
    try:
        from ilim_assistant.motorlar.programlama_faz10 import resolve_scope_rel

        scope = resolve_scope_rel(workspace_root, active_file=active_file) or ""
    except Exception:
        pass
    if scope:
        steps.append(_step("index", "Workspace indeksi", "done", scope))
    else:
        steps.append(_step("index", "Workspace indeksi", "skip", "projects/ odak yok"))

    read_n = 0
    try:
        from ilim_assistant.motorlar.programlama_faz10 import expand_message_paths
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is not None:
            read_n = len(expand_message_paths(msg, workspace_root))
    except Exception:
        pass
    if "@@read" in msg.lower() or read_n:
        steps.append(
            _step("read", "Dosya okuma", "done", f"{read_n or '@@'} yol")
        )
    else:
        steps.append(_step("read", "Dosya okuma", "skip", "gerekirse @@read"))

    llm_status = "active" if phase == "llm" else "done"
    if phase == "prepare":
        llm_status = "skip"
    steps.append(_step("llm", "Kod / patch üretimi", llm_status))

    pm = patch_meta or {}
    action = str(pm.get("action") or "")
    if action == "applied":
        n = len(pm.get("applied") or [])
        steps.append(_step("patch", "Patch diske yazıldı", "done", f"{n} dosya"))
    elif action == "staged":
        steps.append(
            _step("patch", "Patch bekliyor", "active", "patch onayla")
        )
    elif action in ("none", "skip"):
        steps.append(_step("patch", "Patch", "skip"))
    else:
        steps.append(_step("patch", "Patch", "skip"))

    ver = pm.get("verify") if isinstance(pm.get("verify"), dict) else {}
    if ver.get("ok") is True:
        steps.append(_step("verify", "Doğrulama", "done", "geçti"))
    elif ver.get("ok") is False:
        steps.append(_step("verify", "Doğrulama", "active", "kırmızı"))
    elif action == "applied":
        steps.append(_step("verify", "Doğrulama", "skip", "atlandı"))
    else:
        steps.append(_step("verify", "Doğrulama", "skip"))

    return steps


def merge_orchestra_programlama(
    orch: dict[str, Any],
    message: str,
    workspace_root: str | None,
    *,
    active_file: str | None = None,
    phase: str = "prepare",
    patch_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mevcut orkestra sözlüğüne programlama adımlarını ekle."""
    if not _enabled():
        return orch
    steps = build_programlama_orchestra_steps(
        message,
        workspace_root,
        active_file=active_file,
        phase=phase,
        patch_meta=patch_meta,
    )
    if steps:
        orch = dict(orch or {})
        orch["agent_steps"] = steps
        orch["programlama_faz11"] = True
        orch["faz11_version"] = FAZ11_VERSION
    return orch


def orchestra_directive() -> str:
    return (
        "[PROGRAMLAMA ORKESTRA — Faz 11]\n"
        "Sıra: plan → indeks → oku → @@write → patch onayla → proje test.\n"
    )
