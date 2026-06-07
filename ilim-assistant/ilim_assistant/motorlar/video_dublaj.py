# Created by Ümit & Gökçenur
"""
Faz S6 — Film dublaj prototipi (tek anlatıcı).

Akış: video/ses → Whisper segment → çeviri → TTS (Edge/kolon) → zaman çizelgesi → mux.
Çok karakterli / dudak senkronu yok — MVP dublaj.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.altyazi_fabrika import (
    cues_to_srt,
    translate_cues,
)
from ilim_assistant.motorlar.altyazi_fabrika import AltyaziCue
from ilim_assistant.motorlar.ses_klon_motoru import (
    coz_referans_yolu,
    synthesize_clone_wav,
    wav_to_mp3,
    xtts_runtime_available,
)
from ilim_assistant.motorlar.ses_motoru import (
    EDGE_VOICES,
    edge_pitch_string,
    edge_rate_yuzdesi,
    normalize_ses_karakteri,
)
from ilim_assistant.motorlar.ses_stt_pipeline import (
    normalize_stt_language,
    transcribe_media_path,
)
from ilim_assistant.stt_whisper import TranscribeResult
from ilim_assistant.tts_service import _edge_synth_mp3_bytes
from ilim_assistant.video_ffmpeg import (
    audio_duration_sec,
    concat_audio_files,
    ffmpeg_available,
    ffprobe_json,
    generate_silence_wav,
    mux_replace_audio,
)

DUBLAJ_VERSION = "video-dublaj-s6-2026-06-06"
MIMAR = "Ümit & Gökçenur"


@dataclass
class DubSegment:
    index: int
    start: float
    end: float
    source_text: str
    target_text: str = ""
    audio_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "source_text": self.source_text,
            "target_text": self.target_text,
            "has_audio": self.audio_path is not None and self.audio_path.is_file(),
        }


@dataclass
class DubbingResult:
    ok: bool
    output_video: Path | None = None
    output_audio: Path | None = None
    output_srt: Path | None = None
    segments: list[DubSegment] = field(default_factory=list)
    detected_language: str = ""
    target_language: str = ""
    voice_mode: str = "edge"
    error: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "segment_count": len(self.segments),
            "detected_language": self.detected_language,
            "target_language": self.target_language,
            "voice_mode": self.voice_mode,
            "error": self.error,
            "version": DUBLAJ_VERSION,
        }


def dublaj_enabled() -> bool:
    return os.environ.get("RUZGAR_VIDEO_DUB", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def max_dub_segments() -> int:
    try:
        return max(5, int(os.environ.get("RUZGAR_DUB_MAX_SEG", "48")))
    except ValueError:
        return 48


def max_dub_duration_sec() -> float:
    try:
        return max(60.0, float(os.environ.get("RUZGAR_DUB_MAX_SEC", "900")))
    except ValueError:
        return 900.0


def media_duration_sec(path: Path) -> float:
    try:
        return float(ffprobe_json(path).get("format", {}).get("duration") or 0.0)
    except Exception:
        return 0.0


def _stt_to_dub_segments(result: TranscribeResult) -> list[DubSegment]:
    out: list[DubSegment] = []
    for i, seg in enumerate(result.segments, 1):
        txt = (seg.text or "").strip()
        if not txt:
            continue
        start = float(seg.start)
        end = float(max(seg.end, start + 0.25))
        out.append(
            DubSegment(
                index=i,
                start=start,
                end=end,
                source_text=txt,
            )
        )
    return out


def _merge_dub_segments(
    segments: list[DubSegment],
    *,
    max_gap: float = 0.85,
    max_chars: int = 220,
) -> list[DubSegment]:
    if not segments:
        return []
    merged: list[DubSegment] = []
    buf = segments[0]
    for seg in segments[1:]:
        gap = seg.start - buf.end
        combined_len = len(buf.source_text) + len(seg.source_text) + 1
        if gap <= max_gap and combined_len <= max_chars:
            buf = DubSegment(
                index=buf.index,
                start=buf.start,
                end=seg.end,
                source_text=f"{buf.source_text} {seg.source_text}".strip(),
            )
        else:
            merged.append(buf)
            buf = DubSegment(
                index=len(merged) + 1,
                start=seg.start,
                end=seg.end,
                source_text=seg.source_text,
            )
    merged.append(buf)
    for i, s in enumerate(merged, 1):
        merged[i - 1] = DubSegment(
            index=i,
            start=s.start,
            end=s.end,
            source_text=s.source_text,
        )
    return merged


def _translate_segments(
    segments: list[DubSegment],
    *,
    src_lang: str,
    tgt_lang: str,
) -> list[DubSegment]:
    if not segments:
        return []
    tgt = (tgt_lang or "tr").strip().lower()[:2]
    src = (src_lang or "auto").strip().lower()[:8]
    if src in ("", "same", "none") or src == tgt:
        return [
            DubSegment(
                index=s.index,
                start=s.start,
                end=s.end,
                source_text=s.source_text,
                target_text=s.source_text,
            )
            for s in segments
        ]
    cues = [
        AltyaziCue(index=s.index, start=s.start, end=s.end, text=s.source_text)
        for s in segments
    ]
    tr = translate_cues(cues, src_lang=src, tgt_lang=tgt)
    out: list[DubSegment] = []
    for s, c in zip(segments, tr):
        out.append(
            DubSegment(
                index=s.index,
                start=s.start,
                end=s.end,
                source_text=s.source_text,
                target_text=c.text.strip() or s.source_text,
            )
        )
    return out


def _edge_voice_for_dub(karakter: str, tgt_lang: str) -> tuple[str, str, str]:
    kar = normalize_ses_karakteri(karakter)
    if tgt_lang.startswith("ar"):
        voice = os.environ.get("RUZGAR_TTS_AR_VOICE", "ar-SA-HamedNeural")
    elif tgt_lang.startswith("en"):
        voice = "en-US-GuyNeural"
    else:
        voice = EDGE_VOICES.get(kar, "tr-TR-AhmetNeural")
    from ilim_assistant.motorlar.ses_motoru import IcerikYolu

    rate = edge_rate_yuzdesi(karakter=kar, icerik=IcerikYolu.genel)
    pitch = edge_pitch_string(kar, IcerikYolu.genel)
    return voice, rate, pitch


def _synth_segment_edge(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
    out_mp3: Path,
) -> Path:
    data = _edge_synth_mp3_bytes((text.strip(), voice, rate, pitch))
    out_mp3.write_bytes(data)
    return out_mp3


def _synth_segment_clone(
    text: str,
    *,
    speaker: Path,
    language: str,
    work_dir: Path,
) -> Path:
    wav = work_dir / f"seg_{uuid.uuid4().hex[:8]}.wav"
    synthesize_clone_wav(text, speaker, language=language, out_wav=wav)
    mp3 = work_dir / f"seg_{uuid.uuid4().hex[:8]}.mp3"
    wav_to_mp3(wav, mp3)
    try:
        wav.unlink(missing_ok=True)
    except OSError:
        pass
    return mp3


def _mp3_to_wav(mp3: Path, wav: Path) -> Path:
    from ilim_assistant.video_ffmpeg import run_ffmpeg_args

    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(mp3.resolve()),
            "-ar",
            "22050",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav.resolve()),
        ],
        timeout_sec=120,
    )
    return wav


def assemble_dub_audio_track(
    segments: list[DubSegment],
    output_wav: Path,
    *,
    tail_pad_sec: float = 1.5,
) -> Path:
    """Segment MP3'lerini zaman boşluklarıyla tek WAV izinde birleştirir."""
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg gerekli.")
    pieces: list[Path] = []
    temps: list[Path] = []
    prev_end = 0.0
    try:
        for seg in segments:
            if not seg.audio_path or not seg.audio_path.is_file():
                continue
            gap = max(0.0, float(seg.start) - prev_end)
            if gap >= 0.04:
                fd, sil = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                sil_p = Path(sil)
                generate_silence_wav(sil_p, int(gap * 1000), sample_rate=22050)
                pieces.append(sil_p)
                temps.append(sil_p)
            fd2, w = tempfile.mkstemp(suffix=".wav")
            os.close(fd2)
            wav_p = Path(w)
            _mp3_to_wav(seg.audio_path, wav_p)
            pieces.append(wav_p)
            temps.append(wav_p)
            try:
                prev_end = seg.start + audio_duration_sec(wav_p)
            except Exception:
                prev_end = seg.end
        if tail_pad_sec > 0:
            fd3, sil2 = tempfile.mkstemp(suffix=".wav")
            os.close(fd3)
            sil_tail = Path(sil2)
            generate_silence_wav(sil_tail, int(tail_pad_sec * 1000), sample_rate=22050)
            pieces.append(sil_tail)
            temps.append(sil_tail)
        if not pieces:
            raise RuntimeError("Dublaj icin sentezlenmis ses parcasi yok.")
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        concat_audio_files(pieces, output_wav, copy_streams=False)
        return output_wav
    finally:
        for p in temps:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


