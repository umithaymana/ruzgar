"""
Geriye uyum katmanı.

Köprü mimarisi devreden çıkarıldı; tüm motorlar merkezi
`ruzgar_genel_hafiza.json` dosyasına etiketli kayıt yazar/okur.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


_MOTOR_ETIKET = {
    "hafiza": "Hafıza",
    "ses": "Ses",
    "video": "Video",
    "programlama": "Programlama",
    "ilim": "İlim",
    "okuma": "İlim",
}


def ilim_assistant_root() -> Path:
    return Path(__file__).resolve().parents[1]


def genel_path() -> Path:
    return ilim_assistant_root() / "ruzgar_genel_hafiza.json"


def ensure_hafiza_bridge_ready() -> None:
    from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

    get_hafiza_motor()


def sync_after_any_motor_disk_write() -> None:
    # Merkezi modelde ek köprü senkronu gerekmiyor.
    return


def ogren_learning_for_motor(motor_code: str, soru: str, cevap: str) -> None:
    from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

    etiket = _MOTOR_ETIKET.get((motor_code or "").strip().lower(), "Hafıza")
    get_hafiza_motor().ekle_bilgi(soru, cevap, motor_tipi=etiket)


def genel_hafiza_lookup(message: str) -> Optional[str]:
    from ilim_assistant.hafiza_i_ruzgar import genel_hafiza_lookup as _lookup

    return _lookup(message, motor_tipi=None)


def startup_warmup_hafiza_hiyerarsi() -> None:
    ensure_hafiza_bridge_ready()
