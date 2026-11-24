"""K2 üslup + din sorusunun Arapça lugata/anlık karta kaçmaması."""
from ilim_assistant.ruzgar_arapca_lugat import looks_like_arapca_lugat_question, try_arapca_lugat_reply
from ilim_assistant.ruzgar_k2_uslup import (
    PROFIL_ALIM,
    PROFIL_SADE,
    PROFIL_SOHBET,
    uslup_directive,
    uslup_profili,
)
from ilim_assistant.ruzgar_kutuphane_gorev import user_wants_kaynak


def test_din_akaid_lugata_dusmez():
    for q in (
        "Allah'ın sıfatları nelerdir, zâtî ve sübûtî sıfatlar ne demektir?",
        "Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür?",
        "İhlâs Sûresi'nin anlamı nedir?",
    ):
        assert looks_like_arapca_lugat_question(q) is False, q
        assert try_arapca_lugat_reply(q) is None, q


def test_acik_lugat_sorusu_kalir():
    q = "selam kökü nedir lugat"
    assert looks_like_arapca_lugat_question(q) is True


def test_kaynak_goster_tespit():
    assert user_wants_kaynak("Hicret nedir? Kaynak göster, hangi siyer kitabında geçer?")
    assert user_wants_kaynak("Tevhid nedir, kaynak göster")
    assert not user_wants_kaynak("Nasılsın Rüzgar?")


def test_k2_din_alim_profili():
    assert uslup_profili("Abdesti bozan şeyler nelerdir?") == PROFIL_ALIM
    assert uslup_profili("Fotosentez nedir?") == PROFIL_SADE
    d = uslup_directive(PROFIL_ALIM)
    assert "ÂLİM" in d
    assert "vaaz" in d.lower() or "Vaaz" in d
    assert "vakur" in d.lower()


def test_k2_kapatma(monkeypatch):
    monkeypatch.setenv("RUZGAR_K2_USLUP", "0")
    assert uslup_directive(PROFIL_ALIM) == ""
    assert uslup_profili("Abdesti bozan şeyler nelerdir?") == PROFIL_SADE
