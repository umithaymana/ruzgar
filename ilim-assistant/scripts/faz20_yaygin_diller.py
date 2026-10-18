# -*- coding: utf-8 -*-
"""Faz 20 ek — 2026 yoğun kullanılan diller ve üç eşlikçi.

Ölçü: Stack Overflow 2026, son bir yılda yoğun kullanım, yüzde 10 ve üstü.
HTML, CSS, JavaScript ve Python ilk rafta durur. Burada kalanlar ve eşlikçiler var.
Eğitim özeti. Telifli tam metin yok. Saldırı ve exploit yok.
"""
from __future__ import annotations


def _dort(
    kok: str,
    baslik: str,
    aliases: list[str],
    nedir: str,
    duzen: str,
    calistirma: str,
    sinama: str,
) -> list[tuple[str, str, list[str], str]]:
    return [
        (f"{kok}_dili", f"{baslik} dili", aliases, nedir),
        (
            f"{kok}_dosya_duzeni",
            f"{baslik} dosya düzeni",
            [f"{kok} dosya duzeni", f"{kok} dosyalari nasil durur"],
            duzen,
        ),
        (
            f"{kok}_calistirma",
            f"{baslik} çalıştırma",
            [f"{kok} nasil calistirilir", f"{kok} nasıl çalıştırılır"],
            calistirma,
        ),
        (
            f"{kok}_sinama",
            f"{baslik} sınama",
            [f"{kok} nasil sinanir", f"{kok} nasıl sınanır"],
            sinama,
        ),
    ]


PARCALAR_EK: list[tuple[str, str, list[str], str]] = []

PARCALAR_EK += _dort(
    "typescript",
    "TypeScript",
    ["typescript", "typescript nedir", "typescript ile ne yazilir", "typescript ile neler yazilir"],
    "TypeScript, JavaScript'in tipli halidir. Büyük web uygulaması, tarayıcı arayüzü ve sunucu betiği yazılır. Değişkenin türü yazılır; yanlış tür kayıttan önce görülür. Tarayıcı TypeScript'i doğrudan okumaz, JavaScript'e çevrilmiş dosyayı açar. Bu not dili öğretir.",
    "Kaynak ts/ içinde durur. Derlenmiş çıktı js/ altına iner. tsconfig.json kökte tür ve hedefi söyler. HTML, üretilen js dosyasını çağırır. Kaynak ile üretilen dosya karışmaz.",
    "Çalışan dosya, çevrilmiş JavaScript'tir. Sayfa tarayıcıda açılır. Ayrı bir sunucu şart değildir. Çeviri aracı kurulu değilse elde yalnız kaynak metin durur; el onu çalıştırmaz.",
    "Sınama, türün tutması ve saf fonksiyonun sabit girdiye sabit çıktı vermesidir. Sayfada düğmenin metni değişiyor mu diye bakılır. Bu sınama başkasının oturumunu ele geçirmez.",
)

PARCALAR_EK += _dort(
    "sql",
    "SQL",
    ["sql", "sql nedir", "sql ile ne yazilir", "sql ile neler yazilir"],
    "SQL, tablodaki veriyi seçmek, süzmek ve saymak için yazılır. Uygulama ekranı yazılmaz. Sorgu bir cümledir: hangi tablo, hangi koşul, hangi sütun. Veriyi silen veya başkasının tablosunu açan sorgu bu notun konusu değildir.",
    "Küçük işte sorgu.sql tek dosyada durur. Tablo tanımı ayrı, seçme sorgusu ayrı yazılırsa okumak kolaylaşır. Veri dosyası data/ altında kalır. Sorgu, uygulama kodunun içine gizlenmez.",
    "SQL kendi başına bir program olarak çift tıklanmaz. Bir veritabanı aracı sorguyu okur ve satır döndürür. El, sorgu metnini okur; veritabanını kendiliğinden açmaz.",
    "Sınama, bilinen bir tabloya sorulunca beklenen satır sayısının gelmesidir. Boş koşul bütün tabloyu döndürür; koşul yazılır. Bu sınama başkasının verisini çekmek için kullanılmaz.",
)

