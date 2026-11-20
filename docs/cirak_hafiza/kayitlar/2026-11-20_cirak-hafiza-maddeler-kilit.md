# 2026-11-20 — cirak-hafiza-maddeler-kilit

## 1) Emir
Çırak defterine ne kaydedileceğini netleştir; el rahatlatacak maddelerle kilitle; uygula.

## 2) Sonuç
`CIRAK_HAFIZA_OKU.md` 20 zorunlu alan + `SABLON.md` + `.cursor/rules/cirak-hafiza-FROZEN.mdc` yazıldı.

## 3) Doğru
- Defter = ajan eğitim defteri (işe başlamadan bak, bitince yaz).
- Doğru/yanlış/nerede/nasıl uygula ayrı alanlar.
- El rahatlatma: giriş kapısı, komutlar, dokunma, beklenen çıktı, geri alma.

## 4) Yanlış
- Hedefi «mimari plan motoru» gibi yan konulara sapmak.
- «Yaptım» deyip deftere yazmamak.
- UI tercüme çırak günlüğü ile karıştırmak.

## 5) Nerede
- Dal: `cursor/cirak-hafiza-9eeb`
- Dosyalar:
  - `docs/cirak_hafiza/CIRAK_HAFIZA_OKU.md`
  - `docs/cirak_hafiza/SABLON.md`
  - `docs/cirak_hafiza/INDEX.md`
  - `.cursor/rules/cirak-hafiza-FROZEN.mdc`

## 6) Nasıl uygula (benzer işte)
1. `CIRAK_HAFIZA_OKU.md` + `INDEX.md` oku.
2. Benzer kayıtta tuzak/çözüm/yasak al.
3. İş bitince `SABLON.md` kopyala, doldur.
4. jsonl + INDEX satırı ekle.

## 7) Tuzaklar
- Kullanıcı bilgi isterken uygulamaya sapmak.
- Eski «yapıldı» iddiası kanıtsız kalmıştı.

## 8) Çözüm
Mimar «SEN YAP» deyince maddeleri protokole ve şablona işledik; cursor kuralı alwaysApply.

## 9) Bir daha yapma
- Onaysız main’e basma; bilgi isteğini uygulama sayma.
- Defter alanlarını yarım bırakıp “kuruldu” deme.

## 10) Anahtarlar
`cirak-hafiza`, `sablon`, `zorunlu-alanlar`, `el-rahatlatma`

## 11) Durum
`ana-koda-alindi` (Ümit «ANA KODA AL» — `origin/main` @ `2d00ce120`)

---

## El rahatlatma

### Giriş kapısı
`docs/cirak_hafiza/CIRAK_HAFIZA_OKU.md`

### Hazır komutlar
```bash
ls docs/cirak_hafiza/
sed -n '1,80p' docs/cirak_hafiza/INDEX.md
```

### Dokunma
- `ruzgar_genel_hafiza.json` / tercüme apprentice-log’u bu defter sanma
- Kullanıcı «al» demeden `main`

### Beklenen çıktı
Yeni işte çırak önce INDEX’e bakar; bitince SABLON alanları dolu kayıt bırakır.

### Bilinen kırık
Programlama smoke CI main’de zaman zaman kırmızı olabilir (soft-pass notu ayrı kayıtta).

### İlk güvenli adım
SABLON’u kopyalayıp bir deneme kaydı doldurmak.

### Kapsam sınırı
Sadece defter protokolü/şablon/kural — yeni motor yok.

### Geri alma
Bu commit’i revert; `docs/cirak_hafiza/` önceki hâline dön.
