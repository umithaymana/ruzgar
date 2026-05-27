# Created by Ümit & Gökçenur
"""
Rüzgar — Faz 77: Cila + ince ayar (post-ROK).

- Motor KPI özeti (smoke ile)
- Build/manifest senkron ipuçları
"""

from __future__ import annotations

import os
from typing import Any

FAZ77_VERSION = "ruzgar-cila-faz77-v1-2026-05-26"

_MOTOR_FNS: tuple[tuple[str, str, str], ...] = (
    ("programlama", "ilim_assistant.motorlar.programlama_faz68", "faz68_enabled"),
    ("video", "ilim_assistant.motorlar.video_faz71", "faz71_enabled"),
    ("ses", "ilim_assistant.motorlar.ses_faz72", "faz72_enabled"),
    ("okuma", "ilim_assistant.motorlar.okuma_faz73", "faz73_enabled"),
    ("tercume", "ilim_assistant.motorlar.tercume_faz74", "faz74_enabled"),
    ("hafiza", "ilim_assistant.motorlar.hafiza_faz75", "faz75_enabled"),
    ("hizir", "ilim_assistant.motorlar.hizir_faz84", "faz84_enabled"),
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_CILA_FAZ77", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz77_enabled() -> bool:
    return _enabled()


def _flag_on(module: str, attr: str) -> bool:
    try:
        mod = __import__(module, fromlist=[attr])
        return bool(getattr(mod, attr)())
    except Exception:
        return True


def collect_rok_kpi() -> dict[str, Any]:
    """Offline KPI — ROK faz bayrakları ve kernel."""
    motors: dict[str, Any] = {}
    for mid, mod_path, fn in _MOTOR_FNS:
        motors[mid] = {"enabled": _flag_on(mod_path, fn)}
    hub = _flag_on("ilim_assistant.motorlar.ana_motor_hub_faz76", "faz76_enabled")
    kernel = _flag_on("ilim_assistant.ruzgar_motor_kernel", "kernel_enabled")
    ok = hub and kernel and all(m.get("enabled") for m in motors.values())
    return {
        "version": FAZ77_VERSION,
        "motors": motors,
        "hub": hub,
        "kernel": kernel,
        "ok": ok,
    }


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["cila_faz77"] = faz77_enabled()
    if faz77_enabled():
        try:
            kpi = collect_rok_kpi()
            out["rok_kpi_ok"] = bool(kpi.get("ok"))
        except Exception:
            out["rok_kpi_ok"] = None
    return out
