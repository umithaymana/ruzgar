# -*- coding: utf-8 -*-
"""Hadis Faz 5 — Kutüb-i Sitte: her eser ayrı kütüphane raftı.

Kaynak (birincil, Arapça matn):
  fawazahmed0/hadith-api @1 (jsDelivr CDN)
  ara-bukhari / ara-muslim / ara-abudawud / ara-tirmidhi / ara-nasai / ara-ibnmajah

Çıktı:
  knowledge/ilim/din/05_hadis/
    README.md
    catalog.json
    kavramlar_hadis.jsonl
    incremental/hadis_kavramlar_tr.md
    kutub_i_sitte/{eser_id}/
      manifest.json
      hadisler.jsonl
      bolumler.json
      incremental/*.md
  arsiv/_ilim_staging/05_hadis/raw/*.json  (ham baskı yedeği)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "05_hadis"
RAW = STAGE / "raw"
OUT = ROOT / "knowledge" / "ilim" / "din" / "05_hadis"
SITTE = OUT / "kutub_i_sitte"
INCR_ROOT = OUT / "incremental"

CDN = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
CDN_ALT = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"

# Mimar emri: altı eser ayrı ayrı rafta
WORKS: dict[str, dict[str, Any]] = {
    "buhari": {
        "edition": "ara-bukhari",
        "eser_tr": "Sahîh-i Buhârî",
        "eser_ar": "صحيح البخاري",
        "yazar": "İmam Buhârî (Muhammed b. İsmâîl el-Buhârî)",
        "collection": "din_05_hadis_buhari",
        "aliases": ["buhari", "buhârî", "bukhari", "sahih buhari", "sahîh-i buhârî"],
    },
    "muslim": {
        "edition": "ara-muslim",
        "eser_tr": "Sahîh-i Müslim",
        "eser_ar": "صحيح مسلم",
        "yazar": "İmam Müslim (Müslim b. el-Haccâc)",
        "collection": "din_05_hadis_muslim",
        "aliases": ["muslim", "müslim", "sahih muslim", "sahîh-i müslim"],
    },
    "ebu_davud": {
        "edition": "ara-abudawud",
        "eser_tr": "Sünen-i Ebû Dâvûd",
        "eser_ar": "سنن أبي داود",
        "yazar": "Ebû Dâvûd es-Sicistânî",
        "collection": "din_05_hadis_ebu_davud",
        "aliases": ["ebu davud", "ebû dâvûd", "abu dawud", "ebu davûd", "sünen ebu davud"],
    },
    "tirmizi": {
        "edition": "ara-tirmidhi",
        "eser_tr": "Câmiu't-Tirmizî",
        "eser_ar": "جامع الترمذي",
        "yazar": "İmam Tirmizî (Muhammed b. Îsâ)",
        "collection": "din_05_hadis_tirmizi",
        "aliases": ["tirmizi", "tirmizî", "tirmidhi", "cami tirmizi"],
    },
    "nesai": {
        "edition": "ara-nasai",
        "eser_tr": "Sünen-i Nesâî",
        "eser_ar": "سنن النسائي",
        "yazar": "İmam Nesâî (Ahmed b. Şuayb)",
        "collection": "din_05_hadis_nesai",
        "aliases": ["nesai", "nesâî", "nasai", "sünen nesai"],
    },
    "ibn_mace": {
        "edition": "ara-ibnmajah",
        "eser_tr": "Sünen-i İbn Mâce",
        "eser_ar": "سنن ابن ماجه",
        "yazar": "İbn Mâce (Muhammed b. Yezîd)",
        "collection": "din_05_hadis_ibn_mace",
        "aliases": ["ibn mace", "ibn mâce", "ibn majah", "ibn mâce", "sünen ibn mace"],
    },
}

ORDER = ["buhari", "muslim", "ebu_davud", "tirmizi", "nesai", "ibn_mace"]

BATCH_SIZE = 25  # hadis / md dosya (RAG *.md)

_KAYNAK = (
    "Kaynak: fawazahmed0/hadith-api (Arapça matn, Kutüb-i Sitte). "
    "Numaralandırma API hadithnumber / reference.book+hadith. Fetva değildir."
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(edition: str, *, timeout: int = 300) -> bytes:
    urls = [f"{CDN}/{edition}.json", f"{CDN_ALT}/{edition}.json"]
    last: Exception | None = None
    for url in urls:
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "RuzgarHadisIngest/1.0"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.read()
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last = exc
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"İndirilemedi: {edition} ({last})")


def _clean_ar(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


def _write_kavramlar() -> int:
    rows = [
        {
            "id": "hadis",
            "collection": "din_05_hadis_kavram",
            "baslik": "hadis",
            "aliases": ["hadis nedir", "hadîs", "sünnet nedir", "hadis ilmi"],
            "metin": (
                "Hadis (حديث), Hz. Peygamber'in söz, fiil, takrir ve sıfatlarını "
                "nakleden rivayettir. Hadis ilmi; isnad, metin, cerh-ta'dil ve "
                "tasnif usûllerini kapsar. Rüzgar kütüphanesinde Kutüb-i Sitte "
                "Arapça matınları ayrı raflarda tutulur."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "kutub_i_sitte",
            "collection": "din_05_hadis_kavram",
            "baslik": "kutub-i sitte",
            "aliases": [
                "kütüb-i sitte",
                "kutubi sitte",
                "altı kitap",
                "sahihler ve sünenler",
            ],
            "metin": (
                "Kutüb-i Sitte (الكتب الستة): Buhârî, Müslim, Ebû Dâvûd, Tirmizî, "
                "Nesâî ve İbn Mâce. İlk ikisi «Sahîhayn»; diğerleri sünen/câmi "
                "geleneğindedir. Her eser Rüzgar'da ayrı kütüphane raftıdır."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "isnad",
            "collection": "din_05_hadis_kavram",
            "baslik": "isnad",
            "aliases": ["isnad nedir", "sened", "senet"],
            "metin": (
                "İsnad (إسناد), hadisin metnine ulaşan râviler zinciridir. "
                "«Haddesenâ / ahberenâ» kalıplarıyla başlar. Metnin üstündeki "
                "sened, râvi tenkidi (cerh-ta'dil) ile değerlendirilir."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "metin_hadis",
            "collection": "din_05_hadis_kavram",
            "baslik": "metin",
            "aliases": ["metin nedir", "hadis metni", "matn"],
            "metin": (
                "Metin (متن), hadisin asıl söz/fiil kısmıdır; isnadın ardından gelir. "
                "Rüzgar cevabında Arapça matın kaynak numarasıyla verilir."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "sahih",
            "collection": "din_05_hadis_kavram",
            "baslik": "sahih",
            "aliases": ["sahih hadis", "sahîh", "sahih nedir"],
            "metin": (
                "Sahih hadis: adâletli ve zabtı kuvvetli râvilerle muttasıl isnad, "
                "şâz ve muallel olmayan rivayet. Buhârî ve Müslim'in şartları "
                "klasik usûlde en yüksek kabul görmüştür; yine de her rakamın "
                "yorumu âlim ihtilafına açıktır."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "hasen",
            "collection": "din_05_hadis_kavram",
            "baslik": "hasen",
            "aliases": ["hasen hadis", "hasen nedir"],
            "metin": (
                "Hasen: sahihe yakın; râvi zabtı biraz daha zayıf kabul edilen "
                "ama isnadı muttasıl ve illetten uzak rivayet. Tirmizî'nin "
                "tasnifinde sık geçer."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "zaif",
            "collection": "din_05_hadis_kavram",
            "baslik": "zayıf",
            "aliases": ["zaif", "zayıf hadis", "daif"],
            "metin": (
                "Zayıf (ضعيف): sahih/hasen şartlarını taşımayan rivayet. "
                "Türleri çoktur (munkatı', mürsel, müdelles…). Rüzgar hüküm "
                "vermez; kaynağı ve metni gösterir."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "sahihayn",
            "collection": "din_05_hadis_kavram",
            "baslik": "sahihayn",
            "aliases": ["sahihayn", "sahîhayn", "iki sahih"],
            "metin": (
                "Sahîhayn: Sahîh-i Buhârî ve Sahîh-i Müslim. Ehl-i sünnet "
                "geleneğinde en sahih hadis mecmuaları kabul edilir."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "buhari_eser",
            "collection": "din_05_hadis_kavram",
            "baslik": "sahih-i buhari",
            "aliases": ["buhari nedir", "buhârî", "imam buhari", "sahih buhari"],
            "metin": (
                "Sahîh-i Buhârî (صحيح البخاري): İmam Buhârî'nin el-Câmiu's-sahîh'i. "
                "Kitâblara ayrılmış; Rüzgar'da `buhari` raftı. Örnek sorgu: "
                "«buhari 1» veya «buhârî hadis 1»."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "muslim_eser",
            "collection": "din_05_hadis_kavram",
            "baslik": "sahih-i muslim",
            "aliases": ["müslim", "muslim nedir", "sahih muslim", "imam muslim"],
            "metin": (
                "Sahîh-i Müslim: İmam Müslim'in el-Müsnedü's-sahîh'i. "
                "Bâblar konulara göre düzenlenir. Rüzgar raftı: `muslim`."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "ebu_davud_eser",
            "collection": "din_05_hadis_kavram",
            "baslik": "sunen ebu davud",
            "aliases": ["ebu davud", "ebû dâvûd", "sünen ebu davud"],
            "metin": (
                "Sünen-i Ebû Dâvûd: fıkhî ahkâma ağırlık veren sünen. "
                "Rüzgar raftı: `ebu_davud`."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "tirmizi_eser",
            "collection": "din_05_hadis_kavram",
            "baslik": "cami tirmizi",
            "aliases": ["tirmizi", "tirmizî", "câmiu tirmizi"],
            "metin": (
                "Câmiu't-Tirmizî: hadis + hüküm/iller ve bazen râvi notları. "
                "Rüzgar raftı: `tirmizi`."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "nesai_eser",
            "collection": "din_05_hadis_kavram",
            "baslik": "sunen nesai",
            "aliases": ["nesai", "nesâî", "sünen nesai"],
            "metin": (
                "Sünen-i Nesâî (el-Müctebâ): isnad titizliğiyle bilinen sünen. "
                "Rüzgar raftı: `nesai`."
            ),
            "kaynak_notu": _KAYNAK,
        },
        {
            "id": "ibn_mace_eser",
            "collection": "din_05_hadis_kavram",
            "baslik": "sunen ibn mace",
            "aliases": ["ibn mace", "ibn mâce", "ibn majah"],
            "metin": (
                "Sünen-i İbn Mâce: Kutüb-i Sitte'nin altıncı kitabı. "
                "Rüzgar raftı: `ibn_mace`."
            ),
            "kaynak_notu": _KAYNAK,
        },
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "kavramlar_hadis.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    INCR_ROOT.mkdir(parents=True, exist_ok=True)
    md_lines = ["# Hadis — temel kavramlar (TR)", ""]
    for row in rows:
        md_lines.append(f"## {row['baslik']}")
        md_lines.append("")
        md_lines.append(row["metin"])
        md_lines.append("")
        md_lines.append(f"_{row['kaynak_notu']}_")
        md_lines.append("")
    (INCR_ROOT / "hadis_kavramlar_tr.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )
    return len(rows)


def _ingest_work(eser_id: str, *, force: bool = False) -> dict[str, Any]:
    meta_w = WORKS[eser_id]
    edition = meta_w["edition"]
    dest = SITTE / eser_id
    incr = dest / "incremental"
    dest.mkdir(parents=True, exist_ok=True)
    incr.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    raw_path = RAW / f"{edition}.json"
    man_path = dest / "manifest.json"
    if man_path.is_file() and not force:
        old = json.loads(man_path.read_text(encoding="utf-8"))
        if old.get("hadis_sayisi", 0) > 100 and (dest / "hadisler.jsonl").is_file():
            print(f"  [skip] {eser_id} zaten dolu (force yok)")
            return old

    print(f"  [indir] {edition} …")
    data = _fetch(edition)
    digest = _sha256_bytes(data)
    raw_path.write_bytes(data)
    payload = json.loads(data.decode("utf-8"))
    book_meta = payload.get("metadata") or {}
    sections = book_meta.get("sections") or {}
    section_details = book_meta.get("section_details") or {}
    hadiths = payload.get("hadiths") or []

    (dest / "bolumler.json").write_text(
        json.dumps(
            {"sections": sections, "section_details": section_details},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Eski incremental temizle
    for old_md in incr.glob("*.md"):
        old_md.unlink()

    jsonl_path = dest / "hadisler.jsonl"
    kept = 0
    batch_i = 0
    batch_buf: list[str] = []

    def flush_batch() -> None:
        nonlocal batch_i, batch_buf
        if not batch_buf:
            return
        batch_i += 1
        name = f"{eser_id}_batch_{batch_i:04d}.md"
        header = (
            f"# {meta_w['eser_tr']} — paket {batch_i:04d}\n\n"
            f"Eser: {meta_w['eser_ar']} · {meta_w['yazar']}\n\n"
        )
        (incr / name).write_text(header + "\n".join(batch_buf) + "\n", encoding="utf-8")
        batch_buf = []

    with jsonl_path.open("w", encoding="utf-8") as jf:
        for h in hadiths:
            text = _clean_ar(h.get("text") or "")
            if not text:
                continue
            ref = h.get("reference") or {}
            book_no = ref.get("book")
            hadith_in_book = ref.get("hadith")
            hn = h.get("hadithnumber")
            an = h.get("arabicnumber")
            sec_name = ""
            if book_no is not None:
                sec_name = str(sections.get(str(book_no)) or sections.get(book_no) or "")
            grades = h.get("grades") or []
            row = {
                "collection": meta_w["collection"],
                "eser_id": eser_id,
                "eser_tr": meta_w["eser_tr"],
                "edition": edition,
                "hadithnumber": hn,
                "arabicnumber": an,
                "book": book_no,
                "hadith_in_book": hadith_in_book,
                "section": sec_name,
                "text_ar": text,
                "grades": grades,
            }
            jf.write(json.dumps(row, ensure_ascii=False) + "\n")
            kept += 1

            title = f"## {meta_w['eser_tr']} — no {hn}"
            if book_no is not None:
                title += f" (kitâb {book_no}"
                if sec_name:
                    title += f": {sec_name}"
                title += ")"
            block = [
                title,
                "",
                text,
                "",
                f"ref: {eser_id}#{hn} · book={book_no} · in_book={hadith_in_book}",
                "",
            ]
            batch_buf.append("\n".join(block))
            if len(batch_buf) >= BATCH_SIZE:
                flush_batch()
        flush_batch()

    manifest = {
        "eser_id": eser_id,
        "eser_tr": meta_w["eser_tr"],
        "eser_ar": meta_w["eser_ar"],
        "yazar": meta_w["yazar"],
        "edition": edition,
        "collection": meta_w["collection"],
        "aliases": meta_w["aliases"],
        "kaynak": "fawazahmed0/hadith-api@1",
        "kaynak_url": f"{CDN}/{edition}.json",
        "sha256": digest,
        "hadis_sayisi": kept,
        "bolum_sayisi": len([k for k, v in sections.items() if str(k) != "0" and v]),
        "incremental_batches": batch_i,
        "updated_utc": _utc(),
    }
    man_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  [ok] {eser_id}: {kept} hadis, {batch_i} md paket")
    return manifest


def _write_catalog(manifests: list[dict[str, Any]]) -> None:
    catalog = {
        "domain": "din_05_hadis",
        "kutub_i_sitte": ORDER,
        "kaynak": "fawazahmed0/hadith-api@1",
        "updated_utc": _utc(),
        "eserler": manifests,
    }
    (OUT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    readme = """# Din / 05 — Hadis kütüphanesi (Kutüb-i Sitte)

