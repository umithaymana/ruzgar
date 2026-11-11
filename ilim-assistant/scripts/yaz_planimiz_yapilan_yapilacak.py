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
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
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
    "4_dalga_b": "[x]",  # 03/10/21/13 ≥3 derin (2026-11-09)
    "4_dalga_c": "[x]",  # 08/09/07/12 ≥3 derin
    "4_dalga_d": "[x]",  # 14/15/16/17 ≥3 derin (2026-11-10 tam eser)
    "4_dalga_e": "[x]",  # 18/19/20/23/24/22 ≥3 tam eser (2026-11-10)
    "4_dalga_b_e": "[x]",  # B–E tamam (tam eser kuralı)
    "5_ayik_rag": "[x]",
    "5_ocr2": "[x]",  # tam cilt son sayfa + 2 tarama OCR (tur+eng) 2026-11-10
    "6a": "[x]",
    "6b": "[x]",
    "6c": "[x]",  # vitrin 7/7 + atölye mutlu yolu (2026-11-09)
    "6d": "[x]",  # hikâye vitrin 3/3 + mutlu yol (2026-11-09)
    "6e": "[x]",  # plan niyet 5/5 + Büyük Plan + mutlu yol
    "6f": "[x]",  # usta vitrin 5/5 + mutlu yol (2026-11-09)
    "10a_hafiza": "[x]",  # IR+Lucene+OpenSearch+FTS5+Automerge 2026-11-10
    "10b_ses": "[x]",  # Whisper/Piper/Coqui-Vosk/MDN/CommonVoice 2026-11-10
    "10c_tercume": "[x]",  # Marian/OPUS/Argos · ICU · CAMeL/Farasa · TBX 2026-11-10
    "10d_video": "[x]",  # OpenCV/FFmpeg/OTIO/WebRTC/Godot-Three 2026-11-10
    "10e_mimar": "[x]",  # AOSA/SRE/Electron-FastAPI/OPA/threat 2026-11-10
    "10f_programlama": "[x]",  # tree-sitter/Hypothesis/Playwright/llama/sandbox/CI 2026-11-10
    "10g_fenni": "[x]",  # Calc2/3 ILA MIT6042 Manim MapLibre HyperPhysics UP2 2026-11-10
    "10h_merkez": "[x]",  # Proxmox/Nix/ZFS/Syncthing/age/mirror/Prometheus + ince iyileştirme 2026-11-10
    "10i_madde": "[x]",  # ESP-IDF/FreeRTOS/HA/ROS2/Firmata/FreeCAD — 6/6 kalın≥40 2026-11-10
    "10j_profil": "[x]",  # WCAG/privacy/ACM ethics/unutma-miras — 4/4 kalın≥40 2026-11-10
    "10_2_sahne": "[x]",  # §10.2 8 sahne odası kalın≥40 2026-11-10
    "10_3_multimodal": "[x]",  # LLaVA/CLIP Whisper Piper embed/rerank LoRA eval 5/5 kalın≥40 2026-11-10
    "10_4_fenni": "[x]",  # OpenStax/OCW/D2L/atlas/bilim tarihi 5/5 kalın≥40 2026-11-10
    "bilgisayar_rag": "[x]",  # 593898 chunk · 61714 dosya · 24 dal · swap 2026-11-11 18:51
    "donanim_merdiven": "[x]",  # Basamak0 ölçüm+mühür 2026-11-11; alım/aksiyon ayrı Mimar evet
}


# Navigasyon / başlık renkleri — Gezinti paneli STİL rengini okur (koşu rengi yetmez)
_COLOR_DONE = RGBColor(0x1B, 0x7A, 0x3A)  # yeşil — bitti
_COLOR_PARTIAL = RGBColor(0xC4, 0x6B, 0x00)  # turuncu — kısmi
_COLOR_WAIT = None  # hiç başlanmayan — varsayılan
_STATUS_STYLES_READY = False


def _set_style_outline_level(style, outline_level: int) -> None:
    """Word Gezinti: outlineLvl zorunlu (0=Heading1 …)."""
    pPr = style.element.get_or_add_pPr()
    for child in list(pPr):
        if child.tag == qn("w:outlineLvl"):
            pPr.remove(child)
    el = OxmlElement("w:outlineLvl")
    el.set(qn("w:val"), str(max(0, min(8, outline_level))))
    pPr.append(el)


