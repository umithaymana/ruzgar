# F8.1 / F8.2 — LAN & public mode uyarıları

**Tarih:** 2026-11-17 · Mimar: Ümit & Gökçenur

## F8.1 — LAN / CORS

- `desktop_server` LAN’da açıkken (`0.0.0.0:8779` + HTTPS `8443`) **ev ağı** varsayılır.
- Bu bir güvenlik duvarı veya kimlik doğrulama ürünü **değildir**.
- Sıkılaştırma: yalnızca localhost dinle; Tailscale ile sınırlı cihaz; `RUZGAR_PUBLIC_MODE` kapalı tut.
- Mobil mic için HTTPS şart — HTTP’de getUserMedia ölür (PWA otomatik 8443’e iter).

## F8.2 — Public mode

- Public / paylaşılan indeks yolu **auth değildir**.
- Token/Bearer spoof’a karşı tam ürün koruması yok — «bilinçli ev kullanımı».
- Halka açılış (kimlik+TLS ürünü) bu planda **bilinçli ertelenmiş**.

## F8.6 — OSM / harita

- Dünya Gezgini / OSM / CameraRig yarım işleri bu sohbet-kütüphane-ses planından **ayrı / dondurulmuş**.
- Working tree kirliliği: sahne commit’i bu plana karıştırılmaz.
