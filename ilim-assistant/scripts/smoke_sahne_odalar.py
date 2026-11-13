#!/usr/bin/env python3
"""Meslek odaları + A/B/C + API smoke."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/SAHNE_MESLEK_ODALARI.json"
if not p.is_file():
    print("FAIL: odalar json yok")
    sys.exit(1)
d = json.loads(p.read_text(encoding="utf-8"))
od = d.get("odalar") or []
if len(od) < 13:
    print("FAIL: 13 oda beklenir", len(od))
    sys.exit(1)
abc = d.get("abc") or {}
if set(abc) < {"A", "B", "C"}:
    print("FAIL: abc")
    sys.exit(1)
server = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
if "/api/sahne/odalar" not in server:
    print("FAIL: api odalar yok")
    sys.exit(1)
css = (ROOT / "static/mobil-pwa/app.css").read_text(encoding="utf-8")
if 'data-sahne-abc="B"' not in css:
    print("FAIL: mobil abc css yok")
    sys.exit(1)
print("OK: odalar", len(od), "abc", list(abc))
print("SMOKE_SAHNE_ODALAR=PASS")
