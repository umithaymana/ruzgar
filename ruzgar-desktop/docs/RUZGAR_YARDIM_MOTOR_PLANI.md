# Rüzgar — Yardım penceresi (? ikonu) motor rehberi planı

**Ümit abi notu (2026-06-03):** Üst şeritteki **?** (`#btn-faz7-help` → `#faz7-help-overlay`) içine **her motor** için ayrı bölüm eklenecek: ne yapar, nasıl çalışır, yardımcı araçlar — **madde madde**.

**Durum:** İçerik yazımı **ertelendi** — önce motorların güçlendirilmesi ve düzgün çalışması (Ümit abi 2026-06-03). Her şey netleşince madde madde yazmak daha kolay.

**Öncelik sırası:**
1. Motorları sağlamlaştır (Tercüme, Mimar, Programlama, … — çalışır, test, net akış)
2. Sonra bu dosyadaki şablona göre `?` yardım penceresini doldur

**Uygulama yeri:** `ruzgar-desktop/index.html` → `#faz7-help-overlay` → `.faz7-help-body`  
**İsteğe bağlı ileri adım:** Aktif motora göre ilgili `<h3>` bölümüne kaydırma veya vurgulama (`app.js` + `data-motor`).

---

## Motor listesi (sidebar — yazılacak bölümler)

| Motor | `data-mode` | Yardım `<h3>` başlığı önerisi | Öncelik |
|--------|-------------|-------------------------------|---------|
| Ana Motor | `genel` | Ana Motor (genel sohbet) | Kısmen var — genişlet |
| Tercüme Atölyesi | `tercume` | Tercüme motoru | **Yüksek** (Çalışma, İnceleme, dil akışı, segment, PDF) |
| Mimar Motoru | `mimar` | Mimar motoru (Fotoğraf · Resim·Sanat · Tasarım) | Orta |
| Video Motoru | `video` | Video motoru | Orta |
| Programlama Motoru | `programlama` | Programlama motoru | Orta |
| Hafıza Motoru | `hafiza` | Hafıza motoru | Orta |
| HIZIR | `hizir` | HIZIR (pazar / merkezi bellek) | Kısmen var |
| Ses Motoru | `ses` | Ses motoru | Düşük |

---

## Her motor bölümünde olacak maddeler (şablon)

Her motor için aynı iskelet:

1. **Ne işe yarar** (1–2 cümle)
2. **Nasıl çalışır** (akış: aç → seç → çevir / sor / kaydet)
3. **Üst şerit / kısayollar** (o motora özel)
4. **Yardımcı araçlar** (butonlar, paneller, arka plan işleri)
5. **Çıktı / kayıt** (nereye kaydeder, formatlar)
6. **Sık sorun** (1–3 madde, isteğe bağlı)

---

## Tercüme motoru — taslak maddeler (ilk genişletme adayı)

- Çalışma sekmesi: kaynak/hedef, segment düzenleme, PDF önizleme (`pymupdf`)
- İnceleme modu: hizalı diff, akademik kontrol, inceleme kuyruğu
- Dil akışı (üst şerit): kaynak/hedef dil, mod (tek parça / sayfa / aralık)
- Sayfa ve çıktı: sayfa aralığı, `.txt` / `.md` / `.html` / `.docx`
- Terimlerim (TM), TMX, kalite skoru, arka plan çeviri işi
- Yerel araçlar: OCR, Calibre, DjVu — yalnızca eksikte uyarı (UI sadeleştirme notu)
- Kısayollar: `Ctrl+Enter`, `Alt+↑/↓`, `Ctrl+S` (Çalışma katlanır yardımda da geçmeli)

---

## Genel bölümler (tüm motorlarda ortak — üstte kalsın)

- Klavye: Enter, Shift+Enter, ?, Ctrl+/, Escape, Durdur
- Sunucu: `Ruzgar.ps1` / port 8779
- Görünüm: azaltılmış animasyon, düşünme gecikmesi

---

## Yapılacaklar (checklist)

- [ ] `index.html` — her motor için `<h3>` + `<ul class="faz7-help-ul">`
- [ ] Gereksiz “Faz 9–16” teknik listesini kullanıcı diline çevir veya “Geliştirici” altına al
- [ ] (İsteğe bağlı) `faz7-help-motor-{mode}` id’leri + `app.js` ile aktif motor bölümünü aç
- [ ] `tercume-atolye` iç `details.tercume-help-fold` ile üst ? yardımını çift yazma — tek kaynak tercih: **? penceresi**

---

## Referans dosyalar

- `ruzgar-desktop/index.html` — `#faz7-help-overlay`
- `ruzgar-desktop/app.js` — `btn-faz7-help`, yardım aç/kapa
- `ilim-assistant/docs/MIMAR_TERCUME_ATOLYE_PLANI.md` — Tercüme / Mimar ayrımı
- `ilim-assistant/docs/TERCUME_MOTORU_DEVAM_PLANI.md` — Tercüme yetenekleri

**Hatırlatma:** Bu dosyayı güncel tutun; yardım metni yazılırken buradan işaretleyin.