PARCALAR_EK += _dort(
    "bash",
    "Bash",
    ["bash", "bash nedir", "kabuk", "bash ile ne yazilir", "bash ile neler yazilir"],
    "Bash, Unix kabuğunda kendi klasöründeki işi sıraya koymak için yazılır. Dosya adını basmak, bir metni başka dosyaya aktarmak ve küçük bir görevi adlandırmak bu dilin işidir. Başkasının makinesine komut göndermez. Silme bu notta yoktur.",
    "Betik bin/ veya kökte is.sh olarak durur. Ad işi söyler. Gizli anahtar betiğin içine yazılmaz. Üretilen çıktı cikti/ altında kalır.",
    "Kabuk, betiği kendi klasöründe okur. El bu betiği kendiliğinden çalıştırmaz. Çalıştırma, sen söyleyince ve yalnız o dosyada olur.",
    "Sınama, betiğin beklenen dosya adını yazıp yazmadığına bakmaktır. Yan etki istenmiyorsa betik önce boş bir deneme klasöründe okunur. Bu sınama sistemi bozmak için kullanılmaz.",
)

PARCALAR_EK += _dort(
    "java",
    "Java",
    ["java", "java nedir", "java dili", "java ile ne yazilir", "java ile neler yazilir"],
    "Java ile kurum sunucusu, masaüstü aracı ve uzun ömürlü uygulama yazılır. Sınıf işi böler, paket dosyaları toplar. JavaScript ile aynı şey değildir. Bu not dili öğretir.",
    "Kaynak src/ altında paket klasöründe .java dosyası olarak durur. Derlenmiş sınıf ayrı bir çıktı klasörüne iner. Proje adı ve paket adı karışmaz.",
    "Kurulu araç kaynağı sınıf dosyasına çevirir ve o sınıf okunur. El kaynağı okur, kendiliğinden derlemez ve çalıştırmaz.",
    "Sınama, bir metodun sabit girdiye sabit sonuç vermesidir. Test sınıfı kaynakla aynı paketin test klasöründe durur. Bu sınama güvenlik taraması değildir.",
)

PARCALAR_EK += _dort(
    "csharp",
    "C#",
    ["csharp", "c sharp", "c# nedir", "csharp nedir", "c# ile ne yazilir", "csharp ile ne yazilir"],
    "C# ile Windows uygulaması, oyun aracı ve kurum sunucusu yazılır. Türler yazılır, proje bir çözüm klasöründe durur. Bu not dili öğretir.",
    "Kaynak .cs dosyası proje klasöründedir. Proje dosyası hangi kaynakların birlikte derleneceğini söyler. Çıktı bin altında kalır, kaynakla karışmaz.",
    "Proje aracı çözümü derler. El .cs metnini okur. Kendiliğinden derlemez ve çalıştırmaz.",
    "Sınama, bir metodun beklenen değeri döndürmesidir. Test projesi ayrı durur. Bu sınama başkasının sürecine karışmaz.",
)

PARCALAR_EK += _dort(
    "powershell",
    "PowerShell",
    ["powershell", "powershell nedir", "powershell ile ne yazilir", "powershell ile neler yazilir"],
    "PowerShell, Windows'ta kendi klasöründeki işi sıraya koymak için yazılır. Dosya adını basmak ve bir metni okumak bu dilin işidir. Bash'in Windows'taki karşılığına yakındır. Silme ve uzaktaki makineye komut bu notta yoktur.",
    "Betik .ps1 olarak kökte veya bin/ altında durur. Ad işi söyler. Gizli anahtar içine yazılmaz.",
    "Windows kabuğu betiği okur. Çalışan yer, kullanıcının kendi klasörüdür. El betiği kendiliğinden çalıştırmaz.",
    "Sınama, betiğin beklenen adı yazıp yazmadığına bakmaktır. Deneme kendi klasöründe kalır. Bu sınama sistemi değiştirmek için kullanılmaz.",
)

