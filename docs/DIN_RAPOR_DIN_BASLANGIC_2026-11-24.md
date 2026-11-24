# Din raporu — din_baslangic (2026-11-24)

Yalnız **din rafı** (web kapalı). Koşucu: `scripts/altin_set_kos.py din-rapor`; ölçütler: `scripts/din_olcut.py`.

| Ölçüt | Değer |
|---|---:|
| Soru sayısı | 130 |
| Doğru cevap % | %36.2 |
| «Bulamadım» % | %27.7 |
| Ort. kapsama | 0.392 |
| (a) «Kaynak göster» varyantlarında künye gelen % | %0.0 |
| (a) Tüm din cevaplarında doğrulanmış künye % | %0.0 |
| (b) Çoklu eser (≥2 farklı eser anışı) % | %0.0 |
| (b) Çoklu eser — yalnız «kaynak göster» varyantlarında % | %0.0 |
| (c) Uydurma kaynak şüphesi — soru sayısı | 30 |
| (c) Uydurma kaynak şüphesi — atıf sayısı | 47 |
| (d) Sadelik ajan puanı (1–5) | — |
| Medyan sn | 4.13 |
| P90 sn | 18.95 |

Sağlayıcılar: {'None': 47, 'miss_kutuphane': 35, 'gemini': 23, 'hizli': 20, 'kutuphane_extractive': 5}

## Alt-raf bazında

| Alt-raf | N | Doğru % | Bulamadım % |
|---|---:|---:|---:|
| akaid | 21 | 38.1 | 19.0 |
| fikih | 18 | 22.2 | 33.3 |
| hadis | 11 | 54.5 | 45.5 |
| kissa | 8 | 0.0 | 87.5 |
| siyer | 13 | 15.4 | 23.1 |
| tarih | 4 | 25.0 | 0.0 |
| tasavvuf | 24 | 54.2 | 12.5 |
| tefsir | 11 | 45.5 | 0.0 |
| temel | 20 | 40.0 | 40.0 |

## «Kaynak göster» varyantları

| id | Soru | Künye? | Eser sayısı | Şüpheli atıf |
|---|---|:-:|---:|---|
| `din-116` | Abdesti bozan şeyler nelerdir? Kaynak göster. | ✘ | 0 |  |
| `din-117` | Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göste | ✘ | 0 | Bunu kütüphanemdeki şu eserlerden okudum… |
| `din-118` | Kader nedir? Hangi eserlere dayanarak anlatıyorsun, kaynak v | ✘ | 0 |  |
| `din-119` | Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçi | ✘ | 0 | Bunu kütüphanemdeki şu eserlerden okudum… |
| `din-120` | Tövbenin şartları nelerdir? Kaynağını da göster. | ✘ | 0 |  |
| `din-121` | Tasavvuf nedir? Hangi eserlere göre, kaynak göster. | ✘ | 0 |   knowledge/ilim/din/02_tefsir;   knowledge/kutuphane; Bunu kütüphanemdeki şu eserlerden o |
| `din-122` | İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. | ✘ | 0 | Ay Güneş’e; 100 °C; uzaklık |
| `din-123` | Zühd nedir? Kaynak göster, hangi eserde anlatılır? | ✘ | 0 | Bunu kütüphanemdeki şu eserlerden okudum… |
| `din-124` | Sahih, hasen ve zayıf hadis arasındaki fark nedir? Kaynak gö | ✘ | 0 |  |
| `din-125` | Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kit | ✘ | 0 |  |
| `din-126` | Sebeb-i nüzûl nedir? Kaynak göster. | ✘ | 0 |  |
| `din-127` | İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak gö | ✘ | 0 |  |
| `din-128` | Hicret nedir? Kaynak göster, hangi siyer kitabında geçer? | ✘ | 0 |  |
| `din-129` | Hz. Ömer kimdir? Eser ve müellif künyesiyle kaynak göster. | ✘ | 0 |  |
| `din-130` | Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göste | ✘ | 0 | Mâtürîdî Kitâbü't-Tevhîd'i |

