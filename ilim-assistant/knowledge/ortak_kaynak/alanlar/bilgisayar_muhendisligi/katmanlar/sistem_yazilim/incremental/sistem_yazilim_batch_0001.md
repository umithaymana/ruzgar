# Sistem yazılımı

Kaynak: Rüzgar bilgisayar mühendisliği Faz 17. Eğitim özeti. Exploit yok.

## 1. Çekirdek ve sistem çağrısı

İşletim çekirdeği ayrıcalıklı kipte çalışır: sayfa tablosunu, kesmeleri ve aygıt yazmaçlarını o kurar. Kullanıcı programı ayrıcalıksız kipte kalır; aygıta veya başka prosesin belleğine doğrudan gidemez. Sistem çağrısı kontrollü bir kapıdır. Program yazmaçlara çağrı numarasını ve argümanları koyar, bir tuzak komutu çalıştırır. İşlemci çekirdek kipine geçer, çağrı numarasına göre hizmeti yapar, sonucu yazıp kullanıcı kipine döner. Kısa «işletim sistemi donanımı yönetir» cümlesi teknoloji kartındadır. Bu not ayrıcalık sınırını ve tuzağı anlatır. Sınırı aşma yöntemi yoktur.

## 2. Proses ve iş parçacığı

Proses, çalışan programın çekirdekteki kimliğidir: adres uzayı, açık dosya tablosu, durum, yazmaç bağlamı. Durumlar tipik olarak hazır, çalışıyor ve bekliyor diye ayrılır. Bekleyen proses bir olay (disk, kilit, zaman) olmadan işlemci almaz. Bağlam değiştirme, çalışan prosesin yazmaçlarını saklayıp diğerininkini yüklemektir; bunun bedeli önbellek sıcaklığının bozulmasıdır. Zamanlayıcı hazır kuyruğundan seçer. Öncelikli ve adil paylaştırma farklı amaçlardır: gecikme ile verim çelişebilir. İş parçacığı aynı adres uzayını ve dosya tablosunu paylaşan ayrı yürütme akışıdır. Yığınları ayrıdır. Kilit, paylaşılan veride aynı anda tek yazıcı olması içindir. Klasik kilitlenme modeli dört şart bir arada ister: karşılıklı dışlama, tut-ve-bekle, zorla bırakamama, döngüsel bekleme. Şarttan birini kırmak kilitlenmeyi o modelde engeller. Bu not kilit kırma veya yarışla sızma tarifi değildir.

## 3. Sanal bellek

Sanal bellek her prosese kendi adres uzayını gösterir. İşlemcinin ürettiği adres sanaldır. Sayfa tablosu sanal sayfa numarasını fiziksel çerçeveye çevirir. Çok düzeyli tablo, seyrek adres uzayında boş üst düzeyleri tutmayarak yer kazandırır. TLB, son çevirilerin küçük ve hızlı kopyasıdır. TLB ıskasında tablo bellekte yürür. Sayfa bellekte yoksa sayfa hatası olur; çekirdek sayfayı diskten getirebilir veya prosesin yasadışı erişimini sonlandırır. Yer kalmazsa az kullanılan sayfa kovulur. Sürekli kovup geri getirmek (çöpe düşme) sistemi yavaşlatır. Koruma bitleri sayfanın okunup yazılacağını ve kullanıcı kipine açık olup olmadığını söyler. Aşma yöntemi bu notta yoktur.

## 4. Dosya sistemi

Dosya sistemi mantıksal blokları isim, dizin ve üstveri ile sunar. Düğüm (inode) dosyanın sahibini, izinlerini, boyunu ve veri bloklarının adreslerini tutar. Dizin, isimden düğüm numarasına eşlemedir. Yol çözümleme kökten başlayıp dizin dizin iner. Günlük (journal), asıl veri yapılarını değiştirmeden önce niyeti kalıcı bir kayda yazar; çöküşte yarım kalan iş geri alınır veya tamamlanır. İzin, sahip ve grup için oku-yaz-çalıştır bitleridir. Bu not izin aşma veya disk kazıma yöntemi öğretmez.

## 5. Derleyici ve bağlayıcı

Derleyici kaynak metni hedef komut setine indirger. Sözcük çözümleyici karakterleri atomlara böler. Ayrıştırıcı dilbilgisine göre sözdizimi ağacı kurar. Anlam çözümleme tipleri ve bildirimleri denetler. Ara gösterim, dile ve sete daha az bağlı bir biçimdir; iyileştirme burada sabit katlama, ölü kod ve döngü taşıması gibi dönüşümler yapar. Komut seçimi ve yazmaç ataması hedef sete iner. Bağlayıcı, ayrı derlenmiş nesne dosyalarındaki sembolleri çözer, kütüphaneyi yerleştirir, yeniden yerleme ile son adresleri yazar. Yorumlayıcı kaynak veya ara biçimi adım adım yürütür. Anında derleme, sıcak izi çalışma sırasında makine koduna çevirir. Bu not derleyiciyi kırma yöntemi değildir.

## 6. Ağ yığını

Ağ yığını işi katmanlara böler ki üst katman altın her ayrıntısını bilmesin. Bağlantı katmanı bir halkada çerçeve taşır. Ağ katmanı adresler ve yönlendirir: paket bir sonraki sıçramaya gider. Taşıma katmanı uçtan uca teslimi üstlenir. TCP bayt akışını sıra numarası ve alındı ile izler; kayıp olursa yeniden gönderir. Pencere, karşı tarafın kabul edebileceği kadar göndererek akışı sınırlar. Tıkanıklık denetimi, ağın dolduğunu sezip hızı kısar. UDP datagram gönderir; sıra, alındı ve yeniden gönderim sözleşmesi yoktur, bu yüzden gecikmesi daha öngörülebilir olabilir ve kayıp uygulamaya yansır. Uygulama katmanı bu taşımanın üstünde web, posta veya ad çözümleme konuşur. Tarama, paket dövme veya saldırı tarifi yoktur.
