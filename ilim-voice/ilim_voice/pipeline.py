"""Metin ve ses boru hatları."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from ilim_voice.langs import NLLB_CODES, WHISPER_TO_NLLB
from ilim_voice.stt import transcribe_audio
from ilim_voice.translate import translate_text
from ilim_voice.tts_engine import synthesize_to_file


def text_translate_speech(
    text: str,
    src_label: str,
    tgt_label: str,
    speaker_wav: Optional[str | Path],
    out_path: Optional[str | Path] = None,
) -> Tuple[str, str, Path]:
    """
    Metin → çeviri → ses dosyası.
    Dönüş: (orijinal veya kaynak dil metni, çeviri metni, wav yolu)
    """
    src_nllb = NLLB_CODES[src_label]
    tgt_nllb = NLLB_CODES[tgt_label]

    if src_nllb != tgt_nllb:
        translated = translate_text(text, src_nllb, tgt_nllb)
    else:
        translated = text

    out = Path(out_path or "output_ilim.wav")
    synthesize_to_file(translated, out, tgt_nllb, speaker_wav=speaker_wav)
    return text, translated, out


def speech_translate_speech(
    audio_path: str | Path,
    tgt_label: str,
    speaker_wav: Optional[str | Path],
    whisper_lang: Optional[str] = None,
    manual_src_label: Optional[str] = None,
    out_path: Optional[str | Path] = None,
) -> Tuple[str, str, str, Path]:
    """
    Ses → metin → çeviri → ses.
    manual_src_label: Whisper yanlış algılarsa kaynak dili elle (ör. Türkçe).
    whisper_lang: Whisper'a ipucu ISO kod (tr, en, ar, fa).
    Dönüş: (transkript, çeviri, kaynak_nllb_kodu, wav)
    """
    text, detected = transcribe_audio(audio_path, language=whisper_lang)

    if manual_src_label:
        src_nllb = NLLB_CODES[manual_src_label]
    else:
        src_nllb = WHISPER_TO_NLLB.get(detected, "tur_Latn")

    tgt_nllb = NLLB_CODES[tgt_label]
    if src_nllb != tgt_nllb:
        translated = translate_text(text, src_nllb, tgt_nllb)
    else:
        translated = text

    out = Path(out_path or "output_ilim_s2s.wav")
    synthesize_to_file(translated, out, tgt_nllb, speaker_wav=speaker_wav)
    return text, translated, src_nllb, out
