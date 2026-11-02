# V3 — TTS ilk-byte — 2026-11-03

`ses-v3-tts-ilk-byte-v1-2026-11-03`

## Hedef

V0 mühür: Edge stream first-byte **~1686 ms** · ara sıra `NoAudioReceived`.  
Kısa sohbet parçalarında ProcessPool IPC + ID3, uçtan uca gecikmeyi şişiriyordu (~2 s).

## Yama

| Parça | Ne yaptı |
|-------|----------|
| Kısa yol | `len(text) ≤ RUZGAR_TTS_V3_FAST_CHARS` (520) → in-process Edge **stream collect** |
| Retry | `NoAudioReceived` / boş stream → `RUZGAR_TTS_V3_RETRIES` (2) |
| Meta | Kısa yolda ID3 atlanır (`RUZGAR_TTS_V3_SKIP_META=1`) |
| Workers | ProcessPool varsayılan **2** (paralel prefetch; env ile override) |
| Rate | `RUZGAR_TTS_V3_RATE` (boşsa karakter rate’i) — first-byte’ı tek başına kesmez |

## Ölçüm (bu makine, kısa cümle)

| Yol | first-byte / total |
|-----|-------------------|
| V0 mühür stream | **1686** ms |
| ProcessPool + meta | ~2030 ms total |
| V3 stream collect | first **~820** ms · total **~1200** ms |

Ağ dalgalanır; smoke üst tavan 4500 ms.

## Araçlar

- `ilim_assistant/ses_v3_tts_ilk_byte.py`
- `scripts/smoke_v3_tts_ilk_byte.py`
- `POST /api/tts` (prosody kapalı + kısa metin → V3)

## Kapatma

`RUZGAR_TTS_V3=0` → eski ProcessPool yolu.

## Sonraki

**V4** — barge-in / mic↔TTS kilidi.
