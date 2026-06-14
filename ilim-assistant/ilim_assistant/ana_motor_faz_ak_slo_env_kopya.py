# Created by Ümit & Gökçenur
"""Ana Motor — Faz AK1: SLO env diff kopyalanabilir satırlar."""

from __future__ import annotations

import os
from typing import Any

FAZ_AK_SLO_ENV_KOPYA_VERSION = "slo-env-kopya-faz-ak-v1-2026-06-13"


def slo_env_kopya_enabled() -> bool:
    return os.environ.get("RUZGAR_SLO_ENV_KOPYA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_copyable_env_diff(*, limit: int = 8) -> dict[str, Any]:
    """Eksik/farklı env satırlarını panoya kopyalamak için metin."""
    if not slo_env_kopya_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AK_SLO_ENV_KOPYA_VERSION,
            "copy_text": "",
        }
    try:
        from ilim_assistant.ana_motor_faz_aj_slo_env_diff import build_slo_env_diff
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "error": str(exc)[:160],
            "version": FAZ_AK_SLO_ENV_KOPYA_VERSION,
        }

    diff = build_slo_env_diff(limit=limit)
    lines: list[str] = ["# Rüzgar SLO env düzeltmeleri — .env dosyasına elle ekleyin"]
    for row in diff.get("missing") or []:
        if isinstance(row, dict):
            lines.append(f"{row.get('key')}={row.get('suggested', '1')}")
    for row in diff.get("different") or []:
        if isinstance(row, dict):
            lines.append(f"{row.get('key')}={row.get('suggested', '1')}")
    copy_text = "\n".join(lines)
    if len(lines) <= 1:
        copy_text = "# Eksik/farklı env satırı yok — mevcut ayarlar uyumlu görünüyor"

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AK_SLO_ENV_KOPYA_VERSION,
        "copy_text": copy_text[:2000],
        "summary_tr": diff.get("summary_tr"),
        "missing_count": len(diff.get("missing") or []),
        "different_count": len(diff.get("different") or []),
    }


def slo_env_kopya_status() -> dict[str, Any]:
    panel = build_copyable_env_diff(limit=6)
    return {
        "enabled": slo_env_kopya_enabled(),
        "version": FAZ_AK_SLO_ENV_KOPYA_VERSION,
        "summary_tr": panel.get("summary_tr"),
    }
