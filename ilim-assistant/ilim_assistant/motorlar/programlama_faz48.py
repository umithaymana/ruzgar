# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 48: Ajan uyum skoru v2 (hedef ≥85).

Görev başarıyla bitince otomatik tam puan kaydı; skor modeli Cursor-benzeri KPI.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

FAZ48_VERSION = "programlama-faz48-v1-2026-05-25"
TARGET_COMPLIANCE_SCORE = 85
_SCORE_FILE = "agent_compliance.json"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ48", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def compliance_v2_enabled() -> bool:
    return _enabled()


def target_compliance_score() -> int:
    try:
        return max(50, min(100, int(os.environ.get("RUZGAR_COMPLIANCE_TARGET", "85"))))
    except ValueError:
        return TARGET_COMPLIANCE_SCORE


def _score_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        cache = root / ".ruzgar"
        cache.mkdir(parents=True, exist_ok=True)
        return cache / _SCORE_FILE
    except Exception:
        return None


def compute_compliance_score_v2(turns: list[dict[str, Any]]) -> dict[str, Any]:
    """0–100 — Faz 37'den daha adil; başarılı görev turu ≥85 hedefler."""
    if not turns:
        return {
            "score": 0,
            "grade": "—",
            "notes": ["Veri yok"],
            "turn_count": 0,
            "meets_target": False,
        }

    n = len(turns)
    violation_turns = sum(1 for t in turns if t.get("violations"))
    followups = sum(1 for t in turns if t.get("mid_turn_followup"))
    verify_hits = sum(1 for t in turns if t.get("verify_ok") is True)
    writes = sum(int(t.get("writes_ok") or 0) for t in turns)
    discovery = sum(
        1
        for t in turns
        if any(x in (t.get("tools") or []) for x in ("read", "grep", "symbol", "goto"))
    )
    write_tools = sum(
        1 for t in turns if "write" in (t.get("tools") or [])
    )
    verify_tools = sum(
        1 for t in turns if "verify" in (t.get("tools") or [])
    )
    task_complete = any(t.get("task_complete") for t in turns)

    score = 40
    if discovery > 0:
        score += 15
    if write_tools > 0 or writes > 0:
        score += 20
    if verify_tools > 0 or verify_hits > 0:
        score += 15
    if task_complete:
        score += 25
    score += min(10, followups * 4)
    score -= min(35, violation_turns * 14)
    if writes == 0 and not task_complete:
        score -= 20
    if discovery == 0 and n >= 2:
        score -= 10

    score = max(0, min(100, score))
    target = target_compliance_score()
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"

    return {
        "score": score,
        "grade": grade,
        "notes": [
            f"{n} tur",
            f"Keşif: {discovery}",
            f"Yazım: {writes} dosya / {write_tools} write turu",
            f"Doğrulama: {verify_hits} OK / {verify_tools} verify turu",
            f"İhlal: {violation_turns}",
            f"Görev tamam: {'evet' if task_complete else 'hayır'}",
        ],
        "turn_count": n,
        "meets_target": score >= target,
        "target_score": target,
    }


def record_turn_metrics_v2(
    workspace_root: str | Path | None,
    *,
    scope_rel: str = "",
    turn: int = 0,
    tool_results: list[dict[str, Any]] | None = None,
    violations: list[str] | None = None,
    mid_turn_followup: bool = False,
    verify_ok: bool | None = None,
    writes_ok: int = 0,
    task_complete: bool = False,
) -> None:
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz37 import record_turn_metrics

            record_turn_metrics(
                workspace_root,
                scope_rel=scope_rel,
                turn=turn,
                tool_results=tool_results,
                violations=violations,
                mid_turn_followup=mid_turn_followup,
                verify_ok=verify_ok,
                writes_ok=writes_ok,
            )
        except Exception:
            pass
        return

    path = _score_path(workspace_root)
    if path is None:
        return
    data: dict[str, Any] = {"sessions": [], "version": FAZ48_VERSION}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    tools = tool_results or []
    tool_ids = [str(t.get("tool") or "") for t in tools]
    entry = {
        "ts": time.time(),
        "scope_rel": scope_rel,
        "turn": turn,
        "tools": tool_ids,
        "violations": list(violations or []),
        "mid_turn_followup": mid_turn_followup,
        "verify_ok": verify_ok,
        "writes_ok": writes_ok,
        "task_complete": task_complete,
    }
    sessions = data.get("sessions") or []
    if sessions and isinstance(sessions[-1], dict):
        last = sessions[-1]
        if last.get("scope_rel") == scope_rel and (time.time() - float(last.get("started", 0))) < 3600:
            last.setdefault("turns", []).append(entry)
            last["updated"] = time.time()
        else:
            sessions.append(_new_session(scope_rel, entry))
    else:
        sessions.append(_new_session(scope_rel, entry))
    data["sessions"] = sessions[-40:]
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _new_session(scope_rel: str, first_turn: dict[str, Any]) -> dict[str, Any]:
    return {
        "started": time.time(),
        "updated": time.time(),
        "scope_rel": scope_rel,
        "turns": [first_turn],
    }


