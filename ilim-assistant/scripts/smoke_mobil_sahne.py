#!/usr/bin/env python3
"""Mobil sahne izin + PWA sözleşme smoke. Çıkış 0 = yeşil."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_mobil_oturum import (  # noqa: E402
    VERSION,
    _DEFAULT_MOTORS,
    motor_allowed,
    normalize_motors,
)


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def ok(msg: str) -> None:
    print("OK:", msg)


def main() -> None:
    if "sahne" not in _DEFAULT_MOTORS:
        fail("DEFAULT_MOTORS.sahne yok")
    if _DEFAULT_MOTORS["sahne"] is not False:
        fail("sahne varsayılan kapalı olmalı")
    ok("varsayılan sahne=kapalı")

    n = normalize_motors({"sohbet": True})
    if n.get("sahne") is not False:
        fail("normalize eksik anahtarı False yapmalı")
    ok("normalize_motors")

    if motor_allowed({"motors": {"sohbet": True}}, "sahne"):
        fail("sahnesiz kullanıcıya sahne açılmamalı")
    if not motor_allowed({"motors": {"sohbet": True, "sahne": True}}, "sahne"):
        fail("sahne=True iken izin verilmeli")
    ok("motor_allowed sahne")

    if "v3" not in VERSION and "2026-11-13" not in VERSION:
        fail(f"VERSION beklenen dilim değil: {VERSION}")
    ok(f"VERSION={VERSION}")

    pwa = ROOT / "static" / "mobil-pwa"
    html = (pwa / "index.html").read_text(encoding="utf-8")
    js = (pwa / "app.js").read_text(encoding="utf-8")
    css = (pwa / "app.css").read_text(encoding="utf-8")
    for needle in (
        "sahneStage",
        "sahneDurum",
        "sahneDalga",
        "sahne-face-svg",
        'role="status"',
        "app.js?v=64-stac-pano",
        "app.css?v=46-sehir",
        "btnSahneSheet",
        "sahneDock",
        "sahneOrgan",
    ):
        if needle not in html:
            fail(f"index.html eksik: {needle}")
    for needle in (
        "sahneAllowed",
        "setSahneState",
        "applySahneGate",
        "ensureMobilSahneA11y",
        "Rüzgar sahne",
        "Rüzgar sahne · ",
        "aria-busy",
        "aria-atomic",
        'role", "status"',
        'lang", "tr"',
        "is-thinking-sahne",
        "sameStream",
        "onSahneResume",
        "pageshow",
        '"online"',
        "sahneYaziTimer",
        ", 60)",
        "SAHNE_PLACEHOLDER",
        ".inert",
        "Yaz. Cevabı ben buradan söyleyeyim.",
        "Durum: hazir",
        "data-sahne-mode",
        "refreshWhoMotors",
        "/api/mobil/me",
        "640",
        "sahne-gate-hint",
        "Durum: ",
        "visibilitychange",
        "setSahneState(\"dinle\")",
        "sahne-busy",
        "payload.sahne",
        '"sahne"',
        "has-sahne",
        "sheet-open",
        "toggleSahneSheet",
        "syncSahneSheetBtn",
        "applySahneOrgan",
        "runSuperEl",
        "is-fresh",
        '"yazi"',
        "preventScroll",
        "Sahne</b>",
    ):
        if needle not in js:
            fail(f"app.js eksik: {needle}")
    if "640" not in (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.js").read_text(encoding="utf-8"):
        fail("PC soz limiti 640 değil")
    ok("soz limiti 640 çift")
    server = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    if "/api/mobil/me" not in server or "session_me" not in server:
        fail("desktop_server /api/mobil/me yok")
    oturum = (ROOT / "ilim_assistant" / "ruzgar_mobil_oturum.py").read_text(encoding="utf-8")
    if "def session_me" not in oturum:
        fail("session_me yok")
    if 'if cur.get("sahne")' not in oturum or 'cur["sohbet"] = True' not in oturum:
        fail("sahne→sohbet kuralı yok")
    ok("API mobil/me + sahne→sohbet")
    for needle in (
        ".sahne-stage",
        "is-dusun",
        "is-yazi",
        "mobil-talk",
        "mobil-blink",
        "sahne-face-svg",
        "has-sahne",
        "sheet-open",
        "sahne-dock",
        "sahne-sheet-toggle",
        "sahne-organ",
        "focus-visible",
        "is-live .sahne-face-ring",
        "prefers-reduced-motion",
        "safe-area-inset-bottom",
        "sahne-busy",
        "--sahne-gold",
        "user-select: none",
        "touch-callout",
    ):
        if needle not in css:
            fail(f"app.css eksik: {needle}")
    ok("PWA sahne işaretler")
    sw = (pwa / "sw.js").read_text(encoding="utf-8")
    if "ruzgar-pwa-v64-stac-pano" not in sw or "app.js?v=64-stac-pano" not in sw or "app.css?v=46-sehir" not in sw:
        fail("sw.js cache sürümü index ile hizasız")
    ok("SW cache hiza v64-stac-pano")
    if "app.css?v=46-sehir" not in html:
        fail("index.html css sürümü 46-sehir değil")
    if "app.js?v=64-stac-pano" not in html:
        fail("index.html js sürümü 64-stac-pano değil")
    # Harita organı paritesi (PC ile aynı viewer + Cesium/F4 + şehir)
    for needle in (
        "harita-viewer.html",
        "mode_uydu",
        "mode_tur",
        "mode_3d",
        "mode_f4",
        "mode_sentinel",
        "mode_pano",
        "runSuperEl",
        "haritaPilotSehir",
        "era_gelecek",
    ):
        if needle not in js:
            fail(f"app.js harita paritesi eksik: {needle}")
    ok("mobil harita paritesi")
    print("SMOKE_MOBIL_SAHNE=PASS")


if __name__ == "__main__":
    main()
