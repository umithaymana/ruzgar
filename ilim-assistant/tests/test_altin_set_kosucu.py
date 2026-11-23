"""K0 — Altın set koşucusu: puanlama ve soru dosyası bütünlüğü (sunucu gerekmez)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import altin_set_kos as k  # noqa: E402


def test_soru_seti_12_raf_x_20():
    s = k.yukle_sorular()
    assert len(s) == 240
    raflar = {x["raf"] for x in s}
    assert len(raflar) == 12
    for r in raflar:
        assert sum(1 for x in s if x["raf"] == r) == 20
    assert len({x["id"] for x in s}) == 240
    assert all(x["gruplar"] and all(g for g in x["gruplar"]) for x in s)


def test_kapsama_harf_katlama_ve_kisa_anahtar():
    cov, hit = k.kapsama("Net KUVVET, kütle ile İVME çarpımıdır", [["kuvvet"], ["kütle"], ["ivme"]])
    assert cov == 1.0 and all(hit)
    # kısa anahtar kelime sınırı: "ab" kelimesi "abdest" içinde eşleşmemeli
    cov, _ = k.kapsama("abdest alma", [["ab"]])
    assert cov == 0.0


def test_ham_dokum_ve_miss_algilama():
    ham = "Ümit abi — kütüphaneden okuduğum pasaj şöyle: === RÜZGAR KÜTÜPHANESİ (yerel raflar) --- Eser #1 (skor=0.4)"
    s = {"id": "x-01", "raf": "x", "soru": "q", "gruplar": [["pasaj"]]}
    r = k.kayit_uret(s, {"full_reply": ham, "tur_teshis": {"provider": "kutuphane_extractive"}}, 1.0)
    assert r["ham_dokum"] is True
    r2 = k.kayit_uret(s, {"full_reply": "Ümit abi, bu sorunun cevabını bulamadım. Bana öğretir misin?"}, 1.0)
    assert r2["bulamadim"] is True and r2["gecti"] is False
