# -*- coding: utf-8 -*-
"""Bilgisayar mühendisliği Faz 16 — donanım çekirdeği.

Eğitim özeti. Saldırı/exploit tarifi yok. Telifli ders kitabı metni yok.
Teknoloji giriş rafı (Faz 15) ayrı kalır; bu raf mimari derinliğidir.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_muhendisligi"
KAT = OUT / "katmanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_bilgisayar.jsonl"
CATALOG = OUT / "catalog.json"

from bm_derin_icerik import KATMAN, KAVRAMLAR

def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_katman() -> dict:
    spec = KATMAN["donanim_cekirdek"]
    dest = KAT / "donanim_cekirdek"
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        f"# {spec['baslik']}",
        "",
        "Kaynak: Rüzgar bilgisayar mühendisliği Faz 16. Eğitim özeti. Exploit yok.",
        "",
    ]
    for i, (t, x) in enumerate(spec["parcalar"], 1):
        body += [f"## {i}. {t}", "", x, ""]
    (incr / "donanim_cekirdek_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": "donanim_cekirdek",
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "bilgisayar_muhendisligi",
        "faz": 16,
        "dil": "tr",
        "dosya_yolu": "knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi/katmanlar/donanim_cekirdek",
        "parca_sayisi": len(spec["parcalar"]),
        "updated_utc": _utc(),
        "durum": "hazir",
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return man


def _update_ortak(entry: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    found = False
    for r in rows:
        if r.get("kaynak_id") == entry["kaynak_id"]:
            r.update(entry)
            found = True
            break
    if not found:
        rows.append(entry)
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    man = _write_katman()
    _update_ortak(
        {
            "kaynak_id": man["kaynak_id"],
            "kaynak_adi": man["baslik"],
            "yazar": None,
            "ilim_alani": "bilgisayar_muhendisligi",
            "eser_turu": "katman",
            "dil": "tr",
            "yayin": None,
            "cilt": None,
            "bolum": None,
            "sayfa": None,
            "dosya_yolu": man["dosya_yolu"],
            "guvenilirlik": "orta",
            "kaynak_sinifi": "kalici",
            "durum": "hazir",
            "not": "Faz 16 donanım çekirdeği; eğitim; exploit yok.",
        }
    )
    merged: dict[str, dict] = {}
    if KAV.is_file():
        for line in KAV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            kid = str(row.get("id") or "").strip()
            if kid:
                merged[kid] = row
    for row in KAVRAMLAR:
        merged[str(row["id"])] = row
    kavram_rows = list(merged.values())
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in kavram_rows) + "\n",
        encoding="utf-8",
    )
    md_files = list(OUT.rglob("*.md"))
    chars = sum(len(p.read_text(encoding="utf-8")) for p in md_files)
    keep_catalog = False
    if CATALOG.is_file():
        try:
            prev = json.loads(CATALOG.read_text(encoding="utf-8"))
            keep_catalog = bool(prev.get("katmanlar"))
        except json.JSONDecodeError:
            keep_catalog = False
    if not keep_catalog:
        cat = {
            "domain": "bilgisayar_muhendisligi",
            "faz": 16,
            "katman": "donanim_cekirdek",
            "updated_utc": _utc(),
            "politika": "Eğitim özeti. Telifli tam metin yok. Saldırı/exploit yok.",
            "sayilar": {
                "md_dosya": len(md_files),
                "karakter": chars,
                "kavram": len(kavram_rows),
            },
        }
        CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = OUT / "README.md"
    if not readme.is_file() or "Faz 16b" not in readme.read_text(encoding="utf-8"):
        readme.write_text(
            "# Bilgisayar mühendisliği\n\n"
            "## Faz 16 — donanım çekirdeği\n"
            "`katmanlar/donanim_cekirdek`\n\n"
            f"MD: **{len(md_files)}** · Kavram: **{len(kavram_rows)}**\n\n"
            "**Politika:** Eğitim · exploit yok\n"
            "**Script:** `faz16_bilgisayar_muhendisligi_ingest.py` · "
            "**Anlık:** `ruzgar_bilgisayar_kutuphane.py`\n",
            encoding="utf-8",
        )
    print(f"Faz 16 md={len(md_files)} kavram={len(KAVRAMLAR)} char={chars}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
