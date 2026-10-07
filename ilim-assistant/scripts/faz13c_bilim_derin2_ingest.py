# -*- coding: utf-8 -*-
"""Bilim derinleştirme 2 (Faz 13c) — ek eğitim özetleri.

13b üzerine ~13 md + yeni kavram. Tıbbi teşhis yok. Tehlikeli deney yok.
Uydurma kesin rakam yok (mertebe/eğitim).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilim"
KUTUP = ROOT / "knowledge" / "kutuphane" / "raflar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_bilim.jsonl"
CATALOG = OUT / "catalog.json"
KAT = OUT / "katmanlar" / "derin2"

DEEP_MD: dict[str, dict[str, str]] = {
    "01_astronomi_uzay": {
        "011_atmosfer_katmanlari.md": """# Dünya atmosferi — katmanlar (kısa)

Kaynak notu: Eğitim. Kesin yükseklik uydurma yok; mertebe fikri.

## Katmanlar (okul modeli)
Troposfer (hava olayları), stratosfer (ozon bağlamı), mezosfer, termosfer, ekzosfer.

## Önemi
Atmosfer solunabilir hava, ısı dengesi ve meteor yağmurlarını yavaşlatma bağlamında anılır.
""",
        "012_gezegenler_ic_dis.md": """# İç ve dış gezegenler

Kaynak notu: Güneş Sistemi eğitimi.

## İç (kayalık)
Merkür, Venüs, Dünya, Mars — Güneş’e daha yakın, yoğunluk genelde yüksek.

## Dış (gaz/buz devleri)
Jüpiter, Satürn, Uranüs, Neptün — büyük, uyduları çok. Asteroid kuşağı Mars–Jüpiter arasındadır.
""",
        "013_uydu_ve_gps_cerceve.md": """# Yapay uydu ve konum (çerçeve)

Kaynak notu: Kavram. Askerî/operasyonel talimat değildir.

## Uydu
Dünya yörüngesinde iletişim, gözlem, hava durumu, konum servisleri için kullanılır.

## GPS fikri
Birden fazla uydudan gelen zaman sinyalleriyle konum kestirimi (eğitim modeli).
""",
    },
    "02_fizik_kimya": {
        "011_newton_enerji_is.md": """# Newton, iş ve enerji — bağ

Kaynak notu: Lise düzeyi.

## İş
Kuvvet × yol (basit model). Enerji iş yapabilme kapasitesidir.

## Dönüşüm
Potansiyel ↔ kinetik örnekleri (eğik düzlem, sarkaç çerçevesi). Sürtünme ısıya dönüştürür.
""",
        "012_basit_devre_ohm.md": """# Basit devre ve Ohm çerçevesi

Kaynak notu: Eğitim. Elektrik güvenlik protokolü değildir.

## Devre
Kaynak, iletken, yük (ampul vb.) kapalı yol oluşturur.

## Ohm (eğitim)
V ≈ I × R fikri: gerilim, akım, direnç ilişkisi. Ev tesisatı hesabı bu paketin konusu değildir.
""",
        "013_madde_halleri.md": """# Maddenin halleri

Kaynak notu: Genel kimya/fizik.

## Katı–sıvı–gaz
Parçacık düzeni ve hareket farkı. Erime, buharlaşma, yoğuşma, süblimleşme eğitimde anılır.

## Plazma
Yüksek enerjili iyonize durum (yıldızlarda yaygın) — kısa hatırlatma.
""",
        "014_periyodik_gruplar.md": """# Periyodik tablo — grup fikri

Kaynak notu: Kavram. Laboratuvar deneyi yoktur.

## Düzen
Elementler artan atom numarasına göre; aynı grup benzer özellik gösterebilir (alkali metaller, soy gazlar vb. okul örnekleri).

## Sınır
Tek tek element özellikleri bu özetin kapsamı dışındadır.
""",
    },
    "03_biyoloji_dunya": {
        "011_hucre_organeller.md": """# Hücre organelleri — kısa

Kaynak notu: Eğitim. Klinik teşhis değildir.

