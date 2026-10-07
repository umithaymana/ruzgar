# -*- coding: utf-8 -*-
"""Tasavvuf Faz 9 — OpenITI + Internet Archive metin indirme."""
from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "09_tasavvuf"
RAW = STAGE / "raw"
CLONE = STAGE / "openiti_sparse"
RAW.mkdir(parents=True, exist_ok=True)
CLONE.mkdir(parents=True, exist_ok=True)

# OpenITI (Arapça klasik) — kesin URI
OPENITI_WORKS = [
    {
        "id": "gazali_ihya",
        "repo": "0525AH",
        "author": "0505Ghazali",
        "work": "0505Ghazali.IhyaCulumDin",
        "eser_tr": "İhyâü Ulûmi'd-Dîn",
        "eser_ar": "إحياء علوم الدين",
        "yazar": "İmam Gazâlî (ö. 505/1111)",
        "rol": "asıl",
        "dil": "ar",
    },
    {
        "id": "gazali_kimya_saadet",
        "repo": "0525AH",
        "author": "0505Ghazali",
        "work": "0505Ghazali.KimiyaSacada",
        "eser_tr": "Kimyâ-yı Saâdet",
        "eser_ar": "كيمياء السعادة",
        "yazar": "İmam Gazâlî (ö. 505/1111)",
        "rol": "asıl",
        "dil": "fa",
    },
    {
        "id": "ibn_arabi_futuhat",
        "repo": "0650AH",
        "author": "0638IbnCarabi",
        "work": "0638IbnCarabi.FutuhatMakkiyya",
        "eser_tr": "Fütûhât-ı Mekkiyye",
        "eser_ar": "الفتوحات المكية",
        "yazar": "Muhyiddin İbnü'l-Arabî (ö. 638/1240)",
        "rol": "asıl",
        "dil": "ar",
    },
    {
        "id": "ibn_arabi_fusus",
        "repo": "0650AH",
        "author": "0638IbnCarabi",
        "work": "0638IbnCarabi.FususHikam",
        "eser_tr": "Fusûsu'l-Hikem",
        "eser_ar": "فصوص الحكم",
        "yazar": "Muhyiddin İbnü'l-Arabî (ö. 638/1240)",
        "rol": "asıl",
        "dil": "ar",
    },
    # OpenITI'de Fütûhu'l-Gayb / Feth-i Rabbânî yok; Ghunya klasik Geylânî eseri (yedek Arapça)
    {
        "id": "geylani_ghunya",
        "repo": "0575AH",
        "author": "0561CabdQadirJilani",
        "work": "0561CabdQadirJilani.Ghunya",
        "eser_tr": "el-Gunye li-tâlibî tarîki'l-hak",
        "eser_ar": "الغنية لطالبي طريق الحق",
        "yazar": "Abdülkadir Geylânî (ö. 561/1166)",
        "rol": "yedek",
        "dil": "ar",
        "optional": True,
    },
]

