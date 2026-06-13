# Created by Ümit & Gökçenur
"""Ana Motor — Faz K/L/AC3: sesli tur döngüsü + VAD ince ayarı + kullanıcı paneli."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SESLI_TUR_FAZ_K_VERSION = "sesli-tur-vad-ac3-v1-2026-06-13"

_ILIM_ROOT = Path(__file__).resolve().parent.parent
_VAD_AYAR = _ILIM_ROOT / ".ruzgar_vad_ayarlari.json"

VAD_FIELDS: tuple[str, ...] = (
    "silence_end_ms",
    "min_rec_ms",
    "quiet_avg",
    "resume_delay_ms",
)

# alan → (min, max, varsayılan)
VAD_FIELD_BOUNDS: dict[str, tuple[int, int, int]] = {
    "silence_end_ms": (350, 1400, 620),
    "min_rec_ms": (500, 2500, 850),
    "quiet_avg": (4, 18, 9),
    "resume_delay_ms": (150, 1200, 380),
}

VAD_FIELD_LABELS_TR: dict[str, str] = {
    "silence_end_ms": "Sessizlik eşiği (ms) — konuşma biter",
    "min_rec_ms": "Minimum kayıt (ms) — çok kısa tıklamayı yoksay",
    "quiet_avg": "Sessizlik hassasiyeti (düşük = daha hassas)",
    "resume_delay_ms": "TTS sonrası dinlemeye dönüş (ms)",
}


def sesli_tur_enabled() -> bool:
    return os.environ.get("RUZGAR_SESLI_TUR_FAZ_K", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _int_env(name: str, default: int, *, lo: int, hi: int) -> int:
    try:
        v = int(os.environ.get(name, str(default)).strip())
    except ValueError:
        v = default
    return max(lo, min(v, hi))


def _clamp_field(key: str, value: int) -> int:
    lo, hi, _ = VAD_FIELD_BOUNDS.get(key, (0, 99999, value))
    return max(lo, min(int(value), hi))


def sesli_tur_vad_config() -> dict[str, int]:
    """Ortam değişkenlerinden VAD (sunucu varsayılanı)."""
    return {
        "silence_end_ms": _int_env("RUZGAR_SESLI_VAD_SILENCE_MS", 620, lo=350, hi=1400),
        "min_rec_ms": _int_env("RUZGAR_SESLI_VAD_MIN_REC_MS", 850, lo=500, hi=2500),
        "quiet_avg": _int_env("RUZGAR_SESLI_VAD_QUIET_AVG", 9, lo=4, hi=18),
        "resume_delay_ms": _int_env("RUZGAR_SESLI_TUR_RESUME_MS", 380, lo=150, hi=1200),
    }


def read_vad_user_settings() -> dict[str, int]:
    if not _VAD_AYAR.is_file():
        return {}
    try:
        raw = json.loads(_VAD_AYAR.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: dict[str, int] = {}
        for key in VAD_FIELDS:
            if key in raw:
                out[key] = _clamp_field(key, int(raw[key]))
        return out
    except Exception:
        return {}


def write_vad_user_settings(
    patch: dict[str, Any] | None = None,
    *,
    reset: bool = False,
) -> dict[str, int]:
    if reset:
        if _VAD_AYAR.is_file():
            try:
                _VAD_AYAR.unlink()
            except OSError:
                pass
        return {}
    cur = read_vad_user_settings()
    for key in VAD_FIELDS:
        if patch and key in patch and patch[key] is not None:
            cur[key] = _clamp_field(key, int(patch[key]))
    if cur:
        _VAD_AYAR.write_text(
            json.dumps(cur, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    elif _VAD_AYAR.is_file():
        try:
            _VAD_AYAR.unlink()
        except OSError:
            pass
    return dict(cur)


def sesli_tur_vad_effective() -> dict[str, int]:
    """Env + kullanıcı dosyası birleşik."""
    out = sesli_tur_vad_config()
    user = read_vad_user_settings()
    for key, val in user.items():
        if key in out:
            out[key] = _clamp_field(key, val)
    return out


def vad_bounds_payload() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for key, (lo, hi, default) in VAD_FIELD_BOUNDS.items():
        out[key] = {"min": lo, "max": hi, "default": default}
    return out


def sesli_tur_vad_panel_payload() -> dict[str, Any]:
    eff = sesli_tur_vad_effective()
    return {
        "ok": True,
        "version": SESLI_TUR_FAZ_K_VERSION,
        "enabled": sesli_tur_enabled(),
        "vad": eff,
        "vad_defaults": sesli_tur_vad_config(),
        "vad_user": read_vad_user_settings(),
        "vad_bounds": vad_bounds_payload(),
        "labels_tr": VAD_FIELD_LABELS_TR,
        "path": str(_VAD_AYAR.name),
    }


def sesli_tur_status() -> dict[str, object]:
    eff = sesli_tur_vad_effective()
    return {
        "enabled": sesli_tur_enabled(),
        "version": SESLI_TUR_FAZ_K_VERSION,
        "hint": "Konuşunca gönder + sesli yanıt açıkken TTS sonrası mikrofon yeniden dinler",
        "vad": eff,
        "vad_user": read_vad_user_settings(),
    }
