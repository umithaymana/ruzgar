# Çırak teknik tecrübe hafızası — PLAN

**Ümit & Gökçenur** · Usta · 2026-11-18 · Mimar `yap` → **F1–F3 uygulandı**  
**Kod:** `ilim_assistant/ruzgar_cirak_tecrube.py` · disk: `.ruzgar/cirak_tecrube.jsonl`  
**Amaç:** Az yer, yüksek öğreti, **yalnız doğrulanmış** teknik kalıp.  
**Değil:** İş hikâyesi arşivi · kişisel sohbet belleği · yanlış/şüpheli not.

---

## 0) İlke (kilit)

1. Deftere giren her satır **eğitici kural**dır, “şu işi bitirdim” günlüğü değildir.
2. Yanlış bilgi **zehir**dir → şüpheli / kırmızı / usta kurtarmadan gelen “çırak uydurması” **asla** “nasıl yapılır” diye yazılmaz.
3. Kişisel bellek (kimim, aile, zevk) **bu defterde yok** — ayrı kalem, ayrı oda.
4. Yer sınırı sert: şişen defter = zayıf çırak.

---

## 1) Ne yazılır (içerik türleri)

Yalnız şu sınıflar — her biri **1–3 kısa satır + isteğe 4–8 satır iskelet**:

| Kod | Tür | Örnek (özet) |
|-----|-----|----------------|
| `SPEC` | Görev satırı disiplini | Hedefte açık `dosya.py` + `tests/test_*.py` + `def` adı yaz |
| `LAYOUT` | Dosya düzeni | Üretim kodu scope kökünde; testler `tests/`; paket ise `paket/__init__.py` export |
| `API` | Sözleşme | Kapıdaki `def` adını uydurma; generator istenmişse `yield`, liste değil |
| `WRITE` | Yazım sırası | Çırak turunda salt grep/read yasak; önce `@@write`, sonra verify |
| `TEST` | Test biçimi | Hedef test dosyasına pytest; yanlış yoldaki yeşil = yeşil sayılmaz |
| `MULTI` | Çok-modül | `util` + iş modülü ayır; import yolu net |
| `GATE` | Kapı dersi | `cirak_missing_files` / `cirak_missing_api` / `cirak_no_write` ne demek, ne yap |
| `ANTI` | Yasak kalıp | (Yalnız doğrulanmış) “filtrele_satır uydurma”, “testi scope köküne atma” |

**Yazılmaz:** uzun kod dump, tüm proje ağacı, sohbet metni, “belki böyle”, geçici debug, kişisel not, başka kullanıcının işi.

---

## 2) Ne zaman yazılır (giriş kapısı — zehir önleme)

Bir not **ancak** şu koşulla deftere girer:

| Kaynak | Koşul | Not türü |
|--------|--------|----------|
| A | Çırak tek başına yeşil (`verify_ok` + diskte zorunlu dosyalar + hedefli pytest) | `SPEC/LAYOUT/API/WRITE/TEST/MULTI` — **pozitif kalıp** |
| B | Usta kurtarma sonrası yeşil | Yalnız `ANTI` + `GATE` (çırak nerede battı); “kurtarma kodu = örnek reçete” **ayrı etiketle**, çırak uydurması gibi sunulmaz |
| C | Kapı ihlali tekrarı (≥2), sonra yeşil | `GATE` / `ANTI` — kök neden etiketi kanıtlıysa |

**Red (yazma):**  
- Kırmızı bitti → pozitif kalıp yok  
- LLM’in yazdığı ama testte patlayan kod → pozitif yok  
- Aynı kural zaten defterde (benzerlik) → yeni satır yok, sayaç +1  

---

## 3) Kayıt şeması (ince)

Dosya önerisi: `.ruzgar/cirak_tecrube.jsonl` (satır = 1 ders)

```json
{
  "id": "ct-20261118-a1b2",
  "v": 1,
  "kind": "TEST",
  "rule": "Hedef test yolu tests/test_X.py; kökte test_X.py yeşil sayılmaz.",
  "skeleton": "tests/test_foo.py → from foo import f; assert ...",
  "anti": null,
  "tags": ["pytest", "path"],
  "evidence": "green_cirak",
  "scope_sample": "projects/is-b0N",
  "created": "2026-11-18T21:00:00+03:00",
  "hits": 1
}
```

