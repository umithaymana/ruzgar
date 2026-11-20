# 2026-11-20 — onarim-faz6-temizlik

## 1) Emir
Mimar Ümit: Faz 6 — ölü modül etiket, 5-motor docstring, genel-bak, port, çırak isim ayrımı.

## 2) Sonuç
gelisim/dinleme yan etiket; boot 7 motor docstring; genel-bak bakımda; smoke 8779; UI çırak günlüğü ayrımı.

## 3) Doğru
Ölü vaat yok; doküman = boot listesi.

## 4) Yanlış
Eski «5 motor» handoff; genel-bak UI ölü ama endpoint vaat ediyor gibiydi.

## 5) Nerede
- Dal: cursor/ruzgar-onarim-fazlari-9eeb
- Commit: cb9d53e08
- Dosyalar: gelisim/dinleme, run_desktop_api, desktop_server genel-bak, app.js, index.html, smoke scripts

## 6) Nasıl uygula
1. Kullanılmayan modüle DURUM satırı.
2. Docstring boot sayısı güncelle.
3. Ölü endpoint bakim:true.
4. Port örnekleri 8779.

## 7) Tuzaklar
8777 rewrite yardımcıları kalsın (eski istemci).

## 8) Çözüm
Etiket + bakim + docstring.

## 9) Bir daha yapma
«5 motor» yazma; genel-bak’ı sessiz ölü bırakma.

## 10) Anahtarlar
`temizlik`, `genel-bak`, `8779`, `cirak`, `faz6`, `onarim`

## 11) Durum
`hazir`

---
## El rahatlatma
### Giriş kapısı
run_desktop_api._boot_motorlar_locked
### Hazır komutlar
```bash
rg -n "5 ara motor|skipGenelBak|bakim" ilim-assistant ruzgar-desktop
```
### Dokunma
knowledge/** port metinleri
### Beklenen çıktı
Endpoint bakim:true; UI etiket ayrımı
### Bilinen kırık
—
### İlk güvenli adım
Docstring «7 ara»
### Kapsam sınırı
Faz 6
### Geri alma
revert