## Uydurma kaynak şüphesi (ayrıntı — denetleyici sezgiseldir, el ile doğrula)

- `din-04` Zekât kimlere verilir? → şüpheli: ['زكو', 'EN (klasik sözlük) — المعجم العربي الإنجليزي:'] · doğrulanan: [] · künyeler: []
- `din-09` İman esasları nelerdir? → şüpheli: ['أمن'] · doğrulanan: [] · künyeler: []
- `din-12` Cuma namazı nasıl kılınır? → şüpheli: ['صلو', 'EN (klasik sözlük) — المعجم العربي الإنجليزي:'] · doğrulanan: [] · künyeler: []
- `din-20` Vitir namazı nedir? → şüpheli: ['صلو', 'EN (klasik sözlük) — المعجم العربي الإنجليزي:'] · doğrulanan: [] · künyeler: []
- `din-23` Allah'ın sıfatları nelerdir, zâtî ve sübûtî sıfatlar ne demektir? → şüpheli: ['أله'] · doğrulanan: [] · künyeler: []
- `din-31` İman nedir, ameller imanın bir parçası mıdır? → şüpheli: ['أمن'] · doğrulanan: [] · künyeler: []
- `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek c → şüpheli: ['دعو', 'EN (klasik sözlük) — المعجم العربي الإنجليزي:'] · doğrulanan: [] · künyeler: []
- `din-43` Muhabbetullah, yani Allah sevgisi nedir? → şüpheli: ['أله'] · doğrulanan: [] · künyeler: []
- `din-48` İmam Gazâlî kimdir, İhyâu Ulûmid-Dîn eserinin önemi nedir? → şüpheli: ["İmam Gazâlî (ö. 505/1111), İhyâü Ulûmi'd-Dîn"] · doğrulanan: [] · künyeler: []
- `din-49` Mevlânâ Celâleddîn-i Rûmî kimdir, Mesnevî nedir? → şüpheli: ['Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273), Mesnevî'] · doğrulanan: [] · künyeler: []
- `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söy → şüpheli: ["Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem"] · doğrulanan: [] · künyeler: []
- `din-54` Zikir nedir, zikir çeşitleri nelerdir? → şüpheli: ['ذكر'] · doğrulanan: [] · künyeler: []
- `din-58` Namazı bozan şeyler nelerdir? → şüpheli: ['صلو', 'EN (klasik sözlük) — المعجم العربي الإنجليزي:'] · doğrulanan: [] · künyeler: []
- `din-62` Hac ile umre arasındaki fark nedir? → şüpheli: ['حجج', 'AR (klasik lügat) — لسان العرب لابن منظور:'] · doğrulanan: [] · künyeler: []
- `din-63` Kurban kimlere vâciptir? → şüpheli: ['قرأ'] · doğrulanan: [] · künyeler: []
- `din-66` Bayram namazı nasıl kılınır? → şüpheli: ['صلو', 'EN (klasik sözlük) — المعجم العربي الإنجليزي:'] · doğrulanan: [] · künyeler: []
- `din-67` Cenaze namazı nasıl kılınır? → şüpheli: ['صلو', 'EN (klasik sözlük) — المعجم العربي الإنجليزي:'] · doğrulanan: [] · künyeler: []
- `din-78` İmam Buhârî kimdir, Sahîh'i neden önemlidir? → şüpheli: ["el-Câmiu's-sahîh"] · doğrulanan: [] · künyeler: []
- `din-79` «Ameller niyetlere göredir» hadisi ne anlatır? → şüpheli: ['Sahîh-i Buhârî, Kitâbü’l-Îmân (Îman kitabı), hadis no. 1 (Buhârî’nin ilk hadisi). Uydurma cilt/kitap numarası veya başka metin söylemem.', 'Îman', 'niyet hadisi', 'إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى'] · doğrulanan: [] · künyeler: []
- `din-88` Âyetü'l-Kürsî'nin anlamı ve fazileti nedir? → şüpheli: ['أيي'] · doğrulanan: [] · künyeler: []
- `din-89` İhlâs Sûresi'nin anlamı nedir? → şüpheli: ['سور'] · doğrulanan: [] · künyeler: []
- `din-97` Hudeybiye Antlaşması nedir? → şüpheli: ['Huseyin Hudeybiye'] · doğrulanan: [] · künyeler: []
- `din-103` Kerbelâ olayı nedir? → şüpheli: ["Mekke Hicaz'dan", "Muhammed Hicaz'a"] · doğrulanan: [] · künyeler: []
- `din-106` Hıttîn Savaşı ve Selâhaddîn-i Eyyûbî'nin Kudüs'ü fethi nasıl olmuştur? → şüpheli: ['Azerbaycan Atyrau'] · doğrulanan: [] · künyeler: []
- `din-117` Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göster. → şüpheli: ['Bunu kütüphanemdeki şu eserlerden okudum…'] · doğrulanan: [] · künyeler: []
- `din-119` Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçiyor? → şüpheli: ['Bunu kütüphanemdeki şu eserlerden okudum…'] · doğrulanan: [] · künyeler: []
- `din-121` Tasavvuf nedir? Hangi eserlere göre, kaynak göster. → şüpheli: ['  knowledge/ilim/din/02_tefsir', '  knowledge/kutuphane', 'Bunu kütüphanemdeki şu eserlerden okudum…', '100 °C'] · doğrulanan: [] · künyeler: []
- `din-122` İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. → şüpheli: ['Ay Güneş’e', '100 °C', 'uzaklık'] · doğrulanan: [] · künyeler: []
- `din-123` Zühd nedir? Kaynak göster, hangi eserde anlatılır? → şüpheli: ['Bunu kütüphanemdeki şu eserlerden okudum…'] · doğrulanan: [] · künyeler: []
- `din-130` Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göster. → şüpheli: ["Mâtürîdî Kitâbü't-Tevhîd'i"] · doğrulanan: [] · künyeler: []

