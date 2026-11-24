# Created by Ümit & Gökçenur
"""O1 — tek tur Karar kaydı (Kuzey Yıldızı).

Her turda bir kez üretilir: niyet, hedef motor, canlı bilgi, kütüphane, üslup, bütçe, güven.
Kestirmeler sonraki dilimde bu kayda bağlanır. Boot sırasına dokunmaz.
Kapat: RUZGAR_O1_KARAR=0
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any

O1_VERSION = "o1-karar-v1-2026-11-24"


def o1_enabled() -> bool:
    return os.environ.get("RUZGAR_O1_KARAR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


@dataclass
class Karar:
    niyet: str
    hedef_motor: str
    canli: bool
    kutuphane: bool
    uslup: str
    butce_sn: float
    guven: float
    version: str = O1_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def karar_uret(
    message: str,
    *,
    mode_norm: str = "genel",
    question_plan: Any | None = None,
    butce_sn: float | None = None,
) -> Karar:
    """Aynı mesaj + plan → aynı kayıt (yan etki yok)."""
    raw = (message or "").strip()
    primary = str(getattr(question_plan, "primary", "") or "")
    use_rag = bool(getattr(question_plan, "use_ilim_rag", True)) if question_plan is not None else True
    prefer_web = bool(getattr(question_plan, "prefer_web", False)) if question_plan is not None else False

    din = False
    try:
        from ilim_assistant.ruzgar_kutuphane_gorev import din_alani_sorusu, is_kutuphane_bilgi_soru

        din = bool(din_alani_sorusu(raw))
        kutuphane = bool(is_kutuphane_bilgi_soru(raw) or (use_rag and primary in ("bilgi", "bilim", "dilbilgisi")))
    except Exception:
        kutuphane = bool(use_rag and primary in ("bilgi", "bilim", "dilbilgisi"))

    try:
        from ilim_assistant.ruzgar_k2_uslup import uslup_profili

        uslup = uslup_profili(raw, question_plan=question_plan, mode_norm=mode_norm)
    except Exception:
        uslup = "alim" if din else "sade_ogretmen"

    canli = primary == "hava" or prefer_web and primary not in ("bilgi", "bilim")
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import looks_like_live_web_needed

        if looks_like_live_web_needed(raw):
            canli = True
    except Exception:
        pass

    if mode_norm == "programlama" or primary == "islem":
        hedef = "programlama"
        niyet = "islem"
    elif primary == "hava" or canli and not din:
        hedef = "ana_motor"
        niyet = "canli"
    elif din or kutuphane or primary in ("bilgi", "bilim", "dilbilgisi"):
        hedef = "ana_motor"
        niyet = "bilgi"
    elif primary == "gundelik":
        hedef = "ana_motor"
        niyet = "sohbet"
    else:
        hedef = "ana_motor"
        niyet = primary or "diger"

    if butce_sn is None:
        butce_sn = 22.0 if din or niyet == "bilgi" else 15.0
    guven = 0.8 if (din or primary) else 0.55
    if not raw:
        niyet, guven = "emin_degil", 0.0

    return Karar(
        niyet=niyet,
        hedef_motor=hedef,
        canli=bool(canli and not din),
        kutuphane=bool(kutuphane or din),
        uslup=uslup,
        butce_sn=float(butce_sn),
        guven=float(guven),
    )


def attach_karar(
    orchestration_out: dict[str, Any] | None,
    message: str,
    *,
    mode_norm: str = "genel",
    question_plan: Any | None = None,
) -> Karar | None:
    if not o1_enabled():
        return None
    karar = karar_uret(message, mode_norm=mode_norm, question_plan=question_plan)
    if orchestration_out is not None:
        orchestration_out["karar"] = karar.as_dict()
        orchestration_out["o1"] = {"version": O1_VERSION, "niyet": karar.niyet}
    return karar
