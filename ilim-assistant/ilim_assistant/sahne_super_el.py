# -*- coding: utf-8 -*-
"""
Sahne süper-el iskeleti (plan sıra 21).
Söz → niyet → sahne eylemi. Ağır organ sürücüleri sonra bağlanır.
Boot sırasına / yüz kilidine dokunmaz.
"""
from __future__ import annotations

import re
from typing import Any

# Sekiz fiil (plan)
FILLER = (
    "goster",
    "odakla",
    "karsilastir",
    "zaman_kaydir",
    "pin",
    "degistir",
    "disari_ver",
    "temizle",
)

ORGANLAR = (
    "harita",
    "cam",
    "uzay",
    "belge",
    "tablo",
    "sunum",
    "cizim",
    "foto",
    "video",
    "ses",
    "eser",
    "yuz",  # varsayılan Rüzgar yüzü
)

_TR = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "c",
        "Ğ": "g",
        "İ": "i",
        "Ö": "o",
        "Ş": "s",
        "Ü": "u",
    }
)


def _norm(s: str) -> str:
    t = (s or "").strip().lower().translate(_TR)
    t = re.sub(r"\s+", " ", t)
    return t


def resolve_super_el(text: str) -> dict[str, Any]:
    """
    Doğal cümleden süper-el niyeti.
    Dönen: {ok, fiil, organ, hedef, guven, not}
    """
    raw = (text or "").strip()
    n = _norm(raw)
    if not n or len(n) < 2:
        return {
            "ok": False,
            "fiil": None,
            "organ": None,
            "hedef": None,
            "guven": 0.0,
            "not": "bos",
        }

    fiil = None
    guven = 0.55

    if re.search(r"\b(temizle|kapat|kaldir|sil sahne)\b", n):
        fiil = "temizle"
        guven = 0.85
    elif re.search(r"\b(pin|sabitle|hatirla|pinle)\b", n):
        fiil = "pin"
        guven = 0.8
    elif re.search(r"\b(disari|export|indir|kaydet|pdf ver)\b", n):
        fiil = "disari_ver"
        guven = 0.75
    elif re.search(r"\b(karsilastir|yan yana|vs\.?|versus)\b", n):
        fiil = "karsilastir"
        guven = 0.8
    elif re.search(r"(odak|yaklas|zoom)", n) and re.search(
        r"(harita|earth|dunya|cograf)", n
    ):
        fiil = "odakla"
        guven = 0.82
    elif re.search(r"(turkiye|turkey).*(odak|goster|ac)|(odak|goster|ac).*(turkiye|turkey)", n) and re.search(
        r"(harita|earth|dunya|cograf)", n
    ):
        fiil = "odakla"
        guven = 0.8
    elif re.search(r"\b(zaman|faz|4d|timeline|yil)\b", n) and re.search(
        r"\b(kaydir|goster|ac)\b", n
    ):
        fiil = "zaman_kaydir"
        guven = 0.7
    elif re.search(r"\b(degistir|degis|yerine koy|guncelle)\b", n):
        fiil = "degistir"
        guven = 0.65
    elif re.search(r"\b(goster|ac|sahneye koy|yansit|getir)\b", n):
        fiil = "goster"
        guven = 0.78

    organ = "yuz"
    if re.search(r"(harita|earth|cograf|atlas|osm|maplibre)", n):
        organ = "harita"
    elif re.search(r"(kamera|\bcam\b|rtsp|yayin|iss|\btv\b)", n):
        organ = "cam"
    elif re.search(r"(uzay|nasa|hubble|astro|gezegen|teleskop)", n):
        organ = "uzay"
    elif re.search(r"(belge|pdf|metin|\byaz\b)", n):
        organ = "belge"
    elif re.search(r"(tablo|excel|metraj)", n):
        organ = "tablo"
    elif re.search(r"(sunum|slayt)", n):
        organ = "sunum"
    elif re.search(r"(cizim|kroki|\bplan\b)", n):
        organ = "cizim"
    elif re.search(r"(foto|resim|goruntu)", n):
        organ = "foto"
    elif re.search(r"(video|klip|montaj)", n):
        organ = "video"
    elif re.search(r"(\bses\b|muzik|dalga)", n):
        organ = "ses"
    elif re.search(r"(eser|kitap|ayet|hadis|pasaj|tefsir|meal)", n):
        organ = "eser"

    if fiil is None and organ != "yuz":
        fiil = "goster"
        guven = min(guven, 0.6)

    hedef = None
    m = re.search(
        r"(?:odaklan|goster|ac)\s+([a-z0-9\s\-]{2,40})$",
        n,
    )
    if m:
        hedef = m.group(1).strip()
    elif "turkiye" in n or "turkey" in n:
        hedef = "turkiye"

    ok = fiil is not None
    return {
        "ok": ok,
        "fiil": fiil,
        "organ": organ if ok else None,
        "hedef": hedef,
        "guven": round(guven if ok else 0.0, 2),
        "not": "super_el_v1",
        "fiiller": list(FILLER),
        "organlar": list(ORGANLAR),
    }


def smoke_super_el() -> list[str]:
    fails: list[str] = []
    cases = [
        ("haritayi ac turkiyeye odaklan", "odakla", "harita"),
        ("iss yayinini goster", "goster", "cam"),
        ("nasa uzaydan bak", "goster", "uzay"),
        ("sahneyi temizle", "temizle", None),
        ("bunu pinle", "pin", None),
        ("iki tefsiri karsilastir", "karsilastir", "eser"),
    ]
    for text, fiil, organ in cases:
        r = resolve_super_el(text)
        if not r.get("ok"):
            fails.append(f"ok yok: {text}")
            continue
        if r.get("fiil") != fiil:
            fails.append(f"fiil {text}: {r.get('fiil')} != {fiil}")
        if organ and r.get("organ") != organ:
            fails.append(f"organ {text}: {r.get('organ')} != {organ}")
    return fails
