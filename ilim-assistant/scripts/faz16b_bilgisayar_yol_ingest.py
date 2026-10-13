# -*- coding: utf-8 -*-
"""Bilgisayar mühendisliği yolu — Faz 16b … 19.

Sıra: çevre/depolama/saat → dayanak → sistem yazılımı → veri yapıları → programlama uzmanlığı.
Faz 16 donanım çekirdeği korunur (kimliğe göre birleşir).
Eğitim özeti. Telifli tam metin yok. Saldırı/exploit tarifi yok.
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

from bm_derin_icerik import KATMANLAR, KAVRAMLAR_YENI

def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_katman(key: str, spec: dict) -> dict:
    dest = KAT / key
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        f"# {spec['baslik']}",
        "",
        f"Kaynak: Rüzgar bilgisayar mühendisliği Faz {spec['faz']}. Eğitim özeti. Exploit yok.",
        "",
    ]
    for i, (title, text) in enumerate(spec["parcalar"], 1):
        body += [f"## {i}. {title}", "", text, ""]
    (incr / f"{key}_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": key,
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "bilgisayar_muhendisligi",
        "faz": spec["faz"],
        "dil": "tr",
        "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi/katmanlar/{key}",
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


def _merge() -> list[dict]:
    by_id: dict[str, dict] = {}
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
                by_id[kid] = row
    for row in KAVRAMLAR_YENI:
        by_id[str(row["id"])] = row
    return list(by_id.values())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    mans = []
    for key, spec in KATMANLAR.items():
        man = _write_katman(key, spec)
        mans.append(man)
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
                "not": f"Faz {spec['faz']}; eğitim; exploit yok.",
            }
        )
        print(f"  [ok] {key} parca={man['parca_sayisi']}")
    rows = _merge()
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    md_files = [p for p in OUT.rglob("*.md") if p.name != "README.md"]
    chars = sum(len(p.read_text(encoding="utf-8")) for p in md_files)
    cat = {
        "domain": "bilgisayar_muhendisligi",
        "updated_utc": _utc(),
        "politika": "Eğitim özeti. Telifli tam metin yok. Saldırı/exploit yok.",
        "katmanlar": [m["katman_id"] for m in mans],
        "sayilar": {
            "md_dosya": len(md_files),
            "karakter": chars,
            "kavram": len(rows),
        },
    }
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Bilgisayar mühendisliği\n\n"
        "Faz 16 donanım çekirdeği korunur.\n\n"
        "## Faz 16b\n`katmanlar/cevre_depolama_saat`\n\n"
        "## Faz 16c — dayanak\n`katmanlar/dayanak`\n\n"
        "## Faz 17 — sistem yazılımı\n`katmanlar/sistem_yazilim`\n\n"
        "## Faz 18 — veri yapıları\n`katmanlar/veri_yapilari`\n\n"
        "## Faz 19 — programlama uzmanlığı\n`katmanlar/programlama_uzmanlik`\n\n"
        f"MD: **{len(md_files)}** · Kavram: **{len(rows)}**\n\n"
        "Uygulama pratiği programlama motorundadır. Bu raf kavram öğretir.\n\n"
        "**Politika:** Eğitim · exploit yok\n"
        "**Script:** `faz16_bilgisayar_muhendisligi_ingest.py` · "
        "`faz16b_bilgisayar_yol_ingest.py` · "
        "**Anlık:** `ruzgar_bilgisayar_kutuphane.py`\n",
        encoding="utf-8",
    )
    print(f"YOL md={len(md_files)} kavram={len(rows)} char={chars}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
