# -*- coding: utf-8 -*-
"""Usûl-i fıkıh — OpenITI sparse clone + metin seçimi (API rate-limit bypass)."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "07_usul_fikh"
RAW = STAGE / "raw"
CLONE = STAGE / "openiti_sparse"
RAW.mkdir(parents=True, exist_ok=True)
CLONE.mkdir(parents=True, exist_ok=True)

WORKS = [
    {"id": "waraqat", "repo": "0500AH", "author": "0478ImamHaramaynJuwayni",
     "work": "0478ImamHaramaynJuwayni.Waraqat",
     "eser_tr": "el-Varakât", "eser_ar": "الورقات",
     "yazar": "İmâmü'l-Haremeyn el-Cüveynî (ö. 478/1085)", "rol": "matn"},
    {"id": "burhan", "repo": "0500AH", "author": "0478ImamHaramaynJuwayni",
     "work": "0478ImamHaramaynJuwayni.BurhanFiUsulFiqh",
     "eser_tr": "el-Burhân fî usûli'l-fıkh", "eser_ar": "البرهان في أصول الفقه",
     "yazar": "İmâmü'l-Haremeyn el-Cüveynî (ö. 478/1085)", "rol": "muteber"},
    {"id": "mustasfa", "repo": "0525AH", "author": "0505Ghazali",
     "work": "0505Ghazali.Mustasfa",
     "eser_tr": "el-Mustasfâ", "eser_ar": "المستصفى",
     "yazar": "el-Gazzâlî (ö. 505/1111)", "rol": "muteber"},
    {"id": "mankhul", "repo": "0525AH", "author": "0505Ghazali",
     "work": "0505Ghazali.Mankhul",
     "eser_tr": "el-Menhûl", "eser_ar": "المنخول",
     "yazar": "el-Gazzâlî (ö. 505/1111)", "rol": "muteber"},
    {"id": "bazdawi", "repo": "0500AH", "author": "0482IbnMuhammadBazdawi",
     "work": "0482IbnMuhammadBazdawi.KanzWusul",
     "eser_tr": "Kenzü'l-vüsûl (Usûlü'l-Pezdevî)", "eser_ar": "كنز الوصول",
     "yazar": "Fahrülislâm el-Pezdevî (ö. 482/1089)", "rol": "muteber"},
    {"id": "usul_sarakhsi", "repo": "0500AH", "author": "0483IbnAhmadSarakhsi",
     "work": "0483IbnAhmadSarakhsi.Usul",
     "eser_tr": "Usûlü's-Serahsî", "eser_ar": "أصول السرخسي",
     "yazar": "eş-Şemsü'l-Eimme es-Serahsî (ö. 483/1090)", "rol": "muteber"},
    {"id": "ihkam_amidi", "repo": "0650AH", "author": "0631SayfDinAmidi",
     "work": "0631SayfDinAmidi.IhkamFiUsulAhkam",
     "eser_tr": "el-İhkâm fî usûli'l-ahkâm", "eser_ar": "الإحكام في أصول الأحكام",
     "yazar": "Seyfüddîn el-Âmidî (ö. 631/1233)", "rol": "muteber"},
    {"id": "muntaha_ibn_hajib", "repo": "0650AH", "author": "0646IbnCumarIbnHajibKurdi",
     "work": "0646IbnCumarIbnHajibKurdi.MukhtasarMuntaha",
     "eser_tr": "Muhtasar Müntehe's-sûl", "eser_ar": "مختصر منتهى السول",
     "yazar": "İbnü'l-Hâcib (ö. 646/1249)", "rol": "matn"},
    {"id": "minhaj_wusul", "repo": "0700AH", "author": "0685NasirDinBaydawi",
     "work": "0685NasirDinBaydawi.MatnMinhajWusul",
     "eser_tr": "Minhâcü'l-vusûl", "eser_ar": "منهاج الوصول",
     "yazar": "el-Beyzâvî (ö. 685/1286)", "rol": "matn"},
    {"id": "bahr_muhit", "repo": "0800AH", "author": "0794BadrDinZarkashi",
     "work": "0794BadrDinZarkashi.BahrMuhit",
     "eser_tr": "el-Bahru'l-muhît", "eser_ar": "البحر المحيط في أصول الفقه",
     "yazar": "Bedreddîn ez-Zerkeşî (ö. 794/1392)", "rol": "muteber"},
    {"id": "manthur_qawaid", "repo": "0800AH", "author": "0794BadrDinZarkashi",
     "work": "0794BadrDinZarkashi.ManthurFiQawacid",
     "eser_tr": "el-Mensûr fi'l-kavâid", "eser_ar": "المنثور في القواعد",
     "yazar": "Bedreddîn ez-Zerkeşî (ö. 794/1392)", "rol": "qawaid"},
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
    # Sadece eser klasörleri (yazarın tüm eserleri Windows MAX_PATH patlatabiliyor)
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
    return max(files, key=lambda p: p.stat().st_size)


def main() -> int:
    by_repo: dict[str, list[str]] = {}
    for w in WORKS:
        by_repo.setdefault(w["repo"], []).append(f"{w['author']}/{w['work']}")

    for repo, paths in by_repo.items():
        print(f"=== clone/sparse {repo} ({len(paths)} path) ===")
        _ensure_repo(repo, paths)

    catalog = []
    print("=== kopyala ===")
    for w in WORKS:
        work_dir = CLONE / w["repo"] / "data" / w["author"] / w["work"]
        if not work_dir.is_dir():
            print(f"  [miss] {work_dir}")
            continue
        src = _best_text(work_dir)
        dest = RAW / f"{w['id']}__{src.name}"
        if not dest.is_file() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        print(f"  [ok] {w['id']}: {dest.stat().st_size/1e6:.2f} MB ← {src.name}")
        catalog.append(
            {
                **w,
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
    return 0 if len(catalog) >= 8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
