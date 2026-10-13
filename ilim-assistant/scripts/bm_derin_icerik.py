# -*- coding: utf-8 -*-
"""Bilgisayar mühendisliği — üst düzey ders notu.

Özgün eğitim metni. Telifli kitap aktarımı yok. Saldırı, exploit ve laboratuvar talimatı yok.
Anlık kart ile markdown aynı çekirdeği anlatır; markdown biraz daha açar.
"""
from __future__ import annotations

KATMAN = {
    "donanim_cekirdek": {
        "baslik": "Donanım çekirdeği",
        "kaynak_id": "bm_katman_donanim",
        "parcalar": [
            (
                "Sayısal mantık",
                "Sayısal devre bilgiyi iki kararlı düzeyde tutar; lojik 1 ve 0 birer gerilim aralığıdır, tek bir sonsuz kesin volt değildir. "
                "VE, ancak iki giriş de 1 ise 1 üretir. VEYA, en az biri 1 ise 1 üretir. DEĞİL biti tersler. "
                "Özel VEYA (XOR) girişler farklıysa 1 verir; toplayıcının toplam bitinde bu işe yarar. "
                "Kombinasyonel devrenin çıkışı yalnız o anki girişe bağlıdır: çoklayıcı, kod çözücü, toplayıcı böyledir. "
                "Sıralı devre geçmişi saklar. Mandallayıcı ve flip-flop, saat kenarında yazmaca yeni değeri alır. "
                "Kurulum süresi, verinin saat kenarından önce kararlı durması gereken aralıktır. Tutma süresi kenardan sonraki kısa aralıktır. "
                "Bu süreler ihlal edilirse yazmaç yarı kararlı bir ara değerde takılabilir. Not, bu süreyi bozma deneyi değildir.",
            ),
            (
                "İşlemci",
                "Merkezi işlem birimi bir komutu dört işte yürütür: getir, çöz, işlet, yaz. "
                "Program sayacı sıradaki komutun adresini tutar. Komut yazmacı getirilen sözcüğü saklar. "
                "Aritmetik-mantık birimi toplama, çıkarma ve karşılaştırmayı yapar. Denetim birimi, komutun işlem koduna göre hangi yazmaçların okunacağını ve sonucun nereye yazılacağını seçer. "
                "Klasik beş aşamalı iş hattı bu işleri üst üste bindirir: getir, çöz, yürüt, bellek, yaz. "
                "Bir komut yürütülürken sonrakiler önceki aşamalardadır. Saat, aşamaların ortak temposudur. "
                "Veri tehlikesi, bir komutun henüz yazılmamış sonucu okumasıdır. İletim (forwarding), sonucu yazmaç dosyasına inmeden sonraki aşamaya verir. "
                "Denetim tehlikesi, dalın gidileceği adres henüz belli değilken hattın yanlış yoldan komut getirmesidir. "
                "Yanlış tahminde o komutlar atılır. Hattın kazancı, tehlike ve ıskalama ile düşer. Bu anlatım yan kanal saldırısı tarif etmez.",
            ),
            (
                "Komut seti",
                "Komut seti mimarisi, yazılımın gördüğü sözleşmedir: komutlar, yazmaçlar, adresleme ve bayraklar. "
                "Yükle-depola düzeninde aritmetik yalnız yazmaçlar arasındadır; belleğe gitmek ayrı komuttur. "
                "Karmaşık komut düzeninde tek komut bellekteki işleneni de kullanabilir. "
                "Günümüzde bazı karmaşık setler, içeride daha küçük mikro işlemlere çözülür; programcı yine dış sözleşmeyi görür. "
                "Çağrı sözleşmesi, fonksiyon argümanının hangi yazmaçta duracağını ve dönüş adresinin nereye konacağını söyler. "
                "Derleyici yüksek dili bu sözleşmeye indirger. Aynı kaynak, başka sette yeniden derlenir. "
                "Taşınabilirlik kaynakta ve derleyicidedir; ham makine kodu sete bağlıdır.",
            ),
            (
                "Bellek hiyerarşisi",
                "Hiyerarşi hız ile kapasiteyi değiştirir: yazmaç, önbellek, ana bellek, kalıcı depolama. "
                "Üste çıkıldıkça erişim kısalır ve sığa düşer. Gerekçe yerelliktir. "
                "Zamansal yerellik: az önce kullanılan sözcük yine kullanılır. Uzamsal yerellik: komşusu da kullanılır. "
                "Önbellek bu yüzden tek sözcük değil, satır (blok) taşır. "
                "Doğrudan eşlemede bir ana bellek bloğunun gidebileceği tek satır vardır. Küme ilişkili önbellekte o kümede birkaç yol vardır; çakışma ıskası azalır. "
                "Iska türleri: ilk getiriş (zorunlu), sığa yetmemesi, aynı yere düşen blokların birbirini kovması. "
                "Yaz-geçir her yazmayı ana belleğe de geçirir. Geri yazım yazmayı önce önbellekte tutar, satır kirliyse kovulurken belleğe yazar. "
                "Iska olunca satır alt düzeyden dolar; işlemci o sırada bekleyebilir.",
            ),
            (
                "Veri yolu ve giriş-çıkış",
                "Veri yolu işlemci, bellek ve çevre birimleri arasında adres, veri ve denetim taşır. "
                "Adres hangi sözcüğün seçileceğini, veri içeriği, denetim oku-yaz ve hazır işaretini söyler. "
                "Bellek eşlemeli giriş-çıkışta aygıt yazmaçları adres uzayında sıradan bellek gibi görünür; özel bir komut gerekmez, adres aygıta aittir. "
                "Yoklama, işlemcinin aygıtın hazır bayrağını döngüde sormasıdır; basit ve işlemciyi meşgul eder. "
                "Kesme, aygıtın işlemciye «işin var» demesidir. İşlemci o anki durumu saklar, hizmet rutinine gider, sonra kaldığı yere döner. "
                "Doğrudan bellek erişimi, uzun bloğu sözcük sözcük işlemciden geçirmeden bellek ile aygıt arasında taşır; bitince kesme gelir. "
                "Bu not aygıtı ele geçirme yöntemi değildir.",
            ),
            (
                "Von Neumann",
                "Von Neumann makinesinde komutlar ve veriler aynı bellekte durur. Program sayacı sıradaki komut adresini tutar; her getirmeden sonra ilerler, dal bunu değiştirir. "
                "Programın kendisi de veridir: derleyici komut sözcüklerini belleğe yazar, işlemci onları çözer. "
                "Bedel, komut getirisi ile veri erişiminin aynı yolu paylaşmasıdır. İş hattı ikisini aynı anda isterse yol dar boğaz olur. "
                "Ayrı komut ve veri önbelleği bu sıkışmayı azaltır; model hâlâ depolanmış program modelidir. "
                "Harvard düzeni komut ve veriyi fiziksel olarak ayırır; birçok gömülü çekirdek ve önbellek katı bu fikri kullanır.",
            ),
        ],
    }
}

