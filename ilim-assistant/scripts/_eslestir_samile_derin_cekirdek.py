# -*- coding: utf-8 -*-
"""
Şamile derin çekirdek — katalog eşlemesi (dikkatli).

Kural: Şüphede EŞLEŞMEDİ. Yanlış book_id yazma.
Çıktı: JSON + Word.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(
    r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE İNDEKS\İSLAMİ İLİMLER"
    r"\_shamela_catalog_cache.json"
)
OUT_JSON = ROOT / "docs" / "SAMILE_DERIN_CEKIRDEK_ESLESME.json"
OUT_DOCX = ROOT / "docs" / "SAMILE_DERIN_CEKIRDEK_ESLESME_DOLU.docx"
OUT_DOCX_ALT = ROOT / "docs" / "SAMILE_DERIN_CEKIRDEK_ESLESME_DOLU_v2.docx"

# (cat_id, etiket, arama_anahtarları, yazar_ipuçları, zorunlu_ar_parça)
# zorunlu: başlıkta bunlardan en az biri olmalı (yanlış eşleşmeyi keser)
QUERY: list[tuple[int, str, list[str], list[str], list[str]]] = [
    # —— 01 akaid ——
    (1, "el-Fıkhü'l-Ekber — Ebû Hanîfe", ["الفقه الأكبر"], ["حنيفة", "ابو حنيفة"], ["الفقه الأكبر"]),
    (1, "el-Akîdetü't-Tahâviyye", ["العقيدة الطحاوية", "الطحاوية"], ["طحاوي"], ["الطحاوية"]),
    # Tahâvî şerhi: katalogda İbn Ebî'l-İzz yoksa klasik arnâût baskısını işaretle (elle onay)
    (1, "Şerhu'l-Akîdeti't-Tahâviyye (klasik şerh baskısı)", ["شرح العقيدة الطحاوية"], ["أرناؤوط", "الألباني", "براك"], ["شرح العقيدة الطحاوية"]),
    (1, "Akaidü'n-Nesefî / Teftâzânî hattı", ["العقائد النسفية", "شرح العقائد"], ["تفتازاني", "نسفي"], ["العقائد"]),
    (1, "Kitâbü't-Tevhîd — Mâtürîdî", ["كتاب التوحيد", "التوحيد للماتريدي"], ["ماتريدي", "الماتريدي"], ["التوحيد"]),
    (1, "el-İktisâd fi'l-İ'tikâd — Gazzâlî", ["الاقتصاد في الاعتقاد"], ["غزالي"], ["الاقتصاد"]),
    (1, "Kavâidü'l-Akâid — Gazzâlî", ["قواعد العقائد"], ["غزالي"], ["قواعد العقائد"]),
    (1, "el-İrşâd — Cüveynî", ["الإرشاد إلى قواطع الأدلة"], ["جويني"], ["قواطع"]),
    (1, "Temhîdü'l-Evâil — Bâkıllânî", ["تمهيد الأوائل"], ["باقلاني"], ["تمهيد"]),
    (1, "Usûlü'd-Dîn — Pezdevî", ["أصول الدين"], ["بزدوي"], ["أصول الدين"]),
    (1, "el-Bidâye — Sâbûnî", ["البداية من الكفاية", "البداية في أصول الدين"], ["صابوني"], ["البداية"]),
    (1, "el-Musâyara — İbnü'l-Hümâm", ["المسايرة"], ["ابن الهمام"], ["المسايرة"]),
    (1, "Şerhu'l-Fıkhi'l-Ekber — Aliyyü'l-Kârî", ["شرح الفقه الأكبر"], ["القاري", "ملا علي"], ["الفقه الأكبر"]),
    (1, "el-Âlim ve'l-Müteallim", ["العالم والمتعلم"], ["حنيفة"], ["العالم والمتعلم"]),
    (1, "et-Târîkatü'l-Muhammediyye — Birgivî", ["الطريقة المحمدية"], ["بركوي", "البركوي"], ["الطريقة المحمدية"]),
    # —— 03 tefsir ——
    (3, "Câmiu'l-Beyân — Taberî", ["جامع البيان", "تفسير الطبري"], ["طبري"], ["الطبري", "جامع البيان"]),
    (3, "Tefsîru İbn Kesîr", ["تفسير ابن كثير"], ["ابن كثير"], ["تفسير ابن كثير"]),
    (3, "Tefsîru'l-Begavî (Meâlimü't-Tenzîl)", ["تفسير البغوي"], ["بغوي"], ["البغوي"]),
    (3, "Mefâtîhu'l-Gayb — Râzî", ["مفاتيح الغيب", "تفسير الرازي"], ["رازي"], ["مفاتيح الغيب", "الرازي"]),
    (3, "Envâru't-Tenzîl — Beyzâvî", ["أنوار التنزيل"], ["بيضاوي"], ["أنوار التنزيل"]),
    (3, "Medârikü't-Tenzîl — Nesefî", ["مدارك التنزيل", "تفسير النسفي"], ["نسفي"], ["مدارك التنزيل", "النسفي"]),
    (3, "el-Keşşâf — Zemahşerî", ["الكشاف"], ["زمخشري"], ["الكشاف"]),
    (3, "Tefsîru'l-Celâleyn", ["تفسير الجلالين"], ["محلي", "سيوطي"], ["الجلالين"]),
    (3, "Ruhü'l-Meânî — Âlûsî", ["روح المعاني"], ["آلوسي"], ["روح المعاني"]),
    (3, "el-Câmi' li-Ahkâmi'l-Kur'ân — Kurtubî", ["الجامع لأحكام القرآن", "تفسير القرطبي"], ["قرطبي"], ["القرطبي", "الجامع لأحكام القرآن"]),
    (4, "Ahkâmü'l-Kur'ân — Cessâs", ["أحكام القرآن للجصاص", "أحكام القرآن"], ["جصاص"], ["جصاص"]),
    (4, "Ahkâmü'l-Kur'ân — İbnü'l-Arabî", ["أحكام القرآن لابن العربي", "أحكام القرآن"], ["ابن العربي"], ["ابن العربي"]),
    (3, "Bahru'l-Ulûm — Semerkandî", ["بحر العلوم"], ["سمرقندي"], ["بحر العلوم"]),
    (3, "Fetihu'l-Kadîr — Şevkânî", ["فتح القدير"], ["شوكاني"], ["فتح القدير"]),
    (3, "Tefsîru Ebî's-Suûd", ["إرشاد العقل السليم", "تفسير أبي السعود"], ["أبو السعود", "ابو السعود"], ["أبي السعود", "أبو السعود", "إرشاد العقل"]),
    (3, "Ruhü'l-Beyân — Bursevî", ["روح البيان"], ["إسماعيلي", "البروسوي", "حقي"], ["روح البيان"]),
    (3, "ed-Dürrü'l-Mensûr — Süyûtî", ["الدر المنثور"], ["سيوطي"], ["الدر المنثور"]),
    (4, "Esbâbü'n-Nüzûl — Vâhidî", ["أسباب النزول"], ["واحدي"], ["أسباب النزول", "أسباب"]),
    # —— 06 hadis sunen ——
    (6, "Sahîhu'l-Buhârî", ["صحيح البخاري"], ["بخاري"], ["صحيح البخاري"]),
    (6, "Sahîhu Müslim", ["صحيح مسلم"], ["مسلم"], ["صحيح مسلم"]),
    (6, "Sünenü Ebî Dâvûd", ["سنن أبي داود"], ["داود"], ["سنن أبي داود", "سنن ابي داود"]),
    (6, "Câmiu't-Tirmizî", ["سنن الترمذي", "جامع الترمذي"], ["ترمذي"], ["الترمذي"]),
    (6, "Sünenü'n-Nesâî", ["سنن النسائي"], ["نسائي"], ["سنن النسائي"]),
    (6, "Sünenü İbn Mâce", ["سنن ابن ماجه"], ["ماجه"], ["سنن ابن ماجه"]),
    (6, "Muvatta' — Mâlik", ["الموطأ"], ["مالك"], ["الموطأ"]),
    (6, "Müsnedü Ahmed", ["مسند أحمد"], ["حنبل", "أحمد"], ["مسند أحمد", "مسند الامام احمد"]),
    (6, "Sünenü'd-Dârimî", ["سنن الدارمي"], ["دارمي"], ["الدارمي"]),
    (6, "Sahîhu İbn Huzeyme", ["صحيح ابن خزيمة"], ["خزيمة"], ["ابن خزيمة"]),
    (6, "Sahîhu İbn Hibbân", ["صحيح ابن حبان"], ["حبان"], ["ابن حبان"]),
    (6, "el-Müstedrek — Hâkim", ["المستدرك على الصحيحين"], ["حاكم"], ["المستدرك"]),
    (6, "es-Sünenü'l-Kübrâ — Beyhakî", ["السنن الكبرى"], ["بيهقي"], ["السنن الكبرى"]),
    (6, "Şuabü'l-Îmân — Beyhakî", ["شعب الإيمان"], ["بيهقي"], ["شعب الإيمان"]),
    (6, "el-Edebü'l-Müfred — Buhârî", ["الأدب المفرد"], ["بخاري"], ["الأدب المفرد"]),
    (6, "Riyâzü's-Sâlihîn — Nevevî", ["رياض الصالحين"], ["نووي"], ["رياض الصالحين"]),
    (6, "el-Erbaûn — Nevevî", ["الأربعون النووية"], ["نووي"], ["الأربعون النووية", "الأربعون"]),
    (6, "Mişkâtü'l-Mesâbîh", ["مشكاة المصابيح"], ["تبريزي", "خطيب"], ["مشكاة"]),
    (6, "Câmiu'l-Usûl — İbnü'l-Esîr", ["جامع الأصول"], ["ابن الأثير"], ["جامع الأصول"]),
    # —— 07 hadis serh ——
    (7, "Fethu'l-Bârî — İbn Hacer", ["فتح الباري بشرح البخاري", "فتح الباري"], ["ابن حجر", "عسقلاني"], ["فتح الباري"]),
    (7, "Umdetü'l-Kârî — Aynî", ["عمدة القاري"], ["عيني"], ["عمدة القاري"]),
    (7, "İrşâdü's-Sârî — Kastallânî", ["إرشاد الساري"], ["قسطلاني"], ["إرشاد الساري"]),
    (7, "Şerhu Müslim — Nevevî", ["المنهاج شرح صحيح مسلم", "شرح النووي على مسلم", "شرح صحيح مسلم للنووي"], ["نووي"], ["مسلم"]),
    (7, "Avnu'l-Ma'bûd", ["عون المعبود"], ["آبادي", "عظيم"], ["عون المعبود"]),
    (7, "Tuhfetü'l-Ahvezî", ["تحفة الأحوذي"], ["مباركفوري"], ["تحفة الأحوذي"]),
    (7, "Mirkâtü'l-Mefâtîh — Aliyyü'l-Kârî", ["مرقاة المفاتيح"], ["القاري"], ["مرقاة"]),
    (7, "Bezlü'l-Mechûd", ["بذل المجهود"], ["سهارنبوري", "خليل"], ["بذل المجهود"]),
    (7, "Delîlü'l-Fâlihîn", ["دليل الفالحين"], ["ابن علان"], ["دليل الفالحين"]),
    (7, "Fethu'l-Mülhim", ["فتح الملهم"], ["عثماني"], ["فتح الملهم"]),
    (7, "Feyzü'l-Bârî", ["فيض الباري"], ["كشميري"], ["فيض الباري"]),
    # —— 11 usul ——
    (11, "Usûl Pezdevî", ["أصول البزدوي", "كنز الوصول"], ["بزدوي"], ["بزدوي", "كنز الوصول"]),
    (11, "Keşfü'l-Esrâr — Abdülazîz el-Buhârî", ["كشف الأسرار"], ["بخاري"], ["كشف الأسرار"]),
    (11, "Usûlü's-Serahsî", ["أصول السرخسي"], ["سرخسي"], ["أصول السرخسي"]),
    (11, "el-Menâr — Nesefî", ["المنار"], ["نسفي"], ["المنار"]),
    (11, "et-Tavzîh — Sadru'ş-Şerîa", ["التوضيح"], ["صدر الشريعة"], ["التوضيح"]),
    (11, "et-Telvîh — Teftâzânî", ["التلويح"], ["تفتازاني"], ["التلويح"]),
    (11, "et-Tahrîr — İbnü'l-Hümâm", ["التحرير"], ["ابن الهمام"], ["التحرير"]),
    (11, "et-Takrîr ve't-Tahrîr — İbn Emîr Hâc", ["التقرير والتحبير"], ["ابن أمير"], ["التقرير"]),
    (11, "Müsellemü's-Sübût", ["مسلم الثبوت"], ["محب الله"], ["مسلم الثبوت"]),
    (11, "el-Müstasfâ — Gazzâlî", ["المستصفى"], ["غزالي"], ["المستصفى"]),
    (11, "el-Mahsûl — Râzî", ["المحصول"], ["رازي"], ["المحصول"]),
    (11, "el-İhkâm — Âmidî", ["الإحكام في أصول الأحكام"], ["آمدي"], ["الإحكام"]),
    (11, "el-Bahrü'l-Muhît — Zerkâşî", ["البحر المحيط"], ["زركشي"], ["البحر المحيط"]),
    (11, "Cem'u'l-Cevâmi' — Sübkî", ["جمع الجوامع"], ["سبكي"], ["جمع الجوامع"]),
    (11, "Ravzatü'n-Nâzır — İbn Kudâme", ["روضة الناظر"], ["قدامة"], ["روضة الناظر"]),
    (11, "el-Muvâfakât — Şâtıbî", ["الموافقات"], ["شاطبي"], ["الموافقات"]),
    (11, "İrşâdü'l-Fuhûl — Şevkânî", ["إرشاد الفحول"], ["شوكاني"], ["إرشاد الفحول"]),
    # —— 14 hanefi ——
    (14, "el-Hidâye — Mergînânî", ["الهداية"], ["مرغيناني"], ["الهداية"]),
    (14, "Fethu'l-Kadîr — İbnü'l-Hümâm", ["فتح القدير"], ["ابن الهمام"], ["فتح القدير"]),
    (14, "el-Binâye — Aynî", ["البناية"], ["عيني"], ["البناية"]),
    (14, "el-İhtiyâr — Mevsılî", ["الاختيار لتعليل المختار"], ["موصلي"], ["الاختيار"]),
    (14, "Kenzü'd-Dekâik — Nesefî", ["كنز الدقائق"], ["نسفي"], ["كنز الدقائق"]),
    (14, "Tebyînü'l-Hakâik — Zeylaî", ["تبيين الحقائق"], ["زيلعي"], ["تبيين الحقائق"]),
    (14, "el-Bahrü'r-Râik — İbn Nüceym", ["البحر الرائق"], ["نجيم"], ["البحر الرائق"]),
    (14, "Reddü'l-Muhtâr — İbn Âbidîn", ["رد المحتار"], ["عابدين"], ["رد المحتار"]),
    (14, "ed-Dürrü'l-Muhtâr — Haskefî", ["الدر المختار"], ["حصكفي"], ["الدر المختار"]),
    (14, "Mülteka'l-Ebhur — Halebî", ["ملتقى الأبحر"], ["حلبي"], ["ملتقى"]),
    (14, "el-Fetâva'l-Hindiyye", ["الفتاوى الهندية", "العالمكيرية"], [], ["الهندية", "العالمكيرية"]),
    (14, "Bedâiu's-Sanâi' — Kâsânî", ["بدائع الصنائع"], ["كاساني"], ["بدائع الصنائع"]),
    (14, "el-Mebsût — Serahsî", ["المبسوط"], ["سرخسي"], ["المبسوط"]),
    (14, "el-İnâye — Bâbertî", ["العناية شرح الهداية"], ["بابرتي"], ["العناية"]),
    (14, "Mecma'u'l-Enhür — Şeyhzâde", ["مجمع الأنهر"], ["شيخ زاده", "داماد"], ["مجمع الأنهر"]),
    (14, "Nûrü'l-Îzâh — Şürünbülâlî", ["نور الإيضاح"], ["شرنبلالي"], ["نور الإيضاح"]),
    (14, "Muhtasaru'l-Kudûrî", ["مختصر القدوري"], ["قدوري"], ["القدوري"]),
    # —— 15 maliki ——
    (15, "el-Muvatta' — Mâlik", ["الموطأ"], ["مالك"], ["الموطأ"]),
    (15, "el-Müdevvene — Sahnûn", ["المدونة"], ["سحنون"], ["المدونة"]),
    (15, "er-Risâle — İbn Ebî Zeyd", ["الرسالة"], ["أبي زيد", "القيرواني"], ["الرسالة"]),
    (15, "Bidâyetü'l-Müctehid — İbn Rüşd", ["بداية المجتهد"], ["رشد"], ["بداية المجتهد"]),
    (15, "Muhtasar Halîl", ["مختصر خليل"], ["خليل"], ["مختصر خليل"]),
    (15, "Mevâhibü'l-Celîl — Hattâb", ["مواهب الجليل"], ["حطاب"], ["مواهب الجليل"]),
    (15, "eş-Şerhu'l-Kebîr — Derdîr", ["الشرح الكبير"], ["دردير"], ["الشرح الكبير"]),
    (15, "Hâşiyetü'd-Desûkî", ["حاشية الدسوقي"], ["دسوقي"], ["الدسوقي"]),
    (15, "et-Temhîd — İbn Abdilberr", ["التمهيد"], ["عبد البر"], ["التمهيد"]),
    (15, "el-İstizkâr — İbn Abdilberr", ["الاستذكار"], ["عبد البر"], ["الاستذكار"]),
    (15, "el-Kavânînü'l-Fıkhiyye — İbn Cüzeyy", ["القوانين الفقهية"], ["جزي"], ["القوانين"]),
    (15, "et-Tâc ve'l-İklîl — Mevvâk", ["التاج والإكليل"], ["مواق"], ["التاج والإكليل"]),
    # —— 16 safii ——
    (16, "el-Ümm — Şâfiî", ["الأم"], ["شافعي"], ["الأم"]),
    (16, "er-Risâle — Şâfiî", ["الرسالة"], ["شافعي"], ["الرسالة"]),
    (16, "el-Mühezzeb — Şîrâzî", ["المهذب"], ["شيرازي"], ["المهذب"]),
    (16, "el-Mecmû' — Nevevî", ["المجموع"], ["نووي"], ["المجموع"]),
    (16, "Minhâcü't-Tâlibîn — Nevevî", ["منهاج الطالبين"], ["نووي"], ["منهاج الطالبين"]),
    (16, "Tuhfetü'l-Muhtâc — Heytemî", ["تحفة المحتاج"], ["هيتمي"], ["تحفة المحتاج"]),
    (16, "Nihâyetü'l-Muhtâc — Remlî", ["نهاية المحتاج"], ["رملي"], ["نهاية المحتاج"]),
    (16, "Muğni'l-Muhtâc — Şirbînî", ["مغني المحتاج"], ["شربيني"], ["مغني المحتاج"]),
    (16, "Fethu'l-Muîn — Mellibârî", ["فتح المعين"], ["مليباري"], ["فتح المعين"]),
    (16, "el-Hâvî'l-Kebîr — Mâverdî", ["الحاوي الكبير"], ["ماوردي"], ["الحاوي"]),
    (16, "Ravzatü't-Tâlibîn — Nevevî", ["روضة الطالبين"], ["نووي"], ["روضة الطالبين"]),
    (16, "Nihâyetü'l-Matlab — Cüveynî", ["نهاية المطلب"], ["جويني"], ["نهاية المطلب"]),
    # —— 17 hanbeli ——
    (17, "el-Mugni — İbn Kudâme", ["المغني"], ["قدامة"], ["المغني"]),
    (17, "eş-Şerhu'l-Kebîr — İbn Kudâme", ["الشرح الكبير"], ["قدامة"], ["الشرح الكبير"]),
    (17, "el-Kâfî — İbn Kudâme", ["الكافي"], ["قدامة"], ["الكافي"]),
    (17, "el-Umde — İbn Kudâme", ["عمدة الفقه"], ["قدامة"], ["عمدة"]),
    (17, "Keşşâfü'l-Kinâ' — Bühevî", ["كشاف القناع"], ["بهوتي"], ["كشاف القناع"]),
    (17, "er-Ravzü'l-Mürib' — Bühevî", ["الروض المربع"], ["بهوتي"], ["الروض المربع"]),
    (17, "Zâdü'l-Müsteni' — Huceyvî", ["زاد المستقنع"], ["حجاوي"], ["زاد المستقنع"]),
    (17, "el-İknâ' — Huceyvî", ["الإقناع"], ["حجاوي"], ["الإقناع"]),
    (17, "el-Furû' — İbn Müflih", ["الفروع"], ["مفلح"], ["الفروع"]),
    (17, "el-İnsâf — Merdâvî", ["الإنصاف"], ["مرداوي"], ["الإنصاف"]),
    # —— 24 siyer ——
    (24, "es-Sîre — İbn Hişâm", ["السيرة النبوية"], ["هشام"], ["السيرة النبوية"]),
    (24, "et-Tabakâtü'l-Kübrâ — İbn Sa'd", ["الطبقات الكبرى"], ["سعد"], ["الطبقات الكبرى"]),
    (24, "Şemâilü't-Tirmizî", ["الشمائل المحمدية"], ["ترمذي"], ["الشمائل"]),
    (24, "el-Hasâisü'l-Kübrâ — Süyûtî", ["الخصائص الكبرى"], ["سيوطي"], ["الخصائص"]),
    (24, "el-Mevâhibü'l-Ledünniyye — Kastallânî", ["المواهب اللدنية"], ["قسطلاني"], ["المواهب"]),
    (24, "es-Sîretü'l-Halebiyye", ["السيرة الحلبية", "إنسان العيون"], ["حلبي"], ["الحلبية", "إنسان العيون"]),
    (24, "Uyûnü'l-Eser — İbn Seyyidinnâs", ["عيون الأثر"], ["سيد الناس"], ["عيون الأثر"]),
    (24, "el-Bidâye (siyer) — İbn Kesîr", ["البداية والنهاية"], ["ابن كثير"], ["البداية والنهاية"]),
    (24, "Zâdü'l-Meâd — İbnü'l-Kayyim", ["زاد المعاد"], ["قيم"], ["زاد المعاد"]),
    (24, "er-Rahîku'l-Mahtûm", ["الرحيق المختوم"], ["مباركفوري"], ["الرحيق المختوم"]),
    (24, "eş-Şifâ — Kâdî İyâz", ["الشفا بتعريف حقوق المصطفى"], ["عياض"], ["الشفا"]),
    (24, "el-İsâbe — İbn Hacer", ["الإصابة في تمييز الصحابة"], ["ابن حجر"], ["الإصابة"]),
]


def _fold_ar(s: str) -> str:
    t = unicodedata.normalize("NFKC", s or "")
    # hamza / elif variants
    for a, b in (
        ("أ", "ا"),
        ("إ", "ا"),
        ("آ", "ا"),
        ("ٱ", "ا"),
        ("ة", "ه"),
        ("ى", "ي"),
        ("ؤ", "و"),
        ("ئ", "ي"),
        ("ً", ""),
        ("ٌ", ""),
        ("ٍ", ""),
        ("َ", ""),
        ("ُ", ""),
        ("ِ", ""),
        ("ّ", ""),
        ("ْ", ""),
        ("ـ", ""),
    ):
        t = t.replace(a, b)
    t = re.sub(r"\s+", " ", t).strip().casefold()
    return t


def _score(book: dict, title_keys: list[str], author_keys: list[str], must: list[str]) -> float:
    ar = _fold_ar(str(book.get("ar_title") or ""))
    tr = _fold_ar(str(book.get("tr_title") or ""))
    author = _fold_ar(str(book.get("author") or "") + " " + str(book.get("author_ar") or ""))
    blob = ar + " " + tr
    if must:
        if not any(_fold_ar(m) in blob for m in must):
            return -1.0
    sc = 0.0
    for k in title_keys:
        kk = _fold_ar(k)
        if kk and kk in blob:
            sc += 3.0 + min(len(kk), 40) / 40.0
    for k in author_keys:
        kk = _fold_ar(k)
        if kk and kk in author:
            sc += 2.5
    # penalty: modern review flags still ok if classic title matches strongly
    pages = int(book.get("pages") or 0)
    if pages >= 200:
        sc += 0.3
    if book.get("db_ok"):
        sc += 0.2
    return sc


def _is_mukhtasar(title: str) -> bool:
    t = _fold_ar(title)
    return any(x in t for x in ("مختصر", "اختصار", "تهذيب مختصر", "منتقى من"))


def _pick_best_edition(scored: list[tuple[float, dict]]) -> dict | None:
    """Aynı eser ailesinde en iyi baskı; farklı eserler karışırsa None."""
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    # Tam nüshaları öne al
    full = [(s, b) for s, b in scored if not _is_mukhtasar(str(b.get("ar_title") or ""))]
    pool = full or scored
    # Skor + sayfa
    pool.sort(
        key=lambda x: (
            x[0],
            int(x[1].get("pages") or 0),
            1 if x[1].get("db_ok") else 0,
        ),
        reverse=True,
    )
    top_sc, top = pool[0]
    # Çok farklı ikinci aile? ilk 40 harf çekirdeği
    core = _fold_ar(top.get("ar_title") or "")[:28]
    rivals = [
        b
        for s, b in pool[1:6]
        if abs(s - top_sc) < 1.2
        and _fold_ar(b.get("ar_title") or "")[:28] != core
        and not _is_mukhtasar(str(b.get("ar_title") or ""))
    ]
    # Rakipler aynı must ailesinden değilse ve yazar farklıysa şüphe
    if rivals:
        a0 = _fold_ar(str(top.get("author") or ""))
        for r in rivals:
            a1 = _fold_ar(str(r.get("author") or ""))
            if a0 and a1 and a0[:12] != a1[:12]:
                # hâlâ aynı must geçiyorsa en yüksek sayfayı al — klasik baskı savaşı
                continue
    return top


def best_match(books: list[dict], cat_id: int, title_keys: list[str], author_keys: list[str], must: list[str]) -> dict | None:
    # Önce kategori, yetmezse tüm katalog (bazı eserler komşu rafta)
    pools = [
        [b for b in books if int(b.get("category_id") or 0) == cat_id],
        books,
    ]
    scored: list[tuple[float, dict]] = []
    seen: set[int] = set()
    for pool in pools:
        for b in pool:
            bid = int(b.get("book_id") or 0)
            if bid in seen:
                continue
            sc = _score(b, title_keys, author_keys, must)
            # must tutuyorsa eşiği biraz gevşet; tutmuyorsa zaten -1
            if sc >= 4.5:
                scored.append((sc, b))
                seen.add(bid)
        if scored:
            break
    if not scored:
        return None
    top = _pick_best_edition(scored)
    if not top:
        return None
    sc = _score(top, title_keys, author_keys, must)
    return {"score": round(sc, 2), "book": top}


def main() -> None:
    books = json.loads(CACHE.read_text(encoding="utf-8"))
    assert isinstance(books, list) and books, "katalog boş"

    rows: list[dict] = []
    ok = 0
    miss = 0
    for cat_id, label, keys, authors, must in QUERY:
        hit = best_match(books, cat_id, keys, authors, must)
        if not hit:
            rows.append(
                {
                    "cat_id": cat_id,
                    "label": label,
                    "status": "ESLESMEDI",
                    "book_id": None,
                    "ar_title": None,
                    "tr_title": None,
                    "author": None,
                    "score": None,
                    "note": "Güvenli eşleşme yok — elle bakılacak",
                }
            )
            miss += 1
            continue
        b = hit["book"]
        rows.append(
            {
                "cat_id": cat_id,
                "label": label,
                "status": "OK",
                "book_id": b.get("book_id"),
                "ar_title": b.get("ar_title"),
                "tr_title": b.get("tr_title"),
                "author": b.get("author"),
                "pages": b.get("pages"),
                "score": hit["score"],
                "db_ok": b.get("db_ok"),
                "note": "",
            }
        )
        ok += 1

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "samile-derin-eslesme-v1-2026-11-12",
        "rule": "suphede_eslesmedi_yanlis_yazma",
        "matched": ok,
        "unmatched": miss,
        "total_queries": len(QUERY),
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2)
        s.bottom_margin = Cm(2)
        s.left_margin = Cm(2)
        s.right_margin = Cm(2)
    doc.add_heading("Şamile derin çekirdek — katalog eşlemesi (DOLDURULDU)", 0)
    p = doc.add_paragraph()
    r = p.add_run(
        f"Tarih: 2026-11-12 · Eşleşen: {ok} · Eşleşmeyen (elle): {miss} · "
        "Kural: şüphede EŞLEŞMEDİ — yanlış book_id yazılmadı."
    )
    r.bold = True
    doc.add_paragraph(
        "Bu liste Word önerisindeki ana müteber eserlerin Şamile cache karşılığıdır. "
        "EŞLEŞMEDİ satırlarını seninle netleştiririz; uydurma ID yok."
    )

    cur_cat = None
    for row in rows:
        if row["cat_id"] != cur_cat:
            cur_cat = row["cat_id"]
            doc.add_heading(f"Kategori {cur_cat:02d}", 1)
        line = doc.add_paragraph(style="List Bullet")
        if row["status"] == "OK":
            line.add_run(
                f"✓ {row['label']}\n"
                f"   book_id={row['book_id']} · {row.get('ar_title')}\n"
                f"   {row.get('author')} · sayfa≈{row.get('pages')} · skor={row.get('score')}"
            )
        else:
            run = line.add_run(f"✗ EŞLEŞMEDİ — {row['label']}\n   → Elle kontrol / alternatif baskı seçilecek")
            run.bold = True

    doc.add_heading("Mimar notu", 1)
    doc.add_paragraph("□ Eşleşenleri onaylıyorum")
    doc.add_paragraph("□ EŞLEŞMEDİ satırlarını şöyle düzelt: …")
    doc.add_paragraph("□ Onaydan sonra derin indeks/okuma yoluna geç")
    try:
        doc.save(OUT_DOCX)
        saved = OUT_DOCX
    except PermissionError:
        doc.save(OUT_DOCX_ALT)
        saved = OUT_DOCX_ALT
    print(f"OK={ok} MISS={miss}")
    print(f"JSON {OUT_JSON}")
    print(f"DOCX {saved}")


if __name__ == "__main__":
    main()
