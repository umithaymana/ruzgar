# Din raporu — din_k3_onarim (2026-11-24)

Yalnız **din rafı** (web kapalı). Koşucu: `scripts/altin_set_kos.py din-rapor`; ölçütler: `scripts/din_olcut.py`.

| Ölçüt | din_baslangic | din_k3_onarim |
|---|---:|---:|
| Soru sayısı | 130 | 130 |
| Doğru cevap % | %36.2 | %33.1 |
| «Bulamadım» % | %27.7 | %35.4 |
| Ort. kapsama | 0.392 | 0.342 |
| (a) «Kaynak göster» varyantlarında künye gelen % | %0.0 | %0.0 |
| (a) Tüm din cevaplarında doğrulanmış künye % | %0.0 | %0.0 |
| (b) Çoklu eser (≥2 farklı eser anışı) % | %0.0 | %0.0 |
| (b) Çoklu eser — yalnız «kaynak göster» varyantlarında % | %0.0 | %0.0 |
| (c) Uydurma kaynak şüphesi — soru sayısı | 11 | 10 |
| (c) Uydurma kaynak şüphesi — atıf sayısı | 16 | 23 |
| (d) Sadelik ajan puanı (1–5) | — | — |
| Medyan sn | 4.13 | 6.6 |
| P90 sn | 18.95 | 41.39 |

Sağlayıcılar: {'hizli': 46, 'miss_kutuphane': 43, 'None': 39, 'gemini': 2}

## Alt-raf bazında

| Alt-raf | N | Doğru % | Bulamadım % |
|---|---:|---:|---:|
| akaid | 21 | 28.6 | 19.0 |
| fikih | 18 | 16.7 | 61.1 |
| hadis | 11 | 54.5 | 45.5 |
| kissa | 8 | 12.5 | 87.5 |
| siyer | 13 | 15.4 | 23.1 |
| tarih | 4 | 0.0 | 50.0 |
| tasavvuf | 24 | 41.7 | 16.7 |
| tefsir | 11 | 45.5 | 0.0 |
| temel | 20 | 50.0 | 50.0 |

## «Kaynak göster» varyantları

| id | Soru | Künye? | Eser sayısı | Şüpheli atıf |
|---|---|:-:|---:|---|
| `din-116` | Abdesti bozan şeyler nelerdir? Kaynak göster. | ✘ | 0 |  |
| `din-117` | Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göste | ✘ | 0 | Olur Ümit abi, ...; kaynak istedi; yalnızca bağlamda varsa; onu kullan; uydurma; … eserine |
| `din-118` | Kader nedir? Hangi eserlere dayanarak anlatıyorsun, kaynak v | ✘ | 0 |  |
| `din-119` | Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçi | ✘ | 0 |   Arapça eser adı — müellif |
| `din-120` | Tövbenin şartları nelerdir? Kaynağını da göster. | ✘ | 0 | sade, doğal, kısa; uydurma; kesin bilmiyorum |
| `din-121` | Tasavvuf nedir? Hangi eserlere göre, kaynak göster. | ✘ | 0 |  |
| `din-122` | İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. | ✘ | 0 |  |
| `din-123` | Zühd nedir? Kaynak göster, hangi eserde anlatılır? | ✘ | 0 |  |
| `din-124` | Sahih, hasen ve zayıf hadis arasındaki fark nedir? Kaynak gö | ✘ | 0 |  |
| `din-125` | Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kit | ✘ | 0 |  |
| `din-126` | Sebeb-i nüzûl nedir? Kaynak göster. | ✘ | 0 |  |
| `din-127` | İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak gö | ✘ | 0 | 08_siyer / tarih–tabakât hattı. Fetva değildir. |
| `din-128` | Hicret nedir? Kaynak göster, hangi siyer kitabında geçer? | ✘ | 0 |  |
| `din-129` | Hz. Ömer kimdir? Eser ve müellif künyesiyle kaynak göster. | ✘ | 0 |  |
| `din-130` | Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göste | ✘ | 0 | Mâtürîdî Kitâbü't-Tevhîd'i |

## Uydurma kaynak şüphesi (ayrıntı — denetleyici sezgiseldir, el ile doğrula)

