# RÜZGAR — İlim kütüphanesi yükleme planı (onay öncesi)

**Tarih:** 2026-10-05  
**Mimar emri:** Öncelik **din**; sıra **Kur’an → tefsir → akaid → kelam → hadis → fıkıh → diğer İslami ilimler**.  
**Kural:** Bu belgedeki hiçbir madde **otomatik yükleme** sayılmaz; her faz için kaynak listesi + kapsam + onay maddesi tamamlanmadan ingest yapılmaz.

---

## 1. İlkeler (bağlayıcı)

| İlke | Uygulama |
|------|----------|
| **Doğruluk** | Ayet, hadis, meal metni yalnızca onaylı kaynaktan; model uydurması yasak (mevcut `prompts.py` politikası korunur). |
| **Kaynak izi** | Her parça: `kaynak_id`, `baslik`, `surum`, `dil`, `lisans`, `url/dosya`, `checksum`, `yukleme_tarihi`. |
| **Katman ayrımı** | Mushaf (Arapça) ≠ meal ≠ tefsir ≠ fıkıh hükmü ≠ akaid özet; RAG metadata ile karıştırılmaz. |
| **Temiz sayfa (din)** | Eski “din sandığı” hafıza/RAG parçaları karantinaya; kişisel/aile hafızası dokunulmaz. |
| **Canlı bilgi** | Güncel haber/fiyat/spor **hafızadan değil** web yolundan (mevcut düzeltmeler korunur). |
| **İki kütüphane** | `knowledge/kutuphane/` = genel fen/tarih özet v1; **`knowledge/ilim/din/`** = resmi ilim külliyatı (yeni). |

---

## 2. Mevcut durum denetimi (Faz 0 — rapor)

### 2.1 Kur’an arşivi

| Konum | Durum |
|-------|--------|
| `arsiv/kuran/index.jsonl` | Yalnızca **Fatiha 1–2** (transliterasyon örneği); tam mushaf **yok**. |
| `arsiv/Tasavvuf_Kulliyati/Kuran_i_Kerim/index.jsonl` | Aynı **2 satır**; okuma motoru hedefi var, içerik **iskelet**. |

### 2.2 Tefsir / hadis / külliyat klasörleri

| Konum | Durum |
|-------|--------|
| `Tefsir_Kulliyati` | Pratikte **boş** (yüklenecek eser bekliyor). |
| `Hadis_Kulliyati` | Klasör var; tam metin **doğrulanmadı** (manifest’te örnek PDF referansları olabilir). |
| `knowledge/tecvid/kurallar_ornek.md` | TTS/tecvid **simülasyon notları**; ilim külliyatı değil. |

### 2.3 RAG (`.rag_index`)

- Ağırlık: `knowledge/nebula/`, `TARIH_VE_KULTUR/`, TDK vb.
- **Yapılandırılmış Kur’an/hadis/tefsir** indekslenmiş değil.

### 2.4 `ruzgar_genel_hafiza.json` (~435 kayıt)

| Tür | Adet | Din ilmi için risk |
|-----|------|---------------------|
| **BilgiKutuphane** (otomatik web öğrenme) | **17** | **0** gerçek din içeriği; gündem/spor/tarih/hesap. Din sorusunda **yanlış öncelik** verebilir → Faz 0’da **din sorgularında devre dışı** veya tamamen arşiv. |
| **Oturum özeti** (hadis/kuran kelimesi geçen) | ~8 | **Gerçek hadis metni değil**; sohbet özeti. Din cevabında **override** riski → karantina listesi. |
| **«Hatırla» kişisel** | — | **Dokunulmaz** (aile, tercih, proje). |

**Sonuç:** Din için “dolu külliyat” yok; hafızada **yanıltıcı oturum özetleri** var. Temiz sayfa mantıklı.

---

## 3. Master kategori ağacı

### 3.A — `knowledge/ilim/din/` (öncelik 1)

