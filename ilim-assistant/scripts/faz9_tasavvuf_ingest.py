# -*- coding: utf-8 -*-
"""Tasavvuf Faz 9 — metinler → 09_ahlak_tasavvuf + ortak kayıt güncelleme.

Politika: Fetva yok. Kaynakta olmayan sayfa/cilt/bölüm uydurulmaz.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "09_tasavvuf"
RAW = STAGE / "raw"
OUT = ROOT / "knowledge" / "ilim" / "din" / "09_ahlak_tasavvuf"
INCR = OUT / "incremental"
ESER_DIR = OUT / "eserler"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"

CHUNK = 1600
OVERLAP = 120
BATCH_CHUNKS = 20

_KAYNAK = (
    "Kaynak: klasik tasavvuf / ahlâk metni (OpenITI veya Internet Archive çeviri). "
    "Fetva değildir; sayfa/cilt uydurulmaz."
)

WORKS: list[dict[str, Any]] = [
    {
        "id": "gazali_ihya",
        "eser_tr": "İhyâü Ulûmi'd-Dîn",
        "eser_ar": "إحياء علوم الدين",
        "yazar": "İmam Gazâlî (ö. 505/1111)",
        "rol": "asıl",
        "dil": "ar",
    },
    {
        "id": "gazali_kimya_saadet",
        "eser_tr": "Kimyâ-yı Saâdet",
        "eser_ar": "كيمياء السعادة",
        "yazar": "İmam Gazâlî (ö. 505/1111)",
        "rol": "asıl",
        "dil": "fa",
    },
    {
        "id": "geylani_futuh_gayb",
        "eser_tr": "Fütûhu'l-Gayb",
        "eser_ar": "فتوح الغيب",
        "yazar": "Abdülkadir Geylânî (ö. 561/1166)",
        "rol": "asıl",
        "dil": "en",
    },
    {
        "id": "geylani_feth_rabbani",
        "eser_tr": "el-Fethu'r-Rabbânî",
        "eser_ar": "الفتح الرباني",
        "yazar": "Abdülkadir Geylânî (ö. 561/1166)",
        "rol": "asıl",
        "dil": "en",
    },
    {
        "id": "geylani_ghunya",
        "eser_tr": "el-Gunye li-tâlibî tarîki'l-hak",
        "eser_ar": "الغنية لطالبي طريق الحق",
        "yazar": "Abdülkadir Geylânî (ö. 561/1166)",
        "rol": "yedek",
        "dil": "ar",
    },
    {
        "id": "mevlana_mesnevi",
        "eser_tr": "Mesnevî",
        "eser_ar": "المثنوي",
        "yazar": "Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273)",
        "rol": "asıl",
        "dil": "en",
    },
    {
        "id": "mevlana_divan_kebir",
        "eser_tr": "Divân-ı Kebîr",
        "eser_ar": "ديوان كبير",
        "yazar": "Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273)",
        "rol": "asıl",
        "dil": "en",
    },
    {
        "id": "imam_rabbani_mektubat",
        "eser_tr": "Mektûbât",
        "eser_ar": "مكتوبات",
        "yazar": "İmam Rabbânî Ahmed Sirhindî (ö. 1034/1624)",
        "rol": "asıl",
        "dil": "en",
    },
    {
        "id": "ibn_arabi_futuhat",
        "eser_tr": "Fütûhât-ı Mekkiyye",
        "eser_ar": "الفتوحات المكية",
        "yazar": "Muhyiddin İbnü'l-Arabî (ö. 638/1240)",
        "rol": "asıl",
        "dil": "ar",
    },
    {
        "id": "ibn_arabi_fusus",
        "eser_tr": "Fusûsu'l-Hikem",
        "eser_ar": "فصوص الحكم",
        "yazar": "Muhyiddin İbnü'l-Arabî (ö. 638/1240)",
        "rol": "asıl",
        "dil": "ar",
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _script_ratio(s: str) -> float:
    """Arapça/Farsça/Latin harf oranı — boş/çöp parçaları elemek için."""
    ar = len(re.findall(r"[\u0600-\u06FF]", s))
    lat = len(re.findall(r"[A-Za-z]", s))
    tot = ar + lat
    return (ar + lat) / tot if tot else 0.0


def _strip_openiti(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"^######OpenITI[#\w\-.]+\s*", "", text, flags=re.M)
    text = re.sub(r"^#META#[^\n]*\n?", "", text, flags=re.M)
    text = re.sub(r"^#+$", "", text, flags=re.M)
    text = re.sub(r"PageV\d+P\d+", " ", text)
    text = re.sub(r"~~~+", "\n\n", text)
    text = re.sub(r"@+|\|+|=+", " ", text)
    # OCR gürültüsü
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
                if piece and (_script_ratio(piece) >= 0.15 or len(piece) > 100):
                    chunks.append(piece)
            continue
        if len(buf) + len(p) + 2 <= target:
            buf = f"{buf}\n\n{p}".strip() if buf else p
        else:
            if buf and _script_ratio(buf) >= 0.12:
                chunks.append(buf.strip())
            buf = p
    if buf and _script_ratio(buf) >= 0.12:
        chunks.append(buf.strip())
    return chunks


def _find_raw(eser_id: str) -> Path | None:
    hits = [h for h in RAW.glob(f"{eser_id}__*") if h.is_file() and h.stat().st_size > 1000]
    if not hits:
        return None
    merged = [h for h in hits if "merged" in h.name]
    if merged:
        return max(merged, key=lambda p: p.stat().st_size)
    sham = [h for h in hits if "Shamela" in h.name or "ShamAY" in h.name or "Sham19" in h.name]
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
    return [
        {
            "id": "tasavvuf",
            "baslik": "tasavvuf",
            "aliases": ["sufizm", "tasavvuf nedir", "sufi", "ahlak tasavvuf"],
            "metin": (
                "Tasavvuf: İslâm ahlâk ve mânevî terbiye geleneği; kalp temizliği, "
                "ihlas, zühd ve mârifet temaları. Klasik eserler: Gazâlî İhyâ, "
                "Mevlânâ Mesnevî, İbnü'l-Arabî Fusûs. Rüzgar fetva vermez."
            ),
        },
        {
            "id": "ihya",
            "baslik": "ihya",
            "aliases": ["ihyâ", "ihyau ulum", "gazali ihya", "imam gazali ihya"],
            "metin": (
                "İhyâü Ulûmi'd-Dîn: İmam Gazâlî'nin ahlâk ve dinî ilimler üzerine "
                "klasik eseri. İbadet, âdetler, muhlikât (helâk edici huylar) ve "
                "munciyât (kurtarıcı hasletler) bölümleriyle anılır. "
                "Kalbin hastalıkları bu çerçevede işlenir."
            ),
        },
        {
            "id": "kimya_saadet",
            "baslik": "kimya saadet",
            "aliases": ["kimya-yı saadet", "kimyai saadet", "kimya saadet"],
            "metin": (
                "Kimyâ-yı Saâdet: Gazâlî'nin Farsça eseri; İhyâ'nın özü ve "
                "saadet yolu temalarını daha kısa ve halka açık dilde işler."
            ),
        },
        {
            "id": "kalbin_hastaliklari",
            "baslik": "kalbin hastaliklari",
            "aliases": [
                "kalbin hastalıkları",
                "kalp hastaliklari",
                "kalp hastalıkları",
                "gazali kalp",
            ],
            "metin": (
                "Gazâlî İhyâ'da kalbin hastalıkları (haset, kibir, riya, gaflet vb.) "
                "muhlikât bahislerinde ele alınır; tedavi için tevbe, zikir, "
                "mücahede ve ahlâk terbiyesi önerilir. Kesin sayfa numarası "
                "kütüphane kaydında yoksa uydurulmaz."
            ),
        },
        {
            "id": "mesnevi",
            "baslik": "mesnevi",
            "aliases": ["mesnevî", "mathnawi", "masnavi", "mevlana mesnevi"],
            "metin": (
                "Mesnevî: Mevlânâ Celâleddîn-i Rûmî'nin manzum öğretici eseri. "
                "Hikâye ve temsillerle ahlâkî-mânevî dersler verir."
            ),
        },
        {
            "id": "divan_kebir",
            "baslik": "divan kebir",
            "aliases": ["divân-ı kebîr", "divan-i kebir", "divan shams"],
            "metin": (
                "Divân-ı Kebîr: Mevlânâ'nın gazel ve rubâî külliyatı; "
                "aşk, fena ve mânevî vecd temaları ağırlıklıdır."
            ),
        },
        {
            "id": "mektubat",
            "baslik": "mektubat",
            "aliases": ["mektûbât", "imam rabbani", "sirhindi", "müceddid"],
            "metin": (
                "Mektûbât: İmam Rabbânî Ahmed Sirhindî'nin mektup külliyatı; "
                "tarikat ve şeriat dengesi, sünnet vurgusu temalarıyla anılır."
            ),
        },
        {
            "id": "futuh_gayb",
            "baslik": "futuh gayb",
            "aliases": ["fütûhu'l-gayb", "futuhul gayb", "futuh al ghayb"],
            "metin": (
                "Fütûhu'l-Gayb: Abdülkadir Geylânî'ye nispet edilen vaaz/hitap "
                "derlemesi; kalp terbiyesi ve tevekkül temaları."
            ),
        },
        {
            "id": "feth_rabbani",
            "baslik": "feth rabbani",
            "aliases": ["fethu'r-rabbani", "el-fethur rabbani", "fath rabbani"],
            "metin": (
                "el-Fethu'r-Rabbânî: Geylânî'nin sohbet ve vaaz derlemesi; "
                "tevbe, zikir ve ahlâk öğütleri içerir."
            ),
        },
        {
            "id": "fusus",
            "baslik": "fusus",
            "aliases": ["fusûs", "fususul hikem", "fususu'l-hikem"],
            "metin": (
                "Fusûsu'l-Hikem: İbnü'l-Arabî'nin özlü hikmet eseri. "
                "Şerhler `serh_ve_aciklama/` altına konur."
            ),
        },
        {
            "id": "futuhat",
            "baslik": "futuhat",
            "aliases": ["fütûhât", "futuhat-i mekkiyye", "futuhat makkiyya"],
            "metin": (
                "Fütûhât-ı Mekkiyye: İbnü'l-Arabî'nin geniş külliyatı; "
                "mârifet, mertebeler ve tasavvufî ontoloji bahisleri."
            ),
        },
        {
            "id": "ibn_arabi",
            "baslik": "ibn arabi",
            "aliases": ["ibnü'l-arabi", "muhyiddin", "seyh ekber"],
            "metin": (
                "Muhyiddin İbnü'l-Arabî: Endülüslü sûfî; Fusûs ve Fütûhât "
                "başlıca eserleridir. Rüzgar fetva vermez; şerhler ayrı raftadır."
            ),
        },
    ]


def _write_tr_layers(rows: list[dict[str, Any]]) -> None:
    INCR.mkdir(parents=True, exist_ok=True)
    (OUT / "kavramlar_tasavvuf.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    md = ["# Tasavvuf kavramları (TR)", ""]
    for r in rows:
        md += [
            f"## {r['baslik']}",
            "",
            r["metin"],
            "",
            f"_{_KAYNAK}_",
            "",
        ]
    (INCR / "tasavvuf_kavramlar_tr.md").write_text("\n".join(md), encoding="utf-8")

    rehber = """# Tasavvuf — okuma haritası (TR)

