# -*- coding: utf-8 -*-
"""Mobil PWA — sahne kaçma kilidi desktop ile eşit (statik kontrol)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PWA = ROOT / "static" / "mobil-pwa"


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label, flush=True)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    app = (PWA / "app.js").read_text(encoding="utf-8")
    html = (PWA / "index.html").read_text(encoding="utf-8")
    sw = (PWA / "sw.js").read_text(encoding="utf-8")

    failed += _ok("function looksLikeSahneCmd" in app, "looksLikeSahneCmd var")
    failed += _ok("no_sahne_niyet" in app, "niyet kapısı")
    failed += _ok("low_guven_sohbet" in app, "guven kapısı")
    failed += _ok("if (looksLikeSahneCmd(t))" in app, "send/voice niyet")
    failed += _ok("20261121-sahne-kilit" in html, "html cache-bust")
    failed += _ok("20261121-sahne-kilit" in sw, "sw cache-bust")

    # Sunucu tarafı hâlâ sohbeti kaçırmıyor
    sys.path.insert(0, str(ROOT))
    from ilim_assistant.sahne_super_el import resolve_super_el

    bad = resolve_super_el("osmanli tarihi nedir", geocode=False)
    failed += _ok(not bad.get("ok"), "API osmanli kacmaz")
    good = resolve_super_el("haritayi goster", geocode=False)
    failed += _ok(bool(good.get("ok")), "API harita goster")

    total = 8
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Mobil sahne kilit: KIRMIZI", flush=True)
        return 1
    print("Mobil sahne kilit: YEŞİL — desktop parity", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
