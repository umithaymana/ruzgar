"""Dört masa cümlesi sunucuda da aynı eyleme çözülür. Model dosya yazmaz."""

from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
from ilim_assistant.ruzgar_masa_soz import coz, masa_sohbet_yaniti


def test_dort_masa_cumlesi_eyleme_cozulur():
    assert coz("belgeye selam mimar yaz") == {"eylem": "belge.yaz", "metin": "selam mimar"}
    assert coz("belgeye bir satır daha ekle") == {"eylem": "belge.ekle", "metin": "bir satır daha"}
    assert coz("belgeye yaz: selam") is None
    assert coz("tabloda A1 e 10 yaz") == {"eylem": "tablo.hucre", "hucre": "A1", "deger": "10"}
    assert coz("tablo A1 = 10") is None
    assert coz("çizime kutu çiz") == {"eylem": "cizim.kutu", "x": 80, "y": 80, "w": 240, "h": 140}
    assert coz("çizime çizgi çiz")["eylem"] == "cizim.cizgi"
    assert coz("çizime daire çiz")["eylem"] == "cizim.daire"
    assert coz("sunuma Hoş geldin slaytı ekle: bugün deneme") == {
        "eylem": "sunum.ekle",
        "baslik": "Hoş geldin",
        "metin": "bugün deneme",
    }
    assert coz("menüyü lacivert yap") is None
    assert coz("çizgi 40 40 400 200") is None
    assert coz("python nedir") is None
    assert coz("hesap.py ne yapıyor") is None


def test_masa_zinciri_bak_ve_red():
    kabul = "belgeye selam yaz, tabloda A1 e 10 yaz, çizime kutu çiz, sunuma Hoş geldin slaytı ekle: bugün"
    liste = coz(kabul)
    assert [adim["eylem"] for adim in liste["liste"]] == [
        "belge.yaz",
        "tablo.hucre",
        "cizim.kutu",
        "sunum.ekle",
    ]
    assert liste["liste"][0]["metin"] == "selam"
    assert liste["liste"][1]["hucre"] == "A1"
    assert liste["liste"][3]["baslik"] == "Hoş geldin"
    assert coz("belgeye bak ve söyle") == {"bak": "belge"}
    assert coz("çizime bak ve söyle") == {"bak": "cizim"}
    assert coz("belgede selam yerine merhaba yaz") == {
        "eylem": "belge.yerine",
        "eski": "selam",
        "yeni": "merhaba",
    }
    assert coz("A1 hücresini sil") == {"eylem": "tablo.sil", "hucre": "A1"}
    assert coz("A sütununu topla") == {"eylem": "tablo.topla", "sutun": "A"}
    assert coz("çizime mavi kutu çiz")["renk"] == "mavi"
    assert coz("slaytın başlığını Hoş geldin yap") == {"eylem": "sunum.baslik", "baslik": "Hoş geldin"}
    assert coz("belgeyi temizle") == {"eylem": "belge.temizle"}
    assert coz("çizime ortaya mavi kutu çiz")["x"] == 680
    assert coz("belgeye bak ve söyle, belgeye selam yaz") == {"red": True}
    assert coz("masayı baştan tasarla") == {"red": True}
    assert coz("belgeye selam yaz, şunu uydur") == {"red": True}
    assert coz("belgeye selam yaz.") == {"eylem": "belge.yaz", "metin": "selam"}
    assert coz("tabloda A1 e 10 yaz.") == {"eylem": "tablo.hucre", "hucre": "A1", "deger": "10"}
    assert coz("çizime kutu çiz.")["eylem"] == "cizim.kutu"
    assert coz("sunuma Hoş geldin slaytı ekle: bugün.")["metin"] == "bugün"
    assert coz("belgeye 3.14 yaz") == {"eylem": "belge.yaz", "metin": "3.14"}


def test_masa_sohbeti_modelden_once_durur():
    yanit = masa_sohbet_yaniti("belgeye selam yaz")
    assert yanit
    assert "Model dosya yazmadı" in yanit
    red = masa_sohbet_yaniti("masayı baştan tasarla")
    assert red
    assert "Masa değişmedi" in red
    assert masa_sohbet_yaniti("python os modülü ne işe yarar") is None
    assert is_code_agent_task_message("belgeye selam yaz", "programlama") is False
    assert is_code_agent_task_message("çizime kutu çiz", "programlama") is False
