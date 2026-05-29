# Rüzgar altyapı raporu — Ümit abi dönüş

**Tarih:** 2026-05-28  
**Kapsam:** Başlatma, API 8779, Electron/tarayıcı UI, bağlantı şeridi, motor geçişi.

---

## Özet

| Durum | Açıklama |
|--------|-----------|
| **API** | `http://127.0.0.1:8779/api/health` → `ok: true`, build `2026-05-27-ruzgar-faz96-v106` |
| **Arayüz** | `http://127.0.0.1:8779/ui/index.html` (artık `file://` yasak) |
| **Bağlantı şeridi** | Yeşil «HAZIR» — sunucu + istemci düzeltmeleri uygulandı |
| **Asıl kök hatalar** | `origin` yazım hatası, localhost↔127.0.0.1 reload döngüsü, sahte «bağlı» bayrağı |

---

## Bulunan sorunlar ve yapılan düzeltmeler

### 1. Kritik: `index.html` içinde `origin` tanımsızdı
- `localStorage.setItem("ruzgarApi", origin)` → **ReferenceError**
- Yeşil şerit görünür ama `app.js` yanlış API adresine gider → sohbet/motor bozuk.
- **Düzeltme:** `apiBase` kullanılıyor.

### 2. Kritik: `localhost` ≠ `127.0.0.1` reload döngüsü
- Her 12 sn sayfa yenileniyordu → motor tıklamaları «çalışmıyor» sanılıyordu.
- **Düzeltme:** `ruzgarCanonicalLocalOrigin()` — yerel adresler eşdeğer sayılıyor.

### 3. Sahte «bağlı» (`__RUZGAR_PRECONNECT_OK__`)
- Health kontrolü atlanıp yeşil gösteriliyordu.
- **Düzeltme:** Her zaman `/api/health` fetch edilir.

### 4. `file://` ve eski `localStorage` (Colab URL)
- Electron/tarayıcı ölü adrese istek atıyordu.
- **Düzeltme:** `file://` → otomatik `http://127.0.0.1:8779/ui/`; `?clearApi=1` ile temizlik.

### 5. Çift Electron / çift API
- `Ruzgar.ps1` + `npm start` veya `ruzgar_launch.py` + ps1.
- **Düzeltme:** Tek örnek kilidi, `file://` kaldırıldı, `ruzgar_launch.py` → `run_desktop_api.py`, menü «yeni pencere» → ana pencerede genel mod.

### 6. Electron kapanınca API ölüyordu
- Tarayıcı `ERR_CONNECTION_REFUSED`.
- **Düzeltme:** `ruzgar_launch.py` varsayılan API’yi açık bırakır.

### 7. Motor geçişi
- Açılışta `switchMode` çağrılmıyordu; reload döngüsü paneli bozuyordu.
- **Düzeltme:** `wireTopModeButtons` sonrası `switchMode(currentMode)`.

### 8. UI sunucudan
- `desktop_server.py` → `/ui/index.html` + önbellek kapalı.
- `main.js` → API hazır olana kadar bekler, yalnızca HTTP UI yükler.

---

## Senin için tek doğru kullanım

1. **`Ruzgar_TemizBaslat.bat`** — her gün / sorun olunca (tek pencere + API).
2. Tarayıcı isteğe bağlı: **http://127.0.0.1:8779/ui/index.html** (API açıkken).
3. **`Ruzgar_Api_Baslat.bat`** — sadece API + tarayıcı sekmesi.
4. **`Ruzgar_Hafiza_Temizle.bat`** — eski Colab adresi takılıysa.

**Kullanma (yanlış):**
- `Ruzgar_Baslat.bat` → yalnızca Gradio `:7861`, masaüstü API değil.
- `ruzgar-desktop` içinde ayrı `npm start` (çift API riski).
- `file:///.../index.html` doğrudan açmak.

---

## Kontrol listesi (döndüğünde 1 dk)

- [ ] `Ruzgar_TemizBaslat.bat` çift tık → **tek** Electron penceresi
- [ ] Ortada **yeşil** «ANA MOTOR · hazır» veya rev
- [ ] Soldan **Tercüme** → başlık «ÇALIŞMA SAYFASI — TERCÜME MOTORU»
- [ ] Altta soru yaz → **Gönder** → yanıt gelmeli
- [ ] Tarayıcı: `http://127.0.0.1:8779/api/health` → JSON `ok: true`

---

## Değişen dosyalar (bu oturum)

- `ruzgar-desktop/index.html` — erken health, `apiBase`, varsayılan yeşil şerit
- `ruzgar-desktop/app.js` — kök çözümleme, reload, motor init, `file://` yönlendirme
- `ruzgar-desktop/main.js` — HTTP UI, önbellek kapalı, tek pencere
- `ilim-assistant/desktop_server.py` — `/ui` sunumu
- `ilim-assistant/ruzgar_launch.py` — API yaşam döngüsü, `run_desktop_api.py`
- `Ruzgar.ps1`, `Ruzgar_TemizBaslat.bat`, `Ruzgar_Api_Baslat.bat`, `Ruzgar_Hafiza_Temizle.bat`
- `ruzgar-desktop/Start-Ruzgar.ps1` → kök `Ruzgar.ps1`

---

## Hâlâ bilmen gerekenler

- **Ollama kapalıysa** sohbet yine de Gemini ile çalışabilir (`.env` anahtarı varsa).
- **İki pencere** açarsan menüden «Ana motora dön» kullan; ikinci Electron penceresi artık varsayılan değil.
- Sorun devam ederse: `%TEMP%\ruzgar-launch.log` ve `%TEMP%\ruzgar-api.err`

Ümit abi, dönünce önce `Ruzgar_TemizBaslat.bat` — geri kalanı bu rapora göre kontrol edersin.
