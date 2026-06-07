# Created by Ümit & Gökçenur
"""
Faz S4 — XTTS ses klonlama köprüsü (ilim-voice / Coqui TTS).

Referans ses: 30–120 sn temiz .wav/.mp3 → `arsiv/ses-referans/{profil}.wav`
Kapat: RUZGAR_TTS_CLONE=0
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.ses_motoru import SesKarakteri, normalize_ses_karakteri

MIMAR = "Ümit & Gökçenur"
KLON_VERSION = "ses-klon-s4-2026-06-06"

_ILIM_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _ILIM_ROOT.parent

ISO_TO_NLLB: dict[str, str] = {
    "tr": "tur_Latn",
    "en": "eng_Latn",
    "ar": "arb_Arab",
    "fa": "pes_Arab",
    "de": "deu_Latn",
    "fr": "fra_Latn",
    "ru": "rus_Cyrl",
    "id": "ind_Latn",
}

_XTTS_MODEL = os.environ.get(
    "XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2"
)


def clone_enabled() -> bool:
    return os.environ.get("RUZGAR_TTS_CLONE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def clone_max_chars() -> int:
    try:
        return max(80, int(os.environ.get("RUZGAR_TTS_CLONE_MAX_CHARS", "2500")))
    except ValueError:
        return 2500


def referans_klasoru() -> Path:
    custom = os.environ.get("RUZGAR_SES_REFERANS_DIR", "").strip()
    if custom:
        p = Path(custom)
        if not p.is_absolute():
            p = (_REPO_ROOT / custom).resolve()
    else:
        p = (_ILIM_ROOT / "arsiv" / "ses-referans").resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _ilim_voice_root() -> Path | None:
    raw = os.environ.get("RUZGAR_ILIM_VOICE_ROOT", "").strip()
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            p = (_REPO_ROOT / raw).resolve()
        return p if p.is_dir() else None
    p = _REPO_ROOT / "ilim-voice"
    return p if p.is_dir() else None


def _ensure_ilim_voice_import() -> bool:
    root = _ilim_voice_root()
    if not root:
        return False
    s = str(root.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)
    return True


def coqui_tts_importable() -> bool:
    try:
        from TTS.api import TTS  # noqa: F401

        return True
    except Exception:
        return False


def xtts_runtime_available() -> bool:
    if not clone_enabled():
        return False
    return coqui_tts_importable()


def torch_cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def varsayilan_referans_dosyasi(karakter: SesKarakteri) -> Path:
    return referans_klasoru() / f"{karakter.value}.wav"


def coz_referans_yolu(
    karakter: str | SesKarakteri,
    *,
    ayar: dict[str, Any] | None = None,
    speaker_rel: str | None = None,
) -> Path | None:
    """Profil veya göreli yol için geçerli referans .wav döndürür."""
    kar = normalize_ses_karakteri(
        karakter.value if isinstance(karakter, SesKarakteri) else karakter
    )
    adaylar: list[Path] = []

    if speaker_rel and str(speaker_rel).strip():
        rel = str(speaker_rel).strip().replace("\\", "/")
        p = (_REPO_ROOT / rel).resolve()
        adaylar.append(p)

    refs = (ayar or {}).get("referans") or {}
    if isinstance(refs, dict):
        rel2 = refs.get(kar.value) or refs.get(str(kar.value))
        if rel2:
            adaylar.append((_REPO_ROOT / str(rel2).strip()).resolve())

    adaylar.append(varsayilan_referans_dosyasi(kar))

    for p in adaylar:
        if p.is_file() and p.stat().st_size > 4096:
            return p
    return None


def coz_tilavet_referans_yolu(
    tilavet_profil: str,
    *,
    ayar: dict[str, Any] | None = None,
) -> Path | None:
    """kuran / gazel / ilahi tilavet referans sesi."""
    prof = (tilavet_profil or "kuran").strip().lower()
    refs = (ayar or {}).get("referans") or {}
    if isinstance(refs, dict):
        rel = refs.get(prof)
        if rel:
            p = (_REPO_ROOT / str(rel).strip()).resolve()
            if p.is_file() and p.stat().st_size > 4096:
                return p
    p2 = referans_klasoru() / f"{prof}.wav"
    if p2.is_file() and p2.stat().st_size > 4096:
        return p2
    return None


def normalize_reference_to_wav(src: Path, dest: Path) -> Path:
    """Referans sesi XTTS için mono PCM WAV'a dönüştürür."""
    from ilim_assistant.video_ffmpeg import ffmpeg_available, run_ffmpeg_args

    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".wav" and src.resolve() == dest.resolve():
        return dest
    if not ffmpeg_available():
        if src.suffix.lower() == ".wav":
            import shutil

            shutil.copy2(src, dest)
            return dest
        raise RuntimeError("Referans dönüşümü için ffmpeg gerekli.")
    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(src.resolve()),
            "-ar",
            "22050",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dest.resolve()),
        ],
        timeout_sec=180,
    )
    return dest


def kaydet_referans_upload(
    src_bytes_path: Path,
    karakter: str,
) -> tuple[Path, str]:
    """Yüklenen sesi profil referansı olarak kaydeder. Dönüş: (abs_path, repo_rel)."""
    kar = normalize_ses_karakteri(karakter)
    out = varsayilan_referans_dosyasi(kar)
    normalize_reference_to_wav(src_bytes_path, out)
    rel = out.relative_to(_REPO_ROOT.resolve()).as_posix()
    return out, rel


