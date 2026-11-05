#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rüzgar kütüphane envanteri — RAG'e dokunmaz; yalnız manifest + katalog okur, Excel yazar.

Örnek:
  python scripts/ruzgar_kutuphane_envanter.py --cat 01_akaid
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = Path(__file__).resolve().parents[1]
SHAMELA = ROOT / "knowledge" / "ilim" / "din" / "shamela"
ENV_ROOT = Path(r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE ENVANTER")
CATALOG = Path(
    r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE İNDEKS\İSLAMİ İLİMLER\_shamela_catalog_cache.json"
)

# Envanter kategorileri (Excel klasör + etiket).
# Hadis bloğu 06–10 bilinçli olarak ayrı turda (Mimar: önce diğerleri, sonra hadis).
READY_CATS = {
    "01_akaid": ("İSLAMİ İLİMLER", "01_AKAİD", "AKAİD"),
    "02_firak_redler": ("İSLAMİ İLİMLER", "02_FIRAK_VE_REDLER", "FIRAK VE REDLER"),
    "03_tefsir": ("İSLAMİ İLİMLER", "03_TEFSİR", "TEFSİR"),
    "04_kuran_ilim_usul": (
        "İSLAMİ İLİMLER",
        "04_KURAN_ILIMLERI_VE_USUL",
        "KUR'AN İLİMLERİ VE TEFSİR USÛLÜ",
    ),
    "05_tecvid_kiraat": ("İSLAMİ İLİMLER", "05_TECVİD_VE_KIRAAT", "TECVİD VE KIRAAT"),
    "11_usul_fikih": ("İSLAMİ İLİMLER", "11_USUL_FIKIH", "USÛL-İ FIKIH"),
    "12_fikih_kaideler": (
        "İSLAMİ İLİMLER",
        "12_FIKIH_ILIMLERI_VE_KAIDELER",
        "FIKIH İLİMLERİ VE KAİDELER",
    ),
    "13_mantik": ("İSLAMİ İLİMLER", "13_MANTIK", "MANTIK"),
    "14_hanefi": ("İSLAMİ İLİMLER", "14_HANEFI_FIKHI", "HANEFİ FIKHI"),
    "15_maliki": ("İSLAMİ İLİMLER", "15_MALIKI_FIKHI", "MALİKİ FIKHI"),
    "16_safii": ("İSLAMİ İLİMLER", "16_SAFII_FIKHI", "ŞAFİİ FIKHI"),
    "17_hanbeli": ("İSLAMİ İLİMLER", "17_HANBELI_FIKHI", "HANBELİ FIKHI"),
    "18_genel_fikih": ("İSLAMİ İLİMLER", "18_GENEL_FIKIH", "GENEL FIKIH"),
    "19_fikhi_meseleler": ("İSLAMİ İLİMLER", "19_FIKHI_MESELELER", "FIKHÎ MESELELER"),
    "20_siyaset_kaza": (
        "İSLAMİ İLİMLER",
        "20_SIYASET_SERIYYE_VE_KAZA",
        "SİYASET-İ ŞER'İYYE VE KAZÂ",
    ),
    "21_feraiz": ("İSLAMİ İLİMLER", "21_FERAIZ_VE_VESAYA", "FERÂİZ VE VESÂYÂ"),
    "22_fetvalar": ("İSLAMİ İLİMLER", "22_FETVALAR", "FETVÂLAR"),
    "23_rekaik_adab": (
        "İSLAMİ İLİMLER",
        "23_REKAIK_ADAB_VE_EZAKIR",
        "REKÂİK ÂDÂB VE EZÂKİR",
    ),
    "24_siyer": ("İSLAMİ İLİMLER", "24_SIYER", "SİYER"),
    "25_tarih": ("İSLAMİ İLİMLER", "25_TARIH", "TARİH"),
    "26_teracim": ("İSLAMİ İLİMLER", "26_TERACIM_VE_TABAKAT", "TERÂCİM VE TABAKÂT"),
    "27_ensab": ("İSLAMİ İLİMLER", "27_ENSAB", "ENSÂB"),
    "28_buldan": (
        "İSLAMİ İLİMLER",
        "28_BULDAN_VE_SEYAHATNAMELER",
        "BULDÂN VE SEYAHATNAMELER",
    ),
    "29_dil": ("İSLAMİ İLİMLER", "29_DIL_KITAPLARI", "DİL KİTAPLARI"),
    "30_garib_lugat": ("İSLAMİ İLİMLER", "30_GARIB_VE_LUGAT", "GARÎB VE LUGAT"),
    "31_nahiv_sarf": ("İSLAMİ İLİMLER", "31_NAHIV_VE_SARF", "NAHIV VE SARF"),
    "32_edebiyat": ("İSLAMİ İLİMLER", "32_EDEBIYAT", "EDEBİYAT"),
    "33_aruz": ("İSLAMİ İLİMLER", "33_ARUZ_VE_KAFIYE", "ARÛZ VE KAFİYE"),
    "34_divanlar": ("İSLAMİ İLİMLER", "34_DIVANLAR", "DİVANLAR"),
    "35_belagat": ("İSLAMİ İLİMLER", "35_BELAGAT", "BELÂGAT"),
    "36_cevami": ("İSLAMİ İLİMLER", "36_CEVAMI", "CEVÂMİ (TOPLU ESERLER)"),
    "37_fihrist": ("İSLAMİ İLİMLER", "37_FIHRIST_VE_DELILLER", "FİHRİST VE DELİLLER"),
    "38_tip": ("İSLAMİ İLİMLER", "38_TIP", "TIP"),
    "39_genel": ("İSLAMİ İLİMLER", "39_GENEL_KITAPLAR", "GENEL KİTAPLAR"),
    "40_diger": ("İSLAMİ İLİMLER", "40_DIGER_ILIMLER", "DİĞER İLİMLER"),
}

# Bilinçli ertelenen (hadis turu)
DEFERRED_HADIS_CATS = {
    "06_hadis_sunen",
    "07_hadis_serh",
    "08_tahric_etraf",
    "09_ilel_sual",
    "10_hadis_ilimleri",
}

HEADERS = [
    "NO",
    "YAZAR",
    "ESERİN TÜRKÇE ADI",
    "İÇERİK / MAHİYET (KISA)",
    "İLK TARİH (HİCRÎ)",
    "GERÇEK CİLT SAYISI",
    "YÜKLENEN CİLTLER / EKSİK",
]

# Yaygın kelimeler — Latin ilmî okunuş
_WORD = {
    "ال": "el-",
    "في": "fî",
    "على": "alâ",
    "إلى": "ilâ",
    "من": "min",
    "عن": "an",
    "أو": "ev",
    "و": "ve",
    "شرح": "Şerh",
    "كتاب": "Kitâb",
    "رسالة": "Risâle",
    "عقيدة": "Akîde",
    "العقيدة": "el-Akîde",
    "التوحيد": "et-Tevhîd",
    "توحيد": "Tevhîd",
    "الإسلامية": "el-İslâmiyye",
    "الإسلامي": "el-İslâmî",
    "تفسير": "Tefsîr",
    "صحيح": "Sahîh",
    "سنن": "Sünen",
    "مقدمة": "Mukaddime",
    "حاشية": "Hâşiye",
    "الفتاوى": "el-Fetâvâ",
    "الرد": "er-Redd",
    "رد": "Redd",
}

_CHAR = {
    "ا": "a",
    "أ": "e",
    "إ": "i",
    "آ": "â",
    "ب": "b",
    "ت": "t",
    "ث": "s",
    "ج": "c",
    "ح": "h",
    "خ": "h",
    "د": "d",
    "ذ": "z",
    "ر": "r",
    "ز": "z",
    "س": "s",
    "ش": "ş",
    "ص": "s",
    "ض": "d",
    "ط": "t",
    "ظ": "z",
    "ع": "'",
    "غ": "ğ",
    "ف": "f",
    "ق": "k",
    "ك": "k",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "ه": "h",
    "ة": "e",
    "و": "û",
    "ؤ": "ü",
    "ي": "î",
    "ى": "â",
    "ئ": "i",
    "ء": "'",
    "ً": "",
    "ٌ": "",
    "ٍ": "",
    "َ": "",
    "ُ": "",
    "ِ": "",
    "ّ": "",
    "ْ": "",
    "ـ": "",
}


def _looks_english(s: str) -> bool:
    t = (s or "").strip()
    if not t:
        return False
    # Türkçe karakter yok + The/of/in kalıbı
    if re.search(r"[çğıöşüÇĞİÖŞÜ]", t):
        return False
    if re.search(r"\b(The|of|and|in|on|for|with|Explanation|Book|People)\b", t):
        return True
    letters = re.findall(r"[A-Za-z]", t)
    return bool(letters) and not re.search(r"[çğıöşüÇĞİÖŞÜâîûÂÎÛ]", t) and " " in t


def pick_tr(man: dict, cat_row: dict | None) -> str:
    man_tr = (man.get("eser_tr") or "").strip()
    cat_tr = ((cat_row or {}).get("tr_title") or "").strip()
    # Katalog İngilizce bozulmuşsa manifest Türkçesini tercih et
    if cat_tr and not _looks_english(cat_tr):
        return cat_tr
    if man_tr and not _looks_english(man_tr):
        return man_tr
    return cat_tr or man_tr or "—"


def ar_title_to_latin(ar: str) -> str:
    """Okunabilir Latin başlık (yaklaşık ilmî transliterasyon; cilaya açık)."""
    s = (ar or "").strip()
    if not s:
        return "—"
    parts = re.split(r"(\[[^\]]+\]|\([^\)]+\))", s)
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("[") or part.startswith("("):
            inner = part[1:-1]
            out.append(part[0] + ar_title_to_latin(inner) + part[-1])
            continue
        words = part.split()
        buf: list[str] = []
        for w in words:
            punct = ""
            raw = w
            while raw and raw[-1] in "«»\"'،,.؟!":
                punct = raw[-1] + punct
                raw = raw[:-1]
            if raw in _WORD:
                buf.append(_WORD[raw] + punct.replace("،", ",").replace("«", "").replace("»", ""))
                continue
            if raw.startswith("ال") and len(raw) > 2:
                rest = "".join(_CHAR.get(ch, ch if ord(ch) < 128 else "") for ch in raw[2:])
                buf.append("el-" + rest + punct.replace("،", ","))
                continue
            buf.append(
                "".join(_CHAR.get(ch, ch if ord(ch) < 128 else "") for ch in raw)
                + punct.replace("،", ",")
            )
        out.append(" ".join(x for x in buf if x))
    t = " ".join(x for x in out if x)
    t = re.sub(r"\s+", " ", t).strip(" -")
    # Baş harf düzeni: ilk kelime büyük
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    return t or "—"


def load_catalog() -> dict[int, dict]:
    if not CATALOG.is_file():
        return {}
    rows = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {int(r["book_id"]): r for r in rows if r.get("book_id") is not None}


_MASTER = Path(r"D:\shamela4\database\master.db")


def load_book_dates(book_ids: list[int]) -> dict[int, str]:
    """Şamile master.db book_date (Hicrî). 99999 / boş → bilinmiyor.

    Not: Şamile'de bu alan çoğu kayıtta yazar vefat yılına yakın düşer;
    ayrı 'telif yılı' her eserde yok. Kullanıcıya Hicrî olarak yazılır.
    """
    out: dict[int, str] = {}
    if not book_ids or not _MASTER.is_file():
        return out
    import sqlite3

    con = sqlite3.connect(str(_MASTER))
    try:
        q = ",".join("?" * len(book_ids))
        rows = con.execute(
            f"SELECT book_id, book_date FROM book WHERE book_id IN ({q})",
            book_ids,
        ).fetchall()
        for bid, raw in rows:
            try:
                n = int(raw)
            except (TypeError, ValueError):
                out[int(bid)] = "bilinmiyor"
                continue
            if n <= 0 or n >= 90000:
                out[int(bid)] = "bilinmiyor"
            else:
                out[int(bid)] = f"H.{n}"
    finally:
        con.close()
    return out


def display_title(tr: str, ar: str) -> str:
    """Türkçe ad yok/bozuksa orijinal Arapça adı göster."""
    t = (tr or "").strip()
    if t and t not in ("—", "-") and not _looks_english(t) and t != "Türkçe ad henüz netleşmedi":
        return t
    a = (ar or "").strip()
    return a if a else "Ad yok"


def volume_info(man: dict, cat_row: dict | None) -> tuple[int, str]:
    parts = man.get("parts") or []
    pwt = man.get("parts_with_text") or {}
    expected = int(
        man.get("cilt_beklenen")
        or man.get("cilt_db")
        or (cat_row or {}).get("cilt")
        or (len(parts) if parts else 1)
        or 1
    )
    if expected <= 0:
        expected = 1
    have_ids = sorted(
        {str(k) for k, v in pwt.items() if v},
        key=lambda x: int(x) if str(x).isdigit() else 0,
    )
    yuklenen = len(have_ids) if have_ids else (1 if int(man.get("pages_db") or 0) > 0 else 0)
    expected_ids = []
    if parts:
        for p in parts:
            if isinstance(p, (list, tuple)) and p:
                expected_ids.append(str(p[0]))
            else:
                expected_ids.append(str(p))
    else:
        expected_ids = [str(i) for i in range(1, expected + 1)]
    missing = [e for e in expected_ids if e not in set(have_ids)]
    if yuklenen >= expected and not missing:
        durum = f"{yuklenen}/{expected} — tam"
    elif missing:
        durum = f"{yuklenen}/{expected} — eksik cilt: {', '.join(missing)}"
    else:
        durum = f"{yuklenen}/{expected}"
    return expected, durum


_HAT_TR = {
    "ehlisunnet": "ehl-i sünnet",
    "selefi": "selefî",
    "esari": "eş‘arî",
    "maturidi": "mâtürîdî",
}
_ROL_TR = {
    "ogret": "öğretici / ders kitabı niteliğinde",
    "red": "karşı görüşe reddiye",
    "incele": "inceleme / değerlendirme",
    "kaynak": "kaynak eser",
}

# (anahtar, Türkçe konu cümlesi) — başlıkta geçene göre (tüm RAG ready kategoriler)
_TOPIC_RULES: list[tuple[re.Pattern[str], str]] = [
    # --- akaid / kelâm ---
    (re.compile(r"tevh[iî]d|توحيد", re.I), "Allah’ın birliği (tevhid) ve ibadetin yalnızca O’na ait oluşunu işler"),
    (re.compile(r"ak[aâ]id|itikad|i'?tikad|عقيد|اعتقاد", re.I), "inanç esaslarını (akaid/itikad) sistemli biçimde anlatır"),
    (re.compile(r"iman|îman|إيمان|شعب", re.I), "imanın tanımı, şartları veya şubeleri üzerinde durur"),
    (re.compile(r"s[ıi]fat|صفات|اسماء", re.I), "Allah’ın isim ve sıfatları konusunu ele alır"),
    (re.compile(r"kader|قدر|قضا", re.I), "kader ve kazâ meselesini konu edinir"),
    (re.compile(r"şirk|شرك|وثن", re.I), "şirk ve bid‘at türlerine karşı uyarı / açıklama içerir"),
    (re.compile(r"asm[aâ]|أسماء الله", re.I), "Allah’ın güzel isimleri (esmâ-i hüsnâ) etrafında döner"),
    (re.compile(r"nübüvvet|نبوة|رسول|peygamber", re.I), "nübüvvet / peygamberlik inancını işler"),
    (re.compile(r"ahiret|آخرة|جنة|نار|kıyamet", re.I), "ahiret, cennet-cehennem veya kıyamet inancına dairdir"),
    (re.compile(r"vahhab|vehhâb|محمد بن عبد الوهاب", re.I), "Muhammed b. Abdülvehhâb çizgisi veya ona dair akaid metniyle ilişkilidir"),
    (re.compile(r"ibni?\s*teymi|ابن تيمية|teymiyye", re.I), "İbn Teymiyye’nin itikadî görüşleri veya ona dair bir metindir"),
    # --- firak / reddiye ---
    (re.compile(r"red|redd|رد |الرد|nakz|نقض|إبطال", re.I), "belirli görüş veya fırkalara karşı reddiye / cevap niteliğindedir"),
    (re.compile(r"ş[iî]a|rafiz|رافض|شيعة|جعفر", re.I), "Şia / Rafızî görüşlerle ilgili tartışma veya tenkit barındırır"),
    (re.compile(r"cehm|jahm|معتزل|cebr[iî]ye|murci|قدرية|خوارج|باطن", re.I), "kelâmî / bid‘at fırkalara (Cehmiyye, Mu‘tezile, Hâricî vb.) dair tenkit veya açıklama yapar"),
    (re.compile(r"fırk|firak|فرق|مقالات|milal|nihal|ملل|نحل", re.I), "fırkaları, mezhep görüşlerini veya makâlât literatürünü inceler"),
    (re.compile(r"mezheb|مذهب", re.I), "mezhep veya fırkaların itikadî yönlerini inceler"),
    (re.compile(r"bid'?at|بدعة|اهواء", re.I), "bid‘at ve sapma yollarına karşı uyarı / sınıflandırma içerir"),
    # --- tefsir / Kur’an ---
    (re.compile(r"tefs[iî]r|تفسير", re.I), "Kur’ân âyetlerinin anlamını açan bir tefsir / yorum çalışmasıdır"),
    (re.compile(r"ahk[aâ]m|أحكام القرآن|âyât.?ül.?ahkâm", re.I), "hüküm âyetlerini (ahkâm) fıkhî açıdan tefsir eder"),
    (re.compile(r"me'[aâ]n[iî]|معاني القرآن|i'?r[aâ]b.?ül.?kur", re.I), "Kur’ân’ın dilbilgisel / i‘râb ve anlam yönlerini inceler"),
    (re.compile(r"esb[aâ]b|أسباب النزول|nüz[uû]l", re.I), "âyetlerin iniş sebeplerini (esbâb-ı nüzûl) konu edinir"),
    (re.compile(r"n[aâ]sih|mens[uû]h|ناسخ|منسوخ", re.I), "nesih (nâsih–mensûh) meselesini işler"),
    (re.compile(r"muhk[ae]m|müteş[aâ]bih|محكم|متشابه", re.I), "muhkam–müteşâbih ayırımını ve te’vilini ele alır"),
    (re.compile(r"vuc[uû]h|naz[aâ]'?ir|وجوه|نظائر", re.I), "Kur’ân’da eşanlam / çokanlam (vücûh ve nezâir) konusunu işler"),
    (re.compile(r"gar[iî]b|غريب القرآن|mufred[aâ]t", re.I), "Kur’ân’daki garîb / zor kelimeleri açıklar"),
    (re.compile(r"i'?c[aâ]z|إعجاز|bel[aâ]ğ", re.I), "Kur’ân’ın i‘câzı veya belâgat yönünü inceler"),
    (re.compile(r"ul[uû]m.?ül.?kur|علوم القرآن|kur'?[aâ]n.?ilim", re.I), "ulûmü’l-Kur’ân (Kur’ân ilimleri) konularını derler"),
    (re.compile(r"us[uû]l.?ü.?t.?tefs[iî]r|أصول التفسير|man[aâ]hic.?ü.?t.?tefs", re.I), "tefsir usûlü / yöntemlerini öğretir"),
    (re.compile(r"c[aâ]mi'?|جامع|büyük tefs[iî]r|mufassal", re.I), "kapsamlı / çok ciltli bir tefsir veya derleme niteliğindedir"),
    (re.compile(r"s[uû]re|سورة|f[aâ]tiha|bakara|y[aâ]s[iî]n|ihl[aâ]s", re.I), "belirli sûre(ler) üzerine yoğunlaşmış bir tefsir / şerhtir"),
    # --- tecvid / kıraat ---
    (re.compile(r"tecv[iî]d|تجويد", re.I), "Kur’ân tilâvetinde tecvid kurallarını öğretir"),
    (re.compile(r"kira[aâ]t|قراءة|قراءات|aşere|seb'?a", re.I), "kıraat vecihlerini (yedi / on kıraat vb.) inceler"),
    (re.compile(r"mek[aâ]ri[e]?|مخارج|sıfat.?ül.?hur[uû]f", re.I), "harf mahreçleri ve sıfatlarını açıklar"),
    (re.compile(r"vakf|وقف|ibtid[aâ]", re.I), "vakıf ve ibtidâ (durma–başlama) kurallarını ele alır"),
    (re.compile(r"resm|رسم|osman[iî]|ضبط", re.I), "mushaf resmi / yazım ve zabt konularını işler"),
    (re.compile(r"tert[iî]l|تلاو|til[aâ]vet|okuma", re.I), "doğru tilâvet / tertîl pratiklerine odaklanır"),
    # --- mantık ---
    (re.compile(r"mant[iı]k|منطق", re.I), "klasik mantık (kıyas, tanım, önerme) konularını işler"),
    (re.compile(r"k[iı]y[aâ]s|قياس|burh[aâ]n|برهان", re.I), "kıyas / burhân (delil) teorisini anlatır"),
    (re.compile(r"îs[aâ]g[uû]c[iî]|إيساغوجي|porfir|madhal|مدخل", re.I), "Îsâgûcî / mantığa giriş metni veya şerhidir"),
    (re.compile(r"şemsiyye|شمسية|tehz[iî]b|تهذيب", re.I), "şöhretli bir mantık metninin (Şemsiyye, Tehzîb vb.) şerhi / hâşiyesidir"),
    (re.compile(r"cedel|جدل|mun[aâ]zara|مناظرة", re.I), "cedel / münazara yöntemlerini ele alır"),
    (re.compile(r"h[iı]kmet|حكمة|felsefe|فلسفة", re.I), "hikmet / felsefe ile kesişen mantıkî tartışmalar içerir"),
    # --- usûl / fıkıh ---
    (re.compile(r"us[uû]l.?ü.?l.?f[iı]kh|أصول الفقه|usul.?i.?fikih", re.I), "fıkıh usûlü (delil, hüküm, ictihad) konularını öğretir"),
    (re.compile(r"k[aâ]ide|قواعد|قواعد فقه", re.I), "fıkhî kaideleri / genel ilkeleri derler"),
    (re.compile(r"hanef[iî]|حنفي|نعمان", re.I), "Hanefî mezhebi fıkhına aittir"),
    (re.compile(r"m[aâ]lik[iî]|مالكي", re.I), "Mâlikî mezhebi fıkhına aittir"),
    (re.compile(r"ş[aâ]fi[iî]|شافعي", re.I), "Şâfiî mezhebi fıkhına aittir"),
    (re.compile(r"hanbel[iî]|حنبلي|أحمد بن حنبل", re.I), "Hanbelî mezhebi fıkhına aittir"),
    (re.compile(r"ib[aâ]d[aâ]t|عبادات|namaz|salât|zakat|oru[cç]|hac", re.I), "ibadetler (namaz, zekât, oruç, hac vb.) hükümlerini işler"),
    (re.compile(r"mu[aâ]'?mel[aâ]t|معاملات|buy[uû]'?|بيع|rib[aâ]", re.I), "muâmelât / alışveriş ve malî hükümleri konu edinir"),
    (re.compile(r"nik[aâ]h|طلاق|miras|feraiz|فرائض|وصايا", re.I), "aile / miras / ferâiz hükümlerini ele alır"),
    (re.compile(r"kaz[aâ]|قضاء|siy[aâ]set|سياسة|ahk[aâ]m.?ü.?s.?sult", re.I), "kazâ / siyâset-i şer‘iyye veya yargı konularını işler"),
    (re.compile(r"mes'?ele|مسألة|naw[aâ]zil|نوازل", re.I), "belirli fıkhî mesele veya nâzileleri inceler"),
    # --- rekâik / siyer / tarih ---
    (re.compile(r"rek[aâ]'?ik|رقائق|zuhd|زهد|vaaz|موعظة", re.I), "kalp yumuşatıcı / zühd ve vaaz türü bir metindir"),
    (re.compile(r"[aâ]d[aâ]b|آداب|ahl[aâ]k|أخلاق", re.I), "âdâb ve ahlak konularını öğretir"),
    (re.compile(r"ezk[aâ]r|أذكار|dua|دعاء|wird", re.I), "zikir / dua / vird derlemesi içerir"),
    (re.compile(r"siyer|سيرة|meg[aâ]z[iî]|مغازي", re.I), "Peygamber Efendimiz’in (s.a.v.) sîretini / gazvelerini anlatır"),
    (re.compile(r"şem[aâ]'?il|شمائل", re.I), "Hz. Peygamber’in şemâilini (hâl ve şekil) konu edinir"),
    (re.compile(r"tarih|تاريخ|ahb[aâ]r|أخبار|vak'?ayi", re.I), "tarihî olaylar / kronik anlatımıdır"),
    (re.compile(r"ter[aâ]cim|تراجم|tabak[aâ]t|طبقات|ric[aâ]l", re.I), "âlim / râvî biyografileri (terâcim–tabakât) derler"),
    (re.compile(r"ens[aâ]b|أنساب|neseb", re.I), "nesep / soy kütüğü bilgisini işler"),
    (re.compile(r"buld[aâ]n|بلدان|coğraf|رحلات|seyahat", re.I), "belde / coğrafya veya seyahatnâme niteliğindedir"),
    # --- dil / edebiyat ---
    (re.compile(r"lugat|معجم|قاموس|gar[iî]b|غريب", re.I), "lügat / garîb kelime açıklaması veya sözlüktür"),
    (re.compile(r"nahiv|نحو|i'?r[aâ]b|إعراب", re.I), "Arapça nahiv (sözdizimi) konularını öğretir"),
    (re.compile(r"sarf|صرف|tasr[iî]f", re.I), "Arapça sarf (çekim / morfoloji) konularını işler"),
    (re.compile(r"bel[aâ]ğ|بلاغة|me[aâ]n[iî]|bey[aâ]n|bed[iî]'", re.I), "belâgat (meânî–beyân–bedî‘) ilmine dairdir"),
    (re.compile(r"[aâ]r[uû]z|عروض|k[aâ]fiye|قافية", re.I), "arûz ve kafiye (vezin) bilgisini öğretir"),
    (re.compile(r"d[iî]v[aâ]n|ديوان|şiir|شعر", re.I), "şiir dîvânı veya edebî şiir derlemesidir"),
    (re.compile(r"edeb|أدب|nesir|نثر|mak[aâ]m[aâ]t", re.I), "klasik Arap edebiyatı / nesir örneğidir"),
    (re.compile(r"fihrist|فهرس|del[iî]l|دليل", re.I), "fihrist / rehber / indeks niteliğindedir"),
    (re.compile(r"cev[aâ]mi'|جوامع|külliyat|مجموع", re.I), "birden fazla eseri bir araya getiren toplu / külliyat metnidir"),
    (re.compile(r"t[iı]b|طب|tıbb|شفا|dev[aâ]", re.I), "klasik tıp / şifâ konularını ele alır"),
    # --- ortak form ---
    (re.compile(r"sünnet|سنة|سلف|selef", re.I), "selef / ehl-i sünnet çizgisini aktarmayı hedefler"),
    (re.compile(r"şerh|شرح|hâşiye|haşiye|حاشية", re.I), "önceki bir metnin şerhi veya hâşiyesidir"),
    (re.compile(r"muhta[sş]ar|مختصر|özet|talh[iî]s", re.I), "daha geniş bir eserin özeti / muhtasarıdır"),
    (re.compile(r"fetv|فتو", re.I), "fetva / cevap derlemesi içerir"),
    (re.compile(r"ris[aâ]le|رسالة|makale", re.I), "kısa risâle / makale türünde bir çalışmadır"),
]

_AR_SECTION = {
    "مقدمة": "mukaddime / giriş",
    "تمهيد": "önsöz",
    "فصل": "fasıl",
    "باب": "bâb",
    "خاتمة": "hâtime",
    "التوحيد": "tevhid",
    "الإيمان": "iman",
    "الشرك": "şirk",
    "الصفات": "sıfatlar",
    "القدر": "kader",
    "الأسماء": "isimler",
    "التفسير": "tefsir",
    "سورة": "sûre",
    "الآية": "âyet",
    "القراءة": "kıraat",
    "التجويد": "tecvid",
    "الوقف": "vakıf",
    "المخارج": "mahreçler",
    "القياس": "kıyas",
    "الحد": "tanım",
    "القضية": "önerme",
    "الفرق": "fırkalar",
    "الرد": "reddiye",
}


def _first_batch_text(book_dir: Path) -> str:
    inc = book_dir / "incremental"
    if not inc.is_dir():
        return ""
    files = sorted(inc.glob("*.md"))
    if not files:
        return ""
    try:
        return files[0].read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _section_hints(text: str, limit: int = 4) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    skip = re.compile(
        r"paket\s*\d+|parça\s*\d+|cilt\s*\d+|şamile|orijinal:|yazar:|katman:|kaynak:|"
        r"el-mektebet|lucene|book_id|hâşiye|حقوق|الطبعة",
        re.I,
    )
    # Önce gerçek bölüm başlıkları (HTML title)
    for m in re.finditer(
        r'data-type="title"[^>]*>\s*([^<]{3,80})',
        text,
        re.I,
    ):
        raw = re.sub(r"\s+", " ", m.group(1)).strip(" :.-—")
        if len(raw) < 3 or skip.search(raw):
            continue
        mapped = None
        for ar, tr in _AR_SECTION.items():
            if ar in raw:
                mapped = tr
                break
        label = mapped or (
            raw if re.search(r"[A-Za-zçğıöşüÇĞİÖŞÜ]", raw) else None
        )
        if not label:
            # Arapça başlığı bilinen kelimelere çevirmeye çalış
            bits = [tr for ar, tr in _AR_SECTION.items() if ar in raw]
            label = ", ".join(bits) if bits else None
        if label and label not in found:
            found.append(label)
        if len(found) >= limit:
            break
    return found


def _topic_sentences(tr: str, ar: str) -> list[str]:
    blob = f"{tr} {ar}"
    hits: list[str] = []
    for rx, sent in _TOPIC_RULES:
        if rx.search(blob):
            if sent not in hits:
                hits.append(sent)
        if len(hits) >= 3:
            break
    return hits


def mahiyet(man: dict, tr: str, cat_label: str, book_dir: Path | None = None) -> str:
    """Okuyanın 'bu kitap ne anlatıyor?' sorusuna Türkçe cevap."""
    ar = (man.get("eser_ar") or "").strip()
    tip = (tr or "").strip()
    if _looks_english(tip):
        tip = ""

    sentences: list[str] = []
    topics = _topic_sentences(tip, ar)
    if tip and tip not in ("—", "-", "Ad yok") and not re.search(r"[\u0600-\u06FF]", tip):
        if topics:
            sentences.append(f"«{tip}»: {topics[0]}.")
            for t in topics[1:]:
                sentences.append(t[0].upper() + t[1:] + ".")
        else:
            sentences.append(
                f"«{tip}» adlı bu çalışma {cat_label.lower()} sahasında kaleme alınmış bir metindir."
            )
    else:
        if topics:
            sentences.append(f"Bu {cat_label.lower()} eseri {topics[0]}.")
            for t in topics[1:]:
                sentences.append(t[0].upper() + t[1:] + ".")
        else:
            sentences.append(
                f"Bu eser {cat_label.lower()} sahasında yazılmış bir kaynaktır; "
                f"içeriği başlık ve açılış bölümlerinden çıkarılabildiği kadarıyla bu alana aittir."
            )

    rol = _ROL_TR.get((man.get("rol") or "").strip().lower(), "")
    hat = _HAT_TR.get((man.get("hat") or "").strip().lower(), "")
    if rol:
        sentences.append(f"Üslup/amaç: {rol}.")
    if hat:
        sentences.append(f"İtikad hattı: {hat}.")

    if book_dir is not None:
        hints = _section_hints(_first_batch_text(book_dir))
        if hints:
            sentences.append("İçindekilerden görülen başlıklar: " + "; ".join(hints) + ".")

    pages = man.get("pages_db") or man.get("pages_lucene")
    cilt = int(man.get("cilt_beklenen") or man.get("cilt_db") or 0)
    size_bits = []
    if cilt > 1:
        size_bits.append(f"{cilt} cilt")
    if pages:
        size_bits.append(f"yaklaşık {pages} sayfa")
    if size_bits:
        sentences.append("Hacim: " + ", ".join(size_bits) + ".")

    # tek paragraf, okunaklı
    return " ".join(sentences)


def collect_cat(cat: str) -> list[dict]:
    base = SHAMELA / cat
    if not base.is_dir():
        raise SystemExit(f"kategori yok: {base}")
    catalog = load_catalog()
    domain, folder, label = READY_CATS[cat]
    raw_rows: list[dict] = []
    for d in sorted(base.iterdir(), key=lambda p: p.name):
        if not d.is_dir():
            continue
        mp = d / "manifest.json"
        if not mp.is_file():
            continue
        man = json.loads(mp.read_text(encoding="utf-8"))
        bid = int(man.get("book_id") or 0)
        cat_row = catalog.get(bid)
        ar = (man.get("eser_ar") or (cat_row or {}).get("ar_title") or "").strip()
        tr_raw = pick_tr(man, cat_row)
        title = display_title(tr_raw, ar)
        yazar = (
            (cat_row or {}).get("author")
            or man.get("yazar")
            or "—"
        ).strip()
        gercek, yukleme = volume_info(man, cat_row)
        # Mahiyet: Türkçe ad + konu kuralları + açılış/içindekiler
        mah_tr = (
            tr_raw
            if (tr_raw and not _looks_english(tr_raw) and tr_raw not in ("—", "-"))
            else title
        )
        raw_rows.append(
            {
                "tr": title,
                "yazar": yazar if yazar else "Yazar bilinmiyor",
                "cilt": gercek,
                "yukleme": yukleme,
                "mahiyet": mahiyet(man, mah_tr, label, book_dir=d),
                "book_id": bid,
                "eser_id": man.get("eser_id") or d.name,
                "ar": ar,
            }
        )
    dates = load_book_dates([r["book_id"] for r in raw_rows])
    for r in raw_rows:
        r["tarih"] = dates.get(r["book_id"], "bilinmiyor")
    # Yazar A→Z, sonra eser adı
    raw_rows.sort(
        key=lambda r: (
            (r["yazar"] or "").casefold().replace("â", "a").replace("î", "i").replace("û", "u"),
            (r["tr"] or "").casefold(),
            r["book_id"],
        )
    )
    return raw_rows


def _rag_ready_cats() -> set[str]:
    """Shard registry'de ready işaretli kategoriler (yoksa boş)."""
    reg = (
        ROOT
        / ".rag_index"
        / "shards"
        / "shamela"
        / "registry.json"
    )
    if not reg.is_file():
        return set()
    try:
        data = json.loads(reg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return set((data.get("ready") or {}).keys())


def write_xlsx(cat: str, rows: list[dict]) -> Path:
    domain, folder, label = READY_CATS[cat]
    out_dir = ENV_ROOT / domain / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{label}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = label[:31]
    rag_tag = "RAG indeksli" if cat in _rag_ready_cats() else "kütüphane (manifest)"
    ws["A1"] = (
        f"{label} — Rüzgar kütüphane envanteri ({rag_tag}) · "
        f"Toplam {len(rows)} eser · Yazar A→Z · Tarih: Hicrî (Şamile)"
    )
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="C00000")
    ws.merge_cells("A1:G1")
    header_font = Font(name="Calibri", size=11, bold=True)
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    thin = Border(
        left=Side(style="thin", color="B0B0B0"),
        right=Side(style="thin", color="B0B0B0"),
        top=Side(style="thin", color="B0B0B0"),
        bottom=Side(style="thin", color="B0B0B0"),
    )
    for col, h in enumerate(HEADERS, 1):
        cell = ws.cell(2, col, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    for i, r in enumerate(rows, 1):
        vals = [
            i,
            r["yazar"],
            r["tr"],
            r["mahiyet"],
            r.get("tarih") or "bilinmiyor",
            r["cilt"],
            r["yukleme"],
        ]
        for col, v in enumerate(vals, 1):
            cell = ws.cell(2 + i, col, v)
            cell.border = thin
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 48
    ws.column_dimensions["D"].width = 56
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 16
    ws.column_dimensions["G"].width = 28
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:G{2 + len(rows)}"
    # Not sayfası
    ws_note = wb.create_sheet("NOT")
    ws_note["A1"] = (
        "İLK TARİH (HİCRÎ): Şamile katalogundaki book_date alanıdır. "
        "Çoğu kayıtta eser için ayrı telif yılı yoktur; alan yazarın vefat yılına "
        "yakın veya onunla aynı gelir. 99999 / boş → bilinmiyor. "
        "Türkçe adı olmayan satırlarda ESERİN TÜRKÇE ADI sütununa orijinal Arapça ad yazılır."
    )
    ws_note.column_dimensions["A"].width = 100
    ws_note["A1"].alignment = Alignment(wrap_text=True)
    # yardımcı sayfa: id + Arapça orijinal
    ws2 = wb.create_sheet("ID")
    ws2.append(["NO", "YAZAR", "eser_id", "book_id", "eser_ar", "tarih"])
    for i, r in enumerate(rows, 1):
        ws2.append([i, r["yazar"], r["eser_id"], r["book_id"], r["ar"], r.get("tarih")])
    wb.save(path)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", required=True, help="örn. 01_akaid")
    args = ap.parse_args()
    cat = args.cat.strip()
    if cat in DEFERRED_HADIS_CATS:
        print("Hadis kategorisi bu turda ertelendi (06–10). Sonra ayrı üretilecek:", cat)
        return 3
    if cat not in READY_CATS:
        print("Bu kategori envanter listesinde yok:", cat)
        print("Açık:", ", ".join(sorted(READY_CATS)))
        return 2
    rows = collect_cat(cat)
    path = write_xlsx(cat, rows)
    print(json.dumps({"ok": True, "cat": cat, "rows": len(rows), "path": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
