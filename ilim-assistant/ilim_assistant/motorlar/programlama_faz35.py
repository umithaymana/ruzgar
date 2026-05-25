# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 35: Tur-içi araç geri beslemesi.

Araç çıktısı (read/grep) geldikten sonra aynı turda ikinci LLM çağrısı → write.
"""

from __future__ import annotations

import os
from typing import Any, Callable

FAZ35_VERSION = "programlama-faz35-v1-2026-05-25"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ35", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def mid_turn_enabled() -> bool:
    return _enabled()


def max_followups_per_turn() -> int:
    try:
        return max(0, min(int(os.environ.get("RUZGAR_FAZ35_MAX", "1")), 2))
    except ValueError:
        return 1


def _body_has_write(body: str) -> bool:
    raw = body or ""
    if "@@write" in raw.lower():
        return True
    try:
        from ilim_assistant.motorlar.programlama_faz20 import extract_tool_calls

        for spec in extract_tool_calls(raw):
            if str(spec.get("tool") or "").lower() == "write":
                return True
    except Exception:
        pass
    return False


def _tool_results_have_write(tool_results: list[dict[str, Any]]) -> bool:
    return any(
        str(r.get("tool") or "").lower() == "write" and r.get("ok") for r in tool_results
    )


def should_mid_turn_followup(
    tool_results: list[dict[str, Any]],
    llm_body: str,
    *,
    tool_block: str = "",
) -> bool:
    """Keşif yapıldı ama yazım yok → aynı turda takip LLM."""
    if not mid_turn_enabled() or max_followups_per_turn() < 1:
        return False
    if not tool_results:
        return False
    if _body_has_write(llm_body) or _tool_results_have_write(tool_results):
        return False
    useful = [
        r
        for r in tool_results
        if r.get("ok") and str(r.get("output") or "").strip()
    ]
    if not useful:
        return False
    if not (tool_block or "").strip():
        return False
    return True


def build_mid_turn_user_message(
    tool_block: str,
    *,
    goal: str = "",
    turn: int = 1,
) -> str:
    return (
        f"[Faz 35 — tur-içi takip — tur {turn}]\n"
        "Araç sonuçları hazır. Şimdi hedefe uygun `@@write` veya "
        "`ruzgar-tool` write ile dosyayı güncelle.\n"
        "Gereksiz tekrar okuma yok; doğrudan patch yaz.\n\n"
        f"{tool_block.strip()}\n\n"
        f"Hedef: {(goal or '').strip()}\n"
    )


def faz35_directive() -> str:
    return (
        "[TUR-İÇİ ARAÇ — Faz 35]\n"
        "read/grep sonrası aynı turda patch yazılır; araç çıktısı modele geri beslenir.\n"
    )


def run_mid_turn_followup(
    *,
    llm_body: str,
    round_body: str,
    tool_results: list[dict[str, Any]],
    tool_block: str,
    goal: str,
    turn: int,
    agent_system: str,
    round_payload: str,
    model: str,
    active_prior: list,
    message: str,
    turn_plan: Any | None,
    workspace_root: Any,
    scope_rel: str,
    stream_fn: Callable[..., tuple[str, list[str]]],
) -> tuple[str, str, list[dict[str, Any]], list[str], bool]:
    """
    İkinci LLM + araçlar. Dönüş:
    (llm_body, round_body, tool_results, extra_profiles, did_followup)
    """
    block = (tool_block or "").strip()
    if not should_mid_turn_followup(tool_results, llm_body, tool_block=block):
        return llm_body, round_body, tool_results, [], False

    mid_user = build_mid_turn_user_message(block, goal=goal, turn=turn)
    mid_prior = list(active_prior) + [
        {"role": "assistant", "content": (llm_body or "").strip()},
        {"role": "user", "content": mid_user},
    ]
    follow_body, profiles = stream_fn(
        agent_system=agent_system,
        round_payload=round_payload,
        model=model,
        active_prior=mid_prior,
        message=message,
        turn_plan=turn_plan,
    )
    if not (follow_body or "").strip():
        return llm_body, round_body, tool_results, profiles, False

    combined_llm = (llm_body or "").rstrip() + "\n\n---\n\n[Faz 35 takip]\n" + follow_body
    combined_round = (round_body or llm_body or "").rstrip()

    extra_tools: list[dict[str, Any]] = []
    extra_block = ""
    try:
        from ilim_assistant.motorlar.programlama_faz20 import run_tools_from_reply

        extra_tools, extra_block = run_tools_from_reply(
            follow_body, workspace_root, scope_rel=scope_rel
        )
    except Exception:
        pass

    merged_tools = list(tool_results) + list(extra_tools)
    try:
        from ilim_assistant.motorlar.programlama_faz34 import apply_turn_tool_first

        merged_tools, faz34_block, _ = apply_turn_tool_first(
            merged_tools,
            follow_body,
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
    combined_round = combined_round + "\n\n---\n\n[Faz 35 takip yanıt]\n" + follow_body

    return combined_llm, combined_round, merged_tools, profiles, True
