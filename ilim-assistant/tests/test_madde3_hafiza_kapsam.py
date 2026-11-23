"""Madde 3.5 — ruzgar_genel_hafiza.json kullanıcı/cihaz kapsamı."""

from __future__ import annotations

import contextvars
import json
from pathlib import Path

import pytest

from ilim_assistant import hafiza_i_ruzgar as h
from ilim_assistant import ruzgar_kapsam as k
from ilim_assistant import ruzgar_kapsam_hafiza as kh


def _scope(user: str, device: str, *, authed: bool = True) -> k.ChatScope:
    return k.ChatScope(
        key=f"u:{user}|d:{device}" if authed else f"d:{device}",
        user=user if authed else "anon",
        device=device,
        authed=authed,
    )


def _as(scope: k.ChatScope | None, fn):
    def run():
        if scope is not None:
            k.bind_scope(scope)
        return fn()

    return contextvars.copy_context().run(run)


@pytest.fixture()
def ortam(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RUZGAR_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.delenv("RUZGAR_PUBLIC_MODE", raising=False)
    monkeypatch.delenv("RUZGAR_KAPSAM_HAFIZA", raising=False)
    monkeypatch.delenv("RUZGAR_KAPSAM_HAFIZA_PC_KULLANICI", raising=False)
    pc_dosya = tmp_path / "pc" / "ruzgar_genel_hafiza.json"
    pc_dosya.parent.mkdir(parents=True)
    pc_dosya.write_text(
        json.dumps(
            [
                {"motor_tipi": "Hafıza", "soru": "ümit kimdir", "cevap": "AILE-OZEL-BILGI"},
                {"motor_tipi": "Egitim", "soru": "ortak selam tetik", "cevap": "ORTAK-EGITIM"},
                {"motor_tipi": "BilgiKutuphane", "soru": "ortak bilgi sorusu", "cevap": "ORTAK-BILGI"},
                {"motor_tipi": "OturumOzet", "soru": "pc oturum", "cevap": "PC-OTURUM-OZEL"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    pc = h.HafizaIRuzgar(dosya_yolu=pc_dosya)
    monkeypatch.setattr(h, "_hafiza_singleton", pc)
    kh._ONBELLEK.clear()
    yield {"pc": pc, "pc_dosya": pc_dosya, "tmp": tmp_path}
    kh._ONBELLEK.clear()


def test_pc_kapsami_eski_tekil_motoru_kullanir(ortam):
    m = _as(None, h.get_hafiza_motor)
    assert m is ortam["pc"]
    assert not (ortam["tmp"] / "data" / "kapsam_hafiza").exists()


def test_mobil_yazi_pc_dosyasina_gitmez(ortam):
    once = ortam["pc_dosya"].read_bytes()
    sc = _scope("ali", "tel")

    def yaz():
        m = h.get_hafiza_motor()
        m.ekle_bilgi("kedimin adı", "Pamuk", motor_tipi="Hafıza")
        return m

    m = _as(sc, yaz)
    assert isinstance(m, kh.KapsamHafiza)
    assert ortam["pc_dosya"].read_bytes() == once
    assert m.tum_bilgiler(motor_tipi="Hafıza") == {"kedimin adı": "Pamuk"}
    # PC tarafı mobil kaydı görmez
    assert "kedimin adı" not in ortam["pc"].tum_bilgiler(motor_tipi="Hafıza")


def test_pc_kisisel_raflari_mobilde_gorunmez(ortam):
    sc = _scope("ali", "tel")
    m = _as(sc, h.get_hafiza_motor)
    assert m.tum_bilgiler(motor_tipi="Hafıza") == {}
    assert m.tum_bilgiler(motor_tipi="OturumOzet") == {}
    assert m.ogrenme_cevabi_bak("ümit kimdir") is None
    assert m.ogrenme_cevabi_bak("pc oturum") is None


def test_ortak_raflar_mobilde_okunur(ortam):
    sc = _scope("ali", "tel")
    m = _as(sc, h.get_hafiza_motor)
    assert m.ogrenme_cevabi_bak("ortak selam tetik", motor_tipi="Egitim") == "ORTAK-EGITIM"
    assert m.ogrenme_cevabi_bak("ortak bilgi sorusu") == "ORTAK-BILGI"


def test_ortak_raf_kisisel_uzerine_yazma_pc_yi_bozmaz(ortam):
    once = ortam["pc_dosya"].read_bytes()
    sc = _scope("ali", "tel")
    m = _as(sc, h.get_hafiza_motor)
    m.ekle_bilgi("ortak selam tetik", "KISISEL-CEVAP", motor_tipi="Egitim")
    assert m.ogrenme_cevabi_bak("ortak selam tetik", motor_tipi="Egitim") == "KISISEL-CEVAP"
    assert ortam["pc_dosya"].read_bytes() == once
    assert ortam["pc"].ogrenme_cevabi_bak("ortak selam tetik", motor_tipi="Egitim") == "ORTAK-EGITIM"


def test_ortak_satir_mobilde_silinemez(ortam):
    sc = _scope("ali", "tel")
    m = _as(sc, h.get_hafiza_motor)
    assert m.sil_bilgi("ortak selam tetik", motor_tipi="Egitim") is False
    assert m.ogrenme_cevabi_bak("ortak selam tetik", motor_tipi="Egitim") == "ORTAK-EGITIM"
    assert ortam["pc"].ogrenme_cevabi_bak("ortak selam tetik", motor_tipi="Egitim") == "ORTAK-EGITIM"


def test_kisisel_sil_calisir_ve_ortak_geri_gelir(ortam):
    sc = _scope("ali", "tel")
    m = _as(sc, h.get_hafiza_motor)
    m.ekle_bilgi("ortak selam tetik", "KISISEL", motor_tipi="Egitim")
    assert m.sil_bilgi("ortak selam tetik", motor_tipi="Egitim") is True
    assert m.ogrenme_cevabi_bak("ortak selam tetik", motor_tipi="Egitim") == "ORTAK-EGITIM"


def test_iki_kullanici_birbirini_gormez(ortam):
    ali = _scope("ali", "tel")
    veli = _scope("veli", "tel")
    _as(ali, lambda: h.get_hafiza_motor().ekle_bilgi("sır", "ALI-SIR", motor_tipi="Hafıza"))
    mv = _as(veli, h.get_hafiza_motor)
    assert mv.tum_bilgiler(motor_tipi="Hafıza") == {}
    ma = _as(ali, h.get_hafiza_motor)
    assert ma.tum_bilgiler(motor_tipi="Hafıza") == {"sır": "ALI-SIR"}


def test_ayni_kullanici_iki_cihaz_ayni_hafiza(ortam):
    _as(_scope("ali", "tel"), lambda: h.get_hafiza_motor().ekle_bilgi("not", "N1", motor_tipi="Hafıza"))
    m2 = _as(_scope("ali", "tablet"), h.get_hafiza_motor)
    assert m2.tum_bilgiler(motor_tipi="Hafıza") == {"not": "N1"}


def test_cihaz_ipucu_ve_gecersiz_token_ayri_kovalar(ortam):
    a = _as(_scope("x", "cihaz1", authed=False), h.get_hafiza_motor)
    b = _as(k.ChatScope(key="anon:abcd1234", user="anon", device="anon-abcd1234"), h.get_hafiza_motor)
    assert a is not b
    a.ekle_bilgi("q", "a", motor_tipi="Hafıza")
    assert b.tum_bilgiler(motor_tipi="Hafıza") == {}


def test_kisisel_dosya_kalici_ve_ortak_kopya_icermez(ortam):
    sc = _scope("ali", "tel")
    _as(sc, lambda: h.get_hafiza_motor().ekle_bilgi("kalıcı", "K1", motor_tipi="Hafıza"))
    dosyalar = list((ortam["tmp"] / "data" / "kapsam_hafiza").glob("*.json"))
    assert len(dosyalar) == 1
    ham = json.loads(dosyalar[0].read_text(encoding="utf-8"))
    assert [r["soru"] for r in ham] == ["kalıcı"]
    assert all("_ortak" not in r for r in ham)
    # önbellek temizlenince diskten geri okunur
    kh._ONBELLEK.clear()
    m = _as(sc, h.get_hafiza_motor)
    assert m.tum_bilgiler(motor_tipi="Hafıza") == {"kalıcı": "K1"}
    assert m.ogrenme_cevabi_bak("ortak selam tetik", motor_tipi="Egitim") == "ORTAK-EGITIM"
    assert not list((ortam["tmp"] / "data" / "kapsam_hafiza").glob("*.tmp"))


def test_pc_ortak_raf_degisince_mobil_gorur(ortam):
    sc = _scope("ali", "tel")
    m = _as(sc, h.get_hafiza_motor)
    assert m.ogrenme_cevabi_bak("yeni ortak", motor_tipi="Egitim") is None
    ortam["pc"].ekle_bilgi("yeni ortak", "YENI", motor_tipi="Egitim")
    assert m.ogrenme_cevabi_bak("yeni ortak", motor_tipi="Egitim") == "YENI"


def test_kapali_ise_eski_davranis(ortam, monkeypatch):
    monkeypatch.setenv("RUZGAR_KAPSAM_HAFIZA", "0")
    m = _as(_scope("ali", "tel"), h.get_hafiza_motor)
    assert m is ortam["pc"]


def test_pc_kullanici_opt_in(ortam, monkeypatch):
    monkeypatch.setenv("RUZGAR_KAPSAM_HAFIZA_PC_KULLANICI", "ali, veli")
    assert _as(_scope("ali", "tel"), h.get_hafiza_motor) is ortam["pc"]
    assert isinstance(_as(_scope("can", "tel"), h.get_hafiza_motor), kh.KapsamHafiza)


def test_cekirdek_tohum_mobil_kapsamda_bile_pc_ye_yazar(ortam, monkeypatch):
    from ilim_assistant import ruzgar_tek_beyin_hafiza_seed as seed

    monkeypatch.setattr(seed, "_SEEDED", False)
    sc = _scope("ali", "tel")
    sonuc = _as(sc, seed.ensure_core_hafiza_profiles)
    assert sonuc.get("ok") is True
    mm = _as(sc, h.get_hafiza_motor)
    # mobil kişisel dosyada tohum satırı yok
    assert mm.tum_bilgiler(motor_tipi="Hafıza") == {}
    assert len(ortam["pc"].tum_bilgiler(motor_tipi="Hafıza")) > 1


def test_kullanici_baglami_mobilde_pc_dosyasina_yazmaz(ortam, tmp_path, monkeypatch):
    from ilim_assistant import kullanici_baglami as kb

    pc_baglam = tmp_path / "pc" / "ruzgar_kullanici_baglami.json"
    orijinal = kb._path

    def pc_yol():
        # kullanici_baglami._path: kapsam yolu varsa o, yoksa (PC) eski dosya — burada tmp'ye yönlendirildi
        p = kh.baglam_yolu_veya_none()
        return p if p is not None else pc_baglam

    monkeypatch.setattr(kb, "_path", pc_yol)
    _as(_scope("ali", "tel"), lambda: kb.ingest_message("benim gizli test notum alfa bravo charlie"))
    assert not pc_baglam.exists()  # PC dosyasına dokunulmadı
    dosyalar = list((tmp_path / "data" / "kapsam_hafiza").glob("baglam_*.json"))
    assert len(dosyalar) == 1
    assert "gizli test notum" in dosyalar[0].read_text(encoding="utf-8")
    # PC kapsamı kişisel bağlamı görmez
    blok = _as(None, kb.build_context_block)
    assert "gizli test notum" not in blok
    monkeypatch.setattr(kb, "_path", orijinal)


def test_kullanici_baglami_gercek_yol_kapsama_gore(ortam):
    from ilim_assistant import kullanici_baglami as kb

    mobil = _as(_scope("ali", "tel"), kb._path)
    assert mobil.parent.name == "kapsam_hafiza" and mobil.name.startswith("baglam_")
    pc = _as(None, kb._path)
    assert pc.name == "ruzgar_kullanici_baglami.json" and pc.parent.name != "kapsam_hafiza"


def test_baglam_yolu_pc_ve_kapali_none(ortam, monkeypatch):
    assert _as(None, kh.baglam_yolu_veya_none) is None
    monkeypatch.setenv("RUZGAR_KAPSAM_HAFIZA", "0")
    assert _as(_scope("ali", "tel"), kh.baglam_yolu_veya_none) is None


def test_gecici_pc_dosya_bozuksa_kisisel_motor_calisir(ortam):
    sc = _scope("ali", "tel")
    m = _as(sc, h.get_hafiza_motor)
    m.ekle_bilgi("a", "b", motor_tipi="Hafıza")
    ortam["pc_dosya"].write_text("{bozuk", encoding="utf-8")
    assert m.tum_bilgiler(motor_tipi="Hafıza") == {"a": "b"}
