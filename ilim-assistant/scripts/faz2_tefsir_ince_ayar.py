# -*- coding: utf-8 -*-
"""Tefsir ince ayar: eksik/bos ayetleri PDF'den tamamla (Tevbe + Haşr vb.)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "02_tefsir"
OUT = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "kuran_yolu"
MANIFEST = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "manifest.json"

AYET_SAYILARI = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111,
    110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45,
    83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55,
    78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20,
    56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21,
    11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
]

SURE_ADLARI = [
    "Fatiha", "Bakara", "Al-i Imran", "Nisa", "Maide", "Enam", "Araf", "Enfal",
    "Tevbe", "Yunus", "Hud", "Yusuf", "Rad", "Ibrahim", "Hicr", "Nahl", "Isra",
    "Kehf", "Meryem", "Taha", "Enbiya", "Hac", "Muminun", "Nur", "Furkan",
    "Suara", "Neml", "Kasas", "Ankebut", "Rum", "Lokman", "Secde", "Ahzab",
    "Sebe", "Fatir", "Yasin", "Saffat", "Sad", "Zumer", "Mumin", "Fussilet",
    "Sura", "Zuhruf", "Duhan", "Casiye", "Ahkaf", "Muhammed", "Fetih", "Hucurat",
    "Kaf", "Zariyat", "Tur", "Necm", "Kamer", "Rahman", "Vakia", "Hadid",
    "Mucadele", "Hasr", "Mumtehine", "Saff", "Cuma", "Munafikun", "Tegabun",
    "Talak", "Tahrim", "Mulk", "Kalem", "Hakka", "Mearic", "Nuh", "Cin",
    "Muzzemmil", "Muddessir", "Kiyame", "Insan", "Murselat", "Nebe", "Naziat",
    "Abese", "Tekvir", "Infitar", "Mutaffifin", "Insikak", "Buruc", "Tarik",
    "Ala", "Gasiye", "Fecr", "Beled", "Sems", "Leyl", "Duha", "Insirah", "Tin",
    "Alak", "Kadr", "Beyyine", "Zilzal", "Adiyat", "Karia", "Tekasur", "Asr",
    "Humaze", "Fil", "Kureys", "Maun", "Kevser", "Kafirun", "Nasr", "Tebbet",
    "Ihlas", "Felak", "Nas",
]


def extract_pages(pdf: Path, start_1based: int, end_1based: int) -> str:
    r = PdfReader(str(pdf))
    parts = []
    for i in range(start_1based - 1, min(end_1based, len(r.pages))):
        t = r.pages[i].extract_text() or ""
        parts.append(t)
    return "\n\n".join(parts)


def normalize(s: str) -> str:
    s = s.replace("−", "–").replace("—", "–").replace("−", "–")
    s = s.replace("\u00ad", "")  # soft hyphen
    return s


def parse_range_blocks(text: str, ayet_min: int, ayet_max: int) -> list[dict]:
    """Find 'N – M' / 'N' headers and split meal/tefsir sections."""
    text = normalize(text)
    # Candidate range markers: line-ish or before Meâli
    pat = re.compile(
        r"(?:(?<=\n)|(?<=\s)|^)(\d{1,3})\s*[–\-]\s*(\d{1,3})(?=\s*(?:Meâli|MEÂLİ|Meal|Tefsiri|\n|$))",
        re.M,
    )
    singles = re.compile(
        r"(?:(?<=\n)|(?<=\s)|^)(\d{1,3})(?=\s*(?:Meâli|MEÂLİ|Meal)\b)",
        re.M,
    )
    marks: list[tuple[int, int, int]] = []
    for m in pat.finditer(text):
        a, b = int(m.group(1)), int(m.group(2))
        if ayet_min <= a <= ayet_max and a <= b <= ayet_max:
            marks.append((m.start(), a, b))
    for m in singles.finditer(text):
        a = int(m.group(1))
        if ayet_min <= a <= ayet_max:
            marks.append((m.start(), a, a))
    marks.sort()
    # dedupe near-identical starts
    filt: list[tuple[int, int, int]] = []
    for pos, a, b in marks:
        if filt and abs(pos - filt[-1][0]) < 40 and filt[-1][1] == a and filt[-1][2] == b:
            continue
        filt.append((pos, a, b))

    blocks = []
    for i, (pos, a, b) in enumerate(filt):
        end = filt[i + 1][0] if i + 1 < len(filt) else len(text)
        chunk = text[pos:end]
        meal = ""
        tefsir = ""
        mm = re.search(r"Me[âa]li\s*(.*?)(?=Tefsiri|$)", chunk, re.S | re.I)
        tm = re.search(r"Tefsiri\s*(.*)", chunk, re.S | re.I)
        if mm:
            meal = re.sub(r"\s+", " ", mm.group(1)).strip()
        if tm:
            tefsir = re.sub(r"\s+", " ", tm.group(1)).strip()
            # cut trailing next-surah noise
            tefsir = re.split(r"\d+\s*/\s*[A-ZÇĞİÖŞÜÂÎÛ]", tefsir, maxsplit=1)[0].strip()
        if len(meal) + len(tefsir) < 30:
            continue
        blocks.append({"ayet_bas": a, "ayet_bit": b, "meal": meal, "tefsir": tefsir})
    return blocks


def load_blocks() -> list[dict]:
    p = OUT / "tefsir_bloklari.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def save_all(blocks: list[dict]) -> dict:
    # dedupe keep longest
    best: dict[tuple[int, int, int], tuple[int, dict]] = {}
    for b in blocks:
        k = (b["sure_no"], b["ayet_bas"], b["ayet_bit"])
        score = len(b.get("tefsir") or "") + len(b.get("meal") or "")
        if k not in best or score > best[k][0]:
            best[k] = (score, b)
    deduped = [v[1] for v in best.values()]
    deduped.sort(key=lambda x: (x["sure_no"], x["ayet_bas"], x["ayet_bit"]))

    # Also build coverage map preferring specific ranges covering each ayah
    # For each ayah pick the block with smallest span that covers it and has content
    cover: dict[tuple[int, int], dict] = {}
    for b in deduped:
        span = b["ayet_bit"] - b["ayet_bas"]
        has = bool((b.get("tefsir") or "").strip() or (b.get("meal") or "").strip())
        if not has:
            continue
        for a in range(b["ayet_bas"], b["ayet_bit"] + 1):
            key = (b["sure_no"], a)
            prev = cover.get(key)
            if not prev:
                cover[key] = b
                continue
            prev_span = prev["ayet_bit"] - prev["ayet_bas"]
            prev_score = len(prev.get("tefsir") or "") + len(prev.get("meal") or "")
            score = len(b.get("tefsir") or "") + len(b.get("meal") or "")
            # prefer smaller span if both have tefsir; else richer text
            if (b.get("tefsir") and not prev.get("tefsir")) or (
                bool(b.get("tefsir")) == bool(prev.get("tefsir"))
                and (span < prev_span or (span == prev_span and score > prev_score))
            ):
                cover[key] = b

    with (OUT / "tefsir_bloklari.jsonl").open("w", encoding="utf-8") as f:
        for b in deduped:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    rows = []
    for s, n in enumerate(AYET_SAYILARI, 1):
        for a in range(1, n + 1):
            b = cover.get((s, a))
            if not b:
                continue
            rows.append(
                {
                    "collection": "din_02_tefsir",
                    "sure_no": s,
                    "sure_adi_tr": SURE_ADLARI[s - 1],
                    "ayet_no": a,
                    "ayet_bas": b["ayet_bas"],
                    "ayet_bit": b["ayet_bit"],
                    "cilt": b.get("cilt"),
                    "meal_blok": b.get("meal") or "",
                    "tefsir_blok": b.get("tefsir") or "",
                    "kaynak": b.get("kaynak") or "",
                }
            )
    with (OUT / "tefsir_ayet_indeks.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    miss = []
    empty_t = []
    empty_m = []
    by = {(r["sure_no"], r["ayet_no"]): r for r in rows}
    for s, n in enumerate(AYET_SAYILARI, 1):
        for a in range(1, n + 1):
            r = by.get((s, a))
            if not r:
                miss.append((s, a))
                continue
            if not (r.get("tefsir_blok") or "").strip():
                empty_t.append((s, a))
            if not (r.get("meal_blok") or "").strip():
                empty_m.append((s, a))

    qa = {
        "blok_adet": len(deduped),
        "ayet_indeks_adet": len(rows),
        "hedef": 6236,
        "eksik_ayet": miss,
        "bos_tefsir": empty_t,
        "bos_meal": empty_m,
        "tam": len(miss) == 0 and len(empty_t) == 0 and len(empty_m) == 0,
    }
    if MANIFEST.exists():
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        man = {}
    man["qa"] = {**(man.get("qa") or {}), **qa}
    man["cilt_sayisi"] = 5
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return qa


def upsert_pdf_blocks(sure_no: int, cilt: int, kaynak: str, dosya: str, parsed: list[dict], existing: list[dict]) -> list[dict]:
    out = [
        b
        for b in existing
        if not (
            b.get("sure_no") == sure_no
            and b.get("kaynak", "").endswith("pdf:id3790")
            and sure_no == 9
        )
        and not (
            b.get("sure_no") == sure_no
            and "pdf" in (b.get("kaynak") or "")
            and sure_no == 59
        )
    ]
    # For tevbe: remove weak empty-ish blocks overlapping filled ranges from PDF
    for p in parsed:
        out.append(
            {
                "collection": "din_02_tefsir",
                "tip": "ayet_tefsir",
                "eser": "Kur'an Yolu Türkçe Meâl ve Tefsir",
                "cilt": cilt,
                "sure_no": sure_no,
                "sure_adi_tr": SURE_ADLARI[sure_no - 1],
                "ayet_bas": p["ayet_bas"],
                "ayet_bit": p["ayet_bit"],
                "text_ar": "",
                "meal": p["meal"][:30000],
                "tefsir": p["tefsir"][:80000],
                "kaynak": kaynak,
                "dosya": dosya,
            }
        )
    return out


def main() -> None:
    existing = load_blocks()

    # --- Tevbe 38-129 from c3 PDF pages 7-78 ---
    pdf3 = STAGE / "kuran_yolu_tefsir_c3.pdf"
    if pdf3.exists():
        tevbe = extract_pages(pdf3, 7, 78)
        parsed = parse_range_blocks(tevbe, 38, 129)
        # replace previous pdf tevbe blocks
        existing = [
            b
            for b in existing
            if not (b.get("sure_no") == 9 and "pdf" in (b.get("kaynak") or ""))
        ]
        # also drop weak empty epub blocks for tevbe 38+ with empty tefsir/meal so pdf wins
        existing = [
            b
            for b in existing
            if not (
                b.get("sure_no") == 9
                and b.get("ayet_bas", 0) >= 38
                and not (b.get("tefsir") or "").strip()
            )
        ]
        for p in parsed:
            existing.append(
                {
                    "collection": "din_02_tefsir",
                    "tip": "ayet_tefsir",
                    "eser": "Kur'an Yolu Türkçe Meâl ve Tefsir",
                    "cilt": 3,
                    "sure_no": 9,
                    "sure_adi_tr": "Tevbe",
                    "ayet_bas": p["ayet_bas"],
                    "ayet_bit": p["ayet_bit"],
                    "text_ar": "",
                    "meal": p["meal"][:30000],
                    "tefsir": p["tefsir"][:80000],
                    "kaynak": "diyanet:kuran_yolu_tefsir:c3:pdf:id3790",
                    "dosya": "kuran_yolu_tefsir_c3.pdf",
                }
            )
        print("tevbe_pdf_blocks", len(parsed))

    # --- Haşr from c5 PDF (download may still be running) ---
    pdf5 = STAGE / "kuran_yolu_tefsir_c5.pdf"
    if pdf5.exists() and pdf5.stat().st_size > 1_000_000:
        r = PdfReader(str(pdf5))
        # find TOC / Haşr page range
        start = end = None
        for i in range(min(20, len(r.pages))):
            t = r.pages[i].extract_text() or ""
            m = re.search(
                r"(\d+)\s*[–\-]\s*(\d+)\s*59\s*/\s*HA[ŞS]R|HA[ŞS]R[^\n]{0,40}?(\d+)\s*[–\-]\s*(\d+)",
                t,
                re.I,
            )
            if m:
                nums = [int(x) for x in m.groups() if x]
                if len(nums) >= 2:
                    start, end = nums[0], nums[1]
                    break
            # alternate TOC style
            m2 = re.search(r"(\d+)\s*[–\-]\s*(\d+)\s+59\s*/\s*HA", t, re.I)
            if m2:
                start, end = int(m2.group(1)), int(m2.group(2))
                break
        if not start:
            # brute search for Haşr header
            for i, page in enumerate(r.pages):
                t = page.extract_text() or ""
                if re.search(r"59\s*\(.*\)\s*Ha[şs]r\s*S", t, re.I) or re.search(
                    r"HA[ŞS]R SÛRESİ", t, re.I
                ):
                    start = i + 1
                    break
            if start:
                end = min(start + 40, len(r.pages))
        print("hasr_pages", start, end)
        if start and end:
            hasr = extract_pages(pdf5, start, end)
            # stop at next surah if present
            hasr = re.split(r"\n\s*60\s*\(|\n\s*60\s*/\s*MÜMTEHİNE", hasr, maxsplit=1)[0]
            parsed_h = parse_range_blocks(hasr, 1, 24)
            existing = [
                b
                for b in existing
                if not (b.get("sure_no") == 59 and "pdf" in (b.get("kaynak") or ""))
            ]
            for p in parsed_h:
                existing.append(
                    {
                        "collection": "din_02_tefsir",
                        "tip": "ayet_tefsir",
                        "eser": "Kur'an Yolu Türkçe Meâl ve Tefsir",
                        "cilt": 5,
                        "sure_no": 59,
                        "sure_adi_tr": "Hasr",
                        "ayet_bas": p["ayet_bas"],
                        "ayet_bit": p["ayet_bit"],
                        "text_ar": "",
                        "meal": p["meal"][:30000],
                        "tefsir": p["tefsir"][:80000],
                        "kaynak": "diyanet:kuran_yolu_tefsir:c5:pdf:id3792",
                        "dosya": "kuran_yolu_tefsir_c5.pdf",
                    }
                )
            print("hasr_pdf_blocks", len(parsed_h))
    else:
        print("hasr_pdf_yok")

    # Fill remaining empty meal from 01_kuran meal where tefsir block exists but meal empty
    kuran_path = ROOT / "knowledge" / "ilim" / "din" / "01_kuran" / "ayetler.jsonl"
    kuran = {}
    if kuran_path.exists():
        for line in kuran_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            kuran[(row["sure_no"], row["ayet_no"])] = (
                row.get("meal_tr")
                or row.get("meal_tr_kuran_yolu")
                or row.get("meal_tr_diyanet")
                or ""
            )

    # For ayahs still missing after save, create singleton blocks from neighboring PDF re-parse
    qa = save_all(existing)
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
