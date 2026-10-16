# Programlama dilleri

Kaynak: Rüzgar bilgisayar mühendisliği Faz 20. Eğitim özeti. Exploit yok.

## 1. HTML dili

HTML, tarayıcının okuduğu belge iskeletidir. Etiketler metni başlık, paragraf, bağlantı, liste ve görsele ayırır. Tarayıcı etiketleri bir ağaç kurar; görünür sayfa bu ağacın çizimidir. HTML hesap yapmaz. Stil CSS'tedir, davranış JavaScript'tedir. Bu not sayfa yapısını öğretir.

## 2. HTML dosya düzeni

Küçük bir sitede kökte index.html durur. css/ klasörü stilleri, js/ klasörü betikleri, images/ görselleri tutar. index.html bu dosyaları göreli yolla çağırır: css/site.css ve js/site.js. İsimler küçük harf ve tire ile kalırsa adres karışmaz. Bir sayfa bir işi anlatır. Bu düzen sunucu kurmadan klasörde durur.

## 3. HTML çalıştırma

HTML çalıştırmak, dosyayı tarayıcıda açmaktır. index.html dosyasına çift tıklamak veya tarayıcıya sürüklemek yeter. Adres çubuğunda file ile yerel yol görünür. Bağlantılar aynı klasöre göreli ise sayfalar birbirini açar. Ayrı bir derleyici gerekmez. Bu yol kendi dosyanı gösterir.

## 4. HTML sınama

Sınama, belgenin beklenen iskeleti taşıyıp taşımadığına bakmaktır. Başlık etiketi var mı, bağlantı gerçek bir dosyaya mı gidiyor, görselin alternatif metni yazılmış mı. Tarayıcıda sayfayı açıp başlık ve bağlantıyı kontrol etmek ilk sınavdır. Eksik kapanan etiket ağacı bozar. Bu sınama güvenlik taraması değildir.

## 5. CSS dili

CSS, HTML ağacındaki kutuların görünüşünü söyler. Seçici hangi elemanı tutacağını, bildirim rengi, boşluğu, yazı boyutunu ve dizilişi söyler. Aynı seçici sonra gelirse öncekini ezer. HTML iskelet kalır; CSS değişince içerik aynı kalır, görünüş değişir. CSS dosya silmez. Bu not görünüş sözleşmesini öğretir.

## 6. CSS dosya düzeni

Stil tek dosyada durabilir veya işe göre bölünür: temel.css yazı ve boşluk, yerlesim.css sıra ve ızgara, bilesen.css düğme ve kart. HTML head içinde sırayla bağlanır; sonra gelen dosya öncekini ezer. Sınıf adı işi söyler: baslik, kart, dugme. Sayfaya özel kural ayrı dosyada kalırsa ortak stil bozulmaz.

## 7. CSS çalıştırma

CSS ayrı bir program olarak çalışmaz. Tarayıcı, HTML'in bağladığı css dosyasını okur ve kutuları çizer. Dosyayı kaydedip sayfayı yenilemek yeni görünüşü getirir. Yol yanlışsa stil gelmez. Canlı önizleme için dosyayı yine tarayıcıda açmak yeter.

## 8. CSS sınama

Sınama, seçicinin doğru kutuyu tutup tutmadığına ve dar ekranda taşma olup olmadığına bakmaktır. Başlık boyutu, düğme kontrastı ve iki kutunun yan yana durması tarayıcıda kontrol edilir. Aynı sınıf iki yerde farklı iş görüyorsa ad ayrılır. Bozuk yol, stil dosyasının hiç yüklenmemesidir. Bu sınama başkasının sayfasını bozmak için kullanılmaz.

## 9. JavaScript dili

JavaScript, tarayıcıda sayfanın davranışıdır. Düğmeye basılınca metin değişir, listeye satır eklenir, form gönderilmeden önce boş alan uyarılır. Değerler değişkende durur, fonksiyon işi böler, koşul ve döngü tekrarlar. Sayfa yüklenince betik çalışır. Hesap ve etkileşim içindir. İşletim sistemine serbest komut vermek bu notun konusu değildir.

## 10. JavaScript dosya düzeni

