# Rüzgar masaüstü — onaylı çalışan durum (KESİN EMİR)

**Tarih:** 2026-05-29 (rev 2 — Blok J tercüme atölye)  
**Onay commit:** `e2cccb8` — `fix(ruzgar): onayli masaustu taban cizgisi — aa39618 UI + Faz 98 API`  
**Build rev (API):** `2026-05-27-ruzgar-faz98-v107`  
**Doğrulama:** Ümit — motorlar, Gönder, Sunucu ✓, manifest, Faz 98 şeridi çalışır.

## İş planı (A→J)

Uygulama sırası ve commit kuralları: [`PROGRAMLAMA_BLOK_AJ_IS_PLANI.md`](PROGRAMLAMA_BLOK_AJ_IS_PLANI.md)  
Hızlı geri alma: [`../../docs/RUZGAR_HIZLI_GERI_ALMA.md`](../../docs/RUZGAR_HIZLI_GERI_ALMA.md)  
E1 izleme (curl): [`RUZGAR_PROGRAMLAMA_E1_IZLEME.md`](RUZGAR_PROGRAMLAMA_E1_IZLEME.md)

## Kesin emir

1. **`ruzgar-desktop/`** bu commit’teki hâli **onaylı taban çizgisidir**. Motor/sohbet/bağlantı bu kabuk üzerinde doğrulandı.
2. **`078d2ef` tercüme masaüstü genişlemesi** (app.js/index.html/styles.css +400 satır) **geri getirilmez** — API’de tercüme backend kalabilir; UI ayrı, küçük adımlarla ve test sonrası eklenir.
3. **Commit dışı patch yasağı:** `ruzgar-bootstrap.js`, çift script, `bootRuzgarShell`, toplu `app.js` denemeleri **yasak** — önce F12 ilk hata, sonra tek satırlık düzeltme.
4. **Geri alma kuralı:** Masaüstü bozulursa `git checkout e2cccb8 -- ruzgar-desktop/`; yeni sarmalayıcı yazılmaz.
5. **Başlatma (tek giriş):** kök `Ruzgar_TemizBaslat.bat` → API 8779 + Electron; Ctrl+Shift+R ile sert yenile.  
   - Port takılıysa: `Ruzgar_Port_Temizle.bat` → ardından yine `Ruzgar_TemizBaslat.bat`  
   - Sadece API: `Ruzgar_Sadece_Api.bat` · tam yeniden (yönetici): `Ruzgar_Tam_Yeniden.bat`  
   - **Varsayılan masaüstü kısayolu bu bat’a bağlı olmalı** (`scripts/Masaustune_Kisayol.ps1`)
6. **Etiket notu:** İsteğe bağlı tag `ruzgar-desktop-baseline-e2cccb8` — bkz. geri alma doc.

## Mimari not (neden aa39618 UI + Faz 98 API)

- Backend HEAD (Faz 98 onay, manifest, tercüme API) **çalışır**.
- Masaüstü kabuğu **aa39618 (Faz 97 programlama UI)** seviyesinde **stabil**.
- `078d2ef` sonrası masaüstü diff bağlantı/init’i kırdı; geri alma ile düzeldi.

## Test checklist (her masaüstü değişikliğinden sonra)

- [ ] Üst: **Sunucu ✓**
- [ ] **Bağlantı Aktif** bandı
- [ ] Ana Motor şeridi: **Faz 100 hub** (manifest)
- [ ] Sol menü: Hafıza / Tercüme / Programlama geçişi
- [ ] Sohbet: `selam` + **Gönder** → balon
- [ ] Tercüme: arşiv dosyası → **Çevir** → hedef panel dolu → **Hedefi kaydet**
- [ ] Opsiyonel otomasyon: `scripts/ruzgar_masaustu_checklist.ps1`

## Blok J (tercüme — onaylı kapsam)

- `ruzgar-desktop`: OCR, e-kitap açılış, URL indir, hedef kaydet, çeviri → otomatik hedef
- API: `POST /api/tercume/save-target` · bkz. [`TERCUME_ATOLYE_BLOK_J.md`](TERCUME_ATOLYE_BLOK_J.md)
- Programlama motor dosyaları bu blokta **değiştirilmedi**
