# Created by Ümit & Gökçenur
"""Ana Motor Faz K1 — otomatik/manuel paket sihirbazı özet kartı."""

from __future__ import annotations

import os
from typing import Any


_STEP_LABELS = {
    "archive": "Arşiv",
    "ttl_extend": "TTL",
    "remember": "Hafıza",
    "nebula": "Nebula",
}


def paket_ozet_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_OZET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_paket_ozet_card(
    result: dict[str, Any] | None,
    *,
    source: str = "auto",
) -> dict[str, Any] | None:
    """Paket sihirbazı sonucundan UI özet kartı üret."""
    if not paket_ozet_enabled() or not result or not result.get("ok"):
        return None

    steps = list(result.get("steps") or [])
    lines: list[str] = []
    ok_count = 0
    archive_path = None
    for step in steps:
        name = _STEP_LABELS.get(str(step.get("step") or ""), str(step.get("step") or "?"))
        if step.get("ok"):
            ok_count += 1
            lines.append(f"{name} ✓")
        else:
            lines.append(f"{name} ✗")
        if step.get("step") == "archive" and step.get("ok"):
            archive_path = step.get("archive_path")

    upload_ids = list(result.get("upload_ids") or [])
    return {
        "ok": True,
        "source": source,
        "session_id": result.get("session_id"),
        "upload_ids": upload_ids,
        "file_count": len(upload_ids),
        "topic": (result.get("topic") or "").strip()[:200],
        "collection": (result.get("collection") or "").strip(),
        "steps_summary": " · ".join(lines) if lines else "—",
        "ok_steps": ok_count,
        "total_steps": len(steps),
        "nebula_async": bool(result.get("nebula_async")),
        "archive_path": archive_path,
        "partial_errors": list(result.get("partial_errors") or []),
        "hint": (
            result.get("hint")
            or f"Paket özeti: {ok_count}/{len(steps) or 1} adım tamam."
        ),
    }