Betik js/site.js içindedir. HTML sonunda script etiketi ile bağlanır ki belge önce kurulsun, betik sonra elemanı arasın. Küçük işte tek dosya yeter. Büyüyünce saf fonksiyonlar bir dosyada, sayfa bağları başka dosyada durur. İsimler işi söyler. Gizli anahtar ve parola betiğin içine yazılmaz.

## 11. JavaScript çalıştırma

Tarayıcı, HTML'in gösterdiği js dosyasını yükleyip çalıştırır. Sayfayı yenilemek betiği yeniden okur. Hata olursa tarayıcının konsolu satır numarasını yazar. Node kuruluysa tarayıcıya bağlı olmayan dosya node js/site.js ile de çalışır. document çağrısı Node'da yoktur. İlk deneme için sayfayı tarayıcıda açmak yeter.

## 12. JavaScript sınama

Sınama, fonksiyonun belirli girdiye belirli çıktı vermesidir. Saf bir fonksiyon tarayıcı olmadan da çağrılır: boş metin yanlış, dolu metin doğru. Sayfada ise düğmeye basıp metnin değiştiği gözlenir. Konsoldaki kırmızı satır hangi çağrının kırıldığını gösterir. Bir anda hem hesabı hem sayfayı değiştirmek hatayı gizler. Bu sınama başkasının oturumunu ele geçirmez.

## 13. Python dili

Python, metin olarak yazılan ve yorumlayıcının çalıştırdığı dildir. Değişkenler değeri tutar, fonksiyon işi adlandırır, liste ve sözlük veriyi taşır. Girinti bloğu belirler. Küçük araç, hesap ve dosya okuma için uygundur. Standart kütüphane dosya, yol ve tarih işini hazır getirir. Bu not dili öğretir. Sisteme zarar veren komut yazılmaz.

## 14. Python dosya düzeni

Küçük araçta kökte uygulama.py durur. İş büyüyünce paket klasörü açılır: uygulama/cekirdek.py ve tests/test_cekirdek.py. Gereken dış paket requirements.txt içine ad ve sürümle yazılır. Veri data/ altında, üretilen çıktı cikti/ altında kalır. Kaynak ile üretilen dosya karışmaz. Gizli anahtar koda yazılmaz; ortam değişkeninde durur.

## 15. Python çalıştırma

Kurulu yorumlayıcı python uygulama.py ile dosyayı çalıştırır. Sürüm python --version ile görülür. Proje klasöründe sanal ortam açılır: python -m venv .venv. Ortam etkinleştirilir ve pip install -r requirements.txt ile bağımlılık iner. Çalıştırma o ortamın python'u ile yapılır. Böylece bu projenin paketleri sistemdekileri ezmez.

## 16. Python sınama

Sınama, küçük fonksiyonu sabit girdiye bağlar. tests/test_cekirdek.py içinde beklenen sonuç assert ile yazılır. Komut python -m pytest proje klasöründe çalışır. Önce başarısız testi görmek, sonra kodu ona uydurmak hatayı erken gösterir. Sözdizimi python -m compileall uygulama ile de okunur. Test kendi fonksiyonunu ölçer.

## 17. Statik site kurulumu

Statik site, sunucuda hesap olmadan tarayıcının okuduğu dosya kümesidir. Kökte index.html, css/site.css ve js/site.js durur. HTML başlık ve bölümleri kurar, CSS görünüşü bağlar, JavaScript yalnız gerekli etkileşimi ekler. Sayfalar göreli bağlantı ile birbirini açar. Klasörü tarayıcıda açmak kurulumu doğrular. Yayınlamak bu klasörü bir dosya sunucusuna kopyalamaktır. Formun kalıcı kaydı ve gizli anahtar bu iskelette yoktur.

## 18. Küçük Python uygulaması

Küçük uygulama tek işi yapan komut satırı aracıdır. Önce iş bir cümlede yazılır: metin dosyasındaki satır sayısını bas. uygulama.py argümanı okur, dosyayı açar, sayıyı basar. tests/ aynı sayıyı sabit bir örnek dosyayla bekler. python -m pytest geçince araç biter. Klasör düzeni, sanal ortam ve requirements.txt bir arada durur. Araç kendi dosyanı okur.
