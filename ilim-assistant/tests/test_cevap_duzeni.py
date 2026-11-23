# Created by Ümit & Gökçenur
"""Genel sohbet talimatı sonuçla başlar ve görmediğini uydurmaz."""

from ilim_assistant.prompts import pick_system


def test_genel_sohbet_kisa_prompt_kimlik_ve_uydurmama(monkeypatch):
    """Varsayılan (kısa) prompt: kimlik, doğrudan cevap, uydurmama."""
    monkeypatch.setenv("RUZGAR_SOHBET_COMPACT_PROMPT", "1")
    metin = pick_system(False, "genel").lower()
    assert "yapay zeka asistanı" in metin
    assert "esinti veya fırtına değilsin" in metin
    assert "doğrudan cevapla başla" in metin
    assert "uydurma" in metin


def test_genel_sohbet_cevap_duzeni_sonda(monkeypatch):
    # Uzun prompt yolu (kısa prompt kapalı): kural sonda durur.
    monkeypatch.setenv("RUZGAR_SOHBET_COMPACT_PROMPT", "0")
    metin = pick_system(False, "genel")
    kural = "İlk cümle sorunun sonucu olsun."
    assert kural in metin
    assert metin.rfind(kural) > metin.rfind("Sohbet düzeni")
    assert "bu sorunun cevabını bulamadım" in metin
    assert "Sayı, kişi adı ve dosya içeriği" in metin


def test_kod_odasi_cevap_duzenini_almaz():
    metin = pick_system(True, "programlama")
    assert "İlk cümle sorunun sonucu olsun." not in metin


def test_gundelik_kisa_talimat_yapay_zeka_kimligi():
    from ilim_assistant.ana_motor_casual import _casual_system_and_user

    sistem, *_kalan = _casual_system_and_user("sevdiğin birisi var mı", "genel")
    assert "yapay zeka asistanı" in sistem.lower()
    assert "esinti veya fırtına değilsin" in sistem.lower()
    assert "hava değilsin" in sistem.lower()
