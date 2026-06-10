# Created by Ümit & Gökçenur
"""Ana Motor Faz AA2 — birleşik Kaynak & Nebula panel meta."""

from __future__ import annotations

import os
from typing import Any

FAZ_AA_PANEL_VERSION = "ana-motor-kaynak-panel-aa2-2026-06-10"


def kaynak_panel_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_KAYNAK_PANEL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def kaynak_panel_fold_default() -> bool:
    return os.environ.get("RUZGAR_ANA_KAYNAK_PANEL_FOLD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_kaynak_panel_hint(
    research_card: dict[str, Any] | None,
    nebula_card: dict[str, Any] | None,
) -> str:
    parts: list[str] = []
    if research_card and research_card.get("ok"):
        totals = research_card.get("totals") or {}
        n = sum(int(v or 0) for v in totals.values())
        if n:
            parts.append(f"{n} kaynak")
        elif research_card.get("primary"):
            parts.append(str(research_card.get("primary")))
    if nebula_card and nebula_card.get("ok"):
        col = nebula_card.get("collection_title") or nebula_card.get("collection") or "Nebula"
        parts.append(f"öneri: {col}")
    if not parts:
        return "Henüz veri yok — genişlet"
    return " · ".join(parts)


def merge_kaynak_panel_payload(
    research_card: dict[str, Any] | None = None,
    nebula_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not kaynak_panel_enabled():
        return {"ok": False, "disabled": True}
    has_r = bool(research_card and research_card.get("ok"))
    has_n = bool(nebula_card and nebula_card.get("ok"))
    return {
        "ok": has_r or has_n,
        "version": FAZ_AA_PANEL_VERSION,
        "has_research": has_r,
        "has_nebula": has_n,
        "hint": build_kaynak_panel_hint(research_card, nebula_card),
        "fold_default": kaynak_panel_fold_default(),
        "research_card": research_card if has_r else None,
        "nebula_card": nebula_card if has_n else None,
    }


def get_kaynak_panel_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": FAZ_AA_PANEL_VERSION,
        "enabled": kaynak_panel_enabled(),
        "fold_default": kaynak_panel_fold_default(),
    }
