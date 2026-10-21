#!/usr/bin/env python3
"""Smoke — #3 web/genel bilgi: okul sayı cilası + web meta gürültü + reason."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.text_encoding import (
        finalize_assistant_reply,
        strip_web_capability_noise,
    )
    from ilim_assistant.ruzgar_web_arastirma_pro import (
        build_web_pro_system_addon,
        reason_web_question,
    )

    fails: list[str] = []

    noisy = (
        "**Turkiye'de kaç tane özel okul var?**\n\n"
        "Görünmez bir yanıt, ancak web sorgulama yeteneğimle buldum. "
        "2022 itibariyle Türkiye'de 17.000'den fazla özel okul bulunmaktadır.\n\n"
        "---\n"
        "Bu sorunun cevabı, sorulduğunda, ilgili bilgilerimden doğrudan elde edilemedi."
    )
    cleaned = finalize_assistant_reply(noisy)
    if "17.000" in cleaned or "17000" in cleaned.replace(".", ""):
        # rakam scrubbed → honest line
        if "uydur" not in cleaned.lower() and "bulamadım" not in cleaned.lower() and "bulamadim" not in cleaned.lower():
            fails.append(f"okul sayısı kalmış/scrub yok: {cleaned!r}")
    if "görünmez" in cleaned.lower() or "yeteneğimle" in cleaned.lower() or "yetenegimle" in cleaned.lower():
        fails.append(f"web meta kaldı: {cleaned!r}")
    if cleaned.strip().startswith("**") and "?" in cleaned.split("\n", 1)[0]:
        fails.append(f"soru başlığı kaldı: {cleaned!r}")

    # Resmi kaynak geçince rakam dursun
    resmi = (
        "MEB istatistiğine göre Türkiye'de yaklaşık 14.000 özel okul var. "
        "Kaynak: meb.gov.tr"
    )
    keep = finalize_assistant_reply(resmi)
    if "14.000" not in keep and "14000" not in keep.replace(".", ""):
        fails.append(f"resmi kaynak rakamı silindi: {keep!r}")

    r = reason_web_question("Turkiyede kac tane ozel okul vardir webten bak")
    if "MEB" not in (r.get("query") or "") and "özel okul" not in (r.get("query") or "").lower():
        fails.append(f"reason query zayıf: {r}")
    if "uydurma" not in (r.get("want") or "").lower() and "rakam" not in (r.get("want") or "").lower():
        fails.append(f"reason want zayıf: {r}")

    addon = build_web_pro_system_addon("Turkiyede kac ozel okul var")
    if "Sayı sorusu" not in addon and "sayi" not in addon.lower():
        fails.append("web addon sayı kuralı yok")
    if "meta" not in addon.lower() and "yetene" not in addon.lower():
        # soft: either meta warning present
        if "uydurma" not in addon.lower():
            fails.append(f"addon eksik: {addon[:200]!r}")

    # strip alone
    meta_only = strip_web_capability_noise(
        "Görünmez bir yanıt, ancak web sorgulama yeteneğimle buldum. Asıl cevap burada."
    )
    if "görünmez" in meta_only.lower() or "yeteneğimle" in meta_only.lower():
        fails.append(f"strip_web failed: {meta_only!r}")
    if "Asıl cevap" not in meta_only and "Asil cevap" not in meta_only:
        fails.append(f"strip ate body: {meta_only!r}")

    if fails:
        for f in fails:
            print(f"FAIL {f}")
        return 1
    print("PASS web_genel_bilgi_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
