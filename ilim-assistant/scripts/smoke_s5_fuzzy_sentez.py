# -*- coding: utf-8 -*-
"""S5 smoke — fuzzy eşik + soru tipi kayması + doğal sentez sıkı."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.hafiza_dogal_sentez import (
        _dogal_system_tail,
        _hint_min_score,
        append_hafiza_hint_directive,
    )
    from ilim_assistant.hafiza_i_ruzgar import HafizaIRuzgar

    failed = 0
    failed += _ok(HafizaIRuzgar.FUZZY_VARSAYILAN_ESIK >= 0.85, "fuzzy esik≥0.85")
    failed += _ok(_hint_min_score() >= 0.85, "hint min≥0.85")

    # Soru tipi kayması
    failed += _ok(
        HafizaIRuzgar._fuzzy_ozne_uyusmazligi(
            "Lale Devri nedir",
            "Lale Devri'nde hangi alanlarda gelişme oldu",
        ),
        "nedir≠hangi alan",
    )
    failed += _ok(
        HafizaIRuzgar._fuzzy_ozne_uyusmazligi(
            "Lale Devri'nde hangi alanlarda gelişme oldu",
            "Lale Devri nedir",
        ),
        "hangi alan≠nedir",
    )
    failed += _ok(
        not HafizaIRuzgar._fuzzy_ozne_uyusmazligi(
            "Lale Devri nedir",
            "Lale Devri nedir kısaca",
        ),
        "nedir≈nedir ok",
    )
    failed += _ok(
        HafizaIRuzgar._fuzzy_aday_elenmeli_mi(
            "Lale Devri nedir",
            "Lale Devri'nde hangi alanlarda gelişme oldu",
        ),
        "aday elenir",
    )

    # Doğal sentez: bilir-gibi yumuşatıldı
    soft = _dogal_system_tail("genel", fuzzy_weak=True)
    failed += _ok("bilir gibi" in soft or "dürüst" in soft.lower(), "weak tail")
    failed += _ok("S5" in soft, "S5 mark")
    strong = _dogal_system_tail("genel", fuzzy_weak=False)
    failed += _ok("kendin biliyormuşsun" not in strong, "eski özgüven yok")

    hint = {
        "soru": "uzay nedir",
        "cevap": "Uzay, yıldızların bulunduğu boşluktur.",
        "eslesme": "fuzzy",
        "skor": 0.86,
    }
    dir_txt = append_hafiza_hint_directive("merhaba", hint, "uzay nedir")
    failed += _ok("fuzzy" in dir_txt.lower() or "dürüst" in dir_txt.lower(), "hint directive")

    # C3 ayrı koşulur; burada import yolu kırılmasın diye hafif kontrol
    failed += _ok(
        callable(getattr(__import__("ilim_assistant.text_encoding", fromlist=["finalize_assistant_reply"]), "finalize_assistant_reply")),
        "finalize import",
    )

    total = 11
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
