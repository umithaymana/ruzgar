# Created by Ümit & Gökçenur
"""Tek beyin Faz P — zorunlu web araştırması ve kaynak odaklı yanıt."""

from __future__ import annotations

import os
from typing import Any

TEK_BEYIN_WEB_ARASTIRMA_VERSION = "tek-beyin-web-v1-2026-06-13-faz-p"


def tek_beyin_web_arastirma_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_WEB", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def is_force_web_research(orchestration: dict[str, Any] | None) -> bool:
    if not orchestration:
        return False
    return bool(orchestration.get("force_web_research"))


def apply_force_web_to_plan(plan: Any, message: str) -> Any:
    """«Webten ara bul» sonrası plan — web zorunlu, indeks ikincil."""
    if plan is None:
        return plan
    q = (message or "").strip()
    try:
        plan.prefer_web = True
        plan.use_ilim_rag = False
        plan.prefer_archive = False
        if q:
            plan.web_query = q
            plan.rag_query = q
        plan.status_text = f"Web araştırması — «{q[:72]}» için kaynak taraması"
    except Exception:
        pass
    return plan


def build_web_research_system_addon(message: str) -> str:
    q = (message or "").strip()[:200]
    return (
        "\n[TALİMAT — WEB ARAŞTIRMASI (Faz P)]\n"
        f"Kullanıcı «{q}» konusunda **web'den doğrulanmış** bilgi istiyor.\n"
        "- Önce sorunun özünü net yanıtla; gereksiz sohbet ekleme.\n"
        "- Tarih, isim, rakam verirken web kaynaklarıyla uyumlu ol; uydurma.\n"
        "- Çelişkili kaynak varsa en güvenilir olanı söyle, belirsizliği kısaca belirt.\n"
        "- Kişisel hafıza/çevre bilgisi sanma — ansiklopedik/güncel bilgi modu.\n"
    )


def tek_beyin_web_arastirma_status() -> dict[str, Any]:
    return {
        "enabled": tek_beyin_web_arastirma_enabled(),
        "version": TEK_BEYIN_WEB_ARASTIRMA_VERSION,
    }
