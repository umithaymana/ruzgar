# -*- coding: utf-8 -*-
import re
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "ilim_assistant" / "sahne_harita_geo.py"
t = p.read_text(encoding="utf-8")
for name in ("hatay", "mugla", "artvin"):
    t = re.sub(
        rf'("{name}":\s*\{{[^{{}}]*?"zoom":\s*)\d+(\s*,)',
        r"\g<1>13\2",
        t,
    )
p.write_text(t, encoding="utf-8")
from ilim_assistant.sahne_harita_geo import geocode_local

for k in ("hatay", "mugla", "artvin", "istanbul", "turkiye", "palandoken"):
    print(k, geocode_local(k)["zoom"])