def segments_to_translated_srt(segments: list[DubSegment]) -> str:
    cues = [
        AltyaziCue(
            index=s.index,
            start=s.start,
            end=s.end,
            text=(s.target_text or s.source_text).strip(),
        )
        for s in segments
    ]
    return cues_to_srt(cues)


def run_dubbing_pipeline(
    media_path: Path,
    *,
    target_lang: str = "tr",
    source_lang: str | None = "auto",
    voice_mode: str = "auto",
    karakter: str = "asistan",
    ayar: dict[str, Any] | None = None,
    export_dir: Path,
    video_path: Path | None = None,
) -> DubbingResult:
    """
    Tam dublaj hattı. video_path verilirse mux çıktısı üretilir.
    media_path: transkript kaynağı (video veya ses).
    """
    if not dublaj_enabled():
        return DubbingResult(ok=False, error="Dublaj kapali (RUZGAR_VIDEO_DUB=0)")
    if not ffmpeg_available():
        return DubbingResult(ok=False, error="ffmpeg gerekli")
    if not media_path.is_file():
        return DubbingResult(ok=False, error=f"Dosya yok: {media_path}")

    dur = media_duration_sec(media_path)
    if dur > max_dub_duration_sec():
        return DubbingResult(
            ok=False,
            error=f"Medya cok uzun ({int(dur)} sn > {int(max_dub_duration_sec())} sn)",
        )

    wl = normalize_stt_language(source_lang)
    tgt = (target_lang or "tr").strip().lower()[:2]
    tr = transcribe_media_path(media_path, language=wl)
    segments = _stt_to_dub_segments(tr)
    segments = _merge_dub_segments(segments)
    if len(segments) > max_dub_segments():
        segments = segments[: max_dub_segments()]
    if not segments:
        return DubbingResult(ok=False, error="Transkript segmenti yok")

    src_code = tr.language or wl or "auto"
    segments = _translate_segments(segments, src_lang=str(src_code), tgt_lang=tgt)

    mode = (voice_mode or "auto").strip().lower()
    use_clone = mode == "clone" or (
        mode == "auto" and xtts_runtime_available() and coz_referans_yolu(karakter, ayar=ayar)
    )
    speaker = coz_referans_yolu(karakter, ayar=ayar) if use_clone else None
    if mode == "clone" and not speaker:
        return DubbingResult(ok=False, error="Klon referans sesi yok")
    if use_clone and not speaker:
        use_clone = False

    voice, rate, pitch = _edge_voice_for_dub(karakter, tgt)
    work = Path(tempfile.mkdtemp(prefix="ruzgar_dub_"))
    synth: list[DubSegment] = []
    try:
        for seg in segments:
            text = (seg.target_text or seg.source_text).strip()
            if not text:
                synth.append(seg)
                continue
            mp3 = work / f"dub_{seg.index:04d}.mp3"
            try:
                if use_clone and speaker:
                    mp3 = _synth_segment_clone(
                        text,
                        speaker=speaker,
                        language=tgt,
                        work_dir=work,
                    )
                else:
                    _synth_segment_edge(
                        text,
                        voice=voice,
                        rate=rate,
                        pitch=pitch,
                        out_mp3=mp3,
                    )
                synth.append(
                    DubSegment(
                        index=seg.index,
                        start=seg.start,
                        end=seg.end,
                        source_text=seg.source_text,
                        target_text=seg.target_text,
                        audio_path=mp3,
                    )
                )
            except Exception:
                synth.append(seg)
        export_dir.mkdir(parents=True, exist_ok=True)
        stem = media_path.stem or "dub"
        uid = uuid.uuid4().hex[:10]
        audio_out = export_dir / f"ruzgar_dub_{uid}_{stem}.wav"
        assemble_dub_audio_track(synth, audio_out)
        srt_out = export_dir / f"ruzgar_dub_{uid}_{stem}_{tgt}.srt"
        srt_out.write_text(segments_to_translated_srt(segments), encoding="utf-8")

        video_out: Path | None = None
        vp = video_path or (media_path if media_path.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"} else None)
        if vp and vp.is_file():
            video_out = export_dir / f"ruzgar_dub_{uid}_{stem}.mp4"
            mux_replace_audio(vp, audio_out, video_out, copy_video=True, shortest=True)

        return DubbingResult(
            ok=True,
            output_video=video_out,
            output_audio=audio_out,
            output_srt=srt_out,
            segments=synth,
            detected_language=str(tr.language),
            target_language=tgt,
            voice_mode="clone" if use_clone else "edge",
        )
    finally:
        try:
            for f in work.glob("*"):
                try:
                    f.unlink(missing_ok=True)
                except OSError:
                    pass
            work.rmdir()
        except OSError:
            pass


def dubbing_status_snapshot() -> dict[str, Any]:
    return {
        "enabled": dublaj_enabled(),
        "ffmpeg": ffmpeg_available(),
        "max_segments": max_dub_segments(),
        "max_duration_sec": max_dub_duration_sec(),
        "xtts": xtts_runtime_available(),
        "version": DUBLAJ_VERSION,
        "hint_tr": (
            "Kisa klip ile test edin (5 dk alti). Tek anlatıcı dublaj; cok konusmaci ayirmi yok."
        ),
    }
