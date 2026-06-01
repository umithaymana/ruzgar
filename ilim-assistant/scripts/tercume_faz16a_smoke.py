#!/usr/bin/env python3
"""Faz 16A — Calibre/DjVu ebook okuma + pipeline uzantıları smoke."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_ebook_read import (
        CALIBRE_EXTS,
        DJVU_EXTS,
        EBOOK_READ_VERSION,
        calibre_available,
        djvu_available,
        read_ebook_auto,
    )
    from ilim_assistant.motorlar.tercume_atolye import BOOK_EXTENSIONS

    if "v16a" not in EBOOK_READ_VERSION:
        print("FAIL version", EBOOK_READ_VERSION)
        return 1

    exts = set(BOOK_EXTENSIONS or ())
    for need in (".mobi", ".azw", ".djvu"):
        if need not in exts:
            print("FAIL source ext missing", need, "have", sorted(exts))
            return 1

    if not CALIBRE_EXTS or ".mobi" not in CALIBRE_EXTS:
        print("FAIL CALIBRE_EXTS", CALIBRE_EXTS)
        return 1
    if not DJVU_EXTS:
        print("FAIL DJVU_EXTS")
        return 1

    miss = Path("/nonexistent/book.mobi")
    hit = read_ebook_auto(miss)
    if hit.get("ok"):
        print("FAIL should not ok for missing file", hit)
        return 1

    cal = calibre_available()
    djv = djvu_available()
    print(
        "INFO calibre",
        cal,
        "djvu",
        djv,
        "(SKIP live convert if tools absent)",
    )

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    eb = workbench_config().get("ebook_faz16a") or {}
    if not eb.get("calibre_exts") or not eb.get("djvu_exts"):
        print("FAIL ebook_faz16a config", eb)
        return 1

    print("OK tercume faz16a — mobi/djvu pipeline + ebook auto + config")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
