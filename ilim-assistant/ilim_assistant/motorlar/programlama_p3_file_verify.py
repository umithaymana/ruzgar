"""
P3 — Dosya-dosya verify kapısı + heal→kök→pattern (2026-10-23).

- Çok dosyada: 1 dosya yaz → verify → sonraki (nudge + plan metni)
- Verify kırmızı: bilinen kök → P1 pattern yaması (LLM yok)
- Heal dersi: kök neden sonraki tur nudge'a yazılır
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

P3_VERSION = "programlama-p3-file-verify-v1-2026-10-23"

# Kök → pattern_id (supervised_patterns)
_ROOT_TO_PATTERN: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ImportError|NameError|greet.*not defined|cannot import", re.I), "import_fix"),
    (re.compile(r"uptime|KeyError.*uptime|assert.*uptime", re.I), "dict_field"),
    (re.compile(r"/ping|404.*ping|ping.*assert", re.I), "ping_route"),
    (re.compile(r"VERSION|1\.0\.0-broken|test_version|assert VERSION", re.I), "e2_version"),
    (re.compile(r"status|test_health|health.*assert", re.I), "health_fields"),
]

_LESSONS: list[dict[str, Any]] = []
_LESSONS_MAX = 24


@dataclass
class FileVerifyPolicy:
    prefer_one_file: bool
    verify_after_write: bool
    nudge: str = ""
    version: str = P3_VERSION


def p3_enabled() -> bool:
    return os.environ.get("RUZGAR_P3_FILE_VERIFY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def is_multi_goal(goal: str, message: str = "") -> bool:
    raw = f"{message or ''} {goal or ''}"
    try:
        from ilim_assistant.motorlar.programlama_faz56 import looks_like_multi_file_task

        if looks_like_multi_file_task(raw):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_ray_siniflandirici import (
            classify_programlama_ray,
        )

        ray = classify_programlama_ray(goal, message=message).ray
        return ray in ("agent_multi", "agent_mega")
    except Exception:
        return False


def file_verify_policy(
    goal: str,
    *,
    message: str = "",
    writes_this_turn: int = 0,
) -> FileVerifyPolicy:
    if not p3_enabled():
        return FileVerifyPolicy(False, False, "")
    multi = is_multi_goal(goal, message)
    if not multi:
        return FileVerifyPolicy(False, True, "")
    nudge = (
        "[P3 dosya-dosya] Bu turda **1 dosya** yaz → pytest verify → sonraki dosya. "
        "Hepsini bir turda yazma."
    )
    if writes_this_turn >= 2:
        nudge = (
            f"[P3] Bu turda {writes_this_turn} dosya yazıldı — limit aşıldı. "
            "Şimdi verify; sonraki turda yalnız kalan 1 dosya."
        )
    return FileVerifyPolicy(
        prefer_one_file=True,
        verify_after_write=True,
        nudge=nudge,
    )


def classify_heal_root(verify_output: str) -> str | None:
    text = verify_output or ""
    for rx, pid in _ROOT_TO_PATTERN:
        if rx.search(text):
            return pid
    return None


def record_heal_lesson(
    *,
    root_cause: str,
    pattern_id: str,
    detail: str = "",
) -> None:
    _LESSONS.append(
        {
            "ts": time.time(),
            "root_cause": root_cause,
            "pattern_id": pattern_id,
            "detail": (detail or "")[:200],
        }
    )
    if len(_LESSONS) > _LESSONS_MAX:
        del _LESSONS[: len(_LESSONS) - _LESSONS_MAX]


def recent_heal_lessons(limit: int = 5) -> list[dict[str, Any]]:
    return list(_LESSONS[-limit:])


def lessons_nudge_block(scope_rel: str = "") -> str:
    if not _LESSONS:
        return ""
    last = _LESSONS[-3:]
    lines = ["\n[P3 heal dersi — tekrarlama]\n"]
    for L in last:
        lines.append(
            f"· kök `{L.get('root_cause')}` → pattern `{L.get('pattern_id')}` "
            f"({L.get('detail') or 'uygula'})\n"
        )
    if scope_rel:
        lines.append(f"Kapsam: `{scope_rel}`\n")
    return "".join(lines)


def try_pattern_heal_from_verify(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
    *,
    verify_output: str,
) -> dict[str, Any]:
    """
    Verify kırmızı → kök sınıfla → P1 pattern uygula.
    Dönüş: supervised boot ile uyumlu dict (+ healed, pattern_id).
    """
    empty: dict[str, Any] = {
        "ok": False,
        "writes_ok": 0,
        "paths": [],
        "detail": "",
        "source": "p3_pattern_heal",
        "healed": False,
        "pattern_id": "",
        "root_cause": "",
        "version": P3_VERSION,
    }
    if not p3_enabled():
        empty["detail"] = "p3 kapalı"
        return empty
    pid = classify_heal_root(verify_output)
    if not pid:
        empty["detail"] = "bilinen kök yok"
        return empty
    empty["root_cause"] = pid
    empty["pattern_id"] = pid
    try:
        from ilim_assistant.motorlar.programlama_supervised_patterns import (
            try_supervised_pattern_library,
        )

        # Goal'ü pattern match için zenginleştir
        synth_goal = goal or ""
        if pid == "import_fix" and "import" not in synth_goal.lower():
            synth_goal = f"{synth_goal} eksik import düzelt".strip()
        if pid == "dict_field" and "uptime" in (verify_output or "").lower():
            synth_goal = f"{synth_goal} uptime alanı ekle".strip()
        if pid == "ping_route" and "ping" not in synth_goal.lower():
            synth_goal = f"{synth_goal} ping endpoint ekle".strip()
        if pid == "e2_version" and "version" not in synth_goal.lower():
            synth_goal = (
                f"{synth_goal} app/util.py ve app/service.py VERSION 2.0.0".strip()
            )
        if pid == "health_fields" and "status" not in synth_goal.lower():
            synth_goal = f"{synth_goal} health endpointine status alanı ekle".strip()

        hit = try_supervised_pattern_library(
            workspace_root,
            scope_rel,
            synth_goal,
            pattern_ids=[pid],
        )
        if hit.get("writes_ok"):
            record_heal_lesson(
                root_cause=pid,
                pattern_id=pid,
                detail=str(hit.get("detail") or ""),
            )
            return {
                **hit,
                "ok": True,
                "healed": True,
                "source": "p3_pattern_heal",
                "root_cause": pid,
                "pattern_id": pid,
                "version": P3_VERSION,
            }
        empty["detail"] = str(hit.get("detail") or "pattern yazamadı")
        return empty
    except Exception as exc:
        empty["detail"] = str(exc)[:200]
        return empty


def p3_plan_suffix() -> str:
    """Faz56 plan bloğuna ek satır."""
    if not p3_enabled():
        return ""
    return (
        "P3 kuralı: **1 dosya yaz → verify → sonraki dosya**. "
        "Toplu yazım yasak sayılır."
    )
