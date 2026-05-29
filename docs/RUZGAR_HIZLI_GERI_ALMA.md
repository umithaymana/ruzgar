# Rüzgar — hızlı geri alma (onaylı masaüstü tabanı)

**Onaylı commit:** `e2cccb8`  
**Etiket (isteğe bağlı):** `ruzgar-desktop-baseline-e2cccb8`  
**Detay:** `ilim-assistant/docs/RUZGAR_MASAUSTU_ONAYLI_DURUM.md`

## Ne zaman?

- Motor butonları / sohbet / bağlantı bandı bozulduysa
- `ruzgar-desktop/` üzerinde toplu deneme veya `078d2ef` türü geniş UI diff geri geldiğinde
- Electron CSP / çift script hatası şüphesi

## Sadece masaüstü kabuğunu geri al

```powershell
cd "d:\CURSOR PROJELER\YAPAY ZEKA"
git checkout e2cccb8 -- ruzgar-desktop/
```

Sonra:

1. Rüzgar penceresini kapat
2. `Ruzgar_TemizBaslat.bat`
3. Electron içinde **Ctrl+Shift+R**

## API / backend şüphesi (port takılı)

```powershell
cd "d:\CURSOR PROJELER\YAPAY ZEKA"
.\Ruzgar_Port_Temizle.bat
.\Ruzgar_TemizBaslat.bat
```

Gerekirse yönetici: `Ruzgar_Tam_Yeniden.bat`

## Tam proje snapshot’a dönmek (dikkat)

Tüm çalışma alanını `e2cccb8` seviyesine almak **tüm sonraki backend/UI commit’lerini geri alır**. Yalnızca acil durumda:

```powershell
git stash push -m "acil-geri-alma-oncesi"
git checkout e2cccb8
```

Geri dönmek için: `git checkout main` (veya çalıştığınız branch) + `git stash pop`

## Etiket oluşturma (bir kez, opsiyonel)

```powershell
git tag -a ruzgar-desktop-baseline-e2cccb8 e2cccb8 -m "Onayli masaustu taban cizgisi"
git push origin ruzgar-desktop-baseline-e2cccb8
```

## Test checklist (geri alma sonrası)

- [ ] Sunucu ✓ · Bağlantı Aktif
- [ ] Sol menü: Ana Motor / Tercüme / Programlama geçişi
- [ ] `selam` + Gönder → sohbet balonu
- [ ] Programlama şeridi Faz 98 (manifest)
