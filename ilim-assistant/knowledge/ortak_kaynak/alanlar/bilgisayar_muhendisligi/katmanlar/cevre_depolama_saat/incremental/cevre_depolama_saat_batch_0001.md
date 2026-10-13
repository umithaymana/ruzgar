# Çevre birimi, depolama, saat ve güç

Kaynak: Rüzgar bilgisayar mühendisliği Faz 16b. Eğitim özeti. Exploit yok.

## 1. Çevre birimi

Çevre birimi işlemcinin dışındaki giriş-çıkış aygıtıdır: klavye, işaretçi, ekran, ağ arabirimi, disk denetleyicisi. Denetleyici, aygıtın elektriksel veya paket işaretini işlemcinin anlayacağı yazmaçlara çevirir. Sürücü, işletim çekirdeğinde bu yazmaçlara sistem çağrısı ardından dokunan yazılımdır. Bellek eşlemeli modelde program aygıta sıradan yükle-depola ile gider; adres aralığı aygıta ayrılmıştır. Kesme, aygıtın olayını işlemciye taşır. Doğrudan bellek erişimi, disk veya ağ tamponunu işlemciyi her sözcükte kesmeden doldurur. İşlemci transferin başında denetleyiciye adres ve uzunluk yazar, bitişte kesme alır. Bu not sürücü zaafı veya aygıt ele geçirme tarifi değildir.

## 2. Kalıcı depolama

Kalıcı ortam güç kesilince veriyi tutar. Sabit diskte kafa plakanın üzerindeki izi arar; arama süresi mekanik gecikmedir, dönüş gecikmesi sektörün kafa altına gelmesini bekler. Ardışık okuma bu yüzden rasgele okumadan ucuzdur. Katı hal diski NAND hücresinde yük tutar. Okuma sayfa boyundadır. Silme ise daha büyük blok boyundadır; tek sayfayı yerinde değiştirmek için blok okunur, silinir, yeniden yazılır. Aşınma dengeleme, silme sayısını hücreler arasında yayar. Denetleyicinin çeviri katmanı mantıksal bloğu fiziksel sayfaya eşler ve çöp toplar. Dosya sistemi bu mantıksal blokların üstünde isim ve dizin kurar. Bu not bellenim kırma talimatı değildir.

## 3. Saat ve güç

Saat darbesi sıralı elemanların aynı kenarda örneklemesini sağlar. Kritik yol, iki yazmaç arasında kombinasyonel gecikmesi en uzun yoldur. Azami frekans, bu yolun kurulum süresiyle birlikte bir periyoda sığmasıyla sınırlıdır. Anahtarlanan kapasitenin dinamik gücü, kabaca etkinlik çarpı kapasite çarpı gerilimin karesi çarpı frekanstır. Gerilim düşünce güç hızla düşer; frekans da doğrusal girer. Kaçak akım, anahtarlama olmasa da ısı üretir. Soğutma, yonganın güvenli sıcaklık penceresinde kalması içindir. Bu not frekans zorlama, gerilim yükseltme veya laboratuvar kurma talimatı değildir.
