# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 56: Uzun görev v2 + çok dosya patch planı.

- 20 tur / 20 dk (env ile)
- Tur başına max 8 dosya yazımı
- Birleşik verify: pytest + bekleyen patch dosya sayısı
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ56_VERSION = "programlama-faz56-v1-2026-05-26"
_V2_MAX_TURNS_DEFAULT = 20
_V2_BUDGET_SEC_DEFAULT = 1200.0
_MAX_FILES_PER_TURN_DEFAULT = 8

_MULTI_FILE_CUES = (
    r"\b(refactor|refaktör|çok dosya|cok dosya|multi\s*file|tüm dosya|tum dosya)\b",
    r"\b(util|service|main\.py|üç dosya|uc dosya|3 dosya)\b",
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ56", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz56_enabled() -> bool:
    return _enabled()


def long_task_v2_enabled() -> bool:
    return _enabled()


def agent_max_turns_v2() -> int:
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz41 import long_task_max_turns

            return long_task_max_turns()
        except Exception:
            return 15
    try:
        v = int(os.environ.get("RUZGAR_FAZ56_MAX_TURNS", str(_V2_MAX_TURNS_DEFAULT)))
        return max(5, min(v, 30))
    except ValueError:
        return _V2_MAX_TURNS_DEFAULT


def agent_budget_sec_v2() -> float:
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz41 import long_task_budget_sec

            return long_task_budget_sec()
        except Exception:
            return 900.0
    raw = os.environ.get("RUZGAR_FAZ56_BUDGET_SEC", "").strip()
    if not raw:
        raw = os.environ.get("RUZGAR_CODE_AGENT_BUDGET_SEC", "").strip()
    if raw:
        try:
            return max(120.0, float(raw))
        except ValueError:
            pass
    return _V2_BUDGET_SEC_DEFAULT


def max_files_per_turn() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_FAZ56_MAX_FILES_PER_TURN", "8")), 16))
    except ValueError:
        return _MAX_FILES_PER_TURN_DEFAULT


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def looks_like_multi_file_task(message: str, goal: str = "") -> bool:
    raw = _ascii_fold(f"{message} {goal}")
    return any(re.search(p, raw, re.I) for p in _MULTI_FILE_CUES)


def infer_target_files(
    workspace_root: str | Path | None,
    scope_rel: str,
    message: str,
    *,
    limit: int = 12,
) -> list[str]:
    """Hedef dosya listesi — ilgili dosyalar + anahtar kelime."""
    targets: list[str] = []
    try:
        from ilim_assistant.motorlar.programlama_faz44 import select_relevant_files

        targets.extend(
            select_relevant_files(workspace_root, scope_rel, message, limit=limit)
        )
    except Exception:
        pass
    low = _ascii_fold(message)
    for hint in (
        "app/main.py",
        "app/service.py",
        "app/util.py",
        "tests/test_health.py",
        "tests/test_refactor.py",
    ):
        if any(k in low for k in hint.replace("/", " ").split()):
            rel = f"{scope_rel}/{hint}".replace("//", "/")
            if rel not in targets:
                targets.append(rel)
    out: list[str] = []
    for t in targets:
        n = t.replace("\\", "/").lstrip("/")
        if n and n not in out:
            out.append(n)
        if len(out) >= limit:
            break
    return out


def build_multi_file_plan_block(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    message: str,
    goal: str,
    turn: int,
    touched_files: list[str] | None = None,
) -> str:
    if not _enabled():
        return ""
    if not looks_like_multi_file_task(message, goal) and turn > 1:
        return ""
    targets = infer_target_files(workspace_root, scope_rel, f"{message} {goal}")
    touched = set(touched_files or [])
    remaining = [t for t in targets if t not in touched]
    cap = max_files_per_turn()
    lines = [
        f"[ÇOK DOSYA PLANI — Faz 56 — tur {turn}]",
        f"Bu turda en fazla **{cap}** dosya yaz.",
        f"Kapsam: `{scope_rel}`",
    ]
    if remaining:
        lines.append("Öncelikli dosyalar:")
        for rel in remaining[:cap]:
            lines.append(f"  · `{rel}`")
    elif targets:
        lines.append("Hedef dosyaların çoğu işlendi — verify çalıştır.")
    else:
        lines.append("Önce `read`/`grep` ile dosyaları keşfet.")
    lines.append(f"({FAZ56_VERSION})")
    return "\n".join(lines)


def count_turn_writes(
    round_body: str,
    tool_results: list[dict[str, Any]] | None = None,
) -> int:
    paths: set[str] = set()
    for m in re.finditer(
        r"@@write\s+([^\s`]+)",
        round_body or "",
        re.I,
    ):
        paths.add(m.group(1).strip().replace("\\", "/"))
    for r in tool_results or []:
        if str(r.get("tool") or "").lower() == "write" and r.get("ok"):
            p = str(r.get("path") or r.get("detail") or "").strip()
            if p:
                paths.add(p.replace("\\", "/"))
    return len(paths)


def multi_file_cap_nudge(write_count: int) -> str | None:
    cap = max_files_per_turn()
    if write_count <= cap:
        return None
    return (
        f"[FAZ 56] Bu turda {write_count} dosya yazıldı (limit {cap}). "
        "Sonraki turda verify çalıştır; gereksiz dosyayı geri al."
    )


def merge_touched_files(
    existing: list[str] | None,
    round_body: str,
    tool_results: list[dict[str, Any]] | None = None,
) -> list[str]:
    seen = set((existing or []))
    for m in re.finditer(r"@@write\s+([^\s`]+)", round_body or "", re.I):
        seen.add(m.group(1).strip().replace("\\", "/"))
    for r in tool_results or []:
        if str(r.get("tool") or "").lower() == "write" and r.get("ok"):
            p = str(r.get("path") or "").strip()
            if p:
                seen.add(p.replace("\\", "/"))
    return sorted(seen)


def run_combined_verify(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    goal: str = "",
) -> dict[str, Any]:
    """pytest + bekleyen patch özeti."""
    pytest_ok = False
    pytest_detail = ""
    try:
        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

        rep = run_project_verify(workspace_root, scope_rel, goal=goal or "pytest")
        pytest_ok = bool(rep and rep.ok)
        pytest_detail = (rep.output if rep else "")[:500]
    except Exception as exc:
        pytest_detail = str(exc)[:120]

    pending_n = 0
    pending_paths: list[str] = []
    try:
        from ilim_assistant.motorlar.programlama_faz16 import build_pending_bundle

        bundle = build_pending_bundle(workspace_root)
        items = list(bundle.get("items") or [])
        scope_prefix = scope_rel.replace("\\", "/").rstrip("/") + "/"
        for it in items:
            rel = str(it.get("path") or "").replace("\\", "/")
            if rel.startswith(scope_prefix) or scope_rel in rel:
                pending_paths.append(rel)
        pending_n = len(pending_paths)
    except Exception:
        pass

    ok = pytest_ok
    return {
        "ok": ok,
        "pytest_ok": pytest_ok,
        "pending_count": pending_n,
        "pending_paths": pending_paths[:12],
        "detail": pytest_detail,
        "version": FAZ56_VERSION,
    }


def augment_turn_user_message(
    base_message: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    message: str,
    goal: str,
    turn: int,
    touched_files: list[str] | None = None,
) -> str:
    block = build_multi_file_plan_block(
        workspace_root,
        scope_rel=scope_rel,
        message=message,
        goal=goal,
        turn=turn,
        touched_files=touched_files,
    )
    if not block:
        return base_message
    return base_message.rstrip() + "\n\n" + block


def format_long_task_v2_status(scope_rel: str) -> str:
    return (
        f"Uzun görev v2 (Faz 56) — `{scope_rel}` · "
        f"max {agent_max_turns_v2()} tur · "
        f"{int(agent_budget_sec_v2())} sn · "
        f"max {max_files_per_turn()} dosya/tur"
    )


def faz56_directive() -> str:
    return (
        "[UZUN GÖREV v2 — Faz 56]\n"
        f"{agent_max_turns_v2()} tur · {int(agent_budget_sec_v2())} sn · "
        f"çok dosya max {max_files_per_turn()}/tur · birleşik verify.\n"
        "Kapat: RUZGAR_FAZ56=0\n"
    )
