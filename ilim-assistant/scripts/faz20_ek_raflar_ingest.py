# -*- coding: utf-8 -*-
"""Eksik ilim rafları — sırayla dolu yazılır. Boş raf bırakılmaz."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ek_raflar_icerik import RAFLAR  # noqa: E402

ALAN = ROOT / "knowledge" / "ortak_kaynak" / "alanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
SIRA = ALAN / "_ek_raf_sira.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _update_ortak(entry: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    found = False
    for row in rows:
        if row.get("kaynak_id") == entry["kaynak_id"]:
            row.update(entry)
            found = True
            break
    if not found:
        rows.append(entry)
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _check() -> None:
    seen: set[str] = set()
    for raf in RAFLAR:
        if len(raf["kavramlar"]) < 6:
            raise SystemExit(f"az kavram: {raf['id']}")
        for row in raf["kavramlar"]:
            if len(row["metin"]) < 340:
                raise SystemExit(f"kisa metin {raf['id']}/{row['id']} {len(row['metin'])}")
            keys = {row["baslik"], *row["aliases"]}
            for alias in keys:
                key = alias.casefold()
                if key in seen:
                    raise SystemExit(f"alias cakisti: {alias}")
                seen.add(key)


def _write_raf(raf: dict) -> int:
    out = ALAN / raf["id"]
    kat = out / "katmanlar" / "ders"
    incr = kat / "incremental"
    incr.mkdir(parents=True, exist_ok=True)
    for old in incr.glob("*.md"):
        old.unlink()
    body = [
        f"# {raf['baslik']}",
        "",
        f"Sıra: {raf['sira']}. {raf['neden']}",
        "",
        "Kaynak: Rüzgar ek ilim rafları. Özgün eğitim notu. Teşhis, avukatlık, yatırım ve suç tarifi yok.",
        "",
    ]
    chars = 0
    for i, row in enumerate(raf["kavramlar"], 1):
        body += [f"## {i}. {row['baslik']}", "", row["metin"], ""]
        chars += len(row["metin"])
    text = "\n".join(body)
    (incr / "ders_batch_0001.md").write_text(text, encoding="utf-8")
    man = {
        "katman_id": "ders",
        "baslik": raf["baslik"],
        "kaynak_id": f"ek_{raf['id']}",
        "ilim_alani": raf["id"],
        "sira": raf["sira"],
        "dil": "tr",
        "parca_sayisi": len(raf["kavramlar"]),
        "updated_utc": _utc(),
        "durum": "hazir",
    }
    (kat / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = []
    for row in raf["kavramlar"]:
        rows.append(
            {
                "id": row["id"],
                "baslik": row["baslik"],
                "aliases": row["aliases"],
                "metin": row["metin"],
                "kaynak_notu": f"{raf['baslik']} — sıra {raf['sira']}.",
            }
        )
    (out / "kavramlar.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    (out / "catalog.json").write_text(
        json.dumps(
            {
                "domain": raf["id"],
                "sira": raf["sira"],
                "neden": raf["neden"],
                "updated_utc": _utc(),
                "politika": "Eğitim notu. Telifli tam metin yok. Teşhis, avukatlık, yatırım, suç tarifi yok.",
                "sayilar": {"kavram": len(rows), "karakter": chars},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        f"# {raf['baslik']}\n\n"
        f"Sıra **{raf['sira']}**. {raf['neden']}\n\n"
        f"Kavram: **{len(rows)}** · karakter: **{chars}**\n\n"
        "**Politika:** Eğitim · boş raf yok\n"
        "**Script:** `faz20_ek_raflar_ingest.py` · **Anlık:** `ruzgar_ek_raflar.py`\n",
        encoding="utf-8",
    )
    _update_ortak(
        {
            "kaynak_id": man["kaynak_id"],
            "kaynak_adi": raf["baslik"],
            "yazar": None,
            "ilim_alani": raf["id"],
            "eser_turu": "katman",
            "dil": "tr",
            "yayin": None,
            "cilt": None,
            "bolum": None,
            "sayfa": None,
            "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/{raf['id']}/katmanlar/ders",
            "guvenilirlik": "orta",
            "kaynak_sinifi": "kalici",
            "durum": "hazir",
            "not": f"Sıra {raf['sira']}. {raf['neden']}",
        }
    )
    print(f"  [ok] {raf['sira']:02d} {raf['id']} kavram={len(rows)} char={chars}")
    return chars


def main() -> int:
    _check()
    total = 0
    sira = []
    for raf in sorted(RAFLAR, key=lambda r: r["sira"]):
        total += _write_raf(raf)
        sira.append({"sira": raf["sira"], "id": raf["id"], "baslik": raf["baslik"]})
    SIRA.write_text(json.dumps(sira, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TOPLAM raf={len(sira)} karakter={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