- `din-48` İmam Gazâlî kimdir, İhyâu Ulûmid-Dîn eserinin önemi nedir? → şüpheli: ["İmam Gazâlî (ö. 505/1111), İhyâü Ulûmi'd-Dîn"] · doğrulanan: [] · künyeler: []
- `din-49` Mevlânâ Celâleddîn-i Rûmî kimdir, Mesnevî nedir? → şüpheli: ['Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273), Mesnevî'] · doğrulanan: [] · künyeler: []
- `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söy → şüpheli: ["Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem"] · doğrulanan: [] · künyeler: []
- `din-78` İmam Buhârî kimdir, Sahîh'i neden önemlidir? → şüpheli: ["el-Câmiu's-sahîh"] · doğrulanan: [] · künyeler: []
- `din-79` «Ameller niyetlere göredir» hadisi ne anlatır? → şüpheli: ['Sahîh-i Buhârî, Kitâbü’l-Îmân (Îman kitabı), hadis no. 1 (Buhârî’nin ilk hadisi). Uydurma cilt/kitap numarası veya başka metin söylemem.', 'Îman', 'niyet hadisi'] · doğrulanan: [] · künyeler: []
- `din-117` Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göster. → şüpheli: ['Olur Ümit abi, ...', 'kaynak istedi', 'yalnızca bağlamda varsa', 'onu kullan', 'uydurma', '… eserine göre …, … eserinde ise …', 'ayrı eserlere', '[K#] Arapça eser adı — müellif', 'Sabit karşılama', 'Bağlam'] · doğrulanan: [] · künyeler: []
- `din-119` Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçiyor? → şüpheli: ['  Arapça eser adı — müellif'] · doğrulanan: [] · künyeler: []
- `din-120` Tövbenin şartları nelerdir? Kaynağını da göster. → şüpheli: ['sade, doğal, kısa', 'uydurma', 'kesin bilmiyorum'] · doğrulanan: [] · künyeler: []
- `din-127` İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak göster. → şüpheli: ['08_siyer / tarih–tabakât hattı. Fetva değildir.'] · doğrulanan: [] · künyeler: []
- `din-130` Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göster. → şüpheli: ["Mâtürîdî Kitâbü't-Tevhîd'i"] · doğrulanan: [] · künyeler: []

## Ehl-i Sünnet çizgisi soruları — el/ajan incelemesi için cevaplar

### `din-22` Eş'arî ve Mâtürîdî kimdir, itikadda nasıl bir yol izlemişlerdir?
*(doğru=evet, sağlayıcı=hizli)*

> Eş'arî ve Mâtürîdî kimdir?

### `din-26` İnsanın iradesi ve kesb nazariyesi nedir, Cebriyye ve Kaderiyye'den farkı nedir?
*(doğru=hayır, sağlayıcı=hizli)*

> İlgili Bilgilendirme

### `din-27` Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür?
*(doğru=evet, sağlayıcı=hizli)*

> Âhirette Allah'ın görülmesi (ru'yetullah) mümkün değildir.

### `din-29` Şefaat nedir, kimler kimlere şefaat eder?
*(doğru=hayır, sağlayıcı=hizli)*

> Bu turda, **şefaat nedir** sorusu ile başlıyoruz. Şefaat, Islamic terimdir ve İslam'da birer manevi niyetin ve bir insan tarafından bir başka insana veya gruba helpa olmasıdır.

### `din-30` Ehl-i kıble kimdir, bir Müslümanı tekfir etmek neden ağır bir meseledir?
*(doğru=hayır, sağlayıcı=hizli)*

> Ehl-i kıble, İslam dini withinindeki kavram. İslamda ehl-i kıble, Allah'ın ismini söyleyemediği, Allah'ın ismini anamayan, Allah'ın ismini duyuramayan, Allah'ın ismini duymayan, Allah'ın ismini duymakla yetmeyen, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın ismini duymayan, Allah'ın is

### `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir?
*(doğru=hayır, sağlayıcı=None)*

> 

### `din-34` Bid'at nedir, her yenilik bid'at midir?
*(doğru=hayır, sağlayıcı=hizli)*

> Ümit abi, yanıt üretilirken kesinti oldu («Bid'at nedir, her yenilik bid'at midir?») — lütfen bir kez daha yaz veya DURDUR sonrası tekrar dene. (Ollama/Gemini bağlantısı veya süre sınırı olabilir.)

### `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir?
*(doğru=hayır, sağlayıcı=miss_kutuphane)*

> Ümit abi, süre yetmedi; cevap yarım kaldı. Bu bir «bilmiyorum / öğret» değil — biraz sonra tekrar dene veya soruyu kısalt.

