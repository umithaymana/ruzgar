# -*- coding: utf-8 -*-
"""B2 — Lale Devri nedir ≠ hangi alanlarda gelişme."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_otomatik_ogrenme import (  # noqa: E402
    try_bilgi_kutuphane_instant_reply,
)


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    nedir = try_bilgi_kutuphane_instant_reply("Lale Devri nedir?") or ""
    alan = (
        try_bilgi_kutuphane_instant_reply(
            "Lale Devri hangi alanlarda gelisme gosterdi?"
        )
        or ""
    )
    failed += _ok(
        "1718" in nedir and "III. Ahmed" in nedir,
        "nedir → dönem kartı (1718)",
    )
    failed += _ok(
        "mimari" in alan.lower() and "nedim" in alan.lower(),
        "alan → mimari/Nedim",
    )
    failed += _ok(
        "hangi alan" not in nedir.lower() or "görülür" not in nedir.lower(),
        "nedir metni alan listesi değil (gevşek)",
    )
    failed += _ok(
        "patrona" not in alan.lower() or "görülür" in alan.lower(),
        "alan cevabı gelişme odaklı",
    )
    failed += _ok(
        alan != nedir,
        "alan ≠ nedir metni",
    )
    # Kısa «Lale Devri?» hâlâ dönem
    kisa = try_bilgi_kutuphane_instant_reply("Lale Devri?") or ""
    failed += _ok("1718" in kisa, "kısa Lale Devri? → dönem")

    total = 6
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
