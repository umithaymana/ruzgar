# -*- coding: utf-8 -*-
"""Psikoloji Faz 2 — nefs güçleri / ahlâk / klasik–klinik ayrım.

Faz 1 OpenITI korunur. Klinik teşhis/tedavi değildir. Fetva yok.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "psikoloji"
KAT = OUT / "katmanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_psikoloji.jsonl"
CATALOG = OUT / "catalog.json"
CATALOG_F2 = OUT / "catalog_faz2.json"

FAZ1 = [
    {
        "id": "psikoloji",
        "baslik": "psikoloji",
        "aliases": [
            "psikoloji nedir",
            "nefs ilmi",
            "ilm-i nefs",
            "islam psikolojisi",
            "islâm psikolojisi",
        ],
        "metin": (
            "Bu rafta klasik İslâm nefs/ahlâk psikolojisi vardır (İbn Sînâ nefs, Gazâlî Mîzân). "
            "Faz 2: nefs güçleri, idrak, ahlâk–nefs ve klasik/klinik ayrım. "
            "Modern klinik teşhis veya terapi değildir. Krizde profesyonel yardım gerekir."
        ),
        "kaynak_notu": "Psikoloji — Faz 1+2; klinik değil.",
    },
    {
        "id": "nefs",
        "baslik": "nefs",
        "aliases": ["nefis", "nefs nedir", "ruh nefs", "nefs terbiyesi"],
        "metin": (
            "Nefs: klasik literatürde idrak ve arzu gücü; terbiye ve ahlâk konusu. "
            "Şifâ Kitâbü’n-Nefs ve Mîzânü’l-amel bu çerçevededir. Klinik ruh sağlığı teşhisi değildir."
        ),
        "kaynak_notu": "Psikoloji — kavram.",
    },
    {
        "id": "ibn_sina_shifa_nafs",
        "baslik": "sifa nafs",
        "aliases": ["sifa nafs", "şifâ nefs", "shifa nafs", "kitabun nefs", "ibn sina nefs"],
        "metin": (
            "İbn Sînâ Şifâ — Kitâbü’n-Nefs: idrak, nefis güçleri. Klasik nefs ilmi; klinik değil."
        ),
        "kaynak_notu": "Psikoloji Faz 1 — OpenITI.",
    },
    {
        "id": "ibn_sina_marifat_nafs",
        "baslik": "marifat nafs",
        "aliases": [
            "marifat nafs",
            "ma'rifetü nefs",
            "nefsinatiqa",
            "nâtıka nefs",
            "konuşan nefis",
        ],
        "metin": "İbn Sînâ nâtıka nefis risalesi. Klasik; klinik tedavi değildir.",
        "kaynak_notu": "Psikoloji Faz 1 — OpenITI.",
    },
    {
        "id": "gazali_mizan_amal",
        "baslik": "mizan amal",
        "aliases": [
            "mizan amal",
            "mizanul amal",
            "mîzânü'l-amel",
            "amel terazisi",
            "gazali mizan",
        ],
        "metin": (
            "Gazâlî Mîzânü’l-amel: ahlâk, nefis terbiyesi, amelin ölçüsü. "
            "Klasik ahlâk psikolojisi; klinik değildir."
        ),
        "kaynak_notu": "Psikoloji Faz 1 — OpenITI.",
    },
    {
        "id": "ibn_sina_mahiya_ishq",
        "baslik": "mahiyetul isk",
        "aliases": [
            "mahiyetul isk",
            "mahiyyetü'l-işk",
            "ibn sina ask",
            "risale isk",
            "aşk risalesi sina",
        ],
        "metin": (
            "İbn Sînâ aşk/işk mahiyeti risalesi (metafizik–psikoloji). "
            "Klinik ilişki terapisi değildir."
        ),
        "kaynak_notu": "Psikoloji Faz 1 — OpenITI.",
    },
]

FAZ2 = [
    {
        "id": "nefs_gucleri",
        "baslik": "nefs gucleri",
        "aliases": [
            "nefs gucleri",
            "nefis güçleri",
            "kuvve",
            "kuvve-i akile",
            "hayvani nefs",
            "nebati nefs",
        ],
        "metin": (
            "Nefs güçleri (özet): nebâtî (beslenme/büyüme), hayvanî (duyu/hareket), "
            "insânî/nâtıka (akıl). İbn Sînâ nefs kitabında bu tasnif çerçevesi işlenir. "
            "Klinik tanı değildir."
        ),
        "kaynak_notu": "Psikoloji Faz 2.",
    },
    {
        "id": "idrak",
        "baslik": "idrak",
        "aliases": ["idrak", "algı", "his", "duyu", "tahayyul", "vehim"],
        "metin": (
            "İdrak: duyusal ve içsel algı süreçleri. Klasik metinlerde his, tahayyül, "
            "vehim, akıl mertebeleri anılır. Modern bilişsel psikolojiyle birebir aynı "
            "değildir; tarihî çerçevedir."
        ),
        "kaynak_notu": "Psikoloji Faz 2.",
    },
    {
        "id": "ahlak_nefs",
        "baslik": "ahlak ve nefs",
        "aliases": [
            "ahlak nefs",
            "nefs terbiyesi",
            "tezkiye",
            "ahlak psikolojisi",
        ],
        "metin": (
            "Ahlâk–nefs: erdem ve kötü huyların terbiyesi. Gazâlî Mîzân bu bağın "
            "klasik örneklerindendir. Fetva ve klinik terapi değildir."
        ),
        "kaynak_notu": "Psikoloji Faz 2.",
    },
    {
        "id": "duygu_klasik",
        "baslik": "duygu klasik",
        "aliases": ["duygu", "ofke", "öfke", "korku", "sevgi", "huzn", "neşe"],
        "metin": (
            "Klasik duygu çerçevesi: öfke, korku, sevgi, hüzün vb. ahlâk ve nefs "
            "literatüründe ele alınır. DSM/tanı sistemi değildir."
        ),
        "kaynak_notu": "Psikoloji Faz 2; klinik değil.",
    },
    {
        "id": "klasik_vs_klinik",
        "baslik": "klasik ve klinik",
        "aliases": [
            "klinik psikoloji",
            "modern psikoloji",
            "terapi",
            "teshis",
            "teşhis",
            "depresyon tedavisi",
        ],
        "metin": (
            "Klasik nefs ilmi ≠ modern klinik psikoloji/psikiyatri. Rüzgar hastalık "
            "teşhisi koymaz, ilaç/terapi önermez. Kriz ve hastalık için ehil uzmana "
            "başvurulmalıdır."
        ),
        "kaynak_notu": "Psikoloji Faz 2 — uyarı.",
    },
    {
        "id": "akil_nefs",
        "baslik": "akil ve nefs",
        "aliases": ["akil", "akıl", "natiqa", "nâtıka", "akli nefs"],
        "metin": (
            "Nâtıka/aklî nefis: düşünme ve konuşma gücüyle anılır. "
            "Ma’rifetü’n-nefsi’n-nâtıka risalesi bu çerçevededir."
        ),
        "kaynak_notu": "Psikoloji Faz 2.",
    },
    {
        "id": "isk_ask",
        "baslik": "isk ask",
        "aliases": ["isk", "işk", "ask klasik", "aşk klasik", "mahabbet"],
        "metin": (
            "İşk/aşk: klasik risalelerde metafizik ve nefsî bir konu olarak işlenir "
            "(İbn Sînâ risalesi). Modern çift terapisi değildir."
        ),
        "kaynak_notu": "Psikoloji Faz 2.",
    },
]

KATMANLAR = {
    "nefs_gucleri": {
        "baslik": "Nefs güçleri",
        "kaynak_id": "psikoloji_katman_gucler",
        "parcalar": [
            (
                "Üçlü tasnif (özet)",
                "Nebâtî, hayvanî, insânî/nâtıka. Şifâ Kitâbü’n-Nefs bu ayrımı işler. "
                "Klinik beyin haritası değildir.",
            ),
            (
                "İdrak mertebeleri",
                "Dış duyu, ortak duyu, tahayyül, vehim, akıl — eğitim özeti; "
                "modern bilişsel modele birebir eşlenmez.",
            ),
        ],
    },
    "ahlak_bag": {
        "baslik": "Ahlâk ve nefs bağı",
        "kaynak_id": "psikoloji_katman_ahlak",
        "parcalar": [
            (
                "Terbiye",
                "Nefs terbiyesi ahlâkın merkezidir. Mîzânü’l-amel amel ve huyları tartar.",
            ),
            (
                "Komşu raflar",
                "Felsefe ahlâkı, tasavvuf ahlâkı ve bu raf birbirini tamamlar; "
                "fetva makamı değildir.",
            ),
        ],
    },
    "klinik_sinir": {
        "baslik": "Klasik / klinik sınır",
        "kaynak_id": "psikoloji_katman_sinir",
        "parcalar": [
            (
                "Ne değildir",
                "Tanı koyma, ilaç, kriz müdahalesi, DSM eşlemesi yoktur. "
                "Acil durumda sağlık kuruluşuna gidilir.",
            ),
            (
                "Ne vardır",
                "Klasik nefs metinleri (OpenITI) + kavram katmanı. Eğitim ve tarihî çerçeve.",
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
        "Kaynak: Rüzgar psikoloji Faz 2. Klinik teşhis değildir. Fetva yok.",
        "",
    ]
    for i, (t, x) in enumerate(spec["parcalar"], 1):
        body += [f"## {i}. {t}", "", x, ""]
    (incr / f"{key}_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": key,
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "psikoloji",
        "faz": 2,
        "dil": "tr",
        "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/psikoloji/katmanlar/{key}",
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
        "ilim_alani": "psikoloji",
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
        "not": "Psikoloji Faz 2; klinik değil.",
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
        "domain": "psikoloji_nefs",
        "eserler": [],
    }
    cat["faz"] = {"1": "openiti_nefs", "2": "gucler_ahlak_sinir"}
    cat["faz2_katmanlar"] = faz2_rows
    cat["updated_utc"] = _utc()
    cat["politika"] = (
        "2 fazlı. Klasik nefs/ahlâk. Klinik teşhis/tedavi değildir. "
        "Fetva yok. Sayfa uydurma yasak."
    )
    cat.setdefault("sayilar", {})
    cat["sayilar"]["faz2_katman"] = len(faz2_rows)
    cat["sayilar"]["kavram"] = len(all_kav)
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_F2.write_text(
        json.dumps(
            {
                "domain": "psikoloji_faz2",
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
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else "# Psikoloji\n"
    if "Faz 2" not in prev or "faz11b" not in prev:
        prev = prev.rstrip() + (
            "\n\n## Faz 2\n"
            "- `katmanlar/nefs_gucleri` · `ahlak_bag` · `klinik_sinir`\n"
            f"- Kavram toplam: **{len(all_kav)}**\n"
            "- Script: `faz11b_psikoloji_faz2_ingest.py`\n"
            "- **Uyarı:** Klinik teşhis değildir.\n"
        )
        readme.write_text(prev + "\n", encoding="utf-8")

    print(f"\nTOPLAM psikoloji faz2={len(faz2_rows)} kavram={len(all_kav)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
