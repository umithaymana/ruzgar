#!/usr/bin/env python
"""D1 — Şâmile / din kütüphanesi kapsam envanteri (SALT OKUMA).

Hiçbir eser eklemez/indirmez; yalnız `knowledge/ilim/din/shamela/**/manifest.json` ve
`.rag_index/shards/shamela/registry.json` okur. Çekirdek eser listesi VERİ dosyasıdır
(`eval/din/cekirdek_eserler.json`): üretim kodu bu listeye bağlı değildir, yalnız rapor içindir.

Kullanım:
  python scripts/din_kapsam_envanter.py rapor          # docs/DIN_KAPSAM_ENVANTERI_<tarih>.md
  python scripts/din_kapsam_envanter.py dok            # tüm eser başlıklarını TSV dök (inceleme)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "knowledge" / "ilim" / "din" / "shamela"
REG = ROOT / ".rag_index" / "shards" / "shamela" / "registry.json"
CEKIRDEK = ROOT / "eval" / "din" / "cekirdek_eserler.json"
DOCS = ROOT.parent / "docs"

# Kategori -> katman (rapor sınıflaması; Mimar'ın 6b matrisi)
KATMAN = {
    "cekirdek": ["01_akaid", "02_firak_redler", "03_tefsir", "04_kuran_ilim_usul", "05_tecvid_kiraat",
                 "06_hadis_sunen", "07_hadis_serh", "08_tahric_etraf", "09_ilel_sual", "10_hadis_ilimleri"],
    "genis": ["11_usul_fikih", "12_fikih_kaideler", "13_mantik", "14_hanefi", "15_maliki", "16_safii",
              "17_hanbeli", "18_genel_fikih", "19_fikhi_meseleler", "20_siyaset_kaza", "21_feraiz",
              "22_fetvalar", "23_rekaik_adab", "24_siyer"],
    "tarih": ["25_tarih", "26_teracim", "27_ensab", "28_buldan"],
    "dil_diger": ["29_dil", "30_garib_lugat", "31_nahiv_sarf", "32_edebiyat", "33_aruz", "34_divanlar",
                  "35_belagat", "36_cevami", "37_fihrist", "38_tip", "39_genel", "40_diger"],
}
KATMAN_AD = {"cekirdek": "Çekirdek (Kur'an · tefsir · akaid · hadis)",
             "genis": "Geniş (fıkıh · usûl · rekâik/tasavvuf-ahlâk · siyer · kelâm-mantık)",
             "tarih": "Tarih (tarih · terâcim · ensâb · büldân)",
             "dil_diger": "Dil · edebiyat · genel · diğer"}
KAT_AD = {
    "01_akaid": "Akaid", "02_firak_redler": "Fırak ve reddiyeler", "03_tefsir": "Tefsir",
    "04_kuran_ilim_usul": "Kur'ân ilimleri", "05_tecvid_kiraat": "Tecvid ve kırâat",
    "06_hadis_sunen": "Hadis (kütüb/sünen/müsned)", "07_hadis_serh": "Hadis şerhleri",
    "08_tahric_etraf": "Tahrîc ve etrâf", "09_ilel_sual": "İlel ve suâlât", "10_hadis_ilimleri": "Hadis ilimleri",
    "11_usul_fikih": "Usûl-i fıkıh", "12_fikih_kaideler": "Fıkıh kâideleri", "13_mantik": "Mantık",
    "14_hanefi": "Hanefî fıkhı", "15_maliki": "Mâlikî fıkhı", "16_safii": "Şâfiî fıkhı", "17_hanbeli": "Hanbelî fıkhı",
    "18_genel_fikih": "Genel/karşılaştırmalı fıkıh", "19_fikhi_meseleler": "Fıkhî meseleler",
    "20_siyaset_kaza": "Siyâset ve kazâ", "21_feraiz": "Ferâiz", "22_fetvalar": "Fetvâlar",
    "23_rekaik_adab": "Rekâik, âdâb, zühd (tasavvuf-ahlâk)", "24_siyer": "Siyer ve şemâil",
    "25_tarih": "Tarih", "26_teracim": "Terâcim ve tabakât", "27_ensab": "Ensâb", "28_buldan": "Büldân (coğrafya)",
    "29_dil": "Dil", "30_garib_lugat": "Garîb ve lügat", "31_nahiv_sarf": "Nahiv-sarf", "32_edebiyat": "Edebiyat",
    "33_aruz": "Arûz", "34_divanlar": "Dîvânlar", "35_belagat": "Belâgat", "36_cevami": "Câmi' (karma)",
    "37_fihrist": "Fihrist", "38_tip": "Tıp", "39_genel": "Genel", "40_diger": "Diğer",
}

_TASHKEEL = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")


def ar_norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = _TASHKEEL.sub("", s)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def tr_norm(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("ı", "i").replace("İ", "i").lower()


def yukle_eserler() -> list[dict]:
    reg = json.loads(REG.read_text(encoding="utf-8")).get("ready", {}) if REG.is_file() else {}
    out = []
    for cat in sorted(p.name for p in SH.iterdir() if p.is_dir()):
        for b in sorted((SH / cat).iterdir()):
            if not b.is_dir():
                continue
            m = b / "manifest.json"
            d = {}
            if m.is_file():
                try:
                    d = json.loads(m.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    d = {}
            out.append({
                "cat": cat, "klasor": b.name, "book_id": d.get("book_id"),
                "eser_ar": d.get("eser_ar") or "", "eser_tr": d.get("eser_tr") or "",
                "yazar": d.get("yazar") or "", "yazar_ar": d.get("yazar_ar") or "",
                "katman": d.get("katman"), "hat": d.get("hat"), "rol": d.get("rol"),
                "chunk_count": int(d.get("chunk_count") or 0), "cilt": d.get("cilt_db") or d.get("cilt_beklenen"),
                "manifest_var": bool(d),
            })
    return out


def cekirdek_esle(eserler: list[dict]) -> list[dict]:
    spec = json.loads(CEKIRDEK.read_text(encoding="utf-8"))
    for e in eserler:
        e["_ar"] = ar_norm(e["eser_ar"])
        e["_yz"] = ar_norm(e["yazar_ar"])
    sonuc = []
    for g in spec["gruplar"]:
        for it in g["eserler"]:
            keys = [ar_norm(k) for k in it.get("ar", [])]
            ykeys = [ar_norm(k) for k in it.get("yazar", [])]
            bulunan = []
            for e in eserler:
                ok_t = any(k and k in e["_ar"] for k in keys)
                if not ok_t:
                    continue
                if ykeys and not any(k in e["_yz"] or k in e["_ar"] for k in ykeys):
                    continue
                bulunan.append(e)
            sonuc.append({"grup": g["ad"], "katman": g.get("katman", ""), "ad": it["ad"], "not": it.get("not", ""),
                          "bulunan": bulunan})
    return sonuc


def cmd_dok(a) -> int:
    for e in yukle_eserler():
        print("\t".join(str(x) for x in (e["cat"], e["book_id"], e["eser_ar"], e["eser_tr"], e["yazar_ar"], e["chunk_count"])))
    return 0


def cmd_rapor(a) -> int:
    eserler = yukle_eserler()
    reg = json.loads(REG.read_text(encoding="utf-8")).get("ready", {}) if REG.is_file() else {}
    toplam_chunk = sum(int(v.get("chunks") or 0) for v in reg.values())
    toplam_kitap = len(eserler)
    cat_ozet = defaultdict(lambda: {"kitap": 0, "manifest": 0, "chunk_manifest": 0})
    for e in eserler:
        c = cat_ozet[e["cat"]]
        c["kitap"] += 1
        c["manifest"] += int(e["manifest_var"])
        c["chunk_manifest"] += e["chunk_count"]
    L = [f"# Din kütüphanesi kapsam envanteri — {date.today().isoformat()}", "",
         "**Kaynak:** `knowledge/ilim/din/shamela/**/manifest.json` + `.rag_index/shards/shamela/registry.json` (**salt okuma**; eser ekleme/indirme YOK).",
         f"**Üretici:** `scripts/din_kapsam_envanter.py rapor` · çekirdek liste VERİ: `eval/din/cekirdek_eserler.json`.", "",
         "## 1) Genel görünüm", "",
         f"- Şâmile shard sayısı: **{len(reg)}** kategori (hepsi `ready`) · kitap klasörü: **{toplam_kitap:,}** · indeksli parça: **{toplam_chunk:,}**".replace(",", "."),
         "- Gömme modeli: `paraphrase-multilingual-MiniLM-L12-v2` (384 boyut) · arama: kosinüs, brute-force numpy (mmap).",
         "- Ayrıca ana indekste elle derlenmiş `knowledge/ilim/din/01_kuran … 09_ahlak_tasavvuf` klasörleri (özet/kart düzeyi).", ""]
    # katman tablosu
    L += ["## 2) Kategori tablosu (shard bazında)", "",
          "| Katman | Kategori | Kitap | Parça (indeks) | Ort. parça/kitap |", "|---|---|---:|---:|---:|"]
    for kt, cats in KATMAN.items():
        for c in cats:
            r = reg.get(c, {})
            k = cat_ozet.get(c, {}).get("kitap", 0)
            ch = int(r.get("chunks") or 0)
            L.append(f"| {kt} | `{c}` {KAT_AD.get(c, '')} | {k} | {ch:,} | {int(ch / k) if k else 0} |".replace(",", "."))
    L.append("")
    L += ["### Katman toplamları", "", "| Katman | Kitap | Parça |", "|---|---:|---:|"]
    for kt, cats in KATMAN.items():
        kk = sum(cat_ozet.get(c, {}).get("kitap", 0) for c in cats)
        cc = sum(int(reg.get(c, {}).get("chunks") or 0) for c in cats)
        L.append(f"| {KATMAN_AD[kt]} | {kk} | {cc:,} |".replace(",", "."))
    L.append("")
    # manifest alanları
    hat = Counter(str(e["hat"]) for e in eserler)
    kat = Counter(str(e["katman"]) for e in eserler)
    L += ["### Manifest etiketleri (hat / katman)", "",
          f"- `hat`: {dict(hat)}", f"- `katman` (A=asıl/öğret, B=betimle, C=ayır/red): {dict(kat)}",
          f"- Manifestsiz klasör: {sum(1 for e in eserler if not e['manifest_var'])}", ""]
    # çekirdek eşleşme
    esl = cekirdek_esle(eserler)
    L += ["## 3) Çekirdek eser eşleşmesi (olmazsa olmaz + geniş)", "",
          "Eşleşme: eser adı (Arapça, harekesiz/normalize) anahtar içerir. «Var» = en az bir eşleşen cilt/kitap klasörü. "
          "Anahtarlar veri dosyasındadır; yanlış negatif görürseniz anahtar listesine ekleyin (kod değişmez).", ""]
    gruplar: dict[str, list[dict]] = {}
    for r in esl:
        gruplar.setdefault(r["grup"], []).append(r)
    ozet_rows = []
    for g, rows in gruplar.items():
        var = sum(1 for r in rows if r["bulunan"])
        ozet_rows.append((g, rows[0]["katman"], var, len(rows)))
    L += ["| Grup | Katman | Bulunan / aranan | Oran |", "|---|---|---:|---:|"]
    for g, kt, var, n in ozet_rows:
        L.append(f"| {g} | {kt} | {var} / {n} | %{round(100 * var / n)} |")
    L.append("")
    eksik_all = []
    for g, rows in gruplar.items():
        L += [f"### {g}", "", "| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |", "|---|---|---|"]
        for r in rows:
            if r["bulunan"]:
                en = sorted(r["bulunan"], key=lambda e: -e["chunk_count"])[:2]
                s = " ; ".join(f"`{e['cat']}` · {e['book_id']} · {e['chunk_count']} · {e['eser_ar'][:40]}" for e in en)
                extra = f" (+{len(r['bulunan']) - 2} kayıt)" if len(r["bulunan"]) > 2 else ""
                L.append(f"| {r['ad']} | ✔ var | {s}{extra} |")
            else:
                L.append(f"| {r['ad']} | ✘ **EKSİK/bulunamadı** | {r['not']} |")
                eksik_all.append(r)
        L.append("")
    # zayıf alanlar
    L += ["## 4) Zayıf / eksik alanlar (tespit)", ""]
    zay = []
    for g, kt, var, n in ozet_rows:
        if var / n < 0.8:
            zay.append(f"- **{g}**: aranan {n} çekirdek eserin {var}'i bulundu (%{round(100 * var / n)}).")
    L += zay or ["- (çekirdek gruplar ≥ %80)"]
    L += ["", "Şâmile dışı / doğası gereği zayıf noktalar:",
          "- **Türkçe kaynak yok**: bütün shard'lar Arapça; Türkçe soru ↔ Arapça eser eşleşmesi tek köprü (K3 sorgu genişletme). "
          "Türkçe ilmihâl/tefsir/tasavvuf (ör. Elmalılı, Ömer Nasuhi Bilmen, Mesnevî Türkçe) kütüphanede yok → Mimar kararı.",
          "- **Kur'ân metni**: ayrı bir mushaf/meal shard'ı yok; ayet metni tefsirlerin içinde (parça bazlı). «ayet bul» için ayrı bir Kur'ân ayet indeksi yok.",
          "- **Tasavvuf**: ayrı shard yok; `23_rekaik_adab` + `39_genel/40_diger` içinde dağınık (aşağıya bakın). Mevlânâ (Farsça Mesnevî) Şâmile'de yok, yalnız Arapça şerh/özet olabilir.",
          "- **Modern İslâm tarihi (Osmanlı → bugün)**: `25_tarih` ağırlıklı klasik dönem; Osmanlı/Cumhuriyet dönemi Arapça eserlerle sınırlı.",
          "- **Mükerrer cilt/baskı**: aynı eser birden çok book_id ile görünüyor olabilir (parça sayısı şişer; çeşitlilik sorunu için D2).", ""]
    # tasavvuf tarama
    tasv_keys = ["تصوف", "الصوفيه", "الطريقه", "السلوك", "الاحياء", "احياء علوم", "الحكم", "الفتوحات", "المثنوي", "الرساله القشيريه",
                 "طبقات الصوفيه", "حليه الاوليا", "قوت القلوب", "منازل السائرين", "مدارج السالكين", "الغنيه"]
    tas = [e for e in eserler if any(k in e["_ar"] for k in [ar_norm(x) for x in tasv_keys])] if eserler and "_ar" in eserler[0] else []
    L += ["## 5) Tasavvuf ve ahlâk taraması (anahtar kelime ile eser adı)", "",
          f"Eser adında tasavvuf anahtarı geçen kayıt: **{len(tas)}**. İlk 40:", ""]
    for e in sorted(tas, key=lambda e: -e["chunk_count"])[:40]:
        L.append(f"- `{e['cat']}` · {e['book_id']} · {e['eser_ar'][:60]} — {e['yazar_ar'][:30]} ({e['chunk_count']} parça)")
    L.append("")
    # akaid çizgi dağılımı (yazar anahtarları VERİ dosyasında; ajan hüküm vermez, dağılımı gösterir)
    spec = json.loads(CEKIRDEK.read_text(encoding="utf-8"))
    okul = spec.get("okul_yazar_anahtarlari") or {}
    if okul:
        L += ["## 5b) Akaid shard'ında yazar çizgisi dağılımı (Mimar'ın bilgisi için)", "",
              "Yazar adı anahtarlarına göre kaba dağılım (`eval/din/cekirdek_eserler.json` → `okul_yazar_anahtarlari`). "
              "Bu bir **hüküm değil dağılım**dır; Ehl-i Sünnet çizgisinin korunması için cevap üretiminde hangi eserlerin öne çıkacağı D2'de ele alınır.", "",
              "| Çizgi (anahtar listesi) | Kitap | Parça | Pay |", "|---|---:|---:|---:|"]
        ak = [e for e in eserler if e["cat"] == "01_akaid"]
        tot_ak = sum(e["chunk_count"] for e in ak) or 1
        for ad, keys in okul.items():
            kk = [ar_norm(k) for k in keys]
            sel = [e for e in ak if any(k in ar_norm(e["yazar_ar"] + " " + e["yazar"]) for k in kk)]
            ch = sum(e["chunk_count"] for e in sel)
            L.append(f"| {ad} | {len(sel)} | {ch:,} | %{round(100 * ch / tot_ak, 1)} |".replace(",", "."))
        L.append("")
        top_auth = Counter()
        for e in ak:
            top_auth[e["yazar_ar"] or e["yazar"]] += e["chunk_count"]
        L += ["Akaid shard'ında en çok parçası olan 12 yazar: " + " · ".join(f"{a} ({c})" for a, c in top_auth.most_common(12)), ""]
        L += ["> Not: manifestlerin hepsi `hat=ehlisunnet` etiketli (reddiyeler `katman=C`); etiket yazar/okul ayrımı yapmaz. "
              "Sentezde okul dengesi için D2'de «Eş'arî/Mâtürîdî ağırlıklı yazarları öne çıkarma» seçeneği Mimar kararı olarak sunulur.", ""]
    # en büyük eserler
    L += ["## 6) Her kategorinin en büyük 3 eseri (parça sayısı)", ""]
    byc = defaultdict(list)
    for e in eserler:
        byc[e["cat"]].append(e)
    for c in sorted(byc):
        top = sorted(byc[c], key=lambda e: -e["chunk_count"])[:3]
        L.append(f"- `{c}` ({KAT_AD.get(c, '')}): " + " · ".join(f"{e['eser_tr'] or e['eser_ar'][:30]} ({e['chunk_count']})" for e in top))
    L.append("")
    # eksik liste
    L += ["## 7) EKSİK LİSTESİ — Mimar'a (karar Mimar'da; ajan eser eklemedi/indirmedi)", "",
          "Aşağıdaki çekirdek eserler indekste bulunamadı. Eklenip eklenmeyeceği, kaynak (Şâmile'den çıkarım / başka koleksiyon) ve lisans Mimar kararıdır.", ""]
    for r in eksik_all:
        L.append(f"- [{r['grup']}] **{r['ad']}** {('— ' + r['not']) if r['not'] else ''}")
    L += ["", "### Kategori/İçerik düzeyinde eksikler (Mimar kararı)", "",
          "1. Türkçe temel kaynaklar (tefsir, ilmihâl, tasavvuf klasiklerinin Türkçe çevirileri) — şu an yok; cevap Arapça kaynaktan Türkçeye sentezleniyor.",
          "2. Kur'ân-ı Kerîm mushaf metni + meal + sûre/ayet künye tablosu (ayet numarası verebilmek için).",
          "3. Kütüb-i Sitte için hadis numaralı, bölüm başlıklı (kitap/bâb) yapılandırılmış künye (hadis no verebilmek için).",
          "4. Tasavvuf klasiklerinin eksik olanları (yukarıdaki tabloya bakın).",
          "5. Modern dönem İslâm/Osmanlı tarihi (Türkçe).", ""]
    out = DOCS / f"DIN_KAPSAM_ENVANTERI_{date.today().isoformat()}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("yazıldı:", out)
    print("kitap", toplam_kitap, "parça", toplam_chunk, "çekirdek eksik", len(eksik_all), "/", len(esl))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("rapor")
    sp.add_parser("dok")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    return {"rapor": cmd_rapor, "dok": cmd_dok}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
