# V0 — STT/TTS gecikme baseline — 2026-10-23

`ses-v0-baseline-v1-2026-10-23` · venv: `D:\ÜMİT\14-) PROGRAMLAR\venvs\ruzgar`

**Mühür:** Bu dosya Faz V0 kapanış ölçümüdür. Smoke yeniden ölçüm yazmaz; canlı sayılar `V0_STT_TTS_REMEASURE.json`.

## STT (faster-whisper · model=small · cpu/int8)

| Ölçüm | ms | Not |
|-------|-----|-----|
| get_model **soğuk** (ilk indirme) | **504913** | HF hub; bir kez |
| get_model **ılık** (önbellek) | **10288** | V1 ısınma hedefi |
| transcribe (0.6s sessiz wav) | — | `open(... metadata_errors)` hatası — V2’de PyAV yaması |

## TTS (edge-tts · tr-TR-AhmetNeural)

| Ölçüm | ms | Not |
|-------|-----|-----|
| stream first-byte (başarılı tur) | **1686** | ara sıra `NoAudioReceived` |
| synth_full save (başarılı tur) | **1880** | ara sıra `NoAudioReceived` |

Edge ağ kararsızlığı V3’te chunk/retry ile ele alınacak.

## Araçlar

- `ilim_assistant/ses_v0_baseline.py`
- `scripts/smoke_v0_stt_tts_baseline.py` (varsayılan `RUZGAR_V0_STT_LOAD=0`; tam ölçüm: `=1` + venv python)
- Yeniden ölçüm çıktısı: `docs/V0_STT_TTS_REMEASURE.json` (mühürü ezmez)

## Sonraki

**V1** — Whisper `get_model` + TTS pool prime (boot 1–3’ü geciktirmeden, port sonrası). ✅  
**V2** — STT decode (PyAV19 `metadata_errors`) ✅  
**V3** — TTS ilk-byte (chunk / workers / rate) ⬜
