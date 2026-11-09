# Standartlar ve protokol güvenlik analizi

pillar: dual_analysis
lisans: Rüzgar iç omurga
amaç: akademik / blue-red teori

Rüzgar siber kütüphanesi — akademik omurga (savunma + test teorisi).

## OWASP Top 10 (kavram)
Yaygın web uygulama risk sınıfları: erişim denetimi kırıkları, kriptografik hatalar,
enjeksiyon, güvensiz tasarım, yanlış yapılandırma, bileşen zafiyetleri, kimlik doğrulama
başarısızlıkları, yazılım/veri bütünlüğü, güvenlik günlükleme ve izleme eksikleri,
sunucu tarafı istek sahteciliği (SSRF). Amaç: risk dili ortaklaştırmak; istismar kodu değil.

## NIST CSF 2.0 işlevleri
Govern · Identify · Protect · Detect · Respond · Recover. Organizasyonel risk yönetimi
ve olay müdahalesi için sonuç odaklı çerçeve.

## TCP/IP güvenlik bakışı (analiz)
- IP: sahte kaynak, parçalama, yönlendirme güveni.
- TCP: SYN taşması, oturum kaçırma (teorik), sıra numarası tahmini tarihi riskleri.
- HTTP: kimlik bilgisi sızıntısı, önbellek zehirlenmesi kavramları, başlık enjeksiyonu.
- TLS: sürüm düşürme, zayıf şifre takımları, sertifika doğrulama hataları, perfect forward secrecy.

Analiz sorusu örneği: «TLS 1.2 ile 1.3 arasındaki güvenlik farkı nedir?» — Rüzgar RFC + NIST
metinlerinden yanıtlar.
