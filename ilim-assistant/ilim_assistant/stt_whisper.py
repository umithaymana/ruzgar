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
        # V2 — PyAV 19 + faster-whisper 1.2: metadata_errors uyumsuzluğu
        _patch_faster_whisper_decode_audio()
    return _MODEL


def _patch_faster_whisper_decode_audio() -> None:
    """av.open(..., metadata_errors=) PyAV 19'da yok — decode'u sarmala."""
    try:
        import faster_whisper.audio as fw_audio
    except Exception:
        return
    if getattr(fw_audio, "_ruzgar_v2_decode_patched", False):
        return
    _orig = fw_audio.decode_audio

    def _safe_decode(input_file, sampling_rate=16000, **kwargs):
        try:
            return _orig(input_file, sampling_rate=sampling_rate, **kwargs)
        except TypeError as exc:
            if "metadata_errors" not in str(exc):
                raise
            return _decode_audio_f32(Path(str(input_file)), sampling_rate=sampling_rate)

    fw_audio.decode_audio = _safe_decode  # type: ignore[assignment]
    fw_audio._ruzgar_v2_decode_patched = True  # type: ignore[attr-defined]


def _decode_audio_f32(path: Path, *, sampling_rate: int = 16000):
    """WAV/PyAV ile 16 kHz mono float32 — faster-whisper girdi biçimi."""
    import numpy as np

    path = Path(path)
    if path.suffix.lower() == ".wav":
        import wave

        with wave.open(str(path), "rb") as w:
            ch = w.getnchannels()
            sw = w.getsampwidth()
            rate = w.getframerate()
            n = w.getnframes()
            raw = w.readframes(n)
        if sw == 2:
            x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sw == 1:
            x = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            raise ValueError(f"wav sampwidth={sw}")
        if ch > 1:
            x = x.reshape(-1, ch).mean(axis=1)
        if rate != sampling_rate and rate > 0:
            # lineer yeniden örnekleme (bağımlılıksız)
            duration = x.shape[0] / float(rate)
            n_out = max(1, int(round(duration * sampling_rate)))
            xp = np.linspace(0.0, 1.0, num=x.shape[0], endpoint=False)
            x_out = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
            x = np.interp(x_out, xp, x).astype(np.float32)
        return x

    import av

    with av.open(str(path), mode="r") as container:
        stream = next(s for s in container.streams if s.type == "audio")
        resampler = av.audio.resampler.AudioResampler(
            format="flt", layout="mono", rate=sampling_rate
        )
        chunks: list = []
        for frame in container.decode(stream):
            for rf in resampler.resample(frame):
                arr = rf.to_ndarray()
                if arr.ndim > 1:
                    arr = arr.mean(axis=0)
                chunks.append(np.asarray(arr, dtype=np.float32).reshape(-1))
        for rf in resampler.resample(None):
            arr = rf.to_ndarray()
            if arr.ndim > 1:
                arr = arr.mean(axis=0)
            chunks.append(np.asarray(arr, dtype=np.float32).reshape(-1))
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks)


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
    # V2: önce numpy (PyAV metadata_errors tuzağını atlar); gerekirse yol
    try:
        audio = _decode_audio_f32(path, sampling_rate=16000)
        raw_segments, info = model.transcribe(audio, **kwargs)
    except Exception:
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
