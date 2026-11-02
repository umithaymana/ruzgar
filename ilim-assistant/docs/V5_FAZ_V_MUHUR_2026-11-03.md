# Faz V mühür — 2026-11-03

`smoke_v5_faz_v_seal.py` → **YEŞİL** (V0–V5)

## Dilimler

| Dilim | Özet |
|-------|------|
| V0 | STT/TTS gecikme baseline |
| V1 | Port sonrası Whisper+TTS ısınma |
| V2 | STT PyAV19 decode |
| V3 | TTS ilk-byte kısa yol + retry |
| V4 | Barge-in / mic↔TTS kilidi |
| V5 | Sesli tur STT→voice_turn→TTS e2e + mühür |

## V5 e2e

- STT: sessiz wav decode (+ transcribe)
- TTS: V3 stream first-byte
- Sözleşme: `voice_turn` token tavanı + SESLİ TUR addon + `sesli_tur` açık
- UI zinciri: mic→STT→chat(`voiceTurn`)→TTS→`maybeResumeVoiceListenAfterReply` + barge kilit

Araç: `ilim_assistant/ses_v5_sesli_tur.py` · `scripts/smoke_v5_sesli_tur.py`

## Sonraki

**Faz M** — M1 Video → M2 Tercüme → M3 Okuma → M4 Mimar.
