# -*- coding: utf-8 -*-
"""Usûl-i fıkıh Faz 7 — OpenITI metinleri → 07_usul_fikh.

Politika: Fetva yok. Usûl kavramı + Arapça klasik matın/muteber eser.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "07_usul_fikh"
RAW = STAGE / "raw"
OUT = ROOT / "knowledge" / "ilim" / "din" / "07_usul_fikh"
INCR = OUT / "incremental"
ESER_DIR = OUT / "eserler"

CHUNK = 1600
OVERLAP = 120
BATCH_CHUNKS = 20

_KAYNAK = (
    "Kaynak: klasik usûl-i fıkıh metni (OpenITI). Fetva değildir; "
    "mezhep usûl farklılıkları ihtilaflı olabilir."
)

WORKS: list[dict[str, Any]] = [
    {"id": "waraqat", "eser_tr": "el-Varakât", "eser_ar": "الورقات",
     "yazar": "İmâmü'l-Haremeyn el-Cüveynî (ö. 478/1085)", "rol": "matn"},
    {"id": "burhan", "eser_tr": "el-Burhân", "eser_ar": "البرهان في أصول الفقه",
     "yazar": "İmâmü'l-Haremeyn el-Cüveynî (ö. 478/1085)", "rol": "muteber"},
    {"id": "mustasfa", "eser_tr": "el-Mustasfâ", "eser_ar": "المستصفى",
     "yazar": "el-Gazzâlî (ö. 505/1111)", "rol": "muteber"},
    {"id": "mankhul", "eser_tr": "el-Menhûl", "eser_ar": "المنخول",
     "yazar": "el-Gazzâlî (ö. 505/1111)", "rol": "muteber"},
    {"id": "bazdawi", "eser_tr": "Usûlü'l-Pezdevî", "eser_ar": "كنز الوصول",
     "yazar": "Fahrülislâm el-Pezdevî (ö. 482/1089)", "rol": "muteber"},
    {"id": "usul_sarakhsi", "eser_tr": "Usûlü's-Serahsî", "eser_ar": "أصول السرخسي",
     "yazar": "eş-Şemsü'l-Eimme es-Serahsî (ö. 483/1090)", "rol": "muteber"},
    {"id": "ihkam_amidi", "eser_tr": "el-İhkâm", "eser_ar": "الإحكام في أصول الأحكام",
     "yazar": "Seyfüddîn el-Âmidî (ö. 631/1233)", "rol": "muteber"},
    {"id": "muntaha_ibn_hajib", "eser_tr": "Muhtasar Müntehâ", "eser_ar": "مختصر منتهى السول",
     "yazar": "İbnü'l-Hâcib (ö. 646/1249)", "rol": "matn"},
    {"id": "minhaj_wusul", "eser_tr": "Minhâcü'l-vusûl", "eser_ar": "منهاج الوصول",
     "yazar": "el-Beyzâvî (ö. 685/1286)", "rol": "matn"},
    {"id": "bahr_muhit", "eser_tr": "el-Bahru'l-muhît", "eser_ar": "البحر المحيط",
     "yazar": "Bedreddîn ez-Zerkeşî (ö. 794/1392)", "rol": "muteber"},
    {"id": "manthur_qawaid", "eser_tr": "el-Mensûr fi'l-kavâid", "eser_ar": "المنثور في القواعد",
     "yazar": "Bedreddîn ez-Zerkeşî (ö. 794/1392)", "rol": "qawaid"},
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
    # Shamila tercih; yoksa en büyük
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
            "id": "usul_fikh",
            "baslik": "usul fikh",
            "aliases": ["usûl-i fıkıh", "usulü fıkıh", "fıkıh usulü", "usul-i fikh", "usul nedir"],
            "metin": (
                "Usûl-i fıkıh: şer'î amelî hükümleri delillerinden çıkarma yöntemleri ilmi. "
                "Kitap, sünnet, icmâ, kıyas ve bağlı delilleri inceler. Furû' fıkıh ayrıntılı "
                "hükümlerdir; usûl ise o hükümlere giden yol. Rüzgar fetva vermez."
            ),
        },
        {
            "id": "delil",
            "baslik": "delil",
            "aliases": ["edille", "şer'i delil", "hukmi delil"],
            "metin": (
                "Delil (şer'î): hükmün dayandığı kaynak. Asıl deliller: Kitap (Kur'an), "
                "sünnet, icmâ, kıyas. Mezheplere göre istihsân, mesâlih, örf vb. fer'î "
                "deliller de tartışılır."
            ),
        },
        {
            "id": "kitap_delil",
            "baslik": "kitap",
            "aliases": ["kur'an delil", "kitabullah usul"],
            "metin": (
                "Kitap: Kur'ân-ı Kerîm — usûlde en üst delil. Âm/hâs, mutlak/mukayyed, "
                "emir/nehiy gibi lafız bahisleri usûlün ana konularındandır."
            ),
        },
        {
            "id": "sunnet_delil",
            "baslik": "sunnet delil",
            "aliases": ["sünnet delil", "haber", "haber-i vâhid"],
            "metin": (
                "Sünnet: Hz. Peygamber'in söz, fiil ve takriri. Mütevâtir / âhâd ayrımı "
                "ve haber-i vâhidin hüccetliği usûlün klasik tartışmalarındandır."
            ),
        },
        {
            "id": "icma",
            "baslik": "icma",
            "aliases": ["icmâ", "icma nedir", "ümmet icması"],
            "metin": (
                "İcmâ: müctehidlerin bir asırda aynı meselede ittifakı. Usûlde hüccet "
                "kabul edilir; şartları mezheplere göre nüanslıdır."
            ),
        },
        {
            "id": "kiyas",
            "baslik": "kiyas",
            "aliases": ["kıyas nedir", "analoji fıkıh", "illah"],
            "metin": (
                "Kıyas: asıldaki hükmü, ortak illet sebebiyle fer'e geçirmek. "
                "Rükünleri: asıl, fer', illet, hüküm. Zâhirîler kıyası reddeder; "
                "dört mezhep genel olarak kabul eder (şartlarla)."
            ),
        },
        {
            "id": "emir_nehiy",
            "baslik": "emir nehiy",
            "aliases": ["emir", "nehiy", "emr-i nehy"],
            "metin": (
                "Emir ve nehiy: lafız bahisleri. Emir vücûb/nedb, nehiy tahrîm/kerâhet "
                "doğurabilir; karîne ve usûl kaideleriyle belirlenir."
            ),
        },
        {
            "id": "amm_hass",
            "baslik": "amm hass",
            "aliases": ["âm hâs", "genel özel", "tahsis"],
            "metin": (
                "Âm ve hâs: genel–özel lafız. Hâs ile âmın tahsisi, nesh ilişkisi "
                "usûlde ayrıntılı işlenir."
            ),
        },
        {
            "id": "nesih",
            "baslik": "nesih",
            "aliases": ["nesh", "mensuh", "nâsih"],
            "metin": (
                "Nesh: şer'î bir hükmün sonradan gelen delille kaldırılması. "
                "Şartları ve kapsamı usûl kitaplarında tartışılır."
            ),
        },
        {
            "id": "ictihad_usul",
            "baslik": "ictihad",
            "aliases": ["içtihat", "müctehid", "taklid usul"],
            "metin": (
                "İçtihad: müctehidin delilden hüküm çıkarması. Taklid: müctehid "
                "olmayanın bir mezhebe uyması. Rüzgar müctehid hükmü vermez."
            ),
        },
        {
            "id": "istihsan",
            "baslik": "istihsan",
            "aliases": ["istihsân", "istislah", "mesalih"],
            "metin": (
                "İstihsân: özellikle Hanefî usûlünde kıyastan ayrılıp daha uygun "
                "delile yönelme. Mesâlih-i mürsele Mâlikî gelenekte öne çıkar. "
                "Şâfiî klasik usûlde istihsâna temkinlidir."
            ),
        },
        {
            "id": "qawaid_fikhiyya",
            "baslik": "kavaid",
            "aliases": ["kavâid", "kavaid-i fıkhiyye", "fıkıh kaideleri"],
            "metin": (
                "Kavâid-i fıkhiyye: birçok furû' hükmü toplayan genel kaideler "
                "(ör. zarar izale edilir). Usûlden ayrı ama yakın bir disiplindir; "
                "Rüzgar'da Zerkeşî Mensûr bu raftadır."
            ),
        },
        {
            "id": "waraqat_eser",
            "baslik": "varakat",
            "aliases": ["varakât", "el varakat", "waraqat", "cüveyni varakat"],
            "metin": (
                "el-Varakât (Cüveynî): kısa usûl matını; öğrenci seviyesinde klasik "
                "giriş metni. Rüzgar: `eserler/waraqat`."
            ),
        },
        {
            "id": "mustasfa_eser",
            "baslik": "mustasfa",
            "aliases": ["mustasfâ", "el mustasfa", "gazzali usul"],
            "metin": (
                "el-Mustasfâ (Gazzâlî): Şâfiî–Eş'arî çizgide usûlün zirve eserlerinden. "
                "Mantık mukaddimesi ve edille bahisleriyle meşhurdur. Rüzgar: `eserler/mustasfa`."
            ),
        },
        {
            "id": "burhan_eser",
            "baslik": "burhan",
            "aliases": ["el burhan", "cüveyni burhan"],
            "metin": (
                "el-Burhân (Cüveynî): geniş usûl; Gazzâlî'nin de beslendiği klasik. "
                "Rüzgar: `eserler/burhan`."
            ),
        },
        {
            "id": "bazdawi_eser",
            "baslik": "pezdevi",
            "aliases": ["pezdervî", "bazdawi", "usulu pezdevi"],
            "metin": (
                "Usûlü'l-Pezdevî (Kenzü'l-vüsûl): Hanefî usûlün temel metinlerinden. "
                "Rüzgar: `eserler/bazdawi`."
            ),
        },
        {
            "id": "furud_usul_fark",
            "baslik": "furu usul",
            "aliases": ["furû usûl", "fıkıh ile usul farkı"],
            "metin": (
                "Furû' fıkıh: namaz, zekât, alışveriş gibi ayrıntılı hükümler (`06_fikh`). "
                "Usûl-i fıkıh: o hükümlerin nasıl çıkarıldığı (`07_usul_fikh`). "
                "İkisi birbirinin yerine geçmez."
            ),
        },
        {
            "id": "fetva_degil_usul",
            "baslik": "fetva",
            "aliases": ["ruzgar fetva usul"],
            "metin": (
                "Rüzgar fetva vermez; usûl kavramı ve klasik metin özeti sunar. "
                "Kişisel hüküm için ehil âlime başvurulur."
            ),
        },
    ]
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "collection": "din_07_usul_fikh_kavram",
                "baslik": r["baslik"],
                "aliases": r["aliases"],
                "metin": r["metin"],
                "kaynak_notu": _KAYNAK,
            }
        )
    return out


def _write_tr_layers(rows: list[dict[str, Any]]) -> None:
    INCR.mkdir(parents=True, exist_ok=True)
    with (OUT / "kavramlar_usul_fikh.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    md = ["# Usûl-i fıkıh kavramları (TR)", ""]
    for row in rows:
        md += [f"## {row['baslik']}", "", row["metin"], "", f"_{row['kaynak_notu']}_", ""]
    (INCR / "usul_fikh_kavramlar_tr.md").write_text("\n".join(md), encoding="utf-8")

    rehber = """# Usûl-i fıkıh — okuma haritası (TR)

