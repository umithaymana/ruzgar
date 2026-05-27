# Created by Ümit & Gökçenur
"""
Hızır motoru — Faz 84: ROK + Ana Motor hub.

Pazar tara / fırsat / ürün sorgusu → Hızır anlık veya delege.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

from ilim_assistant.ruzgar_motor_kernel import (
    INTENT_CHAT,
    INTENT_COMMAND,
    INTENT_DO,
    register_classifier,
)

FAZ84_VERSION = "hizir-faz84-v1-2026-05-26"

_REGISTERED = False

_HIZIR_DO_RE = re.compile(
    r"(?:pazar\s+tara|pazarları\s+tara|ürün\s+tara|urun\s+tara|ürünleri\s+tara|"
    r"fırsat\s+ara|firsat\s+ara|arbitraj|dropship|trendyol|amazon\s+tr|"
    r"kar\s+marj|komisyon|ekonomik\s+av)",
    re.I,
)
_HIZIR_CMD_RE = re.compile(
    r"(?:hizir\s+durum|hızır\s+durum|fırsat\s+listesi|firsat\s+listesi|"
    r"vitrin\s+temizle|hizir\s+temizle)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_HIZIR_FAZ84", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz84_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_classifier("hizir", classify_hizir_intent)
    _REGISTERED = True


def classify_hizir_intent(
    message: str,
    *,
    mode_norm: str = "hizir",
    **kwargs: Any,
) -> dict[str, Any]:
    _ = kwargs
    if mode_norm != "hizir":
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}
    raw = (message or "").strip()
    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}
    low = _ascii_fold(raw)
    if _HIZIR_CMD_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "hizir_command"}
    if _HIZIR_DO_RE.search(low) or "hizir" in low or "hızır" in low:
        return {"intent": INTENT_DO, "reason": "hizir_operation"}
    return {"intent": INTENT_CHAT, "reason": "conversation"}


def format_hizir_status() -> str:
    lines = [
        "Ümit abi, **Hızır motoru (Faz 84 ROK)**",
        "",
        "· `pazar tara` — ürün / fırsat taraması",
        "· Hızır sekmesinde operasyon merkezi",
        "· API: `/api/hizir/pazar-tara`",
        "",
        f"({FAZ84_VERSION})",
    ]
    try:
        from ilim_assistant.hizir.bellek import find_hizir_firsat_summary_lines

        mem = find_hizir_firsat_summary_lines("")[:5]
        if mem:
            lines.insert(4, "**Son fırsat özeti (bellek):**")
            for ln in mem:
                lines.insert(5, f"· {ln[:100]}")
    except Exception:
        pass
    return "\n".join(lines)


def maybe_instant_faz84(message: str, *, mode_norm: str = "hizir") -> str | None:
    if not _enabled():
        return None
    ensure_kernel_registered()
    raw = (message or "").strip()
    if not raw:
        return None
    low = _ascii_fold(raw)
    if _HIZIR_CMD_RE.search(low) and "durum" in low:
        return format_hizir_status()
    if wants_hub_hizir_route(raw):
        return format_hizir_status()
    return None


def wants_hub_hizir_route(message: str) -> bool:
    """Ana Motor hub — Hızır'a yönlendir."""
    if not _enabled():
        return False
    low = _ascii_fold(message or "")
    return bool(_HIZIR_DO_RE.search(low)) or (
        "hizir" in low and any(x in low for x in ("tara", "fırsat", "firsat", "ürün", "urun"))
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["hizir_faz84"] = faz84_enabled()
    return out


ensure_kernel_registered()
