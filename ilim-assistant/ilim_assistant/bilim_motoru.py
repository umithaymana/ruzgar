# Created by Ümit & Gökçenur
"""Bilim motoru — tabiat, tarih, dil ve ilimî meselelerde bilge üslup (Okuma/İlim motorunun bilim yüzü)."""

from __future__ import annotations

from ilim_assistant.okuma_motoru import build_motor_context as _okuma_context


def build_motor_context(message: str) -> str:
    prompt = (message or "").strip()
    base = _okuma_context(prompt)
    return base + (
        "\n\n[BİLİM MOTORU — Ümit & Gökçenur]\n"
        "Tarih, medeniyet, tabiat ve ilim sorularında yalnızca kuru liste verme; kullanıcının **niyetini** "
        "(genel merak, derinlik, özet mi ayrıntı mı) sez; kısa tarihî veya kavramsal çerçeveyle "
        "ölçülü betimleme yap. Kesin tarih veya rakam uydurma; emin değilsen dürüstçe söyle.\n"
    )
