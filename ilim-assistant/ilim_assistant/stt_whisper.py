"""
Yerel konuşma → metin (Rüzgar masaüstü /api/stt).

RUZGAR_STT=0 ile kapatılabilir.
İlk çağrıda model indirilebilir (venv + disk alanı gerekir).
"""

from __future__ import annotations

import os
from pathlib import Path

_MODEL = None


def stt_runtime_available() -> bool:
    if os.environ.get("RUZGAR_STT", "").strip().lower() in ("0", "false", "no"):
        return False
    try:
        import faster_whisper  # noqa: F401

        return True
    except ImportError:
        return False


def get_model():
    global _MODEL
    from faster_whisper import WhisperModel

    if _MODEL is None:
        name = os.environ.get("RUZGAR_WHISPER_MODEL", "base")
        device = os.environ.get("RUZGAR_WHISPER_DEVICE", "cpu")
        ctype = os.environ.get("RUZGAR_WHISPER_COMPUTE", "int8")
        _MODEL = WhisperModel(name, device=device, compute_type=ctype)
    return _MODEL


def transcribe_file(path: str | Path, language: str | None = "tr") -> tuple[str, str]:
    """
    Ses dosyasını metne çevirir.
    language: ISO kod (ör. tr) veya None = otomatik algılama.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    model = get_model()
    kwargs: dict = {"vad_filter": True}
    if language:
        kwargs["language"] = language
    segments, info = model.transcribe(str(path), **kwargs)
    parts = [s.text.strip() for s in segments if getattr(s, "text", None)]
    text = " ".join(parts).strip()
    lang = getattr(info, "language", None) or language or "unknown"
    return text, str(lang)
