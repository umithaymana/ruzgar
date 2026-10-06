# -*- coding: utf-8 -*-
"""Siyer Faz 8 — OpenITI metinleri → 08_siyer.

Politika: Fetva yok. Klasik siyer/megâzî + TR kavram/okuma haritası.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "08_siyer"
RAW = STAGE / "raw"
OUT = ROOT / "knowledge" / "ilim" / "din" / "08_siyer"
INCR = OUT / "incremental"
ESER_DIR = OUT / "eserler"

CHUNK = 1600
OVERLAP = 120
BATCH_CHUNKS = 20

_KAYNAK = (
    "Kaynak: klasik siyer / megâzî / tabakât metni (OpenITI). "
    "Fetva değildir; rivayet farklılıkları olabilir."
)

WORKS: list[dict[str, Any]] = [
    {
        "id": "sira_ibn_hisham",
        "eser_tr": "es-Sîretü'n-nebeviyye (İbn Hişâm)",
        "eser_ar": "السيرة النبوية",
        "yazar": "İbn Hişâm (ö. 213/828)",
        "rol": "asıl",
    },
    {
        "id": "maghazi_waqidi",
        "eser_tr": "Kitâbü'l-Megâzî",
        "eser_ar": "كتاب المغازي",
        "yazar": "el-Vâkıdî (ö. 207/823)",
        "rol": "maghazi",
    },
    {
        "id": "tabaqat_ibn_sad",
        "eser_tr": "et-Tabakâtü'l-kübrâ",
        "eser_ar": "الطبقات الكبرى",
        "yazar": "İbn Sa'd (ö. 230/845)",
        "rol": "tabakat",
    },
    {
        "id": "tarikh_tabari",
        "eser_tr": "Târîhu'r-rusül ve'l-mülûk",
        "eser_ar": "تاريخ الرسل والملوك",
        "yazar": "et-Taberî (ö. 310/923)",
        "rol": "tarih",
    },
    {
        "id": "ridda_waqidi",
        "eser_tr": "Kitâbü'r-Ridde",
        "eser_ar": "كتاب الردة",
        "yazar": "el-Vâkıdî (ö. 207/823)",
        "rol": "erken",
    },
    {
        "id": "futuh_sham_waqidi",
        "eser_tr": "Fütûhu'ş-Şâm",
        "eser_ar": "فتوح الشام",
        "yazar": "el-Vâkıdî'ye nispet (ö. 207/823)",
        "rol": "futuh",
    },
    {
        "id": "fusul_sira_kathir",
        "eser_tr": "el-Fusûl min sîreti'r-Rasûl",
        "eser_ar": "الفصول من سيرة الرسول",
        "yazar": "İbn Kesîr (ö. 774/1373)",
        "rol": "muteber",
    },
    {
        "id": "bidaya_ibn_kathir",
        "eser_tr": "el-Bidâye ve'n-nihâye",
        "eser_ar": "البداية والنهاية",
        "yazar": "İbn Kesîr (ö. 774/1373)",
        "rol": "muteber",
    },
    {
        "id": "siyar_dhahabi",
        "eser_tr": "Siyeru a'lâmi'n-nübelâ",
        "eser_ar": "سير أعلام النبلاء",
        "yazar": "ez-Zehebî (ö. 748/1348)",
        "rol": "tercuma",
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _arabic_ratio(s: str) -> float:
    ar = len(re.findall(r"[\u0600-\u06FF]", s))
    lat = len(re.findall(r"[A-Za-z]", s))
    tot = ar + lat
    return (ar / tot) if tot else 0.0


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


def _chunk(text: str, target: int = CHUNK) -> list[str]:
    text = _strip_openiti(text)
    if not text:
        return []
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > target * 2:
            if buf:
                chunks.append(buf.strip())
                buf = ""
            for i in range(0, len(p), target - OVERLAP):
                piece = p[i : i + target].strip()
                if piece and (_arabic_ratio(piece) >= 0.20 or len(piece) > 100):
                    chunks.append(piece)
            continue
        if len(buf) + len(p) + 2 <= target:
            buf = f"{buf}\n\n{p}".strip() if buf else p
        else:
            if buf and _arabic_ratio(buf) >= 0.15:
                chunks.append(buf.strip())
            buf = p
    if buf and _arabic_ratio(buf) >= 0.15:
        chunks.append(buf.strip())
    return chunks


def _find_raw(eser_id: str) -> Path | None:
    hits = [h for h in RAW.glob(f"{eser_id}__*") if h.is_file() and h.stat().st_size > 1000]
    if not hits:
        return None
    sham = [h for h in hits if "Shamela" in h.name or "ShamAY" in h.name]
    pool = sham or hits
    return max(pool, key=lambda p: p.stat().st_size)


def _write_batches(dest: Path, *, eser_id: str, title: str, yazar: str, chunks: list[str]) -> int:
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    n_batch = 0
    for i in range(0, len(chunks), BATCH_CHUNKS):
        n_batch += 1
        part = chunks[i : i + BATCH_CHUNKS]
        body = [
            f"# {title} — paket {n_batch:04d}",
            "",
            f"Yazar: {yazar}",
            f"Kaynak: {_KAYNAK}",
            "",
        ]
        for j, ch in enumerate(part, 1):
            body += [f"## parça {i + j}", "", ch, ""]
        (incr / f"{eser_id}_batch_{n_batch:04d}.md").write_text("\n".join(body), encoding="utf-8")
    return n_batch


def _kavram_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "id": "siyer",
            "baslik": "siyer",
            "aliases": ["sira", "sîre", "siret", "siyer nedir", "peygamber hayatı"],
            "metin": (
                "Siyer: Hz. Muhammed'in (s.a.v.) hayatını anlatan ilim ve eserler. "
                "Doğum, bi'set, Mekke–Medine dönemi, gazveler, ahlâk ve sünnet bağlamı. "
                "Klasik kaynak: İbn İshâk → İbn Hişâm. Rüzgar fetva vermez."
            ),
        },
        {
            "id": "maghazi",
            "baslik": "magazi",
            "aliases": ["megazi", "megâzî", "maghazi", "gazve kitabı"],
            "metin": (
                "Megâzî: Hz. Peygamber dönemindeki askerî seferler (gazve/seriyye) "
                "rivayetlerini toplayan disiplin. Vâkıdî'nin Kitâbü'l-Megâzî'si klasiktir."
            ),
        },
        {
            "id": "biset",
            "baslik": "biset",
            "aliases": ["bi'set", "peygamberlik", "vahiy başlangıcı"],
            "metin": (
                "Bi'set: Hz. Muhammed'e peygamberliğin verilmesi (yaklaşık 40 yaşında, "
                "Hira'da ilk vahiy). Siyerde Mekke döneminin başlangıcıdır."
            ),
        },
        {
            "id": "hicret",
            "baslik": "hicret",
            "aliases": ["hicret nedir", "medine hicreti", "muhacir"],
            "metin": (
                "Hicret: Mekke'den Medine'ye göç (622). İslâm takviminin başlangıcı; "
                "Medine dönemi ve Medine toplumunun kurulması siyerin merkezî olaylarındandır."
            ),
        },
        {
            "id": "gazve",
            "baslik": "gazve",
            "aliases": ["gazâ", "seriyye", "sefer"],
            "metin": (
                "Gazve: Hz. Peygamber'in bizzat katıldığı sefer. "
                "Seriyye: O'nun göndermediği/katılmadığı birlik. "
                "Bedir, Uhud, Hendek klasik gazvelerdendir."
            ),
        },
        {
            "id": "bedir",
            "baslik": "bedir",
            "aliases": ["bedir savaşı", "gazve-i bedir"],
            "metin": (
                "Bedir (2/624): Müslümanların ilk büyük zaferi. Kur'an'da da anılır; "
                "siyer ve megâzî eserlerinde ayrıntılı rivayet edilir."
            ),
        },
        {
            "id": "uhud",
            "baslik": "uhud",
            "aliases": ["uhud savaşı", "gazve-i uhud"],
            "metin": (
                "Uhud (3/625): Mekkelilerle yapılan savaş; okçuların mevziyi terk etmesi "
                "ve ağır kayıplarla anılır. Siyerde ders ve sınav teması öne çıkar."
            ),
        },
        {
            "id": "hendek",
            "baslik": "hendek",
            "aliases": ["hendek savaşı", "ahzab", "gazve-i hendek"],
            "metin": (
                "Hendek / Ahzâb (5/627): Medine'nin hendekle savunduğu kuşatma. "
                "Selmân-ı Fârisî'nin hendek önerisi meşhurdur."
            ),
        },
        {
            "id": "fetih_mekke",
            "baslik": "mekke fethi",
            "aliases": ["fetih", "feth-i mekke", "mekke'nin fethi"],
            "metin": (
                "Mekke'nin fethi (8/630): Kan dökülmeden büyük ölçüde gerçekleşen açılış. "
                "Kâbe putlarından arındırma ve genel af siyerin zirve olaylarındandır."
            ),
        },
        {
            "id": "veda_hacci",
            "baslik": "veda hacci",
            "aliases": ["veda hutbesi", "haccetü'l-veda"],
            "metin": (
                "Veda haccı (10/632): Hz. Peygamber'in son haccı ve hutbesi. "
                "Haklar, adalet, kan davasının kaldırılması gibi esaslar vurgulanır."
            ),
        },
        {
            "id": "ibn_hisham",
            "baslik": "ibn hisham",
            "aliases": ["ibn hişam", "ibn hisâm", "siyer ibn hisham"],
            "metin": (
                "İbn Hişâm: İbn İshâk'ın siyerini düzenleyip nakleden klasik kaynak. "
                "Rüzgar: `eserler/sira_ibn_hisham`."
            ),
        },
        {
            "id": "vakidi",
            "baslik": "vakidi",
            "aliases": ["vâkıdî", "el vakidi", "kitabul magazi"],
            "metin": (
                "el-Vâkıdî: megâzî uzmanı; Kitâbü'l-Megâzî sefer rivayetlerinde temeldir. "
                "Rüzgar: `eserler/maghazi_waqidi`."
            ),
        },
        {
            "id": "ibn_sad",
            "baslik": "ibn sad",
            "aliases": ["ibn sa'd", "tabakat kubra", "tabakât"],
            "metin": (
                "İbn Sa'd et-Tabakâtü'l-kübrâ: sahâbe ve tabiin biyografileri; "
                "siyer bölümleri de içerir. Rüzgar: `eserler/tabaqat_ibn_sad`."
            ),
        },
        {
            "id": "tabari_siyer",
            "baslik": "taberi",
            "aliases": ["taberî", "tarih taberi", "tarikh rusul"],
            "metin": (
                "et-Taberî Târîh: genel tarih; risâlet ve Hulefâ dönemi siyer/tarih "
                "için muteber zincirdir. Rüzgar: `eserler/tarikh_tabari`."
            ),
        },
        {
            "id": "fetva_degil_siyer",
            "baslik": "fetva",
            "aliases": ["ruzgar fetva siyer"],
            "metin": (
                "Rüzgar fetva vermez; siyer kavramı ve klasik metin özeti sunar. "
                "İnanç/amel hükmü için ehil âlime başvurulur."
            ),
        },
    ]
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "collection": "din_08_siyer_kavram",
                "baslik": r["baslik"],
                "aliases": r["aliases"],
                "metin": r["metin"],
                "kaynak_notu": _KAYNAK,
            }
        )
    return out


def _write_tr_layers(rows: list[dict[str, Any]]) -> None:
    INCR.mkdir(parents=True, exist_ok=True)
    with (OUT / "kavramlar_siyer.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    md = ["# Siyer kavramları (TR)", ""]
    for row in rows:
        md += [f"## {row['baslik']}", "", row["metin"], "", f"_{row['kaynak_notu']}_", ""]
    (INCR / "siyer_kavramlar_tr.md").write_text("\n".join(md), encoding="utf-8")

    rehber = """# Siyer — okuma haritası (TR)