```
01_kuran/
  mushaf_arapca/          # Uthmani, ayet bazlı
  meal/                   # Diyanet Kur'an Yolu (birincil TR)
  transliterasyon/        # isteğe bağlı, kaynak etiketli
  metadata/               # 114 sure, ayet sayıları, iniş, Mekki/Medeni, konu indeksi
  usul_kiraat/            # Faz 1 sonrası / ayrı onay
02_tefsir/
  klasik/                 # İbn Kesir, Taberi, … (eser eser onay)
  modern/                 # Diyanet tefsiri, Kur'an Yolu tefsiri, …
  konu_tefsiri/           # ayet-sure çapraz referans
03_akaid/
  itikadi_eserler/        # Tahâvî, Nesefî, …
  mezhep_itikadi/         # Eş'ari, Maturidi özet (kaynaklı)
04_kelam/
  mantik_kelam/           # giriş metinleri, terimler
  muhakeme/               # klasik/modern ders notu formatı (kaynaklı)
05_hadis/
  kutub_i_sitte/          # eser eser: Buhari, Müslim, …
  usul_hadis/             # hadis terminolojisi, sened (teori)
  konu_fihrist/           # konuya göre hadis (kaynak zinciri korunur)
06_fikih/
  ibadet/                 # namaz, oruç, hac, zekât
  muamelat/               # aile, ticaret (genel ilim; fetva motoru değil)
  usul_fikih/
  mezhep_mukayese/        # bilgi amaçlı, kaynaklı özet (ihtilaflı konularda tarafsız etiket)
07_diger_islami/
  siyer/                  # sîre, magazi
  tasavvuf/               # klasik metinler (ayrı onay)
  ahlak_tefekkur/
  kiraat_tecvid/          # ilmi tecvid (simülasyon dosyasından ayrı)
  islam_tarihi/           # din perspektifli tarih (genel tarih rafından ayrı metadata)
```

### 3.B — `knowledge/kutuphane/` (mevcut v1 — öncelik 2, din bitene kadar genişletme dondurulabilir)

| Raf ID | Ad |
|--------|-----|
| 01_astronomi_uzay | Astronomi ve uzay |
| 02_fizik_kimya | Fizik ve kimya |
| 03_biyoloji_dunya | Biyoloji |
| 04_cografya | Coğrafya |
| 05_tarih | Tarih (laik/ansiklopedik) |
| 06_matematik | Matematik |
| 07_dil_turkce | Dil |
| 08_teknoloji | Teknoloji |
| 09_kultur_yasam | Kültür |
| 10_hizli_referans | SSS |

### 3.C — Gelecek: `knowledge/ilim/` (din sonrası)

```
tip/          tibbi_kaynaklar (Türk/resmi kılavuz + atlas, aşamalı)
fen/          fizik, kimya, biyoloji (ders kitabı + ansiklopedi seviyesi, kaynaklı)
muhendislik/
sosyal_bilimler/
```

Her dal için aynı şema: **kaynak manifest → staging → QA → RAG incremental**.

---

## 4. Teknik boru hattı (tüm fazlar)

1. **Staging:** `ilim-assistant/arsiv/_ilim_staging/<faz>/` — ham indirme / Mimar PDF’si.
2. **Normalizasyon:** JSONL veya MD chunk; alanlar: `ilim_dali`, `eser`, `bolum`, `sure_no`, `ayet_no`, `hadis_no`, `metin`, `meal`, `not`.
3. **Manifest:** `knowledge/ilim/din/<dal>/manifest.json` — lisans, sürüm, parça sayısı.
4. **QA script:** ayet sayımı (6236), sure adları, rastgele 50 ayet hash karşılaştırması; hadis için kitap/hadis no tutarlılığı.
5. **RAG:** yalnızca onaylı manifest sonrası incremental index; `collection=din_01_kuran` gibi filtre.
6. **Sohbet:** din/ayet/hadis sorgularında `BilgiKutuphane` hafıza eşleşmesi **kapalı**; önce RAG ilim, sonra LLM (uydurma yok).

---

## 5. Faz 1 — Kur’an-ı Kerim (detaylı kapsam)

### 5.1 Hedef çıktılar

| # | Çıktı | Açıklama |
|---|--------|----------|
| K1 | **Mushaf Arapça** | 114 sure, 6236 ayet, Uthmani yazım; ayet sınırları kaynakla birebir. |
| K2 | **Meal (TR)** | **Diyanet — Kur’an Yolu** meal (birincil); her ayet `meal_diyanet` alanı. |
| K3 | **Metadata** | Sure adları (TR/AR), ayet sayısı, iniş sırası, Mekki/Medeni, cüz/hizb (Diyanet takvim verisi). |
| K4 | **Arama** | Sure adı, ayet no, meal içi anahtar kelime (RAG + yapısal lookup). |
| K5 | **Tecvid giriş** | Faz 1’de **yalnızca** Diyanet/Kur’an eğitimi kaynaklı **kısa usul** (ayrı dosya); tam ilmihal tecvid Faz 7’ye. |

