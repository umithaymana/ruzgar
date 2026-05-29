# Created by Ümit & Gökçenur
"""Blok H — Ana Motor ↔ Programlama handoff workbench (v4)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

HANDOFF_WORKBENCH_VERSION = "programlama-handoff-v4-2026-05-29"
_E4_TARGET = 0.85
_HUB_CHAIN = (
    "genel",
    "programlama",
    "video",
    "ses",
    "okuma",
    "tercume",
    "hafiza",
    "hizir",
)


def e4_target_rate() -> float:
    try:
        return max(0.5, min(0.99, float(os.environ.get("RUZGAR_E4_TARGET_RATE", str(_E4_TARGET)))))
    except ValueError:
        return _E4_TARGET


def _load_delegation_items(workspace_root: str | Path | None) -> list[dict[str, Any]]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return []
        path = root / ".ruzgar" / "delegation_summaries.json"
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return list((data or {}).get("items") or [])[-8:]
    except Exception:
        return []


def build_handoff_workbench_payload(
    workspace_root: str | Path | None,
    *,
    message: str = "",
    active_file: str | None = None,
    hub_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ilim_assistant.ana_motor_faz59 import (
        format_delegation_summary_text,
        load_last_delegation_summary,
    )
    from ilim_assistant.motorlar.programlama_faz79 import build_handoff_packet_v3
    from ilim_assistant.ruzgar_ui_manifest import build_ui_manifest

    msg = (message or "").strip()
    last = load_last_delegation_summary(workspace_root)
    if not msg and last:
        msg = str(last.get("goal") or "görev devam programlama")

    pkt = build_handoff_packet_v3(
        msg or "programlama görevi",
        workspace_root,
        active_file=active_file,
        hub_meta=hub_meta,
    )

    items = _load_delegation_items(workspace_root)
    context_log = [
        {
            "scope_rel": it.get("scope_rel"),
            "success": it.get("success"),
            "verify_ok": it.get("verify_ok"),
            "turns_used": it.get("turns_used"),
            "goal": str(it.get("goal") or "")[:80],
        }
        for it in items[-5:]
    ]

    v_ok = last.get("verify_ok") if last else None
    pytest_footer = (
        "pytest: yeşil ✓"
        if v_ok is True
        else ("pytest: kırmızı — tekrar dene" if v_ok is False else "pytest: henüz yok")
    )

    manifest = build_ui_manifest()
    prog_tag = str((manifest.get("motors") or {}).get("programlama", {}).get("tag") or "")
    manifest_ok = bool(prog_tag) and ("programlama" in prog_tag.lower() or "faz" in prog_tag.lower())

    delege_text = ""
    if last:
        delege_text = format_delegation_summary_text(last).strip()

    successes = sum(1 for it in items if it.get("success"))
    e4_rate = (successes / len(items)) if items else 0.0

    return {
        "ok": True,
        "version": HANDOFF_WORKBENCH_VERSION,
        "handoff": {
            "ok": bool(pkt.get("ok")),
            "scope_rel": pkt.get("scope_rel"),
            "template": pkt.get("parsed_template"),
            "packet_preview": str(pkt.get("packet_text") or "")[:1200],
            "v3": bool(pkt.get("handoff_v3")),
        },
        "delegation": {
            "last": last,
            "report_short": delege_text[:500] if delege_text else "",
            "pytest_footer": pytest_footer,
        },
        "motor_chain": [{"id": m, "label": m} for m in _HUB_CHAIN],
        "context_log": context_log,
        "return_hint": (
            "Ana Motor sohbetine dön: genel mod · özet iste"
            if pkt.get("ok")
            else ""
        ),
        "manifest": {
            "programlama_tag": prog_tag,
            "ok": manifest_ok,
        },
        "e4": {
            "target_rate": e4_target_rate(),
            "recent_success_rate": round(e4_rate, 3),
            "sample_count": len(items),
            "meets_target": len(items) >= 3 and e4_rate >= e4_target_rate(),
        },
    }
