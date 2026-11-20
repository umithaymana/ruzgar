# 2026-11-20 — Sohbet tutarlılık fazları (tek kapı)

- **tarih:** 2026-11-20 (Europe/Istanbul)
- **branch:** `cursor/sohbet-tutarlilik-fazlari-9eeb`
- **commit:** `4b6b6b95d` (üstünde çok kaynak `5372ed39f` korunarak)
- **durum:** hazir (main’e alınmadı; Mimar onayı bekler)
- **benzer_anahtarlar:** sohbet, tutarlilik, selam, tek-kapi, faz90, faz91, uslup, zincir

## is_ozeti

Selam/teşekkür için kanonik tek kapı; boş oturumda süreklilik uydurmama; ChatGPT tarzı beyin zincirini bozmadan tek üslup; çok kaynak prompt bloğu silinmedi.

## dosyalar

- `ilim_assistant/ruzgar_sohbet_tek_kapi.py` (yeni)
- `chat_fast_lane.py`, `ana_motor_plan.py`, `chat_core.py`
- `ruzgar_dogal_sohbet_faz91.py`, `ruzgar_genel_faz90.py`
- `ruzgar_session_context.py`, `ruzgar_umed_kurallari.py`, `prompts.py`
- `desktop_server.py`, `tests/test_sohbet_tutarlilik.py`

## tuzaklar

1. Saf selam ile «doğal muhabbet» karışırsa LLM’e zorlanır veya dağınık şablonlar çıkar — `looks_like_pure_greeting` sıkı tutulmalı.
2. Boş history’de `SELAM_WITH_RESUME` («dün konuştuk») **yasak**.
3. Üslup düzenlerken `prompts.py` içindeki **çok kaynak bloğunu silme** — üst commit’i bozar.
4. Sohbet Önce / Faz91 açıkken bile saf selam anlık kalmalı (`allow_instant_greeting_shortcut`).
5. Kapatma acil: `RUZGAR_SOHBET_TEK_KAPI=0`.

## cozum

- Politika B: fast_lane + plan aynı `canonical_selam_reply` kaynağı.
- Selamda hafıza paketi boş; üslup = `RUZGAR_SOHBET_TARZ`; zincir = Faz90/umed.
- Parent artifact: `RUZGAR_USTA_DOGRULAMA.md` — iki dilim (çok kaynak + tutarlılık) hazır.

## rehber (sonraki benzer iş)

Sohbet «tutarsız» şikayetinde önce tek kapı / history prior / prompts bloğu çakışmasına bak. Çok kaynak dalının üstüne rebase veya onun üzerine commit et; paralel çatışan prompt silme.
