# Created by Ümit & Gökçenur
"""Ana Motor Faz F3 — TDK + tarih + nebula öncelik matrisi."""

from __future__ import annotations

import os
import re
from typing import Any


def matrix_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_KAYNAK_MATRIS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


_TARIH_CUES = (
    "osmanlı",
    "osmanli",
    "padişah",
    "padisah",
    "sultan",
    "devlet",
    "cihan",
    "fatih",
    "yavuz",
    "kanuni",
    "cumhuriyet",
    "savaş",
    "savas",
    "antlaşma",
    "antlasma",
    "medeniyet",
    "hanedan",
    "imparator",
    "bizans",
    "selçuk",
    "selcuk",
    "tarih",
    "yüzyıl",
    "yuzyil",
    "mö",
    "ms ",
)

_DIL_CUES = (
    "anlam",
    "anlamı",
    "anlami",
    "köken",
    "koken",
    "yazım",
    "yazim",
    "imla",
    "eş anlam",
    "es anlam",
    "zıt",
    "zit",
    "tanım",
    "tanim",
    "kelime",
    "sözcük",
    "sozcuk",
    "tdk",
    "dilbilgisi",
    "fiil",
    "isim",
    "sıfat",
    "sifat",
    "zarf",
    "ek ",
    "yapım",
    "yapim",
)

_NEBULA_CUES = (
    "nebula",
    "ansiklopedi",
    "külliyat",
    "kulliyat",
    "mektubat",
    "kaynak paket",
    "kitap hafıza",
    "kitap hafiza",
)


def classify_retrieval_profile(query: str, primary: str = "") -> str:
    """
    Profil: tdk | tarih | nebula | arsiv | genel
    """
    low = (query or "").strip().lower()
    p = (primary or "").strip().lower()
    if p == "dilbilgisi":
        return "tdk"
    if p == "bilim" or any(c in low for c in ("hadis", "kuran", "ayet", "fıkıh", "fikih")):
        return "arsiv"
    if any(c in low for c in _DIL_CUES) and "?" in low:
        return "tdk"
    if any(c in low for c in _TARIH_CUES):
        return "tarih"
    if any(c in low for c in _NEBULA_CUES):
        return "nebula"
    if re.search(r"\b(kimdir|kimlerdir|nedir|ne zaman|hangi)\b", low):
        if any(c in low for c in _TARIH_CUES):
            return "tarih"
        return "genel"
    return "genel"


def _profile_top_k(profile: str, k_ar: int, k_ix: int) -> dict[str, int]:
    base = {
        "arsiv": k_ar,
        "indeks": k_ix,
        "tarih": max(2, k_ix),
        "tdk": max(2, k_ix),
        "nebula": max(2, k_ix),
    }
    if profile == "tdk":
        base["tdk"] = max(4, k_ix + 2)
        base["indeks"] = max(1, k_ix - 1)
        base["arsiv"] = max(1, k_ar - 1)
    elif profile == "tarih":
        base["tarih"] = max(4, k_ix + 2)
        base["nebula"] = max(2, k_ix)
        base["arsiv"] = k_ar
    elif profile == "nebula":
        base["nebula"] = max(4, k_ix + 2)
        base["tarih"] = max(2, k_ix)
    elif profile == "arsiv":
        base["arsiv"] = max(4, k_ar + 2)
        base["indeks"] = max(1, k_ix)
    else:
        base["tarih"] = max(2, k_ix)
        base["tdk"] = max(2, k_ix)
        base["nebula"] = max(2, k_ix)
    return base


def retrieve_encyclopedic_matrix(
    msg: str,
    *,
    primary: str = "",
    k_ar: int = 2,
    k_ix: int = 3,
) -> tuple[list[tuple[str, str, float]], str]:
    """
    Matris ile birleşik retrieval.
    Dönüş: (hits, profile)
    """
    from ilim_assistant.main_engine import _merge_hits_dedupe
    from ilim_assistant.rag_store import (
        search as rag_search,
        search_arsiv,
        search_nebula_hafiza,
        search_tarih_hafiza,
        search_tdk_hafiza,
    )

    profile = classify_retrieval_profile(msg, primary)
    caps = _profile_top_k(profile, k_ar, k_ix)

    ar_hits: list[tuple[str, str, float]] = []
    ix_hits: list[tuple[str, str, float]] = []
    tarih_hits: list[tuple[str, str, float]] = []
    tdk_hits: list[tuple[str, str, float]] = []
    nebula_hits: list[tuple[str, str, float]] = []

    try:
        if caps["arsiv"] > 0:
            ar_hits = search_arsiv(msg, top_k=caps["arsiv"])
    except Exception:
        pass
    try:
        if caps["indeks"] > 0:
            ix_hits = rag_search(msg, top_k=caps["indeks"])
    except Exception:
        pass
    try:
        if caps["tarih"] > 0:
            tarih_hits = search_tarih_hafiza(msg, top_k=caps["tarih"])
    except Exception:
        pass
    try:
        if caps["tdk"] > 0:
            tdk_hits = search_tdk_hafiza(msg, top_k=caps["tdk"])
    except Exception:
        pass
    try:
        if caps["nebula"] > 0:
            nebula_hits = search_nebula_hafiza(msg, top_k=caps["nebula"])
    except Exception:
        pass

    if profile == "tdk":
        order = (tdk_hits, ix_hits, tarih_hits, nebula_hits, ar_hits)
    elif profile == "tarih":
        order = (tarih_hits, nebula_hits, ar_hits, ix_hits, tdk_hits)
    elif profile == "nebula":
        order = (nebula_hits, tarih_hits, ar_hits, ix_hits, tdk_hits)
    elif profile == "arsiv":
        order = (ar_hits, ix_hits, tarih_hits, nebula_hits, tdk_hits)
    else:
        order = (ar_hits, ix_hits, tarih_hits, nebula_hits, tdk_hits)

    hits = _merge_hits_dedupe(*order)
    cap = max(k_ar + k_ix + 1, 5)
    return hits[:cap], profile
