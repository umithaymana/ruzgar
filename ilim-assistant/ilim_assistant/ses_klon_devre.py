# Created by Ümit & Gökçenur
"""Klon (XTTS) devre kesici — sohbet TTS'i her cümlede 8 sn boşa beklemesin.

Sorun (2026-11-23, mobil): ``backend=auto`` + ``prefer_clone`` iken her cümle önce XTTS'i dener;
XTTS sohbet süresine (8 sn) yetişemezse Edge'e düşülür. Kuyruktaki her parça aynı 8 sn'yi
yeniden öder → ilk ses 25–30 sn, parçalar arası ~30 sn bekleme.

Çözüm: Klon süreye yetişemeyince devre AÇILIR; ``bekleme_sn()`` boyunca sohbet seslerinde
doğrudan Edge. Süre dolunca tek bir deneme (yarı açık) yapılır: başarılıysa kapanır,
yine kaçırırsa bekleme ikiye katlanır (en çok 1 saat).

Kapsam: yalnız ``backend=auto`` ve sohbet sınıfı sesler (tilavet/âlim ve açıkça ``clone``
istenen çağrılar eski davranışı korur). Kapatma: ``RUZGAR_TTS_KLON_DEVRE=0``.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any

VERSION = "ses-klon-devre-v1-2026-11-23"

# Uzun süre tanınan (devreden muaf) karakterler
MUAF_KARAKTERLER = ("tilavet", "alim")

_LOCK = threading.Lock()
_durum: dict[str, Any] = {
    "acik_until": 0.0,
    "ardisik_hata": 0,
    "toplam_hata": 0,
    "atlanan": 0,
    "son_hata_ts": 0.0,
    "son_basari_ts": 0.0,
}


def _env_float(name: str, default: float, lo: float, hi: float) -> float:
    try:
        v = float((os.environ.get(name) or "").strip() or default)
    except ValueError:
        v = default
    return max(lo, min(hi, v))


def devre_etkin() -> bool:
    return os.environ.get("RUZGAR_TTS_KLON_DEVRE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def bekleme_sn(ardisik: int = 1) -> float:
    """İlk hatada taban süre; ardışık hatalarda iki katına çıkar (üst sınır 1 saat)."""
    taban = _env_float("RUZGAR_TTS_KLON_DEVRE_SEC", 600.0, 30.0, 3600.0)
    return min(3600.0, taban * (2 ** max(0, int(ardisik) - 1)))


def uygulanir(karakter: str | None, backend: str | None) -> bool:
    """Devre bu çağrıya uygulanır mı? (açıkça ``clone`` ve muaf karakterler hariç)"""
    if not devre_etkin():
        return False
    be = (backend or "auto").strip().lower() or "auto"
    if be != "auto":
        return False
    return (karakter or "").strip().lower() not in MUAF_KARAKTERLER


def acik_mi(now: float | None = None) -> bool:
    if not devre_etkin():
        return False
    t = time.time() if now is None else now
    with _LOCK:
        return t < float(_durum["acik_until"])


def atla_say() -> None:
    with _LOCK:
        _durum["atlanan"] = int(_durum["atlanan"]) + 1


def hata_kaydet(now: float | None = None) -> float:
    """Klon süreye yetişemedi → devreyi aç. Dönüş: bekleme süresi (sn)."""
    t = time.time() if now is None else now
    with _LOCK:
        _durum["ardisik_hata"] = int(_durum["ardisik_hata"]) + 1
        _durum["toplam_hata"] = int(_durum["toplam_hata"]) + 1
        bek = bekleme_sn(int(_durum["ardisik_hata"]))
        _durum["acik_until"] = t + bek
        _durum["son_hata_ts"] = t
        return bek


def basari_kaydet(now: float | None = None) -> None:
    t = time.time() if now is None else now
    with _LOCK:
        _durum["ardisik_hata"] = 0
        _durum["acik_until"] = 0.0
        _durum["son_basari_ts"] = t


def sifirla() -> None:
    with _LOCK:
        _durum.update(
            acik_until=0.0,
            ardisik_hata=0,
            toplam_hata=0,
            atlanan=0,
            son_hata_ts=0.0,
            son_basari_ts=0.0,
        )


def durum(now: float | None = None) -> dict[str, Any]:
    t = time.time() if now is None else now
    with _LOCK:
        kalan = max(0.0, float(_durum["acik_until"]) - t)
        return {
            "version": VERSION,
            "etkin": devre_etkin(),
            "acik": kalan > 0.0,
            "kalan_sn": round(kalan, 1),
            "ardisik_hata": int(_durum["ardisik_hata"]),
            "toplam_hata": int(_durum["toplam_hata"]),
            "atlanan": int(_durum["atlanan"]),
        }
