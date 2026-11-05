#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Şamile dışı RAG kaynakları — Şamile envanteri ile AYNI künye mantığı.

Her satır = bir eser:
  NO | YAZAR | ESERİN TÜRKÇE ADI | MAHİYET | TARİH | CİLT | YÜKLEME

Yalnız manifest/catalog/kaynak künyesi olanlar. Raf özeti, sohbet notu,
iskelet alan satırı YOK.

Örnek:
  python scripts/ruzgar_kutuphane_envanter_rag_diger.py
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = Path(__file__).resolve().parents[1]
KNOW = ROOT / "knowledge"
RAG_MANIFEST = ROOT / ".rag_index" / "manifest.json"
ENV_ROOT = Path(r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE ENVANTER")
DOMAIN = "RAG DİĞER KAYNAKLAR"

HEADERS = [
    "NO",
    "YAZAR",
    "ESERİN TÜRKÇE ADI",
    "İÇERİK / MAHİYET (KISA)",
    "İLK TARİH (HİCRÎ)",
    "GERÇEK CİLT SAYISI",
    "YÜKLENEN CİLTLER / EKSİK",
]

# Bilinen açık kaynak kitaplar — katalogda yazar yoksa
_KNOWN_AUTHORS: dict[str, str] = {
    "think python": "Allen B. Downey",
    "think java": "Allen B. Downey",
    "automate the boring stuff": "Al Sweigart",
    "python for everybody": "Charles R. Severance",
    "invent your own computer games": "Al Sweigart",
    "sicp": "Harold Abelson; Gerald Jay Sussman",
    "structure and interpretation": "Harold Abelson; Gerald Jay Sussman",
    "eloquent javascript": "Marijn Haverbeke",
    "crafting interpreters": "Robert Nystrom",
    "the rust programming language": "Steve Klabnik; Carol Nichols",
    "you don't know js": "Kyle Simpson",
    "learn you a haskell": "Miran Lipovača",
    "competitive programmer": "Antti Laaksonen",
    "open data structures": "Pat Morin",
    "algorithms (jeff erickson": "Jeff Erickson",
    "modern c": "Jens Gustedt",
    "the art of unix": "Eric S. Raymond",
    "little book of semaphores": "Allen B. Downey",
    "zero to production": "Luca Palmieri",
    "beej": "Brian “Beej” Hall",
    "aima": "Stuart Russell; Peter Norvig",
    "operating systems: three easy pieces": "Remzi H. Arpaci-Dusseau; Andrea C. Arpaci-Dusseau",
    "ostep": "Remzi H. Arpaci-Dusseau; Andrea C. Arpaci-Dusseau",
}


def _load_rag_paths() -> dict[str, str]:
    if not RAG_MANIFEST.is_file():
        return {}
    data = json.loads(RAG_MANIFEST.read_text(encoding="utf-8"))
    return {str(k).replace("/", "\\"): str(v) for k, v in (data.get("file_digests") or {}).items()}


def _rag_count(rag: dict[str, str], prefix: str) -> int:
    p = prefix.replace("/", "\\").lstrip("\\")
    if p.startswith("knowledge\\"):
        p = p[len("knowledge\\") :]
    return sum(1 for k in rag if k == p or k.startswith(p.rstrip("\\") + "\\"))


def _tarih_from_yazar(yazar: str) -> str:
    m = re.search(r"ö\.\s*~?\s*(\d{2,4})\s*/", yazar or "")
    return f"H.{m.group(1)}" if m else "bilinmiyor"


def _guess_author(title: str, text: str = "") -> str:
    blob = (title or "").lower()
    for key, author in _KNOWN_AUTHORS.items():
        if key in blob:
            return author
    # Başlıkta (Yazar) kalıbı
    m = re.search(r"\(([^)]{3,60})\)\s*$", title or "")
    if m and not re.search(r"\d{4}|PDF|HTML|ch\d|MIT|CC ", m.group(1), re.I):
        return m.group(1).strip()
    # Metinden: "Author: ..." / ilk satırda by X
    for line in (text or "").splitlines()[:30]:
        s = line.strip()
        m = re.match(r"(?:author|yazar|by)\s*[:：]\s*(.+)$", s, re.I)
        if m:
            return m.group(1).strip()[:80]
    return ""


def _clean_title(title: str) -> str:
    t = (title or "").strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*\(ch\d.*$", "", t, flags=re.I)
    t = re.sub(r"\s*\(chapters\)$", "", t, flags=re.I)
    return t or "Ad yok"


def _mahiyet_kitap(title: str, yazar: str, alan: str, ar: str = "", tip: str = "", pages_hint: str = "") -> str:
    """Şamile tarzı kısa Türkçe mahiyet — Arapça dump yok."""
    tip_l = (tip or title or "").lower()
    konu = ""
    rules = [
        (r"tefs[iî]r|تفسير", "Kur’ân tefsiri / âyet yorumu çalışmasıdır"),
        (r"s[iî]yer|s[iî]ret|مغازي|meg[aâ]z", "siyer / gazve anlatımıdır"),
        (r"us[uû]l|أصول", "usûl (delil ve yöntem) eseridir"),
        (r"fıkıh|fikh|فقه", "fıkıh hükmü / fıkhî mesele eseridir"),
        (r"akaid|itikad|tevhid|عقيد", "akaid / itikad eseridir"),
        (r"ihy[aâ]|tasavvuf|mesnevi|füt[uû]h[aâ]t|mektubat", "ahlak / tasavvuf eseridir"),
        (r"felsefe|med[iî]ne|nec[aâ]t|iş[aâ]r[aâ]t|şifa|nefs", "felsefe / nefs eseridir"),
        (r"python|rust|javascript|java|haskell|c\b|program", "programlama / yazılım öğretim kitabıdır"),
        (r"algorithm|veri yap|data structure|interpreter", "algoritma / veri yapıları eseridir"),
        (r"operating system|kernel|unix|network|database", "bilgisayar sistemleri / altyapı eseridir"),
        (r"yapay zeka|artificial intelligence|aima|machine learning", "yapay zekâ / makine öğrenmesi eseridir"),
        (r"lugat|sözlük|dictionary|gar[iî]b", "lügat / sözlük niteliğindedir"),
        (r"tarih|târ[iî]h", "tarih kroniği / tarih eseridir"),
    ]
    for rx, sent in rules:
        if re.search(rx, f"{title} {tip_l} {alan}", re.I):
            konu = sent
            break
    if not konu:
        konu = f"{alan} alanında yazılmış bir kaynaktır"

    parts = [f"«{_clean_title(title)}»: {konu}."]
    if yazar and "bilinmiyor" not in yazar.lower() and "eksik" not in yazar.lower():
        parts.append(f"Müellif künyesi: {yazar}.")
    if ar:
        parts.append(f"Orijinal ad: {ar}.")
    if tip:
        parts.append(f"Tür: {tip}.")
    if pages_hint:
        parts.append(pages_hint)
    return " ".join(parts)


def _row(yazar: str, title: str, mahiyet: str, yukleme: str, tarih: str = "bilinmiyor", cilt: int = 1) -> dict:
    y = (yazar or "").strip()
    if not y:
        y = "Künye eksik (kaynakta yazar yok)"
    return {
        "yazar": y,
        "tr": _clean_title(title),
        "mahiyet": (mahiyet or "—").strip(),
        "tarih": tarih or "bilinmiyor",
        "cilt": cilt if cilt and cilt > 0 else 1,
        "yukleme": yukleme,
    }


def write_xlsx(folder: str, label: str, rows: list[dict]) -> Path:
    out_dir = ENV_ROOT / DOMAIN / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[<>:"/\\|?*]', "_", label)
    path = out_dir / f"{safe}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = label[:31]
    ws["A1"] = (
        f"{label} — Rüzgar envanteri (RAG diğer · eser künyesi) · "
        f"Toplam {len(rows)} eser · Yazar A→Z"
    )
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="C00000")
    ws.merge_cells("A1:G1")
    header_font = Font(name="Calibri", size=11, bold=True)
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    thin = Border(
        left=Side(style="thin", color="B0B0B0"),
        right=Side(style="thin", color="B0B0B0"),
        top=Side(style="thin", color="B0B0B0"),
        bottom=Side(style="thin", color="B0B0B0"),
    )
    for col, h in enumerate(HEADERS, 1):
        cell = ws.cell(2, col, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    for i, r in enumerate(rows, 1):
        vals = [i, r["yazar"], r["tr"], r["mahiyet"], r.get("tarih") or "bilinmiyor", r["cilt"], r["yukleme"]]
        for col, v in enumerate(vals, 1):
            cell = ws.cell(2 + i, col, v)
            cell.border = thin
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 48
    ws.column_dimensions["D"].width = 56
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 16
    ws.column_dimensions["G"].width = 28
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:G{2 + len(rows)}"
    note = wb.create_sheet("NOT")
    note["A1"] = (
        "Şamile listeleriyle aynı sütun düzeni. Yalnız künyeli eserler "
        "(catalog/manifest/kaynak kaydı). Eğitim rafı özeti, sohbet «learned» "
        "ve iskelet alan satırları bu turda yok. Yazar yoksa açıkça "
        "«Künye eksik» yazılır; uydurulmaz. Tarih: yazar vefatından Hicrî (varsa)."
    )
    note.column_dimensions["A"].width = 100
    note["A1"].alignment = Alignment(wrap_text=True)
    wb.save(path)
    return path


def collect_ortak_eserler(rag: dict[str, str]) -> dict[str, list[dict]]:
    """catalog.json içindeki eserler — yazar + eser_tr zorunlu alanlar."""
    out: dict[str, list[dict]] = {}
    root = KNOW / "ortak_kaynak" / "alanlar"
    if not root.is_dir():
        return out
    for alan_dir in sorted(root.iterdir()):
        if not alan_dir.is_dir() or alan_dir.name == "bilgisayar_eserleri":
            continue
        cat_p = alan_dir / "catalog.json"
        if not cat_p.is_file():
            continue
        cat = json.loads(cat_p.read_text(encoding="utf-8"))
        eserler = cat.get("eserler")
        if not isinstance(eserler, list):
            continue
        rows: list[dict] = []
        for e in eserler:
            title = (e.get("eser_tr") or "").strip()
            yazar = (e.get("yazar") or "").strip()
            if not title:
                continue
            if not yazar:
                yazar = "Künye eksik (kaynakta yazar yok)"
            yol = (e.get("dosya_yolu") or "").replace("knowledge/", "").replace("knowledge\\", "")
            n = _rag_count(rag, yol.replace("/", "\\")) if yol else 0
            if n == 0:
                n = _rag_count(
                    rag,
                    f"ortak_kaynak\\alanlar\\{alan_dir.name}\\eserler\\{e.get('eser_id')}",
                )
            batches = ""
            book = KNOW / yol.replace("/", "\\") if yol else None
            if book and book.is_dir():
                inc = book / "incremental"
                if inc.is_dir():
                    bc = len(list(inc.glob("*.md")))
                    if bc:
                        batches = f"Hacim ipucu: {bc} metin paketi."
            mah = _mahiyet_kitap(
                title,
                yazar,
                alan_dir.name,
                ar=(e.get("eser_ar") or ""),
                tip=(e.get("eser_turu") or e.get("rol") or "kitap"),
                pages_hint=batches,
            )
            rows.append(
                _row(
                    yazar,
                    title,
                    mah,
                    f"{n}/{max(n, 1)} — {'tam' if n else 'RAG eşleşmedi'}" if n else "0/? — RAG eşleşmedi",
                    tarih=_tarih_from_yazar(yazar),
                )
            )
        if rows:
            rows.sort(key=lambda r: (r["yazar"].casefold(), r["tr"].casefold()))
            out[alan_dir.name] = rows
    return out


def collect_bilgisayar(rag: dict[str, str]) -> list[dict]:
    base = KNOW / "ortak_kaynak" / "alanlar" / "bilgisayar_eserleri"
    if not base.is_dir():
        return []
    rows: list[dict] = []
    seen: set[str] = set()
    for kat in sorted(base.glob("*/katalog.json")):
        dal = kat.parent.name
        data = json.loads(kat.read_text(encoding="utf-8"))
        kaynaklar = data.get("kaynaklar") or {}
        for _kid, v in kaynaklar.items():
            if not isinstance(v, dict):
                continue
            title = _clean_title(v.get("baslik") or v.get("title") or "")
            if not title or title.lower().startswith("[raf]"):
                continue
            key = title.casefold()
            if key in seen:
                continue
            seen.add(key)
            # metin klasöründen ipucu
            text = ""
            metin = kat.parent / "metin"
            if metin.is_dir():
                stem = (v.get("deep_stem") or v.get("kaynak_id") or "")[:40]
                cands = list(metin.glob(f"*{stem}*")) if stem else []
                if not cands:
                    cands = sorted(metin.glob("*.md"))[:1]
                if cands:
                    try:
                        text = cands[0].read_text(encoding="utf-8", errors="ignore")[:1500]
                    except OSError:
                        text = ""
            yazar = _guess_author(title, text)
            parca = int(v.get("parca_sayisi") or v.get("parca") or 0)
            ok = v.get("ok")
            n = _rag_count(rag, f"ortak_kaynak\\alanlar\\bilgisayar_eserleri\\{dal}")
            # eser bazlı daha dar sayım mümkün değilse dal notu
            yuk = f"RAG dalında ~{n} dosya"
            if parca:
                yuk += f" · kaynak {parca} parça"
            if ok is False:
                yuk += " · indirme eksik"
            elif ok is True:
                yuk += " · yüklü"
            mah = _mahiyet_kitap(
                title,
                yazar or "Künye eksik",
                f"bilgisayar / {dal}",
                tip="yasal açık kaynak eser",
                pages_hint=(f"Lisans: {v['lisans']}." if v.get("lisans") else ""),
            )
            rows.append(
                _row(
                    yazar,
                    title,
                    mah,
                    yuk,
                )
            )
    rows.sort(key=lambda r: (r["yazar"].casefold(), r["tr"].casefold()))
    return rows


def collect_din_manifest(rag: dict[str, str]) -> dict[str, list[dict]]:
    labels = {
        "01_kuran": "KUR'AN (YEREL)",
        "02_tefsir": "TEFSİR (YEREL)",
        "03_arapca_lugat": "ARAPÇA LUGAT (YEREL)",
        "04_akaid": "AKAİD (YEREL)",
        "05_hadis": "HADİS (YEREL)",
        "06_fikh": "FIKIH (YEREL)",
        "07_usul_fikh": "USÛL-İ FIKIH (YEREL)",
        "08_siyer": "SİYER (YEREL)",
        "09_ahlak_tasavvuf": "AHLAK VE TASAVVUF (YEREL)",
    }
    out: dict[str, list[dict]] = {}
    din = KNOW / "ilim" / "din"
    for cat, lab in labels.items():
        base = din / cat
        if not base.is_dir():
            continue
        rows: list[dict] = []
        for folder_name in ("eserler", "klasik"):
            root = base / folder_name
            if not root.is_dir():
                continue
            for d in sorted(root.iterdir()):
                if not d.is_dir():
                    continue
                man_p = d / "manifest.json"
                if not man_p.is_file():
                    continue
                try:
                    man = json.loads(man_p.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                title = (man.get("eser_tr") or "").strip()
                yazar = (man.get("yazar") or "").strip()
                if not title:
                    continue
                rel = str(d.relative_to(KNOW)).replace("/", "\\")
                n = _rag_count(rag, rel)
                batches = man.get("batch_sayisi")
                hint = f"Hacim ipucu: {batches} paket." if batches else ""
                if man.get("char_count"):
                    hint = (hint + f" ~{man['char_count']} karakter.").strip()
                mah = _mahiyet_kitap(
                    title,
                    yazar,
                    lab,
                    ar=(man.get("eser_ar") or ""),
                    tip=(man.get("rol") or "kitap"),
                    pages_hint=hint,
                )
                # yükleme: paket sayısı varsa ona göre
                if batches and n:
                    yuk = f"{n}/{batches} paket — {'tam' if n >= int(batches) else 'kısmi'}"
                elif n:
                    yuk = f"{n} dosya — indekslenmiş"
                else:
                    yuk = "0 — RAG eşleşmedi"
                rows.append(
                    _row(
                        yazar,
                        title,
                        mah,
                        yuk,
                        tarih=_tarih_from_yazar(yazar),
                    )
                )
        if rows:
            rows.sort(key=lambda r: (r["yazar"].casefold(), r["tr"].casefold()))
            out[f"{cat}::{lab}"] = rows
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-old", action="store_true", help="Eski RAG DİĞER klasörünü silme")
    args = ap.parse_args()

    target = ENV_ROOT / DOMAIN
    if target.exists() and not args.keep_old:
        shutil.rmtree(target, ignore_errors=True)

    rag = _load_rag_paths()
    results: list[dict] = []

    for alan, rows in collect_ortak_eserler(rag).items():
        folder = f"01_ORTAK_KAYNAK_ESER\\{alan.upper()}"
        label = alan.replace("_", " ").upper()
        p = write_xlsx(folder, label, rows)
        results.append({"cat": f"ortak:{alan}", "rows": len(rows), "path": str(p)})

    rows_b = collect_bilgisayar(rag)
    if rows_b:
        p = write_xlsx("02_BILGISAYAR_ESERLERI", "BİLGİSAYAR ESERLERİ", rows_b)
        results.append({"cat": "bilgisayar", "rows": len(rows_b), "path": str(p)})

    for key, rows in collect_din_manifest(rag).items():
        cat, lab = key.split("::", 1)
        p = write_xlsx(f"03_ILIM_DIN_YEREL\\{cat.upper()}", lab, rows)
        results.append({"cat": f"din:{cat}", "rows": len(rows), "path": str(p)})

    print(json.dumps({"ok": True, "sheets": len(results), "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
