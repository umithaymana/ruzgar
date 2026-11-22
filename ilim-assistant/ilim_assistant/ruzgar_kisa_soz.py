# Created by Ümit & Gökçenur
"""
Madde 1 — Kısa söz anlayışı (2026-11-22).

«tamam / evet / ok / peki / sağ ol / teşekkürler / görüşürüz / hı» gibi kısa
onay, teşekkür, veda ve dinleme sözleri iş emri veya hafıza araması DEĞİLDİR:
sohbettir. Bu sözler bekleyen bir onay yokken programlama kapısına, bulanık
hafıza eşleşmesine veya «netleştirir misin» sorusuna düşmemelidir.

Ezber cevap üretmez; yalnızca «bu bir kısa söz mü?» kararı verir.
Kapat: RUZGAR_KISA_SOZ=0
"""

from __future__ import annotations

import os
import re
import unicodedata

KISA_SOZ_VERSION = "ruzgar-kisa-soz-v1-2026-11-22"


def kisa_soz_enabled() -> bool:
    return os.environ.get("RUZGAR_KISA_SOZ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("İ", "i").replace("I", "i").lower()
    for a, b in (
        ("ı", "i"),
        ("ğ", "g"),
        ("ü", "u"),
        ("ş", "s"),
        ("ö", "o"),
        ("ç", "c"),
    ):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# Çekirdek sözler (katlanmış). Tam eşleşme — cümle içinde geçmesi yetmez.
_CORE = frozenset(
    {
        # onay / ret / dinleme
        "tamam", "tamamdir", "tmm", "tamamdir abi", "ok", "okey", "okay",
        "evet", "hayir", "yok", "olur", "peki", "pekala", "anladim", "anliyorum",
        "anlasildi", "tabi", "tabii", "elbette", "aynen", "kesinlikle", "dogru",
        "hmm", "hm", "hi", "hihi", "hih", "ha", "he", "haa", "aha", "ya",
        "iyi", "cok iyi", "iyiyim", "sorun yok", "sikinti yok", "yok bir sey",
        "bos ver", "neyse", "devam", "devam et",
        # beğeni
        "harika", "super", "guzel", "mukemmel", "bravo", "aferin", "helal",
        "eline saglik", "eline saglik abi", "cok guzel", "cok super",
        # teşekkür
        "sag ol", "sagol", "sagolun", "sag olun", "saol", "eyvallah",
        "tesekkur", "tesekkurler", "tesekkur ederim", "cok tesekkurler",
        "cok tesekkur ederim", "tesekkurler abi", "mersi", "rica ederim",
        # veda
        "gorusuruz", "gorusmek uzere", "hosca kal", "hoscakal", "hoscakalin",
        "bay bay", "baybay", "bye", "iyi gunler", "kolay gelsin", "iyi calismalar",
        "iyi geceler", "hayirli olsun", "afiyet olsun", "allaha emanet",
    }
)

# Başa/sona eklenebilen hitap ve dolgu sözleri.
_FILLER = frozenset(
    {
        "abi", "abim", "ruzgar", "umit", "kardesim", "canim", "hocam", "dostum",
        "ya", "valla", "he", "yani", "of", "ay", "ee", "eee", "hmm", "cok",
    }
)


def looks_like_short_ack(message: str) -> bool:
    """
    Kısa onay / teşekkür / veda / dinleme sözü mü?

    Tam eşleşme (noktalama ve hitap sözleri yok sayılır). Soru işareti taşıyan
    veya 5 kelimeden uzun mesaj kısa söz sayılmaz.
    """
    if not kisa_soz_enabled():
        return False
    raw = (message or "").strip()
    if not raw or len(raw) > 44:
        return False
    if "?" in raw:
        return False
    f = _fold(raw)
    if not f:
        return False
    words = f.split()
    if len(words) > 5:
        return False
    if f in _CORE:
        return True
    # «tamam tamam», «evet evet» — ardışık tekrarı tek say
    dedup: list[str] = []
    for w in words:
        if not dedup or dedup[-1] != w:
            dedup.append(w)
    words = dedup
    if " ".join(words) in _CORE:
        return True
    # Hitap/dolgu soyup tekrar dene: «tamam abi», «ya tamam», «peki ruzgar»
    core = [w for w in words if w not in _FILLER]
    if not core:
        return False
    return " ".join(core) in _CORE


def kisa_soz_status() -> dict[str, object]:
    return {
        "enabled": kisa_soz_enabled(),
        "version": KISA_SOZ_VERSION,
        "env": "RUZGAR_KISA_SOZ",
    }
