# Din kütüphanesi kapsam envanteri — 2026-11-24

**Kaynak:** `knowledge/ilim/din/shamela/**/manifest.json` + `.rag_index/shards/shamela/registry.json` (**salt okuma**; eser ekleme/indirme YOK).
**Üretici:** `scripts/din_kapsam_envanter.py rapor` · çekirdek liste VERİ: `eval/din/cekirdek_eserler.json`.

## 1) Genel görünüm

- Şâmile shard sayısı: **40** kategori (hepsi `ready`) · kitap klasörü: **5.017** · indeksli parça: **8.231.484**
- Gömme modeli: `paraphrase-multilingual-MiniLM-L12-v2` (384 boyut) · arama: kosinüs, brute-force numpy (mmap).
- Ayrıca ana indekste elle derlenmiş `knowledge/ilim/din/01_kuran … 09_ahlak_tasavvuf` klasörleri (özet/kart düzeyi).

## 2) Kategori tablosu (shard bazında)

| Katman | Kategori | Kitap | Parça (indeks) | Ort. parça/kitap |
|---|---|---:|---:|---:|
| cekirdek | `01_akaid` Akaid | 329 | 178.430 | 542 |
| cekirdek | `02_firak_redler` Fırak ve reddiyeler | 55 | 32.112 | 583 |
| cekirdek | `03_tefsir` Tefsir | 148 | 877.210 | 5927 |
| cekirdek | `04_kuran_ilim_usul` Kur'ân ilimleri | 132 | 135.060 | 1023 |
| cekirdek | `05_tecvid_kiraat` Tecvid ve kırâat | 77 | 72.032 | 935 |
| cekirdek | `06_hadis_sunen` Hadis (kütüb/sünen/müsned) | 1174 | 1.017.742 | 866 |
| cekirdek | `07_hadis_serh` Hadis şerhleri | 172 | 831.892 | 4836 |
| cekirdek | `08_tahric_etraf` Tahrîc ve etrâf | 60 | 145.016 | 2416 |
| cekirdek | `09_ilel_sual` İlel ve suâlât | 62 | 49.704 | 801 |
| cekirdek | `10_hadis_ilimleri` Hadis ilimleri | 132 | 65.357 | 495 |
| genis | `11_usul_fikih` Usûl-i fıkıh | 164 | 226.378 | 1380 |
| genis | `12_fikih_kaideler` Fıkıh kâideleri | 31 | 57.194 | 1844 |
| genis | `13_mantik` Mantık | 6 | 1.621 | 270 |
| genis | `14_hanefi` Hanefî fıkhı | 79 | 338.955 | 4290 |
| genis | `15_maliki` Mâlikî fıkhı | 76 | 338.460 | 4453 |
| genis | `16_safii` Şâfiî fıkhı | 77 | 500.819 | 6504 |
| genis | `17_hanbeli` Hanbelî fıkhı | 106 | 305.809 | 2884 |
| genis | `18_genel_fikih` Genel/karşılaştırmalı fıkıh | 72 | 82.574 | 1146 |
| genis | `19_fikhi_meseleler` Fıkhî meseleler | 125 | 23.118 | 184 |
| genis | `20_siyaset_kaza` Siyâset ve kazâ | 77 | 49.710 | 645 |
| genis | `21_feraiz` Ferâiz | 16 | 2.060 | 128 |
| genis | `22_fetvalar` Fetvâlar | 14 | 11.304 | 807 |
| genis | `23_rekaik_adab` Rekâik. âdâb. zühd (tasavvuf-ahlâk) | 229 | 150.283 | 656 |
| genis | `24_siyer` Siyer ve şemâil | 83 | 155.756 | 1876 |
| tarih | `25_tarih` Tarih | 125 | 422.178 | 3377 |
| tarih | `26_teracim` Terâcim ve tabakât | 415 | 856.177 | 2063 |
| tarih | `27_ensab` Ensâb | 40 | 50.578 | 1264 |
| tarih | `28_buldan` Büldân (coğrafya) | 79 | 93.379 | 1182 |
| dil_diger | `29_dil` Dil | 47 | 19.537 | 415 |
| dil_diger | `30_garib_lugat` Garîb ve lügat | 114 | 270.278 | 2370 |
| dil_diger | `31_nahiv_sarf` Nahiv-sarf | 155 | 156.301 | 1008 |
| dil_diger | `32_edebiyat` Edebiyat | 351 | 399.671 | 1138 |
| dil_diger | `33_aruz` Arûz | 9 | 1.485 | 165 |
| dil_diger | `34_divanlar` Dîvânlar | 15 | 4.871 | 324 |
| dil_diger | `35_belagat` Belâgat | 21 | 21.030 | 1001 |
| dil_diger | `36_cevami` Câmi' (karma) | 38 | 202.994 | 5341 |
| dil_diger | `37_fihrist` Fihrist | 39 | 44.183 | 1132 |
| dil_diger | `38_tip` Tıp | 8 | 17.624 | 2203 |
| dil_diger | `39_genel` Genel | 40 | 10.799 | 269 |
| dil_diger | `40_diger` Diğer | 25 | 11.803 | 472 |

### Katman toplamları

