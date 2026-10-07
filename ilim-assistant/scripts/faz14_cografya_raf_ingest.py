# -*- coding: utf-8 -*-
"""Coğrafya rafı Faz 14 — 2 fazlı dolgu.

Faz 1: kutuphane 04_cografya katalog + ek md + kavram.
Faz 2: beşeri coğrafya, İslam coğrafya mirası, harita okuryazarlığı katmanları.
Politika: Eğitim özeti; siyasi propaganda yok; sayfa uydurma yasak.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "cografya"
KAT = OUT / "katmanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_cografya.jsonl"
CATALOG = OUT / "catalog.json"
CATALOG_F2 = OUT / "catalog_faz2.json"
RAF = ROOT / "knowledge" / "kutuphane" / "raflar" / "04_cografya"

KAVRAMLAR = [
    {
        "id": "cografya",
        "baslik": "cografya",
        "aliases": ["cografya", "coğrafya", "cografya nedir", "coğrafya nedir"],
        "metin": (
            "Coğrafya: yeryüzünü, doğal ortamı, insan–mekân ilişkisini ve bölgeler arası "
            "farklılıkları inceler. Fiziki (iklim, yerşekli) ve beşeri (nüfus, yerleşme) "
            "kolları vardır. Bu raf eğitim özetidir."
        ),
        "kaynak_notu": "Coğrafya rafı — Faz 1+2.",
    },
    {
        "id": "turkiye_cografyasi",
        "baslik": "turkiye cografyasi",
        "aliases": [
            "turkiye cografyasi",
            "türkiye coğrafyası",
            "anadolu",
            "turkiye konumu",
        ],
        "metin": (
            "Türkiye; Anadolu ve Trakya’da, Asya ile Avrupa arasında yer alır. "
            "İstanbul ve Çanakkale boğazları vardır. Coğrafi bölgeler: Karadeniz, Marmara, "
            "Ege, Akdeniz, İç Anadolu, Doğu Anadolu, Güneydoğu Anadolu. Başkent Ankara’dır."
        ),
        "kaynak_notu": "Coğrafya — Türkiye.",
    },
    {
        "id": "kitalar",
        "baslik": "kitalar",
        "aliases": ["kitalar", "kıtalar", "kita", "kıta", "yedi kita"],
        "metin": (
            "Kıtalar: Afrika, Antarktika, Asya, Avrupa, Güney Amerika, Kuzey Amerika, "
            "Okyanusya (Avustralya). Sınırlar kültürel/siyasal tanımlarla da tartışılır."
        ),
        "kaynak_notu": "Coğrafya — dünya.",
    },
    {
        "id": "okyanuslar",
        "baslik": "okyanuslar",
        "aliases": ["okyanuslar", "okyanus", "denizler"],
        "metin": (
            "Başlıca okyanuslar: Pasifik, Atlas (Atlantik), Hint, Güney, Arktik. "
            "Denizler okyanuslara bağlı daha küçük su kütleleridir."
        ),
        "kaynak_notu": "Coğrafya — hidrografya.",
    },
    {
        "id": "harita",
        "baslik": "harita",
        "aliases": ["harita", "harita nedir", "olcek", "ölçek", "yon", "yön"],
        "metin": (
            "Harita: yeryüzünün küçültülmüş, seçilmiş ve işaretlerle gösterilmiş düzlem "
            "görünümüdür. Ölçek küçültme oranını; yön (kuzey vb.) yönelimi verir."
        ),
        "kaynak_notu": "Coğrafya — harita okuryazarlığı.",
    },
    {
        "id": "iklim",
        "baslik": "iklim",
        "aliases": ["iklim", "iklim nedir", "iklim tipleri", "hava durumu"],
        "metin": (
            "İklim: bir yerde uzun yılların ortalama hava koşullarıdır; hava durumu kısa "
            "süreli değişimdir. Türkiye’de Karadeniz, Akdeniz ve karasal özellikler yaygındır."
        ),
        "kaynak_notu": "Coğrafya — klimatoloji özeti.",
    },
    {
        "id": "akarsu_dag",
        "baslik": "turkiye akarsu dag",
        "aliases": [
            "turkiye akarsu",
            "türkiye akarsu",
            "turkiye daglari",
            "türkiye dağları",
            "kizilirmak",
            "fırat",
            "dicle",
        ],
        "metin": (
            "Türkiye’de Kuzey Anadolu ve Toros dağ kuşakları belirgindir. Önemli akarsular "
            "arasında Kızılırmak, Sakarya, Fırat, Dicle anılır. Denizler: Karadeniz, "
            "Marmara, Ege, Akdeniz."
        ),
        "kaynak_notu": "Coğrafya — Türkiye fiziki.",
    },
    {
        "id": "beseri_cografya",
        "baslik": "beseri cografya",
        "aliases": [
            "beseri cografya",
            "beşeri coğrafya",
            "nufus cografyasi",
            "nüfus coğrafyası",
            "yerlesme",
        ],
        "metin": (
            "Beşeri coğrafya: nüfus, yerleşme, göç, ekonomik faaliyet ve kültürel mekân "
            "ilişkilerini inceler. Bu katman kavram/özettir; güncel istatistik için resmi "
            "kaynaklara bakılır."
        ),
        "kaynak_notu": "Coğrafya Faz 2.",
    },
    {
        "id": "islam_cografya_mirasi",
        "baslik": "islam cografya mirasi",
        "aliases": [
            "islam cografya",
            "islâm coğrafya",
            "biruni",
            "bîrûnî",
            "idrisî",
            "idrisi",
        ],
        "metin": (
            "İslâm coğrafya mirası: klasik dönemde dünya tasviri, mesafe ölçümü ve harita "
            "geleneği (ör. Bîrûnî, İdrîsî çerçeveleri). Kavram/özettir; fetva değildir."
        ),
        "kaynak_notu": "Coğrafya Faz 2 — miras.",
    },
    {
        "id": "bolge",
        "baslik": "bolge",
        "aliases": ["bolge", "bölge", "cografi bolge", "coğrafi bölge"],
        "metin": (
            "Bölge: benzer doğal veya beşeri özelliklere göre ayrılmış alan. "
            "Türkiye’nin yedi coğrafi bölgesi okul coğrafyasında yaygın kullanılır."
        ),
        "kaynak_notu": "Coğrafya — kavram.",
    },
]

KATMANLAR = {
    "harita_okuryazarligi": {
        "baslik": "Harita okuryazarlığı",
        "kaynak_id": "cografya_katman_harita",
        "parcalar": [
            (
                "Ölçek ve lejant",
                "Ölçek gerçek uzaklık–harita uzaklığı oranıdır. Lejant (gösterge) renk ve "
                "sembollerin anlamını verir. Kuzey oku yön bulmaya yardım eder.",
            ),
            (
                "Projeksiyon",
                "Küresel yüzeyi düzleme aktarmak bozulma yaratır; farklı projeksiyonlar "
                "farklı amaçlara hizmet eder. Eğitim özetidir.",
            ),
        ],
    },
    "beseri": {
        "baslik": "Beşeri coğrafya (kavram)",
        "kaynak_id": "cografya_katman_beseri",
        "parcalar": [
            (
                "Nüfus ve yerleşme",
                "Nüfus yoğunluğu, kır–kent, göç ve ekonomik faaliyet mekânı şekillendirir. "
                "Güncel sayılar için TÜİK vb. resmi kaynak kullanılır.",
            ),
            (
                "Siyasi sınır",
                "Devlet sınırları tarihî ve siyasi süreçlerle oluşur. Bu raf propaganda "
                "yapmaz; eğitim çerçevesi verir.",
            ),
        ],
    },
    "islam_miras": {
        "baslik": "İslâm coğrafya mirası (kavram)",
        "kaynak_id": "cografya_katman_islam_miras",
        "parcalar": [
            (
                "Çerçeve",
                "Klasik İslâm medeniyetinde yolculuknameler, zîcler ve harita eserleri "
                "coğrafi birikime katkıda bulunmuştur. Özet/kavramdır; sayfa uydurulmaz.",
            ),
            (
                "Örnek isimler",
                "Bîrûnî (ölçüm, kıble, yer bilimi ilgisi), İdrîsî (dünya haritası geleneği). "
                "Modern ölçüm ve uydu verisi bunların yerine geçmez; bağlam sağlar.",
            ),
        ],
    },
}

EXTRA_MD = [
    (
        "006_turkiye_bolgeler_kisa.md",
        "# Türkiye coğrafi bölgeler — kısa\n\n"
        "Kaynak notu: Okul coğrafyası özeti.\n\n"
        "## Yedi bölge\n"
        "1. Karadeniz — yağışlı, kıyı dağları\n"
        "2. Marmara — geçiş iklimi, yoğun nüfus\n"
        "3. Ege — bakı ve zeytin–turizm\n"
        "4. Akdeniz — yazları sıcak–kurak\n"
        "5. İç Anadolu — karasal, bozkır\n"
        "6. Doğu Anadolu — yüksek, sert kış\n"
        "7. Güneydoğu Anadolu — sıcak yaz, ovalar\n",
    ),
    (
        "007_dunya_enlem_boylam.md",
        "# Enlem ve boylam — Rüzgar Kütüphanesi\n\n"
        "Kaynak notu: Temel konum bilgisi.\n\n"
        "## Enlem\n"
        "Ekvatora paralel daireler; 0° ekvator, 90° kutuplar. İklim kuşaklarıyla ilişkilidir.\n\n"
        "## Boylam\n"
        "Greenwich (0°) meridyeninden doğu–batı açısal uzaklık. Saat dilimleri boylamla "
        "bağlantılıdır.\n",
    ),
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_extra() -> int:
    dest = RAF / "incremental"
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, body in EXTRA_MD:
        path = dest / name
        if not path.is_file():
            path.write_text(body, encoding="utf-8")
            n += 1
            print(f"  [+] {name}")
        else:
            print(f"  [=] {name}")
    return n


def _scan() -> dict:
    files = sorted(RAF.rglob("*.md")) if RAF.is_dir() else []
    chars = 0
    for p in files:
        try:
            chars += len(p.read_text(encoding="utf-8"))
        except OSError:
            pass
    return {
        "raf_id": "04_cografya",
        "ad": "Coğrafya",
        "dosya": len(files),
        "karakter": chars,
        "dosya_yolu": "knowledge/kutuphane/raflar/04_cografya",
        "faz": 1,
        "ilim_alani": "cografya",
        "durum": "hazir",
        "updated_utc": _utc(),
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
        "Kaynak: Rüzgar coğrafya Faz 2. Eğitim özeti. Fetva yok. Propaganda yok.",
        "",
    ]
    for i, (title, text) in enumerate(spec["parcalar"], 1):
        body += [f"## {i}. {title}", "", text, ""]
    (incr / f"{key}_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": key,
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "cografya",
        "faz": 2,
        "dil": "tr",
        "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/cografya/katmanlar/{key}",
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
    added = _write_extra()
    sc = _scan()
    print(f"  [ok] raf dosya={sc['dosya']} char={sc['karakter']}")

    _update_ortak(
        {
            "kaynak_id": "cografya_raf_04",
            "kaynak_adi": "Coğrafya (kutuphane rafı)",
            "yazar": None,
            "ilim_alani": "cografya",
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
            "not": "Kutuphane coğrafya rafı; eğitim özeti.",
        }
    )

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
                "not": "Coğrafya Faz 2 katman.",
            }
        )
        print(f"  [ok] {key}")

    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in KAVRAMLAR) + "\n",
        encoding="utf-8",
    )

    cat = {
        "domain": "cografya",
        "faz": {"1": "kutuphane_04", "2": "harita_beseri_miras"},
        "updated_utc": _utc(),
        "politika": (
            "2 fazlı. Eğitim özeti. Fetva yok. Siyasi propaganda yok. "
            "Sayfa/cilt uydurma yasak."
        ),
        "faz1_raf": sc,
        "faz2_katmanlar": faz2,
        "sayilar": {
            "md_dosya": sc["dosya"],
            "faz2_katman": len(faz2),
            "kavram": len(KAVRAMLAR),
            "ek_md_yeni": added,
        },
    }
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_F2.write_text(
        json.dumps(
            {
                "domain": "cografya_faz2",
                "updated_utc": _utc(),
                "katmanlar": faz2,
                "kavram_faz2_ids": [
                    "beseri_cografya",
                    "islam_cografya_mirasi",
                    "harita",
                    "bolge",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (OUT / "README.md").write_text(
        "# Coğrafya — 2 fazlı raf\n\n"
        "## Faz 1\n`knowledge/kutuphane/raflar/04_cografya`\n\n"
        "## Faz 2\n"
        "`katmanlar/harita_okuryazarligi` · `beseri` · `islam_miras`\n\n"
        f"MD: **{sc['dosya']}** · Kavram: **{len(KAVRAMLAR)}**\n\n"
        "**Script:** `faz14_cografya_raf_ingest.py` · "
        "**Anlık:** `ruzgar_cografya_kutuphane.py`\n",
        encoding="utf-8",
    )
    print(
        f"\nTOPLAM cografya md={sc['dosya']} katman={len(faz2)} kavram={len(KAVRAMLAR)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
