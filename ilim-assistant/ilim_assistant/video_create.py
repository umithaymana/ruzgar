# Created by Ümit & Gökçenur
"""
Metinden video oluşturma (V5) — sahne planı, Edge-TTS, sinematik FFmpeg montaj.

Gerçekçi beklenti: slayt + seslendirme + profesyonel kurgu (Ken Burns, geçiş, intro).
Tam AI sinema (Runway/Sora) kapsam dışı.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ilim_assistant.llm_ollama import chat_completion
from ilim_assistant.video_ffmpeg import (
    DEFAULT_FFMPEG_TIMEOUT,
    export_directory,
    ffmpeg_available,
    ffprobe_json,
    run_ffmpeg_args,
    summarize_probe,
)

# --- Preset ve kalite profilleri ---

PRESETS: dict[str, dict[str, int]] = {
    "16:9": {"width": 1920, "height": 1080, "fps": 30},
    "9:16": {"width": 1080, "height": 1920, "fps": 30},
    "1:1": {"width": 1080, "height": 1080, "fps": 30},
}

QUALITY_PROFILES: dict[str, dict[str, str | int]] = {
    "high": {"crf": 18, "preset": "medium", "audio_bitrate": "256k"},
    "balanced": {"crf": 20, "preset": "fast", "audio_bitrate": "192k"},
}

MOOD_COLORS: dict[str, str] = {
    "huzur": "0x1a1a2e",
    "heyecan": "0x3d1f0a",
    "hüzün": "0x1e1e28",
    "huzun": "0x1e1e28",
    "umut": "0x0f2027",
    "saygı": "0x2c1810",
    "saygi": "0x2c1810",
    "merak": "0x162447",
    "sevinç": "0x1a2a1a",
    "sevinc": "0x1a2a1a",
    "korku": "0x0d0d0d",
    "neutral": "0x141820",
}

_XFADE_SEC = 0.45
_INTRO_SEC = 3.0
_OUTRO_SEC = 2.5

# V7.1 — yerel sinematik hareket (FFmpeg zoompan; API yok)
MOTION_STYLES = frozenset({"ken_burns", "zoom_in", "zoom_out", "pan_left", "pan_right", "drift", "static"})

DEFAULT_VIDEO_IMAGES_DIR = "ilim-assistant/arsiv/video_gorseller"
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP")


def _dir_has_images(directory: Path) -> bool:
    for ext in _IMAGE_EXTS:
        if any(directory.glob(f"*{ext}")):
            return True
    return False


def resolve_images_dir_rel(
    rel_images_dir: str,
    user_assets: list[dict[str, Any]] | None,
    *,
    workspace_root: Path,
    default_dir: str = DEFAULT_VIDEO_IMAGES_DIR,
) -> str:
    """Form, asset yolları veya varsayılan klasörden görsel dizinini çöz."""
    explicit = (rel_images_dir or "").strip().replace("\\", "/").lstrip("/")
    if explicit:
        base = (workspace_root / explicit).resolve()
        if base.is_dir():
            return explicit

    parent_dirs: set[str] = set()
    for asset in user_assets or []:
        if not isinstance(asset, dict):
            continue
        rel = str(asset.get("rel") or "").strip().replace("\\", "/").lstrip("/")
        if "/" in rel:
            parent_dirs.add("/".join(rel.split("/")[:-1]))
    if len(parent_dirs) == 1:
        return next(iter(parent_dirs))

    default = (default_dir or DEFAULT_VIDEO_IMAGES_DIR).strip().replace("\\", "/").lstrip("/")
    base = (workspace_root / default).resolve()
    if base.is_dir() and _dir_has_images(base):
        return default
    return explicit or default


def discover_user_assets(
    workspace_root: Path,
    rel_images_dir: str,
    *,
    max_count: int = 12,
) -> list[dict[str, Any]]:
    """001.png … sıralı görselleri asset listesine dönüştür."""
    rel = (rel_images_dir or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        return []
    base = (workspace_root / rel).resolve()
    if not base.is_dir():
        return []

    assets: list[dict[str, Any]] = []
    for i in range(1, max(1, int(max_count or 12)) + 1):
        aid = f"{i:03d}"
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            cand = base / f"{aid}{ext}"
            if cand.is_file():
                assets.append(
                    {
                        "id": aid,
                        "rel": f"{rel}/{aid}{ext}",
                        "note": f"Sahne görseli {i}",
                    }
                )
                break
    return assets


def suggest_render_mode(plan_or_board: dict[str, Any], *, has_images: bool) -> str:
    rec = str(plan_or_board.get("render_recommendation") or "").strip().lower()
    if rec == "generative":
        try:
            from ilim_assistant.video_generative import generative_available

            if generative_available() and has_images:
                return "generative"
        except Exception:
            pass
        return "motion" if has_images else "slideshow"
    if rec == "portrait":
        try:
            from ilim_assistant.video_portrait import portrait_available

            if portrait_available() and has_images:
                return "portrait"
        except Exception:
            pass
        return "motion" if has_images else "slideshow"
    if rec in ("motion", "slideshow"):
        return rec
    return "motion" if has_images else "slideshow"


def video_render_capabilities() -> dict[str, Any]:
    """UI / health için render modu durumu."""
    caps: dict[str, Any] = {
        "slideshow": True,
        "motion": True,
        "portrait": False,
        "generative": False,
    }
    try:
        from ilim_assistant.video_portrait import portrait_status

        caps["portrait"] = bool(portrait_status().get("available"))
    except Exception:
        pass
    try:
        from ilim_assistant.video_generative import generative_status

        caps["generative"] = bool(generative_status().get("available"))
    except Exception:
        pass
    return caps


def _resolve_motion_style(scene: dict[str, Any], render_mode: str) -> str:
    """Storyboard motion_prompt/action → yerel hareket profili."""
    mode = (render_mode or "motion").strip().lower()
    if mode == "slideshow":
        return "static"
    blob = " ".join(
        [
            str(scene.get("motion_prompt") or ""),
            str(scene.get("action") or ""),
            str(scene.get("visual_prompt") or ""),
        ]
    ).lower()
    if any(k in blob for k in ("pan left", "sola kay", "sola", "left pan", "slide left")):
        return "pan_left"
    if any(k in blob for k in ("pan right", "sağa kay", "saga", "right pan", "slide right")):
        return "pan_right"
    if any(k in blob for k in ("zoom out", "uzakla", "pull back", "geriye")):
        return "zoom_out"
    if any(k in blob for k in ("drift", "float", "süzül", "suzul", "rüzgar", "ruzgar")):
        return "drift"
    if any(k in blob for k in ("zoom in", "yakınla", "yakinla", "push in", "close")):
        return "zoom_in"
    return "ken_burns"


def _build_zoompan_filter(
    style: str,
    *,
    frames: int,
    width: int,
    height: int,
    fps: int,
) -> str:
    d = max(int(frames), fps * 2)
    base = f"d={d}:s={width}x{height}:fps={fps}"
    if style == "static":
        z = "1.06"
        return f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':{base}"
    if style == "zoom_in":
        return f"zoompan=z='min(zoom+0.0013,1.24)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':{base}"
    if style == "zoom_out":
        return (
            "zoompan=z='if(eq(on,1),1.22,max(zoom-0.0011,1.04))'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':{base}"
        )
    if style == "pan_left":
        return f"zoompan=z='1.16':x='iw/2-(iw/zoom/2)-on*2.2':y='ih/2-(ih/zoom/2)':{base}"
    if style == "pan_right":
        return f"zoompan=z='1.16':x='iw/2-(iw/zoom/2)+on*2.2':y='ih/2-(ih/zoom/2)':{base}"
    if style == "drift":
        return (
            "zoompan=z='min(zoom+0.0007,1.12)'"
            f":x='iw/2-(iw/zoom/2)+sin(on/48)*12':y='ih/2-(ih/zoom/2)+cos(on/64)*8':{base}"
        )
    return f"zoompan=z='min(zoom+0.0009,1.14)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':{base}"


@dataclass
class CreateVideoResult:
    ok: bool
    output_rel: str = ""
    plan_rel: str = ""
    scene_count: int = 0
    total_duration_sec: float = 0.0
    error: str = ""
    plan: dict[str, Any] | None = None
    render_notes: list[str] = field(default_factory=list)


def _extract_json(text: str) -> str:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("Model çıktısında JSON bulunamadı.")
    return m.group(0)


def _normalize_plan(raw: dict[str, Any]) -> dict[str, Any]:
    scenes = raw.get("scenes") or []
    out_scenes: list[dict[str, Any]] = []
    for i, sc in enumerate(scenes):
        if not isinstance(sc, dict):
            continue
        sid = int(sc.get("scene_id") or i + 1)
        narration = str(sc.get("narration") or sc.get("text") or "").strip()
        if not narration:
            continue
        mood = str(sc.get("mood") or "neutral").strip().lower()
        out_scenes.append(
            {
                "scene_id": sid,
                "narration": narration,
                "mood": mood,
                "visual_prompt": str(sc.get("visual_prompt") or "").strip(),
                "estimated_seconds": float(sc.get("estimated_seconds") or 60),
                "transition": str(sc.get("transition") or "fade").strip().lower(),
            }
        )
    title = str(raw.get("title") or raw.get("project_title") or "").strip()
    return {"title": title, "scenes": out_scenes}


def plan_video_scenes(
    full_text: str,
    theme: str,
    *,
    max_scenes: int = 24,
    project_title: str = "",
) -> dict[str, Any]:
    """LLM ile sinematik sahne planı (Ollama / OpenAI uyumlu)."""
    text = (full_text or "").strip()
    if len(text) < 20:
        raise ValueError("Metin en az 20 karakter olmalı.")
    theme_s = (theme or "genel anlatım").strip()
    cap = max(3, min(int(max_scenes or 24), 40))

    system = f"""Sen ödüllü bir belgesel yönetmeni ve kurgu editörüsün.
