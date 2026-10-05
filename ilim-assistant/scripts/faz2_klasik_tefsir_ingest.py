# -*- coding: utf-8 -*-
"""Klasik tefsir ingest — her eser ayrı klasör; Kur'an Yolu'na dokunmaz.

Kaynak: spa5k/tafsir_api (ayah hizalı Arapça JSON)
Sıra: ibn_kesir → taberi → kurtubi → beyzavi → razi
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "02_tefsir" / "klasik"
OUT_ROOT = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "klasik"
# Kur'an Yolu yolu — ASLA yazma
KURAN_YOLU = ROOT / "knowledge" / "ilim" / "din" / "02_tefsir" / "kuran_yolu"

AYET_SAYILARI = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111,
    110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45,
    83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55,
    78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20,
    56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21,
    11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
]
SURE_ADLARI = [
    "Fatiha", "Bakara", "Al-i Imran", "Nisa", "Maide", "Enam", "Araf", "Enfal",
    "Tevbe", "Yunus", "Hud", "Yusuf", "Rad", "Ibrahim", "Hicr", "Nahl", "Isra",
    "Kehf", "Meryem", "Taha", "Enbiya", "Hac", "Muminun", "Nur", "Furkan",
    "Suara", "Neml", "Kasas", "Ankebut", "Rum", "Lokman", "Secde", "Ahzab",
    "Sebe", "Fatir", "Yasin", "Saffat", "Sad", "Zumer", "Mumin", "Fussilet",
    "Sura", "Zuhruf", "Duhan", "Casiye", "Ahkaf", "Muhammed", "Fetih", "Hucurat",
    "Kaf", "Zariyat", "Tur", "Necm", "Kamer", "Rahman", "Vakia", "Hadid",
    "Mucadele", "Hasr", "Mumtehine", "Saff", "Cuma", "Munafikun", "Tegabun",
    "Talak", "Tahrim", "Mulk", "Kalem", "Hakka", "Mearic", "Nuh", "Cin",
    "Muzzemmil", "Muddessir", "Kiyame", "Insan", "Murselat", "Nebe", "Naziat",
    "Abese", "Tekvir", "Infitar", "Mutaffifin", "Insikak", "Buruc", "Tarik",
    "Ala", "Gasiye", "Fecr", "Beled", "Sems", "Leyl", "Duha", "Insirah", "Tin",
    "Alak", "Kadr", "Beyyine", "Zilzal", "Adiyat", "Karia", "Tekasur", "Asr",
    "Humaze", "Fil", "Kureys", "Maun", "Kevser", "Kafirun", "Nasr", "Tebbet",
    "Ihlas", "Felak", "Nas",
]

# Mimar sırası — bir eser bitmeden sonrakine geçilmez
WORKS: dict[str, dict] = {
    "ibn_kesir": {
        "slug": "ar-tafsir-ibn-kathir",
        "eser": "Tefsîru'l-Kur'âni'l-Azîm",
        "yazar": "İbn Kesîr (Ebü'l-Fidâ İsmâîl b. Ömer)",
        "dil": "ar",
        "collection": "din_02_tefsir_klasik_ibn_kesir",
        "hf_config": "tafsir-ibnkathir-ar",
    },
    "taberi": {
        "slug": "ar-tafsir-al-tabari",
        "eser": "Câmiu'l-beyân an te'vîli âyi'l-Kur'ân",
        "yazar": "Taberî (Ebû Ca'fer Muhammed b. Cerîr)",
        "dil": "ar",
        "collection": "din_02_tefsir_klasik_taberi",
        "hf_config": "tafsir-tabari-ar",
    },
    "kurtubi": {
        "slug": "ar-tafseer-al-qurtubi",
        "eser": "el-Câmi' li-ahkâmi'l-Kur'ân",
        "yazar": "Kurtubî (Ebû Abdillâh Muhammed b. Ahmed)",
        "dil": "ar",
        "collection": "din_02_tefsir_klasik_kurtubi",
        "hf_config": "tafsir-qurtubi-ar",
    },
    "beyzavi": {
        "slug": "tafsir-al-baydawi",
        "eser": "Envârü't-tenzîl ve esrârü't-te'vîl",
        "yazar": "Beyzâvî (Nâsırüddîn Abdullâh b. Ömer)",
        "dil": "ar",
        "collection": "din_02_tefsir_klasik_beyzavi",
        "hf_config": "tafsir-baydawi-ar",
        "prefer_hf": True,
    },
    "razi": {
        "slug": "tafsir-al-razi",
        "eser": "Mefâtîhu'l-gayb (et-Tefsîrü'l-kebîr)",
        "yazar": "Fahreddin er-Râzî",
        "dil": "ar",
        "collection": "din_02_tefsir_klasik_razi",
        "hf_config": "tafsir-razi-ar",
        "prefer_hf": True,
    },
}

ORDER = ["ibn_kesir", "taberi", "kurtubi", "beyzavi", "razi"]

BASES = [
    "https://raw.githubusercontent.com/spa5k/tafsir_api/main/tafsir",
    "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir",
]


def _clean_text(t: str) -> str:
    raw = (t or "").strip()
    if not raw:
        return ""
    # editorial brackets [[...]] lightly strip — ama tüm metin buysa koru
    stripped = re.sub(r"\[\[[^\]]*\]\]", "", raw)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    if stripped:
        return stripped
    # yalnızca dipnot kaldıysa: köşeli parantezleri aç, metni tut
    kept = re.sub(r"\[\[|\]\]", "", raw)
    kept = re.sub(r"\s+", " ", kept).strip()
    return kept


def download_surah(slug: str, sure_no: int, dest: Path, retries: int = 4) -> list[dict]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 50:
        return json.loads(dest.read_text(encoding="utf-8"))
    last_err: Exception | None = None
    for base in BASES:
        url = f"{base}/{slug}/{sure_no}.json"
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "RuzgarIlim/1.0"})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    raw = resp.read()
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, list):
                    raise ValueError(f"unexpected json type {type(data)}")
                dest.write_bytes(raw)
                return data
            except Exception as e:
                last_err = e
                time.sleep(0.6 * (attempt + 1))
        # try next base
    raise RuntimeError(f"download failed {slug} sure {sure_no}: {last_err}")


def load_from_hf(work_id: str, meta: dict, stage: Path) -> dict[tuple[int, int], str] | None:
    """HuggingFace quranlab/quran-tafsir parquet → {(sure,ayet): text}."""
    cfg = meta.get("hf_config")
    if not cfg:
        return None
    try:
        from huggingface_hub import hf_hub_download
        import pyarrow.parquet as pq
    except ImportError as e:
        print(f"  [hf] import fail {e}")
        return None
    rel = f"{cfg}/train-00000-of-00001.parquet"
    print(f"  [hf] downloading {rel} ...", flush=True)
    local = hf_hub_download("quranlab/quran-tafsir", rel, repo_type="dataset")
    # staging kopyası
    dest = stage / "hf_source.parquet"
    if not dest.exists() or dest.stat().st_size == 0:
        dest.write_bytes(Path(local).read_bytes())
    table = pq.read_table(local)
    surahs = table.column("surah").to_pylist()
    ayahs = table.column("ayah").to_pylist()
    texts = table.column("text").to_pylist()
    out: dict[tuple[int, int], str] = {}
    for s, a, t in zip(surahs, ayahs, texts):
        if not isinstance(s, int) or not isinstance(a, int):
            continue
        cleaned = _clean_text(t or "")
        if not cleaned:
            continue
        prev = out.get((s, a), "")
        if len(cleaned) > len(prev):
            out[(s, a)] = cleaned
    print(f"  [hf] loaded {len(out)} ayah texts", flush=True)
    return out


def ingest_work(work_id: str, *, force: bool = False) -> dict:
    meta = WORKS[work_id]
    out = OUT_ROOT / work_id
    stage = STAGE / work_id
    out.mkdir(parents=True, exist_ok=True)
    stage.mkdir(parents=True, exist_ok=True)

    idx_path = out / "tefsir_ayet_indeks.jsonl"
    blok_path = out / "tefsir_bloklari.jsonl"
    man_path = out / "manifest.json"
    inc_dir = out / "incremental"

    if idx_path.is_file() and not force:
        existing_qa = {}
        if man_path.is_file():
            existing_qa = (json.loads(man_path.read_text(encoding="utf-8")).get("qa") or {})
        if existing_qa.get("tam_tefsir"):
            print(f"[skip] {work_id} already complete")
            return existing_qa

    rows: list[dict] = []
    blocks: list[dict] = []
    sha = hashlib.sha256()
    source_note = f"spa5k:tafsir_api:{meta['slug']}"

    hf_map: dict[tuple[int, int], str] | None = None
    if meta.get("prefer_hf") or force:
        hf_map = load_from_hf(work_id, meta, stage)

    # spa5k sure sure (HF yoksa veya tamamlayıcı)
    spa_map: dict[tuple[int, int], str] = {}
    if not hf_map or len(hf_map) < 6000:
        for sure_no in range(1, 115):
            raw_path = stage / f"sure_{sure_no:03d}.json"
            try:
                data = download_surah(meta["slug"], sure_no, raw_path)
            except Exception as e:
                print(f"  [spa5k] sure {sure_no} fail: {e}", flush=True)
                data = []
            sha.update(f"{sure_no}:{len(data)}".encode())
            by_ayah: dict[int, str] = {}
            for item in data:
                a = item.get("ayah")
                if not isinstance(a, int):
                    continue
                txt = _clean_text(item.get("text") or "")
                if not txt:
                    continue
                prev = by_ayah.get(a, "")
                if len(txt) > len(prev):
                    by_ayah[a] = txt
            for a, txt in by_ayah.items():
                spa_map[(sure_no, a)] = txt
            print(f"  {work_id} sure {sure_no}/114 spa5k={len(by_ayah)}", flush=True)

    # birleştir: prefer_hf ise HF birincil, spa5k boşluk doldurur
    combined: dict[tuple[int, int], str] = {}
    if meta.get("prefer_hf") and hf_map:
        combined.update(hf_map)
        source_note = f"huggingface:quranlab/quran-tafsir:{meta.get('hf_config')}"
        for k, v in spa_map.items():
            if k not in combined or len(v) > len(combined[k]):
                combined[k] = v
    else:
        combined.update(spa_map)
        if hf_map:
            for k, v in hf_map.items():
                if k not in combined or len(v) > len(combined.get(k, "")):
                    combined[k] = v
                    source_note = f"spa5k+hf:{meta['slug']}"

    for sure_no in range(1, 115):
        for a in range(1, AYET_SAYILARI[sure_no - 1] + 1):
            tefsir = combined.get((sure_no, a), "")
            row = {
                "collection": meta["collection"],
                "tip": "ayet_tefsir",
                "eser": meta["eser"],
                "eser_id": work_id,
                "yazar": meta["yazar"],
                "dil": meta["dil"],
                "sure_no": sure_no,
                "sure_adi_tr": SURE_ADLARI[sure_no - 1],
                "ayet_no": a,
                "ayet_bas": a,
                "ayet_bit": a,
                "tefsir_blok": tefsir,
                "meal_blok": "",
                "kaynak": source_note,
            }
            rows.append(row)
            if tefsir:
                blocks.append(
                    {
                        "collection": meta["collection"],
                        "tip": "ayet_tefsir",
                        "eser": meta["eser"],
                        "eser_id": work_id,
                        "yazar": meta["yazar"],
                        "dil": meta["dil"],
                        "sure_no": sure_no,
                        "sure_adi_tr": SURE_ADLARI[sure_no - 1],
                        "ayet_bas": a,
                        "ayet_bit": a,
                        "tefsir": tefsir[:200000],
                        "meal": "",
                        "kaynak": source_note,
                    }
                )

    with idx_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with blok_path.open("w", encoding="utf-8") as f:
        for b in blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    qa = fine_tune_qa(work_id, rows)
    write_incremental_md(work_id, meta, rows, inc_dir)

    man = {
        "ok": qa.get("tam_tefsir", False),
        "version": f"din-02-tefsir-klasik-{work_id}-v1",
        "eser_id": work_id,
        "eser": meta["eser"],
        "yazar": meta["yazar"],
        "dil": meta["dil"],
        "collection": meta["collection"],
        "kaynak": source_note,
        "slug": meta["slug"],
        "hf_config": meta.get("hf_config"),
        "staging": str(stage.relative_to(ROOT)).replace("\\", "/"),
        "ciktilar": {
            "ayet_indeks": str(idx_path.relative_to(ROOT)).replace("\\", "/"),
            "bloklar": str(blok_path.relative_to(ROOT)).replace("\\", "/"),
            "incremental": str(inc_dir.relative_to(ROOT)).replace("\\", "/"),
        },
        "ayrilik": {
            "kuran_yolu_dokunulmadi": True,
            "kuran_yolu_path": "knowledge/ilim/din/02_tefsir/kuran_yolu",
        },
        "content_fingerprint": sha.hexdigest()[:16],
        "qa": qa,
    }
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_catalog()
    return qa


def fine_tune_qa(work_id: str, rows: list[dict] | None = None) -> dict:
    out = OUT_ROOT / work_id
    if rows is None:
        rows = [
            json.loads(l)
            for l in (out / "tefsir_ayet_indeks.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
    by = {(r["sure_no"], r["ayet_no"]): r for r in rows}
    miss, empty, short = [], [], []
    for s, n in enumerate(AYET_SAYILARI, 1):
        for a in range(1, n + 1):
            r = by.get((s, a))
            if not r:
                miss.append([s, a])
                continue
            t = (r.get("tefsir_blok") or "").strip()
            if not t:
                empty.append([s, a])
            elif len(t) < 20:
                short.append([s, a])
    # Komşu ayetten doldurma denemesi (aynı surede uzun komşu varsa not düş — kopyalama yok)
    # Eksikleri staging ham JSON'dan tekrar birleştir
    if empty or miss:
        stage = STAGE / work_id
        meta = WORKS[work_id]
        fixed = 0
        for s, a in list(empty) + list(miss):
            raw_path = stage / f"sure_{s:03d}.json"
            if not raw_path.is_file():
                continue
            data = json.loads(raw_path.read_text(encoding="utf-8"))
            cands = [
                _clean_text(x.get("text") or "")
                for x in data
                if x.get("ayah") == a and (x.get("text") or "").strip()
            ]
            if not cands:
                continue
            best = max(cands, key=len)
            if len(best) < 20:
                continue
            if (s, a) in by:
                by[(s, a)]["tefsir_blok"] = best
            else:
                by[(s, a)] = {
                    "collection": meta["collection"],
                    "tip": "ayet_tefsir",
                    "eser": meta["eser"],
                    "eser_id": work_id,
                    "yazar": meta["yazar"],
                    "dil": meta["dil"],
                    "sure_no": s,
                    "sure_adi_tr": SURE_ADLARI[s - 1],
                    "ayet_no": a,
                    "ayet_bas": a,
                    "ayet_bit": a,
                    "tefsir_blok": best,
                    "meal_blok": "",
                    "kaynak": f"spa5k:tafsir_api:{meta['slug']}:retry",
                }
            fixed += 1
        if fixed:
            rows = [by[(s, a)] for s, n in enumerate(AYET_SAYILARI, 1) for a in range(1, n + 1) if (s, a) in by]
            with (out / "tefsir_ayet_indeks.jsonl").open("w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            miss, empty, short = [], [], []
            for s, n in enumerate(AYET_SAYILARI, 1):
                for a in range(1, n + 1):
                    r = by.get((s, a))
                    if not r:
                        miss.append([s, a])
                        continue
                    t = (r.get("tefsir_blok") or "").strip()
                    if not t:
                        empty.append([s, a])
                    elif len(t) < 20:
                        short.append([s, a])

    covered = 6236 - len(miss) - len(empty)
    qa = {
        "hedef": 6236,
        "indeks_adet": len(by),
        "dolu_tefsir": covered,
        "eksik_kayit": miss[:50],
        "eksik_kayit_adet": len(miss),
        "bos_tefsir": empty[:50],
        "bos_tefsir_adet": len(empty),
        "kisa_tefsir_adet": len(short),
        "kisa_tefsir_ornek": short[:20],
        "tam_tefsir": len(miss) == 0 and len(empty) == 0,
        "kapsama_orani": round(covered / 6236, 4),
    }
    print(json.dumps({"work": work_id, **{k: qa[k] for k in ('dolu_tefsir','bos_tefsir_adet','eksik_kayit_adet','tam_tefsir','kapsama_orani')}}, ensure_ascii=False))
    return qa


def write_incremental_md(work_id: str, meta: dict, rows: list[dict], inc_dir: Path) -> None:
    """RAG için ayet başı kısa özet md (max ~600 char) — eserler karışmaz."""
    inc_dir.mkdir(parents=True, exist_ok=True)
    # temizle eski
    for old in inc_dir.glob("*.md"):
        old.unlink()
    batch_size = 80
    batch: list[str] = []
    bi = 1

    def flush() -> None:
        nonlocal bi, batch
        if not batch:
            return
        path = inc_dir / f"{work_id}_batch_{bi:04d}.md"
        header = (
            f"# Tefsir — {meta['eser']}\n"
            f"Yazar: {meta['yazar']}\n"
            f"Eser-ID: {work_id}\n"
            f"Dil: {meta['dil']}\n"
            f"Koleksiyon: {meta['collection']}\n\n"
        )
        path.write_text(header + "\n\n".join(batch), encoding="utf-8")
        bi += 1
        batch = []

    for r in rows:
        t = (r.get("tefsir_blok") or "").strip()
        if not t:
            continue
        excerpt = t[:600]
        batch.append(
            f"## {r['sure_adi_tr']} {r['sure_no']}:{r['ayet_no']}\n"
            f"Kaynak: {meta['eser']} ({work_id})\n\n{excerpt}"
        )
        if len(batch) >= batch_size:
            flush()
    flush()


def update_catalog() -> None:
    catalog = {
        "version": "din-02-tefsir-library-v2",
        "not": "Kur'an Yolu modern katmanda ayrıdır; klasik eserler burada.",
        "modern": {
            "kuran_yolu": {
                "path": "knowledge/ilim/din/02_tefsir/kuran_yolu",
                "manifest": "knowledge/ilim/din/02_tefsir/manifest.json",
            }
        },
        "klasik_sira": ORDER,
        "klasik": {},
    }
    for wid in ORDER:
        man = OUT_ROOT / wid / "manifest.json"
        if man.is_file():
            catalog["klasik"][wid] = json.loads(man.read_text(encoding="utf-8"))
        else:
            catalog["klasik"][wid] = {"ok": False, "eser_id": wid, "durum": "bekliyor"}
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", choices=ORDER + ["all"], default="all")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--qa-only", action="store_true", help="Sadece mevcut indeks QA")
    args = ap.parse_args()
    assert not str(OUT_ROOT).startswith(str(KURAN_YOLU)), "klasik out must not be under kuran_yolu"
    works = ORDER if args.work == "all" else [args.work]
    for wid in works:
        print(f"=== {wid} ===", flush=True)
        if args.qa_only:
            qa = fine_tune_qa(wid)
            man_path = OUT_ROOT / wid / "manifest.json"
            if man_path.is_file():
                man = json.loads(man_path.read_text(encoding="utf-8"))
                man["qa"] = qa
                man["ok"] = bool(qa.get("tam_tefsir"))
                man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            update_catalog()
            if not qa.get("tam_tefsir"):
                print(f"[WARN] {wid} incomplete — sonraki esere geçmeden düzeltin")
                break
            continue
        qa = ingest_work(wid, force=args.force)
        if not qa.get("tam_tefsir"):
            print(f"[STOP] {wid} ince ayar tamam değil; sonraki esere geçilmedi.")
            break
        print(f"[OK] {wid} ince ayar tamam — sonraki esere geçilebilir.")


if __name__ == "__main__":
    main()
