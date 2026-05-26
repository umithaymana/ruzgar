# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 68: ROK pilot + birleşik «konuşarak yap» niyeti (U0+U1).

Tüm «yap/ekle/düzelt…» cümleleri (aktif proje varken) otomatik kod ajanına gider.
Soru / selam → sohbet. Uzman komutlar → anlık katman (Faz 15–67).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from ilim_assistant.ruzgar_motor_kernel import (
    INTENT_CHAT,
    INTENT_COMMAND,
    INTENT_DO,
    classify_motor_intent,
    kernel_enabled,
    register_classifier,
    sse_event,
)

FAZ68_VERSION = "programlama-faz68-v1-2026-05-26"

_REGISTERED = False

_IMPLEMENTATION_RE = re.compile(
    r"(?:yap|olustur|oluştur|ekle|duzelt|düzelt|geçir|gecir|bitir|tamamla|yaz|güncelle|"
    r"guncelle|implement|fix|add|create|build|refactor|calistir|çalıştır|endpoint|"
    r"test\s+gecir|test\s+geçir)",
    re.I,
)
_QUESTION_ONLY_RE = re.compile(
    r"(?:\b(?:nedir|nasıl|nasil|ne\s+demek)\b|^(?:açıkla|acikla|anlat|why|what\s+is)\b)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ68", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz68_enabled() -> bool:
    return _enabled() and kernel_enabled()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_classifier("programlama", classify_programlama_intent)
    _REGISTERED = True


def classify_programlama_intent(
    message: str,
    *,
    mode_norm: str = "programlama",
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
    coding_mode: bool = False,
    motor_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """ROK programlama sınıflandırıcısı."""
    _ = coding_mode, motor_flags
    raw = (message or "").strip()
    if mode_norm != "programlama":
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}

    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}

    low = raw.lower()
    if (
        _QUESTION_ONLY_RE.search(raw.strip())
        or low.rstrip().endswith("?")
        or ("nedir" in low and not _IMPLEMENTATION_RE.search(raw))
    ) and "@@write" not in low:
        if not re.search(r"\b(?:yap|ekle|olustur|oluştur|geçir|gecir|bitir)\b", low, re.I):
            return {"intent": INTENT_CHAT, "reason": "question"}

    try:
        from ilim_assistant.motorlar.programlama_faz14 import (
            wants_code_agent_status,
            wants_code_agent_stop,
        )

        if wants_code_agent_stop(raw) or wants_code_agent_status(raw):
            return {"intent": INTENT_COMMAND, "reason": "agent_control"}
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_motoru import is_programlama_reserved_command

        if is_programlama_reserved_command(raw):
            low = raw.lower()
            if not any(
                k in low
                for k in (
                    "gorev:",
                    "görev:",
                    "iş:",
                    "is:",
                    "yap:",
                    "@@write",
                    "@@find",
                )
            ):
                return {"intent": INTENT_COMMAND, "reason": "reserved_instant"}
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz14 import parse_code_agent_task
        from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message

        if parse_code_agent_task(normalize_agent_message(raw, mode_norm=mode_norm)):
            return {
                "intent": INTENT_DO,
                "reason": "explicit_task",
                "start_agent": True,
            }
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz20 import wants_implementation_agent

        if wants_implementation_agent(raw, mode_norm):
            task_line = build_agent_task_line(
                raw,
                workspace_root,
                active_file=active_file,
            )
            return {
                "intent": INTENT_DO,
                "reason": "implementation",
                "start_agent": bool(task_line),
                "task_line": task_line,
                "block_reason": None if task_line else "proje_kapsami",
            }
    except Exception:
        pass

    if _IMPLEMENTATION_RE.search(raw) and "@@write" not in raw.lower():
        task_line = build_agent_task_line(
            raw,
            workspace_root,
            active_file=active_file,
        )
        if task_line:
            return {
                "intent": INTENT_DO,
                "reason": "action_with_scope",
                "start_agent": True,
                "task_line": task_line,
            }

    return {"intent": INTENT_CHAT, "reason": "conversation"}