Rüzgar **fetva vermez**. Kısa yol:

1. **Gazâlî:** İhyâ (asıl) · Kimyâ-yı Saâdet
2. **Geylânî:** Fütûhu'l-Gayb · Feth-i Rabbânî · (OpenITI) Gunye
3. **Mevlânâ:** Mesnevî · Divân-ı Kebîr
4. **İmam Rabbânî:** Mektûbât
5. **İbnü'l-Arabî:** Fusûs · Fütûhât · şerhler: `serh_ve_aciklama/`

Akaid için `04_akaid` · hadis `05_hadis` · siyer `08_siyer`.
"""
    (INCR / "tasavvuf_okuma_haritasi_tr.md").write_text(rehber, encoding="utf-8")


def _load_catalog_meta() -> dict[str, dict[str, Any]]:
    path = STAGE / "download_catalog.json"
    if not path.is_file():
        return {}
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        if isinstance(r, dict) and r.get("id"):
            out[str(r["id"])] = r
    return out


def _ingest_work(w: dict[str, Any], cat_meta: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    src = _find_raw(w["id"])
    if not src:
        print(f"  [skip] raw yok: {w['id']}")
        return None
    dest = ESER_DIR / w["id"]
    dest.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8", errors="replace")
    chunks = _chunk(text)
    n = _write_batches(dest, eser_id=w["id"], title=w["eser_tr"], yazar=w["yazar"], chunks=chunks)
    meta = cat_meta.get(w["id"]) or {}
    man = {
        "eser_id": w["id"],
        "eser_tr": w["eser_tr"],
        "eser_ar": w["eser_ar"],
        "yazar": w["yazar"],
        "rol": w["rol"],
        "collection": f"din_09_tasavvuf_{w['id']}",
        "ilim_alani": "tasavvuf",
        "eser_turu": "kitap",
        "dil": w.get("dil") or meta.get("dil") or "ar",
        "yayin": None,
        "cilt": None,
        "bolum": None,
        "sayfa": None,
        "dosya_yolu": f"knowledge/ilim/din/09_ahlak_tasavvuf/eserler/{w['id']}",
        "guvenilirlik": "yuksek" if meta.get("kaynak") == "OpenITI" else "orta",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "kaynak": meta.get("kaynak") or "staging",
        "source_file": src.name,
        "sha256": _sha(src),
        "char_count": len(text),
        "chunk_count": len(chunks),
        "batch_sayisi": n,
        "updated_utc": _utc(),
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  [ok] {w['id']}: {len(chunks)} chunk, {n} batch")
    return man


def _update_ortak_kayit(manifests: list[dict[str, Any]]) -> None:
    if not ORTAK.is_file():
        return
    data = json.loads(ORTAK.read_text(encoding="utf-8"))
    by_id = {m["eser_id"]: m for m in manifests}
    rows = data.get("kayitlar") or []
    for row in rows:
        mid = row.get("kaynak_id")
        if mid in by_id:
            m = by_id[mid]
            row["durum"] = "hazir"
            row["guvenilirlik"] = m.get("guvenilirlik") or "orta"
            row["dil"] = m.get("dil")
            row["yazar"] = m.get("yazar")
            row["cilt"] = None
            row["bolum"] = None
            row["sayfa"] = None
    # yeni (ghunya) ekle
    existing = {r.get("kaynak_id") for r in rows}
    for m in manifests:
        if m["eser_id"] in existing:
            continue
        rows.append(
            {
                "kaynak_id": m["eser_id"],
                "kaynak_adi": m["eser_tr"],
                "yazar": m["yazar"],
                "ilim_alani": "tasavvuf",
                "eser_turu": "kitap",
                "dil": m.get("dil"),
                "yayin": None,
                "cilt": None,
                "bolum": None,
                "sayfa": None,
                "dosya_yolu": m.get("dosya_yolu"),
                "guvenilirlik": m.get("guvenilirlik"),
                "kaynak_sinifi": "kalici",
                "durum": "hazir",
            }
        )
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ortak kayıt güncellendi: {len(manifests)} eser")


def main() -> int:
    print("=== Faz 9 Tasavvuf ingest ===")
    OUT.mkdir(parents=True, exist_ok=True)
    cat_meta = _load_catalog_meta()
    rows = _kavram_rows()
    _write_tr_layers(rows)
    print(f"kavramlar: {len(rows)}")

    manifests: list[dict[str, Any]] = []
    for w in WORKS:
        print(f"\n>> {w['id']}")
        man = _ingest_work(w, cat_meta)
        if man:
            manifests.append(man)

    catalog = {
        "domain": "din_09_ahlak_tasavvuf",
        "kaynak": "OpenITI + Internet Archive",
        "updated_utc": _utc(),
        "politika": "Fetva yok. Sayfa/cilt/bölüm uydurma yasak.",
        "eserler": manifests,
        "sayilar": {
            "eser": len(manifests),
            "chunk_toplam": sum(int(m.get("chunk_count") or 0) for m in manifests),
        },
    }
    (OUT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "modul": "09_ahlak_tasavvuf",
                "ad": "Ahlâk ve Tasavvuf",
                "ilim_alani": "tasavvuf",
                "version": "din-09-tasavvuf-v1-2026-10-07",
                "durum": "hazir" if manifests else "placeholder",
                "eser_sayisi": len(manifests),
                "eserler": [m["eser_id"] for m in manifests],
                "serh_rafi": "serh_ve_aciklama",
                "ortak_kaynak": "knowledge/ortak_kaynak/KAYNAK_KAYIT.json",
                "politika": "Fetva yok. Sayfa/cilt/bölüm uydurma yasak.",
                "updated_utc": _utc(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    readme = f"""# Din / 09 — Ahlâk ve Tasavvuf

**Politika:** Fetva yok. Klasik metin + TR kavram. Sayfa/cilt uydurma yasak.

| Müellif | Eserler |
|---------|---------|
| Gazâlî | İhyâ · Kimyâ-yı Saâdet |
| Geylânî | Fütûhu'l-Gayb · Feth-i Rabbânî · Gunye (OpenITI) |
| Mevlânâ | Mesnevî · Divân-ı Kebîr |
| İmam Rabbânî | Mektûbât |
| İbnü'l-Arabî | Fütûhât · Fusûs · şerh: `serh_ve_aciklama/` |

**Kaynak:** OpenITI + Internet Archive · **Modül:** `ruzgar_tasavvuf_kutuphane`  
**Script:** `faz9_tasavvuf_download.py` + `faz9_tasavvuf_ingest.py`

Yüklenen: **{len(manifests)}** eser · **{catalog['sayilar']['chunk_toplam']}** chunk
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    _update_ortak_kayit(manifests)
    print(f"\nTOPLAM eser={len(manifests)} chunk={catalog['sayilar']['chunk_toplam']}")
    return 0 if len(manifests) >= 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