Rüzgar **fetva vermez**. Kısa yol:

1. **Giriş matın:** Varakât (Cüveynî)
2. **Geniş muteber:** Mustasfâ (Gazzâlî), Burhân (Cüveynî)
3. **Hanefî usûl:** Pezdevî, Serahsî Usûl
4. **Sistematik:** İhkâm (Âmidî), Muhtasar Müntehâ (İbnü'l-Hâcib), Minhâcü'l-vusûl (Beyzâvî)
5. **Ansiklopedik / kavâid:** Bahru'l-muhît, Mensûr fi'l-kavâid (Zerkeşî)

Furû' için bkz. `06_fikh`.
"""
    (INCR / "usul_fikh_okuma_haritasi_tr.md").write_text(rehber, encoding="utf-8")

    tarih = """# Usûl-i fıkıh kısa tarihçe

1. **Erken:** İmâm Şâfiî'nin er-Risâle'si usûlün sistemleşmesinde dönüm noktasıdır (ayrı yükleme bekleyebilir).
2. **Klasik olgunluk:** Cüveynî, Gazzâlî, Pezdevî, Serahsî — mezhep usûlleri oturdu.
3. **Şerh–muhtasar çağı:** Âmidî, İbnü'l-Hâcib, Beyzâvî matın/şerh zinciri.
4. **Ansiklopedi:** Zerkeşî Bahru'l-muhît usûl bahislerini derler.
5. **Rüzgar:** `07_usul_fikh` kavram + Arapça metin; fetva yok.
"""
    (INCR / "usul_fikh_tarihce_tr.md").write_text(tarih, encoding="utf-8")


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
        "collection": f"din_07_usul_fikh_{w['id']}",
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
    print("=== Faz 7 Usûl-i fıkıh ingest ===")
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
        "domain": "din_07_usul_fikh",
        "kaynak": "OpenITI",
        "updated_utc": _utc(),
        "politika": "Fetva yok. Usûl kavramı + Arapça klasik metin.",
        "eserler": manifests,
        "sayilar": {
            "eser": len(manifests),
            "chunk_toplam": sum(int(m.get("chunk_count") or 0) for m in manifests),
        },
    }
    (OUT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = f"""# Din / 07 — Usûl-i fıkıh

**Politika:** Fetva yok. Klasik Arapça + TR kavram/okuma haritası.

| Rol | Eserler |
|-----|---------|
| Matın | Varakât, Muhtasar Müntehâ, Minhâcü'l-vusûl |
| Muteber | Burhân, Mustasfâ, Menhûl, Pezdevî, Serahsî, İhkâm, Bahru'l-muhît |
| Kavâid | Mensûr fi'l-kavâid |

**Kaynak:** OpenITI · **Modül:** `ruzgar_usul_fikh_kutuphane`  
**Script:** `faz7_usul_fikh_download.py` + `faz7_usul_fikh_ingest.py`

Yüklenen: **{len(manifests)}** eser · **{catalog['sayilar']['chunk_toplam']}** chunk
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(f"\nTOPLAM eser={len(manifests)} chunk={catalog['sayilar']['chunk_toplam']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
