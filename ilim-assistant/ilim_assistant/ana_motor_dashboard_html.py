# Created by Ümit & Gökçenur
"""Ana Motor Faz U3 — dashboard tek sayfa HTML özeti."""

from __future__ import annotations

import html
import os
import time
from typing import Any


def dashboard_html_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_DASHBOARD_HTML", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _esc(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def build_dashboard_html_summary(*, period_days: int = 7) -> dict[str, Any]:
    """Tüm Ana Motor panellerini tek HTML sayfasında birleştir."""
    if not dashboard_html_enabled():
        return {"ok": True, "html": "", "disabled": True}

    period = max(1, min(int(period_days), 30))
    sections: list[str] = []
    generated = time.strftime("%Y-%m-%d %H:%M")

    try:
        from ilim_assistant.ana_motor_haftalik_ozet import build_weekly_timeline_summary

        ws = build_weekly_timeline_summary(days=period, limit=40)
        card = ws.get("summary_card") if isinstance(ws.get("summary_card"), dict) else {}
        sections.append(
            f"<section><h2>{_esc(card.get('title') or 'Haftalık özet')}</h2>"
            f"<pre>{_esc(card.get('body') or '')}</pre></section>"
        )
    except Exception as exc:
        sections.append(f"<section><h2>Haftalık özet</h2><p>{_esc(exc)}</p></section>")

    try:
        from ilim_assistant.ana_motor_paket_karsilastir import build_paket_history_compare

        cmp = build_paket_history_compare(period_days=period)
        card = cmp.get("compare_card") if isinstance(cmp.get("compare_card"), dict) else {}
        sections.append(
            f"<section><h2>{_esc(card.get('title') or 'Karşılaştırma')}</h2>"
            f"<pre>{_esc(card.get('body') or '')}</pre></section>"
        )
    except Exception as exc:
        sections.append(f"<section><h2>Karşılaştırma</h2><p>{_esc(exc)}</p></section>")

    try:
        from ilim_assistant.ana_motor_compare_grafik import build_compare_dual_chart

        chart = build_compare_dual_chart(period_days=period)
        rows = []
        for g in chart.get("groups") or []:
            rows.append(
                f"<tr><td>{_esc(g.get('label'))}</td>"
                f"<td>{g.get('current', 0)}</td>"
                f"<td>{g.get('previous', 0)}</td></tr>"
            )
        table = (
            "<table><thead><tr><th>Metrik</th><th>Bu dönem</th><th>Önceki</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            if rows
            else "<p>Grafik verisi yok.</p>"
        )
        sections.append(f"<section><h2>Karşılaştırma grafiği</h2>{table}</section>")
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_paket_grafik import build_paket_history_summary

        pg = build_paket_history_summary(limit=80)
        sm = pg.get("summary") if isinstance(pg.get("summary"), dict) else {}
        sections.append(
            f"<section><h2>Paket geçmişi</h2>"
            f"<p>{sm.get('total', 0)} olay · {sm.get('unique_sessions', 0)} oturum · "
            f"{sm.get('file_total', 0)} dosya</p></section>"
        )
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_hatirla_gecmis import list_remember_history

        rh = list_remember_history(limit=8)
        items = "".join(
            f"<li>{_esc((r.get('session_id') or '')[:8])} — {_esc(r.get('topic') or '')}</li>"
            for r in (rh.get("items") or [])
        )
        sections.append(
            f"<section><h2>Hatırla geçmişi ({rh.get('count', 0)})</h2>"
            f"<ul>{items or '<li>—</li>'}</ul></section>"
        )
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_bildirim_gecmis import list_notify_history

        nh = list_notify_history(limit=8)
        items = "".join(
            f"<li>{_esc(r.get('channel'))}: {_esc((r.get('body') or '')[:80])}</li>"
            for r in (nh.get("items") or [])
        )
        sections.append(
            f"<section><h2>Bildirim geçmişi ({nh.get('count', 0)})</h2>"
            f"<ul>{items or '<li>—</li>'}</ul></section>"
        )
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_haftalik_zamanlayici import get_weekly_schedule_status

        st = get_weekly_schedule_status()
        sections.append(
            f"<section><h2>Zamanlayıcı</h2>"
            f"<p>Poll {st.get('poll_sec')} sn · sonraki {st.get('next_poll_in_sec')} sn</p></section>"
        )
    except Exception:
        pass

    page = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8"/>
<title>Rüzgar Ana Motor — Dashboard</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#0f1419;color:#e0e0e0;padding:20px;max-width:900px;margin:auto}}
h1{{color:#58c278}} h2{{color:#9cdc9c;border-bottom:1px solid #333;padding-bottom:4px}}
section{{margin:18px 0;padding:12px;background:#1a1f26;border-radius:8px}}
pre{{white-space:pre-wrap;font-size:13px;color:#b8c4d0}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{border:1px solid #333;padding:6px;text-align:left}}
th{{background:#252526}}
ul{{margin:0;padding-left:18px;font-size:13px}}
footer{{margin-top:24px;font-size:11px;color:#6b7480}}
</style>
</head>
<body>
<h1>Rüzgar Ana Motor — Dashboard Özeti</h1>
<p>Üretim: {_esc(generated)} · Dönem: {period} gün</p>
{''.join(sections)}
<footer>Ümit &amp; Gökçenur — Rüzgar Ana Motor Faz U</footer>
</body>
</html>"""

    return {
        "ok": True,
        "html": page,
        "section_count": len(sections),
        "filename": f"ruzgar_ana_motor_dashboard_{period}g.html",
    }
