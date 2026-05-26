# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 52: Function calling birincil (Faz 40 sertleştirme).

- Görev modunda metin-only tur sonrası zorunlu yapılandırılmış araç kurtarma
- Keşif sonrası write+verify mandate → function calling (tool_choice=required)
- Keşif sonrası +1 tur kota toleransı (Faz 39 üzerine)
"""

from __future__ import annotations

import os
from typing import Any, Callable

FAZ52_VERSION = "programlama-faz52-v1-2026-05-26"

_WRITE_TOOLS = frozenset({"write"})
_VERIFY_TOOLS = frozenset({"verify"})
_DISCOVERY_TOOLS = frozenset({"read", "grep", "symbol", "goto", "refs"})


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ52", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz52_enabled() -> bool:
    return _enabled()


def structured_task_mode_enabled() -> bool:
    if not _enabled():
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz40 import structured_tools_enabled

        return structured_tools_enabled()
    except Exception:
        return False


def mandate_fc_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_FAZ52_MANDATE_FC", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def discovery_bonus_turns() -> int:
    """Keşif sonrası ek tur (kota erken çıkış yumuşatma)."""
    if not _enabled():
        return 0
    try:
        return max(0, min(int(os.environ.get("RUZGAR_FAZ52_DISCOVERY_BONUS", "1")), 2))
    except ValueError:
        return 1


def tool_choice_for_task(*, mandate: bool = False, recovery: bool = False) -> str:
    if not _enabled():
        return "auto"
    if mandate or recovery:
        return "required"
    return "auto"


def turn_had_no_tools(
    llm_body: str,
    tool_results: list[dict[str, Any]] | None,
) -> bool:
    if tool_results:
        return False
    raw = llm_body or ""
    if "@@write" in raw.lower():
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz40 import extract_tool_invocations

        if extract_tool_invocations(raw):
            return False
    except Exception:
        try:
            from ilim_assistant.motorlar.programlama_faz20 import extract_tool_calls

            if extract_tool_calls(raw):
                return False
        except Exception:
            pass
    return True


def _has_write(llm_body: str, tool_results: list[dict[str, Any]] | None) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz39 import _has_write as _f39

        return _f39(llm_body, tool_results)
    except Exception:
        return any(
            str(r.get("tool") or "").lower() == "write" and r.get("ok")
            for r in (tool_results or [])
        )


def _has_verify(tool_results: list[dict[str, Any]] | None) -> bool:
    return any(
        str(r.get("tool") or "").lower() == "verify"
        for r in (tool_results or [])
    )


def turn_had_discovery(tool_results: list[dict[str, Any]] | None) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz39 import turn_had_discovery as _f39d

        return _f39d(tool_results)
    except Exception:
        for r in tool_results or []:
            if r.get("ok") and str(r.get("tool") or "").lower() in _DISCOVERY_TOOLS:
                return True
        return False


def should_force_structured_recovery(
    llm_body: str,
    tool_results: list[dict[str, Any]] | None,
) -> bool:
    """Metin-only tur — function calling kurtarma turu."""
    if not structured_task_mode_enabled():
        return False
    if _has_write(llm_body, tool_results):
        return False
    return turn_had_no_tools(llm_body, tool_results)


def effective_max_turns(
    *,
    base_max: int,
    last_tool_results: list[dict[str, Any]] | None,
    total_writes: int = 0,
) -> int:
    bonus = discovery_bonus_turns()
    if bonus <= 0:
        return base_max
    if total_writes > 0:
        return base_max
    if turn_had_discovery(last_tool_results):
        return base_max + bonus
    return base_max


def should_abort_loop_relaxed_faz52(
    state: Any,
    *,
    last_tool_results: list[dict[str, Any]] | None = None,
    max_turns: int = 8,
) -> tuple[bool, str]:
    """Faz 39 + keşif bonus tur."""
    eff = effective_max_turns(
        base_max=max_turns,
        last_tool_results=last_tool_results,
        total_writes=int(getattr(state, "total_writes", 0) or 0),
    )
    try:
        from ilim_assistant.motorlar.programlama_faz39 import should_abort_loop_relaxed

        return should_abort_loop_relaxed(
            state,
            last_tool_results=last_tool_results,
            max_turns=eff,
        )
    except Exception:
        return False, ""


def build_mandate_fc_user(
    *,
    goal: str,
    scope_rel: str,
    tool_block: str,
    turn: int,
) -> str:
    return (
        f"[FAZ 52 — ZORUNLU ARAÇ — tur {turn}]\n"
        f"Proje: `{scope_rel}`\n"
        "Bu turda **function calling ile** şunları çağır:\n"
        "1. `write` — hedefe uygun dosya patch\n"
        "2. `verify` — pytest veya proje testi\n"
        "Metin-only plan/açıklama YASAK.\n\n"
        f"Hedef: {(goal or '').strip()}\n\n"
        f"{(tool_block or '').strip()}\n"
    )


def run_structured_recovery_turn(
    *,
    agent_system: str,
    goal: str,
    scope_rel: str,
    workspace_root: Any,
    turn_user: str = "",
) -> tuple[str, list[dict[str, Any]], str]:
    """Metin-only tur sonrası tool_choice=required döngüsü."""
    if not structured_task_mode_enabled():
        return "", [], ""
    try:
        from ilim_assistant.motorlar.programlama_faz40 import run_structured_tool_loop

        user = turn_user.strip() or f"Hedef: {goal}\nProje: {scope_rel}"
        user = (
            f"{user}\n\n[FAZ 52] Önceki tur metin-only kaldı. "
            "write ve verify araçlarını çağır."
        )
        return run_structured_tool_loop(
            system=agent_system,
            user=user,
            workspace_root=workspace_root,
            scope_rel=scope_rel,
            goal=goal,
            tool_choice=tool_choice_for_task(recovery=True),
        )
    except Exception as exc:
        return f"[Faz 52 recovery: {str(exc)[:120]}]", [], ""


def run_mandate_function_call(
    *,
    goal: str,
    scope_rel: str,
    tool_block: str,
    turn: int,
    workspace_root: Any,
    agent_system: str = "",
) -> tuple[str, list[dict[str, Any]], str, bool]:
    """
    Keşif sonrası write+verify — Groq/OpenAI tools (required).
  Dönüş: (text, tool_results, tool_block, ran_ok)
    """
    if not mandate_fc_enabled() or not structured_task_mode_enabled():
        return "", [], "", False

    user = build_mandate_fc_user(
        goal=goal,
        scope_rel=scope_rel,
        tool_block=tool_block,
        turn=turn,
    )
    system = (agent_system or "").strip() or (
        "Sen Rüzgar programlama ajanısın. Görev: write + verify araçları."
    )
    all_results: list[dict[str, Any]] = []
    texts: list[str] = []

    try:
        from ilim_assistant.motorlar.programlama_faz40 import (
            chat_completion_with_tools,
            extract_tool_invocations,
            run_tool_specs,
            _format_tool_block,
        )
    except Exception:
        return "", [], "", False

    for rnd in range(2):
        text, batch = chat_completion_with_tools(
            system,
            user if rnd == 0 else (
                f"[FAZ 52 tur {rnd + 1}] Hâlâ write/verify eksik. "
                f"Hedef: {goal}. Zorunlu araç çağrısı yap."
            ),
            scope_rel=scope_rel,
            tool_choice=tool_choice_for_task(mandate=True),
        )
        if text:
            texts.append(text)
        if batch:
            all_results.extend(batch)
        inv = extract_tool_invocations(text or "")
        if inv:
            all_results.extend(
                run_tool_specs(inv, workspace_root, scope_rel=scope_rel)
            )
        if _has_write("\n".join(texts), all_results) and _has_verify(all_results):
            break
        if rnd == 1:
            break

    block = ""
    try:
        block = _format_tool_block(all_results, tag="faz52-mandate")
    except Exception:
        pass
    combined = "\n\n".join(t for t in texts if t.strip())
    ran = bool(all_results) or _has_write(combined, all_results)
    return combined, all_results, block, ran


def run_write_mandate_followup_fc(
    *,
    llm_body: str,
    round_body: str,
    tool_results: list[dict[str, Any]],
    tool_block: str,
    goal: str,
    turn: int,
    scope_rel: str,
    agent_system: str,
    workspace_root: Any,
    stream_fn: Callable[..., tuple[str, list[str]]] | None = None,
    round_payload: str = "",
    model: str = "",
    active_prior: list | None = None,
    message: str = "",
    turn_plan: Any | None = None,
) -> tuple[str, str, list[dict[str, Any]], list[str], bool]:
    """
    Faz 39 mandate — önce function calling; başarısızsa stream_fn (Faz 39).
    """
    try:
        from ilim_assistant.motorlar.programlama_faz39 import (
            mandate_followup_enabled,
            run_write_mandate_followup,
            turn_had_discovery as _disc,
        )
    except Exception:
        return llm_body, round_body, tool_results, [], False

    if not mandate_followup_enabled():
        return llm_body, round_body, tool_results, [], False
    if not _disc(tool_results):
        return llm_body, round_body, tool_results, [], False
    if _has_write(llm_body, tool_results):
        return llm_body, round_body, tool_results, [], False

    fc_text, fc_tools, fc_block, fc_ok = run_mandate_function_call(
        goal=goal,
        scope_rel=scope_rel,
        tool_block=tool_block,
        turn=turn,
        workspace_root=workspace_root,
        agent_system=agent_system,
    )
    if fc_ok and (_has_write(fc_text, fc_tools) or _has_write("", fc_tools)):
        combined_llm = (llm_body or "").rstrip() + "\n\n---\n\n[Faz 52 mandate FC]\n" + (
            fc_text or "(araç)"
        )
        combined_round = (round_body or llm_body or "").rstrip()
        merged = list(tool_results) + list(fc_tools)
        if fc_block:
            combined_round = combined_round + "\n\n" + fc_block
        if fc_text:
            combined_round = combined_round + "\n\n---\n\n[Faz 52 mandate yanıt]\n" + fc_text
        return combined_llm, combined_round, merged, ["faz52-fc"], True

    if stream_fn is None:
        return llm_body, round_body, tool_results, [], False

    return run_write_mandate_followup(
        llm_body=llm_body,
        round_body=round_body,
        tool_results=tool_results,
        tool_block=tool_block,
        goal=goal,
        turn=turn,
        scope_rel=scope_rel,
        agent_system=agent_system,
        round_payload=round_payload,
        model=model,
        active_prior=list(active_prior or []),
        message=message,
        turn_plan=turn_plan,
        workspace_root=workspace_root,
        stream_fn=stream_fn,
    )


def faz52_directive() -> str:
    return (
        "[FUNCTION CALLING BİRİNCİL — Faz 52]\n"
        "Görev modu: metin-only tur → zorunlu araç kurtarma; keşif sonrası write+verify FC.\n"
        "Keşif bonus tur: +1 (RUZGAR_FAZ52_DISCOVERY_BONUS).\n"
        "Kapat: RUZGAR_FAZ52=0\n"
    )
