#!/usr/bin/env python3
"""Smoke — #2 sohbet akıcılığı: Güven/Faz notu + soru yankısı temizliği."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    os.environ.setdefault("RUZGAR_SOHBET_TARZ", "chatgpt")
    from ilim_assistant.text_encoding import (
        finalize_assistant_reply,
        strip_rhetorical_self_question,
        strip_trust_and_faz_noise,
    )
    from ilim_assistant.ruzgar_tek_beyin_bilgi_guard import apply_tek_beyin_bilgi_guard

    fails: list[str] = []

    noisy = (
        "Samanyolu, Dünya'nın içinde bulunduğu galaksidir.\n\n"
        "*Not (Faz J): «Galaksi nedir anlat biraz» sorusuyla konu hizalaması zayıf; "
        "cevabı kaynaklarla doğrula.*\n\n"
        "**Güven: düşük** — kaynak/cevap uyumu zayıf."
    )
    cleaned = strip_trust_and_faz_noise(noisy)
    if "Güven" in cleaned or "Faz J" in cleaned:
        fails.append(f"strip_trust left noise: {cleaned!r}")
    fin = finalize_assistant_reply(noisy)
    if "Güven" in fin or "Faz J" in fin:
        fails.append(f"finalize left noise: {fin!r}")

    echo = (
        "Yapay zeka hakkında ne düşünüyorum? "
        "Bence yararlı bir araç; doğru kullanılınca işi hızlandırır, yanlışta yanılabilir."
    )
    no_echo = strip_rhetorical_self_question(echo)
    if "düşünüyorum" in no_echo.lower() or "dusunuyorum" in no_echo.lower():
        fails.append(f"echo not stripped: {no_echo!r}")
    if "yararlı" not in no_echo.lower() and "yararli" not in no_echo.lower():
        fails.append(f"echo strip ate body: {no_echo!r}")

    # Guard: chatgpt tarzında weak_alignment damgası basmasın
    guarded, meta = apply_tek_beyin_bilgi_guard(
        "Samanyolu büyük bir yıldız sistemidir.",
        "Galaksi nedir anlat biraz",
        hits=[],
        question_plan=None,
        web_was_used=False,
    )
    if "Güven" in guarded or "Faz J" in guarded:
        fails.append(f"guard stamped chatgpt noise: {guarded!r} meta={meta}")

    if fails:
        for f in fails:
            print(f"FAIL {f}")
        return 1
    print("PASS sohbet_akicilik_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
