# Din raporu — din_d2_bm25 (2026-11-24)

Yalnız **din rafı** (web kapalı). Koşucu: `scripts/altin_set_kos.py din-rapor`; ölçütler: `scripts/din_olcut.py`.

| Ölçüt | din_k3_tdkfix | din_d2_bm25 |
|---|---:|---:|
| Soru sayısı | 130 | 130 |
| Doğru cevap % | %57.7 | %73.1 |
| «Bulamadım» % | %31.5 | %3.8 |
| Ort. kapsama | 0.573 | 0.713 |
| (a) «Kaynak göster» varyantlarında künye gelen % | %0.0 | %66.7 |
| (a) Tüm din cevaplarında doğrulanmış künye % | %0.0 | %60.0 |
| (b) Çoklu eser (≥2 farklı eser anışı) % | %0.0 | %59.2 |
| (b) Çoklu eser — yalnız «kaynak göster» varyantlarında % | %0.0 | %66.7 |
| (c) Uydurma kaynak şüphesi — soru sayısı | 19 | 15 |
| (c) Uydurma kaynak şüphesi — atıf sayısı | 23 | 18 |
| (d) Sadelik ajan puanı (1–5) | — | — |
| Medyan sn | 8.54 | 14.07 |
| P90 sn | 31.49 | 49.06 |

Sağlayıcılar: {'gemini': 86, 'None': 42, 'miss_kutuphane': 1, 'kutuphane_extractive': 1}

## Alt-raf bazında

| Alt-raf | N | Doğru % | Bulamadım % |
|---|---:|---:|---:|
| akaid | 21 | 57.1 | 4.8 |
| fikih | 18 | 72.2 | 22.2 |
| hadis | 11 | 100.0 | 0.0 |
| kissa | 8 | 100.0 | 0.0 |
| siyer | 13 | 76.9 | 0.0 |
| tarih | 4 | 50.0 | 0.0 |
| tasavvuf | 24 | 70.8 | 0.0 |
| tefsir | 11 | 36.4 | 0.0 |
| temel | 20 | 90.0 | 0.0 |

## «Kaynak göster» varyantları

| id | Soru | Künye? | Eser sayısı | Şüpheli atıf |
|---|---|:-:|---:|---|
| `din-116` | Abdesti bozan şeyler nelerdir? Kaynak göster. | ✔ | 4 |  |
| `din-117` | Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göste | ✔ | 5 | Kur'an-ı Kerim Tevbe Suresi'nin |
| `din-118` | Kader nedir? Hangi eserlere dayanarak anlatıyorsun, kaynak v | ✔ | 4 |  |
| `din-119` | Ehl-i Sünnet kimlerdir? Kaynak göster, hangi kitaplarda geçi | ✔ | 3 |  |
| `din-120` | Tövbenin şartları nelerdir? Kaynağını da göster. | ✔ | 5 |  |
| `din-121` | Tasavvuf nedir? Hangi eserlere göre, kaynak göster. | ✔ | 4 |  |
| `din-122` | İhsan nedir? Hangi hadis ve kaynakta geçer, kaynak göster. | ✔ | 4 |  |
| `din-123` | Zühd nedir? Kaynak göster, hangi eserde anlatılır? | ✔ | 4 |  |
| `din-124` | Sahih, hasen ve zayıf hadis arasındaki fark nedir? Kaynak gö | ✘ | 0 |  |
| `din-125` | Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kit | ✘ | 0 |  |
| `din-126` | Sebeb-i nüzûl nedir? Kaynak göster. | ✘ | 0 |  |
| `din-127` | İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak gö | ✔ | 4 |  |
| `din-128` | Hicret nedir? Kaynak göster, hangi siyer kitabında geçer? | ✘ | 0 |  |
| `din-129` | Hz. Ömer kimdir? Eser ve müellif künyesiyle kaynak göster. | ✔ | 4 |  |
| `din-130` | Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göste | ✘ | 0 | Mâtürîdî Kitâbü't-Tevhîd'i |

## Uydurma kaynak şüphesi (ayrıntı — denetleyici sezgiseldir, el ile doğrula)

