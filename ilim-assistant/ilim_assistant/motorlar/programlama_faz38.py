# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 38: Uyum şeridi UI + iç içe araç döngüsü + delege zinciri.

- SSE agent_step olaylarına canlı uyum skoru eklenir (Faz 37).
- Tur içinde tool → LLM → tool döngüsü (Faz 35 genişletmesi, max 3).
- Ana Motor delegasyonunda aynı Faz 35–37 zinciri bildirimi.
"""

from __future__ import annotations

import os
from typing import Any, Callable

FAZ38_VERSION = "programlama-faz38-v1-2026-05-25"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ38", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz38_enabled() -> bool:
    return _enabled()


def nested_tool_loop_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_FAZ38_NESTED", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def max_nested_depth() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_FAZ38_MAX_DEPTH", "3")), 4))
    except ValueError:
        return 3


def compliance_sse_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_FAZ38_COMPLIANCE_SSE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


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


def _has_write(llm_body: str, tool_results: list[dict[str, Any]]) -> bool:
    return _body_has_write(llm_body) or _tool_results_have_write(tool_results)


def _build_tool_block_from_results(
    tool_results: list[dict[str, Any]],
    *,
    extra: str = "",
) -> str:
    lines = ["[ARAÇ SONUÇLARI — Faz 38]"]
    for i, r in enumerate(tool_results or [], 1):
        tid = str(r.get("tool") or "?")
        ok = "OK" if r.get("ok") else "HATA"
        out = str(r.get("output") or r.get("error") or "")[:1200]
        lines.append(f"{i}. {tid} [{ok}]")
        if out.strip():
            lines.append("```text")
            lines.append(out.strip())
            lines.append("```")
    block = "\n".join(lines)
    if extra.strip():
        block = block + "\n\n" + extra.strip()
    return block


def live_compliance_snapshot(
    workspace_root: Any,
    *,
    scope_rel: str = "",
) -> dict[str, Any]:
    """Son oturumdan canlı skor — SSE/UI için."""
    if not compliance_sse_enabled():
        return {}
    try:
        from ilim_assistant.motorlar.programlama_faz37 import (
            build_compliance_report,
            compute_compliance_score,
        )

        rep = build_compliance_report(workspace_root)
        if not rep.get("ok"):
            return {}
        data = rep.get("report") or {}
        turns = data.get("recent_turns") or []
        scorecard = compute_compliance_score(turns) if turns else data
        return {
            "score": int(scorecard.get("score") or data.get("score") or 0),
            "grade": str(scorecard.get("grade") or data.get("grade") or "—"),
            "turn_count": int(
                scorecard.get("turn_count") or len(turns) or 0
            ),
            "last_scope": (data.get("last_scope") or scope_rel or "")[:120],
            "version": FAZ38_VERSION,
        }
    except Exception:
        return {}


def enrich_agent_step_event(
    event: dict[str, Any],
    workspace_root: Any,
    *,
    scope_rel: str = "",
) -> dict[str, Any]:
    """agent_step SSE olayına compliance kartı ekler."""
    if not compliance_sse_enabled() or not event:
        return event
    snap = live_compliance_snapshot(workspace_root, scope_rel=scope_rel)
    if not snap:
        return event
    out = dict(event)
    ca = dict(out.get("code_agent") or {})
    ca["compliance"] = snap
    ca["faz38"] = True
    out["code_agent"] = ca
    out["compliance"] = snap
    return out


def delegation_status_text(*, scope_rel: str, goal: str) -> str:
    g = (goal or "").strip()[:80]
    s = (scope_rel or "").strip()
    return (
        f"Ana Motor → Programlama delege (Faz 38) — `{s}`"
        + (f" — {g}" if g else "")
        + " · tur-içi araç + uyum skoru aktif"
    )


def delegation_footer(
    workspace_root: Any,
    *,
    scope_rel: str,
    success: bool,
    turns_used: int,
) -> str:
    snap = live_compliance_snapshot(workspace_root, scope_rel=scope_rel)
    score = snap.get("score", "—")
    grade = snap.get("grade", "—")
    ok_txt = "tamamlandı" if success else "kısmi bitti"
    return (
        f"\n\n---\n**Delege görev {ok_txt}** ({turns_used} tur) · "
        f"uyum **{score}/100** ({grade}) · `ajan uyum` ile detay.\n"
        f"({FAZ38_VERSION})"
    )


def run_nested_tool_loop(
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
) -> tuple[str, str, list[dict[str, Any]], list[str], int]:
    """
    Faz 35 tur-içi takibi en fazla max_nested_depth kez tekrarlar.
    Dönüş: (llm_body, round_body, tool_results, extra_profiles, followup_count)
    """
    if not nested_tool_loop_enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz35 import run_mid_turn_followup

            lb, rb, tr, prof, did = run_mid_turn_followup(
                llm_body=llm_body,
                round_body=round_body,
                tool_results=tool_results,
                tool_block=tool_block,
                goal=goal,
                turn=turn,
                agent_system=agent_system,
                round_payload=round_payload,
                model=model,
                active_prior=active_prior,
                message=message,
                turn_plan=turn_plan,
                workspace_root=workspace_root,
                scope_rel=scope_rel,
                stream_fn=stream_fn,
            )
            return lb, rb, tr, prof, 1 if did else 0
        except Exception:
            return llm_body, round_body, tool_results, [], 0

    from ilim_assistant.motorlar.programlama_faz35 import run_mid_turn_followup

    cur_llm = llm_body
    cur_round = round_body
    cur_tools = list(tool_results)
    cur_block = tool_block
    all_profiles: list[str] = []
    followups = 0
    depth_limit = max_nested_depth()

    for depth in range(depth_limit):
        if _has_write(cur_llm, cur_tools):
            break
        cur_llm, cur_round, cur_tools, prof, did = run_mid_turn_followup(
            llm_body=cur_llm,
            round_body=cur_round,
            tool_results=cur_tools,
            tool_block=cur_block,
            goal=goal,
            turn=turn,
            agent_system=agent_system,
            round_payload=round_payload,
            model=model,
            active_prior=active_prior,
            message=message,
            turn_plan=turn_plan,
            workspace_root=workspace_root,
            scope_rel=scope_rel,
            stream_fn=stream_fn,
        )
        if not did:
            break
        followups += 1
        all_profiles.extend(prof or [])
        if _has_write(cur_llm, cur_tools):
            break
        cur_block = _build_tool_block_from_results(cur_tools)
        if not cur_block.strip():
            break
        tag = f"[Faz 38 iç döngü {depth + 2}/{depth_limit}]"
        cur_block = tag + "\n" + cur_block

    return cur_llm, cur_round, cur_tools, all_profiles, followups


def maybe_enrich_yield(
    event: dict[str, Any] | None,
    workspace_root: Any,
    *,
    scope_rel: str = "",
) -> dict[str, Any] | None:
    if event is None:
        return None
    if event.get("type") != "agent_step":
        return event
    return enrich_agent_step_event(event, workspace_root, scope_rel=scope_rel)


def faz38_directive() -> str:
    return (
        "[FAZ 38 — uyum şeridi + iç araç döngüsü]\n"
        "Görev sırasında atölyede canlı uyum skoru (SSE) görünür.\n"
        "Tur içi: read/grep → LLM → araç (en fazla 3 iç döngü).\n"
        "Ana Motor kod isteğini aynı Faz 35–37 zinciriyle işler.\n"
        "Kapat: RUZGAR_FAZ38=0 · derinlik: RUZGAR_FAZ38_MAX_DEPTH=3\n"
    )
