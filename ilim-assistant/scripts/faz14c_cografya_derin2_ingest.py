# -*- coding: utf-8 -*-
"""Coğrafya derinleştirme 2 (Faz 14c) — ekonomi/iklim/geçiş/yerleşme.

14b üzerine ~12 md + yeni kavram. Uydurma nüfus/istatistik yok.
Fetva/propaganda yok.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "cografya"
RAF_INC = ROOT / "knowledge" / "kutuphane" / "raflar" / "04_cografya" / "incremental"
KAT = OUT / "katmanlar" / "derin2"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_cografya.jsonl"
CATALOG = OUT / "catalog.json"

DEEP_MD: dict[str, str] = {
    "021_bolge_karadeniz_ekonomi.md": """# Karadeniz — ekonomi ve yerleşme (derin2)

Kaynak notu: Okul coğrafyası. Güncel resmi istatistik iddiası yok.

## Tarım ve kıyı
Çay, fındık ve kıyı balıkçılığı bölgeyle anılır. Dağların denize paralel uzanması kıyı şeridini dar tutar.

## Yerleşme
Kıyı boyunca dizilen yerleşmeler; doğuda eğim ve heyelan riski eğitimde vurgulanır. Trabzon, Samsun, Rize, Ordu merkezleri anılır.
""",
    "022_bolge_marmara_sanayi.md": """# Marmara — sanayi ve geçiş (derin2)

Kaynak notu: Eğitim. Propaganda yok.

## Yoğunluk
Nüfus ve sanayi–ticaret yoğunluğu yüksektir. İstanbul boğazı uluslararası geçiş alanıdır.

## Çevre
Sanayi, liman ve ulaşım ağı bölgeyi ülkenin ekonomik omurgalarından biri yapar (kavram). Bursa, Kocaeli, Tekirdağ anılır.
""",
    "023_bogazlar_gecis.md": """# Boğazlar ve geçiş coğrafyası

Kaynak notu: Fiziki–siyasi coğrafya çerçevesi. Hukuk/fetva değildir.

## İstanbul ve Çanakkale
Karadeniz–Marmara–Ege bağlantısı. Stratejik geçiş ve ticaret yolları bağlamında anılır.

## Önemi
İki kıta arasında köprü rolü; deniz trafiği ve güvenlik tartışmaları ayrı uzmanlık alanıdır.
""",
    "024_komsu_ulkeler_cerceve.md": """# Türkiye komşu ülkeler — çerçeve

Kaynak notu: Genel coğrafya. Güncel siyaset yorumu değildir.

## Kara komşular (okul listesi)
Yunanistan, Bulgaristan, Gürcistan, Ermenistan, İran, Irak, Suriye (eğitim çerçevesi).

## Deniz komşuluğu
Karadeniz, Ege, Akdeniz üzerinden deniz komşuları vardır. Sınır anlaşmazlığı yorumu bu pakette yoktur.
""",
    "025_akarsular_havza.md": """# Akarsular ve havza fikri

Kaynak notu: Fiziki coğrafya.

## Havza
Bir akarsuyun sularını toplayan alan. Fırat, Dicle, Kızılırmak, Sakarya, Yeşilırmak okulda anılır.

## Kullanım
Sulama, enerji (baraj), içme suyu bağlamları kavramdır; proje mühendisliği değildir.
""",
    "026_nufus_yerlesme_cerceve.md": """# Nüfus ve yerleşme — çerçeve

Kaynak notu: Beşeri coğrafya. Resmi TÜİK rakamı uydurulmaz.

## Yoğunluk farkı
Batı ve kıyı bölgelerde yoğunluk genelde daha yüksek; iç ve doğuda daha seyrek yerleşim örüntüleri eğitimde anlatılır.

## Kent–kır
Kentleşme, göç ve sanayi–hizmet istihdamı yerleşme biçimini etkiler (kavram).
""",
    "027_iklim_turkiye_ozet.md": """# Türkiye iklimleri — özet (derin2)

Kaynak notu: Okul iklim bilgisi.

## Tipler
Karadeniz (yağışlı kıyı), Akdeniz (yaz kurak), karasal (iç–doğu kış soğuk), Marmara geçiş iklimi.

## Etkenler
Enlem, yükselti, denize uzaklık, bakı ve dağların uzanış yönü yağış ve sıcaklığı biçimlendirir.
""",
    "028_ege_akdeniz_turizm.md": """# Ege ve Akdeniz — turizm–tarım bağı

Kaynak notu: Beşeri–ekonomik coğrafya özeti.

## Ege
Zeytin, üzüm, turizm; dağların denize dik uzanmasıyla oluşan ovalar.

## Akdeniz
Sera tarımı, turizm, Toroslar’ın kıyıya paralelliği. Antalya–Adana–Mersin hattı anılır.
""",
    "029_anadolu_dag_kusaklari.md": """# Anadolu dağ kuşakları

Kaynak notu: Fiziki coğrafya.

