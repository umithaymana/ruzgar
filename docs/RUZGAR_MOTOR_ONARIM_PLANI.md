# Rüzgar Motor Onarım Planı (Faz 5)

**Tarih:** 20 Kasım 2026 · Dal: `cursor/ruzgar-onarim-fazlari-9eeb`  
**Kaynak:** `RUZGAR_ONARIM_PLANI.md` Faz 5 + tam teşekküllü analiz

---

## Amaç

Okuma ≠ mimar; Hafıza modunda doğru motor; boot ↔ çekirdek hikâyesi net; publish_shared hafif köprü.

---

## Motor teker teker

| Motor | Sorun | Dosya | Fix | Smoke |
|-------|--------|-------|-----|-------|
| **Ses** | publish_shared yok (P2) | `motorlar/ses_motoru.py` + `motor_shared_bridge` | Minimal `publish_shared` notu | Mod ses → havuzda ses anahtarı (opsiyonel) |
| **Video** | Zaten publish var | `motorlar/video_motoru.py` | Dokunma | — |
| **Okuma** | `_MODE_ALIASES` okuma→mimar; normalize sonrası `if m=="okuma"` ölü | `chat_core.py` | Alias: okuma→okuma; bilim→okuma; okuma bağlamı `okuma_motoru` | UI Okuma → mimar instant yok |
| **Bilim** | İsim kayması (çekirdek bilim, boot okuma) | `bilim_motoru.py` (shim), `ruzgar_cekirdegi` | bilim→okuma alias; dokümanda «bilim=okuma yüzü» | bilim zinciri okuma yolu |
| **Mimar** | Boot’ta var, çekirdekte yok (bilinçli) | `mimar_motoru.py`, çekirdek docstring | Mimar yalnız atölye; çekirdek listesine zorla ekleme | Mod mimar → mimar_ctx |
| **Tercüme** | publish zayıf | `tercume_motoru.py` | Minimal shared köprü | — |
| **Hafıza** | Mod hafiza iken 5’li çekirdek enjekte; `hafiza_motoru` yok | `chat_core.py` prepare_turn | `m=="hafiza"` → `hafiza_motoru.build_motor_context`; orkestra False | UI Hafıza → hafıza bloğu, ses/video yok |
| **Programlama** | publish var | — | Dokunma | — |
| **Ana** | — | `main_engine` | Değişmez | — |
| **Çekirdek** | 5 motor ≠ boot 7 | `ruzgar_cekirdegi.py` | Docstring: «boot ısınır (mimar+hafıza); orkestra 5’li çağırır» | Boot log = doküman |

---

## Uygulama sırası (bu tur)

1. Motor planı bu dosyaya yazıldı.  
2. `_MODE_ALIASES` düzelt.  
3. `_orkestra_context_for_turn` hafiza/okuma/mimar’da 5’li zorlamasın.  
4. prepare_turn: hafiza + okuma bağlam enjekte.  
5. Çekirdek docstring hizası.  
6. Minimal `motor_shared_bridge` + hafif çağrılar.  
7. Unit smoke + çırak kaydı.

*Yeni motor / UI / HIZIR yok.*
