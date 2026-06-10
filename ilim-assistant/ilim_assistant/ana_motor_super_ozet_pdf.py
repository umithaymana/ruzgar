# Created by Ümit & Gökçenur
"""Ana Motor Faz T1 — tüm paneller tek süper özet PDF."""

from __future__ import annotations

import os
import time
from typing import Any


def super_ozet_pdf_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_SUPER_OZET_PDF", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_super_ozet_lines(*, period_days: int = 7) -> list[str]:
    """Haftalık özet + karşılaştırma + grafik + geçmiş sayıları."""
    lines: list[str] = [f"Ruzgar Ana Motor Super Ozet — {time.strftime('%Y-%m-%d %H:%M')}", ""]

    try:
        from ilim_assistant.ana_motor_haftalik_ozet import build_weekly_timeline_summary

        ws = build_weekly_timeline_summary(days=period_days, limit=40)
        card = ws.get("summary_card") if isinstance(ws.get("summary_card"), dict) else {}
        lines.append("=== Haftalik Ozet ===")
        lines.append(str(card.get("title") or "Haftalik ozet"))
        for part in str(card.get("body") or "").split("\n"):
            if part.strip():
                lines.append(part.strip())
        lines.append("")
    except Exception as exc:
        lines.append(f"Haftalik ozet hatasi: {exc}")

    try:
        from ilim_assistant.ana_motor_paket_karsilastir import build_paket_history_compare

        cmp = build_paket_history_compare(period_days=period_days)
        card = cmp.get("compare_card") if isinstance(cmp.get("compare_card"), dict) else {}
        lines.append("=== Karsilastirma ===")
        for part in str(card.get("body") or "").split("\n"):
            if part.strip():
                lines.append(part.strip())
        lines.append("")
    except Exception as exc:
        lines.append(f"Karsilastirma hatasi: {exc}")

    try:
        from ilim_assistant.ana_motor_paket_grafik import build_paket_history_summary

        pg = build_paket_history_summary(limit=80)
        sm = pg.get("summary") if isinstance(pg.get("summary"), dict) else {}
        lines.append("=== Paket Gecmisi ===")
        lines.append(
            f"Toplam {sm.get('total', 0)} olay · "
            f"{sm.get('unique_sessions', 0)} oturum · "
            f"{sm.get('file_total', 0)} dosya"
        )
        by_olay = sm.get("by_olay") if isinstance(sm.get("by_olay"), dict) else {}
        if by_olay:
            lines.append("Olay: " + " · ".join(f"{k}:{v}" for k, v in list(by_olay.items())[:8]))
        lines.append("")
    except Exception as exc:
        lines.append(f"Paket grafik hatasi: {exc}")

    try:
        from ilim_assistant.ana_motor_hatirla_gecmis import list_remember_history

        rh = list_remember_history(limit=5)
        lines.append(f"=== Hatirla Gecmisi ({rh.get('count', 0)} kayit) ===")
        for item in (rh.get("items") or [])[:5]:
            lines.append(
                f"- {(item.get('session_id') or '')[:8]} "
                f"{'OK' if item.get('ok') else 'FAIL'} "
                f"{(item.get('topic') or '')[:50]}"
            )
        lines.append("")
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_bildirim_gecmis import list_notify_history

        nh = list_notify_history(limit=5)
        lines.append(f"=== Bildirim Gecmisi ({nh.get('count', 0)} kayit) ===")
        for item in (nh.get("items") or [])[:5]:
            lines.append(f"- {item.get('channel')}: {(item.get('body') or '')[:60]}")
        lines.append("")
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_haftalik_zamanlayici import get_weekly_schedule_status

        st = get_weekly_schedule_status()
        lines.append("=== Zamanlayici ===")
        lines.append(
            f"Poll {st.get('poll_sec')}sn · "
            f"sonraki {st.get('next_poll_in_sec')}sn · "
            f"cooldown={'evet' if st.get('notify_cooldown_active') else 'hayir'}"
        )
    except Exception:
        pass

    return lines


def export_super_ozet_pdf(*, period_days: int = 7) -> dict[str, Any]:
    if not super_ozet_pdf_enabled():
        return {"ok": False, "error": "Süper özet PDF kapalı."}
    lines = build_super_ozet_lines(period_days=period_days)
    if len(lines) < 3:
        return {"ok": False, "error": "Süper özet içeriği üretilemedi."}
    from ilim_assistant.ana_motor_paket_export import build_minimal_pdf

    period = max(1, min(int(period_days), 30))
    pdf_bytes = build_minimal_pdf(lines, title="Ruzgar Ana Motor Super Ozet")
    return {
        "ok": True,
        "pdf": pdf_bytes,
        "line_count": len(lines),
        "filename": f"ruzgar_ana_motor_super_ozet_{period}g.pdf",
    }
