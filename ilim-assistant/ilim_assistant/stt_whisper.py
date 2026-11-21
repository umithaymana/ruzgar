"""
Yerel konuşma → metin (Rüzgar masaüstü /api/stt, /api/video/transcribe).

RUZGAR_STT=0 ile kapatılabilir.
İlk çağrıda model indirilebilir (venv + disk alanı gerekir).

Faz S2: segment zaman damgaları + SRT üretimi (`ses_stt_pipeline`).
Varsayılan model: small (RUZGAR_WHISPER_MODEL ile değiştirilir).

Aşama C (2026-11-18): TR kısa utterance düşük gecikme — language=tr zorlama,
beam/vad/condition ayarı, tek model yükü + warm-up. Varsayılan small/cpu/int8 korunur.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_MODEL = None
_MODEL_META: dict[str, Any] = {}
_WARM_DONE = False


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


def whisper_runtime_meta() -> dict[str, Any]:
    """Yüklü model cihaz/compute özeti (Aşama C telemetri)."""
    return dict(_MODEL_META)


def resolve_whisper_device_compute() -> tuple[str, str]:
    """
    Varsayılan: cpu + int8 (bozulmaz).
    RUZGAR_WHISPER_DEVICE=cuda|auto → CUDA dene, olmazsa cpu/int8'e düş.
    """
    raw = (os.environ.get("RUZGAR_WHISPER_DEVICE", "cpu") or "cpu").strip().lower()
    ctype_env = (os.environ.get("RUZGAR_WHISPER_COMPUTE", "") or "").strip()
    if raw in ("cuda", "auto"):
        try:
            import ctranslate2  # type: ignore

            n = int(ctranslate2.get_cuda_device_count() or 0)
            if n > 0:
                # CUDA'da float16 genelde int8'den hızlı/kaliteli; env varsa o geçer
                ctype = ctype_env or ("float16" if raw == "auto" else "float16")
                if raw == "cuda" and ctype_env:
                    ctype = ctype_env
                elif raw == "cuda" and not ctype_env:
                    ctype = "float16"
                return "cuda", ctype
        except Exception:
            pass
        # cuda istendi ama yok → cpu
        return "cpu", ctype_env or "int8"
    return "cpu", ctype_env or "int8"


def unload_model() -> dict[str, Any]:
    """VRAM hakemi — Whisper modelini bellekten bırak."""
    global _MODEL, _MODEL_META, _WARM_DONE
    had = _MODEL is not None
    device = str((_MODEL_META or {}).get("device") or "")
    _MODEL = None
    _MODEL_META = {}
    _WARM_DONE = False
    return {"ok": True, "had_model": had, "device": device}


def get_model():
    global _MODEL, _MODEL_META
    from faster_whisper import WhisperModel

    if _MODEL is None:
        name = whisper_model_name()
        device, ctype = resolve_whisper_device_compute()
        try:
            _MODEL = WhisperModel(name, device=device, compute_type=ctype)
        except Exception:
            # CUDA/compute başarısız → kilitli varsayılan
            if device != "cpu" or ctype != "int8":
                device, ctype = "cpu", "int8"
                _MODEL = WhisperModel(name, device=device, compute_type=ctype)
            else:
                raise
        _MODEL_META = {
            "model": name,
            "device": device,
            "compute_type": ctype,
            "asama_c": True,
        }
        # V2 — PyAV 19 + faster-whisper 1.2: metadata_errors uyumsuzluğu
        _patch_faster_whisper_decode_audio()
    return _MODEL


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name, "1" if default else "0").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)).strip() or str(default))
    except ValueError:
        return default


def build_transcribe_kwargs(
    language: str | None = "tr",
    *,
    duration_sec: float | None = None,
) -> dict[str, Any]:
    """
    Aşama C — TR sohbet klipi için hız/kalite dengesi.
    Varsayılan beam=1 (kısa utterance); uzun klipte beam env ile artar.
    """
    short = duration_sec is None or float(duration_sec) <= 45.0
    beam = max(1, _env_int("RUZGAR_WHISPER_BEAM", 1 if short else 3))
    best_of = max(1, _env_int("RUZGAR_WHISPER_BEST_OF", beam))
    kwargs: dict[str, Any] = {
        "beam_size": beam,
        "best_of": best_of,
        "temperature": 0.0,
        "condition_on_previous_text": False,
        "vad_filter": _env_bool("RUZGAR_WHISPER_VAD", True),
    }
    if language:
        kwargs["language"] = language
    # Kısa ses: zaman damgası/VAD pad hafif; dil algılama yok (tr zorlu)
    if short:
        kwargs["without_timestamps"] = _env_bool("RUZGAR_WHISPER_NO_TS", True)
        if kwargs["vad_filter"]:
            kwargs["vad_parameters"] = {
                "min_silence_duration_ms": _env_int(
                    "RUZGAR_WHISPER_VAD_SILENCE_MS", 280
                ),
                "speech_pad_ms": _env_int("RUZGAR_WHISPER_VAD_PAD_MS", 160),
            }
    return kwargs


def warm_stt_model(*, force: bool = False) -> dict[str, Any]:
    """
    Model yükü + ~0.5 sn sentetik ses ile ilk tur cezası kesilir.
    Tekrar çağrıda no-op (yeniden yükleme yok).
    """
    global _WARM_DONE
    out: dict[str, Any] = {
        "ok": False,
        "already": False,
        "load_ms": None,
        "infer_ms": None,
        "meta": {},
        "note": "",
    }
    if not stt_runtime_available():
        out["note"] = "stt_unavailable"
        return out
    if _WARM_DONE and not force:
        out["ok"] = True
        out["already"] = True
        out["meta"] = whisper_runtime_meta()
        out["note"] = "warm_already"
        return out
    import time

    import numpy as np

    t0 = time.perf_counter()
    model = get_model()
    out["load_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
    # ~0.6 sn sessizlik — decode yolu ısınır, metin beklenmez
    audio = np.zeros(int(16000 * 0.6), dtype=np.float32)
    t1 = time.perf_counter()
    try:
        kw = build_transcribe_kwargs("tr", duration_sec=0.6)
        kw["vad_filter"] = False  # sessizlikte VAD atlanır
        segs, _info = model.transcribe(audio, **kw)
        for _ in segs:
            pass
        out["infer_ms"] = round((time.perf_counter() - t1) * 1000.0, 1)
        out["ok"] = True
        _WARM_DONE = True
    except Exception as exc:
        out["note"] = str(exc)[:200]
        out["ok"] = _MODEL is not None
        if out["ok"]:
            _WARM_DONE = True
    out["meta"] = whisper_runtime_meta()
    return out

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
    Aşama C: varsayılan tr + kısa klip düşük latency kwargs.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    model = get_model()
    duration_hint: float | None = None
    audio = None
    # V2: önce numpy (PyAV metadata_errors tuzağını atlar); gerekirse yol
    try:
        audio = _decode_audio_f32(path, sampling_rate=16000)
        if getattr(audio, "shape", None) is not None and len(audio) > 0:
            duration_hint = float(len(audio)) / 16000.0
    except Exception:
        audio = None
    kwargs = build_transcribe_kwargs(language, duration_sec=duration_hint)
    try:
        if audio is not None:
            raw_segments, info = model.transcribe(audio, **kwargs)
        else:
            raw_segments, info = model.transcribe(str(path), **kwargs)
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
