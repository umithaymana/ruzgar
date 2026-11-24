"""K1 (Kuzey Yıldızı) — ham pasaj dökümü varsayılan kapalı, hep sentez.

Geri alma: RUZGAR_KUTUPHANE_HAM_DOKUM=1 eski davranışı (ham döküm) geri getirir.
"""
from __future__ import annotations

import pytest

from ilim_assistant import chat_core
from ilim_assistant import ruzgar_kutuphane as kut
from ilim_assistant import ruzgar_kutuphane_gorev as gorev

BAYRAK = "RUZGAR_KUTUPHANE_HAM_DOKUM"

AR_HITS = [
    (
        "Elektroliz, bir elektrik akımıyla bileşiklerin ayrıştırılmasıdır. Anot ve katot "
        "elektrotlarında yükseltgenme ve indirgenme olur; örnek olarak suyun hidrojen ve oksijene "
        "ayrışması verilebilir.",
        "arsiv/kimya/elektroliz.md",
        0.61,
    )
]


@pytest.fixture(autouse=True)
def _temiz_env(monkeypatch):
    monkeypatch.delenv(BAYRAK, raising=False)
    monkeypatch.delenv("ENABLE_RAG_ARCHIVE_FAST", raising=False)


def _direkt(mesaj: str):
    return chat_core.try_archive_rag_direct_reply(
        mesaj, AR_HITS, coding_mode=False, mode_norm="genel"
    )


# --- 1) ham döküm varsayılan kapalı; bayrakla geri gelir -------------------------------------


def test_ham_dokum_varsayilan_kapali():
    assert gorev.ham_dokum_enabled() is False
    assert _direkt("Elektroliz nedir?") is None


def test_ham_dokum_bayrakla_geri_gelir(monkeypatch):
    monkeypatch.setenv(BAYRAK, "1")
    assert gorev.ham_dokum_enabled() is True
    out = _direkt("Elektroliz nedir?")
    assert out and "İlim Hazinesi" in out and "Elektroliz" in out


# --- 2) «kaynağı göster / pasajı oku / aslını göster» ham metni verir -------------------------


@pytest.mark.parametrize(
    "mesaj",
    [
        "Elektroliz pasajını oku",
        "elektroliz kaynağını göster",
        "Elektrolizin aslını göster",
        "elektroliz ham metni ver",
        "Elektroliz için ilgili pasajı göster",
    ],
)
def test_acik_istek_ham_metin_verir(mesaj):
    assert gorev.user_wants_raw_passage(mesaj) is True
    out = _direkt(mesaj)
    assert out and "elektroliz" in out.lower()


@pytest.mark.parametrize(
    "mesaj",
    ["Elektroliz nedir?", "Türev nasıl alınır?", "Fotosentezi anlatır mısın?", "Ümit abi merhaba"],
)
def test_normal_soru_ham_istek_sayilmaz(mesaj):
    assert gorev.user_wants_raw_passage(mesaj) is False


# --- 3) zayıf/ilgisiz bulgu kanıt paketine girmez ---------------------------------------------


def test_ilgisiz_eser_kanit_paketine_girmez():
    gunes = (
        "Astronomi ve Uzay 001_gunes_sistemi\n# Güneş Sistemi\nGüneş, Güneş Sisteminin "
        "merkezindeki sarı cüce yıldızdır. Gezegenler: Merkür, Venüs, Dünya, Mars."
    )
    assert gorev.kanit_metni_alakali_mi("Elektroliz nedir?", gunes) is False
    assert gorev.kanit_metni_alakali_mi("Sürtünme kuvveti nedir?", gunes) is False
    assert gorev.kanit_metni_alakali_mi("Güneş nedir?", gunes) is True


def test_kanit_suzgeci_cekim_ekine_dayanikli():
    metin = "Tüketici hakları: ayıplı mal, cayma hakkı ve haksız şartlar."
    assert gorev.kanit_metni_alakali_mi("Tüketicinin hakları nelerdir?", metin) is True


