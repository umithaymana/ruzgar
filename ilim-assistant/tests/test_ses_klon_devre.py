"""Klon devre kesici — sohbet TTS'i her cümlede XTTS süresini boşa beklemesin."""

from __future__ import annotations

import pytest

from ilim_assistant import ses_klon_devre as d


@pytest.fixture(autouse=True)
def _temiz(monkeypatch):
    for ad in ("RUZGAR_TTS_KLON_DEVRE", "RUZGAR_TTS_KLON_DEVRE_SEC"):
        monkeypatch.delenv(ad, raising=False)
    d.sifirla()
    yield
    d.sifirla()


def test_baslangicta_kapali():
    assert d.acik_mi(now=1000.0) is False
    assert d.durum(now=1000.0)["acik"] is False


def test_hata_devreyi_acar_sure_dolunca_kapanir():
    bek = d.hata_kaydet(now=1000.0)
    assert bek == 600.0
    assert d.acik_mi(now=1000.0 + 599) is True
    assert d.acik_mi(now=1000.0 + 601) is False  # yarı açık: bir deneme hakkı


def test_ardisik_hata_beklemeyi_katlar_ust_sinir_bir_saat():
    assert d.hata_kaydet(now=0.0) == 600.0
    assert d.hata_kaydet(now=1.0) == 1200.0
    assert d.hata_kaydet(now=2.0) == 2400.0
    assert d.hata_kaydet(now=3.0) == 3600.0
    assert d.hata_kaydet(now=4.0) == 3600.0


def test_basari_devreyi_kapatir_ve_sayaci_sifirlar():
    d.hata_kaydet(now=0.0)
    d.hata_kaydet(now=1.0)
    d.basari_kaydet(now=2.0)
    assert d.acik_mi(now=3.0) is False
    assert d.durum(now=3.0)["ardisik_hata"] == 0
    assert d.hata_kaydet(now=4.0) == 600.0  # sayaç sıfırdan başladı


@pytest.mark.parametrize(
    "kar,be,beklenen",
    [
        ("muhabbet", "auto", True),
        ("muhabbet", None, True),
        ("edip", "auto", True),
        ("muhabbet", "clone", False),  # açık klon isteği muaf
        ("tilavet", "auto", False),  # uzun süre tanınan sesler muaf
        ("alim", "auto", False),
        ("muhabbet", "edge", False),
    ],
)
def test_uygulanir_kapsami(kar, be, beklenen):
    assert d.uygulanir(kar, be) is beklenen


def test_env_ile_kapatilir(monkeypatch):
    monkeypatch.setenv("RUZGAR_TTS_KLON_DEVRE", "0")
    d.hata_kaydet(now=0.0)
    assert d.acik_mi(now=1.0) is False
    assert d.uygulanir("muhabbet", "auto") is False


def test_bekleme_env_ile_ayarlanir(monkeypatch):
    monkeypatch.setenv("RUZGAR_TTS_KLON_DEVRE_SEC", "120")
    assert d.hata_kaydet(now=0.0) == 120.0


def test_atlanan_sayilir():
    d.hata_kaydet(now=0.0)
    d.atla_say()
    d.atla_say()
    assert d.durum(now=1.0)["atlanan"] == 2
