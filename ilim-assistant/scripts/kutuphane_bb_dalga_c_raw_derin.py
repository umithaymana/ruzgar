# -*- coding: utf-8 -*-
"""Dalga C — 08/09/07/12 raw → derin md (ağ yok)."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAF = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
MAX_CHARS = 10000

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore

JOBS = [
    # 08 mimari — ince olanları kalınlaştır
    ("08_*", "gpp", "Game Programming Patterns", "gpp.html"),
    ("08_*", "swe_book", "Software Engineering at Google", "swe_book_*.html"),
    ("08_*", "azure_patterns", "Azure Architecture Patterns", "azure_patterns_*.html"),
    ("08_*", "aosa_full", "Architecture of Open Source Applications", "aosa_full_*.html"),
    ("08_*", "segoogle", "Site Reliability / SE Google pages", "segoogle.html"),
    ("08_*", "twelve_factor", "The Twelve-Factor App", "twelve_factor*"),
    # 09 devops — ince kalanlar
    ("09_*", "docker_start", "Docker Get Started", "docker_start.html"),
    ("09_*", "ansible_docs", "Ansible documentation", "ansible_docs_*.html"),
    ("09_*", "terraform_docs", "Terraform docs", "terraform_docs*"),
    ("09_*", "dora", "DORA / DevOps Research", "dora_*.html"),
    # 07 siber — ince OWASP gövdeleri
    ("07_*", "owasp_asvs", "OWASP ASVS", "owasp_asvs.html"),
    ("07_*", "owasp_top10", "OWASP Top 10", "owasp_top10*"),
    ("07_*", "owasp_proactive", "OWASP Proactive Controls", "owasp_proactive*"),
    ("07_*", "nist_cyber", "NIST Cybersecurity overview", "nist_cyber_*.html"),
    # 12 bilgisayar müh.
    ("12_*", "ben_eater", "Ben Eater projects", "ben_eater*.html"),
    ("12_*", "computer_systems", "Computer Systems pages", "computer_systems_*.html"),
    ("12_*", "n2t_eng", "Nand2Tetris engineering", "n2t_eng_*.html"),
    ("12_*", "nand2tetris_deep", "Nand2Tetris deep", "nand2tetris_deep_*.html"),
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
    if PdfReader is None:
        return ""
    try:
        reader = PdfReader(str(path))
        parts = []
        for p in reader.pages[:220]:
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
        f"- dalga_c_raw_derin: true\n\n---\n\n"
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
    files = [f for f in sorted(raw_dir.glob(pattern)) if f.is_file()]
    if not files:
        # dizin eşleşmesi: altındaki html/pdf
        dirs = [d for d in sorted(raw_dir.glob(pattern)) if d.is_dir()]
        for d in dirs[:5]:
            files.extend(sorted(d.glob("*.html"))[:20])
            files.extend(sorted(d.glob("*.pdf"))[:5])
    if not files:
        return ""
    parts: list[str] = []
    for f in files[:50]:
        try:
            if f.suffix.lower() == ".pdf":
                parts.append(_pdf_text(f))
            else:
                parts.append(_html_text(f.read_bytes()))
        except OSError:
            continue
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
            print("SKIP", key, "zayif", len(body))
            continue
        meta = {"baslik": baslik, "kaynak_id": f"{dal.name}_{key}", "dal": dal.name}
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
                    "dalga_c_raw_derin": True,
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                }
            )
            kaynaklar[key] = row
            cat["updated_utc"] = datetime.now(timezone.utc).isoformat()
            cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report.append({"key": key, "ok": True, "parca": n, "dal": dal.name})
        print(("OK" if n >= 3 else "THIN"), key, "parca=", n)
    out = ROOT / "docs" / "DALGA_C_RAW_DERIN_RAPOR.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ok_n = sum(1 for r in report if r.get("ok") and int(r.get("parca") or 0) >= 3)
    print("DONE deep>=3", ok_n, "/", len(report), "->", out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
