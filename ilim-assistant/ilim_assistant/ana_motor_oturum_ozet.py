# Created by Ümit & Gökçenur
"""Ana Motor — Faz G: oturum özeti → kalıcı hafıza + export."""

from __future__ import annotations

import json
import os
import time
from typing import Any


FAZ_G_OTURUM_VERSION = "ana-motor-oturum-ozet-g1-2026-06-11"


def oturum_ozet_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_OTURUM_OZET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def export_chat_history_json(
    *,
    limit: int | None = None,
    session_id: str | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    try:
        from ilim_assistant.ana_motor_faz_ab import export_session_json, session_export_enabled

        if session_export_enabled():
            out = export_session_json(
                limit=limit,
                session_id=session_id,
                mode=mode,
            )
            if out.get("ok"):
                out["oturum_version"] = FAZ_G_OTURUM_VERSION
                return out
    except Exception:
        pass

    from ilim_assistant.ana_motor_sohbet_gecmis import export_session_chat_history

    data = export_session_chat_history(
        limit=limit or 100,
        session_id=session_id,
        mode=mode,
    )
    return {
        **data,
        "version": FAZ_G_OTURUM_VERSION,
    }


def maybe_remember_session_summary(
    *,
    user_message: str,
    assistant_message: str,
    mode_norm: str = "genel",
    every_n_turns: int = 5,
) -> dict[str, Any]:
    """Her N turda kısa özet «hatırla» hafızasına (onay gerektirmez — oturum özeti)."""
    if not oturum_ozet_enabled():
        return {"ok": True, "stored": False, "reason": "disabled"}
    if mode_norm != "genel":
        return {"ok": True, "stored": False, "reason": "mode"}
    user = (user_message or "").strip()
    reply = (assistant_message or "").strip()
    if len(user) < 12 or len(reply) < 40:
        return {"ok": True, "stored": False, "reason": "short"}
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import recent_chat_history

        hist = recent_chat_history(limit=every_n_turns + 2)
        count = int(hist.get("count") or 0)
        if count < every_n_turns or count % every_n_turns != 0:
            return {"ok": True, "stored": False, "reason": "not_interval"}
    except Exception:
        return {"ok": True, "stored": False, "reason": "history_err"}

    topics: list[str] = []
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import recent_chat_history

        for row in (recent_chat_history(limit=every_n_turns).get("items") or [])[:every_n_turns]:
            u = str(row.get("user") or "").strip()[:80]
            if u:
                topics.append(u)
    except Exception:
        topics = [user[:80]]

    soru = f"Oturum özeti — son {every_n_turns} tur"
    cevap = (
        f"Ümit abi ile son sohbet başlıkları ({time.strftime('%Y-%m-%d %H:%M')}):\n"
        + "\n".join(f"· {t}" for t in topics[:every_n_turns])
        + f"\n\nSon yanıt özeti: {reply[:280]}…"
    )
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        get_hafiza_motor().ekle_bilgi(soru, cevap[:4000], motor_tipi="OturumOzet")
        return {"ok": True, "stored": True, "version": FAZ_G_OTURUM_VERSION}
    except Exception as exc:
        return {"ok": False, "stored": False, "error": str(exc)[:120]}
