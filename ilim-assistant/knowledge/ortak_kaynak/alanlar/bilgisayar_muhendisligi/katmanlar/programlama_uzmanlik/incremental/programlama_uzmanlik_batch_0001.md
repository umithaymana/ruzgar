# Programlama uzmanlığı

Kaynak: Rüzgar bilgisayar mühendisliği Faz 19. Eğitim özeti. Exploit yok.

## 1. Tasarım

Tasarım, değişme ihtimalini sınırlamaktır. Yüksek yapışkanlık: bir modülün parçaları tek bir işe hizmet eder. Düşük bağlaşım: modüller az ve dar arayüzle konuşur. Arayüz sözleşmedir; çağıran önkoşulu sağlar, çağrılan sonkoşulu. İç gösterim gizlenirse sözleşme bozulmadan iç değişir. Tek sorumluluk, bir değişme sebebinin tek modülü etkilemesidir. Erken soyutlama da borçtur: henüz ikinci kullanım yokken kurulan genel çerçeve okumayı zorlaştırır. Uygulama pratiği programlama motorundadır. Bu not kavramı öğretir.

## 2. Birim testi

Birim testi, küçük bir parçayı dış dünyadan yalıtıp belirli girdiye belirli çıktı bekler. Düzen-uygula-doğrula: girdiyi kur, işlevi çağır, sonucu karşılaştır. Sınır değerler ortaya yakın değerden daha çok hata gösterir: boş koleksiyon, tek eleman, tam kapasite, sıfır, negatif. Önce başarısız test, sonra onu geçiren en küçük kod, sonra yeniden düzenleme. Test yokken yapılan düzenleme davranışı sessiz kaydırabilir. Test hata bulur; her doğru programı kanıtlamaz. Birim, entegrasyonun yerine geçmez: parçalar doğru olup birleşince protokolü bozabilir. Bu not güvenlik açığı tarayıcısı değildir.

## 3. Hata ayıklama

Hata ayıklama bir hipotez işidir. Önce belirti yeniden üretilir; üretilmeyen hata ölçülemez. Beklenen ile gözlenen ayrılır. Hipotez, hangi ara değer yanlışsa belirtiyi açıklar. Daraltma, girdiyi veya kod bölgesini ikiye bölüp hangi yarıda bozulduğuna bakmaktır. Kesme noktası o andaki yazmaç ve değişkeni gösterir. Günlük, kesme koyamadığın yerde zaman sırasını bırakır. Bir anda çok şeyi değiştirmek hipotezi siler. Düzeltme, yeniden üreten test ile kalıcı olur. Bu yöntem güvenlik açığı aramak veya bellek bozmak için anlatılmaz.

## 4. Sürüm kontrolü

Sürüm kontrolü dosya ağacının anlık görüntülerini ve onları kim, neden değiştirdiğini saklar. Kayıt (commit) bir görüntüdür. Not, ne değiştiğini değil neden değiştiğini söyler. Dal, ana çizgiden ayrılan bir uçtur; deneme ana çizgiyi bozmaz. Birleştirme iki ucun değişikliklerini ortak atadan beri uygular. Aynı satır iki uçta değiştiyse çakışma elle çözülür. Geçmişi yeniden yazmak yayımlanmış ucu başkalarının kaydından koparır; yerel denemede kullanılabilir, paylaşılan dalda gerekçe ister. Bu not depo ele geçirme yöntemi değildir.