KAVRAMLAR = [
    {
        "id": "bilgisayar_muhendisligi",
        "baslik": "bilgisayar mühendisliği",
        "aliases": [
            "bilgisayar muhendisligi",
            "bilgisayar mühendisliği",
            "bilgisayar muhendisi",
            "bilgisayar mühendisi",
        ],
        "metin": (
            "Bilgisayar mühendisliği, sayısal devreyi, komut setini, bellek hiyerarşisini ve işletim çekirdeğini tek sistem olarak tasarlar. "
            "Donanım sözleşmesi komut setidir. Derleyici yüksek dili bu sözleşmeye indirger. Çekirdek, kullanıcı programına ayrıcalıklı işlemleri sistem çağrısı ile açar. "
            "Bu raf o katmanların mekanizmasını anlatır: iş hattı, önbellek, sanal bellek, dosya sistemi, veri yapıları ve sınanabilir tasarım. "
            "Giriş teknoloji kartı ayrıdır. Saldırı veya exploit tarifi yoktur."
        ),
        "kaynak_notu": "Bilgisayar mühendisliği — yol özeti.",
    },
    {
        "id": "sayisal_mantik",
        "baslik": "sayısal mantık",
        "aliases": ["sayisal mantik", "sayısal mantık", "dijital mantik", "dijital mantık", "mantik kapisi", "mantık kapısı"],
        "metin": (
            "Sayısal mantık bitleri kapılarla birleştirir. VE iki giriş de 1 ise 1 üretir; VEYA en az biri 1 ise 1; DEĞİL tersler. "
            "XOR girişler farklıysa 1 verir. Kombinasyonel devre bellek tutmaz; çoklayıcı ve toplayıcı böyledir. "
            "Sıralı devre flip-flop ile durum saklar ve saat kenarında güncellenir. "
            "Kurulum süresi verinin kenardan önce kararlı olması, tutma süresi kenardan sonra kısa süre bozulmamasıdır. "
            "İhlal, yazmacı yarı kararlı ara değere düşürebilir. Bu not o süreyi kasıtlı bozma deneyi değildir."
        ),
        "kaynak_notu": "Bilgisayar mühendisliği — sayısal mantık.",
    },
    {
        "id": "islemci",
        "baslik": "işlemci",
        "aliases": ["islemci", "işlemci", "merkezi islem birimi", "merkezi işlem birimi", "cpu nedir"],
        "metin": (
            "İşlemci komutu bellekten getirir, çözer, işletir ve sonucu yazar. Program sayacı sıradaki adresi tutar. "
            "Aritmetik-mantık birimi hesap ve karşılaştırma yapar; denetim birimi yazmaç seçimini yönetir. "
            "İş hattı getir, çöz, yürüt, bellek ve yaz aşamalarını üst üste bindirir. Saat bu aşamaların temposudur. "
            "Veri tehlikesinde sonuç henüz yazılmadan okunur; iletim sonucu erken taşır. "
            "Dalın hedefi geç belli olursa yanlış getirilen komutlar atılır. Bu anlatım yan kanal saldırısı içermez."
        ),
        "kaynak_notu": "Bilgisayar mühendisliği — işlemci.",
    },
    {
        "id": "komut_seti",
        "baslik": "komut seti",
        "aliases": ["komut seti", "komut seti mimarisi", "instruction set"],
        "metin": (
            "Komut seti, işlemcinin anladığı komutlar, yazmaçlar, adresleme ve bayraklardır. "
            "Yükle-depola düzeninde hesap yazmaçta yapılır, bellek erişimi ayrı komuttur. Karmaşık sette tek komut bellek işleneni de kullanabilir; içeride mikro işleme çözülebilir. "
            "Çağrı sözleşmesi argüman yazmacını ve dönüş adresini sabitler. Derleyici yüksek dili bu sözleşmeye indirger. "
            "Ham makine kodu sete bağlıdır; taşınabilirlik kaynak ve derleyici katmanındadır."
        ),
        "kaynak_notu": "Bilgisayar mühendisliği — komut seti.",
    },
    {
        "id": "bellek_hiyerarsisi",
        "baslik": "bellek hiyerarşisi",
        "aliases": ["bellek hiyerarsisi", "bellek hiyerarşisi", "onbellek", "önbellek", "cache bellek"],
        "metin": (
            "Hiyerarşi yazmaç, önbellek, ana bellek ve kalıcı depolamadır. Üst düzey hızlı ve küçüktür. "
            "Gerekçe yerelliktir: az önce kullanılan ve komşusu yine gerekir. Önbellek bu yüzden satır taşır. "
            "Doğrudan eşlemede bloğun tek yeri vardır; küme ilişkili önbellekte birkaç yol çakışmayı azaltır. "
            "Iska; zorunlu ilk getiriş, sığa, ya da aynı yere düşen blokların birbirini kovmasıdır. "
            "Geri yazım kirli satırı kovulurken belleğe yazar. Yaz-geçir her yazmayı belleğe de geçirir."
        ),
        "kaynak_notu": "Bilgisayar mühendisliği — bellek.",
    },
    {
        "id": "veri_yolu",
        "baslik": "veri yolu",
        "aliases": ["veri yolu", "adres yolu", "kesme nedir", "giris cikis", "giriş çıkış"],
        "metin": (
            "Veri yolu adres, veri ve denetim hatlarıyla işlemci, bellek ve aygıtı bağlar. "
            "Bellek eşlemeli giriş-çıkışta aygıt yazmaçları adres uzayındadır. "
            "Yoklama hazır bayrağını işlemcinin sormasıdır. Kesme, aygıtın işlemciyi haberdar etmesidir; durum saklanır, hizmet rutini çalışır, dönüşte kaldığı yer sürer. "
            "Doğrudan bellek erişimi uzun bloğu işlemciden sözcük sözcük geçirmeden taşır, bitince kesme gelir. "
            "Bu not aygıtı ele geçirme yöntemi değildir."
        ),
        "kaynak_notu": "Bilgisayar mühendisliği — veri yolu.",
    },
    {
        "id": "von_neumann",
        "baslik": "von Neumann mimarisi",
        "aliases": ["von neumann", "von neumann mimarisi", "depolanmis program", "depolanmış program"],
        "metin": (
            "Von Neumann makinesinde komut ve veri aynı bellektedir. Program sayacı sıradaki komut adresini tutar; dal onu değiştirir. "
            "Program da veridir: derleyici komut sözcüklerini belleğe yazar. "
            "Bedel, komut getirisi ile veri erişiminin aynı yolu paylaşmasıdır. Ayrı komut ve veri önbelleği bu dar boğazı azaltır. "
            "Harvard düzeni komut ve veriyi fiziksel olarak ayırır; birçok gömülü çekirdek bu ayrımı kullanır."
        ),
        "kaynak_notu": "Bilgisayar mühendisliği — von Neumann.",
    },
]

