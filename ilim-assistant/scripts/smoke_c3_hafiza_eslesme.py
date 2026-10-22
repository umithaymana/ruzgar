# -*- coding: utf-8 -*-
"""C3 — zehirli/fuzzy yanlış kart: kısa alias + scrub (Lale dışı)."""
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
    failed = 0
    from ilim_assistant.ruzgar_bilim_kutuphane import try_bilim_reply
    from ilim_assistant.ruzgar_cografya_kutuphane import try_cografya_reply
    from ilim_assistant.ruzgar_teknoloji_kutuphane import try_teknoloji_reply
    from ilim_assistant.ruzgar_tasavvuf_kutuphane import try_tasavvuf_reply
    from ilim_assistant.text_encoding import finalize_assistant_reply

    os_tek = try_teknoloji_reply("os nedir") or ""
    os_bil = try_bilim_reply("os nedir") or ""
    failed += _ok(
        "işletim" in os_tek.lower() or "isletim" in os_tek.lower(),
        "os → işletim sistemi (tech)",
    )
    failed += _ok(
        "atmosfer" not in (os_bil or "").lower() and "atmosfer" not in os_tek.lower(),
        "os → atmosfer tuzağı yok",
    )

    kd = try_cografya_reply("Karadeniz nedir") or ""
    failed += _ok(
        "karadeniz" in kd.lower() and "ege denizi" not in kd.lower(),
        "Karadeniz doğru raf",
    )

    nefs = try_tasavvuf_reply("nefs nedir") or ""
    if not nefs:
        from ilim_assistant.ruzgar_psikoloji_kutuphane import try_psikoloji_reply

        nefs = try_psikoloji_reply("nefs nedir") or ""
    failed += _ok(
        bool(nefs) and "atmosfer" not in nefs.lower(),
        "nefs eşleşir, yanlış raf yok",
    )

    poison = finalize_assistant_reply(
        "Turkiyede 209 üniversite var. Webten bakarak bu bilgiye ulaştım."
    )
    failed += _ok(
        "209" not in poison
        and (
            "uydurmam" in poison.lower()
            or "yök" in poison.lower()
            or "yok" in poison.lower()
        ),
        "209+webten invalid scrub",
    )

    total = 5
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
