# Created by Ümit & Gökçenur
"""
Faz S5 — Tilavet / kutsal okuma hattı.

Arapça ayet ayrımı, vakıf/sûre durakları, Edge Arapça ses veya Alim profili.
Tecvid bilgisi: knowledge/tecvid/kurallar_ornek.md
"""

from __future__ import annotations

import os
import re
from enum import Enum
from pathlib import Path

from ilim_assistant.motorlar.ses_motoru import (
    IcerikYolu,
    SesKarakteri,
    analiz_icerik_yolu,
    edge_pitch_string,
    edge_rate_yuzdesi,
    normalize_ses_karakteri,
)
from ilim_assistant.motorlar.ses_prosody import (
    DurakTuru,
    KonusmaParcasi,
    durak_suresi_ms,
    metin_normalize,
)

TILAVET_VERSION = "ses-tilavet-s5-2026-06-06"
_TECVID_MD = (
    Path(__file__).resolve().parents[2] / "knowledge" / "tecvid" / "kurallar_ornek.md"
)

_ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)
_BESMELE_RE = re.compile(
    r"ب\s*س\s*م\s*ال\s*ل\s*ه|"
    r"bismillah|"
    r"bismillahirrahmanirrahim",
    re.I,
)
_SURE_BAS = re.compile(
    r"^(?:s[üu]re\s*[-:]?\s*\d+|"
    r"el-fatiha|fatiha|yasin|yaseen|"
    r"البقرة|الفاتحة|يس)\b",
    re.I | re.M,
)
_AYET_AYRAC = re.compile(
    r"(?:"
    r"۝|"
    r"[\uFD3E\uFD3F]\s*\d{1,3}\s*[\uFD3E\uFD3F]?|"
    r"﴿\s*\d{1,3}\s*﴾|"
    r"\(\s*\d{1,3}\s*\)"
    r")"
)
_EDGE_AR = os.environ.get("RUZGAR_TTS_AR_VOICE", "ar-SA-HamedNeural")
_EDGE_TR_ALIM = os.environ.get("RUZGAR_TTS_TR_ALIM_VOICE", "tr-TR-AhmetNeural")


class TilavetMod(str, Enum):
    kuran_ar = "kuran_ar"
    kuran_meal = "kuran_meal"
    hadis_risale = "hadis_risale"
    genel_vakur = "genel_vakur"


