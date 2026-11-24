"""D2 — aynı kitaptan yığılma yerine birkaç eser; künye metni kanıttan üretilir."""
from ilim_assistant.ruzgar_kunye import cesitlendir_eser, kaynak_izi_metni


def test_cesitlendir_farkli_eser():
    hits = [
        ("a", "shamela/shamela_1/incremental/a.md", 0.9),
        ("b", "shamela/shamela_1/incremental/b.md", 0.8),
        ("c", "shamela/shamela_2/incremental/c.md", 0.7),
        ("d", "shamela/shamela_3/incremental/d.md", 0.6),
    ]
    out = cesitlendir_eser(hits, limit=4)
    ids = [h[1] for h in out]
    assert len(out) == 3
    assert ids[0].endswith("a.md")
    assert "shamela_2" in ids[1]
    assert "shamela_3" in ids[2]


def test_kaynak_izi_eser_adi():
    metin = kaynak_izi_metni(
        [{"eser_ar": "بدائع الصنائع", "yazar_ar": "الكاساني"}, {"eser_ar": "", "yol_adi": ""}]
    )
    assert "Kaynak izi" in metin
    assert "بدائع الصنائع" in metin
    assert "الكاساني" in metin
    assert kaynak_izi_metni([]) == ""
