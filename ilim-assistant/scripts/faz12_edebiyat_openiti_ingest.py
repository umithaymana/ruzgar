# -*- coding: utf-8 -*-
"""Edebiyat ve sanat rafı Faz 12 — klasik Arap adab / şiir (OpenITI).

Kelîle, makâmât, Dîvân, şi'r tarihi. Fetva değildir.
Politika: Sayfa/cilt uydurma yasak.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "12_edebiyat"
RAW = STAGE / "raw"
CLONE = STAGE / "openiti_sparse"
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "edebiyat_sanat"
ESER = OUT / "eserler"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_edebiyat.jsonl"
CATALOG = OUT / "catalog.json"

CHUNK = 1600
OVERLAP = 120
BATCH = 20

OPENITI_WORKS = [
    {
        "id": "ibn_muqaffa_kalila",
        "repo": "0150AH",
        "author": "0139IbnMuqaffac",
        "work": "0139IbnMuqaffac.KalilaWaDimna",
        "eser_tr": "Kelîle ve Dimne",
        "eser_ar": "كليلة ودمنة",
        "yazar": "İbnü'l-Mukaffaʿ (ö. ~139/757)",
        "aliases": [
            "kelile",
            "kelile ve dimne",
            "kalila",
            "kalila wa dimna",
            "ibn mukaffa",
        ],
        "metin": (
            "İbnü'l-Mukaffaʿ'ın Kelîle ve Dimne'si: Sanskrit kökenli hikâye zincirinin "
            "klasik Arapça edebî uyarlaması; siyaset ve ahlâk öğüdü. Fetva değildir."
        ),
    },
    {
        "id": "hamadhani_maqamat",
        "repo": "0400AH",
        "author": "0398BadicZamanHamadhani",
        "work": "0398BadicZamanHamadhani.Maqamat",
        "eser_tr": "Makâmât (Bedîüzzaman el-Hemedânî)",
        "eser_ar": "مقامات بديع الزمان الهمذاني",
        "yazar": "Bedîüzzaman el-Hemedânî (ö. 398/1008)",
        "aliases": [
            "maqamat hemedani",
            "makamat hemedani",
            "bediuzzaman makamat",
            "hemedani makamat",
            "hamadhani maqamat",
        ],
        "metin": (
            "Bedîüzzaman el-Hemedânî'nin Makâmât'ı: klasik Arap nesirinin makâme türü; "
            "dil ustalığı ve hikâye. Fetva değildir."
        ),
    },
    {
        "id": "hariri_maqamat",
        "repo": "0525AH",
        "author": "0516IbnCaliHariri",
        "work": "0516IbnCaliHariri.Maqamat",
        "eser_tr": "Makâmâtü'l-Harîrî",
        "eser_ar": "مقامات الحريري",
        "yazar": "el-Harîrî (ö. 516/1122)",
        "aliases": [
            "hariri makamat",
            "maqamat hariri",
            "makamatü hariri",
            "harîrî makâmât",
            "el hariri",
        ],
        "metin": (
            "el-Harîrî'nin Makâmât'ı: makâme türünün doruk örneklerinden; "
            "Arap edebî nesri ve dil sanatı. Fetva değildir."
        ),
    },
    {
        "id": "abu_tammam_diwan",
        "repo": "0250AH",
        "author": "0231AbuTamam",
        "work": "0231AbuTamam.Diwan",
        "eser_tr": "Dîvânü Ebî Temmâm",
        "eser_ar": "ديوان أبي تمام",
        "yazar": "Ebû Temmâm (ö. 231/846)",
        "aliases": [
            "abu tammam",
            "ebu temmam",
            "ebû temmâm",
            "diwan abu tammam",
            "divan ebu temmam",
        ],
        "metin": (
            "Ebû Temmâm'ın Dîvân'ı: Abbâsî dönemi klasik Arap şiiri. "
            "Edebî metindir; fetva değildir."
        ),
    },
    {
        "id": "ibn_qutayba_shir",
        "repo": "0300AH",
        "author": "0276IbnQutaybaDinawari",
        "work": "0276IbnQutaybaDinawari.ShicrWaShucara",
        "eser_tr": "eş-Şiʿr ve'ş-şuʿarâ",
        "eser_ar": "الشعر والشعراء",
        "yazar": "İbn Kuteybe (ö. 276/889)",
        "aliases": [
            "sir ve suara",
            "şiir ve şairler",
            "shicr wa shucara",
            "ibn kuteybe siir",
            "ibn qutayba poetry",
        ],
        "metin": (
            "İbn Kuteybe'nin eş-Şiʿr ve'ş-şuʿarâ'sı: klasik Arap şiir tarihi ve şair "
            "biyografileri. Edebî kaynaktır; fetva değildir."
        ),
    },
    {
        "id": "buhturi_diwan",
        "repo": "0300AH",
        "author": "0284Buhturi",
        "work": "0284Buhturi.Diwan",
        "eser_tr": "Dîvânü'l-Buḥturî",
        "eser_ar": "ديوان البحتري",
        "yazar": "el-Buḥturî (ö. 284/897)",
        "aliases": [
            "buhturi",
            "buhturî",
            "el buhturi",
            "diwan buhturi",
            "divan buhturi",
        ],
        "metin": (
            "el-Buḥturî'nin Dîvân'ı: Abbâsî klasik Arap şiiri; Ebû Temmâm çizgisinin "
            "çağdaşı. Edebî metindir; fetva değildir."
        ),
    },
    {
        "id": "maarri_diwan",
        "repo": "0450AH",
        "author": "0449AbuCalaMacarri",
        "work": "0449AbuCalaMacarri.Diwan",
        "eser_tr": "Dîvânü Ebî'l-Alâ el-Maʿarrî",
        "eser_ar": "ديوان أبي العلاء المعري",
        "yazar": "Ebü'l-Alâ el-Maʿarrî (ö. 449/1057)",
        "aliases": [
            "maarri",
            "maʿarrî",
            "el maarri",
            "abu ala maarri",
            "diwan maarri",
            "divan maarri",
        ],
        "metin": (
            "Ebü'l-Alâ el-Maʿarrî'nin Dîvân'ı: klasik Arap şiiri ve düşünce tonu. "
            "Edebî metindir; fetva değildir."
        ),
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    preferred = [
        f
        for f in files
        if any(x in f.name for x in ("Shamela", "ShamAY", "JK", "Rafed", "ALCorpus", "Hindawi"))
    ]
    pool = preferred or files

    def score(p: Path) -> tuple:
        n = p.name
        return (
            1 if "completed" in n else 0,
            1 if "mARkdown" in n else 0,
            p.stat().st_size,
        )

    return max(pool, key=score)


def _strip_openiti(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"^######OpenITI[#\w\-.]+\s*", "", text, flags=re.M)
    text = re.sub(r"^#META#[^\n]*\n?", "", text, flags=re.M)
    text = re.sub(r"^#+$", "", text, flags=re.M)
    text = re.sub(r"PageV\d+P\d+", " ", text)
    text = re.sub(r"~~~+", "\n\n", text)
    text = re.sub(r"@+|\|+|=+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


def _script_ratio(s: str) -> float:
    ar = len(re.findall(r"[\u0600-\u06FF]", s))
    lat = len(re.findall(r"[A-Za-z]", s))
    tot = ar + lat
    return (ar + lat) / tot if tot else 0.0


def _chunk(text: str) -> list[str]:
    text = _strip_openiti(text)
    if not text:
        return []
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > CHUNK * 2:
            if buf:
                chunks.append(buf.strip())
                buf = ""
            for i in range(0, len(p), CHUNK - OVERLAP):
                piece = p[i : i + CHUNK].strip()
                if piece and (_script_ratio(piece) >= 0.12 or len(piece) > 100):
                    chunks.append(piece)
            continue
        if len(buf) + len(p) + 2 <= CHUNK:
            buf = f"{buf}\n\n{p}".strip() if buf else p
        else:
            if buf and _script_ratio(buf) >= 0.10:
                chunks.append(buf.strip())
            buf = p
    if buf and _script_ratio(buf) >= 0.10:
        chunks.append(buf.strip())
    return chunks


def _write_batches(dest: Path, w: dict, chunks: list[str]) -> int:
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    n = 0
    for i in range(0, len(chunks), BATCH):
        n += 1
        part = chunks[i : i + BATCH]
        body = [
            f"# {w['eser_tr']} — paket {n:04d}",
            "",
            f"Yazar: {w['yazar']}",
            "Kaynak: OpenITI Arapça klasik (edebiyat/adab). Fetva değildir; "
            "sayfa/cilt uydurulmaz.",
            "",
        ]
        for j, ch in enumerate(part, 1):
            body += [f"## parça {i + j}", "", ch, ""]
        (incr / f"{w['id']}_batch_{n:04d}.md").write_text(
            "\n".join(body), encoding="utf-8"
        )
    return n


def _update_ortak(man: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    entry = {
        "kaynak_id": man["eser_id"],
        "kaynak_adi": man["eser_tr"],
        "yazar": man["yazar"],
        "ilim_alani": "edebiyat_sanat",
        "eser_turu": "kitap",
        "dil": "ar",
        "yayin": None,
        "cilt": None,
        "bolum": None,
        "sayfa": None,
        "dosya_yolu": man["dosya_yolu"],
        "guvenilirlik": "yuksek",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "not": "OpenITI klasik edebiyat/adab; fetva değil; sayfa uydurma yasak.",
    }
    found = False
    for r in rows:
        if r.get("kaynak_id") == man["eser_id"]:
            r.update(entry)
            found = True
            break
    if not found:
        rows.append(entry)
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_kavramlar(works: list[dict]) -> None:
    rows = [
        {
            "id": "edebiyat",
            "baslik": "edebiyat",
            "aliases": [
                "edebiyat nedir",
                "arap edebiyati",
                "arap edebiyatı",
                "klasik edebiyat",
                "adab",
                "edebiyat sanat",
            ],
            "metin": (
                "Bu rafta klasik Arap edebiyatı ve adab vardır: Kelîle ve Dimne, "
                "makâmât (Hemedânî, Harîrî), Dîvân (Ebû Temmâm, Buḥturî, Maʿarrî), "
                "şi'r tarihi (İbn Kuteybe). Fetva değildir; edebî metindir."
            ),
            "kaynak_notu": "Edebiyat rafı — klasik adab/şiir.",
        },
        {
            "id": "makamat",
            "baslik": "makamat",
            "aliases": ["makâme", "maqama", "maqamat", "makame türü"],
            "metin": (
                "Makâme: klasik Arap nesrinde süslü dil ve serüven anlatısı türü. "
                "Örnekler: Hemedânî ve Harîrî Makâmât. Fetva değildir."
            ),
            "kaynak_notu": "Edebiyat rafı — kavram.",
        },
    ]
    for w in works:
        rows.append(
            {
                "id": w["id"],
                "baslik": w["aliases"][0],
                "aliases": w["aliases"],
                "metin": w["metin"],
                "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
            }
        )
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    CLONE.mkdir(parents=True, exist_ok=True)
    ESER.mkdir(parents=True, exist_ok=True)

    by_repo: dict[str, list[str]] = {}
    for w in OPENITI_WORKS:
        by_repo.setdefault(w["repo"], []).append(f"{w['author']}/{w['work']}")
    for repo, paths in by_repo.items():
        print(f"=== OpenITI {repo} ===")
        _ensure_repo(repo, paths)

    catalog_rows: list[dict] = []
    ok = 0
    for w in OPENITI_WORKS:
        print(f"\n>> {w['id']}")
        work_dir = CLONE / w["repo"] / "data" / w["author"] / w["work"]
        if not work_dir.is_dir():
            print("  [miss] work dir")
            continue
        src = _best_text(work_dir)
        staged = RAW / f"{w['id']}__{src.name}"
        if not staged.is_file() or staged.stat().st_size != src.stat().st_size:
            shutil.copy2(src, staged)
        text = staged.read_text(encoding="utf-8", errors="replace")
        chunks = _chunk(text)
        dest = ESER / w["id"]
        dest.mkdir(parents=True, exist_ok=True)
        n = _write_batches(dest, w, chunks)
        man = {
            "eser_id": w["id"],
            "eser_tr": w["eser_tr"],
            "eser_ar": w["eser_ar"],
            "yazar": w["yazar"],
            "rol": "asıl",
            "eser_turu": "kitap",
            "ilim_alani": "edebiyat_sanat",
            "dil": "ar",
            "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/edebiyat_sanat/eserler/{w['id']}",
            "guvenilirlik": "yuksek",
            "kaynak_sinifi": "kalici",
            "durum": "hazir",
            "kaynak": "OpenITI",
            "source_file": src.name,
            "sha256": hashlib.sha256(staged.read_bytes()).hexdigest(),
            "char_count": len(text),
            "chunk_count": len(chunks),
            "batch_sayisi": n,
            "updated_utc": _utc(),
        }
        (dest / "manifest.json").write_text(
            json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        _update_ortak(man)
        catalog_rows.append(man)
        print(f"  [ok] chunks={len(chunks)} batches={n} <- {src.name}")
        ok += 1

    _write_kavramlar(OPENITI_WORKS)
    cat = {
        "domain": "edebiyat_sanat",
        "kaynak": "OpenITI",
        "updated_utc": _utc(),
        "politika": "Klasik edebiyat/adab. Fetva yok. Sayfa/cilt uydurma yasak.",
        "eserler": catalog_rows,
        "sayilar": {
            "eser": len(catalog_rows),
            "chunk_toplam": sum(int(r.get("chunk_count") or 0) for r in catalog_rows),
        },
    }
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows_md = ["| Eser | Müellif |", "|------|---------|"]
    for r in catalog_rows:
        rows_md.append(
            f"| `{r['eser_id']}` | {(r.get('yazar') or '').split('(')[0].strip()} |"
        )
    (OUT / "README.md").write_text(
        "# Edebiyat ve sanat — klasik Arap adab / şiir\n\n"
        + "\n".join(rows_md)
        + "\n\n"
        f"Yüklenen: **{len(catalog_rows)}** eser · "
        f"**{cat['sayilar']['chunk_toplam']}** chunk\n\n"
        "**Politika:** Fetva yok · OpenITI Arapça · sayfa uydurma yasak.\n"
        "**Script:** `faz12_edebiyat_openiti_ingest.py` · "
        "**Anlık:** `ruzgar_edebiyat_kutuphane.py`\n",
        encoding="utf-8",
    )
    print(f"\nTOPLAM edebiyat eser={ok} chunk={cat['sayilar']['chunk_toplam']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
