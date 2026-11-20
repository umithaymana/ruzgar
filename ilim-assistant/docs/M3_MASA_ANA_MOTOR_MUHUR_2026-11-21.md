# Masa → Ana Motor mühür (M3) — 2026-11-21

`smoke_masa_m3_muhur.py` → **YEŞİL**

## Dilimler

| Dilim | Durum | Not |
|-------|--------|-----|
| M1 | ✅ | Nezaket (`lütfen`) · bağ smoke · full `masa` alanı |
| M2 | ✅ | Doğal cümle · zincir (`ardından`/,/;`) · onay→liste |
| M3 | ✅ | Bu mühür — masa gerçek iş kapısı kilit |

## Sözleşme (kilit)

1. Sohbet cümlesi → `masa_sohbet_paket` → (yazmada) onay kapısı → `yap` → `done.masa` / full JSON `masa`.
2. İstemci: `ruzgarMasaSunucuUygula` — model dosya yazmaz; izinli eylem yüzeye iner.
3. Okuma serbest (`belgede ne yazıyor` / `belgeyi oku`); yazma onay ister.
4. Sohbet RAG güvenli nokta `8da0da320` bozulmaz; arayüz / boot kilidine dokunulmaz.

## Batarya

- `pytest tests/test_masa_sohbet.py`
- `scripts/smoke_masa_ana_motor_bag.py`
- `scripts/smoke_sohbet_onay_s1.py`
- `scripts/smoke_masa_m3_muhur.py`

## Sonraki

**Çırak Dilim A** — `RUZGAR_CIRAK_GELISIM_PLAN_2026-11-18.md` (atölye; ana kod yok).  
Askıda: Ses → Okuma → kitap okutma.
