# Created by Ümit & Gökçenur
"""Ana Motor — Faz J: önerilen akıl profili (ChatGPT yakınlık)."""

from __future__ import annotations

import os

AKIL_FAZ_J_VERSION = "akil-faz-j-v1-2026-06-11"


def akil_faz_j_enabled() -> bool:
    return os.environ.get("RUZGAR_AKIL_FAZ_J", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def recommended_brain_env() -> dict[str, str]:
    """Önerilen ortam — kullanıcı RUZGAR_BRAIN.env içine kopyalayabilir."""
    return {
        "GROQ_BILGI_MODEL": "llama-3.1-8b-instant",
        "RUZGAR_BILGI_CLOUD_FAST": "1",
        "RUZGAR_BILGI_HYBRID": "1",
        "RUZGAR_ILIM_RAG_CLOUD_FIRST": "1",
        "RUZGAR_GENEL_LOCAL_FIRST": "1",
        "RUZGAR_UMED_ILIM_BUDGET_SEC": "38",
        "RUZGAR_HUB_SSE_FAZ_D": "1",
        "RUZGAR_HUB_SSE_FAZ_E": "1",
        "RUZGAR_TEK_SES_FAZ_B": "1",
        "RUZGAR_ORKESTRASYON_FAZ_C": "1",
    }


def akil_faz_j_status() -> dict[str, object]:
    rec = recommended_brain_env()
    active = {k: os.environ.get(k, "") for k in rec}
    return {
        "enabled": akil_faz_j_enabled(),
        "version": AKIL_FAZ_J_VERSION,
        "recommended": rec,
        "active_match": {k: active.get(k, "") == v for k, v in rec.items()},
    }
