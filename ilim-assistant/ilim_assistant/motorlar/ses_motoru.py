# Created by Ümit & Gökçenur
"""
RÜZGAR Ses Motoru — nihai karakter profilleri ve Edge-TTS uyumu.

Profiller:
  • Alim — Kur'an ve Hadis: yavaş, vakur, tane tane, derin (tilavet/hadis hattı).
  • Edip — edebiyat ve gazeller: lirik, duygusal, yumuşak.
  • Asistan — günlük sohbet: net, yardımcı, nazik.

Arka uç: edge-tts. Metadata: Ümit & Gökçenur imzası (tts_service + ID3).
Paralel TTS: desktop_server RUZGAR_TTS_MP + ruzgar_perf hattı.

Masaüstü oynatıcı tamponu (CPU yükünde yankıyı azaltmak): ruzgar-desktop/app.js —
``RUZGAR_TTS_PLAY_PREROLL_MS``, ``RUZGAR_TTS_CHUNK_GAP_MS``.

Faz S1 prosody (doğal durak): ``motorlar/ses_prosody.py`` + ``tts_service.synthesize_edge_mp3_prosody``.
Faz S4 klon (XTTS): ``motorlar/ses_klon_motoru.py`` + ``/api/tts/clone`` — referans ``arsiv/ses-referans/``.
Faz S5 tilavet: ``motorlar/ses_tilavet.py`` + ``/api/tts/tilavet`` — ayet/vakif durak, Arapca Edge ses.
Uzun metinlerde cümle/paragraf arası sessizlik; Kur'an/hadis hattında daha uzun durak.
Kapat: ``RUZGAR_TTS_PROSODY=0`` veya ``.ruzgar_ses_ayarlari.json`` → ``"prosody": false``.

İlim ve İdrak (Aktif Okuyucu): uzun metin özeti talimatı chat_core → ilim_ve_idrak ile gelir.
"""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any

from ilim_assistant.ruzgar_perf import RUZGAR_PERF_MIMAR

MIMAR_IMZA = RUZGAR_PERF_MIMAR
PROJE_ADI = "RÜZGAR"

_PROFILE_ALIM = (
    "[Alim] Kur'an ve Hadis hattında ses: yavaş, vakur, tane tane ve derin; "
    "her kelimede duruş payı; acele yok; hürmet ve sükûnet önde."
)
_PROFILE_EDIP = (
    "[Edip] Edebiyat ve gazel okumasında: lirik, duygusal, yumuşak; "
    "sesin müzikliliği ve imgelerin tadı öne çıksın."
)
_PROFILE_ASISTAN = (
    "[Asistan] Günlük sohbet: net, yardımcı, nazik; doğal tempo; gereksiz ağırlık yok."
)


class SesKarakteri(str, Enum):
    """Rüzgar ses profili — menü ve .ruzgar_ses_ayarlari.json ile seçilir."""

    alim = "alim"
    edip = "edip"
    asistan = "asistan"


# Eski kayıtlar (bilge/sair/kari) normalize_ses_karakteri ile taşınır.
_ESKI_PROFILLER = {
    "bilge": SesKarakteri.alim,
    "sair": SesKarakteri.edip,
    "kari": SesKarakteri.alim,
}


def normalize_ses_karakteri(raw: str | None) -> SesKarakteri:
    """Menü/API metnini enum'a çevirir; bilinmeyen → asistan."""
    s = (raw or "").strip().lower()
    if s in _ESKI_PROFILLER:
        return _ESKI_PROFILLER[s]
    try:
        return SesKarakteri(s)
    except ValueError:
        return SesKarakteri.asistan


class IcerikYolu(str, Enum):
    tasavvuf_hadis = "tasavvuf_hadis"
    klasik_edebiyat = "klasik_edebiyat"
    kuran = "kuran"
    genel = "genel"


def profil_aciklamasi(k: SesKarakteri) -> str:
    if k == SesKarakteri.alim:
        return _PROFILE_ALIM
    if k == SesKarakteri.edip:
        return _PROFILE_EDIP
    return _PROFILE_ASISTAN


# Edge-TTS: Türkçe neural (profil bazlı ses seçimi)
EDGE_VOICES = {
    SesKarakteri.alim: "tr-TR-AhmetNeural",
    SesKarakteri.edip: "tr-TR-EmelNeural",
    SesKarakteri.asistan: "tr-TR-EmelNeural",
}

_KURAN_IO = re.compile(
    r"kur[\'’]?an|k\.i\.k|tilavet|tecvid|kiraat|ayet|sure\s|s[üu]re\s|mushaf|c[uü]z",
    re.I,
)
_KLASIK_IO = re.compile(
    r"gazel|beyit|divan|mesnevi|aruz|redif|kafiye|kaside|nezim|şiir|siir|rubai",
    re.I,
)
_HADIS_TAS_IO = re.compile(
    r"hadis|mektubat|tasavvuf|risale|sahih|buhari|muslim|rivayet|ravi|isnad|zikr|tarikat|marifet",
    re.I,
)


def analiz_icerik_yolu(metin: str) -> IcerikYolu:
    s = (metin or "").strip()
    if not s:
        return IcerikYolu.genel
    low = s.lower()
    if _KURAN_IO.search(low):
        return IcerikYolu.kuran
    if _KLASIK_IO.search(low) and not _KURAN_IO.search(low):
        return IcerikYolu.klasik_edebiyat
    if _HADIS_TAS_IO.search(low):
        return IcerikYolu.tasavvuf_hadis
    return IcerikYolu.genel


