#!/usr/bin/env python3
"""Smoke — #5 hafıza/eşleşme: Karadeniz, Hicret, Lale, os≠atmosfer."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_cografya_kutuphane import (
        _load_kavramlar,
        try_cografya_reply,
    )
    from ilim_assistant.ruzgar_siyer_kutuphane import try_siyer_reply
    from ilim_assistant.ruzgar_teknoloji_kutuphane import try_teknoloji_reply
    from ilim_assistant.ruzgar_otomatik_ogrenme import try_bilgi_kutuphane_instant_reply
    from ilim_assistant.ruzgar_anlik_niyet_gate import (
        is_strict_library_lookup,
        should_defer_library_instant,
    )

    _load_kavramlar.cache_clear()
    fails: list[str] = []

    kar = try_cografya_reply("Karadeniz nedir") or ""
    if "karadeniz" not in kar.lower():
        fails.append(f"Karadeniz miss: {kar[:120]!r}")
    if "**cografya**" in kar.lower() or kar.lower().startswith("**cografya**"):
        fails.append(f"Karadeniz fell to generic cografya: {kar[:120]!r}")

    cog = try_cografya_reply("cografya nedir") or ""
    if "cografya" not in cog.lower() and "coğrafya" not in cog.lower():
        fails.append(f"cografya nedir miss: {cog[:80]!r}")

    hic = try_siyer_reply("Hicret ne zaman oldu") or ""
    if "622" not in hic and "medine" not in hic.lower():
        fails.append(f"Hicret ne zaman miss: {hic[:120]!r}")

    if not is_strict_library_lookup("Hicret ne zaman oldu"):
        fails.append("Hicret ne zaman should be strict lookup")
    if should_defer_library_instant("Hicret ne zaman oldu"):
        fails.append("Hicret ne zaman should not defer in chatgpt")

    lale = try_bilgi_kutuphane_instant_reply("Lale Devri nedir") or ""
    if "1718" not in lale:
        fails.append(f"Lale miss 1718: {lale[:120]!r}")
    if "19. yüzyıl" in lale.lower() or "tanzimat" in lale.lower() and "değil" not in lale.lower():
        # tanzimat with değil is OK
        if "değil" not in lale.lower() and "degil" not in lale.lower():
            fails.append(f"Lale wrong era: {lale[:120]!r}")

    # os ≠ atmosfer (kısa alias)
    atm = try_cografya_reply("atmosfer nedir")  # may be None — bilim handles
    os_r = try_teknoloji_reply("os nedir") or ""
    if "atmosfer" in os_r.lower():
        fails.append(f"os matched atmosfer: {os_r[:80]!r}")
    if "isletim" not in os_r.lower() and "işletim" not in os_r.lower() and "operating" not in os_r.lower():
        # teknoloji may say OS differently
        if "os" not in os_r.lower() and "sistem" not in os_r.lower():
            fails.append(f"os nedir weak: {os_r[:80]!r}")

    if fails:
        for f in fails:
            print(f"FAIL {f}")
        return 1
    print("PASS hafiza_eslesme_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
