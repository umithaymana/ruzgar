# Created by Ümit & Gökçenur
"""V1.2 — Video dublaj kalite mux: normalize, orijinal+dublaj miks, süre yumuşatma.

Boot / yüz / hub dokunulmaz. FFmpeg zorunlu.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

MUX_VERSION = "ses-v1-dub-kalite-mux-v1-2026-11-21"

# Soft tempo penceresi (atempo tek geçiş 0.5–2.0; biz dar tutuyoruz)
ATEMPO_MIN = 0.87
ATEMPO_MAX = 1.15
# Genel sohbet dublaj loudness hedefi (LUFS yaklaşık)
LOUDNORM_I = -16.0
LOUDNORM_TP = -1.5
LOUDNORM_LRA = 11.0
# Orijinal iz varsayılan duck (dB)
DEFAULT_ORIG_DUCK_DB = -16.0


def mux_enabled() -> bool:
    return os.environ.get("RUZGAR_DUB_V12_MUX", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def soft_fit_ratio(src_sec: float, slot_sec: float) -> float:
    """Kaynak/slot → atempo oranı (1.0 = dokunma)."""
    if src_sec <= 0.05 or slot_sec <= 0.05:
        return 1.0
    # atempo: çıktı süresi ≈ src/tempo → tempo = src/slot
    return float(src_sec) / float(slot_sec)


def plan_soft_fit(src_sec: float, slot_sec: float) -> dict[str, Any]:
    """
    Süre kayması planı:
    - oran ATEMPO penceresinde → atempo
    - kaynak kısa → pad
    - kaynak uzun → soft atempo max + atrim
    """
    if src_sec <= 0.05 or slot_sec <= 0.05:
        return {"action": "copy", "tempo": 1.0, "pad_sec": 0.0, "trim_sec": None}
    ratio = soft_fit_ratio(src_sec, slot_sec)
    if ATEMPO_MIN <= ratio <= ATEMPO_MAX:
        return {
            "action": "atempo",
            "tempo": ratio,
            "pad_sec": 0.0,
            "trim_sec": float(slot_sec),
            "ratio": ratio,
        }
    if ratio < ATEMPO_MIN:
        # Çok kısa: yavaşlat (min) + pad
        after = src_sec / ATEMPO_MIN
        pad = max(0.0, slot_sec - after)
        return {
            "action": "atempo_pad",
            "tempo": ATEMPO_MIN,
            "pad_sec": pad,
            "trim_sec": float(slot_sec),
            "ratio": ratio,
        }
    # Çok uzun: hızlandır (max) + trim
    return {
        "action": "atempo_trim",
        "tempo": ATEMPO_MAX,
        "pad_sec": 0.0,
        "trim_sec": float(slot_sec),
        "ratio": ratio,
    }


def soft_fit_audio_duration(
    src: Path,
    dst: Path,
    slot_sec: float,
    *,
    sample_rate: int = 22050,
) -> dict[str, Any]:
    """Segmenti slot süresine yumuşak uydur (atempo + pad/trim)."""
    from ilim_assistant.video_ffmpeg import audio_duration_sec, run_ffmpeg_args

    src_p = Path(src)
    dst_p = Path(dst)
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    src_sec = audio_duration_sec(src_p)
    plan = plan_soft_fit(src_sec, float(slot_sec))
    if plan["action"] == "copy" or abs(src_sec - float(slot_sec)) < 0.04:
        shutil.copy2(src_p, dst_p)
        return {**plan, "src_sec": src_sec, "out_sec": audio_duration_sec(dst_p), "copied": True}

    tempo = float(plan["tempo"])
    filters: list[str] = []
    if abs(tempo - 1.0) >= 0.01:
        # zincir: atempo yalnız 0.5–2.0
        t = tempo
        while t > 2.0:
            filters.append("atempo=2.0")
            t /= 2.0
        while t < 0.5:
            filters.append("atempo=0.5")
            t /= 0.5
        filters.append(f"atempo={t:.4f}")
    pad = float(plan.get("pad_sec") or 0.0)
    if pad >= 0.04:
        filters.append(f"apad=pad_dur={pad:.3f}")
    trim = plan.get("trim_sec")
    if trim is not None and float(trim) > 0.05:
        filters.append(f"atrim=0:{float(trim):.3f}")
        filters.append("asetpts=PTS-STARTPTS")
    if not filters:
        shutil.copy2(src_p, dst_p)
        return {**plan, "src_sec": src_sec, "copied": True}

    af = ",".join(filters)
    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(src_p.resolve()),
            "-af",
            af,
            "-ar",
            str(int(sample_rate)),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dst_p.resolve()),
        ],
        timeout_sec=180,
    )
    return {
        **plan,
        "src_sec": src_sec,
        "out_sec": audio_duration_sec(dst_p),
        "filter": af,
        "copied": False,
    }


def normalize_loudness(
    src: Path,
    dst: Path,
    *,
    target_i: float = LOUDNORM_I,
    true_peak: float = LOUDNORM_TP,
    lra: float = LOUDNORM_LRA,
    sample_rate: int = 22050,
) -> dict[str, Any]:
    """Loudness + peak dengeleme (loudnorm; başarısızsa dynaudnorm)."""
    from ilim_assistant.video_ffmpeg import run_ffmpeg_args

    src_p = Path(src)
    dst_p = Path(dst)
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    ln = (
        f"loudnorm=I={target_i:.1f}:TP={true_peak:.1f}:LRA={lra:.1f}:"
        f"print_format=summary"
    )
    try:
        run_ffmpeg_args(
            [
                "-y",
                "-i",
                str(src_p.resolve()),
                "-af",
                ln,
                "-ar",
                str(int(sample_rate)),
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(dst_p.resolve()),
            ],
            timeout_sec=300,
        )
        return {"ok": True, "method": "loudnorm", "I": target_i, "TP": true_peak}
    except Exception as exc:
        # Yedek: dynaudnorm + alimiter
        try:
            run_ffmpeg_args(
                [
                    "-y",
                    "-i",
                    str(src_p.resolve()),
                    "-af",
                    "dynaudnorm=f=150:g=15,alimiter=limit=0.95",
                    "-ar",
                    str(int(sample_rate)),
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    str(dst_p.resolve()),
                ],
                timeout_sec=300,
            )
            return {
                "ok": True,
                "method": "dynaudnorm",
                "note": str(exc)[:120],
            }
        except Exception as exc2:
            shutil.copy2(src_p, dst_p)
            return {"ok": False, "method": "copy", "error": str(exc2)[:160]}


def db_to_linear(db: float) -> float:
    return float(10 ** (float(db) / 20.0))


def mix_dub_over_original(
    original: Path,
    dub: Path,
    dst: Path,
    *,
    orig_duck_db: float = DEFAULT_ORIG_DUCK_DB,
    dub_gain_db: float = 0.0,
    sample_rate: int = 22050,
) -> dict[str, Any]:
    """
    Kısık orijinal + dublaj amix.
    duration=first → dublaj süresi esas; orijinal ezilmeden duyulur.
    """
    from ilim_assistant.video_ffmpeg import audio_duration_sec, run_ffmpeg_args

    orig_p = Path(original)
    dub_p = Path(dub)
    dst_p = Path(dst)
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    ov = db_to_linear(orig_duck_db)
    dv = db_to_linear(dub_gain_db)
    # duration=first: ilk girdi = dublaj (map sırası)
    filt = (
        f"[0:a]volume={dv:.4f},aformat=sample_rates={sample_rate}:channel_layouts=mono[d];"
        f"[1:a]volume={ov:.4f},aformat=sample_rates={sample_rate}:channel_layouts=mono[o];"
        f"[d][o]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[a]"
    )
    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(dub_p.resolve()),
            "-i",
            str(orig_p.resolve()),
            "-filter_complex",
            filt,
            "-map",
            "[a]",
            "-ar",
            str(int(sample_rate)),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dst_p.resolve()),
        ],
        timeout_sec=300,
    )
    return {
        "ok": True,
        "orig_duck_db": orig_duck_db,
        "dub_gain_db": dub_gain_db,
        "out_sec": audio_duration_sec(dst_p),
        "method": "amix_duck",
    }


def extract_media_audio_wav(
    media: Path,
    dst: Path,
    *,
    sample_rate: int = 22050,
) -> Path:
    from ilim_assistant.video_ffmpeg import run_ffmpeg_args

    dst_p = Path(dst)
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(Path(media).resolve()),
            "-vn",
            "-ar",
            str(int(sample_rate)),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dst_p.resolve()),
        ],
        timeout_sec=300,
    )
    return dst_p


def apply_quality_mux(
    dub_wav: Path,
    *,
    media_path: Path | None = None,
    mix_original: bool = False,
    orig_duck_db: float | None = None,
    normalize: bool = True,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    """
    V1.2 son adım: normalize (±) isteğe bağlı orijinal miks.
    Dönüş: {ok, audio_path, steps, version}
    """
    if not mux_enabled():
        return {
            "ok": True,
            "audio_path": Path(dub_wav),
            "skipped": True,
            "version": MUX_VERSION,
        }

    owned = False
    if work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="ruzgar_v12_"))
        owned = True
    steps: list[dict[str, Any]] = []
    cur = Path(dub_wav)
    try:
        if normalize:
            norm_out = work_dir / "dub_norm.wav"
            info = normalize_loudness(cur, norm_out)
            steps.append({"normalize": info})
            if norm_out.is_file() and norm_out.stat().st_size > 64:
                cur = norm_out

        mixed = False
        if mix_original and media_path is not None and Path(media_path).is_file():
            duck = (
                DEFAULT_ORIG_DUCK_DB
                if orig_duck_db is None
                else float(orig_duck_db)
            )
            try:
                orig_wav = work_dir / "orig.wav"
                extract_media_audio_wav(Path(media_path), orig_wav)
                mix_out = work_dir / "dub_mix.wav"
                minfo = mix_dub_over_original(
                    orig_wav, cur, mix_out, orig_duck_db=duck
                )
                steps.append({"mix": minfo})
                if mix_out.is_file() and mix_out.stat().st_size > 64:
                    cur = mix_out
                    mixed = True
            except Exception as exc:
                steps.append({"mix_error": str(exc)[:160]})

        # Kalıcı çıktıya kopyala (aynı isim üzerine)
        final = Path(dub_wav)
        if cur.resolve() != final.resolve():
            shutil.copy2(cur, final)
        return {
            "ok": True,
            "audio_path": final,
            "normalized": bool(normalize),
            "mixed": mixed,
            "steps": steps,
            "version": MUX_VERSION,
        }
    finally:
        if owned:
            try:
                for f in work_dir.glob("*"):
                    try:
                        f.unlink(missing_ok=True)
                    except OSError:
                        pass
                work_dir.rmdir()
            except OSError:
                pass
