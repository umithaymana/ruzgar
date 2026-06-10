# Created by Ümit & Gökçenur
"""Ana Motor Faz P1 — paket geçmişi JSON/PDF dışa aktarım."""

from __future__ import annotations

import json
import os
import time
from typing import Any


def paket_json_export_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_JSON_EXPORT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def paket_pdf_export_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_PDF_EXPORT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _pdf_safe(text: str) -> str:
    repl = {
        "ı": "i",
        "İ": "I",
        "ş": "s",
        "Ş": "S",
        "ğ": "g",
        "Ğ": "G",
        "ü": "u",
        "Ü": "U",
        "ö": "o",
        "Ö": "O",
        "ç": "c",
        "Ç": "C",
        "—": "-",
        "·": ".",
    }
    out = str(text or "")
    for k, v in repl.items():
        out = out.replace(k, v)
    return out.encode("latin-1", errors="replace").decode("latin-1")


def _escape_pdf_text(text: str) -> str:
    return _pdf_safe(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_minimal_pdf(lines: list[str], *, title: str = "Ruzgar Ana Motor") -> bytes:
    """Bagimlilik olmadan basit tek sayfa PDF."""
    y = 750
    parts = ["BT", "/F1 10 Tf", f"50 {y} Td ({_escape_pdf_text(title)}) Tj"]
    y -= 18
    parts.append(f"0 -18 Td ({_escape_pdf_text('Uretim: ' + time.strftime('%Y-%m-%d %H:%M'))}) Tj")
    y -= 14
    for line in lines[:72]:
        parts.append(f"0 -12 Td ({_escape_pdf_text(line[:110])}) Tj")
        y -= 12
        if y < 48:
            break
    parts.append("ET")
    stream = "\n".join(parts).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    objects.append(
        f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode()
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    header = b"%PDF-1.4\n"
    body = b""
    offsets = [0]
    pos = len(header)
    for obj in objects:
        offsets.append(pos)
        body += obj
        pos += len(obj)

    xref_pos = pos
    xref = f"xref\n0 {len(offsets)}\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n"
    trailer = f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    return header + body + xref.encode() + trailer.encode()


def export_paket_history_json(*, limit: int = 200) -> dict[str, Any]:
    if not paket_json_export_enabled():
        return {"ok": False, "error": "Paket JSON dışa aktarım kapalı."}
    from ilim_assistant.ana_motor_paket_csv import build_paket_history_rows

    rows = build_paket_history_rows(limit=limit)
    if not rows:
        return {"ok": False, "error": "Dışa aktarılacak paket geçmişi yok."}
    payload = {
        "generated_at": time.time(),
        "row_count": len(rows),
        "rows": rows,
    }
    return {
        "ok": True,
        "json": json.dumps(payload, ensure_ascii=False, indent=2),
        "row_count": len(rows),
        "filename": "ruzgar_ana_motor_paket_gecmisi.json",
    }


def export_paket_history_pdf(*, limit: int = 200) -> dict[str, Any]:
    if not paket_pdf_export_enabled():
        return {"ok": False, "error": "Paket PDF dışa aktarım kapalı."}
    from ilim_assistant.ana_motor_paket_csv import build_paket_history_rows

    rows = build_paket_history_rows(limit=limit)
    if not rows:
        return {"ok": False, "error": "Dışa aktarılacak paket geçmişi yok."}
    lines = [f"Toplam kayit: {len(rows)}", ""]
    for i, row in enumerate(rows[:60], 1):
        lines.append(
            f"{i}. [{row.get('olay')}] {str(row.get('session_id') or '')[:12]} "
            f"- {row.get('zaman')} - {str(row.get('konu') or '')[:50]}"
        )
    pdf_bytes = build_minimal_pdf(lines, title="Ruzgar Ana Motor Paket Gecmisi")
    return {
        "ok": True,
        "pdf": pdf_bytes,
        "row_count": len(rows),
        "filename": "ruzgar_ana_motor_paket_gecmisi.pdf",
    }
