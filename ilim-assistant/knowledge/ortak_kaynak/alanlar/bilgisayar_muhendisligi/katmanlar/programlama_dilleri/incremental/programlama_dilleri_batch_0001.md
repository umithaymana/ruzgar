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

## 19. TypeScript dili

TypeScript, JavaScript'in tipli halidir. Büyük web uygulaması, tarayıcı arayüzü ve sunucu betiği yazılır. Değişkenin türü yazılır; yanlış tür kayıttan önce görülür. Tarayıcı TypeScript'i doğrudan okumaz, JavaScript'e çevrilmiş dosyayı açar. Bu not dili öğretir.

## 20. TypeScript dosya düzeni

Kaynak ts/ içinde durur. Derlenmiş çıktı js/ altına iner. tsconfig.json kökte tür ve hedefi söyler. HTML, üretilen js dosyasını çağırır. Kaynak ile üretilen dosya karışmaz.

## 21. TypeScript çalıştırma

Çalışan dosya, çevrilmiş JavaScript'tir. Sayfa tarayıcıda açılır. Ayrı bir sunucu şart değildir. Çeviri aracı kurulu değilse elde yalnız kaynak metin durur; el onu çalıştırmaz.

## 22. TypeScript sınama

Sınama, türün tutması ve saf fonksiyonun sabit girdiye sabit çıktı vermesidir. Sayfada düğmenin metni değişiyor mu diye bakılır. Bu sınama başkasının oturumunu ele geçirmez.

## 23. SQL dili

SQL, tablodaki veriyi seçmek, süzmek ve saymak için yazılır. Uygulama ekranı yazılmaz. Sorgu bir cümledir: hangi tablo, hangi koşul, hangi sütun. Veriyi silen veya başkasının tablosunu açan sorgu bu notun konusu değildir.

## 24. SQL dosya düzeni

Küçük işte sorgu.sql tek dosyada durur. Tablo tanımı ayrı, seçme sorgusu ayrı yazılırsa okumak kolaylaşır. Veri dosyası data/ altında kalır. Sorgu, uygulama kodunun içine gizlenmez.

## 25. SQL çalıştırma

SQL kendi başına bir program olarak çift tıklanmaz. Bir veritabanı aracı sorguyu okur ve satır döndürür. El, sorgu metnini okur; veritabanını kendiliğinden açmaz.

## 26. SQL sınama

Sınama, bilinen bir tabloya sorulunca beklenen satır sayısının gelmesidir. Boş koşul bütün tabloyu döndürür; koşul yazılır. Bu sınama başkasının verisini çekmek için kullanılmaz.

## 27. Bash dili

Bash, Unix kabuğunda kendi klasöründeki işi sıraya koymak için yazılır. Dosya adını basmak, bir metni başka dosyaya aktarmak ve küçük bir görevi adlandırmak bu dilin işidir. Başkasının makinesine komut göndermez. Silme bu notta yoktur.

## 28. Bash dosya düzeni

Betik bin/ veya kökte is.sh olarak durur. Ad işi söyler. Gizli anahtar betiğin içine yazılmaz. Üretilen çıktı cikti/ altında kalır.

## 29. Bash çalıştırma

Kabuk, betiği kendi klasöründe okur. El bu betiği kendiliğinden çalıştırmaz. Çalıştırma, sen söyleyince ve yalnız o dosyada olur.

## 30. Bash sınama

Sınama, betiğin beklenen dosya adını yazıp yazmadığına bakmaktır. Yan etki istenmiyorsa betik önce boş bir deneme klasöründe okunur. Bu sınama sistemi bozmak için kullanılmaz.

## 31. Java dili

Java ile kurum sunucusu, masaüstü aracı ve uzun ömürlü uygulama yazılır. Sınıf işi böler, paket dosyaları toplar. JavaScript ile aynı şey değildir. Bu not dili öğretir.

## 32. Java dosya düzeni

Kaynak src/ altında paket klasöründe .java dosyası olarak durur. Derlenmiş sınıf ayrı bir çıktı klasörüne iner. Proje adı ve paket adı karışmaz.

## 33. Java çalıştırma

Kurulu araç kaynağı sınıf dosyasına çevirir ve o sınıf okunur. El kaynağı okur, kendiliğinden derlemez ve çalıştırmaz.

## 34. Java sınama

Sınama, bir metodun sabit girdiye sabit sonuç vermesidir. Test sınıfı kaynakla aynı paketin test klasöründe durur. Bu sınama güvenlik taraması değildir.

## 35. C# dili

C# ile Windows uygulaması, oyun aracı ve kurum sunucusu yazılır. Türler yazılır, proje bir çözüm klasöründe durur. Bu not dili öğretir.

## 36. C# dosya düzeni

Kaynak .cs dosyası proje klasöründedir. Proje dosyası hangi kaynakların birlikte derleneceğini söyler. Çıktı bin altında kalır, kaynakla karışmaz.

## 37. C# çalıştırma

Proje aracı çözümü derler. El .cs metnini okur. Kendiliğinden derlemez ve çalıştırmaz.

## 38. C# sınama

Sınama, bir metodun beklenen değeri döndürmesidir. Test projesi ayrı durur. Bu sınama başkasının sürecine karışmaz.

## 39. PowerShell dili

PowerShell, Windows'ta kendi klasöründeki işi sıraya koymak için yazılır. Dosya adını basmak ve bir metni okumak bu dilin işidir. Bash'in Windows'taki karşılığına yakındır. Silme ve uzaktaki makineye komut bu notta yoktur.

## 40. PowerShell dosya düzeni

Betik .ps1 olarak kökte veya bin/ altında durur. Ad işi söyler. Gizli anahtar içine yazılmaz.

## 41. PowerShell çalıştırma

Windows kabuğu betiği okur. Çalışan yer, kullanıcının kendi klasörüdür. El betiği kendiliğinden çalıştırmaz.

## 42. PowerShell sınama

Sınama, betiğin beklenen adı yazıp yazmadığına bakmaktır. Deneme kendi klasöründe kalır. Bu sınama sistemi değiştirmek için kullanılmaz.

## 43. C++ dili

C++ ile oyun motoru, sistem aracı ve hız isteyen program yazılır. Bellek ve tür programcıdadır. C'nin üzerine sınıf ve şablon ekler. Bu not dili öğretir. Zararlı kod yazılmaz.

## 44. C++ dosya düzeni

Kaynak src/ içinde .cpp ve .h olarak durur. Derleme tarifi kökte bir dosyada yazılır. Üretilen program çıktı klasörüne iner.

## 45. C++ çalıştırma

Derleyici kaynağı makine koduna çevirir. El kaynağı okur. Kendiliğinden derlemez ve çalıştırmaz.

## 46. C++ sınama

Sınama, saf bir fonksiyonun sabit girdiye sabit çıktı vermesidir. Test derlemesi ayrıdır. Bu sınama bellek bozmak için kullanılmaz.

## 47. C dili

C dili ile işletim çekirdeğine yakın araç ve gömülü aygıt programı yazılır. Az araçla çok iş yapılır. C++ ve C# başka dillerdir. Bu not dili öğretir. Zararlı kod yazılmaz.

## 48. C dosya düzeni

Kaynak src/ içinde .c ve .h olarak durur. Her dosya bir işi taşır. Derleme tarifi ayrı yazılır.

## 49. C çalıştırma

Derleyici .c dosyasını çevirir. El metni okur. Kendiliğinden derlemez ve çalıştırmaz.

## 50. C sınama

Sınama, fonksiyonun bilinen girdiye bilinen sayı döndürmesidir. Taşan bellek bu notun örneği değildir.

## 51. Rust dili

Rust ile bellek güvenliği isteyen sistem aracı ve ağ servisi yazılır. Ödünç alma kuralları, geçersiz bellek kullanımını derlemede durdurur. Bu not dili öğretir.

## 52. Rust dosya düzeni

Kökte Cargo.toml projeyi tanıtır. Kaynak src/main.rs veya src/lib.rs içindedir. Bağımlılık sürümü toml dosyasında durur, koda gömülmez.

## 53. Rust çalıştırma

Proje aracı kaynağı derler. El rs metnini okur. Kendiliğinden derlemez ve çalıştırmaz.

## 54. Rust sınama

Sınama, kütüphane fonksiyonunun sabit girdiye sabit çıktı vermesidir. Test kaynakla aynı pakette durur. Bu sınama güvenlik açığı aramak değildir.

## 55. PHP dili

PHP ile sunucunun her istekte ürettiği web sayfası yazılır. HTML iskeletin içine sunucu hesabı girer. Tarayıcıya giden sonuç HTML'dir. Gizli anahtar koda yazılmaz.

## 56. PHP dosya düzeni

Genel sayfalar public/ altında .php olarak durur. Ortak fonksiyon includes/ içinde durur. Ayar dosyası kaynak ağacının dışındaki ortamda kalır.

## 57. PHP çalıştırma

Sayfa bir PHP okuyucusu olan sunucuda açılır. El dosyayı metin olarak okur. Kendiliğinden sunucu kurmaz ve çalıştırmaz.

## 58. PHP sınama

Sınama, saf bir fonksiyonun beklenen metni üretmesidir. Sayfanın başlığı tarayıcıda kontrol edilir. Bu sınama sunucuya sızmak için kullanılmaz.

## 59. Go dili

Go ile ağ servisi, küçük sunucu ve komut satırı aracı yazılır. Az sözdizimi ve hızlı derleme esastır. Bu not dili öğretir.

## 60. Go dosya düzeni

Kökte go.mod modülün adını söyler. Kaynak .go dosyaları paket klasöründedir. Komut cmd/ altında, kütüphane iç pakette durur.

## 61. Go çalıştırma

Go aracı paketi derler. Üretilen program çıktı klasörüne iner. El kaynağı okur. Kendiliğinden derlemez ve çalıştırmaz.

## 62. Go sınama

Sınama, fonksiyonun sabit girdiye sabit çıktı vermesidir. Test dosyası _test.go ile biter. Bu sınama ağa saldırmaz.

## 63. Kotlin dili

Kotlin ile Android uygulaması ve JVM üzerinde çalışan sunucu aracı yazılır. Java kütüphaneleriyle aynı makinede durabilir. Bu not dili öğretir.

## 64. Kotlin dosya düzeni

Uygulama kaynağı app/src altında .kt dosyasıdır. Gradle dosyası hangi kütüphanenin ineceğini söyler. Gizli anahtar depoya yazılmaz.

## 65. Kotlin çalıştırma

Proje aracı paketi derler. El .kt metnini okur. Kendiliğinden derlemez, telefona kurmaz ve çalıştırmaz.

## 66. Kotlin sınama

Sınama, bir fonksiyonun beklenen değeri döndürmesidir. Test kaynak ağacının test klasöründedir. Bu sınama cihaz ele geçirmez.

## 67. JSON dili

JSON, programların birbirine verdiği veri dosyası için yazılır. Uygulama davranışı yazılmaz. Nesne, dizi, metin ve sayı tutar. Yorum satırı yoktur.

## 68. JSON dosya düzeni

Veri data/ içinde .json olarak durur. Ad işi söyler: ayar.json, liste.json. İç içe yapı gerekmedikçe düz kalır.

## 69. JSON çalıştırma

JSON çalıştırılmaz. Bir program onu okur ve sözlüğe çevirir. El metni okur, dosyayı kendiliğinden yüklemez.

## 70. JSON sınama

Sınama, dosyanın geçerli JSON olması ve beklenen anahtarı taşımasıdır. Eksik virgül dosyayı bozar. Bu sınama veri çalmaz.

## 71. Markdown dili

Markdown, not, belge ve okuma metni yazmak içindir. Program çalıştırmaz. Başlık, liste ve bağlantı düz karakterle yazılır.

## 72. Markdown dosya düzeni

Notlar docs/ veya kökte .md olarak durur. Bir dosya bir konuyu anlatır. Üretilen HTML varsa ayrı klasörde kalır.

## 73. Markdown çalıştırma

Markdown çalıştırılmaz. Bir görüntüleyici onu başlık ve paragrafa çevirir. El ham metni okur.

## 74. Markdown sınama

Sınama, başlık satırının beklenen metni taşımasıdır. Bozuk bağlantı bir dosyaya gitmiyorsa not düşülür. Bu sınama sayfa bozmak için kullanılmaz.

## 75. SQLite dili

SQLite, tek dosyada duran veritabanıdır. Tablo ve sorgu SQL ile yazılır. Ayrı bir veritabanı sunucusu gerekmez. Uygulama ekranı bu dosyada yazılmaz.

## 76. SQLite dosya düzeni

Veri data/uygulama.db olarak durur. Tablo kuran SQL data/sema.sql içindedir. Veritabanı dosyası kaynak kodla karışmaz.

## 77. SQLite çalıştırma

SQLite aracı dosyayı açar ve SQL okur. El şemayı metin olarak okur. Veritabanını kendiliğinden açmaz ve çalıştırmaz.

## 78. SQLite sınama

Sınama, bilinen satır sayısının sorgudan dönmesidir. Deneme kopyası ayrı dosyadadır. Bu sınama başkasının veritabanını açmaz.

## 79. HTML sözdizimi

HTML etiketlerle kurulur. Etiket açılır, içine metin veya başka etiket girer, kapanır. Belge html köküdür; head görünmeyen bilgiyi, body görüneni taşır. Nitelik etiketinin içinde ad="değer" biçiminde durur.

## 80. HTML türleri

HTML'de sayı veya dize türü yoktur. İçerik metindir. Bağlantı, görsel ve düğme ayrı etiketlerdir: a, img, button. Başlıklar h1'den h6'ya kadar sıradır. Boş etiketler img, meta ve link kendi kendine kapanır.

## 81. HTML ataması

HTML'de değişken atanmaz. Görünen metin etiketin içine yazılır. Bağlantının hedefi href, görselin yolu src, düğmenin yazısı kendi içindedir. Aynı iş ikinci kez yazılırsa sayfada iki kez durur.

## 82. HTML fonksiyonu

HTML'de fonksiyon yoktur. Tekrar eden parça ya yeniden yazılır ya da JavaScript ile kurulur. Form, alanları bir arada tutar; gönderme adresi action niteliğindedir. Hesap bu dosyada yapılmaz.

## 83. HTML koşulu

HTML koşul çalıştırmaz. Bir blok ya belgededir ya yoktur. Görünüp gizlenme CSS veya JavaScript işidir. Zorunlu alan, input üzerinde required niteliğiyle işaretlenir; karar yine betiğe kalır.

## 84. HTML döngüsü

HTML döngü kurmaz. Liste li etiketlerinin elle yazılmasıdır. Yüz satırı betik veya sunucu üretir. Şablon döngüsü bu dilin parçası değildir.

## 85. HTML veri yapısı

Veri, etiket ağacıdır. ul ve ol liste, table satır ve hücre, form alan taşır. Başlık ile gövde ayrıdır. Ağaç yanlış kapanırsa tarayıcı kendi düzeltmesini yapar ve görünüş kayar.

## 86. HTML modülü

HTML modül sistemine sahip değildir. Başka dosya link, script ve img ile bağlanır. Yol görelidir: css/site.css, js/site.js. Başka bir sayfaya a etiketi gider.

## 87. HTML hatası

Hata çoğunlukla kapanmayan etiket, yanlış yol ve eksik alt metnidir. Tarayıcı sayfayı yine çizer; kırık görsel ve boş bağlantı sınamada görünür. Ayrı bir derleme hatası yoktur.

## 88. HTML standart kütüphanesi

Çekirdek etiketler: html, head, body, title, meta, h1, p, a, img, ul, ol, li, table, form, input, button, section, main. Bunlar iskelet içindir. Stil ve davranış buraya yazılmaz.

## 89. HTML sınırı

El, kilitli klasörde bilinen şablonla sayfa yazar ve yazıyı geri okur. Etiketi kendiliğinden uydurup çalıştırmaz. Sunucuya koymaz, formu kalıcı kaydetmez.

## 90. CSS sözdizimi

CSS kuralı seçici ve bildirim bloğundan oluşur. Seçici kutuyu tutar, bildirim özellik ve değerdir. Kurallar sırayla okunur; aynı özgüllükte sonra gelen kazanır. Yorum /* */ arasındadır.

## 91. CSS türleri

CSS'de program türü yoktur. Değer renk, uzunluk, yazı adı veya anahtar sözcüktür. Uzunluk px, rem veya yüzde olur. Renk ad, hex veya rgb ile yazılır. Yanlış değer yok sayılır, sayfa çökmez.

## 92. CSS ataması

Atama, bir özelliğe değer vermektir: color, margin, font-size. Değişken özel özelliktir, --ad biçiminde tanımlanır ve var(--ad) ile okunur. HTML metnini CSS değiştirmez.

## 93. CSS fonksiyonu

CSS'de fonksiyon, rengi ve hesabı değerin içinde üretir: rgb(), calc(). Sayfa davranışı yazılmaz. Tekrar eden görünüş sınıf adında toplanır. Sınıf HTML'de class ile bağlanır.

## 94. CSS koşulu

Koşul, media sorgusudur. Dar ekran ayrı kural alır. Ayrıca :hover ve :focus gibi durum seçicileri vardır. Bunlar program koşulu değil, tarayıcının gördüğü durumdur.

## 95. CSS döngüsü

Döngü yoktur. Tekrar, aynı sınıfı birden çok kutuya vermektir. Çok öğeyi dizmek flex veya grid işidir. Listeyi üretmek HTML veya JavaScript'tedir.

## 96. CSS veri yapısı

Kutu modeli içerik, iç boşluk, çerçeve ve dış boşluktur. flex satır veya sütun dizer. grid satır ve sütun ızgarası kurar. Akış normalde yukarıdan aşağıdır.

## 97. CSS modülü

Başka dosya @import ile çağrılabilir; tercih, HTML head içinde sırayla link vermektir. Sonra gelen dosya öncekini ezer. Ortak kural ayrı, sayfa kuralı ayrı dosyada durur.

## 98. CSS hatası

Hata, seçicinin hiçbir kutuyu tutmaması veya yolun bozuk olmasıdır. Stil gelmez, belge durur. Yazım yanlışı olan bildirim yok sayılır. Tarayıcı araçları hangi kuralın kazandığını gösterir.

## 99. CSS standart kütüphanesi

Sık özellikler: color, background, font, margin, padding, border, width, display, position, flex, grid, gap. Seçiciler eleman, sınıf ve kimliktir. Animasyon ayrı bir iştir, ilk raflarda zorunlu değildir.

## 100. CSS sınırı

El, şablondaki site.css dosyasını yazar ve metnini okur. Seçiciyi kendiliğinden üretip tarayıcıda çalıştırmaz. Başkasının sayfasına kural basmaz.

## 101. JavaScript sözdizimi

JavaScript ifadelerden ve bloklardan kurulur. Deyim noktalı virgülle bitebilir. Blok süslü parantez içindedir. Yorum // veya /* */ olur. İsim harf, alt çizgi veya dolarla başlar.

## 102. JavaScript türleri

Temel türler sayı, metin, mantıksal, null, undefined ve semboldür. Nesne ve dizi referanstır. typeof operatörü türün adını verir. Sayı ayrı bir tamsayı türü değildir; hepsi Number'dır.

## 103. JavaScript ataması

let ve const ad bağlar. const yeniden atanmaz, let atanır. var eski biçimdir, fonksiyon kapsamı taşır. Atama = işaretidir. Eşitlik karşılaştırması === tercih edilir; == tür de çevirir.

## 104. JavaScript fonksiyonu

Fonksiyon function ad() veya ok işlevi () => ile yazılır. Parametre parantezdedir. return değeri verir. Fonksiyon da bir değerdir, değişkene konabilir. Saf fonksiyon aynı girdiye aynı çıktıyı verir.

## 105. JavaScript koşulu

if koşulu parantezde, gövde süslü parantezdedir. else alternatif, else if ek koşuldur. Üçlü operatör koşul ? a : b kısa seçimdir. Koşul hesaplanır, kendiliğinden dosya yazmaz.

## 106. JavaScript döngüsü

for sayaçla, while koşul doğru olduğu sürece, for...of dizinin öğeleriyle döner. break döngüyü keser, continue sonraki tura geçer. Sonsuz döngü sayfayı kilitler; koşul bir yerde yanlış olmalıdır.

## 107. JavaScript veri yapısı

Dizi sıralı listedir: push, pop, map, filter. Nesne ad-değer tutar. Map ve Set ayrı koleksiyonlardır. Metin değişmezdir; yöntem yeni metin döndürür. JSON.parse metni nesneye, JSON.stringify tersine çevirir.

## 108. JavaScript modülü

Tarayıcıda başka dosya script etiketiyle bağlanır. import ve export ancak modül olarak işaretlenmiş betikte geçerlidir. Node ortamında require veya import paket bağlar. document yalnız tarayıcıdadır.

## 109. JavaScript hatası

Hata throw ile atılır, try ve catch ile tutulur. Tutulmayan hata konsola düşer ve o çağrıyı keser. TypeError yanlış türde işlem, ReferenceError tanımsız addır. finally her durumda çalışır.

## 110. JavaScript standart kütüphanesi

Dilde hazır olanlar: Object, Array, String, Number, Math, JSON, Date, Map, Set, Promise. Tarayıcı ekler: document, window. Ağ isteği fetch ile yapılır; el bunu kendiliğinden çağırmaz.

## 111. JavaScript sınırı

El, şablondaki site.js metnini yazar ve okur. Betiği kendiliğinden çalıştırmaz. eval, ağ isteği ve başkasının sayfasına yazma bu elin işi değildir.

## 112. TypeScript sözdizimi

TypeScript, JavaScript sözdiziminin üzerine tür yazar. Değişken, parametre ve dönüş türü iki nokta ile belirtilir. Derleyici türü siler, ortaya JavaScript çıkar. Yorum ve blok JavaScript ile aynıdır.

## 113. TypeScript türleri

number, string, boolean, null ve undefined temel türlerdir. any denetimi kapatır, unknown önce daraltmayı ister. Dizi türü T[] veya Array<T> olur. union A | B iki türden birini kabul eder.

## 114. TypeScript ataması

let ve const JavaScript ile aynıdır; türe aykırı atama derlemede durur. Tür çıkarımı ilk değerden türü bulur. as ile yapılan zorlama son çaredir, yanlışsa çalışma anına hata kalır.

## 115. TypeScript fonksiyonu

Fonksiyonun parametre ve dönüş türü yazılır. Arayüz veya type ile nesnenin şekli adlandırılır. Ok işlevi de tür alır. Generic, türü çağıran yere bırakır: fonksiyon<T>(x: T).

## 116. TypeScript koşulu

if ile yapılan tür daraltması, blok içinde daha ince tür gösterir. instanceof ve in operatörü de daraltır. Koşulun kendisi JavaScript'tir; tür yalnız derlemede vardır.

## 117. TypeScript döngüsü

Döngüler JavaScript ile aynıdır: for, while, for...of. Tür, döngü değişkenine de yazılır. Dizi yöntemleri map ve filter türü taşır. Sonsuz döngü aynı tehlikeyi taşır.

## 118. TypeScript veri yapısı

Dizi, nesne, tuple ve enum veri biçimidir. Readonly diziye sonradan öğe eklenmez. interface genişletilir, type kesişim ile birleşir. JSON sınırı unknown olarak okunur, sonra daraltılır.

