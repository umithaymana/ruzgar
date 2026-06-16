# Created by Ümit & Gökçenur
"""
Programlama motoru — Adım 7: kök neden öğrenme.

Başarısız görev → kök neden etiketi → tekrar edince ajan bağlamına kural enjekte.
Kalıcı ipuçları: `.ruzgar/root_cause_rule_hints.jsonl`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

ROOT_CAUSE_LEARN_VERSION = "programlama-root-cause-learn-v1-2026-06-16"
_INJECT_THRESHOLD = 2
_HINTS_FILE = "root_cause_rule_hints.jsonl"


def root_cause_learn_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_ROOT_CAUSE_LEARN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _inject_threshold() -> int:
    try:
        return max(2, int(os.environ.get("RUZGAR_ROOT_CAUSE_INJECT_AT", "2")))
    except ValueError:
        return _INJECT_THRESHOLD


def _hints_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _outcomes_path

        op = _outcomes_path(workspace_root)
        if op is None:
            return None
        return op.parent / _HINTS_FILE
    except Exception:
        return None


def load_persisted_hints(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    limit: int = 6,
) -> list[dict[str, Any]]:
    path = _hints_path(workspace_root)
    if path is None or not path.is_file():
        return []
    scope = (scope_rel or "").replace("\\", "/").strip("/")
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            rs = str(row.get("scope_rel") or "").replace("\\", "/").strip("/")
            if scope and rs and rs != scope:
                continue
            rows.append(row)
    except OSError:
        return []
    rows.sort(key=lambda r: float(r.get("ts") or 0), reverse=True)
    return rows[:limit]


def count_recent_root_cause(
    workspace_root: str | Path | None,
    root_cause: str,
    *,
    scope_rel: str | None = None,
    window_days: int = 7,
) -> int:
    cause = (root_cause or "").strip()
    if not cause or cause == "ok":
        return 0
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _load_store, _outcomes_path

        path = _outcomes_path(workspace_root)
        if path is None or not path.is_file():
            return 0
        store = _load_store(path)
        cutoff = time.time() - window_days * 86400
        scope = (scope_rel or "").replace("\\", "/").strip("/")
        n = 0
        for row in store.get("outcomes") or []:
            if not isinstance(row, dict):
                continue
            if float(row.get("ts") or 0) < cutoff:
                continue
            if str(row.get("root_cause") or "") != cause:
                continue
            rs = str(row.get("scope_rel") or "").replace("\\", "/").strip("/")
            if scope and rs and rs != scope:
                continue
            if not row.get("success"):
                n += 1
        return n
    except Exception:
        return 0


def infer_root_cause_from_snippet(
    failure_snippet: str = "",
    *,
    verify_ok: bool = False,
) -> str:
    try:
        from ilim_assistant.motorlar.programlama_faz102_e1_live import classify_root_cause

        return classify_root_cause(
            success=False,
            verify_ok=verify_ok,
            writes_ok=1,
            detail=failure_snippet or "",
            bonus_retry=True,
        )
    except Exception:
        low = (failure_snippet or "").lower()
        if "pytest" in low or "assert" in low:
            return "pytest_failed"
        return "verify_failed"


def resolve_rule_text(root_cause: str) -> str:
    try:
        from ilim_assistant.motorlar.programlama_faz102_e1_live import _rule_suggestion_for

        return _rule_suggestion_for(root_cause)
    except Exception:
        return "Önceki hatayı tekrarlama; verify çıktısını oku ve düzelt."


def active_root_cause_rules(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    current_cause: str | None = None,
) -> list[dict[str, str]]:
    """Tekrar eşiğine ulaşan kök nedenler + kalıcı jsonl kuralları."""
    if not root_cause_learn_enabled():
        return []
    scope = (scope_rel or "").replace("\\", "/").strip("/")
    threshold = _inject_threshold()
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    for hint in load_persisted_hints(workspace_root, scope_rel=scope):
        cause = str(hint.get("root_cause") or "")
        if not cause or cause in seen:
            continue
        seen.add(cause)
        out.append(
            {
                "cause": cause,
                "rule": str(hint.get("suggestion") or resolve_rule_text(cause)),
                "source": "persisted",
            }
        )

    candidates: list[str] = []
    if current_cause and current_cause not in ("ok", ""):
        candidates.append(current_cause)
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _load_store, _outcomes_path

        path = _outcomes_path(workspace_root)
        if path and path.is_file():
            store = _load_store(path)
            cutoff = time.time() - 7 * 86400
            freq: dict[str, int] = {}
            for row in store.get("outcomes") or []:
                if not isinstance(row, dict) or row.get("success"):
                    continue
                if float(row.get("ts") or 0) < cutoff:
                    continue
                rs = str(row.get("scope_rel") or "").replace("\\", "/").strip("/")
                if scope and rs and rs != scope:
                    continue
                c = str(row.get("root_cause") or "")
                if c and c != "ok":
                    freq[c] = freq.get(c, 0) + 1
            for c, n in sorted(freq.items(), key=lambda x: -x[1]):
                if n >= threshold and c not in candidates:
                    candidates.append(c)
    except Exception:
        pass

    for cause in candidates:
        if cause in seen:
            continue
        if count_recent_root_cause(workspace_root, cause, scope_rel=scope) >= threshold:
            seen.add(cause)
            out.append(
                {
                    "cause": cause,
                    "rule": resolve_rule_text(cause),
                    "source": "repeat_detect",
                }
            )
    return out[:5]


def build_root_cause_learn_block(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    current_cause: str | None = None,
) -> str:
    rules = active_root_cause_rules(
        workspace_root,
        scope_rel=scope_rel,
        current_cause=current_cause,
    )
    if not rules:
        return ""
    lines = [f"[KÖK NEDEN ÖĞRENME — {ROOT_CAUSE_LEARN_VERSION}]"]
    lines.append(
        "Bu proje veya son görevlerde tekrar eden hatalar için bağlayıcı kurallar:"
    )
    for r in rules:
        lines.append(f"- `{r.get('cause')}` -> {r.get('rule')}")
    return "\n".join(lines)[:3500]


def augment_turn_with_root_cause_learn(
    turn_user: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    failure_snippet: str = "",
    current_cause: str | None = None,
) -> str:
    if not root_cause_learn_enabled():
        return turn_user
    cause = current_cause or infer_root_cause_from_snippet(failure_snippet)
    block = build_root_cause_learn_block(
        workspace_root,
        scope_rel=scope_rel,
        current_cause=cause,
    )
    if not block:
        return turn_user
    return block.rstrip() + "\n\n" + (turn_user or "").lstrip()


def root_cause_learn_directive() -> str:
    return (
        "[KÖK NEDEN ÖĞRENME — Adım 7]\n"
        "Tekrarlayan görev hataları bağlama kural olarak enjekte edilir.\n"
        "Kapat: RUZGAR_PROG_ROOT_CAUSE_LEARN=0\n"
    )


def run_root_cause_learn_smoke(
    workspace_root: str | Path | None,
    *,
    scope_rel: str = "projects/smoke-live-test",
) -> dict[str, Any]:
    """Bench: 2 aynı kök neden → kural bloğu görünür."""
    if not root_cause_learn_enabled():
        return {"ok": False, "error": "RUZGAR_PROG_ROOT_CAUSE_LEARN=0"}
    cause = "pytest_failed"
    try:
        from ilim_assistant.motorlar.programlama_faz55 import record_task_outcome

        for _ in range(2):
            record_task_outcome(
                workspace_root,
                scope_rel=scope_rel,
                goal="smoke root cause learn",
                success=False,
                verify_ok=False,
                writes_ok=1,
                detail="pytest assert failed in test_health",
            )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}

    block = build_root_cause_learn_block(
        workspace_root,
        scope_rel=scope_rel,
        current_cause=cause,
    )
    count = count_recent_root_cause(workspace_root, cause, scope_rel=scope_rel)
    has_rule = "pytest" in block.lower() or "verify" in block.lower()
    ok = bool(block.strip()) and count >= 2 and has_rule

    try:
        from ilim_assistant.motorlar.programlama_faz102_e1_live import record_root_cause_hint

        hint_rep = record_root_cause_hint(
            workspace_root, scope_rel=scope_rel, root_cause=cause
        )
    except Exception as exc:
        hint_rep = {"ok": False, "error": str(exc)[:80]}

    return {
        "ok": ok,
        "repeat_count": count,
        "block_preview": block[:500],
        "hint": hint_rep,
        "version": ROOT_CAUSE_LEARN_VERSION,
    }
