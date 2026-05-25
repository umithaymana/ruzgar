# Created by Ümit & Gökçenur
"""Faz 46 — Cursor parity kilidi (programlama_cursor_parity.py üstü)."""

from __future__ import annotations

from ilim_assistant.motorlar.programlama_cursor_parity import (
    CURSOR_PARITY_VERSION,
    FAZ46_VERSION,
    TARGET_CURSOR_SCORE,
    ci_score_warning,
    cursor_parity_enabled,
    format_cursor_seviye_report,
    run_cursor_seviye_assessment,
    save_cursor_seviye_json,
)


def _enabled() -> bool:
    return cursor_parity_enabled()


def faz46_directive() -> str:
    return (
        "[CURSOR SEVİYE — Faz 46]\n"
        f"3 senaryo offline · hedef skor ≥{TARGET_CURSOR_SCORE}/100.\n"
        "Rapor: scripts/ruzgar_cursor_seviye_sonuc.json · CI uyarı (bloklamaz).\n"
        "Kapat: RUZGAR_FAZ46=0\n"
    )