def ton_metni_icerik(yol: IcerikYolu) -> str:
    if yol == IcerikYolu.kuran:
        return (
            "[Tecvid / tilavet çizgisi] Med ve duraklar için zaman genişletme; vakıf yerlerinde nefes; "
            "Diyanet/hoca tilavet üslubuna yaklaşan yavaş taban tempo (simülasyon, öğretmenlik değil)."
        )
    if yol == IcerikYolu.klasik_edebiyat:
        return _PROFILE_EDIP
    if yol == IcerikYolu.tasavvuf_hadis:
        return _PROFILE_ALIM
    return _PROFILE_ASISTAN


def varsayilan_karakter_icerige(yol: IcerikYolu) -> SesKarakteri:
    """İçerik türüne göre önerilen profil (menü seçimi yoksa ipucu)."""
    if yol == IcerikYolu.klasik_edebiyat:
        return SesKarakteri.edip
    if yol in (IcerikYolu.kuran, IcerikYolu.tasavvuf_hadis):
        return SesKarakteri.alim
    return SesKarakteri.asistan


def edge_rate_yuzdesi(
    *,
    karakter: SesKarakteri,
    icerik: IcerikYolu,
    hiz_carpani: float = 0.92,
    huzur_carpani: float = 0.88,
) -> str:
    hiz_carpani = max(0.55, min(1.0, float(hiz_carpani)))
    huzur_carpani = max(0.55, min(1.0, float(huzur_carpani)))
    base = -5.0
    if karakter == SesKarakteri.alim:
        base -= 14.0
    elif karakter == SesKarakteri.edip:
        base -= 8.0
    else:
        base -= 2.0
    if icerik == IcerikYolu.kuran:
        base -= 10.0
    elif icerik == IcerikYolu.tasavvuf_hadis:
        base -= 7.0
    elif icerik == IcerikYolu.klasik_edebiyat:
        base -= 4.0
    yavas = (1.0 - hiz_carpani) * 18.0 + (1.0 - huzur_carpani) * 22.0
    pct = base - yavas
    pct = max(-48.0, min(8.0, pct))
    return f"{pct:.0f}%"


def edge_pitch_string(karakter: SesKarakteri, icerik: IcerikYolu) -> str:
    if karakter == SesKarakteri.edip:
        return "+3Hz"
    if karakter == SesKarakteri.alim or icerik == IcerikYolu.kuran:
        return "-3Hz"
    return "+1Hz"


def tts_metadata_kimlik(
    *,
    karakter: str,
    icerik_yolu: str,
    ses_dosyasi_yolu: str | None = None,
    edge_voice: str | None = None,
    ek: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = {
        "proje": PROJE_ADI,
        "mimarlar": MIMAR_IMZA,
        "created_by": MIMAR_IMZA,
        "ses_profili": karakter,
        "icerik_yolu": icerik_yolu,
        "vizyon": "RÜZGAR — Alim / Edip / Asistan ses profilleri (Edge-TTS)",
    }
    if ses_dosyasi_yolu:
        meta["cikti_yolu"] = ses_dosyasi_yolu
    if edge_voice:
        meta["edge_voice"] = edge_voice
    if ek:
        meta.update(ek)
    return meta


def metadata_json_imza() -> str:
    return json.dumps(
        {"mimarlar": MIMAR_IMZA, "proje": PROJE_ADI, "created_by": MIMAR_IMZA},
        ensure_ascii=False,
    )


def pdf_metni_oku(yol: str | Path, *, max_karakter: int = 500_000) -> str:
    path = Path(yol)
    if not path.is_file():
        return ""
    reader_cls = None
    try:
        from PyPDF2 import PdfReader as reader_cls  # type: ignore
    except ImportError:
        try:
            from pypdf import PdfReader as reader_cls  # type: ignore
        except ImportError:
            return ""
    try:
        reader = reader_cls(str(path))
        parcalar: list[str] = []
        for page in reader.pages:
            t = page.extract_text()
            parcalar.append(t if t else "")
        birlesik = "\n\n".join(parcalar).strip()
        return birlesik[:max_karakter] if len(birlesik) > max_karakter else birlesik
    except Exception:
        return ""


def kutsal_okuma_tonu_gerekli(mesaj: str) -> bool:
    return analiz_icerik_yolu(mesaj) == IcerikYolu.kuran or bool(
        re.search(r"mektubat|risale|ilah[iı]", (mesaj or "").lower())
    )


def build_tts_yonergesi(metin_or_mesaj: str) -> str:
    yol = analiz_icerik_yolu(metin_or_mesaj)
    return ton_metni_icerik(yol)


def build_motor_context(message: str) -> str:
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    yol = analiz_icerik_yolu(prompt)
    oneri = varsayilan_karakter_icerige(yol)
    ton_ctx = ton_metni_icerik(yol)
    base = dinamit_heartbeat() + (
        f"[SES MOTORU — Created by {MIMAR_IMZA}]\n"
        f"Profiller — Alim: Kur'an/Hadis (yavaş, vakur, tane tane, derin); "
        f"Edip: edebiyat/gazel (lirik, yumuşak); Asistan: sohbet (net, nazik).\n"
        f"İçerik hattı: {yol.value}. Önerilen profil: {oneri.value}. {profil_aciklamasi(oneri)}\n"
        f"{ton_ctx}\n"
        "Telaffuz Edge-TTS ile; çıktı dosyalarında mimar metadata zorunlu.\n"
        f"Kullanıcı mesajı: {prompt}"
    )
    try:
        from ilim_assistant.motorlar.ses_faz72 import augment_ses_context

        return augment_ses_context(base)
    except Exception:
        return base
