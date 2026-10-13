# -*- coding: utf-8 -*-
"""Eksik ilim rafları — bağımlılık sırası.

Özgün ders notu. Telifli kitap aktarımı yok.
Tıbbi teşhis, avukatlık, yatırım tavsiyesi, suç işleme ve elektrik tesisatı tarifi yok.
"""
from __future__ import annotations

# Sıra bağlayıcıdır: nicel temel → yer ve gök → canlı → dil ve sanat → toplum → eğitim.
RAFLAR: list[dict] = [
    {
        "id": "matematik_derin",
        "baslik": "Matematik derin",
        "sira": 1,
        "neden": "İstatistik, elektrik, astronomi ve ekonominin ortak dili.",
        "kavramlar": [
            {
                "id": "matematik_derin",
                "baslik": "matematik derin",
                "aliases": ["matematik derin", "yuksek matematik", "yüksek matematik", "kalkulus", "kalkülüs"],
                "metin": (
                    "Derin matematik, sezgisel hesabı limit diliyle kesinleştirir. Fonksiyon bir büyüklüğü başka bir büyüklüğe bağlar. "
                    "Limit, girdi bir değere yaklaşırken çıktının hangi değere oturduğunu söyler; fonksiyon o noktada tanımlı olmak zorunda değildir. "
                    "Süreklilik, limitin fonksiyonun kendi değerine eşit olmasıdır. Türev anlık değişim, integral birikmiş değişimdir. "
                    "Lineer cebir aynı değişimi düzlem ve uzayda doğrusal dönüşüm olarak görür. Bu raf okul özetinin üstüdür; ispat alıştırmasının tamamı değildir."
                ),
            },
            {
                "id": "limit_sureklilik",
                "baslik": "limit ve süreklilik",
                "aliases": ["limit nedir", "sureklilik", "süreklilik", "epsilon delta"],
                "metin": (
                    "Limit, x bir a sayısına yaklaşırken f(x) değerlerinin bir L sayısına yaklaşmasıdır. x, a’ya hiç eşit olmadan da limit var olabilir; delik olan bir grafikte böyledir. "
                    "Epsilon-delta dili şunu söyler: L’nin her komşuluğu için a’nın yeterince dar bir komşuluğu vardır ki oradaki f değerleri o komşulukta kalsın. "
                    "Sağ ve sol limitler ayrıysa iki taraflı limit yoktur. Süreklilik, limitin var olması ve f(a) ile eşit olmasıdır. "
                    "Polinomlar tanım kümesinde süreklidir. Süreksizlik sıçrama, sonsuz veya kaldırılabilir olabilir."
                ),
            },
            {
                "id": "turev",
                "baslik": "türev",
                "aliases": ["turev", "türev", "turev nedir", "türev nedir", "anlik degisim"],
                "metin": (
                    "Türev, fonksiyonun bir noktadaki anlık değişim oranıdır; grafikte o noktadaki teğetin eğimidir. "
                    "Ortalama değişim, iki nokta arasındaki kirişin eğimidir. Noktalar birbirine yaklaştıkça kiriş teğete döner; bu limit türevdir. "
                    "Türev pozitifse fonksiyon o aralıkta artar, negatifse azalır, sıfırsa yatay teğet vardır. "
                    "Toplamın türevi türevlerin toplamıdır. Çarpım kuralı iki fonksiyonun birbirini sürüklediğini ayırır. Zincir kuralı iç içe fonksiyonun değişimlerini çarpar. "
                    "Hız, konumun zamana göre türevidir; ivme hızın türevidir."
                ),
            },
            {
                "id": "integral",
                "baslik": "integral",
                "aliases": ["integral", "integral nedir", "belirli integral", "alan hesabi"],
                "metin": (
                    "Belirsiz integral, türevi verilen fonksiyona eşit olan fonksiyon ailesidir; sabit farkı serbesttir. "
                    "Belirli integral, bir aralıkta fonksiyonun biriktirdiği net büyüklüktür. Pozitif fonksiyonun grafiği altında kalan alan bunun örneğidir. "
                    "Riemann fikri, aralığı ince dilimlere bölüp yükseklikleri toplamaktır; dilim inceldikçe toplam alana oturur. "
                    "Analizin temel teoremi iki yüzü bağlar: türevin integrali net değişimi verir, integralin türevi fonksiyonun kendisine döner. "
                    "Yer değiştirme, hızın zamana integralidir."
                ),
            },
            {
                "id": "lineer_cebir",
                "baslik": "lineer cebir",
                "aliases": ["lineer cebir", "lineer cebir nedir", "matris", "vektor uzayi", "vektör uzayı"],
                "metin": (
                    "Lineer cebir, toplamaya ve sayıyla çarpmaya kapalı vektör uzaylarını inceler. Düzlemdeki oklar bir örnektir. "
                    "Matris, doğrusal dönüşümün seçilen tabandaki tablosudur: vektörü alır, başka bir vektöre götürür. "
                    "Denklem sistemi, matris çarpı bilinmeyen eşittir sonuç diye yazılır. Çözüm, dönüşümün o sonucu üreten girdileridir. "
                    "Ters matris varsa çözüm tektir. Determinant sıfırsa dönüşüm alanı ezer ve ters yoktur. "
                    "Özvektör, dönüşümün yalnız uzatıp kısalttığı yöndür; özdeğer o çarpandır. Bu not bir ders kitabının problem çözümü değildir."
                ),
            },
            {
                "id": "fonksiyon_grafigi",
                "baslik": "fonksiyon",
                "aliases": ["fonksiyon nedir", "birebir orten", "birebir örten", "tanim kumesi"],
                "metin": (
                    "Fonksiyon, tanım kümesindeki her elemana değer kümesinde tam bir eleman bağlar. Bir girdiye iki çıktı bağlanırsa fonksiyon değildir. "
                    "Birebir fonksiyon farklı girdileri farklı çıktılara götürür. Örten fonksiyon değer kümesinin her elemanına ulaşır. "
                    "İkisi birden varsa ters fonksiyon vardır. Bileşke, birinin çıktısını diğerinin girdisi yapmaktır. "
                    "Grafik, girdi-çıktı çiftlerinin düzlemdeki yeridir. Dikey doğru bir grafiği iki noktada keserse o eğri fonksiyon değildir. "
                    "Polinom, rasyonel, üstel ve trigonometrik fonksiyonlar bu sözleşmenin örnekleridir."
                ),
            },
        ],
    },
    {
        "id": "istatistik_olasilik",
        "baslik": "İstatistik ve olasılık",
        "sira": 2,
        "neden": "Ölçülen bilginin belirsizliğini matematik üstüne kurar.",
        "kavramlar": [
            {
                "id": "olasilik",
                "baslik": "olasılık",
                "aliases": ["olasilik", "olasılık", "olasilik nedir", "olasılık nedir", "kosullu olasilik"],
                "metin": (
                    "Olasılık, bir olayın olabilirliğine 0 ile 1 arasında sayı verir. İmkânsız olay 0, kesin olay 1’dir. "
                    "Ayrık olayların olasılıkları toplanır. Tümleyen, olayın olmamasıdır ve biri tamamlar. "
                    "Koşullu olasılık, bir şey bilinirken diğerinin olasılığıdır. Bağımsızlık, birini bilmenin diğerini değiştirmemesidir; o zaman ortak olasılık çarpımdır. "
                    "Bu sayılar modeldir: yazı-tura idealleşmesi gerçek paranın her savruluşunu tek tek söylemez. "
                    "Ortalama ve medyanın kısa tanımı bilim rafındadır; bu raf belirsizliğin hesabıdır."
                ),
            },
            {
                "id": "beklenen_varyans",
                "baslik": "beklenen değer ve varyans",
                "aliases": ["beklenen deger", "beklenen değer", "varyans", "standart sapma"],
                "metin": (
                    "Beklenen değer, sonuçların olasılıklarıyla ağırlıklı ortalamasıdır. Uzun vadede tekrarlanan denemenin merkezidir; tek bir denemenin sonucu olmak zorunda değildir. "
                    "Varyans, sonuçların bu merkezden karesel ortalama uzaklığıdır. Standart sapma varyansın kareköküdür ve sonuçla aynı birimdedir. "
                    "Bağımsız toplamın varyansı varyansların toplamıdır. Yayılım büyükse ortalama tek başına dağılımı anlatmaz. "
                    "Aykırı değer ortalamayı kaydırır; medyan sıranın ortasında kaldığı için buna daha az duyarlıdır."
                ),
            },
            {
                "id": "normal_dagilim",
                "baslik": "normal dağılım",
                "aliases": ["normal dagilim", "normal dağılım", "can egrisi", "çan eğrisi"],
                "metin": (
                    "Normal dağılım, ortalaması ve standart sapmasıyla belirlenen çan biçimli bir modeldir. Simetriktir; ortalama, medyan ve tepe aynı yerdedir. "
                    "Birçok küçük ve bağımsız etkinin toplamı, şartlar uygunsa normale yaklaşır; buna merkezi limit fikri denir. "
                    "Her veri normal değildir: gelir, bekleme süresi ve sayım çoğu zaman çarpıktır. Modeli veriye bakmadan varsaymak hatadır. "
                    "Standart normal, ortalaması 0 ve sapması 1 olacak şekilde kaydırılıp ölçeklenmiş halidir."
                ),
            },
            {
                "id": "orneklem",
                "baslik": "örneklem",
                "aliases": ["orneklem", "örneklem", "yigin ve orneklem", "anakitle"],
                "metin": (
                    "Anakitle, hakkında söz söylemek istediğin bütün kümedir. Örneklem, ondan seçilen alt kümedir. "
                    "İstatistik, örneklemden anakitleye ihtiyatlı genellemedir. Rasgele seçim, her birimin bilinen bir şansı olmasıdır; kolayına gelen kişiyi sormak rasgele değildir. "
                    "Yanlı seçim, sonucu anakitleden sistemli kaydırır. Örneklem büyüdükçe ortalamanın sapması genelde azalır, ama yanlılık büyümekle düzelmez. "
                    "Güven aralığı, yöntemin tekrarında gerçek parametreyi belirli bir sıklıkla örtecek biçimde kurulur; tek bir aralık için «yüzde şu ihtimalle içinde» demek aynı cümle değildir."
                ),
            },
            {
                "id": "hipotez_testi",
                "baslik": "hipotez testi",
                "aliases": ["hipotez testi", "p degeri", "p değeri", "sifir hipotezi", "sıfır hipotezi"],
                "metin": (
                    "Sıfır hipotezi, fark yok veya etki yok gibi bir başlangıç iddiasıdır. Karşı hipotez, bakılan yöndeki ayrılıştır. "
                    "Test, veri sıfır altındayken ne kadar uçta diye bakar. p değeri, sıfır doğruysa gözlenen veya daha uç bir sonucun olasılığıdır. "
                    "Küçük p, verinin sıfırla uyumunun zayıf olduğunu söyler; tek başına etkinin büyük olduğunu veya kararın bittiğini söylemez. Eşik, örneklem büyüklüğü ve bağlam birlikte okunur. "
                    "Anlamlılık ile pratik önem ayrıdır. Bu not tıbbi teşhis veya tedavi kararı değildir."
                ),
            },
            {
                "id": "korelasyon",
                "baslik": "korelasyon",
                "aliases": ["korelasyon", "korelasyon nedir", "nedensellik degil"],
                "metin": (
                    "Korelasyon, iki değişkenin birlikte artıp azalmasının ölçüsüdür. Bire yakın değer aynı yönde, eksi bire yakın değer ters yönde sıkı ilişkiyi anlatır. Sıfır, doğrusal ilişkinin görünmediğidir; her ilişkinin yokluğu değildir. "
                    "Birlikte değişmek, birinin diğerini ürettiğini göstermez. Ortak bir üçüncü sebep ikisini birden sürükleyebilir. "
                    "Nedensellik için zaman sırası, alternatiflerin elenmesi ve çoğu zaman bir müdahale tasarımı gerekir. Grafiği görmeden yalnız katsayıya bakmak da yanıltır."
                ),
            },
        ],
    },
    {
        "id": "elektrik_elektronik",
        "baslik": "Elektrik ve elektronik",
        "sira": 3,
        "neden": "Bilgisayar donanımının fiziksel dili. Ev tesisatı tarifi değildir.",
        "kavramlar": [
            {
                "id": "ohm_kirchhoff",
                "baslik": "Ohm ve Kirchhoff",
                "aliases": ["ohm kanunu derin", "kirchhoff", "kirchhoff kanunu", "gerilim akim direnc"],
                "metin": (
                    "Ohm ilişkisi, birçok iletkende gerilim düşümünün akım ile direncin çarpımı olmasıdır. Direnç, akıma karşı konulan ölçüdür. "
                    "Kirchhoff akım kanunu, bir düğüme giren akımların toplamının çıkanlara eşit olmasıdır; yük birikmez. "
                    "Gerilim kanunu, kapalı bir çevrimde gerilim düşümlerinin cebirsel toplamının sıfır olmasıdır; enerji halkada kaybolmadan hesaplanır. "
                    "Seri kolda akım ortaktır, dirençler toplanır. Paralel kolda gerilim ortaktır, akımlar dallanır. "
                    "Bu eğitim modelidir. Ev tesisatı hesabı, sigorta seçimi ve şebekeye müdahale bu rafın konusu değildir."
                ),
            },
            {
                "id": "kondansator_bobin",
                "baslik": "kondansatör ve bobin",
                "aliases": ["kondansator", "kondansatör", "bobin", "induktor", "indüktör"],
                "metin": (
                    "Kondansatör elektrik alanında enerji biriktirir. İki iletken plaka arasına gerilim konunca yük ayrılır. Doğru akımda sürekli akım geçirmez, dolar ve akım kesilir. Değişen gerilimde akım sürer. "
                    "Bobin manyetik alanda enerji biriktirir. Akım değişince öz endüksiyon, değişime karşı gerilim üretir. Doğru akım kararlı olunca ideal bobin kısa devre gibi durur. "
                    "İkisi birlikte salınım yapabilir: enerji alanda ve manyetik alanda gidip gelir. Frekans, kapasite ve endüktansla belirlenir. "
                    "Bu not devre kurma talimatı değildir."
                ),
            },
            {
                "id": "alternatif_akim",
                "baslik": "alternatif akım",
                "aliases": ["alternatif akim", "alternatif akım", "etkin deger", "etkin değer"],
                "metin": (
                    "Alternatif akım, yönü ve şiddeti periyotla değişen akımdır. Sinüs modeli bir periyotta ortalaması sıfırdır; bu yüzden ısıtma etkisi ortalama ile değil karenin ortalamasının kökü ile anlatılır. Buna etkin değer denir. "
                    "Frekans saniyedeki çevrim sayısıdır. Faz, iki dalganın birbirine göre kaymasıdır. "
                    "Empedans, direnç ile bobin ve kondansatörün frekansa bağlı karşı koymasını birleştirir. "
                    "Şebeke gerilimine dokunmak, priz bağlamak veya pano açmak bu kartta yoktur."
                ),
            },
            {
                "id": "yariletken",
                "baslik": "yarıiletken",
                "aliases": ["yariletken", "yarıiletken", "diyot", "p-n eklemi", "pn eklemi"],
                "metin": (
                    "Yarıiletken, iletken ile yalıtkan arasında bir malzemedir; katkılama ile elektron veya boşluk çoğunluğu ayarlanır. "
                    "p-n eklemi, bu iki tipin birleştiği sınırdır. Bir yönde gerilim engeli alçaltır ve akım geçer; ters yönde engel büyür ve ideal modelde akım kesilir. Diyot bu tek yönlü davranışı kullanır. "
                    "Eşik, eklemin iletime geçtiği gerilim mertebesidir. Isı, taşıyıcı sayısını ve sızıntıyı değiştirir. "
                    "Transistörün anahtar modeli bilgisayar mühendisliği rafındadır. Bu not yonga üretme veya lehim talimatı değildir."
                ),
            },
            {
                "id": "sinyal_analog_sayisal",
                "baslik": "analog ve sayısal işaret",
                "aliases": ["analog sinyal", "sayisal sinyal", "sayısal sinyal", "ornekleme"],
                "metin": (
                    "Analog işaret zamanda sürekli bir büyüklüktür. Sayısal işaret, zamanı ve genliği basamaklara böler. "
                    "Örnekleme, sürekli işaretten belirli anlarda değer almaktır. Örnekler yeterince sıksa, bant sınırlı bir işaret yeniden kurulabilir; bu bir teorem çerçevesidir, her gürültülü kaydın sonsuz doğruluğu değildir. "
                    "Niceleme, genliği sonlu adıma yuvarlar ve hata ekler. Analog-sayısal çevirici bu iki işi yapar. "
                    "Bilgisayarın içinde bilgi sayısal düzeylerde tutulur; duyarga çoğu zaman önce analog görür."
                ),
            },
            {
                "id": "elektrik_guc",
                "baslik": "elektrik gücü",
                "aliases": ["elektrik gucu", "elektrik gücü", "watt nedir"],
                "metin": (
                    "Elektrik gücü, birim zamanda aktarılan enerjidir. Doğru akımda gerilim ile akımın çarpımıdır. Dirençte bu enerji ısıya döner. "
                    "Enerji, gücün zamanla birikmesidir. Verim, çıkan yararlı gücün giren güce oranıdır; kayıp çoğu zaman ısıdır. "
                    "Kaynak, yük ve hat birlikte düşünülür: hat direnci gerilim düşürür ve ısıtır. "
                    "Ev faturası, sigorta ve kablo kesiti seçmek bu kartın işi değildir."
                ),
            },
        ],
    },
    {
        "id": "astronomi_derin",
        "baslik": "Astronomi derin",
        "sira": 4,
        "neden": "Bilim rafındaki gök girişinin üstüne ölçme ve evrim.",
        "kavramlar": [
            {
                "id": "astronomi_derin",
                "baslik": "astronomi derin",
                "aliases": ["astronomi derin", "gokbilim derin", "gökbilim derin"],
                "metin": (
                    "Derin astronomi, gök cisimlerinin uzaklığını, ışığını ve zaman içindeki değişimini ölçer. Giriş kartı Güneş Sistemi ve galaksi adını söyler; bu raf paralaks, yıldız evrimi ve kırmızıya kaymayı açar. "
                    "Işık hem enerji taşır hem de uzak geçmişten gelir: uzağa bakmak geriye bakmaktır. "
                    "Uzaklık merdiveni paralakstan başlar, parlaklık ve kırmızıya kaymayla uzar. "
                    "Model, gözlemi açıklayana kadar hipotezdir. Burç yorumu astronomi değildir."
                ),
            },
            {
                "id": "paralaks",
                "baslik": "paralaks",
                "aliases": ["paralaks", "yildiz uzakligi", "yıldız uzaklığı", "parsek"],
                "metin": (
                    "Paralaks, gözlemci yer değiştirince yakın cismin uzak yıldızlara göre kaymasıdır. Dünya Güneş’in çevresinde dolanırken yakın yıldız küçük bir elips çizer. "
                    "Kayma açısı ne kadar küçükse yıldız o kadar uzaktır. Parsek, bir astronomi uzaklık birimidir ve bu açı ölçüsüne bağlanır. "
                    "Yöntem yakın yıldızlarda doğrudan çalışır. Daha uzağı için parlaklık, dönem-parlaklık ilişkisi ve kırmızıya kayma gibi bir merdiven kurulur. Her basamak bir öncekinin kalibrasyonuna bağlıdır."
                ),
            },
            {
                "id": "yildiz_evrimi",
                "baslik": "yıldız evrimi",
                "aliases": ["yildiz evrimi", "yıldız evrimi", "anakol", "beyaz cucce", "beyaz cüce"],
                "metin": (
                    "Yıldız, kütleçekimin sıkıştırdığı gazın merkezinde füzyonla enerji üreten bir küredir. Anakol, hidrojenin helyuma dönüştüğü uzun duraktır. "
                    "Kütle kaderi belirler. Güneş benzeri yıldız şişip gezegenimsi bulutsu bırakır ve beyaz cüceye döner. "
                    "Çok daha büyük yıldız çekirdeğini demire kadar yakar, süpernova ile dağılır; artığı nötron yıldızı veya karadelik olabilir. "
                    "Renk-parlaklık diyagramı bu durakları gözlemde ayırır. Ayrıntılı nükleer ağ bir ders kitabının tablosudur; burada yolun mantığı vardır."
                ),
            },
            {
                "id": "karadelik",
                "baslik": "karadelik",
                "aliases": ["karadelik", "kara delik", "olay ufku"],
                "metin": (
                    "Karadelik, belirli bir kütlenin olay ufku denen yüzeyi içinde ışığın dahi kaçamayacağı kadar sıkışmış halidir. Ufuk bir maddenin yüzeyi değil, kaçış hızının ışık hızına eşit olduğu sınırdır. "
                    "Dışarıdan bakınca ufka yaklaşan ışık kırmızıya kayar ve saat yavaşlar gibi görünür. İçerideki gözlemci için bu bir duvar hissi olmak zorunda değildir; model bunu ayırır. "
                    "Kütle, dönüş ve yük, dışarıdan ölçülebilen parametrelerdir. Galaksi merkezlerinde büyük kütleli karadelikler yıldız hareketleriyle tartılır. "
                    "Bu not bilimkurgu senaryosu değildir."
                ),
            },
            {
                "id": "kirmiziya_kayma",
                "baslik": "kırmızıya kayma",
                "aliases": ["kirmiziya kayma", "kırmızıya kayma", "genisleme", "genişleme", "buyuk patlama modeli"],
                "metin": (
                    "Kırmızıya kayma, ışığın dalga boyunun uzamasıdır. Bir kısmı kaynak ile gözlemcinin birbirinden uzaklaşmasıdır. Kozmolojik kayma, uzayın kendisinin genişlemesinden gelir; galaksi uzayda bir kurşun gibi kaçmak zorunda değildir, aradaki ölçek büyür. "
                    "Uzak galaksilerde kayma genelde daha büyüktür. Bu, evrenin genişlediği gözlemin omurgasıdır. "
                    "Büyük Patlama modeli, bu genişlemeyi geri sardığında sıcak ve yoğun bir başlangıç hali tarif eder. Model, tek bir andın romanı değil, gözlenen ışık ve element oranlarıyla sınanan bir çerçevedir."
                ),
            },
            {
                "id": "gezegen_olusumu",
                "baslik": "gezegen oluşumu",
                "aliases": ["gezegen olusumu", "gezegen oluşumu", "on gezegen diski", "ön gezegen diski"],
                "metin": (
                    "Yıldız oluşurken çevresinde gaz ve toz diski kalır. Toz taneleri çarpışıp büyür, gezegencikler olur. "
                    "Kar çizgisinin içinde kayalık, dışında buz ve gaz birikmesi kolaylaşır; Güneş Sistemi’ndeki iç kayalık ve dış dev gezegen ayrımı bu çerçeveyle anlatılır. "
                    "Disk dağılınca büyüme yavaşlar. Başka yıldızların çevresinde bulunan gezegenler bu modelin yalnız Güneş’e özgü olmadığını gösterir. "
                    "Burçlar ve kişilik yorumu bu rafda yoktur."
                ),
            },
        ],
    },
    {
        "id": "jeoloji",
        "baslik": "Jeoloji",
        "sira": 5,
        "neden": "Coğrafyanın yer şeklinin altındaki taş ve zaman bilimi.",
        "kavramlar": [
            {
                "id": "levha_tektonigi",
                "baslik": "levha tektoniği",
                "aliases": ["levha tektonigi", "levha tektoniği", "plaka tektonigi", "plaka tektoniği"],
                "metin": (
                    "Levha tektoniği, yer kabuğunun ve üst manto parçasının büyük levhalar halinde hareket etmesidir. Motor, mantodaki ısı akışı ve levhanın kendi ağırlığıdır. "
                    "Iraksak sınırda levhalar ayrılır, yeni kabuk oluşur. Yakınsak sınırda biri diğerinin altına dalabilir; sıradağ ve derin deprem buna bağlıdır. "
                    "Doğrultu atımlı sınırda levhalar yan yana kayar. Deprem, biriken gerilmenin kırılmasıdır. Volkan, eriyiğin yüzeye çıkmasıdır; her sınırda aynı şekilde görülmez. "
                    "Kıtaların uyumu ve okyanus tabanındaki manyetik şeritler bu modelin gözlemleridir."
                ),
            },
            {
                "id": "kaya_dongusu",
                "baslik": "kaya döngüsü",
                "aliases": ["kaya dongusu", "kaya döngüsü", "magmatik", "metamorfik", "tortul kaya"],
                "metin": (
                    "Kaya döngüsü, taşın bir türden diğerine dönüşmesidir. Magmatik kaya, eriyiğin soğumasıdır; derinde yavaş soğursa iri kristal, yüzeyde hızlı soğursa ince kristal oluşur. "
                    "Tortul kaya, aşınan parçaların taşınması, çökelmesi ve sıkışmasıyla oluşur. Metamorfik kaya, katı halde ısı ve basınçla mineral dokusunun değişmesidir. "
                    "Aşınma ve ergime döngüyü kapatır. Mineral, belirli bileşimi ve iç düzeni olan katıdır; kaya çoğu zaman minerallerin karışımıdır."
                ),
            },
            {
                "id": "sismik_dalga",
                "baslik": "sismik dalga",
                "aliases": ["sismik dalga", "p dalgasi", "p dalgası", "s dalgasi", "s dalgası"],
                "metin": (
                    "Deprem dalgaları yerin içini yoklar. P dalgası sıkışıp gevşeyerek ilerler, katı ve sıvıdan geçer, daha hızlıdır. "
                    "S dalgası kayma hareketidir, sıvıdan geçmez, daha yavaştır. S dalgasının dış çekirdekte kesilmesi, o katmanın sıvı davrandığının kanıtıdır. "
                    "Yüzey dalgaları yerin üstünde daha yavaş ve yıkıcı olabilir. İstasyonlara varış farkı, odağı üçgenlemeye yarar. "
                    "Bu not deprem tahmini vaadi veya yapı denetimi değildir."
                ),
            },
            {
                "id": "stratigrafi",
                "baslik": "stratigrafi",
                "aliases": ["stratigrafi", "superpozisyon", "süperpozisyon", "fosil yas"],
                "metin": (
                    "Stratigrafi, katmanların sırasından zaman okumaktır. Bozulmamış bir istifte alttaki katman üsttekinden önce çökelmiştir. "
                    "Kesilen katman, kesenden daha yaşlıdır. Fosil toplulukları uzak bölgeleri aynı zaman dilimine bağlar. "
                    "Radyometrik yaş, bazı minerallerde bozunan izotopun oranından sayısal süre verir; bağıl sıra ile birlikte okunur. "
                    "Tek bir fosil, bütün bir dağın yaşını bağlam olmadan bitirmez."
                ),
            },
            {
                "id": "mineral",
                "baslik": "mineral",
                "aliases": ["mineral nedir", "mohs", "mohs sertligi", "mohs sertliği"],
                "metin": (
                    "Mineral, doğal, çoğu zaman kristal iç düzeni olan, belirli kimyasal bileşimi bulunan katı bir maddedir. Kaya, bir veya birçok mineralin topluluğudur. "
                    "Sertlik, bir mineralin diğerini çizmesidir; Mohs dizisi bağıl bir merdivendir, mutlak basınç değeri değildir. "
                    "Renk yanıltabilir; aynı mineral katkıyla renk değiştirir. Çizgi rengi ve kırılım daha ayırt edicidir. "
                    "Maden işletme, değer biçme ve taş tedavisi bu kartta yoktur."
                ),
            },
            {
                "id": "ayrisma",
                "baslik": "ayrışma ve aşınma",
                "aliases": ["ayrisma", "ayrışma", "erozyon", "asinma"],
                "metin": (
                    "Ayrışma, kayanın yerinde parçalanmasıdır. Fiziksel ayrışma donma-çözülme ve sıcaklık farkıyla olur. Kimyasal ayrışma su ve asidin mineralleri çözmesidir. "
                    "Aşınma, parçanın su, buz, rüzgâr veya kütle hareketiyle taşınmasıdır. Çökelme, taşıyıcı yavaşlayınca parçanın birikmesidir. "
                    "Akarsu vadisi, buzul çizikleri ve kumul bu süreçlerin yer şeklidir. İklimin uzun dönem tanımı coğrafya rafındadır; burada taşın başına gelen vardır."
                ),
            },
        ],
    },
    {
        "id": "cevre_bilimleri",
        "baslik": "Çevre bilimleri",
        "sira": 6,
        "neden": "Jeoloji, coğrafya ve canlılığın ortak madde döngüsü.",
        "kavramlar": [
            {
                "id": "sera_etkisi",
                "baslik": "sera etkisi",
                "aliases": ["sera etkisi", "sera gazi", "sera gazı", "karbon dongusu"],
                "metin": (
                    "Güneş’in kısa dalga ışığı yeri ısıtır. Yer, daha uzun dalgayla enerji geri verir. Bazı gazlar bu uzun dalganın bir kısmını tutar ve atmosferi ısıtır; buna sera etkisi denir. Su buharı ve karbondioksit bu gazlardandır. Etki olmasa yer çok daha soğuk olurdu. "
                    "Karbon döngüsü, karbonun hava, canlı, toprak ve okyanus arasında dolaşmasıdır. Fosil yakıt, uzun süre gömülü karbonu kısa sürede havaya katar. "
                    "İklimin bölge bölge tanımı coğrafya rafındadır. Bu kart enerji dengesini anlatır; politika sloganı değildir."
                ),
            },
            {
                "id": "azot_dongusu",
                "baslik": "azot döngüsü",
                "aliases": ["azot dongusu", "azot döngüsü", "azot baglanmasi", "azot bağlanması"],
                "metin": (
                    "Havanın çoğu azottur ama canlılar onu doğrudan protein yapamaz. Bağlama, bazı bakterilerin ve endüstriyel sürecin azotu amonyağa çevirmesidir. "
                    "Nitrifikasyon amonyağı nitrata taşır. Bitki nitratı alır, hayvan bitkiden alır. Ayrıştırıcı organik azotu yeniden toprağa verir. Denitrifikasyon bir kısmını havaya döndürür. "
                    "Fazla gübre, suya azot taşır; yosun patlaması oksijeni tüketebilir. Döngü bozulunca etki yerelde kalmaz."
                ),
            },
            {
                "id": "biyocesitlilik",
                "baslik": "biyoçeşitlilik",
                "aliases": ["biyocesitlilik", "biyoçeşitlilik", "tur cesitliligi", "tür çeşitliliği"],
                "metin": (
                    "Biyoçeşitlilik, gen, tür ve ekosistem düzeyindeki çeşitliliktir. Tür sayısı tek başına yetmez; türlerin işlevi ve genetik açıklığı da sayılır. "
                    "Çeşitlilik, sistemin bir bozulmadan sonra toparlanma payıdır: bir tür gerilese işi gören başka bir tür kalabilir. "
                    "Yaşam alanı bölünmesi, yabancı tür ve aşırı avlanma çeşitliliği daraltır. Ekosistemin kısa tanımı bilim rafındadır; burada çeşitliliğin katmanları vardır. "
                    "Bu not bir tür listesi veya saha talimatı değildir."
                ),
            },
            {
                "id": "tasiyici_kapasite",
                "baslik": "taşıyıcı kapasite",
                "aliases": ["tasiyici kapasite", "taşıyıcı kapasite", "nufus ekolojisi"],
                "metin": (
                    "Taşıyıcı kapasite, bir ortamın bir canlı topluluğunu sürdürülebilir biçimde besleyebildiği düzeydir. Besin, su, alan ve atık sınırı birlikte belirler. "
                    "Nüfus bu düzeye yaklaşınca büyüme yavaşlar. Kapasite sabit değildir; iklim, teknoloji ve başka türler onu kaydırır. "
                    "Aşmak, kısa süre mümkün olur ve ardından çöküş veya göç gelebilir. İnsan için kapasite yalnız biyolojiden ibaret değildir; enerji ve atık da bağlar. "
                    "Bu bir kehanet sayısı değildir."
                ),
            },
            {
                "id": "kirlilik",
                "baslik": "kirlilik",
                "aliases": ["kirlilik nedir", "biyobirikim", "ötrofikasyon", "otrofikasyon"],
                "metin": (
                    "Kirlilik, bir maddenin veya enerjinin zarar verecek yoğunlukta yanlış yerde birikmesidir. Doz ve süre etkiyi belirler; her iz zarar demek değildir. "
                    "Ötrofikasyon, besinin suya aşırı girmesiyle alglerin çoğalıp çürümesi ve oksijenin düşmesidir. "
                    "Biyobirikim, bazı maddelerin canlı dokuda besin zinciri boyunca yoğunlaşmasıdır. "
                    "Hava, su ve toprak birbirine akar; bacadaki madde yağmurla toprağa iner. Arıtma, kaynağı kesmek ve seyreltmeyi ummak ayrı şeylerdir."
                ),
            },
            {
                "id": "surdurulebilirlik",
                "baslik": "sürdürülebilirlik",
                "aliases": ["surdurulebilirlik", "sürdürülebilirlik", "yenilenebilir kaynak"],
                "metin": (
                    "Sürdürülebilirlik, bir kullanımın kaynağı kendini yenileme hızının üstünde tüketmemesidir. Yenilenebilir kaynak, akış hızıyla kullanılırsa tükenmez; orman kesimi büyümeden hızlıysa yenilenebilir etiket yetmez. "
                    "Tükenen kaynak stoktur; kullanım onu azaltır. Atık da bir stoktur. "
                    "Üç ayak sık anılır: ekolojik sınır, geçim ve kurum. Biri çökerse diğerinin sloganı sistemi taşımaz. "
                    "Bu kart bir sertifika veya alışveriş listesi değildir."
                ),
            },
        ],
    },
    {
        "id": "anatomi_fizyoloji",
        "baslik": "Anatomi ve fizyoloji",
        "sira": 7,
        "neden": "Canlının yapısı ve işleyişi. Teşhis ve tedavi yoktur.",
        "kavramlar": [
            {
                "id": "doku_organ",
                "baslik": "doku ve organ",
                "aliases": ["doku nedir", "organ sistemi", "homeostazi", "homeostazi nedir"],
                "metin": (
                    "Anatomi yapıyı, fizyoloji işleyişi anlatır. Hücre yaşamın birimidir; kısa tanımı bilim rafındadır. Doku, benzer hücrelerin ortak işidir: örtü, bağ, kas ve sinir dokusu temel ayrımdır. "
                    "Organ, birkaç dokunun bir işlev için birleşmesidir. Sistem, organların ortak bir iş etrafında durmasıdır. "
                    "Homeostazi, iç ortamın dar bir aralıkta tutulmasıdır: sıcaklık, su, glikoz ve asitlik örnek verilir. Sapma olunca düzeltici halka çalışır. "
                    "Bu raf teşhis, ilaç, doz ve tedavi söylemez."
                ),
            },
            {
                "id": "dolasim",
                "baslik": "dolaşım",
                "aliases": ["dolasim sistemi", "dolaşım sistemi", "atar damar", "toplar damar"],
                "metin": (
                    "Dolaşım, kanı kapalı bir ağda hareket ettirir. Kalp bir pompadır; kasılıp gevşeyerek basınç farkı üretir. "
                    "Atardamar kanı kalpten uzağa, toplardamar kalbe doğru taşır. Kılcal damar, dokuyla madde değişiminin olduğu ince ağdır. "
                    "Akciğer dolaşımı kanı oksijenlenmeye götürür; sistemik dolaşım vücuda dağıtır. Kapakçıklar geri akışı engeller. "
                    "Bu yapı dersidir. Göğüs ağrısı, tansiyon veya ilaç bu kartın konusu değildir."
                ),
            },
            {
                "id": "solunum_sistemi",
                "baslik": "solunum sistemi",
                "aliases": ["solunum sistemi", "alveol", "alveol nedir", "gaz degisimi"],
                "metin": (
                    "Solunum sistemi havayı akciğere taşır. Diyafram kasılınca göğüs hacmi artar, basınç düşer, hava girer. Gevşeyince hava çıkar. "
                    "Alveol, havanın kana komşu olduğu ince keseciktir. Oksijen kana, karbondioksit havaya geçer; geçiş basınç farkıyla olur. "
                    "Hücre solunumu ayrı bir kimyadır: besinden enerji çıkarırken oksijen kullanılır. Havalandırma ile hücre solunumu aynı kelime değildir. "
                    "Nefes egzersizi veya hastalık tarifi yoktur."
                ),
            },
            {
                "id": "sinir_sistemi",
                "baslik": "sinir sistemi",
                "aliases": ["sinir sistemi", "noron", "nöron", "merkezi sinir"],
                "metin": (
                    "Sinir sistemi bilgiyi hızla taşır. Merkezi kısım beyin ve omuriliktir. Çevresel kısım, organlara giden sinirlerdir. "
                    "Nöron, uyarıyı zarındaki elektrik değişimi ve uçtaki kimyasal aktarımla iletir. Sinaps, iki hücrenin buluştuğu aralıktır. "
                    "Duyu, içeri haber getirir. Motor yol, kasa emir götürür. Refleks, bazı uyarılarda beyni beklemeden omurilikte dönen kısa halkadır. "
                    "Bu not ruh hali teşhisi, nöbet veya ilaç anlatmaz."
                ),
            },
            {
                "id": "sindirim",
                "baslik": "sindirim",
                "aliases": ["sindirim sistemi", "sindirim nedir", "emilim"],
                "metin": (
                    "Sindirim, besini kana geçebilecek küçüklüğe indirmektir. Ağızda mekanik parçalama ve tükürük başlar. Mide asit ve enzimle proteine çalışır. "
                    "İnce bağırsak sindirimin ve emilimin ana yeridir; yüzey kıvrımlarla genişler. Kalın bağırsak suyu geri alır. Karaciğer ve pankreas salgılarıyla bu işe katılır. "
                    "Emilim, küçük moleküllerin kana veya lenfe geçmesidir. "
                    "Diyet listesi, zayıflama ve hastalık bu kartta yoktur."
                ),
            },
            {
                "id": "iskelet_kas",
                "baslik": "iskelet ve kas",
                "aliases": ["iskelet sistemi", "kas kasilmasi", "kas kasılması", "eklem"],
                "metin": (
                    "İskelet destekler, organı korur ve kasla birlikte hareket üretir. Kemik canlı dokudur; mineral sertlik, kolajen esneklik verir. Eklem, iki kemiğin buluşmasıdır; kıkırdak sürtünmeyi azaltır. "
                    "İskelet kası kirişle kemiğe tutunur. Kasılma, kas lifinin içindeki ipliklerin birbiri üzerinde kaymasıdır; kalsiyum ve enerji bu kaymayı başlatır. "
                    "Kas yalnız çekerek iş görür; bir eklemin iki yönü için karşıt kaslar vardır. "
                    "Kırık, ağrı ve idman programı bu notun dışındadır."
                ),
            },
        ],
    },
    {
        "id": "dilbilim",
        "baslik": "Dilbilim",
        "sira": 8,
        "neden": "Türkçe yazım rafının üstünde, dilin kendisinin bilimi.",
        "kavramlar": [
            {
                "id": "sesbilim",
                "baslik": "sesbilim",
                "aliases": ["sesbilim", "fonem", "fonetik", "sesbirim"],
                "metin": (
                    "Fonetik, sesin fiziksel üretimini inceler: ciğer havası, ses telleri, ağız boşluğu. Sesbilim, o seslerden hangisinin dilde anlam farkı yarattığını ayırır. "
                    "Fonem, anlam değiştiren en küçük ses birimidir. Almanca veya Türkçede ayrı fonem olan bir karşıtlık başka dilde duyulmayabilir. "
                    "Allophone, aynı fonemin bağlama göre değişen sesleridir; konuşmacı onları ayrı harf saymaz. "
                    "Yazım kuralları Türkçe rafındadır. Burada ses ile harf aynı şey değildir."
                ),
            },
            {
                "id": "bicimbilim",
                "baslik": "biçimbilim",
                "aliases": ["bicimbilim", "biçimbilim", "morfem", "eklemeli dil"],
                "metin": (
                    "Biçimbilim, kelimenin iç yapılarını inceler. Morfem, anlam veya görev taşıyan en küçük parçadır. Kök sözlük anlamını, ek görevini taşır. "
                    "Çekim eki, kelimeyi cümledeki yerine uydurur. Yapım eki, yeni kelime türü veya anlam üretebilir. "
                    "Eklemeli dillerde ekler art arda dizilir; Türkçe bu tipe örnektir. Bükümlü dillerde parça daha çok içten değişir. "
                    "Aynı ek her dilde aynı işi görmez. Bu not imla düzeltmesi değildir."
                ),
            },
            {
                "id": "sozdizim",
                "baslik": "sözdizim",
                "aliases": ["sozdizim", "sözdizim", "cumle yapisi", "cümle yapısı"],
                "metin": (
                    "Sözdizim, kelimelerin cümlede hangi kuralla dizildiğini inceler. Öbek, birlikte davranan kelime grubudur: bir tamlayan ile tamlanan tek birim gibi yer değiştirir. "
                    "Özne ve yüklem birçok dilde cümlenin omurgasıdır. Sözcük sırası dilden dile değişir; Türkçede temel düzen özne-nesne-yüklem diye anılır, vurgu sırayı esnetebilir. "
                    "Dilbilgisi yargı cümlesi, konuşmacının iç kuralıdır; yazım kılavuzu ise toplumsal uzlaşıdır. İkisi karıştırılınca her devrik cümle hata sanılır."
                ),
            },
            {
                "id": "anlambilim_edimbilim",
                "baslik": "anlambilim ve edimbilim",
                "aliases": ["anlambilim", "edimbilim", "soz eylem", "söz eylem"],
                "metin": (
                    "Anlambilim, ifadelerin bağlama girmeden önceki anlamını inceler: sözcük anlamı, eş anlam, karşıt anlam, doğru veya yanlış olabilen önerme. "
                    "Edimbilim, aynı cümlenin kim, kime, nerede söylediğinde ne iş gördüğünü inceler. «Pencere açık» bir tespit de olabilir, kapatma isteği de. "
                    "Söz eylem, söylemenin bir iş yapmasıdır: söz vermek, ad koymak, ilan etmek. "
                    "Anlam yalnız sözlükte durmaz. Bu not bir konuşma hilesi değildir."
                ),
            },
            {
                "id": "dil_ailesi",
                "baslik": "dil ailesi",
                "aliases": ["dil ailesi", "karsilastirmali dilbilim", "karşılaştırmalı dilbilim", "turk dilleri"],
                "metin": (
                    "Dil ailesi, ortak bir atadan düzenli ses değişimleriyle ayrılmış dillerin grubudur. Karşılaştırmalı yöntem, akraba kelimelerdeki ses eşleşmelerini arar. "
                    "Tesadüf veya ödünç alma, akrabalığı taklit edebilir; yöntem bunları ayırmaya çalışır. "
                    "Türk dilleri kendi ailesini kurar. Komşu dilden geçen kelime, aileyi değiştirmez. "
                    "Yazı, dilin kendisi değildir; aynı dil birden çok alfabe görmüş olabilir. Bu not bir soy ağacı politikası değildir."
                ),
            },
            {
                "id": "edinim",
                "baslik": "dil edinimi",
                "aliases": ["dil edinimi", "anadil edinimi", "ikinci dil"],
                "metin": (
                    "Ana dil edinimi, çocuğun çevresindeki dili kural hale getirmesidir. Taklit tek başına yetmez; çocuk duymadığı biçimleri de kurar ve sonra düzeltir. "
                    "Girdi gerekli, ama girdi bir ders kitabı sırasıyla gelmez. İkinci dil, kurulu bir sistemin yanına yenisini eklemektir; ana dildeki alışkanlık hem yardım hem engel olur. "
                    "Yetişkin kuralı bilinçle öğrenebilir, sesi çocuk kadar kendiliğinden oturtamayabilir. "
                    "Bu not bir kurs vaadi veya zekâ ölçüsü değildir."
                ),
            },
        ],
    },
    {
        "id": "muzik",
        "baslik": "Müzik",
        "sira": 9,
        "neden": "Sesin zaman ve yükseklik düzeni. Nota defteri kopyası yok.",
        "kavramlar": [
            {
                "id": "nota_aralik",
                "baslik": "nota ve aralık",
                "aliases": ["nota nedir", "muzik araligi", "müzik aralığı", "oktav"],
                "metin": (
                    "Nota, bir sesin yüksekliğini ve süresini işaret eden semboldür. Yükseklik, sesin frekansıyla ilişkilidir; iki kat frekans kulağa aynı sınıfın bir oktav üstü gibi gelir. "
                    "Aralık, iki yükseklik arasındaki mesafedir. Bazı aralıklar birçok müzik dilinde kararlı duyulur, bazıları gerilim gibi durur. "
                    "Tını, aynı yükseklikte keman ile neyin ayrılmasıdır; dalganın üst tonları bunu belirler. "
                    "Bu kart bir eser notası veya şarkı sözü değildir."
                ),
            },
            {
                "id": "olcek_makam",
                "baslik": "ölçek ve makam",
                "aliases": ["makam", "majör olcek", "majör ölçek", "dizisel muzik"],
                "metin": (
                    "Ölçek, bir oktav içine dizilmiş yükseklik basamaklarıdır. Majör ve minör, Batı pratiğinde iki temel dizidir; aralarındaki yarım ses yerleri rengi değiştirir. "
                    "Makam, bir dizi ile birlikte o dizide hangi perdenin durak, hangi perdenin güç olduğunu ve seyirin nasıl yürüdüğünü de söyler. Türk sanat müziğinde makam bu zenginliği taşır. "
                    "Aynı notalar farklı makamda başka merkez hissi verir. "
                    "Bu not bir icra metodu veya kayıtlı eser değildir."
                ),
            },
            {
                "id": "ritim_olcu",
                "baslik": "ritim ve ölçü",
                "aliases": ["ritim", "olcu muzik", "ölçü müzik", "usul"],
                "metin": (
                    "Ritim, seslerin ve susların zaman içindeki dizilişidir. Vuruş, hissedilen nabızdır. Ölçü, vurşuları güçlü ve zayıf diye gruplar. "
                    "Usul, özellikle Türk müziğinde bu kalıbın adıdır; aksak usuller eşit ikiliye bölünmeyen gruplar kurar. "
                    "Tempo, nabzın hızıdır. Ritimsiz bir melodi yükseklik taşır ama yürüyüş taşımaz. Sus da ritmin parçasıdır. "
                    "Dans adımı veya metronom ayarı bu kartta tarif edilmez."
                ),
            },
            {
                "id": "armoni",
                "baslik": "armoni",
                "aliases": ["armoni", "akor", "uc ses", "üç ses"],
                "metin": (
                    "Armoni, aynı anda duyulan seslerin ilişkisiyle ilgilenir. Üç ses, bir temel üzerine üçlü aralıklarla kurulan akordur. "
                    "Kararlı akor durağan, gerilimli akor çözüm bekler gibi duyulur. Bu beklenti kültüre ve dinleyenin alışkanlığına bağlıdır; evrensel bir fizik kanunu diye sunulmaz. "
                    "Çok seslilik, bağımsız çizgilerin birlikte yürümesidir; homofoni bir melodinin akorla taşınmasıdır. "
                    "Bu not bir şarkının akor şeması değildir."
                ),
            },
            {
                "id": "muzik_form",
                "baslik": "müzik formu",
                "aliases": ["muzik formu", "müzik formu", "motif", "frase"],
                "metin": (
                    "Form, eserin zaman içindeki mimarisidir. Motif, tanınan en küçük müzikal fikirdir. Cümle, motiflerin nefes alacak kadar bir araya gelmesidir. "
                    "Tekrar, karşıtlık ve geliştirme formun üç temel hareketidir. A-B-A, bir fikrin uzaklaşıp dönmesidir. "
                    "Dinleyici formu fark etmeden de hisseder; analiz onu adlandırmaktır. Tekrar ile karşıtlık formu ayakta tutar. "
                    "Belirli bir bestenin çözümü ve nota kopyası bu rafta yoktur."
                ),
            },
            {
                "id": "muzik_akustik",
                "baslik": "müzik akustiği",
                "aliases": ["muzik akustigi", "müzik akustiği", "rezonans", "üst ton"],
                "metin": (
                    "Tel veya hava sütunu, belirli boylarda titreşmeyi sever; bunlara rezonans denir. Temel frekans yükseklik hissini verir. Üst tonlar, temel frekansın katlarıdır ve tınıyı kurar. "
                    "İnsan kulağı logaritmik bir aralıkta duyar: eşit çarpımlar eşit aralık gibi gelir. "
                    "Oda, yansımayla sesi uzatır; yankı süresi müziğin seçtiği hızı etkiler. Kuru oda ritmi net, canlı oda akoru uzatır. "
                    "Enstrüman yapım ölçüsü ve stüdyo tarifi bu kartta yoktur."
                ),
            },
        ],
    },
    {
        "id": "sosyoloji",
        "baslik": "Sosyoloji",
        "sira": 10,
        "neden": "Toplumun kurum ve eşitsizlik düzeni. İkna hilesi yok.",
        "kavramlar": [
            {
                "id": "toplumsal_kurum",
                "baslik": "toplumsal kurum",
                "aliases": ["toplumsal kurum", "sosyal kurum", "sosyoloji nedir"],
                "metin": (
                    "Sosyoloji, insanların birlikte yaşarken kurduğu düzeni inceler. Kurum, tekrarlanan bir ihtiyacı karşılayan kalıp bütündür: aile, eğitim, ekonomi, din, siyaset örnek verilir. "
                    "Kurum kişiden uzun ömürlüdür; kişi değişir, kalıp sürer. Kurumlar birbirini sınırlar: okul ile iş piyasası aynı insanı farklı ister. "
                    "Bu inceleme, bir grubu yüceltmek veya dağıtmak için değildir."
                ),
            },
            {
                "id": "norm_rol",
                "baslik": "norm ve rol",
                "aliases": ["toplumsal norm", "toplumsal rol", "sosyal rol"],
                "metin": (
                    "Norm, bir durumda neyin uygun sayıldığının paylaşılmış beklentisidir. Yaptırım, norma uymayanın gördüğü karşılıktır; ayıplamadan hukuka kadar değişir. "
                    "Rol, bir konumun beklenen davranış paketidir. Aynı kişi birden çok rol taşır; çatışma, iki rolün aynı anda ayrı şey istemesidir. "
                    "Statü, konumun toplumdaki yeridir. Kazanılmış statü çabayla, verilmiş statü doğumla gelir; sınır her toplumda aynı değildir. "
                    "Bu not insan yönetme tekniği değildir."
                ),
            },
            {
                "id": "tabakalasma",
                "baslik": "tabakalaşma",
                "aliases": ["tabakalasma", "tabakalaşma", "sosyal esitsizlik", "sosyal eşitsizlik"],
                "metin": (
                    "Tabakalaşma, toplumda mal, saygınlık ve gücün katmanlar halinde dağılmasıdır. Eşit olmayan dağılım her bilinen toplumda görülür; biçimi değişir. "
                    "Sınıf, çoğu zaman üretim ve gelirle anlatılır. Statü grubu saygınlıkla, parti ise örgütlü güçle ayrılır. "
                    "Hareketlilik, kişinin veya çocuğunun katman değiştirmesidir. Fırsat eşitliği ile sonuç eşitliği ayrı iddialardır. "
                    "Bu kart bir siyaset programı değildir."
                ),
            },
            {
                "id": "sosyallesme",
                "baslik": "sosyalleşme",
                "aliases": ["sosyallesme", "sosyalleşme", "toplumsalilesme"],
                "metin": (
                    "Sosyalleşme, kişinin toplumun dilini, normunu ve rolünü öğrenmesidir. Aile ilk çevredir; okul, arkadaş ve iş sonrakilerdir. "
                    "Birincil sosyalleşme çocuklukta kimliği kurar. İkincil sosyalleşme, yeni bir kuruma girince rol öğrenmektir. "
                    "Yeniden sosyalleşme, eski rolün bırakılıp yenisinin alınmasıdır; kurum değişince görülür. "
                    "Kişi yalnız kalıp değildir; normu da değiştirir. Bu not bir terbiye reçetesi değildir."
                ),
            },
            {
                "id": "sosyoloji_yontem",
                "baslik": "sosyoloji yöntemi",
                "aliases": ["sosyoloji yontemi", "sosyoloji yöntemi", "etnografya", "anket yontemi"],
                "metin": (
                    "Sosyoloji iddiayı yöntemle sınar. Anket, çok kişiden karşılaştırılabilir cevap toplar; sorunun nasıl kurulduğu cevabı kaydırır. "
                    "Etnografya, bir ortamda uzun süre kalarak anlamı yerinden anlamaya çalışır; genellemesi dardır, derinliği fazladır. "
                    "İstatistik ilişkiyi sayar, anlamı her zaman açıklamaz. Sayı ile hikâye birbirinin düşmanı değildir. "
                    "Yöntem, istediğin sonucu çıkarmak için seçilmez."
                ),
            },
            {
                "id": "toplumsal_degisim",
                "baslik": "toplumsal değişim",
                "aliases": ["toplumsal degisim", "toplumsal değişim", "modernlesme"],
                "metin": (
                    "Toplumsal değişim, kurumların ve normların zaman içinde kaymasıdır. Teknoloji, nüfus, fikir ve ekonomi birbirini iter. "
                    "Modernleşme, tek bir doğru yol diye sunulursa gözlemi ideolojiye çevirir. Farklı toplumlar aynı aleti farklı kuruma oturtur. "
                    "Değişim herkes için aynı hızda hissedilmez; katmanlar ayrı etkilenir. "
                    "Bu not bir çağın hüküm cümlesi değildir."
                ),
            },
        ],
    },
    {
        "id": "siyaset",
        "baslik": "Siyaset",
        "sira": 11,
        "neden": "Devlet, meşruiyet ve kuvvet. Seçim mühendisliği yok.",
        "kavramlar": [
            {
                "id": "devlet",
                "baslik": "devlet",
                "aliases": ["devlet nedir", "egemenlik", "mesruiyet", "meşruiyet"],
                "metin": (
                    "Devlet, belirli bir toprak üzerinde zor kullanma iddiasını kuran siyasal örgüttür. Egemenlik, o topraklarda son kararın kime ait olduğu iddiasıdır. "
                    "Meşruiyet, yönetilenlerin bu iddiayı haklı görmesidir. Korku ile rıza ayrı kaynaklardır; ikisi bir arada da bulunabilir. "
                    "Ulus, devlet ve hükümet aynı kelime değildir. Hükümet gelip gider, devlet örgütü daha uzun ömürlü tarif edilir. "
                    "Bu not bir rejim övgüsü veya devirme planı değildir."
                ),
            },
            {
                "id": "kuvvetler_ayriligi",
                "baslik": "kuvvetler ayrılığı",
                "aliases": ["kuvvetler ayriligi", "kuvvetler ayrılığı", "yasama yurutme", "yasama yürütme"],
                "metin": (
                    "Kuvvetler ayrılığı, yasa yapan, uygulayan ve uyuşmazlığı çözen işlevlerin aynı elde birleşmemesidir. Amaç, iktidarın kendini denetlemesidir. "
                    "Yasama kural koyar, yürütme uygular, yargı uyuşmazlıkta hükmeder. Fiiliyatta yürütme düzenleyici işlem de çıkarır; sınır anayasa ve denetime bağlıdır. "
                    "Ayrılık yoksa kuralı koyan, uygulayan ve kendi davasının hâkimi aynı kapı olur. "
                    "Bu kart bir ülke scoring’i değildir."
                ),
            },
            {
                "id": "demokrasi",
                "baslik": "demokrasi",
                "aliases": ["demokrasi nedir", "temsili demokrasi", "cogunluk yonetimi"],
                "metin": (
                    "Demokrasi, kamusal kararın yönetilenlerin katılımına dayandığı rejim ailesidir. Doğrudan biçim, kararın kendisine halkın oy vermesidir. Temsili biçim, karar için seçilenlere yetki vermektir. "
                    "Çoğunluk, azınlığın temel haklarını silebiliyorsa yalnız çoğunluk kuralı demokrasiyi tamamlamaz. "
                    "Seçim, ifade ve örgütlenme bu ailenin sık anılan şartlarıdır. Bir seçimin varlığı, şartların hepsinin işlediğini tek başına kanıtlamaz. "
                    "Kampanya yöntemi ve oy yönlendirme bu rafta yoktur."
                ),
            },
            {
                "id": "siyasal_temsil",
                "baslik": "siyasal temsil",
                "aliases": ["siyasal temsil", "secim sistemi", "seçim sistemi"],
                "metin": (
                    "Temsil, bir kişinin veya kurulun başkaları adına karar yetkisi taşımasıdır. Seçim sistemi, oyların sandalyeye nasıl çevrileceğinin kuralıdır. "
                    "Dar bölge, bir çevrede birinciyi öne çıkarır. Nispi temsil, oy oranını sandalye oranına yaklaştırmaya çalışır. İkisi farklı çoğunluk ve çeşitlilik üretir; ikisi de nötr bir doğa kanunu değildir. "
                    "Eşik, küçük grupları meclis dışında bırakabilir. "
                    "Nasıl kampanya yürütülür, bu notta yoktur."
                ),
            },
            {
                "id": "siyasal_ideoloji",
                "baslik": "siyasal ideoloji",
                "aliases": ["siyasal ideoloji", "ideoloji nedir"],
                "metin": (
                    "İdeoloji, toplumun nasıl düzenlenmesi gerektiğine dair birbirine bağlı inançlar kümesidir. İktidarı, mülkiyeti, eşitliği ve özgürlüğü farklı tartar. "
                    "Kavram haritası, bir tarafı haklı ilan etmek için değil, iddianın hangi varsayıma dayandığını görmek içindir. "
                    "Aynı kelime iki gelenekte ayrı anlama gelebilir. Etiket, programın yerine geçmez. "
                    "Bu raf propaganda metni üretmez."
                ),
            },
            {
                "id": "kamuoyu",
                "baslik": "kamuoyu",
                "aliases": ["kamuoyu", "kamuoyu nedir"],
                "metin": (
                    "Kamuoyu, kamusal bir meselede paylaşıldığı varsayılan görüşler toplamıdır. Tek bir ağız değildir; ölçüm, kimin sorulduğuna ve sorunun cümlesine bağlıdır. "
                    "Sessizlik, onay demek olmayabilir. Medya, hangi meselenin görünür olacağını seçerek gündemi kaydırır; görüşü her zaman tek yönlü üretmez. "
                    "Anket bir fotoğraftır, bir emir değildir. "
                    "Algı operasyonu ve seçmen yönlendirme tarifi yoktur."
                ),
            },
        ],
    },
    {
        "id": "ekonomi",
        "baslik": "Ekonomi",
        "sira": 12,
        "neden": "Kıtlık ve tercih. Yatırım tavsiyesi yok.",
        "kavramlar": [
            {
                "id": "firsat_maliyeti",
                "baslik": "fırsat maliyeti",
                "aliases": ["firsat maliyeti", "fırsat maliyeti", "kitlik", "kıtlık"],
                "metin": (
                    "Ekonomi, kıt kaynakların alternatif kullanımlar arasında nasıl seçildiğini inceler. Kıtlık, her isteğin aynı anda karşılanamamasıdır. "
                    "Fırsat maliyeti, bir şeyi seçince vazgeçilen en iyi ikinci seçenektir. Para harcaması sıfır olsa da süre ve dikkat tükeniyorsa maliyet vardır. "
                    "Teşvik, insanın o maliyete göre davranışını kaydıran ödüldür. İyi niyet, teşviki değiştirmezse sonucu değiştirmez. "
                    "Bu not kişisel bütçe danışmanlığı değildir."
                ),
            },
            {
                "id": "arz_talep",
                "baslik": "arz ve talep",
                "aliases": ["arz talep", "arz ve talep", "denge fiyati", "denge fiyatı"],
                "metin": (
                    "Talep, bir malın fiyatı düşünce genelde daha çok istenmesidir; başka her şey sabitken. Arz, fiyat yükseldikçe üreticinin daha çok sunmak istemesidir. "
                    "Denge fiyatı, istenen miktar ile sunulan miktarın karşılaştığı düzeydir. Fiyat bunun altındaysa kuyruk veya karne, üstündeyse stok birikir. "
                    "Talep kayması, fiyat dışındaki bir sebeple bütün eğrinin yer değiştirmesidir: gelir, zevk, başka malın fiyatı. "
                    "Model sadeleştirmedir. Bu kart al-sat tavsiyesi değildir."
                ),
            },
            {
                "id": "gsyh",
                "baslik": "gayri safi yurt içi hasıla",
                "aliases": ["gsyh", "gayri safi", "milli gelir"],
                "metin": (
                    "GSYH, bir ülkede belirli sürede üretilen nihai mal ve hizmetlerin piyasa değeridir. Ara mallar çift sayılmasın diye nihai satışa bakılır. "
                    "Büyüme, bu değerin fiyat etkisinden arındırılmış artışıdır. Kişi başına düşen değer, nüfusu böler. "
                    "GSYH refahın tamamı değildir: ev içi ücretsiz emek, çevre aşınması ve dağılım tek sayıda görünmez. Yüksek GSYH, herkesin aynı payı aldığı anlamına gelmez. "
                    "Bu bir tahmin raporu değildir."
                ),
            },
            {
                "id": "enflasyon",
                "baslik": "enflasyon",
                "aliases": ["enflasyon", "enflasyon nedir", "tuketici fiyat"],
                "metin": (
                    "Enflasyon, genel fiyat düzeyinin süregelen yükselmesidir. Tek bir malın pahalanması enflasyon olmak zorunda değildir. "
                    "Endeks, bir sepet malın fiyatının zamanla karşılaştırılmasıdır. Sepet, herkesin harcamasını birebir tutmayabilir. "
                    "Para, mal miktarından hızlı artarsa fiyat düzeyi üstünde basınç oluşur; arz şoku da aynı anda fiyatı iter. Sebep tek cümleyle kapanmaz. "
                    "Enflasyon borcu olan ile nakitte tutanı farklı etkiler. Bu not döviz veya faiz tavsiyesi değildir."
                ),
            },
            {
                "id": "para_politikasi",
                "baslik": "para ve maliye politikası",
                "aliases": ["para politikasi", "para politikası", "maliye politikasi", "maliye politikası"],
                "metin": (
                    "Para politikası, merkez bankasının para miktarı ve faiz üzerinden toplam harcamayı etkileme çabasıdır. Politika faizi, bankaların birbirine ve merkeze borçlanma maliyetini kaydırır. "
                    "Maliye politikası, devletin vergi ve harcamasıdır. Harcama artışı veya vergi indirimi talebi destekleyebilir; borç ve enflasyon sınırı bunu bedelsiz yapmaz. "
                    "İkisi aynı anda ayrı yönlere de çekebilir. Gecikme vardır: karar ile etki aynı gün gelmez. "
                    "Bu kart bir ülkeye reçete değildir."
                ),
            },
            {
                "id": "piyasa_basarisizligi",
                "baslik": "piyasa başarısızlığı",
                "aliases": ["piyasa basarisizligi", "piyasa başarısızlığı", "disaridan etki", "dışsallık"],
                "metin": (
                    "Piyasa, fiyat üzerinden birçok kararı koordine eder. Başarısızlık, fiyatın bir maliyet veya faydayı taşımadığı yerdir. "
                    "Dışsallık, bir işlemin tarafları dışında birine yük veya yarar binmesidir; bacanın komşuya dumanı böyledir. Kamu malı, birinin kullanmasının diğerini dışlamadığı ve bedavacılığın kolay olduğu maldır. "
                    "Tekel, tek satıcının miktarı kısarak fiyatı denge üstüne çekebilmesidir. "
                    "Müdahale de başarısız olabilir: yanlış vergi, aranan zararı büyütür. Bu not bir sektör tavsiyesi değildir."
                ),
            },
        ],
    },
    {
        "id": "hukuk",
        "baslik": "Hukuk",
        "sira": 13,
        "neden": "Norm, yetki ve uyuşmazlık. Avukatlık ve suç tarifi yok.",
        "kavramlar": [
            {
                "id": "hukuk_devleti",
                "baslik": "hukuk devleti",
                "aliases": ["hukuk devleti", "hukuk nedir", "norm hiyerarsisi"],
                "metin": (
                    "Hukuk, uyuşmazlığı ve yetkiyi önceden bilinebilir kuralla çözen norm düzenidir. Hukuk devleti, devletin de kendi koyduğu kuralla bağlı olmasıdır. "
                    "Normlar hiyerarşi kurar: anayasa üstte, kanun onun altında, yönetmelik daha altta diye öğretilir. Alt norm üstüne aykırı olamaz. "
                    "Keyfilik, kuralın olay olmadan önce bilinmemesi veya aynı olaya ayrı uygulanmasıdır. "
                    "Bu not bir dava dilekçesi veya hukuki mütalaa değildir."
                ),
            },
            {
                "id": "anayasa",
                "baslik": "anayasa",
                "aliases": ["anayasa nedir", "temel hak", "denetim yolu"],
                "metin": (
                    "Anayasa, devletin kuruluşunu ve kişinin temel haklarını düzenleyen üst hukuk metnidir. Yasama organı kanun çıkarırken bu çerçevede kalır. "
                    "Temel hak, kişinin devlet karşısındaki çekirdek güvenceleridir; sınırlanması da kural altındadır, sınırsız değildir. "
                    "Anayasa yargısı, bir kanunun anayasaya uygunluğunu denetleyen yoldur. Siyaset kuvvetlerin görevini, hukuk o görevin sınırını anlatır. "
                    "Bu kart bir ülkenin anayasa metninin yerine geçmez."
                ),
            },
            {
                "id": "borc_sozlesme",
                "baslik": "sözleşme",
                "aliases": ["sozlesme nedir", "sözleşme nedir", "borclar hukuku", "borçlar hukuku"],
                "metin": (
                    "Sözleşme, iki iradenin bir hukuki sonuç üzerinde birleşmesidir. Öneri, kabul edilince borç doğar. İrade sakatlığı, yanıltma, korkutma veya aşırı yararlanma hallerinde rızanın geçerliliği tartışılır. "
                    "Borç, bir edimi isteme hakkıdır. Alacaklı ister, borçlu yerine getirir. İfa, borcun gereği gibi yapılmasıdır. "
                    "Şekil, bazı sözleşmelerde yazılı veya resmi olmayı şart koşar; her anlaşma aynı kalıpta değildir. "
                    "Bu anlatım somut bir sözleşmenin hükmü değildir. Avukata danışmanın yerini tutmaz."
                ),
            },
            {
                "id": "ceza_ilkesi",
                "baslik": "ceza hukuku ilkesi",
                "aliases": ["ceza hukuku ilkesi", "kanunilik", "kusur ilkesi"],
                "metin": (
                    "Ceza hukuku, hangi fiilin suç sayılacağını ve yaptırımın şartını koyar. Kanunilik, suç ve cezanın işlenmeden önce yasada yazılı olmasını ister; sonradan çıkan yasayla geçmiş fiil suç sayılamaz. "
                    "Tipiklik, fiilin yasadaki tanıma uyup uymadığıdır. Hukuka aykırılık, bir izin veya hakkın o fiili örtmemesidir. Kusur, kişinin o fiil için kınanabilir olmasıdır. "
                    "Bu üçü birlikte aranır. Kart, bir fiilin nasıl işleneceğini anlatmaz. Suç itirafı veya savunma stratejisi de değildir."
                ),
            },
            {
                "id": "yargi_usul",
                "baslik": "yargılama",
                "aliases": ["yargilama", "yargılama", "adil yargilanma", "adil yargılanma"],
                "metin": (
                    "Yargılama, uyuşmazlığın bağımsız bir mahkeme önünde, tarafların iddia ve savunmasıyla çözülmesidir. "
                    "Adil yargılanma, haberdar olmayı, savunmayı, makul süreyi ve gerekçeli kararı içerir. İspat yükü, iddiayı ortaya koyana aittir; cezada şüphe sanık yararına okunur diye öğretilir. "
                    "Kesin hüküm, aynı uyuşmazlığın yeniden açılmasını sınırlar. Kanun yolu, hatalı kararı üst mahkemeye götürür. "
                    "Dilekçe örneği ve duruşma taktiği bu rafta yoktur."
                ),
            },
            {
                "id": "kamu_ozel_hukuk",
                "baslik": "kamu ve özel hukuk",
                "aliases": ["kamu hukuku", "ozel hukuk", "özel hukuk"],
                "metin": (
                    "Kamu hukuku, devletin örgütü ve kişiyle devlet arasındaki üstün yetkiyi düzenler: anayasa, idare, ceza bu yana çekilir. "
                    "Özel hukuk, kişilerin eşit sayıldığı ilişkileri düzenler: borç, eşya, aile buna örnektir. "
                    "Aynı olay iki yana da değebilir; bir sözleşme idareyle yapıldıysa kamu hukuku usulü de karışır. "
                    "Ayrım, hangi mahkemenin ve hangi ilkenin işe yarayacağını seçmek içindir. Somut dosya tavsiyesi değildir."
                ),
            },
        ],
    },
    {
        "id": "egitim_bilimleri",
        "baslik": "Eğitim bilimleri",
        "sira": 14,
        "neden": "Öğrenmenin ve müfredatın kendisi. Sınav hilesi yok.",
        "kavramlar": [
            {
                "id": "ogrenme_kuramlari",
                "baslik": "öğrenme kuramları",
                "aliases": ["ogrenme kurami", "öğrenme kuramı", "yapilandirmacilik", "yapılandırmacılık"],
                "metin": (
                    "Davranışçılık, öğrenmeyi gözlenen tepkinin pekişmesiyle açıklar. Bilişsel kuram, zihindeki şema ve işlemeyi öne çıkarır. "
                    "Yapılandırmacılık, kişinin yeni bilgiyi eski bilgisiyle kendisinin kurduğunu söyler; anlatmak tek başına öğrenme değildir. "
                    "Üçü de bir yanını görür: pekişme, anlam ve önceki bilgi birlikte çalışır. Tek kuramı din diye sunmak sınıfı eksik bırakır. "
                    "Bu not bir yöntem satışı değildir."
                ),
            },
            {
                "id": "mufredat",
                "baslik": "müfredat",
                "aliases": ["mufredat", "müfredat", "ogrenme hedefi", "öğrenme hedefi"],
                "metin": (
                    "Müfredat, neyin, hangi sırayla, hangi derinlikte öğretileceğinin tasarımıdır. Hedef, öğrencinin sonunda ne yapabildiğini söyler; konu listesi hedef değildir. "
                    "Hizalama, hedefin, dersin ve ölçmenin aynı şeye bakmasıdır. Derste anlatılmayan şeyin sınanması hizayı bozar. "
                    "Önkoşul, bir hedefin başka bir hedefe dayanmasıdır; matematik derin rafının istatistikten önce gelmesi bu mantığa örnektir. "
                    "Gizli müfredat, yazılmadan öğrenilen normdur: susmak, yarışmak, itaat. Onu görmezden gelmek programı eksik okur."
                ),
            },
            {
                "id": "olcme_degerlendirme",
                "baslik": "ölçme ve değerlendirme",
                "aliases": ["olcme degerlendirme", "ölçme ve değerlendirme", "formatif", "summatif"],
                "metin": (
                    "Ölçme, bir niteliği sayı veya kategoriye çevirmektir. Değerlendirme, o ölçüye bir ölçütle hüküm vermektir. "
                    "Biçimlendirici değerlendirme öğrenme sürerken verilir; amacı not değil, yolu düzeltmektir. Düzey belirleyici değerlendirme bir ünitenin sonunda düzeyi kaydeder. "
                    "Geçerlik, aracın ölçmek istediğini ölçmesidir. Güvenirlik, tekrarda benzer sonucu vermesidir. Güvenilir olup yanlış şeyi ölçen araç hâlâ geçersizdir. "
                    "Sınav sorusu sızdırmak veya ölçmeyi aldatmak bu rafın konusu değildir."
                ),
            },
            {
                "id": "pedagoji",
                "baslik": "pedagoji",
                "aliases": ["pedagoji", "pedagoji nedir", "iskele kurma"],
                "metin": (
                    "Pedagoji, öğretme sanatının ve bilgisinin adıdır. Yakınsak gelişim alanı, öğrencinin tek başına yapamadığı ama destekle yaptığı işlerin bandıdır. "
                    "İskele, o banttaki geçici destektir; iş öğrenilince destek çekilir. Destek hiç çekilmezse bağımlılık olur, hiç kurulmazsa öğrenci eşikte kalır. "
                    "Geri bildirim, neyin iyi gittiğini ve sonraki adımı söyler; yalnız puan geri bildirim değildir. "
                    "Bu not bir sınıf yönetim dayatması değildir."
                ),
            },
            {
                "id": "andragoji",
                "baslik": "andragoji",
                "aliases": ["andragoji", "yetiskin egitimi", "yetişkin eğitimi"],
                "metin": (
                    "Andragoji, yetişkin öğrenmesini çocuk öğretiminden ayıran çerçevedir. Yetişkin deneyim getirir; yeni bilgi o deneyimle çelişirse direnç normaldir. "
                    "Öğrenme, işine yarayacağı görülünce hızlanır. Zaman kıttır; saygı, hazır cevaptan önce deneyimin sorulmasıdır. "
                    "Yetişkin de temel beceri eksiği taşıyabilir; deneyim her konunun önkoşulunu otomatik vermez. "
                    "Bu kart bir koçluk vaadi değildir."
                ),
            },
            {
                "id": "egitimde_esitlik",
                "baslik": "eğitimde eşitlik",
                "aliases": ["egitimde esitlik", "eğitimde eşitlik", "firsat esitligi egitim"],
                "metin": (
                    "Fırsat eşitliği, başlangıç şartlarının öğrenmeye kapanmamasıdır. Sonuç eşitliği, herkesin aynı çıktıyı almasıdır; ikisi aynı iddia değildir. "
                    "Eşit davranmak, aynı engeli taşımayan öğrencilere aynı süreyi vermek olabilir ve yine de eşiği aşmalarını sağlamaz. Hakkaniyet, desteği ihtiyaca göre ayırmaktır. "
                    "Dil, gelir ve önceki okul bu farkı üretir. Ölçme, farkı görünmez sayarsa eşitsizliği meşrulaştırır. "
                    "Bu not bir okul politikası emri değildir."
                ),
            },
        ],
    },
]
