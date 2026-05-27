# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 88: Ajan görev pili (E1 — gerçek döngü ölçümü).

Offline: doğrulama → Faz 87 heal → yeniden doğrulama (LLM yok).
Canlı (--live): hızlı yol kapalı, Faz 14 kod ajanı (Ollama/Groq/Gemini).

Komut: «ajan görev test» · API: GET /api/programlama/agent-task-battery
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from typing import Any

FAZ88_VERSION = "programlama-faz88-v1-2026-05-27"
_BATTERY_RE = re.compile(
    r"(?:ajan\s+gorev\s+test|ajan\s+görev\s+test|agent\s+task\s+battery|"
    r"ajan\s+pili|e1\s+ajan\s+test)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ88", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz88_enabled() -> bool:
    return _enabled()


def wants_agent_task_battery(message: str) -> bool:
    return _enabled() and bool(_BATTERY_RE.search((message or "").strip()))


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def brain_available() -> bool:
    if os.environ.get("GROQ_API_KEY", "").strip():
        return True
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"):
        if os.environ.get(key, "").strip():
            return True
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        return bool(ollama_reachable())
    except Exception:
        return False


def live_llm_requested() -> bool:
    return os.environ.get("RUZGAR_AGENT_BATTERY_LIVE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _setup_broken_health(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> tuple[bool, str]:
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        slug = scope_rel.split("/")[-1]
        service = slug.replace("-", "_")
        sc = run_scaffold("fastapi_api", slug, workspace_root, force=True)
        if not sc.get("ok"):
            return False, str(sc.get("error") or "scaffold")
        broken = f'''"""FastAPI — agent battery."""
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "false", "service": "wrong"}}
'''
        rel = f"{scope_rel}/app/main.py"
        w = ProgramlamaAraclari(workspace_root).write(rel, broken)
        if not w.ok:
            return False, w.detail
        return True, f"broken health ({service})"
    except Exception as exc:
        return False, str(exc)[:120]


def _setup_missing_version(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> tuple[bool, str]:
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        slug = scope_rel.split("/")[-1]
        service = slug.replace("-", "_")
        sc = run_scaffold("fastapi_api", slug, workspace_root, force=True)
        if not sc.get("ok"):
            return False, str(sc.get("error") or "scaffold")
        main = f'''"""FastAPI — version battery."""
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "true", "service": "{service}"}}
'''
        rel = f"{scope_rel}/app/main.py"
        w = ProgramlamaAraclari(workspace_root).write(rel, main)
        if not w.ok:
            return False, w.detail
        return True, "health without version"
    except Exception as exc:
        return False, str(exc)[:120]


def run_verify_heal_cycle(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> dict[str, Any]:
    """Faz 14 tur sonu: verify kırmızı → Faz 87 heal → yeniden verify."""
    t0 = time.perf_counter()
    try:
        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify
        from ilim_assistant.motorlar.programlama_faz87 import try_post_verify_heal
    except Exception as exc:
        return {
            "ok": False,
            "detail": str(exc)[:120],
            "elapsed_sec": time.perf_counter() - t0,
            "source": "verify_heal_cycle",
        }
    v0 = run_project_verify(workspace_root, scope_rel, goal=goal)
    if v0 and v0.ok:
        return {
            "ok": True,
            "detail": "zaten yeşil (verify OK)",
            "elapsed_sec": time.perf_counter() - t0,
            "source": "verify_heal_cycle",
            "verify_ok": True,
            "writes_ok": 0,
        }
    heal = try_post_verify_heal(
        workspace_root,
        scope_rel,
        goal,
        verify_output=(v0.output if v0 else "") or "",
    )
    elapsed = time.perf_counter() - t0
    if not heal:
        return {
            "ok": False,
            "detail": "heal uygulanamadı",
            "elapsed_sec": elapsed,
            "source": "verify_heal_cycle",
            "verify_ok": False,
            "writes_ok": 0,
        }
    ok = bool(heal.get("verify_ok"))
    return {
        "ok": ok,
        "detail": str(heal.get("detail") or ""),
        "elapsed_sec": round(elapsed, 2),
        "source": str(heal.get("source") or "post_verify_heal_faz87"),
        "verify_ok": ok,
        "writes_ok": int(heal.get("writes_ok") or 0),
    }


def run_live_code_agent(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
    *,
    max_turns: int = 3,
) -> dict[str, Any]:
    """Hızlı yol kapalı — gerçek Faz 14 ajan döngüsü."""
    t0 = time.perf_counter()
    slug = scope_rel.split("/")[-1]
    prev_f85 = os.environ.get("RUZGAR_FAZ85")
    prev_turns = os.environ.get("RUZGAR_CODE_AGENT_MAX_TURNS")
    os.environ["RUZGAR_FAZ85"] = "0"
    os.environ["RUZGAR_CODE_AGENT_MAX_TURNS"] = str(max(1, min(6, max_turns)))
    out: dict[str, Any] = {
        "ok": False,
        "detail": "",
        "elapsed_sec": 0.0,
        "source": "code_agent_live",
        "verify_ok": False,
        "writes_ok": 0,
        "turns": 0,
        "skipped": False,
    }
    try:
        from ilim_assistant.motorlar.programlama_faz65 import run_code_agent_on_workspace

        root = str(workspace_root) if workspace_root else ""
        if not root:
            from ilim_assistant.motorlar.programlama_motoru import repo_root

            p = repo_root(None)
            root = str(p) if p else ""
        if not root:
            out["detail"] = "workspace yok"
            return out
        agent = run_code_agent_on_workspace(
            root,
            slug,
            goal,
            scope_rel=scope_rel,
        )
        out["turns"] = int(agent.get("turns") or 0)
        success = bool(agent.get("success"))
        out["ok"] = success
        out["verify_ok"] = success
        tail = str(agent.get("reply_tail") or agent.get("error") or "")[:400]
        out["detail"] = tail or ("OK" if success else "ajan kırmızı")
        if agent.get("error"):
            out["detail"] = f"{agent.get('error')}: {tail}"[:500]
    except Exception as exc:
        out["detail"] = str(exc)[:200]
    finally:
        if prev_f85 is None:
            os.environ.pop("RUZGAR_FAZ85", None)
        else:
            os.environ["RUZGAR_FAZ85"] = prev_f85
        if prev_turns is None:
            os.environ.pop("RUZGAR_CODE_AGENT_MAX_TURNS", None)
        else:
            os.environ["RUZGAR_CODE_AGENT_MAX_TURNS"] = prev_turns
    out["elapsed_sec"] = round(time.perf_counter() - t0, 2)
    return out


def _record_battery_outcome(
    workspace_root: str | Path | None,
    *,
    name: str,
    scope_rel: str,
    goal: str,
    row: dict[str, Any],
) -> None:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import record_task_outcome

        record_task_outcome(
            workspace_root,
            scope_rel=scope_rel,
            goal=goal[:200],
            success=bool(row.get("ok")),
            turns_used=int(row.get("turns") or 0),
            verify_ok=bool(row.get("verify_ok")),
            writes_ok=int(row.get("writes_ok") or 0),
            elapsed_sec=float(row.get("elapsed_sec") or 0),
            source=f"agent_battery_{row.get('source', 'faz88')}",
            detail=f"[{name}] {str(row.get('detail') or '')[:180]}",
        )
    except Exception:
        pass


def _run_scenario(
    workspace_root: str | Path | None,
    *,
    name: str,
    scope_rel: str,
    goal: str,
    mode: str,
    setup: str | None = None,
) -> dict[str, Any]:
    detail_parts: list[str] = []
    if setup == "broken_health":
        ok_setup, msg = _setup_broken_health(workspace_root, scope_rel)
        if not ok_setup:
            return {
                "name": name,
                "mode": mode,
                "ok": False,
                "detail": f"setup: {msg}",
                "elapsed_sec": 0.0,
                "source": "setup",
                "skipped": False,
            }
        detail_parts.append(msg)
    elif setup == "missing_version":
        ok_setup, msg = _setup_missing_version(workspace_root, scope_rel)
        if not ok_setup:
            return {
                "name": name,
                "mode": mode,
                "ok": False,
                "detail": f"setup: {msg}",
                "elapsed_sec": 0.0,
                "source": "setup",
                "skipped": False,
            }
        detail_parts.append(msg)

    if mode == "offline_heal":
        row = run_verify_heal_cycle(workspace_root, scope_rel, goal)
    elif mode == "live_agent":
        if not brain_available():
            return {
                "name": name,
                "mode": mode,
                "ok": False,
                "detail": "canlı ajan atlandı (Ollama/Groq/Gemini yok)",
                "elapsed_sec": 0.0,
                "source": "skipped",
                "skipped": True,
                "verify_ok": False,
                "writes_ok": 0,
            }
        row = run_live_code_agent(workspace_root, scope_rel, goal)
    else:
        return {
            "name": name,
            "mode": mode,
            "ok": False,
            "detail": f"bilinmeyen mod: {mode}",
            "elapsed_sec": 0.0,
            "source": "error",
            "skipped": False,
        }

    detail_parts.append(str(row.get("detail") or ""))
    result = {
        "name": name,
        "mode": mode,
        "ok": bool(row.get("ok")),
        "detail": "\n".join(detail_parts),
        "elapsed_sec": row.get("elapsed_sec", 0.0),
        "source": row.get("source", mode),
        "verify_ok": bool(row.get("verify_ok")),
        "writes_ok": int(row.get("writes_ok") or 0),
        "turns": int(row.get("turns") or 0),
        "skipped": bool(row.get("skipped")),
    }
    if not result["skipped"]:
        _record_battery_outcome(
            workspace_root,
            name=name,
            scope_rel=scope_rel,
            goal=goal,
            row=result,
        )
    return result


def run_agent_task_battery(
    workspace_root: str | Path | None,
    *,
    live_llm: bool | None = None,
) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "faz88 kapalı"}
    if live_llm is None:
        live_llm = live_llm_requested()
    stamp = int(time.time())
    scenarios: list[dict[str, Any]] = [
        {
            "name": "verify-heal-cycle",
            "scope_rel": f"projects/agent-bat-{stamp}-h1",
            "goal": "health duzelt pytest gecir",
            "mode": "offline_heal",
            "setup": "broken_health",
        },
        {
            "name": "missing-version-heal",
            "scope_rel": f"projects/agent-bat-{stamp}-h2",
            "goal": "health endpointine version ekle pytest gecir",
            "mode": "offline_heal",
            "setup": "missing_version",
        },
    ]
    if live_llm:
        scenarios.extend(
            [
                {
                    "name": "live-agent-fix-health",
                    "scope_rel": f"projects/agent-bat-{stamp}-l1",
                    "goal": "health duzelt ok false pytest gecir",
                    "mode": "live_agent",
                    "setup": "broken_health",
                },
                {
                    "name": "live-agent-add-version",
                    "scope_rel": f"projects/agent-bat-{stamp}-l2",
                    "goal": "health endpointine version ekle pytest gecir",
                    "mode": "live_agent",
                    "setup": "missing_version",
                },
            ]
        )
    rows = [
        _run_scenario(
            workspace_root,
            name=s["name"],
            scope_rel=s["scope_rel"],
            goal=s["goal"],
            mode=s["mode"],
            setup=s.get("setup"),
        )
        for s in scenarios
    ]
    scored = [r for r in rows if not r.get("skipped")]
    skipped = [r for r in rows if r.get("skipped")]
    ok_count = sum(1 for r in scored if r.get("ok"))
    total = len(scored)
    rate = ok_count / total if total else 0.0
    offline_rows = [r for r in rows if r.get("mode") == "offline_heal"]
    offline_ok = sum(1 for r in offline_rows if r.get("ok"))
    offline_rate = offline_ok / len(offline_rows) if offline_rows else 0.0

    try:
        from ilim_assistant.motorlar.programlama_faz55 import compute_task_stats

        stats = compute_task_stats(workspace_root, window_days=7)
    except Exception:
        stats = {}
    try:
        from ilim_assistant.motorlar.programlama_faz82 import build_weakness_report

        wr = build_weakness_report(workspace_root)
    except Exception:
        wr = {}

    return {
        "ok": True,
        "version": FAZ88_VERSION,
        "generated_at": time.time(),
        "live_llm": bool(live_llm),
        "brain_available": brain_available(),
        "total": total,
        "success_count": ok_count,
        "success_rate": rate,
        "meets_target_70": rate >= 0.7 if total else False,
        "offline_total": len(offline_rows),
        "offline_success_count": offline_ok,
        "offline_success_rate": offline_rate,
        "offline_meets_target_70": offline_rate >= 0.7 if offline_rows else False,
        "skipped_count": len(skipped),
        "scenarios": rows,
        "task_stats_7d": stats,
        "weakness": wr,
    }


def run_combined_e1_battery(
    workspace_root: str | Path | None,
    *,
    live_llm: bool | None = None,
) -> dict[str, Any]:
    """Faz 86 (hızlı) + Faz 88 (ajan) birleşik E1 raporu."""
    fast: dict[str, Any] = {}
    agent: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz86 import run_live_task_battery

        fast = run_live_task_battery(workspace_root)
    except Exception as exc:
        fast = {"ok": False, "error": str(exc)[:120]}
    try:
        agent = run_agent_task_battery(workspace_root, live_llm=live_llm)
    except Exception as exc:
        agent = {"ok": False, "error": str(exc)[:120]}
    f_rate = float(fast.get("success_rate") or 0) if fast.get("ok") else 0.0
    a_rate = float(agent.get("offline_success_rate") or agent.get("success_rate") or 0)
    if agent.get("ok") and agent.get("live_llm") and agent.get("total"):
        a_rate = float(agent.get("success_rate") or 0)
    combined = (f_rate + a_rate) / 2.0
    return {
        "ok": True,
        "version": FAZ88_VERSION,
        "fast_battery": fast,
        "agent_battery": agent,
        "combined_success_rate": combined,
        "combined_meets_target_70": combined >= 0.7,
    }


def _ascii_report(text: str) -> str:
    return (
        (text or "")
        .replace("\u2192", "->")
        .replace("\u2265", ">=")
    )


def format_agent_battery_report(report: dict[str, Any]) -> str:
    if not report.get("ok"):
        return f"Ajan görev pili çalışmadı: {report.get('error', '?')}"
    lines = [
        "**Ajan görev pili (Faz 88)** — E1 ölçümü",
        "",
    ]
    if report.get("live_llm"):
        lines.append(
            f"Mod: **canlı LLM** · beyin: "
            f"{'var' if report.get('brain_available') else 'yok'}"
        )
    else:
        lines.append("Mod: **offline** (verify->heal->verify, LLM yok)")
    lines.append(
        f"Sonuç: **{report.get('success_count')}/{report.get('total')}** "
        f"(**{int(float(report.get('success_rate', 0)) * 100)}%**)"
    )
    if report.get("offline_total"):
        opct = int(float(report.get("offline_success_rate", 0)) * 100)
        lines.append(
            f"Offline: **{report.get('offline_success_count')}/"
            f"{report.get('offline_total')}** ({opct}%)"
        )
    if report.get("meets_target_70"):
        lines.append("Hedef >=%70: **evet**")
    else:
        lines.append("Hedef >=%70: **hayir**")
    sk = int(report.get("skipped_count") or 0)
    if sk:
        lines.append(f"Atlanan canlı senaryo: {sk} (beyin yok — `RUZGAR_AGENT_BATTERY_LIVE=1`)")
    lines.append("")
    for row in report.get("scenarios") or []:
        if row.get("skipped"):
            mark = "ATLANDI"
        else:
            mark = "OK" if row.get("ok") else "KIRMIZI"
        det = _ascii_report(str(row.get("detail") or "")[:100].replace("\n", " "))
        lines.append(
            f"- **{row.get('name')}** [{mark}] "
            f"({row.get('elapsed_sec')}s · {row.get('mode')}) — {det}"
        )
    ts = report.get("task_stats_7d") or {}
    if ts.get("total", 0) > 0:
        pct = int(float(ts.get("success_rate", 0)) * 100)
        lines.append("")
        lines.append(
            f"Son 7 gün canlı görev KPI: **{pct}%** "
            f"({ts.get('success_count')}/{ts.get('total')})"
        )
    lines.append(f"\n({FAZ88_VERSION})")
    return _ascii_report("\n".join(lines))


def format_combined_e1_report(bundle: dict[str, Any]) -> str:
    if not bundle.get("ok"):
        return "Birleşik E1 pili çalışmadı."
    lines = [
        "**Birleşik E1 pili (Faz 86+88)**",
        "",
        f"Kombine başarı: **{int(float(bundle.get('combined_success_rate', 0)) * 100)}%**",
    ]
    if bundle.get("combined_meets_target_70"):
        lines.append("Hedef >=%70: **evet**")
    else:
        lines.append("Hedef >=%70: **hayir**")
    lines.append("")
    fast = bundle.get("fast_battery") or {}
    if fast.get("ok"):
        lines.append(
            f"- Hızlı yol (86): {fast.get('success_count')}/{fast.get('total')} "
            f"({int(float(fast.get('success_rate', 0)) * 100)}%)"
        )
    agent = bundle.get("agent_battery") or {}
    if agent.get("ok"):
        lines.append(
            f"- Ajan (88): {agent.get('success_count')}/{agent.get('total')} "
            f"({int(float(agent.get('success_rate', 0)) * 100)}%)"
        )
    lines.append(f"\n({FAZ88_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz88(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not wants_agent_task_battery(message):
        return None
    low = _ascii_fold(message)
    combined = "birlesik" in low or "combined" in low or "e1 pil" in low
    if combined:
        bundle = run_combined_e1_battery(workspace_root)
        return format_combined_e1_report(bundle)
    report = run_agent_task_battery(workspace_root)
    return format_agent_battery_report(report)


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz88"] = faz88_enabled()
    return out


def faz88_directive() -> str:
    return (
        "[Faz 88 — ajan görev pili]\n"
        "Komut: `ajan görev test` · birleşik: `e1 pil birleşik`\n"
        "Canlı LLM: RUZGAR_AGENT_BATTERY_LIVE=1\n"
        f"Kapat: RUZGAR_FAZ88=0 · {FAZ88_VERSION}\n"
    )