## 119. TypeScript modülü

import ve export modül bağlar. Tür yalnız import type ile de alınabilir. tsconfig hangi klasörün derleneceğini söyler. Çıktı .js dosyasıdır; HTML onu çağırır.

## 120. TypeScript hatası

Derleme hatası dosyaya yazılmadan önce görünür. Çalışma hatası yine throw ve try ile tutulur. strict ayarı null ve implicit any kaçaklarını kapatır. Hata metni dosya ve satır taşır.

## 121. TypeScript standart kütüphanesi

Dil ekleri: Partial, Pick, Omit, Record, ReturnType. Çalışma kütüphanesi JavaScript'tir. Tarayıcı ve Node API'leri tür paketleriyle tarif edilir. El bu paketleri kendiliğinden indirmez.

## 122. TypeScript sınırı

El, TypeScript kartını okur. Kendiliğinden .ts yazıp derlemez ve çalıştırmaz. Tür hatasını karttaki kurala göre söyler, uydurma API yazmaz.

## 123. Python sözdizimi

Python girintiyle blok kurar. Dört boşluk standarttır. Satır bir deyimdir. Yorum # ile başlar. İki nokta if, for, def ve class satırının sonundadır. Parantez içindeki ifade satır kırabilir.

## 124. Python türleri

int, float, str, bool, None temel değerlerdir. list, dict, tuple, set koleksiyondur. type(x) türü verir. Metin ile sayıyı + birleştirmez; önce çevirmek gerekir. bool, True ve False'tur.

## 125. Python ataması

Ad = değer ile bağlanır. Aynı ada yeni değer verilebilir. Çoklu atama a, b = 1, 2 biçimindedir. Büyük harfli ad sabit niyetini söyler, dil zorlamaz. Fonksiyon içindeki atama o adı yerel yapar.

## 126. Python fonksiyonu

def ad(parametre): fonksiyon açar. Dönüş return iledir. Varsayılan parametre soldan sağa gelir. *args fazla konumu, **kwargs fazla adı toplar. Docstring fonksiyonun ilk satırındaki üç tırnaktır.

## 127. Python koşulu

if koşul: gövde girintidedir. elif ek koşul, else kalandır. Karşılaştırma ==, !=, <, >, <=, >= ve in olur. and, or, not mantığı bağlar. Koşul doğruysa yalnız o blok çalışır.

## 128. Python döngüsü

for öğe in dizi: her öğeyi bir kez verir. while koşul: koşul doğru kaldıkça döner. range(n) sıfırdan n-1'e sayar. break çıkar, continue turu atlar. İç döngü dışın içinde girintilenir.

## 129. Python veri yapısı

list sıralı ve değişkendir. tuple sıralı ve değişmezdir. dict anahtar-değer tutar. set benzersiz öğe tutar. Metin değişmezdir; yöntem yeni metin döndürür. Dilim a[baş:son] kopya alır.

## 130. Python modülü

import modul adresi yükler. from modul import ad tek adı alır. Paket klasöründe __init__.py durabilir. Göreli içe alma paketinin içinden yapılır. El, içe alma adını okur, modülü kendiliğinden çalıştırmaz.

## 131. Python hatası

Hata bir istisnadır. try bloğu dener, except türü tutar, else hata yoksa, finally her durumda çalışır. raise hata fırlatır. SyntaxError ayrıştırmaz, NameError tanımsız ad, TypeError yanlış tür, ValueError yanlış değerdir.

## 132. Python standart kütüphanesi

Sık standart modüller: pathlib yol, json metin veri, sqlite3 tek dosya veritabanı, datetime tarih, re desen, math sayı, collections ek koleksiyon, argparse komut argümanı. Ağ ve süreç modülleri elin kendiliğinden çağırdığı yer değildir.

## 133. Python sınırı

El, kilitli klasördeki .py dosyasını ağaçla okur: imza, dönüş, çağrı, satır, atama, koşul, sınıf, içe alma. Şablon arac.py yazar. Kodu çalıştırmaz, eval etmez, uygulama klasörüne yazmaz.

## 134. SQL sözdizimi

SQL bildirimseldir. Cümle bir fiille başlar: SELECT, INSERT, UPDATE. Sözcükler büyük yazılabilir; anlam değişmez. Metin tek tırnak içindedir. Noktalı virgül cümleyi bitirir. Yorum -- veya /* */ olur.

## 135. SQL türleri

Sütun türü tabloda tanımlanır: tamsayı, metin, gerçek sayı, tarih, mantıksal. NULL bilinmeyen değerdir; boş metinle aynı değildir. Karşılaştırma NULL ile = değil, IS NULL ile yapılır.

## 136. SQL ataması

INSERT satıra değer koyar, UPDATE mevcut satırın sütununu değiştirir. SET soluna sütun, sağına değer gelir. WHERE yoksa UPDATE bütün satırlara gider; bu yüzden koşul yazılır. El silme cümlesi kurmaz.

## 137. SQL fonksiyonu

İş birimi sorgudur, fonksiyon değildir. SELECT sütun seçer, FROM tabloyu söyler. Fonksiyon varsa motorun kendi işlevidir: COUNT, SUM, AVG. Kullanıcı fonksiyonu bu rafın konusu değildir.

## 138. SQL koşulu

WHERE satırı süzer. AND ve OR koşulları bağlar. Parantez önceliği belirler. JOIN iki tabloyu ortak sütunda birleştirir. HAVING, gruplandıktan sonraki koşuldur; WHERE gruplamadan öncedir.

## 139. SQL döngüsü

Döngü yazılmaz. Motor satırların üzerinde kendisi yürür. GROUP BY aynı değere sahip satırları bir kovada toplar. ORDER BY sırayı söyler. LIMIT kaç satır döneceğini keser.

## 140. SQL veri yapısı

Veri tablodur: satır ve sütun. Anahtar satırı benzersiz tutar. Yabancı anahtar başka tabloya işaret eder. Görünüm, saklanmış bir SELECT'tir. Dizin aramayı hızlandırır, verinin kendisi değildir.

## 141. SQL modülü

Başka sorgu alt sorgu olarak paranteze girer. Şema dosyası tabloyu kurar, seçme dosyası okur. Uygulama kodu sorguyu metin olarak taşır. İki iş aynı dosyada karışırsa okumak zorlaşır.

## 142. SQL hatası

Hata, olmayan sütun, tür uyuşmazlığı ve boş gruplamadır. Motor cümleyi reddeder, tablo durur. Belirsiz sütun adı tablo adıyla nitelenir. El, hata metnini okur, veritabanını kendiliğinden açmaz.

## 143. SQL standart kütüphanesi

Çekirdek sözcükler: SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, INSERT, UPDATE, CREATE TABLE. COUNT ve SUM hesaptır. SQLite bu sözcüklerin küçük gömülü motorudur.

## 144. SQL sınırı

El, SQL kartını ve şema metnini okur. Sorguyu kendiliğinden çalıştırmaz. Başkasının veritabanına bağlanmaz. Silme ve yetki değiştirme bu elde yoktur.

## 145. Bash sözdizimi

Bash satır satır okunur. İlk satırdaki #! yorumlayıcıyı söyler. # yorumdur. Komut, boşlukla ayrılmış sözcüklerdir. Tırnak, boşluklu metni bir sözcük yapar. Çift tırnak değişkeni açar, tek tırnak açmaz.

## 146. Bash türleri

Tür sistemi yoktur. Her değer metindir. Sayı hesabı $(( )) içine yazılır. Boş metin ile atanmamış ad ayrıdır. Çıkış kodu 0 başarı, sıfırdan başka değer başarısızlıktır.

## 147. Bash ataması

ad=değer boşluksuz atanır. Okuma $ad veya ${ad} iledir. export adı çocuk sürece taşır. Boşluklu değer tırnaklanır. El, atamayı okur; betiği kendiliğinden çalıştırmaz.

## 148. Bash fonksiyonu

fonksiyon() { komutlar; } işi adlandırır. return çıkış kodu verir, metin döndürmez; metin echo ile basılır. Yerel ad local ile sınırlanır. Parametreler $1, $2 sırasıdır.

## 149. Bash koşulu

if komut; then gövde; fi biçimindedir. Koşul çoğunlukla [ ] veya [[ ]] testidir. -f dosya var mı, -d klasör mü diye bakar. else ve elif alternatif tutar. Test, dosyayı silmez.

## 150. Bash döngüsü

for ad in liste; do gövde; done her sözcükte döner. while koşul; do gövde; done koşul sürdükçe döner. break çıkar. Liste, kendi klasöründeki adlar olabilir. Başka makinenin listesi bu notta yoktur.

## 151. Bash veri yapısı

Veri metin ve dosyadır. Dizi dizi=(a b) ile kurulur. Boru | bir komutun çıktısını sonrakinin girdisi yapar. Dosya yönlendirme > yazmayı, >> eklemeyi anlatır. El, silme yönlendirmesi kurmaz.

## 152. Bash modülü

Başka betik source veya . ile aynı sürece alınır. Ayrı süreç olarak adıyla çağrılır. PATH, komutun aranacağı klasörleri tutar. Betik kendi klasöründe durur.

## 153. Bash hatası

set -e hata olan komutta durabilir. $? son çıkış kodudur. Hata metni standart hataya gider. Tutmak için komut || yedek yazılır. El, hatayı karttan söyler, betiği çalıştırmaz.

## 154. Bash standart kütüphanesi

Sık işler: echo bas, cd klasör değiştir, pwd yerini söyle, ls adları listele, mkdir klasör aç, cp kopyala. Bulma ve akış: grep, sed, awk. Silme komutu bu kartta tarif edilmez.

## 155. Bash sınırı

El, Bash kartını okur. Kilitli klasörün dışına çıkmaz, betiği kendiliğinden çalıştırmaz, uzaktaki makineye komut yazmaz.

## 156. PowerShell sözdizimi

PowerShell cmdlet'leri Fiil-Ad biçimindedir. Satır bir komuttur. # yorumdur. Blok süslü parantezdedir. Değişken $ ile başlar. Metin çift tırnakta değişkeni açar.

## 157. PowerShell türleri

Değer nesnedir, yalnız metin değildir. Sayı, metin, tarih ve dosya bilgisi ayrı türler olarak taşınır. $null boş değerdir. Tür, GetType ile sorulur. Boru nesneyi metne çevirmeden geçirebilir.

## 158. PowerShell ataması

$ad = değer atar. Özellik nokta ile okunur. Ortam değişkeni $env:AD biçimindedir. Atama bir nesneyi bağlar. El atamayı okur, komutu kendiliğinden çalıştırmaz.

## 159. PowerShell fonksiyonu

function Ad { param($x) gövde } işi adlandırır. Dönüş, çıktıya yazılan nesnedir. return hem yazar hem çıkar. İleri düzey parametre bu rafın ilk katıdır; zorunlu alan param bloğunda durur.

## 160. PowerShell koşulu

if (koşul) { } elseif { } else { } biçimindedir. Karşılaştırma -eq, -ne, -lt, -gt ile yazılır. -and ve -or bağlar. Test-Path yol var mı diye bakar, silmez.

## 161. PowerShell döngüsü

foreach ($öğe in $liste) { } her öğede döner. ForEach-Object boru üstünde döner. while (koşul) { } sürdürür. break çıkar. Liste kendi klasörünün nesneleridir.

## 162. PowerShell veri yapısı

Dizi @() ve hashtable @{ad=değer} veri tutar. Boru | nesneyi sonraki cmdlet'e verir. Where-Object süzer, Select-Object sütun seçer. Dosya Get-Content ile okunur, Set-Content ile yazılır.

## 163. PowerShell modülü

Başka betik nokta ile aynı kapsama alınır veya & ile ayrı çağrılır. Modül Import-Module ile gelir. Betik .ps1 dosyasıdır. El modülü kendiliğinden yüklemez.

## 164. PowerShell hatası

Hata ErrorAction ile sürer veya durur. try, catch, finally tutulur. throw hata fırlatır. Kırmızı metin hata akışıdır. El hatayı okur, betiği çalıştırmaz.

## 165. PowerShell standart kütüphanesi

Sık cmdlet'ler: Get-ChildItem liste, Get-Content oku, Set-Content yaz, Where-Object süz, ForEach-Object dön, Test-Path bak, Join-Path yol birleştir. Kaldırma cmdlet'i bu kartta tarif edilmez.

## 166. PowerShell sınırı

El, PowerShell kartını okur. Windows betiğini kendiliğinden çalıştırmaz. Kilitli klasörün dışına ve uzaktaki oturuma komut yazmaz.

## 167. Java sözdizimi

Java sınıf dosyasında durur. Her deyim noktalı virgülle biter. Blok süslü parantezdedir. public class Ad dosya adıyla aynıdır. Yorum // veya /* */ olur. Paket ilk satırda bildirilir.

## 168. Java türleri

İlkel türler int, long, double, boolean, char'tır. String nesnedir, ilkel değildir. Dizi sabit uzunlukta T[] olur. ArrayList büyür. null referans yoktur. Tür derlemede denetlenir.

## 169. Java ataması

Tür ad = değer; atar. Aynı adı yeniden atamak tür uygunsa geçerlidir. final yeniden bağlamaz. Alan sınıfın içindedir, yerel ad metodun içindedir. this o nesneyi gösterir.

## 170. Java fonksiyonu

DönüşTürü ad(parametreler) { } metot açar. void dönüşsüzdür. return değeri verir. Aşırı yükleme aynı adın başka parametre listesidir. static metot nesne kurmadan çağrılır.

## 171. Java koşulu

if (koşul) { } else if { } else { } biçimindedir. switch değer seçer. Karşılaştırma sayılarda ==, metinde equals ile yapılır. && ve || kısa devre yapar. Koşul yan etki taşıyorsa okumak zorlaşır.

## 172. Java döngüsü

for (başlangıç; koşul; adım) klasik sayaçtır. for (Tür ö : dizi) her öğeyi verir. while ve do-while koşulla döner. break çıkar, continue turu atlar. İç döngü etiketle de kırılabilir.

## 173. Java veri yapısı

Dizi, List, Set ve Map temel koleksiyonlardır. List sıra tutar, Set benzersiz tutar, Map anahtar-değer tutar. String değişmezdir. record basit veri taşıyıcısıdır. Sınıf hem veri hem metot tutar.

## 174. Java modülü

package adı klasörle aynı yolu izler. import türün adını kısaltır. Aynı paketteki tür import istemez. Modül sistemi module-info ile sınır çizer. El, import satırını okur, paketi çalıştırmaz.

## 175. Java hatası

Kontrol edilen istisna imzada bildirilir. try, catch, finally tutulur. throw fırlatır. RuntimeException bildirim istemez. NullPointerException boş referans, derleme hatası ise hiç sınıf üretmez.

## 176. Java standart kütüphanesi

java.lang her zaman görünür: String, Math, Object. java.util koleksiyon, java.io ve java.nio dosya, java.time tarih, java.net ağ. El ağ ve süreç sınıflarını kendiliğinden çağırmaz.

## 177. Java sınırı

El, Java kartını okur. .java metnini kendiliğinden derlemez ve çalıştırmaz. Uygulama klasörüne sınıf yazmaz.

## 178. C# sözdizimi

C# deyimleri noktalı virgülle biter. Blok süslü parantezdedir. Ad alanı namespace ile açılır. Sınıf class, dosya çoğunlukla sınıf adını taşır. Yorum // veya /* */ olur.

## 179. C# türleri

int, long, double, decimal, bool, char ve string sık türlerdir. string değişmezdir. Dizi T[] sabit, List<T> büyür. null referans türlerinde ayrıca işaretlenir. var ilk değerden tür çıkarır.

## 180. C# ataması

tür ad = değer; atar. const derleme sabiti, readonly alan kurulurken bağlanır. Atama tür uymazsa derleme durur. Özellik get ve set ile alana kapı olur.

## 181. C# fonksiyonu

DönüşTürü Ad(parametre) { } metot açar. void dönüşsüzdür. İfade gövdeli üye => ile tek satır döner. Aşırı yükleme parametreyle ayrılır. static sınıf adına aittir.

## 182. C# koşulu

if, else if, else ve switch seçer. Desen eşleme switch ifadesinde tür ve şekle bakar. && ve || kısa devre yapar. Koşul parantez içindedir.

## 183. C# döngüsü

for, foreach, while ve do döngü kurar. foreach koleksiyonun öğesinde yürür. break ve continue aynı işi görür. await döngünün içinde varsa metot async olmalıdır.

## 184. C# veri yapısı

Dizi, List, Dictionary ve HashSet koleksiyondur. record değer taşıyan türdür. tuple birden çok dönüşü adsız taşır. LINQ sorgusu koleksiyonu süzüp seçer, kaynağı kendiliğinden silmez.

## 185. C# modülü

namespace türleri gruplar. using satırı adı kısaltır. Proje dosyası hangi kaynakların birlikte derleneceğini söyler. Başka proje referansla bağlanır. El paketi kendiliğinden indirmez.

## 186. C# hatası

try, catch, finally ve throw hata tutar. Exception tabandır. await hataları da aynı yolla çıkar. Derleme hatası dosya ve satır verir. null bağışlanmayan türe null vermek derlemede durur.

## 187. C# standart kütüphanesi

System temel türleri, System.Collections.Generic koleksiyonu, System.IO dosyayı, System.Linq sorguyu, System.Text.Json metin veriyi taşır. Ağ ve süreç adları elin kendiliğinden çağırdığı yer değildir.

## 188. C# sınırı

El, C# kartını okur. .cs metnini kendiliğinden derlemez ve çalıştırmaz. Çözümü uygulama klasörüne yazmaz.

## 189. C++ sözdizimi

C++ deyimleri noktalı virgülle biter. Blok süslü parantezdedir. #include başlık çeker, ön işlem satırıdır. Yorum // veya /* */ olur. main programın girişidir. Ad büyük-küçük harf duyarlıdır.

## 190. C++ türleri

int, double, bool, char ve işaretçiler temeldir. std::string metin nesnesidir. auto ilk değerden tür çıkarır. const söz verir, değiştirilmez. Referans & bir ada takma ad olur, kopyalamaz.

## 191. C++ ataması

tür ad = değer; veya tür ad{değer}; atar. İşaretçi bir adres tutar. Sahip olan işaretçi ile ödünç alan referans ayrı niyettir. El, sahipliği karttan söyler, programı çalıştırmaz.

## 192. C++ fonksiyonu

DönüşTürü ad(parametre) { } fonksiyon açar. Referansla geçiş kopyayı önler. Şablon template <typename T> türü çağrıya bırakır. Sınıf metodu nesnenin üstündedir. inline başlıkta kısa fonksiyon içindir.

## 193. C++ koşulu

if, else ve switch seçer. Koşul parantezdedir. && ve || kısa devre yapar. Üçlü operatör kısa seçimdir. Derleme koşulu #if ayrıdır; program koşulu değildir.

## 194. C++ döngüsü

for, while ve do döngü kurar. Aralık tabanlı for (öğe : dizi) kapları dolaşır. break ve continue aynı işi görür. İşaretçi aritmetiği bu rafın örnek konusu değildir.

## 195. C++ veri yapısı

std::vector büyüyen dizi, std::string metin, std::map sıralı anahtar, std::unordered_map karma anahtardır. Dizi T a[n] sabit boydadır. Akıllı işaretçi unique_ptr tek sahip tutar.

## 196. C++ modülü

Başlık .h veya .hpp arayüzü, .cpp gövdeyi taşır. include koruması aynı başlığın iki kez açılmasını keser. Ad alanı namespace çakışmayı ayırır. Derleme tarifi kaynakları birbirine bağlar.

## 197. C++ hatası

İstisna throw, try ve catch ile tutulur. Tutulmayan istisna programı düşürür. Derleme hatası tür uyuşmazlığı ve eksik bildiridir. Tanımsız davranış bu kartta tarif edilmez; el onu örneklemez.

## 198. C++ standart kütüphanesi

iostream giriş-çıkış, vector, string, map, algorithm ve filesystem sık başlıklardır. C başlıkları da durur. Algoritma başlığı sıralama ve arama verir. El bu başlıkları kendiliğinden derlemez.

## 199. C++ sınırı

El, C++ kartını okur. Kaynağı kendiliğinden derlemez ve çalıştırmaz. Bellek bozma ve saldırı kodu yazmaz.

## 200. C sözdizimi

C deyimleri noktalı virgülle biter. Blok süslü parantezdedir. #include başlık çeker. main giriş noktasıdır. Yorum /* */ veya // olur. Bildirim kullanılmadan önce görünür.

## 201. C türleri

int, char, float, double ve işaretçi temel türlerdir. Dizi, aynı türden bitişik hücredir. struct alanları bir arada tutar. Ayrı bir metin türü yoktur; metin char dizisi ve sonda sıfır baytıdır. void dönüşsüz veya türsüz işaretçidir.

## 202. C ataması

tür ad = değer; atar. İşaretçi adres tutar, * ile gösterdiği yere bakılır. & adresini alır. Dizi adı ilk elemanın adresine dönüşür. El atamayı okur, programı çalıştırmaz.

## 203. C fonksiyonu

DönüşTürü ad(parametreler) { } fonksiyon açar. Parametre değerle geçilir; dizide adres geçilir. Prototip başlıkta durur, gövde .c dosyasındadır. return değeri verir.

## 204. C koşulu

if, else ve switch seçer. Koşul parantez içindedir, sıfır yanlış, başka her sayı doğrudur. && ve || kısa devre yapar. switch case etiketleri break ile kesilmezse alta düşer.

## 205. C döngüsü

for, while ve do döngü kurar. for (i = 0; i < n; i++) klasik sayaçtır. break çıkar, continue turu atlar. Sınır, dizinin uzunluğundan ayrıca bilinmelidir; dil uzunluğu taşımaz.

## 206. C veri yapısı

Dizi sabit boydadır. struct kayıt, union aynı bellek üstünde birden çok görünümdür. Metin kütüphane işlevleriyle kopyalanır. Dinamik bellek malloc ile istenir, free ile geri verilir. El bu çağrıları çalıştırmaz.

## 207. C modülü

Başlık .h bildirim, .c tanım taşır. include koruması çift almayı keser. Başka dosyanın fonksiyonu başlıkta ilan edilir. Derleyici dosyaları ayrı çevirir, bağlayıcı birleştirir.

## 208. C hatası

Ayrı bir istisna yoktur. Hata çoğunlukla dönüş kodu ve errno ile söylenir. NULL boş işaretçidir. Derleme uyarısı tür ve imza uyuşmazlığını gösterir. Taşma ve serbest bırakılmış belleği kullanmak bu kartta örneklenmez.

## 209. C standart kütüphanesi

stdio.h giriş-çıkış, stdlib.h genel araç ve bellek, string.h metin, math.h sayı başlıklarıdır. printf biçimli basar, fopen dosya açar. El bu işlevleri kendiliğinden çağırmaz.

## 210. C sınırı

El, C kartını okur. Kaynağı kendiliğinden derlemez ve çalıştırmaz. Bellek bozma kodu yazmaz.

## 211. Rust sözdizimi