def test_kutuphane_baglami_ilgisiz_eser_dokmez(monkeypatch):
    ctx = kut.build_kutuphane_context("Elektroliz nedir?")
    assert "Güneş Sistemi" not in ctx
    ctx_alakali = kut.build_kutuphane_context("Güneş nedir?")
    assert "gunes_sistemi" in ctx_alakali
    # eski davranış: süzgeç kapalı
    monkeypatch.setenv(BAYRAK, "1")
    assert "gunes_sistemi" in kut.build_kutuphane_context("Elektroliz nedir?")


# --- 4) din/âlim alanı mührü + yönerge --------------------------------------------------------


def test_din_alani_ayrimi():
    assert gorev.din_alani_sorusu("Abdesti bozan şeyler nelerdir?") is True
    assert gorev.din_alani_sorusu("Namazın şartları nelerdir?") is True
    assert gorev.din_alani_sorusu("Fotosentez nasıl gerçekleşir?") is False
    assert gorev.din_alani_sorusu("Elektroliz nedir?") is False


def test_yonerge_kanitsiz_genel_bilgi_ile_surer():
    d = gorev.grounding_directive(want_source=False, source_count=0, din=False)
    assert "KANITSIZ SENTEZ" in d
    assert "uydurma" in d


def test_yonerge_din_kanitsiz_bulamadim_muhru_korunur():
    d = gorev.grounding_directive(want_source=False, source_count=0, din=True)
    assert "İNDEKS İSABETİ YOK" in d and "bulamadım" in d


def test_yonerge_kanit_paketi_sentez_ve_kaynak_cumle_icinde():
    d = gorev.grounding_directive(want_source=False, source_count=2, din=False)
    assert "KANIT PAKETİ" in d
    assert "cümle içinde" in d
    assert "adıyla anan" in d
    assert "aynen yapıştırma" in d


def test_yonerge_bayrakla_eski_metne_doner(monkeypatch):
    monkeypatch.setenv(BAYRAK, "1")
    d = gorev.grounding_directive(want_source=False, source_count=0, din=False)
    assert "İNDEKS İSABETİ YOK" in d


# --- 5) uçtan uca: prepare_turn ---------------------------------------------------------------


_ILGISIZ_HIT = [
    (
        "Güneş Sistemi sekiz gezegenden oluşur; Merkür Güneş'e en yakın gezegendir ve yörüngesi "
        "en kısa olandır. Dünya üçüncü gezegendir.",
        "knowledge/ilim/gokbilim/gunes_sistemi.md",
        0.55,
    )
]


@pytest.fixture
def _hermetik_arama(monkeypatch):
    """Gerçek indeksten bağımsız: «Elektroliz» için yalnız ilgisiz bir bulgu döner (K1 senaryosu)."""
    from ilim_assistant import rag_store

    monkeypatch.setattr(rag_store, "search", lambda q, top_k=5: list(_ILGISIZ_HIT))
    monkeypatch.setattr(chat_core, "search", lambda q, top_k=5: list(_ILGISIZ_HIT))
    monkeypatch.setattr(rag_store, "search_arsiv", lambda q, top_k=5: [])
    monkeypatch.setattr(chat_core, "search_tdk_exact_lemma", lambda lemma, top_k=5: [])
    monkeypatch.setattr(chat_core, "search_tarih_hafiza", lambda q, top_k=5, scan_cap=96: [])


def _hazirla(mesaj: str):
    return chat_core.prepare_turn(
        mesaj, [], False, 0.0, False, False, mode="genel", orchestration_out={}
    )


def test_prepare_turn_ilgisiz_bulgu_ham_dokulmez_zincir_surer(_hermetik_arama):
    _msg, _hits, payload, _system, _model, direct = _hazirla("Elektroliz nedir?")
    assert not direct  # ham döküm / sabit cevap yok → LLM zinciri çalışacak
    assert "Güneş Sistemi" not in payload
    assert "RÜZGAR KÜTÜPHANESİ" not in payload
    assert "KANITSIZ SENTEZ" in payload


def test_prepare_turn_bayrakla_eski_ham_dokum_gelir(monkeypatch, _hermetik_arama):
    monkeypatch.setenv(BAYRAK, "1")
    o: dict = {}
    r = chat_core.prepare_turn(
        "Elektroliz nedir?", [], False, 0.0, False, False, mode="genel", orchestration_out=o
    )
    direct = r[5]
    assert direct and "kütüphaneden okuduğum pasaj" in direct
    assert o.get("provider") == "kutuphane_extractive"

