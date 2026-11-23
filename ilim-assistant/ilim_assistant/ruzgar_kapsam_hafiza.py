"""Madde 3.5 — ``ruzgar_genel_hafiza.json`` kullanıcı/cihaz kapsamı.

Kural (Mimar, 2026-11-22):
- Mevcut ``ruzgar_genel_hafiza.json`` = PC (Mimar) hafızası. Dosya ASLA silinmez,
  taşınmaz, yeniden yazılmaz; PC kapsamı eski tekil motoru aynen kullanır.
- PC dışı kapsam (mobil kullanıcı, cihaz ipucu, geçersiz token) kendi kişisel
  dosyasına yazar: ``<data_root>/kapsam_hafiza/<anahtar>.json``.
- Ortak raflar (``Egitim``, ``EgitimDuzeltme``, ``BilgiKutuphane``, ``Eylem``) PC
  dosyasından YALNIZ OKUNUR (kişisel kopya olarak görünür, PC'ye yazılmaz).
  Kişisel raflar (``Hafıza``, ``OturumOzet``, ``Dosya`` …) PC'den hiç okunmaz.
- Kullanıcı girişi yapılmışsa anahtar kullanıcıdır (``u:<kullanici>``): aynı
  kullanıcının tüm cihazları aynı hafızayı görür. Cihaz katmanı (3.4) ayrıca eklenir.

Kapatma: ``RUZGAR_KAPSAM_HAFIZA=0`` (eski tekil davranış).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Callable

from ilim_assistant.hafiza_i_ruzgar import HafizaIRuzgar

_ORTAK_VARSAYILAN = ("Egitim", "EgitimDuzeltme", "BilgiKutuphane", "Eylem")
_MAX_ONBELLEK = 128
_ORTAK_ISARET = "_ortak"
_SLUG = re.compile(r"[^A-Za-z0-9_-]+")

_LOCK = threading.RLock()
_ONBELLEK: dict[str, "KapsamHafiza"] = {}


def _env_on(name: str, default: str = "1") -> bool:
    return (os.environ.get(name, default) or default).strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def kapsam_hafiza_enabled() -> bool:
    return _env_on("RUZGAR_KAPSAM_HAFIZA") and _env_on("RUZGAR_KAPSAM")


def ortak_raflar() -> frozenset[str]:
    raw = (os.environ.get("RUZGAR_KAPSAM_ORTAK_RAFLAR") or "").strip()
    if raw:
        return frozenset(p.strip() for p in raw.split(",") if p.strip())
    return frozenset(_ORTAK_VARSAYILAN)


def pc_kullanicilari() -> frozenset[str]:
    """İsteğe bağlı: bu kullanıcılar PC hafızasını kullanır (``RUZGAR_KAPSAM_HAFIZA_PC_KULLANICI``)."""
    raw = (os.environ.get("RUZGAR_KAPSAM_HAFIZA_PC_KULLANICI") or "").strip().lower()
    return frozenset(p.strip() for p in raw.split(",") if p.strip())


def hafiza_anahtari(scope: Any) -> str:
    """Kişisel hafıza anahtarı: girişli kullanıcı → ``u:<kullanici>``; aksi hâlde kapsam anahtarı."""
    if getattr(scope, "authed", False) and getattr(scope, "user", ""):
        return f"u:{scope.user}"
    return str(getattr(scope, "key", "") or "anon")


def _dosya_adi(anahtar: str) -> str:
    slug = _SLUG.sub("-", anahtar).strip("-")[:40] or "x"
    h = hashlib.sha1(anahtar.encode("utf-8")).hexdigest()[:8]
    return f"{slug}_{h}.json"


def kapsam_hafiza_dizini() -> Path:
    from ilim_assistant.ruzgar_public_mode import data_root

    d = data_root() / "kapsam_hafiza"
    d.mkdir(parents=True, exist_ok=True)
    return d


class KapsamHafiza(HafizaIRuzgar):
    """Kişisel dosya + PC'nin ortak raflarının salt okunur görünümü."""

    def __init__(self, anahtar: str, dosya_yolu: Path, pc_motor: Callable[[], HafizaIRuzgar]) -> None:
        self._anahtar = anahtar
        self._pc_motor = pc_motor
        self._yaz_kilit = threading.RLock()
        dosya_yolu = Path(dosya_yolu)
        dosya_yolu.parent.mkdir(parents=True, exist_ok=True)
        if not dosya_yolu.exists():
            # Eski kök dosyalarının kopyalanmasını önle: boş kişisel dosya ile başla.
            dosya_yolu.write_text("[]", encoding="utf-8")
        super().__init__(dosya_yolu=dosya_yolu)
        self._eski_dosya_yollari = []

    # -- görünüm: kişisel + ortak (kişisel sonra gelir → arama sırasında öncelikli) --
    def _ortak_satirlar(self) -> list[dict[str, str]]:
        try:
            pc = self._pc_motor()
            pc._reload_if_disk_changed()
            raflar = ortak_raflar()
            out: list[dict[str, str]] = []
            for row in pc._kayitlar:
                if row.get("motor_tipi") in raflar:
                    kopya = dict(row)
                    kopya[_ORTAK_ISARET] = "1"
                    out.append(kopya)
            return out
        except Exception:
            return []

    def _disk_mtime_ns(self) -> int | None:
        own = super()._disk_mtime_ns()
        try:
            pc_motor = self._pc_motor()
            pc = pc_motor._disk_mtime_ns()
            # Windows zaman damgası ~15 ms adımlıdır: aynı adımda iki yazım aynı mtime verir.
            # Boyut da imzaya girer → ortak raf değişimi kaçmaz.
            try:
                pc_boyut = pc_motor._dosya_yolu.stat().st_size
            except OSError:
                pc_boyut = None
        except Exception:
            pc = None
            pc_boyut = None
        return hash((own, pc, pc_boyut))

    def _yukle_veya_olustur(self) -> None:
        with self._yaz_kilit:
            self._ensure_store_ready()
            kisisel: list[dict[str, str]] = []
            try:
                icerik = self._dosya_yolu.read_text(encoding="utf-8")
                parsed = json.loads(icerik) if icerik.strip() else {}
                kisisel = self._normalize_loaded_store(parsed)
            except Exception:
                kisisel = []
            self._kayitlar = self._ortak_satirlar() + kisisel
            self._sync_hafiza_view()
            self._sync_disk_mtime_after_load()

    def _dosyaya_kaydet(self) -> None:
        """Yalnız kişisel satırları (ortak kopyalar hariç) atomik yazar; sonra görünümü tazeler."""
        with self._yaz_kilit:
            self._ensure_store_ready()
            kisisel = [
                {k: v for k, v in row.items() if k != _ORTAK_ISARET}
                for row in self._kayitlar
                if not row.get(_ORTAK_ISARET)
            ]
            tmp = self._dosya_yolu.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(kisisel, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self._dosya_yolu)
            self._yukle_veya_olustur()

    def sil_bilgi(self, soru: str, motor_tipi: str = HafizaIRuzgar.VARSAYILAN_MOTOR_TIPI) -> bool:
        """Ortak (PC) satırlar silinemez; yalnız kişisel satır silinir."""
        self._ensure_store_ready()
        anahtar = (soru or "").strip()
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        if not any(
            (not r.get(_ORTAK_ISARET)) and r.get("motor_tipi") == mt and r.get("soru") == anahtar
            for r in self._kayitlar
        ):
            return False
        return super().sil_bilgi(soru, motor_tipi)


