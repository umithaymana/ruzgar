# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 24: plan SSE + canlı adım şeridi.

Otonom görev turunda `agent_step` olayları UI'da anlık güncellenir.
"""

from __future__ import annotations

import os
import re
from typing import Any

FAZ24_VERSION = "programlama-faz24-v1-2026-05-25"

_PLAN_LINE_RE = re.compile(
    r"^\s*(?:\d+[\).\]]\s*|[-*•]\s*)?(.{4,120})$",
    re.M,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ24", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def sse_steps_enabled() -> bool:
    return _enabled()


def _step(sid: str, label: str, status: str, detail: str = "") -> dict[str, str]:
    return {"id": sid, "label": label, "status": status, "detail": detail}


def extract_plan_lines(reply: str, *, max_lines: int = 3) -> str:
    """LLM yanıtından kısa plan özeti (ilk madde satırları)."""
    lines: list[str] = []
    for raw in (reply or "").splitlines():
        t = raw.strip()
        if not t or t.startswith("```"):
            continue
        if t.lower().startswith(("plan", "adım", "adim", "tur ", "@@write", "[araç")):
            m = _PLAN_LINE_RE.match(t)
            if m:
                lines.append(m.group(1).strip()[:100])
        elif len(lines) < max_lines and len(t) < 100 and not t.startswith("{"):
            if any(k in t.lower() for k in ("ekle", "düzelt", "duzelt", "test", "yaz", "okuy")):
                lines.append(t[:100])
        if len(lines) >= max_lines:
            break
    return " · ".join(lines)[:220]


class CodeAgentStepTracker:
    """Canlı ajan adım şeridi — Faz 24."""

    def __init__(
        self,
        *,
        scope_rel: str,
        goal: str,
        max_turns: int,
        budget_sec: float,
    ) -> None:
        self.scope_rel = scope_rel
        self.goal = (goal or "").strip()
        self.max_turns = max(1, int(max_turns))
        self.budget_sec = float(budget_sec)
        self.current_turn = 0
        self._steps: list[dict[str, str]] = [
            _step("task", "Görev", "active", scope_rel[:80]),
            _step("plan", "Plan", "skip", ""),
            _step("brain", "Model", "skip", ""),
            _step("turn", "Aktif tur", "skip", ""),
            _step("write", "Dosya yazımı", "skip", ""),
            _step("tools", "Araçlar", "skip", ""),
            _step("verify", "Doğrulama", "skip", ""),
            _step("done", "Sonuç", "skip", ""),
        ]

    def _get(self, sid: str) -> dict[str, str] | None:
        for s in self._steps:
            if s["id"] == sid:
                return s
        return None

    def snapshot(self) -> list[dict[str, str]]:
        return [dict(s) for s in self._steps]

    def sse_event(self, *, phase: str = "", **extra: Any) -> dict[str, Any]:
        ca: dict[str, Any] = {
            "phase": phase,
            "scope_rel": self.scope_rel,
            "turn": self.current_turn,
            "max_turns": self.max_turns,
            "budget_sec": self.budget_sec,
            "version": FAZ24_VERSION,
        }
        ca.update(extra)
        return {
            "type": "agent_step",
            "steps": self.snapshot(),
            "code_agent": ca,
        }

    def on_started(self, *, brain_chain: list[str] | None = None) -> dict[str, Any]:
        t = self._get("task")
        if t:
            t["status"] = "done"
        p = self._get("plan")
        if p:
            p["status"] = "active"
            p["detail"] = (self.goal or "")[:120]
        b = self._get("brain")
        if b and brain_chain:
            b["status"] = "done"
            b["detail"] = ", ".join(str(x) for x in brain_chain[:4])
        return self.sse_event(phase="started")

    def on_turn_start(self, turn: int) -> dict[str, Any]:
        self.current_turn = turn
        tr = self._get("turn")
        if tr:
            tr["status"] = "active"
            tr["detail"] = f"Tur {turn}/{self.max_turns}"
        w = self._get("write")
        if w:
            w["status"] = "skip"
            w["detail"] = ""
        v = self._get("verify")
        if v:
            v["status"] = "skip"
        tl = self._get("tools")
        if tl:
            tl["status"] = "skip"
        return self.sse_event(phase="turn_start", turn=turn)

    def on_llm_start(self, turn: int) -> dict[str, Any]:
        self.current_turn = turn
        tr = self._get("turn")
        if tr:
            tr["status"] = "active"
            tr["detail"] = f"Tur {turn}/{self.max_turns} — LLM"
        return self.sse_event(phase="llm_start", turn=turn)

    def on_llm_done(self, turn: int, reply: str = "") -> dict[str, Any]:
        plan_txt = extract_plan_lines(reply)
        p = self._get("plan")
        if p and plan_txt:
            p["status"] = "done"
            p["detail"] = plan_txt
        return self.sse_event(phase="llm_done", turn=turn)

    def on_tools(self, turn: int, count: int) -> dict[str, Any]:
        tl = self._get("tools")
        if tl:
            if count > 0:
                tl["status"] = "done"
                tl["detail"] = f"{count} araç"
            else:
                tl["status"] = "skip"
        return self.sse_event(phase="tools", turn=turn, tool_count=count)

    def on_writes(self, turn: int, writes_ok: int, paths: list[str] | None = None) -> dict[str, Any]:
        w = self._get("write")
        if w:
            if writes_ok > 0:
                w["status"] = "done"
                sample = (paths or [""])[0]
                w["detail"] = f"{writes_ok} dosya" + (f" · `{sample}`" if sample else "")
            else:
                w["status"] = "active"
                w["detail"] = "bekleniyor"
        return self.sse_event(phase="write", turn=turn, writes=writes_ok)

    def on_verify(self, turn: int, ok: bool, snippet: str = "") -> dict[str, Any]:
        v = self._get("verify")
        if v:
            v["status"] = "done" if ok else "active"
            v["detail"] = "geçti" if ok else (snippet[:80] or "kırmızı")
        return self.sse_event(phase="verify", turn=turn, verify_ok=ok)

    def on_finish(self, *, success: bool, elapsed_sec: float, turns_used: int) -> dict[str, Any]:
        for sid in ("turn", "write", "tools"):
            s = self._get(sid)
            if s and s["status"] == "active":
                s["status"] = "done"
        v = self._get("verify")
        if v:
            v["status"] = "done" if success else "active"
        d = self._get("done")
        if d:
            d["status"] = "done" if success else "active"
            d["detail"] = (
                f"{'Tamamlandı' if success else 'Bitti (kısmi)'} · "
                f"{turns_used} tur · {int(elapsed_sec)} sn"
            )
        return self.sse_event(
            phase="finish",
            success=success,
            elapsed_sec=elapsed_sec,
            turns_used=turns_used,
        )


def create_tracker(
    *,
    scope_rel: str,
    goal: str,
    max_turns: int,
    budget_sec: float | None = None,
) -> CodeAgentStepTracker | None:
    if not sse_steps_enabled():
        return None
    if budget_sec is None:
        try:
            from ilim_assistant.motorlar.programlama_faz23 import code_agent_budget_sec

            budget_sec = code_agent_budget_sec()
        except Exception:
            budget_sec = 300.0
    return CodeAgentStepTracker(
        scope_rel=scope_rel,
        goal=goal,
        max_turns=max_turns,
        budget_sec=float(budget_sec),
    )


def maybe_yield_step(tracker: CodeAgentStepTracker | None, event: dict[str, Any]) -> dict[str, Any] | None:
    if tracker is None:
        return None
    return event


def faz24_directive() -> str:
    return (
        "[ADIM ŞERİDİ — Faz 24]\n"
        "Görev sırasında atölyede tur/tur ilerleme görünür (SSE agent_step).\n"
        "Kapat: RUZGAR_FAZ24=0\n"
    )
