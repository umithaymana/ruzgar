# -*- coding: utf-8 -*-
"""Teknoloji rafı Faz 15 — 2 fazlı dolgu.

Faz 1: kutuphane 08_teknoloji + ek eğitim md + kavram.
Faz 2: güvenlik hijyeni, yazılım kavramları, YZ sınırları.
Politika: Eğitim. Saldırı/exploit tarifı yok. Teşhis/tedavi yok.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "teknoloji"
KAT = OUT / "katmanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_teknoloji.jsonl"
CATALOG = OUT / "catalog.json"
CATALOG_F2 = OUT / "catalog_faz2.json"
RAF = ROOT / "knowledge" / "kutuphane" / "raflar" / "08_teknoloji"

EXTRA_MD = {
    "006_isletim_sistemi.md": """# İşletim sistemi — kısa

Kaynak notu: Eğitim özeti.

## Ne işe yarar
Donanımı yönetir; programlara bellek, dosya ve ağ erişimi sağlar. Windows, Linux, macOS yaygın örneklerdir.

## Dosya ve işlem
Dosyalar diskte; çalışan programlar işlemdir (process). Güncelleme güvenlik için önemlidir.
""",
    "007_programlama_kavram.md": """# Programlama kavramları — kısa

Kaynak notu: Genel. Saldırı kodu yoktur.

## Algoritma ve kod
Algoritma: adım adım çözüm. Program: bilgisayarın çalıştırdığı talimatlar.

## Değişken, koşul, döngü
Veri saklama; eğer–ise karar; tekrarlayan işlem. Yazılım motoru ayrı derinlikte işler.
""",
    "008_internet_dns_http.md": """# İnternet, DNS, HTTP — kısa

Kaynak notu: Eğitim.

## İnternet
Ağların ağı. IP adresleri cihazları tanımlar; DNS isimleri adrese çevirir.

## HTTP/HTTPS
Web sayfası isteği. HTTPS şifreli taşıma katmanıdır (eğitim çerçevesi).
""",
    "009_sifre_2fa_hijyen.md": """# Şifre ve 2FA hijyeni

Kaynak notu: Savunma hijyeni. Saldırı tarifi yok.

## İyi alışkanlık
Uzun ve benzersiz şifre; her siteye ayrı; mümkünse iki adımlı doğrulama (2FA).

## Olmaması gereken
Şifreyi paylaşmak, her yerde aynı şifre, şüpheli linkte oturum açmak.
""",
    "010_yapay_zeka_sinir.md": """# Yapay zekâ — sınırlar

Kaynak notu: Kavram. Rüzgar kendi mimarisinden ayrı genel çerçeve.

## Ne yapabilir
Metin özeti, çeviri yardımı, kod iskeleti, soru–cevap (yanılabilir).

