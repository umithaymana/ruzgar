# Created by Ümit & Gökçenur — gece T5 (spec uyumu)
from filtre_yardim import normalize


def filtre_satirlar(satirlar, anahtar: str):
    """Anahtar içeren satırları yield eden generator."""
    key = normalize(anahtar)
    for s in satirlar or []:
        if key and key in normalize(str(s)):
            yield s