## Kuzey ve güney
Kuzeyde Karadeniz dağları, güneyde Toroslar; içte platolar. Doğu Anadolu’da yükselti artar.

## Etki
Yağış dağılışı, ulaşım geçitleri ve yerleşme bu kuşaklarla ilişkilidir.
""",
    "030_harita_projeksiyon_kisa.md": """# Harita ve projeksiyon — kısa

Kaynak notu: Kartografya temeli.

## Ölçek
Büyük ölçek ayrıntılı, küçük ölçek genel gösterir.

## Projeksiyon
Küre düzleme aktarılırken şekil/alan/mesafe bozulmaları olabilir; amaç doğru projeksiyon seçmektir (kavram).
""",
    "031_beseri_cografya_kisa.md": """# Beşeri coğrafya — kısa

Kaynak notu: Eğitim.

## Konu
Nüfus, yerleşme, tarım, sanayi, turizm, ulaşım — insan–mekân ilişkisi.

## Fiziki bağ
İklim ve yerşekli beşeri faaliyetleri kısıtlar veya kolaylaştırır; tamamen belirlemez (kavram).
""",
    "032_dogal_afet_cerceve.md": """# Doğal afet coğrafyası — çerçeve

Kaynak notu: Bilinçlendirme eğitimi. Acil durum talimatı / resmi uyarı değildir.

## Türler
Deprem, heyelan, sel, orman yangını, çığ — Türkiye’de farklı bölgelerde riskler anılır.