PARCALAR_EK += _dort(
    "cpp",
    "C++",
    ["cpp", "c++", "c arti arti", "c++ nedir", "cpp nedir", "c++ ile ne yazilir", "cpp ile ne yazilir"],
    "C++ ile oyun motoru, sistem aracı ve hız isteyen program yazılır. Bellek ve tür programcıdadır. C'nin üzerine sınıf ve şablon ekler. Bu not dili öğretir. Zararlı kod yazılmaz.",
    "Kaynak src/ içinde .cpp ve .h olarak durur. Derleme tarifi kökte bir dosyada yazılır. Üretilen program çıktı klasörüne iner.",
    "Derleyici kaynağı makine koduna çevirir. El kaynağı okur. Kendiliğinden derlemez ve çalıştırmaz.",
    "Sınama, saf bir fonksiyonun sabit girdiye sabit çıktı vermesidir. Test derlemesi ayrıdır. Bu sınama bellek bozmak için kullanılmaz.",
)

PARCALAR_EK += _dort(
    "c",
    "C",
    ["c dili", "c dili nedir", "c dili ile ne yazilir", "c dili ile neler yazilir"],
    "C dili ile işletim çekirdeğine yakın araç ve gömülü aygıt programı yazılır. Az araçla çok iş yapılır. C++ ve C# başka dillerdir. Bu not dili öğretir. Zararlı kod yazılmaz.",
    "Kaynak src/ içinde .c ve .h olarak durur. Her dosya bir işi taşır. Derleme tarifi ayrı yazılır.",
    "Derleyici .c dosyasını çevirir. El metni okur. Kendiliğinden derlemez ve çalıştırmaz.",
    "Sınama, fonksiyonun bilinen girdiye bilinen sayı döndürmesidir. Taşan bellek bu notun örneği değildir.",
)

PARCALAR_EK += _dort(
    "rust",
    "Rust",
    ["rust", "rust nedir", "rust dili", "rust ile ne yazilir", "rust ile neler yazilir"],
    "Rust ile bellek güvenliği isteyen sistem aracı ve ağ servisi yazılır. Ödünç alma kuralları, geçersiz bellek kullanımını derlemede durdurur. Bu not dili öğretir.",
    "Kökte Cargo.toml projeyi tanıtır. Kaynak src/main.rs veya src/lib.rs içindedir. Bağımlılık sürümü toml dosyasında durur, koda gömülmez.",
    "Proje aracı kaynağı derler. El rs metnini okur. Kendiliğinden derlemez ve çalıştırmaz.",
    "Sınama, kütüphane fonksiyonunun sabit girdiye sabit çıktı vermesidir. Test kaynakla aynı pakette durur. Bu sınama güvenlik açığı aramak değildir.",
)

PARCALAR_EK += _dort(
    "php",
    "PHP",
    ["php", "php nedir", "php dili", "php ile ne yazilir", "php ile neler yazilir"],
    "PHP ile sunucunun her istekte ürettiği web sayfası yazılır. HTML iskeletin içine sunucu hesabı girer. Tarayıcıya giden sonuç HTML'dir. Gizli anahtar koda yazılmaz.",
    "Genel sayfalar public/ altında .php olarak durur. Ortak fonksiyon includes/ içinde durur. Ayar dosyası kaynak ağacının dışındaki ortamda kalır.",
    "Sayfa bir PHP okuyucusu olan sunucuda açılır. El dosyayı metin olarak okur. Kendiliğinden sunucu kurmaz ve çalıştırmaz.",
    "Sınama, saf bir fonksiyonun beklenen metni üretmesidir. Sayfanın başlığı tarayıcıda kontrol edilir. Bu sınama sunucuya sızmak için kullanılmaz.",
)

PARCALAR_EK += _dort(
    "go",
    "Go",
    ["go", "golang", "go nedir", "go dili", "go ile ne yazilir", "golang ile ne yazilir"],
    "Go ile ağ servisi, küçük sunucu ve komut satırı aracı yazılır. Az sözdizimi ve hızlı derleme esastır. Bu not dili öğretir.",
    "Kökte go.mod modülün adını söyler. Kaynak .go dosyaları paket klasöründedir. Komut cmd/ altında, kütüphane iç pakette durur.",
    "Go aracı paketi derler. Üretilen program çıktı klasörüne iner. El kaynağı okur. Kendiliğinden derlemez ve çalıştırmaz.",
    "Sınama, fonksiyonun sabit girdiye sabit çıktı vermesidir. Test dosyası _test.go ile biter. Bu sınama ağa saldırmaz.",
)

