# -*- coding: utf-8 -*-
"""B5 — anlık kart **başlık** + _dipnot_ → düzyazı."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_bilim_kutuphane import try_bilim_reply  # noqa: E402
from ilim_assistant.ruzgar_cografya_kutuphane import try_cografya_reply  # noqa: E402
from ilim_assistant.ruzgar_siyer_kutuphane import try_siyer_reply  # noqa: E402
from ilim_assistant.text_encoding import (  # noqa: E402
    cila_anlik_kart_prose,
    finalize_assistant_reply,
)


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    sample = (
        "**fotosentez**\n\n"
        "Fotosentez: ışıkla CO₂ ve sudan glikoz ve oksijen üretimi. "
        "Ekosistemin enerji girişidir.\n\n"
        "_Bilim — biyoloji._"
    )
    prose = cila_anlik_kart_prose(sample)
    failed += _ok(not prose.strip().startswith("**"), "başlık ** yok")
    failed += _ok("_Bilim" not in prose and "biyoloji._" not in prose, "dipnot yok")
    failed += _ok(
        "ışıkla" in prose.lower() or "glikoz" in prose.lower(),
        "gövde korunur",
    )
    failed += _ok(
        "Fotosentez" in prose or "fotosentez" in prose.lower(),
        "konu adı düzyazıda",
    )

    fin = finalize_assistant_reply(sample)
    failed += _ok(not fin.startswith("**"), "finalize başlık yok")
    failed += _ok("_Bilim" not in fin, "finalize dipnot yok")

    # Canlı raftan
    for label, fn, q in (
        ("bilim", try_bilim_reply, "Fotosentez nedir?"),
        ("siyer", try_siyer_reply, "Hicret nedir?"),
        ("cografya", try_cografya_reply, "Karadeniz nedir?"),
    ):
        raw = fn(q) or ""
        out = finalize_assistant_reply(raw)
        failed += _ok(bool(raw), f"{label} ham kart var")
        failed += _ok(
            bool(out) and not out.startswith("**") and not out.strip().endswith("_"),
            f"{label} finalize düzyazı",
        )

    total = 10
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
