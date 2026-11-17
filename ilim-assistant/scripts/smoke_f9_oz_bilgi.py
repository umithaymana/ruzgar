# Created by Ümit & Gökçenur
"""F9 — öz-bilgi niyet kapısı smoke (≥12 katalog sorusu)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CATALOG = [
    "Sen kimsin?",
    "Neler biliyorsun?",
    "Neler yapabilirsin?",
    "Ne yapamazsın?",
    "Zayıf yanların neler?",
    "Kütüphanende ne var?",
    "Hafızanda ne tür bilgiler var?",
    "Motorların neler?",
    "Kaç motorun var?",
    "Okuma ile mimar farkı nedir?",
    "Cevabı nereden buldun?",
    "Internete bakıyor musun?",
    "Sesli sohbet yapabilir misin?",
    "Limitlerin neler?",
    "Ilık mısın?",
    "Hub durum",
]


def main() -> int:
    from ilim_assistant.ruzgar_oz_bilgi import (
        OZ_BILGI_VERSION,
        canli_envanter,
        classify_oz_bilgi_intent,
        format_oz_bilgi_reply,
        kapasite_karti,
        motor_kartlari,
    )

    kap = kapasite_karti()
    assert kap["kim"]["ad"] == "Rüzgar"
    assert len(motor_kartlari()) >= 7
    inv = canli_envanter()
    assert "rag_chunks" in inv and "shamela" in inv

    hits = 0
    for q in CATALOG:
        intent = classify_oz_bilgi_intent(q)
        reply = format_oz_bilgi_reply(q)
        assert intent, f"niyet yok: {q}"
        assert reply and len(reply) >= 20, f"cevap zayıf: {q} → {reply!r}"
        # Gemini şişirme yok — karttan
        assert "Gemini diye" not in reply
        hits += 1
    assert hits >= 12, hits

    # Uydurma yasağı: zayıf yanlarda abartı yok
    z = format_oz_bilgi_reply("zayıf yanların neler") or ""
    assert "her şeyi bilirim" not in z.lower()
    assert "%70" in z or "zayıf" in z.lower() or "Zayıf" in z

    # F9.5 — hub_help sohbet kartı ile aynı kaynak
    from ilim_assistant.ruzgar_oz_bilgi import format_hub_help_card, oz_bilgi_public_payload

    help_txt = format_hub_help_card()
    assert "Rüzgar" in help_txt and "Motorlar" in help_txt
    assert "Ümit & Gökçenur" in help_txt
    payload = oz_bilgi_public_payload()
    assert payload.get("hub_help") == help_txt

    print("smoke_f9_oz_bilgi OK", OZ_BILGI_VERSION, f"n={hits} hub_help=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
