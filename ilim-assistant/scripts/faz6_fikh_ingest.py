# -*- coding: utf-8 -*-
"""Fıkıh Faz 6 — 4 mezhep müteber eserler + ilmihal matınları.

Kaynak: arabic-digital-humanities/fiqh (OpenITI / Şâmile kökenli Arapça)
Politika: Fetva yok. Mezhep içi kaynaklı özet + Arapça metin.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "06_fikh"
RAW = STAGE / "raw"
OUT = ROOT / "knowledge" / "ilim" / "din" / "06_fikh"
INCR = OUT / "incremental"
MEZHEP_DIR = OUT / "mezhepler"

CHUNK = 1600
OVERLAP = 120
BATCH_CHUNKS = 20

# download_catalog.json ile aynı kimlikler
WORKS: list[dict[str, Any]] = [
    {"mezhep": "hanafi", "id": "quduri", "file": "0428AlQuduri.Mukhtasar.txt",
     "eser_tr": "Muhtasarü'l-Kudûrî", "eser_ar": "مختصر القدوري",
     "yazar": "el-Kudûrî (ö. 428/1037)", "rol": "matn_ilmihal"},
    {"mezhep": "hanafi", "id": "kasani", "file": "0587IbnMascudCalaDinKasani.BadaicSanaic.txt",
     "eser_tr": "Bedâiu's-sanâi'", "eser_ar": "بدائع الصنائع",
     "yazar": "el-Kâsânî (ö. 587/1191)", "rol": "muteber"},
    {"mezhep": "hanafi", "id": "ikhtiyar", "file": "0683AlMusali.AlIkhtiar.txt",
     "eser_tr": "el-İhtiyâr", "eser_ar": "الاختيار لتعليل المختار",
     "yazar": "el-Mevsılî (ö. 683/1284)", "rol": "matn_ilmihal"},
    {"mezhep": "hanafi", "id": "lubab", "file": "1298AlMaidani.AlLubab.txt",
     "eser_tr": "el-Lübâb", "eser_ar": "اللباب في شرح الكتاب",
     "yazar": "el-Meydânî (ö. 1298/1881)", "rol": "matn_ilmihal"},
    {"mezhep": "hanafi", "id": "ibn_abidin", "file": "1252IbnCabidinDimashqi.RaddMuhtar.txt",
     "eser_tr": "Reddü'l-muhtâr", "eser_ar": "رد المحتار",
     "yazar": "İbn Âbidîn (ö. 1252/1836)", "rol": "muteber"},
    {"mezhep": "maliki", "id": "muwatta", "file": "0179MalikIbnAnas.Muwatta.txt",
     "eser_tr": "el-Muvatta'", "eser_ar": "الموطأ",
     "yazar": "İmam Mâlik (ö. 179/795)", "rol": "temel"},
    {"mezhep": "maliki", "id": "kafi_ibn_abd_barr", "file": "0463IbnCabdBarr.KafiFiFiqh.txt",
     "eser_tr": "el-Kâfî fi'l-fıkh", "eser_ar": "الكافي في فقه أهل المدينة",
     "yazar": "İbn Abdilberr (ö. 463/1071)", "rol": "matn_ilmihal"},
    {"mezhep": "maliki", "id": "qarafi_dhakhira", "file": "0684ShihabDinQarafi.Thakhira.txt",
     "eser_tr": "ez-Zehîra", "eser_ar": "الذخيرة",
     "yazar": "el-Karâfî (ö. 684/1285)", "rol": "muteber"},
    {"mezhep": "maliki", "id": "taj_iklil", "file": "0897IbnYusufCabdariGharnati.TajWaIklilLiMukhtasarKhalil.txt",
     "eser_tr": "et-Tâc ve'l-iklîl", "eser_ar": "التاج والإكليل لمختصر خليل",
     "yazar": "el-Mevvâk (ö. 897/1492)", "rol": "muteber"},
    {"mezhep": "maliki", "id": "dusuqi", "file": "1230Dusuqi.SharhKabir.txt",
     "eser_tr": "Hâşiyetü'd-Düsûkî", "eser_ar": "حاشية الدسوقي",
     "yazar": "ed-Düsûkî (ö. 1230/1815)", "rol": "matn_ilmihal"},
    {"mezhep": "shafii", "id": "umm", "file": "0204Shafici.Umm.txt",
     "eser_tr": "el-Ümm", "eser_ar": "الأم",
     "yazar": "İmam Şâfiî (ö. 204/820)", "rol": "temel"},
    {"mezhep": "shafii", "id": "minhaj", "file": "0676Nawawi.ManahijTalibin.txt",
     "eser_tr": "Minhâcü't-tâlibîn", "eser_ar": "منهاج الطالبين",
     "yazar": "en-Nevevî (ö. 676/1277)", "rol": "matn_ilmihal"},
    {"mezhep": "shafii", "id": "kifayat_akhyar", "file": "0829TaqiDinDimashqiHisni.KifayatAkhyar.txt",
     "eser_tr": "Kifâyetü'l-ahyâr", "eser_ar": "كفاية الأخيار",
     "yazar": "el-Hısnî (ö. 829/1426)", "rol": "matn_ilmihal"},
    {"mezhep": "shafii", "id": "tuhfat", "file": "0973AlHutaimi.TuhfatAlmuhtaj.txt",
     "eser_tr": "Tuhfetü'l-muhtâc", "eser_ar": "تحفة المحتاج",
     "yazar": "İbn Hacer el-Heytemî (ö. 974/1567)", "rol": "muteber"},
    {"mezhep": "shafii", "id": "nihayat", "file": "1004ShamsDinRamli.NihayatMuhtaj.txt",
     "eser_tr": "Nihâyetü'l-muhtâc", "eser_ar": "نهاية المحتاج",
     "yazar": "er-Remlî (ö. 1004/1596)", "rol": "muteber"},
    {"mezhep": "hanbeli", "id": "khiraqi", "file": "0334IbnHusaynKhiraqi.MukhtasarMinMasailIbnHanbal.txt",
     "eser_tr": "Muhtasarü'l-Hırakî", "eser_ar": "مختصر الخرقي",
     "yazar": "el-Hırakî (ö. 334/945)", "rol": "matn_ilmihal"},
    {"mezhep": "hanbeli", "id": "mughni", "file": "0620IbnQudamaMaqdisi.MughniFiFiqh.txt",
     "eser_tr": "el-Muğnî", "eser_ar": "المغني",
     "yazar": "İbn Kudâme (ö. 620/1223)", "rol": "muteber"},
    {"mezhep": "hanbeli", "id": "rawd_murbi", "file": "1051IbnYunusBuhutiHanbali.RawdMurbic.txt",
     "eser_tr": "er-Ravzü'l-murbi'", "eser_ar": "الروض المربع",
     "yazar": "el-Buhûtî (ö. 1051/1641)", "rol": "matn_ilmihal"},
    {"mezhep": "hanbeli", "id": "muntaha", "file": "0972IbnAhmadIbnNajjarHanbali.MuntahaIradat.txt",
     "eser_tr": "Müntehe'l-irâdât", "eser_ar": "منتهى الإرادات",
     "yazar": "İbnü'n-Neccâr (ö. 972/1564)", "rol": "muteber"},
]

MEZHEP_META = {
    "hanafi": {"tr": "Hanefî", "ar": "الحنفي", "imam": "İmam Ebû Hanîfe (ö. 150/767)"},
    "maliki": {"tr": "Mâlikî", "ar": "المالكي", "imam": "İmam Mâlik (ö. 179/795)"},
    "shafii": {"tr": "Şâfiî", "ar": "الشافعي", "imam": "İmam Şâfiî (ö. 204/820)"},
    "hanbeli": {"tr": "Hanbelî", "ar": "الحنبلي", "imam": "İmam Ahmed b. Hanbel (ö. 241/855)"},
}

_KAYNAK = (
    "Kaynak: klasik fıkıh metni (OpenITI / arabic-digital-humanities fiqh corpus, "
    "Şâmile kökenli). Fetva değildir; mezhep içi nüanslar ihtilaflı olabilir."
)


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
    """OpenITI mARkdown / meta satırlarını sadeleştir."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Yaygın OpenITI etiketleri
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


