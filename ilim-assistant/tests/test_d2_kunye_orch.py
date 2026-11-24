"""D2 — orchestration künye notları silinmesin; Kaynak izi kanıttan gelsin."""
from ilim_assistant.idrak_entegrasyon import append_idrak_agent_layer
from ilim_assistant.ruzgar_kunye import cevap_kaynak_izi_uygula, strip_kaynak_izi


def test_idrak_orch_rag_notlarini_silmez():
    orch = {
        "hits_count": 3,
        "kaynak_kunye": [{"eser_ar": "بدائع الصنائع", "yazar_ar": "الكاساني"}],
        "kutuphane_usable": True,
        "k3": {"ar_query": "صلاة الجمعة"},
    }
    append_idrak_agent_layer(
        "merhaba",
        "Cuma namazı nasıl kılınır?",
        "genel",
        [("x", "shamela_1.md", 0.9)],
        False,
        True,
        orchestration_out=orch,
    )
    assert orch["hits_count"] == 3
    assert orch["kaynak_kunye"][0]["eser_ar"] == "بدائع الصنائع"
    assert orch["kutuphane_usable"] is True
    assert orch["k3"]["ar_query"] == "صلاة الجمعة"
    assert "motors" in orch
    assert "query" in orch


def test_uydurma_kaynak_izi_kanitla_degisir():
    fake = (
        "Cuma namazı hutbeden sonra kılınır.\n\n"
        "Kaynak izi:\n"
        "- [K1] Uydurma Kitap — Uydurma Yazar\n"
    )
    real = [{"eser_ar": "بدائع الصنائع", "yazar_ar": "الكاساني"}]
    out = cevap_kaynak_izi_uygula(fake, real)
    assert "Uydurma Kitap" not in out
    assert "بدائع الصنائع" in out
    assert out.count("Kaynak izi") == 1


def test_strip_kaynak_izi_bos_kunyede():
    fake = "Cevap metni.\n\nKaynak izi:\n[K1] Yok\n"
    assert "Kaynak izi" not in strip_kaynak_izi(fake)
    assert cevap_kaynak_izi_uygula(fake, []) == "Cevap metni."
