# RÜZGAR — oturum özeti (kalıcı)

**Son güncelleme:** 2026-05-10

Bu dosya sohbet sıfırlanınca bağlamı taşımak için tutulur. Kapatmadan önce «durumu güncelle» denmesi yeterli (çarpı ile kapanışta otomatik yazılamaz).

## Kuzey yıldızı — asıl amaç

**Rüzgar’ı dijital kayıt cihazı veya dar bir araç değil; bağlam kuran, tam teşekküllü bir asistan yapmak istiyoruz.** Hedef, ChatGPT veya Gemini’ye benzeyen çizgide: geniş bilgi ve akıl yürütme, sorulara anlamlı yanıt, problemleri çözmeye çalışma, gerektiğinde program üretip projeyi çalışır hale getirebilme — yani **her şeyi bilen tek bir devasa liste değil**, katmanlı hafıza + bilgi + dil modeli ve motorlarla **gerçek bir yapay zekâ yardımcısı** oluşturmak. Atölyeler (video, programlama, tercüme vb.) bu vizyonun **parçaları**; amaç bunların üzerinde birleşen **tek yüz ve güçlü akıl**.

## Bu oturumda netleşenler

- **Sohbet belleği:** Bilgisayar/kapanış sonrası model bağlamı sıfırlanır; tam çözüm **bu dosya + anlamlı commit mesajları**.
- **Plan özeti (önceki oturumlardan):** Katmanlı akıl (hafıza + RAG + LLM); beş ara motor (Ses, Video, Okuma, Tercüme, Programlama) güçlenir, sonra Ana Motor’da orkestrasyon; `.cursorrules` motor sırasına uy.
- **Programlama Atölyesi:** Kodda **Faz 1.1–1.3** işlenmiş (arayüzde «1.3 tamam»). **1.4 / 1.5 / 1.6** diye sabit bir üst sınır yok; numaralandırma ihtiyaca göre uzar.
- **Video Atölyesi:** **v1–v4** tarafında temel işlevler kodlandı (kesim, dönüştürme, birleştirme, altyazı gömme, ses bağlama, zaman çizelgesi, altyazıyı Tercüme’ye gönderme). FFmpeg ortamı doğrulanmıştı.
- **Arayüz:** Kullanıcıya dönük metinler Türkçeleştirildi; çok dillilik sonra bağlanacak.
- **Doğrulama:** `ruzgar-desktop` içinde `npm run test:phase11` — kod kartı fenced ayrıştırma senkron kontrolü.

## Sıradaki adım (devam)

Örnek seçenekler: çeviri sonrası **`.srt` üretimi** veya **yumuşak altyazı izi**; arayüz için **çeviri anahtarları**; Programlama **Faz 1.4+**; Ana Motor’dan **tek sohbetten motor orkestrasyonu**. Öncelik her oturumda birlikte seçilir.

## Referans

Geçmiş Cursor oturum özetleri (yerel): `agent-transcripts` altında; örn. programlama / plan tartışması ile ilişkili kayıtlar `2ef431a9-a39f-4e81-90ce-896ec19d93f9`, plan özeti `b8ad8767-ad71-4e4d-8cf0-09b001298000`.

---

**Not:** Yeni oturumda önce bu dosyayı okuyarak devam et; özellikle **Kuzey yıldızı** bölümü proje kararları için bağlayıcı vizyondur.