### 5.2 Önerilen birincil kaynaklar (onayınıza sunulur)

| Kaynak | Ne alınır | Lisans / not |
|--------|-----------|----------------|
| **Tanzil.net** | Uthmani Arapça metin (XML/TXT) | Açık; atıf zorunlu; ticari olmayan kullanım. |
| **quran.com / Quran Foundation API** | Ayet metni, sure metadata (doğrulama çapraz) | API şartları; rate limit; yedek doğrulama. |
| **Diyanet (kurumsal)** | Kur’an Yolu **meal** + resmi sure bilgileri | **Telif:** resmi dağıtım veya Mimar’ın sağladığı onaylı dosya (PDF/Word/API). İndirme yolu onayda netleşir. |
| **Alternatif meal (Faz 1b, isteğe bağlı)** | Elmalılı, Öztürk vb. | **Yalnızca** Mimar’ın yüklediği lisanslı dosya; otomatik web kopyası **yapılmaz**. |

**Yapılmayacak:** Wikipedia/Türkçe wiki meal ile “tam mushaf”; tek başına LLM ile meal üretimi.

### 5.3 Veri şeması (örnek satır)

```json
{
  "collection": "din_01_kuran",
  "sure_no": 1,
  "sure_adi_ar": "الفاتحة",
  "sure_adi_tr": "Fatiha",
  "ayet_no": 1,
  "text_ar_uthmani": "...",
  "meal_tr_diyanet": "...",
  "kaynak_ar": "tanzil:v1.0.2",
  "kaynak_meal": "diyanet:kuran_yolu:YYYY",
  "checksum_ar": "sha256:..."
}
```

### 5.4 Faz 1 onay kontrol listesi

- [ ] Arapça metin kaynağı: Tanzil **evet/hayır**
- [ ] Meal: Diyanet Kur’an Yolu **evet/hayır** (dosya/API yolu)
- [ ] Ek meal dosyaları: **liste**
- [ ] Transliterasyon: **evet/hayır**
- [ ] Eski `index.jsonl` (2 ayet): **arşivle/sil** onayı
- [ ] Faz 0 hafıza temizliği: **evet/hayır**

### 5.5 Tahmini hacim

- JSONL + indeks: ~15–25 MB (metin); embedding ile RAG boyutu ayrı raporlanır.

---

## 6. Faz 2 — Tefsir

### 6.1 Sıra (öneri)

1. **Kur’an Yolu tefsiri** (Diyanet) — meal ile uyumlu.  
2. **İbn Kesir** (özet/ tam — eser onayı).  
3. **Taberi / Kurtubi / Razi** — eser eser, telif onayı ile.

### 6.2 Kaynak modeli

| Tür | Kaynak | Yükleme |
|-----|--------|---------|
| Resmi TR | Diyanet tefsir | Mimar onaylı PDF veya kurumsal metin |
| Arapça klasik | Shamela / lisanslı PDF | Staging + OCR kalite kontrol |
| Ayet bağlantısı | Her chunk: `sure_no`, `ayet_no`, `eser`, `cilt`, `sayfa` |

**Onay maddesi:** Hangi eserler, hangi dil, tam metin mi özet mi.

---

## 7. Faz 3 — Akaid

| Eser / konu | Not |
|-------------|-----|
| Akâid-i Tahâviyye (TR) | Temel metin |
| Eş'ari / Maturidi itikad özetleri | Ders kitabı seviyesi, kaynaklı |
| Güncel akaid soruları | **Fetva değil**; tanım ve mezhep literatürü referansı |

Kaynak: Maturidi/Eş'ari metinlerin **lisanslı çeviri** PDF’leri veya Mimar listesi.

---

## 8. Faz 4 — Kelam

- Mantık-kelam terminolojisi (kavram sözlüğü, kaynaklı).
- Seçilmiş klasik parçalar (Teftâzânî vb.) — **eser listesi onay**.

---

## 9. Faz 5 — Hadis

### 9.1 Önerilen yapılandırılmış kaynaklar

