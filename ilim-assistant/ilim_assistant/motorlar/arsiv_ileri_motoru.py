# Created by Ümit & Gökçenur
"""Arşiv ileri araştırma motoru — Osmanlıca OCR + Tarih dedektifliği birleşimi (temel)."""

from __future__ import annotations

import os

from ilim_assistant.motorlar.tarih_dedektifligi import build_tarih_dedektif_context


def arsiv_ileri_motor_enabled() -> bool:
    return os.environ.get("RUZGAR_ARSIV_ILERI_MOTOR", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def enrich_archive_turn(
    msg: str,
    hits: list[tuple[str, str, float]],
) -> str:
    """
    Arşiv öncelikli turda modele eklenecek ek talimat / bağlam.
    OCR katmanı görüntü yolu olmadan çağrılmaz; metin tabanlı arşivde tarih ipuçları kullanılır.
    """
    if not arsiv_ileri_motor_enabled():
        return ""
    parts: list[str] = []
    td = build_tarih_dedektif_context(
        msg, hits, invoke_via_arsiv_ileri=True
    ).strip()
    if td:
        parts.append(td)
    return "\n".join(parts).strip()
