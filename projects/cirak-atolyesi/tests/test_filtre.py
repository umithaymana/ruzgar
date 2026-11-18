# Created by Ümit & Gökçenur — gece T5 (spec uyumu)
from filtre_satir import filtre_satirlar


def test_filtre():
    assert list(filtre_satirlar(["Merhaba", "x", "MERHABA dünya"], "merhaba")) == [
        "Merhaba",
        "MERHABA dünya",
    ]
    assert list(filtre_satirlar([], "a")) == []
