# -*- coding: utf-8 -*-
"""Sohbet → sahneye kaçma yok; gerçek harita komutu çalışır (ağ yok)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label, flush=True)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.sahne_super_el import resolve_super_el, smoke_super_el

    sohbetler = (
        "osmanli hakkinda anlat",
        "osmanli tarihi nedir",
        "aciklar misin fotosentezi",
        "kitap okuyalim mi",
        "metin ne demek",
        "bak ne guzel",
        "nasilsin bugun",
    )
    for t in sohbetler:
        r = resolve_super_el(t, geocode=False)
        failed += _ok(not r.get("ok"), f"sohbet kacmaz: {t[:28]}")

    harita = resolve_super_el("haritayi goster", geocode=False)
    failed += _ok(
        bool(harita.get("ok") and harita.get("organ") == "harita"),
        "haritayi goster",
    )
    odak = resolve_super_el("erzuruma odaklan", geocode=False)
    failed += _ok(
        bool(odak.get("ok") and odak.get("fiil") == "odakla"),
        "erzuruma odaklan",
    )
    nasa = resolve_super_el("nasa uzaydan bak", geocode=False)
    failed += _ok(
        bool(nasa.get("ok") and nasa.get("organ") == "uzay"),
        "nasa uzaydan bak",
    )

    fails = smoke_super_el()
    failed += _ok(not fails, "smoke_super_el paket")

    total = len(sohbetler) + 4
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Sohbet sahne kacma: KIRMIZI", flush=True)
        return 1
    print("Sohbet sahne kacma: YEŞİL", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
