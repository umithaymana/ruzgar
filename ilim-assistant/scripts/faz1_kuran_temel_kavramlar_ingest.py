# -*- coding: utf-8 -*-
"""Faz 1 ek — Kur'an temel metadata + kavram / tecvid giriş sözlüğü.

Mimar emri: sure/ayet/kronoloji/sıralama/tecvid ve dinî-Arapça terimler
eksiksiz yüklensin ki Rüzgar doğru analiz etsin.

Çıktılar:
  knowledge/ilim/din/01_kuran/metadata/sureler.json   (zenginleştirilmiş)
  knowledge/ilim/din/01_kuran/metadata/cuz_hizb.json
  knowledge/ilim/din/01_kuran/metadata/nuzul_sirasi.json
  knowledge/ilim/din/01_kuran/temel_kavramlar.jsonl
  knowledge/ilim/din/01_kuran/tecvid_giris.jsonl
  knowledge/ilim/din/01_kuran/incremental/*.md
  knowledge/ilim/din/01_kuran/manifest_temel.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KURAN = ROOT / "knowledge" / "ilim" / "din" / "01_kuran"
META = KURAN / "metadata"
INCR = KURAN / "incremental"
AYETLER = KURAN / "ayetler.jsonl"

# Ayet sayıları (1..114) — standart mushaf
AYET_SAYILARI = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111,
    110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45,
    83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55,
    78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20,
    56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21,
    11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
]

# Arapça sure adları (Osmânî / yaygın)
SURE_ADI_AR = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف",
    "الأنفال", "التوبة", "يونس", "هود", "يوسف", "الرعد", "إبراهيم", "الحجر",
    "النحل", "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج", "المؤمنون",
    "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص",
    "الزمر", "غافر", "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية",
    "الأحقاف", "محمد", "الفتح", "الحجرات", "ق", "الذاريات", "الطور", "النجم",
    "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك",
    "القلم", "الحاقة", "المعارج", "نوح", "الجن", "المزمل", "المدثر",
    "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس", "التكوير",
    "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى",
    "الغاشية", "الفجر", "البلد", "الشمس", "الليل", "الضحى", "الشرح", "التين",
    "العلق", "القدر", "البينة", "الزلزلة", "العاديات", "القارعة", "التكاثر",
    "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون",
    "النصر", "المسد", "الإخلاص", "الفلق", "الناس",
]

SURE_ADI_TR = [
    "Fâtiha", "Bakara", "Âl-i İmrân", "Nisâ", "Mâide", "En'âm", "A'râf", "Enfâl",
    "Tevbe", "Yûnus", "Hûd", "Yûsuf", "Ra'd", "İbrâhîm", "Hicr", "Nahl", "İsrâ",
    "Kehf", "Meryem", "Tâhâ", "Enbiyâ", "Hac", "Mü'minûn", "Nûr", "Furkân",
    "Şuarâ", "Neml", "Kasas", "Ankebût", "Rûm", "Lokmân", "Secde", "Ahzâb",
    "Sebe'", "Fâtır", "Yâsîn", "Sâffât", "Sâd", "Zümer", "Mü'min (Gâfir)",
    "Fussilet", "Şûrâ", "Zuhruf", "Duhân", "Câsiye", "Ahkâf", "Muhammed",
    "Fetih", "Hucurât", "Kâf", "Zâriyât", "Tûr", "Necm", "Kamer", "Rahmân",
    "Vâkıa", "Hadîd", "Mücâdele", "Haşr", "Mümtehine", "Saff", "Cuma",
    "Münâfikûn", "Teğâbün", "Talâk", "Tahrîm", "Mülk", "Kalem", "Hâkka",
    "Meâric", "Nûh", "Cin", "Müzzemmil", "Müddessir", "Kıyâme", "İnsan",
    "Mürselât", "Nebe'", "Nâziât", "Abese", "Tekvîr", "İnfitâr", "Mutaffifîn",
    "İnşikâk", "Bürûc", "Târık", "A'lâ", "Gâşiye", "Fecr", "Beled", "Şems",
    "Leyl", "Duhâ", "İnşirâh", "Tîn", "Alak", "Kadr", "Beyyine", "Zilzâl",
    "Âdiyât", "Kâria", "Tekâsür", "Asr", "Hümeze", "Fîl", "Kureyş", "Mâûn",
    "Kevser", "Kâfirûn", "Nasr", "Tebbet (Mesed)", "İhlâs", "Felak", "Nâs",
]

# Standart Medenî sûreler (Mısır / yaygın Diyanet uyumlu liste; ihtilaflılar notlu)
MEDENI = {
    2, 3, 4, 5, 8, 9, 13, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60, 61, 62,
    63, 64, 65, 66, 76, 98, 99, 110,
}
# İhtilaflı / tartışmalı sınıflandırma notu
IHTILAFLI = {13, 22, 55, 76, 99}  # bazı âlimlerde Mekkî sayılır

# Nüzûl sırası: liste[i] = mushaf sure_no (i=0 → ilk inen)
# Klasik Mısır kronolojik sırası (yaygın eğitim standardı)
NUZUL_ORDER = [
    96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108, 102, 107,
    109, 105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106, 101, 75, 104, 77,
    50, 90, 86, 54, 38, 7, 72, 36, 25, 35, 19, 20, 56, 26, 27, 28, 17, 10, 11,
    12, 15, 6, 37, 31, 34, 39, 40, 41, 42, 43, 44, 45, 46, 51, 88, 18, 16, 71,
    14, 21, 23, 32, 52, 67, 69, 70, 78, 79, 82, 84, 30, 29, 83, 2, 8, 3, 33,
    60, 4, 99, 57, 47, 13, 55, 76, 65, 98, 59, 24, 22, 63, 58, 49, 66, 64, 61,
    62, 48, 5, 9, 110,
]

# 30 cüz başlangıç (sure, ayet) — standart mushaf
CUZ_START = [
    (1, 1), (2, 142), (2, 253), (3, 92), (4, 24), (4, 148), (5, 82), (6, 111),
    (7, 88), (8, 41), (9, 93), (11, 6), (12, 53), (15, 1), (17, 1), (18, 75),
    (21, 1), (23, 1), (25, 21), (27, 56), (29, 46), (33, 31), (36, 28),
    (39, 32), (41, 47), (46, 1), (51, 31), (58, 1), (67, 1), (78, 1),
]

KAYNAK_NOTU = (
    "Diyanet mushaf düzeni + klasik Mısır kronolojik nüzûl sırası / "
    "yaygın Medenî-Mekkî sınıflandırması. İhtilaflı sûreler işaretlidir. "
    "Tecvid giriş: kısa usul özeti (tam ilmihal değil)."
)


def _nuzul_map() -> dict[int, int]:
    """sure_no -> nüzûl sırası (1..114)."""
    return {sno: i + 1 for i, sno in enumerate(NUZUL_ORDER)}


def _build_sureler(existing: list[dict] | None) -> list[dict]:
    by_no = {int(r["sure_no"]): r for r in (existing or []) if r.get("sure_no")}
    nmap = _nuzul_map()
    out: list[dict] = []
    for i in range(114):
        sno = i + 1
        old = by_no.get(sno) or {}
        row = {
            "sure_no": sno,
            "mushaf_sirasi": sno,
            "nuzul_sirasi": nmap[sno],
            "sure_adi_tr": SURE_ADI_TR[i],
            "sure_adi_ar": SURE_ADI_AR[i],
            "ayet_sayisi": AYET_SAYILARI[i],
            "iniş": "Medenî" if sno in MEDENI else "Mekkî",
            "inis_ihtilafli": sno in IHTILAFLI,
            "kaynak_notu": KAYNAK_NOTU,
        }
        # eski alanları koru (varsa)
        for k, v in old.items():
            if k not in row and v not in (None, ""):
                row[k] = v
        out.append(row)
    return out


def _build_cuz() -> dict:
    items = []
    for i, (s, a) in enumerate(CUZ_START, start=1):
        end_s, end_a = (CUZ_START[i] if i < 30 else (114, 6))
        # bitiş: sonraki cüzden bir ayet önce — basit etiket
        items.append(
            {
                "cuz_no": i,
                "baslangic_sure": s,
                "baslangic_ayet": a,
                "baslangic_sure_adi": SURE_ADI_TR[s - 1],
                "sonraki_cuz_baslangic": (
                    {"sure": end_s, "ayet": end_a} if i < 30 else None
                ),
            }
        )
    return {
        "ok": True,
        "cuz_sayisi": 30,
        "hizb_sayisi": 60,
        "not": "Her cüz ≈ 2 hizb; hizb ≈ 4 rub'. Tam hizb sınırları mushaf işaretlerine göredir.",
        "items": items,
        "kaynak_notu": KAYNAK_NOTU,
    }


def _kavramlar() -> list[dict]:
    """Temel dinî / Kur'anî / Arapça terimler — Rüzgar anlık cevap için."""
    rows: list[tuple[str, str, list[str]]] = [
        (
            "sure",
            "Sûre (سورة), Kur'an-ı Kerîm'in bağımsız bölümüdür. Mushafta 114 sûre vardır. "
            "Her sûrenin bir adı, ayet sayısı ve (çoğunlukla) Mekkî veya Medenî oluşu bellidir. "
            "Mushaf sırası (Fâtiha'dan Nâs'a) nüzûl (iniş) sırasından farklıdır.",
            ["sûre", "sure nedir", "sûre nedir", "sure ne demek"],
        ),
        (
            "ayet",
            "Âyet (آية), Kur'an'ın en küçük anlamlı birimidir; mucize / işaret anlamı da taşır. "
            "Toplam 6236 ayet (Diyanet / standart sayım; bazı geleneklerde besmele sayımı fark eder). "
            "Atıf biçimi: sûre adı veya numarası + ayet numarası (örn. Bakara 2:255).",
            ["âyet", "ayet nedir", "âyet nedir", "ayet ne demek"],
        ),
        (
            "mushaf",
            "Mushaf (مصحف), Kur'an metninin yazılı derlemesidir. Bugün yaygın Osmânî imlâ "
            "üzerine kurulu mushaflar kullanılır. Mushaf sırası Hz. Osmân döneminde sabitlenen "
            "tertibe göredir; ilk sûre Fâtiha, son sûre Nâs'tır.",
            ["mushaf nedir", "mushaflar"],
        ),
        (
            "nuzul_kronoloji",
            "Nüzûl (iniş) kronolojisi, ayet ve sûrelerin vahiy sürecindeki zaman sırasını ifade eder. "
            "İlk inen ayetler Alak sûresinin başındadır (96). Mushaf sırası ≠ nüzûl sırası. "
            "Kronoloji âlim rivayetlerine dayanır; bazı sûrelerde ihtilaf vardır.",
            ["nüzul", "nüzûl", "kronoloji", "iniş sırası", "nüzul sırası", "hangi sure önce indi"],
        ),
        (
            "mushaf_sirasi",
            "Mushaf sıralaması (tertîb), Kur'an'ın ciltlenmiş mushaftaki 1–114 sırasıdır. "
            "1. Fâtiha, 2. Bakara … 114. Nâs. Namazda ve ezberde bu sıra kullanılır; "
            "tarihî iniş sırası için nüzûl sırasına bakılır.",
            ["sıralama", "mushaf sırası", "sure sırası", "tertib", "tertîb"],
        ),
        (
            "mekki_medeni",
            "Mekkî sûreler hicretten önce; Medenî sûreler hicretten sonra inmiştir (genel kural). "
            "Mekkîler daha çok tevhid, ahiret, ahlak; Medenîler hukuk, toplum, cihad, münafık "
            "konularına ağırlık verir. Bazı sûrelerde sınıflandırma ihtilaflıdır.",
            ["mekki", "medenî", "medeni", "mekkî", "hicret öncesi"],
        ),
        (
            "cuz",
            "Cüz (جزء), Kur'an'ın 30 eşit parçaya bölünmesidir; hatim kolaylığı içindir. "
            "1. cüz Fâtiha ile başlar; 30. cüz Nebe' ile başlar. Her cüz kabaca iki hizbe ayrılır.",
            ["cüz", "cuz", "cüz nedir", "30 cüz"],
        ),
        (
            "hizb",
            "Hizb (حزب), cüzün yarısıdır; mushafta 60 hizb bulunur. Her hizb dört rub'a "
            "(çeyreğe) ayrılabilir. Tilavet ve hatim planında kullanılır.",
            ["hizb", "hizip", "rub"],
        ),
        (
            "ruku",
            "Rükû' (ركوع) işareti, bazı mushaflarda konu bütünlüğüne göre ayet gruplarını "
            "gösterir. Namazdaki rükûdan farklı bir işaretleme geleneğidir.",
            ["rüku", "rükû", "ruku"],
        ),
        (
            "besmele",
            "Besmele: «Bismillâhirrahmânirrahîm». Tevbe sûresi dışında her sûre başında yazılır. "
            "Fâtiha'da ayet sayılıp sayılmadığı mezheplere göre değişir; Diyanet mealinde "
            "genelde Fâtiha'nın 1. ayeti olarak yer alır.",
            ["besmele", "bismillah"],
        ),
        (
            "meal",
            "Meal, Kur'an'ın başka bir dile anlam aktarımıdır; vahyin Arapça lafzının "
            "yerine geçmez. Türkiye'de Diyanet Kur'an Yolu ve DİB Cep Meal yaygın mealdir. "
            "Rüzgar yerel kütüphanesinde her iki meal de vardır.",
            ["meal nedir", "meâl", "çeviri kuran"],
        ),
        (
            "tefsir",
            "Tefsir (تفسير), ayetlerin açıklanması ve yorumudur. Mealden daha geniştir; "
            "dil, sebeb-i nüzûl, hadis, fıkıh ve kelam delilleri kullanılabilir. "
            "Rüzgar kütüphanesinde Kur'an Yolu ile İbn Kesîr, Taberî, Kurtubî, Beyzâvî, Râzî vardır.",
            ["tefsir nedir", "müfessir", "mufessir"],
        ),
        (
            "sebeb_i_nuzul",
            "Sebeb-i nüzûl, bir ayetin inişine vesile olan olay veya sorudur. Her ayetin "
            "bilinen bir sebebi yoktur; olanlar tefsir ve hadis kaynaklarında rivayet edilir.",
            ["sebeb-i nüzul", "sebebi nüzul", "iniş sebebi"],
        ),
        (
            "tecvid",
            "Tecvid (تجويد), Kur'an'ı harflerin hakkını vererek, doğru mahreç ve sıfatlarla "
            "okuma ilmidir. Med, idgam, ihfa, iklab, gunne, vakıf gibi kuralları vardır. "
            "Rüzgar'daki kısa tecvid girişi özet usuldür; icazetli tilavet insan hocası ister.",
            ["tecvid", "tecvit", "tecvid nedir", "tilavet kuralı"],
        ),
        (
            "kiraat",
            "Kıraat (قراءة), Kur'an'ın mütevâtir okunuş vecihleridir. En yaygın: Âsım kıraati "
            "(Hafs rivayeti). Farklı kıraatler bazı kelimelerde telaffuz / anlam nüansı doğurur.",
            ["kıraat", "kiraat", "hafs", "asim"],
        ),
        (
            "mahreç",
            "Mahreç (مخرج), harfin ağız/boğaz/dil üzerindeki çıkış yeridir. Tecvidde her "
            "harfin mahreci ve sıfatı (şiddet, rihvet, tefhim, terkik…) vardır.",
            ["mahreç", "mahrec", "harf çıkışı"],
        ),
        (
            "med",
            "Med (مد), sesin uzatılmasıdır. Tabii med ~1 elif; muttasıl, munfasıl, lazım "
            "gibi çeşitlerde uzatma miktarı artar. TTS motorları med uzunluğunu tam vermez.",
            ["med", "uzatma", "meddi tabii"],
        ),
        (
            "idgam",
            "İdgam (إدغام), nun sakin / tenvin sonrası ي ن م و harflerinde sesin "
            "kaynaşmasıdır. İdgam-ı mea'l-gunne ve bila gunne çeşitleri vardır.",
            ["idgam", "idğam"],
        ),
        (
            "ihfa",
            "İhfa (إخفاء), nun sakin / tenvin sonrası belirli harflerde gizleyerek "
            "okumaktır; tam izhar veya tam idgam değildir, gunne ile yapılır.",
            ["ihfa", "ihfâ"],
        ),
        (
            "iklab",
            "İklab (إقلاب), nun sakin / tenvin sonrası ب harfinde nun'un mim'e "
            "dönüştürülerek gunne ile okunmasıdır.",
            ["iklab", "iqlab"],
        ),
        (
            "izhar",
            "İzhar (إظهار), nun sakin / tenvin sonrası boğaz harflerinde (ء ه ع ح غ خ) "
            "nun'un açık ve net okunmasıdır.",
            ["izhar", "izhâr"],
        ),
        (
            "vakif",
            "Vakıf (وقف), okurken duraktır. Ayet sonu, lâzim vakıf, caiz vakıf gibi "
            "işaretler mushafta bulunur. Anlamı bozmayacak yerde durmak esastır.",
            ["vakıf", "vakif", "durak", "tilavet durak"],
        ),
        (
            "secde_ayeti",
            "Secde ayeti, okunduğunda veya işitildiğinde tilavet secdesi yapılan ayettir. "
            "Kur'an'da bilinen secde ayetleri vardır (örn. A'râf 206, Secde 15, Fussilet 37…). "
            "Fıkhî ayrıntı mezhebe göre değişebilir.",
            ["secde ayeti", "tilavet secdesi"],
        ),
        (
            "hatim",
            "Hatim, Kur'an'ı baştan sona okuyup bitirmektir. Genelde 30 cüz üzerinden "
            "planlanır (günde bir cüz ≈ bir ayda hatim).",
            ["hatim", "hatim nedir"],
        ),
        (
            "ulumul_kuran",
            "Ulûmu'l-Kur'an, Kur'an ilimleridir: nüzûl, mecaz, muhkem-müteşabih, "
            "nesih, kıraat, tecvid, tefsir usulü vb. Rüzgar bunları kaynaklı özetler; "
            "fetva vermez.",
            ["ulumul kuran", "kur'an ilimleri", "ulûmu'l-kur'an"],
        ),
        (
            "muhkem_mutesabih",
            "Muhkem ayetler anlamı açık olanlar; müteşâbih ayetler te'vil gerektiren "
            "veya birden fazla yoruma açık olanlardır. Âl-i İmrân 7 bu ayrımı zikreder.",
            ["muhkem", "müteşabih", "mutesabih"],
        ),
        (
            "nesih",
            "Nesih (نسخ), bazı hüküm ayetlerinin sonradan inen ayetlerle yürürlükten "
            "kalkmasıdır (usûl tartışması geniştir). Meal/tefsirde ihtiyatlı işaretlenir.",
            ["nesih", "mensuh", "nâsih"],
        ),
        (
            "vahiy",
            "Vahiy, Allah'ın peygamberine bildirimidir. Kur'an, Hz. Muhammed'e (s.a.v.) "
            "Cebrail vasıtasıyla indirilen kelâmullah'tır.",
            ["vahiy", "vahy"],
        ),
        (
            "kelamullah",
            "Kelâmullah, Allah'ın kelamıdır. Kur'an bu sıfatla anılır; meal ve tefsir "
            "beşerî açıklamalardır, asıl metin Arapça vahiydir.",
            ["kelamullah", "kelâmullah"],
        ),
        (
            "ayetel_kursi",
            "Âyetü'l-Kürsî, Bakara sûresi 255. ayettir. Allah'ın birliği, hayy ve kayyûm "
            "sıfatları ve kudreti anlatılır; fazileti hadislerde sık geçer.",
            ["ayetel kursi", "ayatul kursi", "âyetü'l-kürsî", "kursi ayeti"],
        ),
        (
            "fatiha",
            "Fâtiha, mushafın ilk sûresidir (7 ayet). Ümmü'l-Kitâb / es-Seb'u'l-Mesânî "
            "olarak da anılır; namazda okunur. Nüzûl sırasında erken Mekkî sûrelerdendir.",
            ["fatiha nedir", "fâtiha", "ummi kitab"],
        ),
        (
            "arapca_kuran",
            "Kur'an Arapça indirilmiştir. Tilavet Arapça lafızladır; Türkçe meal anlam "
            "yardımcısıdır. Rüzgar ayet sorularında Arapça metin + Türkçe meal birlikte verir.",
            ["arapça kuran", "kuran dili"],
        ),
        (
            "cuz_hatim_plan",
            "Günde bir cüz okumak yaklaşık bir ayda hatim demektir. Cüz numarası mushaf "
            "kenarındaki işaretlerle takip edilir; Rüzgar cüz başlangıçlarını bilir.",
            ["hatim planı", "günde bir cüz"],
        ),
        (
            "sahabe_tedvin",
            "Kur'an Hz. Peygamber döneminde ezberlenip yazılmış; Hz. Ebû Bekir döneminde "
            "cem edilmiş, Hz. Osmân döneminde tek mushaf nüshası çoğaltılmıştır. "
            "Bugünkü tertip bu Osmânî mushafa dayanır.",
            ["tedvin", "osman mushafı", "cem'i kuran"],
        ),
        (
            "isim_ul_kuran",
            "Kur'an'ın adları arasında el-Kitâb, el-Furkân, ez-Zikr, et-Tenzîl vardır. "
            "Her biri vahyin bir yönünü vurgular.",
            ["furkan", "tenzil", "ez zikr"],
        ),
        (
            "secavend",
            "Secâvend / vakıf işaretleri (م ط ج ز صلي قلي …) mushafta durulacak "
            "veya geçilecek yerleri gösterir. Anlamı bozacak yerde durulmaz.",
            ["secavend", "vakıf işaretleri", "mim vakıf"],
        ),
        (
            "tenvin",
            "Tenvin, ismin sonundaki çift harekedir (ً ٍ ٌ); nun sakin gibi tecvid "
            "kurallarına (izhar, idgam, ihfa, iklab) girer.",
            ["tenvin", "tenvîn"],
        ),
        (
            "hareke",
            "Hareke (fetha, kesra, damme) harfin kısa sesini gösterir. Sükûn harekesizlik; "
            "şedde (teşdid) harfin iki kez okunmasıdır.",
            ["hareke", "fetha", "kesra", "damme", "şedde", "sükun"],
        ),
        (
            "lafzi_manawi",
            "Lafzî okuma Arapça kelimeleri; manevî okuma anlamı kavramaktır. "
            "İdeal tilavet ikisini birleştirir: tecvidli okuyuş + meal/tefsir.",
            ["lafzi", "manawi", "anlayarak okuma"],
        ),
        (
            "esbab",
            "Esbâb-ı nüzûl literatürü, ayetlerin iniş bağlamını toplar. "
            "Bağlam tefsire yardımcı olur; her ayete zorla sebep aranmaz.",
            ["esbabı nüzul", "esbab-ı nüzul"],
        ),
        (
            "uc_sure",
            "Felak ve Nâs (Muavvizeteyn) ile İhlâs sık birlikte okunur; "
            "korunma ve tevhid vurgusu taşırlar. Fâtiha ile birlikte namaz ve tilavette "
            "merkezîdirler.",
            ["muavvizeteyn", "ihlas felak nas"],
        ),
    ]
    out: list[dict] = []
    for kid, text, aliases in rows:
        out.append(
            {
                "id": kid,
                "collection": "din_01_kuran_kavram",
                "baslik": kid,
                "aliases": aliases,
                "metin": text,
                "kaynak_notu": KAYNAK_NOTU,
            }
        )
    return out