def _synthesize_xtts_direct(
    text: str,
    speaker_wav: Path,
    *,
    language: str,
    out_wav: Path,
) -> None:
    from TTS.api import TTS

    lang = (language or "tr").strip().lower()[:2]
    xtts_lang = {
        "tr": "tr",
        "en": "en",
        "ar": "ar",
        "de": "de",
        "fr": "fr",
        "ru": "ru",
        "id": "id",
    }.get(lang, "tr")
    gpu = torch_cuda_available()
    tts = TTS(model_name=_XTTS_MODEL, gpu=gpu)
    tts.tts_to_file(
        text=text.strip(),
        file_path=str(out_wav),
        speaker_wav=str(speaker_wav),
        language=xtts_lang,
    )


def _synthesize_via_ilim_voice(
    text: str,
    speaker_wav: Path,
    *,
    language: str,
    out_wav: Path,
) -> None:
    if not _ensure_ilim_voice_import():
        raise RuntimeError("ilim-voice klasörü bulunamadı.")
    from ilim_voice.tts_engine import synthesize_to_file

    lang = (language or "tr").strip().lower()[:2]
    nllb = ISO_TO_NLLB.get(lang, "tur_Latn")
    synthesize_to_file(text, out_wav, nllb, speaker_wav=speaker_wav)


def synthesize_clone_wav(
    text: str,
    speaker_wav: Path,
    *,
    language: str = "tr",
    out_wav: Path | None = None,
) -> Path:
    """XTTS ile klon ses WAV üretir."""
    if not xtts_runtime_available():
        raise RuntimeError(
            "XTTS kullanılamıyor. Kurulum: pip install TTS torch — "
            "veya ilim-voice/requirements-tts.txt (CPU yavaş, GPU önerilir)."
        )
    body = (text or "").strip()
    if len(body) < 2:
        raise ValueError("Metin çok kısa.")
    if len(body) > clone_max_chars():
        body = body[: clone_max_chars()]

    sp = Path(speaker_wav)
    if not sp.is_file():
        raise FileNotFoundError(f"Referans ses yok: {sp}")

    fd, tmp_norm = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    norm_path = Path(tmp_norm)
    try:
        normalize_reference_to_wav(sp, norm_path)
        if out_wav is None:
            fd2, tmp_out = tempfile.mkstemp(suffix=".wav")
            os.close(fd2)
            out_path = Path(tmp_out)
        else:
            out_path = Path(out_wav)
            out_path.parent.mkdir(parents=True, exist_ok=True)

        prefer_ilim = os.environ.get("RUZGAR_TTS_CLONE_ILIM_VOICE", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )
        if prefer_ilim and _ensure_ilim_voice_import():
            try:
                _synthesize_via_ilim_voice(body, norm_path, language=language, out_wav=out_path)
                return out_path
            except Exception:
                pass
        _synthesize_xtts_direct(body, norm_path, language=language, out_wav=out_path)
        return out_path
    finally:
        try:
            norm_path.unlink(missing_ok=True)
        except OSError:
            pass


def wav_to_mp3(wav_path: Path, mp3_path: Path) -> Path:
    from ilim_assistant.video_ffmpeg import ffmpeg_available, run_ffmpeg_args

    if not ffmpeg_available():
        raise RuntimeError("MP3 çıktı için ffmpeg gerekli.")
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(wav_path.resolve()),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(mp3_path.resolve()),
        ],
        timeout_sec=300,
    )
    return mp3_path


def should_use_clone(
    *,
    backend: str,
    karakter: str,
    ayar: dict[str, Any] | None,
    speaker_rel: str | None = None,
) -> bool:
    mode = (backend or "auto").strip().lower()
    if mode == "edge":
        return False
    if mode == "clone":
        return True
    if not clone_enabled() or not xtts_runtime_available():
        return False
    return coz_referans_yolu(karakter, ayar=ayar, speaker_rel=speaker_rel) is not None


def clone_status_snapshot() -> dict[str, Any]:
    refs: dict[str, bool] = {}
    for k in SesKarakteri:
        refs[k.value] = varsayilan_referans_dosyasi(k).is_file()
    for prof in ("kuran", "gazel", "ilahi"):
        refs[prof] = (referans_klasoru() / f"{prof}.wav").is_file()
    return {
        "enabled": clone_enabled(),
        "xtts": xtts_runtime_available(),
        "coqui_import": coqui_tts_importable(),
        "cuda": torch_cuda_available(),
        "ilim_voice": _ilim_voice_root().as_posix() if _ilim_voice_root() else None,
        "referans_dir": referans_klasoru().relative_to(_REPO_ROOT.resolve()).as_posix()
        if str(referans_klasoru()).startswith(str(_REPO_ROOT.resolve()))
        else str(referans_klasoru()),
        "referans": refs,
        "max_chars": clone_max_chars(),
        "hint_tr": (
            "Referans yukleyin: Ses atolyesi - Klon referans (30-120 sn temiz konusma). "
            "Kurulum: pip install TTS torch soundfile"
            if not xtts_runtime_available()
            else (
                "Klon hazır — referans profil dosyası varsa «auto» backend kullanılır."
                if any(refs.values())
                else "XTTS kurulu; arsiv/ses-referans/{alim|edip|asistan}.wav bekleniyor."
            )
        ),
        "version": KLON_VERSION,
        "mimarlar": MIMAR,
    }
