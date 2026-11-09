# -*- coding: utf-8 -*-
"""Adım 5.d — Ayıklama tam cilt / 2. dalga (sayfa tavanını yükselt).

1. dalga çoğu eserde MAX_PAGES=60 ile kesildi.
Bu script mevcut md'yi korur; eksik sayfalardan devam parçaları yazar.
Tarama-only (metin 0) eserleri raporlar — Tesseract yoksa OCR atlanır.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / ".ruzgar" / "ayiklama_secim.json"
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "ruzgar_indir_secim"
REPORT = ROOT / ".ruzgar" / "ayiklama_tam_cilt_dalga2.json"
MAX_CHARS = 10000
# 2. dalga tavanı (tam cilt için yükseltilebilir)
# 0 / boş / "all" = kitabın son sayfasına kadar (yarım bırakma)
_raw_max = (os.environ.get("RUZGAR_AYIK_MAX_PAGES2", "0") or "0").strip().lower()
MAX_PAGES = 10**9 if _raw_max in ("0", "all", "tam", "full") else int(_raw_max)


def _slug(s: str) -> str:
    t = re.sub(r"[^\w\-]+", "_", s, flags=re.U).strip("_")
    return (t[:80] or "eser").lower()


def _next_part_n(out_dir: Path) -> int:
    nums = []
    for p in out_dir.glob("*.md"):
        m = re.match(r"^(\d+)\.md$", p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def _covered_hint(out_dir: Path) -> int:
    """Mevcut parçalardan kabaca kaç sayfa işlendi (başlıktan)."""
    max_page = 0
    for p in out_dir.glob("*.md"):
        try:
            head = p.read_text(encoding="utf-8", errors="ignore")[:400]
        except OSError:
            continue
        m = re.search(r"Sayfa dilimi:\s*(\d+)/", head)
        if m:
            max_page = max(max_page, int(m.group(1)))
    return max_page


def extend_pdf(pdf: Path, out_dir: Path, baslik: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        reader = PdfReader(str(pdf))
    except Exception as e:
        return {"ok": False, "error": str(e), "added": 0}
    total = len(reader.pages)
    start = _covered_hint(out_dir)
    # en azından 1. dalga 60 ise oradan devam
    if start < 1 and list(out_dir.glob("*.md")):
        start = 60
    end = total if MAX_PAGES >= 10**8 else min(total, MAX_PAGES)
    if start >= end:
        return {
            "ok": True,
            "added": 0,
            "skipped": True,
            "reason": "already_covered",
            "start": start,
            "end": end,
            "total_pages": total,
        }

    buf: list[str] = []
    chars = 0
    empty = 0
    added = 0
    n = _next_part_n(out_dir)
    for i in range(start, end):
        try:
            t = reader.pages[i].extract_text() or ""
        except Exception:
            t = ""
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            empty += 1
            continue
        buf.append(t)
        chars += len(t)
        joined = "\n\n".join(buf)
        last = i == end - 1
        if len(joined) >= MAX_CHARS or last:
            if not joined.strip():
                continue
            (out_dir / f"{n:03d}.md").write_text(
                f"# {baslik}\n\n"
                f"Kaynak: {pdf.name}\n"
                f"Yol: {pdf}\n"
                f"Dalga: 2 (tam cilt uzatma)\n"
                f"Sayfa dilimi: {i + 1}/{end} (kitap {total})\n\n"
                f"{joined[: MAX_CHARS + 2500]}\n",
                encoding="utf-8",
            )
            added += 1
            n += 1
            buf = []

    return {
        "ok": True,
        "added": added,
        "chars": chars,
        "empty_pages": empty,
        "start": start,
        "end": end,
        "total_pages": total,
        "parts_now": len(list(out_dir.glob("*.md"))),
        "needs_ocr": added == 0 and empty > 0 and chars < 200,
    }


def main() -> int:
    if not SEL.is_file():
        print("NO_SELECTION", SEL)
        return 1
    data = json.loads(SEL.read_text(encoding="utf-8"))
    items = list(data.get("items") or [])
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    t0 = time.time()
    print(f"DALGA2 max_pages={MAX_PAGES} n={len(items)}")
    for i, it in enumerate(items, 1):
        pdf = Path(it.get("file") or "")
        name = str(it.get("name") or pdf.stem)
        key = f"{i:02d}_{_slug(name)}"
        out_dir = OUT / key
        print(f"[{i}/{len(items)}] {name[:55]}")
        if not pdf.is_file():
            results.append({"name": name, "ok": False, "error": "missing"})
            print("  MISSING")
            continue
        r = extend_pdf(pdf, out_dir, name)
        print(" ", {k: r.get(k) for k in ("added", "start", "end", "total_pages", "needs_ocr", "skipped", "error")})
        results.append({"name": name, "file": str(pdf), "key": key, **r})

    payload = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "max_pages": MAX_PAGES,
        "n": len(items),
        "elapsed_sec": round(time.time() - t0, 1),
        "extended": sum(1 for r in results if int(r.get("added") or 0) > 0),
        "needs_ocr": [r.get("name") for r in results if r.get("needs_ocr")],
        "results": results,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("REPORT", REPORT)
    print(
        "DONE extended=",
        payload["extended"],
        "needs_ocr=",
        len(payload["needs_ocr"]),
        "sec=",
        payload["elapsed_sec"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
