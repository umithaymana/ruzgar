#!/usr/bin/env python3
"""Araç kayıt defteri smoke (Faz 2). Çıkış 0 = yeşil."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_arac_kayit import (  # noqa: E402
    KAYIT_YOLU,
    smoke_arac_kayit,
    tara,
)


def main() -> None:
    r = smoke_arac_kayit()
    if not r.get("ok"):
        print("FAIL:", r.get("fails"))
        sys.exit(1)
    doc = tara()
    print("OK: kayıt", KAYIT_YOLU.name)
    print("OK: kurulu", doc.get("kurulu_sayisi"), "/", doc.get("toplam"))
    server = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    for needle in (
        "/api/araclar",
        "/api/araclar/tara",
        "/api/araclar/sec",
        "/api/araclar/kaydet",
        "ruzgar_arac_kayit",
    ):
        if needle not in server:
            print("FAIL: desktop_server eksik:", needle)
            sys.exit(1)
    print("OK: API uçları")
    print("SMOKE_ARAC_KAYIT=PASS")


if __name__ == "__main__":
    main()
