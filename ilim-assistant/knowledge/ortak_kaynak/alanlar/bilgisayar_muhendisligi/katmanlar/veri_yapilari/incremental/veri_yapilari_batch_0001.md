# Veri yapıları ve algoritmalar

Kaynak: Rüzgar bilgisayar mühendisliği Faz 18. Eğitim özeti. Exploit yok.

## 1. Veri yapısı

Veri yapısı, veriyi bir erişim ve güncelleme sözleşmesiyle tutar. Sözleşme maliyetleri birlikte gelir. Dizi sürekli bellektedir. İndeksle erişim sabittir, çünkü adres taban artı indeks çarpı eleman boyudur. Ortaya eklemek kaydırmayı gerektirir; maliyet eleman sayısıyla büyür. Bağlı listede her düğüm değeri ve sonraki düğümün adresini tutar. Başı bilinirken ortaya veya başa eklemek sabittir. n’inci elemana gitmek n adım sürer; önbellek de düğümler dağınık olduğu için dizi kadar sıcak kalmaz. Seçim, erişim örüntüsüne göre yapılır: çok indeks varsa dizi, çok ekleme-silme ve az rasgele erişim varsa liste.

## 2. Yığın ve kuyruk

Yığın son giren ilk çıkar. Push tepeye koyar, pop tepeden alır. İkisi de sabittir. Çağrı yığını fonksiyonun dönüş adresini, kaydedilen yazmaçları ve yerel değişkenleri çerçeve olarak tutar. Çağrı push, dönüş pop’tur. Derin özyineleme yığını büyütür; taşma o çerçevenin ayrılan sınırı aşmasıdır. Bu not taşmayı istismar etmeyi anlatmaz. Kuyruk ilk giren ilk çıkar. Üretici arkaya ekler, tüketici önden alır. Dairesel tampon, sabit dizide baş ve son indeksi ilerletir; dolduğunda üretici bekler. İşletim sistemindeki hazır kuyruğu ve G/Ç tamponu bu sözleşmedir.

## 3. Ağaç ve çizge

Ağaç, kökü olan bağlantılı çevrimsiz çizgedir. Her düğümün tek ebeveyni vardır, kök hariç. İkili arama ağacında bir düğümün sol alt ağacı küçük, sağı büyüktür. Arama, her adımda bir yana iner. Ağaç zincire dönerse arama eleman sayısı kadar uzar. Dengeli ağaç yüksekliği logaritmik tutulur; dönüşler veya renk kuralları dengeyi onarır. Yığın (heap) tam bir ağaçtır ve ebeveyn çocuklardan küçük ya da eşittir; öncelik kuyruğunda kök en küçük elemandır. Çizge düğüm ve kenardan oluşur; kenar yönlü veya ağırlıklı olabilir. Genişlik öncelikli arama bir kaynaktan katman katman gider, ağırlıksız kenarda en kısa yolun kenar sayısını verir. Derinlik öncelikli arama bir dalı sonuna kadar iner, geri sarar. İkisi de her düğüm ve kenarı sabit kez ziyaret eder.

## 4. Karmaşıklık, sıralama, arama

Algoritma sonlu, belirli adımlarla sonuca gider. Büyük-O, girdi n büyürken adım sayısının üst sınırıdır; sabit çarpanları ve küçük terimleri atar. İç içe tam tarama sık sık n kare mertebesine gider. Sıralı dizide ikili arama her adımda aralığı yarılar; adım sayısı logaritmiktir. Sıralı değilse bu garanti yoktur. Birleştirerek sıralama diziyi yarıya böler, yanları sıralar, birleştirir. En kötü durumda da n log n mertebesindedir ve ek bellek ister. Hızlı sıralama bir dayanak seçer, küçükleri sola büyükleri sağa ayırır, yanlarda yineler. Ortalama durumda n log n, dayanak hep uçta kalırsa n kareye düşer. Karşılaştırmalı sıralamanın en kötü durumda n log n’den iyi bir alt sınırı vardır; sayarak sıralama karşılaştırmadan kaçtığı için tam sayılarda doğrusal olabilir, ama değer aralığına bellek ayırır.

## 5. Hash tablosu

Hash tablosu anahtarı bir fonksiyonla kova indisine indirger. İyi fonksiyon anahtarları kovalara dengeli yayar. Yük faktörü, eleman sayısının kova sayısına oranıdır. Zincirlemede aynı kovaya düşen anahtarlar listede durur; basit düzgün yayılım varsayımında ortalama zincir yük faktörü kadardır. Açık adreslemede çakışan anahtar tablonun başka bir boş gözüne kayar. Tablo dolunca ekleme pahalanır; büyütüp yeniden özetlemek maliyeti seyrekleştirir. Bu yapı sözlük ve küme içindir. Parola kırma, özet çarpıştırma veya güvenlik özeti kırma tarifi yoktur. Kriptografik özet ile tablo fonksiyonu aynı iş değildir; tablo fonksiyonu hız ve yayılım ister, gizlilik ispatı iddia etmez.
