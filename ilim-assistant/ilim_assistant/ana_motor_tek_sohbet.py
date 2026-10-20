# Created by Ümit & Gökçenur
"""Ana Motor — tek sohbet orkestrasyonu (2026-10-20).

Genel sohbette yüzey → motor gönderme niyetini tanır; UI'ya quiet handoff
sinyali verir. Motor sekmesine zorla geçmez (unified face).
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

TEK_SOHBET_VERSION = "ana-motor-tek-sohbet-v1-2026-10-20"

_MOTOR_MAP = {
    "tercumeye": "tercume",
    "tercümeye": "tercume",
    "ceviriye": "tercume",
    "programlamaya": "programlama",
    "koda": "programlama",
    "sese": "ses",
    "videoya": "video",
    "hafizaya": "hafiza",
    "hafızaya": "hafiza",
    "okumaya": "okuma",
    "mimara": "mimar",
    "tercume": "tercume",
    "programlama": "programlama",
    "ses": "ses",
    "video": "video",
    "hafiza": "hafiza",
    "okuma": "okuma",
    "mimar": "mimar",
}

_SURFACE_SEND_RE = re.compile(
    r"^(?:bunu|belgeyi|kodu|notlari|notları|metni|yuzeyi|yüzeyi|tabloyu|sunumu|"
    r"okumayi|okumayı)\s+"
    r"(tercumeye|tercümeye|ceviriye|programlamaya|koda|sese|videoya|"
    r"hafizaya|hafızaya|okumaya|mimara)\s+g[öo]nder[.!?]*$",
    re.I,
)

_KOPRU_RE = re.compile(
    r"^(?:kopru|köprü)\s*[:\-]?\s*"
    r"(tercume|tercüme|programlama|ses|video|hafiza|hafıza|okuma|mimar)[.!?]*$",
    re.I,
)


def tek_sohbet_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_TEK_SOHBET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").strip()
    return t


def parse_surface_motor_send(message: str) -> dict[str, Any] | None:
    """«belgeyi tercümeye gönder» / «köprü: programlama» → motor id."""
    if not tek_sohbet_enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 400:
        return None
    m = _SURFACE_SEND_RE.match(raw)
    if m:
        key = m.group(1).lower()
        mid = _MOTOR_MAP.get(key) or _MOTOR_MAP.get(
            key.replace("ü", "u").replace("ı", "i").replace("ö", "o")
        )
        if mid:
            return {
                "motor": mid,
                "kind": "surface_handoff",
                "version": TEK_SOHBET_VERSION,
            }
    m2 = _KOPRU_RE.match(raw)
    if m2:
        key = m2.group(1).lower().replace("ü", "u").replace("ı", "i")
        mid = _MOTOR_MAP.get(key) or _MOTOR_MAP.get(m2.group(1).lower())
        if mid == "okuma":
            mid = "mimar"
        if mid:
            return {
                "motor": mid,
                "kind": "surface_handoff",
                "version": TEK_SOHBET_VERSION,
            }
    return None


def enrich_orchestra_tek_sohbet(
    orch: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    """Orchestra meta — tek sohbet quiet handoff bayrağı."""
    out = dict(orch or {})
    if not tek_sohbet_enabled():
        return out
    hit = parse_surface_motor_send(message)
    if not hit:
        out.setdefault("tek_sohbet", True)
        return out
    mid = str(hit["motor"])
    try:
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import enrich_orchestra_motor

        out = enrich_orchestra_motor(
            out,
            target=mid,
            channel="tek_sohbet_surface",
        )
    except Exception:
        out["active_motor"] = mid
        out["motors"] = list(out.get("motors") or []) + [
            {"id": mid, "label": mid, "handoff": "surface", "quiet": True}
        ]
    out["tek_sohbet"] = True
    out["quiet"] = True
    out["ui_action"] = {
        "type": "surface_handoff",
        "motor": mid,
        "version": TEK_SOHBET_VERSION,
    }
    out["faz_tek_sohbet"] = TEK_SOHBET_VERSION
    return out


def tek_sohbet_status() -> dict[str, Any]:
    return {
        "enabled": tek_sohbet_enabled(),
        "version": TEK_SOHBET_VERSION,
    }