KATMANLAR = {
    "cevre_depolama_saat": {
        "baslik": "Çevre birimi, depolama, saat ve güç",
        "kaynak_id": "bm_katman_cevre",
        "faz": "16b",
        "parcalar": [
            (
                "Çevre birimi",
                "Çevre birimi işlemcinin dışındaki giriş-çıkış aygıtıdır: klavye, işaretçi, ekran, ağ arabirimi, disk denetleyicisi. "
                "Denetleyici, aygıtın elektriksel veya paket işaretini işlemcinin anlayacağı yazmaçlara çevirir. "
                "Sürücü, işletim çekirdeğinde bu yazmaçlara sistem çağrısı ardından dokunan yazılımdır. "
                "Bellek eşlemeli modelde program aygıta sıradan yükle-depola ile gider; adres aralığı aygıta ayrılmıştır. "
                "Kesme, aygıtın olayını işlemciye taşır. Doğrudan bellek erişimi, disk veya ağ tamponunu işlemciyi her sözcükte kesmeden doldurur. "
                "İşlemci transferin başında denetleyiciye adres ve uzunluk yazar, bitişte kesme alır. "
                "Bu not sürücü zaafı veya aygıt ele geçirme tarifi değildir.",
            ),
            (
                "Kalıcı depolama",
                "Kalıcı ortam güç kesilince veriyi tutar. Sabit diskte kafa plakanın üzerindeki izi arar; arama süresi mekanik gecikmedir, dönüş gecikmesi sektörün kafa altına gelmesini bekler. "
                "Ardışık okuma bu yüzden rasgele okumadan ucuzdur. "
                "Katı hal diski NAND hücresinde yük tutar. Okuma sayfa boyundadır. Silme ise daha büyük blok boyundadır; tek sayfayı yerinde değiştirmek için blok okunur, silinir, yeniden yazılır. "
                "Aşınma dengeleme, silme sayısını hücreler arasında yayar. Denetleyicinin çeviri katmanı mantıksal bloğu fiziksel sayfaya eşler ve çöp toplar. "
                "Dosya sistemi bu mantıksal blokların üstünde isim ve dizin kurar. Bu not bellenim kırma talimatı değildir.",
            ),
            (
                "Saat ve güç",
                "Saat darbesi sıralı elemanların aynı kenarda örneklemesini sağlar. Kritik yol, iki yazmaç arasında kombinasyonel gecikmesi en uzun yoldur. "
                "Azami frekans, bu yolun kurulum süresiyle birlikte bir periyoda sığmasıyla sınırlıdır. "
                "Anahtarlanan kapasitenin dinamik gücü, kabaca etkinlik çarpı kapasite çarpı gerilimin karesi çarpı frekanstır. Gerilim düşünce güç hızla düşer; frekans da doğrusal girer. "
                "Kaçak akım, anahtarlama olmasa da ısı üretir. Soğutma, yonganın güvenli sıcaklık penceresinde kalması içindir. "
                "Bu not frekans zorlama, gerilim yükseltme veya laboratuvar kurma talimatı değildir.",
            ),
        ],
    },
    "dayanak": {
        "baslik": "Mühendislik dayanağı",
        "kaynak_id": "bm_katman_dayanak",
        "faz": "16c",
        "parcalar": [
            (
                "Ayrık matematik",
                "Ayrık matematik sonlu veya sayılabilir nesnelerle uğraşır. Küme, elemanların sırasız topluluğudur. "
                "İlişki, iki kümenin kartezyen çarpımının alt kümesidir; «küçük veya eşit» bir sıralama ilişkisidir. "
                "Fonksiyon her elemana tam bir sonuç bağlar. Birebir ve örten fonksiyon tersinir. "
                "Tümevarım, bir taban adımı ve «n için doğruysa n+1 için doğrudur» adımıyla doğal sayılarda önermeyi taşır; döngü ve özyineleme doğruluğunda bu kalıp kullanılır. "
                "Çizge, düğüm ve kenardan oluşur. Ağaç, bağlantılı ve çevrimsiz çizgedir. "
                "Sayma, kaç farklı dizinin mümkün olduğunu söyler; karmaşıklık da adım sayısını girdi boyuna bağlar. "
                "Boolean cebir VE, VEYA, DEĞİL ile sayısal kapının cebiridir. Bu kart felsefedeki kıyas geleneğinin yerine geçmez.",
            ),
            (
                "Önerme mantığı",
                "Önerme doğru ya da yanlıştır. Atomik önerme daha küçüğe bölünmez. "
                "Değil, ve, veya, ise bağlaçları doğruluk tablosu ile tanımlanır. «İse» yalnız öncül doğru art bileşen yanlışken yanlıştır. "
                "Totoloji her atamada doğrudur. Çelişki her atamada yanlıştır. "
                "Sağlanabilir formül, en az bir atamada doğru olandır. "
                "Mühendislik bunu devre şartında ve program önkoşulunda kullanır. Bu kart felsefe rafındaki kıyas ve Organon çizgisini değiştirmez; doğruluk tablosu mühendislik aracıdır.",
            ),
            (
                "Transistör anahtar",
                "Sayısal CMOS kapıda transistör analog yükselteç gibi değil, anahtar gibi durur. "
                "Tersleyicide çekme-yukarı ağı çıkışı besleme gerilimine, çekme-aşağı ağı toprağa bağlar. Giriş 0 iken çıkış 1, giriş 1 iken çıkış 0 olur; ikisi birden iletimde kalmaz, statik akım idealleşmede yoktur. "
                "Lojik 1 ve 0, gürültü payı bırakılmış gerilim aralıklarıdır. Aralıkların arası yasak bölgedir; orada kapı kararsızdır. "
                "Eşik, anahtarın açıldığı gerilim mertebesidir. Bu not yonga üretme veya laboratuvar kurma talimatı değildir.",
            ),
        ],
    },
    "sistem_yazilim": {
        "baslik": "Sistem yazılımı",
        "kaynak_id": "bm_katman_sistem",
        "faz": "17",
        "parcalar": [
            (
                "Çekirdek ve sistem çağrısı",
                "İşletim çekirdeği ayrıcalıklı kipte çalışır: sayfa tablosunu, kesmeleri ve aygıt yazmaçlarını o kurar. "
                "Kullanıcı programı ayrıcalıksız kipte kalır; aygıta veya başka prosesin belleğine doğrudan gidemez. "
                "Sistem çağrısı kontrollü bir kapıdır. Program yazmaçlara çağrı numarasını ve argümanları koyar, bir tuzak komutu çalıştırır. "
                "İşlemci çekirdek kipine geçer, çağrı numarasına göre hizmeti yapar, sonucu yazıp kullanıcı kipine döner. "
                "Kısa «işletim sistemi donanımı yönetir» cümlesi teknoloji kartındadır. Bu not ayrıcalık sınırını ve tuzağı anlatır. "
                "Sınırı aşma yöntemi yoktur.",
            ),
            (
                "Proses ve iş parçacığı",
                "Proses, çalışan programın çekirdekteki kimliğidir: adres uzayı, açık dosya tablosu, durum, yazmaç bağlamı. "
                "Durumlar tipik olarak hazır, çalışıyor ve bekliyor diye ayrılır. Bekleyen proses bir olay (disk, kilit, zaman) olmadan işlemci almaz. "
                "Bağlam değiştirme, çalışan prosesin yazmaçlarını saklayıp diğerininkini yüklemektir; bunun bedeli önbellek sıcaklığının bozulmasıdır. "
                "Zamanlayıcı hazır kuyruğundan seçer. Öncelikli ve adil paylaştırma farklı amaçlardır: gecikme ile verim çelişebilir. "
                "İş parçacığı aynı adres uzayını ve dosya tablosunu paylaşan ayrı yürütme akışıdır. Yığınları ayrıdır. "
                "Kilit, paylaşılan veride aynı anda tek yazıcı olması içindir. "
                "Klasik kilitlenme modeli dört şart bir arada ister: karşılıklı dışlama, tut-ve-bekle, zorla bırakamama, döngüsel bekleme. "
                "Şarttan birini kırmak kilitlenmeyi o modelde engeller. Bu not kilit kırma veya yarışla sızma tarifi değildir.",
            ),
            (
                "Sanal bellek",
                "Sanal bellek her prosese kendi adres uzayını gösterir. İşlemcinin ürettiği adres sanaldır. "
                "Sayfa tablosu sanal sayfa numarasını fiziksel çerçeveye çevirir. Çok düzeyli tablo, seyrek adres uzayında boş üst düzeyleri tutmayarak yer kazandırır. "
                "TLB, son çevirilerin küçük ve hızlı kopyasıdır. TLB ıskasında tablo bellekte yürür. "
                "Sayfa bellekte yoksa sayfa hatası olur; çekirdek sayfayı diskten getirebilir veya prosesin yasadışı erişimini sonlandırır. "
                "Yer kalmazsa az kullanılan sayfa kovulur. Sürekli kovup geri getirmek (çöpe düşme) sistemi yavaşlatır. "
                "Koruma bitleri sayfanın okunup yazılacağını ve kullanıcı kipine açık olup olmadığını söyler. Aşma yöntemi bu notta yoktur.",
            ),
            (
                "Dosya sistemi",
                "Dosya sistemi mantıksal blokları isim, dizin ve üstveri ile sunar. "
                "Düğüm (inode) dosyanın sahibini, izinlerini, boyunu ve veri bloklarının adreslerini tutar. Dizin, isimden düğüm numarasına eşlemedir. "
                "Yol çözümleme kökten başlayıp dizin dizin iner. "
                "Günlük (journal), asıl veri yapılarını değiştirmeden önce niyeti kalıcı bir kayda yazar; çöküşte yarım kalan iş geri alınır veya tamamlanır. "
                "İzin, sahip ve grup için oku-yaz-çalıştır bitleridir. Bu not izin aşma veya disk kazıma yöntemi öğretmez.",
            ),
            (
                "Derleyici ve bağlayıcı",
                "Derleyici kaynak metni hedef komut setine indirger. Sözcük çözümleyici karakterleri atomlara böler. "
                "Ayrıştırıcı dilbilgisine göre sözdizimi ağacı kurar. Anlam çözümleme tipleri ve bildirimleri denetler. "
                "Ara gösterim, dile ve sete daha az bağlı bir biçimdir; iyileştirme burada sabit katlama, ölü kod ve döngü taşıması gibi dönüşümler yapar. "
                "Komut seçimi ve yazmaç ataması hedef sete iner. "
                "Bağlayıcı, ayrı derlenmiş nesne dosyalarındaki sembolleri çözer, kütüphaneyi yerleştirir, yeniden yerleme ile son adresleri yazar. "
                "Yorumlayıcı kaynak veya ara biçimi adım adım yürütür. Anında derleme, sıcak izi çalışma sırasında makine koduna çevirir. "
                "Bu not derleyiciyi kırma yöntemi değildir.",
            ),
            (
                "Ağ yığını",
                "Ağ yığını işi katmanlara böler ki üst katman altın her ayrıntısını bilmesin. "
                "Bağlantı katmanı bir halkada çerçeve taşır. Ağ katmanı adresler ve yönlendirir: paket bir sonraki sıçramaya gider. "
                "Taşıma katmanı uçtan uca teslimi üstlenir. TCP bayt akışını sıra numarası ve alındı ile izler; kayıp olursa yeniden gönderir. "
                "Pencere, karşı tarafın kabul edebileceği kadar göndererek akışı sınırlar. Tıkanıklık denetimi, ağın dolduğunu sezip hızı kısar. "
                "UDP datagram gönderir; sıra, alındı ve yeniden gönderim sözleşmesi yoktur, bu yüzden gecikmesi daha öngörülebilir olabilir ve kayıp uygulamaya yansır. "
                "Uygulama katmanı bu taşımanın üstünde web, posta veya ad çözümleme konuşur. "
                "Tarama, paket dövme veya saldırı tarifi yoktur.",
            ),
        ],
    },
    "veri_yapilari": {
        "baslik": "Veri yapıları ve algoritmalar",
        "kaynak_id": "bm_katman_veri",
        "faz": "18",
        "parcalar": [
            (
                "Veri yapısı",
                "Veri yapısı, veriyi bir erişim ve güncelleme sözleşmesiyle tutar. Sözleşme maliyetleri birlikte gelir. "
                "Dizi sürekli bellektedir. İndeksle erişim sabittir, çünkü adres taban artı indeks çarpı eleman boyudur. "
                "Ortaya eklemek kaydırmayı gerektirir; maliyet eleman sayısıyla büyür. "
                "Bağlı listede her düğüm değeri ve sonraki düğümün adresini tutar. Başı bilinirken ortaya veya başa eklemek sabittir. "
                "n’inci elemana gitmek n adım sürer; önbellek de düğümler dağınık olduğu için dizi kadar sıcak kalmaz. "
                "Seçim, erişim örüntüsüne göre yapılır: çok indeks varsa dizi, çok ekleme-silme ve az rasgele erişim varsa liste.",
            ),
            (
                "Yığın ve kuyruk",
                "Yığın son giren ilk çıkar. Push tepeye koyar, pop tepeden alır. İkisi de sabittir. "
                "Çağrı yığını fonksiyonun dönüş adresini, kaydedilen yazmaçları ve yerel değişkenleri çerçeve olarak tutar. Çağrı push, dönüş pop’tur. "
                "Derin özyineleme yığını büyütür; taşma o çerçevenin ayrılan sınırı aşmasıdır. Bu not taşmayı istismar etmeyi anlatmaz. "
                "Kuyruk ilk giren ilk çıkar. Üretici arkaya ekler, tüketici önden alır. "
                "Dairesel tampon, sabit dizide baş ve son indeksi ilerletir; dolduğunda üretici bekler. İşletim sistemindeki hazır kuyruğu ve G/Ç tamponu bu sözleşmedir.",
            ),
            (
                "Ağaç ve çizge",
                "Ağaç, kökü olan bağlantılı çevrimsiz çizgedir. Her düğümün tek ebeveyni vardır, kök hariç. "
                "İkili arama ağacında bir düğümün sol alt ağacı küçük, sağı büyüktür. Arama, her adımda bir yana iner. "
                "Ağaç zincire dönerse arama eleman sayısı kadar uzar. Dengeli ağaç yüksekliği logaritmik tutulur; dönüşler veya renk kuralları dengeyi onarır. "
                "Yığın (heap) tam bir ağaçtır ve ebeveyn çocuklardan küçük ya da eşittir; öncelik kuyruğunda kök en küçük elemandır. "
                "Çizge düğüm ve kenardan oluşur; kenar yönlü veya ağırlıklı olabilir. "
                "Genişlik öncelikli arama bir kaynaktan katman katman gider, ağırlıksız kenarda en kısa yolun kenar sayısını verir. "
                "Derinlik öncelikli arama bir dalı sonuna kadar iner, geri sarar. İkisi de her düğüm ve kenarı sabit kez ziyaret eder.",
            ),
            (
                "Karmaşıklık, sıralama, arama",
                "Algoritma sonlu, belirli adımlarla sonuca gider. Büyük-O, girdi n büyürken adım sayısının üst sınırıdır; sabit çarpanları ve küçük terimleri atar. "
                "İç içe tam tarama sık sık n kare mertebesine gider. Sıralı dizide ikili arama her adımda aralığı yarılar; adım sayısı logaritmiktir. Sıralı değilse bu garanti yoktur. "
                "Birleştirerek sıralama diziyi yarıya böler, yanları sıralar, birleştirir. En kötü durumda da n log n mertebesindedir ve ek bellek ister. "
                "Hızlı sıralama bir dayanak seçer, küçükleri sola büyükleri sağa ayırır, yanlarda yineler. Ortalama durumda n log n, dayanak hep uçta kalırsa n kareye düşer. "
                "Karşılaştırmalı sıralamanın en kötü durumda n log n’den iyi bir alt sınırı vardır; sayarak sıralama karşılaştırmadan kaçtığı için tam sayılarda doğrusal olabilir, ama değer aralığına bellek ayırır.",
            ),
            (
                "Hash tablosu",
                "Hash tablosu anahtarı bir fonksiyonla kova indisine indirger. İyi fonksiyon anahtarları kovalara dengeli yayar. "
                "Yük faktörü, eleman sayısının kova sayısına oranıdır. Zincirlemede aynı kovaya düşen anahtarlar listede durur; basit düzgün yayılım varsayımında ortalama zincir yük faktörü kadardır. "
                "Açık adreslemede çakışan anahtar tablonun başka bir boş gözüne kayar. Tablo dolunca ekleme pahalanır; büyütüp yeniden özetlemek maliyeti seyrekleştirir. "
                "Bu yapı sözlük ve küme içindir. Parola kırma, özet çarpıştırma veya güvenlik özeti kırma tarifi yoktur. "
                "Kriptografik özet ile tablo fonksiyonu aynı iş değildir; tablo fonksiyonu hız ve yayılım ister, gizlilik ispatı iddia etmez.",
            ),
        ],
    },
    "programlama_uzmanlik": {
        "baslik": "Programlama uzmanlığı",
        "kaynak_id": "bm_katman_uzmanlik",
        "faz": "19",
        "parcalar": [
            (
                "Tasarım",
                "Tasarım, değişme ihtimalini sınırlamaktır. Yüksek yapışkanlık: bir modülün parçaları tek bir işe hizmet eder. "
                "Düşük bağlaşım: modüller az ve dar arayüzle konuşur. "
                "Arayüz sözleşmedir; çağıran önkoşulu sağlar, çağrılan sonkoşulu. İç gösterim gizlenirse sözleşme bozulmadan iç değişir. "
                "Tek sorumluluk, bir değişme sebebinin tek modülü etkilemesidir. "
                "Erken soyutlama da borçtur: henüz ikinci kullanım yokken kurulan genel çerçeve okumayı zorlaştırır. "
                "Uygulama pratiği programlama motorundadır. Bu not kavramı öğretir.",
            ),
            (
                "Birim testi",
                "Birim testi, küçük bir parçayı dış dünyadan yalıtıp belirli girdiye belirli çıktı bekler. "
                "Düzen-uygula-doğrula: girdiyi kur, işlevi çağır, sonucu karşılaştır. "
                "Sınır değerler ortaya yakın değerden daha çok hata gösterir: boş koleksiyon, tek eleman, tam kapasite, sıfır, negatif. "
                "Önce başarısız test, sonra onu geçiren en küçük kod, sonra yeniden düzenleme. Test yokken yapılan düzenleme davranışı sessiz kaydırabilir. "
                "Test hata bulur; her doğru programı kanıtlamaz. Birim, entegrasyonun yerine geçmez: parçalar doğru olup birleşince protokolü bozabilir. "
                "Bu not güvenlik açığı tarayıcısı değildir.",
            ),
            (
                "Hata ayıklama",
                "Hata ayıklama bir hipotez işidir. Önce belirti yeniden üretilir; üretilmeyen hata ölçülemez. "
                "Beklenen ile gözlenen ayrılır. Hipotez, hangi ara değer yanlışsa belirtiyi açıklar. "
                "Daraltma, girdiyi veya kod bölgesini ikiye bölüp hangi yarıda bozulduğuna bakmaktır. "
                "Kesme noktası o andaki yazmaç ve değişkeni gösterir. Günlük, kesme koyamadığın yerde zaman sırasını bırakır. "
                "Bir anda çok şeyi değiştirmek hipotezi siler. Düzeltme, yeniden üreten test ile kalıcı olur. "
                "Bu yöntem güvenlik açığı aramak veya bellek bozmak için anlatılmaz.",
            ),
            (
                "Sürüm kontrolü",
                "Sürüm kontrolü dosya ağacının anlık görüntülerini ve onları kim, neden değiştirdiğini saklar. "
                "Kayıt (commit) bir görüntüdür. Not, ne değiştiğini değil neden değiştiğini söyler. "
                "Dal, ana çizgiden ayrılan bir uçtur; deneme ana çizgiyi bozmaz. "
                "Birleştirme iki ucun değişikliklerini ortak atadan beri uygular. Aynı satır iki uçta değiştiyse çakışma elle çözülür. "
                "Geçmişi yeniden yazmak yayımlanmış ucu başkalarının kaydından koparır; yerel denemede kullanılabilir, paylaşılan dalda gerekçe ister. "
                "Bu not depo ele geçirme yöntemi değildir.",
            ),
        ],
    },
}