def _write_batches(dest: Path, *, eser_id: str, title: str, yazar: str, mezhep: str, chunks: list[str]) -> int:
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    n_batch = 0
    for i in range(0, len(chunks), BATCH_CHUNKS):
        n_batch += 1
        part = chunks[i : i + BATCH_CHUNKS]
        body_parts = [
            f"# {title} — paket {n_batch:04d}",
            "",
            f"Mezhep: {mezhep} · Yazar: {yazar}",
            f"Kaynak: {_KAYNAK}",
            "",
        ]
        for j, ch in enumerate(part, 1):
            body_parts.append(f"## parça {i + j}")
            body_parts.append("")
            body_parts.append(ch)
            body_parts.append("")
        (incr / f"{eser_id}_batch_{n_batch:04d}.md").write_text(
            "\n".join(body_parts), encoding="utf-8"
        )
    return n_batch


def _kavram_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "id": "fikh",
            "baslik": "fıkıh",
            "aliases": ["fikih", "fikh nedir", "fıkıh nedir", "islam hukuku"],
            "metin": (
                "Fıkıh (فقه): şer'î amelî hükümleri delillerinden çıkarma ilmi. "
                "İbadât, muâmelât, ukûbât ve aile hukukunu kapsar. Rüzgar dört "
                "Sünnî mezhebin müteber metinlerini ayrı raflarda tutar; fetva vermez."
            ),
        },
        {
            "id": "mezhep",
            "baslik": "mezhep",
            "aliases": ["mezhep nedir", "dört mezhep", "mezahib"],
            "metin": (
                "Mezhep: müctehid imamın fıkhî yöntem ve görüşler bütünü. "
                "Dört büyük Sünnî mezhep: Hanefî, Mâlikî, Şâfiî, Hanbelî. "
                "Hepsi Ehl-i sünnet çerçevesindedir; ihtilaflar usûl ve "
                "içtihat farkından doğar."
            ),
        },
        {
            "id": "hanafi",
            "baslik": "hanefi",
            "aliases": ["hanefî", "ebu hanife", "ebû hanîfe", "hanafi mezhebi"],
            "metin": (
                "Hanefî mezhebi: İmam Ebû Hanîfe (ö. 150/767) ve ashâbı "
                "(Ebû Yûsuf, Muhammed eş-Şeybânî). Rey ve kıyasa geniş yer; "
                "Osmanlı ve Anadolu'da yaygın. Matın/ilmihal: Kudûrî, İhtiyâr, "
                "Lübâb; muteber: Bedâiu's-sanâi', Reddü'l-muhtâr."
            ),
        },
        {
            "id": "maliki",
            "baslik": "maliki",
            "aliases": ["mâlikî", "imam malik", "maliki mezhebi"],
            "metin": (
                "Mâlikî mezhebi: İmam Mâlik (ö. 179/795). Medine ameli önemli. "
                "Kuzey Afrika ve Mağrib'de yaygın. Temel: Muvatta'; ilmihal: "
                "Kâfî (İbn Abdilberr), Düsûkî; muteber: Zehîra, Tâc ve İklîl."
            ),
        },
        {
            "id": "shafii",
            "baslik": "safii",
            "aliases": ["şafii", "şâfiî", "imam safii", "shafii"],
            "metin": (
                "Şâfiî mezhebi: İmam Şâfiî (ö. 204/820). Usûlde dengeli yol. "
                "Mısır, Levant, Güneydoğu Asya. Temel: el-Ümm; ilmihal: "
                "Minhâc (Nevevî), Kifâyetü'l-ahyâr; muteber: Tuhfe, Nihâye."
            ),
        },
        {
            "id": "hanbeli",
            "baslik": "hanbeli",
            "aliases": ["hanbelî", "ahmed b hanbel", "hanbali mezhebi"],
            "metin": (
                "Hanbelî mezhebi: İmam Ahmed b. Hanbel (ö. 241/855). "
                "Hadise sıkı bağlılık vurgusu. Arap yarımadasında yaygın. "
                "Matın: Hırakî, Ravzü'l-murbi'; muteber: Muğnî, Müntehâ."
            ),
        },
        {
            "id": "ilmihal",
            "baslik": "ilmihal",
            "aliases": ["ilmihal nedir", "ilm-i hal", "pratik fıkıh"],
            "metin": (
                "İlmihal: günlük ibadet ve muamelât için sadeleştirilmiş fıkıh "
                "özeti. Klasik karşılığı «matın»dır (Kudûrî, Minhâc, Hırakî…). "
                "Rüzgar'da her mezhebin matın/ilmihal raftı ayrıdır; modern "
                "telifli TR ilmihaller `bekleyen_tr/` ile eklenir."
            ),
        },
        {
            "id": "ibadat",
            "baslik": "ibadat",
            "aliases": ["ibadetler", "ibâdât", "taharet abdest namaz"],
            "metin": (
                "İbâdât: tahâret, namaz, zekât, oruç, hac gibi kulluk "
                "hükümleri. Mezhep kitaplarında genellikle ilk kitâblardır."
            ),
        },
        {
            "id": "muamelat",
            "baslik": "muamelat",
            "aliases": ["muâmelât", "alışveriş", "akitler"],
            "metin": (
                "Muâmelât: alışveriş, kira, şirket, vekâlet vb. insanlar "
                "arası hukuki işlemler. Klasik fıkıh kitaplarında ayrı "
                "kitâblar halinde işlenir."
            ),
        },
        {
            "id": "ictihad",
            "baslik": "ictihad",
            "aliases": ["içtihat", "müctehid", "taklid"],
            "metin": (
                "İçtihad: müctehidin delilden hüküm çıkarması. Taklid: "
                "müctehid olmayan kişinin bir mezhebe uyması. Rüzgar "
                "müctehid hükmü vermez; kaynak gösterir."
            ),
        },
        {
            "id": "usul_fikh",
            "baslik": "usul fikh",
            "aliases": ["usûl-i fıkıh", "usulü fıkıh", "fıkıh usulü"],
            "metin": (
                "Usûl-i fıkıh: hüküm çıkarma yöntemleri (kitap, sünnet, icmâ, "
                "kıyas…). Furû' fıkıh ise bu usûlle üretilen ayrıntılı "
                "hükümlerdir. Bu rafta furû' ağırlıklıdır."
            ),
        },
        {
            "id": "quduri_eser",
            "baslik": "kuduri",
            "aliases": ["kudûrî", "muhtasar kuduri", "quduri"],
            "metin": (
                "Muhtasarü'l-Kudûrî: Hanefî matınların en meşhurlarından. "
                "İbadât ve muâmelâtı özlü verir; Lübâb gibi şerhlerle okunur. "
                "Rüzgar raftı: `hanafi/quduri`."
            ),
        },
        {
            "id": "minhaj_eser",
            "baslik": "minhac",
            "aliases": ["minhâc", "minhacü talibin", "nevevi minhac"],
            "metin": (
                "Minhâcü't-tâlibîn (Nevevî): Şâfiî mezhebinde mu'temed matın. "
                "Tuhfe ve Nihâye gibi şerhlerin omurgasıdır. Rüzgar: `shafii/minhaj`."
            ),
        },
        {
            "id": "mughni_eser",
            "baslik": "mugni",
            "aliases": ["muğnî", "ibn kudame", "el mugni"],
            "metin": (
                "el-Muğnî (İbn Kudâme): Hanbelî ansiklopedik furû'. Diğer "
                "mezhep görüşlerini de karşılaştırmalı verir. Rüzgar: `hanbeli/mughni`."
            ),
        },
        {
            "id": "muwatta_eser",
            "baslik": "muvatta",
            "aliases": ["muvatta nedir", "el muvatta", "malik muvatta"],
            "metin": (
                "el-Muvatta': İmam Mâlik'in hadis+fıkıh derlemesi; Mâlikî "
                "geleneğin temeli. Rüzgar: `maliki/muwatta`."
            ),
        },
        {
            "id": "rawd_eser",
            "baslik": "ravzul murbi",
            "aliases": ["ravzü'l-murbi", "rawd murbi", "buhuti"],
            "metin": (
                "er-Ravzü'l-murbi' (Buhûtî): Zâdü'l-müstakni' şerhi; Hanbelî "
                "pratik ilmihal düzeyinde yaygın matın. Rüzgar: `hanbeli/rawd_murbi`."
            ),
        },
        {
            "id": "ibn_abidin_eser",
            "baslik": "ibn abidin",
            "aliases": ["ibn âbidîn", "reddul muhtar", "haşiye ibn abidin"],
            "metin": (
                "Reddü'l-muhtâr: İbn Âbidîn'in Hanefî hâşiyesi; geç dönem "
                "Hanefî fetva uygulamasında çok başvurulan muteber kaynaktır. "
                "Rüzgar: `hanafi/ibn_abidin`."
            ),
        },
        {
            "id": "fetva_degil",
            "baslik": "fetva",
            "aliases": ["fetva nedir", "ruzgar fetva"],
            "metin": (
                "Fetva: yetkili müftünün kişiye özel hükmü. Rüzgar fetva "
                "vermez; klasik metin ve kavram özeti sunar. Kişisel hüküm "
                "için ehil âlime başvurulur."
            ),
        },
    ]
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "collection": "din_06_fikh_kavram",
                "baslik": r["baslik"],
                "aliases": r["aliases"],
                "metin": r["metin"],
                "kaynak_notu": _KAYNAK,
            }
        )
    return out


