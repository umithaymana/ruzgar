# -*- coding: utf-8 -*-
"""Adım 5.d — 2 tarama PDF (metin yok) → Tesseract OCR → md parçaları."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / ".ruzgar" / "ayiklama_secim.json"
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "ruzgar_indir_secim"
REPORT = ROOT / ".ruzgar" / "ayiklama_ocr_iki_tarama.json"
MAX_CHARS = 10000
# Tam cilt — yarım bırakma (istersen RUZGAR_AYIK_OCR_MAX_PAGES ile sınırla)
_raw = (os.environ.get("RUZGAR_AYIK_OCR_MAX_PAGES", "0") or "0").strip()
MAX_PAGES = 10**9 if _raw in ("0", "", "all") else int(_raw)
DPI = int(os.environ.get("RUZGAR_AYIK_OCR_DPI", "200") or "200")
LANG = os.environ.get("RUZGAR_AYIK_OCR_LANG", "tur+eng")
TESS = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = ROOT / ".ruzgar" / "tessdata"

# İlerleme raporunda needs_ocr=True olan adlar (esnek eşleşme)
TARGETS = ("coğrafya", "cografya", "1931")


def _slug(s: str) -> str:
    t = re.sub(r"[^\w\-]+", "_", s, flags=re.U).strip("_")
    return (t[:80] or "eser").lower()


def _match(name: str) -> bool:
    n = (name or "").casefold()
    n2 = n.replace("ğ", "g").replace("ı", "i").replace("ş", "s").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    return any(t in n or t in n2 for t in TARGETS)


def ocr_pdf(pdf: Path, out_dir: Path, baslik: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    # yeniden OCR — eski boş klasörü temizle
    for old in out_dir.glob("*.md"):
        old.unlink()
    doc = fitz.open(str(pdf))
    total = len(doc)
    end = min(total, MAX_PAGES)
    buf: list[str] = []
    chars = 0
    n = 0
    empty = 0
    for i in range(end):
        page = doc[i]
        pix = page.get_pixmap(dpi=DPI)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        try:
            t = pytesseract.image_to_string(img, lang=LANG) or ""
        except Exception as e:
            return {"ok": False, "error": f"ocr_fail page={i+1}: {e}", "parts": n}
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            empty += 1
            continue
        buf.append(t)
        chars += len(t)
        joined = "\n\n".join(buf)
        last = i == end - 1
        if len(joined) >= MAX_CHARS or last:
            if not joined.strip() and not last:
                continue
            if joined.strip():
                n += 1
                (out_dir / f"{n:03d}.md").write_text(
                    f"# {baslik}\n\n"
                    f"Kaynak: {pdf.name}\n"
                    f"Yol: {pdf}\n"
                    f"Dalga: OCR Tesseract ({LANG})\n"
                    f"Sayfa dilimi: {i + 1}/{end} (kitap {total})\n\n"
                    f"{joined[: MAX_CHARS + 2500]}\n",
                    encoding="utf-8",
                )
            buf = []
        if (i + 1) % 25 == 0:
            print(f"  OCR {i+1}/{end} parts={n} chars={chars}")
    doc.close()
    return {
        "ok": n > 0,
        "parts": n,
        "chars": chars,
        "empty_pages": empty,
        "pages": end,
        "total_pages": total,
    }


def main() -> int:
    if TESS.is_file():
        pytesseract.pytesseract.tesseract_cmd = str(TESS)
    if TESSDATA.is_dir():
        os.environ["TESSDATA_PREFIX"] = str(TESSDATA)
    if not SEL.is_file():
        print("NO_SELECTION")
        return 1
    items = list(json.loads(SEL.read_text(encoding="utf-8")).get("items") or [])
    picked = [(i, it) for i, it in enumerate(items, 1) if _match(str(it.get("name") or ""))]
    print(f"OCR targets={len(picked)} lang={LANG} dpi={DPI}")
    results = []
    t0 = time.time()
    for i, it in picked:
        pdf = Path(it.get("file") or "")
        name = str(it.get("name") or pdf.stem)
        key = f"{i:02d}_{_slug(name)}"
        print(f"[{i}] {name[:60]}")
        if not pdf.is_file():
            results.append({"name": name, "ok": False, "error": "missing"})
            continue
        r = ocr_pdf(pdf, OUT / key, name)
        print(" ", r)
        results.append({"name": name, "file": str(pdf), "key": key, **r})
    payload = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_sec": round(time.time() - t0, 1),
        "results": results,
        "ok": sum(1 for r in results if r.get("ok")),
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("REPORT", REPORT, "ok=", payload["ok"])
    return 0 if payload["ok"] == len(picked) else 1


if __name__ == "__main__":
    raise SystemExit(main())