Alan limitleri:
- `rule` ≤ 160 karakter  
- `skeleton` ≤ 400 karakter (veya yok)  
- `anti` ≤ 120 karakter  
- Toplam aktif ders üst sınırı: **80** (aşınca en az `hits` + en eski birleşir/silinir)

İnsan okuması (isteğe bağlı, üretilir): `projects/cirak-atolyesi/CIRAK_TECRUBE_OZET.md` — en çok kullanılan 20 kural, tek sayfa.

---

## 4) Ne zaman okunur (enjeksiyon)

Çırak görev turu başında (`looks_like_cirak_gorev` / `is_cirak_yazim_gorev`):

1. Görev metninden etiket çıkar (`MULTI`, `TEST`, `paket`, `generator` …).  
2. Defterden en fazla **3–5** ders seç (etiket örtüşmesi + yüksek `hits`).  
3. Prompt’a blok:

```
[ÇIRAK TECRÜBE — yalnız uygula, uydurma]
- ...
```

**Yasak:** Tüm defteri basmak · başarısız denemelerin ham dökümü · kişisel bellek karışımı.

Mevcut `task_outcomes.json` / `root_cause_rule_hints` **KPI ve hata etiketi** olarak kalır; bu defter **öğreti** katmanıdır — karıştırılmaz, gerekirse `GATE` ile köprülenir.

---

## 5) İlk tohum (B dalgasından — doğrulanmış)

Kod yazılınca otomatik çıkarım + usta onayı ile şunlar aday (özet):

1. **SPEC:** Görevde açık `.py` yolları yoksa dosya kapısı kör kalır → her görevde path yaz.  
2. **WRITE:** Sessiz/async fırlatma yetmez; ajan idle ise yazım başlamamış say.  
3. **LAYOUT:** Test `tests/` altında; paket işinde `__init__` export.  
4. **API:** İstenen `def` adını değiştirme (`filtre_satirlar` ≠ uydurma ad).  
5. **MULTI:** `util` + iş modülü; normalize tek yerde.  
6. **TEST:** Yeşil = zorunlu dosyalar diskte + **hedefli** pytest.  
7. **ANTI:** Salt keşif turu ile “bitti” sayma.

(Bunlar plana tohum; koda dökülmeden önce Mimar `evet`.)

---

## 6) Uygulama fazları (kod — ayrı emir)

| Faz | Ne | Kapı |
|-----|-----|------|
| F0 | Bu plan (dosya) | ✓ |
| F1 | `cirak_tecrube.jsonl` yaz/oku + limit + dedup | ✓ |
| F2 | Yeşil çırak bitişinde otomatik aday ders (dar şablon) | ✓ (`faz14` outcome) |
| F3 | Tur başı 3–5 ders enjeksiyonu | ✓ (`faz14` turn) |
| F4 | Özet md + zehir taraması | ✓ kısmi (`CIRAK_TECRUBE_OZET.md` + poison/red red) |

**Yapılmaz bu planda:** genel saha açmak · sohbet/kişisel bellek · boot/hub.

---

## 7) Doğruluk / zehir testleri (kabul)

- Kırmızı görevden sonra defterde yeni `evidence=green_cirak` satırı **olmamalı**.  
- Aynı `rule` metni iki kez şişirmemeli (`hits++`).  
- Enjeksiyon ≤ 5 satır kural.  
- Kişisel anahtar kelimeler (aile, severim, …) yazımda **red**.  

---

## 8) Mimar’a soru

Bu doğrultu uygunsa:  
- yalnız `plana yaz` / `kaydet` → plan kilitli kalsın  
- `yap` / `F1 yap` → kod fazına geçilsin  

**Önerilen aksiyon:** F1’e yeşil ışık.  
**Olası riskler:** Otomatik kural çıkarımı gevşek olursa zehir riski → F2’de dar şablon + kanıt zorunlu.