| Katman | Kitap | Parça |
|---|---:|---:|
| Çekirdek (Kur'an · tefsir · akaid · hadis) | 2341 | 3.404.555 |
| Geniş (fıkıh · usûl · rekâik/tasavvuf-ahlâk · siyer · kelâm-mantık) | 1155 | 2.244.041 |
| Tarih (tarih · terâcim · ensâb · büldân) | 659 | 1.422.312 |
| Dil · edebiyat · genel · diğer | 862 | 1.160.576 |

### Manifest etiketleri (hat / katman)

- `hat`: {'ehlisunnet': 4889, 'reddiye': 55, 'genel': 73}
- `katman` (A=asıl/öğret, B=betimle, C=ayır/red): {'A': 4962, 'C': 55}
- Manifestsiz klasör: 0

## 3) Çekirdek eser eşleşmesi (olmazsa olmaz + geniş)

Eşleşme: eser adı (Arapça, harekesiz/normalize) anahtar içerir. «Var» = en az bir eşleşen cilt/kitap klasörü. Anahtarlar veri dosyasındadır; yanlış negatif görürseniz anahtar listesine ekleyin (kod değişmez).

| Grup | Katman | Bulunan / aranan | Oran |
|---|---|---:|---:|
| Tefsir | çekirdek | 20 / 20 | %100 |
| Kur'ân ilimleri / tecvid | çekirdek | 5 / 5 | %100 |
| Akaid ve kelâm (Eş'arî-Mâtürîdî) | çekirdek | 11 / 20 | %55 |
| Hadis — Kütüb-i Sitte ve temel mecmualar | çekirdek | 23 / 23 | %100 |
| Hadis şerhleri ve hadis ilimleri | çekirdek | 18 / 18 | %100 |
| Fıkıh — dört mezhep ve karşılaştırmalı | geniş | 27 / 30 | %90 |
| Usûl-i fıkıh ve kâideler | geniş | 12 / 12 | %100 |
| Siyer ve şemâil | geniş | 14 / 14 | %100 |
| İslâm tarihi ve kıssa-i enbiyâ | tarih | 17 / 20 | %85 |
| Tasavvuf ve ahlâk | geniş | 23 / 33 | %70 |

### Tefsir

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Tefsîr-i Taberî (Câmiu'l-Beyân) | ✔ var | `03_tefsir` · 7798 · 20216 · تفسير الطبري جامع البيان - ت التركي ; `03_tefsir` · 43 · 17493 · تفسير الطبري جامع البيان - ط دار التربية (+2 kayıt) |
| İbn Kesîr Tefsîri | ✔ var | `03_tefsir` · 1509 · 13091 · تفسير ابن كثير - ط أولاد الشيخ ; `03_tefsir` · 1503 · 9399 · تفسير ابن كثير - ط ابن الجوزي (+2 kayıt) |
| Kurtubî (el-Câmi' li-Ahkâmi'l-Kur'ân) | ✔ var | `03_tefsir` · 20855 · 13826 · تفسير القرطبي = الجامع لأحكام القرآن |
| Fahreddîn er-Râzî (Mefâtîhu'l-Gayb) | ✔ var | `03_tefsir` · 23635 · 21810 · تفسير الرازي = مفاتيح الغيب أو التفسير ا ; `03_tefsir` · 419 · 4942 · تفسير الحداد المطبوع خطأ باسم التفسير ال |
| Beydâvî (Envârü't-Tenzîl) | ✔ var | `03_tefsir` · 23588 · 2769 · تفسير البيضاوي = أنوار التنزيل وأسرار ال |
| Nesefî (Medârikü't-Tenzîl) | ✔ var | `03_tefsir` · 1394 · 7814 · تفسير النسفي = مدارك التنزيل وحقائق التأ |
| Celâleyn Tefsîri | ✔ var | `03_tefsir` · 12876 · 6934 · تفسير الجلالين |
| Begavî (Meâlimü't-Tenzîl) | ✔ var | `03_tefsir` · 12217 · 7286 · تفسير البغوي - إحياء التراث ; `03_tefsir` · 41 · 6711 · تفسير البغوي - طيبة |
| Âlûsî (Rûhu'l-Me'ânî) | ✔ var | `03_tefsir` · 22835 · 11055 · تفسير الألوسي = روح المعاني |
| Ebüssuûd (İrşâdü'l-Aklî's-Selîm) | ✔ var | `03_tefsir` · 1429 · 8654 · تفسير أبي السعود = إرشاد العقل السليم إل |
| Mâtürîdî (Te'vîlâtü Ehli's-Sünne) | ✔ var | `03_tefsir` · 95590 · 6013 · تفسير الماتريدي = تأويلات أهل السنة |
| Suyûtî (ed-Dürrü'l-Mensûr) | ✔ var | `03_tefsir` · 12884 · 7338 · الدر المنثور في التفسير بالمأثور ; `26_teracim` · 9229 · 559 · الدر المنثور في طبقات ربات الخدور |
| Şevkânî (Fethu'l-Kadîr) | ✔ var | `03_tefsir` · 23623 · 11928 · فتح القدير للشوكاني |
| Ebû Hayyân (el-Bahru'l-Muhît) | ✔ var | `03_tefsir` · 23591 · 12697 · البحر المحيط في التفسير - ط الفكر |
| İbn Âşûr (et-Tahrîr ve't-Tenvîr) | ✔ var | `03_tefsir` · 9776 · 12117 · التحرير والتنوير |
| Zemahşerî (el-Keşşâf) — Mu'tezilî, mukayese için | ✔ var | `03_tefsir` · 20891 · 9345 · فتوح الغيب في الكشف عن قناع الريب (حاشية ; `03_tefsir` · 23627 · 5396 · تفسير الكشاف - ومعه الانتصاف ومشاهد الإن (+1 kayıt) |
| Kuşeyrî (Letâifü'l-İşârât) — işârî tefsir | ✔ var | `03_tefsir` · 23629 · 2781 · لطائف الإشارات = تفسير القشيري |
| Sa'dî (Teysîru'l-Kerîmi'r-Rahmân) | ✔ var | `03_tefsir` · 42 · 3434 · تفسير السعدي = تيسير الكريم الرحمن |
| Sem'ânî / Semerkandî (Bahru'l-Ulûm) | ✔ var | `03_tefsir` · 23594 · 2041 · تفسير السمرقندي = بحر العلوم |
| Vâhidî (el-Vecîz/el-Basît/Esbâb-ı Nüzûl) | ✔ var | `04_kuran_ilim_usul` · 11456 · 861 · أسباب النزول ت زغلول ; `04_kuran_ilim_usul` · 11314 · 787 · أسباب النزول ت الحميدان |

### Kur'ân ilimleri / tecvid

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Suyûtî (el-İtkân fî Ulûmi'l-Kur'ân) | ✔ var | `04_kuran_ilim_usul` · 11728 · 1459 · الإتقان في علوم القرآن |
| Zerkeşî (el-Burhân fî Ulûmi'l-Kur'ân) | ✔ var | `04_kuran_ilim_usul` · 11436 · 1944 · البرهان في علوم القرآن ; `03_tefsir` · 14114 · 609 · البرهان في علوم القرآن للإمام الحوفي - س |
| İbnü'l-Cezerî (en-Neşr fi'l-Kırââti'l-Aşr) | ✔ var | `05_tecvid_kiraat` · 22642 · 970 · النشر في القراءات العشر |
| Ebû Amr ed-Dânî (et-Teysîr) | ✔ var | `05_tecvid_kiraat` · 147812 · 621 · التيسير في القراءات السبع ت الشغدلي ; `05_tecvid_kiraat` · 5527 · 227 · التيسير في القراءات السبع |
| Nâsih-Mensûh / Müşkilü'l-Kur'ân | ✔ var | `04_kuran_ilim_usul` · 13073 · 838 · الناسخ والمنسوخ - النحاس ; `04_kuran_ilim_usul` · 37834 · 617 · الناسخ والمنسوخ - أبو عبيد (+10 kayıt) |

### Akaid ve kelâm (Eş'arî-Mâtürîdî)

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Tahâvî (el-Akîdetü't-Tahâviyye) ve şerhleri | ✔ var | `01_akaid` · 10777 · 995 · شرح العقيدة الطحاوية - ط الأوقاف السعودي ; `01_akaid` · 10549 · 915 · شرح العقيدة الطحاوية - بتخريج الألباني (+3 kayıt) |
| Nesefî (el-Akâid) / Teftâzânî Şerhu'l-Akâid | ✘ **EKSİK/bulunamadı** | Şâmile'de yalnız Nesefî'nin tefsiri/fıkıh eserleri var; el-Akâid ve Teftâzânî şerhi YOK (Eş'arî-Mâtürîdî okul metni). |
| Teftâzânî (Şerhu'l-Makâsıd) | ✘ **EKSİK/bulunamadı** | Teftâzânî'den yalnız et-Telvîh (usûl) var. |
| Îcî / Cürcânî (el-Mevâkıf ve Şerhi) | ✘ **EKSİK/bulunamadı** | Îcî'den yalnız Şerhu'l-Adud (usûl) ve tefsiri var; el-Mevâkıf YOK. |
| Gazâlî (el-İktisâd fi'l-İ'tikâd) | ✔ var | `01_akaid` · 7546 · 248 · الاقتصاد في الاعتقاد للمقدسي ; `01_akaid` · 9217 · 130 · الاقتصاد في الاعتقاد للغزالي |
| Cüveynî (el-Irşâd) | ✘ **EKSİK/bulunamadı** | Cüveynî'den Lum'u'l-Edille ve el-Verakât var; el-Irşâd YOK. |
| Bâkıllânî (et-Temhîd) | ✔ var | `01_akaid` · 6389 · 536 · تمهيد الأوائل وتلخيص الدلائل |
| Eş'arî (el-İbâne / Makâlâtü'l-İslâmiyyîn / el-Lüma') | ✔ var | `02_firak_redler` · 4137 · 859 · مقالات الإسلاميين ت زرزور ; `01_akaid` · 911 · 769 · الإبانة عن أصول الديانة - ت العصيمي (+2 kayıt) |
| Mâtürîdî (Kitâbü't-Tevhîd) | ✔ var | `01_akaid` · 6365 · 399 · التوحيد للماتريدي |
| Ebu'l-Muîn en-Nesefî (Tabsıratü'l-Edille) | ✘ **EKSİK/bulunamadı** | Nesefî Ebu'l-Muîn'in Tabsıra'sı YOK. |
| Pezdevî (Usûlü'd-Dîn) | ✘ **EKSİK/bulunamadı** | Pezdevî'den yalnız usûl-i fıkıh (Keşfü'l-Esrâr şerhi) var; Usûlü'd-Dîn YOK. |
| Beyhakî (el-İ'tikād ve'l-Hidâye) | ✘ **EKSİK/bulunamadı** | Beyhakî'den Şuabü'l-Îmân ve Sünen var; el-İ'tikād ve'l-Hidâye YOK. |
| Fahreddîn er-Râzî (el-Erba'în fî Usûli'd-Dîn / Esâsü't-Takdîs) | ✔ var | `01_akaid` · 6372 · 120 · معالم أصول الدين |
| Ebû Hanîfe (el-Fıkhu'l-Ekber) ve şerhi | ✔ var | `01_akaid` · 6388 · 92 · الفقه الأكبر |
| Sünûsî (Ümmü'l-Berâhîn) / Cevheretü't-Tevhîd | ✘ **EKSİK/bulunamadı** | Ümmü'l-Berâhîn/Cevheretü't-Tevhîd YOK (Mâlikî-Eş'arî ilmihâl akaidi). |
| Kâdî Iyâz (eş-Şifâ bi-Ta'rîfi Hukûki'l-Mustafâ) | ✔ var | `24_siyer` · 23645 · 1608 · الشفا بتعريف حقوق المصطفى - محذوف الأسان ; `24_siyer` · 1753 · 1135 · الشفا بتعريف حقوق المصطفى - وحاشية الشمن |
| Şehristânî (el-Milel ve'n-Nihal) | ✔ var | `01_akaid` · 11812 · 676 · الملل والنحل |
| Bağdâdî (el-Fark beyne'l-Fırak / Usûlü'd-Dîn) | ✔ var | `02_firak_redler` · 6520 · 353 · الفرق بين الفرق |
| İbn Hazm (el-Fisal fi'l-Milel) | ✔ var | `02_firak_redler` · 6521 · 1404 · الفصل في الملل والأهواء والنحل |
| Sâbûnî (el-Bidâye fî Usûli'd-Dîn) | ✘ **EKSİK/bulunamadı** | Sâbûnî'nin el-Bidâye'si YOK. |

### Hadis — Kütüb-i Sitte ve temel mecmualar

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Sahîh-i Buhârî | ✔ var | `07_hadis_serh` · 5756 · 26370 · عمدة القاري شرح صحيح البخاري ; `07_hadis_serh` · 21715 · 15421 · شرح القسطلاني = إرشاد الساري لشرح صحيح ا (+19 kayıt) |
| Sahîh-i Müslim | ✔ var | `06_hadis_sunen` · 711 · 9178 · صحيح مسلم - ط التركية ; `06_hadis_sunen` · 1727 · 7979 · صحيح مسلم - ت عبد الباقي (+6 kayıt) |
| Sünen-i Tirmizî | ✔ var | `06_hadis_sunen` · 7895 · 6696 · سنن الترمذي - ت بشار ; `06_hadis_sunen` · 1435 · 6627 · سنن الترمذي - ت شاكر (+12 kayıt) |
| Sünen-i Ebû Dâvûd | ✔ var | `07_hadis_serh` · 131521 · 14069 · شرح سنن أبي داود لابن رسلان ; `07_hadis_serh` · 14601 · 10060 · بذل المجهود في حل سنن أبي داود (+11 kayıt) |
| Sünen-i Nesâî | ✔ var | `06_hadis_sunen` · 829 · 8328 · سنن النسائي - ط المصرية ; `06_hadis_sunen` · 1339 · 5567 · سنن النسائي - ط الرسالة (+4 kayıt) |
| Sünen-i İbn Mâce | ✔ var | `06_hadis_sunen` · 1198 · 5997 · سنن ابن ماجه - ت عبد الباقي ; `07_hadis_serh` · 9810 · 5238 · حاشية السندي على سنن ابن ماجه (+7 kayıt) |
| Muvatta (Mâlik) | ✔ var | `07_hadis_serh` · 6684 · 8929 · المنتقى شرح الموطإ ; `07_hadis_serh` · 551 · 5893 · شرح الزرقاني على الموطأ (+14 kayıt) |
| Müsned-i Ahmed | ✔ var | `06_hadis_sunen` · 25794 · 25181 · مسند أحمد - ط الرسالة ; `07_hadis_serh` · 124910 · 13049 · الفتح الرباني لترتيب مسند الإمام أحمد بن (+7 kayıt) |
| Sünen-i Dârimî | ✔ var | `06_hadis_sunen` · 21795 · 4863 · مسند الدارمي - ت حسين أسد ; `06_hadis_sunen` · 36114 · 2139 · مسند الدارمي - ت الزهراني |
| Sahîh-i İbn Hibbân | ✔ var | `06_hadis_sunen` · 1729 · 12779 · الإحسان في تقريب صحيح ابن حبان ; `06_hadis_sunen` · 537 · 8343 · صحيح ابن حبان: التقاسيم والأنواع |
| Sahîh-i İbn Huzeyme | ✔ var | `06_hadis_sunen` · 1446 · 5182 · صحيح ابن خزيمة ; `06_hadis_sunen` · 121382 · 2815 · صحيح ابن خزيمة ط 3 |
| Müstedrek (Hâkim) | ✔ var | `06_hadis_sunen` · 1424 · 11971 · المستدرك على الصحيحين - ط الرسالة ; `06_hadis_sunen` · 2266 · 9895 · المستدرك على الصحيحين - ط العلمية (+1 kayıt) |
| Sünenü'l-Kübrâ (Beyhakî) | ✔ var | `06_hadis_sunen` · 7861 · 24970 · السنن الكبرى - البيهقي - ط العلمية ; `06_hadis_sunen` · 8361 · 16421 · السنن الكبرى - النسائي - ط الرسالة (+3 kayıt) |
| Mu'cemü'l-Kebîr / Evsat (Taberânî) | ✔ var | `06_hadis_sunen` · 1733 · 27063 · المعجم الكبير للطبراني ; `06_hadis_sunen` · 28171 · 9949 · المعجم الأوسط للطبراني (+6 kayıt) |
| Musannef (Abdürrezzâk / İbn Ebî Şeybe) | ✔ var | `06_hadis_sunen` · 333 · 46584 · المصنف - ابن أبي شيبة - ت الشثري ; `06_hadis_sunen` · 9944 · 42924 · المصنف - ابن أبي شيبة - ت الحوت (+8 kayıt) |
| Şerhu Meâni'l-Âsâr (Tahâvî) | ✔ var | `07_hadis_serh` · 13667 · 8786 · نخب الأفكار في تنقيح مباني الأخبار في شر ; `06_hadis_sunen` · 21108 · 5728 · شرح معاني الآثار |
| Riyâzü's-Sâlihîn (Nevevî) | ✔ var | `07_hadis_serh` · 140 · 2654 · دليل الفالحين لطرق رياض الصالحين ; `06_hadis_sunen` · 2348 · 2179 · رياض الصالحين - ت الفحل (+4 kayıt) |
| el-Erbaûn en-Neveviyye | ✔ var | `07_hadis_serh` · 133377 · 358 · شرح الأربعين النووية للمناوي حـ 29 - 35 ; `07_hadis_serh` · 11244 · 129 · شرح الأربعين النووية لابن دقيق العيد |
| Mişkâtü'l-Mesâbîh | ✔ var | `07_hadis_serh` · 8176 · 14810 · مرقاة المفاتيح شرح مشكاة المصابيح ; `06_hadis_sunen` · 8360 · 7460 · مشكاة المصابيح (+1 kayıt) |
| et-Terğîb ve't-Terhîb (Münzirî) | ✔ var | `07_hadis_serh` · 660 · 10826 · فتح القريب المجيب على الترغيب والترهيب ; `23_rekaik_adab` · 13223 · 4510 · الترغيب والترهيب للمنذري - ت عمارة (+3 kayıt) |
| Bulûğu'l-Merâm (İbn Hacer) | ✔ var | `07_hadis_serh` · 1082 · 4795 · سبل السلام شرح بلوغ المرام - ت حلاق ; `07_hadis_serh` · 17747 · 4633 · البدر التمام شرح بلوغ المرام ت الزبن (+3 kayıt) |
| el-Câmiu's-Sağîr / Feyzü'l-Kadîr (Suyûtî/Münâvî) | ✔ var | `06_hadis_sunen` · 21659 · 14619 · الجامع الصغير وزيادته ; `07_hadis_serh` · 21660 · 10769 · فيض القدير (+7 kayıt) |
| Mecmaü'z-Zevâid (Heysemî) | ✔ var | `06_hadis_sunen` · 36446 · 10666 · جمع الفوائد من جامع الأصول ومجمع الزوائد ; `06_hadis_sunen` · 61 · 4182 · مجمع الزوائد ومنبع الفوائد (+1 kayıt) |

### Hadis şerhleri ve hadis ilimleri

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Fethu'l-Bârî (İbn Hacer) | ✔ var | `07_hadis_serh` · 1673 · 27203 · فتح الباري بشرح البخاري - ط السلفية ; `07_hadis_serh` · 137 · 4840 · فتح الباري لابن رجب (+2 kayıt) |
| Umdetü'l-Kârî (Aynî) | ✔ var | `07_hadis_serh` · 5756 · 26370 · عمدة القاري شرح صحيح البخاري |
| İrşâdü's-Sârî (Kastallânî) | ✔ var | `07_hadis_serh` · 21715 · 15421 · شرح القسطلاني = إرشاد الساري لشرح صحيح ا |
| Nevevî Şerhu Sahîh-i Müslim (el-Minhâc) | ✔ var | `07_hadis_serh` · 1711 · 4214 · شرح النووي على مسلم |
| Tuhfetü'l-Ahvezî | ✔ var | `07_hadis_serh` · 21662 · 5504 · تحفة الأحوذي |
| Avnü'l-Ma'bûd | ✔ var | `06_hadis_sunen` · 654 · 7177 · سنن أبي داود - ط دهلي مع عون المعبود ; `07_hadis_serh` · 5760 · 5288 · عون المعبود وحاشية ابن القيم |
| Mirkâtü'l-Mefâtîh (Aliyyülkârî) | ✔ var | `07_hadis_serh` · 8176 · 14810 · مرقاة المفاتيح شرح مشكاة المصابيح |
| Neylü'l-Evtâr (Şevkânî) | ✔ var | `07_hadis_serh` · 1218 · 11397 · نيل الأوطار شرح منتقى الأخبار - ت حلاق ; `07_hadis_serh` · 9242 · 6778 · نيل الأوطار شرح منتقى الأخبار - ط الحديث (+1 kayıt) |
| Subulü's-Selâm (San'ânî) | ✔ var | `07_hadis_serh` · 1082 · 4795 · سبل السلام شرح بلوغ المرام - ت حلاق ; `07_hadis_serh` · 21590 · 2001 · سبل السلام شرح بلوغ المرام - ط الحديث (+1 kayıt) |
| Nasbü'r-Râye (Zeylaî) | ✔ var | `08_tahric_etraf` · 11428 · 4196 · نصب الراية |
| Mukaddime (İbnü's-Salâh) | ✔ var | `10_hadis_ilimleri` · 29878 · 1486 · مقدمة ابن الصلاح ومحاسن الاصطلاح ; `10_hadis_ilimleri` · 789 · 1190 · الكافي في علوم الحديث (+14 kayıt) |
| Nüzhetü'n-Nazar (İbn Hacer) | ✔ var | `10_hadis_ilimleri` · 316 · 315 · نزهة النظر في توضيح نخبة الفكر - ت القاس ; `10_hadis_ilimleri` · 37456 · 254 · نزهة النظر في توضيح نخبة الفكر - ت الرحي (+1 kayıt) |
| Tedrîbü'r-Râvî (Suyûtî) | ✔ var | `10_hadis_ilimleri` · 9329 · 948 · تدريب الراوي في شرح تقريب النواوي |
| Takrîbü't-Tehzîb / Tehzîbü't-Tehzîb (İbn Hacer) | ✔ var | `26_teracim` · 1278 · 13647 · تهذيب التهذيب - ط دبي ; `26_teracim` · 1290 · 6870 · تهذيب التهذيب - ط المعرفة (+3 kayıt) |
| Tehzîbü'l-Kemâl (Mizzî) | ✔ var | `26_teracim` · 3722 · 21290 · تهذيب الكمال في أسماء الرجال ; `26_teracim` · 89 · 5323 · إكمال تهذيب الكمال - ط العلمية (+4 kayıt) |
| Mîzânü'l-İ'tidâl (Zehebî) | ✔ var | `26_teracim` · 1692 · 2760 · ميزان الاعتدال ; `26_teracim` · 5847 · 215 · ذيل ميزان الاعتدال |
| el-Câmi' li-Ahlâkı'r-Râvî (Hatîb) | ✔ var | `10_hadis_ilimleri` · 13012 · 2236 · الجامع لأخلاق الراوي وآداب السامع للخطيب |
| el-Kifâye fî İlmi'r-Rivâye (Hatîb) | ✔ var | `06_hadis_sunen` · 13055 · 1571 · الكفاية في علم الرواية للخطيب البغدادي |

### Fıkıh — dört mezhep ve karşılaştırmalı

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Hanefî: el-Hidâye (Merğînânî) | ✔ var | `14_hanefi` · 11820 · 1237 · الهداية في شرح بداية المبتدي |
| Hanefî: Fethu'l-Kadîr (İbnü'l-Hümâm) | ✔ var | `14_hanefi` · 21744 · 8189 · فتح القدير للكمال بن الهمام - ط الحلبي |
| Hanefî: Reddü'l-Muhtâr (İbn Âbidîn) | ✔ var | `14_hanefi` · 21613 · 16815 · حاشية ابن عابدين = رد المحتار ط الحلبي ; `14_hanefi` · 918 · 2804 · تكملة حاشية ابن عابدين = قرة عيون الأخيا |
| Hanefî: Bedâi'u's-Sanâi' (Kâsânî) | ✔ var | `14_hanefi` · 8183 · 10453 · بدائع الصنائع في ترتيب الشرائع |
| Hanefî: el-Mebsût (Serahsî) | ✔ var | `14_hanefi` · 5423 · 17545 · المبسوط للسرخسي |
| Hanefî: el-Bahru'r-Râik (İbn Nüceym) | ✔ var | `14_hanefi` · 12227 · 15326 · البحر الرائق شرح كنز الدقائق ومنحة الخال |
| Hanefî: el-Lübâb / Muhtasarü'l-Kudûrî | ✔ var | `14_hanefi` · 21596 · 2666 · الجوهرة النيرة على مختصر القدوري ; `14_hanefi` · 21496 · 934 · اللباب في شرح الكتاب (+2 kayıt) |
| Hanefî: Merâkı'l-Felâh / Hâşiyetü't-Tahtâvî | ✔ var | `14_hanefi` · 11993 · 867 · حاشية الطحطاوي على مراقي الفلاح شرح نور  ; `14_hanefi` · 412 · 443 · مراقي الفلاح شرح نور الإيضاح |
| Hanefî: el-Fetâvâ el-Hindiyye (Âlemgîriyye) | ✔ var | `14_hanefi` · 21640 · 11585 · الفتاوى العالمكيرية = الفتاوى الهندية |
| Mâlikî: el-Müdevvene | ✔ var | `15_maliki` · 18607 · 9651 · الجامع لمسائل المدونة ; `15_maliki` · 96257 · 7380 · النوادر والزيادات على ما في المدونة من غ (+7 kayıt) |
| Mâlikî: Muhtasar Halîl ve şerhleri (Mevâhib, Hattâb, Harşî) | ✔ var | `15_maliki` · 91 · 13654 · شرح الخرشي على مختصر خليل - ومعه حاشية ا ; `15_maliki` · 569 · 9915 · مواهب الجليل في شرح مختصر خليل (+6 kayıt) |
| Mâlikî: Bidâyetü'l-Müctehid (İbn Rüşd) | ✔ var | `15_maliki` · 21739 · 1389 · بداية المجتهد ونهاية المقتصد |
| Mâlikî: er-Risâle (İbn Ebî Zeyd el-Kayrevânî) | ✔ var | `15_maliki` · 21589 · 3779 · الفواكه الدواني على رسالة ابن أبي زيد ال ; `15_maliki` · 7441 · 751 · الثمر الداني شرح رسالة ابن أبي زيد القير (+3 kayıt) |
| Mâlikî: eş-Şerhu'l-Kebîr / Hâşiyetü'd-Desûkî | ✔ var | `15_maliki` · 21604 · 11060 · الشرح الكبير للشيخ الدردير وحاشية الدسوق ; `35_belagat` · 147062 · 3083 · حاشية الدسوقي على مختصر المعاني |
| Şâfiî: el-Ümm | ✔ var | `16_safii` · 1655 · 7966 · الأم للشافعي - ط الفكر ; `16_safii` · 21721 · 7092 · البيان في مذهب الإمام الشافعي (+6 kayıt) |
| Şâfiî: el-Mecmû' (Nevevî) | ✔ var | `16_safii` · 2186 · 6548 · المجموع شرح المهذب - ط المنيرية ; `16_safii` · 1022 · 1677 · تكملة السبكي على المجموع شرح المهذب - ط  |
| Şâfiî: Ravdatü't-Tâlibîn | ✔ var | `16_safii` · 499 · 4944 · روضة الطالبين وعمدة المفتين |
| Şâfiî: Minhâcü't-Tâlibîn / Muğni'l-Muhtâc | ✔ var | `16_safii` · 11444 · 8816 · مغني المحتاج إلى معرفة معاني ألفاظ المنه ; `16_safii` · 12096 · 406 · منهاج الطالبين وعمدة المفتين في الفقه |
| Şâfiî: Tuhfetü'l-Muhtâc / Nihâyetü'l-Muhtâc | ✔ var | `16_safii` · 9059 · 27474 · تحفة المحتاج في شرح المنهاج وحواشي الشرو ; `16_safii` · 3565 · 15574 · نهاية المحتاج إلى شرح المنهاج (+1 kayıt) |
| Şâfiî: Fethu'l-Mu'în / İ'âne / Gâyetü'l-İhtisâr | ✔ var | `16_safii` · 963 · 4142 · إعانة الطالبين على حل ألفاظ فتح المعين ; `16_safii` · 11327 · 674 · فتح المعين بشرح قرة العين بمهمات الدين (+2 kayıt) |
| Şâfiî: el-Hâvî (Mâverdî) / el-Vasît (Gazâlî) | ✔ var | `16_safii` · 6157 · 11149 · الحاوي الكبير ; `16_safii` · 6128 · 3585 · الوسيط في المذهب |
| Hanbelî: el-Muğnî (İbn Kudâme) | ✔ var | `17_hanbeli` · 6910 · 15518 · المغني لابن قدامة - ت التركي ; `17_hanbeli` · 8463 · 10674 · المغني لابن قدامة - ط مكتبة القاهرة |
| Hanbelî: Keşşâfü'l-Kınâ' / Şerhu Müntehe'l-İrâdât | ✔ var | `17_hanbeli` · 622 · 7827 · كشاف القناع عن متن الإقناع - ط وزارة الع ; `17_hanbeli` · 776 · 5592 · شرح منتهى الإرادات لابن النجار = معونة أ (+2 kayıt) |
| Hanbelî: Zâdü'l-Müstakni' / el-İnsâf | ✔ var | `17_hanbeli` · 19228 · 14605 · الإنصاف في معرفة الراجح من الخلاف - ت ال ; `17_hanbeli` · 21609 · 5685 · الإنصاف في معرفة الراجح من الخلاف - ت ال (+5 kayıt) |
| Karşılaştırmalı: el-Fıkhu ale'l-Mezâhibi'l-Erbaa (Cezîrî) | ✔ var | `18_genel_fikih` · 9849 · 4309 · الفقه على المذاهب الأربعة |
| Karşılaştırmalı: el-Mevsûatü'l-Fıkhiyye el-Kuveytiyye | ✘ **EKSİK/bulunamadı** | Modern ansiklopedi; Şâmile'de farklı adla olabilir — anahtar bulunamadı. |
| Karşılaştırmalı: Fıkhu's-Sünne (Sâbık) | ✘ **EKSİK/bulunamadı** | Modern eser; bulunamadı. |
| Karşılaştırmalı: el-Muhallâ (İbn Hazm) | ✔ var | `18_genel_fikih` · 767 · 5389 · المحلى بالآثار ; `11_usul_fikih` · 21608 · 3733 · حاشية العطار على شرح الجلال المحلي على ج (+1 kayıt) |
| Karşılaştırmalı: el-Fıkhu'l-İslâmî ve Edilletühû (Zuhaylî) | ✘ **EKSİK/bulunamadı** | Modern eser; bulunamadı. |
| Karşılaştırmalı: İhtilâfü'l-Fukahâ / el-İcmâ' (İbnü'l-Münzir) | ✔ var | `18_genel_fikih` · 1568 · 7146 · الأوسط من السنن والإجماع والاختلاف - ط ا ; `18_genel_fikih` · 119492 · 2883 · الإشراف على مذاهب العلماء لابن المنذر (+6 kayıt) |

### Usûl-i fıkıh ve kâideler

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| er-Risâle (Şâfiî) | ✔ var | `11_usul_fikih` · 8180 · 849 · الرسالة للشافعي |
| el-Müstasfâ (Gazâlî) | ✔ var | `11_usul_fikih` · 5459 · 1404 · المستصفى ; `11_usul_fikih` · 1703 · 115 · الضروري في أصول الفقه = مختصر المستصفى |
| el-Burhân (Cüveynî) | ✔ var | `11_usul_fikih` · 13791 · 2928 · التحقيق والبيان في شرح البرهان في أصول ا ; `11_usul_fikih` · 7439 · 672 · البرهان في أصول الفقه |
| el-Mahsûl (Râzî) | ✔ var | `11_usul_fikih` · 14280 · 4032 · نفائس الأصول في شرح المحصول ; `11_usul_fikih` · 2022 · 2180 · المحصول للرازي (+3 kayıt) |
| el-Muvâfakât (Şâtıbî) | ✔ var | `11_usul_fikih` · 11435 · 5342 · الموافقات ; `06_hadis_sunen` · 30134 · 88 · من عوالي الضياء المقدسي تخريجه من المواف (+3 kayıt) |
| el-Fusûl fi'l-Usûl (Cessâs) | ✔ var | `11_usul_fikih` · 676 · 1263 · الفصول في الأصول ; `11_usul_fikih` · 6301 · 724 · أصول السرخسي = تمهيد الفصول في الأصول |
| Keşfü'l-Esrâr (Pezdevî şerhi) | ✔ var | `11_usul_fikih` · 9062 · 6136 · كشف الأسرار عن أصول فخر الإسلام البزدوي ; `32_edebiyat` · 31379 · 53 · كشف الأسرار في حكم الطيور والأزهار |
| el-İhkâm fî Usûli'l-Ahkâm (Âmidî) | ✔ var | `11_usul_fikih` · 10801 · 2062 · الإحكام في أصول الأحكام - الآمدي ; `11_usul_fikih` · 10432 · 1413 · الإحكام في أصول الأحكام - ابن حزم |
| İrşâdü'l-Fuhûl (Şevkânî) | ✔ var | `11_usul_fikih` · 11437 · 1520 · إرشاد الفحول إلى تحقيق الحق من علم الأصو |
| el-Eşbâh ve'n-Nezâir (Suyûtî / İbn Nüceym) | ✔ var | `12_fikih_kaideler` · 21588 · 1757 · غمز عيون البصائر في شرح الأشباه والنظائر ; `12_fikih_kaideler` · 18192 · 1096 · الأشباه والنظائر لابن الملقن ت الأزهري (+4 kayıt) |
| el-Kavâid (İbn Receb / Karâfî el-Furûk) | ✔ var | `31_nahiv_sarf` · 16826 · 9812 · تمهيد القواعد بشرح تسهيل الفوائد ; `12_fikih_kaideler` · 2215 · 5601 · الفروق للقرافي = أنوار البروق في أنواء ا (+20 kayıt) |
| İ'lâmü'l-Muvakkıîn (İbn Kayyim) | ✔ var | `11_usul_fikih` · 17798 · 6039 · إعلام الموقعين عن رب العالمين - ت مشهور ; `11_usul_fikih` · 29911 · 2999 · أعلام الموقعين عن رب العالمين - ط عطاءات (+2 kayıt) |

### Siyer ve şemâil

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| es-Sîre en-Nebeviyye (İbn Hişâm) | ✔ var | `24_siyer` · 23833 · 2738 · سيرة ابن هشام ت السقا ; `24_siyer` · 7450 · 1024 · سيرة ابن هشام ت طه عبد الرؤوف سعد (+1 kayıt) |
| et-Tabakâtü'l-Kübrâ (İbn Sa'd) | ✔ var | `26_teracim` · 146 · 6766 · الطبقات الكبرى - ط الخانجي ; `26_teracim` · 1686 · 3966 · الطبقات الكبرى - ط العلمية (+4 kayıt) |
| Zâdü'l-Me'âd (İbn Kayyim) | ✔ var | `24_siyer` · 197 · 4184 · زاد المعاد في هدي خير العباد - ط عطاءات  ; `24_siyer` · 21713 · 2628 · زاد المعاد في هدي خير العباد - ت الرسالة (+1 kayıt) |
| Dalâilü'n-Nübüvve (Beyhakî / Ebû Nuaym) | ✔ var | `24_siyer` · 7478 · 5373 · دلائل النبوة للبيهقي ; `24_siyer` · 10637 · 938 · دلائل النبوة لأبي نعيم الأصبهاني (+3 kayıt) |
| el-Mevâhibü'l-Ledünniyye (Kastallânî) | ✔ var | `24_siyer` · 26568 · 11461 · شرح الزرقاني على المواهب اللدنية بالمنح  ; `24_siyer` · 23685 · 2388 · المواهب اللدنية بالمنح المحمدية |
| Subulü'l-Hüdâ ve'r-Reşâd (Sâlihî eş-Şâmî) | ✔ var | `24_siyer` · 1693 · 8065 · سبل الهدى والرشاد في سيرة خير العباد |
| es-Sîretü'l-Halebiyye (İnsânü'l-Uyûn) | ✔ var | `24_siyer` · 9873 · 1574 · السيرة الحلبية = إنسان العيون في سيرة ال |
| eş-Şemâilü'l-Muhammediyye (Tirmizî) | ✔ var | `24_siyer` · 13037 · 464 · الشمائل المحمدية للترمذي ط المكتبة التجا ; `24_siyer` · 23647 · 308 · الشمائل المحمدية للترمذي ط إحياء التراث |
| el-Hasâisü'l-Kübrâ (Suyûtî) | ✔ var | `24_siyer` · 6590 · 961 · الخصائص الكبرى |
| el-Megâzî (Vâkıdî) | ✔ var | `24_siyer` · 10695 · 578 · الدرر في اختصار المغازي والسير ; `24_siyer` · 9862 · 386 · سيرة ابن اسحاق = السير والمغازي (+1 kayıt) |
| er-Rahîku'l-Mahtûm | ✔ var | `21_feraiz` · 1635 · 80 · الرحيق المختوم شرح قلائد المنظوم - ط إسط |
| el-Bidâye ve'n-Nihâye (İbn Kesîr; yaratılıştan siyere) | ✔ var | `25_tarih` · 30097 · 16085 · البداية والنهاية - ط دار ابن كثير ; `25_tarih` · 8376 · 13680 · البداية والنهاية - ت شيري (+5 kayıt) |
| Üsdü'l-Gâbe / el-İsâbe (sahâbe tabakâtı) | ✔ var | `26_teracim` · 9767 · 7736 · الإصابة في تمييز الصحابة ; `26_teracim` · 1564 · 5691 · أسد الغابة في معرفة الصحابة - ط الشعب (+3 kayıt) |
| Şifâ-i Şerîf şerhleri (Aliyyülkârî, Hafâcî) | ✔ var | `24_siyer` · 9918 · 1336 · شرح الشفا |

### İslâm tarihi ve kıssa-i enbiyâ

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Taberî Tarihi (Târîhu'r-Rusül ve'l-Mülûk) | ✔ var | `25_tarih` · 9783 · 6435 · تاريخ الطبري = تاريخ الرسل والملوك، وصلة ; `25_tarih` · 6616 · 237 · تكملة تاريخ الطبري |
| el-Kâmil fi't-Târîh (İbnü'l-Esîr) | ✔ var | `25_tarih` · 21712 · 6244 · الكامل في التاريخ - ت تدمري |
| Târîhu'l-İslâm (Zehebî) | ✔ var | `25_tarih` · 12397 · 33748 · تاريخ الإسلام - ت تدمري ; `25_tarih` · 22771 · 15246 · تاريخ الإسلام - ط التوفيقية (+2 kayıt) |
| Siyeru A'lâmi'n-Nübelâ (Zehebî) | ✔ var | `26_teracim` · 10906 · 23114 · سير أعلام النبلاء - ط الرسالة ; `26_teracim` · 22669 · 12381 · سير أعلام النبلاء - ط الحديث |
| Târîhu Dımaşk (İbn Asâkir) | ✔ var | `26_teracim` · 71 · 47950 · تاريخ دمشق لابن عساكر ; `26_teracim` · 3118 · 10589 · مختصر تاريخ دمشق (+1 kayıt) |
| Târîhu Bağdâd (Hatîb el-Bağdâdî) | ✔ var | `26_teracim` · 23764 · 10863 · تاريخ بغداد - ط العلمية ; `26_teracim` · 736 · 9517 · تاريخ بغداد - ت بشار (+2 kayıt) |
| el-Müntazam (İbnü'l-Cevzî) | ✔ var | `25_tarih` · 12406 · 9521 · المنتظم في تاريخ الملوك والأمم |
| Mürûcü'z-Zeheb (Mes'ûdî) | ✘ **EKSİK/bulunamadı** | Mes'ûdî'den yalnız et-Tenbîh ve'l-İşrâf ile Ahbârü'z-Zamân var; Mürûcü'z-Zeheb YOK. |
| Mukaddime / Târîh (İbn Haldûn) | ✔ var | `25_tarih` · 12320 · 8069 · تاريخ ابن خلدون |
| Târîhu'l-Hulefâ (Suyûtî) | ✔ var | `25_tarih` · 11997 · 630 · تاريخ الخلفاء ; `25_tarih` · 12289 · 330 · الإنباء في تاريخ الخلفاء |
| Vefeyâtü'l-A'yân (İbn Hallikân) | ✔ var | `26_teracim` · 1000 · 3483 · وفيات الأعيان |
| el-Vâfî bi'l-Vefeyât (Safedî) | ✔ var | `26_teracim` · 6677 · 7342 · الوافي بالوفيات |
| Şezerâtü'z-Zeheb (İbnü'l-İmâd) | ✔ var | `25_tarih` · 12398 · 6525 · شذرات الذهب في أخبار من ذهب |
| el-Hıtat (Makrîzî) / es-Sülûk | ✔ var | `26_teracim` · 6667 · 3252 · السلوك لمعرفة دول الملوك ; `28_buldan` · 11566 · 1786 · المواعظ والاعتبار بذكر الخطط والآثار |
| Bedâi'u'z-Zühûr (İbn İyâs) | ✘ **EKSİK/bulunamadı** | İbn İyâs YOK (Memlûk dönemi tarihi). |
| Mu'cemü'l-Büldân (Yâkût) | ✔ var | `28_buldan` · 23735 · 3626 · معجم البلدان |
| Kısasü'l-Enbiyâ (İbn Kesîr / Sa'lebî / Nüccâr) | ✔ var | `24_siyer` · 932 · 1430 · قصص الأنبياء من البداية والنهاية - ت عبد |
| Arâisü'l-Mecâlis (Sa'lebî) | ✘ **EKSİK/bulunamadı** | Sa'lebî'den tefsiri (el-Keşf ve'l-Beyân) var; Arâis YOK. |
| Ensâbü'l-Eşrâf (Belâzürî) / Fütûhu'l-Büldân | ✔ var | `27_ensab` · 9773 · 5557 · أنساب الأشراف - ط الفكر ; `27_ensab` · 1379 · 713 · أنساب الأشراف - ت حميد الله (+1 kayıt) |
| Târîhu'l-Hamîs / el-Hulefâ er-Râşidûn | ✔ var | `24_siyer` · 9784 · 1236 · تاريخ الخميس في أحوال أنفس النفيس |

### Tasavvuf ve ahlâk

| Eser | Durum | Şâmile kaydı (kategori · book_id · parça) |
|---|---|---|
| Kuşeyrî (er-Risâletü'l-Kuşeyriyye) | ✔ var | `23_rekaik_adab` · 9953 · 562 · الرسالة القشيرية |
| Gazâlî (İhyâü Ulûmi'd-Dîn) | ✔ var | `23_rekaik_adab` · 9472 · 3197 · إحياء علوم الدين ; `08_tahric_etraf` · 38171 · 2785 · تخريج أحاديث إحياء علوم الدين (+1 kayıt) |
| Gazâlî (Mîzânü'l-Amel / Minhâcü'l-Âbidîn / Bidâyetü'l-Hidâye / Mişkâtü'l-Envâr) | ✔ var | `23_rekaik_adab` · 9264 · 231 · ميزان العمل ; `23_rekaik_adab` · 12421 · 89 · مشكاة الأنوار (+1 kayıt) |
| Ebû Nuaym (Hilyetü'l-Evliyâ) | ✔ var | `06_hadis_sunen` · 10495 · 4313 · حلية الأولياء وطبقات الأصفياء - ط السعاد |
| Sülemî (Tabakâtü's-Sûfiyye) | ✔ var | `26_teracim` · 6686 · 405 · طبقات الصوفية للسلمي ويليه ذكر النسوة ال |
| Serrâc (el-Lüma' fi't-Tasavvuf) | ✘ **EKSİK/bulunamadı** | Serrâc'ın el-Lüma'ı YOK (Sülemî'nin bazı risâleleri var). |
| Ebû Tâlib el-Mekkî (Kûtü'l-Kulûb) | ✔ var | `23_rekaik_adab` · 482 · 983 · قوت القلوب في معاملة المحبوب ووصف طريق ا |
| Kelâbâzî (et-Ta'arruf li-Mezhebi Ehli't-Tasavvuf) | ✔ var | `01_akaid` · 6518 · 159 · التعرف لمذهب أهل التصوف |
| Herevî (Menâzilü's-Sâirîn) | ✔ var | `23_rekaik_adab` · 6876 · 137 · منازل السائرين |
| İbn Kayyim (Medâricü's-Sâlikîn) | ✔ var | `23_rekaik_adab` · 199 · 2566 · مدارج السالكين - ط عطاءات العلم ; `23_rekaik_adab` · 8370 · 1533 · مدارج السالكين - ط الكتاب العربي |
| Sühreverdî (Avârifü'l-Me'ârif) | ✘ **EKSİK/bulunamadı** | Avârifü'l-Me'ârif YOK. |
| İbn Atâillah (el-Hikem; Letâifü'l-Minen) ve şerhleri | ✘ **EKSİK/bulunamadı** | el-Hikem, Letâifü'l-Minen ve şerhleri YOK — Mimar'ın tasavvuf önceliği için kritik. |
| İbn Arabî (el-Fütûhâtü'l-Mekkiyye) | ✘ **EKSİK/bulunamadı** | YOK (yalnız İbn Arabî'yi reddeden eserler var: ör. Bikâî Masra'ut-Tasavvuf). Mimar'ın kararı: İbn Arabî tasavvuf ve Ehl-i Sünnet çizgisi değerlendirmesi. |
| İbn Arabî (Fusûsü'l-Hikem) ve şerhleri | ✘ **EKSİK/bulunamadı** | YOK (yalnız reddiyeler). |
| Abdülkâdir Geylânî (Gunyetü't-Tâlibîn / el-Fethu'r-Rabbânî / Fütûhu'l-Gayb) | ✔ var | `07_hadis_serh` · 124910 · 13049 · الفتح الرباني لترتيب مسند الإمام أحمد بن ; `03_tefsir` · 20891 · 9345 · فتوح الغيب في الكشف عن قناع الريب (حاشية (+2 kayıt) |
| Şa'rânî (et-Tabakâtü'l-Kübrâ / el-Yevâkît ve'l-Cevâhir) | ✘ **EKSİK/bulunamadı** | Şa'rânî (et-Tabakât, el-Yevâkît) YOK. |
| Nablusî (el-Hadîkatü'n-Nediyye / Şerhu Mesnevî / Tasavvuf eserleri) | ✘ **EKSİK/bulunamadı** | Nablusî'den yalnız Ta'tîrü'l-Enâm (rüya tabiri) var. |
| Mevlânâ (Mesnevî / Dîvân-ı Kebîr — Arapça çeviri/şerh) | ✘ **EKSİK/bulunamadı** | Mevlânâ'nın Mesnevî/Dîvân'ı (Farsça) ve Arapça çevirisi YOK. |
| Hârisü'l-Muhâsibî (er-Riâye li-Hukûkıllâh) | ✔ var | `23_rekaik_adab` · 6875 · 164 · مقاصد الرعاية لحقوق الله عز وجل |
| Cüneyd / Bistâmî / Hallâc / Hakîm Tirmizî (Hatmü'l-Evliyâ) | ✘ **EKSİK/bulunamadı** | Hakîm Tirmizî'den başka eserler var (Nevâdirü'l-Usûl, Rıyâdetü'n-Nefs); Hatmü'l-Evliyâ YOK. |
| Ahmed Zerrûk / Şâzelî (Kavâidü't-Tasavvuf) | ✘ **EKSİK/bulunamadı** | Zerrûk'tan Uddetü'l-Mürîd var; Kavâidü't-Tasavvuf YOK. |
| Zühd: İbnü'l-Mübârek / Ahmed b. Hanbel (Kitâbü'z-Zühd) | ✔ var | `23_rekaik_adab` · 8494 · 2493 · الزهد لأحمد بن حنبل ; `06_hadis_sunen` · 13028 · 2173 · الزهد والرقائق - ابن المبارك - ت الأعظمي (+14 kayıt) |
| İbn Kayyim (el-Fevâid / el-Vâbilü's-Sayyib / Ravdatü'l-Muhibbîn) | ✔ var | `08_tahric_etraf` · 26324 · 32174 · إتحاف المهرة بالفوائد المبتكرة من أطراف  ; `06_hadis_sunen` · 36446 · 10666 · جمع الفوائد من جامع الأصول ومجمع الزوائد (+71 kayıt) |
| İbnü'l-Cevzî (Sıfatü's-Safve / Telbîsü İblîs) | ✔ var | `23_rekaik_adab` · 12031 · 1840 · صفة الصفوة ; `23_rekaik_adab` · 11438 · 496 · تلبيس إبليس |
| Mâverdî (Edebü'd-Dünyâ ve'd-Dîn) | ✔ var | `23_rekaik_adab` · 765 · 342 · أدب الدنيا والدين |
| İbn Ebi'd-Dünyâ (Mekârimü'l-Ahlâk / Kitâbü't-Tevbe) | ✔ var | `06_hadis_sunen` · 9595 · 1131 · مكارم الأخلاق للخرائطي ; `06_hadis_sunen` · 11930 · 842 · المنتقى من كتاب مكارم الأخلاق ومعاليها (+5 kayıt) |
| Buhârî (el-Edebü'l-Müfred) | ✔ var | `06_hadis_sunen` · 12991 · 2012 · الأدب المفرد - ت عبد الباقي ; `06_hadis_sunen` · 9647 · 737 · الأدب المفرد - بأحكام الألباني - ت الزهي |
| Beyhakî (Şu'abü'l-Îmân) | ✔ var | `06_hadis_sunen` · 10660 · 12323 · شعب الإيمان - ط الرشد ; `06_hadis_sunen` · 748 · 3816 · شعب الإيمان - ت زغلول (+3 kayıt) |
| Halîmî (el-Minhâc fî Şu'abi'l-Îmân) | ✔ var | `01_akaid` · 18567 · 1512 · المنهاج في شعب الإيمان |
| Sülemî (Âdâbü's-Suhbe, Fütüvvet, el-Erba'în fi't-Tasavvuf) | ✔ var | `06_hadis_sunen` · 12982 · 190 · آداب الصحبة لأبي عبد الرحمن السلمي ; `06_hadis_sunen` · 26864 · 92 · الفتوة لأبي عبد الرحمن السلمي (+2 kayıt) |
| Hakîm Tirmizî (Nevâdirü'l-Usûl / Rıyâdetü'n-Nefs) | ✔ var | `06_hadis_sunen` · 720 · 1237 · نوادر الأصول في أحاديث الرسول ; `23_rekaik_adab` · 37033 · 48 · رياضة النفس |
| Hârisü'l-Muhâsibî (Fehmü'l-Kur'ân / et-Tevehhüm) | ✔ var | `04_kuran_ilim_usul` · 5550 · 257 · فهم القرآن ; `23_rekaik_adab` · 21799 · 109 · التوهم في وصف أحوال الآخرة |
| Zerrûk (Uddetü'l-Mürîd es-Sâdık) | ✔ var | `23_rekaik_adab` · 123663 · 414 · عدة المريد الصادق |

## 4) Zayıf / eksik alanlar (tespit)

- **Akaid ve kelâm (Eş'arî-Mâtürîdî)**: aranan 20 çekirdek eserin 11'i bulundu (%55).
- **Tasavvuf ve ahlâk**: aranan 33 çekirdek eserin 23'i bulundu (%70).

Şâmile dışı / doğası gereği zayıf noktalar:
- **Türkçe kaynak yok**: bütün shard'lar Arapça; Türkçe soru ↔ Arapça eser eşleşmesi tek köprü (K3 sorgu genişletme). Türkçe ilmihâl/tefsir/tasavvuf (ör. Elmalılı, Ömer Nasuhi Bilmen, Mesnevî Türkçe) kütüphanede yok → Mimar kararı.
- **Kur'ân metni**: ayrı bir mushaf/meal shard'ı yok; ayet metni tefsirlerin içinde (parça bazlı). «ayet bul» için ayrı bir Kur'ân ayet indeksi yok.
- **Tasavvuf**: ayrı shard yok; `23_rekaik_adab` + `39_genel/40_diger` içinde dağınık (aşağıya bakın). Mevlânâ (Farsça Mesnevî) Şâmile'de yok, yalnız Arapça şerh/özet olabilir.
- **Modern İslâm tarihi (Osmanlı → bugün)**: `25_tarih` ağırlıklı klasik dönem; Osmanlı/Cumhuriyet dönemi Arapça eserlerle sınırlı.
- **Mükerrer cilt/baskı**: aynı eser birden çok book_id ile görünüyor olabilir (parça sayısı şişer; çeşitlilik sorunu için D2).

## 5) Tasavvuf ve ahlâk taraması (anahtar kelime ile eser adı)

Eser adında tasavvuf anahtarı geçen kayıt: **56**. İlk 40:

- `08_tahric_etraf` · 21550 · تخريج أحاديث الإحياء = المغني عن حمل الأسفار — العراقي (4761 parça)
- `06_hadis_sunen` · 10495 · حلية الأولياء وطبقات الأصفياء - ط السعادة — أبو نعيم الأصبهاني (4313 parça)
- `26_teracim` · 6667 · السلوك لمعرفة دول الملوك — المقريزي (3252 parça)
- `23_rekaik_adab` · 9472 · إحياء علوم الدين — أبو حامد الغزالي (3197 parça)
- `08_tahric_etraf` · 38171 · تخريج أحاديث إحياء علوم الدين — مرتضى الزبيدي (2785 parça)
- `23_rekaik_adab` · 23625 · الفتوحات الربانية على الأذكار النواوية — ابن علان (2734 parça)
- `23_rekaik_adab` · 199 · مدارج السالكين - ط عطاءات العلم — ابن القيم (2566 parça)
- `03_tefsir` · 122173 · درج الدرر في تفسير الآي والسور ط الحكمة — عبد القاهر الجرجاني (2449 parça)
- `07_hadis_serh` · 10443 · جامع العلوم والحكم - ت أبي النور — ابن رجب الحنبلي (2199 parça)
- `07_hadis_serh` · 949 · جامع العلوم والحكم - ت الفحل — ابن رجب الحنبلي (1663 parça)
- `23_rekaik_adab` · 8370 · مدارج السالكين - ط الكتاب العربي — ابن القيم (1533 parça)
- `07_hadis_serh` · 4268 · جامع العلوم والحكم - ت الأرنؤوط — ابن رجب الحنبلي (1205 parça)
- `01_akaid` · 205 · شفاء العليل في مسائل القضاء والقدر والحكمة والتعليل - ط عطاء — ابن القيم (1045 parça)
- `20_siyaset_kaza` · 18159 · الطرق الحكمية في السياسة الشرعية - ط عطاءات العلم — ابن القيم (1025 parça)
- `26_teracim` · 6668 · السلوك في طبقات العلماء والملوك — الجندي، بهاء الدين (1016 parça)
- `23_rekaik_adab` · 482 · قوت القلوب في معاملة المحبوب ووصف طريق المريد إلى مقام التوح — أبو طالب المكي (983 parça)
- `32_edebiyat` · 7414 · زهر الأكم في الأمثال والحكم — الحسن اليوسي (902 parça)
- `15_maliki` · 1206 · المختصر الصغير لابن عبد الحكم «خلافيات في الفقه» — ابن عبد الحكم الفقيه (682 parça)
- `23_rekaik_adab` · 17817 · الغنية لطالبي طريق الحق — عبد القادر الجيلاني (666 parça)
- `23_rekaik_adab` · 22842 · موعظة المؤمنين من إحياء علوم الدين — جمال الدين القاسمي (645 parça)
- `23_rekaik_adab` · 9953 · الرسالة القشيرية — عبد الكريم القشيري (562 parça)
- `14_hanefi` · 13784 · منحة السلوك في شرح تحفة الملوك — بدر الدين العيني (463 parça)
- `11_usul_fikih` · 9885 · مذكرة أصول الفقه على روضة الناظر- ط مكتبة العلوم والحكم — محمد الأمين الشنقيطي (424 parça)
- `01_akaid` · 12021 · شفاء العليل في مسائل القضاء والقدر والحكمة والتعليل - ط المع — ابن القيم (421 parça)
- `26_teracim` · 6686 · طبقات الصوفية للسلمي ويليه ذكر النسوة المتعبدات الصوفيات — أبو عبد الرحمن السلمي (405 parça)
- `01_akaid` · 8317 · مصرع التصوف = تنبيه الغبي إلى تكفير ابن عربي وتحذير العباد م — برهان الدين البقاعي (375 parça)
- `20_siyaset_kaza` · 11495 · الطرق الحكمية في السياسة الشرعية - ط البيان — ابن القيم (372 parça)
- `26_teracim` · 26336 · إخبار العلماء بأخبار الحكماء — جمال الدين القفطي (355 parça)
- `23_rekaik_adab` · 16759 · الأمثال والحكم - الماوردي — الماوردي (311 parça)
- `06_hadis_sunen` · 26463 · الغنية في شيوخ القاضي عياض — القاضي عياض (196 parça)
- `06_hadis_sunen` · 8247 · الأربعون في شيوخ الصوفية للماليني — الماليني (187 parça)
- `12_fikih_kaideler` · 20763 · الفروق الفقهية للدمشقي - ط الحكمة — أبو الفضل الدمشقي (178 parça)
- `01_akaid` · 6518 · التعرف لمذهب أهل التصوف — أبو بكر الكلاباذي (159 parça)
- `23_rekaik_adab` · 6876 · منازل السائرين — أبو إسماعيل الهروي (137 parça)
- `20_siyaset_kaza` · 7241 · حسن السلوك الحافظ دولة الملوك — ابن الموصلي (133 parça)
- `23_rekaik_adab` · 31375 · في السلوك الإسلامي القويم — ابن الشوكاني (121 parça)
- `32_edebiyat` · 6903 · السحر الحلال في الحكم والأمثال — أحمد الهاشمي (115 parça)
- `20_siyaset_kaza` · 96556 · المال والحكم في الإسلام — عبد القادر عودة (108 parça)
- `19_fikhi_meseleler` · 450 · الحكم المشروع في الطلاق المجموع - ضمن «آثار المعلمي» — عبد الرحمن المعلمي اليماني (107 parça)
- `06_hadis_sunen` · 8246 · الأربعون على مذهب المتحققين من الصوفية لأبي نعيم الأصبهاني — أبو نعيم الأصبهاني (100 parça)

## 5b) Akaid shard'ında yazar çizgisi dağılımı (Mimar'ın bilgisi için)

Yazar adı anahtarlarına göre kaba dağılım (`eval/din/cekirdek_eserler.json` → `okul_yazar_anahtarlari`). Bu bir **hüküm değil dağılım**dır; Ehl-i Sünnet çizgisinin korunması için cevap üretiminde hangi eserlerin öne çıkacağı D2'de ele alınır.

| Çizgi (anahtar listesi) | Kitap | Parça | Pay |
|---|---:|---:|---:|
| Eş'arî / Mâtürîdî / Şâfiî-Mâlikî-Hanefî kelâm çizgisi | 21 | 6.394 | %5.0 |
| Selefî-Hanbelî / Necid çizgisi | 126 | 54.539 | %42.5 |

Akaid shard'ında en çok parçası olan 12 yazar: ابن تيمية (31767) · ابن المحب الصامت (8177) · ابن الوزير (5615) · ابن القيم (5458) · ابن بطة (3531) · الشاطبي الأصولي النحوي (3316) · محمود شكري الألوسي (2878) · ابن أبي العز (2707) · عبد الرحمن بن حسن آل الشيخ (2597) · عبد الرحمن المعلمي اليماني (2466) · عثمان بن سعيد الدارمي (2458) · حافظ بن أحمد حكمي (2300)

> Not: manifestlerin hepsi `hat=ehlisunnet` etiketli (reddiyeler `katman=C`); etiket yazar/okul ayrımı yapmaz. Sentezde okul dengesi için D2'de «Eş'arî/Mâtürîdî ağırlıklı yazarları öne çıkarma» seçeneği Mimar kararı olarak sunulur.

## 6) Her kategorinin en büyük 3 eseri (parça sayısı)

- `01_akaid` (Akaid): Nebi Sallallahu Aleyhi ve Sellem'in Sünneti (8145) · The Attributes of the Lord of the Universe - Academic Messages - Incomplete (5836) · Cehmîlerin İtikâdî İhtilâfına Karşı Çözüm (4879)
- `02_firak_redler` (Fırak ve reddiyeler): Kösük (1509) · Cehmiye ve İlgisizler Üzerine Gönderilen Şimşekler - İstanbul Baskısı (1428) · Dinler ve Mezhepler Hakkında (1404)
- `03_tefsir` (Tefsir): Razi Tefsiri (21810) · Taberî Tefsiri (20216) · Taberî Tefsiri (17493)
- `04_kuran_ilim_usul` (Kur'ân ilimleri): Kur'an Hukukları el-Cessas (5615) · Kutsal Kur'an'ın İ'rabı Hakkında Kitap (4407) · Quran Bilgisinde Artış ve İyilik (4238)
- `05_tecvid_kiraat` (Tecvid ve kırâat): Yedi Okuma Şeklinin Açıklanması (3164) · El-Hüccetü li'l-Kurââtü's-Sevbe (2953) · Quran Okumayı Başlayanlara ve Bitirmiş Olganlara İlerleme - Quran Okumayı Başlayanlara ve Bitirmiş Olganlara İlerleme (2811)
- `06_hadis_sunen` (Hadis (kütüb/sünen/müsned)): El-Musannef - İbn Ebî Şeybe - El-Şeybani (46584) · Hadisler Koleksiyonu (42924) · Câmiü'l-Kebîr (34379)
- `07_hadis_serh` (Hadis şerhleri): Fethü'l-Bârî Şih-i Buhârî - el-Selfiye (27203) · Qarî'nin Şehâdi - Sahih-i Buhârî (26370) · Sahihin Açıklaması (21890)
- `08_tahric_etraf` (Tahrîc ve etrâf): İntihap-i Mehreyye (İslam Akidelerini Kolaylaştırma) (32174) · Akraba Hadisler Hakkında Ihsan (28774) · İtâraf-i Mesnad (Mesnad'da Hadisler) (17173)
- `09_ilel_sual` (İlel ve suâlât): Al-'Ilal Al-Darqutnîye (Al-'Ilal Nedensiz Ahadis) (6701) · El-Elalü'l-Hamidi (5678) · El-Defa'ü'l-Kebir (4625)
- `10_hadis_ilimleri` (Hadis ilimleri): Hadis Bilgisi ve Din Bilgisine Uyum (2236) · İbn-i Salah'ın Önsözü ve İslahî İlimlerin Güzellikleri (1486) · Hadis'in Açıklaması ile İlgili Bağımsızlık (1419)
- `11_usul_fikih` (Usûl-i fıkıh): İslam'ın Önderi Buzdavi'nin Asılları (6136) · Allah'ın Evreni Yöneten Rabbı Bilme (6039) · İmzalı Kitap (5342)
- `12_fikih_kaideler` (Fıkıh kâideleri): Hakanların Cenneti (7339) · Kuraflı'nın Farklılıkları = Işık Yılı Farklılıklarında Yaygın Farklılıklar (5601) · Fıkıh Usulü İle İlgili Birleştirme ve Ayrılma (2128)
- `13_mantik` (Mantık): Araştırma ve Tartışma Adabı (383) · Mantık ve Fıkıh Kuralları Hakkında Kısa Açıklama (286) · Bilgi Alanında Kriter (286)
- `14_hanefi` (Hanefî fıkhı): Serahsi'nin Müsaiti (17545) · İbn Abidin'in Haşiyesi (16815) · El-Berî'ü'r-Râkık (15326)
- `15_maliki` (Mâlikî fıkhı): Şerh-i Hareşi Üzerine Kısa Şerh - Ve Hâşiye-i Edvi (13654) · Lâmi'ü'l-Durri fî Hükmü'l-Muktezâ (12929) · Şeyh Derder'in Büyük Şerhi ve Düsküki'nin Notları (11060)
- `16_safii` (Şâfiî fıkhı): Doğru Yolun açıklaması ve Şerwânî ve Ebûbâdî'nin notları (27474) · Mezni'nin İhtiyacı ile Manevi Yolun Açıklaması (15574) · El-Cemel'in Şerhu'l-Menhece'ne Şerhi (14897)
- `17_hanbeli` (Hanbelî fıkhı): Zâdü'l-Me'talın Açıklaması (15701) · 〔Türkçe anlam bekler〕 (15518) · Fıkhi Rağbetin Tespitine Dair İnsâf (14605)
- `18_genel_fikih` (Genel/karşılaştırmalı fıkıh): Ahadis, İcma ve Muhakeme - Fıkhı'l-Falah (7146) · Eserler ve Etkiler (5389) · Dört Mezhebe Göre Fıkıh (4309)
- `19_fikhi_meseleler` (Fıkhî meseleler): Dinî Ahkâm-ı Zimmîler - Tahtayi Ramazan (1326) · Dinî Ahkâm-ı Zimmîler - Tahtayi Ataât-ı Ulûm (1180) · Boşanma İle İlgili Soruşturma (1106)
- `20_siyaset_kaza` (Siyâset ve kazâ): Şerhü's-Sîru'l-Kebîr (2213) · İtkân ve Ahkâm (2029) · Buhârî'nin Tefsiri (1800)
- `21_feraiz` (Ferâiz): Mirasların Önemli Kavramları (815) · Miras Hukuku (160) · Miras Hukuku ve Vasiyet Ahkâmı (122)
- `22_fetvalar` (Fetvâlar): Şeyh Muhammed bin İbrahim bin Abdüllatif el-Şeyhin Fıkıh Yorumları ve Mektupları (3872) · Fıkıh Sorularına Cevaplar (1303) · Necd Fıkıh Soruları ve Makaleleri (3. Cilt) (540)
- `23_rekaik_adab` (Rekâik, âdâb, zühd (tasavvuf-ahlâk)): İnsanların İlgisi (6638) · Menzurî'nin Terbiye ve Tehdid (4510) · Mahmudiye İnceliği - Muhammed'i Yolu ve Nabiye Şer'iyesi Ahmed'i Yolu (3783)
- `24_siyer` (Siyer ve şemâil): Zarkani'nin Muhammedî Menkıbeleri Üzerine Açıklamalar (11461) · Dinleyicilerin İncisi (8637) · İyilik Olanların Sünneti (8065)
- `25_tarih` (Tarih): Tarihi Islam - Tarihi Islam (33748) · Mârahâtü'l-Zemân fi Târîkhı'l-Ā'yan - Mârahâtü'l-Zemânın Ā'yanın Tarihindeki Mârahâtı (16698) · El-Bidayâ ve'n-Nihâye - Terc. Dar-i Ibn-i Hacer (16085)
- `26_teracim` (Terâcim ve tabakât): İbn Asakir'in Şam Tarihi (47950) · Nefelilerin Hikâyeleri - Risale (23114) · Tehdid el-Kamal fi Asamir el-Rijal (21290)
- `27_ensab` (Ensâb): Anasab - Es-Semâvî - Hint (5634) · Anasabü'l-Ashrâf - Fekr (5557) · Anasab - Es-Semâvî - Emîn Demirci (5059)
- `28_buldan` (Büldân (coğrafya)): Görmek İçin Yolculuk Etmek (7740) · 〔Türkçe anlam bekler〕 (5805) · hakkında / içinde Tarih 〔Türkçe tam anlam bekler〕 (4679)
- `29_dil` (Dil): Teymur'un Büyük Sözlüğü (1792) · Fasih Dil (1018) · İmla Sanatı (997)
- `30_garib_lugat` (Garîb ve lügat): Güzellik Taçları (21563) · Lisanu'l-Ârâb - Lisanu'l-Ârâb Kitabı (17472) · Arapların Kullandığı Kelimelerin İyileştirilmesi (8623)
- `31_nahiv_sarf` (Nahiv-sarf): Fıtratın Temellerini Kolaylaştırma (9812) · İbn Malik'in Felsefesi Anlatımı (5493) · El-Mefsu'l-İbâdî Şerhi (4573)
- `32_edebiyat` (Edebiyat): El-Resale Dergisi (65431) · Edebiyat Sanatları (13766) · Ebû İshâk el-İsfahânî'nin Sabahı Fırsatın açıklaması (7500)
- `33_aruz` (Arûz): Kâfî'nin Kısa Qavâfi Kitabı (226) · Redif ve Qavâfi Bilgisi (215) · Gizli Anlamda Kalem (199)
- `34_divanlar` (Dîvânlar): Zü'l-Rümeym'in Divanı (1895) · Cerrah'ın Divanı (992) · Ebü'n-Nebî'ten Dîvân (596)
- `35_belagat` (Belâgat): Anlamın Kısa Özetine Ait Açıklamalar (3083) · Aṣlūl Sharḥ Ṭelḥīṣ Miftāḥ al-ʿUlūm - Blâğatın Usûlleri'nin Telhîsli Sharḥı (1698) · Sevgi Çiçekleri: Miftah'ın Kısa Özetinin Açıklaması (1611)
- `36_cevami` (Câmi' (karma)): Menar Dergisi (32285) · Feth Muhendisligi (17217) · Sönmeyen Yıldızlar: Cevaplar (7895)
- `37_fihrist` (Fihrist): Kitap ve Fenler Kataloğu - F.İ. Kuran (5693) · Kitap ve Fenler Kataloğu - İ.İstanbul (2923) · Arapça ve Arapça Olarak Basılmış Kitaplar Listesi (2057)
- `38_tip` (Tıp): Tıp Ansiklopedisi (3272) · Tıp Kanunu (2169) · Nebi Sallallahu Aleyhi ve Sellem'in Tıp Bilgisi (536)
- `39_genel` (Genel): İhtida'nın Zararları (616) · Arap Medeniyeti (598) · İslam'ın İlanı ve İmperiyalizm (484)
- `40_diger` (Diğer): Kelimelerin Anlamı (975) · Rüya Anlatımı - Anlam (960) · Rüya Anlatımı = Klasik Rüya Anlatımı (830)

## 7) EKSİK LİSTESİ — Mimar'a (karar Mimar'da; ajan eser eklemedi/indirmedi)

Aşağıdaki çekirdek eserler indekste bulunamadı. Eklenip eklenmeyeceği, kaynak (Şâmile'den çıkarım / başka koleksiyon) ve lisans Mimar kararıdır.

- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Nesefî (el-Akâid) / Teftâzânî Şerhu'l-Akâid** — Şâmile'de yalnız Nesefî'nin tefsiri/fıkıh eserleri var; el-Akâid ve Teftâzânî şerhi YOK (Eş'arî-Mâtürîdî okul metni).
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Teftâzânî (Şerhu'l-Makâsıd)** — Teftâzânî'den yalnız et-Telvîh (usûl) var.
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Îcî / Cürcânî (el-Mevâkıf ve Şerhi)** — Îcî'den yalnız Şerhu'l-Adud (usûl) ve tefsiri var; el-Mevâkıf YOK.
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Cüveynî (el-Irşâd)** — Cüveynî'den Lum'u'l-Edille ve el-Verakât var; el-Irşâd YOK.
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Ebu'l-Muîn en-Nesefî (Tabsıratü'l-Edille)** — Nesefî Ebu'l-Muîn'in Tabsıra'sı YOK.
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Pezdevî (Usûlü'd-Dîn)** — Pezdevî'den yalnız usûl-i fıkıh (Keşfü'l-Esrâr şerhi) var; Usûlü'd-Dîn YOK.
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Beyhakî (el-İ'tikād ve'l-Hidâye)** — Beyhakî'den Şuabü'l-Îmân ve Sünen var; el-İ'tikād ve'l-Hidâye YOK.
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Sünûsî (Ümmü'l-Berâhîn) / Cevheretü't-Tevhîd** — Ümmü'l-Berâhîn/Cevheretü't-Tevhîd YOK (Mâlikî-Eş'arî ilmihâl akaidi).
- [Akaid ve kelâm (Eş'arî-Mâtürîdî)] **Sâbûnî (el-Bidâye fî Usûli'd-Dîn)** — Sâbûnî'nin el-Bidâye'si YOK.
- [Fıkıh — dört mezhep ve karşılaştırmalı] **Karşılaştırmalı: el-Mevsûatü'l-Fıkhiyye el-Kuveytiyye** — Modern ansiklopedi; Şâmile'de farklı adla olabilir — anahtar bulunamadı.
- [Fıkıh — dört mezhep ve karşılaştırmalı] **Karşılaştırmalı: Fıkhu's-Sünne (Sâbık)** — Modern eser; bulunamadı.
- [Fıkıh — dört mezhep ve karşılaştırmalı] **Karşılaştırmalı: el-Fıkhu'l-İslâmî ve Edilletühû (Zuhaylî)** — Modern eser; bulunamadı.
- [İslâm tarihi ve kıssa-i enbiyâ] **Mürûcü'z-Zeheb (Mes'ûdî)** — Mes'ûdî'den yalnız et-Tenbîh ve'l-İşrâf ile Ahbârü'z-Zamân var; Mürûcü'z-Zeheb YOK.
- [İslâm tarihi ve kıssa-i enbiyâ] **Bedâi'u'z-Zühûr (İbn İyâs)** — İbn İyâs YOK (Memlûk dönemi tarihi).
- [İslâm tarihi ve kıssa-i enbiyâ] **Arâisü'l-Mecâlis (Sa'lebî)** — Sa'lebî'den tefsiri (el-Keşf ve'l-Beyân) var; Arâis YOK.
- [Tasavvuf ve ahlâk] **Serrâc (el-Lüma' fi't-Tasavvuf)** — Serrâc'ın el-Lüma'ı YOK (Sülemî'nin bazı risâleleri var).
- [Tasavvuf ve ahlâk] **Sühreverdî (Avârifü'l-Me'ârif)** — Avârifü'l-Me'ârif YOK.
- [Tasavvuf ve ahlâk] **İbn Atâillah (el-Hikem; Letâifü'l-Minen) ve şerhleri** — el-Hikem, Letâifü'l-Minen ve şerhleri YOK — Mimar'ın tasavvuf önceliği için kritik.
- [Tasavvuf ve ahlâk] **İbn Arabî (el-Fütûhâtü'l-Mekkiyye)** — YOK (yalnız İbn Arabî'yi reddeden eserler var: ör. Bikâî Masra'ut-Tasavvuf). Mimar'ın kararı: İbn Arabî tasavvuf ve Ehl-i Sünnet çizgisi değerlendirmesi.
- [Tasavvuf ve ahlâk] **İbn Arabî (Fusûsü'l-Hikem) ve şerhleri** — YOK (yalnız reddiyeler).
- [Tasavvuf ve ahlâk] **Şa'rânî (et-Tabakâtü'l-Kübrâ / el-Yevâkît ve'l-Cevâhir)** — Şa'rânî (et-Tabakât, el-Yevâkît) YOK.
- [Tasavvuf ve ahlâk] **Nablusî (el-Hadîkatü'n-Nediyye / Şerhu Mesnevî / Tasavvuf eserleri)** — Nablusî'den yalnız Ta'tîrü'l-Enâm (rüya tabiri) var.
- [Tasavvuf ve ahlâk] **Mevlânâ (Mesnevî / Dîvân-ı Kebîr — Arapça çeviri/şerh)** — Mevlânâ'nın Mesnevî/Dîvân'ı (Farsça) ve Arapça çevirisi YOK.
- [Tasavvuf ve ahlâk] **Cüneyd / Bistâmî / Hallâc / Hakîm Tirmizî (Hatmü'l-Evliyâ)** — Hakîm Tirmizî'den başka eserler var (Nevâdirü'l-Usûl, Rıyâdetü'n-Nefs); Hatmü'l-Evliyâ YOK.
- [Tasavvuf ve ahlâk] **Ahmed Zerrûk / Şâzelî (Kavâidü't-Tasavvuf)** — Zerrûk'tan Uddetü'l-Mürîd var; Kavâidü't-Tasavvuf YOK.

### Kategori/İçerik düzeyinde eksikler (Mimar kararı)

1. Türkçe temel kaynaklar (tefsir, ilmihâl, tasavvuf klasiklerinin Türkçe çevirileri) — şu an yok; cevap Arapça kaynaktan Türkçeye sentezleniyor.
2. Kur'ân-ı Kerîm mushaf metni + meal + sûre/ayet künye tablosu (ayet numarası verebilmek için).
3. Kütüb-i Sitte için hadis numaralı, bölüm başlıklı (kitap/bâb) yapılandırılmış künye (hadis no verebilmek için).
4. Tasavvuf klasiklerinin eksik olanları (yukarıdaki tabloya bakın).
5. Modern dönem İslâm/Osmanlı tarihi (Türkçe).
