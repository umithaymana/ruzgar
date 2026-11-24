# Din raporu — din_k3_tdkfix (2026-11-24)

Yalnız **din rafı** (web kapalı). Koşucu: `scripts/altin_set_kos.py din-rapor`; ölçütler: `scripts/din_olcut.py`.

| Ölçüt | din_baslangic | din_k3_tdkfix |
|---|---:|---:|
| Soru sayısı | 130 | 130 |
| Doğru cevap % | %36.2 | %57.7 |
| «Bulamadım» % | %27.7 | %31.5 |
| Ort. kapsama | 0.392 | 0.573 |
| (a) «Kaynak göster» varyantlarında künye gelen % | %0.0 | %0.0 |
| (a) Tüm din cevaplarında doğrulanmış künye % | %0.0 | %0.0 |
| (b) Çoklu eser (≥2 farklı eser anışı) % | %0.0 | %0.0 |
| (b) Çoklu eser — yalnız «kaynak göster» varyantlarında % | %0.0 | %0.0 |
| (c) Uydurma kaynak şüphesi — soru sayısı | 11 | 19 |
| (c) Uydurma kaynak şüphesi — atıf sayısı | 16 | 23 |
| (d) Sadelik ajan puanı (1–5) | — | — |
| Medyan sn | 4.13 | 8.54 |
| P90 sn | 18.95 | 31.49 |

Sağlayıcılar: {'gemini': 55, 'miss_kutuphane': 39, 'None': 36}

## Alt-raf bazında

| Alt-raf | N | Doğru % | Bulamadım % |
|---|---:|---:|---:|
| akaid | 21 | 57.1 | 28.6 |
| fikih | 18 | 33.3 | 66.7 |
| hadis | 11 | 54.5 | 45.5 |
| kissa | 8 | 12.5 | 87.5 |
| siyer | 13 | 69.2 | 23.1 |
| tarih | 4 | 75.0 | 0.0 |
| tasavvuf | 24 | 83.3 | 16.7 |
| tefsir | 11 | 36.4 | 0.0 |
| temel | 20 | 70.0 | 20.0 |

## «Kaynak göster» varyantları

