# -*- coding: utf-8 -*-
"""Felsefe Faz 2 — mektep/kavram/dönem katmanları.

Faz 1 OpenITI eserleri korunur. Fetva yok. Sayfa uydurma yasak.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "felsefe"
KAT = OUT / "katmanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_felsefe.jsonl"
CATALOG = OUT / "catalog.json"
CATALOG_F2 = OUT / "catalog_faz2.json"

# Faz 1 eser kavramları (koru)
FAZ1 = [
    {
        "id": "felsefe",
        "baslik": "felsefe",
        "aliases": [
            "felsefe nedir",
            "islam felsefesi",
            "islâm felsefesi",
            "hikmet",
            "felsefe tarihi",
        ],
        "metin": (
            "İslâm felsefesi: Meşşâî (Fârâbî, İbn Sînâ), eleştirel çizgi (Gazâlî Tehâfüt) "
            "ve makâsıd/hikmet tartışmaları. Rüzgar’da OpenITI klasik metinler (Faz 1) ve "
            "mektep–kavram katmanı (Faz 2) vardır. Fetva değildir."
        ),
        "kaynak_notu": "Felsefe — Faz 1+2.",
    },
    {
        "id": "farabi_ara_ahl_madina",
        "baslik": "farabi",
        "aliases": ["farabi", "fârâbî", "medinei fazila", "medine-i fazıla", "ara ahl madina"],
        "metin": (
            "Fârâbî: Meşşâî siyaset ve erdemli şehir (Medîne-i Fâzıla) çerçevesi. "
            "OpenITI metni raftadır. Fetva değildir."
        ),
        "kaynak_notu": "Felsefe Faz 1 — OpenITI.",
    },
    {
        "id": "ibn_sina_isharat",
        "baslik": "ibn sina",
        "aliases": ["ibn sina", "ibni sina", "avicenna", "işarat", "isharat", "işârât"],
        "metin": (
            "İbn Sînâ: İşârât ve’t-Tenbîhât vb. Meşşâî metafizik–mantık çizgisi. "
            "OpenITI metni raftadır."
        ),
        "kaynak_notu": "Felsefe Faz 1 — OpenITI.",
    },
    {
        "id": "gazali_tahafut",
        "baslik": "tahafut",
        "aliases": ["tahafut", "tehafut", "tehâfüt", "gazali tehafut"],
        "metin": (
            "Gazâlî Tehâfütü’l-felâsife: filozoflara eleştirel cevap. Fetva kitabı değildir; "
            "felsefî-kelâmî tartışma metnidir."
        ),
        "kaynak_notu": "Felsefe Faz 1 — OpenITI.",
    },
    {
        "id": "gazali_maqasid",
        "baslik": "maqasid",
        "aliases": ["maqasid", "makasid", "makâsıd", "makasidul felasife"],
        "metin": "Gazâlî Makâsıdü’l-felâsife: filozofların maksatlarını özetleme çerçevesi.",
        "kaynak_notu": "Felsefe Faz 1 — OpenITI.",
    },
    {
        "id": "farabi_siyasa",
        "baslik": "siyasa farabi",
        "aliases": ["siyasa farabi", "siyaseti medeniye", "siyâsetü'l-medeniyye"],
        "metin": "Fârâbî siyasetü’l-medeniyye: medenî siyaset ve erdemli yönetim kavramları.",
        "kaynak_notu": "Felsefe Faz 1 — OpenITI.",
    },
    {
        "id": "ibn_sina_najat",
        "baslik": "necat",
        "aliases": ["necat", "najat", "necât", "kitabun necat"],
        "metin": "İbn Sînâ Necât: mantık–tabîiyyât–ilâhiyyât özet külliyatı çerçevesi.",
        "kaynak_notu": "Felsefe Faz 1 — OpenITI.",
    },
    {
        "id": "ibn_sina_shifa_ilahiyyat",
        "baslik": "sifa ilahiyyat",
        "aliases": ["sifa ilahiyyat", "şifâ ilâhiyyât", "shifa ilahiyyat", "ilahiyyat"],
        "metin": "İbn Sînâ Şifâ — İlâhiyyât: metafizik bölüm. OpenITI metni raftadır.",
        "kaynak_notu": "Felsefe Faz 1 — OpenITI.",
    },
]

FAZ2 = [
    {
        "id": "messai",
        "baslik": "messai",
        "aliases": ["messai", "meşşai", "meşşâî", "peripatetik", "aristo culugu"],
        "metin": (
            "Meşşâîlik: Aristotelesçi çizginin İslâm dünyasındaki devamı. "
            "Mantık, fizik, metafizik sistematiği; Fârâbî ve İbn Sînâ tipik temsilcilerdir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — mektep.",
    },
    {
        "id": "israk",
        "baslik": "israk",
        "aliases": ["israk", "işrak", "işrâk", "suhreverdi", "işrakilik"],
        "metin": (
            "İşrâk: aydınlanma/işrak vurgulu felsefî çizgi (Sühreverdî çerçevesi). "
            "Bu rafta ayrı OpenITI yükü yoksa kavram olarak tutulur; fetva değildir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — mektep.",
    },
    {
        "id": "kelam_felsefe",
        "baslik": "kelam ve felsefe",
        "aliases": ["kelam", "kelâm", "kelam felsefe", "mutezile", "esari"],
        "metin": (
            "Kelâm ile felsefe: aklî delil ve itikadî konuların kesişim–gerilim alanı. "
            "Gazâlî Tehâfüt bu gerilimin klasik örneğidir. Akaid fetvası değildir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — ilişki.",
    },
    {
        "id": "metafizik",
        "baslik": "metafizik",
        "aliases": ["metafizik", "ilahiyyat", "ilâhiyyât", "vucud", "vücud", "mahiyet"],
        "metin": (
            "Metafizik/ilâhiyyât: varlık (vücûd), mahiyet, zorunlu varlık tartışmaları. "
            "İbn Sînâ Şifâ İlâhiyyât bu alanın ana metinlerindendir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — kavram.",
    },
    {
        "id": "mantik",
        "baslik": "mantik",
        "aliases": ["mantik", "mantık", "kıyas", "organon"],
        "metin": (
            "Mantık: doğru düşünmenin araçları; Meşşâî gelenekte Organon çizgisi. "
            "Necât ve İşârât’ta mantık bölümleri anılır."
        ),
        "kaynak_notu": "Felsefe Faz 2 — kavram.",
    },
    {
        "id": "siyaset_felsefesi",
        "baslik": "siyaset felsefesi",
        "aliases": [
            "siyaset felsefesi",
            "erdemli sehir",
            "erdemli şehir",
            "medinei fazila",
            "siyaseti medeniye",
        ],
        "metin": (
            "Siyaset felsefesi: erdem, adalet ve medenî düzen. Fârâbî Medîne-i Fâzıla ve "
            "Siyâsetü’l-medeniyye bu çerçevenin klasikleridir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — kavram.",
    },
    {
        "id": "ahlak_felsefesi",
        "baslik": "ahlak felsefesi",
        "aliases": ["ahlak felsefesi", "etik", "fazilet", "erdem etiği"],
        "metin": (
            "Ahlâk felsefesi: erdem, mutluluk (saâdet) ve nefs terbiyesi. "
            "Felsefe rafı ile psikoloji/nefs ve tasavvuf ahlâkı komşu alanlardır."
        ),
        "kaynak_notu": "Felsefe Faz 2 — kavram.",
    },
    {
        "id": "nedensellik",
        "baslik": "nedensellik",
        "aliases": ["nedensellik", "illet", "sebebiyet", "illiyet"],
        "metin": (
            "Nedensellik/illet: varlıkta sebep–sonuç bağı. Meşşâîlerde zorunlu bağ; "
            "Gazâlî eleştirisinde âdetullah tartışması anılır (özet). Fetva değildir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — kavram.",
    },
    {
        "id": "aristo_platon_kopru",
        "baslik": "aristo platon",
        "aliases": [
            "aristo",
            "aristoteles",
            "platon",
            "eflatun",
            "yunan felsefesi",
        ],
        "metin": (
            "Antik köprü: Platon (idealar/siyaset) ve Aristoteles (mantık/metafizik) "
            "İslâm felsefesine çeviri ve şerh yoluyla girmiştir. Bu katman kavramdır; "
            "tam Yunanca corpus yükü değildir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — köprü.",
    },
    {
        "id": "donem_islam_felsefe",
        "baslik": "islam felsefe donemi",
        "aliases": [
            "islam felsefe tarihi",
            "islâm felsefe tarihi",
            "çeviri hareketi",
            "ceviri hareketi",
            "beytul hikmet felsefe",
        ],
        "metin": (
            "Dönem çerçevesi: çeviri hareketi → sistematik Meşşâîler → Gazâlî eleştirisi → "
            "sonraki sentez/yeniden yorumlar. Kronoloji eğitim özetidir."
        ),
        "kaynak_notu": "Felsefe Faz 2 — dönem.",
    },
]

KATMANLAR = {
    "mektepler": {
        "baslik": "Felsefe mektepleri",
        "kaynak_id": "felsefe_katman_mektepler",
        "parcalar": [
            (
                "Meşşâî",
                "Aristotelesçi sistematik: mantık → tabîiyyât → ilâhiyyât. "
                "Fârâbî, İbn Sînâ bu çizginin büyük temsilcileridir.",
            ),
            (
                "Eleştirel kelâmî hat",
                "Gazâlî Tehâfüt: filozofların bazı iddialarına itiraz. "
                "Felsefeyi toptan yok sayma değil; sınır çizme tartışmasıdır (özet).",
            ),
            (
                "İşrâk (kavram)",
                "Aydınlanma vurgulu çizgi; bu turda ayrı tam metin yoksa kavram olarak durur.",
            ),
        ],
    },
    "kavramlar": {
        "baslik": "Temel felsefe kavramları",
        "kaynak_id": "felsefe_katman_kavramlar",
        "parcalar": [
            (
                "Varlık ve mahiyet",
                "Vücûd–mahiyet ayrımı İbn Sînâ metafiziğinde merkezîdir. "
                "Zorunlu varlık tartışması ilâhiyyâtın omurgasıdır.",
            ),
            (
                "Mantık ve siyaset",
                "Doğru düşünme (mantık) ile erdemli şehir (siyaset) Meşşâîlerde "
                "birlikte anılır; Fârâbî buna örnektir.",
            ),
            (
                "Nedensellik",
                "İllet bağı ve âdet tartışması Tehâfüt bağlamında özetlenir. Fetva değildir.",
            ),
        ],
    },
    "donem_kopru": {
        "baslik": "Dönem ve antik köprü",
        "kaynak_id": "felsefe_katman_donem",
        "parcalar": [
            (
                "Çeviri ve şerh",
                "Yunanca eserlerin Arapçaya aktarımı İslâm felsefesinin zeminidir. "
                "Platon–Aristoteles köprüsü kavramsal tutulur.",
            ),
            (
                "Raf içeriği",
                "Faz 1: OpenITI klasik metinler. Faz 2: mektep/kavram/dönem. "
                "Sayfa/cilt uydurulmaz.",
            ),
        ],
    },
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_katman(key: str, spec: dict) -> dict:
    dest = KAT / key
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        f"# {spec['baslik']}",
        "",
        "Kaynak: Rüzgar felsefe Faz 2. Fetva yok. Sayfa uydurma yasak.",
        "",
    ]
    for i, (t, x) in enumerate(spec["parcalar"], 1):
        body += [f"## {i}. {t}", "", x, ""]
    (incr / f"{key}_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": key,
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "felsefe",
        "faz": 2,
        "dil": "tr",
        "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/felsefe/katmanlar/{key}",
        "parca_sayisi": len(spec["parcalar"]),
        "updated_utc": _utc(),
        "durum": "hazir",
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return man


def _update_ortak(man: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    entry = {
        "kaynak_id": man["kaynak_id"],
        "kaynak_adi": man["baslik"],
        "yazar": None,
        "ilim_alani": "felsefe",
        "eser_turu": "katman",
        "dil": "tr",
        "yayin": None,
        "cilt": None,
        "bolum": None,
        "sayfa": None,
        "dosya_yolu": man["dosya_yolu"],
        "guvenilirlik": "orta",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "not": "Felsefe Faz 2 katman.",
    }
    found = False
    for r in rows:
        if r.get("kaynak_id") == entry["kaynak_id"]:
            r.update(entry)
            found = True
            break
    if not found:
        rows.append(entry)
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    KAT.mkdir(parents=True, exist_ok=True)
    faz2_rows = []
    for key, spec in KATMANLAR.items():
        print(f">> {key}")
        man = _write_katman(key, spec)
        _update_ortak(man)
        faz2_rows.append(man)

    all_kav = FAZ1 + FAZ2
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in all_kav) + "\n",
        encoding="utf-8",
    )

    cat = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.is_file() else {
        "domain": "felsefe_islam",
        "eserler": [],
    }
    cat["faz"] = {"1": "openiti", "2": "mektep_kavram_donem"}
    cat["faz2_katmanlar"] = faz2_rows
    cat["updated_utc"] = _utc()
    cat["politika"] = (
        "2 fazlı. Faz1 OpenITI. Faz2 mektep/kavram. Fetva yok. Sayfa uydurma yasak."
    )
    cat.setdefault("sayilar", {})
    cat["sayilar"]["faz2_katman"] = len(faz2_rows)
    cat["sayilar"]["kavram"] = len(all_kav)
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_F2.write_text(
        json.dumps(
            {
                "domain": "felsefe_faz2",
                "updated_utc": _utc(),
                "katmanlar": faz2_rows,
                "kavram_faz2": len(FAZ2),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else "# Felsefe\n"
    if "Faz 2" not in prev:
        prev = prev.rstrip() + (
            "\n\n## Faz 2\n"
            "- `katmanlar/mektepler` · `kavramlar` · `donem_kopru`\n"
            f"- Kavram toplam: **{len(all_kav)}**\n"
            "- Script: `faz10b_felsefe_faz2_ingest.py`\n"
        )
        readme.write_text(prev + "\n", encoding="utf-8")

    print(f"\nTOPLAM felsefe faz2={len(faz2_rows)} kavram={len(all_kav)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
