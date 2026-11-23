"""STT doğruluk katmanı — güven puanı, halüsinasyon temizliği, ayar varsayılanları."""

from __future__ import annotations

import pytest

from ilim_assistant import stt_whisper as sw


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for ad in (
        "RUZGAR_WHISPER_BEAM",
        "RUZGAR_WHISPER_TEMP_FALLBACK",
        "RUZGAR_WHISPER_PROMPT",
        "RUZGAR_STT_LOGPROB_MIN",
        "RUZGAR_STT_NO_SPEECH_MAX",
    ):
        monkeypatch.delenv(ad, raising=False)


def test_guven_yuksek_net_konusma():
    g, dusuk = sw.degerlendir_guven([(2.0, -0.2, 0.01), (1.5, -0.3, 0.02)])
    assert g is not None and g > 0.7
    assert dusuk is False


def test_guven_dusuk_logprob_isaretlenir():
    g, dusuk = sw.degerlendir_guven([(3.0, -1.6, 0.1)])
    assert g is not None and g < 0.25
    assert dusuk is True


def test_guven_konusma_yok_ihtimali_isaretlenir():
    _, dusuk = sw.degerlendir_guven([(2.0, -0.3, 0.92)])
    assert dusuk is True


def test_guven_sure_agirlikli():
    # uzun net parça kısa kötü parçayı bastırır
    _, dusuk = sw.degerlendir_guven([(6.0, -0.2, 0.0), (0.3, -2.5, 0.0)])
    assert dusuk is False


def test_guven_veri_yoksa_bilinmez():
    assert sw.degerlendir_guven([]) == (None, False)
    assert sw.degerlendir_guven([(1.0, None, None)]) == (None, False)


def test_guven_esik_env_ile_ayarlanir(monkeypatch):
    monkeypatch.setenv("RUZGAR_STT_LOGPROB_MIN", "-0.1")
    _, dusuk = sw.degerlendir_guven([(2.0, -0.3, 0.0)])
    assert dusuk is True


def test_halusinasyon_temizligi():
    assert sw.temizle_halusinasyon("Altyazı M.K.") == ""
    assert sw.temizle_halusinasyon("İzlediğiniz için teşekkürler.") == ""
    assert sw.temizle_halusinasyon("Yarın hava nasıl olacak?") == "Yarın hava nasıl olacak?"
    # gerçek cümlenin içindeki «teşekkürler» silinmez
    assert sw.temizle_halusinasyon("Teşekkürler Rüzgar") == "Teşekkürler Rüzgar"


def test_ipucu_yankisi_temizlenir():
    ip = sw.stt_baglam_ipucu()
    assert ip
    assert sw.temizle_halusinasyon(ip + " Merhaba", ip) == "Merhaba"


def test_varsayilan_ayarlar_dogru():
    kw = sw.build_transcribe_kwargs("tr", duration_sec=3.0)
    assert kw["beam_size"] == 3
    assert kw["temperature"] == (0.0, 0.2, 0.4)  # güvensiz çözümde yedek sıcaklık
    assert kw["initial_prompt"]
    assert kw["language"] == "tr"
    assert kw["condition_on_previous_text"] is False


def test_eski_davranisa_env_ile_donulur(monkeypatch):
    monkeypatch.setenv("RUZGAR_WHISPER_BEAM", "1")
    monkeypatch.setenv("RUZGAR_WHISPER_TEMP_FALLBACK", "0")
    monkeypatch.setenv("RUZGAR_WHISPER_PROMPT", "0")
    kw = sw.build_transcribe_kwargs("tr", duration_sec=3.0)
    assert kw["beam_size"] == 1
    assert kw["temperature"] == 0.0
    assert "initial_prompt" not in kw


def test_sonuc_sozlugu_guven_alanlarini_tasir():
    r = sw.TranscribeResult(text="x", language="tr", segments=[], guven=0.8, dusuk_guven=True)
    d = r.to_dict()
    assert d["guven"] == 0.8 and d["dusuk_guven"] is True
