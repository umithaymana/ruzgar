#!/usr/bin/env python3
"""Faz 14E — md/html çıktı biçimlendirme."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_export_format import (
        EXPORT_FORMAT_VERSION,
        format_export_body,
    )

    if "v14e" not in EXPORT_FORMAT_VERSION:
        print("FAIL version", EXPORT_FORMAT_VERSION)
        return 1

    md = format_export_body(
        "Giriş\n\nBirinci bölüm\n\nUzun paragraf. Cümle devam.",
        "md",
        source_rel="ilim-assistant/arsiv/kitap.pdf",
        tgt_lang="tr",
        title="Test Kitap",
    )
    if "# Test Kitap" not in md or "## Birinci bölüm" not in md:
        print("FAIL md", md[:200])
        return 1

    html_out = format_export_body("Başlık satırı\n\nMetin paragrafı.", "html", title="X")
    if "<!DOCTYPE html>" not in html_out or "<h2>" not in html_out:
        print("FAIL html", html_out[:200])
        return 1

    plain = format_export_body("düz", "txt")
    if plain.strip() != "düz":
        print("FAIL txt", plain)
        return 1

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    ex = workbench_config().get("export_faz14e") or {}
    if "html" not in (ex.get("formats") or []):
        print("FAIL config", ex)
        return 1

    print("OK tercume faz14e — md/html export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
