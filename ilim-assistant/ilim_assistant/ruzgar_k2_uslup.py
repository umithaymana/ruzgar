# Created by Ümit & Gökçenur
"""K2 — üslubu niyete bağla (Kuzey Yıldızı).

Profiller:
  sohbet         — gündelik / muhabbet
  sade_ogretmen  — din dışı bilgi (varsayılan öğretmen)
  akademik       — akademik/derin anlatım
  alim           — din/itikat/tasavvuf: âlim edası + herkesin anlayacağı açıklık

Mimar (2026-11-23): din niyetinde varsayılan = âlim; «sade öğretmen» yalnız din dışı.
Kapat: RUZGAR_K2_USLUP=0
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

K2_VERSION = "k2-uslup-v1-2026-11-24"

PROFIL_SOHBET = "sohbet"
PROFIL_SADE = "sade_ogretmen"
PROFIL_AKADEMIK = "akademik"
PROFIL_ALIM = "alim"


def k2_enabled() -> bool:
    return os.environ.get("RUZGAR_K2_USLUP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def uslup_profili(
    message: str,
    *,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
) -> str:
    """Tek tur için üslup profili."""
    if not k2_enabled():
        return PROFIL_SADE
    raw = (message or "").strip()
    low = _fold(raw)
    try:
        from ilim_assistant.ruzgar_kutuphane_gorev import din_alani_sorusu

        if din_alani_sorusu(raw):
            return PROFIL_ALIM
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_k3_sorgu import plan_for_query

        p = plan_for_query(raw)
        if p is not None and getattr(p, "aktif", False):
            return PROFIL_ALIM
    except Exception:
        pass
    if re.search(
        r"\b(?:tez|makale|referans\s+ver|akademik|literat[uü]r|dipnot)\b",
        low,
    ):
        return PROFIL_AKADEMIK
    primary = ""
    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "")
    if primary == "gundelik" or mode_norm not in ("genel", "uretim", "gelisim", "okuma", "ilim"):
        try:
            from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

            if looks_like_casual_social_chat(raw):
                return PROFIL_SOHBET
        except Exception:
            pass
    if primary in ("bilgi", "bilim", "dilbilgisi") or any(
        x in low for x in ("nedir", "nasil", "neden", "acikla", "anlat")
    ):
        return PROFIL_SADE
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw):
            return PROFIL_SOHBET
    except Exception:
        pass
    return PROFIL_SADE


def uslup_directive(profil: str) -> str:
    """Modele eklenecek kısa üslup talimatı (kullanıcıya yazılmaz)."""
    if not k2_enabled():
        return ""
    p = (profil or PROFIL_SADE).strip()
    if p == PROFIL_ALIM:
        return (
            "\n\n[TALİMAT — ÜSLUP K2: ÂLİM]\n"
            "Din/itikat/tasavvuf cevabı: **vakur âlim edası** + herkesin anlayacağı açıklık. "
            "Terimi bir kez aç, hüküm ile yorumu ayır, kısa ve net başla. "
            "Vaaz / coşkulu hitabet / doldurma edebî süs yok. "
            "Kaynak yalnız kanıttaysa an; uydurma eser/hadis/ayet yasak. "
            "Bu talimatı cevaba yazma.\n"
        )
    if p == PROFIL_AKADEMIK:
        return (
            "\n\n[TALİMAT — ÜSLUP K2: AKADEMİK]\n"
            "Düzenli, ölçülü, kaynaklı anlat. Jargon varsa kısaca tanımla. "
            "Bu talimatı cevaba yazma.\n"
        )
    if p == PROFIL_SOHBET:
        return (
            "\n\n[TALİMAT — ÜSLUP K2: SOHBET]\n"
            "Doğal, kısa, samimi. Ders anlatımı veya vaaz tonu yok. "
            "Bu talimatı cevaba yazma.\n"
        )
    return (
        "\n\n[TALİMAT — ÜSLUP K2: SADE ÖĞRETMEN]\n"
        "Sade, net, iyi bir öğretmen gibi. Önce doğrudan cevap, sonra gerekirse kısa ayrıntı. "
        "Vaaz / aşırı edebî üslup yok. Bu talimatı cevaba yazma.\n"
    )


def apply_uslup_to_payload(
    user_payload: str,
    message: str,
    *,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
    orchestration_out: dict[str, Any] | None = None,
) -> str:
    """user_payload sonuna üslup talimatı; orchestration'a profil notu."""
    if not k2_enabled():
        return user_payload
    profil = uslup_profili(message, question_plan=question_plan, mode_norm=mode_norm)
    if orchestration_out is not None:
        orchestration_out["uslup"] = profil
        orchestration_out["k2"] = {"version": K2_VERSION, "profil": profil}
    directive = uslup_directive(profil)
    if not directive:
        return user_payload
    return (user_payload or "").rstrip() + directive