Rust deyimleri noktalı virgülle biter. Blok süslü parantezdedir ve bir değer verebilir. let ad bağlar. Yorum // veya /* */ olur. Fonksiyon fn ile açılır. main giriş noktasıdır.

## 212. Rust türleri

i32, i64, u32, f64, bool, char ve &str temeldir. String sahip olunan metindir. Option bazı veya hiç, Result tamam veya hatadır. Tür çıkarımı let satırında çalışır. null yoktur.

## 213. Rust ataması

let ad = değer; bağlar. let mut değişebilir bağlar. Atama, sahipliği taşır; kopya türleri kopyalanır. Ödünç & okur, &mut yazar. Aynı anda bir yazan veya çok okuyan olur.

## 214. Rust fonksiyonu

fn ad(parametre: Tür) -> Dönüş { } fonksiyon açar. Son ifadede noktalı virgül yoksa o değer döner. Metot impl bloğunda türün üstüne yazılır. Generic <T> türü çağrıya bırakır.

## 215. Rust koşulu

if koşul { } else { } değer de verebilir. Koşul bool olmalıdır, sayı yetmez. match her dalı örter. if let tek deseni açar. Eksik dal derlemede durur.

## 216. Rust döngüsü

loop sonsuz döngüdür, break ile çıkar. while koşul sürdürür. for öğe in koleksiyon yineleyicide yürür. continue turu atlar. Yineleyici map ve filter ara koleksiyon da kurabilir.

## 217. Rust veri yapısı

struct alanlı kayıt, enum ayrı varyantlar, Vec büyüyen dizi, HashMap anahtar-değerdir. Dilim &[T] bir dizinin görünümüdür. String sahip olur, &str ödünç alır. tuple birden çok türü yan yana tutar.

## 218. Rust modülü

mod dosyayı veya bloğu modül yapar. use adı içeri alır. pub görünür kılar. Cargo.toml paket adı ve bağımlılığı söyler. crate kökü src/main.rs veya src/lib.rs olur.

## 219. Rust hatası

Kurtarılabilir hata Result döndürür. ? operatörü hatayı yukarı verir. panic durdurulamaz hatada düşer. Derleyici ödünç ve tür hatalarını çalışmadan söyler. El, panic örneğini saldırıya çevirmez.

## 220. Rust standart kütüphanesi

std::fs dosya, std::io akış, std::collections koleksiyon, std::net ağ, std::env ortam adlarıdır. Ağ elin kendiliğinden açtığı yer değildir. Dış kasa Cargo ile bağlanır, el indirmez.

## 221. Rust sınırı

El, Rust kartını okur. .rs metnini kendiliğinden derlemez ve çalıştırmaz. unsafe blok yazmaz.

## 222. PHP sözdizimi

PHP bloğu <?php ile açılır. Deyimler noktalı virgülle biter. Değişken $ ile başlar. Yorum // veya /* */ olur. HTML ile aynı dosyada durabilir; PHP parçası sunucuda hesaplanır, tarayıcıya sonuç gider.

## 223. PHP türleri

Değerler null, bool, int, float, string, dizi ve nesnedir. Tür bildirmek isteğe bağlıdır, declare strict_types ile sıkılaşır. Dizi hem liste hem eşlemedir. string değişkendir.

## 224. PHP ataması

$ad = değer; atar. Dizi elemanı $a[anahtar] ile yazılır. Referans & ile takma ad olur. Global ad fonksiyonun içinde global ile görülür. El atamayı okur, sayfayı çalıştırmaz.

## 225. PHP fonksiyonu

function ad($parametre) { } fonksiyon açar. Dönüş return iledir. Tür yazılırsa parametre ve dönüş daralır. Anonim fonksiyon değişkene konur. Sınıf metodu nesnenin üstündedir.

## 226. PHP koşulu

if, elseif, else ve switch seçer. Karşılaştırma == tür çevirir, === tür de ister. && ve || bağlar. Koşul parantezde, gövde süslü parantezdedir.

## 227. PHP döngüsü

for, foreach, while ve do döngü kurar. foreach ($dizi as $anahtar => $değer) eşlemede yürür. break ve continue aynı işi görür. Listeyi üretmek döngünün işidir, HTML'e echo ile basılır.

## 228. PHP veri yapısı

Dizi [] ile kurulur. Liste ardışık anahtar, eşleme adlı anahtar tutar. Nesne sınıf örneğidir. Metin . operatörüyle birleşir. JSON fonksiyonları metin ve dizi arasında çevirir.

## 229. PHP modülü

include ve require başka dosyayı aynı isteğe alır. require yoksa durur. namespace ve use sınıf adını kısaltır. Autoload sınıf dosyasını ada göre bulur. El dosyayı kendiliğinden sunmaz.

## 230. PHP hatası

try, catch, finally ve throw hata tutar. Error ve Exception ayrı tabanlardır. Uyarı bazı eski çağrılarda düşer, istisna olmaz. Tür uyuşmazlığı strict modda durur.

## 231. PHP standart kütüphanesi

Dizi işlevleri, metin işlevleri, DateTime ve PDO sık araçlardır. PDO veritabanına hazır cümle ile gider. Ağ ve süreç işlevleri elin kendiliğinden çağırdığı yer değildir. Gizli anahtar koda yazılmaz.

## 232. PHP sınırı

El, PHP kartını okur. Dosyayı kendiliğinden sunucuda çalıştırmaz. Uzaktan istek ve kabuk çağrısı yazmaz.

## 233. Go sözdizimi

Go deyimleri ayrı satırdadır, noktalı virgül derleyicinin işidir. Blok süslü parantezdedir, açılış süslüsü satırın sonundadır. Yorum // veya /* */ olur. Kullanılmayan import derlemede durur. main paketi giriş taşır.

## 234. Go türleri

int, int64, float64, string, bool temeldir. byte ve rune özel sayılardır. İşaretçi *T adres tutar. nil dilim, harita, işaretçi ve arayüz için boş değerdir. Tür dönüşü açık yazılır, gizli çeviri yoktur.

## 235. Go ataması

ad := değer kısa bağlar ve türü çıkarır. var ad tür uzun bildirir. = mevcut ada atar. Çoklu dönüş a, b := f() biçimindedir. Atanmayan yerel ad derlemede durur.

## 236. Go fonksiyonu

func ad(parametre tür) dönüş { } fonksiyon açar. Çok değer dönebilir. Metot func (a Alıcı) Ad() biçimindedir. defer fonksiyon bitince çalışacak çağrıyı erteler. El çağrıyı kendisi yapmaz.

## 237. Go koşulu

if koşul { } parantezsizdir. else süslünün yanında durur. switch değer veya koşul seçer. Kısa bildirim if ad := f(); ad > 0 biçiminde koşula yerel ad bağlar.

## 238. Go döngüsü

for tek döngü sözcüğüdür. for i := 0; i < n; i++ sayaç, for koşul while yerine, for öğe := range koleksiyon yürür. break ve continue aynı işi görür. İç içe range kopya veya indeks verir.

## 239. Go veri yapısı

Dilim dinamik görünüm, dizi sabit boy, map anahtar-değer, struct kayıt, interface metot kümesidir. append dilimi büyütür. Metin değişmezdir. range haritada sıra garanti değildir.

## 240. Go modülü

package adı dosyanın paketidir. import yol getirir. Büyük harfle başlayan ad başka pakete görünür. go.mod modül yolunu söyler. İç paket internal/ altında dışarı kapalıdır.

## 241. Go hatası

Hata bir dönüş değeridir, çoğunlukla error arayüzü. if err != nil kalıbı hatayı yerinde söyler. panic düşer, recover defer içinde tutar. Derleme hatası kullanılmayan ad ve tür uyuşmazlığıdır.

## 242. Go standart kütüphanesi

fmt basma, os ortam ve dosya, io akış, strings ve strconv metin ve sayı, encoding/json veri, time tarih, net/http ağ servisi adlarıdır. El http sunucusunu kendiliğinden açmaz.

## 243. Go sınırı

El, Go kartını okur. .go metnini kendiliğinden derlemez ve çalıştırmaz. Modülü uygulama klasörüne yazmaz.

## 244. Kotlin sözdizimi

Kotlin deyimleri satır sonuyla ayrılabilir. Blok süslü parantezdedir. Noktalı virgül gerekmez. Yorum // veya /* */ olur. Paket dosyanın başında durur. main giriş fonksiyonudur.

## 245. Kotlin türleri

Int, Long, Double, Boolean ve String temeldir. String değişmezdir. Herhangi bir türün sonuna ? konursa null taşıyabilir. Null taşımayan türe null verilemez. Unit, anlamlı dönüş olmadığını söyler.

## 246. Kotlin ataması

val ad = değer bağlar ve yeniden atamaz. var yeniden atar. Tür çoğunlukla çıkarılır. Lateinit sonra dolacak alanı işaretler. ?. boşsa zinciri keser, ?: varsayılan verir.

## 247. Kotlin fonksiyonu

fun ad(parametre: Tür): Dönüş { } fonksiyon açar. Tek ifade = ile gövde olur. Varsayılan parametre ve adlandırılmış argüman vardır. Metot sınıfta aynı fun ile yazılır. data class eşitlik ve kopya üretir.

## 248. Kotlin koşulu

if bir ifadedir, değer verebilir. when dal seçer ve eksik dalı derlemede sorar. && ve || kısa devre yapar. Akıllı dönüş, if içinden sonra türü daraltır.

## 249. Kotlin döngüsü

for (öğe in koleksiyon) yürür. while ve do-while koşulla döner. Aralık 1..n kapalı, until yarı açıktır. break ve continue etiketle dış döngüyü de kesebilir. repeat(n) sabit kez döner.

## 250. Kotlin veri yapısı

List, Set ve Map salt okunur arayüz, MutableList değişendir. Dizi Array ayrıca durur. data class kayıt taşır. sealed class kapalı bir varyant ailesidir. Pair ve Triple küçük demetlerdir.

## 251. Kotlin modülü

package klasörle aynı olmak zorunda değildir. import adı kısaltır. Dosyanın üst düzey fonksiyonu pakete aittir. Gradle hangi kaynağın derleneceğini söyler. El bağımlılığı kendiliğinden indirmez.

## 252. Kotlin hatası

throw, try ve catch hata tutar. Denetlenen istisna zorunluluğu yoktur. Elvis ve ?. null hatasını azaltır. Derleme hatası tür ve null kaçaklarını söyler. El hatayı karttan okur.

## 253. Kotlin standart kütüphanesi

kotlin koleksiyonları, kotlin.io dosya yardımcıları ve kotlin.text metin araçları standarttır. Java standart kütüphanesi JVM üstünde durur. Android arayüz kitabı ayrıdır. El telefona paket kurmaz.

## 254. Kotlin sınırı

El, Kotlin kartını okur. .kt metnini kendiliğinden derlemez, telefona kurmaz ve çalıştırmaz.

## 255. JSON sözdizimi

JSON nesne ve diziden kurulur. Nesne süslü parantez, dizi köşeli parantezdir. Ad çift tırnakta, ardından iki nokta ve değer gelir. Öğeler virgülle ayrılır. Son öğeden sonra virgül yoktur. Yorum yoktur.

## 256. JSON türleri

Değerler nesne, dizi, metin, sayı, true, false ve null'dur. Metin çift tırnak ister, tek tırnak geçersizdir. Sayı tırnaksızdır. Tarih ve bayt için ayrı tür yoktur; metin olarak yazılır.

## 257. JSON ataması

Atama yoktur. Değer, anahtarın karşısına bir kez yazılır. Aynı anahtar iki kez yazılırsa okuyan araç sonuncuyu veya ilkini tutabilir; bu yüzden anahtar tek olur. El dosyayı kendiliğinden ayrıştırıp çalıştırmaz.

## 258. JSON fonksiyonu

Fonksiyon yoktur. JSON hesap yapmaz. İş, onu okuyan programdadır. Şema ayrı bir tarifse zorunlu anahtar orada söylenir. JSON Schema bu rafın tam metni değildir.

## 259. JSON koşulu

Koşul yoktur. Bir alan ya durur ya durmaz. Seçim, okuyan programın işidir. null, alanın bilinmediğini söyler; anahtarın hiç olmaması ayrı bir durumdur.

## 260. JSON döngüsü

Döngü yoktur. Tekrar, dizinin içine aynı biçimde nesneler yazmaktır. Dizi sıra tutar. Nesne anahtar sırasını garanti etmez.

## 261. JSON veri yapısı

Nesne ad-değer, dizi sıralı değer tutar. İç içe nesne ve dizi olur. Anahtar metindir. Sayı, metin olarak yazılırsa tür okuyanda metin kalır. Derinlik arttıkça okumak zorlaşır.

## 262. JSON modülü

Başka dosyayı içerme sözdizimi yoktur. Büyük veri bölünürse her dosya geçerli bir JSON değeri olmalıdır. Program dosyaları kendisi yan yana okur. Yol, JSON'un içinde göreli metin olarak durabilir.

## 263. JSON hatası

Hata, eksik tırnak, sondaki virgül, tek tırnak ve yorumdur. Ayrıştırıcı dosyayı reddeder. Satır numarası aracın işidir. El, metni gözle okur, geçerliliği karttaki kurala göre söyler.

## 264. JSON standart kütüphanesi

Biçimin kendisi küçüktür: nesne, dizi, metin, sayı, true, false, null. Boşluk anlam taşımaz. UTF-8 olağan kodlamadır. Yorum, tarih türü ve fonksiyon bu biçimde yoktur.

## 265. JSON sınırı

El, JSON kartını ve kilitli klasördeki .json metnini okur. Dosyayı kendiliğinden yükleyip program gibi çalıştırmaz. Dış adresten JSON çekmez.

## 266. Markdown sözdizimi

Markdown düz metindir. Başlık satır başında # ile başlar, sayı düzeyi söyler. Paragraf boş satırla ayrılır. Vurgu * veya _ ile, kod ters tırnakla yazılır. Çitli kod üç ters tırnakla açılır.

## 267. Markdown türleri

Tür yoktur. Her şey metindir. Bağlantı [yazı](adres), görsel ![yazı](yol) biçimindedir. Liste - veya 1. ile başlar. Alıntı > ile girintilenir. Ham HTML bazı görüntüleyicilerde geçebilir; bu raf onu önermez.

## 268. Markdown ataması

Atama yoktur. Metin olduğu yere yazılır. Başlığın yazısı # işaretinden sonraki metindir. Bağlantının hedefi parantezin içindedir. Aynı başlık iki kez yazılırsa belgede iki kez durur.

## 269. Markdown fonksiyonu

Fonksiyon yoktur. Tekrar, aynı liste maddesini yeniden yazmaktır. Şablon ve dahil etme bu biçimin çekirdeğinde yoktur. Bazı araçlar ek sözdizimi getirir; çekirdek kart onları şart koşmaz.

## 270. Markdown koşulu

Koşul yoktur. Bir satır ya belgededir ya değildir. Görünüp gizlenme görüntüleyicinin işi değildir, belgenin kendisinde dal yoktur.

## 271. Markdown döngüsü

Döngü yoktur. Liste elle yazılır. Numaralı liste sıra gösterir. İç liste girintiyle kurulur. Yüz madde üretilecekse üreten program ayrıdır.

## 272. Markdown veri yapısı

Veri, başlık, paragraf, liste, tablo ve kod bloğudur. Tablo | ile sütun ayırır. Kod bloğu dil adını çitin yanında taşıyabilir. Başlıklar belgenin içindekiler ağacını kurar.

## 273. Markdown modülü

Başka dosya, göreli bağlantıyla anılır. İçerme standart değildir. Bir konu bir dosyada durur. Görüntüleyici bu dosyaları siteye çevirirse çıktı ayrı klasördedir.

## 274. Markdown hatası

Hata, kapanmayan çit, bozuk tablo ve olmayan dosyaya giden bağdır. Belge yine okunur. Eksik boş satır listeyi paragrafa yapıştırır. El, başlık ve bağı karttaki kurala göre söyler.

## 275. Markdown standart kütüphanesi

Çekirdek: başlık, paragraf, vurgu, bağlantı, görsel, sıra ve numara liste, alıntı, satır içi kod, çit, tablo. Dipnot ve renk çoğu çekirdekte yoktur.

## 276. Markdown sınırı

El, Markdown kartını ve kilitli klasördeki .md metnini okur. Dosyayı kendiliğinden siteye çevirmez ve yayınlamaz.

## 277. SQLite sözdizimi

SQLite, tek dosyada duran SQL motorudur. Sözdizimi SQL'dir. Cümle noktalı virgülle biter. Metin tek tırnak, tanımlayıcı gerekirse çift tırnak veya köşeli parantez olur. Yorum -- veya /* */ olur.

## 278. SQLite türleri

Depolama sınıfları NULL, INTEGER, REAL, TEXT ve BLOB'dur. Bildirilen tür yumuşaktır; sütun çoğu zaman değeri olduğu gibi koyar. INTEGER PRIMARY KEY satır kimliği olur. Tarih çoğunlukla metin veya sayı olarak saklanır.

## 279. SQLite ataması

INSERT satır ekler, UPDATE sütunu değiştirir. WHERE yazılmazsa UPDATE bütün tabloya gider. Parametre ? ile bağlanır, değer metnin içine yapıştırılmaz. El bu cümleleri kendiliğinden motoru açarak çalıştırmaz.

## 280. SQLite fonksiyonu

İş birimi SQL cümlesidir. COUNT, SUM ve AVG hazır işlevlerdir. CREATE VIEW sorguyu adlandırmaktır. Tetikleyici bu rafın ilk katında zorunlu değildir. Kullanıcı işlevi ayrıca bağlanır, el bağlamaz.

## 281. SQLite koşulu

WHERE, JOIN, GROUP BY ve HAVING SQL ile aynı rolle durur. ON çakışmasında ne yapılacağını söyler. Koşul satırı seçer, dosyayı silmez. El silme cümlesini kartın gereği olarak kurmaz.

## 282. SQLite döngüsü

Döngü yazılmaz. Motor satırlarda yürür. RECURSIVE sorgu bir tabloyu kendi üstüne tekrar bağlar; ilk raflarda şart değildir. LIMIT sonucu keser. Sıra ORDER BY ile söylenir.

## 283. SQLite veri yapısı

Veri, dosyanın içindeki tablodur. Şema CREATE TABLE ile kurulur. Dizin CREATE INDEX ile aramayı hızlandırır. Yabancı anahtar ayrı bir açma komutu ister. Veritabanı dosyası kaynak koddan ayrı klasörde durur.

## 284. SQLite modülü

Başka veritabanı ATTACH ile aynı bağlantıya takılabilir. Şema metni .sql dosyasında, veri .db dosyasındadır. Uygulama bu ikisini yolu ile açar. El yolu okur, dosyayı kendiliğinden açmaz.

## 285. SQLite hatası

Hata, kilitli dosya, bozuk SQL ve türün beklenmedik biçimde durmasıdır. Motor cümleyi reddeder, dosya kalır. İşlem BEGIN ve ROLLBACK ile geri alınabilir. El işlemi kendiliğinden açmaz.

## 286. SQLite standart kütüphanesi

Çekirdek SQL sözcükleri ve sqlite_master şema tablosu hazırdır. Tarih işlevleri metin üzerinde çalışır. Ağ sunucusu yoktur; erişim dosyanın kendisinedir. Yedek, dosyanın kopyasıdır.

## 287. SQLite sınırı

El, SQLite kartını ve şema metnini okur. .db dosyasını kendiliğinden açmaz, sorgu çalıştırmaz, başkasının veritabanına bağlanmaz.

## 288. HTML örneği

Küçük örnek: <h1>Başlık</h1> ve <p>Cümle</p>. Bu etiketler sayfanın iskeletidir. Çalıştırılmaz, okunur.

## 289. HTML adlandırması

Dosya adı küçük harf ve tire olur: index.html, hakkimizda.html. Etiket adı da küçük yazılır. Türkçe karakter dosya adında karışıklık çıkarır.

## 290. HTML yorumu

Yorum <!-- not --> biçimindedir. Tarayıcı onu çizmez. Uzun açıklama sayfanın içinde değil, ayrı notta durur.

## 291. HTML girdisi

Girdi, formun input ve button etiketleridir. Kullanıcının yazdığı değer name niteliğiyle anılır. Kalıcı kayıt bu dosyada yoktur.

## 292. HTML metin işlemi

Metin, etiketin arasına yazılır. Başlık h1, paragraf p, vurgu strong olur. Boşluklar tarayıcıda bir boşluğa iner.

## 293. HTML sayı işlemi

HTML sayı hesaplamaz. Bir fiyat metin olarak yazılır. Toplam JavaScript veya sunucu işidir.

## 294. HTML gezmesi

Liste ul ve li ile gezilir. Sıra, etiketlerin belgedeki sırasıdır. Döngü yoktur.

## 295. HTML dosya okuması

Başka sayfa a href ile, görsel img src ile okunur. Yol görelidir. El dosyayı tarayıcıda kendiliğinden açmaz.

## 296. HTML hata örneği

Sık hata, kapanmayan etiket ve yanlış dosya yoludur. Sayfa yine çizilir; bağ boş kalır. Ayrı bir derleme satırı yoktur.

## 297. HTML karıştığı

HTML, CSS ve JavaScript ile karışır. İskelet buradadır. Renk CSS'te, düğme davranışı JavaScript'tedir.

## 298. HTML ne zaman seçilir

Sayfanın iskeleti, başlık, paragraf, liste, form ve bağlantı yazılacaksa HTML seçilir. Sunucusuz klasörde durabilir.

## 299. HTML ne zaman seçilmez

Hesap, sorgu, sistem aracı veya telefon uygulaması yazılacaksa HTML seçilmez. O iş başka dile gider.

## 300. HTML küçük işi

Küçük iş tek index.html olur: bir başlık, bir paragraf, bir bağlantı. Başka dosya şart değildir.

## 301. HTML orta işi

Orta iş index.html, site.css ve site.js üçlüsüdür. HTML bağlar, diğerleri görünüş ve davranışı taşır.

## 302. HTML el cümlesi

Bu dili açan cümleler: html nedir. html nerede kullanılır. html nasıl kullanılır. html örneği nedir. html ne zaman seçilir. html ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 303. CSS örneği

