# Created by Ümit & Gökçenur
"""Ana Motor Faz V2 — dashboard HTML içeriğinin PDF dışa aktarımı."""

from __future__ import annotations

import os
import time
from typing import Any


def dashboard_pdf_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_DASHBOARD_PDF", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_dashboard_pdf_lines(*, period_days: int = 7) -> list[str]:
    """Dashboard panellerini düz metin satırlarına dönüştür (PDF için)."""
    period = max(1, min(int(period_days), 30))
    lines: list[str] = [
        f"Ruzgar Ana Motor Dashboard — {time.strftime('%Y-%m-%d %H:%M')}",
        f"Donem: {period} gun",
        "",
    ]

    try:
        from ilim_assistant.ana_motor_haftalik_ozet import build_weekly_timeline_summary

        ws = build_weekly_timeline_summary(days=period, limit=40)
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

        cmp = build_paket_history_compare(period_days=period)
        card = cmp.get("compare_card") if isinstance(cmp.get("compare_card"), dict) else {}
        lines.append("=== Karsilastirma ===")
        for part in str(card.get("body") or "").split("\n"):
            if part.strip():
                lines.append(part.strip())
        lines.append("")
    except Exception as exc:
        lines.append(f"Karsilastirma hatasi: {exc}")

    try:
        from ilim_assistant.ana_motor_compare_grafik import build_compare_dual_chart

        chart = build_compare_dual_chart(period_days=period)
        lines.append("=== Karsilastirma Grafigi ===")
        for g in chart.get("groups") or []:
            lines.append(
                f"{g.get('label')}: bu={g.get('current', 0)} onceki={g.get('previous', 0)}"
            )
        lines.append("")
    except Exception:
        pass

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
        lines.append("")
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_hatirla_gecmis import list_remember_history

        rh = list_remember_history(limit=8)
        lines.append(f"=== Hatirla Gecmisi ({rh.get('count', 0)} kayit) ===")
        for item in (rh.get("items") or [])[:8]:
            lines.append(
                f"- {(item.get('session_id') or '')[:8]} "
                f"{(item.get('topic') or '')[:50]}"
            )
        lines.append("")
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_bildirim_gecmis import list_notify_history

        nh = list_notify_history(limit=8)
        lines.append(f"=== Bildirim Gecmisi ({nh.get('count', 0)} kayit) ===")
        for item in (nh.get("items") or [])[:8]:
            lines.append(f"- {item.get('channel')}: {(item.get('body') or '')[:60]}")
        lines.append("")
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_haftalik_zamanlayici import get_weekly_schedule_status

        st = get_weekly_schedule_status()
        lines.append("=== Zamanlayici ===")
        lines.append(
            f"Poll {st.get('poll_sec')}sn · sonraki {st.get('next_poll_in_sec')}sn"
        )
    except Exception:
        pass

    return lines


def export_dashboard_pdf(*, period_days: int = 7) -> dict[str, Any]:
    if not dashboard_pdf_enabled():
        return {"ok": False, "error": "Dashboard PDF dışa aktarım kapalı."}
    lines = build_dashboard_pdf_lines(period_days=period_days)
    if len(lines) < 3:
        return {"ok": False, "error": "Dashboard PDF içeriği üretilemedi."}
    from ilim_assistant.ana_motor_paket_export import build_minimal_pdf

    period = max(1, min(int(period_days), 30))
    pdf_bytes = build_minimal_pdf(lines, title="Ruzgar Ana Motor Dashboard")
    return {
        "ok": True,
        "pdf": pdf_bytes,
        "line_count": len(lines),
        "filename": f"ruzgar_ana_motor_dashboard_{period}g.pdf",
    }