def build_agent_task_line(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    """Doğal cümle → `görev: slug hedef` (aktif proje öncelikli)."""
    raw = (message or "").strip()
    if not raw:
        return None

    try:
        from ilim_assistant.motorlar.programlama_faz69 import ensure_scope_for_agent

        ens = ensure_scope_for_agent(
            raw, workspace_root, active_file=active_file
        )
        if ens.get("action") == "none" and not ens.get("ok"):
            return None
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz33 import (
            active_scope_from_context,
            build_implicit_task_line,
            normalize_for_agent,
        )

        scope = active_scope_from_context(workspace_root, active_file=active_file)
        if scope:
            slug = scope.split("/")[-1]
            goal = raw
            try:
                from ilim_assistant.motorlar.programlama_faz33 import resolve_project_slug

                rs = resolve_project_slug(raw, workspace_root, active_file=active_file)
                if rs and rs.lower() != slug.lower():
                    goal = raw
                elif raw.lower().startswith(slug.lower()):
                    goal = raw[len(slug) :].lstrip(" :-\t,.") or raw
            except Exception:
                pass
            if len(goal.strip()) >= 3:
                return f"görev: {slug} {goal.strip()}"

        implicit = build_implicit_task_line(
            raw,
            workspace_root,
            active_file=active_file,
            mode_norm="programlama",
        )
        if implicit:
            return implicit

        norm = normalize_for_agent(
            raw,
            "programlama",
            workspace_root=workspace_root,
            active_file=active_file,
        )
        if norm != raw and "görev:" in norm.lower():
            return norm
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz19 import parse_implicit_programming_task

        imp = parse_implicit_programming_task(raw)
        if imp:
            if str(imp).lower().startswith("görev:") or str(imp).lower().startswith("gorev:"):
                return str(imp)
            return f"görev: {imp}"
    except Exception:
        pass
    return None


def should_run_agent_via_kernel(
    message: str,
    mode_norm: str = "",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
) -> bool:
    """Faz 20 `should_run_unified_programming_agent` girişi."""
    if not _enabled():
        return _legacy_should_run(
            message,
            mode_norm,
            workspace_root=workspace_root,
            active_file=active_file,
        )
    ensure_kernel_registered()
    intent = classify_motor_intent(
        message,
        "programlama",
        mode_norm=mode_norm,
        workspace_root=workspace_root,
        active_file=active_file,
    )
    if intent.get("intent") != INTENT_DO:
        return False
    if intent.get("start_agent"):
        return True
    line = build_agent_task_line(
        message,
        workspace_root,
        active_file=active_file,
    )
    return bool(line)


def normalize_message_for_agent(
    message: str,
    mode_norm: str = "",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
) -> str:
    if not _enabled() or mode_norm != "programlama":
        try:
            from ilim_assistant.motorlar.programlama_faz33 import normalize_for_agent

            return normalize_for_agent(
                message,
                mode_norm,
                workspace_root=workspace_root,
                active_file=active_file,
            )
        except Exception:
            return message
    line = build_agent_task_line(
        message,
        workspace_root,
        active_file=active_file,
    )
    if line:
        return line
    try:
        from ilim_assistant.motorlar.programlama_faz33 import normalize_for_agent

        return normalize_for_agent(
            message,
            mode_norm,
            workspace_root=workspace_root,
            active_file=active_file,
        )
    except Exception:
        return message


def agent_plan_sse(message: str, *, scope_rel: str | None = None) -> dict[str, Any]:
    """Ajan başlamadan kısa plan olayı (ROK sözleşmesi)."""
    scope = scope_rel or "projects/…"
    preview = (message or "").strip()[:120]
    return sse_event(
        "status",
        phase="agent_plan",
        text=(
            f"Ümit abi, programlama ajanı başlıyor — `{scope}`\n"
            f"Hedef: {preview}{'…' if len((message or '')) > 120 else ''}"
        ),
        extra={"faz68": True, "version": FAZ68_VERSION},
    )


def _legacy_should_run(
    message: str,
    mode_norm: str,
    *,
    workspace_root: str | Path | None,
    active_file: str | None,
) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz33 import should_auto_programming_agent

        return should_auto_programming_agent(
            message,
            mode_norm,
            workspace_root=workspace_root,
            active_file=active_file,
        )
    except Exception:
        return False


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz68"] = faz68_enabled()
    out["motor_kernel"] = kernel_enabled()
    ensure_kernel_registered()
    return out


def faz68_directive() -> str:
    return (
        "[KONUŞARAK YAP — Faz 68 / ROK]\n"
        "Programlama sekmesinde yazmanız yeterli: «health'e version ekle, test geçir».\n"
        "Aktif proje: `projects/<ad>/` dosyası açık veya `proje sec: ad`.\n"
        "Kapat: RUZGAR_FAZ68=0 · Çekirdek: RUZGAR_MOTOR_KERNEL=0\n"
    )


# Modül importunda kayıt
ensure_kernel_registered()
