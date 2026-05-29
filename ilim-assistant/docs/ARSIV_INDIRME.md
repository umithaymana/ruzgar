# Arşiv indirme (Tercüme atölyesi)

Ümit onayı ile **Internet Archive** üzerinden seçilmiş açık erişim PDF’ler `ilim-assistant/arsiv/` altındaki klasörlere iner.

## Panelde kullanım

1. **Tercüme motoru** → orta sütun **İnternet kaynakları** → **Ara** (B planı: DuckDuckGo genel + Archive / Yazma Eserler / Şamile… birleşik liste).
2. Sohbette `… eserlerini ara` veya orta kutuda arama — gerçek sonuçlar listelenir (Groq’a gitmez).
3. Siteyi açıp inceleyin → **İndir (klasör seç)** ile URL indirin.
4. Sol listeden dosyaya tıklayın → kaynak panel; **Çevir** ile devam.
5. Sol sütunda **Arşiv indir**: manifest’ten toplu indirme.

## Manifest

Kayıt listesi: `ilim-assistant/arsiv/arsiv_indirme_manifest.json`  
Büyük dosyalar (ör. ~95 MB tarama) indirme birkaç dakika sürebilir.

## API (yerel sunucu)

- `GET /api/arsiv/download-catalog`
- `POST /api/arsiv/download-item` — `item_id`
- `POST /api/arsiv/download-next` — `limit` (1–5)

## Yasal not

Yalnızca kamuya açık / arşiv kaynakları kullanılır. Telifli veya lisanslı içerikleri izinsiz çoğaltmayın; inceleme sonrası çeviriye geçin.