KAVRAMLAR_YENI = [
    KAVRAMLAR[0],
    {
        "id": "cevre_birimi",
        "baslik": "çevre birimi",
        "aliases": ["cevre birimi", "çevre birimi", "giris aygiti", "giriş aygıtı", "disk denetleyicisi"],
        "metin": (
            "Çevre birimi işlemcinin dışındaki giriş-çıkış aygıtıdır. Denetleyici, aygıt işaretini yazmaçlara çevirir. "
            "Sürücü bu yazmaçlara çekirdek içinden gider. Bellek eşlemeli modelde aygıt adres uzayındadır. "
            "Kesme olayı işlemciye taşır. Doğrudan bellek erişimi uzun bloğu işlemciyi her sözcükte meşgul etmeden taşır; bitişte kesme gelir. "
            "Sürücü zaafı veya aygıt ele geçirme tarifi yoktur."
        ),
        "kaynak_notu": "Faz 16b — çevre birimi.",
    },
    {
        "id": "kalici_depolama",
        "baslik": "kalıcı depolama",
        "aliases": ["kalici depolama", "kalıcı depolama", "sabit disk", "kati hal diski", "katı hal diski", "ssd disk"],
        "metin": (
            "Kalıcı depolama güç kesilince veriyi tutar. Sabit diskte arama süresi kafa hareketi, dönüş gecikmesi sektörün kafa altına gelmesidir; ardışık okuma rasgeleden ucuzdur. "
            "Katı hal diskinde okuma sayfa, silme daha büyük blok boyundadır. Aşınma dengeleme silmeleri yayar. "
            "Çeviri katmanı mantıksal bloğu fiziksel sayfaya eşler. Dosya sistemi bu blokların üstünde isim kurar. "
            "Bellenim kırma talimatı yoktur."
        ),
        "kaynak_notu": "Faz 16b — depolama.",
    },
    {
        "id": "saat_darbesi",
        "baslik": "saat darbesi",
        "aliases": ["saat darbesi", "saat frekansi", "saat frekansı", "islemci saati", "işlemci saati"],
        "metin": (
            "Saat darbesi sıralı elemanları aynı kenarda örnekletir. Kritik yol, iki yazmaç arasındaki en uzun kombinasyonel gecikmedir; azami frekans bu yolun bir periyoda sığmasıyla sınırlıdır. "
            "Dinamik güç kabaca etkinlik, kapasite, gerilimin karesi ve frekansın çarpımıdır. Kaçak akım anahtarlama olmadan da ısı üretir. "
            "Soğutma yongayı güvenli sıcaklıkta tutar. Frekans zorlama veya gerilim yükseltme talimatı değildir."
        ),
        "kaynak_notu": "Faz 16b — saat ve güç.",
    },
    {
        "id": "ayrik_matematik",
        "baslik": "ayrık matematik",
        "aliases": ["ayrik matematik", "ayrık matematik", "boolean cebir", "dogruluk tablosu", "doğruluk tablosu"],
        "metin": (
            "Ayrık matematik küme, ilişki, fonksiyon ve saymayı konu alır. Fonksiyon her elemana tam bir sonuç bağlar. "
            "Tümevarım taban adımı ve «n doğruysa n+1 doğrudur» adımıyla döngü ve özyinelemeyi taşır. "
            "Çizge düğüm ve kenardır; ağaç bağlantılı ve çevrimsiz olandır. "
            "Boolean cebir VE, VEYA ve DEĞİL ile kapıların cebiridir. Doğruluk tablosu bağlacın her atamadaki sonucunu gösterir. "
            "Felsefedeki kıyas geleneği ayrı raftadır."
        ),
        "kaynak_notu": "Faz 16c — dayanak. Felsefe kıyası ayrı raftadır.",
    },
    {
        "id": "transistor_anahtar",
        "baslik": "transistör anahtar",
        "aliases": ["transistor anahtar", "transistör anahtar", "lojik seviye", "lojik 1"],
        "metin": (
            "CMOS kapıda transistör anahtardır. Tersleyicide çekme-yukarı çıkışı beslemeye, çekme-aşağı toprağa bağlar; ikisi birden iletimde kalmaz. "
            "Giriş 0 iken çıkış 1, giriş 1 iken çıkış 0 olur. "
            "Lojik 1 ve 0 gürültü paylı gerilim aralıklarıdır; aradaki bölge yasaktır. "
            "Yonga üretme veya laboratuvar kurma talimatı değildir."
        ),
        "kaynak_notu": "Faz 16c — dayanak.",
    },
    {
        "id": "isletim_cekirdegi",
        "baslik": "işletim çekirdeği",
        "aliases": ["isletim cekirdegi", "işletim çekirdeği", "kernel nedir", "sistem cagrisi", "sistem çağrısı"],
        "metin": (
            "İşletim çekirdeği ayrıcalıklı kipte sayfa tablosunu, kesmeleri ve aygıt yazmaçlarını kurar. Kullanıcı programı bu kaynaklara doğrudan gidemez. "
            "Sistem çağrısı tuzakla çekirdek kipine geçer; çağrı numarası hizmeti seçer, sonuçla kullanıcı kipine dönülür. "
            "Kısa işletim sistemi tanımı teknoloji rafındadır. Bu kart ayrıcalık sınırını anlatır. Sınırı aşma yöntemi yoktur."
        ),
        "kaynak_notu": "Faz 17 — sistem yazılımı.",
    },
    {
        "id": "proses",
        "baslik": "proses",
        "aliases": ["proses", "is parcacigi", "iş parçacığı", "zamanlayici", "zamanlayıcı"],
        "metin": (
            "Proses, programın çekirdekteki kimliğidir: adres uzayı, açık dosyalar, durum, yazmaç bağlamı. Hazır, çalışıyor ve bekliyor durumları işlemcinin kime gideceğini belirler. "
            "Bağlam değiştirme yazmaçları saklayıp diğer prosesinkini yükler. "
            "İş parçacığı aynı adres uzayını paylaşan ayrı akıştır; yığını ayrıdır. "
            "Klasik kilitlenme dört şartın bir arada olmasıdır: karşılıklı dışlama, tut-ve-bekle, zorla bırakamama, döngüsel bekleme. "
            "Kilit kırma tarifi yoktur."
        ),
        "kaynak_notu": "Faz 17 — proses.",
    },
    {
        "id": "sanal_bellek",
        "baslik": "sanal bellek",
        "aliases": ["sanal bellek", "sayfa tablosu", "sayfalama"],
        "metin": (
            "Sanal bellek her prosese kendi adres uzayını gösterir. Sayfa tablosu sanal sayfayı fiziksel çerçeveye çevirir; çok düzeyli tablo seyrek uzayda yer kazandırır. "
            "TLB son çevirilerin hızlı kopyasıdır. Sayfa bellekte yoksa sayfa hatası olur; çekirdek diskten getirebilir veya yasadışı erişimi sonlandırır. "
            "Sürekli kovup geri getirmek sistemi yavaşlatır. Koruma bitleri okuma, yazma ve kullanıcı kipini sınırlar. Aşma yöntemi yoktur."
        ),
        "kaynak_notu": "Faz 17 — sanal bellek.",
    },
    {
        "id": "dosya_sistemi",
        "baslik": "dosya sistemi",
        "aliases": ["dosya sistemi", "dizin agaci", "dizin ağacı"],
        "metin": (
            "Dosya sistemi blokları isim ve üstveri ile sunar. Düğüm; sahip, izin, boy ve veri bloklarının adresini tutar. "
            "Dizin isimden düğüm numarasına eşler. Yol kökten çözülür. "
            "Günlük, değişikliği uygulamadan önce niyeti kaydeder; çöküşte yarım iş toparlanır. "
            "İzin oku-yaz-çalıştır bitleridir. Sert bağ aynı düğüme ikinci isim, sembolik bağ ise yolu gösteren ayrı dosyadır. "
            "İzin aşma veya disk kazıma yöntemi yoktur."
        ),
        "kaynak_notu": "Faz 17 — dosya sistemi.",
    },
    {
        "id": "derleyici",
        "baslik": "derleyici",
        "aliases": ["derleyici", "baglayici", "bağlayıcı", "yorumlayici", "yorumlayıcı"],
        "metin": (
            "Derleyici kaynak metni sözcüklere böler, dilbilgisine göre ağaç kurar, tipleri denetler, ara gösterimde iyileştirir, sonra hedef komut setine ve yazmaçlara indirger. "
            "Bağlayıcı nesne dosyalarındaki sembolleri çözer ve son adresleri yazar. "
            "Yorumlayıcı adım adım yürütür. Anında derleme sıcak izi çalışma sırasında makine koduna çevirir. "
            "Derleyiciyi kırma yöntemi yoktur."
        ),
        "kaynak_notu": "Faz 17 — derleyici.",
    },
    {
        "id": "ag_yigini",
        "baslik": "ağ yığını",
        "aliases": ["ag yigini", "ağ yığını", "tcp ip modeli"],
        "metin": (
            "Ağ yığını işi katmanlara böler: çerçeve, adres ve yönlendirme, uçtan uca taşıma, uygulama. "
            "TCP bayt akışını sıra numarası ve alındı ile izler; kayıp olursa yeniden gönderir. Pencere karşı tarafın alabildiği kadar gönderir. "
            "UDP datagramdır; sıra ve yeniden gönderim sözleşmesi yoktur, kayıp uygulamaya yansır. "
            "Tıkanıklık denetimi ağ dolduğunda gönderim hızını kısar. Tarama veya paket dövme tarifi yoktur."
        ),
        "kaynak_notu": "Faz 17 — ağ yığını.",
    },
    {
        "id": "veri_yapisi",
        "baslik": "veri yapısı",
        "aliases": ["veri yapisi", "veri yapısı", "bagli liste", "bağlı liste", "dizi indeks"],
        "metin": (
            "Veri yapısı erişim sözleşmesiyle birlikte maliyeti de taşır. Dizi sürekli bellektedir; indeksle erişim sabittir, ortaya eklemek kaydırır. "
            "Bağlı liste düğümleri işaretçi ile bağlar; başa eklemek ucuz, n’inci elemana gitmek n adımdır ve önbellek dağınık düğümde soğur. "
            "Çok indeks varsa dizi, çok ekleme ve az rasgele erişim varsa liste seçilir. "
            "Dizi önbellekte sıcak kalır; dağınık düğüm aynı satıra sığmaz."
        ),
        "kaynak_notu": "Faz 18 — veri yapısı.",
    },
    {
        "id": "yigin_kuyruk",
        "baslik": "yığın ve kuyruk",
        "aliases": ["yigin", "yığın", "veri kuyrugu", "veri kuyruğu", "cagri yigini", "çağrı yığını"],
        "metin": (
            "Yığın son giren ilk çıkar; tepeye koyma ve tepeden alma sabittir. Çağrı yığını dönüş adresini ve yerel çerçeveyi tutar. Derin özyineleme bu sınırı aşabilir. "
            "Taşmayı istismar etme anlatılmaz. "
            "Kuyruk ilk giren ilk çıkar. Dairesel tampon sabit dizide baş ve son indeksi ilerletir; dolduğunda üretici bekler. "
            "Hazır kuyruğu ve G/Ç tamponu bu sözleşmedir. İki uç da sabit zamanda ilerler."
        ),
        "kaynak_notu": "Faz 18 — yığın ve kuyruk.",
    },
    {
        "id": "agac_cizge",
        "baslik": "ağaç ve çizge",
        "aliases": ["ikili arama agaci", "ikili arama ağacı", "cizge", "çizge", "graf teorisi"],
        "metin": (
            "Ağaç köklü, bağlantılı ve çevrimsizdir. İkili arama ağacında sol alt ağaç küçük, sağ büyüktür. Zincire dönerse arama doğrusal uzar; dengeli ağaç yüksekliği logaritmik tutar. "
            "Yığın ağacında ebeveyn çocuklardan küçük ya da eşittir; kök öncelik kuyruğunun başıdır. "
            "Genişlik öncelikli arama katman katman gider. Derinlik öncelikli arama dalı sonuna kadar iner. İkisi de düğüm ve kenarı sabit kez ziyaret eder."
        ),
        "kaynak_notu": "Faz 18 — ağaç ve çizge.",
    },
    {
        "id": "algoritma_karmasiklik",
        "baslik": "algoritma karmaşıklığı",
        "aliases": ["algoritma karmasikligi", "algoritma karmaşıklığı", "buyuk o", "büyük o", "ikili arama", "hizli siralama", "hızlı sıralama"],
        "metin": (
            "Algoritma sonlu adımlarla sonuca gider. Büyük-O, adım sayısının girdiye göre üst sınırıdır; sabitleri atar. "
            "İkili arama sıralı dizide aralığı yarılar, adım sayısı logaritmiktir. "
            "Birleştirerek sıralama en kötü durumda da n log n mertebesindedir. "
            "Hızlı sıralama ortalama durumda n log n, dayanak hep uçta kalırsa n kareye düşer. "
            "Karşılaştırmalı sıralama en kötü durumda n log n alt sınırına oturur."
        ),
        "kaynak_notu": "Faz 18 — karmaşıklık.",
    },
    {
        "id": "hash_tablosu",
        "baslik": "hash tablosu",
        "aliases": ["hash tablosu", "ozet tablosu", "özet tablosu"],
        "metin": (
            "Hash tablosu anahtarı bir fonksiyonla kova indisine indirger. Yük faktörü eleman sayısının kova sayısına oranıdır. "
            "Zincirlemede çakışan anahtarlar listede durur; düzgün yayılımda ortalama zincir bu orandadır. "
            "Açık adresleme çakışanı başka boş göze kaydırır. Tablo dolunca büyütülüp yeniden özetlenir. "
            "Parola kırma veya çarpıştırma tarifi yoktur. Tablo fonksiyonu gizlilik ispatı iddia etmez."
        ),
        "kaynak_notu": "Faz 18 — hash tablosu.",
    },
    {
        "id": "yazilim_tasarimi",
        "baslik": "yazılım tasarımı",
        "aliases": ["yazilim tasarimi", "yazılım tasarımı", "sorumluluk bolme", "sorumluluk bölme"],
        "metin": (
            "Tasarım değişme ihtimalini sınırlar. Yüksek yapışkanlıkta modülün parçaları tek işe hizmet eder. Düşük bağlaşımda modüller dar arayüzle konuşur. "
            "Arayüz sözleşmedir; iç gösterim gizlenirse sözleşme bozulmadan iç değişir. "
            "Tek sorumluluk, bir değişme sebebinin tek modülü etkilemesidir. Henüz ikinci kullanım yokken kurulan genel çerçeve de borç olabilir."
        ),
        "kaynak_notu": "Faz 19 — tasarım.",
    },
    {
        "id": "birim_testi",
        "baslik": "birim testi",
        "aliases": ["birim testi", "birim test", "otomatik test"],
        "metin": (
            "Birim testi küçük bir parçayı belirli girdiye belirli çıktı ile bağlar. Düzen-uygula-doğrula: girdiyi kur, çağır, karşılaştır. "
            "Boş, tek eleman, tam kapasite ve sıfır gibi sınırlar ortaya yakın değerden daha çok hata gösterir. "
            "Önce başarısız test, sonra onu geçiren kod, sonra düzenleme. "
            "Parçalar doğru olup birleşince protokol yine bozulabilir; birim testi entegrasyonun yerine geçmez. Her doğruluğu kanıtlamaz."
        ),
        "kaynak_notu": "Faz 19 — test.",
    },
    {
        "id": "hata_ayiklama",
        "baslik": "hata ayıklama",
        "aliases": ["hata ayiklama", "hata ayıklama", "kesme noktasi", "kesme noktası"],
        "metin": (
            "Hata ayıklama hipotez işidir. Belirti önce yeniden üretilir. Beklenen ile gözlenen ayrılır. "
            "Daraltma, bölgeyi ikiye bölüp hangi yarıda bozulduğuna bakmaktır. Kesme noktası o andaki yazmaç ve değişkeni gösterir; günlük, kesme koyamadığın yerde sırayı bırakır. "
            "Bir anda çok şeyi değiştirmek hipotezi siler. Düzeltme, yeniden üreten test ile kalıcı olur. "
            "Güvenlik açığı arama veya bellek bozma yöntemi değildir."
        ),
        "kaynak_notu": "Faz 19 — hata ayıklama.",
    },
    {
        "id": "surum_kontrolu",
        "baslik": "sürüm kontrolü",
        "aliases": ["surum kontrolu", "sürüm kontrolü", "git dali", "git dalı"],
        "metin": (
            "Sürüm kontrolü dosya ağacının görüntülerini ve neden değiştiğini saklar. Kayıt bir görüntüdür; not nedeni söyler. "
            "Dal ana çizgiyi bozmadan deneme yapar. Birleştirme iki ucu ortak atadan beri uygular; aynı satır iki yerde değiştiyse çakışma çözülür. "
            "Yayımlanmış geçmişi yeniden yazmak başkalarının kaydını koparır. Depo ele geçirme yöntemi değildir."
        ),
        "kaynak_notu": "Faz 19 — sürüm kontrolü.",
    },
]