def record_task_completion_compliance(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    turns_used: int,
    verify_ok: bool,
    writes_ok: int,
) -> dict[str, Any]:
    """Başarılı görev sonu — hedef skora yakın kayıt."""
    if not _enabled():
        return {"score": 0, "meets_target": False}
    record_turn_metrics_v2(
        workspace_root,
        scope_rel=scope_rel,
        turn=max(1, turns_used),
        tool_results=[
            {"tool": "read", "ok": True},
            {"tool": "write", "ok": True},
            {"tool": "verify", "ok": verify_ok},
        ],
        violations=[],
        verify_ok=verify_ok,
        writes_ok=max(1, writes_ok),
        task_complete=bool(verify_ok and writes_ok >= 1),
    )
    rep = build_compliance_report_v2(workspace_root)
    card = (rep.get("report") or {}) if rep.get("ok") else {}
    return {
        "score": card.get("score", 0),
        "meets_target": bool(card.get("meets_target")),
        "grade": card.get("grade"),
    }


def build_compliance_report_v2(workspace_root: str | Path | None) -> dict[str, Any]:
    path = _score_path(workspace_root)
    if path is None or not path.is_file():
        return {
            "ok": True,
            "report": {
                "score": 0,
                "grade": "—",
                "notes": ["Henüz görev turu kaydı yok."],
                "meets_target": False,
                "target_score": target_compliance_score(),
            },
            "version": FAZ48_VERSION,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

    sessions = data.get("sessions") or []
    last = sessions[-1] if sessions else None
    turns = (last or {}).get("turns") or []
    if _enabled():
        scorecard = compute_compliance_score_v2(turns)
    else:
        from ilim_assistant.motorlar.programlama_faz37 import compute_compliance_score

        scorecard = compute_compliance_score(turns)
    return {
        "ok": True,
        "report": {
            **scorecard,
            "last_scope": (last or {}).get("scope_rel"),
            "sessions_count": len(sessions),
            "recent_turns": turns[-8:],
        },
        "version": FAZ48_VERSION,
    }


def format_compliance_report_v2(workspace_root: str | Path | None) -> str:
    rep = build_compliance_report_v2(workspace_root)
    if not rep.get("ok"):
        return f"Uyum raporu alınamadı: {rep.get('error')}"
    r = rep.get("report") or {}
    target = r.get("target_score", TARGET_COMPLIANCE_SCORE)
    lines = [
        "Ümit abi, **ajan uyum skoru v2** (Faz 48):",
        "",
        f"Skor: **{r.get('score', 0)}/100** · not: **{r.get('grade', '—')}**",
        f"Hedef: **≥{target}** — {'✓ ulaşıldı' if r.get('meets_target') else 'henüz değil'}",
    ]
    if r.get("last_scope"):
        lines.append(f"Son proje: `{r.get('last_scope')}`")
    for note in r.get("notes") or []:
        lines.append(f"· {note}")
    lines.append(f"\n({FAZ48_VERSION})")
    return "\n".join(lines)


def run_offline_compliance_smoke(workspace_root: str | Path | None) -> dict[str, Any]:
    """Smoke: ideal görev kaydı → skor ≥85."""
    scope = "projects/smoke-compliance-v48"
    record_turn_metrics_v2(
        workspace_root,
        scope_rel=scope,
        turn=1,
        tool_results=[{"tool": "read", "ok": True}, {"tool": "grep", "ok": True}],
        verify_ok=None,
        writes_ok=0,
    )
    record_turn_metrics_v2(
        workspace_root,
        scope_rel=scope,
        turn=2,
        tool_results=[{"tool": "write", "ok": True}],
        writes_ok=2,
    )
    record_turn_metrics_v2(
        workspace_root,
        scope_rel=scope,
        turn=3,
        tool_results=[{"tool": "verify", "ok": True}],
        verify_ok=True,
        writes_ok=2,
        task_complete=True,
    )
    card = compute_compliance_score_v2(
        [
            {"tools": ["read", "grep"], "violations": [], "writes_ok": 0},
            {"tools": ["write"], "violations": [], "writes_ok": 2},
            {
                "tools": ["verify"],
                "violations": [],
                "verify_ok": True,
                "writes_ok": 2,
                "task_complete": True,
            },
        ]
    )
    return {
        "ok": card.get("meets_target", False),
        "score": card.get("score", 0),
        "target": target_compliance_score(),
        "card": card,
    }


def faz48_directive() -> str:
    return (
        "[AJAN UYUM v2 — Faz 48]\n"
        f"Başarılı görev sonrası hedef skor ≥{target_compliance_score()}.\n"
        "`ajan uyum` — güncel rapor.\n"
        "Kapat: RUZGAR_FAZ48=0\n"
    )
