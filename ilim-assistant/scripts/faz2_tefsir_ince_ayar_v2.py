# -*- coding: utf-8 -*-
"""Tefsir ince ayar v2: PDF 'SÛRESİ · ayet' bloklarını tam çıkar + meal yedekle."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "02_tefsir"
OUT = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "kuran_yolu"
MANIFEST = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "manifest.json"
KURAN = ROOT / "knowledge" / "ilim" / "din" / "01_kuran" / "ayetler.jsonl"

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


def load_kuran_meals() -> dict[tuple[int, int], str]:
    out = {}
    for line in KURAN.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        meal = (
            r.get("meal_tr")
            or r.get("meal_tr_kuran_yolu")
            or r.get("meal_tr_diyanet")
            or ""
        ).strip()
        out[(r["sure_no"], r["ayet_no"])] = meal
    return out


def pages_text(pdf: Path, a: int, b: int) -> str:
    r = PdfReader(str(pdf))
    parts = []
    for i in range(a - 1, min(b, len(r.pages))):
        parts.append(r.pages[i].extract_text() or "")
    return "\n".join(parts)


def parse_sure_dot_blocks(text: str, sure_no: int, ayet_lo: int, ayet_hi: int) -> list[dict]:
    """Parse Meâl(i)/Tefsiri blocks; ayet aralığını meal içindeki N. numaralarından çıkar."""
    text = text.replace("−", "–").replace("—", "–")
    blocks: list[dict] = []

    meali_starts = list(re.finditer(r"Meâl\.?i?\s+", text, re.I))
    for i, m in enumerate(meali_starts):
        start = m.end()
        end = meali_starts[i + 1].start() if i + 1 < len(meali_starts) else len(text)
        chunk = text[start:end]
        tm = re.search(r"Tefsiri\s*(.*)", chunk, re.S | re.I)
        if tm:
            meal_raw = chunk[: tm.start()]
            tefsir_raw = tm.group(1)
        else:
            # Bakara 212 style: '212. meal' then '212. tefsir' (no Tefsiri label)
            meal_raw = ""
            tefsir_raw = ""
            # Prefer back-header ayet no
            back = text[max(0, m.start() - 200) : m.start()]
            hm = re.search(
                rf"{sure_no}\s*/\s*[^\n]*·\s*(\d{{1,3}})(?:\s*[–\-]\s*(\d{{1,3}}))?\s*$",
                back,
                re.M | re.I,
            )
            a_hint = int(hm.group(1)) if hm else None
            if a_hint is not None and hm.group(2) is None:
                parts = re.split(rf"(?:^|\n)\s*{a_hint}\.\s+", chunk)
                if len(parts) >= 3:
                    meal_raw = parts[1]
                    tefsir_raw = parts[2]
                elif len(parts) == 2:
                    meal_raw = parts[1]
            if not meal_raw and not tefsir_raw:
                continue

        tefsir_raw = re.split(rf"\n\s*{sure_no}\s*/\s*", tefsir_raw, maxsplit=1)[0]
        # stop tefsir at bare next range label near end (e.g. '128 – 129')
        tefsir_raw = re.split(
            r"\n\s*\d{1,3}\s*[–\-]\s*\d{1,3}\s*(?:\n\d+\s*){0,6}\s*$",
            tefsir_raw,
            maxsplit=1,
        )[0]
        meal = re.sub(r"\s+", " ", meal_raw).strip()
        tefsir = re.sub(r"\s+", " ", tefsir_raw).strip()

        nums = [int(x) for x in re.findall(r"(?:^|\s)(\d{1,3})\.\s", meal_raw)]
        if not nums:
            rm = re.match(r"\s*(\d{1,3})\s*[–\-]\s*(\d{1,3})\.", tefsir_raw)
            if rm:
                nums = list(range(int(rm.group(1)), int(rm.group(2)) + 1))
            else:
                sm = re.match(r"\s*(\d{1,3})\.", tefsir_raw)
                if sm:
                    nums = [int(sm.group(1))]
        back = text[max(0, m.start() - 250) : m.start()]
        header_range = None
        bm = re.search(
            rf"(?:·\s*)?(\d{{1,3}})\s*[–\-]\s*(\d{{1,3}})\s*$|(?:·\s*)(\d{{1,3}})\s*$",
            back,
            re.M,
        )
        if bm:
            if bm.group(1) and bm.group(2):
                header_range = (int(bm.group(1)), int(bm.group(2)))
            elif bm.group(3):
                header_range = (int(bm.group(3)), int(bm.group(3)))
        if not nums and header_range:
            nums = list(range(header_range[0], header_range[1] + 1))
        if not nums:
            continue
        a, b = min(nums), max(nums)
        # Header aralığı meal numaralarını kapsıyorsa (eksik 24. gibi) header'ı kullan
        if header_range and header_range[0] <= a and b <= header_range[1]:
            a, b = header_range
        if b < ayet_lo or a > ayet_hi:
            continue
        a = max(a, ayet_lo)
        b = min(b, ayet_hi)
        if len(meal) + len(tefsir) < 20:
            continue
        blocks.append({"ayet_bas": a, "ayet_bit": b, "meal": meal, "tefsir": tefsir})

    best: dict[tuple[int, int], dict] = {}
    for b in blocks:
        k = (b["ayet_bas"], b["ayet_bit"])
        prev = best.get(k)
        if not prev or len(b["tefsir"]) > len(prev["tefsir"]):
            best[k] = b
    return sorted(best.values(), key=lambda x: (x["ayet_bas"], x["ayet_bit"]))


def make_block(sure_no: int, cilt: int, kaynak: str, dosya: str, p: dict) -> dict:
    return {
        "collection": "din_02_tefsir",
        "tip": "ayet_tefsir",
        "eser": "Kur'an Yolu Türkçe Meâl ve Tefsir",
        "cilt": cilt,
        "sure_no": sure_no,
        "sure_adi_tr": SURE_ADLARI[sure_no - 1],
        "ayet_bas": p["ayet_bas"],
        "ayet_bit": p["ayet_bit"],
        "text_ar": "",
        "meal": (p.get("meal") or "")[:30000],
        "tefsir": (p.get("tefsir") or "")[:100000],
        "kaynak": kaynak,
        "dosya": dosya,
    }


def extract_ayah_meal(block_meal: str, ayet_no: int) -> str:
    """Multi-ayah meal bloğundan 'N. ...' dilimini çıkar."""
    if not block_meal:
        return ""
    # Numbered items: 38. ... 39. ...
    parts = re.split(r"(?:^|\s)(\d{1,3})\.\s+", block_meal)
    # parts: [pre, num, text, num, text, ...]
    by_no: dict[int, str] = {}
    i = 1
    while i + 1 < len(parts):
        try:
            n = int(parts[i])
        except ValueError:
            i += 1
            continue
        by_no[n] = re.sub(r"\s+", " ", parts[i + 1]).strip()
        i += 2
    text = by_no.get(ayet_no, "")
    # cut at next ayah residue if any leaked
    if text and len(text) > 1500:
        text = text[:1500].rsplit(" ", 1)[0]
    return text


def rebuild(blocks: list[dict], meals: dict[tuple[int, int], str]) -> dict:
    # dedupe by sure/bas/bit keep richest
    best: dict[tuple[int, int, int], dict] = {}
    for b in blocks:
        k = (b["sure_no"], b["ayet_bas"], b["ayet_bit"])
        score = len(b.get("tefsir") or "") * 3 + len(b.get("meal") or "")
        prev = best.get(k)
        if not prev or score > len(prev.get("tefsir") or "") * 3 + len(prev.get("meal") or ""):
            best[k] = b
    deduped = sorted(best.values(), key=lambda x: (x["sure_no"], x["ayet_bas"], x["ayet_bit"]))

    # per-ayah coverage: prefer block with tefsir, then smaller span, then longer text
    cover: dict[tuple[int, int], dict] = {}
    for b in deduped:
        span = b["ayet_bit"] - b["ayet_bas"]
        for a in range(b["ayet_bas"], b["ayet_bit"] + 1):
            key = (b["sure_no"], a)
            cur = cover.get(key)
            if not cur:
                cover[key] = b
                continue
            cur_span = cur["ayet_bit"] - cur["ayet_bas"]
            cur_has = bool((cur.get("tefsir") or "").strip())
            new_has = bool((b.get("tefsir") or "").strip())
            if new_has and not cur_has:
                cover[key] = b
            elif new_has == cur_has and (
                span < cur_span
                or (
                    span == cur_span
                    and len(b.get("tefsir") or "") > len(cur.get("tefsir") or "")
                )
            ):
                cover[key] = b

    rows = []
    for s, n in enumerate(AYET_SAYILARI, 1):
        for a in range(1, n + 1):
            b = cover.get((s, a))
            if not b:
                continue
            block_meal = (b.get("meal") or "").strip()
            kmeal = (meals.get((s, a), "") or "").strip()
            # Prefer clean per-ayah: extract from block, else short kuran meal, else block
            meal = extract_ayah_meal(block_meal, a) if b["ayet_bas"] != b["ayet_bit"] else ""
            if not meal and kmeal and len(kmeal) <= 1200:
                meal = kmeal
            if not meal and block_meal and len(block_meal) <= 1200:
                meal = block_meal
            if not meal and kmeal:
                # last resort: first sentence-ish of polluted meal
                meal = re.split(r"\s*\[\d+\]\s*", kmeal, maxsplit=1)[0].strip()
                if len(meal) > 800:
                    meal = meal[:800].rsplit(" ", 1)[0]
            if not meal:
                meal = block_meal[:800] if block_meal else ""
            tefsir = (b.get("tefsir") or "").strip()
            rows.append(
                {
                    "collection": "din_02_tefsir",
                    "sure_no": s,
                    "sure_adi_tr": SURE_ADLARI[s - 1],
                    "ayet_no": a,
                    "ayet_bas": b["ayet_bas"],
                    "ayet_bit": b["ayet_bit"],
                    "cilt": b.get("cilt"),
                    "meal_blok": meal,
                    "tefsir_blok": tefsir,
                    "kaynak": b.get("kaynak") or "",
                }
            )

    with (OUT / "tefsir_bloklari.jsonl").open("w", encoding="utf-8") as f:
        for b in deduped:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    with (OUT / "tefsir_ayet_indeks.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    by = {(r["sure_no"], r["ayet_no"]): r for r in rows}
    miss, empty_t, empty_m = [], [], []
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
        "tam_meal_tefsir": len(miss) == 0 and len(empty_t) == 0 and len(empty_m) == 0,
        "cilt_sayisi": 5,
    }
    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    man["cilt_sayisi"] = 5
    man["qa"] = {**(man.get("qa") or {}), **qa}
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return qa


def main() -> None:
    meals = load_kuran_meals()
    existing = [
        json.loads(l)
        for l in (OUT / "tefsir_bloklari.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]

    # Drop previous weak PDF patches for Tevbe/Haşr/Bakara212; re-add fresh
    existing = [
        b
        for b in existing
        if not (
            "pdf" in (b.get("kaynak") or "")
            and (
                (b.get("sure_no") == 9 and b.get("ayet_bas", 0) >= 38)
                or b.get("sure_no") == 59
                or (b.get("sure_no") == 2 and b.get("ayet_bas") == 212)
            )
        )
    ]

    # Tevbe 38-129 from c3 PDF (TOC: ~p8–end of Tevbe before Yunus)
    pdf3 = STAGE / "kuran_yolu_tefsir_c3.pdf"
    tevbe_txt = pages_text(pdf3, 8, 80)
    tevbe_blocks = parse_sure_dot_blocks(tevbe_txt, 9, 38, 129)
    print(
        "tevbe_blocks",
        len(tevbe_blocks),
        "ranges",
        [(b["ayet_bas"], b["ayet_bit"]) for b in tevbe_blocks],
    )
    for p in tevbe_blocks:
        existing.append(
            make_block(9, 3, "diyanet:kuran_yolu_tefsir:c3:pdf:id3790", "kuran_yolu_tefsir_c3.pdf", p)
        )

    # Haşr full from c5 PDF (intro ~280, ayets ~283-305)
    pdf5 = STAGE / "kuran_yolu_tefsir_c5.pdf"
    hasr_txt = pages_text(pdf5, 283, 305)
    hasr_blocks = parse_sure_dot_blocks(hasr_txt, 59, 1, 24)
    print(
        "hasr_blocks",
        len(hasr_blocks),
        [(b["ayet_bas"], b["ayet_bit"], len(b["tefsir"]), len(b["meal"])) for b in hasr_blocks],
    )
    for p in hasr_blocks:
        existing.append(
            make_block(59, 5, "diyanet:kuran_yolu_tefsir:c5:pdf:id3792", "kuran_yolu_tefsir_c5.pdf", p)
        )

    # Bakara 212 from c1 PDF page 329 (known; no Tefsiri label)
    pdf1 = STAGE / "kuran_yolu_tefsir_c1.pdf"
    bt = pages_text(pdf1, 328, 330)
    bblocks = parse_sure_dot_blocks(bt, 2, 212, 212)
    if not any(b["ayet_bas"] == 212 and b["ayet_bit"] == 212 and (b.get("tefsir") or "").strip() for b in bblocks):
        m = re.search(
            r"Meâli\s*212\.\s*(.*?)\s*212\.\s+(.*?)(?=\n\s*212\s*$|\n\s*2\s*/|\Z)",
            bt,
            re.S | re.I,
        )
        if m:
            bblocks = [
                {
                    "ayet_bas": 212,
                    "ayet_bit": 212,
                    "meal": re.sub(r"\s+", " ", m.group(1)).strip(),
                    "tefsir": re.sub(r"\s+", " ", m.group(2)).strip(),
                }
            ]
    print(
        "bakara212",
        [
            (b["ayet_bas"], b["ayet_bit"], len(b.get("tefsir") or ""), len(b.get("meal") or ""))
            for b in bblocks
            if b["ayet_bas"] <= 212 <= b["ayet_bit"]
        ],
    )
    for p in bblocks:
        if p["ayet_bas"] <= 212 <= p["ayet_bit"] and p["ayet_bit"] - p["ayet_bas"] <= 0:
            existing.append(
                make_block(2, 1, "diyanet:kuran_yolu_tefsir:c1:pdf:id3788", "kuran_yolu_tefsir_c1.pdf", p)
            )

    qa = rebuild(existing, meals)
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
