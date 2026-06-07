"""
Yerel konuşma → metin (Rüzgar masaüstü /api/stt, /api/video/transcribe).

RUZGAR_STT=0 ile kapatılabilir.
İlk çağrıda model indirilebilir (venv + disk alanı gerekir).

Faz S2: segment zaman damgaları + SRT üretimi (`ses_stt_pipeline`).
Varsayılan model: small (RUZGAR_WHISPER_MODEL ile değiştirilir).
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
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


def whisper_available() -> bool:
    """Uyumluluk: dinleme_motoru ve sağlık uçları."""
    return stt_runtime_available()


def whisper_model_name() -> str:
    return os.environ.get("RUZGAR_WHISPER_MODEL", "small").strip() or "small"


def get_model():
    global _MODEL
    from faster_whisper import WhisperModel

    if _MODEL is None:
        name = whisper_model_name()
        device = os.environ.get("RUZGAR_WHISPER_DEVICE", "cpu")
        ctype = os.environ.get("RUZGAR_WHISPER_COMPUTE", "int8")
        _MODEL = WhisperModel(name, device=device, compute_type=ctype)
    return _MODEL


@dataclass(frozen=True)
class SttSegment:
    start: float
    end: float
    text: str

    def to_dict(self) -> dict[str, float | str]:
        return {"start": self.start, "end": self.end, "text": self.text}


@dataclass(frozen=True)
class TranscribeResult:
    text: str
    language: str
    segments: list[SttSegment]
    language_probability: float | None = None
    duration_sec: float | None = None

    def to_dict(self, *, include_segments: bool = True) -> dict:
        out: dict = {
            "text": self.text,
            "language": self.language,
            "language_probability": self.language_probability,
            "duration_sec": self.duration_sec,
        }
        if include_segments:
            out["segments"] = [s.to_dict() for s in self.segments]
        return out


def transcribe_file_detailed(
    path: str | Path,
    language: str | None = "tr",
) -> TranscribeResult:
    """
    Ses dosyasını segmentlerle metne çevirir.
    language: ISO kod (ör. tr) veya None = otomatik algılama.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    model = get_model()
    kwargs: dict = {"vad_filter": True}
    if language:
        kwargs["language"] = language
    raw_segments, info = model.transcribe(str(path), **kwargs)
    segments: list[SttSegment] = []
    parts: list[str] = []
    for s in raw_segments:
        t = (getattr(s, "text", None) or "").strip()
        if not t:
            continue
        start = float(getattr(s, "start", 0.0) or 0.0)
        end = float(getattr(s, "end", start) or start)
        segments.append(SttSegment(start=start, end=end, text=t))
        parts.append(t)
    text = " ".join(parts).strip()
    lang = getattr(info, "language", None) or language or "unknown"
    prob = getattr(info, "language_probability", None)
    dur = getattr(info, "duration", None)
    return TranscribeResult(
        text=text,
        language=str(lang),
        segments=segments,
        language_probability=float(prob) if prob is not None else None,
        duration_sec=float(dur) if dur is not None else None,
    )


def transcribe_file(path: str | Path, language: str | None = "tr") -> tuple[str, str]:
    """Geriye uyumlu kısa API."""
    result = transcribe_file_detailed(path, language)
    return result.text, result.language


def format_srt_timestamp(seconds: float) -> str:
    ms_total = max(0, int(round(float(seconds) * 1000)))
    h, rem = divmod(ms_total, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_to_srt(segments: list[SttSegment]) -> str:
    """Whisper segmentlerinden SRT metni."""
    lines: list[str] = []
    idx = 1
    for seg in segments:
        body = seg.text.strip()
        if not body:
            continue
        lines.append(str(idx))
        lines.append(
            f"{format_srt_timestamp(seg.start)} --> {format_srt_timestamp(seg.end)}"
        )
        lines.append(body)
        lines.append("")
        idx += 1
    return "\n".join(lines).strip() + ("\n" if lines else "")


def segments_to_dicts(segments: list[SttSegment]) -> list[dict]:
    return [asdict(s) for s in segments]
