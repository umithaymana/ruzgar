# 2026-11-20 — onarim-faz5-motor-routing

## 1) Emir
Mimar Ümit: Faz 5 — önce motor planı yaz, sonra okuma≠mimar, hafıza bağlamı, çekirdek↔boot, publish_shared.

## 2) Sonuç
Motor planı `/opt/cursor/artifacts/RUZGAR_MOTOR_ONARIM_PLANI.md`; alias düzeltildi; hafiza/okuma/ses/tercume bağlamı; çekirdek docstring; minimal shared bridge.

## 3) Doğru
- okuma/bilim → okuma (mimar değil).
- hafiza modunda hafiza_motoru; 5’li çekirdek yok.

## 4) Yanlış
- Eskiden okuma→mimar; hafiza’da ses/video orkestra.

## 5) Nerede
- Dal: cursor/ruzgar-onarim-fazlari-9eeb
- Commit: 4d756ca90
- Dosyalar: chat_core.py, ruzgar_cekirdegi.py, motor_shared_bridge.py, app.js, tests/test_motor_routing_faz5.py
- Plan: /opt/cursor/artifacts/RUZGAR_MOTOR_ONARIM_PLANI.md

## 6) Nasıl uygula
1. Önce motor planı yaz.
2. Alias + orkestra istisna listesi.
3. prepare_turn özel mod bağlamları.
4. Docstring boot≠çekirdek.

## 7) Tuzaklar
bilim→okuma köprüsü bir sürüm kalsın.

## 8) Çözüm
Alias + özel elif’ler + docstring.

## 9) Bir daha yapma
okuma’yı mimar’a alias etme.

## 10) Anahtarlar
`motor`, `okuma`, `mimar`, `hafiza`, `alias`, `faz5`, `onarim`

## 11) Durum
`hazir`

---
## El rahatlatma
### Giriş kapısı
`/opt/cursor/artifacts/RUZGAR_MOTOR_ONARIM_PLANI.md`
### Hazır komutlar
```bash
cd ilim-assistant && python3 -m pytest tests/test_motor_routing_faz5.py -q
```
### Dokunma
Yeni motor/UI/HIZIR
### Beklenen çıktı
normalize(okuma)==okuma; 5 test yeşil
### Bilinen kırık
—
### İlk güvenli adım
normalize_mode('okuma')
### Kapsam sınırı
Faz 5
### Geri alma
revert
