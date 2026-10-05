# -*- coding: utf-8 -*-
"""Diyanet resmi yayınlarından Kur'an mushaf + meal indeksleme (Faz 1).

Kaynaklar (kuran.diyanet.gov.tr / dijital.diyanet.gov.tr):
  - kuran_mushaf.docx          Arapça mushaf (Word)
  - diyanet_meali.epub         DİB Kur'an-ı Kerim Meali
  - kuran_yolu_meali.epub      Kur'an Yolu Meali
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "01_kuran"
OUT = ROOT / "knowledge" / "ilim" / "din" / "01_kuran"
LEGACY_DIRS = [
    ROOT / "arsiv" / "kuran",
    ROOT / "arsiv" / "Tasavvuf_Kulliyati" / "Kuran_i_Kerim",
]

# Standart mushaf ayet sayıları (114 sure = 6236)
AYET_SAYILARI = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111,
    110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45,
    83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55,
    78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20,
    56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21,
    11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
]

SURE_ADLARI_TR = [
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<script.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?</style>", " ", html)
    html = re.sub(r"(?is)<div[^>]*class=\"_idFootnotes\".*?</div>", " ", html)
    html = re.sub(r"(?is)<sup\b.*?</sup>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p>", "\n", html)
    html = re.sub(r"(?is)</h1>", "\n", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    html = unescape(html)
    html = html.replace("\xa0", " ")
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{2,}", "\n", html)
    return html.strip()


def parse_mushaf_docx(path: Path) -> dict[tuple[int, int], str]:
    """Arapça mushaf: ﴿N﴾ ayet ayırıcı + sure başlıkları."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    xml = unescape(xml)
    xml = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), xml)
    xml = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), xml)

    # Sure başlığı: ﷍﴿N﴾ سُورَةُ ...﷌
    parts = re.split(r"[\ufd4d]?\s*﴿\s*(\d+)\s*﴾\s*(سُورَةُ[^﴿\ufd4c]*)[\ufd4c]?", xml)
    # Alternatif: simpler scan
    out: dict[tuple[int, int], str] = {}
    sure_no = 0
    # Split by surah headers containing سُورَةُ
    chunks = re.split(r"(?=﴿\s*\d+\s*﴾\s*سُورَةُ)", xml)
    for chunk in chunks:
        m_sure = re.search(r"﴿\s*(\d+)\s*﴾\s*سُورَةُ", chunk)
        if not m_sure:
            continue
        sure_no = int(m_sure.group(1))
        body = chunk[m_sure.end() :]
        # remove surah name until first ayah or basmala
        # Split ayahs by ﴿N﴾
        tokens = re.split(r"﴿\s*(\d+)\s*﴾", body)
        # tokens: [preamble, num, text, num, text, ...]
        # For Fatiha: preamble may include ﷽ ﴿1﴾ already consumed? 
        # Actually basmala line: ﷽ ﴿1﴾ then next line starts with text ending ﴿2﴾
        i = 1
        while i + 1 < len(tokens):
            ayet_no = int(tokens[i])
            text = tokens[i + 1]
            # stop at next surah marker remnant
            text = re.split(r"﴿\s*\d+\s*﴾\s*سُورَةُ", text)[0]
            text = text.replace("\ufd4d", " ").replace("\ufd4c", " ")
            text = re.sub(r"\s+", " ", text).strip()
            # drop orphan basmala-only lines without number (already numbered)
            if text.startswith("﷽") and ayet_no == 1 and sure_no == 1:
                # Fatiha 1 is basmala
                text = text.strip()
            elif text == "﷽" or text.startswith("﷽") and len(text) < 5:
                # standalone basmala before ayah 1 of other surahs — not counted
                i += 2
                continue
            # If text begins with ﷽ and ayah is 1 for non-Fatiha, strip basmala
            if sure_no != 1 and text.startswith("﷽"):
                text = text.lstrip("﷽").strip()
            if text:
                out[(sure_no, ayet_no)] = text
            i += 2
    return out