## Temeller
Çekirdek (kalıtım bilgisi), mitokondri (enerji), ribozom (protein), hücre zarı (seçici geçiş).

## Bitki–hayvan
Bitki hücresinde hücre duvarı ve kloroplast (fotosentez) okulda vurgulanır.
""",
        "012_dna_kalitim_cerceve.md": """# DNA ve kalıtım — çerçeve

Kaynak notu: Genel biyoloji. Genetik danışmanlık/teşhis değildir.

## DNA
Kalıtsal bilgi; genler işlevsel birimler. Eşeyli üremede ebeveynlerden aktarım eğitimi.

## Mendel fikri
Baskın/çekinik özellik modeli okul biyolojisinde anılır (basitleştirilmiş).
""",
        "013_bagisiklik_genel.md": """# Bağışıklık — genel çerçeve

Kaynak notu: Okul bilgisi. Teşhis, aşı takvimi veya tedavi önerisi değildir.

## Fikir
Vücut zararlı etkenlere karşı savunma katmanları kullanır (deri, hücreler, antikor çerçevesi).

## Sınır
Hastalık adı koyma, ilaç/doz, aşı kararı bu pakette yoktur.
""",
    },
    "06_matematik": {
        "011_oran_oranti.md": """# Oran ve orantı

Kaynak notu: Günlük matematik.

## Oran
a:b veya a/b. Tarif, harita ölçeği, hız–zaman problemlerinde kullanılır.

## Orantı
a/b = c/d ise çapraz çarpım (eğitim). Birim dönüşümünde faydalıdır.
""",
        "012_istatistik_ortalama.md": """# İstatistik özetleri — kısa

Kaynak notu: Temel. Anket/siyaset yorumu değildir.

## Ortalama–medyan–mod
Ortalama: toplam/adet. Medyan: sıralı ortadaki. Mod: en sık değer.

## Dikkat
Aykırı değer ortalamayı çeker; medyan daha dayanıklı olabilir (kavram).
""",
        "013_aci_ucgen.md": """# Açı ve üçgen — kısa

Kaynak notu: Temel geometri.

## Açı
Derece ile ölçülür; doğru açı 180°, tam tur 360° (okul modeli).

