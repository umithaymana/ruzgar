# -*- coding: utf-8 -*-
"""Download priority Kutub al-madhahib from arabic-digital-humanities/fiqh."""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "06_fikh"
RAW = STAGE / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://raw.githubusercontent.com/arabic-digital-humanities/fiqh/master/txt"
API = "https://api.github.com/repos/arabic-digital-humanities/fiqh/contents/txt"

# mezhep → (eser_id, github_filename, eser_tr, yazar, rol)
WORKS: list[dict] = [
    # Hanafi
    {"mezhep": "hanafi", "id": "quduri", "file": "0428AlQuduri.Mukhtasar.txt",
     "eser_tr": "Muhtasarü'l-Kudûrî", "yazar": "el-Kudûrî (ö. 428/1037)", "rol": "matn_ilmihal"},
    {"mezhep": "hanafi", "id": "kasani", "file": "0587IbnMascudCalaDinKasani.BadaicSanaic.txt",
     "eser_tr": "Bedâiu's-sanâi'", "yazar": "el-Kâsânî (ö. 587/1191)", "rol": "muteber"},
    {"mezhep": "hanafi", "id": "ikhtiyar", "file": "0683AlMusali.AlIkhtiar.txt",
     "eser_tr": "el-İhtiyâr", "yazar": "el-Mevsılî (ö. 683/1284)", "rol": "matn_ilmihal"},
    {"mezhep": "hanafi", "id": "lubab", "file": "1298AlMaidani.AlLubab.txt",
     "eser_tr": "el-Lübâb fî şerhi'l-Kitâb", "yazar": "el-Meydânî (ö. 1298/1881)", "rol": "matn_ilmihal"},
    {"mezhep": "hanafi", "id": "ibn_abidin", "file": "1252IbnCabidinDimashqi.RaddMuhtar.txt",
     "eser_tr": "Reddü'l-muhtâr", "yazar": "İbn Âbidîn (ö. 1252/1836)", "rol": "muteber"},
    # Maliki
    {"mezhep": "maliki", "id": "muwatta", "file": "0179MalikIbnAnas.Muwatta.txt",
     "eser_tr": "el-Muvatta'", "yazar": "İmam Mâlik (ö. 179/795)", "rol": "temel"},
    {"mezhep": "maliki", "id": "kafi_ibn_abd_barr", "file": "0463IbnCabdBarr.KafiFiFiqh.txt",
     "eser_tr": "el-Kâfî fi'l-fıkh", "yazar": "İbn Abdilberr (ö. 463/1071)", "rol": "matn_ilmihal"},
    {"mezhep": "maliki", "id": "qarafi_dhakhira", "file": "0684ShihabDinQarafi.Thakhira.txt",
     "eser_tr": "ez-Zehîra", "yazar": "el-Karâfî (ö. 684/1285)", "rol": "muteber"},
    {"mezhep": "maliki", "id": "taj_iklil", "file": "0897IbnYusufCabdariGharnati.TajWaIklilLiMukhtasarKhalil.txt",
     "eser_tr": "et-Tâc ve'l-iklîl (Muhtasar Halîl)", "yazar": "el-Mevvâk (ö. 897/1492)", "rol": "muteber"},
    {"mezhep": "maliki", "id": "dusuqi", "file": "1230Dusuqi.SharhKabir.txt",
     "eser_tr": "Hâşiyetü'd-Düsûkî", "yazar": "ed-Düsûkî (ö. 1230/1815)", "rol": "matn_ilmihal"},
    # Shafi
    {"mezhep": "shafii", "id": "umm", "file": "0204Shafici.Umm.txt",
     "eser_tr": "el-Ümm", "yazar": "İmam Şâfiî (ö. 204/820)", "rol": "temel"},
    {"mezhep": "shafii", "id": "minhaj", "file": "0676Nawawi.ManahijTalibin.txt",
     "eser_tr": "Minhâcü't-tâlibîn", "yazar": "en-Nevevî (ö. 676/1277)", "rol": "matn_ilmihal"},
    {"mezhep": "shafii", "id": "kifayat_akhyar", "file": "0829TaqiDinDimashqiHisni.KifayatAkhyar.txt",
     "eser_tr": "Kifâyetü'l-ahyâr", "yazar": "el-Hısnî (ö. 829/1426)", "rol": "matn_ilmihal"},
    {"mezhep": "shafii", "id": "tuhfat", "file": "0973AlHutaimi.TuhfatAlmuhtaj.txt",
     "eser_tr": "Tuhfetü'l-muhtâc", "yazar": "İbn Hacer el-Heytemî (ö. 974/1567)", "rol": "muteber"},
    {"mezhep": "shafii", "id": "nihayat", "file": "1004ShamsDinRamli.NihayatMuhtaj.txt",
     "eser_tr": "Nihâyetü'l-muhtâc", "yazar": "er-Remlî (ö. 1004/1596)", "rol": "muteber"},
    # Hanbali
    {"mezhep": "hanbeli", "id": "khiraqi", "file": "0334IbnHusaynKhiraqi.MukhtasarMinMasailIbnHanbal.txt",
     "eser_tr": "Muhtasarü'l-Hırakî", "yazar": "el-Hırakî (ö. 334/945)", "rol": "matn_ilmihal"},
    {"mezhep": "hanbeli", "id": "mughni", "file": "0620IbnQudamaMaqdisi.MughniFiFiqh.txt",
     "eser_tr": "el-Muğnî", "yazar": "İbn Kudâme (ö. 620/1223)", "rol": "muteber"},
    {"mezhep": "hanbeli", "id": "rawd_murbi", "file": "1051IbnYunusBuhutiHanbali.RawdMurbic.txt",
     "eser_tr": "er-Ravzü'l-murbi'", "yazar": "el-Buhûtî (ö. 1051/1641)", "rol": "matn_ilmihal"},
    {"mezhep": "hanbeli", "id": "muntaha", "file": "0972IbnAhmadIbnNajjarHanbali.MuntahaIradat.txt",
     "eser_tr": "Müntehe'l-irâdât", "yazar": "İbnü'n-Neccâr (ö. 972/1564)", "rol": "muteber"},
]

UA = {"User-Agent": "RuzgarFiqhIngest/1.0"}


def fetch(url: str, dest: Path, *, timeout: int = 600) -> int:
    if dest.is_file() and dest.stat().st_size > 10_000:
        print(f"  [skip] {dest.name} ({dest.stat().st_size/1e6:.1f} MB)")
        return dest.stat().st_size
    req = urllib.request.Request(url, headers=UA)
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            dest.write_bytes(data)
            print(f"  [ok] {dest.name} ({len(data)/1e6:.1f} MB)")
            return len(data)
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"indirme başarısız: {url} ({last})")


def main() -> int:
    catalog = []
    print("=== Fıkıh indirme (4 mezhep) ===")
    for w in WORKS:
        dest = RAW / w["file"]
        url = f"{BASE}/{w['file']}"
        print(f">> {w['mezhep']}/{w['id']}")
        size = fetch(url, dest)
        catalog.append({**w, "bytes": size, "local": str(dest.relative_to(ROOT)).replace("\\", "/")})
        time.sleep(0.3)
    (STAGE / "download_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(c["bytes"] for c in catalog)
    print(f"TOPLAM: {total/1e6:.1f} MB · {len(catalog)} eser")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
