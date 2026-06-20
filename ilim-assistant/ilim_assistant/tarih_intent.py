# Created by Ümit & Gökçenur
"""Tarih niyeti — chat_core/RAG importu olmadan hafif sınıflandırma."""

from __future__ import annotations

import os
import unicodedata


def _norm_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _looks_like_weather_not_tarih(msg: str) -> bool:
    low = (msg or "").lower()
    if not low:
        return False
    return any(
        n in low
        for n in (
            "hava nasil",
            "hava nasıl",
            "hava durumu",
            "kac derece",
            "kaç derece",
            "yagmur",
            "yağmur",
        )
    )


def tarih_intent(msg: str) -> bool:
    """
    Tarih / medeniyet sorulari — TARIH_VE_KULTUR yolu.
    Kapatmak: RUZGAR_TARIH_INTENT=0
    """
    if os.environ.get("RUZGAR_TARIH_INTENT", "1").strip().lower() in ("0", "false", "no"):
        return False
    raw = (msg or "").strip()
    if len(raw) < 6:
        return False
    if _looks_like_weather_not_tarih(raw):
        return False
    low = _norm_ascii(raw)
    low_tr = raw.lower()
    blob = low_tr + " " + low
    needles = (
        "lale devri",
        "gokturk",
        "göktürk",
        "osmanli",
        "osmanlı",
        "selcuklu",
        "selçuklu",
        "turk tarih kurumu",
        "türk tarih kurumu",
        " turk tarih",
        " turk tarih kurumu",
        "ottoman",
        "padisah",
        "padişah",
        "hanedan",
        " malazgirt",
        "manzikert",
        "kurtulus savasi",
        "kurtuluş savaşı",
        "bizans",
        "fatih sultan",
        "fethett",
        "fethi",
        "istanbul",
        "konstantinopolis",
        "4. murat",
        "dorduncu murat",
        "murat ",
        "kanuni sultan",
        "yavuz sultan",
        "orhun",
        "bilge kag",
        "bumin kag",
        "buyuk turk tarihi",
        "büyük türk tarihi",
        "mezopotamya",
        "anadolu selcuk",
        "anzak",
        "canakkale savas",
        "çanakkale savaş",
        "tanzimat",
        "ilk turk ",
        "ilk türk ",
        "gokturkler",
        "göktürkler",
        " osmanli imparator",
        " osmanlı imparator",
        "osman bey",
        "osman gazi",
        " osman bey",
        " saltanat",
        " cumhuriyet ilan",
        " cumhuriyet'in ilan",
    )
    if any(n in blob for n in needles):
        return True
    if any(x in blob for x in (" ttk ", " ttk,", " (ttk", "[ttk", "ttk ", "ttk'n")):
        return True
    if "tarih" in blob or "tarihi" in blob:
        hints = (
            "nedir",
            "kim",
            "ne zaman",
            "hangi",
            "nasil",
            "nasıl",
            "donem",
            "dönem",
            "devir",
            "olayi",
            "olayı",
            " savas",
            " savaş",
            " imparator",
            "beylik",
            "yonetimi",
            "yönetimi",
            "hanedan",
            "padişah",
            "padisah",
            "sultan",
        )
        if any(h in blob for h in hints):
            return True
    return False
