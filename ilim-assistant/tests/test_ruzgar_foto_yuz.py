"""Foto / yüz katmanları — sahte eşleşme yok; OpenCV yoksa katman kapıları yine test edilir."""

from __future__ import annotations

from pathlib import Path

from ilim_assistant import ruzgar_foto_yuz as fz


def test_durum_bos(tmp_path, monkeypatch):
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_CATALOG", tmp_path / "idx" / "katalog.json")
    monkeypatch.setattr(fz, "_YUZ", tmp_path / "idx" / "yuz.json")
    monkeypatch.setattr(fz, "_GOMME", tmp_path / "idx" / "gomme.json")
    st = fz.durum()
    assert st["ok"] is True
    assert st["katman"]["katalog"] is False
    assert st["sonraki"] == "katalog"


def test_katalog_tara(tmp_path, monkeypatch):
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_CATALOG", tmp_path / "idx" / "katalog.json")
    monkeypatch.setattr(fz, "_YUZ", tmp_path / "idx" / "yuz.json")
    monkeypatch.setattr(fz, "_GOMME", tmp_path / "idx" / "gomme.json")
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"0" * 200)
    (tmp_path / "x.txt").write_text("nope", encoding="utf-8")
    out = fz.katalog_tara(str(tmp_path), limit=100)
    assert out["ok"] is True
    assert out["dosya_sayisi"] == 1
    assert out["katman"]["katalog"] is True
    assert out["sonraki"] == "yuz"


def test_eslestir_katalogsuz(tmp_path, monkeypatch):
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_CATALOG", tmp_path / "idx" / "katalog.json")
    monkeypatch.setattr(fz, "_YUZ", tmp_path / "idx" / "yuz.json")
    monkeypatch.setattr(fz, "_GOMME", tmp_path / "idx" / "gomme.json")
    r = fz.eslestir_istem("ben.jpg")
    assert r["ok"] is False
    assert r["sonraki"] == "katalog"
    assert r["sonuclar"] == []


def test_eslestir_katman_sirasi(tmp_path, monkeypatch):
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_CATALOG", tmp_path / "idx" / "katalog.json")
    monkeypatch.setattr(fz, "_YUZ", tmp_path / "idx" / "yuz.json")
    monkeypatch.setattr(fz, "_GOMME", tmp_path / "idx" / "gomme.json")
    img = tmp_path / "b.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"1" * 200)
    fz.katalog_tara(str(tmp_path))
    r = fz.eslestir_istem("ref.jpg")
    assert r["ok"] is False
    assert r["sonraki"] == "yuz"
    assert r["sonuclar"] == []


def test_yuz_tara_opencv_yoksa(tmp_path, monkeypatch):
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_CATALOG", tmp_path / "idx" / "katalog.json")
    monkeypatch.setattr(fz, "_YUZ", tmp_path / "idx" / "yuz.json")
    monkeypatch.setattr(fz, "_GOMME", tmp_path / "idx" / "gomme.json")
    monkeypatch.setattr(fz, "opencv_hazir", lambda: False)
    (tmp_path / "c.jpg").write_bytes(b"\xff\xd8\xff" + b"0" * 200)
    fz.katalog_tara(str(tmp_path))
    try:
        fz.yuz_tara()
        assert False, "OpenCV yokken RuntimeError beklenirdi"
    except RuntimeError as exc:
        assert "OpenCV" in str(exc)


def test_referans_normalize_jpeg(tmp_path, monkeypatch):
    if not fz.opencv_hazir():
        return
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_REF_FILE", tmp_path / "idx" / "referans_secilen")
    monkeypatch.setattr(fz, "_REF_META", tmp_path / "idx" / "referans_secilen.json")
    import numpy as np
    import cv2

    big = np.zeros((3000, 4000, 3), dtype=np.uint8)
    big[:] = (40, 90, 180)
    ok, enc = cv2.imencode(".png", big)
    assert ok
    out = fz.referans_yaz_normalize(enc.tobytes(), "devasa.png")
    assert out["ok"] is True
    assert out["w"] <= 2048 and out["h"] <= 2048
    assert fz._REF_FILE.is_file()
    assert out["mime"] == "image/jpeg"


def test_coz_katalog_dosya(tmp_path, monkeypatch):
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_CATALOG", tmp_path / "idx" / "katalog.json")
    monkeypatch.setattr(fz, "_YUZ", tmp_path / "idx" / "yuz.json")
    monkeypatch.setattr(fz, "_GOMME", tmp_path / "idx" / "gomme.json")
    lib = tmp_path / "lib"
    lib.mkdir()
    img = lib / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"0" * 200)
    fz.katalog_tara(str(lib))
    p = fz.coz_katalog_dosya("a.jpg")
    assert p.is_file()
    try:
        fz.coz_katalog_dosya("../x.jpg")
        assert False, "kaçış beklenirdi"
    except ValueError:
        pass


def test_face_detector_hazir():
    if not fz.opencv_hazir():
        return
    kind, det = fz._make_face_detector()
    assert kind in ("yunet", "haar")
    assert det is not None
    if kind == "yunet":
        assert fz._yunet_model_path() is not None
    else:
        assert fz._haar_cascade_path() is not None


def test_pipeline_lena_eslesme(tmp_path, monkeypatch):
    if not fz.opencv_hazir():
        return
    fixture = Path(__file__).resolve().parent / "fixtures" / "lena.jpg"
    if not fixture.is_file():
        return
    monkeypatch.setattr(fz, "_INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(fz, "_CATALOG", tmp_path / "idx" / "katalog.json")
    monkeypatch.setattr(fz, "_YUZ", tmp_path / "idx" / "yuz.json")
    monkeypatch.setattr(fz, "_GOMME", tmp_path / "idx" / "gomme.json")
    lib = tmp_path / "lib"
    lib.mkdir()
    for i in range(3):
        (lib / f"f{i}.jpg").write_bytes(fixture.read_bytes())
    ref = tmp_path / "ref.jpg"
    ref.write_bytes(fixture.read_bytes())
    assert fz.katalog_tara(str(lib))["dosya_sayisi"] == 3
    yuz = fz.yuz_tara()
    assert yuz["yuz_sayisi"] >= 1
    assert yuz["katman"]["yuz"] is True
    assert yuz.get("motor") in ("yunet", "haar")
    gom = fz.gomme_kur()
    assert gom["katman"]["gomme"] is True
    esle = fz.eslestir_bytes(ref.read_bytes(), referans_adi="ref.jpg")
    assert esle["ok"] is True
    assert len(esle.get("sonuclar") or []) >= 1
    esle2 = fz.eslestir_istem(str(ref))
    assert esle2["ok"] is True
    assert len(esle2.get("sonuclar") or []) >= 1
