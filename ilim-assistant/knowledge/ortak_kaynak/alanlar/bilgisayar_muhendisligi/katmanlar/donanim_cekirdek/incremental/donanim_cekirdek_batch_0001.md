# Donanım çekirdeği

Kaynak: Rüzgar bilgisayar mühendisliği Faz 16. Eğitim özeti. Exploit yok.

## 1. Sayısal mantık

Sayısal devre bilgiyi iki kararlı düzeyde tutar; lojik 1 ve 0 birer gerilim aralığıdır, tek bir sonsuz kesin volt değildir. VE, ancak iki giriş de 1 ise 1 üretir. VEYA, en az biri 1 ise 1 üretir. DEĞİL biti tersler. Özel VEYA (XOR) girişler farklıysa 1 verir; toplayıcının toplam bitinde bu işe yarar. Kombinasyonel devrenin çıkışı yalnız o anki girişe bağlıdır: çoklayıcı, kod çözücü, toplayıcı böyledir. Sıralı devre geçmişi saklar. Mandallayıcı ve flip-flop, saat kenarında yazmaca yeni değeri alır. Kurulum süresi, verinin saat kenarından önce kararlı durması gereken aralıktır. Tutma süresi kenardan sonraki kısa aralıktır. Bu süreler ihlal edilirse yazmaç yarı kararlı bir ara değerde takılabilir. Not, bu süreyi bozma deneyi değildir.

## 2. İşlemci

Merkezi işlem birimi bir komutu dört işte yürütür: getir, çöz, işlet, yaz. Program sayacı sıradaki komutun adresini tutar. Komut yazmacı getirilen sözcüğü saklar. Aritmetik-mantık birimi toplama, çıkarma ve karşılaştırmayı yapar. Denetim birimi, komutun işlem koduna göre hangi yazmaçların okunacağını ve sonucun nereye yazılacağını seçer. Klasik beş aşamalı iş hattı bu işleri üst üste bindirir: getir, çöz, yürüt, bellek, yaz. Bir komut yürütülürken sonrakiler önceki aşamalardadır. Saat, aşamaların ortak temposudur. Veri tehlikesi, bir komutun henüz yazılmamış sonucu okumasıdır. İletim (forwarding), sonucu yazmaç dosyasına inmeden sonraki aşamaya verir. Denetim tehlikesi, dalın gidileceği adres henüz belli değilken hattın yanlış yoldan komut getirmesidir. Yanlış tahminde o komutlar atılır. Hattın kazancı, tehlike ve ıskalama ile düşer. Bu anlatım yan kanal saldırısı tarif etmez.

## 3. Komut seti

Komut seti mimarisi, yazılımın gördüğü sözleşmedir: komutlar, yazmaçlar, adresleme ve bayraklar. Yükle-depola düzeninde aritmetik yalnız yazmaçlar arasındadır; belleğe gitmek ayrı komuttur. Karmaşık komut düzeninde tek komut bellekteki işleneni de kullanabilir. Günümüzde bazı karmaşık setler, içeride daha küçük mikro işlemlere çözülür; programcı yine dış sözleşmeyi görür. Çağrı sözleşmesi, fonksiyon argümanının hangi yazmaçta duracağını ve dönüş adresinin nereye konacağını söyler. Derleyici yüksek dili bu sözleşmeye indirger. Aynı kaynak, başka sette yeniden derlenir. Taşınabilirlik kaynakta ve derleyicidedir; ham makine kodu sete bağlıdır.

## 4. Bellek hiyerarşisi

Hiyerarşi hız ile kapasiteyi değiştirir: yazmaç, önbellek, ana bellek, kalıcı depolama. Üste çıkıldıkça erişim kısalır ve sığa düşer. Gerekçe yerelliktir. Zamansal yerellik: az önce kullanılan sözcük yine kullanılır. Uzamsal yerellik: komşusu da kullanılır. Önbellek bu yüzden tek sözcük değil, satır (blok) taşır. Doğrudan eşlemede bir ana bellek bloğunun gidebileceği tek satır vardır. Küme ilişkili önbellekte o kümede birkaç yol vardır; çakışma ıskası azalır. Iska türleri: ilk getiriş (zorunlu), sığa yetmemesi, aynı yere düşen blokların birbirini kovması. Yaz-geçir her yazmayı ana belleğe de geçirir. Geri yazım yazmayı önce önbellekte tutar, satır kirliyse kovulurken belleğe yazar. Iska olunca satır alt düzeyden dolar; işlemci o sırada bekleyebilir.

## 5. Veri yolu ve giriş-çıkış

Veri yolu işlemci, bellek ve çevre birimleri arasında adres, veri ve denetim taşır. Adres hangi sözcüğün seçileceğini, veri içeriği, denetim oku-yaz ve hazır işaretini söyler. Bellek eşlemeli giriş-çıkışta aygıt yazmaçları adres uzayında sıradan bellek gibi görünür; özel bir komut gerekmez, adres aygıta aittir. Yoklama, işlemcinin aygıtın hazır bayrağını döngüde sormasıdır; basit ve işlemciyi meşgul eder. Kesme, aygıtın işlemciye «işin var» demesidir. İşlemci o anki durumu saklar, hizmet rutinine gider, sonra kaldığı yere döner. Doğrudan bellek erişimi, uzun bloğu sözcük sözcük işlemciden geçirmeden bellek ile aygıt arasında taşır; bitince kesme gelir. Bu not aygıtı ele geçirme yöntemi değildir.

## 6. Von Neumann

Von Neumann makinesinde komutlar ve veriler aynı bellekte durur. Program sayacı sıradaki komut adresini tutar; her getirmeden sonra ilerler, dal bunu değiştirir. Programın kendisi de veridir: derleyici komut sözcüklerini belleğe yazar, işlemci onları çözer. Bedel, komut getirisi ile veri erişiminin aynı yolu paylaşmasıdır. İş hattı ikisini aynı anda isterse yol dar boğaz olur. Ayrı komut ve veri önbelleği bu sıkışmayı azaltır; model hâlâ depolanmış program modelidir. Harvard düzeni komut ve veriyi fiziksel olarak ayırır; birçok gömülü çekirdek ve önbellek katı bu fikri kullanır.
