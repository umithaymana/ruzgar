# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 37: Ajan uyum skoru + rapor.

Araç sırası (Faz 34) ve tur-içi takip (Faz 35) metrikleri; API raporu.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

FAZ37_VERSION = "programlama-faz37-v1-2026-05-25"
_SCORE_FILE = "agent_compliance.json"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ37", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def compliance_tracking_enabled() -> bool:
    return _enabled()


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


def record_turn_metrics(
    workspace_root: str | Path | None,
    *,
    scope_rel: str = "",
    turn: int = 0,
    tool_results: list[dict[str, Any]] | None = None,
    violations: list[str] | None = None,
    mid_turn_followup: bool = False,
    verify_ok: bool | None = None,
    writes_ok: int = 0,
) -> None:
    if not compliance_tracking_enabled():
        return
    path = _score_path(workspace_root)
    if path is None:
        return
    data: dict[str, Any] = {"sessions": [], "version": FAZ37_VERSION}
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
    }
    sessions = data.get("sessions") or []
    if sessions and isinstance(sessions[-1], dict):
        last = sessions[-1]
        if last.get("scope_rel") == scope_rel and (time.time() - float(last.get("started", 0))) < 3600:
            turns = last.setdefault("turns", [])
            turns.append(entry)
            last["updated"] = time.time()
        else:
            sessions.append(_new_session(scope_rel, entry))
    else:
        sessions.append(_new_session(scope_rel, entry))
    data["sessions"] = sessions[-40:]
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _new_session(scope_rel: str, first_turn: dict[str, Any]) -> dict[str, Any]:
    return {
        "started": time.time(),
        "updated": time.time(),
        "scope_rel": scope_rel,
        "turns": [first_turn],
    }


def compute_compliance_score(turns: list[dict[str, Any]]) -> dict[str, Any]:
    """0–100 skor ve özet."""
    if not turns:
        return {"score": 0, "grade": "—", "notes": ["Veri yok"]}
    n = len(turns)
    violation_turns = sum(1 for t in turns if t.get("violations"))
    followups = sum(1 for t in turns if t.get("mid_turn_followup"))
    verify_ok = sum(1 for t in turns if t.get("verify_ok") is True)
    writes = sum(int(t.get("writes_ok") or 0) for t in turns)
    discovery_turns = sum(
        1
        for t in turns
        if any(x in (t.get("tools") or []) for x in ("read", "grep", "symbol", "goto"))
    )

    score = 100
    score -= min(40, violation_turns * 12)
    if writes == 0:
        score -= 25
    if discovery_turns == 0 and n > 0:
        score -= 15
    score += min(15, verify_ok * 5)
    score += min(10, followups * 3)
    score = max(0, min(100, score))

    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 55:
        grade = "C"
    else:
        grade = "D"

    notes = [
        f"{n} tur kayıtlı",
        f"İhlal turu: {violation_turns}",
        f"Tur-içi takip: {followups}",
        f"Doğrulama OK: {verify_ok}",
        f"Yazım: {writes} dosya",
    ]
    return {
        "score": score,
        "grade": grade,
        "notes": notes,
        "turn_count": n,
    }


def build_compliance_report(workspace_root: str | Path | None) -> dict[str, Any]:
    path = _score_path(workspace_root)
    if path is None or not path.is_file():
        return {
            "ok": True,
            "report": {
                "score": 0,
                "grade": "—",
                "notes": ["Henüz görev turu kaydı yok."],
                "sessions": [],
            },
            "version": FAZ37_VERSION,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

    sessions = data.get("sessions") or []
    last = sessions[-1] if sessions else None
    turns = (last or {}).get("turns") or []
    scorecard = compute_compliance_score(turns)
    return {
        "ok": True,
        "report": {
            **scorecard,
            "last_scope": (last or {}).get("scope_rel"),
            "sessions_count": len(sessions),
            "recent_turns": turns[-8:],
        },
        "version": FAZ37_VERSION,
    }


def format_compliance_report(workspace_root: str | Path | None) -> str:
    rep = build_compliance_report(workspace_root)
    if not rep.get("ok"):
        return f"Uyum raporu alınamadı: {rep.get('error')}"
    r = rep.get("report") or {}
    lines = [
        "Ümit abi, **ajan uyum skoru** (Faz 37):",
        "",
        f"Skor: **{r.get('score', 0)}/100** · not: **{r.get('grade', '—')}**",
    ]
    if r.get("last_scope"):
        lines.append(f"Son proje: `{r.get('last_scope')}`")
    for note in r.get("notes") or []:
        lines.append(f"· {note}")
    lines.append(f"\n({FAZ37_VERSION})")
    return "\n".join(lines)


def wants_compliance_report(message: str) -> bool:
    low = (message or "").lower().replace("ı", "i").replace("ş", "s")
    return bool(
        re.search(
            r"(?:ajan|agent)\s+(?:uyum|skor|score|rapor)|uyum\s+skor|compliance\s+report",
            low,
        )
    )


def maybe_instant_faz37(message: str, workspace_root: str | Path | None) -> str | None:
    if not _enabled() or not wants_compliance_report(message):
        return None
    return format_compliance_report(workspace_root)


def faz37_directive() -> str:
    return (
        "[AJAN UYUM — Faz 37]\n"
        "Görev turları `.ruzgar/agent_compliance.json` dosyasına kaydedilir.\n"
        "`ajan uyum` — son oturum skoru (0–100).\n"
    )
