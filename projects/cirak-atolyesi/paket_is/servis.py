# Created by Ümit & Gökçenur — Dilim gercek_paket
from paket_is.yardim import normalize

def isle(satirlar, anahtar: str) -> list[str]:
    key = normalize(anahtar)
    out = []
    for s in satirlar or []:
        if key and key in normalize(str(s)):
            out.append(s)
    return out