def _ensure_status_heading_styles(doc: Document) -> None:
    """Yeşil/turuncu özel başlık stilleri — Gezinti’de renk görünür."""
    global _STATUS_STYLES_READY
    if _STATUS_STYLES_READY:
        return
    styles = doc.styles
    for level in range(0, 5):  # 0=Title benzeri, 1–4 Heading
        base_name = "Title" if level == 0 else f"Heading {level}"
        try:
            base = styles[base_name]
        except KeyError:
            base = styles["Heading 1"] if level == 0 else None
            if base is None:
                continue
        outline = 0 if level == 0 else level - 1
        for status, color, label in (
            ("done", _COLOR_DONE, "Bitti"),
            ("partial", _COLOR_PARTIAL, "Kismi"),
        ):
            name = f"Ruzgar {label} H{level}"
            try:
                st = styles[name]
            except KeyError:
                st = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
                st.base_style = base
            st.font.color.rgb = color
            st.font.bold = True
            try:
                st.paragraph_format.left_indent = Pt(0)
                st.paragraph_format.first_line_indent = Pt(0)
                st.paragraph_format.space_before = Pt(10)
                st.paragraph_format.space_after = Pt(10)
            except Exception:
                pass
            _set_style_outline_level(st, outline)
    _STATUS_STYLES_READY = True


_PREFIX_DONE = "BİTTİ  ·  "
_PREFIX_PARTIAL = "KISMİ  ·  "
_PREFIX_STRIP_RE = re.compile(
    r"^(?:✓|◐|○|■+|【BİTTİ】|【KISMİ】|BİTTİ\s*·\s*|KISMİ\s*·\s*|\[x\]|\[~\]|\[\s\])\s*",
    re.I,
)


def _flush_left(p) -> None:
    """Sola sıfır — Gezinti/gövde girintisi yok."""
    fmt = p.paragraph_format
    fmt.left_indent = Pt(0)
    fmt.first_line_indent = Pt(0)
    fmt.space_before = Pt(10)
    fmt.space_after = Pt(10)


def add_heading(
    doc: Document,
    text: str,
    level: int = 1,
    *,
    status: str | None = None,
    legend: bool = False,
) -> None:
    """status: 'done' | 'partial' | 'wait'/None.

    Word koyu Gezinti stil rengini beyaza zorlar → kalın metin öneki.
    legend=True: önek eklemeden olduğu gibi yazar (üst şerit için).
    """
    _ensure_status_heading_styles(doc)
    st = (status or "").strip().lower()
    raw = (text or "").strip()
    if not legend:
        raw = _PREFIX_STRIP_RE.sub("", raw).strip()
    if legend:
        label = raw
        if st in ("done", "x", "[x]", "bitti"):
            style_name = f"Ruzgar Bitti H{level}"
            color = _COLOR_DONE
        elif st in ("partial", "~", "[~]", "kismi", "kısmi"):
            style_name = f"Ruzgar Kismi H{level}"
            color = _COLOR_PARTIAL
        else:
            style_name = "Title" if level == 0 else f"Heading {level}"
            color = None
    elif st in ("done", "x", "[x]", "bitti"):
        style_name = f"Ruzgar Bitti H{level}"
        color = _COLOR_DONE
        label = f"{_PREFIX_DONE}{raw}"
    elif st in ("partial", "~", "[~]", "kismi", "kısmi"):
        style_name = f"Ruzgar Kismi H{level}"
        color = _COLOR_PARTIAL
        label = f"{_PREFIX_PARTIAL}{raw}"
    else:
        style_name = "Title" if level == 0 else f"Heading {level}"
        color = None
        label = raw  # başlanmayan — işaretsiz
    try:
        p = doc.add_paragraph(label, style=style_name)
    except KeyError:
        p = doc.add_heading(label, level=level)
    _flush_left(p)
    if color is not None:
        for run in p.runs:
            run.font.color.rgb = color
            run.bold = True
            if legend:
                run.font.size = Pt(22 if level <= 1 else 16)
    elif legend:
        for run in p.runs:
            run.bold = True
            run.font.size = Pt(18)
    return None


