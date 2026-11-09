# -*- coding: utf-8 -*-
"""
PLANIMIZ — Yapılan ve Yapılacak İşler — YYYY-MM-DD.docx

Sıra kaynağı: RUZGAR_BILGISAYAR_RAF_DOLUM_LISTESI.md (baştan sona).
Karşılaştırma: RUZGAR_KUTUPHANE_SONRASI_YOL_HARITASI.md + RÜZGAR_BUYUK_PLAN.xlsx
+ fiili durum (katalog / ayıklama / motor).

KURAL: Katalog özeti YALNIZ ### 01–24 raf başlıklarına (tam iki haneli) bağlanır.
7.3 / 8.1 gibi alt başlıklara raf kataloğu YAPISTIRILMAZ.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from openpyxl import load_workbook

DESK = Path(r"C:\Users\hayma\Desktop\RÜZGAR")
_TODAY = datetime.now().strftime("%Y-%m-%d")
_TITLE = f"PLANIMIZ — Yapılan ve Yapılacak İşler — {_TODAY}"
OUT = DESK / f"{_TITLE}.docx"

ROOT = Path(__file__).resolve().parents[1]
RAF_MD = ROOT / "docs" / "RUZGAR_BILGISAYAR_RAF_DOLUM_LISTESI.md"
# Masaüstü kopyası varsa onu da dene (Mimar oradan açıyor)
RAF_MD_DESK = DESK / "RUZGAR_BILGISAYAR_RAF_DOLUM_LISTESI.md"
YOL_MD = DESK / "RUZGAR_KUTUPHANE_SONRASI_YOL_HARITASI.md"
BUYUK_XLSX = DESK / "RÜZGAR_BUYUK_PLAN.xlsx"
AYIK = ROOT / ".ruzgar" / "ayiklama_secim.json"
RAF_DIR = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_eserleri"

# Fiili durum (2026-11-09 turu — kod + indeks)
FACT = {
    "0_rag": "[x]",
    "1_sohbet": "[x]",
    "2_mobil": "[x]",
    "3_ayiklama": "[x]",
    "4_masa": "[x]",
    "4_dalga_a": "[x]",  # 01–06+11 ≥3 derin
    "4_dalga_b_e": "[~]",
    "5_ayik_rag": "[x]",
    "5_ocr2": "[~]",
    "6a": "[x]",
    "6b": "[x]",
    "6c": "[x]",  # vitrin 7/7 + atölye mutlu yolu (2026-11-09)
    "6d": "[x]",  # hikâye vitrin 3/3 + mutlu yol (2026-11-09)
    "6e": "[x]",  # plan niyet 5/5 + Büyük Plan + mutlu yol
    "6f": "[x]",  # usta vitrin 5/5 + mutlu yol (2026-11-09)
}


# Navigasyon / başlık renkleri (sağ panelde de görünür)
_COLOR_DONE = RGBColor(0x1B, 0x7A, 0x3A)  # yeşil — bitti
_COLOR_PARTIAL = RGBColor(0xC4, 0x6B, 0x00)  # turuncu — kısmi
_COLOR_WAIT = None  # hiç başlanmayan — varsayılan


def add_heading(
    doc: Document,
    text: str,
    level: int = 1,
    *,
    status: str | None = None,
) -> None:
    """status: 'done' | 'partial' | 'wait'/None — başlık rengi (Word gezgini)."""
    p = doc.add_heading(text, level=level)
    color = None
    st = (status or "").strip().lower()
    if st in ("done", "x", "[x]", "bitti"):
        color = _COLOR_DONE
    elif st in ("partial", "~", "[~]", "kismi", "kısmi"):
        color = _COLOR_PARTIAL
    if color is not None:
        for run in p.runs:
            run.font.color.rgb = color
    return None


def add_p(doc: Document, text: str, *, bold: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(11)


def add_item(doc: Document, mark: str, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    r0 = p.add_run(f"{mark} ")
    r0.bold = True
    if mark.startswith("[x]"):
        r0.font.color.rgb = RGBColor(0x1B, 0x7A, 0x3A)
    elif mark.startswith("[~]"):
        r0.font.color.rgb = RGBColor(0xB8, 0x6B, 0x00)
    elif mark.startswith("[-]"):
        r0.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    p.add_run(text)


def _fold(s: str) -> str:
    s = (s or "").casefold()
    return s.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))


def load_katalog() -> dict[int, dict]:
    """raf_no (1..24) -> {deep_n, src_n, rows:[(baslik,parca,deep)] , name}"""
    out: dict[int, dict] = {}
    if not RAF_DIR.is_dir():
        return out
    for d in sorted(RAF_DIR.iterdir()):
        m = re.match(r"^(\d{2})_", d.name)
        if not m or not d.is_dir():
            continue
        num = int(m.group(1))
        kat_path = d / "katalog.json"
        rows: list[tuple[str, int, bool]] = []
        if kat_path.is_file():
            try:
                kat = json.loads(kat_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                kat = {}
            for key, meta in (kat.get("kaynaklar") or {}).items():
                if not isinstance(meta, dict):
                    continue
                baslik = str(meta.get("baslik") or key)
                parca = int(meta.get("parca") or 0)
                deep = parca >= 20 and bool(meta.get("ok", True))
                rows.append((baslik, parca, deep))
        out[num] = {
            "name": d.name,
            "rows": rows,
            "deep_n": sum(1 for _, p, dpth in rows if dpth),
            "src_n": len(rows),
        }
    return out


def mark_eser(name: str, rows: list[tuple[str, int, bool]]) -> str:
    nf = _fold(name)
    tokens = [t for t in re.split(r"[^\w]+", nf) if len(t) >= 4]
    best = 0
    deep = False
    for baslik, parca, is_deep in rows:
        bf = _fold(baslik)
        score = 0
        head = nf[:20]
        if head and head in bf:
            score += 3
        for t in tokens[:6]:
            if t in bf:
                score += 1
        if score > best:
            best = score
            deep = bool(is_deep)
    if best >= 3 and deep:
        return "[x]"
    if best >= 2:
        return "[~]"
    return "[ ]"


def raf_shelf_num(heading: str) -> int | None:
    """Yalnız '01 — ...' / '24 — ...' → raf no. '7.3' / 'Dalga A' → None."""
    m = re.match(r"^(\d{2})\s*[—\-:]", heading.strip())
    if not m:
        return None
    n = int(m.group(1))
    return n if 1 <= n <= 24 else None


def parse_raf_document(text: str) -> list[dict]:
    """
    Belge sırasıyla bloklar:
      kind: h2 | h3 | h4 | bullet | table_row | para | code
    """
    blocks: list[dict] = []
    in_code = False
    code_buf: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                blocks.append({"kind": "code", "text": "\n".join(code_buf)})
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue
        if line.startswith("#### "):
            blocks.append({"kind": "h4", "text": line[5:].strip()})
            continue
        if line.startswith("### "):
            blocks.append({"kind": "h3", "text": line[4:].strip()})
            continue
        if line.startswith("## "):
            blocks.append({"kind": "h2", "text": line[3:].strip()})
            continue
        if line.startswith("# "):
            blocks.append({"kind": "h1", "text": line[2:].strip()})
            continue
        # tablo satırı (başlık hariç)
        if line.startswith("|") and "---" not in line and not re.match(r"^\|\s*[-:]+", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0].lower() not in ("küme", "katman", "eser / gövde", "dalga", "seviye", "oda"):
                # keep header-ish rows that are data too
                blocks.append({"kind": "table_row", "cells": cells})
            elif cells:
                blocks.append({"kind": "table_header", "cells": cells})
            continue
        if re.match(r"^\s*[-*]\s+", line):
            item = re.sub(r"^\s*[-*]\s+", "", line).strip()
            # bold title extract for marking
            bm = re.match(r"\*\*(.+?)\*\*\s*(.*)$", item)
            if bm:
                blocks.append(
                    {
                        "kind": "bullet_eser",
                        "title": bm.group(1).strip(),
                        "rest": bm.group(2).strip(),
                        "raw": item,
                    }
                )
            else:
                blocks.append({"kind": "bullet", "text": item})
            continue
        if re.match(r"^\s*\d+\.\s+\*\*", line):
            # numbered vision rooms
            item = re.sub(r"^\s*\d+\.\s+", "", line).strip()
            bm = re.match(r"\*\*(.+?)\*\*\s*(.*)$", item)
            if bm:
                blocks.append(
                    {
                        "kind": "bullet_eser",
                        "title": bm.group(1).strip(),
                        "rest": bm.group(2).strip(),
                        "raw": item,
                    }
                )
            else:
                blocks.append({"kind": "bullet", "text": item})
            continue
        if line.strip().startswith(">"):
            blocks.append({"kind": "quote", "text": line.lstrip("> ").strip()})
            continue
        if not line.strip() or set(line.strip()) == {"-"}:
            continue
        if line.strip().startswith("**") and line.strip().endswith("**") and len(line) < 200:
            blocks.append({"kind": "para_bold", "text": line.strip().strip("*")})
            continue
        blocks.append({"kind": "para", "text": line.strip()})
    return blocks


def load_ayiklama() -> list[dict]:
    if not AYIK.is_file():
        return []
    data = json.loads(AYIK.read_text(encoding="utf-8"))
    return list(data.get("items") or [])


def read_buyuk_ana_sira() -> list[tuple]:
    if not BUYUK_XLSX.is_file():
        return []
    wb = load_workbook(BUYUK_XLSX, read_only=True, data_only=True)
    if "1_Ana_Sıra" not in wb.sheetnames:
        return []
    ws = wb["1_Ana_Sıra"]
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        if row and row[0] is not None:
            rows.append(tuple(row[:7]))
    return rows


def fact_mark_for_ana(sira) -> str:
    try:
        n = int(sira)
    except (TypeError, ValueError):
        return "[ ]"
    return {
        0: FACT["0_rag"],
        1: FACT["1_sohbet"],
        2: FACT["2_mobil"],
        3: FACT["3_ayiklama"],
        4: "[~]" if FACT["4_dalga_b_e"] == "[~]" else FACT["4_dalga_a"],
        5: FACT["5_ayik_rag"],
        6: "[x]",  # A→F vitrin + mutlu yol (2026-11-09)
    }.get(n, "[ ]")


def main() -> int:
    raf_path = RAF_MD_DESK if RAF_MD_DESK.is_file() else RAF_MD
    if not raf_path.is_file():
        raf_path = RAF_MD
    raf_text = raf_path.read_text(encoding="utf-8")
    blocks = parse_raf_document(raf_text)
    katalog = load_katalog()
    ayik = load_ayiklama()
    ana = read_buyuk_ana_sira()

    doc = Document()
    add_heading(doc, _TITLE, 0, status="partial")
    add_p(
        doc,
        f"Güncellendi: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Ümit & Gökçenur",
        bold=True,
    )
    add_p(
        doc,
        "İşaret: [x] bitti · [~] kısmi · [ ] bekliyor · [-] bilerek yok/erte. "
        "Raf eser işaretleri = disk katalog (derin ≥20 parça).",
    )
    add_p(
        doc,
        "Başlık renkleri (sağ gezgin): YEŞİL = bölüm bitti · TURUNCU = kısmi · "
        "siyah/varsayılan = henüz başlanmadı veya vizyon.",
        bold=True,
    )
    add_p(
        doc,
        "Omurga sıra: Yol haritası kilit + Büyük Plan Ana_Sıra. "
        "Raf gövdesi: BİLGİSAYAR_RAF_DOLUM_LISTESI — belge sırası bozulmadan.",
        bold=True,
    )

    # ——— BÖLÜM 1: Neredeyiz ———
    add_heading(doc, "1) Neredeyiz (tek bakış)", 1, status="partial")
    for m, t in [
        (FACT["0_rag"], "Adım 0 — Şamile RAG shard’ları"),
        (FACT["1_sohbet"], "Adım 1 — Rüzgar Sohbet omurgası (S0–S5)"),
        (FACT["2_mobil"], "Adım 2 — Mobil Yönetim (PWA / Tailscale / panel / üçlü)"),
        (FACT["3_ayiklama"], "Adım 3 — Kısa ayıklama (~50 seçim)"),
        (FACT["4_masa"], "Adım 4 — Masa omurgası (Belge/Tablo/Çizim/Sunum + onay)"),
        (FACT["4_dalga_a"], "Adım 4 — Dalga A omurga rafları derin (≥3 eser: 01–06, 11)"),
        (FACT["4_dalga_b_e"], "Adım 4 — Dalga B–E + kalan raflar (devam)"),
        (FACT["5_ayik_rag"], "Adım 5 — Seçili PDF → ayıklama yan RAG"),
        (FACT["5_ocr2"], "Adım 5.d — Tam cilt / OCR 2. dalga"),
        (FACT["6a"], "Motor A — Okuma + Hafıza odaları"),
        (FACT["6b"], "Motor B — Ses süper-el + PWA mikrofon"),
        (FACT["6c"], "Motor C — Tercüme ← SIRADAKİ"),
        (FACT["6d"], "Motor D — Video"),
        (FACT["6e"], "Motor E — Mimar / sahne binası"),
        (FACT["6f"], "Motor F — Programlama organ fabrikası"),
    ]:
        add_item(doc, m, t)

    # ——— BÖLÜM 2: Yol haritası kilit ———
    add_heading(doc, "2) Yol haritası — kilitli sıra (karşılaştırma)", 1, status="partial")
    add_p(doc, f"Kaynak: {YOL_MD.name if YOL_MD.is_file() else 'RUZGAR_KUTUPHANE_SONRASI_YOL_HARITASI.md'}")
    add_p(doc, "Yol haritası §0 maddeleri × fiili durum:")
    for m, t in [
        (FACT["0_rag"], "YH-1 Şamile RAG bitsin"),
        (FACT["2_mobil"], "YH-2 Telefon/tablet uzaktan sohbet (ince istemci)"),
        (FACT["3_ayiklama"], "YH-3 Kısa ayıklama ~30–50"),
        ("[~]", "YH-4 Bilgisayar rafları derin + sahne/masa (Dalga A+masa ✓; B–E ve sahne hayali devam)"),
        (FACT["5_ayik_rag"], "YH-5 Seçilmiş PDF → RAG"),
        ("[~]", "YH-6 Motor A→F (A+B ✓; C sırada)"),
        ("[ ]", "YH-7 Fenni ilimler + görseller (ileri)"),
        ("[ ]", "YH-§9 İleri aşama (A→F sonrası)"),
    ]:
        add_item(doc, m, t)

    add_heading(
        doc,
        "2.b Yol haritasında olup Büyük Plan Ana_Sıra’da ayrı satır olanlar",
        2,
        status="done",
    )
    add_p(
        doc,
        "2026-11-08 kilidiyle Büyük Plan Ana_Sıra güncellendi: "
        "0 RAG → 1 Sohbet → 2 Mobil → 3 Ayıklama → 4 Bilgisayar/masa → 5 PDF RAG → 6 Motor+ileri. "
        "Eski yol metninde «ayıklama 1. sıra» vardı; fiili kilit sohbet+mobil’i öne aldı — Word fiili kilidi kullanır.",
    )

    # ——— BÖLÜM 3: Büyük Plan Ana_Sıra ———
    add_heading(doc, "3) Büyük Plan — Ana_Sıra (Excel) × fiili işaret", 1, status="partial")
    add_p(doc, f"Kaynak: {BUYUK_XLSX.name if BUYUK_XLSX.is_file() else 'RÜZGAR_BUYUK_PLAN.xlsx'} · sayfa 1_Ana_Sıra")
    if ana:
        for row in ana:
            sira, adim, ne, *_rest = (list(row) + [None] * 7)[:7]
            excel_durum = row[6] if len(row) > 6 else ""
            mark = fact_mark_for_ana(sira)
            add_item(
                doc,
                mark,
                f"Sıra {sira} — {adim}: {ne}  | Excel notu: {excel_durum}",
            )
    else:
        add_p(doc, "(Excel okunamadı)")

    add_heading(doc, "3.b Büyük Plan sayfaları (var / fiili)", 2, status="partial")
    for m, t in [
        ("[x]", "11_Mobil_Yonetim — plan yazıldı + PWA/panel uygulandı"),
        ("[x]", "12_Ruzgar_Sohbet — S0–S5 kod yolu"),
        ("[x]", "2_Bilgisayar_Rafları — Dalga A–E tanımı (içerik A kısmen doldu)"),
        ("[x]", "3_Masa_ve_Yüz — yüz kilidi + masa bağ temel"),
        ("[~]", "4_Motor_Dalgaları — A+B yapıldı; C–F bekliyor"),
        ("[x]", "5_Orkestra — rol tablosu kayıtlı"),
        ("[ ]", "6_Donanım_Merdiveni — vizyon; aksiyon sonra"),
        ("[x]", "7_rüzgar_indir_Paket — ayıklama seçim ile işlendi"),
        ("[ ]", "10_Ileri_Sistem_Donanim — ileri"),
    ]:
        add_item(doc, m, t)

    # ——— BÖLÜM 4: Ayıklama 50 ———
    add_heading(doc, "4) Ayıklama seçimi — 50 eser (tam ad)", 1, status="done")
    add_item(doc, FACT["3_ayiklama"], f"{len(ayik)} eser seçildi (.ruzgar/ayiklama_secim.json)")
    add_item(doc, "[-]", "Kalan ~240 aynı anda RAG — yasak")
    for it in ayik:
        name = str(it.get("name") or "?")
        cat = str(it.get("cat") or "")
        add_item(doc, "[x]", f"{name} — {cat}")

    # ——— BÖLÜM 5: RAF DOLUM — belge sırası ———
    add_heading(
        doc,
        "5) Bilgisayar raf dolum listesi — baştan sona (omurga içerik)",
        1,
        status="partial",
    )
    add_p(
        doc,
        f"Kaynak dosya: {raf_path.name}. Aşağıdaki sıra MD ile aynıdır. "
        "Katalog satırı yalnız «01 — …» … «24 — …» raf başlıklarında.",
        bold=True,
    )

    current_shelf: int | None = None
    shelf_rows: list[tuple[str, int, bool]] = []
    eser_count = 0
    for b in blocks:
        kind = b["kind"]
        if kind == "h1":
            continue  # doc title already
        if kind == "h2":
            current_shelf = None
            shelf_rows = []
            # §2 raflar kısmi; §3 yasak done; vizyon §6–10 wait/partial
            h2 = b["text"]
            h2st = "wait"
            if h2.startswith("0)") or h2.startswith("1)") or h2.startswith("3)"):
                h2st = "done"
            elif h2.startswith("2)") or h2.startswith("4)") or h2.startswith("5)"):
                h2st = "partial"
            elif h2.startswith("6)") or h2.startswith("7)") or h2.startswith("8)") or h2.startswith(
                "9)"
            ) or h2.startswith("10)"):
                h2st = "wait"
            add_heading(doc, h2, 2, status=h2st)
            continue
        if kind == "h3":
            title = b["text"]
            current_shelf = raf_shelf_num(title)
            if current_shelf is not None:
                info = katalog.get(current_shelf, {"deep_n": 0, "src_n": 0, "rows": []})
                shelf_rows = list(info.get("rows") or [])
                deep_n = int(info.get("deep_n") or 0)
                if deep_n >= 3:
                    st = "done"
                elif deep_n >= 1:
                    st = "partial"
                else:
                    st = "wait"
                add_heading(doc, title, 3, status=st)
                add_p(
                    doc,
                    f"Katalog (raf {current_shelf:02d}): {info.get('deep_n', 0)} derin eser · "
                    f"{info.get('src_n', 0)} kayıtlı kaynak"
                    + (f" · klasör `{info.get('name')}`" if info.get("name") else ""),
                )
            else:
                shelf_rows = []
                # Dalga A omurga kısmen; diğer vizyon başlıkları wait
                st = "wait"
                if title.startswith("Dalga A"):
                    st = "done"
                elif title.startswith("Dalga B") or title.startswith("Dalga C"):
                    st = "partial"
                add_heading(doc, title, 3, status=st)
            continue
        if kind == "h4":
            add_heading(doc, b["text"], 4, status="wait")
            continue
        if kind == "quote":
            add_p(doc, b["text"])
            continue
        if kind == "para_bold":
            add_p(doc, b["text"], bold=True)
            continue
        if kind == "para":
            add_p(doc, b["text"])
            continue
        if kind == "code":
            add_p(doc, "[sıra şeması]\n" + b["text"][:1500])
            continue
        if kind == "table_header":
            add_p(doc, " · ".join(b["cells"]), bold=True)
            continue
        if kind == "table_row":
            cells = b["cells"]
            # try mark first meaningful cell if shelf context
            label = " — ".join(c for c in cells if c)
            if current_shelf is not None and shelf_rows and cells:
                # first cell often küme name — don't mark as eser deep usually
                add_item(doc, "[ ]", label)
            else:
                add_item(doc, "[ ]", label)
            continue
        if kind == "bullet_eser":
            title = b["title"]
            rest = b.get("rest") or ""
            line = f"{title}" + (f" {rest}" if rest else "")
            if current_shelf is not None:
                mark = mark_eser(title, shelf_rows)
                eser_count += 1
            else:
                # vizyon / dalga maddeleri — henüz «raf derin» değil
                mark = "[ ]"
            add_item(doc, mark, line)
            continue
        if kind == "bullet":
            if current_shelf is not None:
                add_item(doc, "[ ]", b["text"])
            else:
                add_item(doc, "[ ]", b["text"])
            continue

    add_p(doc, f"(Raf bölümünde işaretlenen eser maddesi sayısı: {eser_count})", bold=True)

    # ——— BÖLÜM 6: Katalogda fiilen derin ———
    add_heading(doc, "6) Diskte derin gövde olanlar (katalog gerçeği)", 1, status="done")
    for num in sorted(katalog):
        info = katalog[num]
        deep = [(b, p) for b, p, d in info["rows"] if d]
        if not deep:
            continue
        add_heading(doc, f"Raf {num:02d} — {info['name']}", 3, status="done")
        for baslik, parca in sorted(deep, key=lambda x: -x[1]):
            add_item(doc, "[x]", f"{baslik} — {parca} parça")

    # ——— BÖLÜM 7: Motor ———
    add_heading(doc, "7) Motor dalgaları A→F (yol §5 × fiili)", 1, status="done")
    for m, t in [
        (FACT["6a"], "A Okuma + Hafıza — oda/pin/hatırla"),
        (FACT["6b"], "B Ses — süper-el"),
        (FACT["6c"], "C Tercüme — çift dilli vitrin + mutlu yol"),
        (FACT["6d"], "D Video — hikâye/cam köprüsü + mutlu yol"),
        (FACT["6e"], "E Mimar — plan/sahne niyet + mutlu yol"),
        (FACT["6f"], "F Programlama — usta vitrin + mutlu yol"),
        ("[x]", "Boot sırası teknik dokunulmaz"),
    ]:
        add_item(doc, m, t)

    add_heading(doc, "8) Sıradaki tek iş", 1, status="partial")
    add_p(
        doc,
        "Dalga B–E raf derinliği (bilgisayar kütüphanesi) + OCR-2 kısmi. "
        "Motor A→F vitrin/mutlu yol bu turda tamam.",
        bold=True,
    )

    add_heading(doc, "9) Bu Word’ü besleyen kaynaklar", 1, status="done")
    for p in [
        str(raf_path),
        str(YOL_MD) if YOL_MD.is_file() else "YOL_HARITASI (masaüstü)",
        str(BUYUK_XLSX) if BUYUK_XLSX.is_file() else "BUYUK_PLAN.xlsx",
        str(AYIK),
        str(RAF_DIR / "*/katalog.json"),
    ]:
        add_item(doc, "[x]", p)

    DESK.mkdir(parents=True, exist_ok=True)
    # eski tarihsiz / önceki gün kopyalarını silme — yalnız aynı gün dosyasının üzerine yaz
    try:
        doc.save(OUT)
        print("WROTE", OUT)
    except PermissionError:
        print("LOCKED", OUT)
        print("UYARI: Word açık — kaydedip kapatın, tekrar «yap» deyin.")
        return 2

    # Eski tarihsiz PLANIMIZ varsa temizle (tek dosya kuralı)
    undated = DESK / "PLANIMIZ — Yapılan ve Yapılacak İşler.docx"
    if undated.is_file() and undated.resolve() != OUT.resolve():
        try:
            undated.unlink()
            print("REMOVED", undated.name)
        except PermissionError:
            print("KEEP_LOCKED", undated.name)

    print("ESER_MARKED", eser_count, "SHELVES", len(katalog), "AYIK", len(ayik))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