def _tecvid_giris() -> list[dict]:
    rows = [
        (
            "tecvid_tanim",
            "Tecvid girişi",
            "Tecvid, harfleri mahreç ve sıfatlarına uygun okuyup med/gunne/vakıf "
            "kurallarına riayet etmektir. Amaç: lahn (hata) olmadan tilavet.",
        ),
        (
            "nun_sakin_ozet",
            "Nûn sâkin / tenvin",
            "Nûn sâkin veya tenvin sonrası: izhar (boğaz harfleri), idgam (ي ن م و), "
            "iklab (ب), ihfa (kalan harfler). Bu dörtlü tecvidin temelidir.",
        ),
        (
            "mim_sakin_ozet",
            "Mîm sâkin",
            "Mîm sâkin sonrası: ihfa şefevi (ب), idgam misleyn (م), izhar şefevi (diğer).",
        ),
        (
            "med_ozet",
            "Med çeşitleri (özet)",
            "Tabii med (~1 elif); munfasıl / muttasıl med; medd-i lâzım (en uzun). "
            "Uygulamalı ölçü icazetli hocadan öğrenilir.",
        ),
        (
            "kalkale",
            "Kalkale",
            "Kalkale, sakin ق ط ب ج د harflerinde titreşimli çıkıştır (özellikle vakıfta).",
        ),
        (
            "gunne",
            "Gunne",
            "Gunne, burundan gelen tınlamadır; idgam mea'l-gunne, ihfa ve iklabda vardır.",
        ),
        (
            "lahn",
            "Lahn",
            "Lahn, tilavette hatadır. Celî lahn anlamı bozar; hafî lahn incelik hatalarıdır.",
        ),
        (
            "ruzgar_sinir",
            "Rüzgar tilavet sınırı",
            "Rüzgar TTS ile okuyabilir; tecvidi tam icra eden insan kıraati değildir. "
            "Durak süreleri simüle edilir; med/mahreç için hoca veya kayıtlı kıraat gerekir.",
        ),
    ]
    return [
        {
            "id": rid,
            "collection": "din_01_kuran_tecvid",
            "baslik": title,
            "metin": text,
            "kaynak_notu": KAYNAK_NOTU,
        }
        for rid, title, text in rows
    ]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_incremental(kavramlar: list[dict], tecvid: list[dict], sureler: list[dict]) -> None:
    INCR.mkdir(parents=True, exist_ok=True)
    # kavram batch
    lines = ["# Kur'an — temel kavramlar\n", f"Kaynak notu: {KAYNAK_NOTU}\n"]
    for r in kavramlar:
        lines.append(f"\n## {r['baslik']}\n")
        lines.append(r["metin"] + "\n")
        if r.get("aliases"):
            lines.append("Anahtarlar: " + ", ".join(r["aliases"]) + "\n")
    (INCR / "kavramlar_temel.md").write_text("".join(lines), encoding="utf-8")

    tlines = ["# Kur'an — tecvid giriş (kısa usul)\n", f"Kaynak notu: {KAYNAK_NOTU}\n"]
    for r in tecvid:
        tlines.append(f"\n## {r['baslik']}\n")
        tlines.append(r["metin"] + "\n")
    (INCR / "tecvid_giris.md").write_text("".join(tlines), encoding="utf-8")

    # sure katalog özeti (ilk 40 + not)
    slines = [
        "# 114 sûre — mushaf / nüzûl / iniş özeti\n",
        f"Kaynak notu: {KAYNAK_NOTU}\n\n",
        "| No | Ad | Ayet | İniş | Nüzûl sırası |\n|---:|---|---:|---|---:|\n",
    ]
    for r in sureler:
        flag = "*" if r.get("inis_ihtilafli") else ""
        slines.append(
            f"| {r['sure_no']} | {r['sure_adi_tr']} | {r['ayet_sayisi']} | "
            f"{r['iniş']}{flag} | {r['nuzul_sirasi']} |\n"
        )
    slines.append("\n\\* = iniş sınıflandırması ihtilaflı olabilir.\n")
    (INCR / "sureler_katalog.md").write_text("".join(slines), encoding="utf-8")


