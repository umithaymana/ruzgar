# Created by Ümit & Gökçenur
"""«Yanlış, doğrusu şu» son soruya yazılır ve kartın önüne geçer."""

from ilim_assistant import ruzgar_egitim as eg


class _Raf:
    def __init__(self):
        self._kayitlar = []

    def ekle_bilgi(self, soru, cevap, motor_tipi="Hafıza"):
        self._kayitlar.append(
            {"soru": soru, "cevap": cevap, "motor_tipi": motor_tipi}
        )
        return "ok"


def _disk_yok(monkeypatch, raf):
    monkeypatch.setattr(eg, "_load_durum", lambda: {})
    monkeypatch.setattr(eg, "_save_durum", lambda _data: None)
    monkeypatch.setattr(
        "ilim_assistant.hafiza_i_ruzgar.get_hafiza_motor", lambda: raf
    )


def test_yanlis_dogrusu_cumlesi_ayrilir():
    govde = eg._extract_dogrusu_su_body(
        "yanlış, doğrusu şu: Samanyolu'nda yüz milyarlarca yıldız vardır"
    )
    assert govde == "Samanyolu'nda yüz milyarlarca yıldız vardır"
    assert eg.is_wrong_answer_trigger(
        "yanlış, doğrusu şu: Samanyolu'nda yüz milyarlarca yıldız vardır"
    )


def test_duzeltme_saklanir_ve_karttan_once_soylenir(monkeypatch):
    raf = _Raf()
    _disk_yok(monkeypatch, raf)
    gecmis = [{"role": "user", "content": "dünyamız hangi galaksıde yer alır"}]
    yanit = eg.try_consume_egitim_command(
        "yanlış, doğrusu şu: Samanyolu'nda yüz milyarlarca yıldız vardır",
        gecmis,
    )
    assert yanit
    assert "kaydettim" in yanit
    assert any(r["motor_tipi"] == "EgitimDuzeltme" for r in raf._kayitlar)
    bulunan = eg.lookup_onayli_duzeltme("dünyamız hangi galakside yer alır")
    assert bulunan == "Samanyolu'nda yüz milyarlarca yıldız vardır"


def test_gundelik_laf_duzeltme_rafina_yazilmaz(monkeypatch):
    raf = _Raf()
    _disk_yok(monkeypatch, raf)
    assert eg.lookup_onayli_duzeltme("sen kimsin") is None
    assert not any(r["motor_tipi"] == "EgitimDuzeltme" for r in raf._kayitlar)
