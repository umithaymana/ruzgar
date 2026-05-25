# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 23: görev modu otomatik uygula + 5 dk bütçe.

Otonom görev / birleşik ajan turunda patch onayı atlanır; süre varsayılan 300 sn.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

FAZ23_VERSION = "programlama-faz23-v1-2026-05-25"
_TASK_MODE_ENV = "RUZGAR_CODE_AGENT_TASK_MODE"
_LEGACY_BUDGET_DEFAULT = 120.0
_TASK_BUDGET_DEFAULT = 300.0


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ23", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def task_mode_active() -> bool:
    return os.environ.get(_TASK_MODE_ENV, "").strip() == "1"


def task_auto_apply_enabled() -> bool:
    """Görev döngüsünde @@write / ruzgar-tool doğrudan diske."""
    if not _enabled():
        return os.environ.get("RUZGAR_AGENT_AUTO_APPLY", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )
    if task_mode_active():
        return True
    return os.environ.get("RUZGAR_AGENT_AUTO_APPLY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def resolve_code_agent_budget_sec() -> float:
    """Env varsa onu kullan; Faz 41 → 900 sn; Faz 23 açıkken 300 sn."""
    try:
        from ilim_assistant.motorlar.programlama_faz41 import (
            long_task_budget_sec,
            long_task_enabled,
        )

        if long_task_enabled():
            return long_task_budget_sec()
    except Exception:
        pass
    raw = os.environ.get("RUZGAR_CODE_AGENT_BUDGET_SEC", "").strip()
    if raw:
        try:
            return max(30.0, float(raw))
        except ValueError:
            pass
    if _enabled():
        return _TASK_BUDGET_DEFAULT
    return _LEGACY_BUDGET_DEFAULT


def code_agent_budget_sec() -> float:
    return resolve_code_agent_budget_sec()


def budget_exceeded(start_mono: float) -> bool:
    return (time.perf_counter() - start_mono) >= code_agent_budget_sec()


def max_task_file_writes() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_TASK_MAX_FILE_WRITES", "32")), 64))
    except ValueError:
        return 32


def enter_task_mode() -> None:
    """Otonom görev başında — patch onaysız, 5 dk bütçe."""
    os.environ[_TASK_MODE_ENV] = "1"
    if task_auto_apply_enabled():
        os.environ["RUZGAR_FAZ10_AUTO_PATCH"] = "1"


def exit_task_mode() -> None:
    os.environ.pop(_TASK_MODE_ENV, None)


@contextmanager
def task_mode_context() -> Iterator[None]:
    enter_task_mode()
    try:
        yield
    finally:
        exit_task_mode()


def effective_auto_patch_for_task() -> bool:
    """Faz 16 — görev modunda otomatik diske yaz."""
    if task_mode_active() and task_auto_apply_enabled():
        return True
    raw = os.environ.get("RUZGAR_FAZ10_AUTO_PATCH", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    return False


def apply_agent_turn_patches(
    reply_body: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
) -> dict[str, Any]:
    """Tur sonu — görev modunda kalan @@write bloklarını uygula."""
    if not task_auto_apply_enabled():
        return {"action": "skip"}
    try:
        from ilim_assistant.motorlar.programlama_faz16 import process_reply_patches_v16

        os.environ["RUZGAR_FAZ10_AUTO_PATCH"] = "1"
        return process_reply_patches_v16(
            reply_body,
            workspace_root,
            scope_rel=scope_rel,
            skip_if_debug_loop=False,
        )
    except Exception as exc:
        return {"action": "error", "error": str(exc)[:200]}


def finalize_agent_patches(
    reply_body: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    skip_if_debug_loop: bool = False,
) -> dict[str, Any]:
    """Görev bitişi — bekleyen patch yok; kalan @@write uygula."""
    if task_mode_active() and task_auto_apply_enabled():
        return apply_agent_turn_patches(
            reply_body,
            workspace_root,
            scope_rel=scope_rel,
        )
    try:
        from ilim_assistant.motorlar.programlama_faz10 import process_assistant_reply_patches

        return process_assistant_reply_patches(
            reply_body,
            workspace_root,
            scope_rel=scope_rel,
            skip_if_debug_loop=skip_if_debug_loop,
        )
    except Exception:
        return {"action": "skip"}


def task_success_met(
    *,
    verify_ok: bool,
    writes_ok: int,
    min_writes: int = 1,
) -> bool:
    """Görev başarı ölçütü: doğrulama yeşil + en az bir yazım."""
    return bool(verify_ok) and writes_ok >= min_writes


def format_task_mode_status(scope_rel: str, budget_sec: float) -> str:
    auto = "açık" if task_auto_apply_enabled() else "kapalı"
    return (
        f"Görev modu (Faz 23) — `{scope_rel}` · "
        f"bütçe {int(budget_sec)} sn · otomatik patch {auto}"
    )


def faz23_directive() -> str:
    return (
        "[GÖREV MODU — Faz 23]\n"
        "Otonom görevde patch onayı yok; @@write ve ruzgar-tool write doğrudan diske.\n"
        f"Varsayılan süre: {int(_TASK_BUDGET_DEFAULT)} sn — `RUZGAR_CODE_AGENT_BUDGET_SEC` ile değişir.\n"
        "Kapat: RUZGAR_FAZ23=0 veya RUZGAR_AGENT_AUTO_APPLY=0\n"
    )