## Ne değildir
Kesin hakikat motoru, hukuki/tıbbi nihai merci, sınırsız bellek. Kaynak kontrolü gerekir.
""",
}

KAVRAMLAR = [
    {
        "id": "teknoloji",
        "baslik": "teknoloji",
        "aliases": ["teknoloji", "teknoloji nedir", "bilgisayar", "dijital"],
        "metin": (
            "Teknoloji rafı: bilgisayar temeli, ağ, güvenlik hijyeni, veri/yedek ve yapay zekâ "
            "kavramları. Eğitim özetidir; saldırı/exploit tarifi yoktur."
        ),
        "kaynak_notu": "Teknoloji — Faz 1+2.",
    },
    {
        "id": "bilgisayar",
        "baslik": "bilgisayar",
        "aliases": ["bilgisayar", "pc", "donanim", "donanım", "yazilim", "yazılım"],
        "metin": (
            "Bilgisayar: donanım (işlemci, bellek, depolama) + yazılım (işletim sistemi ve programlar). "
            "Veriyi işler ve saklar."
        ),
        "kaynak_notu": "Teknoloji — temel.",
    },
    {
        "id": "isletim_sistemi",
        "baslik": "isletim sistemi",
        "aliases": ["isletim sistemi", "işletim sistemi", "windows", "linux", "macos", "os"],
        "metin": (
            "İşletim sistemi donanımı yönetir ve programlara kaynak verir. "
            "Güncel tutmak güvenlik hijyeninin parçasıdır."
        ),
        "kaynak_notu": "Teknoloji — OS.",
    },
    {
        "id": "internet",
        "baslik": "internet",
        "aliases": ["internet", "ag", "ağ", "www", "web"],
        "metin": (
            "İnternet: küresel ağ. Web onun üzerindeki hizmetlerden biridir. "
            "DNS isim çözümler; HTTP/HTTPS sayfa taşır."
        ),
        "kaynak_notu": "Teknoloji — ağ.",
    },
    {
        "id": "url",
        "baslik": "url",
        "aliases": ["url", "link", "adres cubugu", "https"],
        "metin": (
            "URL: kaynağın adresi. HTTPS şifreli bağlantı işaretidir; yine de sahte site "
            "olabileceğinden dikkat gerekir (hijyen)."
        ),
        "kaynak_notu": "Teknoloji — ağ.",
    },
    {
        "id": "guvenlik",
        "baslik": "guvenlik",
        "aliases": [
            "guvenlik",
            "güvenlik",
            "siber guvenlik",
            "siber güvenlik",
            "guvenlik hijyeni",
        ],
        "metin": (
            "Güvenlik hijyeni: güçlü şifre, 2FA, güncelleme, şüpheli e-posta/linkten uzak durma. "
            "Bu raf saldırı yöntemleri öğretmez; korunma ilkelerini özetler."
        ),
        "kaynak_notu": "Teknoloji — savunma hijyeni.",
    },
    {
        "id": "sifre",
        "baslik": "sifre",
        "aliases": ["sifre", "şifre", "parola", "2fa", "iki adimli"],
        "metin": (
            "Şifre: uzun, benzersiz, paylaşılmaz. 2FA ikinci doğrulama katmanıdır. "
            "Kırılma/exploit tarifi yoktur."
        ),
        "kaynak_notu": "Teknoloji — hijyen.",
    },
    {
        "id": "veri_yedek",
        "baslik": "veri yedek",
        "aliases": ["yedek", "backup", "bulut", "cloud", "veri yedekleme"],
        "metin": (
            "Yedekleme: önemli verinin kopyası. 3-2-1 fikri eğitimde anılır "
            "(üç kopya, iki ortam, biri uzakta — özet). Bulut da bir ortam olabilir."
        ),
        "kaynak_notu": "Teknoloji — veri.",
    },
    {
        "id": "yapay_zeka",
        "baslik": "yapay zeka",
        "aliases": [
            "yapay zeka",
            "yapay zekâ",
            "ai",
            "llm",
            "dil modeli",
            "chatgpt",
        ],
        "metin": (
            "Yapay zekâ (genel): örüntü öğrenen sistemler; dil modelleri metin üretir ama "
            "yanılabilir. Kesin kaynak yerine geçmez. Rüzgar’ın kendi motor sırası ayrıdır."
        ),
        "kaynak_notu": "Teknoloji — YZ kavram.",
    },
    {
        "id": "programlama",
        "baslik": "programlama",
        "aliases": ["programlama", "kodlama", "algoritma", "yazilim gelistirme"],
        "metin": (
            "Programlama: problemi algoritmaya döküp kodla ifade etmek. "
            "Değişken, koşul, döngü temeldir. Derin uygulama programlama motorundadır."
        ),
        "kaynak_notu": "Teknoloji — yazılım kavram.",
    },
    {
        "id": "dosya",
        "baslik": "dosya",
        "aliases": ["dosya", "klasor", "klasör", "uzanti", "uzantı"],
        "metin": (
            "Dosya: saklanan veri birimi; uzantı tür ipucu verir (.txt, .jpg). "
            "Bilinmeyen ekleri açmamak hijyendir."
        ),
        "kaynak_notu": "Teknoloji — temel.",
    },
    {
        "id": "gizlilik",
        "baslik": "gizlilik",
        "aliases": ["gizlilik", "mahremiyet", "privacy", "kisisel veri"],
        "metin": (
            "Gizlilik: kişisel veriyi gereksiz paylaşmamak, izinleri kontrol etmek. "
            "Eğitim ilkesi; hukukî danışmanlık değildir."
        ),
        "kaynak_notu": "Teknoloji Faz 2.",
    },
    {
        "id": "zararli_yazilim",
        "baslik": "zararli yazilim",
        "aliases": ["virüs", "virus", "malware", "zararli yazilim", "zararlı yazılım"],
        "metin": (
            "Zararlı yazılım: istenmeyen zararlı programlar. Korunma: güncelleme, "
            "güvenilir kaynak, şüpheli ek/linkten kaçınma. Üretim/yayma tarifi yoktur."
        ),
        "kaynak_notu": "Teknoloji — savunma; saldırı yok.",
    },
]

KATMANLAR = {
    "guvenlik_hijyen": {
        "baslik": "Güvenlik hijyeni",
        "kaynak_id": "teknoloji_katman_guvenlik",
        "parcalar": [
            (
                "Temel üçlü",
                "Güncelle · güçlü/benzersiz şifre + 2FA · şüpheli ileti/linke tıklama.",
            ),
            (
                "Sınır",
                "Bu raf saldırı, exploit, keylogger, yetkisiz erişim öğretmez. "
                "Yalnızca korunma ilkeleri.",
            ),
        ],
    },
    "yazilim": {
        "baslik": "Yazılım kavramları",
        "kaynak_id": "teknoloji_katman_yazilim",
        "parcalar": [
            (
                "Katmanlar",
                "İşletim sistemi → uygulamalar → veri. Programlama temel yapıları "
                "(değişken, koşul, döngü) eğitim özetidir.",
            ),
            (
                "Rüzgar bağı",
                "Derin kod işi programlama motoruna aittir; bu raf genel okuryazarlıktır.",
            ),
        ],
    },
    "yz_sinir": {
        "baslik": "YZ sınırları",
        "kaynak_id": "teknoloji_katman_yz",
        "parcalar": [
            (
                "Yanılabilirlik",
                "Dil modelleri uydurabilir; önemli iddiayı kaynakla doğrula.",
            ),
            (
                "Rol",
                "Yardımıcı araçtır; nihai hukuki/tıbbi/fetva mercii değildir.",
            ),
        ],
    },
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_extra() -> int:
    dest = RAF / "incremental"
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, body in EXTRA_MD.items():
        path = dest / name
        path.write_text(body.lstrip(), encoding="utf-8")
        n += 1
        print(f"  [w] {name}")
    return n


def _scan() -> dict:
    files = sorted(RAF.rglob("*.md")) if RAF.is_dir() else []
    chars = sum(len(p.read_text(encoding="utf-8")) for p in files)
    return {
        "raf_id": "08_teknoloji",
        "ad": "Teknoloji ve Bilgisayar",
        "dosya": len(files),
        "karakter": chars,
        "dosya_yolu": "knowledge/kutuphane/raflar/08_teknoloji",
        "faz": 1,
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
        "Kaynak: Rüzgar teknoloji Faz 2. Eğitim. Saldırı/exploit yok.",
        "",
    ]
    for i, (t, x) in enumerate(spec["parcalar"], 1):
        body += [f"## {i}. {t}", "", x, ""]
    (incr / f"{key}_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": key,
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "teknoloji",
        "faz": 2,
        "dil": "tr",
        "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/teknoloji/katmanlar/{key}",
        "parca_sayisi": len(spec["parcalar"]),
        "updated_utc": _utc(),
        "durum": "hazir",
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

    print("=== Faz 1 md ===")
    added = _write_extra()
    sc = _scan()
    print(f"  raf md={sc['dosya']} char={sc['karakter']}")

    _update_ortak(
        {
            "kaynak_id": "teknoloji_raf_08",
            "kaynak_adi": sc["ad"],
            "yazar": None,
            "ilim_alani": "teknoloji",
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
            "not": "Kutuphane teknoloji rafı; eğitim; saldırı yok.",
        }
    )

    print("=== Faz 2 ===")
    faz2 = []
    for key, spec in KATMANLAR.items():
        man = _write_katman(key, spec)
        faz2.append(man)
        _update_ortak(
            {
                "kaynak_id": man["kaynak_id"],
                "kaynak_adi": man["baslik"],
                "yazar": None,
                "ilim_alani": "teknoloji",
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
                "not": "Teknoloji Faz 2; exploit yok.",
            }
        )
        print(f"  [ok] {key}")

    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in KAVRAMLAR) + "\n",
        encoding="utf-8",
    )

    cat = {
        "domain": "teknoloji",
        "faz": {"1": "kutuphane_08", "2": "guvenlik_yazilim_yz"},
        "updated_utc": _utc(),
        "politika": "2 fazlı. Eğitim. Saldırı/exploit tarifi yok.",
        "faz1_raf": sc,
        "faz2_katmanlar": faz2,
        "sayilar": {
            "md_dosya": sc["dosya"],
            "karakter": sc["karakter"],
            "faz2_katman": len(faz2),
            "kavram": len(KAVRAMLAR),
            "ek_md": added,
        },
    }
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_F2.write_text(
        json.dumps(
            {"domain": "teknoloji_faz2", "updated_utc": _utc(), "katmanlar": faz2},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (OUT / "README.md").write_text(
        "# Teknoloji — 2 fazlı raf\n\n"
        "## Faz 1\n`knowledge/kutuphane/raflar/08_teknoloji`\n\n"
        "## Faz 2\n`guvenlik_hijyen` · `yazilim` · `yz_sinir`\n\n"
        f"MD: **{sc['dosya']}** · Kavram: **{len(KAVRAMLAR)}**\n\n"
        "**Politika:** Eğitim · saldırı/exploit yok\n"
        "**Script:** `faz15_teknoloji_raf_ingest.py` · "
        "**Anlık:** `ruzgar_teknoloji_kutuphane.py`\n",
        encoding="utf-8",
    )
    print(f"\nTOPLAM teknoloji md={sc['dosya']} katman={len(faz2)} kavram={len(KAVRAMLAR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