- `din-09` İman esasları nelerdir? → şüpheli: ['Cibril Hz'] · doğrulanan: ['  الإيمان لابن تيمية — ابن تيمية', '  منحة القريب المجيب في الرد على عباد الصليب — عبد العزيز بن حمد آل معمر', '  الصواعق المرسلة على الجهمية والمعطلة - ط عطاءات العلم — ابن القيم'] · künyeler: ['الإيمان لابن تيمية', 'منحة القريب المجيب في الرد على عباد الصليب', 'الصواعق المرسلة على الجهمية والمعطلة - ط عطاءات العلم', 'النبوات لابن تيمية']
- `din-47` Abdülkadir Geylânî kimdir? → şüpheli: ["Sultanü'l-Evliya"] · doğrulanan: [] · künyeler: []
- `din-48` İmam Gazâlî kimdir, İhyâu Ulûmid-Dîn eserinin önemi nedir? → şüpheli: ["İmam Gazâlî (ö. 505/1111), İhyâü Ulûmi'd-Dîn"] · doğrulanan: [] · künyeler: []
- `din-49` Mevlânâ Celâleddîn-i Rûmî kimdir, Mesnevî nedir? → şüpheli: ['Mevlânâ Celâleddîn-i Rûmî (ö. 672/1273), Mesnevî'] · doğrulanan: [] · künyeler: []
- `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söy → şüpheli: ["Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem"] · doğrulanan: [] · künyeler: []
- `din-58` Namazı bozan şeyler nelerdir? → şüpheli: ['bu kişi namazda değil'] · doğrulanan: ['  منهج السالكين وتوضيح الفقة في الدين — عبد الرحمن السعدي', '  فتاوى ورسائل سماحة الشيخ محمد بن إبراهيم بن عبد اللطيف آل الشيخ — محمد بن إبراهيم آل الشيخ', '  الفقه على المذاهب الأربعة — عبد الرحمن الجزيري'] · künyeler: ['منهج السالكين وتوضيح الفقة في الدين', 'فتاوى ورسائل سماحة الشيخ محمد بن إبراهيم بن عبد اللطيف آل الشيخ', 'الفقه على المذاهب الأربعة', 'الدين الخالص أو إرشاد الخلق إلى دين الحق']
- `din-78` İmam Buhârî kimdir, Sahîh'i neden önemlidir? → şüpheli: ["el-Câmiu's-sahîh"] · doğrulanan: [] · künyeler: []
- `din-79` «Ameller niyetlere göredir» hadisi ne anlatır? → şüpheli: ['Sahîh-i Buhârî, Kitâbü’l-Îmân (Îman kitabı), hadis no. 1 (Buhârî’nin ilk hadisi). Uydurma cilt/kitap numarası veya başka metin söylemem.', 'Îman', 'niyet hadisi'] · doğrulanan: [] · künyeler: []
- `din-83` Erbaîn (kırk hadis) geleneği nedir? → şüpheli: ['Bağlamdaki'] · doğrulanan: ['  البحر الذي زخر في شرح ألفية الأثر - قسم 1 - ت الأندونوسي — الجلال السيوطي', '  التلخيص الحبير - ط أضواء السلف — ابن حجر العسقلاني', '  كشف الخفاء ت هنداوي — العجلوني'] · künyeler: ['البحر الذي زخر في شرح ألفية الأثر - قسم 1 - ت الأندونوسي', 'التلخيص الحبير - ط أضواء السلف', 'كشف الخفاء ت هنداوي', 'إرشاد طلاب الحقائق إلى معرفة سنن خير الخلائق صلى الله عليه وسلم']
- `din-94` İslâm'ı ilk kabul edenler kimlerdir? → şüpheli: ["Ali İslam'ın"] · doğrulanan: ['  سبل الهدى والرشاد في سيرة خير العباد — الصالحي الشامي', '  عيون الأثر — ابن سيد الناس', '  الإشارة إلى سيرة المصطفى وتاريخ من بعده من الخلفا — علاء الدين مغلطاي'] · künyeler: ['سبل الهدى والرشاد في سيرة خير العباد', 'عيون الأثر', 'الإشارة إلى سيرة المصطفى وتاريخ من بعده من الخلفا', 'الإنجاد في أبواب الجهاد']
- `din-100` İsrâ ve Mi'râc mucizesi nedir? → şüpheli: ['Muhammed Mekke’deki Mescid-i Haram’dan Kudüs’teki', "Kur'an-ı Kerim İsrâ Suresi'nde"] · doğrulanan: [] · künyeler: []
- `din-109` Hz. Nûh ve tûfan kıssası nedir? → şüpheli: ['Sekizler'] · doğrulanan: ['  نزهة الأنظار في عجائب التواريخ والأخبار — محمود مقديش', '  مرآة الزمان في تواريخ الأعيان — سبط ابن الجوزي', '  موسوعة مرآة الحرمين الشريفين وجزيرة العرب — أيوب صبري باشا'] · künyeler: ['نزهة الأنظار في عجائب التواريخ والأخبار', 'مرآة الزمان في تواريخ الأعيان', 'موسوعة مرآة الحرمين الشريفين وجزيرة العرب', 'البدء والتاريخ']
- `din-112` Hz. Mûsâ ile Firavun kıssası nedir? → şüpheli: ["İsrâiloğulları Mısır'daki"] · doğrulanan: ['  التاريخ المعتبر في أنباء من غبر — مجير الدين العليمي', '  البداية والنهاية - ط دار ابن كثير — ابن كثير', '  مرآة الزمان في تواريخ الأعيان — سبط ابن الجوزي'] · künyeler: ['التاريخ المعتبر في أنباء من غبر', 'البداية والنهاية - ط دار ابن كثير', 'مرآة الزمان في تواريخ الأعيان', 'نزهة الأنظار في عجائب التواريخ والأخبار']
- `din-117` Zekât kimlere verilir? Hangi eserde yazıyor, kaynağını göster. → şüpheli: ["Kur'an-ı Kerim Tevbe Suresi'nin"] · doğrulanan: ['  النقد والبيان في دفع أوهام خزيران — محمد كامل القصاب', '  قرة العين بفتاوى علماء الحرمين — حسين المغربي', '  فتاوى ورسائل سماحة الشيخ محمد بن إبراهيم بن عبد اللطيف آل الشيخ — محمد بن إبراهيم آل الشيخ'] · künyeler: ['النقد والبيان في دفع أوهام خزيران', 'قرة العين بفتاوى علماء الحرمين', 'فتاوى ورسائل سماحة الشيخ محمد بن إبراهيم بن عبد اللطيف آل الشيخ', 'زاد المعاد في هدي خير العباد - ت الرسالة الثاني']
- `din-130` Tevhid nedir, Allah'ın birliği nasıl anlatılır? Kaynak göster. → şüpheli: ["Mâtürîdî Kitâbü't-Tevhîd'i"] · doğrulanan: [] · künyeler: []

## Ehl-i Sünnet çizgisi soruları — el/ajan incelemesi için cevaplar

### `din-22` Eş'arî ve Mâtürîdî kimdir, itikadda nasıl bir yol izlemişlerdir?
*(doğru=evet, sağlayıcı=gemini)*

> Eş'arî ve Mâtürîdî, Ehl-i sünnet vel-cemaat inancının akaid ve kelâm
> 
> Kaynak izi:
> [K1] تنبيه الرجل العاقل على تمويه الجدل الباطل — ابن تيمية
> [K2] لوائح الأنوار السنية ولواقح الأفكار السنية — السفاريني
> [K3] التسعينية — ابن تيمية
> [K4] التنكيل بما في تأنيب الكوثري من الأباطيل - ضمن «آثار المعلمي» — عبد الرحمن المعلمي اليماني

### `din-26` İnsanın iradesi ve kesb nazariyesi nedir, Cebriyye ve Kaderiyye'den farkı nedir?
*(doğru=evet, sağlayıcı=gemini)*

> Ümit abi, insanın iradesi ve kesb nazariyesi, kulun fiillerindeki sorumluluğunu ve ilâhî irade ile olan ilişkisini açıklayan temel kelâm konularıdır. Cebriyye mezhebi insanın iradesini tamamen inkar ederek kulu rüzgar önündeki yaprak gibi iradesiz görür; Kaderiyye (ve Mutezile) ise kulun kendi fiilinin tam ve müstakil yaratıcısı olduğunu savunarak ilâhî iradeyi bu alanda devre dışı bırakır. Ehl-i Sünnet'in benimsediği **kesb nazariyesi** ise orta yolu tutar: Allah yaratır (halk), kul ise iradesiyle tercih eder ve üstlenir (kesb); böylece ne kul iradesiz bir mahkûmdur ne de Allah'ın iradesi dışında bir halik vardır.
> 
> Ebû الحسن الأشعري'nin *Resâil* ve diğer kelâm kaynaklarında geçtiği üzere, kulun kendi fiillerini irade etmesi ve bu iradenin Allah'ın kainattaki genel yaratma kanunuyla buluşması, insanın hem sorumlu tutulmasının hem de ilâhî adaletin temelini oluşturur.
> 
> Kaynak izi:
> [K1] ال

### `din-27` Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, **Otomatik → İngilizce** çeviri:
> 
> manifestation (spiri

### `din-29` Şefaat nedir, kimler kimlere şefaat eder?
*(doğru=evet, sağlayıcı=gemini)*

> Şefaat, kıyamet gününde günahkâr müminlerin bağışlanması veya derecelerinin yükseltilmesi için peygamberlerin, meleklerin ve salih kulların Allah katında dua ve telkinde bulunmasıdır; ehli sünnet akidesine göre peygamberimizin büyük günah işleyenler dâhil olmak üzere müminlere şefaati haktır.
> 
> İbnü'l-Kayyim'in *İslam Ordularının Birleşmesi* adlı eserinde ve İbn Teymiyye'nin *İktisada Sıkı Tutunmak* ile *Tescينية* gibi çalışmalarında vurgulandığı üzere; peygamberlerin, meleklerin, şehitlerin ve salih müminlerin izin verilen ölçüde şefaat etme hakkı vardır. Ancak bu şefaat yalnızca Allah'ın izni ve rızasıyla, Ehl-i sünnet çizgisinde, tevhit ehli olan ve şirk koşmadan vefat eden müminler için geçerlidir; Kur'an'da ve sahih hadislerde bildirilen bu gerçek, Harici ve Mutezile gibi bazı fırkalar tarafından inkâr edilmiştir.
> 
> Kaynak izi:
> [K1] اجتماع الجيوش الإسلامية - ط عطاءات العلم — ابن القيم

### `din-30` Ehl-i kıble kimdir, bir Müslümanı tekfir etmek neden ağır bir meseledir?
*(doğru=evet, sağlayıcı=gemini)*

> Ehl-i kıble, kıstası namazda Kâbe yönü olan, yani İslâm şiarını benimsemiş ve kelime-i şehadetle Müslüman kabul edilen topluluğu ifade eder. Bir Müslümanı tekfir etmek, yani onu kâfir ilan etmek oldukça ağır bir meseledir; çünkü bu durum kişinin hem bu dünyadaki hukukunu hem de ahiret hükmünü doğrudan sarsan büyük bir vebaldir.
> 
> İslâm âlimlerinin temel prensibine göre, bir kişinin ibadetleri ve kelime-i şehadeti ortadayken, sırf hataları veya tevil yoluyla işlediği günahlar yüzünden tekfir edilmesi Ehl-i sünnet çizgisinde makul görülmemiştir. Nitekim İbn Ebî el-Z’nin *Şerhu’n-Akīdeti’t-Tahâviyye* adlı eserinde vurgulandığı üzere, Ehl-i sünnet âlimleri "ehl-i kıbleden hiç kimseyi, helâl saymadığı sürece işlediği bir günahtan dolayı tekfir etmeyiz" kaidesini
> 
> Kaynak izi:
> [K1] تحفة الطالب والجليس في كشف شبه داود بن جرجيس — عبد اللطيف آل الشيخ
> [K2] شرح العقيدة الطحاوية - بتخريج الألباني — اب

### `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir?
*(doğru=hayır, sağlayıcı=gemini)*