Küçük örnek: h1 { color: #1a365d; }. Seçici başlığı tutar, bildirim rengi söyler. Bu kural çalıştırılmaz, okunur.

## 304. CSS adlandırması

Sınıf adı işi söyler: baslik, kart, dugme. Kimlik tek kutuya kalır. Dosya adı site.css gibi küçük harftir.

## 305. CSS yorumu

Yorum /* not */ olur. Kuralın nedeni kısa yazılır. Eski deneme kuralı yorumda bırakılmaz, silinmesi ayrı emirdir.

## 306. CSS girdisi

CSS kullanıcının yazdığı metni almaz. Girdi HTML formundadır. CSS yalnız kutunun görünüşünü değiştirir.

## 307. CSS metin işlemi

Yazı font-family, font-size ve line-height ile kurulur. Metnin kendisi HTML'de kalır. CSS harfleri yeniden yazmaz.

## 308. CSS sayı işlemi

Sayı, uzunluk ve orandır: px, rem, yüzde. calc() iki uzunluğu toplar. Bu hesap görünüş içindir, veri tutmaz.

## 309. CSS gezmesi

Çok kutu flex veya grid ile dizilir. gap aralığı söyler. Her kutuyu elle koordinatlamak zorunda değildir.

## 310. CSS dosya okuması

HTML, css dosyasını link ile okur. Yol bozuksa kural gelmez, iskelet durur. El tarayıcıyı kendiliğinden açmaz.

## 311. CSS hata örneği

Sık hata, seçicinin hiçbir elemana uymaması ve yazımı bozuk bildirimdir. O satır yok sayılır. Sayfa çökmez.

## 312. CSS karıştığı

CSS, HTML ile karışır. Renk ve boşluk buradadır. Yeni eleman eklemek HTML işidir. Hesap JavaScript işidir.

## 313. CSS ne zaman seçilir

Aynı iskeletin görünüşü değişecekse CSS seçilir. Dar ekran için media kuralı da burada durur.

## 314. CSS ne zaman seçilmez

Veri sorgusu, dosya aracı veya sunucu hesabı yazılacaksa CSS seçilmez. Onda koşul ve kayıt yoktur.

## 315. CSS küçük işi

Küçük iş tek site.css olur: yazı, boşluk ve bir düğme. HTML onu head içinde bağlar.

## 316. CSS orta işi

Orta iş temel.css, yerlesim.css ve bilesen.css diye bölünür. Sonra gelen dosya öncekini ezer.

## 317. CSS el cümlesi

Bu dili açan cümleler: css nedir. css nerede kullanılır. css nasıl kullanılır. css örneği nedir. css ne zaman seçilir. css ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 318. JavaScript örneği

Küçük örnek: function topla(a, b) { return a + b; }. Fonksiyon iki sayıyı döndürür. Bu satır çalıştırılmaz, okunur.

## 319. JavaScript adlandırması

Fonksiyon ve değişken işi söyler: topla, baslik, dugme. Dosya site.js olur. Kısa ve anlamsız ad okumayı bozar.

## 320. JavaScript yorumu

Yorum // satır veya /* blok */ olur. Neden yazılır, ne yaptığı kodun kendisinde görünüyorsa yorum şişmez.

## 321. JavaScript girdisi

Girdi, form alanının value değeridir. Düğme click ile dinlenir. Ağdan veri çekmek bu elin işi değildir.

## 322. JavaScript metin işlemi

Metin String yöntemleriyle okunur: length, slice, toLowerCase. Birleştirme + ile olur. Sayı ile metni + yapıştırmak türü metne çevirir.

## 323. JavaScript sayı işlemi

Sayı Number'dır. Toplama +, kesir aynı türdedir. Number("12") metni sayıya çevirir. Çevrilemeyen değer NaN olur.

## 324. JavaScript gezmesi

Dizi for...of veya forEach ile gezilir. map yeni dizi döndürür, kaynak durur. Nesnenin anahtarları ayrıca gezilir.

## 325. JavaScript dosya okuması

Tarayıcıda dosya, kullanıcının seçtiği File nesnesiyle okunur. Node'da dosya modülü vardır. El bu okumayı kendiliğinden yapmaz.

## 326. JavaScript hata örneği

Sık hata, tanımsız ad ReferenceError ve yanlış tür TypeError'dur. Konsol satır numarasını yazar. Sayfanın geri kalanı sürebilir.

## 327. JavaScript karıştığı

JavaScript, Java ve TypeScript ile karışır. Java başka dildir. TypeScript bunun tipli yazımıdır, tarayıcıya JavaScript iner.

## 328. JavaScript ne zaman seçilir

Sayfada düğme, liste ve küçük hesap gerekiyorsa JavaScript seçilir. HTML iskeletin ardından gelir.

## 329. JavaScript ne zaman seçilmez

Kalıcı tablo, sistem aracı veya tipli büyük kod tabanı tek başına JavaScript istemeyebilir. O iş SQL, Python veya TypeScript'e gider.

## 330. JavaScript küçük işi

Küçük iş site.js içinde bir düğmenin metnini değiştirir. Hesap ayrı fonksiyonda durur.

## 331. JavaScript orta işi

Orta iş saf fonksiyonlar bir dosyada, sayfa bağları başka dosyada durur. İkisi de HTML sonunda bağlanır.

## 332. JavaScript el cümlesi

Bu dili açan cümleler: javascript nedir. javascript nerede kullanılır. javascript nasıl kullanılır. javascript örneği nedir. javascript ne zaman seçilir. javascript ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 333. TypeScript örneği

Küçük örnek: function topla(a: number, b: number): number { return a + b; }. Türler derlemede denetlenir. Satır çalıştırılmaz, okunur.

## 334. TypeScript adlandırması

Ad, işi ve türü birlikte söyler. Dosya .ts, derlenmiş hali .js olur. any kaçak kapısıdır, sık kullanılmaz.

## 335. TypeScript yorumu

Yorum JavaScript ile aynıdır. Türün adı zaten anlatıyorsa yorum tekrar etmez. tsconfig bir yorum dosyası değildir.

## 336. TypeScript girdisi

Girdi, form değerinin string olmasıdır. Sayıya çevirmeden aritmetik yapılmaz. Ağ isteği elin kendiliğinden açtığı kapı değildir.

## 337. TypeScript metin işlemi

Metin string türündedir. Şablon tırnağı başka değer gömer. Yanlışlıkla number verilen metin derlemede durur.

## 338. TypeScript sayı işlemi

Sayı number veya belirli bir birleşimdir. Toplama aynı türde kalır. NaN yine çalışma anında çıkar, tür onu tek başına yok etmez.

## 339. TypeScript gezmesi

Dizi T[] üzerinde for...of yürür. map dönüş türünü taşır. readonly diziye ekleme derlemede durur.

## 340. TypeScript dosya okuması

Dosya okuma çalışma anında JavaScript kütüphanesindedir. Tür tarifi ayrıca yazılır. El dosyayı kendiliğinden açmaz.

## 341. TypeScript hata örneği

Sık hata, türe aykırı atama ve null verilmiş strict alandır. Derleyici dosya ve satır yazar. Çalışma hatası ayrıca try ile tutulur.

## 342. TypeScript karıştığı

TypeScript, JavaScript ile karışır. Kaynak buradadır. Tarayıcının gördüğü dosya çevrilmiş JavaScript'tir.

## 343. TypeScript ne zaman seçilir

Büyük web işinde tür hatası kayıttan önce görülsün diye TypeScript seçilir. Küçük tek dosyada şart değildir.

## 344. TypeScript ne zaman seçilmez

Tarayıcıya doğrudan .ts vermek için seçilmez. Çeviri yoksa sayfa betiği yüklemez. Sistem aracı için de ilk tercih değildir.

## 345. TypeScript küçük işi

Küçük iş bir fonksiyon ve onun türüdür. Çıktı tek js dosyasına iner. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 346. TypeScript orta işi

Orta iş src altındaki modüller ve ortak bir tür dosyasıdır. tsconfig klasörü sınırlar.

## 347. TypeScript el cümlesi

Bu dili açan cümleler: typescript nedir. typescript nerede kullanılır. typescript nasıl kullanılır. typescript örneği nedir. typescript ne zaman seçilir. typescript ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 348. Python örneği

Küçük örnek: def topla(a, b): return a + b. Girinti gövdeyi belirler. Bu fonksiyon çalıştırılmaz, okunur.

## 349. Python adlandırması

Fonksiyon ve modül küçük harf ve alt çizgi kullanır: satir_say, dosya_oku. Sınıf BüyükHarf olur. Dosya hesap.py gibi işi söyler.

## 350. Python yorumu

Yorum # ile başlar. Docstring fonksiyonun ilk satırında üç tırnaktır. El, docstring'in ilk satırını imza kartında okur.

## 351. Python girdisi

Girdi, fonksiyon parametresidir. Komut satırı argümanı ayrı modüldedir. El argümanı kendiliğinden okumaz.

## 352. Python metin işlemi

Metin str'dir. Birleştirme +, parça bölme split, kenar boşluğu strip ile alınır. Sayı ile metin + ile birleşmez.

## 353. Python sayı işlemi

Sayı int veya float olur. Bölme / kesir verir. Tam bölüm // olur. int("12") metni sayıya çevirir. Boş metin ValueError verir.

## 354. Python gezmesi

Liste for öğe in liste ile gezilir. dict için anahtar ve değer birlikte gezilebilir. range sayaç üretir.

## 355. Python dosya okuması

Dosya pathlib veya open ile okunur. El, kilitli klasörde dosyayı metin olarak açar, Python'a işletmez. Yol klasör dışına çıkmaz.

## 356. Python hata örneği

Sık hata, girinti SyntaxError, tanımsız ad NameError ve yanlış tür TypeError'dur. El sözdizimini ağaçla okur, istisnayı çalıştırarak üretmez.

## 357. Python karıştığı

Python, JavaScript ve Java ile karışır. Girinti burada bloktur. Süslü parantez blok kurmaz. pip paketi standart kütüphane değildir.

## 358. Python ne zaman seçilir

Küçük araç, hesap, dosya okuma ve tek işli komut yazılacaksa Python seçilir. Raftaki arac.py bu yüzden Python'dur.

## 359. Python ne zaman seçilmez

Sayfa görünüşü, tarayıcı düğmesi veya telefon arayüzü için seçilmez. O iş HTML, CSS, JavaScript veya Kotlin'e gider.

## 360. Python küçük işi

Küçük iş tek fonksiyonlu hesap.py olur. İmzası, dönüşü ve çağrıları el tarafından okunur.

## 361. Python orta işi

Orta iş bir modül ve bir test niyetidir. El şablonu yazar, pytest'i kendiliğinden çalıştırmaz.

## 362. Python el cümlesi

Bu dili açan cümleler: python nedir. python nerede kullanılır. python nasıl kullanılır. python örneği nedir. python ne zaman seçilir. python ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 363. SQL örneği

Küçük örnek: SELECT ad FROM kisi WHERE yil > 2000. Hangi sütun, hangi tablo, hangi koşul. Cümle çalıştırılmaz, okunur.

## 364. SQL adlandırması

Tablo ve sütun işi söyler: kisi, ad, yil. Boşluklu ad tırnak ister. Kısaltma okumayı zorlaştırır.

## 365. SQL yorumu

Yorum -- satır veya /* blok */ olur. Sorgunun niyeti bir satırda yazılır. Eski koşul yorumda bırakılıp unutulmaz.

## 366. SQL girdisi

Girdi, WHERE içindeki değerdir. Değer cümlenin içine yapıştırılmaz, parametre olarak bağlanır. El sorguyu kendiliğinden çalıştırmaz.

## 367. SQL metin işlemi

Metin tek tırnak içindedir. Birleştirme motora göre değişir. LIKE kalıp arar. Boş metin ile NULL aynı değildir.

## 368. SQL sayı işlemi

Sayı tırnaksız yazılır. COUNT satır sayar, SUM toplar. Karşılaştırma ve aritmetik sütunun türüne uyar.

## 369. SQL gezmesi

Gezme yazılmaz. Motor satırlarda yürür. ORDER BY sırayı, LIMIT adedi söyler. GROUP BY aynı değeri bir kovaya koyar.

## 370. SQL dosya okuması

Sorgu bir tabloyu okur. Dosyanın kendisi SQLite'da .db olabilir. El şema metnini okur, motoru açmaz.

## 371. SQL hata örneği

Sık hata, olmayan sütun adı ve WHERE unutulmuş güncellemedir. Motor cümleyi reddeder veya fazla satır döndürür. El silme cümlesi kurmaz.

## 372. SQL karıştığı

SQL, Python ile karışır. Sorgu buradadır. Dosyayı açan program Python veya başka bir dil olabilir. İkisi aynı dosyada karışmaz.

## 373. SQL ne zaman seçilir

Tablodan satır seçmek, süzmek ve saymak için SQL seçilir. Ekran çizmek için seçilmez.

## 374. SQL ne zaman seçilmez

Sayfa, düğme ve sistem aracı yazılacaksa SQL seçilmez. Onda pencere ve dosya ağacı yoktur.

## 375. SQL küçük işi

Küçük iş tek SELECT olur. Sütun, tablo ve koşul bir cümlededir. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 376. SQL orta işi

Orta iş şema dosyası ve ayrı bir seçme dosyasıdır. Kurma ile okuma karışmaz. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 377. SQL el cümlesi

Bu dili açan cümleler: sql nedir. sql nerede kullanılır. sql nasıl kullanılır. sql örneği nedir. sql ne zaman seçilir. sql ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 378. Bash örneği

Küçük örnek: echo "$ad". Değişken basılır. Tırnak boşluğu bir sözcük tutar. Satır çalıştırılmaz, okunur.

## 379. Bash adlandırması

Betik işi söyler: yedekle.sh, listele.sh. Küçük harf ve tire kullanılır. Ad, sileceği işi çağrıştırıyorsa o ad seçilmez.

## 380. Bash yorumu

Yorum # ile başlar. İlk satırdaki #! hangi kabuğun okuyacağını söyler. Bu bir yorum gibi durur, anlamı ayrıdır.

## 381. Bash girdisi

Girdi, $1 gibi parametre veya okunan satırdır. El parametreyi kendiliğinden vermez. Uzak makine bu kartta yoktur.

## 382. Bash metin işlemi

Metin tırnakla korunur. Çift tırnak değişkeni açar, tek tırnak açmaz. Kesme ve birleştirme metin araçlarıyla yapılır, el onları çalıştırmaz.

## 383. Bash sayı işlemi

Sayı $(( )) içine yazılır. Tür yoktur, sonuç yine metindir. Boş değer ile sıfır aynı değildir.

## 384. Bash gezmesi

for ad in liste; do ...; done her sözcükte döner. Liste kendi klasörünün adları olabilir. Başka bilgisayarın listesi yazılmaz.

## 385. Bash dosya okuması

Dosya, yönlendirme veya bir okuma komutuyla görülür. El betiği çalıştırmaz. Klasör dışına çıkan yol bu elde yoktur.

## 386. Bash hata örneği

Sık hata, tırnaksız boşluk ve sıfır olmayan çıkış kodudur. $? son kodu tutar. El betiği çalıştırıp kodu ölçmez.

## 387. Bash karıştığı

Bash, Python ve PowerShell ile karışır. Unix kabuğu buradadır. Windows görev sırası PowerShell'e daha yakındır.

## 388. Bash ne zaman seçilir

Kendi klasöründe dosya adını basmak ve küçük bir sırayı yazmak için Bash seçilir. Sayfa çizmek için seçilmez.

## 389. Bash ne zaman seçilmez

Kalıcı tablo, telefon uygulaması ve tarayıcı düğmesi için seçilmez. Silme işi bu kartın konusu değildir.

## 390. Bash küçük işi

Küçük iş bir echo ve bir değişken olur. Betik kendi klasöründe durur. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 391. Bash orta işi

Orta iş adlandırılmış bir fonksiyon ve kendi klasöründe bir çıktı dizinidir. El bunu kendiliğinden çalıştırmaz.

## 392. Bash el cümlesi

Bu dili açan cümleler: bash nedir. bash nerede kullanılır. bash nasıl kullanılır. bash örneği nedir. bash ne zaman seçilir. bash ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 393. PowerShell örneği

Küçük örnek: $ad = "Ruzgar"; Write-Output $ad. Değişken nesne de taşıyabilir. Satır çalıştırılmaz, okunur.

## 394. PowerShell adlandırması

Betik işi söyler: Listele.ps1. Fiil-Ad cmdlet adıdır, betik adı da işi söyler. Kaldırma fiili bu kartta örneklenmez.

## 395. PowerShell yorumu

Yorum # ile başlar. Blok yorum <# #> olur. Neden yazılır. Deneme satırı yorumda bırakılıp unutulmaz.

## 396. PowerShell girdisi

Girdi, param($yol) ile alınır. Boru da nesne taşır. El betiğe değer vermez ve uzaktaki oturuma bağlanmaz.

## 397. PowerShell metin işlemi

Metin çift tırnakta değişkeni açar. Tek tırnak açmaz. Birleştirme + veya biçim ile olur. El bunu çalıştırmaz.

## 398. PowerShell sayı işlemi

Sayı .NET türündedir. Toplama + olur. Metin ile sayıyı bilinçsiz toplamak birleştirebilir. Türü söylemek okumayı netleştirir.

## 399. PowerShell gezmesi

foreach ve ForEach-Object koleksiyonu gezer. Where-Object süzer. El bu gezmeyi kendiliğinden başlatmaz.

## 400. PowerShell dosya okuması

Get-Content dosyayı satır satır okur. Yol kendi klasöründe kalır. El komutu çalıştırmaz.

## 401. PowerShell hata örneği

Sık hata, yanlış cmdlet adı ve kırmızı hata akışıdır. try ve catch tutar. El hatayı karttan söyler, betiği koşmaz.

## 402. PowerShell karıştığı

PowerShell, Bash ile karışır. İkisi de görev sırasıdır. Biri Windows nesnesi, biri Unix metni taşır.

## 403. PowerShell ne zaman seçilir

Windows'ta kendi klasöründeki dosyayı okuyup adını basmak için PowerShell seçilir.

## 404. PowerShell ne zaman seçilmez

Web iskeleti, tablo sorgusu ve telefon uygulaması için seçilmez. Kaldırma ve uzak oturum bu elde yoktur.

## 405. PowerShell küçük işi

Küçük iş bir değişken ve Write-Output olur. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 406. PowerShell orta işi

Orta iş param ile yol alan ve Where-Object ile süzen bir .ps1 dosyasıdır. El onu çalıştırmaz.

## 407. PowerShell el cümlesi

Bu dili açan cümleler: powershell nedir. powershell nerede kullanılır. powershell nasıl kullanılır. powershell örneği nedir. powershell ne zaman seçilir. powershell ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 408. Java örneği

Küçük örnek: int topla(int a, int b) { return a + b; }. Metot sınıfta durur. Satır çalıştırılmaz, okunur.

## 409. Java adlandırması

Sınıf BüyükHarf, metot küçükHarf olur. Dosya adı sınıf adıyla aynıdır. Paket klasör yolunu izler.

## 410. Java yorumu

Yorum // veya /* */ olur. Javadoc /** */ ile metot anlatılır. El gövdeyi kendiliğinden derlemez.

## 411. Java girdisi

Girdi, metot parametresi veya bir okuyucudur. El okuyucuyu kendiliğinden açmaz. Ağ soketi bu kartta yoktur.

## 412. Java metin işlemi

Metin String'dir. Birleştirme + olur. equals içerik karşılaştırır, == kimlik karşılaştırabilir. Bu ayrım okumada sık gerekir.

## 413. Java sayı işlemi

Sayı int, long veya double olur. Bölme iki int arasında tam sonuç verir. El hesabı çalıştırmaz.

## 414. Java gezmesi

Dizi ve List for-each ile gezilir. Map anahtar kümesi ayrıca gezilir. El döngüyü işletmez.

## 415. Java dosya okuması

java.nio dosya yolunu temsil eder. El .java metnini okur, dosyayı Java ile açmaz.

## 416. Java hata örneği

Sık hata, NullPointerException ve derlemede tür uyuşmazlığıdır. El istisnayı çalıştırarak üretmez.

## 417. Java karıştığı

Java, JavaScript ile karışır. Adları benzer, dilleri ayrıdır. Tarayıcı düğmesi JavaScript işidir.

## 418. Java ne zaman seçilir

Uzun ömürlü kurum uygulaması ve sınıf düzeni gerekiyorsa Java seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 419. Java ne zaman seçilmez

Tek sayfalık site veya küçük metin aracı için seçilmez. O iş HTML veya Python'a gider.

## 420. Java küçük işi

Küçük iş bir sınıf ve bir metottur. Dosya adı sınıfı taşır. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 421. Java orta işi

Orta iş bir paket, bir çekirdek sınıf ve ayrı bir test niyetidir. El derlemez. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 422. Java el cümlesi

Bu dili açan cümleler: java nedir. java nerede kullanılır. java nasıl kullanılır. java örneği nedir. java ne zaman seçilir. java ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 423. C# örneği

Küçük örnek: int Topla(int a, int b) => a + b;. İfade gövdesi tek satır döner. Satır çalıştırılmaz, okunur.

## 424. C# adlandırması

Sınıf ve metot PascalCase olur. Yerel değişken camelCase olur. Dosya çoğunlukla sınıf adını taşır.

## 425. C# yorumu

Yorum // veya /* */ olur. /// belge yorumudur. El derlemeden okur. Yorum programın davranışını değiştirmez. El yorumu da çalıştırmaz.

## 426. C# girdisi

Girdi, metot parametresidir. Konsol okuma ayrı çağrıdır. El o çağrıyı yapmaz. Değer dışarıdan gelir. El o değeri kendiliğinden vermez.

## 427. C# metin işlemi

Metin string'dir ve değişmezdir. Birleştirme + veya ara değer ile olur. El bunu çalıştırmaz.

## 428. C# sayı işlemi

Sayı int, long veya decimal olur. decimal para için daha uygun anlatılır. El hesabı işletmez.

## 429. C# gezmesi

List ve dizi foreach ile gezilir. LINQ süzer ve seçer, kaynağı kendiliğinden silmez.

## 430. C# dosya okuması

System.IO dosya yolunu temsil eder. El .cs metnini okur, dosyayı C# ile açmaz. Okuma niyeti karttadır. El dosyayı bu dille kendiliğinden açmaz.

## 431. C# hata örneği

Sık hata, null değer ve derlemede tür uyuşmazlığıdır. El istisnayı çalıştırarak görmez.

## 432. C# karıştığı

C#, C ve C++ ile karışır. Adları yakın, dilleri ayrıdır. Bellek yönetimi burada çöp toplayıcıya yakındır.

## 433. C# ne zaman seçilir

Windows uygulaması veya oyun aracı yazılacaksa C# seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 434. C# ne zaman seçilmez

Tek HTML sayfası veya gömülü aygıt için seçilmez. O iş HTML veya C'ye gider. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 435. C# küçük işi

Küçük iş bir metot ve onun dönüşüdür. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 436. C# orta işi

Orta iş bir proje dosyası ve birkaç sınıf olur. El çözümü derlemez. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 437. C# el cümlesi

Bu dili açan cümleler: csharp nedir. csharp nerede kullanılır. csharp nasıl kullanılır. csharp örneği nedir. csharp ne zaman seçilir. csharp ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 438. C++ örneği

Küçük örnek: int topla(int a, int b) { return a + b; }. Başlık bildirim, kaynak gövde taşır. Satır çalıştırılmaz, okunur.

## 439. C++ adlandırması

Fonksiyon küçük harf veya ekip sözleşmesiyle yazılır. Sınıf BüyükHarf olur. Dosya işi söyler: hesap.cpp.

## 440. C++ yorumu

Yorum // veya /* */ olur. Başlıktaki yorum arayüzü anlatır. El derlemez. Yorum programın davranışını değiştirmez. El yorumu da çalıştırmaz.

## 441. C++ girdisi

Girdi, parametre veya akıştır. Referans kopyayı önler. El akışı kendiliğinden açmaz.

## 442. C++ metin işlemi

Metin std::string olur. Birleştirme + vardır. char dizisi ayrı ve daha kırılgandır. El ikisini de çalıştırmaz.

## 443. C++ sayı işlemi

Sayı int veya double olur. Tür dönüşü açık yazılır. El hesabı işletmez. Hesap anlatılır, sonuç üretilmez. El ifadeyi çalıştırmaz.

## 444. C++ gezmesi

vector aralık tabanlı for ile gezilir. El döngüyü çalıştırmaz. Gezme sırası kartta durur. El döngüyü kendiliğinden başlatmaz.

## 445. C++ dosya okuması

filesystem yolu temsil eder. El .cpp metnini okur, dosyayı programla açmaz. Okuma niyeti karttadır. El dosyayı bu dille kendiliğinden açmaz.

## 446. C++ hata örneği

Sık hata, tür uyuşmazlığı ve eksik bildiridir. Tanımsız davranış bu kartta örneklenmez.

## 447. C++ karıştığı

C++, C ve C# ile karışır. Sınıf ve şablon burada vardır. C daha küçük bir dildir.

## 448. C++ ne zaman seçilir

Oyun motoru veya hız isteyen sistem aracı yazılacaksa C++ seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 449. C++ ne zaman seçilmez

Basit sayfa veya küçük metin sayacı için seçilmez. O iş HTML veya Python'a gider.

## 450. C++ küçük işi

Küçük iş bir fonksiyon ve bir başlık bildirimi olur. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 451. C++ orta işi

Orta iş src altında .h ve .cpp çiftidir. Derleme tarifi ayrı durur. El derlemez.

## 452. C++ el cümlesi

Bu dili açan cümleler: cpp nedir. cpp nerede kullanılır. cpp nasıl kullanılır. cpp örneği nedir. cpp ne zaman seçilir. cpp ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 453. C örneği

Küçük örnek: int topla(int a, int b) { return a + b; }. Bildirim başlıkta, gövde .c dosyasındadır. Satır çalıştırılmaz, okunur.

## 454. C adlandırması

Fonksiyon küçük harf ve alt çizgi kullanır: satir_say. Dosya işi söyler. Büyük harfli ad makro niyeti taşır.

## 455. C yorumu

Yorum /* */ veya // olur. Makro #define bir yorum değildir. El kaynağı okur, derlemez.

## 456. C girdisi

Girdi, parametre veya stdin niyetidir. Dizi uzunluğu ayrıca geçilir. El programı çalıştırmaz.

## 457. C metin işlemi

Metin char dizisidir ve sonda sıfır bayt taşır. Kopyalama kütüphane işleviyle anlatılır. El o işlevi çağırmaz.

## 458. C sayı işlemi

Sayı int veya double olur. İki int bölmesi tam sonuç verir. El hesabı işletmez. Hesap anlatılır, sonuç üretilmez. El ifadeyi çalıştırmaz.

## 459. C gezmesi

Dizi for (i = 0; i < n; i++) ile gezilir. Uzunluk dil tarafından taşınmaz, n ayrıca bilinir.

## 460. C dosya okuması

stdio dosya niyetini anlatır. El .c metnini okur, fopen çağırmaz. Okuma niyeti karttadır. El dosyayı bu dille kendiliğinden açmaz.

## 461. C hata örneği

Sık hata, dönüş kodunun bakılmaması ve bildirimsiz fonksiyondur. Taşan bellek bu kartta örneklenmez.

## 462. C karıştığı

C, C++ ve C# ile karışır. Burada sınıf yoktur. Metin bir dizi ve sıfır bayttır. Karışan adlar ayrı kartlardadır. El yanlış dile kaymaz.

## 463. C ne zaman seçilir

Çekirdeğe yakın küçük araç veya gömülü iş için C seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 464. C ne zaman seçilmez

Web sayfası, tablo sorgusu ve telefon arayüzü için seçilmez. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 465. C küçük işi

Küçük iş bir fonksiyon ve onun başlık bildirimidir. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 466. C orta işi

Orta iş birkaç .c dosyası ve bir .h arayüzüdür. El bağlayıcıyı çalıştırmaz. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 467. C el cümlesi

Bu dili açan cümleler: c nedir. c nerede kullanılır. c nasıl kullanılır. c örneği nedir. c ne zaman seçilir. c ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 468. Rust örneği

Küçük örnek: fn topla(a: i32, b: i32) -> i32 { a + b }. Son ifade döner. Satır çalıştırılmaz, okunur.

## 469. Rust adlandırması

Fonksiyon ve modül yılan_ad kullanır. Tür PascalAd olur. Dosya src/lib.rs veya src/main.rs olur.

## 470. Rust yorumu

Yorum // veya /// belge olur. El kaynağı okur, derlemez. Yorum programın davranışını değiştirmez. El yorumu da çalıştırmaz.

## 471. Rust girdisi

Girdi, parametre veya Result döndüren bir okumadır. El o okumayı kendiliğinden yapmaz.

## 472. Rust metin işlemi

Metin String sahip olur, &str ödünç alır. Bu ayrım okumada sık gerekir. El ikisini de çalıştırmaz.

## 473. Rust sayı işlemi

Sayı i32 veya f64 olur. Tür dönüşü açık yazılır. El hesabı işletmez. Hesap anlatılır, sonuç üretilmez. El ifadeyi çalıştırmaz.

## 474. Rust gezmesi

Vec for öğe in liste ile gezilir. Yineleyici map ara değer de kurabilir. El döngüyü çalıştırmaz.

## 475. Rust dosya okuması

std::fs dosya niyetini anlatır. El .rs metnini okur, dosyayı Rust ile açmaz. Okuma niyeti karttadır. El dosyayı bu dille kendiliğinden açmaz.

## 476. Rust hata örneği

Sık hata, ödünç alma uyuşmazlığı ve Result'un yok sayılmasıdır. Derleyici satır yazar. El derlemez.

## 477. Rust karıştığı

Rust, C++ ile karışır. İkisi de sistem işine yakındır. Burada sahiplik derlemede denetlenir.

## 478. Rust ne zaman seçilir

Bellek kuralı derlemede görülsün istenen sistem aracı için Rust seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 479. Rust ne zaman seçilmez

Küçük HTML sayfası veya hızlı bir metin notu için seçilmez. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 480. Rust küçük işi

Küçük iş bir fn ve onun türüdür. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 481. Rust orta işi

Orta iş src/lib.rs ve Cargo.toml olur. El kasayı indirmez ve derlemez. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 482. Rust el cümlesi

Bu dili açan cümleler: rust nedir. rust nerede kullanılır. rust nasıl kullanılır. rust örneği nedir. rust ne zaman seçilir. rust ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 483. PHP örneği

Küçük örnek: function topla(int $a, int $b): int { return $a + $b; }. Değişken $ ile başlar. Satır çalıştırılmaz, okunur.

## 484. PHP adlandırması

Fonksiyon küçük harf ve alt çizgi kullanır. Sınıf BüyükHarf olur. Dosya .php sayfanın adını taşır.

## 485. PHP yorumu

Yorum // veya /* */ olur. HTML ile aynı dosyada duran PHP bloğu <?php ile açılır. El sunucuyu açmaz.

## 486. PHP girdisi

Girdi, istek alanının değeridir. Değer sorguya yapıştırılmaz. El isteği kendiliğinden okumaz.

## 487. PHP metin işlemi

Metin string'dir. Birleştirme nokta operatörüdür. Bu, Python'daki + ile karışır. El birleştirmeyi çalıştırmaz.

## 488. PHP sayı işlemi

Sayı int veya float olur. Tür strict modda sıkılaşır. El hesabı işletmez. Hesap anlatılır, sonuç üretilmez. El ifadeyi çalıştırmaz.

## 489. PHP gezmesi

Dizi foreach ile gezilir. Aynı yapı liste ve eşleme tutabilir. El döngüyü çalıştırmaz.

## 490. PHP dosya okuması

Dosya işlevleri yolu okur. El .php metnini okur, sayfayı sunmaz. Okuma niyeti karttadır. El dosyayı bu dille kendiliğinden açmaz.

## 491. PHP hata örneği

Sık hata, tanımsız değişken uyarısı ve tür uyuşmazlığıdır. El uyarıyı çalıştırarak üretmez.

## 492. PHP karıştığı

PHP, Python ve HTML ile karışır. Sayfa üretimi buradadır. İskeletin kendisi HTML olarak tarayıcıya gider.

## 493. PHP ne zaman seçilir

Sunucunun her istekte HTML üretmesi gerekiyorsa PHP seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 494. PHP ne zaman seçilmez

Masaüstü araç veya tarayıcıda duran küçük hesap için seçilmez. O iş Python veya JavaScript'e gider.

## 495. PHP küçük işi

Küçük iş bir fonksiyon ve onun dönüşüdür. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 496. PHP orta işi

Orta iş public altındaki sayfa ve includes altındaki ortak fonksiyondur. El sunucu kurmaz.

## 497. PHP el cümlesi

Bu dili açan cümleler: php nedir. php nerede kullanılır. php nasıl kullanılır. php örneği nedir. php ne zaman seçilir. php ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 498. Go örneği

Küçük örnek: func Topla(a int, b int) int { return a + b }. Dışa açık ad büyük harfle başlar. Satır çalıştırılmaz, okunur.

## 499. Go adlandırması

Yerel ad kısa ve küçük olur. Dışa açık fonksiyon BüyükHarf olur. Dosya .go, modül go.mod ile anılır.

## 500. Go yorumu

Yorum // veya /* */ olur. Dışa açık adın üstündeki yorum belgedir. El derlemez. Yorum programın davranışını değiştirmez. El yorumu da çalıştırmaz.

## 501. Go girdisi

Girdi, parametre veya bir okuyucudur. Hata ikinci dönüş değeridir. El fonksiyonu çağırmaz.

## 502. Go metin işlemi

Metin string'dir ve değişmezdir. Bayt dilimi ayrıdır. El dönüşümü çalıştırmaz. Metin kuralı okunur. El birleştirmeyi kendiliğinden yapmaz.

## 503. Go sayı işlemi

Sayı int veya float64 olur. Tür dönüşü açık yazılır. El hesabı işletmez. Hesap anlatılır, sonuç üretilmez. El ifadeyi çalıştırmaz.

## 504. Go gezmesi

Dilim for i, öğe := range liste ile gezilir. Map sırası garanti değildir. El döngüyü çalıştırmaz.

## 505. Go dosya okuması

os dosya niyetini anlatır. El .go metnini okur, dosyayı Go ile açmaz. Okuma niyeti karttadır. El dosyayı bu dille kendiliğinden açmaz.

## 506. Go hata örneği

Sık hata, kullanılmayan değişken ve bakılmamış err değeridir. Derleyici durur. El derlemez.

## 507. Go karıştığı

Go, Python ile karışır. İkisi de araç yazar. Burada hata bir dönüş değeridir, istisna alışkanlığı değildir.

## 508. Go ne zaman seçilir

Küçük ağ servisi veya komut satırı aracı yazılacaksa Go seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 509. Go ne zaman seçilmez

Sayfa görünüşü ve telefon arayüzü için seçilmez. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 510. Go küçük işi

Küçük iş bir func ve go.mod olur. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 511. Go orta işi

Orta iş cmd altında bir komut ve iç pakette bir kütüphanedir. El derlemez. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 512. Go el cümlesi

Bu dili açan cümleler: go nedir. go nerede kullanılır. go nasıl kullanılır. go örneği nedir. go ne zaman seçilir. go ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 513. Kotlin örneği

Küçük örnek: fun topla(a: Int, b: Int): Int = a + b. Tek ifade eşittir ile döner. Satır çalıştırılmaz, okunur.

## 514. Kotlin adlandırması

Fonksiyon camelCase, sınıf PascalCase olur. Dosya .kt işi söyler. Paket adı klasörle aynı olmak zorunda değildir.

## 515. Kotlin yorumu

Yorum // veya /* */ olur. El kaynağı okur, derlemez ve telefona kurmaz. Yorum programın davranışını değiştirmez. El yorumu da çalıştırmaz.

## 516. Kotlin girdisi

Girdi, parametredir. Null olabilen değer ? taşır. El çağrıyı yapmaz. Değer dışarıdan gelir. El o değeri kendiliğinden vermez.

## 517. Kotlin metin işlemi

Metin String'dir. Şablon "$ad" değer gömer. El birleştirmeyi çalıştırmaz. Metin kuralı okunur. El birleştirmeyi kendiliğinden yapmaz.

## 518. Kotlin sayı işlemi

Sayı Int veya Double olur. Bölme türüne uyar. El hesabı işletmez. Hesap anlatılır, sonuç üretilmez. El ifadeyi çalıştırmaz.

## 519. Kotlin gezmesi

Liste for (öğe in liste) ile gezilir. map yeni liste döndürür. El döngüyü çalıştırmaz.

## 520. Kotlin dosya okuması

kotlin.io dosya niyetini anlatır. El .kt metnini okur, dosyayı açmaz. Okuma niyeti karttadır. El dosyayı bu dille kendiliğinden açmaz.

## 521. Kotlin hata örneği

Sık hata, null verilmiş alan ve derlemede tür uyuşmazlığıdır. El derlemez. Hata adı karttan okunur. El hatayı çalıştırarak üretmez.

## 522. Kotlin karıştığı

Kotlin, Java ile karışır. İkisi de JVM'de durabilir. Telefon arayüzü Kotlin'de daha sık anlatılır.

## 523. Kotlin ne zaman seçilir

Android uygulaması yazılacaksa Kotlin seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 524. Kotlin ne zaman seçilmez

Basit statik sayfa veya tek dosyalık metin sayacı için seçilmez. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 525. Kotlin küçük işi

Küçük iş bir fun ve onun türüdür. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 526. Kotlin orta işi

Orta iş app/src altındaki birkaç .kt dosyasıdır. El paketi indirmez ve kurmaz. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 527. Kotlin el cümlesi

Bu dili açan cümleler: kotlin nedir. kotlin nerede kullanılır. kotlin nasıl kullanılır. kotlin örneği nedir. kotlin ne zaman seçilir. kotlin ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 528. JSON örneği

Küçük örnek: {"ad": "Ruzgar", "yil": 2026}. Anahtar çift tırnakta, sayıda tırnak yoktur. Metin çalıştırılmaz, okunur.

## 529. JSON adlandırması

Dosya işi söyler: ayar.json, liste.json. Anahtar küçük harf ve kısa olur. Aynı anahtar iki kez yazılmaz.

## 530. JSON yorumu

Yorum yoktur. Açıklama ayrı bir .md dosyasında durur. JSON içine // koymak dosyayı bozar.

## 531. JSON girdisi

Girdi yoktur. Değer dosyaya yazılır, program onu okur. El dosyayı program gibi yüklemez.

## 532. JSON metin işlemi

Metin çift tırnak ister. Tek tırnak geçersizdir. İç tırnak ters bölü ile kaçar. Metin kuralı okunur. El birleştirmeyi kendiliğinden yapmaz.

## 533. JSON sayı işlemi

Sayı tırnaksızdır. Metin olarak yazılan sayı okuyanda metin kalır. El çevirmeyi kendiliğinden yapmaz.

## 534. JSON gezmesi

Dizi sıra tutar, nesne anahtar tutar. Gezme, okuyan programın işidir. JSON döngü yazmaz.

## 535. JSON dosya okuması

Dosyanın kendisi veridir. Başka dosyayı içerme sözdizimi yoktur. El .json metnini okur.

## 536. JSON hata örneği

Sık hata, sondaki virgül ve eksik tırnaktır. Ayrıştırıcı dosyayı reddeder. El ayrıştırıcıyı çalıştırmaz, kuralı karttan söyler.

## 537. JSON karıştığı

JSON, JavaScript ile karışır. Biçim buradadır. Davranış JavaScript'tedir. İkisi aynı şey değildir.

## 538. JSON ne zaman seçilir

İki programın birbirine verdiği ayar veya liste yazılacaksa JSON seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 539. JSON ne zaman seçilmez

Sayfa, fonksiyon ve sorgu yazılacaksa JSON seçilmez. Onda hesap yoktur. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 540. JSON küçük işi

Küçük iş tek nesnedir: birkaç anahtar ve değer. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 541. JSON orta işi

Orta iş bir liste nesneleridir. Her nesne aynı anahtarları taşır. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 542. JSON el cümlesi

Bu dili açan cümleler: json nedir. json nerede kullanılır. json nasıl kullanılır. json örneği nedir. json ne zaman seçilir. json ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 543. Markdown örneği

Küçük örnek: # Başlık ve ardından bir paragraf. Boş satır paragrafı ayırır. Metin çalıştırılmaz, okunur.

## 544. Markdown adlandırması

Dosya konu.md olur. Başlık işi söyler. Bir dosya bir konuyu anlatır. Ad işi söyler. El dosyayı bu adla kendiliğinden oluşturmaz.

## 545. Markdown yorumu

Asıl yorum sözdizimi yoktur. Yazılmayan not dosyaya girmez. HTML yorumu bu rafın önerisi değildir.

## 546. Markdown girdisi

Girdi yoktur. Yazar metni doğrudan yazar. Okur görüntüleyicide başlık ve liste görür.

## 547. Markdown metin işlemi

Vurgu *yıldız* veya _alt çizgi_ ile olur. Satır içi kod ters tırnaktır. Metin olduğu yerde durur.

## 548. Markdown sayı işlemi

Sayı, numaralı listenin işaretidir. Hesap yapılmaz. 1. madde sırayı gösterir. Hesap anlatılır, sonuç üretilmez. El ifadeyi çalıştırmaz.

## 549. Markdown gezmesi

Liste - veya 1. ile gezilir. İç liste girintiyle kurulur. Döngü yoktur. Gezme sırası kartta durur. El döngüyü kendiliğinden başlatmaz.

## 550. Markdown dosya okuması

Başka not, göreli bağlantıyla anılır. Dosya yoksa bağ boş kalır. El siteye çevirmez.

## 551. Markdown hata örneği

Sık hata, kapanmayan kod çiti ve yapışık listedir. Belge yine okunur. Görünüş bozulur.

## 552. Markdown karıştığı

Markdown, HTML ile karışır. Not buradadır. Yayımlanan sayfa ayrıca HTML'e çevrilebilir. Çekirdek kart çeviriyi şart koşmaz.

## 553. Markdown ne zaman seçilir

Not, belge ve okuma metni yazılacaksa Markdown seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 554. Markdown ne zaman seçilmez

Düğme, sorgu ve sistem aracı için seçilmez. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 555. Markdown küçük işi

Küçük iş bir başlık ve bir paragraftır. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 556. Markdown orta işi

Orta iş birkaç başlık, bir liste ve bir kod çitidir. Her konu ayrı dosyada durur.

## 557. Markdown el cümlesi

Bu dili açan cümleler: markdown nedir. markdown nerede kullanılır. markdown nasıl kullanılır. markdown örneği nedir. markdown ne zaman seçilir. markdown ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 558. SQLite örneği

Küçük örnek: CREATE TABLE kisi (id INTEGER PRIMARY KEY, ad TEXT);. Şema metindir. Cümle çalıştırılmaz, okunur.

## 559. SQLite adlandırması

Dosya uygulama.db, şema sema.sql olur. Tablo adı işi söyler. Kaynak kod ile veritabanı aynı klasörde karışmaz.

## 560. SQLite yorumu

Yorum SQL ile aynıdır: -- ve /* */. Şemanın niyeti kısa yazılır. El motoru açmaz.

## 561. SQLite girdisi

Girdi, parametre ? ile bağlanır. Değer SQL metninin içine yapıştırılmaz. El bağlamayı kendiliğinden yapmaz.

## 562. SQLite metin işlemi

Metin TEXT olarak durur. Tek tırnak değer, çift tırnak gerekirse addır. El sorguyu çalıştırmaz.

## 563. SQLite sayı işlemi

Sayı INTEGER veya REAL olur. INTEGER PRIMARY KEY satır kimliği olabilir. El hesabı işletmez.

## 564. SQLite gezmesi

Gezme SQL motorundadır. SELECT satır döndürür. Uygulama döngüsü ayrı dildedir. El ikisini de çalıştırmaz.

## 565. SQLite dosya okuması

Veri tek dosyadadır. Şema .sql olarak okunur. El .db dosyasını kendiliğinden açmaz.

## 566. SQLite hata örneği

Sık hata, bozuk SQL ve kilitli dosyadır. Motor cümleyi reddeder, dosya kalır. El işlemi açmaz.

## 567. SQLite karıştığı

SQLite, SQL ve bir sunucu veritabanı ile karışır. Dil SQL'dir. Motor tek dosyadır, ayrı sunucu istemez.

## 568. SQLite ne zaman seçilir

Tek kullanıcılı küçük kayıt, sunucusuz duracaksa SQLite seçilir. Seçim raftaki iş listesine bakar. El dili kendiliğinden açmaz.

## 569. SQLite ne zaman seçilmez

Sayfa çizmek veya çok sunuculu büyük kurgu için seçilmez. Görünüş HTML'dedir. Yanlış dilde yazılan iş sonra başka karta taşınır. El o taşımayı kendiliğinden yapmaz.

## 570. SQLite küçük işi

Küçük iş bir tablo ve bir SELECT olur. Tek dosya yeter. El bu işi kendiliğinden çalıştırmaz, dosya aynı kalır.

## 571. SQLite orta işi

Orta iş sema.sql ve data/uygulama.db ayrımıdır. El dosyayı açmaz. Dosyalar ayrı durur. El şablonu kendiliğinden derlemez ve çalıştırmaz.

## 572. SQLite el cümlesi

Bu dili açan cümleler: sqlite nedir. sqlite nerede kullanılır. sqlite nasıl kullanılır. sqlite örneği nedir. sqlite ne zaman seçilir. sqlite ne zaman seçilmez. Cümle kartın adına oturursa raf okunur. Oturtmazsa model konuşur ve uydurabilir.

## 573. HTML işleci

HTML'de aritmetik işleç yoktur. Nitelikteki eşittir, değerin adını bağlar; hesap yapmaz. Toplama başka dilin işidir.

## 574. HTML karşılaştırması

Etiketler birbirine eşit diye karşılaştırılmaz. İki başlık ayrı elemandır. Sıra, belgedeki yazılma sırasıdır.

## 575. HTML mantığı

Ve, veya, değil diye bir mantık sözdizimi yoktur. Görünürlük ve koşul CSS veya JavaScript kartındadır.

## 576. HTML boş değeri

Boş değer, kapanmayan boş etiket veya yazılmamış niteliktir. br ve img gibi etiketler içerik taşımaz. Bu bir hata sayılmaz.

## 577. HTML tür dönüşümü

Metin sayıya çevrilmez. 12 yazısı hâlâ metindir. Çeviri JavaScript veya sunucu dilinde anlatılır.

## 578. HTML metin biçimi

Boşluklar tarayıcıda tek boşluğa iner. Satır sonu yeni paragraf açmaz. Paragraf için p gerekir.

## 579. HTML koleksiyonu

Koleksiyon, ul veya ol içindeki li listesidir. Sıra belgededir. Döngüyle üretilmez.

## 580. HTML kapsamı

Kapsam, belgenin kendisidir. Etiket adının bir değişken ömrü yoktur. Aynı ad ikinci kez yazılırsa ikinci eleman olur.

## 581. HTML giriş noktası

Giriş noktası, klasördeki index.html ve içindeki body'dir. İlk başlık sayfanın adını taşır.

## 582. HTML çıktısı

Çıktı, tarayıcının çizdiği sayfadır. print diye bir söz yoktur. El tarayıcıyı kendiliğinden açmaz.

## 583. HTML dosya yolu

Dosya yolu, a ve img içinde göreli yazılır. Üst klasöre çıkan yol bu elde önerilmez. Kilitli klasörde kalınır.

## 584. HTML uzantısı

Uzantı .html olur. .htm eski bir ikizdir. Sayfa adı küçük harf ve tire taşır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 585. HTML paketi

Paket yöneticisi şart değildir. Başka dosya, link ve script ile bağlanır. El paket indirmez.

## 586. HTML yazımı

Etiket ve nitelik küçük harfle yazılır. Her açılan kap, kapanır. Girinti okumayı kolaylaştırır, anlamı değiştirmez.

## 587. HTML el sınırı

El HTML metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 588. CSS işleci

Seçici birleştirme boşluk, >, + ve ~ ile olur. calc içinde + ve - uzunluk toplar. Bu hesap görünüş içindir.

## 589. CSS karşılaştırması

Karşılaştırma, media içindeki genişlik koşuludur. İki rengi birbirine eşitleyen bir cümle yoktur.

## 590. CSS mantığı

Mantık, media kuralında and ile birleşir. Seçicide değil diye bir işleç bu kartta yoktur.

## 591. CSS boş değeri

Boş değer initial veya unset olabilir. Yazılmayan özellik, miras veya başlangıç değerine döner.

## 592. CSS tür dönüşümü

Sayı birimine çevrilir: 16px, 1rem, %10. Birimsiz uzunluk çoğu yerde geçersizdir. El dönüşümü çalıştırmaz.

## 593. CSS metin biçimi

Renk # ile altı haneli yazılır. Yazı font-family ve font-size ile biçilir. Metnin kendisi HTML'de kalır.

## 594. CSS koleksiyonu

Koleksiyon, virgülle ayrılmış seçici listesidir. Hepsi aynı bildirimi paylaşır. Dizi yöntemi yoktur.

## 595. CSS kapsamı

Kapsam, seçicinin tuttuğu elemanlardır. Sonra gelen ve daha özel kural öncekini ezer. Dosya sırası da etkiler.

## 596. CSS giriş noktası

Giriş noktası, HTML'in head içinde bağladığı ilk css dosyasıdır. Bağ yoksa kural gelmez.

## 597. CSS çıktısı

Çıktı, kutunun boyanmış hâlidir. Konsola basılan bir satır yoktur. El tarayıcıyı açmaz.

## 598. CSS dosya yolu

Dosya yolu url() içinde görelidir. Üst klasöre çıkan yol bu elde yazılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 599. CSS uzantısı

Uzantı .css olur. Dosya adı işi söyler: site.css, yerlesim.css. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 600. CSS paketi

Paket şart değildir. Birden çok css dosyası HTML'den sırayla bağlanır. El paket indirmez.

## 601. CSS yazımı

Bir satırda bir bildirim durur. Seçici işi söyler. Renk ve boşluk aynı kuralda toplanır.

## 602. CSS el sınırı

El CSS metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 603. JavaScript işleci

Toplama +, eşitleme =, bakma === olur. + hem sayı toplar hem metin yapıştırır. Bu ayrım okumada sık gerekir.

## 604. JavaScript karşılaştırması

=== türü de bakar. == türü gevşetebilir. El ikisini de çalıştırmaz. Yeni kartta === tercih edilir.

## 605. JavaScript mantığı

Mantık &&, || ve ! ile yazılır. Kısa devre, sağ tarafı her zaman okumaz. El bunu işletmez.

## 606. JavaScript boş değeri

Boş değer null veya undefined olabilir. İkisi aynı değildir. İkisi de dolu bir metin değildir.

## 607. JavaScript tür dönüşümü

Number metni sayıya, String sayıyı metne çevirir. Çevrilemeyen sayı NaN olur. El çevirmeyi yapmaz.

## 608. JavaScript metin biçimi

Şablon tırnağı `adet: ${n}` biçimindedir. İçindeki değer metne gömülür. El gömmeyi çalıştırmaz.

## 609. JavaScript koleksiyonu

Dizi köşeli parantez, nesne süslü parantezdir. Dizi sıra tutar. Nesne anahtar tutar.

## 610. JavaScript kapsamı

let ve const blokta yaşar. var daha geniş kaçar. Fonksiyonun içindeki ad dışarı sızmaz.

## 611. JavaScript giriş noktası

Giriş noktası, HTML sonunda bağlanan site.js dosyasıdır. Modül ise kendi dosyasından başlar.

## 612. JavaScript çıktısı

console.log satır basar. return değer döndürür. İkisi aynı iş değildir. El ikisini de çağırmaz.

## 613. JavaScript dosya yolu

Dosya yolu göreli yazılır. Üst klasöre çıkmak ve uzak adres açmak bu elde yoktur.

## 614. JavaScript uzantısı

Uzantı .js olur. İş adı dosyaya geçer: site.js, hesap.js. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 615. JavaScript paketi

Küçük iş için paket şart değildir. El npm kurmaz ve paket çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 616. JavaScript yazımı

Fonksiyon ve değişken camelCase olur. Dosya küçük harftir. Kısa anlamsız ad okumayı bozar.

## 617. JavaScript el sınırı

El JavaScript metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 618. TypeScript işleci

İşleçler JavaScript ile aynıdır: +, =, ===. Tür, derlemede ayrıca denetlenir. El derlemez.

## 619. TypeScript karşılaştırması

=== tercih edilir. Türler ayrı olduğu için gevşek == az gerekir. El karşılaştırmayı çalıştırmaz.

## 620. TypeScript mantığı

&&, || ve ! aynıdır. Tür daraltması, boş olmayan kolda değeri netleştirir. El bunu derlemez.

## 621. TypeScript boş değeri

null ve undefined ayrı boş değerlerdir. strict açıkken ikisi de açıkça yazılır. El derlemez.

## 622. TypeScript tür dönüşümü

Sayıya Number veya belirli bir çeviri gider. as yalnız tür bakışıdır, değeri kendiliğinden doğrulamaz.

## 623. TypeScript metin biçimi

Şablon tırnağı JavaScript ile aynıdır. İçindeki değerin türü string beklenir. El biçimi çalıştırmaz.

## 624. TypeScript koleksiyonu

Dizi T[] , nesne alanları tür taşır. readonly diziye ekleme derlemede durur. El derlemez.

## 625. TypeScript kapsamı

Blok kapsamı let ve const ile aynıdır. Dışa açılan ad export ile anılır. El modülü yüklemez.

## 626. TypeScript giriş noktası

Giriş, src altındaki .ts dosyasıdır. Tarayıcının gördüğü kapı, çevrilmiş .js dosyasıdır.

## 627. TypeScript çıktısı

Çıktı yine console veya return olur. Tür, basılan değeri değiştirmez. El basmaz.

## 628. TypeScript dosya yolu

Yol, derleme tarifindeki köke göredir. El klasör dışına çıkmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 629. TypeScript uzantısı

Kaynak .ts, ürün .js olur. İkisi aynı dosya değildir. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 630. TypeScript paketi

Paket adı package.json içinde durur. El npm kurmaz ve tsc çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 631. TypeScript yazımı

Ad camelCase, tür PascalCase olur. any kaçak kapısıdır, sık yazılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 632. TypeScript el sınırı

El TypeScript metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 633. Python işleci

Toplama +, atama =, bakma == olur. and, or, not sözcüktür. + sayı toplar; iki metni de yapıştırır, sayı ile metni yapıştırmaz.

## 634. Python karşılaştırması

== değeri karşılaştırır. is kimliği karşılaştırır. None ile bakışta is None yazılır. El bunu çalıştırmaz.

## 635. Python mantığı

Mantık and, or, not ile yazılır. Karşılaştırma zinciri a < b < c biçiminde okunur. El zinciri işletmez.

## 636. Python boş değeri

Boş değer None'dır. Boş metin, boş liste ve sıfır None değildir. Üçü de dolu bir yokluktur, başka anlama gelir.

## 637. Python tür dönüşümü

int metni tamsayıya, str değeri metne çevirir. Boş metin ValueError verir. El çevirmeyi yapmaz.

## 638. Python metin biçimi

Biçim f"adet: {n}" olur. Süslü parantezin içi ifadedir. El o ifadeyi hesaplamaz.

## 639. Python koleksiyonu

Liste sıra tutar, dict anahtar tutar, tuple değişmez sıradır. Köşeli, süslü ve normal parantez bu üçü ayırır.

## 640. Python kapsamı

Fonksiyonun içindeki ad dışarı çıkmaz. Girinti kapsamı gösterir. Sınıfın alanı self ile anılır.

## 641. Python giriş noktası

Giriş, dosyanın kendisidir. if __name__ satırı, dosya doğrudan açıldığında çalışacak kapıyı anlatır. El o kapıyı açmaz.

## 642. Python çıktısı

print satır basar. return değer döndürür. El ikisini de çağırmaz. Okuma kartı dönüşü metin olarak söyler.

## 643. Python dosya yolu

Yol pathlib ile göreli yazılır. Üst klasöre çıkan .. bu elde yoktur. Kilitli klasör sınırı durur.

## 644. Python uzantısı

Uzantı .py olur. Dosya işi söyler: hesap.py, arac.py. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 645. Python paketi

Standart kütüphane paket sanılmaz. Üçüncü parti ad requirements içinde durabilir. El pip çalıştırmaz.

## 646. Python yazımı

Fonksiyon küçük harf ve alt çizgi kullanır. Sınıf BüyükHarf olur. Dört boşluk bir girintidir.

## 647. Python el sınırı

El Python metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 648. SQL işleci

Karşılaştırma = ve <> ile yazılır. WHERE koşulu süzer. Atama bu kartın konusu değildir. El sorguyu çalıştırmaz.

## 649. SQL karşılaştırması

= değeri bakar. NULL için = yetmez, IS NULL yazılır. Bu ayrım okumada sık gerekir.

## 650. SQL mantığı

Mantık AND, OR, NOT ile birleşir. Parantez hangi koşulun önce bağlanacağını söyler. El koşulu işletmez.

## 651. SQL boş değeri

Boş değer NULL'dur. Boş metin NULL değildir. NULL ile aritmetik NULL kalır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 652. SQL tür dönüşümü

CAST(deger AS INTEGER) tür çevirisini anlatır. El çevirmeyi motorla yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 653. SQL metin biçimi

Metin tek tırnak içindedir. Biçim, seçilen sütunun motordaki gösterimidir. El gösterimi üretmez.

## 654. SQL koleksiyonu

Koleksiyon, satır kümesidir. Dizi yazılmaz. GROUP BY aynı değeri bir kovaya koyar.

## 655. SQL kapsamı

Kapsam, o cümlenin baktığı tablodur. İç sorgu kendi kapsamını taşır. El sorguyu açmaz.

## 656. SQL giriş noktası

Giriş noktası, tek SELECT cümlesidir. Sütun, tablo ve koşul aynı cümlede durur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 657. SQL çıktısı

Çıktı, dönen satırlardır. print yoktur. El satır üretmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 658. SQL dosya yolu

Dosya yolu bir sütun değeri olabilir. Şema metni .sql dosyasındadır. El motoru açmaz.

## 659. SQL uzantısı

Sorgu dosyası .sql olur. Veritabanı dosyası başka uzantı taşıyabilir. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 660. SQL paketi

SQL'in paket yöneticisi yoktur. Motorun adı ayrı karttadır. El motor kurmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 661. SQL yazımı

Anahtar sözcük büyük yazılırsa okumak kolaylaşır. Tablo ve sütun küçük ve işi söyler.

## 662. SQL el sınırı

El SQL metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 663. Bash işleci

Atama boşluksuz ad=deger olur. Bakış [[ ]] içindedir. $(( )) sayı toplar. El bunları çalıştırmaz.

## 664. Bash karşılaştırması

Metin bakışı = ile, sayı bakışı -eq ile anlatılır. Tırnaksız boşluk karşılaştırmayı böler.

## 665. Bash mantığı

&& sonraki adımı öncekinin sıfır çıkışına bağlar. || diğer kola gider. El adımı başlatmaz.

## 666. Bash boş değeri

Boş değer, boş metindir. Atanmamış ad da boş görünebilir. Sıfır sayısı boş değildir.

## 667. Bash tür dönüşümü

Ayrı bir tür dönüşümü yoktur. Sonuç çoğu yerde metin kalır. El dönüşümü çalıştırmaz.

## 668. Bash metin biçimi

Çift tırnak "$ad" değişkeni açar. Tek tırnak açmaz. Biçim bu ayrımla okunur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 669. Bash koleksiyonu

Liste, boşlukla ayrılmış sözcüklerdir. for o listeyi gezer. El gezmeyi başlatmaz.

## 670. Bash kapsamı

Fonksiyonun içi kendi gövdesidir. Dışarı sızan ad, betiğin geri kalanında durur. local bunu daraltır.

## 671. Bash giriş noktası

Giriş, betik dosyasının ilk komut satırıdır. #! hangi kabuğun okuyacağını söyler. El kabuğu açmaz.

## 672. Bash çıktısı

echo satır basar. return fonksiyonun çıkış kodunu söyler. El ikisini de çağırmaz.

## 673. Bash dosya yolu

Yol göreli ve kendi klasöründedir. Üst klasöre çıkan .. ve uzak makine bu elde yoktur.

## 674. Bash uzantısı

Uzantı .sh olur. Ad işi söyler: listele.sh. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 675. Bash paketi

Paket kurulumu bu kartta yoktur. Betik, kabuğun kendi sözcükleriyle yetinir. El kurulum çalıştırmaz.

## 676. Bash yazımı

Ad küçük harf ve tire olur. Değişken tırnaklanır. Silme işi örneklenmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 677. Bash el sınırı

El Bash metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 678. PowerShell işleci

Atama $ad = deger olur. Karşılaştırma -eq, -gt gibidir. + hem sayı toplar hem metin yapıştırabilir. El çalıştırmaz.

## 679. PowerShell karşılaştırması

-eq değer bakar. -ne denk değildir. Büyük küçük harf ayrı bir anahtarla anlatılır. El bakışı yapmaz.

## 680. PowerShell mantığı

-and, -or ve -not sözcük işleçtir. && bu kartın alışkanlığı değildir. El koşulu işletmez.

## 681. PowerShell boş değeri

Boş değer $null'dır. Boş metin ve $null aynı değildir. El ikisini de üretmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 682. PowerShell tür dönüşümü

[int] "12" metni sayıya çevirir. Çevrilemeyen metin hata verir. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 683. PowerShell metin biçimi

"adet: $ad" değişkeni açar. -f biçim dizisi ayrı bir yoldur. El biçimi çalıştırmaz.

## 684. PowerShell koleksiyonu

Dizi virgülle yazılır. Nesne özellik taşır. Boru, nesneyi sonraki cmdlet'e verir. El boruyu açmaz.

## 685. PowerShell kapsamı

param ile gelen ad fonksiyonun kapsamındadır. Betiğin üstündeki ad daha geniş durur.

## 686. PowerShell giriş noktası

Giriş, .ps1 dosyasının ilk çalışan satırıdır. El betiği başlatmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 687. PowerShell çıktısı

Write-Output boruya değer verir. Write-Host yalnız ekrana benzer. El ikisini de çağırmaz.

## 688. PowerShell dosya yolu

Yol kendi klasöründe görelidir. Üst klasöre çıkan ve uzak oturum bu elde yoktur.

## 689. PowerShell uzantısı

Uzantı .ps1 olur. Ad işi söyler. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 690. PowerShell paketi

Modül adı ayrıca anılabilir. El modül kurmaz ve Import-Module çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 691. PowerShell yazımı

Cmdlet Fiil-Ad biçimindedir. Değişken $ ile başlar. Kaldırma fiili örneklenmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 692. PowerShell el sınırı

El PowerShell metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 693. Java işleci

Sayıda +, atamada =, bakışta == olur. Metinde + yapıştırır. El ifadeyi çalıştırmaz.

## 694. Java karşılaştırması

İlkel sayıda == değer bakar. String için equals içerik bakar. == iki metin nesnesinin kimliğine bakabilir.

## 695. Java mantığı

&& ve || kısa devre yapar. ! ters çevirir. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 696. Java boş değeri

Boş nesne null'dır. İlkel sayıda null olmaz. El null ile çağrı örneği çalıştırmaz.

## 697. Java tür dönüşümü

Integer.parseInt metni int yapar. (int) kesirden tam kısma bakar. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 698. Java metin biçimi

String biçimi birleştirme veya biçim çağrısıyla anlatılır. El o çağrıyı yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 699. Java koleksiyonu

Dizi sabit uzunluktadır. List büyüyebilir. Map anahtar tutar. El gezmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 700. Java kapsamı

Blok süslü parantezdir. Metotun içindeki ad dışarı çıkmaz. Alan, sınıfın ömründedir.

## 701. Java giriş noktası

Giriş, main metodudur. İmza sınıfın kapısıdır. El main çağırmaz ve derlemez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 702. Java çıktısı

System.out.println satır basar. return değer döndürür. El ikisini de çağırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 703. Java dosya yolu

Yol metin olarak durur. Üst klasöre çıkan yol bu elde yazılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 704. Java uzantısı

Uzantı .java olur. Dosya adı public sınıf adıyla aynıdır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 705. Java paketi

package satırı klasörü adlandırır. El Maven veya Gradle çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 706. Java yazımı

Sınıf PascalCase, metot camelCase olur. Girinti okumayı taşır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 707. Java el sınırı

El Java metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 708. C# işleci

+ toplar, = atar, == bakar. Metinde + yapıştırır. El ifadeyi çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 709. C# karşılaştırması

== çoğu değerde içerik bakar. Nesnede ayrı bir eşitlik tarif edilebilir. El bakışı yapmaz.

## 710. C# mantığı

&& ve || kısa devre yapar. ! ters çevirir. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 711. C# boş değeri

Boş referans null'dır. Değer türü null taşımaz, yanına ? konursa taşıyabilir. El çağırmaz.

## 712. C# tür dönüşümü

int.Parse metni sayıya çevirir. (int) kesiri daraltır. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 713. C# metin biçimi

$"adet: {n}" biçimidir. Süslü parantez değeri gömer. El gömmeyi yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 714. C# koleksiyonu

Dizi sabit, List büyür. Dictionary anahtar tutar. El gezmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 715. C# kapsamı

Blok süslü parantezdir. Metotun yerel adı dışarı çıkmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 716. C# giriş noktası

Giriş, Main metodudur. El Main çağırmaz ve çözümü derlemez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 717. C# çıktısı

Console.WriteLine satır basar. return değer döndürür. El ikisini de çağırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 718. C# dosya yolu

Yol metin olarak durur. Klasör dışına çıkan yol bu elde yoktur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 719. C# uzantısı

Uzantı .cs olur. Proje dosyası ayrıca .csproj taşır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 720. C# paketi

namespace adı klasörü anlatır. El dotnet çalıştırmaz ve paket indirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 721. C# yazımı

Sınıf ve metot PascalCase, yerel ad camelCase olur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 722. C# el sınırı

El C# metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 723. C++ işleci

+ toplar, = atar, == bakar. << akışa yazar. El ifadeyi çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 724. C++ karşılaştırması

== değer bakar. Nesnede eşitlik ayrıca tarif edilebilir. El bakışı yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 725. C++ mantığı

&& ve || kısa devre yapar. ! ters çevirir. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 726. C++ boş değeri

Boş işaretçi nullptr olur. Eski NULL ayrı bir alışkanlıktır. El işaretçiyi çözmez.

## 727. C++ tür dönüşümü

static_cast<int> açık dönüşümdür. El dönüşümü çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 728. C++ metin biçimi

std::string birleştirme + ile anlatılır. Akış << de metin basar. El basmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 729. C++ koleksiyonu

vector büyüyen dizidir. map anahtar tutar. Düz dizi uzunluğunu ayrıca taşır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 730. C++ kapsamı

Blok süslü parantezdir. Fonksiyonun yerel adı dışarı çıkmaz. Alan, nesnenin ömründedir.

## 731. C++ giriş noktası

Giriş, main fonksiyonudur. El main çağırmaz ve derlemez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 732. C++ çıktısı

std::cout satır basar. return çıkış kodu veya değer verir. El ikisini de çağırmaz.

## 733. C++ dosya yolu

Yol metin olarak durur. Üst klasöre çıkan yol bu elde yazılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 734. C++ uzantısı

Başlık .h, gövde .cpp olur. İkisi aynı işi böler. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 735. C++ paketi

namespace adı çakışmayı ayırır. El paket yöneticisi çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 736. C++ yazımı

Sınıf PascalCase, fonksiyon ekibin sözleşmesiyle yazılır. Başlıkta bildirim, kaynakta gövde durur.

## 737. C++ el sınırı

El C++ metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 738. C işleci

+ toplar, = atar, == bakar. İşaretçi işleci bu kartta örneklenmez. El ifadeyi çalıştırmaz.

## 739. C karşılaştırması

== değer bakar. Metin dizisinde == ilk baytı değil, karşılaştırmanın kendisini anlatmaz; kütüphane işlevi anılır, çağrılmaz.

## 740. C mantığı

&& ve || kısa devre yapar. ! ters çevirir. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 741. C boş değeri

Boş işaretçi NULL ile anılır. El işaretçiyi çözmez ve bellek örneği yazmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 742. C tür dönüşümü

(int) açık daraltmadır. Metinden sayıya çeviri ayrı bir kütüphane işlevidir. El onu çağırmaz.

## 743. C metin biçimi

printf biçim dizisi %d ve %s taşır. Biçim ile değerin türü aynı olmalıdır. El printf çağırmaz.

## 744. C koleksiyonu

Dizi sabit uzunluktadır. Uzunluk dil tarafından taşınmaz, n ayrıca bilinir. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 745. C kapsamı

Blok süslü parantezdir. Fonksiyonun yerel adı dışarı çıkmaz. Dosya kapsamındaki ad daha geniş durur.

## 746. C giriş noktası

Giriş, main fonksiyonudur. El main çağırmaz ve derlemez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 747. C çıktısı

printf basar. return çıkış kodunu verir. El ikisini de çağırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 748. C dosya yolu

Yol, bir char dizisi olarak anlatılır. Üst klasöre çıkan yol bu elde yoktur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 749. C uzantısı

Gövde .c, arayüz .h olur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 750. C paketi

Paket yöneticisi bu dilin çekirdeğinde yoktur. Başlık adı #include ile anılır. El derleyiciyi açmaz.

## 751. C yazımı

Fonksiyon küçük harf ve alt çizgi kullanır. Büyük harfli ad makro niyeti taşır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 752. C el sınırı

El C metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 753. Rust işleci

+ toplar, let ile bağlanır, == bakar. Atama mut ile ayrıca açılır. El ifadeyi çalıştırmaz.

## 754. Rust karşılaştırması

== değer bakar. Türler aynı olmalıdır. El bakışı yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 755. Rust mantığı

&& ve || kısa devre yapar. ! ters çevirir. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 756. Rust boş değeri

Yokluk Option içindeki None'dır. null sözcüğü bu dilin alışkanlığı değildir. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 757. Rust tür dönüşümü

as i32 sayı daraltmasını anlatır. Metinden parse, Result döndürür. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 758. Rust metin biçimi

format! makrosu metin kurar. println! basar. El ikisini de çağırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 759. Rust koleksiyonu

Vec büyüyen dizidir. HashMap anahtar tutar. Dizi sabit uzunluk da taşıyabilir. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 760. Rust kapsamı

Blok kapsamdır. Ödünç alınan değer, sahibinin ömrünü aşmaz. El derlemez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 761. Rust giriş noktası

Giriş, src/main.rs içindeki main veya src/lib.rs kütüphanesidir. El kasayı açmaz.

## 762. Rust çıktısı

println! satır basar. Son ifade return olmadan dönebilir. El çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 763. Rust dosya yolu

Yol, standart kütüphanenin yol türüyle anlatılır. Klasör dışına çıkılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 764. Rust uzantısı

Uzantı .rs olur. Modül dosyası da .rs taşır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 765. Rust paketi

Kasa adı Cargo.toml içindedir. El cargo kurmaz ve derlemez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 766. Rust yazımı

Fonksiyon yılan_ad, tür PascalAd olur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 767. Rust el sınırı

El Rust metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 768. PHP işleci

$ ile atama olur. + sayı toplar. Metin birleştirme noktadır. El ifadeyi çalıştırmaz.

## 769. PHP karşılaştırması

=== türü de bakar. == gevşetebilir. Yeni kartta === tercih edilir. El bakışı yapmaz.

## 770. PHP mantığı

&& ve || yazılır. and ve or daha gevşek öncelik taşır. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 771. PHP boş değeri

Boş değer null'dır. Boş metin ve 0 null değildir. El üretmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 772. PHP tür dönüşümü

(int) metni sayıya çevirir. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 773. PHP metin biçimi

Çift tırnak "$ad" değişkeni açar. Tek tırnak açmaz. El biçimi çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 774. PHP koleksiyonu

array hem liste hem eşleme tutabilir. Köşeli parantez de dizi yazar. El gezmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 775. PHP kapsamı

Fonksiyonun içindeki ad dışarı çıkmaz. Sınıf alanı $this ile anılır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 776. PHP giriş noktası

Giriş, sunucunun açtığı .php dosyasıdır. <?php bloğu HTML içine gömülebilir. El sunucu açmaz.

## 777. PHP çıktısı

echo basar. return değer döndürür. El ikisini de çağırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 778. PHP dosya yolu

Yol göreli yazılır. Üst klasöre çıkan yol bu elde yoktur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 779. PHP uzantısı

Uzantı .php olur. Sayfa dosyası bu adı taşır. HTML ile aynı klasörde durabilir. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 780. PHP paketi

Composer adı ayrıca durabilir. El composer çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 781. PHP yazımı

Fonksiyon küçük harf ve alt çizgi, sınıf PascalCase olur. Değişken $ ile başlar.

## 782. PHP el sınırı

El PHP metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 783. Go işleci

+ toplar, = ve := bağlar, == bakar. := türü sağdan çıkarır. El ifadeyi çalıştırmaz.

## 784. Go karşılaştırması

== değer bakar. Türler aynı olmalıdır. El bakışı yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 785. Go mantığı

&& ve || kısa devre yapar. ! ters çevirir. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 786. Go boş değeri

Boş referans nil'dir. Sıfır değeri, türüne göre 0 veya boş metindir. nil her türün sıfırı değildir.

## 787. Go tür dönüşümü

int(x) sayı daraltmasını anlatır. Metinden sayı, ayrı bir işlev ve hata değeriyle okunur. El çevirmez.

## 788. Go metin biçimi

fmt.Sprintf biçim kurar. %d ve %s yer tutar. El biçimi çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 789. Go koleksiyonu

Dilim büyüyebilir. Dizi sabit uzunluktadır. Map anahtar tutar ve gezinme sırası garanti değildir.

## 790. Go kapsamı

Blok süslü parantezdir. Fonksiyonun yerel adı dışarı çıkmaz. Büyük harfli ad paket dışına açılır.

## 791. Go giriş noktası

Giriş, main paketindeki main fonksiyonudur. Kütüphane paketinin main'i yoktur. El derlemez.

## 792. Go çıktısı

fmt.Println basar. return değer ve çoğu zaman hata döndürür. El ikisini de çağırmaz.

## 793. Go dosya yolu

Yol metin olarak durur. Klasör dışına çıkılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 794. Go uzantısı

Uzantı .go olur. Paket dosyası go.mod ayrıca durur. İkisi aynı işi bölüşür. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 795. Go paketi

Modül adı go.mod içindedir. El go get çalıştırmaz ve paket indirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 796. Go yazımı

Yerel ad kısa ve küçük, dışa açık ad BüyükHarf olur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 797. Go el sınırı

El Go metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 798. Kotlin işleci

+ toplar, = atar, == bakar. El ifadeyi çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 799. Kotlin karşılaştırması

== değer bakar. === kimlik bakışı olarak anılır. El bakışı yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 800. Kotlin mantığı

&& ve || kısa devre yapar. ! ters çevirir. El koşulu işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 801. Kotlin boş değeri

Boş değer null'dır. Türün yanında ? yoksa null atanamaz. El çağırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 802. Kotlin tür dönüşümü

toInt() metni sayıya çevirir. Hatalı metin istisna verebilir. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 803. Kotlin metin biçimi

"adet: $ad" şablonudur. ${} daha uzun ifade gömer. El gömmeyi yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 804. Kotlin koleksiyonu

listOf sıra tutar. mapOf anahtar tutar. El gezmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 805. Kotlin kapsamı

Blok kapsamdır. Fonksiyonun yerel adı dışarı çıkmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 806. Kotlin giriş noktası

Giriş, main fonksiyonudur. Telefon uygulamasında kapı ayrıca bir etkinliktir. El kurmaz.

## 807. Kotlin çıktısı

println basar. return değer döndürür. El ikisini de çağırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 808. Kotlin dosya yolu

Yol metin olarak durur. Klasör dışına çıkılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 809. Kotlin uzantısı

Uzantı .kt olur. Bir dosya bir işi anlatır. Sınıf adı dosyayla aynı olmak zorunda değildir.

## 810. Kotlin paketi

Paket adı dosyanın başında durur. El Gradle çalıştırmaz ve bağımlılık indirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 811. Kotlin yazımı

Fonksiyon camelCase, sınıf PascalCase olur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 812. Kotlin el sınırı

El Kotlin metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 813. JSON işleci

Aritmetik işleç yoktur. İki nokta anahtarı değere bağlar. Virgül sonraki çifti ayırır. Hesap yapılmaz.

## 814. JSON karşılaştırması

İki değer dosyanın içinde karşılaştırılmaz. Eşitlik, okuyan programın işidir. El o programı çalıştırmaz.

## 815. JSON mantığı

Ve, veya, değil yoktur. Koşul JSON'a yazılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 816. JSON boş değeri

Boş değer null olur. Boş metin "" null değildir. Boş nesne {} ve boş dizi [] de null değildir.

## 817. JSON tür dönüşümü

Tür dönüşümü yoktur. Tırnaklı 12 metindir, tırnaksız 12 sayıdır. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 818. JSON metin biçimi

Biçim, girinti ve satır sonudur. Anlamı değiştirmez. Anahtar yine çift tırnak ister.

## 819. JSON koleksiyonu

Köşeli parantez dizi, süslü parantez nesnedir. Dizi sıra tutar. Nesne anahtar tutar.

## 820. JSON kapsamı

Kapsam, iç içe nesnenin kendisidir. Dış anahtar içeri sızmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 821. JSON giriş noktası

Giriş, dosyanın kökündeki nesne veya dizidir. İkinci kök yoktur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 822. JSON çıktısı

Çıktı, dosyanın kendisidir. print yoktur. El dosyayı program gibi yüklemez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 823. JSON dosya yolu

Başka dosyayı içerme yolu yoktur. Her JSON kendi dosyasıdır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 824. JSON uzantısı

Uzantı .json olur. Ad işi söyler: ayar.json. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 825. JSON paketi

Paket yoktur. Başka araç bu dosyayı okur. El araç kurmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 826. JSON yazımı

Anahtar küçük harf ve kısa olur. Sondaki virgül yazılmaz. Tek tırnak kullanılmaz.

## 827. JSON el sınırı

El JSON metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 828. Markdown işleci

Aritmetik işleç yoktur. # başlık düzeyi, - liste, ` kod işaretidir. Hesap yapılmaz.

## 829. Markdown karşılaştırması

İki satır birbirine eşit diye karşılaştırılmaz. Sıra, dosyadaki yazılma sırasıdır.

## 830. Markdown mantığı

Mantık sözdizimi yoktur. Koşul bu belgede yazılmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 831. Markdown boş değeri

Boş satır, paragrafı ayırır. Boş başlık anlamsızdır. Yazılmayan not dosyada yoktur.

## 832. Markdown tür dönüşümü

Tür dönüşümü yoktur. Her şey metindir. Sayı da metin olarak durur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 833. Markdown metin biçimi

Vurgu yıldız veya alt çizgi, satır içi kod ters tırnaktır. Kod çiti üç ters tırnakla açılır.

## 834. Markdown koleksiyonu

Koleksiyon, - veya 1. ile yazılmış listedir. İç liste girintiyle kurulur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 835. Markdown kapsamı

Kapsam, o dosyadır. Başlık başka dosyanın değişkeni olmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 836. Markdown giriş noktası

Giriş, dosyanın ilk başlığıdır. Bir dosya bir konuyu anlatır. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 837. Markdown çıktısı

Çıktı, okurun gördüğü başlık ve paragraftır. El siteye çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 838. Markdown dosya yolu

Bağlantı göreli yazılır. Üst klasöre çıkan yol bu elde önerilmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 839. Markdown uzantısı

Uzantı .md olur. Ad konuyu söyler. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 840. Markdown paketi

Paket şart değildir. Yayımlama aracı ayrı bir iştir. El o aracı kurmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 841. Markdown yazımı

Başlık kısa, paragraf tek düşünce olur. Kod örneği çit içinde durur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 842. Markdown el sınırı

El Markdown metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 843. SQLite işleci

İşleç SQL ile aynıdır: =, <>, AND, OR. El cümleyi motorla çalıştırmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 844. SQLite karşılaştırması

= değer bakar. NULL için IS NULL yazılır. El bakışı yapmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 845. SQLite mantığı

AND, OR, NOT koşulu birleştirir. Parantez önceliği söyler. El işletmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 846. SQLite boş değeri

NULL boş değerdir. INTEGER PRIMARY KEY boş satır kimliği taşımaz. El satır yazmaz.

## 847. SQLite tür dönüşümü

CAST SQL ile aynı anlatılır. El çevirmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 848. SQLite metin biçimi

Metin tek tırnak, sayı tırnaksızdır. El gösterim üretmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 849. SQLite koleksiyonu

Koleksiyon, tablodaki satırlardır. Ayrı bir dizi sözdizimi çekirdekte şart değildir.

## 850. SQLite kapsamı

Kapsam, açık olan tek dosyalık veritabanıdır. İkinci sunucu yoktur. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 851. SQLite giriş noktası

Giriş, sema.sql içindeki CREATE TABLE cümlesidir. El dosyayı açmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 852. SQLite çıktısı

Çıktı, SELECT ile dönen satırdır. El satır üretmez. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 853. SQLite dosya yolu

Veri dosyası kendi klasöründe data/uygulama.db olarak durur. Üst klasöre çıkılmaz.

## 854. SQLite uzantısı

Şema .sql, veri .db olur. İkisi karışmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 855. SQLite paketi

Ayrı paket şart değildir. Motor tek dosyadır. El motor kurmaz. Bu kart okunur. El satırı derlemez, kurmaz ve çalıştırmaz.

## 856. SQLite yazımı

Tablo adı küçük ve işi söyler. Kurma cümlesi ile seçme cümlesi ayrı dosyada durur.

## 857. SQLite el sınırı

El SQLite metnini okur. Derlemez, kurmaz ve çalıştırmaz. Kilitli klasörün dışına çıkmaz. Dosya silinmez.

## 858. Python modülü abc

Soyut temel sınıf tanımlamak için kullanılır. Alt sınıf eksik metodu olursa nesne kurulamaz. El bu modülü yüklemez ve çalıştırmaz.

## 859. Python modülü annotationlib

Python 3.14 ile gelen modüldür. İşlev notlarını (annotation) incelemek içindir. El bu modülü yüklemez ve çalıştırmaz.

## 860. Python modülü antigravity

Standart kütüphanedeki şaka modülüdür. Bir web çizgi romanına işaret eder. El bu modülü yüklemez ve çalıştırmaz.

## 861. Python modülü argparse

Komut satırı argümanlarının adını, türünü ve yardım yazısını tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 862. Python modülü array

Aynı türden sayıları bitişik dizide tutar. Liste kadar genel değildir. El bu modülü yüklemez ve çalıştırmaz.

## 863. Python modülü ast

Python kaynağını sözdizimi ağacına çevirir. El bu ağacı okur, düğümü çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 864. Python modülü asyncio

Tek iş parçacığında bekleyen işleri (eşzamanlılık) tarif eden kütüphanedir. El bu modülü yüklemez ve çalıştırmaz.

## 865. Python modülü atexit

Yorumlayıcı kapanırken çalışacak işlevi kaydeder. El kapanışı tetiklemez. El bu modülü yüklemez ve çalıştırmaz.

## 866. Python modülü base64

İkili veriyi yalnızca metin harfleriyle yazar ve geri okur. El bu modülü yüklemez ve çalıştırmaz.

## 867. Python modülü bdb

Hata ayıklayıcının temel sınıfıdır. pdb bunun üzerine kuruludur. El bu modülü yüklemez ve çalıştırmaz.

## 868. Python modülü binascii

İkili veri ile hex ve base64 gibi metin biçimleri arasında çeviri yapar. El bu modülü yüklemez ve çalıştırmaz.

## 869. Python modülü bisect

Sıralı listede bir değerin gireceği yeri ikili aramayla bulur. El bu modülü yüklemez ve çalıştırmaz.

## 870. Python modülü builtins

print, len, int gibi her zaman açık olan adların modülüdür. El bu modülü yüklemez ve çalıştırmaz.

## 871. Python modülü bz2

bzip2 ile sıkıştırılmış baytları okur ve yazar. El bu modülü yüklemez ve çalıştırmaz.

## 872. Python modülü cProfile

İşlevlerin ne kadar sürdüğünü ölçen belirleyici profil aracıdır. El bu modülü yüklemez ve çalıştırmaz.

## 873. Python modülü calendar

Ay ve hafta takvimini metin olarak kurar. Saat dilimi zoneinfo kartındadır. El bu modülü yüklemez ve çalıştırmaz.

## 874. Python modülü cmath

Karmaşık sayılarda karekök ve logaritma gibi hesaplar tanımlar. El bu modülü yüklemez ve çalıştırmaz.

## 875. Python modülü cmd

Satır satır komut okuyan küçük bir kabuk iskeletidir. El bu modülü yüklemez ve çalıştırmaz.

## 876. Python modülü code

Etkileşimli yorumlayıcı iskeleti sunar. El bir yorumlayıcı açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 877. Python modülü codecs

Metin kodlamasını (utf-8 gibi) kaydeder ve çevirir. El bu modülü yüklemez ve çalıştırmaz.

## 878. Python modülü codeop

Etkileşimli ortamda kodun tamamlanıp tamamlanmadığını anlamaya yardım eder. El bu modülü yüklemez ve çalıştırmaz.

## 879. Python modülü collections

deque, Counter, defaultdict gibi liste ve sözlük türevlerini taşır. El bu modülü yüklemez ve çalıştırmaz.

## 880. Python modülü colorsys

RGB, HLS ve HSV renk düzenleri arasında dönüşüm tanımlar. El bu modülü yüklemez ve çalıştırmaz.

## 881. Python modülü compileall

Bir klasördeki .py dosyalarını bayt koduna çevirmeyi tarif eder. El derlemez. El bu modülü yüklemez ve çalıştırmaz.

## 882. Python modülü compression

Sıkıştırma modüllerinin üst paket adıdır. gzip, bz2, lzma ve zlib ayrı adlardır. El bu modülü yüklemez ve çalıştırmaz.

## 883. Python modülü concurrent

concurrent.futures ile iş havuzu tarif edilir. El havuzu başlatmaz. El bu modülü yüklemez ve çalıştırmaz.

## 884. Python modülü configparser

INI benzeri ayar dosyasını bölüm ve anahtar olarak okur. El bu modülü yüklemez ve çalıştırmaz.

## 885. Python modülü contextlib

with bloğu için bağlam yöneticisi kurmayı kolaylaştırır. El bu modülü yüklemez ve çalıştırmaz.

## 886. Python modülü contextvars

Görevden göreve taşınan, genel değişkenden ayrı küçük bir bağlam tutar. El bu modülü yüklemez ve çalıştırmaz.

## 887. Python modülü copy

Bir nesnenin sığ veya derin kopyasını tarif eder. El kopyalamaz. El bu modülü yüklemez ve çalıştırmaz.

## 888. Python modülü copyreg

pickle için tür kayıt etme düzenidir. Güvenilmeyen veri açılmaz. El bu modülü yüklemez ve çalıştırmaz.

## 889. Python modülü csv

Virgül veya benzeri ayraçlı tabloları satır satır okur ve yazar. El bu modülü yüklemez ve çalıştırmaz.

## 890. Python modülü ctypes

Python'dan C türlerine ve paylaşılan kütüphaneye köprü tarifidir. El çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 891. Python modülü curses

Unix uçbiriminde metin ekranı çizmeyi tarif eder. El ekran açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 892. Python modülü dataclasses

Sınıf alanlarını kısa bildirimle kurar. Eşitlik ve gösterim kendiliğinden gelir. El bu modülü yüklemez ve çalıştırmaz.

## 893. Python modülü datetime

Tarih, saat ve aralık tutar. Saat dilimi için zoneinfo ayrıca durur. El bu modülü yüklemez ve çalıştırmaz.

## 894. Python modülü dbm

Basit anahtar-değer dosya veritabanlarının ortak yüzüdür. El bu modülü yüklemez ve çalıştırmaz.

## 895. Python modülü decimal

Taban 10 kesir tutar. Para hesabında ikili float yerine anlatılır. El bu modülü yüklemez ve çalıştırmaz.

## 896. Python modülü difflib

İki metin dizisinin farkını ve benzerliğini hesaplamayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 897. Python modülü dis

Derlenmiş kodun işlem kodlarını metin olarak döker. El kodu çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 898. Python modülü doctest

Belge dizisindeki örnek satırları sınama niyetiyle tarif eder. El sınamaz. El bu modülü yüklemez ve çalıştırmaz.

## 899. Python modülü email

E-posta iletisini başlık ve gövde olarak kurmayı ve okumayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 900. Python modülü encodings

Metin kodlamalarının kayıt paketidir. codecs bununla konuşur. El bu modülü yüklemez ve çalıştırmaz.

## 901. Python modülü ensurepip

Kurulumda pip paketini hazırlamayı tarif eder. El pip kurmaz. El bu modülü yüklemez ve çalıştırmaz.

## 902. Python modülü enum

Sabit adlı seçenek kümeleri tanımlar. Değerler adla anılır. El bu modülü yüklemez ve çalıştırmaz.

## 903. Python modülü errno

İşletim sistemi hata numaralarının sembolik adlarını taşır. El bu modülü yüklemez ve çalıştırmaz.

## 904. Python modülü faulthandler

Çökme anında Python izini yazdırmayı tarif eder. El çökme üretmez. El bu modülü yüklemez ve çalıştırmaz.

## 905. Python modülü fcntl

Unix dosya denetim çağrılarını tarif eder. El bu çağrıyı yapmaz. El bu modülü yüklemez ve çalıştırmaz.

## 906. Python modülü filecmp

İki dosya veya iki klasörün içeriğini karşılaştırmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 907. Python modülü fileinput

Birden çok dosyayı art arda satır satır okumayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 908. Python modülü fnmatch

Dosya adını kabuk kalıbıyla (*, ?) karşılaştırmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 909. Python modülü fractions

Tam pay ve payda ile kesir tutar. İkili float yuvarlamasından ayrıdır. El bu modülü yüklemez ve çalıştırmaz.

## 910. Python modülü ftplib

FTP ile dosya aktarmayı tarif eder. El sunucuya bağlanmaz. El bu modülü yüklemez ve çalıştırmaz.

## 911. Python modülü functools

Önbellek, kısmi uygulama ve karşılaştırma gibi işlev araçlarını taşır. El bu modülü yüklemez ve çalıştırmaz.

## 912. Python modülü gc

Çöp toplayıcının eşik ve sayaçlarını okumayı tarif eder. El toplayıcıyı zorlamaz. El bu modülü yüklemez ve çalıştırmaz.

## 913. Python modülü genericpath

posixpath ve ntpath modüllerinin paylaştığı ortak yol işlemleridir. El bu modülü yüklemez ve çalıştırmaz.

## 914. Python modülü getopt

Kısa komut satırı seçeneklerini okumanın eski yoludur. argparse daha yenidir. El bu modülü yüklemez ve çalıştırmaz.

## 915. Python modülü getpass

Parolayı ekrana basmadan okumayı tarif eder. El parola istemez. El bu modülü yüklemez ve çalıştırmaz.

## 916. Python modülü gettext

Arayüz metnini başka dile çevirmek için ileti kataloğu tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 917. Python modülü glob

Klasörde kalıba uyan dosya adlarını bulmayı tarif eder. El klasör dışına çıkmaz. El bu modülü yüklemez ve çalıştırmaz.

## 918. Python modülü graphlib

Düğümlerin birbirine bağlı sırasını (topolojik sıra) kurmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 919. Python modülü grp

Unix grup veritabanını okumayı tarif eder. Windows kartı değildir. El bu modülü yüklemez ve çalıştırmaz.

## 920. Python modülü gzip

gzip ile sıkıştırılmış baytları okur ve yazar. El bu modülü yüklemez ve çalıştırmaz.

## 921. Python modülü hashlib

sha256 gibi özet işlevlerini tarif eder. El özet hesaplatmaz, parola kırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 922. Python modülü heapq

Listeyi yığın gibi kullanarak en küçük öğeyi hızlı seçmeyi tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 923. Python modülü hmac

Bir anahtarla mesaj doğrulama kodu tarif eder. El anahtar üretmez. El bu modülü yüklemez ve çalıştırmaz.

## 924. Python modülü html

Metindeki < ve & işaretlerini kaçırmayı tarif eder. Sayfa iskeleti HTML dilidir, bu modül değildir. El bu modülü yüklemez ve çalıştırmaz.

## 925. Python modülü http

HTTP durum kodları ve istemci parçalarının paketidir. El istek göndermez. El bu modülü yüklemez ve çalıştırmaz.

## 926. Python modülü idlelib

IDLE düzenleyicisinin paketidir. El düzenleyici açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 927. Python modülü imaplib

IMAP ile posta kutusunu okumayı tarif eder. El sunucuya bağlanmaz. El bu modülü yüklemez ve çalıştırmaz.

## 928. Python modülü importlib

Modülün bulunması ve yüklenmesi bu paketle tarif edilir. El yüklemez. El bu modülü yüklemez ve çalıştırmaz.

## 929. Python modülü inspect

İşlevin imzasını, kaynağını ve dosya yerini okumayı tarif eder. El kaynak çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 930. Python modülü io

Bellekte veya dosyada akan metin ve bayt akışlarının temelidir. El bu modülü yüklemez ve çalıştırmaz.

## 931. Python modülü ipaddress

IPv4 ve IPv6 adresini ve ağı nesne olarak tutmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 932. Python modülü itertools

Sayma, zincirleme ve kombinasyon gibi tembel yineleyiciler taşır. El bu modülü yüklemez ve çalıştırmaz.

## 933. Python modülü json

JSON metnini Python sözlük ve listesine çevirmeyi tarif eder. JSON dilinin kartı ayrıdır. El bu modülü yüklemez ve çalıştırmaz.

## 934. Python modülü keyword

Python anahtar sözcüklerinin listesini taşır. def ve class gibi adlar buradadır. El bu modülü yüklemez ve çalıştırmaz.

## 935. Python modülü linecache

Bir kaynak dosyanın istenen satırını önbellekten okumayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 936. Python modülü locale

Ondalık virgül ve para biçimi gibi yerel ayarları tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 937. Python modülü logging

Günlük satırlarını düzey ve hedefe göre yazmayı tarif eder. El günlük açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 938. Python modülü lzma

LZMA ile sıkıştırılmış baytları okur ve yazar. El bu modülü yüklemez ve çalıştırmaz.

## 939. Python modülü mailbox

Maildir ve mbox gibi yerel posta kutusu biçimlerini tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 940. Python modülü marshal

Python değerlerinin iç bayt biçimidir. Güvenilmeyen veri bu modülle açılmaz. El bu modülü yüklemez ve çalıştırmaz.

## 941. Python modülü math

Karekök, yuvarlama ve trigonometri gibi gerçel sayı hesaplarını tanımlar. El bu modülü yüklemez ve çalıştırmaz.

## 942. Python modülü mimetypes

Dosya uzantısından içerik türünü (text/plain gibi) tahmin etmeyi tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 943. Python modülü mmap

Dosyayı bellekten okunur gibi haritalamayı tarif eder. El haritalamaz. El bu modülü yüklemez ve çalıştırmaz.

## 944. Python modülü modulefinder

Bir betiğin hangi modüllere bağlı olduğunu aramayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 945. Python modülü msvcrt

Windows konsolunun C çalışma zamanı uçlarını tarif eder. Unix kartı değildir. El bu modülü yüklemez ve çalıştırmaz.

## 946. Python modülü multiprocessing

Ayrı süreçlerde iş bölmeyi tarif eder. El süreç başlatmaz. El bu modülü yüklemez ve çalıştırmaz.

## 947. Python modülü netrc

netrc dosyasındaki makine ve kullanıcı satırını okumayı tarif eder. El parola kullanmaz. El bu modülü yüklemez ve çalıştırmaz.

## 948. Python modülü nt

Windows'a özgü işletim sistemi çağrılarının modül adıdır. os bunun üzerine konuşur. El bu modülü yüklemez ve çalıştırmaz.

## 949. Python modülü ntpath

Windows yol ayıracını işleyen yol modülüdür. pathlib daha üst yüzdür. El bu modülü yüklemez ve çalıştırmaz.

## 950. Python modülü nturl2path

Windows yolunu file URL biçimine çevirmeyi tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 951. Python modülü numbers

Sayı türlerinin soyut sınıflarını tanımlar. int ve float bunların altındadır. El bu modülü yüklemez ve çalıştırmaz.

## 952. Python modülü opcode

Yorumlayıcının işlem kodu adlarını ve numaralarını taşır. El bu modülü yüklemez ve çalıştırmaz.

## 953. Python modülü operator

Toplama ve öğe okuma gibi işleçlerin işlev karşılığını taşır. El bu modülü yüklemez ve çalıştırmaz.

## 954. Python modülü optparse

Komut satırı ayrıştırmanın eski modülüdür. Yeni kod argparse kullanır. El bu modülü yüklemez ve çalıştırmaz.

## 955. Python modülü os

Dosya, klasör ve ortam değişkeni için işletim sistemi yüzüdür. El komut çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 956. Python modülü pathlib

Dosya yolunu nesne olarak kurar. Kilitli klasörün dışına çıkan yol bu elde yoktur. El bu modülü yüklemez ve çalıştırmaz.

## 957. Python modülü pdb

Satır satır hata ayıklama aracını tarif eder. El ayıklayıcı açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 958. Python modülü pickle

Python nesnesini bayta çevirir. Güvenilmeyen veri bu modülle açılmaz. El bu modülü yüklemez ve çalıştırmaz.

## 959. Python modülü pickletools

pickle baytlarının yapısını okumayı tarif eder. El veri açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 960. Python modülü pkgutil

Paket içindeki modülleri gezmeyi tarif eder. El paket kurmaz. El bu modülü yüklemez ve çalıştırmaz.

## 961. Python modülü platform

İşletim sistemi ve Python sürümünü okumayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 962. Python modülü plistlib

Apple plist dosyasını okumayı ve yazmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 963. Python modülü poplib

POP3 ile posta almayı tarif eder. El sunucuya bağlanmaz. El bu modülü yüklemez ve çalıştırmaz.

## 964. Python modülü posix

Unix işletim sistemi çağrılarının modül adıdır. os bunun üzerine konuşur. El bu modülü yüklemez ve çalıştırmaz.

## 965. Python modülü posixpath

Unix yol ayıracını işleyen yol modülüdür. pathlib bu ailenin üst yüzüdür. El bu modülü yüklemez ve çalıştırmaz.

## 966. Python modülü pprint

Sözlük ve listeyi satır satır okunur basmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 967. Python modülü profile

Eski, saf Python profil aracıdır. Ölçüm için cProfile daha sık anılır. El bu modülü yüklemez ve çalıştırmaz.

## 968. Python modülü pstats

Profil çıktısını okuyup sıralamayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 969. Python modülü pty

Unix sözde uçbirim açmayı tarif eder. El uçbirim açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 970. Python modülü pwd

Unix kullanıcı veritabanını okumayı tarif eder. Windows kartı değildir. El bu modülü yüklemez ve çalıştırmaz.

## 971. Python modülü py_compile

Tek bir .py dosyasını bayt koduna çevirmeyi tarif eder. El derlemez. El bu modülü yüklemez ve çalıştırmaz.

## 972. Python modülü pyclbr

Bir modüldeki sınıf ve işlevleri, gövdeyi çalıştırmadan tarar. El bu modülü yüklemez ve çalıştırmaz.

## 973. Python modülü pydoc

Modülün yardım metnini üretmeyi tarif eder. El yardım sunucusu açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 974. Python modülü pydoc_data

pydoc'un kullandığı konu verilerinin paketidir. El bu modülü yüklemez ve çalıştırmaz.

## 975. Python modülü pyexpat

XML ayrıştırıcısının hızlandırılmış yüzüdür. xml paketi bunun üzerindedir. El bu modülü yüklemez ve çalıştırmaz.

## 976. Python modülü queue

İş parçacıkları arasında güvenli kuyruk tarif eder. El iş parçacığı başlatmaz. El bu modülü yüklemez ve çalıştırmaz.

## 977. Python modülü quopri

Quoted-printable metin kodlamasını okur ve yazar. E-posta gövdesinde geçer. El bu modülü yüklemez ve çalıştırmaz.

## 978. Python modülü random

Sözde rastgele sayı üretir. Gizli anahtar için secrets modülü anılır. El bu modülü yüklemez ve çalıştırmaz.

## 979. Python modülü re

Düzenli ifade ile metin aramayı ve bölmeyi tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 980. Python modülü readline

Unix satır düzenleme kütüphanesine köprüyü tarif eder. El kabuk açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 981. Python modülü reprlib

Çok uzun nesnelerin gösterimini kısaltarak basmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 982. Python modülü resource

Unix süreç kaynak sınırlarını okumayı tarif eder. El sınır değiştirmez. El bu modülü yüklemez ve çalıştırmaz.

## 983. Python modülü rlcompleter

Etkileşimli tamamlamayı readline ile tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 984. Python modülü runpy

Bir modülü dosya gibi çalıştırma düzenini tarif eder. El çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 985. Python modülü sched

Zamanı gelince çağrılacak işleri sıraya koymayı tarif eder. El zamanlayıcıyı başlatmaz. El bu modülü yüklemez ve çalıştırmaz.

## 986. Python modülü secrets

Parola ve jeton için kriptografik rastgele değer tarif eder. El jeton üretmez. El bu modülü yüklemez ve çalıştırmaz.

## 987. Python modülü select

Birden çok soketin hangisinin hazır olduğunu beklemeyi tarif eder. El soket açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 988. Python modülü selectors

select üzerine kurulan daha yüksek bekleme yüzüdür. El bu modülü yüklemez ve çalıştırmaz.

## 989. Python modülü shelve

Anahtar-değer rafını pickle ile dosyaya yazmayı tarif eder. Güvenilmeyen veri açılmaz. El bu modülü yüklemez ve çalıştırmaz.

## 990. Python modülü shlex

Kabuk sözcüklerine göre metni bölmeyi tarif eder. El kabuk çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 991. Python modülü shutil

Dosya kopyalama ve klasör ağacı gezmeyi tarif eder. El dosya silmez. El bu modülü yüklemez ve çalıştırmaz.

## 992. Python modülü signal

Süreç sinyallerini yakalamayı tarif eder. El sinyal göndermez. El bu modülü yüklemez ve çalıştırmaz.

## 993. Python modülü site

Yorumlayıcı açılışında site paketlerinin yolunu kurmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 994. Python modülü smtplib

SMTP ile mektup göndermeyi tarif eder. El sunucuya bağlanmaz. El bu modülü yüklemez ve çalıştırmaz.

## 995. Python modülü socket

Ağ soketi açmayı tarif eder. El bağlantı kurmaz. El bu modülü yüklemez ve çalıştırmaz.

## 996. Python modülü socketserver

Soket dinleyen sunucu iskeletini tarif eder. El sunucu açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 997. Python modülü sqlite3

SQLite dosyasına Python'dan bakmayı tarif eder. SQL dili ayrı karttadır. El dosyayı açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 998. Python modülü sre_compile

re modülünün iç derleyicisidir. Kullanıcı kodu re kullanır. El bu modülü yüklemez ve çalıştırmaz.

## 999. Python modülü sre_constants

Düzenli ifade motorunun iç sabitleridir. Kullanıcı kodu re kullanır. El bu modülü yüklemez ve çalıştırmaz.

## 1000. Python modülü sre_parse

Düzenli ifadeyi iç ağaca çevirir. Kullanıcı kodu re kullanır. El bu modülü yüklemez ve çalıştırmaz.

## 1001. Python modülü ssl

Soketin üzerine TLS sarmalamayı tarif eder. El sertifika ve bağlantı açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1002. Python modülü stat

Dosya izin bitlerinin ve tür bayraklarının adlarını taşır. El bu modülü yüklemez ve çalıştırmaz.

## 1003. Python modülü statistics

Ortalama, ortanca ve standart sapma gibi özet hesapları tanımlar. El bu modülü yüklemez ve çalıştırmaz.

## 1004. Python modülü string

Hazır harf kümeleri ve eski metin şablonu araçlarını taşır. El bu modülü yüklemez ve çalıştırmaz.

## 1005. Python modülü stringprep

Unicode dizgisini RFC stringprep kurallarıyla hazırlamayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1006. Python modülü struct

Sayıları C dilindeki gibi sabit bayt düzenine çevirmeyi tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1007. Python modülü subprocess

Başka bir süreci başlatmayı tarif eder. El süreç başlatmaz ve komut çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1008. Python modülü symtable

Derleyicinin sembol tablosunu okumayı tarif eder. El kod çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1009. Python modülü sys

Sürüm, yol ve komut argümanı gibi yorumlayıcı durumunu okumayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1010. Python modülü sysconfig

Python'un kurulu olduğu yolları ve derleme ayarlarını okumayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1011. Python modülü syslog

Unix sistem günlüğüne yazmayı tarif eder. El günlük açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1012. Python modülü tabnanny

Girinti tutarsızlığını aramayı tarif eder. El dosyayı değiştirmez. El bu modülü yüklemez ve çalıştırmaz.

## 1013. Python modülü tarfile

tar arşivini okumayı ve yazmayı tarif eder. El arşiv açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1014. Python modülü tempfile

Geçici dosya ve klasör adını tarif eder. El dosya bırakmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1015. Python modülü termios

Unix uçbirim ayarlarını tarif eder. El uçbirimi değiştirmez. El bu modülü yüklemez ve çalıştırmaz.

## 1016. Python modülü textwrap

Uzun metni verilen genişlikte satırlara bölmeyi tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1017. Python modülü this

Zen of Python metnini gösteren küçük modüldür. El o metni basmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1018. Python modülü threading

İş parçacığı başlatmayı tarif eder. El iş parçacığı açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1019. Python modülü time

Saniye, uyku ve saat okumayı tarif eder. El programı uyutmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1020. Python modülü timeit

Küçük bir kod parçasının süresini ölçmeyi tarif eder. El ölçüm başlatmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1021. Python modülü tkinter

Tk ile pencere ve düğme kurmayı tarif eder. El pencere açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1022. Python modülü token

Sözcük türlerinin numaralarını taşır. tokenize bu numaraları kullanır. El bu modülü yüklemez ve çalıştırmaz.

## 1023. Python modülü tokenize

Python kaynağını sözcüklere ayırmayı tarif eder. El kaynak çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1024. Python modülü tomllib

TOML ayar dosyasını okumayı tarif eder. Yalnızca okuma yüzüdür. El bu modülü yüklemez ve çalıştırmaz.

## 1025. Python modülü trace

Hangi satırların işlendiğini izlemeyi tarif eder. El iz sürmez. El bu modülü yüklemez ve çalıştırmaz.

## 1026. Python modülü traceback

Hata izini metin olarak biçimlemeyi tarif eder. El hata üretmez. El bu modülü yüklemez ve çalıştırmaz.

## 1027. Python modülü tracemalloc

Hangi satırın bellek ayırdığını izlemeyi tarif eder. El iz açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1028. Python modülü tty

Unix uçbirimini ham veya pişmiş kipe almayı tarif eder. El kip değiştirmez. El bu modülü yüklemez ve çalıştırmaz.

## 1029. Python modülü turtle

Kaplumbağa grafiğiyle çizim yapmayı tarif eder. El pencere açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1030. Python modülü turtledemo

turtle örneklerinin paketidir. El örnek çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1031. Python modülü types

İşlev, modül ve None türü gibi hazır tür nesnelerini taşır. El bu modülü yüklemez ve çalıştırmaz.

## 1032. Python modülü typing

Liste, sözlük ve isteğe bağlı tür gibi notları yazmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1033. Python modülü unicodedata

Bir harfin Unicode adını ve kategorisini okumayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1034. Python modülü unittest

Sınama sınıfı ve doğrulama yöntemlerini tarif eder. El sınama çalıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1035. Python modülü urllib

Adres okuma ve çözümleme paketidir. El ağa çıkmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1036. Python modülü uuid

Evrensel benzersiz kimlik üretmeyi tarif eder. El kimlik dağıtmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1037. Python modülü venv

Sanal Python ortamı kurmayı tarif eder. El ortam kurmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1038. Python modülü warnings

Uyarı süzmeyi ve uyarı basmayı tarif eder. El uyarı üretmez. El bu modülü yüklemez ve çalıştırmaz.

## 1039. Python modülü wave

WAV ses dosyasının başlığını okumayı tarif eder. El ses çalmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1040. Python modülü weakref

Nesneyi, çöp toplayıcıyı tek başına tutmadan anmayı tarif eder. El bu modülü yüklemez ve çalıştırmaz.

## 1041. Python modülü webbrowser

Sistem tarayıcısını açmayı tarif eder. El tarayıcı açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1042. Python modülü winreg

Windows kayıt defterini okumayı tarif eder. El kayıt defterini açmaz ve yazmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1043. Python modülü winsound

Windows'ta kısa ses çalmayı tarif eder. El ses çalmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1044. Python modülü wsgiref

WSGI sunucu iskeletinin referans paketidir. El sunucu açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1045. Python modülü xml

XML okuma paketinin üst adıdır. El belge indirip ayrıştırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1046. Python modülü xmlrpc

XML-RPC çağrısını tarif eder. El uzaktaki yordamı çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1047. Python modülü zipapp

Bir klasörü tek çalıştırılabilir zip uygulamaya sarmayı tarif eder. El paketlemez. El bu modülü yüklemez ve çalıştırmaz.

## 1048. Python modülü zipfile

ZIP arşivini okumayı ve yazmayı tarif eder. El arşiv açmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1049. Python modülü zipimport

ZIP içinden modül yüklemeyi tarif eder. El yüklemez. El bu modülü yüklemez ve çalıştırmaz.

## 1050. Python modülü zlib

DEFLATE sıkıştırmasının temel modülüdür. gzip bunun üzerine kuruludur. El bu modülü yüklemez ve çalıştırmaz.

## 1051. Python modülü zoneinfo

IANA saat dilimi veritabanını tarif eder. datetime buna bağlanır. El bu modülü yüklemez ve çalıştırmaz.

## 1052. Python iç modülü __future__

__future__, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1053. Python iç modülü _abc

_abc, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1054. Python iç modülü _aix_support

_aix_support, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1055. Python iç modülü _android_support

_android_support, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1056. Python iç modülü _apple_support

_apple_support, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1057. Python iç modülü _ast

_ast, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1058. Python iç modülü _ast_unparse

_ast_unparse, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1059. Python iç modülü _asyncio

_asyncio, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1060. Python iç modülü _bisect

_bisect, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1061. Python iç modülü _blake2

_blake2, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1062. Python iç modülü _bz2

_bz2, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1063. Python iç modülü _codecs

_codecs, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1064. Python iç modülü _codecs_cn

_codecs_cn, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1065. Python iç modülü _codecs_hk

_codecs_hk, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1066. Python iç modülü _codecs_iso2022

_codecs_iso2022, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1067. Python iç modülü _codecs_jp

_codecs_jp, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1068. Python iç modülü _codecs_kr

_codecs_kr, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1069. Python iç modülü _codecs_tw

_codecs_tw, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1070. Python iç modülü _collections

_collections, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1071. Python iç modülü _collections_abc

_collections_abc, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1072. Python iç modülü _colorize

_colorize, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1073. Python iç modülü _compat_pickle

_compat_pickle, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1074. Python iç modülü _contextvars

_contextvars, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1075. Python iç modülü _csv

_csv, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1076. Python iç modülü _ctypes

_ctypes, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1077. Python iç modülü _curses

_curses, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1078. Python iç modülü _curses_panel

_curses_panel, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1079. Python iç modülü _datetime

_datetime, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1080. Python iç modülü _dbm

_dbm, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1081. Python iç modülü _decimal

_decimal, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1082. Python iç modülü _elementtree

_elementtree, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1083. Python iç modülü _frozen_importlib

_frozen_importlib, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1084. Python iç modülü _frozen_importlib_external

_frozen_importlib_external, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1085. Python iç modülü _functools

_functools, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1086. Python iç modülü _gdbm

_gdbm, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1087. Python iç modülü _hashlib

_hashlib, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1088. Python iç modülü _heapq

_heapq, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1089. Python iç modülü _hmac

_hmac, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1090. Python iç modülü _imp

_imp, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1091. Python iç modülü _interpchannels

_interpchannels, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1092. Python iç modülü _interpqueues

_interpqueues, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1093. Python iç modülü _interpreters

_interpreters, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1094. Python iç modülü _io

_io, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1095. Python iç modülü _ios_support

_ios_support, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1096. Python iç modülü _json

_json, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1097. Python iç modülü _locale

_locale, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1098. Python iç modülü _lsprof

_lsprof, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1099. Python iç modülü _lzma

_lzma, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1100. Python iç modülü _markupbase

_markupbase, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1101. Python iç modülü _md5

_md5, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1102. Python iç modülü _multibytecodec

_multibytecodec, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1103. Python iç modülü _multiprocessing

_multiprocessing, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1104. Python iç modülü _opcode

_opcode, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1105. Python iç modülü _opcode_metadata

_opcode_metadata, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1106. Python iç modülü _operator

_operator, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1107. Python iç modülü _osx_support

_osx_support, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1108. Python iç modülü _overlapped

_overlapped, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1109. Python iç modülü _pickle

_pickle, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1110. Python iç modülü _posixshmem

_posixshmem, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1111. Python iç modülü _posixsubprocess

_posixsubprocess, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1112. Python iç modülü _py_abc

_py_abc, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1113. Python iç modülü _py_warnings

_py_warnings, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1114. Python iç modülü _pydatetime

_pydatetime, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1115. Python iç modülü _pydecimal

_pydecimal, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1116. Python iç modülü _pyio

_pyio, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1117. Python iç modülü _pylong

_pylong, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1118. Python iç modülü _pyrepl

_pyrepl, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1119. Python iç modülü _queue

_queue, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1120. Python iç modülü _random

_random, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1121. Python iç modülü _remote_debugging

_remote_debugging, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1122. Python iç modülü _scproxy

_scproxy, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1123. Python iç modülü _sha1

_sha1, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1124. Python iç modülü _sha2

_sha2, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1125. Python iç modülü _sha3

_sha3, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1126. Python iç modülü _signal

_signal, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1127. Python iç modülü _sitebuiltins

_sitebuiltins, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1128. Python iç modülü _socket

_socket, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1129. Python iç modülü _sqlite3

_sqlite3, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1130. Python iç modülü _sre

_sre, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1131. Python iç modülü _ssl

_ssl, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1132. Python iç modülü _stat

_stat, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1133. Python iç modülü _statistics

_statistics, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1134. Python iç modülü _string

_string, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1135. Python iç modülü _strptime

_strptime, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1136. Python iç modülü _struct

_struct, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1137. Python iç modülü _suggestions

_suggestions, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1138. Python iç modülü _symtable

_symtable, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1139. Python iç modülü _sysconfig

_sysconfig, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1140. Python iç modülü _thread

_thread, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1141. Python iç modülü _threading_local

_threading_local, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1142. Python iç modülü _tkinter

_tkinter, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1143. Python iç modülü _tokenize

_tokenize, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1144. Python iç modülü _tracemalloc

_tracemalloc, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1145. Python iç modülü _types

_types, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1146. Python iç modülü _typing

_typing, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1147. Python iç modülü _uuid

_uuid, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1148. Python iç modülü _warnings

_warnings, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1149. Python iç modülü _weakref

_weakref, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1150. Python iç modülü _weakrefset

_weakrefset, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1151. Python iç modülü _winapi

_winapi, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1152. Python iç modülü _wmi

_wmi, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1153. Python iç modülü _zoneinfo

_zoneinfo, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.

## 1154. Python iç modülü _zstd

_zstd, CPython 3.14.5 standart kütüphane listesindeki iç modüldür. Kullanıcı kodu bunu doğrudan çağırmaz. El bu modülü yüklemez ve çalıştırmaz.
