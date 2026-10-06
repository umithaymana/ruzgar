# -*- coding: utf-8 -*-
"""Siyer — OpenITI sparse clone + metin seçimi (API rate-limit bypass)."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "08_siyer"
RAW = STAGE / "raw"
CLONE = STAGE / "openiti_sparse"
RAW.mkdir(parents=True, exist_ok=True)
CLONE.mkdir(parents=True, exist_ok=True)

WORKS = [
    {
        "id": "sira_ibn_hisham",
        "repo": "0225AH",
        "author": "0213IbnHisham",
        "work": "0213IbnHisham.SiraNabawiyya",
        "eser_tr": "es-Sîretü'n-nebeviyye (İbn Hişâm)",
        "eser_ar": "السيرة النبوية",
        "yazar": "İbn Hişâm (ö. 213/828)",
        "rol": "asıl",
    },
    {
        "id": "maghazi_waqidi",
        "repo": "0225AH",
        "author": "0207Waqidi",
        "work": "0207Waqidi.Maghazi",
        "eser_tr": "Kitâbü'l-Megâzî",
        "eser_ar": "كتاب المغازي",
        "yazar": "el-Vâkıdî (ö. 207/823)",
        "rol": "maghazi",
    },
    {
        "id": "tabaqat_ibn_sad",
        "repo": "0250AH",
        "author": "0230IbnSacd",
        "work": "0230IbnSacd.TabaqatKubra",
        "eser_tr": "et-Tabakâtü'l-kübrâ",
        "eser_ar": "الطبقات الكبرى",
        "yazar": "İbn Sa'd (ö. 230/845)",
        "rol": "tabakat",
    },
    {
        "id": "tarikh_tabari",
        "repo": "0325AH",
        "author": "0310Tabari",
        "work": "0310Tabari.Tarikh",
        "eser_tr": "Târîhu'r-rusül ve'l-mülûk",
        "eser_ar": "تاريخ الرسل والملوك",
        "yazar": "et-Taberî (ö. 310/923)",
        "rol": "tarih",
    },
    {
        "id": "ridda_waqidi",
        "repo": "0225AH",
        "author": "0207Waqidi",
        "work": "0207Waqidi.Ridda",
        "eser_tr": "Kitâbü'r-Ridde",
        "eser_ar": "كتاب الردة",
        "yazar": "el-Vâkıdî (ö. 207/823)",
        "rol": "erken",
    },
    {
        "id": "futuh_sham_waqidi",
        "repo": "0225AH",
        "author": "0207Waqidi",
        "work": "0207Waqidi.FutuhSham",
        "eser_tr": "Fütûhu'ş-Şâm",
        "eser_ar": "فتوح الشام",
        "yazar": "el-Vâkıdî'ye nispet (ö. 207/823)",
        "rol": "futuh",
    },
    # İbn Kesîr / Zehebî — URI'ler klonda doğrulanınca doldurulur (opsiyonel)
    {
        "id": "fusul_sira_kathir",
        "repo": "0775AH",
        "author": "0774IbnKathir",
        "work": "0774IbnKathir.FusulMinSira",
        "eser_tr": "el-Fusûl min sîreti'r-Rasûl",
        "eser_ar": "الفصول من سيرة الرسول",
        "yazar": "İbn Kesîr (ö. 774/1373)",
        "rol": "muteber",
    },
    {
        "id": "bidaya_ibn_kathir",
        "repo": "0775AH",
        "author": "0774IbnKathir",
        "work": "0774IbnKathir.Bidaya",
        "eser_tr": "el-Bidâye ve'n-nihâye",
        "eser_ar": "البداية والنهاية",
        "yazar": "İbn Kesîr (ö. 774/1373)",
        "rol": "muteber",
    },
    {
        "id": "siyar_dhahabi",
        "repo": "0750AH",
        "author": "0748Dhahabi",
        "work": "0748Dhahabi.SiyarAclamNubala",
        "eser_tr": "Siyeru a'lâmi'n-nübelâ",
        "eser_ar": "سير أعلام النبلاء",
        "yazar": "ez-Zehebî (ö. 748/1348)",
        "rol": "tercuma",
        "optional": True,
    },
]


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print(" $", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def _ensure_repo(repo: str, paths: list[str]) -> Path:
    dest = CLONE / repo
    url = f"https://github.com/OpenITI/{repo}.git"
    if not (dest / ".git").is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                url,
                str(dest),
            ]
        )
    _run(["git", "config", "core.longpaths", "true"], cwd=dest)
    sparse_paths = sorted({f"data/{p}" for p in paths})
    _run(["git", "sparse-checkout", "set", "--no-cone", *sparse_paths], cwd=dest)
    _run(["git", "checkout"], cwd=dest)
    return dest


def _best_text(work_dir: Path) -> Path:
    files = [
        f
        for f in work_dir.iterdir()
        if f.is_file()
        and not f.name.endswith((".yml", ".yaml", ".md"))
        and "README" not in f.name
    ]
    if not files:
        raise FileNotFoundError(f"metin yok: {work_dir}")
    sham = [f for f in files if "Shamela" in f.name or "ShamAY" in f.name]
    pool = sham or files
    # Prefer completed / mARkdown when similar size
    def score(p: Path) -> tuple:
        n = p.name
        return (
            1 if "completed" in n else 0,
            1 if "mARkdown" in n else 0,
            p.stat().st_size,
        )

    return max(pool, key=score)


def main() -> int:
    by_repo: dict[str, list[str]] = {}
    for w in WORKS:
        by_repo.setdefault(w["repo"], []).append(f"{w['author']}/{w['work']}")

    for repo, paths in by_repo.items():
        print(f"=== clone/sparse {repo} ({len(paths)} path) ===")
        try:
            _ensure_repo(repo, paths)
        except Exception as e:
            print(f"  [warn] {repo}: {e}")

    catalog = []
    print("=== kopyala ===")
    for w in WORKS:
        work_dir = CLONE / w["repo"] / "data" / w["author"] / w["work"]
        if not work_dir.is_dir():
            # İbn Kesîr / Zehebî URI varyantları
            author_dir = CLONE / w["repo"] / "data" / w["author"]
            if author_dir.is_dir():
                hits = [
                    d
                    for d in author_dir.iterdir()
                    if d.is_dir()
                    and any(
                        k in d.name.lower()
                        for k in ("bidaya", "nihaya", "sira", "siyar", "nubala")
                    )
                ]
                if hits:
                    work_dir = hits[0]
                    print(f"  [alias] {w['id']} → {work_dir.name}")
            if not work_dir.is_dir():
                msg = f"  [miss] {w['id']}"
                if w.get("optional"):
                    print(msg + " (optional)")
                    continue
                print(msg)
                continue
        try:
            src = _best_text(work_dir)
        except FileNotFoundError as e:
            print(f"  [miss] {e}")
            continue
        dest = RAW / f"{w['id']}__{src.name}"
        if not dest.is_file() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        print(f"  [ok] {w['id']}: {dest.stat().st_size/1e6:.2f} MB ← {src.name}")
        catalog.append(
            {
                **{k: v for k, v in w.items() if k != "optional"},
                "source_file": src.name,
                "bytes": dest.stat().st_size,
                "local": str(dest.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    (STAGE / "download_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(c["bytes"] for c in catalog)
    print(f"TOPLAM: {total/1e6:.1f} MB · {len(catalog)} eser")
    return 0 if len(catalog) >= 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
