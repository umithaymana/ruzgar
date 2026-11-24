"""K3 (din odaklı ilk dilim) — TR→AR sorgu genişletme, sözlük bütünlüğü, kelime tabanlı sıralama, künye (sunucu gerekmez)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from ilim_assistant import ruzgar_k3_sorgu as k3
from ilim_assistant import ruzgar_kunye as kn

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _k3_acik(monkeypatch):
    monkeypatch.delenv("RUZGAR_K3_DIN_SORGU", raising=False)
    monkeypatch.delenv("RUZGAR_KUNYE", raising=False)


def _ids(p):
    return [x["id"] for x in p.kavramlar]


def test_dil_tespiti_tr_ar_en():
    assert k3.dil_tespit("Abdesti bozan şeyler nelerdir?") == "tr"
    assert k3.dil_tespit("نواقض الوضوء ما هي") == "ar"
    assert k3.dil_tespit("What are the nullifiers of ablution?") == "en"


def test_tr_soru_arapca_terime_genisler():
    p = k3.plan_for_query("Abdesti bozan şeyler nelerdir?")
    assert p is not None and p.aktif and p.hedef_dil == "ar" and p.kaynak_dil == "tr"
    assert "abdest_bozan" in _ids(p)
    assert "نواقض الوضوء" in p.sorgular["ar"]
    assert p.kategoriler and p.kelime_terimleri


def test_cekim_ekine_dayanikli_eslesme():
    for q in ("Zekât kimlere verilir?", "zekâtın kimlere verileceği nedir"):
        p = k3.plan_for_query(q)
        assert p is not None and "zekat_sarf" in _ids(p), q


def test_dil_bagimsiz_alanlar_ve_en_sorgu():
    p = k3.plan_for_query("What invalidates wudu? nullifiers of wudu")
    # EN sözlük biçimi de kavrama bağlanır (kaynak dil en, hedef ar)
    assert p is not None and p.kaynak_dil == "en" and p.hedef_dil == "ar"
    assert p.ozet()["kaynak_dil"] == "en"
    # kaynak dili = hedef dil ise genişletme yok
    assert k3.plan_for_query("نواقض الوضوء") is None


def test_din_disi_sorular_tetiklemez():
    for q in ("Fotosentez nedir?", "Dünyanın en uzun nehri hangisidir?", "Kalp kaç odacıklıdır?",
              "Atatürk ne zaman vefat etti?", "Medeni hukuk ile ceza hukuku arasındaki fark nedir?",
              "Yunus Emre kimdir?", "Kıdem tazminatı nedir?", "Osmanlı tarihi nedir?"):
        p = k3.plan_for_query(q)
        assert p is None or not p.aktif, (q, p and p.ozet())


def test_kapatma_bayragi(monkeypatch):
    monkeypatch.setenv("RUZGAR_K3_DIN_SORGU", "0")
    assert k3.plan_for_query("Abdesti bozan şeyler nelerdir?") is None
    assert k3.kanit_dil_notu([("المسألة الفقهية في الوضوء والصلاة", "x")]) == ""


def test_sozluk_butunlugu_ve_hardcode_yasagi():
    d = json.loads((ROOT / "data" / "terim_sozlugu" / "din.json").read_text(encoding="utf-8"))
    ids = [g["id"] for g in d["girdiler"]]
    assert len(ids) == len(set(ids)) and len(ids) >= 300
    for g in d["girdiler"]:
        assert g["tr"] and g["ar"] and isinstance(g.get("w", 1.0), (int, float)), g["id"]
        assert any(re.search(r"[\u0600-\u06FF]", a) for a in g["ar"]), g["id"]
    # alan başına yeterli kapsam
    alanlar = {g["alan"] for g in d["girdiler"]}
    for a in ("fikih", "akaid", "tasavvuf", "hadis", "tefsir", "siyer", "tarih", "kissa"):
        assert a in alanlar and sum(1 for g in d["girdiler"] if g["alan"] == a) >= 10, a
    # üretim kodu konuya özel değil: Arapça kelime sabiti yalnız normalizasyon tablosunda
    src = (ROOT / "ilim_assistant" / "ruzgar_k3_sorgu.py").read_text(encoding="utf-8")
    kod = re.sub(r'\("[أإآٱىةؤئاي]", "[اويهي]"\)', "", src)
    kod = re.sub(r"\[\\u0600-\\u06FF\]|\\u06[0-9a-fA-F]{2}", "", kod)
    assert not re.search(r"[\u0600-\u06FF]{4,}", kod.replace('"ال"', ""))


def test_kelime_tabanli_siralama_lexik_bonus():
    p = k3.plan_for_query("Abdesti bozan şeyler nelerdir?")
    b_var, n_var = k3.lex_skor("وَمِنْ نَوَاقِضِ الْوُضُوءِ خُرُوجُ الْبَوْلِ والغائط", p)
    b_yok, n_yok = k3.lex_skor("باب الزكاة والصيام والحج", p)
    assert n_var >= 1 and b_var > 0
    assert n_yok == 0 and b_yok == 0
    assert k3.kanit_alakali_mi(p, [("باب نواقض الوضوء", "s", 0.5)])
    assert not k3.kanit_alakali_mi(p, [("باب الزكاة", "s", 0.5)])


def test_bm25_terimli_parcayi_one_alir():
    p = k3.plan_for_query("Abdesti bozan şeyler nelerdir?")
    hits = [
        ("كتاب الصلاة باب الجمعة والعيدين", "salat", 0.92),
        ("من نواقض الوضوء خروج الخارج من السبيلين", "nawaqid", 0.41),
        ("الوضوء شرط ونواقضه كثيرة", "wudu", 0.48),
    ]
    out = k3.bm25_rerank(hits, p)
    assert out[0][1] in ("nawaqid", "wudu")
    assert "salat" in {h[1] for h in out[1:]}


def test_kanit_dil_notu_arapca_kanitta_cikar():
    ar_blok = ("[K1] x\nمن نواقض الوضوء خروج الخارج من السبيلين وزوال العقل بالنوم أو الإغماء", "src")
    tr_blok = ("[K1] y\nAbdest bozulması hakkında kısa Türkçe metin parçası burada", "src")
    note = k3.kanit_dil_notu([ar_blok], want_source=True)
    assert "ARAPÇA KANIT" in note
    assert "sistem kanıt künyesinden" in note.lower() or "Kaynak izi" in note
    assert k3.kanit_dil_notu([tr_blok]) == ""


def test_kunye_manifestten_gelir():
    root = ROOT / "knowledge" / "ilim" / "din" / "shamela"
    ms = list(root.glob("*/*/manifest.json"))[:1]
    if not ms:
        pytest.skip("Şâmile manifestleri yok")
    bd = ms[0].parent
    src = f"ilim/din/shamela/{bd.parent.name}/{bd.name}/incremental/{bd.name}_batch_0001.md"
    kun = kn.kunye_for_source(src)
    assert kun and kun["eser_id"] == bd.name
    et = kn.kunye_etiketi(src)
    assert et and bd.name in et
    assert kn.label_for_source("knowledge/yok/olmayan.md") == "knowledge/yok/olmayan.md"


def test_kunye_kapatma(monkeypatch):
    root = ROOT / "knowledge" / "ilim" / "din" / "shamela"
    ms = list(root.glob("*/*/manifest.json"))[:1]
    if not ms:
        pytest.skip("Şâmile manifestleri yok")
    bd = ms[0].parent
    src = f"ilim/din/shamela/{bd.parent.name}/{bd.name}/incremental/x.md"
    monkeypatch.setenv("RUZGAR_KUNYE", "0")
    assert kn.kunye_etiketi(src) == ""


def test_shard_secimi_veri_ipucunu_onceler():
    from ilim_assistant import shamela_rag_shards as sh

    ready = {c: {"chunks": 1} for c in ("18_genel_fikih", "19_fikhi_meseleler", "22_fetvalar", "01_akaid", "06_hadis_sunen")}
    got = sh.pick_shamela_cats_for_query("herhangi bir soru", ready, prefer=["01_akaid", "18_genel_fikih"])
    assert got[:2] == ["01_akaid", "18_genel_fikih"]
    # prefer yoksa eski davranış bozulmaz
    assert sh.pick_shamela_cats_for_query("buhari hadis niyet", ready)