| id | Soru | Künye? | Eser sayısı | Şüpheli atıf |
|---|---|:-:|---:|---|
| `din-116` | Abdesti bozan şeyler nelerdir? Kaynak göster. | ✘ | 0 |  |
| `din-117` | Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göste | ✘ | 0 | Fıkıh ve Tefsir Külliyatı (Şâmile ve Açık İlim Arşivi) |
| `din-118` | Kader nedir? Hangi eserlere dayanarak anlatıyorsun, kaynak v | ✘ | 0 | Klasik akaid/kelâm özeti (Mâtürîdî *Kitâbü't-Tevhîd*, Eş'arî *el-Luma'*/Makâlât literatürü |
| `din-119` | Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçi | ✘ | 0 | sünnet ve cemaat |
| `din-120` | Tövbenin şartları nelerdir? Kaynağını da göster. | ✘ | 0 | tevbû ilellâhi tevbeten nasûhâ |
| `din-121` | Tasavvuf nedir? Hangi eserlere göre, kaynak göster. | ✘ | 0 |  |
| `din-122` | İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. | ✘ | 0 | klasik hadis usûlü/tarihçe özeti (İbnü's-Salâh Mukaddime, İbn Hacer Nuhbe, Kutüb-i Sitte l |
| `din-123` | Zühd nedir? Kaynak göster, hangi eserde anlatılır? | ✘ | 0 |  |
| `din-124` | Sahih, hasen ve zayıf hadis arasındaki fark nedir? Kaynak gö | ✘ | 0 |  |
| `din-125` | Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kit | ✘ | 0 |  |
| `din-126` | Sebeb-i nüzûl nedir? Kaynak göster. | ✘ | 0 |  |
| `din-127` | İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak gö | ✘ | 0 |  |
| `din-128` | Hicret nedir? Kaynak göster, hangi siyer kitabında geçer? | ✘ | 0 |  |
| `din-129` | Hz. Ömer kimdir? Eser ve müellif künyesiyle kaynak göster. | ✘ | 0 |  |
| `din-130` | Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göste | ✘ | 0 | Mâtürîdî Kitâbü't-Tevhîd'i |

## Uydurma kaynak şüphesi (ayrıntı — denetleyici sezgiseldir, el ile doğrula)

- `din-03` İslam'ın şartları nelerdir? → şüpheli: ["İbnü Teymiyye'nin İmanı", 'İbnü Teymiyye İmanı'] · doğrulanan: [] · künyeler: []
- `din-09` İman esasları nelerdir? → şüpheli: ['Örneğin'] · doğrulanan: [] · künyeler: []
- `din-37` Mu'tezile mezhebi nedir, temel görüşleri nelerdir? → şüpheli: ['Tevhid:'] · doğrulanan: [] · künyeler: []
- `din-48` İmam Gazâlî kimdir, İhyâu Ulûmid-Dîn eserinin önemi nedir? → şüpheli: ["İmam Gazâlî (ö. 505/1111), İhyâü Ulûmi'd-Dîn"] · doğrulanan: [] · künyeler: []
- `din-49` Mevlânâ Celâleddîn-i Rûmî kimdir, Mesnevî nedir? → şüpheli: ['Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273), Mesnevî'] · doğrulanan: [] · künyeler: []
- `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söy → şüpheli: ["Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem"] · doğrulanan: [] · künyeler: []
- `din-78` İmam Buhârî kimdir, Sahîh'i neden önemlidir? → şüpheli: ["el-Câmiu's-sahîh"] · doğrulanan: [] · künyeler: []
- `din-79` «Ameller niyetlere göredir» hadisi ne anlatır? → şüpheli: ['Sahîh-i Buhârî, Kitâbü’l-Îmân (Îman kitabı), hadis no. 1 (Buhârî’nin ilk hadisi). Uydurma cilt/kitap numarası veya başka metin söylemem.', 'Îman', 'niyet hadisi'] · doğrulanan: [] · künyeler: []
- `din-97` Hudeybiye Antlaşması nedir? → şüpheli: ['Kureyş İslam'] · doğrulanan: [] · künyeler: []
- `din-98` Mekke'nin fethi nasıl olmuştur? → şüpheli: ['Hudeybiye Antlaşması Kureyş'] · doğrulanan: [] · künyeler: []
- `din-100` İsrâ ve Mi'râc mucizesi nedir? → şüpheli: ['Muhammed Mekke’deki Mescid-i Haram’dan Kudüs’teki', 'Kur’an-ı Kerim İsrâ'] · doğrulanan: [] · künyeler: []
- `din-107` Hilâfet Osmanlılara ne zaman ve nasıl geçmiştir? → şüpheli: ['Yavuz Sultan Selim Mercidabık'] · doğrulanan: [] · künyeler: []
- `din-114` Ashâb-ı Kehf kıssası nedir? → şüpheli: ["Kur'an-ı Kerim Kehf Suresi'nde"] · doğrulanan: [] · künyeler: []
- `din-117` Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göster. → şüpheli: ['Fıkıh ve Tefsir Külliyatı (Şâmile ve Açık İlim Arşivi)'] · doğrulanan: [] · künyeler: []
- `din-118` Kader nedir? Hangi eserlere dayanarak anlatıyorsun, kaynak ver. → şüpheli: ["Klasik akaid/kelâm özeti (Mâtürîdî *Kitâbü't-Tevhîd*, Eş'arî *el-Luma'*/Makâlât literatürü)."] · doğrulanan: [] · künyeler: []
- `din-119` Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçiyor? → şüpheli: ['sünnet ve cemaat'] · doğrulanan: [] · künyeler: []
- `din-120` Tövbenin şartları nelerdir? Kaynağını da göster. → şüpheli: ['tevbû ilellâhi tevbeten nasûhâ'] · doğrulanan: [] · künyeler: []
- `din-122` İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. → şüpheli: ["klasik hadis usûlü/tarihçe özeti (İbnü's-Salâh Mukaddime, İbn Hacer Nuhbe, Kutüb-i Sitte literatürü)."] · doğrulanan: [] · künyeler: []
- `din-130` Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göster. → şüpheli: ["Mâtürîdî Kitâbü't-Tevhîd'i"] · doğrulanan: [] · künyeler: []

## Ehl-i Sünnet çizgisi soruları — el/ajan incelemesi için cevaplar

### `din-22` Eş'arî ve Mâtürîdî kimdir, itikadda nasıl bir yol izlemişlerdir?
*(doğru=evet, sağlayıcı=gemini)*

> Ebu'l-Hasan el-Eş'arî ve İmam Mâtürîdî, Ehl-i sünnet itikadının temelini atan, inanç esaslarını akli ve nakli delillerle sistematize eden iki büyük kelâm âlimidir.
> 
> İkisi de iman esaslarını Kur'an ve sünnet çizgisinde savunurken aklı ve nakli telif etmede benzer bir metodoloji izlemiş, ancak bazı teferruat meselelerinde farklı görüşler benimsemiştir. Eş'arî ve Mâtürîdî ekolleri, Yunan felsefesinden ve sapkın akımlardan gelen şüpheciliğe karşı İslam inancını savunmak için kelâm ilmini geliştirmiş; sıfatlar, kader, irade ve kulun fiilleri gibi konularda İslam dünyasında günümüze kadar gelen iki ana kelâm mercii olmuştur.

### `din-26` İnsanın iradesi ve kesb nazariyesi nedir, Cebriyye ve Kaderiyye'den farkı nedir?
*(doğru=evet, sağlayıcı=gemini)*

> İnsanın iradesi, kulun kendi hür iradesiyle bir fiili seçebilme gücüdür; kesb nazariyesi ise Ehl-i sünnet kelâmında kulun iradesiyle yöneldiği fiili Allah'ın yaratması ve kulun da bu fiili kesb etmesi (sahip çıkması ve sorumluluğunu üstlenmesi) esasına dayanır.
> 
> Cebriyye ve Kaderiyye mezhepleri bu konuda iki zıt uçta yer alır. Cebriyye, insanın hiçbir iradesi ve seçme hakkı olmadığını, kulun rüzgar önündeki yaprak gibi mecburî olarak davrandığını savunur; böylece insanın iradesini tamamen reddeder. Kaderiyye ise kulun kendi fiillerinin mutlak yaratıcısı olduğunu, Allah'ın takdirinin bu alana karışmadığını iddia ederek kulun kudretini öne çıkarır. Ehl-i sünnetin kesb anlayışı ise bu iki aşırı uç arasında bir denge kurarak kulun cüz'î iradesini ve mesuliyetini kabul ederken, asıl yaratmanın Allah'a ait olduğunu vurgular.

### `din-27` Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, **Otomatik → İngilizce** çeviri:
> 
> of being seen (sp

### `din-29` Şefaat nedir, kimler kimlere şefaat eder?
*(doğru=evet, sağlayıcı=gemini)*

> Şefaat, dinî bir terim olarak günahkâr müminlerin bağışlanması veya derecelerinin yükseltilmesi için peygamberlerin, evliyaların ve Allah'ın izin verdiği salih kimselerin katında aracı olup dua etmesi anlamına gelir.
> 
> İslami inanca göre şefaat yetkisi tamamen Allah'a aittir ve O'nun izni olmadan hiç kimse başkasına şefaat edemez. Bu izni alanlar arasında başta Hz. Muhammed olmak üzere diğer peygamberler, şehitler, alimler, hafızlar ve Allah katında değerli kılınmış salih kullar yer alır; bu kimseler yine Allah'ın rıza gösterdiği mümin kardeşleri lehine kıyamet gününde şefaatçi olabileceklerdir.

### `din-30` Ehl-i kıble kimdir, bir Müslümanı tekfir etmek neden ağır bir meseledir?
*(doğru=evet, sağlayıcı=gemini)*

> Ehl-i kıble, kıble olarak kabul edilen Kaçeye yönelen, yani kelime-i şehadet getirerek İslam ümmetine dahil olduğunu, iman esaslarını benimsediğini ikrar eden her Müslümana denir. Bir kimsenin kalbindeki imanı ve niyetini yalnızca Allah bilebileceği için, dışarıdan Müslüman olduğunu söyleyen ve kıbleye yönelen birine "kâfir" hükmünü vermek son derece tehlikelidir ve fıkıh ile kelam ilminde çok ağır bir mesuliyet taşır.
> 
> Bunun sebebi, tekfir etmenin (dinden çıkmakla suçlamanın) iki ucu keskin bir kılıç olmasıdır. Hz. Muhammed’in hadislerinde, bir Müslümanın kardeşine kâfir demesi durumunda, bu suçlamanın hak etmeyen kişiye gitmemesi halinde söyleyenin kendisine döneceği açıkça bildirilmiştir. Bu yüzden İslam âlimleri, bir kişinin söz veya davranışında kâfrliğini gerektirecek çok açık ve kesin bir delil (inkâr) bulunmadığı sürece, zahirdeki imanına bakarak tekfirden kaçınmışlar, hata yapma

### `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir?
*(doğru=hayır, sağlayıcı=miss_kutuphane)*

> Ümit abi, bu sorunun cevabını bulamadım. Bana öğretir misin?

### `din-34` Bid'at nedir, her yenilik bid'at midir?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, **Otomatik → İngilizce** çeviri:
> 
> What is a horse, every innovation bid

### `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir?
*(doğru=hayır, sağlayıcı=miss_kutuphane)*

> Ümit abi, bu sorunun cevabını bulamadım. Bana öğretir misin?

### `din-37` Mu'tezile mezhebi nedir, temel görüşleri nelerdir?
*(doğru=evet, sağlayıcı=gemini)*

> Mu'tezile, İslam düşünce tarihinde akıl ve iradeyi merkeze alan, kelam ilminin ilk önemli ekollerinden biridir. Hasan-ı Basri'nin ders halkasından ayrılan Vâsıl bin Atâ tarafından kurulmuş; İslam coğrafyasında özellikle Abbasi döneminde akılcı ve felsefi tartışmalarıyla öne çıkmıştır.
> 
> Temel görüşleri beş ana ilke (Usûl-i Hamse) üzerine kuruludur:
> 1. **Tevhid:** Allah'ın birliğini savunurken, O'nun sıfât-ı zâtiyyesini tefsir eder ve Kur'an'ın mahluk (yaratılmış) olduğunu öne sürerler.
> 2. **Adl:** Allah'ın mutlak adalet sahibi olduğunu; bu nedenle kötülüğü yaratmayacağını, insanlara irade vererek fiillerinde özgür kıldığını savunurlar.
> 3. **Va'd ve Va'id:** Allah'ın iyilik yapanlara mükafat (va'd), kötülük yapanlara ceza (va'id) vereceğinin kesin olduğunu belirtirler.
> 4. **El-Menziletü beyne'l-menziletenk:** Büyük günah işleyen bir kişinin mümin ile kafir arasında, arafta bir konumda oldu

### `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söylenir?
*(doğru=evet, sağlayıcı=None)*

> Fusûsu'l-Hikem: İbnü'l-Arabî'nin özlü hikmet eseri. Şerhler `serh_ve_aciklama/` altına konur.
> 
> Kaynak: Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem

## Geçmeyen sorular

- `din-02` Namazın şartları nelerdir? → kap=0.5 · gemini · hits=0
- `din-11` Dört Sünnî fıkıh mezhebi hangileridir? → kap=0.0 · None · hits=0
- `din-12` Cuma namazı nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-15` Gusül abdesti nasıl alınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-19` Fıkıhta farz ile vâcip arasındaki fark nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-20` Vitir namazı nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-21` Ehl-i Sünnet ve'l-Cemaat kimlere denir? → BULAMADIM · miss_kutuphane · hits=0
- `din-23` Allah'ın sıfatları nelerdir, zâtî ve sübûtî sıfatlar ne demektir? → kap=0.0 · None · hits=0
- `din-24` Allah'ın selbî sıfatları hangileridir? → BULAMADIM · miss_kutuphane · hits=0
- `din-27` Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür? → kap=0.0 · None · hits=0
- `din-31` İman nedir, ameller imanın bir parçası mıdır? → BULAMADIM · miss_kutuphane · hits=0
- `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-34` Bid'at nedir, her yenilik bid'at midir? → kap=0.0 · None · hits=0
- `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir? → BULAMADIM · miss_kutuphane · hits=0
- `din-38` Hâricîler kimlerdir, hangi görüşleri yüzünden Ehl-i Sünnet'ten ayrılmışlardır? → BULAMADIM · miss_kutuphane · hits=0
- `din-40` İhsan nedir, Cibrîl hadisinde nasıl tarif edilmiştir? → BULAMADIM · miss_kutuphane · hits=0
- `din-43` Muhabbetullah, yani Allah sevgisi nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-51` Tasavvufta makam ile hâl arasındaki fark nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-58` Namazı bozan şeyler nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-59` Beş vakit namazın vakitleri nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-60` Ramazan orucunu tutmayabilecek kimseler kimlerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-61` Zekâtın nisabı ve oranı nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-62` Hac ile umre arasındaki fark nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-63` Kurban kimlere vâciptir? → BULAMADIM · miss_kutuphane · hits=0
- `din-64` Hanefî ve Şâfiî mezhebi abdestte hangi konularda ayrılır? → BULAMADIM · None · hits=0
- `din-65` Teravih namazı kaç rekâttır, nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-66` Bayram namazı nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-67` Cenaze namazı nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-68` Faiz (ribâ) nedir, neden haramdır? → BULAMADIM · miss_kutuphane · hits=0
- `din-76` Hadiste isnad (senet) nedir, neden önemlidir? → BULAMADIM · miss_kutuphane · hits=0
- `din-77` Mevzû (uydurma) hadis nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-80` Sünnetin İslâm'daki yeri nedir, neden delildir? → BULAMADIM · miss_kutuphane · hits=0
- `din-82` Hadis-i kudsî nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-83` Erbaîn (kırk hadis) geleneği nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-84` Tefsirde rivayet ve dirayet usulü nedir? → kap=0.333 · None · hits=0
- `din-88` Âyetü'l-Kürsî'nin anlamı ve fazileti nedir? → kap=0.0 · None · hits=0
- `din-89` İhlâs Sûresi'nin anlamı nedir? → kap=0.0 · None · hits=0
- `din-90` Kur'ân-ı Kerîm kaç cüzden ve yaklaşık kaç âyetten oluşur? → kap=0.5 · None · hits=0
- `din-91` Kur'ân'ın ilk inen âyetleri hangileridir, nerede inmiştir? → kap=0.0 · None · hits=0
- `din-92` Kur'ân-ı Kerîm nasıl bir mushaf hâline getirilmiştir (cem' tarihi)? → kap=0.333 · None · hits=0
- `din-93` Hz. Muhammed kaç yaşında peygamber olmuştur, ilk vahiy nasıl gelmiştir? → kap=0.333 · None · hits=0
- `din-94` İslâm'ı ilk kabul edenler kimlerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-99` Hz. Peygamber ne zaman ve nerede vefat etmiştir? → BULAMADIM · miss_kutuphane · hits=0
- `din-106` Hıttîn Savaşı ve Selâhaddîn-i Eyyûbî'nin Kudüs'ü fethi nasıl olmuştur? → kap=0.0 · None · hits=0
- `din-108` Hz. Âdem'in yaratılışı ve cennetten çıkarılışı nasıldır? → BULAMADIM · miss_kutuphane · hits=0
- `din-109` Hz. Nûh ve tûfan kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-110` Hz. İbrâhîm ve Nemrut kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-111` Hz. Yûsuf kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-112` Hz. Mûsâ ile Firavun kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-113` Hz. Îsâ'nın doğumu nasıl olmuştur? → BULAMADIM · miss_kutuphane · hits=0
- `din-115` Hz. Yûnus'un balığın karnında kalması kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-116` Abdesti bozan şeyler nelerdir? Kaynak göster. → BULAMADIM · miss_kutuphane · hits=0
- `din-121` Tasavvuf nedir? Hangi eserlere göre, kaynak göster. → BULAMADIM · gemini · hits=0
- `din-125` Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kitabında geçer, kaynak ver. → kap=0.333 · None · hits=0
- `din-129` Hz. Ömer kimdir? Eser ve müellif künyesiyle kaynak göster. → BULAMADIM · miss_kutuphane · hits=0