Her eser **ayrı raf**:

| ID | Eser | Klasör |
|----|------|--------|
| `buhari` | Sahîh-i Buhârî | `kutub_i_sitte/buhari/` |
| `muslim` | Sahîh-i Müslim | `kutub_i_sitte/muslim/` |
| `ebu_davud` | Sünen-i Ebû Dâvûd | `kutub_i_sitte/ebu_davud/` |
| `tirmizi` | Câmiu't-Tirmizî | `kutub_i_sitte/tirmizi/` |
| `nesai` | Sünen-i Nesâî | `kutub_i_sitte/nesai/` |
| `ibn_mace` | Sünen-i İbn Mâce | `kutub_i_sitte/ibn_mace/` |

| Katman | İçerik |
|--------|--------|
| **Kavramlar (TR)** | `kavramlar_hadis.jsonl` + `incremental/hadis_kavramlar_tr.md` |
| **Matın (AR)** | her rafta `hadisler.jsonl` + `incremental/*_batch_*.md` |
| **Bölümler** | `bolumler.json` (kitâb adları) |

**Kaynak:** fawazahmed0/hadith-api (Arapça). Anlık sorgu: `ruzgar_hadis_kutuphane`.

**Politika:** Fetva yok. Kaynak numaralı Arapça matın + usûl kavramı.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Kutüb-i Sitte ingest")
    ap.add_argument("--force", action="store_true", help="Mevcut raftarı yeniden indir")
    ap.add_argument(
        "--only",
        choices=ORDER,
        action="append",
        help="Yalnız seçilen eser(ler); birden fazla verilebilir",
    )
    args = ap.parse_args()
    only = args.only or ORDER

    print("=== Faz 5 Hadis — Kutüb-i Sitte ===")
    n_kav = _write_kavramlar()
    print(f"kavramlar: {n_kav}")

    manifests: list[dict[str, Any]] = []
    for eser_id in ORDER:
        if eser_id not in only:
            man_path = SITTE / eser_id / "manifest.json"
            if man_path.is_file():
                manifests.append(json.loads(man_path.read_text(encoding="utf-8")))
            continue
        print(f"\n>> {eser_id}")
        manifests.append(_ingest_work(eser_id, force=args.force))

    # katalog sırası ORDER'a göre
    by_id = {m["eser_id"]: m for m in manifests if m.get("eser_id")}
    ordered = [by_id[i] for i in ORDER if i in by_id]
    _write_catalog(ordered)
    total = sum(int(m.get("hadis_sayisi") or 0) for m in ordered)
    print(f"\nTOPLAM: {total} hadis · {len(ordered)} eser")
    print(f"çıkış: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
