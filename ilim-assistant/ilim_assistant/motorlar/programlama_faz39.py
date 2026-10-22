# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 39: Görev tamamlama kilidi (P0).

Kota/boş tur erken çıkışını yumuşatır; keşif sonrası zorunlu yazım mandate LLM turu.
Görev modunda groq,kod önceliği güçlendirilir.
"""

from __future__ import annotations

import os
from typing import Any, Callable

FAZ39_VERSION = "programlama-faz39-v1.1-2026-10-22"
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
    """Faz 80 mega → 30 tur; Faz 56 → 20 tur; Faz 41 → 15 tur; Faz 39 → 12 tur.

    `RUZGAR_CODE_AGENT_MAX_TURNS` açıkça set ise **üst tavan** (canlı E2 pil).
    """
    env_cap: int | None = None
    raw_cap = os.environ.get("RUZGAR_CODE_AGENT_MAX_TURNS", "").strip()
    if raw_cap:
        try:
            env_cap = max(1, min(int(raw_cap), 40))
        except ValueError:
            env_cap = None

    def _cap(n: int) -> int:
        if env_cap is None:
            return n
        return min(n, env_cap)

    try:
        from ilim_assistant.motorlar.programlama_faz80 import (
            agent_max_turns_mega,
            mega_context_active,
        )

        if mega_context_active():
            return _cap(agent_max_turns_mega())
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz56 import (
            long_task_v2_enabled,
            agent_max_turns_v2,
        )

        if long_task_v2_enabled():
            return _cap(agent_max_turns_v2())
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz41 import (
            long_task_enabled,
            long_task_max_turns,
        )

        if long_task_enabled():
            return _cap(long_task_max_turns())
    except Exception:
        pass
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz14 import code_agent_max_turns

            return _cap(code_agent_max_turns())
        except Exception:
            return _cap(8)
    if env_cap is not None:
        return env_cap
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
    raw = os.environ.get("RUZGAR_FAZ39_TASK_BRAIN", "").strip()
    if raw:
        return raw
    try:
        from ilim_assistant.motorlar.programlama_faz85 import ollama_available

        return "kod" if ollama_available() else "groq"
    except Exception:
        return "groq"


def programming_brain_chain_for_task() -> list[str]:
    try:
        from ilim_assistant.motorlar.programlama_faz26 import programming_brain_chain_ids

        chain = programming_brain_chain_ids()
    except Exception:
        chain = ["groq", "kod", "gemini"]
    if not _enabled():
        return chain
    preferred = ["kod", "denge", "groq"]
    out: list[str] = []
    for p in preferred:
        if p in chain and p not in out:
            out.append(p)
    for x in chain:
        if x not in out:
            out.append(x)
    merged = out or ["kod", "groq", "gemini"]
    try:
        from ilim_assistant.motorlar.programlama_faz85 import local_first_brain_chain

        merged = local_first_brain_chain(merged)
    except Exception:
        pass
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
    """@@write / write aracı / @@patch (D2 — patch de yazım sayılır)."""
    raw = llm_body or ""
    low = raw.lower()
    if "@@write" in low or "@@patch" in low:
        return True
    if "```search-replace" in low or "```patch" in low:
        if "<<<search" in low or "<<<SEARCH" in raw:
            return True
    try:
        from ilim_assistant.motorlar.programlama_faz20 import extract_tool_calls

        for spec in extract_tool_calls(raw):
            if str(spec.get("tool") or "").lower() in ("write", "patch", "search_replace"):
                return True
    except Exception:
        pass
    write_tools = frozenset({"write", "patch", "search_replace", "apply_patch"})
    return any(
        str(r.get("tool") or "").lower() in write_tools and r.get("ok")
        for r in (tool_results or [])
    )


def turn_was_read_only(
    llm_body: str,
    tool_results: list[dict[str, Any]] | None,
) -> bool:
    """Keşif var, yazım yok — mandate / yazım-önce tetikleyici (D2)."""
    if _has_write(llm_body, tool_results or []):
        return False
    return turn_had_discovery(tool_results)


def build_write_mandate_message(
    *,
    goal: str,
    scope_rel: str,
    tool_block: str,
    turn: int,
) -> str:
    multi_hint = ""
    try:
        from ilim_assistant.motorlar.programlama_faz56 import looks_like_multi_file_task
        from ilim_assistant.motorlar.programlama_faz85 import goal_wants_agent_path

        if looks_like_multi_file_task(goal) or goal_wants_agent_path(goal):
            multi_hint = (
                "\nE2/çok dosya: her hedef dosyaya ayrı @@patch + search-replace "
                "veya @@write.\n"
                "Boş tur / yalnız grep-read YASAK — en az bir dosya içeriği değişmeli.\n"
            )
            try:
                from ilim_assistant.motorlar.programlama_faz103_e2 import (
                    e2_write_template_nudge,
                )

                multi_hint += e2_write_template_nudge(scope_rel, goal) or ""
            except Exception:
                pass
    except Exception:
        pass
    fields_hint = ""
    try:
        from ilim_assistant.motorlar.programlama_faz85 import (
            extract_health_fields,
            _goal_wants_health_extra_fields,
        )

        if _goal_wants_health_extra_fields(goal or ""):
            fields = extract_health_fields(goal or "")
            status_val = fields.get("status") or "ok"
            fields_hint = (
                f"\nHealth: `{scope_rel}/app/main.py` health() return'e "
                f'`"status": "{status_val}"` ekle — boş tur YASAK.\n'
            )
    except Exception:
        pass
    return (
        f"[FAZ 39 — ZORUNLU YAZIM — tur {turn}]\n"
        f"Proje: `{scope_rel}`\n"
        "Bu turda **mutlaka** dosya yaz (önceki turda yazım yoktu veya keşif bitti):\n"
        "- İlk satır: `@@patch yol` (fence İÇİNE alma) + ```search-replace```\n"
        "- veya `@@write` / `ruzgar-tool` write\n"
        "- Ardından verify (pytest) çalıştır\n"
        "Salt okuma / yalnız grep-read / plan-yalnız YASAK — somut kod değişikliği şart.\n"
        f"{multi_hint}{fields_hint}\n"
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
    """Yazım yok — son şans LLM + araçlar (keşif VEYA E2/çok dosya niyeti)."""
    if not mandate_followup_enabled():
        return llm_body, round_body, tool_results, [], False
    if _has_write(llm_body, tool_results):
        return llm_body, round_body, tool_results, [], False
    force_write = False
    try:
        from ilim_assistant.motorlar.programlama_faz56 import looks_like_multi_file_task
        from ilim_assistant.motorlar.programlama_faz85 import (
            goal_wants_agent_path,
            _goal_wants_health_extra_fields,
        )

        force_write = (
            looks_like_multi_file_task(goal)
            or goal_wants_agent_path(goal)
            or _goal_wants_health_extra_fields(goal)
        )
    except Exception:
        force_write = False
    if not turn_had_discovery(tool_results) and not force_write:
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
