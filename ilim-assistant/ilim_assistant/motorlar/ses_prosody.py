# Created by Ümit & Gökçenur
"""
Faz S1 — doğal okuma prosody katmanı.

Metni konuşma parçalarına böler; parçalar arasına içerik türüne göre sessizlik süresi önerir.
Edge-TTS tek başına nefes/durak vermez; birleştirme `tts_service.synthesize_edge_mp3_prosody` ile yapılır.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum

from ilim_assistant.motorlar.ses_motoru import IcerikYolu

MAX_PARCA_CHARS = max(120, int(os.environ.get("RUZGAR_TTS_PROSODY_CHUNK", "420")))
MIN_PROSODY_CHARS = max(20, int(os.environ.get("RUZGAR_TTS_PROSODY_MIN", "70")))


class DurakTuru(str, Enum):
    yok = "yok"
    virgul = "virgul"
    orta = "orta"
    cumle = "cumle"
    paragraf = "paragraf"
    ayet = "ayet"
    vakif = "vakif"
    besmele = "besmele"
    sure_sonu = "sure_sonu"


@dataclass(frozen=True)
class KonusmaParcasi:
    metin: str
    sonraki_durak: DurakTuru


_AYET_SON = re.compile(
    r"(?:"
    r"[\uFD3E\uFD3F]|"
    r"۝|"
    r"﴿[^﴾]*﴾|"
    r"\(\d{1,3}\)\s*$"
    r")"
)
_CUMLE_SON = re.compile(r"[.!?…؟][\"»')\]]*\s*$")
_VIRGUL_SON = re.compile(r"[,،]\s*$")
_ORTA_SON = re.compile(r"[;:]\s*$")

_DURAK_TABAN_MS: dict[DurakTuru, int] = {
    DurakTuru.yok: 0,
    DurakTuru.virgul: 280,
    DurakTuru.orta: 420,
    DurakTuru.cumle: 650,
    DurakTuru.paragraf: 1100,
    DurakTuru.ayet: 1650,
    DurakTuru.vakif: 1950,
    DurakTuru.besmele: 1400,
    DurakTuru.sure_sonu: 2400,
}


def prosody_etkin(ayar: dict | None = None) -> bool:
    raw = os.environ.get("RUZGAR_TTS_PROSODY", "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if ayar is not None and ayar.get("prosody") is False:
        return False
    return True


def metin_normalize(metin: str) -> str:
    t = (metin or "").replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def prosody_gerekli(metin: str, icerik: IcerikYolu | None = None) -> bool:
    """Genel sohbet kısa yanıtları tek parça Edge-TTS (Gemini gibi akıcı); özel içerikte durak."""
    t = metin_normalize(metin)
    if len(t) < MIN_PROSODY_CHARS:
        return False
    if icerik is not None and icerik != IcerikYolu.genel:
        return True
    if "\n\n" in t:
        return True
    if len(t) > max(900, MAX_PARCA_CHARS * 2):
        return True
    return False


def _sonraki_durak(
    parca: str,
    *,
    paragraf_sonu: bool,
    icerik: IcerikYolu,
) -> DurakTuru:
    if paragraf_sonu:
        return DurakTuru.paragraf
    s = parca.rstrip()
    if icerik == IcerikYolu.kuran and _AYET_SON.search(s):
        return DurakTuru.ayet
    if _VIRGUL_SON.search(s):
        return DurakTuru.virgul
    if _ORTA_SON.search(s):
        return DurakTuru.orta
    if _CUMLE_SON.search(s):
        return DurakTuru.cumle
    return DurakTuru.cumle


def _cumlelere_bol(paragraf: str) -> list[str]:
    parca = paragraf.strip()
    if not parca:
        return []
    raw = re.split(r"(?<=[.!?…؟])\s+", parca)
    out: list[str] = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        if len(s) <= MAX_PARCA_CHARS:
            out.append(s)
            continue
        for alt in _virgul_ile_bol(s):
            if alt.strip():
                out.append(alt.strip())
    return out


def _virgul_ile_bol(cumle: str) -> list[str]:
    if len(cumle) <= MAX_PARCA_CHARS:
        return [cumle]
    parcalar = re.split(r"([,،]\s+)", cumle)
    birlesik: list[str] = []
    buf = ""
    for i, p in enumerate(parcalar):
        if i % 2 == 1 and p:
            buf += p
            continue
        aday = (buf + p).strip()
        buf = ""
        if not aday:
            continue
        if len(aday) <= MAX_PARCA_CHARS:
            birlesik.append(aday)
        else:
            kelimeler = aday.split()
            satir: list[str] = []
            uz = 0
            for k in kelimeler:
                ek = len(k) + (1 if satir else 0)
                if satir and uz + ek > MAX_PARCA_CHARS:
                    birlesik.append(" ".join(satir))
                    satir = [k]
                    uz = len(k)
                else:
                    satir.append(k)
                    uz += ek
            if satir:
                birlesik.append(" ".join(satir))
    return birlesik or [cumle[:MAX_PARCA_CHARS]]


def metin_parcala(metin: str, icerik: IcerikYolu) -> list[KonusmaParcasi]:
    """Konuşma parçaları; son parçanın sonraki_durak değeri yok."""
    norm = metin_normalize(metin)
    if not norm:
        return []

    paragraflar = [p.strip() for p in norm.split("\n\n") if p.strip()]
    if not paragraflar:
        paragraflar = [norm]

    cumleler: list[tuple[str, bool]] = []
    for pi, par in enumerate(paragraflar):
        for c in _cumlelere_bol(par):
            cumleler.append((c, pi < len(paragraflar) - 1))

    if not cumleler:
        return [KonusmaParcasi(metin=norm, sonraki_durak=DurakTuru.yok)]

    sonuc: list[KonusmaParcasi] = []
    for i, (cumle, paragraf_sonu) in enumerate(cumleler):
        if i == len(cumleler) - 1:
            sonuc.append(KonusmaParcasi(metin=cumle, sonraki_durak=DurakTuru.yok))
            continue
        if paragraf_sonu:
            durak = DurakTuru.paragraf
        else:
            durak = _sonraki_durak(cumle, paragraf_sonu=False, icerik=icerik)
        sonuc.append(KonusmaParcasi(metin=cumle, sonraki_durak=durak))
    return sonuc


def durak_suresi_ms(
    tur: DurakTuru,
    *,
    icerik: IcerikYolu,
    durak_carpani: float = 1.0,
    huzur_carpani: float = 0.88,
    tilavet: bool = False,
) -> int:
    if tur == DurakTuru.yok:
        return 0
    ms = float(_DURAK_TABAN_MS.get(tur, 650))
    if icerik == IcerikYolu.kuran:
        ms *= 1.35 if tur in (DurakTuru.cumle, DurakTuru.ayet, DurakTuru.vakif) else 1.12
    elif icerik == IcerikYolu.tasavvuf_hadis:
        ms *= 1.15
    elif icerik == IcerikYolu.klasik_edebiyat and tur == DurakTuru.cumle:
        ms *= 1.08
    if tilavet:
        ms *= 1.22
    huzur = max(0.45, min(1.0, float(huzur_carpani)))
    durak = max(0.55, min(1.6, float(durak_carpani)))
    huzur_factor = 1.0 + (1.0 - huzur) * 0.85
    return max(0, int(ms * durak * huzur_factor))


def prosody_ozet(parcalar: list[KonusmaParcasi]) -> dict[str, int | bool]:
    duraklar = [p.sonraki_durak for p in parcalar if p.sonraki_durak != DurakTuru.yok]
    return {
        "parcalar": len(parcalar),
        "durak_sayisi": len(duraklar),
        "cok_parca": len(parcalar) > 1,
    }
