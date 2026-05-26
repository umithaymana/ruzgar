# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 39: Görev tamamlama kilidi (P0).

Kota/boş tur erken çıkışını yumuşatır; keşif sonrası zorunlu yazım mandate LLM turu.
Görev modunda groq,kod önceliği güçlendirilir.
"""

from __future__ import annotations

import os
from typing import Any, Callable

FAZ39_VERSION = "programlama-faz39-v1-2026-05-25"
_DISCOVERY_TOOLS = frozenset({"read", "grep", "symbol", "goto"})


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ39", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def completion_gate_enabled() -> bool:
    return _enabled()


def mandate_followup_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_FAZ39_MANDATE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def code_agent_max_turns_effective() -> int:
    """Faz 56 → 20 tur; Faz 41 → 15 tur; Faz 39 → 12 tur (env ile override)."""
    try:
        from ilim_assistant.motorlar.programlama_faz56 import (
            long_task_v2_enabled,
            agent_max_turns_v2,
        )

        if long_task_v2_enabled():
            return agent_max_turns_v2()
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz41 import (
            long_task_enabled,
            long_task_max_turns,
        )

        if long_task_enabled():
            return long_task_max_turns()
    except Exception:
        pass
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz14 import code_agent_max_turns

            return code_agent_max_turns()
        except Exception:
            return 8
    try:
        v = int(os.environ.get("RUZGAR_CODE_AGENT_MAX_TURNS", "12"))
        return max(3, min(v, 20))
    except ValueError:
        return 12


def task_brain_profile_override() -> str | None:
    """Görev turunda tek profil zorlaması (ilk deneme)."""
    if not _enabled():
        return None
    try:
        from ilim_assistant.motorlar.programlama_faz57 import task_brain_profile_when_no_groq

        alt = task_brain_profile_when_no_groq()
        if alt:
            return alt
    except Exception:
        pass
    return os.environ.get("RUZGAR_FAZ39_TASK_BRAIN", "groq").strip() or "groq"


def programming_brain_chain_for_task() -> list[str]:
    try:
        from ilim_assistant.motorlar.programlama_faz26 import programming_brain_chain_ids

        chain = programming_brain_chain_ids()
    except Exception:
        chain = ["groq", "kod", "gemini"]
    if not _enabled():
        return chain
    preferred = ["groq", "kod"]
    out: list[str] = []
    for p in preferred:
        if p in chain and p not in out:
            out.append(p)
    for x in chain:
        if x not in out:
            out.append(x)
    merged = out or ["groq", "kod", "gemini"]
    try:
        from ilim_assistant.motorlar.programlama_faz57 import reorder_brain_chain_for_fc

        return reorder_brain_chain_for_fc(merged)
    except Exception:
        return merged


def turn_had_discovery(tool_results: list[dict[str, Any]] | None) -> bool:
    for r in tool_results or []:
        if r.get("ok") and str(r.get("tool") or "").lower() in _DISCOVERY_TOOLS:
            return True
    return False


def should_abort_loop_relaxed(
    state: Any,
    *,
    last_tool_results: list[dict[str, Any]] | None = None,
    max_turns: int = 8,
) -> tuple[bool, str]:
    """
    Faz 19 erken dur kuralları + keşif toleransı.
    """
    try:
        from ilim_assistant.motorlar.programlama_faz19 import should_abort_loop

        abort, reason = should_abort_loop(state)
    except Exception:
        return False, ""

    if not _enabled() or not abort:
        return abort, reason

    try:
        from ilim_assistant.motorlar.programlama_faz52 import (
            faz52_enabled,
            effective_max_turns,
        )

        if faz52_enabled():
            max_turns = effective_max_turns(
                base_max=max_turns,
                last_tool_results=last_tool_results,
                total_writes=int(getattr(state, "total_writes", 0) or 0),
            )
    except Exception:
        pass

    if turn_had_discovery(last_tool_results) and state.turns_done < max_turns - 1:
        if state.total_writes == 0 and "kota" in reason.lower():
            return (
                False,
                "Faz 39: keşif yapıldı — kota sonrası bir tur daha deneniyor.",
            )
        if state.empty_streak < 3 and "bos" in _ascii_fold(reason):
            return False, "Faz 39: keşif sonrası yazım için tur uzatıldı."

    return abort, reason


def _ascii_fold(text: str) -> str:
    return (text or "").lower().replace("ı", "i").replace("ş", "s")


def _has_write(llm_body: str, tool_results: list[dict[str, Any]]) -> bool:
    raw = llm_body or ""
    if "@@write" in raw.lower():
        return True
    try:
        from ilim_assistant.motorlar.programlama_faz20 import extract_tool_calls

        for spec in extract_tool_calls(raw):
            if str(spec.get("tool") or "").lower() == "write":
                return True
    except Exception:
        pass
    return any(
        str(r.get("tool") or "").lower() == "write" and r.get("ok")
        for r in (tool_results or [])
    )


def build_write_mandate_message(
    *,
    goal: str,
    scope_rel: str,
    tool_block: str,
    turn: int,
) -> str:
    return (
        f"[FAZ 39 — ZORUNLU YAZIM — tur {turn}]\n"
        f"Proje: `{scope_rel}`\n"
        "Keşif tamamlandı. Bu turda **mutlaka** dosya yaz:\n"
        "- `ruzgar-tool` write VEYA `@@write` ile patch\n"
        "- Ardından verify (pytest) çalıştır\n"
        "Sadece plan veya açıklama YASAK — somut kod değişikliği şart.\n\n"
        f"Hedef: {(goal or '').strip()}\n\n"
        f"{(tool_block or '').strip()}\n"
    )


def run_write_mandate_followup(
    *,
    llm_body: str,
    round_body: str,
    tool_results: list[dict[str, Any]],
    tool_block: str,
    goal: str,
    turn: int,
    scope_rel: str,
    agent_system: str,
    round_payload: str,
    model: str,
    active_prior: list,
    message: str,
    turn_plan: Any | None,
    workspace_root: Any,
    stream_fn: Callable[..., tuple[str, list[str]]],
) -> tuple[str, str, list[dict[str, Any]], list[str], bool]:
    """Keşif var, yazım yok — son şans LLM + araçlar."""
    if not mandate_followup_enabled():
        return llm_body, round_body, tool_results, [], False
    if _has_write(llm_body, tool_results):
        return llm_body, round_body, tool_results, [], False
    if not turn_had_discovery(tool_results):
        return llm_body, round_body, tool_results, [], False

    mandate_user = build_write_mandate_message(
        goal=goal,
        scope_rel=scope_rel,
        tool_block=tool_block,
        turn=turn,
    )
    mid_prior = list(active_prior) + [
        {"role": "assistant", "content": (llm_body or "").strip()[:8000]},
        {"role": "user", "content": mandate_user},
    ]
    body, profiles = stream_fn(
        agent_system=agent_system,
        round_payload=round_payload,
        model=model,
        active_prior=mid_prior,
        message=message,
        turn_plan=turn_plan,
    )
    if not (body or "").strip():
        return llm_body, round_body, tool_results, [], False

    combined_llm = (llm_body or "").rstrip() + "\n\n---\n\n[Faz 39 zorunlu yazım]\n" + body
    combined_round = (round_body or llm_body or "").rstrip()

    extra_tools: list[dict[str, Any]] = []
    extra_block = ""
    try:
        from ilim_assistant.motorlar.programlama_faz20 import run_tools_from_reply

        extra_tools, extra_block = run_tools_from_reply(
            body, workspace_root, scope_rel=scope_rel
        )
    except Exception:
        pass

    merged = list(tool_results) + list(extra_tools)
    try:
        from ilim_assistant.motorlar.programlama_faz34 import apply_turn_tool_first

        merged, faz34_block, _ = apply_turn_tool_first(
            merged,
            body,
            workspace_root,
            scope_rel,
            goal,
            turn,
        )
        if faz34_block:
            extra_block = (extra_block or "").rstrip() + "\n\n" + faz34_block
    except Exception:
        pass

    if extra_block:
        combined_round = combined_round + "\n\n" + extra_block
    combined_round = combined_round + "\n\n---\n\n[Faz 39 mandate yanıt]\n" + body

    return combined_llm, combined_round, merged, profiles, True


def faz39_directive() -> str:
    return (
        "[GÖREV TAMAMLAMA — Faz 39]\n"
        "Keşif sonrası yazım zorunlu; kota/boş turda ek tur toleransı.\n"
        "Görev beyin önceliği: groq → kod.\n"
        "Kapat: RUZGAR_FAZ39=0\n"
    )
