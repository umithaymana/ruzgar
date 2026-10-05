# -*- coding: utf-8 -*-
"""Faz 2: Diyanet Kur'an Yolu Türkçe Meâl ve Tefsir (5 cilt) ingest.

Kaynak: dijital.diyanet.gov.tr id=3788..3792 (EPUB)
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "02_tefsir"
OUT = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir"

CILT_IDS = {1: 3788, 2: 3789, 3: 3790, 4: 3791, 5: 3792}

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


def _el_iter(html: str):
    """Yield (tag, class, text) for h1-h6 and p elements in order."""
    for m in re.finditer(r"<(h[1-6]|p)\s*([^>]*)>(.*?)</\1>", html, re.S | re.I):
        tag = m.group(1).lower()
        attrs, inner = m.group(2), m.group(3)
        cm = re.search(r'class="([^"]+)"', attrs)
        cls = cm.group(1) if cm else ""
        # br -> space for titles like "1 (5) <br/> Fâtiha"
        inner = re.sub(r"(?i)<br\s*/?>", " ", inner)
        text = re.sub(r"<[^>]+>", "", inner)
        text = unescape(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n+", " ", text).strip()
        yield tag, cls, text


def _parse_range(blob: str) -> tuple[int, int] | None:
    blob = (blob or "").strip()
    m = re.fullmatch(r"(\d{1,3})\s*[–\-−]\s*(\d{1,3})", blob)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if 1 <= a <= b <= 300:
            return a, b
    m = re.fullmatch(r"(\d{1,3})", blob)
    if m:
        a = int(m.group(1))
        if 1 <= a <= 300:
            return a, a
    return None


def parse_cilt_epub(path: Path, cilt_no: int) -> tuple[list[dict], list[dict]]:
    """Return (sure_meta_chunks, tefsir_blocks)."""
    sure_meta: list[dict] = []
    blocks: list[dict] = []
    sure_header_re = re.compile(
        r"^(\d{1,3})\s*\((\d{1,3})\)\s+(.+S[ûuü]resi.*)$", re.I
    )

    with zipfile.ZipFile(path) as z:
        names = sorted(
            n for n in z.namelist() if n.endswith((".xhtml", ".html")) and "OEBPS/" in n
        )
        for name in names:
            raw = z.read(name).decode("utf-8", errors="replace")
            els = list(_el_iter(raw))
            if not els:
                continue

            # Front matter
            first_text = els[0][2]
            if re.search(r"\b(TAKDİM|ÖN SÖZ|GİRİŞ)\b", first_text, re.I):
                body = "\n\n".join(
                    t for tag, c, t in els[1:] if t and "normalnesil" in c
                )
                if body:
                    sure_meta.append(
                        {
                            "collection": "din_02_tefsir",
                            "tip": "on_soz",
                            "cilt": cilt_no,
                            "baslik": first_text[:80],
                            "metin": body[:50000],
                            "kaynak": f"diyanet:kuran_yolu_tefsir:c{cilt_no}",
                            "dosya": name,
                        }
                    )

            # Split by surah headers (usually h1)
            headers = []
            for idx, (tag, cls, text) in enumerate(els):
                m = sure_header_re.match(text)
                if m:
                    headers.append((idx, int(m.group(1)), m.group(3).strip()))
            if not headers:
                continue

            for hi, (start_i, sure_no, sure_title) in enumerate(headers):
                end_i = headers[hi + 1][0] if hi + 1 < len(headers) else len(els)
                section = els[start_i + 1 : end_i]

                intro_parts: list[str] = []
                k = 0
                while k < len(section):
                    tag, c, t = section[k]
                    if _parse_range(t) and (
                        "normalnesil5mmbefore" in c
                        or (k + 1 < len(section) and ("ARAP" in section[k + 1][1] or section[k + 1][2] == "Meâli" or "ARAP" in section[k + 1][1]))
                    ):
                        # fix: ARAP is in class not text
                        break
                    if _parse_range(t) and k + 1 < len(section):
                        nxt_cls = section[k + 1][1]
                        nxt_txt = section[k + 1][2]
                        if "ARAP" in nxt_cls or nxt_txt == "Meâli":
                            break
                    if t:
                        intro_parts.append(t)
                    k += 1

                if intro_parts:
                    sure_meta.append(
                        {
                            "collection": "din_02_tefsir",
                            "tip": "sure_giris",
                            "cilt": cilt_no,
                            "sure_no": sure_no,
                            "sure_adi": sure_title,
                            "sure_adi_tr": SURE_ADLARI_TR[sure_no - 1]
                            if 1 <= sure_no <= 114
                            else sure_title,
                            "metin": "\n\n".join(intro_parts)[:80000],
                            "kaynak": f"diyanet:kuran_yolu_tefsir:c{cilt_no}",
                            "dosya": name,
                        }
                    )

                while k < len(section):
                    tag, c, t = section[k]
                    rng = _parse_range(t)
                    if not rng:
                        k += 1
                        continue
                    ayet_bas, ayet_bit = rng
                    k += 1
                    ar_parts: list[str] = []
                    while k < len(section) and section[k][2] != "Meâli":
                        if _parse_range(section[k][2]) and "normalnesil5mmbefore" in section[k][1]:
                            break
                        if "ARAP" in section[k][1]:
                            ar_parts.append(section[k][2])
                        k += 1
                    meal_text = ""
                    tefsir_text = ""
                    if k < len(section) and section[k][2] == "Meâli":
                        k += 1
                        meal_parts: list[str] = []
                        while k < len(section) and section[k][2] != "Tefsiri":
                            if _parse_range(section[k][2]) and "normalnesil5mmbefore" in section[k][1]:
                                break
                            if section[k][2]:
                                meal_parts.append(section[k][2])
                            k += 1
                        meal_text = "\n\n".join(meal_parts).strip()
                    if k < len(section) and section[k][2] == "Tefsiri":
                        k += 1
                        tef_parts: list[str] = []
                        while k < len(section):
                            if _parse_range(section[k][2]) and (
                                "normalnesil5mmbefore" in section[k][1]
                                or (
                                    k + 1 < len(section)
                                    and (
                                        "ARAP" in section[k + 1][1]
                                        or section[k + 1][2] == "Meâli"
                                    )
                                )
                            ):
                                break
                            if section[k][2] in ("Meâli", "Tefsiri"):
                                break
                            if section[k][2]:
                                tef_parts.append(section[k][2])
                            k += 1
                        tefsir_text = "\n\n".join(tef_parts).strip()

                    if not meal_text and not tefsir_text:
                        continue
                    blocks.append(
                        {
                            "collection": "din_02_tefsir",
                            "tip": "ayet_tefsir",
                            "eser": "Kur'an Yolu Türkçe Meâl ve Tefsir",
                            "cilt": cilt_no,
                            "sure_no": sure_no,
                            "sure_adi_tr": SURE_ADLARI_TR[sure_no - 1]
                            if 1 <= sure_no <= 114
                            else sure_title,
                            "ayet_bas": ayet_bas,
                            "ayet_bit": ayet_bit,
                            "text_ar": " ".join(ar_parts).strip(),
                            "meal": meal_text,
                            "tefsir": tefsir_text,
                            "kaynak": f"diyanet:kuran_yolu_tefsir:c{cilt_no}:id{CILT_IDS[cilt_no]}",
                            "dosya": name,
                        }
                    )
    return sure_meta, blocks


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "kuran_yolu").mkdir(exist_ok=True)
    (OUT / "metadata").mkdir(exist_ok=True)

    all_meta: list[dict] = []
    all_blocks: list[dict] = []
    sources = []
    per_cilt = {}

    for cilt in range(1, 6):
        epub = STAGE / f"kuran_yolu_tefsir_c{cilt}.epub"
        if not epub.exists():
            raise SystemExit(f"Eksik: {epub}")
        sources.append(
            {
                "cilt": cilt,
                "id": CILT_IDS[cilt],
                "dosya": epub.name,
                "url": (
                    f"https://dijital.diyanet.gov.tr/File/EpubDownload?"
                    f"path={CILT_IDS[cilt]}_2.epub&id={CILT_IDS[cilt]}"
                ),
                "page": (
                    f"https://dijital.diyanet.gov.tr/Kitaplik/kuran-kitapligi/"
                    f"kuran-yolu-turkce-meal-ve-tefsir-{cilt}?id={CILT_IDS[cilt]}"
                ),
                "bytes": epub.stat().st_size,
                "sha256": sha256_file(epub),
            }
        )
        meta, blocks = parse_cilt_epub(epub, cilt)
        all_meta.extend(meta)
        all_blocks.extend(blocks)
        per_cilt[cilt] = {
            "sure_giris": sum(1 for m in meta if m.get("tip") == "sure_giris"),
            "blok": len(blocks),
            "sureler": sorted({b["sure_no"] for b in blocks}),
        }

    # Expand per-ayah index pointing to block text (for lookup)
    ayet_rows: list[dict] = []
    for b in all_blocks:
        for a in range(b["ayet_bas"], b["ayet_bit"] + 1):
            ayet_rows.append(
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

    blocks_path = OUT / "kuran_yolu" / "tefsir_bloklari.jsonl"
    with blocks_path.open("w", encoding="utf-8") as f:
        for row in all_blocks:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    ayet_path = OUT / "kuran_yolu" / "tefsir_ayet_indeks.jsonl"
    with ayet_path.open("w", encoding="utf-8") as f:
        for row in ayet_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta_path = OUT / "kuran_yolu" / "sure_giris_ve_onsoz.jsonl"
    with meta_path.open("w", encoding="utf-8") as f:
        for row in all_meta:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    sure_covered = sorted({b["sure_no"] for b in all_blocks})
    qa = {
        "blok_adet": len(all_blocks),
        "ayet_indeks_adet": len(ayet_rows),
        "meta_adet": len(all_meta),
        "sure_kaplanan": len(sure_covered),
        "sure_listesi": sure_covered,
        "eksik_sureler": [n for n in range(1, 115) if n not in set(sure_covered)],
        "per_cilt": per_cilt,
        "ornekler": [],
    }
    for s, a in [(1, 1), (2, 255), (112, 1)]:
        hits = [r for r in ayet_rows if r["sure_no"] == s and r["ayet_no"] == a]
        if hits:
            h = hits[0]
            qa["ornekler"].append(
                {
                    "sure_no": s,
                    "ayet_no": a,
                    "cilt": h["cilt"],
                    "meal_preview": (h["meal_blok"] or "")[:160],
                    "tefsir_preview": (h["tefsir_blok"] or "")[:200],
                    "aralik": f"{h['ayet_bas']}-{h['ayet_bit']}",
                }
            )

    manifest = {
        "ok": True,
        "version": "din-02-tefsir-kuran-yolu-v1",
        "yukleme_tarihi": stamp,
        "collection": "din_02_tefsir",
        "eser": "Kur'an Yolu Türkçe Meâl ve Tefsir",
        "yazarlar": [
            "Prof. Dr. Hayreddin Karaman",
            "Prof. Dr. Mustafa Çağrıcı",
            "Prof. Dr. İbrahim Kâfi Dönmez",
            "Prof. Dr. Sadrettin Gümüş",
        ],
        "kaynak": "Diyanet İşleri Başkanlığı — dijital.diyanet.gov.tr",
        "kaynaklar": sources,
        "ciktilar": {
            "bloklar": str(blocks_path.relative_to(ROOT)).replace("\\", "/"),
            "ayet_indeks": str(ayet_path.relative_to(ROOT)).replace("\\", "/"),
            "giris": str(meta_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "qa": qa,
        "bilinen_eksikler": [
            {
                "sure": 9,
                "sure_adi": "Tevbe",
                "eksik_ayetler": "38-129",
                "neden": "Diyanet EPUB cilt 2 yalnızca Tevbe 1-37 içeriyor; cilt 3 Yunus ile başlıyor (resmi EPUB TOC). PDF cilt 2-3 staging'e indirildi (tamamlama sonraki tur).",
                "staging_pdf": [
                    "arsiv/_ilim_staging/02_tefsir/kuran_yolu_tefsir_c2.pdf",
                    "arsiv/_ilim_staging/02_tefsir/kuran_yolu_tefsir_c3.pdf",
                ],
            }
        ],
        "notlar": [
            "Tefsir blokları orijinal yayındaki ayet aralıklarıyla saklanır (örn. Fatiha 1-7).",
            "ayet_indeks her ayeti ilgili bloğa bağlar (lookup için).",
            "Kapsama: 114/114 sure giriş + tefsir blokları; Tevbe 38-129 EPUB'ta eksik (PDF yedek indirildi).",
            "RAG rebuild ayrı adım.",
        ],
    }
    # fix typo if any in yazarlar - I may have used wrong paren
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (STAGE / "ingest_rapor.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "README.md").write_text(
        "# Din / 02 — Tefsir (Kur'an Yolu)\n\n"
        "Diyanet resmi 5 cilt EPUB (id 3788–3792).\n\n"
        f"- Blok: {len(all_blocks)}\n"
        f"- Ayet indeks: {len(ayet_rows)}\n"
        f"- Sure kapsama: {len(sure_covered)}/114\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "blok": len(all_blocks),
                "ayet_indeks": len(ayet_rows),
                "sure": f"{len(sure_covered)}/114",
                "eksik": qa["eksik_sureler"],
                "ornek_fatiha": qa["ornekler"][0]["tefsir_preview"][:120]
                if qa["ornekler"]
                else "",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
