# 2026-11-20 — cirak-hafiza-ana-koda

## 1) Emir
Ümit: «ANA KODA AL» — çırak hafıza defteri main’de olsun; çıraklar sürekli kullansın.

## 2) Sonuç
`docs/cirak_hafiza/**` + `.cursor/rules/cirak-hafiza-FROZEN.mdc` `origin/main`’e girdi (`2d00ce120`). Required check `smoke-offline-slo` yeşilken FF push.

## 3) Doğru
- Required check yeşilken FF push (soft-pass zaten main’de).
- Defter ana kodda; sürekli kullanım kuralı alwaysApply frozen.

## 4) Yanlış
- «Al» yokken main zorlamak.
- Eski `cursor/sohbet-akicilik-a-f` geçmişini bu işe karıştırmak.

## 5) Nerede
- Dal (landed): `cursor/cirak-hafiza-main-al-9eeb` → `main`
- Commit: `2d00ce120`
- Dosyalar:
  - `docs/cirak_hafiza/`
  - `.cursor/rules/cirak-hafiza-FROZEN.mdc`

## 6) Nasıl uygula (benzer işte)
1. Feature dalı main tip’e rebase/merge.
2. `smoke-offline-slo` durumunu oku; yeşilse FF push.
3. Dosyaların `origin/main`’de olduğunu doğrula.
4. Defter `durum` → `ana-koda-alindi`.

## 7) Tuzaklar
- Protected branch: required `smoke-offline-slo` kırmızıysa push reddedilir.
- `gh pr create` / statuses API bu tokende 403 olabilir — doğrudan push yolu çalışabilir.

## 8) Çözüm
Dal üzerinde check yeşil → `git merge --ff-only` main → `git push origin main`.

## 9) Bir daha yapma
- Bu oturum dışı eski dalları (sohbet-akicilik vb.) Ümit sormadan merge etme.

## 10) Anahtarlar
`cirak-hafiza`, `main`, `ana-koda-al`, `surekli-kullanim`

## 11) Durum
`ana-koda-alindi`

---

## El rahatlatma

### Giriş kapısı
`docs/cirak_hafiza/CIRAK_HAFIZA_OKU.md` + `.cursor/rules/cirak-hafiza-FROZEN.mdc`

### Hazır komutlar
```bash
git fetch origin main
git ls-tree -r origin/main --name-only | rg cirak
```

### Dokunma
- `cursor/sohbet-akicilik-a-f` (eski, bu oturum değil)

### Beklenen çıktı
Main’de defter + frozen kural; çırak her işte okur/yazar.

### Bilinen kırık
Ana-ROK smoke bu dalda kırmızı olabilir; required check değil.

### İlk güvenli adım
INDEX + CIRAK_HAFIZA_OKU oku.

### Kapsam sınırı
Yalnız defter land + durum kaydı.

### Geri alma
`git revert` main’deki cirak-hafiza commit’leri (Ümit onayıyla).
