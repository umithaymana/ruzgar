# -*- coding: utf-8 -*-
"""Tevbe 38-129: Diyanet Kur'an Yolu cilt 3 PDF'den tamamla (EPUB'ta yok)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "02_tefsir"
OUT = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "kuran_yolu"
MANIFEST = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "manifest.json"


def main() -> None:
    pdf = STAGE / "kuran_yolu_tefsir_c3.pdf"
    reader = PdfReader(str(pdf))
    pages = []
    for i in range(6, min(90, len(reader.pages))):
        t = reader.pages[i].extract_text() or ""
        pages.append((i + 1, t))

    text_parts = []
    for n, t in pages:
        if n >= 79 and re.search(r"10\s*/\s*Y[ÛU]NUS", t):
            if not re.search(r"9\s*/\s*TEVBE|Tevbe S", t, re.I):
                break
        text_parts.append(t)
    tevbe_text = "\n\n".join(text_parts).replace("−", "–").replace("—", "–")

    matches = []
    for m in re.finditer(r"(\d{1,3})\s*[–\-]\s*(\d{1,3})", tevbe_text):
        a, b = int(m.group(1)), int(m.group(2))
        if 38 <= a <= 129 and a <= b <= 129:
            matches.append((m.start(), a, b))

    filt = []
    for pos, a, b in matches:
        if filt and pos - filt[-1][0] < 30 and filt[-1][1] == a:
            continue
        filt.append((pos, a, b))

    blocks = []
    for i, (pos, a, b) in enumerate(filt):
        end = filt[i + 1][0] if i + 1 < len(filt) else len(tevbe_text)
        chunk = tevbe_text[pos:end]
        meal = ""
        tefsir = ""
        mm = re.search(r"Meâli\s*(.*?)(?=Tefsiri|$)", chunk, re.S | re.I)
        tm = re.search(r"Tefsiri\s*(.*)", chunk, re.S | re.I)
        if mm:
            meal = re.sub(r"\s+", " ", mm.group(1)).strip()
        if tm:
            tefsir = re.sub(r"\s+", " ", tm.group(1)).strip()
        if len(meal) + len(tefsir) < 40:
            continue
        blocks.append(
            {
                "collection": "din_02_tefsir",
                "tip": "ayet_tefsir",
                "eser": "Kur'an Yolu Türkçe Meâl ve Tefsir",
                "cilt": 3,
                "sure_no": 9,
                "sure_adi_tr": "Tevbe",
                "ayet_bas": a,
                "ayet_bit": b,
                "text_ar": "",
                "meal": meal[:20000],
                "tefsir": tefsir[:50000],
                "kaynak": "diyanet:kuran_yolu_tefsir:c3:pdf:id3790",
                "dosya": "kuran_yolu_tefsir_c3.pdf",
            }
        )

    blok_path = OUT / "tefsir_bloklari.jsonl"
    ayet_path = OUT / "tefsir_ayet_indeks.jsonl"
    existing = [
        json.loads(l)
        for l in blok_path.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    existing = [
        b
        for b in existing
        if not (b.get("sure_no") == 9 and b.get("ayet_bas", 0) >= 38)
    ]
    existing.extend(blocks)
    with blok_path.open("w", encoding="utf-8") as f:
        for b in existing:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    rows = []
    for b in existing:
        for a in range(b["ayet_bas"], b["ayet_bit"] + 1):
            rows.append(
                {
                    "collection": "din_02_tefsir",
                    "sure_no": b["sure_no"],
                    "sure_adi_tr": b["sure_adi_tr"],
                    "ayet_no": a,
                    "ayet_bas": b["ayet_bas"],
                    "ayet_bit": b["ayet_bit"],
                    "cilt": b["cilt"],
                    "meal_blok": b["meal"],
                    "tefsir_blok": b["tefsir"],
                    "kaynak": b["kaynak"],
                }
            )
    with ayet_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    have = {(r["sure_no"], r["ayet_no"]) for r in rows}
    miss = [(9, a) for a in range(38, 130) if (9, a) not in have]
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    man["qa"]["blok_adet"] = len(existing)
    man["qa"]["ayet_indeks_adet"] = len(rows)
    man["qa"]["tevbe_pdf_tamamlanan_blok"] = len(blocks)
    man["bilinen_eksikler"] = [
        {
            "sure": 9,
            "durum": "pdf_c3_ile_tamamlandi" if not miss else "kismen",
            "eksik_kalan": miss,
            "eklenen_blok": len(blocks),
        }
    ]
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "pdf_blocks": len(blocks),
                "total_blocks": len(existing),
                "ayet_indeks": len(rows),
                "tevbe_38_129_miss": len(miss),
                "sample": [(b["ayet_bas"], b["ayet_bit"]) for b in blocks[:8]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
