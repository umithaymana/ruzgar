# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 61 (Faz 55b): Başarısız görevde otomatik retry turu.

Uygulama çekirdeği: programlama_faz55 (bonus tur + nudge).
"""

from __future__ import annotations

from typing import Any

FAZ61_VERSION = "programlama-faz61-v1-2026-05-26"


def faz61_enabled() -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import faz55b_enabled

        return faz55b_enabled()
    except Exception:
        return False


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz61"] = faz61_enabled()
    out["faz55b_auto_retry"] = out["faz61"]
    return out


def faz61_directive() -> str:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import faz55b_directive

        return faz55b_directive()
    except Exception:
        return ""