## Üçgen
İç açılar toplamı 180°. Dik, ikizkenar, eşkenar türleri eğitimde anılır.
""",
    },
}

# Yalnızca 13c ekleri — mevcut jsonl ile birleştirilir
KAVRAMLAR_YENI = [
    {
        "id": "atmosfer",
        "baslik": "atmosfer",
        "aliases": ["atmosfer", "atmosfer katmanlari", "troposfer", "ozon"],
        "metin": (
            "Atmosfer: Dünya’yı saran gaz katmanı. Troposferde hava olayları olur; "
            "stratosferde ozon bağlamı okulda anılır. Solunum ve iklim dengesi için kritiktir."
        ),
        "kaynak_notu": "Bilim 13c — astronomi/yer.",
    },
    {
        "id": "ic_dis_gezegen",
        "baslik": "ic dis gezegen",
        "aliases": [
            "ic gezegen",
            "iç gezegen",
            "dis gezegen",
            "dış gezegen",
            "kayalik gezegen",
            "gaz devi",
        ],
        "metin": (
            "İç gezegenler kayalık (Merkür–Mars); dış gezegenler gaz/buz devleridir "
            "(Jüpiter–Neptün). Asteroid kuşağı Mars ile Jüpiter arasındadır."
        ),
        "kaynak_notu": "Bilim 13c — Güneş Sistemi.",
    },
    {
        "id": "uydu_gps",
        "baslik": "uydu gps",
        "aliases": ["yapay uydu", "uydu", "gps", "konum servisi", "gps nedir"],
        "metin": (
            "Yapay uydular iletişim, gözlem ve konum için yörüngede çalışır. "
            "GPS: birden fazla uydudan zaman sinyaliyle konum kestirimi (eğitim modeli)."
        ),
        "kaynak_notu": "Bilim 13c — uzay teknolojisi çerçevesi.",
    },
    {
        "id": "is_enerji",
        "baslik": "is ve enerji",
        "aliases": ["is nedir", "iş nedir", "is enerji", "enerji donusumu"],
        "metin": (
            "İş: kuvvet × yol (basit model). Enerji iş kapasitesidir; potansiyel–kinetik "
            "dönüşümü ve sürtünmeyle ısıya geçiş eğitimde anılır."
        ),
        "kaynak_notu": "Bilim 13c — fizik.",
    },
    {
        "id": "ohm_devre",
        "baslik": "ohm ve devre",
        "aliases": ["ohm", "ohm kanunu", "basit devre", "direnc", "direnç", "akim gerilim"],
        "metin": (
            "Basit devre kapalı yoldur. Ohm çerçevesi: V ≈ I×R (eğitim). "
            "Ev elektrik hesabı/güvenlik protokolü değildir."
        ),
        "kaynak_notu": "Bilim 13c — fizik.",
    },
    {
        "id": "madde_halleri",
        "baslik": "madde halleri",
        "aliases": ["madde halleri", "kati sivi gaz", "katı sıvı gaz", "plazma", "erime"],
        "metin": (
            "Madde katı, sıvı, gaz (ve plazma) hallerinde olabilir. Erime, buharlaşma, "
            "yoğuşma faz değişimleridir."
        ),
        "kaynak_notu": "Bilim 13c — kimya/fizik.",
    },
    {
        "id": "periyodik_grup",
        "baslik": "periyodik grup",
        "aliases": ["periyodik tablo", "element grubu", "soy gaz", "alkali metal"],
        "metin": (
            "Periyodik tabloda elementler atom numarasına göre düzenlenir; aynı grup "
            "benzer özellik gösterebilir. Laboratuvar deneyi yoktur."
        ),
        "kaynak_notu": "Bilim 13c — kimya.",
    },
    {
        "id": "organeller",
        "baslik": "hucre organelleri",
        "aliases": [
            "organeller",
            "mitokondri",
            "ribozom",
            "kloroplast",
            "hucre zar",
            "hücre zarı",
        ],
        "metin": (
            "Organeller hücre içinde iş bölümü yapar: çekirdek, mitokondri, ribozom, zar. "
            "Bitkide kloroplast fotosentez yapar. Klinik teşhis değildir."
        ),
        "kaynak_notu": "Bilim 13c — biyoloji.",
    },
    {
        "id": "kalitim",
        "baslik": "kalitim",
        "aliases": ["kalitim", "kalıtım", "mendel", "baskin gen", "çekinik"],
        "metin": (
            "Kalıtım: özelliklerin DNA/genler yoluyla aktarımı. Mendel modeli okulda "
            "basitleştirilir. Genetik danışmanlık değildir."
        ),
        "kaynak_notu": "Bilim 13c — biyoloji; klinik değil.",
    },
    {
        "id": "bagisiklik",
        "baslik": "bagisiklik",
        "aliases": ["bagisiklik", "bağışıklık", "antikor", "bagisiklik sistemi"],
        "metin": (
            "Bağışıklık: vücudun zararlı etkenlere karşı savunma katmanları. "
            "Teşhis, aşı takvimi veya tedavi önerisi değildir."
        ),
        "kaynak_notu": "Bilim 13c — biyoloji; klinik değil.",
    },
    {
        "id": "oran_oranti",
        "baslik": "oran oranti",
        "aliases": ["oran", "oranti", "orantı", "oran oranti", "capraz carpim"],
        "metin": (
            "Oran a:b veya a/b’dir. Orantıda a/b = c/d ise çapraz çarpım kullanılır. "
            "Ölçek ve tarif problemlerinde işe yarar."
        ),
        "kaynak_notu": "Bilim 13c — matematik.",
    },
    {
        "id": "ortalama_medyan",
        "baslik": "ortalama medyan",
        "aliases": ["ortalama", "medyan", "mod", "istatistik", "ortalama nedir"],
        "metin": (
            "Ortalama = toplam/adet; medyan sıralı ortadaki; mod en sık değer. "
            "Aykırı değer ortalamayı etkileyebilir."
        ),
        "kaynak_notu": "Bilim 13c — matematik.",
    },
    {
        "id": "aci_ucgen",
        "baslik": "aci ve ucgen",
        "aliases": ["aci", "açı", "ucgen", "üçgen", "dik ucgen", "ic acilar"],
        "metin": (
            "Açı derece ile ölçülür. Üçgen iç açıları toplamı 180°. "
            "Dik, ikizkenar, eşkenar türleri vardır."
        ),
        "kaynak_notu": "Bilim 13c — matematik.",
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_mds() -> int:
    n = 0
    for raf, files in DEEP_MD.items():
        dest = KUTUP / raf / "incremental"
        dest.mkdir(parents=True, exist_ok=True)
        for name, body in files.items():
            path = dest / name
            path.write_text(body.lstrip(), encoding="utf-8")
            n += 1
            print(f"  [w] {raf}/{name}")
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


def _scan() -> dict:
    out: dict = {}
    total_md = 0
    total_ch = 0
    for raf in ("01_astronomi_uzay", "02_fizik_kimya", "03_biyoloji_dunya", "06_matematik"):
        files = list((KUTUP / raf).rglob("*.md"))
        ch = sum(len(p.read_text(encoding="utf-8")) for p in files)
        out[raf] = {"md": len(files), "char": ch}
        total_md += len(files)
        total_ch += ch
    out["_toplam"] = {"md": total_md, "char": total_ch}
    return out


def _write_katman() -> dict:
    dest = KAT
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        "# Bilim derin2 katman indeksi",
        "",
        "Kaynak: Rüzgar bilim 13c. Eğitim. Tıbbi teşhis yok. Tehlikeli deney yok.",
        "",
        "## Eklenenler",
        "",
        "Atmosfer · iç/dış gezegen · uydu/GPS çerçevesi · iş–enerji · Ohm/devre · "
        "madde halleri · periyodik grup · organeller · kalıtım · bağışıklık (genel) · "
        "oran–orantı · ortalama/medyan · açı–üçgen.",
        "",
        "## Sınır",
        "",
        "Klinik teşhis, laboratuvar protokolü ve uydurma kesin rakam yoktur.",
        "",
    ]
    (incr / "derin2_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": "derin2",
        "baslik": "Bilim derin2 katman indeksi",
        "kaynak_id": "bilim_katman_derin2",
        "ilim_alani": "bilim",
        "faz": "13c_derin2",
        "dosya_yolu": "knowledge/ortak_kaynak/alanlar/bilim/katmanlar/derin2",
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
        "not": "Bilim derinleştirme 2 (13c).",
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
    print("=== 13c derin2 md ===")
    n = _write_mds()
    man = _write_katman()
    _update_ortak(man)
    kav = _merge_kavramlar()
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in kav) + "\n",
        encoding="utf-8",
    )
    sc = _scan()
    cat = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.is_file() else {}
    cat["updated_utc"] = _utc()
    cat["derinlestirme_13c"] = {
        "script": "faz13c_bilim_derin2_ingest.py",
        "ek_md": n,
        "kavram_yeni": len(KAVRAMLAR_YENI),
        "kavram_toplam": len(kav),
        "scan": sc,
        "updated_utc": _utc(),
    }
    cat.setdefault("sayilar", {})
    cat["sayilar"]["md_dosya"] = sc["_toplam"]["md"]
    cat["sayilar"]["karakter"] = sc["_toplam"]["char"]
    cat["sayilar"]["kavram"] = len(kav)
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else "# Bilim\n"
    if "13c" not in prev:
        prev = prev.rstrip() + (
            "\n\n## Derinleştirme 2 (13c)\n"
            f"- +{n} md · kavram toplam: **{len(kav)}**\n"
            "- Script: `faz13c_bilim_derin2_ingest.py`\n"
        )
        readme.write_text(prev + "\n", encoding="utf-8")

    print(
        f"\nTOPLAM ek_md={n} md={sc['_toplam']['md']} "
        f"char={sc['_toplam']['char']} kavram={len(kav)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