def tilavet_etkin(ayar: dict | None = None) -> bool:
    raw = os.environ.get("RUZGAR_TTS_TILAVET", "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if ayar is not None and ayar.get("tilavet") is False:
        return False
    return True


def arabice_oran(metin: str) -> float:
    s = metin or ""
    if not s.strip():
        return 0.0
    ar = len(_ARABIC_RE.findall(s))
    return ar / max(1, len(s.replace(" ", "")))


def tespit_tilavet_modu(metin: str) -> TilavetMod:
    yol = analiz_icerik_yolu(metin)
    oran = arabice_oran(metin)
    if oran >= 0.35:
        return TilavetMod.kuran_ar
    if yol == IcerikYolu.kuran:
        return TilavetMod.kuran_meal
    if yol == IcerikYolu.tasavvuf_hadis:
        return TilavetMod.hadis_risale
    return TilavetMod.genel_vakur


def edge_ses_tilavet(
    metin: str,
    *,
    karakter: str | SesKarakteri = SesKarakteri.alim,
    mod: TilavetMod | None = None,
) -> str:
    kar = normalize_ses_karakteri(
        karakter.value if isinstance(karakter, SesKarakteri) else karakter
    )
    m = mod or tespit_tilavet_modu(metin)
    if m == TilavetMod.kuran_ar:
        return _EDGE_AR
    if kar == SesKarakteri.edip:
        return "tr-TR-EmelNeural"
    return _EDGE_TR_ALIM


def tilavet_rate_pitch(
    metin: str,
    *,
    karakter: str = "alim",
    hiz_carpani: float = 0.88,
    huzur_carpani: float = 0.82,
) -> tuple[str, str]:
    """Tilavet icin ekstra yavas rate ve dusuk pitch."""
    kar = normalize_ses_karakteri(karakter)
    mod = tespit_tilavet_modu(metin)
    yol = IcerikYolu.kuran if mod in (TilavetMod.kuran_ar, TilavetMod.kuran_meal) else IcerikYolu.tasavvuf_hadis
    if mod == TilavetMod.genel_vakur:
        yol = analiz_icerik_yolu(metin)
    rate = edge_rate_yuzdesi(
        karakter=kar,
        icerik=yol,
        hiz_carpani=min(hiz_carpani, 0.9),
        huzur_carpani=min(huzur_carpani, 0.85),
    )
    # Tilavet ekstra yavaslik
    try:
        pct = float(rate.rstrip("%"))
        pct -= 6.0 if mod == TilavetMod.kuran_ar else 4.0
        pct = max(-48.0, pct)
        rate = f"{pct:.0f}%"
    except ValueError:
        pass
    pitch = edge_pitch_string(kar, yol)
    if mod == TilavetMod.kuran_ar:
        pitch = "-2Hz"
    return rate, pitch


def _ayet_satirlarina_bol(metin: str) -> list[str]:
    t = metin_normalize(metin)
    t = _AYET_AYRAC.sub("\n\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    bloklar = [b.strip() for b in t.split("\n\n") if b.strip()]
    if len(bloklar) > 1:
        return bloklar
    if arabice_oran(t) >= 0.35:
        kelimeler = t.split()
        if len(kelimeler) <= 6:
            return [t]
        satir: list[str] = []
        buf: list[str] = []
        for k in kelimeler:
            buf.append(k)
            if len(buf) >= 5:
                satir.append(" ".join(buf))
                buf = []
        if buf:
            satir.append(" ".join(buf))
        return satir or [t]
    return [t]


def _sonraki_tilavet_durak(
    parca: str,
    *,
    paragraf_sonu: bool,
    mod: TilavetMod,
    besmele_sonu: bool = False,
) -> DurakTuru:
    if besmele_sonu:
        return DurakTuru.besmele
    if paragraf_sonu:
        if _SURE_BAS.search(parca):
            return DurakTuru.sure_sonu
        return DurakTuru.paragraf
    s = parca.rstrip()
    if _AYET_AYRAC.search(s) or re.search(r"[\uFD3E\uFD3F]|۝|﴿", s):
        return DurakTuru.ayet
    if mod in (TilavetMod.kuran_ar, TilavetMod.kuran_meal):
        if re.search(r"[.!?…؟]\s*$", s):
            return DurakTuru.vakif
    if re.search(r"[,،]\s*$", s):
        return DurakTuru.virgul
    if re.search(r"[.!?…؟]\s*$", s):
        return DurakTuru.cumle
    return DurakTuru.vakif if mod == TilavetMod.kuran_ar else DurakTuru.cumle


def tilavet_parcala(metin: str, mod: TilavetMod | None = None) -> list[KonusmaParcasi]:
    """Tilavet modu icin konuşma parcalari (uzun duraklar)."""
    m = mod or tespit_tilavet_modu(metin)
    norm = metin_normalize(metin)
    if not norm:
        return []

    paragraflar = [p.strip() for p in norm.split("\n\n") if p.strip()] or [norm]
    birimler: list[tuple[str, bool]] = []
    for pi, par in enumerate(paragraflar):
        for satir in _ayet_satirlarina_bol(par):
            birimler.append((satir, pi < len(paragraflar) - 1))

    sonuc: list[KonusmaParcasi] = []
    for i, (parca, paragraf_sonu) in enumerate(birimler):
        besmele_sonu = bool(i == 0 and _BESMELE_RE.search(parca) and len(birimler) > 1)
        if i == len(birimler) - 1:
            sonuc.append(KonusmaParcasi(metin=parca, sonraki_durak=DurakTuru.yok))
            continue
        if besmele_sonu:
            durak = DurakTuru.besmele
        elif paragraf_sonu:
            durak = _sonraki_tilavet_durak(parca, paragraf_sonu=True, mod=m)
        else:
            durak = _sonraki_tilavet_durak(parca, paragraf_sonu=False, mod=m)
        sonuc.append(KonusmaParcasi(metin=parca, sonraki_durak=durak))
    return sonuc


def tilavet_durak_ms(
    tur: DurakTuru,
    *,
    mod: TilavetMod,
    durak_carpani: float = 1.0,
    huzur_carpani: float = 0.82,
) -> int:
    yol = IcerikYolu.kuran if mod in (TilavetMod.kuran_ar, TilavetMod.kuran_meal) else IcerikYolu.tasavvuf_hadis
    ms = durak_suresi_ms(
        tur,
        icerik=yol,
        durak_carpani=durak_carpani,
        huzur_carpani=huzur_carpani,
        tilavet=True,
    )
    if mod == TilavetMod.kuran_ar and tur in (DurakTuru.ayet, DurakTuru.vakif, DurakTuru.sure_sonu):
        ms = int(ms * 1.15)
    return ms


def tilavet_ozet(metin: str) -> dict[str, str | float | int]:
    mod = tespit_tilavet_modu(metin)
    parcalar = tilavet_parcala(metin, mod)
    return {
        "mod": mod.value,
        "arabice_oran": round(arabice_oran(metin), 3),
        "edge_voice": edge_ses_tilavet(metin, mod=mod),
        "parcalar": len(parcalar),
        "tecvid_dosya": str(_TECVID_MD.name) if _TECVID_MD.is_file() else "",
        "version": TILAVET_VERSION,
    }
