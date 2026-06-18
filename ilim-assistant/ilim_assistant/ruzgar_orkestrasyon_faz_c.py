# Created by Ümit & Gökçenur
"""
Ana Motor — Faz C «Tek Yüz Orkestrasyon» (2026-06-11).

Yardımcı motor yanıtları tek sohbet balonunda, Tek Ses ile uyumlu.
Hub meta → orchestra köprüsü (çalışma sayfası).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

ORKESTRASYON_FAZ_C_VERSION = "orkestrasyon-faz-c-v1-2026-06-11"

_HUB_BOILER = re.compile(
    r"\(Sohbet\s+Ana\s+Motor['']da\.?\)|\(sohbet\s+ana\s+motor['']da\.?\)",
    re.I,
)
_MOTOR_LABEL = {
    "programlama": "Programlama",
    "video": "Video",
    "hafiza": "Hafıza",
    "tercume": "Tercüme",
    "ses": "Ses",
    "mimar": "Mimar",
    "okuma": "Mimar",
    "hizir": "Hızır",
    "genel": "Ana Motor",
}


def orkestrasyon_faz_c_enabled() -> bool:
    return os.environ.get("RUZGAR_ORKESTRASYON_FAZ_C", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def motor_label_tr(motor_id: str) -> str:
    return _MOTOR_LABEL.get((motor_id or "").strip().lower(), motor_id or "Motor")


def polish_motor_reply(
    reply: str,
    *,
    target: str = "",
    channel: str = "",
) -> str:
    """Yardımcı motor çıktısı — Tek Ses + hub kalıbı temizliği."""
    if not orkestrasyon_faz_c_enabled():
        return (reply or "").strip()
    t = (reply or "").strip()
    if not t:
        return t
    t = _HUB_BOILER.sub("", t).strip()
    try:
        from ilim_assistant.ruzgar_tek_ses_faz_b import polish_tek_ses

        t = polish_tek_ses(t, channel=channel or target)
    except Exception:
        pass
    return t.strip()


def enrich_orchestra_motor(
    orch: dict[str, Any] | None,
    *,
    target: str,
    channel: str = "",
    plan: Any | None = None,
) -> dict[str, Any]:
    """Orchestra meta — motor köprüsü + tek yüz bayrağı."""
    out = dict(orch or {})
    if not orkestrasyon_faz_c_enabled():
        return out
    out["unified_face"] = True
    out["faz_c"] = ORKESTRASYON_FAZ_C_VERSION
    mid = (target or "").strip().lower()
    if mid and mid != "genel":
        motors = list(out.get("motors") or [])
        label = motor_label_tr(mid)
        entry = {
            "id": mid,
            "label": label,
            "handoff": channel or mid,
            "quiet": True,
        }
        if not any(str(m.get("id")) == mid for m in motors if isinstance(m, dict)):
            motors.append(entry)
        out["motors"] = motors
        out["active_motor"] = mid
        out.setdefault("hub", {})["target"] = mid
        out["hub"]["channel"] = channel or ""
    if plan is not None:
        try:
            if hasattr(plan, "to_dict"):
                out["plan"] = plan.to_dict()
            elif isinstance(plan, dict):
                out["plan"] = plan
        except Exception:
            pass
    return out


def build_genel_orchestra_preview(
    message: str,
    workspace_root: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Genel sohbet — erken orkestra UI (Faz C + hub hedef önizleme).
    resolve_hub_target yalnızca; anında hub yanıtı çalıştırmaz.
    """
    from ilim_assistant.idrak_entegrasyon import (
        build_orchestra_ui_payload,
        motor_niyeti_heuristic,
    )

    flags = motor_niyeti_heuristic(message)
    orch = build_orchestra_ui_payload(message, motor_flags=flags)
    route_patch: dict[str, Any] = {}
    if not orkestrasyon_faz_c_enabled():
        return orch, route_patch
    try:
        from ilim_assistant.motorlar.ana_motor_hub_faz76 import (
            faz76_enabled,
            resolve_hub_target,
        )

        if faz76_enabled():
            target, meta = resolve_hub_target(
                message, flags, workspace_root=workspace_root
            )
            route_patch["hub_delegate"] = dict(meta or {})
            if target and target != "genel":
                route_patch["hub_target"] = target
                orch = enrich_orchestra_motor(
                    orch,
                    target=target,
                    channel=str(meta.get("reason") or ""),
                )
            elif meta.get("winner"):
                orch["hub_preview"] = {
                    "winner": meta.get("winner"),
                    "reason": meta.get("reason"),
                }
    except Exception:
        pass
    return orch, route_patch


def orkestrasyon_status() -> dict[str, object]:
    return {
        "enabled": orkestrasyon_faz_c_enabled(),
        "version": ORKESTRASYON_FAZ_C_VERSION,
    }
