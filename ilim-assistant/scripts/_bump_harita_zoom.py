# -*- coding: utf-8 -*-
"""One-shot: yerel geo zoom kademelerini Faz 2'ye çek."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "ilim_assistant" / "sahne_harita_geo.py"
t = p.read_text(encoding="utf-8")

# Ülke/bölge 6 → 7
for name in (
    "turkiye",
    "turkey",
    "anadolu",
    "almanya",
    "germany",
    "fransa",
    "france",
    "italya",
    "ispanya",
    "misir",
    "irak",
):
    t = re.sub(
        rf'("{name}":\s*\{{[^{{}}]*?"zoom":\s*)6(\s*,)',
        r"\g<1>7\2",
        t,
    )

# Şehir 11 → 14
t = re.sub(r'("zoom":\s*)11(\s*,\s*"label")', r"\g<1>14\2", t)
# İl ölçeği 10 → 13
t = re.sub(r'("zoom":\s*)10(\s*,\s*"label")', r"\g<1>13\2", t)
# İlçe/kasaba 12 → 15, 13 → 16
t = re.sub(r'("zoom":\s*)12(\s*,\s*"label")', r"\g<1>15\2", t)
t = re.sub(r'("zoom":\s*)13(\s*,\s*"label")', r"\g<1>16\2", t)

# Nominatim kademeleri
old_nom = '''        zoom = 11
        if kind in ("country", "nation"):
            zoom = 6
        elif kind in ("state", "province", "region", "county"):
            zoom = 8
        elif kind in ("city", "town"):
            zoom = 11
        elif kind in ("village", "hamlet", "suburb", "neighbourhood"):
            zoom = 14
        elif kind in ("peak", "mountain"):
            zoom = 13'''
new_nom = '''        zoom = 14
        if kind in ("country", "nation"):
            zoom = 7
        elif kind in ("state", "province", "region"):
            zoom = 8
        elif kind in ("county"):
            zoom = 15
        elif kind in ("city", "town"):
            zoom = 14
        elif kind in ("suburb", "neighbourhood", "quarter", "city_block"):
            zoom = 17
        elif kind in ("village", "hamlet", "locality"):
            zoom = 16
        elif kind in ("peak", "mountain"):
            zoom = 16'''
if old_nom not in t:
    raise SystemExit("nominatim zoom bloğu bulunamadı")
t = t.replace(old_nom, new_nom)

# yorum satırını güncelle
t = t.replace(
    "# zoom: 5 ülke · 8 bölge · 11 şehir · 13 ilçe · 15 mahalle/kasaba",
    "# zoom: 7-8 ülke · 13-14 şehir · 15-16 ilçe · 17-18 mahalle",
)

p.write_text(t, encoding="utf-8")
print("OK wrote", p)
