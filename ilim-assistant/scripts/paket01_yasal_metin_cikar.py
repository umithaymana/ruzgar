# -*- coding: utf-8 -*-
"""Paket 01 — yasal PDF'lerden Rüzgar metin parçaları (md)."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PAKET = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/paket_01_yasal"
RAW = PAKET / "raw"
METIN = PAKET / "metin"
MAX_CHARS_PER_FILE = 12000
MAX_PAGES_HUGE = 80  # RL gibi büyük kitaplarda üst sınır


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _clean(t: str) -> str:
    t = t.replace("\x00", " ")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def extract_pdf(path: Path, *, max_pages: int | None = None) -> str:
    reader = PdfReader(str(path))
    pages = reader.pages
    if max_pages is not None:
        pages = pages[:max_pages]
    parts: list[str] = []
    for i, page in enumerate(pages):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt.strip():
            parts.append(f"<!-- sayfa {i+1} -->\n{_clean(txt)}")
    return "\n\n".join(parts)


def chunk_write(stem: str, body: str, meta: dict) -> list[Path]:
    out_dir = METIN / stem
    out_dir.mkdir(parents=True, exist_ok=True)
    # header
    head = (
        f"# {meta['baslik']}\n\n"
        f"- kaynak_id: `{meta['kaynak_id']}`\n"
        f"- yazar: {meta['yazar']}\n"
        f"- lisans: {meta['lisans']}\n"
        f"- url: {meta['url']}\n"
        f"- checksum_pdf: {meta.get('checksum', '')}\n"
        f"- paket: paket_01_yasal\n\n---\n\n"
    )
    if len(body) <= MAX_CHARS_PER_FILE:
        p = out_dir / "001.md"
        p.write_text(head + body, encoding="utf-8")
        return [p]
    written: list[Path] = []
    i = 0
    pos = 0
    while pos < len(body):
        i += 1
        chunk = body[pos : pos + MAX_CHARS_PER_FILE]
        # break on paragraph if possible
        cut = chunk.rfind("\n\n")
        if cut > MAX_CHARS_PER_FILE // 2:
            chunk = chunk[:cut]
            pos += cut
        else:
            pos += len(chunk)
        p = out_dir / f"{i:03d}.md"
        p.write_text(head + chunk.strip() + "\n", encoding="utf-8")
        written.append(p)
        head = f"# {meta['baslik']} (devam {i})\n\n---\n\n"
    return written


def main() -> int:
    METIN.mkdir(parents=True, exist_ok=True)
    catalog: list[dict] = []

    jobs = [
        {
            "file": RAW / "think_python_2.pdf",
            "stem": "think_python_2",
            "baslik": "Think Python 2e",
            "yazar": "Allen B. Downey",
            "lisans": "CC BY-NC 3.0 (Green Tea Press)",
            "url": "https://greenteapress.com/thinkpython2/thinkpython2.pdf",
            "max_pages": None,
        },
        {
            "file": RAW / "think_stats_2.pdf",
            "stem": "think_stats_2",
            "baslik": "Think Stats 2e",
            "yazar": "Allen B. Downey",
            "lisans": "CC BY-NC (Green Tea Press)",
            "url": "https://greenteapress.com/thinkstats2/thinkstats2.pdf",
            "max_pages": None,
        },
        {
            "file": RAW / "think_bayes_2.pdf",
            "stem": "think_bayes",
            "baslik": "Think Bayes",
            "yazar": "Allen B. Downey",
            "lisans": "CC BY-NC (Green Tea Press)",
            "url": "https://greenteapress.com/thinkbayes/thinkbayes.pdf",
            "max_pages": None,
        },
        {
            "file": RAW / "open_data_structures_python.pdf",
            "stem": "open_data_structures",
            "baslik": "Open Data Structures (Python)",
            "yazar": "Pat Morin",
            "lisans": "CC BY (opendatastructures.org)",
            "url": "https://opendatastructures.org/ods-python.pdf",
            "max_pages": None,
        },
        {
            "file": RAW / "eloquent_javascript.pdf",
            "stem": "eloquent_javascript",
            "baslik": "Eloquent JavaScript",
            "yazar": "Marijn Haverbeke",
            "lisans": "CC BY-NC",
            "url": "https://eloquentjavascript.net/",
            "max_pages": None,
        },
        {
            "file": RAW / "rl_sutton_barto_2020.pdf",
            "stem": "rl_sutton_barto",
            "baslik": "Reinforcement Learning: An Introduction (2e) — ilk bölümler",
            "yazar": "Sutton & Barto",
            "lisans": "Yazar sitesinden ücretsiz PDF (incompleteideas.net)",
            "url": "http://incompleteideas.net/book/RLbook2020.pdf",
            "max_pages": MAX_PAGES_HUGE,
        },
    ]

    # OSTEP chapters
    ostep_dir = RAW / "ostep_chapters"
    if ostep_dir.is_dir():
        parts = []
        for pdf in sorted(ostep_dir.glob("*.pdf")):
            parts.append(f"## {pdf.stem}\n\n" + extract_pdf(pdf))
        body = "\n\n".join(parts)
        meta = {
            "kaynak_id": "bm_eser_ostep",
            "baslik": "Operating Systems: Three Easy Pieces (seçme bölümler)",
            "yazar": "Remzi & Andrea Arpaci-Dusseau",
            "lisans": "Ücretsiz çevrimiçi bölümler (ostep.org / UW)",
            "url": "https://pages.cs.wisc.edu/~remzi/OSTEP/",
            "checksum": "",
        }
        files = chunk_write("ostep", body, meta)
        catalog.append(
            {
                **meta,
                "parca_sayisi": len(files),
                "durum": "metin_hazir",
            }
        )
        print("OK ostep", len(files), "parca", len(body), "char")

    for job in jobs:
        path: Path = job["file"]
        if not path.is_file() or path.stat().st_size < 20_000:
            print("SKIP", path.name, "missing_or_tiny")
            continue
        print("EXTRACT", path.name, "...")
        body = extract_pdf(path, max_pages=job["max_pages"])
        if len(body) < 500:
            print("SKIP empty text", path.name)
            continue
        meta = {
            "kaynak_id": f"bm_eser_{job['stem']}",
            "baslik": job["baslik"],
            "yazar": job["yazar"],
            "lisans": job["lisans"],
            "url": job["url"],
            "checksum": _sha(path),
        }
        files = chunk_write(job["stem"], body, meta)
        catalog.append(
            {
                **meta,
                "parca_sayisi": len(files),
                "pdf": str(path.relative_to(PAKET)).replace("\\", "/"),
                "durum": "metin_hazir",
                "max_pages": job["max_pages"],
            }
        )
        print("OK", job["stem"], len(files), "parca", len(body), "char")

    man = {
        "paket_id": "paket_01_yasal",
        "baslik": "Bilgisayar eserleri — yasal paket 1",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "eser_sayisi": len(catalog),
        "eserler": catalog,
        "not": "Telifli ticari kitaplar yok. RL PDF'nin tamamı raw'da; metin ilk sayfalar.",
    }
    (PAKET / "katalog.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("katalog", len(catalog), "eser")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
