from filtre_satir import filtre_satirlar

def test_filtre_satirlar():
    veri = ["merhaba dünya", "python programlama", "merhaba ruzgar"]
    sonuc = list(filtre_satirlar(veri, "merhaba"))
    assert sonuc == ["merhaba dünya", "merhaba ruzgar"]