## Ehl-i Sünnet çizgisi soruları — el/ajan incelemesi için cevaplar

### `din-22` Eş'arî ve Mâtürîdî kimdir, itikadda nasıl bir yol izlemişlerdir?
*(doğru=evet, sağlayıcı=gemini)*

> Eş'arî ve Mâtürîdî, İslâm düşünce tarihinde Ehl-i Sünnet akaidinin kelâm alanındaki iki büyük imamıdır; her ikisi de inanç esaslarını akli ve nakli delillerle sistemleştirerek sapkın akımlara karşı savunmuşlardır.
> 
> İmam Ebû Hasan el-Eş'arî ve İmam Ebû Mansûr el-Mâtürîdî, vahyi temel almakla birlikte akla ve istidlâle önemli bir rol vermiştir. Bununla birlikte metodolojik olarak bazı noktalarda ayrılmışlardır; örneğin irade, tekvin sıfatı ve kulun fiillerinin yaratılması gibi kelâmî meselelerde kendilerine has tahliller geliştirmişler, ancak sonuç itibarıyla aynı inanç havzasının iki ana sütunu olmuşlardır.

### `din-26` İnsanın iradesi ve kesb nazariyesi nedir, Cebriyye ve Kaderiyye'den farkı nedir?
*(doğru=hayır, sağlayıcı=gemini)*

> İnsanın iradesi ve kesb nazariyesi, kulun