# Internet Archive — istenen eserler (OpenITI'de yok / Farsça-İngilizce)
IA_WORKS = [
    {
        "id": "geylani_futuh_gayb",
        "eser_tr": "Fütûhu'l-Gayb",
        "eser_ar": "فتوح الغيب",
        "yazar": "Abdülkadir Geylânî (ö. 561/1166)",
        "rol": "asıl",
        "dil": "en",
        "ia_id": "abdalqadiralgilanirevelationsoftheunseenfutuhalghayb",
        "files": [
            "Abd al Qadir al Gilani - Revelations of the Unseen (Futuh al-Ghayb)_djvu.txt",
        ],
        "kaynak": "Internet Archive (EN çeviri)",
    },
    {
        "id": "geylani_feth_rabbani",
        "eser_tr": "el-Fethu'r-Rabbânî",
        "eser_ar": "الفتح الرباني",
        "yazar": "Abdülkadir Geylânî (ö. 561/1166)",
        "rol": "asıl",
        "dil": "en",
        "ia_id": "Al-fathAl-rabbaniByShaykhGilani",
        "files": [
            "50913918-AL-FATHUR-RABBANI-BY-SHEIKH-ABDUL-QADIR-JILLANI_djvu.txt",
        ],
        "kaynak": "Internet Archive (EN çeviri)",
    },
    {
        "id": "mevlana_mesnevi",
        "eser_tr": "Mesnevî",
        "eser_ar": "المثنوي",
        "yazar": "Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273)",
        "rol": "asıl",
        "dil": "en",
        "ia_id": "rumi-masnavi",
        "files": [
            "Rumi-Book-I-Version-1.0_djvu.txt",
            "Rumi-Book-II-Version-1.0_djvu.txt",
            "Rumi-Book-III-Version-1.0_djvu.txt",
            "Rumi-Book-IV-Version-1.0_djvu.txt",
            "Rumi-Book-V-version-1.0_djvu.txt",
            "Rumi-Book-VI-Version-1.0_djvu.txt",
        ],
        "kaynak": "Internet Archive rumi-masnavi",
        "merge": True,
    },
    {
        "id": "mevlana_divan_kebir",
        "eser_tr": "Divân-ı Kebîr",
        "eser_ar": "ديوان كبير",
        "yazar": "Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273)",
        "rol": "asıl",
        "dil": "en",
        "ia_id": "Rumi-Divan-Kabir",
        "files": [
            "Divan Kabir vol.1_djvu.txt",
            "Divan Kabir vol.2_djvu.txt",
            "Divan Kabir vol.3_djvu.txt",
            "Divan Kabir vol.4_djvu.txt",
            "Divan Kabir vol.5_djvu.txt",
        ],
        "kaynak": "Internet Archive Rumi-Divan-Kabir",
        "merge": True,
        "optional_files": True,
    },
    {
        "id": "imam_rabbani_mektubat",
        "eser_tr": "Mektûbât",
        "eser_ar": "مكتوبات",
        "yazar": "İmam Rabbânî Ahmed Sirhindî (ö. 1034/1624)",
        "rol": "asıl",
        "dil": "en",
        "ia_id": "maktubat-e-imam-rabbani-ahmad-sirhindi",
        "files": [
            "Maktubat E Imam Rabbani(English)Volume 1_djvu.txt",
            "Maktubat E Imam Rabbani(English)Volume 2_djvu.txt",
            "Maktubat E Imam Rabbani(English)Volume 3_djvu.txt",
        ],
        "kaynak": "Internet Archive (EN çeviri)",
        "merge": True,
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
    sham = [f for f in files if "Shamela" in f.name or "ShamAY" in f.name or "Sham19" in f.name]
    pool = sham or files

    def score(p: Path) -> tuple:
        n = p.name
        return (
            1 if "completed" in n else 0,
            1 if "mARkdown" in n else 0,
            p.stat().st_size,
        )

    return max(pool, key=score)


def _http_get(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Ruzgar-Ilim/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def _download_openiti() -> list[dict]:
    by_repo: dict[str, list[str]] = {}
    for w in OPENITI_WORKS:
        by_repo.setdefault(w["repo"], []).append(f"{w['author']}/{w['work']}")

    for repo, paths in by_repo.items():
        print(f"=== OpenITI clone/sparse {repo} ({len(paths)} path) ===")
        try:
            _ensure_repo(repo, paths)
        except Exception as e:
            print(f"  [warn] {repo}: {e}")

    catalog: list[dict] = []
    print("=== OpenITI kopyala ===")
    for w in OPENITI_WORKS:
        work_dir = CLONE / w["repo"] / "data" / w["author"] / w["work"]
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
        print(f"  [ok] {w['id']}: {dest.stat().st_size/1e6:.2f} MB <- {src.name}")
        catalog.append(
            {
                **{k: v for k, v in w.items() if k != "optional"},
                "source_file": src.name,
                "bytes": dest.stat().st_size,
                "local": str(dest.relative_to(ROOT)).replace("\\", "/"),
                "kaynak": "OpenITI",
            }
        )
    return catalog


def _download_ia() -> list[dict]:
    catalog: list[dict] = []
    print("=== Internet Archive ===")
    for w in IA_WORKS:
        parts: list[Path] = []
        for fname in w["files"]:
            enc = urllib.request.quote(fname)
            url = f"https://archive.org/download/{w['ia_id']}/{enc}"
            dest = RAW / f"{w['id']}__{Path(fname).name}"
            if dest.is_file() and dest.stat().st_size > 1000:
                print(f"  [skip-exist] {dest.name}")
                parts.append(dest)
                continue
            try:
                print(f"  [get] {w['id']} <- {fname}")
                _http_get(url, dest)
                if dest.stat().st_size < 500:
                    print(f"  [warn] çok küçük: {dest.name}")
                    if w.get("optional_files"):
                        dest.unlink(missing_ok=True)
                        continue
                parts.append(dest)
            except Exception as e:
                print(f"  [miss] {w['id']} / {fname}: {e}")
                if not w.get("optional_files"):
                    break

        if not parts:
            print(f"  [fail] {w['id']}")
            continue

        if w.get("merge") and len(parts) > 1:
            merged = RAW / f"{w['id']}__merged.txt"
            texts = []
            for p in parts:
                texts.append(p.read_text(encoding="utf-8", errors="replace"))
            merged.write_text("\n\n".join(texts), encoding="utf-8")
            out = merged
        else:
            out = max(parts, key=lambda p: p.stat().st_size)

        print(f"  [ok] {w['id']}: {out.stat().st_size/1e6:.2f} MB")
        catalog.append(
            {
                "id": w["id"],
                "eser_tr": w["eser_tr"],
                "eser_ar": w["eser_ar"],
                "yazar": w["yazar"],
                "rol": w["rol"],
                "dil": w["dil"],
                "kaynak": w["kaynak"],
                "ia_id": w["ia_id"],
                "source_file": out.name,
                "bytes": out.stat().st_size,
                "local": str(out.relative_to(ROOT)).replace("\\", "/"),
            }
        )
    return catalog


def main() -> int:
    cat_o = _download_openiti()
    cat_i = _download_ia()
    catalog = cat_o + cat_i
    (STAGE / "download_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(c["bytes"] for c in catalog)
    print(f"TOPLAM: {total/1e6:.1f} MB · {len(catalog)} eser")
    # En az Gazâlî+İbnü'l-Arabî (4) beklenir
    return 0 if len(catalog) >= 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
