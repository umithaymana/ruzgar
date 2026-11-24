"""D1 — Din altın seti + din ölçütleri (sunucu gerekmez)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import altin_set_kos as k  # noqa: E402
import din_olcut as d  # noqa: E402


def _din():
    return [x for x in k.yukle_sorular() if x["raf"] == "din"]


def test_din_rafi_en_az_80_ve_ilk_20_korundu():
    s = _din()
    assert len(s) >= 80
    ilk = s[:20]
    assert ilk[0]["soru"] == "Abdesti bozan şeyler nelerdir?"
    assert ilk[19]["soru"] == "Vitir namazı nedir?"
    assert all(x["alt"] == "" for x in ilk)  # eski sorular meta almadı


def test_din_kapsam_alt_raflar_ve_kaynak_varyantlari():
    s = _din()[20:]
    alt = {x["alt"] for x in s}
    for a in ("akaid", "tasavvuf", "fikih", "hadis", "tefsir", "siyer", "tarih", "kissa"):
        assert a in alt, a
    assert sum(1 for x in s if x["kaynak_iste"]) >= 10
    assert sum(1 for x in s if x["cizgi"]) >= 5
    assert sum(1 for x in s if x["alt"] == "tasavvuf") >= 15
    # her kaynak varyantı soru metninde açıkça kaynak ister
    for x in s:
        if x["kaynak_iste"]:
            assert "kayna" in x["soru"].lower()


def test_atif_denetimi_dogrulanan_ve_supheli():
    kun = [{"eser_id": "shamela_9849", "eser_ar": "الفقه على المذاهب الأربعة", "yazar": "Abdurrahman el-cziri",
            "yazar_ar": "عبد الرحمن الجزيري", "eser_tr": "Dört Mezhebe Göre Fıkıh"}]
    iyi = "Abdesti bozanlar el-Fıkh ale'l-Mezâhibi'l-Erbaa adlı eserde sayılır.\n\n**Kaynak izi:**\n- [K1] الفقه على المذاهب الأربعة — عبد الرحمن الجزيري"
    r = d.kaynak_denetim(iyi, kun, "Abdesti bozan şeyler nelerdir?")
    assert r["kunye_var"] and r["eser_sayisi"] == 1 and not r["supheli"]
    kotu = "**Kaynak izi:**\n- [K1] Hâfız Sahte, Uydurma Eser adlı kitap"
    r2 = d.kaynak_denetim(kotu, kun, "Abdesti bozan şeyler nelerdir?")
    assert r2["supheli"] and not r2["kunye_var"]


def test_atif_yoksa_supheli_sayilmaz_ve_kanitsiz_atif_supheli():
    r = d.kaynak_denetim("Abdest, namaz için temizliktir.", [], "Abdest nedir?")
    assert r["atif_sayisi"] == 0 and not r["supheli"]
    r2 = d.kaynak_denetim("Bu bilgi Nevevî'nin el-Mecmû' adlı eserinde geçer.", [], "Abdest nedir?")
    assert r2["supheli"], r2


def test_din_ozet_kaynak_ve_coklu_eser():
    kun = [{"eser_id": "a1", "eser_ar": "الفقه على المذاهب الأربعة", "yazar_ar": "عبد الرحمن الجزيري"},
           {"eser_id": "b2", "eser_ar": "قواعد العقائد", "yazar_ar": "أبو حامد الغزالي", "yazar": "Ebu Hamid Gazali"}]
    cevap = "El-Fıkh ale'l-Mezâhib'e göre ... Gazâlî'nin Kavâidü'l-Akâid adlı eserinde ise ...\n**Kaynak izi:**\n- [K1] الفقه على المذاهب الأربعة\n- [K2] قواعد العقائد"
    rows = [{"id": "din-21", "raf": "din", "soru": "Q", "cevap": cevap, "kapsama": 1.0, "gecti": True,
             "bulamadim": False, "kaynak_iste": True, "alt": "fikih", "kaynak_kunye": kun,
             "gecikme_sn": 1.0, "saglayici": "gemini", "din": d.kaynak_denetim(cevap, kun, "Q")}]
    o = k.din_ozet(rows)
    assert o["kaynak_verme_pct"] == 100.0 and o["coklu_eser_pct"] == 100.0 and o["uydurma_supheli_soru"] == 0
