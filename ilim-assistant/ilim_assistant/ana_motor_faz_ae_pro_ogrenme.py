# Created by Ümit & Gökçenur
"""Ana Motor — Faz AE2: Sentez PRO turundan güçlendirilmiş otomatik öğrenme köprüsü."""

from __future__ import annotations

import os
from typing import Any

FAZ_AE_PRO_OGRENME_VERSION = "pro-ogrenme-faz-ae-v1-2026-06-13"


def pro_ogrenme_bridge_enabled() -> bool:
    if os.environ.get("RUZGAR_PRO_OGRENME_BRIDGE", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    try:
        from ilim_assistant.ana_motor_faz_ad_sentez_pro import sentez_pro_enabled

        return sentez_pro_enabled()
    except Exception:
        return True


def maybe_boost_learn_after_pro_turn(
    user_message: str,
    assistant_message: str,
    learn_meta: dict[str, Any] | None,
    *,
    sentez_pro: bool,
    plan_primary: str = "",
    web_used: bool = False,
    hits: list | None = None,
) -> dict[str, Any]:
    """
    Sentez PRO kullanılan turda Nebula köprüsünü güçlendir.
    Hafıza zaten kaydedildiyse ve Nebula atlandıysa force_web ile yeniden dene.
    """
    meta = dict(learn_meta or {})
    if not sentez_pro or not pro_ogrenme_bridge_enabled():
        return meta
    if not meta.get("saved"):
        return meta

    meta["sentez_pro_learn"] = True
    meta["pro_ogrenme_version"] = FAZ_AE_PRO_OGRENME_VERSION

    if meta.get("nebula_bridge", {}).get("ok"):
        meta["pro_ogrenme_note"] = "Nebula zaten uygulandı"
        return meta

    try:
        from ilim_assistant.ruzgar_otomatik_ogrenme import maybe_nebula_bridge_from_learn

        nb = maybe_nebula_bridge_from_learn(
            user_message,
            assistant_message,
            plan_primary=plan_primary,
            web_used=True,
            force_web=True,
            hits=hits,
        )
        if nb.get("ok"):
            meta["nebula_bridge"] = nb
            meta["pro_ogrenme_note"] = "PRO tur — Nebula köprüsü güçlendirildi"
        elif nb.get("skipped"):
            meta["pro_ogrenme_skipped"] = nb.get("reason")
        else:
            meta["pro_ogrenme_error"] = nb.get("error")
    except Exception as exc:
        meta["pro_ogrenme_error"] = str(exc)[:200]
    return meta


def pro_ogrenme_status() -> dict[str, Any]:
    return {
        "enabled": pro_ogrenme_bridge_enabled(),
        "version": FAZ_AE_PRO_OGRENME_VERSION,
        "requires_sentez_pro": True,
    }
