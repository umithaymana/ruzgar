# Zafiyet ve tehdit modelleme literatürü

pillar: dual_analysis
lisans: Rüzgar iç omurga
amaç: akademik / blue-red teori

## Tehdit modelleme
Varlık → tehdit aktörü → saldırı yüzeyi → azaltım. STRIDE / ATT&CK / CAPEC dilinde
sınıflandırma. Attack surface: giriş noktaları, güven sınırları, veri akışları.

## Statik analiz (SAST) mantığı
Kaynak/bayt kodunda kalıp ve veri akışı taraması; yanlış pozitif/negatif dengesi;
güvenlik kuralları (enjeksiyon, path traversal, zayıf kripto). Çalıştırmaz; inceler.

## Dinamik analiz (DAST) mantığı
Çalışan uygulamaya kontrollü girdiler; davranış gözlemi. Laboratuvar / yetkili test
kapsamında. Rüzgar burada yalnızca metodoloji ve raporlama ilkelerini tutar.

## Zafiyet tarama mantığı
İmza + sürüm eşleştirme + yapılandırma kontrolleri. Sonuç = hipotez; doğrulama gerekir.
CVE/CWE dili ile sınıflandırma.
