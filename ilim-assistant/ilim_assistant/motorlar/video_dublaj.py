# Created by Ümit & Gökçenur
"""
V1.2 Video Dublaj — tek anlatıcı (omurga + iptal/VRAM + kalite mux).

Akış: video/ses → Whisper → çeviri → S1–S3 TTS → soft_fit → loudnorm → (opsiyon miks) → mux.
V1.0: muhabbet/âlim/tilavet/asistan → BUSENAZ / kuran + Edge yedek.
V1.1: segment iptal + VRAM hold(xtts).
V1.2: normalize, orijinal duck miks, soft_fit süre yumuşatma.
Çok karakterli / dudak senkronu yok.
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
    should_use_clone,
    synthesize_clone_wav,
    wav_to_mp3,
    xtts_runtime_available,
)
from ilim_assistant.motorlar.ses_motoru import (
    EDGE_VOICES,
    IcerikYolu,
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

DUBLAJ_VERSION = "video-dublaj-v1.2-2026-11-21"
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
    karakter: str = "muhabbet"
    tavan: str = "muhabbet"
    edge_yedek: bool = False
    cancel_token: int | None = None
    error: str | None = None
    cancelled: bool = False
    quality_mux: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "segment_count": len(self.segments),
            "detected_language": self.detected_language,
            "target_language": self.target_language,
            "voice_mode": self.voice_mode,
            "karakter": self.karakter,
            "tavan": self.tavan,
            "edge_yedek": self.edge_yedek,
            "cancel_token": self.cancel_token,
            "cancelled": self.cancelled,
            "quality_mux": dict(self.quality_mux or {}),
            "error": self.error,
            "version": DUBLAJ_VERSION,
            "v1": {
                "omurga": True,
                "iptal_vram": True,
                "kalite_mux": True,
            },
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


def resolve_dub_omurga(
    karakter: str | None,
    *,
    voice_mode: str = "auto",
    ayar: dict[str, Any] | None = None,
    tgt_lang: str = "tr",
) -> dict[str, Any]:
    """
    V1.0 — S1–S3 omurga planı: tavan profil + klon/Edge kararı + rate/pitch.
    /api/tts ile aynı should_use_clone + coz_referans_yolu.
    """
    from ilim_assistant.ses_s1_tavan_profil import coz_tavan_profil

    tavan = coz_tavan_profil(karakter)
    kar = normalize_ses_karakteri(tavan)
    mode = (voice_mode or "auto").strip().lower()
    if mode in ("", "default"):
        mode = "auto"

    # Dublajda auto: TTS ile aynı onay kapısı; yoksa klon_onay yoksa Edge
    use_clone = should_use_clone(
        backend=mode if mode in ("edge", "clone", "auto") else "auto",
        karakter=kar.value,
        ayar=ayar,
    )
    speaker = coz_referans_yolu(kar.value, ayar=ayar) if use_clone or mode == "clone" else None
    if mode == "clone" and speaker is None:
        return {
            "ok": False,
            "error": "Klon referans sesi yok",
            "tavan": tavan,
            "karakter": kar.value,
            "voice_mode": mode,
        }
    if use_clone and speaker is None:
        use_clone = False

    # Edge parametreleri — S2 tavan varsa uygula
    tgt = (tgt_lang or "tr").strip().lower()[:2]
    if tgt.startswith("ar"):
        voice = os.environ.get("RUZGAR_TTS_AR_VOICE", "ar-SA-HamedNeural")
    elif tgt.startswith("en"):
        voice = "en-US-GuyNeural"
    else:
        voice = EDGE_VOICES.get(kar, "tr-TR-AhmetNeural")

    icerik = (
        IcerikYolu.kuran
        if tavan == "tilavet"
        else (IcerikYolu.tasavvuf_hadis if tavan == "alim" else IcerikYolu.genel)
    )
    try:
        from ilim_assistant.ses_s2_prosodi_tavan import (
            ayarla_pitch_string,
            ayarla_rate_string,
            coz_tts_tavan_paketi,
        )

        s2 = coz_tts_tavan_paketi(kar.value, ayar=ayar)
        rate = edge_rate_yuzdesi(
            karakter=kar,
            icerik=icerik,
            hiz_carpani=float(s2["hiz"]),
            huzur_carpani=float(s2["huzur"]),
        )
        pitch = edge_pitch_string(kar, icerik)
        rate = ayarla_rate_string(rate, kar.value)
        pitch = ayarla_pitch_string(pitch, kar.value)
        s2_meta = {"hiz": s2["hiz"], "huzur": s2["huzur"], "durak": s2["durak_carpani"]}
    except Exception:
        rate = edge_rate_yuzdesi(karakter=kar, icerik=icerik)
        pitch = edge_pitch_string(kar, icerik)
        s2_meta = None

    return {
        "ok": True,
        "tavan": tavan,
        "karakter": kar.value,
        "voice_mode_req": mode,
        "use_clone": bool(use_clone and speaker is not None),
        "speaker": speaker,
        "speaker_name": speaker.name if speaker else None,
        "xtts": xtts_runtime_available(),
        "edge_voice": voice,
        "rate": rate,
        "pitch": pitch,
        "icerik": icerik.value,
        "s2": s2_meta,
        "version": DUBLAJ_VERSION,
    }


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
    cancel_token: int | None = None,
) -> Path:
    """V1.1 — cancel_token + VRAM (synthesize_clone_wav içinde hold)."""
    wav = work_dir / f"seg_{uuid.uuid4().hex[:8]}.wav"
    synthesize_clone_wav(
        text,
        speaker,
        language=language,
        out_wav=wav,
        cancel_token=cancel_token,
    )
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
    soft_fit: bool = True,
) -> dict[str, Any]:
    """
    Segment MP3 → WAV; V1.2 soft_fit ile slot süresine uydur; birleştir.
    Dönüş: {path, fit_plans}
    """
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg gerekli.")
    from ilim_assistant.ses_v1_dub_kalite_mux import soft_fit_audio_duration

    pieces: list[Path] = []
    temps: list[Path] = []
    fit_plans: list[dict[str, Any]] = []
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
            wav_raw = Path(w)
            _mp3_to_wav(seg.audio_path, wav_raw)
            temps.append(wav_raw)
            slot = max(0.25, float(seg.end) - float(seg.start))
            wav_p = wav_raw
            if soft_fit:
                fd3, wf = tempfile.mkstemp(suffix=".wav")
                os.close(fd3)
                fitted = Path(wf)
                plan = soft_fit_audio_duration(wav_raw, fitted, slot)
                plan["index"] = seg.index
                fit_plans.append(plan)
                temps.append(fitted)
                wav_p = fitted
            pieces.append(wav_p)
            # Zaman çizelgesi: slot sonuna hizala (kayma birikmesin)
            prev_end = float(seg.end)
        if tail_pad_sec > 0:
            fd4, sil2 = tempfile.mkstemp(suffix=".wav")
            os.close(fd4)
            sil_tail = Path(sil2)
            generate_silence_wav(sil_tail, int(tail_pad_sec * 1000), sample_rate=22050)
            pieces.append(sil_tail)
            temps.append(sil_tail)
        if not pieces:
            raise RuntimeError("Dublaj icin sentezlenmis ses parcasi yok.")
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        concat_audio_files(pieces, output_wav, copy_streams=False)
        return {"path": output_wav, "fit_plans": fit_plans, "segments_used": len(fit_plans)}
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
    cancel_token: int | None = None,
    mix_original: bool = False,
    orig_duck_db: float | None = None,
    normalize: bool = True,
    soft_fit: bool = True,
) -> DubbingResult:
    """
    Tam dublaj hattı. video_path verilirse mux çıktısı üretilir.
    V1.0 omurga + V1.1 iptal/VRAM + V1.2 kalite mux (normalize / miks / soft_fit).
    """
    from ilim_assistant.ses_xtts_iptal import (
        CloneCancelled,
        begin_job,
        check as xtts_check,
        end_job,
        iptal_enabled,
    )

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

    plan = resolve_dub_omurga(
        karakter, voice_mode=voice_mode, ayar=ayar, tgt_lang=target_lang or "tr"
    )
    if not plan.get("ok"):
        return DubbingResult(
            ok=False,
            error=str(plan.get("error") or "Omurga plani basarisiz"),
            karakter=str(plan.get("karakter") or "muhabbet"),
            tavan=str(plan.get("tavan") or "muhabbet"),
        )

    tavan = str(plan["tavan"])
    kar_val = str(plan["karakter"])
    use_clone = bool(plan["use_clone"])
    speaker: Path | None = plan.get("speaker")
    voice = str(plan["edge_voice"])
    rate = str(plan["rate"])
    pitch = str(plan["pitch"])
    edge_yedek = False

    wl = normalize_stt_language(source_lang)
    tgt = (target_lang or "tr").strip().lower()[:2]
    tr = transcribe_media_path(media_path, language=wl)
    segments = _stt_to_dub_segments(tr)
    segments = _merge_dub_segments(segments)
    if len(segments) > max_dub_segments():
        segments = segments[: max_dub_segments()]
    if not segments:
        return DubbingResult(
            ok=False,
            error="Transkript segmenti yok",
            karakter=kar_val,
            tavan=tavan,
        )

    src_code = tr.language or wl or "auto"
    segments = _translate_segments(segments, src_lang=str(src_code), tgt_lang=tgt)

    # V1.1 — iş jetonu: /api/tts/cancel → cancel_all bu gen'i keser
    token = cancel_token
    owned = False
    if token is None and iptal_enabled():
        token = begin_job()
        owned = True

    work = Path(tempfile.mkdtemp(prefix="ruzgar_dub_"))
    synth: list[DubSegment] = []
    cancelled = False
    try:
        for seg in segments:
            if token is not None:
                try:
                    xtts_check(token)
                except CloneCancelled:
                    cancelled = True
                    break
            text = (seg.target_text or seg.source_text).strip()
            if not text:
                synth.append(seg)
                continue
            # Köşeli etiketler ham okunmasın
            try:
                from ilim_assistant.ses_etiket_prosodi import parse_ses_etiketleri

                text = parse_ses_etiketleri(text).temiz_metin or text
            except Exception:
                pass
            mp3 = work / f"dub_{seg.index:04d}.mp3"
            try:
                if use_clone and speaker is not None:
                    try:
                        mp3 = _synth_segment_clone(
                            text,
                            speaker=speaker,
                            language=tgt,
                            work_dir=work,
                            cancel_token=token,
                        )
                    except CloneCancelled:
                        cancelled = True
                        break
                    except Exception:
                        # S3 tarzı Edge yedek
                        use_clone = False
                        edge_yedek = True
                        _synth_segment_edge(
                            text,
                            voice=voice,
                            rate=rate,
                            pitch=pitch,
                            out_mp3=mp3,
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
            except CloneCancelled:
                cancelled = True
                break
            except Exception:
                synth.append(seg)

        if cancelled:
            return DubbingResult(
                ok=False,
                error="Dublaj iptal edildi (cancel)",
                segments=synth,
                detected_language=str(tr.language),
                target_language=tgt,
                voice_mode="clone" if (plan["use_clone"] and not edge_yedek) else "edge",
                karakter=kar_val,
                tavan=tavan,
                edge_yedek=edge_yedek,
                cancel_token=token,
                cancelled=True,
            )

        export_dir.mkdir(parents=True, exist_ok=True)
        stem = media_path.stem or "dub"
        uid = uuid.uuid4().hex[:10]
        audio_out = export_dir / f"ruzgar_dub_{uid}_{stem}.wav"
        asm = assemble_dub_audio_track(synth, audio_out, soft_fit=soft_fit)

        # V1.2 — loudness + isteğe bağlı orijinal miks
        from ilim_assistant.ses_v1_dub_kalite_mux import apply_quality_mux

        v12_dir = work / "v12"
        v12_dir.mkdir(parents=True, exist_ok=True)
        qmux = apply_quality_mux(
            audio_out,
            media_path=media_path,
            mix_original=bool(mix_original),
            orig_duck_db=orig_duck_db,
            normalize=bool(normalize),
            work_dir=v12_dir,
        )
        qmux["fit_plans"] = list(asm.get("fit_plans") or [])[:24]
        qmux["soft_fit"] = bool(soft_fit)

        srt_out = export_dir / f"ruzgar_dub_{uid}_{stem}_{tgt}.srt"
        srt_out.write_text(segments_to_translated_srt(segments), encoding="utf-8")

        video_out: Path | None = None
        vp = video_path or (
            media_path
            if media_path.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}
            else None
        )
        if vp and vp.is_file():
            video_out = export_dir / f"ruzgar_dub_{uid}_{stem}.mp4"
            mux_replace_audio(vp, audio_out, video_out, copy_video=True, shortest=True)

        final_clone = bool(plan["use_clone"]) and not edge_yedek and speaker is not None
        return DubbingResult(
            ok=True,
            output_video=video_out,
            output_audio=audio_out,
            output_srt=srt_out,
            segments=synth,
            detected_language=str(tr.language),
            target_language=tgt,
            voice_mode="clone" if final_clone else "edge",
            karakter=kar_val,
            tavan=tavan,
            edge_yedek=edge_yedek,
            cancel_token=token,
            quality_mux=qmux,
        )
    finally:
        if owned and token is not None:
            try:
                end_job(token)
            except Exception:
                pass
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
    from ilim_assistant.ses_xtts_iptal import snapshot as iptal_snap
    from ilim_assistant.ses_vram_hakem import snapshot as vram_snap

    ayar = None
    try:
        from ilim_assistant.tts_service import read_ses_ayarlari

        ayar = read_ses_ayarlari()
    except Exception:
        ayar = {}

    plans = {}
    for k in ("muhabbet", "alim", "tilavet", "asistan"):
        try:
            p = resolve_dub_omurga(k, voice_mode="auto", ayar=ayar)
            plans[k] = {
                "tavan": p.get("tavan"),
                "use_clone": p.get("use_clone"),
                "speaker": p.get("speaker_name"),
                "rate": p.get("rate"),
                "edge_voice": p.get("edge_voice"),
            }
        except Exception as exc:
            plans[k] = {"error": str(exc)[:80]}

    return {
        "enabled": dublaj_enabled(),
        "ffmpeg": ffmpeg_available(),
        "max_segments": max_dub_segments(),
        "max_duration_sec": max_dub_duration_sec(),
        "xtts": xtts_runtime_available(),
        "version": DUBLAJ_VERSION,
        "v1": {"omurga": True, "iptal_vram": True, "kalite_mux": True},
        "omurga_plans": plans,
        "iptal": iptal_snap(),
        "vram": vram_snap(),
        "hint_tr": (
            "V1.2: omurga + iptal/VRAM + kalite mux (loudnorm, soft_fit, "
            "mix_original=1 ile kısık orijinal+dublaj). Kısa klip; tek anlatıcı."
        ),
    }
