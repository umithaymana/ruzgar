"""Madde 3.4 + 3.7 — iki hafıza katmanı kabulü.

- Kullanıcı katmanı (tercihler/«hatırla»): aynı kullanıcının cihazları arasında ortak.
- Cihaz/oturum katmanı («az önce konuştuk», sohbet arşivi): cihazda kalır, asla sızmaz.
- PC'de sor → telefonda yankı yok; telefonda «dün» → PC sohbetini karıştırmaz.
"""

from __future__ import annotations

import contextvars
import json
from pathlib import Path

import pytest

from ilim_assistant import ana_motor_sohbet_gecmis as gecmis
from ilim_assistant import hafiza_i_ruzgar as h
from ilim_assistant import ruzgar_kapsam as k
from ilim_assistant import ruzgar_kapsam_hafiza as kh

TOKENS = {
    "tok-tel": {"kullanici": "ali", "device_id": "tel-1"},
    "tok-tab": {"kullanici": "ali", "device_id": "tab-1"},
    "tok-veli": {"kullanici": "veli", "device_id": "tel-1"},
}


@pytest.fixture(autouse=True)
def ortam(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RUZGAR_DATA_ROOT", str(tmp_path / "data"))
    for ad in ("RUZGAR_PUBLIC_MODE", "RUZGAR_KAPSAM", "RUZGAR_KAPSAM_LEGACY", "RUZGAR_KAPSAM_HAFIZA"):
        monkeypatch.delenv(ad, raising=False)
    monkeypatch.setattr(gecmis, "_HISTORY_PATH", tmp_path / "hist.jsonl")
    pc_dosya = tmp_path / "pc" / "ruzgar_genel_hafiza.json"
    pc_dosya.parent.mkdir(parents=True)
    pc_dosya.write_text(
        json.dumps(
            [{"motor_tipi": "Hafıza", "soru": "pc sırrı", "cevap": "PC-OZEL"}], ensure_ascii=False
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(h, "_hafiza_singleton", h.HafizaIRuzgar(dosya_yolu=pc_dosya))
    kh._ONBELLEK.clear()

    import ilim_assistant.ruzgar_mobil_oturum as mo

    monkeypatch.setattr(mo, "validate_token", lambda t: TOKENS.get(t))
    k._current.set(None)
    k._pending.set(None)
    yield
    kh._ONBELLEK.clear()
    k._current.set(None)
    k._pending.set(None)


def _as(token: str | None, fn):
    def run():
        k.bind_scope(k.resolve_scope(token))
        return fn()

    return contextvars.copy_context().run(run)


def test_tercih_kullanici_katmaninda_ortak_sohbet_cihazda_kalir():
    # Telefonda bir tercih öğret + bir sohbet turu yaz
    _as("tok-tel", lambda: h.get_hafiza_motor().ekle_bilgi("kahve tercihim", "sade", motor_tipi="Hafıza"))
    _as(
        "tok-tel",
        lambda: gecmis.append_chat_turn(
            user_message="telefonda az önce konuştuk", assistant_message="telefon cevabı yeterince uzun"
        ),
    )
    # Aynı kullanıcının tableti: tercih görünür, sohbet görünmez
    tercih = _as("tok-tab", lambda: h.get_hafiza_motor().tum_bilgiler(motor_tipi="Hafıza"))
    assert tercih == {"kahve tercihim": "sade"}
    assert _as("tok-tab", lambda: gecmis._load_entries(limit=50)) == []
    # Telefonun kendisi kendi sohbetini görür
    assert [r["user"] for r in _as("tok-tel", lambda: gecmis._load_entries(limit=50))] == [
        "telefonda az önce konuştuk"
    ]


def test_baska_kullanici_ne_tercihi_ne_sohbeti_gorur():
    _as("tok-tel", lambda: h.get_hafiza_motor().ekle_bilgi("sır", "ALI", motor_tipi="Hafıza"))
    _as("tok-tel", lambda: gecmis.append_chat_turn(user_message="ali sorusu", assistant_message="ali cevabı uzun yeterli"))
    assert _as("tok-veli", lambda: h.get_hafiza_motor().tum_bilgiler(motor_tipi="Hafıza")) == {}
    assert _as("tok-veli", lambda: gecmis._load_entries(limit=50)) == []


def test_pc_sorar_telefonda_yanki_yok_ve_tersi():
    _as(None, lambda: gecmis.append_chat_turn(user_message="pc sorusu özel", assistant_message="pc cevabı yeterince uzun"))
    assert _as("tok-tel", lambda: gecmis._load_entries(limit=50)) == []
    _as("tok-tel", lambda: gecmis.append_chat_turn(user_message="telefon dün sorusu", assistant_message="tel cevabı yeterince uzun"))
    pc_satirlar = _as(None, lambda: gecmis._load_entries(limit=50))
    assert [r["user"] for r in pc_satirlar] == ["pc sorusu özel"]


def test_telefon_pc_kisisel_hafizasini_gormez():
    assert _as("tok-tel", lambda: h.get_hafiza_motor().tum_bilgiler(motor_tipi="Hafıza")) == {}
    assert _as(None, lambda: h.get_hafiza_motor().tum_bilgiler(motor_tipi="Hafıza")) == {"pc sırrı": "PC-OZEL"}