### `din-27` Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, **Otomatik → İngilizce** çeviri:
> 
> of the appearance (sp

### `din-29` Şefaat nedir, kimler kimlere şefaat eder?
*(doğru=evet, sağlayıcı=gemini)*

> Şefaat, dinî terminolojide günahkâr müminlerin bağışlanması veya derecelerinin yükseltilmesi için peygamberlerin, evliyaların ve Allah'ın izin verdiği salih kimselerin O'nun katında dua ve aracı olması anlamına gelir.
> 
> İslami inanca göre şefaatin asıl sahibi ve izni verecek olan yalnızca Allah'tır; Kur'an'da "De ki: Şefaatin tümü ancak Allah'a aittir" buyrulur. Kimlerin kime şefaat edeceği konusunda ise en yetkili ve kapsamlı şefaatin (şefaat-i uzmâ) Hz. Muhammed'e mahsus olduğu, bunun yanı sıra peygamberlerin, meleklerin, şehitlerin, hafızların ve Allah'ın izin verdiği salih kulların da kendi yakınlarına ve uygun görülen müminlere şefaat edebileceği bildirilmiştir.

### `din-30` Ehl-i kıble kimdir, bir Müslümanı tekfir etmek neden ağır bir meseledir?
*(doğru=hayır, sağlayıcı=gemini)*

> Ümit abi, süre yetmedi; cevap yarım kaldı. Bu bir «bilmiyorum / öğret» değil — biraz sonra tekrar dene veya soruyu kısalt.

### `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir?
*(doğru=hayır, sağlayıcı=miss_kutuphane)*

> Ümit abi, bu sorunun cevabını bulamadım. Bana öğretir misin?

### `din-34` Bid'at nedir, her yenilik bid'at midir?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, **Otomatik → İngilizce** çeviri:
> 
> what is a horse, every innovation is a bid

### `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, kök **دعو**:
> **TR (kısa):** dua, çağrı
> **EN (Lane / Kur'an kök):** The root دعو (daʿaw) primarily means to call, invite, or summon. It also encompasses praying or supplicating to God, whether for good or against someone.
> **EN (klasik sözlük) — المعجم العربي الإنجليزي:** دعو1 دَعَوْتُ and دَعَيْتُ signify the same: (Fr, K and TA in art. دعى:) the aor. of the former is أَدْعُو, (TA in that art.,) sec. Pers\. fem. sing.تَدْعِينَ and تَدْعُوِينَ and تَدٌعُيْنَ, the last with an inclination to the sound of a dammeh in the vowel of the ع [so that it is between a kesreh and a dammeh], and sec. Pers\. masc. and fem. pl. تَدْعُونَ: (S, TA:) aor. of the latter verb أَدْعِى: inf. n. دُعَآءٌ. (TA in art. دعى.) دُعَآءٌ [generally] signifies [or implies] The act of seeking
> **Müştak / formlar:** ٱدْعُ, دَعا, دُعَآءً, دُعاء, دَعْوَةَ, دَّاعِ, دَعَا, دَعْوَة, داع, يَدْعُ, يَدْعُوٓا۟, دُعُ
> **Ku

### `din-37` Mu'tezile mezhebi nedir, temel görüşleri nelerdir?
*(doğru=evet, sağlayıcı=gemini)*

> Mu'tezile mezhebi, İslam düşünce tarihinde aklı ve akıl yürütmeyi dinî metinlerin önüne koyan, adalet ve tevhit gibi temel ilkeler etrafında şekillenmiş erken

### `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söylenir?
*(doğru=evet, sağlayıcı=None)*

> Fusûsu'l-Hikem: İbnü'l-Arabî'nin özlü hikmet eseri. Şerhler `serh_ve_aciklama/` altına konur.
> 
> Kaynak: Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem

## Geçmeyen sorular

- `din-01` Abdesti bozan şeyler nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-02` Namazın şartları nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-03` İslam'ın şartları nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-04` Zekât kimlere verilir? → kap=0.0 · None · hits=0
- `din-05` Ramazan orucunu bozan şeyler nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-07` Haccın farzları nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-09` İman esasları nelerdir? → kap=0.0 · None · hits=0
- `din-11` Dört Sünnî fıkıh mezhebi hangileridir? → BULAMADIM · miss_kutuphane · hits=0
- `din-12` Cuma namazı nasıl kılınır? → kap=0.0 · None · hits=0
- `din-15` Gusül abdesti nasıl alınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-19` Fıkıhta farz ile vâcip arasındaki fark nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-20` Vitir namazı nedir? → kap=0.0 · None · hits=0
- `din-21` Ehl-i Sünnet ve'l-Cemaat kimlere denir? → BULAMADIM · miss_kutuphane · hits=0
- `din-23` Allah'ın sıfatları nelerdir, zâtî ve sübûtî sıfatlar ne demektir? → kap=0.0 · None · hits=0
- `din-24` Allah'ın selbî sıfatları hangileridir? → BULAMADIM · miss_kutuphane · hits=0
- `din-26` İnsanın iradesi ve kesb nazariyesi nedir, Cebriyye ve Kaderiyye'den farkı nedir? → kap=0.333 · gemini · hits=0
- `din-27` Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür? → kap=0.0 · None · hits=0
- `din-30` Ehl-i kıble kimdir, bir Müslümanı tekfir etmek neden ağır bir meseledir? → kap=0.0 · gemini · hits=0
- `din-31` İman nedir, ameller imanın bir parçası mıdır? → kap=0.0 · None · hits=0
- `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-34` Bid'at nedir, her yenilik bid'at midir? → kap=0.0 · None · hits=0
- `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir? → kap=0.333 · None · hits=0
- `din-38` Hâricîler kimlerdir, hangi görüşleri yüzünden Ehl-i Sünnet'ten ayrılmışlardır? → BULAMADIM · miss_kutuphane · hits=0
- `din-40` İhsan nedir, Cibrîl hadisinde nasıl tarif edilmiştir? → BULAMADIM · miss_kutuphane · hits=0
- `din-43` Muhabbetullah, yani Allah sevgisi nedir? → kap=0.333 · None · hits=0
- `din-45` Tarikat edebi nedir, mürit ile mürşid arasındaki edep nasıl olmalıdır? → kap=0.333 · gemini · hits=0
- `din-51` Tasavvufta makam ile hâl arasındaki fark nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-54` Zikir nedir, zikir çeşitleri nelerdir? → kap=0.333 · None · hits=0
- `din-56` Nefsin mertebeleri nelerdir? → kap=0.0 · gemini · hits=0
- `din-58` Namazı bozan şeyler nelerdir? → kap=0.0 · None · hits=0
- `din-59` Beş vakit namazın vakitleri nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-60` Ramazan orucunu tutmayabilecek kimseler kimlerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-61` Zekâtın nisabı ve oranı nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-62` Hac ile umre arasındaki fark nedir? → kap=0.333 · None · hits=0
- `din-63` Kurban kimlere vâciptir? → kap=0.0 · None · hits=0
- `din-64` Hanefî ve Şâfiî mezhebi abdestte hangi konularda ayrılır? → kap=0.0 · None · hits=0
- `din-65` Teravih namazı kaç rekâttır, nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-66` Bayram namazı nasıl kılınır? → kap=0.333 · None · hits=0
- `din-68` Faiz (ribâ) nedir, neden haramdır? → BULAMADIM · miss_kutuphane · hits=0
- `din-70` Talak (boşanma) çeşitleri nelerdir? → kap=0.333 · hizli · hits=0
- `din-73` Cünüplük halinde neler yasaktır? → kap=0.0 · hizli · hits=0
- `din-76` Hadiste isnad (senet) nedir, neden önemlidir? → BULAMADIM · miss_kutuphane · hits=0
- `din-77` Mevzû (uydurma) hadis nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-80` Sünnetin İslâm'daki yeri nedir, neden delildir? → BULAMADIM · miss_kutuphane · hits=0
- `din-82` Hadis-i kudsî nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-83` Erbaîn (kırk hadis) geleneği nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-84` Tefsirde rivayet ve dirayet usulü nedir? → kap=0.333 · None · hits=0
- `din-88` Âyetü'l-Kürsî'nin anlamı ve fazileti nedir? → kap=0.333 · None · hits=0
- `din-89` İhlâs Sûresi'nin anlamı nedir? → kap=0.0 · None · hits=0
- `din-90` Kur'ân-ı Kerîm kaç cüzden ve yaklaşık kaç âyetten oluşur? → kap=0.5 · None · hits=0
- `din-91` Kur'ân'ın ilk inen âyetleri hangileridir, nerede inmiştir? → kap=0.333 · None · hits=0
- `din-93` Hz. Muhammed kaç yaşında peygamber olmuştur, ilk vahiy nasıl gelmiştir? → kap=0.333 · None · hits=0
- `din-94` İslâm'ı ilk kabul edenler kimlerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-95` Bedir Savaşı ne zaman olmuştur ve sonucu nedir? → kap=0.0 · hizli · hits=0
- `din-96` Uhud Savaşı'nda ne olmuştur? → kap=0.0 · hizli · hits=0
- `din-97` Hudeybiye Antlaşması nedir? → kap=0.333 · hizli · hits=0
- `din-98` Mekke'nin fethi nasıl olmuştur? → kap=0.333 · hizli · hits=0
- `din-99` Hz. Peygamber ne zaman ve nerede vefat etmiştir? → BULAMADIM · miss_kutuphane · hits=0
- `din-100` İsrâ ve Mi'râc mucizesi nedir? → kap=0.333 · hizli · hits=0
- `din-102` Aşere-i Mübeşşere kimlerdir? → kap=0.0 · hizli · hits=0
- `din-103` Kerbelâ olayı nedir? → kap=0.333 · hizli · hits=0
- `din-104` Emevî devleti ne zaman kurulmuştur, başkenti neresidir? → kap=0.0 · hizli · hits=0
- `din-105` Endülüs'ün fethi nasıl gerçekleşmiştir? → kap=0.333 · hizli · hits=0
- `din-107` Hilâfet Osmanlılara ne zaman ve nasıl geçmiştir? → kap=0.333 · hizli · hits=0
- `din-108` Hz. Âdem'in yaratılışı ve cennetten çıkarılışı nasıldır? → BULAMADIM · miss_kutuphane · hits=0
- `din-109` Hz. Nûh ve tûfan kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-110` Hz. İbrâhîm ve Nemrut kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-111` Hz. Yûsuf kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-112` Hz. Mûsâ ile Firavun kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-113` Hz. Îsâ'nın doğumu nasıl olmuştur? → BULAMADIM · miss_kutuphane · hits=0
- `din-114` Ashâb-ı Kehf kıssası nedir? → kap=0.333 · hizli · hits=0
- `din-115` Hz. Yûnus'un balığın karnında kalması kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-116` Abdesti bozan şeyler nelerdir? Kaynak göster. → BULAMADIM · miss_kutuphane · hits=0
- `din-117` Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göster. → kap=0.0 · kutuphane_extractive · hits=0
- `din-118` Kader nedir? Hangi eserlere dayanarak anlatıyorsun, kaynak ver. → kap=0.5 · hizli · hits=0
- `din-119` Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçiyor? → kap=0.0 · kutuphane_extractive · hits=0
- `din-120` Tövbenin şartları nelerdir? Kaynağını da göster. → BULAMADIM · hizli · hits=0
- `din-121` Tasavvuf nedir? Hangi eserlere göre, kaynak göster. → kap=0.0 · kutuphane_extractive · hits=0
- `din-122` İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. → kap=0.0 · kutuphane_extractive · hits=0
- `din-123` Zühd nedir? Kaynak göster, hangi eserde anlatılır? → kap=0.0 · kutuphane_extractive · hits=0
- `din-125` Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kitabında geçer, kaynak ver. → kap=0.333 · None · hits=0
- `din-127` İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak göster. → kap=0.0 · hizli · hits=0
- `din-129` Hz. Ömer kimdir? Eser ve müellif künyesiyle kaynak göster. → BULAMADIM · miss_kutuphane · hits=0