> Ehl-i Sünnet’in sahâbe hakkındaki temel görüşü, aralarında geçen olaylarda onları tenkit etmekten kaçınmak ve her birinin iyi niyetle hareket ettiğini kabul ederek dili tutmaktır. Abdurrahman b. Kasım, *حاشية الدرة المضية في عقد الفرقة المرضية* adlı eserinde, sahâbe arasında yaşanan نزاع (içtihat kaynaklı çekişmeler) konusunda mezhebin tutumunu şöyle açıklar: Onların hatalarının ya bağışlandığını, ya geçmişteki büyük faziletleri ve erdemleri sayesinde örtüldüğünü ya da bu hataların işledikleri sevaplar ve Hz. Muhammed’in şefaatiyle ortadan kalktığını kabul ederler. Zira onlar bu ümmetin صفوة (seçkinleri) ve Allah katında en değerli insanlarıdır.
> 
> Kaynak izi:
> [K1] حاشية الدرة المضية في عقد الفرقة المرضية — عبد الرحمن بن قاسم
> [K2] طليعة التنكيل وتعزيز الطليعة وشكر الترحيب - ضمن «آثار المعلمي» — عبد الرحمن المعلمي اليماني
> [K3] نونية ابن القيم الكافية الشافية - ط عطاءات العلم — ابن القيم
> [K4

### `din-34` Bid'at nedir, her yenilik bid'at midir?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, **Otomatik → İngilizce** çeviri:
> 
> What is a horse, every innovation is a bid.

### `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, süre yetmedi; cevap yarım kaldı. Bu bir «bilmiyorum / öğret» değil — biraz sonra tekrar dene veya soruyu kısalt.
> 
> Kaynak izi:
> [K1] الرد على الشاذلي في حزبيه وما صنفه في آداب الطريق — ابن تيمية
> [K2] شرح الزرقاني على المواهب اللدنية بالمنح المحمدية — الزرقاني، محمد بن عبد الباقي
> [K3] أنموذج اللبيب في خصائص الحبيب — الجلال السيوطي
> [K4] اقتضاء الصراط المستقيم لمخالفة أصحاب الجحيم — ابن تيمية

### `din-37` Mu'tezile mezhebi nedir, temel görüşleri nelerdir?
*(doğru=hayır, sağlayıcı=None)*

> Ümit abi, «Mu'tezile mezhebi nedir, temel görüşleri nelerdir?» sorusuna net ve güvenilir bir yanıt veremedim. Yanıt soruyla tam örtüşmüyor; önceki bağlam veya model kayması olabilir. Web araması açıksa tekrar deneyebilir veya soruyu biraz daha netleştirebilirsin.
> 
> Kaynak izi:
> [K1] شرح الزرقاني على المواهب اللدنية بالمنح المحمدية — الزرقاني، محمد بن عبد الباقي
> [K2] الانتصار في الرد على المعتزلة القدرية الأشرار — العمراني
> [K3] السيرة النبوية من البداية والنهاية - ت عبد الواحد — ابن كثير
> [K4] رسالة السجزي إلى أهل زبيد في الرد على من أنكر الحرف والصوت — عبيد الله السجزي

### `din-50` İbn Arabî kimdir, Fusûsü'l-Hikem ve Fütûhât-ı Mekkiyye hakkında ne söylenir?
*(doğru=evet, sağlayıcı=None)*

> Fusûsu'l-Hikem: İbnü'l-Arabî'nin özlü hikmet eseri. Şerhler `serh_ve_aciklama/` altına konur.
> 
> Kaynak: Muhyiddin İbnü'l-Arabî (ö. 638/1240), Fusûsu'l-Hikem

## Geçmeyen sorular

- `din-02` Namazın şartları nelerdir? → kap=0.5 · gemini · hits=5
- `din-07` Haccın farzları nelerdir? → kap=0.0 · gemini · hits=5
- `din-23` Allah'ın sıfatları nelerdir, zâtî ve sübûtî sıfatlar ne demektir? → kap=0.0 · None · hits=0
- `din-24` Allah'ın selbî sıfatları hangileridir? → kap=0.0 · gemini · hits=5
- `din-27` Âhirette Allah'ın görülmesi (ru'yetullah) mümkün müdür? → kap=0.0 · None · hits=0
- `din-33` Sahâbe hakkında Ehl-i Sünnet'in görüşü nedir? → kap=0.333 · gemini · hits=5
- `din-34` Bid'at nedir, her yenilik bid'at midir? → kap=0.0 · None · hits=0
- `din-35` Tevessül nedir, peygamberi ve salih kulları vesile kılarak dua etmek caiz midir? → kap=0.0 · None · hits=5
- `din-36` Hulefâ-yı Râşidîn kimlerdir, hilâfet sırası nasıldır? → kap=0.0 · None · hits=5
- `din-37` Mu'tezile mezhebi nedir, temel görüşleri nelerdir? → kap=0.333 · None · hits=5
- `din-38` Hâricîler kimlerdir, hangi görüşleri yüzünden Ehl-i Sünnet'ten ayrılmışlardır? → BULAMADIM · None · hits=5
- `din-40` İhsan nedir, Cibrîl hadisinde nasıl tarif edilmiştir? → kap=0.333 · None · hits=5
- `din-41` Tövbe nedir, tövbenin şartları nelerdir? → kap=0.333 · None · hits=5
- `din-44` Sülûk ve seyr-i sülûk ne demektir? → kap=0.0 · gemini · hits=0
- `din-46` Başlıca tarikatlar hangileridir? → kap=0.0 · gemini · hits=0
- `din-56` Nefsin mertebeleri nelerdir? → kap=0.0 · gemini · hits=0
- `din-59` Beş vakit namazın vakitleri nelerdir? → BULAMADIM · gemini · hits=5
- `din-63` Kurban kimlere vâciptir? → BULAMADIM · miss_kutuphane · hits=0
- `din-64` Hanefî ve Şâfiî mezhebi abdestte hangi konularda ayrılır? → BULAMADIM · None · hits=0
- `din-69` Nikâhın sahih olması için gereken şartlar nelerdir? → kap=0.0 · gemini · hits=5
- `din-84` Tefsirde rivayet ve dirayet usulü nedir? → kap=0.333 · None · hits=0
- `din-88` Âyetü'l-Kürsî'nin anlamı ve fazileti nedir? → kap=0.333 · None · hits=0
- `din-89` İhlâs Sûresi'nin anlamı nedir? → kap=0.0 · None · hits=0
- `din-90` Kur'ân-ı Kerîm kaç cüzden ve yaklaşık kaç âyetten oluşur? → kap=0.5 · None · hits=0
- `din-91` Kur'ân'ın ilk inen âyetleri hangileridir, nerede inmiştir? → kap=0.0 · None · hits=0
- `din-92` Kur'ân-ı Kerîm nasıl bir mushaf hâline getirilmiştir (cem' tarihi)? → kap=0.333 · None · hits=0
- `din-93` Hz. Muhammed kaç yaşında peygamber olmuştur, ilk vahiy nasıl gelmiştir? → kap=0.333 · None · hits=0
- `din-98` Mekke'nin fethi nasıl olmuştur? → kap=0.0 · gemini · hits=5
- `din-99` Hz. Peygamber ne zaman ve nerede vefat etmiştir? → kap=0.0 · gemini · hits=5
- `din-106` Hıttîn Savaşı ve Selâhaddîn-i Eyyûbî'nin Kudüs'ü fethi nasıl olmuştur? → kap=0.0 · None · hits=0
- `din-107` Hilâfet Osmanlılara ne zaman ve nasıl geçmiştir? → kap=0.0 · None · hits=0
- `din-116` Abdesti bozan şeyler nelerdir? Kaynak göster. → BULAMADIM · gemini · hits=5
- `din-121` Tasavvuf nedir? Hangi eserlere göre, kaynak göster. → kap=0.5 · gemini · hits=5
- `din-125` Nâsih ve mensûh nedir? Hangi tefsir veya Kur'ân ilimleri kitabında geçer, kaynak ver. → kap=0.333 · None · hits=0
- `din-127` İmam Gazâlî kimdir? Hangi kaynaklarda anlatılıyor, kaynak göster. → kap=0.0 · kutuphane_extractive · hits=5