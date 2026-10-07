# -*- coding: utf-8 -*-
"""Bilim rafı Faz 13 — 2 fazlı dolgu.

Faz 1: mevcut kutuphane rafları (astronomi/fizik-kimya/biyoloji/matematik) katalog + kavram.
Faz 2: bilimsel yöntem, İslâm bilim mirası, disiplin haritası katmanları.
Politika: Eğitim özeti; tıbbi teşhis/tedavi yok; sayfa uydurma yasak.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilim"
KAT = OUT / "katmanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_bilim.jsonl"
CATALOG = OUT / "catalog.json"
CATALOG_F2 = OUT / "catalog_faz2.json"
KUTUP = ROOT / "knowledge" / "kutuphane" / "raflar"

FAZ1_RAFLAR = [
    {
        "id": "01_astronomi_uzay",
        "ad": "Astronomi ve Uzay",
        "etiketler": ["astronomi", "uzay", "gezegen", "yildiz", "galaksi"],
    },
    {
        "id": "02_fizik_kimya",
        "ad": "Fizik ve Kimya",
        "etiketler": ["fizik", "kimya", "atom", "enerji", "elektrik"],
    },
    {
        "id": "03_biyoloji_dunya",
        "ad": "Biyoloji ve Canlılar",
        "etiketler": ["biyoloji", "hucre", "ekosistem", "fotosentez"],
    },
    {
        "id": "06_matematik",
        "ad": "Matematik",
        "etiketler": ["matematik", "geometri", "oran", "istatistik"],
    },
]

KAVRAMLAR = [
    {
        "id": "bilim",
        "baslik": "bilim",
        "aliases": ["bilim nedir", "fen", "fen bilimleri", "pozitif bilim"],
        "metin": (
            "Bilim: gözlem, ölçüm, hipotez ve sınamayla doğayı anlamaya çalışan yöntemli bilgi. "
            "Rüzgar bilim rafında astronomi, fizik–kimya, biyoloji ve matematik özetleri vardır. "
            "Tıbbi teşhis/tedavi vermez; eğitim amaçlıdır."
        ),
        "kaynak_notu": "Bilim rafı — Faz 1+2.",
    },
    {
        "id": "astronomi",
        "baslik": "astronomi",
        "aliases": ["astronomi", "gok bilimi", "gök bilimi", "uzay bilimi"],
        "metin": (
            "Astronomi: gök cisimleri ve evreni inceler. Bu rafta Güneş Sistemi, yıldızlar, "
            "galaksiler, Ay evreleri ve uzay araştırması özetleri vardır."
        ),
        "kaynak_notu": "Bilim — astronomi rafı.",
    },
    {
        "id": "gunes_sistemi",
        "baslik": "gunes sistemi",
        "aliases": ["gunes sistemi", "güneş sistemi", "gezegenler", "sekiz gezegen"],
        "metin": (
            "Güneş Sistemi: merkezde Güneş (sarı cüce); sekiz gezegen (Merkür…Neptün), "
            "cüce gezegenler, asteroid ve kuyruklu yıldızlar. Dünya sıvı su ve yaşam için "
            "özel koşullara sahiptir. Sayılar yuvarlak eğitim özetidir."
        ),
        "kaynak_notu": "Bilim — 01_astronomi.",
    },
    {
        "id": "galaksi",
        "baslik": "galaksi",
        "aliases": ["galaksi", "samanyolu", "samanyolu galaksisi"],
        "metin": (
            "Galaksi: yıldız, gaz, toz ve karanlık maddeden oluşan büyük sistem. "
            "Dünya, Samanyolu galaksisindedir."
        ),
        "kaynak_notu": "Bilim — astronomi.",
    },
    {
        "id": "fizik",
        "baslik": "fizik",
        "aliases": ["fizik", "fizik nedir"],
        "metin": (
            "Fizik: madde, enerji, hareket, kuvvet, ısı, elektrik ve manyetizma gibi "
            "doğa yasalarını inceler. Bu rafta temel özetler vardır."
        ),
        "kaynak_notu": "Bilim — fizik/kimya.",
    },
    {
        "id": "kimya",
        "baslik": "kimya",
        "aliases": ["kimya", "kimya nedir", "element", "periyodik tablo"],
        "metin": (
            "Kimya: maddenin yapısı, elementler, bileşikler ve tepkimeler. "
            "Atom ve periyodik tablo bu rafın temel konularındandır."
        ),
        "kaynak_notu": "Bilim — fizik/kimya.",
    },
    {
        "id": "atom",
        "baslik": "atom",
        "aliases": ["atom", "atom nedir", "proton elektron nortron"],
        "metin": (
            "Atom: maddenin kimyasal özelliklerini taşıyan temel birim; çekirdekte proton "
            "(ve genelde nötron), çevrede elektron. Elementler atom türleridir."
        ),
        "kaynak_notu": "Bilim — kimya özeti.",
    },
    {
        "id": "enerji",
        "baslik": "enerji",
        "aliases": ["enerji", "enerji nedir", "kinetik potansiyel"],
        "metin": (
            "Enerji: iş yapabilme kapasitesi; kinetik, potansiyel, ısı, elektrik vb. "
            "biçimlerde görülür. Korunum ilkesi eğitim özetinde anılır."
        ),
        "kaynak_notu": "Bilim — fizik.",
    },
    {
        "id": "biyoloji",
        "baslik": "biyoloji",
        "aliases": ["biyoloji", "biyoloji nedir", "canli bilimi"],
        "metin": (
            "Biyoloji: canlıları inceler — hücre, genetik temeller, ekosistem, bitki ve hayvan. "
            "Bu raf genel eğitim özetidir; tıbbi teşhis koymaz."
        ),
        "kaynak_notu": "Bilim — biyoloji; klinik değil.",
    },
    {
        "id": "hucre",
        "baslik": "hucre",
        "aliases": ["hucre", "hücre", "hucre nedir", "hücre nedir"],
        "metin": (
            "Hücre: yaşamın temel birimi. Bitki ve hayvan hücreleri organeller taşır; "
            "fotosentez bitki hücrelerinde gerçekleşir."
        ),
        "kaynak_notu": "Bilim — biyoloji.",
    },
    {
        "id": "fotosentez",
        "baslik": "fotosentez",
        "aliases": ["fotosentez", "fotosentez nedir"],
        "metin": (
            "Fotosentez: bitkilerin ışık enerjisiyle karbondioksit ve sudan besin "
            "(glikoz) ve oksijen üretmesi. Ekosistemin enerji girişidir."
        ),
        "kaynak_notu": "Bilim — biyoloji.",
    },
    {
        "id": "ekosistem",
        "baslik": "ekosistem",
        "aliases": ["ekosistem", "besin zinciri", "besin piramidi"],
        "metin": (
            "Ekosistem: canlılar ve cansız çevre etkileşimi. Besin zinciri üretici → "
            "tüketici → ayrıştırıcı akışını gösterir."
        ),
        "kaynak_notu": "Bilim — biyoloji.",
    },
    {
        "id": "matematik",
        "baslik": "matematik",
        "aliases": ["matematik", "matematik nedir", "hesap"],
        "metin": (
            "Matematik: sayı, oran, geometri, birim ve istatistik gibi nicel düşünme araçları. "
            "Bu rafta günlük matematik özetleri vardır."
        ),
        "kaynak_notu": "Bilim — matematik.",
    },
    {
        "id": "geometri",
        "baslik": "geometri",
        "aliases": ["geometri", "alan cevre", "üçgen daire"],
        "metin": (
            "Geometri: şekil, açı, alan ve hacim ilişkileri. Temel formüller eğitim "
            "özetinde yer alır."
        ),
        "kaynak_notu": "Bilim — matematik.",
    },
    # Faz 2 kavramlar
    {
        "id": "bilimsel_yontem",
        "baslik": "bilimsel yontem",
        "aliases": [
            "bilimsel yontem",
            "bilimsel yöntem",
            "hipotez",
            "deney",
            "gozlem",
            "gözlem",
        ],
        "metin": (
            "Bilimsel yöntem: soru → gözlem/veri → hipotez → sınama (deney/ölçüm) → "
            "sonuç ve yeniden değerlendirme. Tek bir «sihirli formül» değil; tekrarlanabilirlik "
            "ve yanlışlanabilirlik önemlidir."
        ),
        "kaynak_notu": "Bilim Faz 2 — yöntem.",
    },
    {
        "id": "islam_bilim_mirasi",
        "baslik": "islam bilim mirasi",
        "aliases": [
            "islam bilim mirasi",
            "islâm bilim mirası",
            "islam bilimi",
            "beytul hikmet",
            "beytü'l-hikme",
            "golden age science",
        ],
        "metin": (
            "İslâm bilim mirası: klasik dönemde astronomi, tıp, matematik, optik ve kimya "
            "alanlarında birikim (ör. Hârizmî, İbn Sînâ, İbnü'l-Heysem çizgisi). "
            "Bu katman kavram/özettir; fetva değildir."
        ),
        "kaynak_notu": "Bilim Faz 2 — tarih/miras.",
    },
    {
        "id": "harizmi",
        "baslik": "harizmi",
        "aliases": ["harizmi", "hârizmî", "al khwarizmi", "cebir"],
        "metin": (
            "Hârizmî: klasik matematik ve cebir geleneğinin önemli isimlerinden; "
            "algoritma sözcüğünün kökeniyle anılır. Kavram/özet; eser sayfası uydurulmaz."
        ),
        "kaynak_notu": "Bilim Faz 2 — miras.",
    },
    {
        "id": "ibn_heysem",
        "baslik": "ibn heysem",
        "aliases": ["ibn heysem", "ibnul heysem", "ibn al haytham", "optik"],
        "metin": (
            "İbnü'l-Heysem: optik ve deneysel yönteme katkılarıyla anılır (Kitâbü'l-Menâzır "
            "çerçevesi). Kavram/özet; fetva değildir."
        ),
        "kaynak_notu": "Bilim Faz 2 — miras.",
    },
    {
        "id": "disiplinler",
        "baslik": "fen disiplinleri",
        "aliases": [
            "fen disiplinleri",
            "bilim dallari",
            "bilim dalları",
            "hangi bilim",
        ],
        "metin": (
            "Bu raftaki ana disiplinler: astronomi/uzay, fizik, kimya, biyoloji, matematik. "
            "Coğrafya ayrı ortak alandır; teknoloji ayrı raftadır."
        ),
        "kaynak_notu": "Bilim Faz 2 — harita.",
    },
]

KATMANLAR = {
    "bilimsel_yontem": {
        "baslik": "Bilimsel yöntem",
        "kaynak_id": "bilim_katman_yontem",
        "parcalar": [
            (
                "Döngü",
                "Soru sor → gözlem/ölç → hipotez kur → sınanabilir öngörü üret → dene/ölç → "
                "sonucu paylaş ve gerekirse revize et. Bilim kesin dogma değil, düzeltilen bilgidir.",
            ),
            (
                "Ölçüm ve birim",
                "Karşılaştırılabilir sonuç için birim ve hata payı önemlidir. "
                "Günlük hayatta da ölçü birimleri (metre, kilogram, saniye) bu disiplinin parçasıdır.",
            ),
            (
                "Sınır",
                "Rüzgar eğitim özeti verir; laboratuvar protokolü veya tehlikeli deney yönergesi "
                "vermez. Tıbbi teşhis koymaz.",
            ),
        ],
    },
    "islam_bilim_mirasi": {
        "baslik": "İslâm bilim mirası (kavram)",
        "kaynak_id": "bilim_katman_islam_miras",
        "parcalar": [
            (
                "Çerçeve",
                "Klasik İslâm medeniyetinde çeviri hareketi, gözlemevleri, tıp ve matematik "
                "okulları birikim oluşturmuştur. Bu katman özet/kavramdır; fetva değildir.",
            ),
            (
                "Örnek isimler",
                "Hârizmî (matematik/cebir), İbn Sînâ (tıp/felsefe köprüsü — klinik teşhis değil), "
                "İbnü'l-Heysem (optik), Bîrûnî (ölçüm/coğrafya-astronomi ilgisi). "
                "Sayfa/cilt uydurulmaz.",
            ),
            (
                "Modern bilimle ilişki",
                "Tarihî birikim modern disiplinin yerine geçmez; köprü ve bağlam sağlar. "
                "Güncel ölçümler için güncel kaynaklar esastır.",
            ),
        ],
    },
    "disiplinler": {
        "baslik": "Disiplin haritası",
        "kaynak_id": "bilim_katman_disiplin",
        "parcalar": [
            (
                "Raflar",
                "01 Astronomi/uzay · 02 Fizik–kimya · 03 Biyoloji · 06 Matematik. "
                "İçerik: knowledge/kutuphane/raflar/ altındaki md özetler.",
            ),
            (
                "Komşu alanlar",
                "Coğrafya ayrı alandır. Teknoloji/bilgisayar ayrı raftır. "
                "Psikoloji klasik nefs rafı klinik değildir.",
            ),
        ],
    },
}

# Faz 1 derinleştirme — ek kısa md (mevcut raflara)
EXTRA_MD = {
    "01_astronomi_uzay": [
        (
            "007_karadelik_ve_evren_olcek.md",
            "# Kara delik ve evren ölçeği — Rüzgar Kütüphanesi\n\n"
            "Kaynak notu: Eğitim özeti. Sayılar mertebe düzeyindedir.\n\n"
            "## Kara delik nedir\n"
            "Kara delik, kütleçekimi o kadar güçlü bir bölgedir ki ışık bile kaçamayacak "
            "kadar uzayı büker. Gözlemler dolaylıdır (yörünge, kütleçekim merceklenmesi, "
            "olay ufku gölgesi).\n\n"
            "## Evren ölçeği\n"
            "Güneş Sistemi ≪ Samanyolu ≪ gökada kümeleri ≪ gözlenebilir evren. "
            "Işık yılı: ışığın bir yılda aldığı yol (~9,46×10¹² km).\n",
        )
    ],
    "02_fizik_kimya": [
        (
            "006_basit_newton_kuvvet.md",
            "# Newton ve kuvvet — Rüzgar Kütüphanesi\n\n"
            "Kaynak notu: Lise düzeyinde özet; mühendislik hesabı değildir.\n\n"
            "## Kuvvet ve hareket\n"
            "Kuvvet, cismin hareket durumunu değiştirmeye çalışan etkidir. "
            "Newton’un hareket yasaları: eylemsizlik, F=ma çerçevesi, etki–tepki.\n\n"
            "## Sürtünme\n"
            "Sürtünme hareketi zorlaştırır; yürüyüş ve fren için de gereklidir.\n",
        )
    ],
    "03_biyoloji_dunya": [
        (
            "006_dna_genetik_kisa.md",
            "# DNA ve genetik (kısa) — Rüzgar Kütüphanesi\n\n"
            "Kaynak notu: Genel eğitim. Tıbbi teşhis/genetik danışmanlık değildir.\n\n"
            "## DNA\n"
            "DNA, canlılarda kalıtsal bilginin taşındığı moleküldür. Genler bu bilginin "
            "işlevsel birimleridir.\n\n"
            "## Kalıtım\n"
            "Özellikler ebeveynden yavruya genlerle aktarılır; çevre de gelişimi etkiler.\n",
        )
    ],
    "06_matematik": [
        (
            "006_yuzde_faiz_kisa.md",
            "# Yüzde ve basit faiz — Rüzgar Kütüphanesi\n\n"
            "Kaynak notu: Günlük hesap özeti; mali tavsiye değildir.\n\n"
            "## Yüzde\n"
            "a’nın %p’si = a × (p/100). Örnek: 200’ün %15’i = 30.\n\n"
            "## Basit faiz fikri\n"
            "Basit faiz = anapara × oran × süre (birimler uyumlu olmalı). "
            "Bileşik faiz ayrıdır.\n",
        )
    ],
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_extra_md() -> int:
    n = 0
    for raf_id, files in EXTRA_MD.items():
        dest = KUTUP / raf_id / "incremental"
        dest.mkdir(parents=True, exist_ok=True)
        for name, body in files:
            path = dest / name
            if not path.is_file():
                path.write_text(body, encoding="utf-8")
                n += 1
                print(f"  [+] {raf_id}/{name}")
            else:
                print(f"  [=] {raf_id}/{name}")
    return n


def _scan_raf(raf_id: str) -> dict:
    d = KUTUP / raf_id
    files = sorted(d.rglob("*.md")) if d.is_dir() else []
    chars = 0
    for p in files:
        try:
            chars += len(p.read_text(encoding="utf-8"))
        except OSError:
            pass
    return {
        "raf_id": raf_id,
        "dosya": len(files),
        "karakter": chars,
        "dosya_yolu": f"knowledge/kutuphane/raflar/{raf_id}",
    }


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
        "Kaynak: Rüzgar bilim Faz 2. Eğitim özeti. Tıbbi teşhis yok. Fetva yok.",
        "",
    ]
    for i, (title, text) in enumerate(spec["parcalar"], 1):
        body += [f"## {i}. {title}", "", text, ""]
    (incr / f"{key}_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": key,
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "bilim",
        "faz": 2,
        "dil": "tr",
        "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/bilim/katmanlar/{key}",
        "guvenilirlik": "orta",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "parca_sayisi": len(spec["parcalar"]),
        "batch_sayisi": 1,
        "updated_utc": _utc(),
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return man


def _update_ortak(entry: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
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
    OUT.mkdir(parents=True, exist_ok=True)
    KAT.mkdir(parents=True, exist_ok=True)

    print("=== Faz 1 ekstra md ===")
    added = _write_extra_md()

    print("=== Faz 1 katalog ===")
    eserler = []
    for raf in FAZ1_RAFLAR:
        sc = _scan_raf(raf["id"])
        row = {
            **raf,
            **sc,
            "faz": 1,
            "ilim_alani": "bilim",
            "durum": "hazir",
            "updated_utc": _utc(),
        }
        eserler.append(row)
        _update_ortak(
            {
                "kaynak_id": f"bilim_raf_{raf['id']}",
                "kaynak_adi": raf["ad"],
                "yazar": None,
                "ilim_alani": "bilim",
                "eser_turu": "raf",
                "dil": "tr",
                "yayin": None,
                "cilt": None,
                "bolum": None,
                "sayfa": None,
                "dosya_yolu": sc["dosya_yolu"],
                "guvenilirlik": "orta",
                "kaynak_sinifi": "kalici",
                "durum": "hazir",
                "not": "Kutuphane bilim rafı; eğitim özeti.",
            }
        )
        print(f"  [ok] {raf['id']} dosya={sc['dosya']} char={sc['karakter']}")

    print("=== Faz 2 katman ===")
    faz2 = []
    for key, spec in KATMANLAR.items():
        man = _write_katman(key, spec)
        faz2.append(man)
        _update_ortak(
            {
                "kaynak_id": man["kaynak_id"],
                "kaynak_adi": man["baslik"],
                "yazar": None,
                "ilim_alani": "bilim",
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
                "not": "Bilim Faz 2 katman.",
            }
        )
        print(f"  [ok] {key}")

    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in KAVRAMLAR) + "\n",
        encoding="utf-8",
    )

    cat = {
        "domain": "bilim",
        "faz": {"1": "kutuphane_raflar", "2": "yontem_miras_disiplin"},
        "updated_utc": _utc(),
        "politika": (
            "2 fazlı. Eğitim özeti. Tıbbi teşhis/tedavi yok. Fetva yok. "
            "Sayfa/cilt uydurma yasak."
        ),
        "faz1_raflar": eserler,
        "faz2_katmanlar": faz2,
        "sayilar": {
            "raf": len(eserler),
            "md_dosya": sum(int(e["dosya"]) for e in eserler),
            "faz2_katman": len(faz2),
            "kavram": len(KAVRAMLAR),
            "ek_md_yeni": added,
        },
    }
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_F2.write_text(
        json.dumps(
            {
                "domain": "bilim_faz2",
                "updated_utc": _utc(),
                "katmanlar": faz2,
                "kavram_faz2_ids": [
                    "bilimsel_yontem",
                    "islam_bilim_mirasi",
                    "harizmi",
                    "ibn_heysem",
                    "disiplinler",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (OUT / "README.md").write_text(
        "# Bilim — 2 fazlı raf\n\n"
        "## Faz 1\n"
        "Kutuphane: `01_astronomi_uzay` · `02_fizik_kimya` · `03_biyoloji_dunya` · `06_matematik`\n\n"
        "## Faz 2\n"
        "`katmanlar/bilimsel_yontem` · `islam_bilim_mirasi` · `disiplinler`\n\n"
        f"MD dosya: **{cat['sayilar']['md_dosya']}** · Kavram: **{len(KAVRAMLAR)}**\n\n"
        "**Politika:** Eğitim · tıbbi teşhis yok · fetva yok\n"
        "**Script:** `faz13_bilim_raf_ingest.py` · **Anlık:** `ruzgar_bilim_kutuphane.py`\n",
        encoding="utf-8",
    )
    print(
        f"\nTOPLAM bilim raf={len(eserler)} md={cat['sayilar']['md_dosya']} "
        f"katman={len(faz2)} kavram={len(KAVRAMLAR)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