### `din-37` Mu'tezile mezhebi nedir, temel görüşleri nelerdir?
*(doğru=hayır, sağlayıcı=hizli)*

> Mu'tezile mezhebi, İslam hukukunda ve teolojisinde önemli bir rol oynayan bir mezheptir. Bu mezhep, Arapça ve Farsça literatürde çok fazla yer alan ilmi-ahkamî ve felsefi konuları ele alan bir geleneğe sahiptir.
> 
> Mu'tezile'nin temel görüşleri arasında以下 konular yer almaktadır:
> 
> 1. **Ilm-i Akid**: Mu'teziler, ilm-i akid (ilahiyat) ve ilm-i faris (felsefe) alanlarında önemli contributions yapmıştır. Bu alanlarda, ilahiyatın ve felsefenin İslam dininin temel konularını ele alphabetik ve sistemli bir şekilde incelemeyi amaçlarlar. Bu konularda, ilahiyat ve felsefenin temel sorularını ve cevaplarını, özellikle de Allah'ın varlığı, Allah'ın ilahi bir doğası ve Allah'ın insanlarla ilişkisi gibi konuları ele alır.
> 2. **İslam Hukuku**: Mu'teziler, İslam hukukunu geliştirmişlerdir. Bu mezhep, İslam hukukunda, kader ve kismet, Allah'ın planları ve insanlarda yer alan yerli ve yabancı karakterleri e

### `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söylenir?
*(doğru=evet, sağlayıcı=None)*

> Fusûsu'l-Hikem: İbnü'l-Arabî'nin özlü hikmet eseri. Şerhler `serh_ve_aciklama/` altına konur.
> 
> Kaynak: Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem

## Geçmeyen sorular