Görev: verilen metni sinematik sahnelere böl; ritim, nefes ve duygusal yay çiz.

Her sahne için JSON alanları:
- scene_id: sıra (1…)
- narration: seslendirilecek metin (orijinalden; gereksiz tekrar yok; akıcı Türkçe)
- mood: huzur | heyecan | hüzün | umut | saygı | merak | sevinç | korku | neutral
- visual_prompt: görsel tasviri (ışık, renk, mekân — kısa)
- estimated_seconds: 25–90 arası makul süre
- transition: fade | dissolve | cut (sahne geçişi; çoğu fade)

Kurgu kuralları:
- Açılış sahnesi kısa ve çekici; kapanış sahnesi toparlayıcı.
- Cümle ortasında kesme; anlam bütünlüğü koru.
- Toplam sahne sayısı en fazla {cap}.
- Uzun metinde tempoyu çeşitlendir (kısa + orta sahneler).

Çıktı yalnızca geçerli JSON:
{{"title": "...", "scenes": [{{...}}, ...]}}"""

    user = f"Tema: {theme_s}\n"
    if project_title:
        user += f"Proje başlığı: {project_title}\n"
    user += f"\nMetin:\n{text[:12000]}"

    raw_reply = chat_completion(system, user)
    if raw_reply.startswith("[HTTP") or raw_reply.startswith("Ollama") or raw_reply.startswith("LLM hatası"):
        raise RuntimeError(raw_reply)
    parsed = json.loads(_extract_json(raw_reply))
    plan = _normalize_plan(parsed)
    if not plan["scenes"]:
        raise ValueError("Plan boş — model sahne üretemedi.")
    if not plan["title"] and project_title:
        plan["title"] = project_title
    return plan


def _mood_color(mood: str) -> str:
    key = (mood or "neutral").strip().lower()
    key = key.replace("ü", "u").replace("ı", "i").replace("ö", "o").replace("ş", "s").replace("ç", "c").replace("ğ", "g")
    for k, v in MOOD_COLORS.items():
        kk = k.replace("ü", "u").replace("ı", "i")
        if key == kk or key.startswith(kk):
            return v
    return MOOD_COLORS["neutral"]


def _find_scene_image(
    workspace_root: Path,
    images_dir_rel: str,
    scene_id: int,
    fallback: Path | None,
    asset_id: str = "",
) -> Path | None:
    """Klasörde asset_id (001) veya scene_id sırasına göre görsel arar."""
    rel = (images_dir_rel or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        return fallback
    base = (workspace_root / rel).resolve()
    if not base.is_dir():
        return fallback
    sid = int(scene_id)
    names: list[str] = []
    aid = (asset_id or "").strip()
    if aid:
        names.append(aid)
        if aid.isdigit():
            names.append(f"{int(aid):03d}")
    names.extend((f"{sid:03d}", f"scene_{sid}"))
    seen: set[str] = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG"):
            cand = base / f"{name}{ext}"
            if cand.is_file():
                return cand
    return fallback


def _win_font_path() -> str | None:
    candidates = [
        os.environ.get("RUZGAR_VIDEO_FONT", "").strip(),
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c).resolve().as_posix().replace(":", "\\:")
    return None


def _escape_drawtext(s: str) -> str:
    s = s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")
    return s[:80]


def _audio_duration_sec(path: Path) -> float:
    data = ffprobe_json(path)
    return float(summarize_probe(data).get("duration_sec") or 0.0)


def _mp3_to_wav(mp3: Path, wav: Path) -> None:
    wav.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(mp3.resolve()),
            "-ar",
            "48000",
            "-ac",
            "2",
            str(wav.resolve()),
        ],
        timeout_sec=300,
    )


def _synthesize_wav_sync(
    text: str,
    out_wav: Path,
    *,
    voice: str,
    rate: str,
    pitch: str,
) -> Path:
    """
    Edge-TTS → WAV (senkron, ProcessPool).
    FastAPI run_in_threadpool içinden güvenli — asyncio/run_in_threadpool iç içe DEĞİL.
    """
    from ilim_assistant.tts_service import (
        _edge_synth_mp3_bytes,
        edge_available,
        get_tts_process_pool,
    )

    if not edge_available():
        raise RuntimeError("Edge-TTS yok: pip install edge-tts")
    to = float(os.environ.get("RUZGAR_TTS_MP_TIMEOUT", "120"))
    pool = get_tts_process_pool()
    data = pool.submit(
        _edge_synth_mp3_bytes,
        (text.strip(), voice, rate, pitch),
    ).result(timeout=to)
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    mp3_path = Path(tmp)
    try:
        mp3_path.write_bytes(data)
        _mp3_to_wav(mp3_path, out_wav)
        return out_wav
    finally:
        try:
            mp3_path.unlink(missing_ok=True)
        except OSError:
            pass


async def _synthesize_wav_async(
    text: str,
    out_wav: Path,
    *,
    voice: str,
    rate: str,
    pitch: str,
) -> Path:
    from ilim_assistant.tts_service import edge_available, synthesize_edge_mp3_in_process

    if not edge_available():
        raise RuntimeError("Edge-TTS yok: pip install edge-tts")
    mp3_out = await synthesize_edge_mp3_in_process(
        text.strip(),
        voice=voice,
        rate=rate,
        pitch=pitch,
        meta={"source": "video_create_v5"},
    )
    _mp3_to_wav(mp3_out, out_wav)
    try:
        mp3_out.unlink(missing_ok=True)
    except OSError:
        pass
    return out_wav


def _render_title_card(
    out_mp4: Path,
    *,
    title: str,
    subtitle: str,
    duration_sec: float,
    width: int,
    height: int,
    fps: int,
    color: str,
    crf: int,
    preset: str,
) -> None:
    """Intro/outro kartı — renk zemin + başlık."""
    dur = max(1.5, float(duration_sec))
    font = _win_font_path()
    title_esc = _escape_drawtext(title or "RÜZGAR")
    sub_esc = _escape_drawtext(subtitle or "")

    vf_parts = [
        f"scale={width}:{height}",
        "setsar=1",
        f"fade=t=in:st=0:d=0.5",
        f"fade=t=out:st={max(0.1, dur - 0.6):.2f}:d=0.5",
    ]
    if font:
        vf_parts.append(
            f"drawtext=fontfile='{font}':text='{title_esc}':fontcolor=white:fontsize=48:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-30:shadowcolor=black@0.5:shadowx=2:shadowy=2"
        )
        if sub_esc:
            vf_parts.append(
                f"drawtext=fontfile='{font}':text='{sub_esc}':fontcolor=white@0.85:fontsize=28:"
                f"x=(w-text_w)/2:y=(h-text_h)/2+40"
            )
    vf = ",".join(vf_parts)

    run_ffmpeg_args(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={width}x{height}:d={dur}:r={fps}",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=48000:cl=stereo:d={dur}",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            str(preset),
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out_mp4.resolve()),
        ],
        timeout_sec=600,
    )


def _render_scene_clip(
    out_mp4: Path,
    *,
    audio_wav: Path,
    width: int,
    height: int,
    fps: int,
    mood: str,
    background_image: Path | None,
    crf: int,
    preset: str,
    audio_bitrate: str,
    motion_style: str = "ken_burns",
) -> None:
    """Tek sahne: sinematik hareket (V7.1) + ses + fade."""
    dur = _audio_duration_sec(audio_wav)
    if dur < 0.5:
        dur = 5.0
    fade_in = min(0.7, dur * 0.08)
    fade_out = min(0.8, dur * 0.1)
    fade_out_st = max(fade_in + 0.1, dur - fade_out)
    frames = max(int(dur * fps), fps * 2)

    color = _mood_color(mood)
    pan_filter = _build_zoompan_filter(
        motion_style if motion_style in MOTION_STYLES else "ken_burns",
        frames=frames,
        width=width,
        height=height,
        fps=fps,
    )

    if background_image and background_image.is_file():
        vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{pan_filter}"
        vf += f",fade=t=in:st=0:d={fade_in:.2f},fade=t=out:st={fade_out_st:.2f}:d={fade_out:.2f}"
        run_ffmpeg_args(
            [
                "-y",
                "-loop",
                "1",
                "-i",
                str(background_image.resolve()),
                "-i",
                str(audio_wav.resolve()),
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-preset",
                str(preset),
                "-crf",
                str(crf),
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                str(audio_bitrate),
                "-af",
                "afade=t=in:st=0:d=0.3,afade=t=out:st="
                f"{max(0.1, dur - 0.35):.2f}:d=0.35,loudnorm=I=-16:TP=-1.5:LRA=11",
                "-shortest",
                "-movflags",
                "+faststart",
                str(out_mp4.resolve()),
            ],
            timeout_sec=max(600, int(dur * 8)),
        )
    else:
        vf = f"scale={width}:{height},setsar=1,{pan_filter}"
        vf += f",fade=t=in:st=0:d={fade_in:.2f},fade=t=out:st={fade_out_st:.2f}:d={fade_out:.2f}"
        run_ffmpeg_args(
            [
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s={width}x{height}:d={dur + 0.5}:r={fps}",
                "-i",
                str(audio_wav.resolve()),
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-preset",
                str(preset),
                "-crf",
                str(crf),
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                str(audio_bitrate),
                "-af",
                "afade=t=in:st=0:d=0.3,afade=t=out:st="
                f"{max(0.1, dur - 0.35):.2f}:d=0.35,loudnorm=I=-16:TP=-1.5:LRA=11",
                "-shortest",
                "-movflags",
                "+faststart",
                str(out_mp4.resolve()),
            ],
            timeout_sec=max(600, int(dur * 8)),
        )


def _concat_with_xfade(
    parts: list[Path],
    final_out: Path,
    *,
    crf: int,
    preset: str,
    audio_bitrate: str,
) -> None:
    """Parçaları xfade ile birleştirir (profesyonel geçiş)."""
    if len(parts) == 1:
        shutil.copy2(parts[0], final_out)
        return

    durations = [_audio_duration_sec(p) for p in parts]
    # video duration ≈ audio duration from probe
    for i, d in enumerate(durations):
        if d <= 0:
            durations[i] = 5.0

    n = len(parts)
    inputs: list[str] = []
    for p in parts:
        inputs.extend(["-i", str(p.resolve())])

    vf_parts: list[str] = []
    af_parts: list[str] = []
    v_prev = "[0:v]"
    a_prev = "[0:a]"
    offset = durations[0] - _XFADE_SEC

    for i in range(1, n):
        v_out = f"[v{i}]" if i < n - 1 else "[vout]"
        a_out = f"[a{i}]" if i < n - 1 else "[aout]"
        vf_parts.append(
            f"{v_prev}[{i}:v]xfade=transition=fade:duration={_XFADE_SEC}:offset={max(0.1, offset):.3f}{v_out}"
        )
        af_parts.append(
            f"{a_prev}[{i}:a]acrossfade=d={_XFADE_SEC}:c1=tri:c2=tri{a_out}"
        )
        v_prev = v_out
        a_prev = a_out
        offset += durations[i] - _XFADE_SEC

    fc = ";".join(vf_parts + af_parts)
    run_ffmpeg_args(
        inputs
        + [
            "-filter_complex",
            fc,
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-preset",
            str(preset),
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            str(audio_bitrate),
            "-movflags",
            "+faststart",
            "-y",
            str(final_out.resolve()),
        ],
        timeout_sec=DEFAULT_FFMPEG_TIMEOUT,
    )


def _concat_simple(parts: list[Path], final_out: Path) -> None:
    """xfade başarısız olursa yedek: concat demuxer."""
    lst = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    try:
        for p in parts:
            safe = str(p.resolve()).replace("'", "'\\''")
            lst.write(f"file '{safe}'\n")
        lst.close()
        run_ffmpeg_args(
            [
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                lst.name,
                "-c",
                "copy",
                str(final_out.resolve()),
            ],
            timeout_sec=DEFAULT_FFMPEG_TIMEOUT,
        )
    finally:
        Path(lst.name).unlink(missing_ok=True)


def save_plan_file(plan: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def _render_scene_for_plan(
    out_mp4: Path,
    *,
    scene: dict[str, Any],
    scene_id: int,
    audio_wav: Path,
    background_image: Path | None,
    render_mode: str,
    width: int,
    height: int,
    fps: int,
    mood: str,
    crf: int,
    preset: str,
    audio_bitrate: str,
    render_notes: list[str],
) -> None:
    """V7.1 motion · V7.2 portrait · V8 generative — başarısızsa motion yedeği."""
    mode = (render_mode or "motion").strip().lower()
    sid = int(scene_id)

    if mode == "portrait" and background_image:
        try:
            from ilim_assistant.video_portrait import portrait_available, render_portrait_scene, scene_wants_portrait

            if portrait_available() and scene_wants_portrait(scene):
                render_portrait_scene(
                    background_image,
                    audio_wav,
                    out_mp4,
                    width=width,
                    height=height,
                    crf=crf,
                    preset=preset,
                )
                return
        except Exception as e:
            render_notes.append(f"Sahne {sid}: portre → hareket yedeği ({e})")

    if mode == "generative":
        try:
            from ilim_assistant.video_generative import (
                generative_available,
                render_generative_scene,
                scene_generative_prompt,
            )

            if generative_available():
                render_generative_scene(
                    background_image,
                    scene_generative_prompt(scene),
                    audio_wav,
                    out_mp4,
                    width=width,
                    height=height,
                    crf=crf,
                    preset=preset,
                )
                return
        except Exception as e:
            render_notes.append(f"Sahne {sid}: AI klip → hareket yedeği ({e})")

    motion = _resolve_motion_style(scene, render_mode if mode == "slideshow" else "motion")
    if mode == "slideshow":
        motion = "static"
    _render_scene_clip(
        out_mp4,
        audio_wav=audio_wav,
        width=width,
        height=height,
        fps=fps,
        mood=mood,
        background_image=background_image,
        crf=crf,
        preset=preset,
        audio_bitrate=audio_bitrate,
        motion_style=motion,
    )


def render_video_from_plan(
    plan: dict[str, Any],
    *,
    workspace_root: Path,
    preset_key: str = "16:9",
    quality_key: str = "high",
    voice: str,
    rate: str,
    pitch: str,
    background_rel: str = "",
    images_dir_rel: str = "",
    render_mode: str = "motion",
    intro_title: str = "",
    outro_title: str = "",
    project_slug: str = "",
) -> CreateVideoResult:
    """Plan + TTS + montaj → MP4."""
    if not ffmpeg_available():
        return CreateVideoResult(ok=False, error="ffmpeg bulunamadı.")

    preset = PRESETS.get(preset_key) or PRESETS["16:9"]
    qual = QUALITY_PROFILES.get(quality_key) or QUALITY_PROFILES["high"]
    w, h, fps = int(preset["width"]), int(preset["height"]), int(preset["fps"])
    crf = int(qual["crf"])
    enc_preset = str(qual["preset"])
    abr = str(qual["audio_bitrate"])

    scenes = plan.get("scenes") or []
    if not scenes:
        return CreateVideoResult(ok=False, error="Plan içinde sahne yok.")

    bg_path: Path | None = None
    if background_rel.strip():
        cand = (workspace_root / background_rel.strip().replace("\\", "/").lstrip("/")).resolve()
        if cand.is_file():
            bg_path = cand

    slug = project_slug or uuid.uuid4().hex[:10]
    out_dir = export_directory(workspace_root)
    work = Path(tempfile.mkdtemp(prefix=f"ruzgar_vid_{slug}_"))
    audio_dir = work / "audio"
    parts_dir = work / "parts"
    audio_dir.mkdir(parents=True, exist_ok=True)
    parts_dir.mkdir(parents=True, exist_ok=True)

    plan_path = out_dir / f"ruzgar_plan_{slug}.json"
    save_plan_file(plan, plan_path)
    plan_rel = plan_path.relative_to(workspace_root.resolve()).as_posix()

    parts: list[Path] = []
    title = intro_title or str(plan.get("title") or "").strip()
    render_notes: list[str] = []
    mode_key = (render_mode or "motion").strip().lower()
    if mode_key == "portrait":
        try:
            from ilim_assistant.video_portrait import portrait_available

            if not portrait_available():
                render_notes.append("V7.2 SadTalker yapılandırılmadı — sinematik hareket yedeği kullanıldı.")
        except Exception:
            render_notes.append("V7.2 portre modu kullanılamadı — hareket yedeği.")
    elif mode_key == "generative":
        try:
            from ilim_assistant.video_generative import generative_available

            if not generative_available():
                render_notes.append("V8 Runway API anahtarı yok — sinematik hareket yedeği kullanıldı.")
        except Exception:
            render_notes.append("V8 generative modu kullanılamadı — hareket yedeği.")

    try:
        # Intro kartı
        if title:
            intro_mp4 = parts_dir / "000_intro.mp4"
            _render_title_card(
                intro_mp4,
                title=title,
                subtitle=str(plan.get("theme") or ""),
                duration_sec=_INTRO_SEC,
                width=w,
                height=h,
                fps=fps,
                color=MOOD_COLORS["neutral"],
                crf=crf,
                preset=enc_preset,
            )
            parts.append(intro_mp4)

        # Sahne sesleri + klipler (senkron TTS — API threadpool uyumlu)
        wavs: list[Path] = []
        for i, sc in enumerate(scenes):
            sid = int(sc.get("scene_id") or i + 1)
            narration = str(sc.get("narration") or "").strip()
            wav = audio_dir / f"{sid:03d}.wav"
            _synthesize_wav_sync(
                narration,
                wav,
                voice=voice,
                rate=rate,
                pitch=pitch,
            )
            wavs.append(wav)

        for i, sc in enumerate(scenes):
            sid = int(sc.get("scene_id") or i + 1)
            mood = str(sc.get("mood") or "neutral")
            part = parts_dir / f"part_{sid:03d}.mp4"
            asset_id = str(sc.get("asset_id") or "").strip()
            scene_bg = _find_scene_image(
                workspace_root, images_dir_rel, sid, bg_path, asset_id=asset_id
            )
            _render_scene_for_plan(
                part,
                scene=sc,
                scene_id=sid,
                audio_wav=wavs[i],
                background_image=scene_bg,
                render_mode=render_mode,
                width=w,
                height=h,
                fps=fps,
                mood=mood,
                crf=crf,
                preset=enc_preset,
                audio_bitrate=abr,
                render_notes=render_notes,
            )
            parts.append(part)

        # Outro
        outro_text = outro_title or "RÜZGAR"
        outro_mp4 = parts_dir / "999_outro.mp4"
        _render_title_card(
            outro_mp4,
            title=outro_text,
            subtitle="",
            duration_sec=_OUTRO_SEC,
            width=w,
            height=h,
            fps=fps,
            color=_mood_color("saygi"),
            crf=crf,
            preset=enc_preset,
        )
        parts.append(outro_mp4)

        final_name = f"ruzgar_create_{slug}.mp4"
        final_path = out_dir / final_name

        try:
            _concat_with_xfade(
                parts,
                final_path,
                crf=crf,
                preset=enc_preset,
                audio_bitrate=abr,
            )
        except Exception:
            _concat_simple(parts, final_path)

        total_dur = _audio_duration_sec(final_path)
        rel_out = final_path.relative_to(workspace_root.resolve()).as_posix()
        return CreateVideoResult(
            ok=True,
            output_rel=rel_out,
            plan_rel=plan_rel,
            scene_count=len(scenes),
            total_duration_sec=total_dur,
            plan=plan,
            render_notes=render_notes,
        )
    except Exception as e:
        return CreateVideoResult(ok=False, error=str(e), plan_rel=plan_rel, plan=plan)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def create_video_from_text(
    text: str,
    theme: str,
    *,
    workspace_root: Path,
    preset_key: str = "16:9",
    quality_key: str = "high",
    voice: str,
    rate: str,
    pitch: str,
    max_scenes: int = 24,
    project_title: str = "",
    background_rel: str = "",
    images_dir_rel: str = "",
    render_mode: str = "motion",
    intro_title: str = "",
    outro_title: str = "",
    existing_plan: dict[str, Any] | None = None,
) -> CreateVideoResult:
    """Tam akış: plan (isteğe bağlı atla) → render."""
    plan = existing_plan
    if plan is None:
        try:
            plan = plan_video_scenes(
                text,
                theme,
                max_scenes=max_scenes,
                project_title=project_title,
            )
        except Exception as e:
            return CreateVideoResult(ok=False, error=str(e))
    if theme and not plan.get("theme"):
        plan["theme"] = theme

    slug = re.sub(r"[^\w\-]+", "_", (project_title or plan.get("title") or "film"))[:32].strip("_") or uuid.uuid4().hex[:8]
    return render_video_from_plan(
        plan,
        workspace_root=workspace_root,
        preset_key=preset_key,
        quality_key=quality_key,
        voice=voice,
        rate=rate,
        pitch=pitch,
        background_rel=background_rel,
        images_dir_rel=images_dir_rel,
        render_mode=render_mode,
        intro_title=intro_title or str(plan.get("title") or ""),
        outro_title=outro_title,
        project_slug=slug,
    )
