# Rüzgar masaüstü — onaylı çalışan durum (KESİN EMİR)

**Tarih:** 2026-05-28  
**Onay commit:** `e2cccb8` — `fix(ruzgar): onayli masaustu taban cizgisi — aa39618 UI + Faz 98 API`  
**Build rev (API):** `2026-05-27-ruzgar-faz98-v107`  
**Doğrulama:** Ümit — motorlar, Gönder, Sunucu ✓, manifest, Faz 98 şeridi çalışır.

## Kesin emir

1. **`ruzgar-desktop/`** bu commit’teki hâli **onaylı taban çizgisidir**. Motor/sohbet/bağlantı bu kabuk üzerinde doğrulandı.
2. **`078d2ef` tercüme masaüstü genişlemesi** (app.js/index.html/styles.css +400 satır) **geri getirilmez** — API’de tercüme backend kalabilir; UI ayrı, küçük adımlarla ve test sonrası eklenir.
3. **Commit dışı patch yasağı:** `ruzgar-bootstrap.js`, çift script, `bootRuzgarShell`, toplu `app.js` denemeleri **yasak** — önce F12 ilk hata, sonra tek satırlık düzeltme.
4. **Geri alma kuralı:** Masaüstü bozulursa `git checkout e2cccb8 -- ruzgar-desktop/`; yeni sarmalayıcı yazılmaz.
5. **Başlatma:** `Ruzgar_TemizBaslat.bat` → API 8779 + Electron; Ctrl+Shift+R ile sert yenile.

## Mimari not (neden aa39618 UI + Faz 98 API)

- Backend HEAD (Faz 98 onay, manifest, tercüme API) **çalışır**.
- Masaüstü kabuğu **aa39618 (Faz 97 programlama UI)** seviyesinde **stabil**.
- `078d2ef` sonrası masaüstü diff bağlantı/init’i kırdı; geri alma ile düzeldi.

## Test checklist (her masaüstü değişikliğinden sonra)

- [ ] Üst: **Sunucu ✓**
- [ ] **Bağlantı Aktif** bandı
- [ ] Ana Motor şeridi: **Faz 98 · hazır** (manifest)
- [ ] Sol menü: Hafıza / Tercüme / Programlama geçişi
- [ ] Sohbet: `selam` + **Gönder** → balon
