"""Whisper tabanlı çok dilli konuşmayı metne (STT)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import torch
from faster_whisper import WhisperModel

# Ortam değişkeni ile model boyutu: tiny, base, small, medium, large-v3
_WHISPER_SIZE = os.environ.get("WHISPER_MODEL", "large-v3")
_WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
_WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE_TYPE", "float16" if _WHISPER_DEVICE == "cuda" else "int8")

_model: Optional[WhisperModel] = None


def get_whisper() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(_WHISPER_SIZE, device=_WHISPER_DEVICE, compute_type=_WHISPER_COMPUTE)
    return _model


def transcribe_audio(
    audio_path: str | Path,
    language: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Ses dosyasını metne çevirir.
    language: ISO 639-1 kodu (ör. tr, en, ar, fa) veya None = otomatik algılama.
    Dönüş: (metin, algılanan veya kullanılan dil kodu)
    """
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    model = get_whisper()
    segments, info = model.transcribe(
        str(path),
        language=language,
        vad_filter=True,
    )
    parts = [s.text for s in segments]
    text = " ".join(p.strip() for p in parts if p.strip()).strip()
    lang = info.language or (language or "unknown")
    return text, lang


def transcribe_uploaded_file(upload_path: str, language: Optional[str] = None) -> Tuple[str, str]:
    """Gradio vb. geçici dosya yolu için."""
    return transcribe_audio(upload_path, language=language)