## Sınır
Tahliye planı, bina mühendisliği ve canlı uyarı bu paketin konusu değildir; yetkili kurumlara başvurulur.
""",
}

KAVRAMLAR_YENI = [
    {
        "id": "karadeniz_ekonomi",
        "baslik": "karadeniz ekonomi",
        "aliases": ["karadeniz tarim", "karadeniz cay", "karadeniz findik", "trabzon cografya"],
        "metin": (
            "Karadeniz’de çay–fındık ve kıyı yerleşmesi öne çıkar; dağlar kıyı şeridini dar tutar. "
            "Doğuda eğim ve heyelan riski eğitimde vurgulanır."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "marmara_sanayi",
        "baslik": "marmara sanayi",
        "aliases": ["marmara sanayi", "istanbul sanayi", "kocaeli sanayi", "marmara ekonomi"],
        "metin": (
            "Marmara: yoğun nüfus, sanayi–ticaret ve liman ağı. İstanbul boğazı geçiş "
            "coğrafyasının merkezidir."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "bogazlar",
        "baslik": "bogazlar",
        "aliases": [
            "bogazlar",
            "boğazlar",
            "istanbul bogazi",
            "istanbul boğazı",
            "canakkale bogazi",
            "çanakkale boğazı",
        ],
        "metin": (
            "İstanbul ve Çanakkale boğazları Karadeniz’i Ege’ye bağlar. "
            "Stratejik geçiş ve ticaret bağlamında anılır; hukuk yorumu değildir."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "komsu_ulkeler",
        "baslik": "komsu ulkeler",
        "aliases": ["komsu ulkeler", "komşu ülkeler", "turkiye komsulari", "türkiye komşuları"],
        "metin": (
            "Kara komşular okul listesinde: Yunanistan, Bulgaristan, Gürcistan, Ermenistan, "
            "İran, Irak, Suriye. Deniz komşuları da vardır. Siyaset yorumu yoktur."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "havza",
        "baslik": "akarsu havza",
        "aliases": ["havza", "akarsu havzasi", "kizilirmak", "fir at", "fırat", "dicle"],
        "metin": (
            "Havza: akarsuyun sularını topladığı alan. Kızılırmak, Sakarya, Fırat, Dicle "
            "okulda anılır. Sulama ve enerji bağlamı kavramdır."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "nufus_yerlesme",
        "baslik": "nufus yerlesme",
        "aliases": ["nufus", "nüfus", "yerlesme", "yerleşme", "kentlesme", "kentleşme"],
        "metin": (
            "Türkiye’de batı ve kıyılarda yoğunluk genelde daha yüksek anlatılır. "
            "Kentleşme ve göç yerleşme biçimini etkiler. Resmi rakam uydurulmaz."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "iklim_turkiye",
        "baslik": "turkiye iklimleri",
        "aliases": [
            "turkiye iklimleri",
            "türkiye iklimleri",
            "karasal iklim",
            "akdeniz iklimi",
            "karadeniz iklimi",
        ],
        "metin": (
            "Karadeniz yağışlı kıyı, Akdeniz yaz kurak, iç–doğu karasal, Marmara geçiş. "
            "Enlem, yükselti, denize uzaklık ve bakı etkilidir."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "dag_kusaklari",
        "baslik": "anadolu dag kusaklari",
        "aliases": ["toroslar", "karadeniz daglari", "anadolu daglari", "dag kusagi"],
        "metin": (
            "Kuzeyde Karadeniz dağları, güneyde Toroslar; içte platolar; doğuda yükselti artar. "
            "Yağış ve ulaşım geçitlerini etkiler."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "projeksiyon",
        "baslik": "harita projeksiyon",
        "aliases": ["projeksiyon", "harita projeksiyon", "olcek nedir", "büyük olcek"],
        "metin": (
            "Haritada ölçek ayrıntıyı belirler. Projeksiyon küreyi düzleme aktarırken "
            "şekil/alan/mesafe bozulması olabilir."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "dogal_afet",
        "baslik": "dogal afet",
        "aliases": ["dogal afet", "doğal afet", "deprem cografya", "heyelan", "sel riski"],
        "metin": (
            "Deprem, heyelan, sel, yangın gibi afetler bölgesel risklerle anılır. "
            "Acil durum talimatı değildir; yetkili kurumlara başvurulur."
        ),
        "kaynak_notu": "Coğrafya 14c — bilinçlendirme.",
    },
    {
        "id": "ege_akdeniz_ekonomi",
        "baslik": "ege akdeniz ekonomi",
        "aliases": ["ege turizm", "akdeniz turizm", "sera tarimi", "zeytin ege"],
        "metin": (
            "Ege’de zeytin–üzüm–turizm; Akdeniz’de sera ve turizm öne çıkar. "
            "Dağ uzanışı ovaları ve kıyı kullanımını etkiler."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
    {
        "id": "beseri_kisa",
        "baslik": "beseri cografya kisa",
        "aliases": ["beseri faaliyet", "beşeri faaliyet", "insan mekan", "insan mekân"],
        "metin": (
            "Beşeri coğrafya nüfus, yerleşme, tarım, sanayi, turizm ve ulaşımı inceler. "
            "Fiziki ortam kolaylaştırır veya kısıtlar; tamamen belirlemez."
        ),
        "kaynak_notu": "Coğrafya 14c.",
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_mds() -> int:
    RAF_INC.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, body in DEEP_MD.items():
        path = RAF_INC / name
        path.write_text(body.lstrip(), encoding="utf-8")
        n += 1
        print(f"  [w] {name}")
    return n


def _load_kavramlar() -> list[dict]:
    if not KAV.is_file():
        return []
    rows: list[dict] = []
    for line in KAV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _merge_kavramlar() -> list[dict]:
    by_id: dict[str, dict] = {}
    for r in _load_kavramlar():
        kid = str(r.get("id") or "").strip()
        if kid:
            by_id[kid] = r
    for r in KAVRAMLAR_YENI:
        by_id[str(r["id"])] = r
    return list(by_id.values())


def _write_katman() -> dict:
    dest = KAT
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        "# Coğrafya derin2 katman indeksi",
        "",
        "Kaynak: Rüzgar coğrafya 14c. Eğitim. Uydurma istatistik yok.",
        "",
        "## Eklenenler",
        "",
        "Karadeniz/Marmara ekonomi · boğazlar · komşular · havza · nüfus–yerleşme · "
        "Türkiye iklimleri · Ege–Akdeniz · dağ kuşakları · projeksiyon · afet çerçevesi · beşeri kısa.",
        "",
    ]
    (incr / "derin2_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": "derin2",
        "baslik": "Coğrafya derin2 katman indeksi",
        "kaynak_id": "cografya_katman_derin2",
        "ilim_alani": "cografya",
        "faz": "14c_derin2",
        "dosya_yolu": "knowledge/ortak_kaynak/alanlar/cografya/katmanlar/derin2",
        "updated_utc": _utc(),
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
        "ilim_alani": "cografya",
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
        "not": "Coğrafya derinleştirme 2 (14c).",
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
    print("=== 14c derin2 md ===")
    n = _write_mds()
    man = _write_katman()
    _update_ortak(man)
    kav = _merge_kavramlar()
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in kav) + "\n",
        encoding="utf-8",
    )
    files = sorted(RAF_INC.glob("*.md"))
    chars = sum(len(p.read_text(encoding="utf-8")) for p in files)
    cat = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.is_file() else {}
    cat["updated_utc"] = _utc()
    cat["derinlestirme_14c"] = {
        "script": "faz14c_cografya_derin2_ingest.py",
        "ek_md": n,
        "kavram_yeni": len(KAVRAMLAR_YENI),
        "kavram_toplam": len(kav),
        "updated_utc": _utc(),
    }
    cat.setdefault("sayilar", {})
    cat["sayilar"]["md_dosya"] = len(files)
    cat["sayilar"]["karakter"] = chars
    cat["sayilar"]["kavram"] = len(kav)
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else "# Coğrafya\n"
    if "14c" not in prev:
        prev = prev.rstrip() + (
            "\n\n## Derinleştirme 2 (14c)\n"
            f"- +{n} md · kavram toplam: **{len(kav)}**\n"
            "- Script: `faz14c_cografya_derin2_ingest.py`\n"
        )
        readme.write_text(prev + "\n", encoding="utf-8")

    print(f"\nTOPLAM ek_md={n} md={len(files)} char={chars} kavram={len(kav)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