Rüzgar **fetva vermez**. Kısa yol:

1. **Asıl siyer:** İbn Hişâm (İbn İshâk düzenlemesi)
2. **Megâzî:** Vâkıdî Kitâbü'l-Megâzî
3. **Tabakât / biyografi:** İbn Sa'd Tabakâtü'l-kübrâ
4. **Tarih zinciri:** Taberî Târîh (risâlet bahisleri)
5. **Geniş muteber (varsa):** İbn Kesîr Bidâye, Zehebî Siyer

Hadis için bkz. `05_hadis` · furû' için `06_fikh`.
"""
    (INCR / "siyer_okuma_haritasi_tr.md").write_text(rehber, encoding="utf-8")

    tarih = """# Siyer kısa tarihçe

1. **Erken:** İbn İshâk'ın siyer nüshası (bugün İbn Hişâm üzerinden).
2. **Megâzî:** Vâkıdî ve çağdaşları sefer rivayetlerini derledi.
3. **Tabakât:** İbn Sa'd sahâbe/tabiin tabakalarını yazdı.
4. **Tarih:** Taberî genel tarihte risâleti sistematik anlattı.
5. **Rüzgar:** `08_siyer` kavram + Arapça metin; fetva yok.
"""
    (INCR / "siyer_tarihce_tr.md").write_text(tarih, encoding="utf-8")


def _ingest_work(w: dict[str, Any]) -> dict[str, Any] | None:
    src = _find_raw(w["id"])
    if not src:
        print(f"  [skip] raw yok: {w['id']}")
        return None
    dest = ESER_DIR / w["id"]
    dest.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8", errors="replace")
    chunks = _chunk(text)
    n = _write_batches(dest, eser_id=w["id"], title=w["eser_tr"], yazar=w["yazar"], chunks=chunks)
    man = {
        "eser_id": w["id"],
        "eser_tr": w["eser_tr"],
        "eser_ar": w["eser_ar"],
        "yazar": w["yazar"],
        "rol": w["rol"],
        "collection": f"din_08_siyer_{w['id']}",
        "kaynak": "OpenITI",
        "source_file": src.name,
        "sha256": _sha(src),
        "char_count": len(text),
        "chunk_count": len(chunks),
        "batch_sayisi": n,
        "updated_utc": _utc(),
    }
    (dest / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  [ok] {w['id']}: {len(chunks)} chunk, {n} batch")
    return man


def main() -> int:
    print("=== Faz 8 Siyer ingest ===")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = _kavram_rows()
    _write_tr_layers(rows)
    print(f"kavramlar: {len(rows)}")

    manifests: list[dict[str, Any]] = []
    for w in WORKS:
        print(f"\n>> {w['id']}")
        man = _ingest_work(w)
        if man:
            manifests.append(man)

    catalog = {
        "domain": "din_08_siyer",
        "kaynak": "OpenITI",
        "updated_utc": _utc(),
        "politika": "Fetva yok. Siyer kavramı + Arapça klasik metin.",
        "eserler": manifests,
        "sayilar": {
            "eser": len(manifests),
            "chunk_toplam": sum(int(m.get("chunk_count") or 0) for m in manifests),
        },
    }
    (OUT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = f"""# Din / 08 — Siyer

**Politika:** Fetva yok. Klasik Arapça + TR kavram/okuma haritası.

| Rol | Eserler |
|-----|---------|
| Asıl | İbn Hişâm Sîre |
| Megâzî | Vâkıdî Megâzî |
| Tabakât | İbn Sa'd Tabakâtü'l-kübrâ |
| Tarih | Taberî Târîh |
| Erken / fütuh | Ridde, Fütûhu'ş-Şâm |
| Muteber (varsa) | İbn Kesîr Bidâye, Zehebî Siyer |

**Kaynak:** OpenITI · **Modül:** `ruzgar_siyer_kutuphane`  
**Script:** `faz8_siyer_download.py` + `faz8_siyer_ingest.py`

Yüklenen: **{len(manifests)}** eser · **{catalog['sayilar']['chunk_toplam']}** chunk
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(f"\nTOPLAM eser={len(manifests)} chunk={catalog['sayilar']['chunk_toplam']}")
    return 0 if manifests else 1


if __name__ == "__main__":
    raise SystemExit(main())