def main() -> None:
    META.mkdir(parents=True, exist_ok=True)
    existing = []
    sp = META / "sureler.json"
    if sp.is_file():
        existing = json.loads(sp.read_text(encoding="utf-8"))

    sureler = _build_sureler(existing)
    sp.write_text(json.dumps(sureler, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cuz = _build_cuz()
    (META / "cuz_hizb.json").write_text(
        json.dumps(cuz, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    nuzul_doc = {
        "ok": True,
        "aciklama": "nuzul_sirasi: 1=ilk inen. Liste mushaf sure numarasıdır.",
        "sira_mushaf_no": NUZUL_ORDER,
        "sure_no_to_nuzul": _nuzul_map(),
        "kaynak_notu": KAYNAK_NOTU,
    }
    (META / "nuzul_sirasi.json").write_text(
        json.dumps(nuzul_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    kavramlar = _kavramlar()
    tecvid = _tecvid_giris()
    _write_jsonl(KURAN / "temel_kavramlar.jsonl", kavramlar)
    _write_jsonl(KURAN / "tecvid_giris.jsonl", tecvid)
    _write_incremental(kavramlar, tecvid, sureler)

    # ayet sayısı doğrula
    ayet_count = 0
    if AYETLER.is_file():
        ayet_count = sum(1 for _ in AYETLER.open(encoding="utf-8") if _.strip())

    manifest = {
        "ok": True,
        "version": "din-01-kuran-temel-kavramlar-v1",
        "yukleme_tarihi": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collection": "din_01_kuran_kavram",
        "kaynak_notu": KAYNAK_NOTU,
        "qa": {
            "sure_adet": len(sureler),
            "sure_beklenen": 114,
            "kavram_adet": len(kavramlar),
            "tecvid_madde": len(tecvid),
            "cuz_adet": 30,
            "nuzul_liste_uzunluk": len(NUZUL_ORDER),
            "ayetler_jsonl_satir": ayet_count,
            "ayet_beklenen": 6236,
            "mekki_adet": sum(1 for s in sureler if s["iniş"] == "Mekkî"),
            "medeni_adet": sum(1 for s in sureler if s["iniş"] == "Medenî"),
        },
        "dosyalar": {
            "sureler": "metadata/sureler.json",
            "cuz_hizb": "metadata/cuz_hizb.json",
            "nuzul_sirasi": "metadata/nuzul_sirasi.json",
            "temel_kavramlar": "temel_kavramlar.jsonl",
            "tecvid_giris": "tecvid_giris.jsonl",
            "incremental": "incremental/",
        },
    }
    (KURAN / "manifest_temel.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # README güncelle
    readme = KURAN / "README.md"
    extra = (
        "\n## Temel kavramlar (Faz 1 ek)\n\n"
        "| Dosya | Açıklama |\n|-------|----------|\n"
        "| `metadata/sureler.json` | 114 sure — ad TR/AR, ayet, Mekkî/Medenî, nüzûl sırası |\n"
        "| `metadata/nuzul_sirasi.json` | İniş kronolojisi |\n"
        "| `metadata/cuz_hizb.json` | 30 cüz başlangıçları |\n"
        "| `temel_kavramlar.jsonl` | Sûre, âyet, meal, tefsir, tecvid… tanımları |\n"
        "| `tecvid_giris.jsonl` | Kısa tecvid usulü |\n"
        "| `incremental/*.md` | RAG için düz metin |\n"
    )
    if readme.is_file():
        t = readme.read_text(encoding="utf-8")
        if "Temel kavramlar" not in t:
            readme.write_text(t.rstrip() + "\n" + extra, encoding="utf-8")
    else:
        readme.write_text("# Din / 01 — Kur'an-ı Kerim\n" + extra, encoding="utf-8")

    print(json.dumps(manifest["qa"], ensure_ascii=False, indent=2))
    print("OK", KURAN)


if __name__ == "__main__":
    main()
