# -*- coding: utf-8 -*-
"""Dalga B — 03/10/21/13 raw → derin md (ağ yok)."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RAF = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
MAX_CHARS = 10000
MAX_PAGES = 220

# (dal_glob, key, baslik, raw_glob)
JOBS = [
    ("03_*", "nndl", "Neural Networks and Deep Learning", "nndl.html"),
    ("03_*", "fastai", "fast.ai course docs", "fastai.html"),
    ("03_*", "aima_site", "AIMA site pages", "aima_site_*.html"),
    ("10_*", "pandas_docs", "pandas documentation", "pandas_docs_*.html"),
    ("10_*", "sklearn_ug", "scikit-learn user guide", "sklearn_ug.html"),
    ("10_*", "pdsh", "Python Data Science Handbook", "pdsh_*.html"),
    ("21_*", "slp", "Speech and Language Processing hub", "slp.html"),
    ("21_*", "nltk_book", "NLTK Book", "nltk_book*.html"),
    ("13_*", "openstax_calc1", "OpenStax Calculus Volume 1", "openstax_calc1.html"),
    ("13_*", "openstax_linalg", "OpenStax Algebra and Trigonometry", "openstax_linalg.html"),
    ("13_*", "3blue1brown_essence", "Essence of Linear Algebra (3Blue1Brown)", "3blue1brown_essence.html"),
    ("13_*", "mcs_html_deep", "MIT MCS HTML deep", "mcs_html_deep_*.html"),
    ("13_*", "mcs_math", "Mathematics for Computer Science (MIT)", "mcs_math.pdf"),
]


def _dal(glob_pat: str) -> Path | None:
    hits = sorted(RAF.glob(glob_pat))
    return hits[0] if hits else None


def _html_text(data: bytes) -> str:
    raw = data.decode("utf-8", errors="ignore")
    raw = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style.*?>.*?</style>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def _pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        parts = []
        for p in reader.pages[:MAX_PAGES]:
            try:
                t = p.extract_text() or ""
            except Exception:
                t = ""
            if t.strip():
                parts.append(t)
        return "\n\n".join(parts)
    except Exception:
        return ""


def _chunk_write(metin: Path, stem: str, body: str, meta: dict) -> int:
    out = metin / stem
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    if not body.strip():
        body = f"Kaynak: {meta.get('baslik')}\n"
    head = (
        f"# {meta['baslik']}\n\n"
        f"- kaynak_id: `{meta['kaynak_id']}`\n"
        f"- dal: {meta['dal']}\n"
        f"- dalga_b_raw_derin: true\n\n---\n\n"
    )
    n = pos = 0
    while True:
        n += 1
        chunk = body[pos : pos + MAX_CHARS]
        cut = chunk.rfind("\n\n")
        if cut > MAX_CHARS // 2:
            chunk = chunk[:cut]
            pos += cut
        else:
            pos += max(len(chunk), 1)
        (out / f"{n:03d}.md").write_text(
            (head if n == 1 else f"# {meta['baslik']} (devam {n})\n\n---\n\n")
            + chunk.strip()
            + "\n",
            encoding="utf-8",
        )
        if pos >= len(body) or n >= 120:
            break
    return n


def _gather(raw_dir: Path, pattern: str) -> str:
    files = sorted(raw_dir.glob(pattern))
    if not files:
        return ""
    parts: list[str] = []
    for f in files[:40]:
        if f.suffix.lower() == ".pdf":
            parts.append(_pdf_text(f))
        else:
            parts.append(_html_text(f.read_bytes()))
    return "\n\n".join(p for p in parts if p.strip())


def main() -> int:
    report = []
    for dal_g, key, baslik, raw_pat in JOBS:
        dal = _dal(dal_g)
        if not dal:
            report.append({"key": key, "ok": False, "err": "dal yok"})
            continue
        raw_dir = dal / "raw"
        metin = dal / "metin"
        metin.mkdir(parents=True, exist_ok=True)
        body = _gather(raw_dir, raw_pat) if raw_dir.is_dir() else ""
        if len(body) < 400:
            report.append({"key": key, "ok": False, "err": f"zayif_raw len={len(body)}"})
            continue
        meta = {
            "baslik": baslik,
            "kaynak_id": f"{dal.name}_{key}",
            "dal": dal.name,
        }
        n = _chunk_write(metin, key, body, meta)
        cat_path = dal / "katalog.json"
        if cat_path.is_file():
            cat = json.loads(cat_path.read_text(encoding="utf-8"))
            kaynaklar = cat.setdefault("kaynaklar", {})
            row = kaynaklar.get(key) or {}
            row.update(
                {
                    "kaynak_id": meta["kaynak_id"],
                    "baslik": baslik,
                    "dal": dal.name,
                    "ok": True,
                    "parca": n,
                    "parca_sayisi": n,
                    "dalga_b_raw_derin": True,
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                }
            )
            kaynaklar[key] = row
            cat["updated_utc"] = datetime.now(timezone.utc).isoformat()
            cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report.append({"key": key, "ok": True, "parca": n, "dal": dal.name})
        print(("OK" if n >= 3 else "THIN"), key, "parca=", n, "dal=", dal.name)
    out = ROOT / "docs" / "DALGA_B_RAW_DERIN_RAPOR.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ok_n = sum(1 for r in report if r.get("ok") and int(r.get("parca") or 0) >= 3)
    print("DONE deep>=3", ok_n, "/", len(report), "->", out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
