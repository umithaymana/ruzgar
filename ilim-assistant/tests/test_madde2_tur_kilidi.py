"""Madde 2.4 / 2.6 — tur kilidi (turn_id) + ses telemetrisi birim testleri."""

from __future__ import annotations

import pytest

from ilim_assistant import ses_tur_kilidi as tk


@pytest.fixture(autouse=True)
def _izole(monkeypatch):
    monkeypatch.delenv("RUZGAR_SES_TUR_KILIDI", raising=False)
    monkeypatch.delenv("RUZGAR_SES_TELEMETRI", raising=False)
    tk.sifirla_test()
    yield
    tk.sifirla_test()


def test_temiz_id_ve_kanal():
    assert tk.temiz_id("t-1_a.b:c") == "t-1_a.b:c"
    assert tk.temiz_id("ç ş") == ""
    assert tk.temiz_id("x" * 65) == ""
    assert tk.kanal_anahtari(None, None) == "pc"
    a = tk.kanal_anahtari("dev_1", None)
    assert a.startswith("k") and "dev_1" not in a  # ham kimlik sızmaz
    assert tk.kanal_anahtari("dev_1", None) == a
    assert tk.kanal_etiketi(None, None) == "pc"
    assert tk.kanal_etiketi("dev_1", None) == "mobil"
    assert tk.kanal_etiketi(None, "tok") == "mobil"


def test_yeni_tur_eskisini_iptal_eder():
    k = tk.kanal_anahtari("dev_1")
    r1 = tk.begin(k, "tur-1")
    assert r1["ok"] and r1["onceki_iptal"] is None
    assert tk.durum("tur-1", k) == "ok"
    r2 = tk.begin(k, "tur-2")
    assert r2["onceki_iptal"] == "tur-1"
    assert tk.durum("tur-1", k) == "iptal"
    assert tk.durum("tur-2", k) == "ok"
    ok, neden = tk.tts_izin("tur-1", k)
    assert ok is False and neden == "iptal"
    ok2, _ = tk.tts_izin("tur-2", k)
    assert ok2 is True


def test_kanallar_birbirini_etkilemez():
    a, b = tk.kanal_anahtari("dev_a"), tk.kanal_anahtari("dev_b")
    tk.begin(a, "ta")
    tk.begin(b, "tb")
    assert tk.durum("ta", a) == "ok" and tk.durum("tb", b) == "ok"


def test_barge_iptal_ve_onceden_iptal_yarisi():
    k = tk.kanal_anahtari("dev_1")
    tk.begin(k, "t1")
    assert tk.cancel("t1", kanal=k) == ["t1"]
    assert tk.durum("t1", k) == "iptal"
    # henüz görülmemiş tur için iptal gelirse sonradan gelen TTS reddedilir
    assert tk.cancel("t-gelecek", kanal=k) == ["t-gelecek"]
    tk.begin(k, "t-gelecek")
    assert tk.durum("t-gelecek", k) == "iptal"
    # kanal bazlı iptal (turn_id verilmeden)
    tk.begin(k, "t2")
    assert tk.cancel(None, kanal=k) == ["t2"]
    assert tk.durum("t2", k) == "iptal"
    # idempotent
    assert tk.cancel("t2", kanal=k) == []


def test_eski_tur_kanal_aktifi_degisince():
    k = tk.kanal_anahtari("dev_1")
    tk.begin(k, "a")
    tk.begin(k, "b")
    # 'a' zaten iptal edildi; yine de kanal aktifi farklıysa 'eski' ya da 'iptal' — çalınmaz
    assert tk.durum("a", k) in ("iptal", "eski")


def test_turn_id_yok_veya_kilit_kapali_hep_ok(monkeypatch):
    assert tk.durum("", "k") == "ok"
    assert tk.durum(None, None) == "ok"
    assert tk.tts_izin("", None) == (True, "ok")
    monkeypatch.setenv("RUZGAR_SES_TUR_KILIDI", "0")
    k = tk.kanal_anahtari("dev_1")
    tk.begin(k, "x1")
    tk.begin(k, "x2")
    assert tk.durum("x1", k) == "ok"
    assert tk.cancel("x2", kanal=k) == []


def test_bellek_sinirli_ve_ttl(monkeypatch):
    k = tk.kanal_anahtari("dev_1")
    for i in range(tk._MAX_TURN + 40):
        tk.begin(f"k{i % 7}", f"t{i}")
    assert len(tk._turns) <= tk._MAX_TURN
    # TTL: eski kayıtlar budanır
    tk.sifirla_test()
    tk.begin(k, "eski")
    tk._turns["eski"]["t"] -= tk._TTL_SEC + 5
    tk.begin(k, "yeni")
    assert "eski" not in tk._turns


def test_telemetri_kisisel_veri_yok_ve_ayri_metrikler():
    tk.tel_kaydet(kanal="mobil", kaynak="istemci", ilk_token_ms=420, ilk_ses_ms=980, ilk_ses_yolu="akis", parca=3)
    tk.tel_kaydet(kanal="mobil", kaynak="sunucu", ilk_token_ms=300)
    tk.tel_kaydet(kanal="pc", kaynak="sunucu", ilk_token_ms=150)
    tk.tel_kaydet(kanal="tts", kaynak="sunucu", tts_ilk_bayt_ms=700)
    assert tk.tel_kaydet(kanal="mobil") is None  # boş kayıt yazılmaz
    assert tk.tel_kaydet(kanal="mobil", ilk_token_ms=-5) is None  # geçersiz sayı
    assert tk.tel_kaydet(kanal="mobil", ilk_token_ms="abc") is None
    oz = tk.tel_ozet()
    assert oz["kayit"] == 4
    assert oz["ilk_token_ms"]["istemci"]["n"] == 1
    assert oz["ilk_token_ms"]["sunucu"]["n"] == 2
    assert oz["ilk_ses_ms"]["n"] == 1 and oz["ilk_ses_ms"]["son"] == 980.0
    assert oz["ilk_ses_ms"]["alti_1sn"] == 1.0
    assert oz["tts_ilk_bayt_ms"]["son"] == 700.0
    assert set(oz["kanallar"]) == {"mobil", "pc", "tts"}
    # kişisel veri alanı yok
    blob = repr(oz)
    for yasak in ("session", "token\":", "kullanici", "device_id", "text"):
        assert yasak not in blob.replace("ilk_token_ms", "")


def test_telemetri_kanal_etiketi_temizlenir():
    r = tk.tel_kaydet(kanal="MOBİL<script>", kaynak="istemci", ilk_token_ms=10)
    assert r is not None and r["kanal"].replace("_", "").isalnum()


def test_telemetri_kapali(monkeypatch):
    monkeypatch.setenv("RUZGAR_SES_TELEMETRI", "0")
    assert tk.tel_kaydet(kanal="pc", ilk_token_ms=10) is None
    assert tk.tel_ozet()["kayit"] == 0