- `din-01` Abdesti bozan şeyler nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-02` Namazın şartları nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-03` İslam'ın şartları nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-04` Zekât kimlere verilir? → BULAMADIM · miss_kutuphane · hits=0
- `din-05` Ramazan orucunu bozan şeyler nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-07` Haccın farzları nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-11` Dört Sünnî fıkıh mezhebi hangileridir? → BULAMADIM · miss_kutuphane · hits=0
- `din-12` Cuma namazı nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-15` Gusül abdesti nasıl alınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-20` Vitir namazı nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-21` Ehl-i Sünnet ve'l-Cemaat kimlere denir? → BULAMADIM · miss_kutuphane · hits=0
- `din-23` Allah'ın sıfatları nelerdir, zâtî ve sübûtî sıfatlar ne demektir? → kap=0.0 · None · hits=0
- `din-24` Allah'ın selbî sıfatları hangileridir? → BULAMADIM · miss_kutuphane · hits=0
- `din-26` İnsanın iradesi ve kesb nazariyesi nedir, Cebriyye ve Kaderiyye'den farkı nedir? → kap=0.0 · hizli · hits=0
- `din-28` Kabir hayatı, ba's ve haşir nedir? → kap=0.333 · hizli · hits=0
- `din-29` Şefaat nedir, kimler kimlere şefaat eder? → kap=0.0 · hizli · hits=0
- `din-30` Ehl-i kıble kimdir, bir Müslümanı tekfir etmek neden ağır bir meseledir? → kap=0.333 · hizli · hits=0
- `din-31` İman nedir, ameller imanın bir parçası mıdır? → kap=0.333 · hizli · hits=0
- `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir? → BULAMADIM · None · hits=None
- `din-34` Bid'at nedir, her yenilik bid'at midir? → kap=0.333 · hizli · hits=0
- `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir? → kap=0.0 · miss_kutuphane · hits=0
- `din-37` Mu'tezile mezhebi nedir, temel görüşleri nelerdir? → kap=0.333 · hizli · hits=0
- `din-38` Hâricîler kimlerdir, hangi görüşleri yüzünden Ehl-i Sünnet'ten ayrılmışlardır? → BULAMADIM · miss_kutuphane · hits=0
- `din-40` İhsan nedir, Cibrîl hadisinde nasıl tarif edilmiştir? → BULAMADIM · miss_kutuphane · hits=0
- `din-41` Tövbe nedir, tövbenin şartları nelerdir? → kap=0.0 · hizli · hits=0
- `din-42` Zühd nedir? → kap=0.0 · hizli · hits=0
- `din-43` Muhabbetullah, yani Allah sevgisi nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-46` Başlıca tarikatlar hangileridir? → kap=0.333 · hizli · hits=0
- `din-51` Tasavvufta makam ile hâl arasındaki fark nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-54` Zikir nedir, zikir çeşitleri nelerdir? → kap=0.333 · hizli · hits=0
- `din-55` Veli kimdir, velâyet ne demektir? → kap=0.333 · hizli · hits=0
- `din-56` Nefsin mertebeleri nelerdir? → kap=0.0 · hizli · hits=0
- `din-58` Namazı bozan şeyler nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-59` Beş vakit namazın vakitleri nelerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-60` Ramazan orucunu tutmayabilecek kimseler kimlerdir? → BULAMADIM · miss_kutuphane · hits=0
- `din-61` Zekâtın nisabı ve oranı nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-62` Hac ile umre arasındaki fark nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-63` Kurban kimlere vâciptir? → BULAMADIM · miss_kutuphane · hits=0
- `din-64` Hanefî ve Şâfiî mezhebi abdestte hangi konularda ayrılır? → kap=0.0 · None · hits=0
- `din-65` Teravih namazı kaç rekâttır, nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-66` Bayram namazı nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
- `din-67` Cenaze namazı nasıl kılınır? → BULAMADIM · miss_kutuphane · hits=0
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
- `din-98` Mekke'nin fethi nasıl olmuştur? → kap=0.0 · hizli · hits=0
- `din-99` Hz. Peygamber ne zaman ve nerede vefat etmiştir? → BULAMADIM · miss_kutuphane · hits=0
- `din-100` İsrâ ve Mi'râc mucizesi nedir? → kap=0.333 · hizli · hits=0
- `din-102` Aşere-i Mübeşşere kimlerdir? → kap=0.0 · hizli · hits=0
- `din-103` Kerbelâ olayı nedir? → kap=0.333 · hizli · hits=0
- `din-104` Emevî devleti ne zaman kurulmuştur, başkenti neresidir? → BULAMADIM · None · hits=None
- `din-105` Endülüs'ün fethi nasıl gerçekleşmiştir? → BULAMADIM · None · hits=None
- `din-106` Hıttîn Savaşı ve Selâhaddîn-i Eyyûbî'nin Kudüs'ü fethi nasıl olmuştur? → kap=0.0 · None · hits=0
- `din-107` Hilâfet Osmanlılara ne zaman ve nasıl geçmiştir? → kap=0.333 · None · hits=0
- `din-108` Hz. Âdem'in yaratılışı ve cennetten çıkarılışı nasıldır? → BULAMADIM · miss_kutuphane · hits=0
- `din-109` Hz. Nûh ve tûfan kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-110` Hz. İbrâhîm ve Nemrut kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-111` Hz. Yûsuf kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-112` Hz. Mûsâ ile Firavun kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-113` Hz. Îsâ'nın doğumu nasıl olmuştur? → BULAMADIM · miss_kutuphane · hits=0
- `din-115` Hz. Yûnus'un balığın karnında kalması kıssası nedir? → BULAMADIM · miss_kutuphane · hits=0
- `din-116` Abdesti bozan şeyler nelerdir? Kaynak göster. → BULAMADIM · miss_kutuphane · hits=0
- `din-117` Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göster. → kap=0.0 · hizli · hits=0
- `din-118` Kader nedir? Hangi eserlere dayanarak anlatıyorsun, kaynak ver. → kap=0.0 · None · hits=0
- `din-119` Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçiyor? → kap=0.0 · hizli · hits=0
- `din-120` Tövbenin şartları nelerdir? Kaynağını da göster. → BULAMADIM · hizli · hits=0
- `din-121` Tasavvuf nedir? Hangi eserlere göre, kaynak göster. → kap=0.0 · hizli · hits=0
- `din-122` İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. → kap=0.0 · None · hits=0
- `din-123` Zühd nedir? Kaynak göster, hangi eserde anlatılır? → kap=0.0 · hizli · hits=0
- `din-125` Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kitabında geçer, kaynak ver. → kap=0.333 · None · hits=0
- `din-127` İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak göster. → kap=0.0 · hizli · hits=0
- `din-128` Hicret nedir? Kaynak göster, hangi siyer kitabında geçer? → kap=0.0 · None · hits=0
- `din-129` Hz. Ömer kimdir? Eser ve müellif künyesiyle kaynak göster. → BULAMADIM · miss_kutuphane · hits=0