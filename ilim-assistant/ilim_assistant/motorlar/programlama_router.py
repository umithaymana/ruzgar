# Created by Ümit & Gökçenur
"""
Programlama motoru — tek giriş router.

Yollar:
  instant — LLM atlanır (komut / scaffold / onay)
  agent   — otonom görev döngüsü (Faz 14)
  chat    — normal programlama sohbeti
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any, Callable

PROG_ROUTER_VERSION = "programlama-router-v1-2026-06-15"

InstantHandler = Callable[..., str | dict[str, Any] | None]


class ProgRoute(str, Enum):
    INSTANT = "instant"
    AGENT = "agent"
    CHAT = "chat"


def router_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_ROUTER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def classify_route(
    message: str,
    mode_norm: str = "programlama",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
) -> ProgRoute:
    if mode_norm != "programlama":
        return ProgRoute.CHAT
    try:
        from ilim_assistant.motorlar.programlama_faz14 import should_run_code_agent_loop

        if should_run_code_agent_loop(
            message,
            mode_norm,
            workspace_root=workspace_root,
            active_file=active_file,
        ):
            return ProgRoute.AGENT
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_motoru import is_programlama_reserved_command

        if is_programlama_reserved_command(message):
            return ProgRoute.INSTANT
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_motoru import (
            wants_autonomous_code_debug,
            wants_self_scan,
        )

        if wants_autonomous_code_debug(message) or wants_self_scan(message):
            return ProgRoute.INSTANT
    except Exception:
        pass
    return ProgRoute.CHAT


def dispatch_instant_reply(
    message: str,
    mode_norm: str,
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
    editor_snippet: str | None = None,
) -> str | dict[str, Any] | None:
    """
    Anında yanıt — mevcut maybe_programlama_instant_reply gövdesine delege eder.
    Router açıkken önce rota sınıflandırması yapılır; chat rotası None döner.
    """
    if mode_norm != "programlama":
        return None
    if router_enabled():
        route = classify_route(
            message,
            mode_norm,
            workspace_root=workspace_root,
            active_file=active_file,
        )
        if route == ProgRoute.AGENT:
            return None
        if route == ProgRoute.CHAT:
            return None
    from ilim_assistant.motorlar.programlama_motoru import (
        _maybe_programlama_instant_reply_impl,
    )

    return _maybe_programlama_instant_reply_impl(
        message,
        mode_norm,
        workspace_root=workspace_root,
        active_file=active_file,
        editor_snippet=editor_snippet,
    )


def run_monorepo_router_smoke(workspace_root: str | Path | None) -> dict[str, object]:
    """S6 — router + patch + budget modülleri yüklü mü."""
    checks: dict[str, bool] = {}
    try:
        from ilim_assistant.motorlar.programlama_patch import run_monorepo_patch_smoke

        patch = run_monorepo_patch_smoke(workspace_root)
        checks["patch_smoke"] = bool(patch.get("ok"))
    except Exception:
        checks["patch_smoke"] = False
    try:
        from ilim_assistant.motorlar.programlama_context_budget import assemble_context, ContextPart

        out, rep = assemble_context(
            [ContextPart(key="a", text="x" * 100, priority=50)]
        )
        checks["context_budget"] = len(out) > 0 and rep.budget_chars >= 2000
    except Exception:
        checks["context_budget"] = False
    checks["router_classify"] = classify_route("görev: foo bar", "programlama") in (
        ProgRoute.AGENT,
        ProgRoute.INSTANT,
        ProgRoute.CHAT,
    )
    try:
        from ilim_assistant.motorlar.programlama_havuz_bridge import havuz_bridge_enabled

        checks["havuz_bridge"] = havuz_bridge_enabled()
    except Exception:
        checks["havuz_bridge"] = False
    ok = all(checks.values())
    return {
        "ok": ok,
        "checks": checks,
        "version": PROG_ROUTER_VERSION,
    }
