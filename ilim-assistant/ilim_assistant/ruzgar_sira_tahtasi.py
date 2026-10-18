"""Sıra tahtasını okur. Dosyaya yazmaz."""

from __future__ import annotations

import re
from pathlib import Path

_CUMLE = re.compile(
    r"^(?:s[ıi]ra tahtas[ıi]|s[ıi]rada ne var|ne bitti)$",
    re.I,
)
_SATIR = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|")


def sira_tahtasi_cumlesi(message: str) -> bool:
    return bool(_CUMLE.match(re.sub(r"\s+", " ", message or "").strip()))


def sira_tahtasi_yaniti(message: str, tahta: Path) -> str | None:
    if not sira_tahtasi_cumlesi(message):
        return None
    if not tahta.is_file():
        return "Sıra tahtasını bulamadım."
    metin = tahta.read_text(encoding="utf-8")
    biten: tuple[int, str] | None = None
    acik: tuple[int, str] | None = None
    for satir in metin.splitlines():
        bulunan = _SATIR.match(satir.strip())
        if not bulunan:
            continue
        no = int(bulunan.group(1))
        ad = bulunan.group(2).strip()
        durum = bulunan.group(3).strip().lower()
        if durum == "bitti":
            if biten is None or no > biten[0]:
                biten = (no, ad)
        elif acik is None or no < acik[0]:
            acik = (no, ad)
    deneme = ""
    for satir in metin.splitlines():
        if satir.startswith("**Denenecek cümle:**"):
            deneme = satir.split("**", 2)[-1].strip()
            break
    kapali = ""
    for satir in metin.splitlines():
        if satir.startswith("**Bilerek kapalı:**"):
            kapali = satir.split(":", 1)[-1].strip().lstrip("*").strip()
            break
    parca = []
    if biten:
        parca.append(f"Son biten iş {biten[0]}: {biten[1]}.")
    else:
        parca.append("Bitmiş iş yok.")
    if acik:
        parca.append(f"Sırada {acik[0]}: {acik[1]}.")
    else:
        parca.append("Açık satır yok.")
    if deneme:
        parca.append("Denenecek cümle: " + deneme)
    if kapali:
        parca.append("Kapalı duran: " + kapali)
    return "\n".join(parca)
