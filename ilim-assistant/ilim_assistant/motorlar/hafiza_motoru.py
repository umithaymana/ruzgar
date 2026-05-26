# Created by Ümit & Gökçenur
"""
Hafıza motoru — kişisel not, görev, hatırlatıcı ve genel sözlük (Faz 75 ROK).
"""

from __future__ import annotations

from ilim_assistant.ruzgar_perf import RUZGAR_PERF_MIMAR

MIMAR_IMZA = RUZGAR_PERF_MIMAR


def build_motor_context(message: str) -> str:
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    base = dinamit_heartbeat() + (
        f"[HAFIZA MOTORU — {MIMAR_IMZA}]\n"
        "Kişisel hatırla/unut, görev listesi, zamanlı hatırlatıcı ve "
        "`ruzgar_genel_hafiza.json` sözlük eşleşmesi bu modda önceliklidir.\n"
        "Ham JSON kopyalama; kullanıcıya doğal Türkçe özet ver.\n"
        f"Kullanıcı mesajı: {prompt}"
    )
    try:
        from ilim_assistant.motorlar.hafiza_faz75 import augment_hafiza_context

        return augment_hafiza_context(base)
    except Exception:
        return base
