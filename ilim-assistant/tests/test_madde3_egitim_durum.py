"""Madde 3 — öğretme «bekleyen durum» (ruzgar_egitim_durum) kapsamlı olmalı.

Bir cihaz «öğretir misin?» beklerken başka cihazın (veya PC'nin) bir sonraki mesajı
o beklemenin cevabı sayılmasın; PC'nin mevcut dosyası PC kapsamında aynen kalsın.
"""

from __future__ import annotations

import contextvars
import json
from pathlib import Path

import pytest

from ilim_assistant import ruzgar_egitim as eg
from ilim_assistant import ruzgar_kapsam as k

TOKENS = {
    "tok-tel": {"kullanici": "ali", "device_id": "tel-1"},
    "tok-tab": {"kullanici": "ali", "device_id": "tab-1"},
}


@pytest.fixture(autouse=True)
def ortam(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RUZGAR_DATA_ROOT", str(tmp_path / "data"))
    for ad in ("RUZGAR_PUBLIC_MODE", "RUZGAR_KAPSAM", "RUZGAR_KAPSAM_LEGACY"):
        monkeypatch.delenv(ad, raising=False)
    pc_durum = tmp_path / "pc_durum.json"
    monkeypatch.setattr(eg, "_PC_DURUM_YOLU", pc_durum, raising=False)
    import ilim_assistant.ruzgar_mobil_oturum as mo

    monkeypatch.setattr(mo, "validate_token", lambda t: TOKENS.get(t))
    k._current.set(None)
    k._pending.set(None)
    yield {"pc_durum": pc_durum}
    k._current.set(None)
    k._pending.set(None)


def _as(token, fn):
    def run():
        k.bind_scope(k.resolve_scope(token))
        return fn()

    return contextvars.copy_context().run(run)


def test_cihaz_bekleyen_durumu_baska_cihaza_sizmaz():
    _as("tok-tel", lambda: eg.set_pending("teach", "tel sorusu"))
    assert _as("tok-tel", eg.get_pending).get("soru") == "tel sorusu"
    assert _as("tok-tab", eg.get_pending) == {}
    assert _as(None, eg.get_pending) == {}


def test_pc_bekleyen_durumu_mobile_sizmaz(ortam):
    _as(None, lambda: eg.set_pending("teach", "pc sorusu"))
    assert _as(None, eg.get_pending).get("soru") == "pc sorusu"
    assert _as("tok-tel", eg.get_pending) == {}
    # PC'nin dosyası PC kapsamında yazıldı
    assert json.loads(ortam["pc_durum"].read_text(encoding="utf-8"))["soru"] == "pc sorusu"


def test_mobil_temizle_pc_beklemesini_silmez():
    _as(None, lambda: eg.set_pending("teach", "pc sorusu"))
    _as("tok-tel", lambda: eg.set_pending("teach", "tel sorusu"))
    _as("tok-tel", eg.clear_pending)
    assert _as(None, eg.get_pending).get("soru") == "pc sorusu"
    assert _as("tok-tel", eg.get_pending) == {}


def test_kapsam_kapaliysa_tek_dosya(monkeypatch):
    monkeypatch.setenv("RUZGAR_KAPSAM", "0")
    _as("tok-tel", lambda: eg.set_pending("teach", "x sorusu"))
    assert _as("tok-tab", eg.get_pending).get("soru") == "x sorusu"