def parse_mushaf_docx_v2(path: Path) -> dict[tuple[int, int], str]:
    """Daha sağlam: satır satır sure/ayet yakala."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    xml = unescape(xml)
    xml = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), xml)
    xml = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), xml)

    out: dict[tuple[int, int], str] = {}
    sure_no = 0
    # Find all surah header positions
    header_re = re.compile(r"﴿\s*(\d+)\s*﴾\s*سُورَةُ")
    headers = list(header_re.finditer(xml))
    for idx, hm in enumerate(headers):
        sure_no = int(hm.group(1))
        start = hm.end()
        end = headers[idx + 1].start() if idx + 1 < len(headers) else len(xml)
        body = xml[start:end]
        # Collect (ayet_no, end_pos) markers
        marks = list(re.finditer(r"﴿\s*(\d+)\s*﴾", body))
        for j, mm in enumerate(marks):
            ayet_no = int(mm.group(1))
            # text is BETWEEN previous mark end and this mark start
            prev_end = marks[j - 1].end() if j > 0 else 0
            text = body[prev_end:mm.start()]
            text = text.replace("\ufd4d", " ").replace("\ufd4c", " ")
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            # Sure adı artığı (başlık satırından sonra kalan)
            text = re.sub(r"^.*?سُورَةُ[^\ufd4c﴾]*", "", text).strip()
            text = re.sub(r"^[^\u0600-\u06FF﷽]*", "", text).strip()
            # İzole besmele (Fatiha dışı surelerde ayet sayılmaz)
            if text == "﷽" or re.fullmatch(r"﷽+", text):
                continue
            if sure_no == 1 and ayet_no == 1:
                # Fatiha 1 = besmele (Diyanet Word'de ﷽)
                if "﷽" in text:
                    text = "﷽"
                text = re.sub(r"^.*?﷽", "﷽", text).strip() or "﷽"
            elif sure_no != 1:
                # ﷽ sonrası asıl ayet metni
                if "﷽" in text:
                    text = text.split("﷽", 1)[-1].strip()
                # Başta kalan kısa sure adı parçaları
                text = re.sub(r"^(?:ال)?[\u0600-\u06FF]{2,20}ِ?\s+(?=قُلْ|الٓ|يٰ|اِذ|تَبَ|قُل)", "", text)
            if not text:
                continue
            out[(sure_no, ayet_no)] = text
    return out


def _expand_ayet_nums(num_blob: str) -> list[int]:
    """'2, 3, 4' veya '6-7' veya '1' -> [2,3,4]."""
    nums: list[int] = []
    blob = (num_blob or "").strip().strip(",").strip()
    if not blob:
        return nums
    for part in re.split(r"[,\s]+", blob):
        part = part.strip().strip(",").strip()
        if not part:
            continue
        if "-" in part or "–" in part:
            bits = re.split(r"[-–]", part, maxsplit=1)
            if len(bits) != 2 or not bits[0].isdigit() or not bits[1].isdigit():
                continue
            a, b = int(bits[0]), int(bits[1])
            if a > b or b - a > 50:
                continue
            nums.extend(range(a, b + 1))
        elif part.isdigit():
            nums.append(int(part))
    return nums


def parse_meal_epub(path: Path, style: str) -> dict[tuple[int, int], dict]:
    """EPUB meal -> {(sure,ayet): {text, birlesik?}}.

    style:
      - diyanet_cep: '1.' / '2, 3, 4.' kalıbı
      - kuran_yolu: '1. ' ayrı ayet
    """
    out: dict[tuple[int, int], dict] = {}
    with zipfile.ZipFile(path) as z:
        names = sorted(
            n
            for n in z.namelist()
            if n.lower().endswith((".xhtml", ".html")) and "OEBPS/" in n
        )
        for name in names:
            raw = z.read(name).decode("utf-8", errors="replace")
            if "_idFootnotes" in raw:
                # keep body only before footnotes already stripped in _strip_html
                pass
            text = _strip_html(raw)
            # Sure başlığı: "1 FÂTİHA SÛRESİ" veya "1. FÂTİHA SÛRESİ"
            sure_matches = list(
                re.finditer(
                    r"(?m)^(?:\s*)(\d{1,3})\s*\.?\s+([^\n]{0,80}?S[ÛU]RES[İI])\s*$",
                    text,
                    re.I,
                )
            )
            if not sure_matches:
                # inline in same line as content
                sure_matches = list(
                    re.finditer(
                        r"(?m)(?:^|\n)\s*(\d{1,3})\s*\.?\s+([A-ZÇĞİÖŞÜÂÎÛâîû][^\n]{0,60}?S[ÛU]RES[İI])",
                        text,
                        re.I,
                    )
                )
            if not sure_matches:
                continue

            for si, sm in enumerate(sure_matches):
                sure_no = int(sm.group(1))
                start = sm.end()
                end = sure_matches[si + 1].start() if si + 1 < len(sure_matches) else len(text)
                body = text[start:end]
                # Skip intro paragraphs until first numbered ayah
                # Pattern: bold numbers at start of ayah blocks
                # Match "1. text" or "2, 3, 4. text"
                # Not: bazı EPUB satırlarında yazım/biçim hatası ",40." şeklinde gelir.
                ayah_re = re.compile(
                    r"(?m)(?:^|\n|,)\s*((?:\d{1,3}(?:\s*[,–-]\s*\d{1,3})*)\s*\.)\s+([^\n]+(?:\n(?!\s*,?\s*\d{1,3}(?:\s*[,–-]\s*\d{1,3})*\s*\.)[^\n]+)*)"
                )
                found = list(ayah_re.finditer(body))
                if not found:
                    ayah_re2 = re.compile(
                        r"(?m)(?:^|\n|,)\s*((?:\d{1,3}(?:\s*,\s*\d{1,3})+|\d{1,3})\.)\s+(.+?)(?=(?:\n\s*,?\s*(?:\d{1,3}(?:\s*,\s*\d{1,3})*|\d{1,3})\.)|\Z)",
                        re.S,
                    )
                    found = list(ayah_re2.finditer(body))

                for fm in found:
                    num_part = fm.group(1).rstrip(".").strip()
                    meal = re.sub(r"\s+", " ", fm.group(2)).strip()
                    # drop "Âmin!" only lines etc. without number already handled
                    if meal.lower().startswith("âmin") and not num_part:
                        continue
                    nums = _expand_ayet_nums(num_part)
                    if not nums:
                        continue
                    # Filter out surah meta false positives (huge intro numbered?)
                    if max(nums) > 300:
                        continue
                    birlesik = len(nums) > 1
                    for n in nums:
                        out[(sure_no, n)] = {
                            "text": meal,
                            "birlesik": birlesik,
                            "birlesik_ayetler": nums if birlesik else None,
                        }
    return out


def archive_legacy() -> list[str]:
    moved = []
    legacy_root = ROOT / "arsiv" / "_legacy_demo" / "kuran_demo_2ayet"
    legacy_root.mkdir(parents=True, exist_ok=True)
    for d in LEGACY_DIRS:
        idx = d / "index.jsonl"
        if not idx.exists():
            continue
        # Yalnızca eski demo (çok küçük) taşınır; tam indeks asla silinmez.
        try:
            nlines = sum(1 for _ in idx.open(encoding="utf-8"))
        except OSError:
            continue
        if nlines > 20:
            continue
        dest = legacy_root / f"{d.name}_index.jsonl"
        shutil.move(str(idx), str(dest))
        moved.append(str(dest.relative_to(ROOT)))
        (d / "README.md").write_text(
            "# Eski demo indeks taşındı\n\n"
            f"Yeni kaynak: `knowledge/ilim/din/01_kuran/`\n"
            f"Eski dosya: `{dest.relative_to(ROOT).as_posix()}`\n",
            encoding="utf-8",
        )
    return moved


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    mushaf_path = STAGE / "kuran_mushaf.docx"
    meal_dib = STAGE / "diyanet_meali.epub"
    meal_ky = STAGE / "kuran_yolu_meali.epub"
    for p in (mushaf_path, meal_dib, meal_ky):
        if not p.exists():
            raise SystemExit(f"Eksik staging dosyası: {p}")

    # Eski 2 ayetlik demoyu önce arşivle; yeni indeks bunun üstüne yazılacak.
    moved = archive_legacy()

    arabic = parse_mushaf_docx_v2(mushaf_path)
    meal_diyanet = parse_meal_epub(meal_dib, "diyanet_cep")
    meal_yolu = parse_meal_epub(meal_ky, "kuran_yolu")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mushaf_arapca").mkdir(exist_ok=True)
    (OUT / "meal").mkdir(exist_ok=True)
    (OUT / "metadata").mkdir(exist_ok=True)

    rows: list[dict] = []
    qa = {
        "sure_beklenen": 114,
        "ayet_beklenen": 6236,
        "arapca_adet": len(arabic),
        "meal_diyanet_adet": len(meal_diyanet),
        "meal_kuran_yolu_adet": len(meal_yolu),
        "sure_eksik_arapca": [],
        "sure_eksik_meal_diyanet": [],
        "sure_eksik_meal_yolu": [],
        "ornekler": [],
    }

    for sure_no in range(1, 115):
        expected = AYET_SAYILARI[sure_no - 1]
        ar_count = sum(1 for a in range(1, expected + 1) if (sure_no, a) in arabic)
        md_count = sum(1 for a in range(1, expected + 1) if (sure_no, a) in meal_diyanet)
        my_count = sum(1 for a in range(1, expected + 1) if (sure_no, a) in meal_yolu)
        if ar_count != expected:
            qa["sure_eksik_arapca"].append({"sure": sure_no, "beklenen": expected, "bulunan": ar_count})
        if md_count != expected:
            qa["sure_eksik_meal_diyanet"].append({"sure": sure_no, "beklenen": expected, "bulunan": md_count})
        if my_count != expected:
            qa["sure_eksik_meal_yolu"].append({"sure": sure_no, "beklenen": expected, "bulunan": my_count})

        for ayet_no in range(1, expected + 1):
            key = (sure_no, ayet_no)
            md = meal_diyanet.get(key) or {}
            my = meal_yolu.get(key) or {}
            meal_dib = md.get("text", "")
            meal_ky = my.get("text", "")
            # Cep Meal EPUB resmi indirmede bazı sureler boş (Neml/Saffat stub).
            # Birincil meal = Kur'an Yolu; Cep Meal boşsa yedek olarak Yolu kullan.
            meal_dib_kaynak = "diyanet_meali.epub"
            if not meal_dib and meal_ky:
                meal_dib = meal_ky
                meal_dib_kaynak = "kuran_yolu_meali.epub (cep_meal_epub_bos_yedek)"
            row = {
                "collection": "din_01_kuran",
                "sure_no": sure_no,
                "sure_adi_tr": SURE_ADLARI_TR[sure_no - 1],
                "ayet_no": ayet_no,
                "text_ar": arabic.get(key, ""),
                "meal_tr": meal_ky or meal_dib,
                "meal_tr_diyanet": meal_dib,
                "meal_tr_kuran_yolu": meal_ky,
                "meal_diyanet_birlesik": bool(md.get("birlesik")),
                "meal_diyanet_birlesik_ayetler": md.get("birlesik_ayetler"),
                "meal_diyanet_kaynak": meal_dib_kaynak,
                "kaynak_ar": "diyanet:kuran.docx:web",
                "kaynak_meal_diyanet": "diyanet:diyanet_meali.epub",
                "kaynak_meal_kuran_yolu": "diyanet:kuran_yolu_meali.epub",
            }
            rows.append(row)

    # index.jsonl
    index_path = OUT / "ayetler.jsonl"
    with index_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # also sync to arsiv indexes for okuma / tercume motorlari
    sync_targets = [
        ROOT / "arsiv" / "kuran" / "index.jsonl",
        ROOT / "arsiv" / "Tasavvuf_Kulliyati" / "Kuran_i_Kerim" / "index.jsonl",
    ]
    for simple_index in sync_targets:
        simple_index.parent.mkdir(parents=True, exist_ok=True)
        with simple_index.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(
                    json.dumps(
                        {
                            "sure": row["sure_adi_tr"],
                            "sure_no": row["sure_no"],
                            "ayet": str(row["ayet_no"]),
                            "text": row["text_ar"],
                            "text_ar": row["text_ar"],
                            "meal_tr": row.get("meal_tr")
                            or row["meal_tr_kuran_yolu"]
                            or row["meal_tr_diyanet"],
                            "meal_tr_diyanet": row["meal_tr_diyanet"],
                            "meal_tr_kuran_yolu": row["meal_tr_kuran_yolu"],
                            "kaynak": "diyanet",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    # sure metadata
    sure_meta = []
    for i, name in enumerate(SURE_ADLARI_TR, start=1):
        sure_meta.append(
            {
                "sure_no": i,
                "sure_adi_tr": name,
                "ayet_sayisi": AYET_SAYILARI[i - 1],
            }
        )
    (OUT / "metadata" / "sureler.json").write_text(
        json.dumps(sure_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # copy samples
    for s, a in [(1, 1), (1, 7), (2, 255), (112, 1)]:
        r = next(x for x in rows if x["sure_no"] == s and x["ayet_no"] == a)
        qa["ornekler"].append(
            {
                "sure_no": s,
                "ayet_no": a,
                "ar_len": len(r["text_ar"]),
                "meal_dib_len": len(r["meal_tr_diyanet"]),
                "meal_ky_len": len(r["meal_tr_kuran_yolu"]),
                "ar_preview": r["text_ar"][:80],
                "meal_ky_preview": r["meal_tr_kuran_yolu"][:120],
            }
        )

    sources = []
    for name, url in [
        ("kuran_mushaf.docx", "https://kuran.diyanet.gov.tr/Content/dosyalar/kuran.docx"),
        (
            "diyanet_meali.epub",
            "https://dijital.diyanet.gov.tr/File/EpubDownload?path=430_2.epub&name=KUR%27AN-I_KER%C4%B0M_MEAL%C4%B0&id=430",
        ),
        (
            "kuran_yolu_meali.epub",
            "https://dijital.diyanet.gov.tr/File/EpubDownload?path=429_2.epub&name=KUR%27AN_YOLU_MEAL%C4%B0&id=429",
        ),
        (
            "diyanet_meali.pdf",
            "https://dijital.diyanet.gov.tr/File/Download?path=430_1.pdf&id=430",
        ),
    ]:
        p = STAGE / name
        if p.exists():
            sources.append(
                {
                    "dosya": name,
                    "url": url,
                    "bytes": p.stat().st_size,
                    "sha256": sha256_file(p),
                }
            )

    filled_ar = sum(1 for r in rows if r["text_ar"])
    filled_dib = sum(1 for r in rows if r["meal_tr_diyanet"])
    filled_ky = sum(1 for r in rows if r["meal_tr_kuran_yolu"])
    qa.update(
        {
            "dolu_arapca": filled_ar,
            "dolu_meal_diyanet": filled_dib,
            "dolu_meal_kuran_yolu": filled_ky,
            "tam_arapca": filled_ar == 6236,
            "tam_meal_diyanet": filled_dib == 6236,
            "tam_meal_kuran_yolu": filled_ky == 6236,
        }
    )

    manifest = {
        "ok": True,
        "version": "din-01-kuran-v1",
        "yukleme_tarihi": stamp,
        "collection": "din_01_kuran",
        "kaynak": "Diyanet İşleri Başkanlığı — kuran.diyanet.gov.tr / dijital.diyanet.gov.tr",
        "kaynaklar": sources,
        "ciktilar": {
            "ayetler_jsonl": str(index_path.relative_to(ROOT)).replace("\\", "/"),
            "arsiv_index": "arsiv/kuran/index.jsonl",
            "sureler": "knowledge/ilim/din/01_kuran/metadata/sureler.json",
        },
        "qa": qa,
        "legacy_tasinan": moved,
        "notlar": [
            "Birincil meal: Kur'an Yolu (EPUB) — ayet ayet (Diyanet resmi yayın).",
            "İkincil meal: DİB Cep Meal EPUB — bazı sureler resmi EPUB'ta boş stub (Neml/Saffat); boş kalanlar Kur'an Yolu ile dolduruldu ve meal_diyanet_kaynak alanında işaretlendi.",
            "Cep Meal'de birleşik ayet meal'leri orijinal yayına sadık (meal_diyanet_birlesik).",
            "Arapça: Diyanet Word mushaf (Hamdullah hattı) — 6236/6236.",
            "RAG rebuild bu scriptte yapılmaz; ayrı adım.",
        ],
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (STAGE / "ingest_rapor.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, "qa_ozet": {
        "arapca": f"{filled_ar}/6236",
        "meal_diyanet": f"{filled_dib}/6236",
        "meal_kuran_yolu": f"{filled_ky}/6236",
        "sure_eksik_ar": len(qa["sure_eksik_arapca"]),
        "sure_eksik_dib": len(qa["sure_eksik_meal_diyanet"]),
        "sure_eksik_ky": len(qa["sure_eksik_meal_yolu"]),
        "ornek_fatiha1_ky": qa["ornekler"][0]["meal_ky_preview"] if qa["ornekler"] else "",
    }}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
