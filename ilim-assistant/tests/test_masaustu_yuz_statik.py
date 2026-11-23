"""Masaüstü yeni sohbet yüzü (ruzgar-yuz) — kilitli yüz bozulmaz, eski görünüme sızmaz (statik kontrol)."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

DESK = Path(__file__).resolve().parents[2] / "ruzgar-desktop"


def _css_kurallari(css: str) -> list[str]:
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


def test_yuz_css_eski_sohbete_sizmaz():
    css = (DESK / "ruzgar-yuz.css").read_text(encoding="utf-8")
    izinli_onek = ("html.ryd", ".ryd-", "html {")
    kotu: list[str] = []
    for blok in _css_kurallari(css):
        for sec in (s.strip() for s in blok.split(",")):
            if sec and not sec.startswith(izinli_onek) and sec != "html":
                kotu.append(sec)
    assert not kotu, f"Eski görünümü etkileyebilecek seçiciler: {kotu}"


def test_yuz_css_kilitli_bolgelere_dokunmaz():
    """Motor listesi, üst düğmeler, tutamaç, masa ve sahne seçicileri bu dosyada olmaz."""
    css = (DESK / "ruzgar-yuz.css").read_text(encoding="utf-8")
    for yasak in (
        "ruzgar-masa",
        "ruzgar-sahne",
        "ruzgar-split",
        "motor-side",
        "ruzgar-chat-w",
        "panel-main",
        "workbench",
        "ruzgar-robot-dock",
    ):
        assert yasak not in css, f"Kilitli bölge seçicisi yüz CSS'inde: {yasak}"


def test_yuz_dosyalari_bagli_ve_kilitli_yuz_yerinde():
    html = (DESK / "index.html").read_text(encoding="utf-8")
    assert "ruzgar-yuz.css" in html and "ruzgar-yuz.js" in html
    # kilitli yüz: motor listesi, geri/ileri/yenile, tutamaç, dört masa, sahne yerinde
    for parca in (
        'id="ruzgar-sahne"',
        'id="ruzgar-masa"',
        'data-pane="belge"',
        'data-pane="tablo"',
        'data-pane="cizim"',
        'data-pane="sunum"',
        'id="ruzgar-sahne-masa"',
        "ruzgar-split.js",
        "ruzgar-masa.js",
    ):
        assert parca in html, f"kilitli yüz parçası kayıp: {parca}"
    # mevcut ses/yazı düğmeleri HTML'de duruyor (yüz bunları taşır, silmez)
    for kimlik in ("msg-input", "btn-send", "btn-mic", "btn-stop", "btn-tts-pause"):
        assert f'id="{kimlik}"' in html


def test_yuz_mevcut_dugmeleri_tasir_yeniden_yazmaz():
    js = (DESK / "ruzgar-yuz.js").read_text(encoding="utf-8")
    for kimlik in ("msg-input", "btn-send", "btn-mic", "btn-stop", "btn-tts-pause", "ruzgar-sahne"):
        assert f'getElementById("{kimlik}")' in js
    # varsayılan açık ama kapatılabilir; kapalıyken hiçbir şey değişmez
    assert 'if (tercih !== "1") return;' in js
    assert "Eski sohbete dön" in js
    # app.js'e dokunulmaz: yüz yalnız mevcut genel API'yi çağırır
    assert "window.ruzgarSpeak" in js


@pytest.mark.skipif(shutil.which("node") is None, reason="node yok")
def test_yuz_node_saf_yardimcilar():
    r = subprocess.run(
        ["node", str(DESK / "ruzgar-yuz.test.js")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert r.returncode == 0, r.stdout + r.stderr
