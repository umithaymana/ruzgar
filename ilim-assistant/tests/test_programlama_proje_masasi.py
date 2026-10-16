# Created by Ümit & Gökçenur
"""Çalışma sayfası projects/ sınırını aşmaz."""

import pytest

from ilim_assistant.motorlar.programlama_proje_masasi import (
    ajan_uygula,
    list_projeler,
    normalize_proje_rel,
    onizleme_dosyasi,
    sil_proje_yolu,
    yaz_proje_dosyasi,
)


def test_yol_projects_disina_cikmaz():
    assert normalize_proje_rel("projects/vitrin/index.html") == "projects/vitrin/index.html"
    with pytest.raises(ValueError):
        normalize_proje_rel("projects/../desktop_server.py")
    with pytest.raises(ValueError):
        normalize_proje_rel("ilim-assistant/desktop_server.py")
    with pytest.raises(ValueError):
        normalize_proje_rel("projects")


def test_yaz_goster_sil(tmp_path):
    (tmp_path / "projects").mkdir()
    (tmp_path / "projects" / "smoke-eski").mkdir()
    (tmp_path / "projects" / "live-bat").mkdir()
    yaz_proje_dosyasi(tmp_path, "projects/vitrin/index.html", "<title>vitrin</title>")
    yaz_proje_dosyasi(tmp_path, "projects/vitrin/css/styles.css", "body{}")
    rows = list_projeler(tmp_path)
    assert rows[0]["name"] == "vitrin"
    assert rows[0]["site"] is True
    assert rows[1]["deneme"] is True
    assert all(row["deneme"] for row in rows if row["name"] != "vitrin")
    path, mime = onizleme_dosyasi(tmp_path, "projects/vitrin/index.html")
    assert path.is_file()
    assert "html" in mime
    with pytest.raises(ValueError):
        yaz_proje_dosyasi(tmp_path, "projects/vitrin/run.exe", "no")
    sil_proje_yolu(tmp_path, "projects/vitrin/css/styles.css")
    assert not (tmp_path / "projects" / "vitrin" / "css" / "styles.css").exists()
    sil_proje_yolu(tmp_path, "projects/vitrin")
    assert not (tmp_path / "projects" / "vitrin").exists()
    assert (tmp_path / "projects").is_dir()


def test_ajan_baslik_paragraf_kacis_ve_red(tmp_path):
    (tmp_path / "projects").mkdir()
    yaz_proje_dosyasi(
        tmp_path,
        "projects/vitrin/index.html",
        "<html><head><title>vitrin</title></head><body><h1>vitrin</h1></body></html>",
    )
    baslik = ajan_uygula(tmp_path, "projects/vitrin", "başlığı Vitrin Ajan yap")
    body = (tmp_path / "projects" / "vitrin" / "index.html").read_text(encoding="utf-8")
    assert baslik["ok"] is True
    assert "<title>Vitrin Ajan</title>" in body
    assert "<h1>Vitrin Ajan</h1>" in body
    ajan_uygula(tmp_path, "projects/vitrin", "paragraf ekle: <script>alert(1)</script>")
    body = (tmp_path / "projects" / "vitrin" / "index.html").read_text(encoding="utf-8")
    assert "<script>" not in body
    assert "&lt;script&gt;" in body
    with pytest.raises(ValueError):
        ajan_uygula(tmp_path, "projects/vitrin", "sunucuyu sil")
    assert "sunucuyu sil" not in body
