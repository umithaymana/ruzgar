# Rüzgar Çırak — Geniş Yol Haritası (Mimar dili)

**Tarih:** 2026-11-18 (revize — kritikler öne alındı)  
**Amaç:** Güvenilir usta yardımcısı.  
**Kural:** Yeşil = iş + kanıt. Bilgiye uzanamayan / Mimar’ı anlamayan çırak üst basamağa çıkmaz.

---

## Mimar’ın iki kritik uyarısı (plana gömüldü)

1. **Bilgi yoksa iş olmaz.** Kitaplık dolu ama görev borusu raftan kopuk → bunu **en öne** aldık.  
2. **Mimar’ı anlamadan proje çıkaramaz.** “Ben ne istiyorum, nasıl bir ürün?” çırağın bu aşamada bilmesi lazım; plan ve projeyi baştan sona okumayı usta yanında öğrenecek.

```
  ÖNCE (zorunlu köprü)          SONRA (merdiven)
  ┌─────────────────────┐       ┌──────────────────┐
  │ 0A Bilgiye uzan     │       │ 1 Atölye (bitti) │
  │ 0B Mimar’ı anla     │  →    │ 2 Güvenilir yardım│
  └─────────────────────┘       │ 3…5 üst katmanlar │
                                └──────────────────┘
```

---

## Bugün neredeyiz?

Atölye A–G + tavan T+1 **hazır** (yaz / kanıt / tavan bilinci).  
**Eksik (kritik):** görevde kütüphaneye uzanma; Mimar vizyon kartı çırağa yazılı değil.

```
[ KAPALI ]                 [ AÇIK ]
  boot / yüz / hub           cirak-atolyesi
  genel saha / %90           hibrit G + dar ajan
  görev→kitap köprüsü ❌     sohbet kütüphane ✅
  Mimar vizyon kartı ❌
```

---

## Sıra — EN ÖNDE (şimdi yapılacak)

### 0A — Bilgi köprüsü (KRİTİK · 1. iş)
**Neden:** Bilgiye uzanamayan çırak uydurur veya susar; iş olmaz.  
**Ne:** Çırak **görev** sırasında (yazmadan önce) ilgili bilgiye uzansın:
- bilgisayar eserleri / PY4E vb. dar `read` veya bilgisayar-RAG **snippet**
- grep hâlâ yazımı `projects/` ile sınırlı; **okuma** knowledge’a açılır (dar, izli)
- programlama “no-RAG” kör kapağı çırak/atölye için **istisna** (hafif, gecikmesiz)
**Yeşil:** Görev cevabında “okunan kaynak yolu” + sonra disk yazımı + smoke (G kuralı).  
**Yapmaz:** Ana koda yazmak; tüm RAG’i boğmak.

### 0B — Mimar’ı anla (KRİTİK · 2. iş, 0A ile paralel başlar)
**Neden:** Ne istediğini bilmeyen çırak yanlış proje üretir.  
**Ne (şimdi):**
- Tek kart: `projects/cirak-atolyesi/MIMAR_VIZYON.md`  
  - Ümit ne istiyor? (kısa)  
  - Nasıl bir ürün / Rüzgar ne olacak?  
  - Çırak sınırı (atölye, tavan)  
  - Başarı = kanıtlı yardım, abartı yok  
- Çırak her ciddi görev öncesi bu kartı **okumuş** sayılsın (supervised veya görev ön-okuma).  
**Yeşil:** Kart var + çırak “vizyon özeti”ni doğru tekrarlayabiliyor (kısa smoke/soru).  
**Sonra usta öğretir (yol boyunca):**
- İstekten **plan** nasıl çıkarılır  
- Projeyi **baştan sona** nasıl okunur (giriş → omurga → test → mühür)  
- “Mimar bunu mu istedi?” kontrol sorusu

---

## Büyük resim (0A/0B’den sonra)

```
  0A Bilgiye uzan ──┐
  0B Mimar’ı anla ──┼──► 1 Atölye ✅ ──► 2 Güvenilir yardımcı
                    │         │
                    │         ▼
                    │    3 Usta yardımcısı → 4 Saha ortağı → 5 (isteğe) geniş
                    │
                    └── Usta yanında: plan yapma + projeyi baştan sona okuma
```

### Katman 1 — Atölye çırağı ✅
Yaz, doğrula, tavan bil; abartma. (A–G, T+1 bitti.)

### Katman 2 — Güvenilir yardımcı
Küçük gerçek iş + **0A kaynaklı** + G kapısı.  
Mimar: “Verdim → kanıtlı bitti.”

### Katman 3–5
Aynı güvenlik ağı; alan genişler yalnız Mimar onayıyla.  
Her genişlemede: vizyon kartı güncel mi? bilgi köprüsü çalışıyor mu?

---

## Usta’nın öğreteceği (senin yanında yol)

| Ders | Ne zaman |
|------|----------|
| Bilgiye uzan → sonra yaz | 0A (hemen) |
| Mimar ne istiyor? kartı | 0B (hemen) |
| İstek → plan iskeleti | 0B sonrası, her görevde |
| Projeyi baştan sona oku | Katman 2–3’e geçerken |
| “Bu Mimar’ın istediği mi?” | Her yeşilden önce |

---

## Zaman çizgisi (revize)

| Dönem | Hedef |
|-------|--------|
| **Şimdi · 1** | 0A bilgi köprüsü yeşil |
| **Şimdi · 2** | 0B MIMAR_VIZYON + anlama smoke |
| **Yakın** | Katman 2 (kaynaklı + kanıtlı küçük iş) |
| **Orta** | Katman 3 + proje okuma alıştırması |
| **İleride** | 4–5 yalnız sen istersen |

---

## Bilinçli yapılmayacaklar

- Bilgi köprüsü olmadan “büyük iş / saha”  
- Vizyon kartı olmadan “ürün çıkardım” iddiası  
- Boot / yüz / hub / %90 serbest  
- Yeşilsiz atlama  

---

## Sonraki somut adım (onaylı sıra)

1. **0A** dilimini yaz + uygula (görev-içi dar kütüphane/read).  
2. **0B** `MIMAR_VIZYON.md` — Mimar’ın cümleleriyle doldur (usta taslak + sen düzelt).  
3. Sonra Katman 2’nin ilk gerçek fonksiyon+test işi.

---

## Tek bakışta

| Soru | Cevap |
|------|--------|
| En kritik ne? | Bilgiye uzan + Mimar’ı anla |
| Neredeyiz? | Atölye becerisi var; iki köprü eksik |
| Nereye? | Köprüler → güvenilir yardımcı → … |
| Usta ne öğretir? | Plan + projeyi baştan sona okuma (yanında) |