PARCALAR_EK += _dort(
    "kotlin",
    "Kotlin",
    ["kotlin", "kotlin nedir", "kotlin ile ne yazilir", "kotlin ile neler yazilir"],
    "Kotlin ile Android uygulaması ve JVM üzerinde çalışan sunucu aracı yazılır. Java kütüphaneleriyle aynı makinede durabilir. Bu not dili öğretir.",
    "Uygulama kaynağı app/src altında .kt dosyasıdır. Gradle dosyası hangi kütüphanenin ineceğini söyler. Gizli anahtar depoya yazılmaz.",
    "Proje aracı paketi derler. El .kt metnini okur. Kendiliğinden derlemez, telefona kurmaz ve çalıştırmaz.",
    "Sınama, bir fonksiyonun beklenen değeri döndürmesidir. Test kaynak ağacının test klasöründedir. Bu sınama cihaz ele geçirmez.",
)

PARCALAR_EK += _dort(
    "json",
    "JSON",
    ["json", "json nedir", "json ile ne yazilir", "json ile neler yazilir"],
    "JSON, programların birbirine verdiği veri dosyası için yazılır. Uygulama davranışı yazılmaz. Nesne, dizi, metin ve sayı tutar. Yorum satırı yoktur.",
    "Veri data/ içinde .json olarak durur. Ad işi söyler: ayar.json, liste.json. İç içe yapı gerekmedikçe düz kalır.",
    "JSON çalıştırılmaz. Bir program onu okur ve sözlüğe çevirir. El metni okur, dosyayı kendiliğinden yüklemez.",
    "Sınama, dosyanın geçerli JSON olması ve beklenen anahtarı taşımasıdır. Eksik virgül dosyayı bozar. Bu sınama veri çalmaz.",
)

PARCALAR_EK += _dort(
    "markdown",
    "Markdown",
    ["markdown", "markdown nedir", "markdown ile ne yazilir", "markdown ile neler yazilir"],
    "Markdown, not, belge ve okuma metni yazmak içindir. Program çalıştırmaz. Başlık, liste ve bağlantı düz karakterle yazılır.",
    "Notlar docs/ veya kökte .md olarak durur. Bir dosya bir konuyu anlatır. Üretilen HTML varsa ayrı klasörde kalır.",
    "Markdown çalıştırılmaz. Bir görüntüleyici onu başlık ve paragrafa çevirir. El ham metni okur.",
    "Sınama, başlık satırının beklenen metni taşımasıdır. Bozuk bağlantı bir dosyaya gitmiyorsa not düşülür. Bu sınama sayfa bozmak için kullanılmaz.",
)

PARCALAR_EK += _dort(
    "sqlite",
    "SQLite",
    ["sqlite", "sqlite nedir", "sqlite ile ne yazilir", "sqlite ile neler yazilir"],
    "SQLite, tek dosyada duran veritabanıdır. Tablo ve sorgu SQL ile yazılır. Ayrı bir veritabanı sunucusu gerekmez. Uygulama ekranı bu dosyada yazılmaz.",
    "Veri data/uygulama.db olarak durur. Tablo kuran SQL data/sema.sql içindedir. Veritabanı dosyası kaynak kodla karışmaz.",
    "SQLite aracı dosyayı açar ve SQL okur. El şemayı metin olarak okur. Veritabanını kendiliğinden açmaz ve çalıştırmaz.",
    "Sınama, bilinen satır sayısının sorgudan dönmesidir. Deneme kopyası ayrı dosyadadır. Bu sınama başkasının veritabanını açmaz.",
)


_IKIZ = (
    ("yazilir", "yazılır"),
    ("nasil", "nasıl"),
    ("calistirilir", "çalıştırılır"),
    ("sinanir", "sınanır"),
    ("dosyalari", "dosyaları"),
)


def _ikizle(parcalar: list[tuple[str, str, list[str], str]]) -> list[tuple[str, str, list[str], str]]:
    yeni: list[tuple[str, str, list[str], str]] = []
    for kid, title, aliases, metin in parcalar:
        ek = list(aliases)
        for ad in aliases:
            b = ad
            for src, dst in _IKIZ:
                b = b.replace(src, dst)
            if b != ad and b not in ek:
                ek.append(b)
        yeni.append((kid, title, ek, metin))
    return yeni


PARCALAR_EK = _ikizle(PARCALAR_EK)
