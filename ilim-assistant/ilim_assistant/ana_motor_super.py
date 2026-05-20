# Created by Ümit & Gökçenur
"""Ana Motor Süper Beyin — bilgi/ilim sorularında tam ve dürüst yanıt talimatı."""

from __future__ import annotations

import os
from typing import Any


def super_directive_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_SUPER_DIRECTIVE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def append_super_brain_directive(
    user_payload: str,
    *,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
) -> str:
    if not super_directive_enabled():
        return user_payload
    primary = ""
    if question_plan is not None:
        if hasattr(question_plan, "primary"):
            primary = str(getattr(question_plan, "primary", "") or "").strip().lower()
        elif isinstance(question_plan, dict):
            primary = str(question_plan.get("primary") or "").strip().lower()
    if primary not in ("bilgi", "bilim", "dilbilgisi") and mode_norm not in (
        "okuma",
        "hafiza",
    ):
        return user_payload
    block = (
        "\n\n[TALİMAT — ANA MOTOR SÜPER BEYİN — Ümit & Gökçenur]\n"
        "Ümit abi'ye **doğrudan, eksiksiz ve saygılı** Türkçe yanıt ver; "
        "soru ne soruyorsa ona odaklan (gereksiz karşılama veya «nasıl yardımcı olabilirim» yok).\n"
        "- Önce BAĞLAM ve kaynaklar; yetersizse dürüstçe sınırını belirt.\n"
        "- Teknik, tarih, ilim ve günlük bilgi sorularında **madde madde veya net paragraflar** kullan.\n"
        "- Bilmediğin detayı **uydurma**; «emin değilim» demek, yanlış bilgi vermekten iyidir.\n"
        "- Yanıtın sonunda **Güven:** satırı zorunlu (yüksek / orta / düşük + bir cümle gerekçe).\n"
    )
    return user_payload.rstrip() + block
