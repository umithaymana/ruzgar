# -*- coding: utf-8 -*-
import json
from collections import defaultdict
from pathlib import Path

RAF = Path(__file__).resolve().parents[1] / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
by_key = defaultdict(list)
by_url = defaultdict(list)
for d in sorted(RAF.iterdir()):
    if not d.is_dir() or d.name.startswith("paket"):
        continue
    k = d / "katalog.json"
    if not k.exists():
        continue
    data = json.loads(k.read_text(encoding="utf-8"))
    srcs = data.get("kaynaklar") or {}
    ok = sum(1 for s in srcs.values() if isinstance(s, dict) and s.get("ok"))
    print(f"{d.name}: {ok}/{len(srcs)} -> {list(srcs.keys())}")
    for key, meta in srcs.items():
        by_key[key].append(d.name)
        if isinstance(meta, dict) and meta.get("url"):
            by_url[meta["url"]].append(d.name)

print("\nDUP KEYS", sum(1 for v in by_key.values() if len(v) > 1))
for key, dals in sorted(by_key.items(), key=lambda x: -len(x[1])):
    if len(dals) > 1:
        print(" ", key, dals)
print("DUP URLS", sum(1 for v in by_url.values() if len(v) > 1))
for url, dals in sorted(by_url.items(), key=lambda x: -len(x[1])):
    if len(dals) > 1:
        print(" ", len(dals), url[:80], dals)
