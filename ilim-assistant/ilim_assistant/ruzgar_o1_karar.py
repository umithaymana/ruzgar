# Created by Ümit & Gökçenur
"""O1 — tek tur Karar kaydı (Kuzey Yıldızı).

Her turda bir kez üretilir: niyet, hedef motor, canlı bilgi, kütüphane, üslup, bütçe, güven, alan.
Kestirmeler bu kayda tabidir (`kestirme_izinli`). Boot sırasına dokunmaz.
Kapat: RUZGAR_O1_KARAR=0
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

O1_VERSION = "o1-karar-v2-2026-11-25"

_DIN_ALAN = frozenset(
    {"fikh", "usul", "tefsir", "kuran", "hadis", "siyer", "tasavvuf", "akaid", "din"}
)

# Tek başına başka alana da oturan ipuçları — raf seçmeden önce ayıklanır.
_AMBIG: dict[str, tuple[str, ...]] = {
    "akaid": ("sıfat", "sifat"),
    "kuran": ("medeni", "medenî", "mekki", "mekkî"),
}

_DETECTORS: tuple[tuple[str, str, str], ...] = (
    ("fikh", "ilim_assistant.ruzgar_fikh_kutuphane", "looks_like_fikh_question"),
    ("usul", "ilim_assistant.ruzgar_usul_fikh_kutuphane", "looks_like_usul_question"),
    ("tefsir", "ilim_assistant.ruzgar_tefsir_kutuphane", "looks_like_tefsir_question"),
    ("kuran", "ilim_assistant.ruzgar_kuran_anlik", "looks_like_kuran_question"),
    ("hadis", "ilim_assistant.ruzgar_hadis_kutuphane", "looks_like_hadis_question"),
    ("siyer", "ilim_assistant.ruzgar_siyer_kutuphane", "looks_like_siyer_question"),
    ("tasavvuf", "ilim_assistant.ruzgar_tasavvuf_kutuphane", "looks_like_tasavvuf_question"),
    ("akaid", "ilim_assistant.ruzgar_akaid_kutuphane", "looks_like_akaid_question"),
    ("felsefe", "ilim_assistant.ruzgar_felsefe_kutuphane", "looks_like_felsefe_question"),
    ("edebiyat", "ilim_assistant.ruzgar_edebiyat_kutuphane", "looks_like_edebiyat_question"),
    ("psikoloji", "ilim_assistant.ruzgar_psikoloji_kutuphane", "looks_like_psikoloji_question"),
    ("bilgisayar", "ilim_assistant.ruzgar_bilgisayar_kutuphane", "looks_like_bilgisayar_question"),
    ("teknoloji", "ilim_assistant.ruzgar_teknoloji_kutuphane", "looks_like_teknoloji_question"),
    ("cografya", "ilim_assistant.ruzgar_cografya_kutuphane", "looks_like_cografya_question"),
    ("bilim", "ilim_assistant.ruzgar_bilim_kutuphane", "looks_like_bilim_question"),
)

_FN_AILE: dict[str, str] = {
    "try_akaid_reply": "akaid",
    "try_hadis_reply": "hadis",
    "try_siyer_reply": "siyer",
    "try_tasavvuf_reply": "tasavvuf",
    "try_felsefe_reply": "felsefe",
    "try_psikoloji_reply": "psikoloji",
    "try_edebiyat_reply": "edebiyat",
    "try_ek_raf_reply": "ek",
    "try_bilim_reply": "bilim",
    "try_cografya_reply": "cografya",
    "try_bilgisayar_reply": "bilgisayar",
    "try_teknoloji_reply": "teknoloji",
    "try_usul_fikh_reply": "usul",
    "try_fikh_reply": "fikh",
    "try_kuran_instant_reply": "kuran",
    "try_kutuphane_instant_reply": "kutuphane",
    "try_bilgi_kutuphane_instant_reply": "kutuphane",
    "maybe_gundelik_instant_reply": "sohbet",
    "try_instant_reply": "sohbet",
    "maybe_weather_instant_reply": "hava",
    "maybe_programlama_instant_reply": "programlama",
    "looks_like_arapca_lugat_question": "lugat",
}

# Canlı kapı kaydı. Tarihsel «168» sayımı X1 ölçümüne kalır; burada emekliye alınmaz.
KESTIRME_KAYIT: tuple[dict[str, str], ...] = (
    {"ad": "sohbet", "tur": "yonlendirici", "giris": "maybe_gundelik_instant_reply / try_instant_reply", "kural": "niyet sohbet"},
    {"ad": "hava", "tur": "yonlendirici", "giris": "maybe_weather_instant_reply", "kural": "canli"},
    {"ad": "programlama", "tur": "yonlendirici", "giris": "should_delegate_to_programlama", "kural": "hedef programlama"},
    {"ad": "lugat", "tur": "yonlendirici", "giris": "looks_like_arapca_lugat_question", "kural": "alan dil"},
    {"ad": "kutuphane", "tur": "yonlendirici", "giris": "_library_instant_or_none", "kural": "raf alani eslesir"},
    {"ad": "web", "tur": "yonlendirici", "giris": "looks_like_live_web_needed", "kural": "canli ve niyet canli"},
    {"ad": "fikh", "tur": "kestirme", "giris": "try_fikh_reply", "kural": "alan fikh veya din"},
    {"ad": "usul", "tur": "kestirme", "giris": "try_usul_fikh_reply", "kural": "alan usul veya din"},
    {"ad": "tefsir", "tur": "kestirme", "giris": "looks_like_tefsir_question", "kural": "alan tefsir veya din"},
    {"ad": "kuran", "tur": "kestirme", "giris": "looks_like_kuran_question", "kural": "alan kuran veya din"},
    {"ad": "hadis", "tur": "kestirme", "giris": "try_hadis_reply", "kural": "alan hadis veya din"},
    {"ad": "siyer", "tur": "kestirme", "giris": "try_siyer_reply", "kural": "alan siyer veya din"},
    {"ad": "tasavvuf", "tur": "kestirme", "giris": "try_tasavvuf_reply", "kural": "alan tasavvuf veya din"},
    {"ad": "akaid", "tur": "kestirme", "giris": "try_akaid_reply", "kural": "alan akaid veya din"},
    {"ad": "felsefe", "tur": "kestirme", "giris": "try_felsefe_reply", "kural": "alan felsefe"},
    {"ad": "edebiyat", "tur": "kestirme", "giris": "try_edebiyat_reply", "kural": "alan edebiyat"},
    {"ad": "psikoloji", "tur": "kestirme", "giris": "try_psikoloji_reply", "kural": "alan psikoloji"},
    {"ad": "bilgisayar", "tur": "kestirme", "giris": "try_bilgisayar_reply", "kural": "alan bilgisayar"},
    {"ad": "teknoloji", "tur": "kestirme", "giris": "try_teknoloji_reply", "kural": "alan teknoloji"},
    {"ad": "cografya", "tur": "kestirme", "giris": "try_cografya_reply", "kural": "alan cografya"},
    {"ad": "bilim", "tur": "kestirme", "giris": "try_bilim_reply", "kural": "alan bilim"},
    {"ad": "ek", "tur": "kestirme", "giris": "try_ek_raf_reply", "kural": "alan genel"},
)


def o1_enabled() -> bool:
    return os.environ.get("RUZGAR_O1_KARAR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().translate(str.maketrans("ışğüöçâîû", "isguocaiu"))
    return t.strip()


@dataclass
class Karar:
    niyet: str
    hedef_motor: str
    canli: bool
    kutuphane: bool
    uslup: str
    butce_sn: float
    guven: float
    alan: str = "genel"
    version: str = O1_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def kestirme_envanteri() -> list[dict[str, str]]:
    """6 yönlendirici + bağlı kestirmeler. Ölü kayıt silinmez (X1)."""
    return [dict(row) for row in KESTIRME_KAYIT]


def aile_from_callable(fn: Any) -> str:
    name = str(getattr(fn, "__name__", "") or "")
    return _FN_AILE.get(name, "")


@lru_cache(maxsize=64)
def _detector(mod_path: str, fn_name: str):
    import importlib

    return getattr(importlib.import_module(mod_path), fn_name)


def _looks(aile: str, message: str) -> bool:
    for ad, mod, fn in _DETECTORS:
        if ad != aile:
            continue
        try:
            return bool(_detector(mod, fn)(message))
        except Exception:
            return False
    return False


def _looks_strong(aile: str, message: str) -> bool:
    if not _looks(aile, message):
        return False
    amb = _AMBIG.get(aile)
    if not amb:
        return True
    text = message or ""
    for tok in amb:
        text = re.sub(rf"(?i)(?<![\w]){re.escape(tok)}\w*", " ", text)
    return _looks(aile, text)


def _acik_dil(message: str) -> bool:
    low = _fold(message)
    return bool(
        re.search(
            r"\b(?:lugat|sozluk|nahiv|sarf|irab|lane|morfoloji|mushtaq|mustak)\b",
            low,
        )
        or re.search(r"\bkok(?:u|un|unu)?\b", low)
    )


def _matematik(message: str) -> bool:
    low = _fold(message)
    return bool(
        re.search(
            r"\b(?:matris|vektor|sinus|kosinus|turev|integral|denklem|"
            r"geometri|trigonometri|logaritma)\w*\b",
            low,
        )
    )


def _hukuk(message: str) -> bool:
    low = _fold(message)
    return bool(
        re.search(
            r"\b(?:medeni\s+hukuk|ceza\s+hukuk|borclar\s+hukuk|"
            r"anayasa|mahkeme|kanun|dava|hukuk)\w*\b",
            low,
        )
    )


def _kisa_sohbet(message: str) -> bool:
    low = _fold(message)
    if not low or len(low) > 56:
        return False
    return bool(
        re.fullmatch(
            r"(?:selam|merhaba|naber|ne haber|nasilsin|iyi misin|"
            r"gunaydin|iyi aksam|iyi geceler|tesekkur(?:ler)?|sagol|eyvallah)"
            r"(?:\s+(?:ruzgar|abi|umit|kardesim))?[\s!.?]*",
            low,
        )
    )


def _hava(message: str) -> bool:
    low = _fold(message)
    return bool(re.search(r"\bhava\b", low))


def alan_tespit(message: str, *, question_plan: Any | None = None) -> str:
    """Aynı metin → aynı alan. Şehir/koordinat yok."""
    raw = (message or "").strip()
    if not raw:
        return "genel"
    if _kisa_sohbet(raw):
        return "sohbet"
    if _acik_dil(raw) and not _matematik(raw):
        return "dil"
    if _matematik(raw):
        return "matematik"
    for ad, _mod, _fn in _DETECTORS:
        if _looks_strong(ad, raw):
            return ad
    if _hukuk(raw):
        stripped = raw
        for tok in _AMBIG["kuran"]:
            stripped = re.sub(rf"(?i)(?<![\w]){re.escape(tok)}\w*", " ", stripped)
        try:
            from ilim_assistant.ruzgar_kutuphane_gorev import din_alani_sorusu

            if not din_alani_sorusu(stripped):
                return "hukuk"
        except Exception:
            return "hukuk"
    try:
        from ilim_assistant.ruzgar_kutuphane_gorev import din_alani_sorusu

        if din_alani_sorusu(raw):
            return "din"
    except Exception:
        pass
    if _hava(raw):
        return "canli"
    if _kisa_sohbet(raw):
        return "sohbet"
    primary = str(getattr(question_plan, "primary", "") or "")
    if primary == "hava":
        return "canli"
    if primary == "gundelik":
        return "sohbet"
    return "genel"


def _acik_kod_isi(message: str) -> bool:
    low = _fold(message)
    return bool(
        re.search(
            r"\b(?:kod(?:u|unu)?|fonksiyon|function|terminal|pytest|script|"
            r"calistir|yazilim|debug|repo)\b",
            low,
        )
    )


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
    alan = alan_tespit(raw, question_plan=question_plan)

    din = alan in _DIN_ALAN
    try:
        from ilim_assistant.ruzgar_kutuphane_gorev import din_alani_sorusu, is_kutuphane_bilgi_soru

        din = din or bool(din_alani_sorusu(raw))
        kutuphane = bool(
            is_kutuphane_bilgi_soru(raw) or (use_rag and primary in ("bilgi", "bilim", "dilbilgisi"))
        )
    except Exception:
        kutuphane = bool(use_rag and primary in ("bilgi", "bilim", "dilbilgisi"))

    try:
        from ilim_assistant.ruzgar_k2_uslup import uslup_profili

        uslup = uslup_profili(raw, question_plan=question_plan, mode_norm=mode_norm)
    except Exception:
        uslup = "alim" if din else "sade_ogretmen"

    canli = primary == "hava" or (prefer_web and primary not in ("bilgi", "bilim")) or alan == "canli"
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import looks_like_live_web_needed

        if looks_like_live_web_needed(raw):
            canli = True
    except Exception:
        pass

    bilgi_alani = alan not in ("genel", "sohbet", "canli", "islem", "")
    kod = _acik_kod_isi(raw)
    if not raw:
        hedef, niyet, guven = "ana_motor", "emin_degil", 0.0
    elif kod and not din:
        hedef, niyet = "programlama", "islem"
        guven = 0.75
    elif alan != "canli" and (bilgi_alani or din or (kutuphane and alan != "sohbet")):
        hedef, niyet = "ana_motor", "bilgi"
        guven = 0.8
    elif alan == "canli" or primary == "hava" or (canli and not din):
        hedef, niyet = "ana_motor", "canli"
        guven = 0.7
    elif mode_norm == "programlama" or primary == "islem":
        hedef, niyet = "programlama", "islem"
        guven = 0.75
    elif primary == "gundelik" or alan == "sohbet":
        hedef, niyet = "ana_motor", "sohbet"
        guven = 0.7
    else:
        hedef, niyet = "ana_motor", primary or "diger"
        guven = 0.55 if primary else 0.55

    if butce_sn is None:
        butce_sn = 22.0 if din or niyet == "bilgi" else 15.0

    return Karar(
        niyet=niyet,
        hedef_motor=hedef,
        canli=bool(canli and not din and niyet != "bilgi"),
        kutuphane=bool(kutuphane or din or (bilgi_alani and alan not in ("dil",))),
        uslup=uslup,
        butce_sn=float(butce_sn),
        guven=float(guven),
        alan=alan,
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
        orchestration_out["o1"] = {
            "version": O1_VERSION,
            "niyet": karar.niyet,
            "alan": karar.alan,
        }
    return karar


def delege_sonrasi_mod(mode_before: str, mode_now: str, karar: Karar | None) -> str:
    """Bilgi sorusu programlamaya kaçtıysa eski moda dön."""
    if not o1_enabled() or karar is None:
        return mode_now
    if (
        mode_now == "programlama"
        and mode_before != "programlama"
        and karar.hedef_motor != "programlama"
    ):
        return mode_before
    return mode_now


def kestirme_izinli(aile: str, karar: Karar | None, message: str = "") -> bool:
    """Kestirme, bu turun Karar alanına uymuyorsa susar."""
    if not o1_enabled():
        return True
    if karar is None:
        karar = karar_uret(message)
    a = (aile or "").strip().lower()
    if not a:
        return True
    alan = karar.alan or "genel"
    if a in ("sohbet", "gundelik", "fast_lane", "selam"):
        return karar.niyet == "sohbet"
    if a in ("hava", "canli"):
        return bool(karar.canli) or alan == "canli"
    if a in ("programlama", "terminal"):
        return karar.hedef_motor == "programlama"
    if a in ("lugat", "tercume"):
        return alan == "dil"
    if a == "web":
        return bool(karar.canli) and karar.niyet == "canli"
    if a == "ek":
        return alan == "genel"
    if a == "kutuphane":
        if karar.niyet in ("sohbet", "canli") or alan in ("canli", "hukuk", "matematik", "dil"):
            return False
        return bool(karar.kutuphane or karar.niyet == "bilgi")
    raflar = _DIN_ALAN | {
        "felsefe",
        "edebiyat",
        "psikoloji",
        "bilgisayar",
        "teknoloji",
        "cografya",
        "bilim",
        "matematik",
        "hukuk",
        "dil",
    }
    if a in raflar:
        if alan == a:
            return True
        if alan == "din" and a in _DIN_ALAN:
            return True
        if alan == "genel":
            # Din rafları belirsiz tek kelimede (sıfat, medenî) susar.
            # Fen/teknik kart, soruyu kendi kavramıyla tutuyorsa açık kalır.
            if a in _DIN_ALAN:
                return _looks_strong(a, message)
            return True
        return False
    return True