def add_gezinti_legend(doc: Document) -> None:
    """Gezinti’nin en üstü: çizgi + büyük durum anahtarı (renk yoksa bile okunur)."""
    line = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    add_heading(doc, line, 1, status="wait", legend=True)
    add_heading(doc, "BİTTİ  ·  =  İŞ TAMAM", 1, status="done", legend=True)
    add_heading(doc, "KISMİ  ·  =  YARIM KALDI", 1, status="partial", legend=True)
    add_heading(doc, "(işaretsiz)  =  HENÜZ BAŞLANMADI", 1, status="wait", legend=True)
    add_heading(doc, line, 1, status="wait", legend=True)


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
    global _STATUS_STYLES_READY
    _STATUS_STYLES_READY = False
    raf_path = RAF_MD_DESK if RAF_MD_DESK.is_file() else RAF_MD
    if not raf_path.is_file():
        raf_path = RAF_MD
    raf_text = raf_path.read_text(encoding="utf-8")
    blocks = parse_raf_document(raf_text)
    katalog = load_katalog()
    ayik = load_ayiklama()
    ana = read_buyuk_ana_sira()

    doc = Document()
    # Gezinti’nin en başı: çizgi + büyük anahtar (tek bakış)
    add_gezinti_legend(doc)
    add_heading(doc, _TITLE, 0, status="wait")  # başlıkta durum gürültüsü yok
    add_p(
        doc,
        f"Güncellendi: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Ümit & Gökçenur",
        bold=True,
    )
    add_p(
        doc,
        "Madde işaret: [x] bitti · [~] kısmi · [ ] bekliyor · [-] bilerek yok/erte. "
        "Raf eser = disk katalog (derin ≥20 parça).",
    )
    add_p(
        doc,
        "Gezinti: üstteki çizgi + «BİTTİ  ·» / «KISMİ  ·» / (işaretsiz). "
        "Sola sıfır · aralık açık. Word koyu tema rengi göstermez.",
        bold=True,
    )
    add_p(
        doc,
        "Omurga sıra: Yol haritası kilit + Büyük Plan Ana_Sıra. "
        "Raf gövdesi: BİLGİSAYAR_RAF_DOLUM_LISTESI — belge sırası bozulmadan.",
        bold=True,
    )

    # ——— BÖLÜM 1: Neredeyiz ———
    add_heading(doc, "1) Neredeyiz (tek bakış)", 1, status="done")
    for m, t in [
        (FACT["0_rag"], "Adım 0 — Şamile RAG shard’ları"),
        (FACT["1_sohbet"], "Adım 1 — Rüzgar Sohbet omurgası (S0–S5)"),
        (FACT["2_mobil"], "Adım 2 — Mobil Yönetim (PWA / Tailscale / panel / üçlü)"),
        (FACT["3_ayiklama"], "Adım 3 — Kısa ayıklama (~50 seçim)"),
        (FACT["4_masa"], "Adım 4 — Masa omurgası (Belge/Tablo/Çizim/Sunum + onay)"),
        (FACT["4_dalga_a"], "Adım 4 — Dalga A omurga rafları derin (≥3 eser: 01–06, 11)"),
        (FACT["4_dalga_b_e"], "Adım 4 — Dalga B–E + kalan raflar (tamam)"),
        (FACT["5_ayik_rag"], "Adım 5 — Seçili PDF → ayıklama yan RAG"),
        (FACT["5_ocr2"], "Adım 5.d — Tam cilt / OCR 2. dalga"),
        (FACT["6a"], "Motor A — Okuma + Hafıza odaları"),
        (FACT["6b"], "Motor B — Ses süper-el + PWA mikrofon"),
        (FACT["6c"], "Motor C — Tercüme"),
        (FACT["6d"], "Motor D — Video"),
        (FACT["6e"], "Motor E — Mimar / sahne binası"),
        (FACT["6f"], "Motor F — Programlama organ fabrikası"),
        (FACT["10a_hafiza"], "§10 İleri A — Hafıza yakıtı (IR / Lucene / OpenSearch / FTS5 / Automerge)"),
        (FACT["10b_ses"], "§10 İleri B — Ses yakıtı (Whisper / Piper / Coqui-Vosk / MDN / Common Voice)"),
        (FACT["10c_tercume"], "§10 İleri C — Tercüme yakıtı (Marian/OPUS/Argos · ICU · CAMeL/Farasa · TBX)"),
        (FACT["10d_video"], "§10 İleri D — Video yakıtı (OpenCV / FFmpeg / OTIO / WebRTC / Godot-Three)"),
        (FACT["10e_mimar"], "§10 İleri E — Mimar yakıtı (AOSA / SRE / Electron-FastAPI / OPA / Threat)"),
        (FACT["10f_programlama"], "§10 İleri F — Programlama yakıtı (tree-sitter / Hypothesis / Playwright / llama / sandbox)"),
        (FACT["10g_fenni"], "§10 İleri G — Fenni+görsel (Calc2/3 · ILA · MIT 6.042 · Manim · MapLibre · HyperPhysics · UP2)"),
        (FACT["10h_merkez"], "§10 İleri H — Merkez 7/24 (Proxmox/Nix/ZFS/Syncthing/age/mirror/Prometheus) KALIN"),
        (FACT["10i_madde"], "§10 İleri I — Madde el (ESP-IDF/FreeRTOS/HA/ROS2/Firmata/FreeCAD) 6/6 KALIN≥40"),
        (FACT["10j_profil"], "§10 İleri J — Çok profil (WCAG/privacy/ACM ethics/unutma-miras) 4/4 KALIN≥40"),
        (FACT["10_2_sahne"], "§10.2 İleri sahne odaları — 8/8 KALIN≥40 (ömür/mahkeme/dil/coğrafya/astro/atölye/brifing/güvenlik)"),
        (FACT["10_3_multimodal"], "§10.3 Multimodal/yerel beyin — 5/5 KALIN≥40 (LLaVA·CLIP · Whisper/Piper · embed/rerank · LoRA · eval)"),
        (FACT["10_4_fenni"], "§10.4 Fenni derinleşme — 5/5 KALIN≥40 (OpenStax · MIT OCW · D2L/ISLR · atlas · bilim tarihi)"),
        (FACT["bilgisayar_rag"], "Bilgisayar RAG yeniden indeks — 593898 chunk · 61714 dosya · 24 dal (sağlama ✓ 2026-11-11 18:51)"),
        (FACT["donanim_merdiven"], "Donanım merdiveni — Basamak 0 ölçüm mühür (16GB·4060·Ryzen5500); alım sırası kayıtlı, satın alma ayrı evet"),
    ]:
        add_item(doc, m, t)

    # ——— BÖLÜM 2: Yol haritası kilit ———
    add_heading(doc, "2) Yol haritası — kilitli sıra (karşılaştırma)", 1, status="done")
    add_p(doc, f"Kaynak: {YOL_MD.name if YOL_MD.is_file() else 'RUZGAR_KUTUPHANE_SONRASI_YOL_HARITASI.md'}")
    add_p(doc, "Yol haritası §0 maddeleri × fiili durum:")
    for m, t in [
        (FACT["0_rag"], "YH-1 Şamile RAG bitsin"),
        (FACT["2_mobil"], "YH-2 Telefon/tablet uzaktan sohbet (ince istemci)"),
        (FACT["3_ayiklama"], "YH-3 Kısa ayıklama ~30–50"),
        (FACT["4_dalga_b_e"], "YH-4 Bilgisayar rafları derin + sahne/masa (Dalga A–E ✓)"),
        (FACT["5_ayik_rag"], "YH-5 Seçilmiş PDF → RAG"),
        (FACT["6f"], "YH-6 Motor A→F (A–F ✓)"),
        (FACT["10_4_fenni"], "YH-7 Fenni ilimler + görseller (ileri)"),
        (FACT["10a_hafiza"], "YH-§9/§10 İleri aşama (A→J + 10.2–10.4 ✓)"),
        (FACT["bilgisayar_rag"], "YH-son — Bilgisayar RAG yeniden indeks"),
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
    add_heading(doc, "3) Büyük Plan — Ana_Sıra (Excel) × fiili işaret", 1, status="done")
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

    add_heading(doc, "3.b Büyük Plan sayfaları (var / fiili)", 2, status="done")
    for m, t in [
        ("[x]", "11_Mobil_Yonetim — plan yazıldı + PWA/panel uygulandı"),
        ("[x]", "12_Ruzgar_Sohbet — S0–S5 kod yolu"),
        ("[x]", "2_Bilgisayar_Rafları — Dalga A–E tanımı ve tam eser mühürü"),
        ("[x]", "3_Masa_ve_Yüz — yüz kilidi + masa bağ temel"),
        ("[x]", "4_Motor_Dalgaları — A→F vitrin + mutlu yol ✓"),
        ("[x]", "5_Orkestra — rol tablosu kayıtlı"),
        (FACT["donanim_merdiven"], "6_Donanım_Merdiveni — Basamak 0 ölçüm mühür; alım ayrı evet"),
        ("[x]", "7_rüzgar_indir_Paket — ayıklama seçim ile işlendi"),
        (FACT["donanim_merdiven"], "10_Ileri_Sistem_Donanim — yazılım omurgası ✓; alım merdiveni kayıtlı"),
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
                if title.startswith("Dalga A") or title.startswith("Dalga B") or title.startswith(
                    "Dalga C"
                ) or title.startswith("Dalga D") or title.startswith("Dalga E"):
                    st = "done"
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

    add_heading(doc, "8) Sıradaki tek iş", 1, status="done")
    add_p(
        doc,
        "Büyük plan yazılım işleri tamam (0→6 + §10 yakıt A→J + 10.2–10.4 + bilgisayar RAG + Basamak0 ölçüm). "
        "Alım yok. Madde el / 7/24 merkez bilinçli kapalı: bunlar fiziksel kurulum (cihaz/7-24 ev); "
        "yakıt kalın dolduruldu, canlı bağ/kurulum ayrı açık Mimar «evet» ister — §10.5.",
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
