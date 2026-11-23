"""Mobil yeni sohbet yüzü (ruzgar-yuz) — eski yüze sızmaz, dosyalar bağlı (statik kontrol)."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

PWA = Path(__file__).resolve().parents[1] / "static" / "mobil-pwa"


def _css_kurallari(css: str) -> list[str]:
    """Yorumları ve @keyframes/@media gövdelerini atıp en üst düzey seçicileri döndürür."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    secici: list[str] = []
    derin = 0
    tampon = ""
    atla_derinlik = None
    for ch in css:
        if ch == "{":
            ad = tampon.strip()
            if derin == 0 and ad.startswith("@"):
                atla_derinlik = 0
            elif derin == 0:
                secici.append(ad)
            tampon = ""
            derin += 1
        elif ch == "}":
            derin -= 1
            tampon = ""
            if atla_derinlik is not None and derin == atla_derinlik:
                atla_derinlik = None
        elif atla_derinlik is None:
            tampon += ch
    return secici


def test_yuz_css_eski_yuze_sizmaz():
    css = (PWA / "ruzgar-yuz.css").read_text(encoding="utf-8")
    izinli_onek = ("html.ry", ".ry-", "#btnYuzYeni", "#ryUstBtn", "body.ry-menu-acik")
    kotu: list[str] = []
    for blok in _css_kurallari(css):
        for sec in (s.strip() for s in blok.split(",")):
            if sec and not sec.startswith(izinli_onek):
                kotu.append(sec)
    assert not kotu, f"Eski yüzü etkileyebilecek seçiciler: {kotu}"


def test_yuz_dosyalari_baglanti_ve_onbellek():
    html = (PWA / "index.html").read_text(encoding="utf-8")
    sw = (PWA / "sw.js").read_text(encoding="utf-8")
    for ad in ("ruzgar-yuz.css", "ruzgar-yuz.js"):
        assert ad in html, f"index.html {ad} yüklemiyor"
        assert ad in sw, f"sw.js {ad} önbelleğe/ağ-öncelikli listeye almıyor"
    # her iki yerde aynı sürüm etiketi
    v_html = set(re.findall(r"\?v=(\d{8}-[a-z0-9]+)", html))
    assert "20261123-yuz2" in v_html
    assert "20261123-yuz2" in sw
    assert 'id="btnYuzYeni"' in html


def test_yuz_varsayilan_kapali_ve_mevcut_dugmeler_korunur():
    js = (PWA / "ruzgar-yuz.js").read_text(encoding="utf-8")
    # Varsayılan kapalı: tercih "1" değilse hiçbir şey değişmez
    assert 'if (tercih !== "1") return;' in js
    # Mevcut ses düğmeleri taşınır, yeniden yazılmaz (aynı DOM düğümü → aynı olay dinleyicileri)
    for kimlik in ("btnMic", "btnSend", "input"):
        assert f'getElementById("{kimlik}")' in js
    app = (PWA / "app.js").read_text(encoding="utf-8")
    assert "window.ruzgarMobil" in app


@pytest.mark.skipif(shutil.which("node") is None, reason="node yok")
def test_yuz_node_saf_yardimcilar():
    r = subprocess.run(
        ["node", str(PWA / "ruzgar-yuz.test.js")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert r.returncode == 0, r.stdout + r.stderr
