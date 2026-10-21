# -*- coding: utf-8 -*-
"""B6 — galaksi kartı: 1 net tanım + 1 örnek."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_bilim_kutuphane import (  # noqa: E402
    _load_kavramlar,
    try_bilim_reply,
)
from ilim_assistant.text_encoding import finalize_assistant_reply  # noqa: E402


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    _load_kavramlar.cache_clear()
    raw = try_bilim_reply("Galaksi nedir?") or ""
    out = finalize_assistant_reply(raw)
    low = out.lower()
    failed += _ok(bool(out), "galaksi cevap var")
    failed += _ok(
        "yıldız" in low or "yildiz" in low or "yerçekimi" in low or "yercekimi" in low,
        "net tanım (yıldız/yerçekimi)",
    )
    failed += _ok(
        "samanyolu" in low or "andromeda" in low,
        "örnek galaksi adı",
    )
    failed += _ok(len(out) >= 80, f"derinlik len>={len(out)}")
    failed += _ok(not out.startswith("**"), "düzyazı (B5)")

    sam = finalize_assistant_reply(try_bilim_reply("Samanyolu nedir?") or "")
    failed += _ok("samanyolu" in sam.lower() or "galaksi" in sam.lower(), "Samanyolu eşleşir")

    total = 6
    print(f"result: {total - failed}/{total} pass")
    print("OUT:", out[:220])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