| Kaynak | Kapsam | Not |
|--------|--------|-----|
| **sunnah.com** (API) | Kutub-i Sitte parçalar | API kullanım şartları; Arapça+TR where available |
| **fawazahmed0/hadith-api** (GitHub) | JSON hadis koleksiyonları | Açık veri; doğrulama örneklemesi |
| **Diyanet hadis projeleri** | TR meal/şerh | Varsa resmi dosya — onay |

### 9.2 Yükleme sırası (öneri)

1. **Sahih-i Buhari** (tam, kitap/bab/no ile)  
2. **Sahih-i Müslim**  
3. **Sünen Ebû Dâvûd, Tirmizî, Nesâî, İbn Mace**  
4. **Muvatta, Musned** (onay ile)  
5. **Usûl-i hadis** (Hadis terminolojisi — ayrı klasör)

Her hadis kaydı: `eser`, `kitap`, `bab`, `hadis_no`, `metin_ar`, `meal_tr`, `sahih_zayif` (yalnızca kaynakta varsa; **model tahmini yok**).

---

## 10. Faz 6 — Fıkıh

| Blok | İçerik | Kaynak önerisi |
|------|--------|----------------|
| İbadet | Namaz, oruç, hac, zekât | Diyanet **İlmihal** (Mimar PDF) |
| Muamelat | Genel hükümler, tanımlar | Aynı; **kişisel fetva yok** |
| Usul | Fıkıh usulü giriş | Ders metni (onaylı) |
| Mezhep | Hanefi, Şafii, … **mukayeseli bilgi** | Kaynaklı tablo; ihtilaf etiketli |

---

## 11. Faz 7 — Diğer İslami ilimler

| Dal | Örnek içerik |
|-----|----------------|
| Siyer | İbn Hişam, Vakidi özet/tam (onay) |
| Tasavvuf | Klasik metinler (kulliyata ayrı manifest) |
| Ahlak | Güzel ahlak eserleri ( seçilmiş ) |
| Kıraat / tecvid | İlmihal düzeyinden **yukarı** (Faz 1 simülasyon dosyası devre dışı) |
| İslam tarihi | Hulefa, Emevi, Abbasi … (din metadata) |

---

## 12. Faz 0 — Temizlik (onay sonrası uygulama)

| Adım | İşlem |
|------|--------|
| H0.1 | 17 **BilgiKutuphane** kaydını dışa aktar → `arsiv/hafiza_karantina/`; din/ayet/hadis/fıkıh sorgularında eşleşmeyi kapat. |
| H0.2 | Hadis/kuran kelimeli **oturum özetlerini** karantinaya al (silmeden önce liste Mimar’a). |
| H0.3 | `arsiv/kuran/index.jsonl` → `_legacy_demo/` taşı; yeni K1 indeks bağla. |
| H0.4 | `knowledge/tecvid/kurallar_ornek.md` → `tecvid_simulasyon/` (RAG’ten `collection!=din` veya exclude). |
| H0.5 | `RUZGAR_ILIM_DIN_ONCE=1` (veya eşdeğer) — din sorgularında önce `knowledge/ilim/din` RAG. |

---

## 13. Onay özeti (Mimar tek mesajda)

Lütfen sırayla işaretleyin veya “evet hepsi” deyin:

1. **Faz 0** hafıza/karantina planı  
2. **Faz 1** kaynaklar: Tanzil Arapça + Diyanet Kur’an Yolu meal  
3. **Klasör:** `knowledge/ilim/din/01_kuran/`  
4. **Faz 2–7** sırası (bu belgedeki gibi)  
5. Ek meal / Elmalılı dosyası var mı? (yol belirtin)  
6. Hadis için öncelik: **Buhari → Müslim → …** onayı  

**Onay gelene kadar:** indirme, OCR, RAG rebuild, hafıza silme **yapılmaz** (yalnızca bu plan ve isteğe bağlı karantina listesi export).

---

## 14. Sonraki adım (onaydan hemen sonra)

1. Faz 0 export + config  
2. Faz 1 staging indirme + QA script  
3. `manifest.json` + ilk RAG incremental  
4. Smoke: “Bakara 255 Arapça+meal”, “Fatiha ayet sayısı”, “yanlış ayet uydurma testi”  
5. `PROJE_DURUMU.md` güncelleme + Mimar raporu  

---

*Belge: Rüzgar geliştirme ortağı — Ümit & Gökçenur onayına sunulmuştur.*