def _write_tr_layers(rows: list[dict[str, Any]]) -> None:
    INCR.mkdir(parents=True, exist_ok=True)
    kav_path = OUT / "kavramlar_fikh.jsonl"
    with kav_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    kav_md = ["# Fıkıh kavramları (TR)", ""]
    for row in rows:
        kav_md += [f"## {row['baslik']}", "", row["metin"], "", f"_{row['kaynak_notu']}_", ""]
    (INCR / "fikh_kavramlar_tr.md").write_text("\n".join(kav_md), encoding="utf-8")

    ilmihal = """# Dört mezhep — ilmihal / matın rehberi (TR)

Rüzgar **fetva vermez**. Aşağısı klasik matınların hangi mezhepte «pratik rehber» sayıldığının özetidir.

## Hanefî
- **Kudûrî**: kısa matın (ibadet + muamelât)
- **İhtiyâr** (Mevsılî): Muhtâr şerhi; ders kitabı niteliği
- **Lübâb** (Meydânî): Kudûrî şerhi — ilmihal okuma yolu
- **Reddü'l-muhtâr**: geç dönem muteber hâşiye (uygulama incelikleri)

## Mâlikî
- **Muvatta'**: temel (hadis+fıkıh)
- **el-Kâfî** (İbn Abdilberr): Medine fıkhı özeti
- **Düsûkî hâşiyesi**: Halîl çizgisi pratik şerh
- **Zehîra / Tâc ve İklîl**: geniş muteber kaynak

## Şâfiî
- **Minhâc** (Nevevî): mu'temed matın
- **Kifâyetü'l-ahyâr**: öğrenci/ilmihal düzeyi
- **Tuhfe / Nihâye**: şerh zirvesi (mu'temed görüşler)

## Hanbelî
- **Hırakî muhtasarı**: erken matın
- **Ravzü'l-murbi'**: Zâd şerhi — yaygın pratik metin
- **Muğnî**: ansiklopedik karşılaştırma
- **Müntehâ**: geç dönem matın

_Modern Türkçe ilmihaller (telifli) `bekleyen_tr/` ile eklenir._
"""
    (INCR / "fikh_ilmihal_rehberi_tr.md").write_text(ilmihal, encoding="utf-8")

    tarih = """# Fıkıh mezheplerinin oluşumu (kısa)

1. **Sahâbe–tâbiîn**: Medine ve Irak fıkıh çevreleri.
2. **Müctehid imamlar**: Ebû Hanîfe, Mâlik, Şâfiî, Ahmed — usûl ve furû' sistemleşti.
3. **Ashâbü'l-mezheb**: talebeler matın, şerh, hâşiye zinciri kurdu.
4. **Mu'temedleşme**: her mezhepte «son söz» kabul edilen matın/şerhler (Minhâc, Kudûrî, Zâd…).
5. **Rüzgar**: dört mezhep ayrı raf; soruda mezhep adı varsa o raftan, yoksa kavram katmanı.

Fetva değildir.
"""
    (INCR / "fikh_mezhep_tarihce_tr.md").write_text(tarih, encoding="utf-8")