def pc_hafiza_motoru() -> HafizaIRuzgar:
    """PC (Mimar) hafızası — kapsamdan bağımsız tekil motor."""
    from ilim_assistant import hafiza_i_ruzgar as h

    if h._hafiza_singleton is None:
        h._hafiza_singleton = HafizaIRuzgar()
    return h._hafiza_singleton


def kapsam_motoru(scope: Any) -> HafizaIRuzgar:
    """PC dışı kapsam için kişisel motor (önbellekli)."""
    anahtar = hafiza_anahtari(scope)
    with _LOCK:
        m = _ONBELLEK.get(anahtar)
        if m is not None:
            return m
        yol = kapsam_hafiza_dizini() / _dosya_adi(anahtar)
        m = KapsamHafiza(anahtar, yol, pc_hafiza_motoru)
        if len(_ONBELLEK) >= _MAX_ONBELLEK:
            _ONBELLEK.pop(next(iter(_ONBELLEK)), None)
        _ONBELLEK[anahtar] = m
        return m


def _kisisel_kapsam_veya_none() -> Any | None:
    """Geçerli istek PC dışıysa kapsamı döndür; PC / kapalı / hata → None (eski yol)."""
    if not kapsam_hafiza_enabled():
        return None
    try:
        from ilim_assistant.ruzgar_kapsam import current_scope

        sc = current_scope()
        if sc.is_pc:
            return None
        if getattr(sc, "authed", False) and str(sc.user).lower() in pc_kullanicilari():
            return None
        return sc
    except Exception:
        return None


def secili_motor_veya_none() -> HafizaIRuzgar | None:
    """Geçerli istek PC dışıysa kişisel motor; PC / kapalı / hata → None (eski yol)."""
    sc = _kisisel_kapsam_veya_none()
    if sc is None:
        return None
    try:
        return kapsam_motoru(sc)
    except Exception:
        return None


def baglam_yolu_veya_none() -> Path | None:
    """``ruzgar_kullanici_baglami.json`` karşılığı: PC dışı kapsamda kişisel dosya."""
    sc = _kisisel_kapsam_veya_none()
    if sc is None:
        return None
    try:
        return kapsam_hafiza_dizini() / ("baglam_" + _dosya_adi(hafiza_anahtari(sc)))
    except Exception:
        return None


def kapsam_hafiza_status() -> dict[str, Any]:
    try:
        from ilim_assistant.ruzgar_kapsam import current_scope

        sc = current_scope()
    except Exception:
        sc = None
    return {
        "enabled": kapsam_hafiza_enabled(),
        "ortak_raflar": sorted(ortak_raflar()),
        "kisisel_motor_sayisi": len(_ONBELLEK),
        "kapsam": getattr(sc, "key", None),
    }
