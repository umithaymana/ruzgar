# Çırak Hafıza — Defter (bağlayıcı)

**Amaç (Mimar Ümit):** Çırak yaptığı işi unutmasın. Doğru/yanlış, nerede uygulandı, sonraki işte örnek alınacak ince detay burada dursun.  
**Yer:** `docs/cirak_hafiza/` — **ana kodda (main); bundan sonra her çırak sürekli kullanır.**  
**Bu defter ≠** uygulama sohbet hafızası, ≠ UI «Çırak günlüğü» (tercüme paneli).

---

## A) İşe başlamadan — ZORUNLU

Kod / commit / büyük değişiklik **yok** — önce:

1. Bu dosyayı oku.  
2. `INDEX.md` içinde işine benzer **anahtar** ara.  
3. Benzer kayıt varsa oku: **tuzaklar, çözüm, bir daha yapma, hazır komutlar, dokunma listesi**.  
4. Yoksa `kayitlar.jsonl` son 3–5 satıra bak.  
5. Elini rahatlatacak malzemeyi çıkar; kör tekrar etme.

---

## B) İş bitince — ne kaydedilecek (zorunlu maddeler)

Her biten iş için:

- `kayitlar/YYYY-MM-DD_<kisa-slug>.md` (şablon: `SABLON.md`)  
- `kayitlar.jsonl` içine **bir satır**  
- `INDEX.md` içine **bir satır**

### Zorunlu alanlar

| # | Alan | Ne yazılır |
|---|------|------------|
| 1 | **tarih** | Gün + saat (Europe/Istanbul) |
| 2 | **emir** | Mimar ne istedi — 1 cümle |
| 3 | **sonuc** | Ne yapıldı — 1–2 cümle |
| 4 | **dogru** | Bu işte doğru olan / korunacak davranış |
| 5 | **yanlis** | Bu işte yanlış olan / sapma |
| 6 | **nerede** | Dal + kısa commit; kritik dosya yolları (en fazla 10) |
| 7 | **nasil_uygula** | Benzer işte sırayla ne yapılacak (3–7 adım) |
| 8 | **tuzaklar** | Nerede kırıldı, ne yanlış varsayıldı |
| 9 | **cozum** | Ne işe yaradı |
| 10 | **bir_daha_yapma** | Tekrarlama yasağı — net cümle |
| 11 | **anahtarlar** | Arama kelimeleri (ör. `selam`, `sentez`, `main-al`) |
| 12 | **durum** | `hazir` / `mimar-onay-bekliyor` / `yarim` / `ana-koda-alindi` |

### El rahatlatma (zorunlu — kısa)

| # | Alan | Ne yazılır |
|---|------|------------|
| 13 | **giris_kapisi** | Önce hangi dosya / hangi komut |
| 14 | **hazir_komutlar** | 2–5 işe yarar komut |
| 15 | **dokunma** | El sürülmeyecek yerler |
| 16 | **beklenen_cikti** | Bitince ne görünmeli (test, davranış) |
| 17 | **bilinen_kirik** | Zaten bozuk CI/test — yeni hata sanma |
| 18 | **ilk_guvenli_adim** | Riski düşük, hemen doğrulanan tek adım |
| 19 | **kapsam_siniri** | Bu kadar yeter — dışına çıkma |
| 20 | **geri_alma** | Bozulursa nasıl dönülür |

### Yazılmayacaklar

- API anahtarı, şifre, gizli .env  
- Uzun kod yapıştırma (yol + özet yeter)  
- «Yaptım» boş laf — **dal + commit** şart  

---

## C) Mimar kuralları (deftere işlenmiş hatırlatma)

- Ümit **«yap / uygula / al / düzelt»** demeden büyük işe başlama.  
- «İncele / rapor / bilgi» ≠ uygulama emri.  
- **«al»** yoksa `main`’e basma.  
- «Yaptım» demek yetmez: bu deftere kayıt + commit kanıtı.

---

## D) Dosyalar

```text
docs/cirak_hafiza/CIRAK_HAFIZA_OKU.md   ← bu protokol
docs/cirak_hafiza/SABLON.md             ← kopyala-doldur
docs/cirak_hafiza/INDEX.md              ← anahtar → kayıt
docs/cirak_hafiza/kayitlar/*.md         ← detay
docs/cirak_hafiza/kayitlar.jsonl        ← tek satır log
```