def _ingest_work(w: dict[str, Any]) -> dict[str, Any] | None:
    src = RAW / w["file"]
    if not src.is_file() or src.stat().st_size < 1000:
        print(f"  [skip] yok/küçük: {w['file']}")
        return None
    mezhep = w["mezhep"]
    dest = MEZHEP_DIR / mezhep / w["id"]
    dest.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8", errors="replace")
    chunks = _chunk(text)
    n = _write_batches(
        dest,
        eser_id=w["id"],
        title=w["eser_tr"],
        yazar=w["yazar"],
        mezhep=MEZHEP_META[mezhep]["tr"],
        chunks=chunks,
    )
    man = {
        "eser_id": w["id"],
        "mezhep": mezhep,
        "mezhep_tr": MEZHEP_META[mezhep]["tr"],
        "eser_tr": w["eser_tr"],
        "eser_ar": w["eser_ar"],
        "yazar": w["yazar"],
        "rol": w["rol"],
        "collection": f"din_06_fikh_{mezhep}_{w['id']}",
        "kaynak": "arabic-digital-humanities/fiqh",
        "source_file": w["file"],
        "sha256": _sha(src),
        "char_count": len(text),
        "chunk_count": len(chunks),
        "batch_sayisi": n,
        "updated_utc": _utc(),
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  [ok] {mezhep}/{w['id']}: {len(chunks)} chunk, {n} batch")
    return man


def main() -> int:
    print("=== Faz 6 Fıkıh ingest ===")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = _kavram_rows()
    _write_tr_layers(rows)
    print(f"kavramlar: {len(rows)}")

    manifests: list[dict[str, Any]] = []
    for w in WORKS:
        print(f"\n>> {w['mezhep']}/{w['id']}")
        man = _ingest_work(w)
        if man:
            manifests.append(man)

    catalog = {
        "domain": "din_06_fikh",
        "mezhepler": list(MEZHEP_META.keys()),
        "kaynak": "arabic-digital-humanities/fiqh (OpenITI)",
        "updated_utc": _utc(),
        "politika": "Fetva yok. Kaynaklı özet + Arapça metin.",
        "eserler": manifests,
        "sayilar": {
            "eser": len(manifests),
            "chunk_toplam": sum(int(m.get("chunk_count") or 0) for m in manifests),
            "mezhep": {
                k: sum(1 for m in manifests if m["mezhep"] == k) for k in MEZHEP_META
            },
        },
    }
    (OUT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    readme = f"""# Din / 06 — Fıkıh kütüphanesi (4 mezhep)

**Politika:** Fetva yok. Klasik Arapça metin + TR kavram/ilmihal rehberi.

## Mezhep rafları

| Mezhep | Klasör | Temsilî matın / ilmihal | Muteber |
|--------|--------|-------------------------|---------|
| Hanefî | `mezhepler/hanafi/` | Kudûrî, İhtiyâr, Lübâb | Bedâi', Reddü'l-muhtâr |
| Mâlikî | `mezhepler/maliki/` | Kâfî, Düsûkî | Muvatta', Zehîra, Tâc |
| Şâfiî | `mezhepler/shafii/` | Minhâc, Kifâyetü'l-ahyâr | Ümm, Tuhfe, Nihâye |
| Hanbelî | `mezhepler/hanbeli/` | Hırakî, Ravzü'l-murbi' | Muğnî, Müntehâ |

## TR katman

- `kavramlar_fikh.jsonl`
- `incremental/fikh_kavramlar_tr.md`
- `incremental/fikh_ilmihal_rehberi_tr.md`
- `incremental/fikh_mezhep_tarihce_tr.md`

**Kaynak:** [arabic-digital-humanities/fiqh](https://github.com/arabic-digital-humanities/fiqh) (OpenITI).  
**Modül:** `ruzgar_fikh_kutuphane` · İncegest: `scripts/faz6_fikh_ingest.py`

Yüklenen eser: **{len(manifests)}** · chunk: **{catalog['sayilar']['chunk_toplam']}**
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(f"\nTOPLAM eser={len(manifests)} chunk={catalog['sayilar']['chunk_toplam']}")
    print(f"çıkış: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
