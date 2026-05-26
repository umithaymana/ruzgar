# Created by Ümit & Gökçenur
"""
Video motoru — Faz 71: ROK pilot (U2) — konuşarak yap.

Doğal cümle + URL → indirme; soru → sohbet; «son indirmeler» → liste.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

from ilim_assistant.ruzgar_motor_kernel import (
    INTENT_CHAT,
    INTENT_COMMAND,
    INTENT_DO,
    register_classifier,
    sse_event,
)

FAZ71_VERSION = "video-faz71-v1-2026-05-26"

_URL_RE = re.compile(r"https?://[^\s<>\"{}|\\^`\[\]]+", re.I)
_QUESTION_RE = re.compile(
    r"(?:\b(?:nedir|nasıl|nasil|ne\s+demek)\b|^(?:açıkla|acikla|anlat)\b)",
    re.I,
)
_ACTION_RE = re.compile(
    r"(?:indir|download|youtube|kes|kurgu|birleştir|birlestir|altyazı|altyazi|"
    r"göm|gom|ffmpeg|video\s+yap|klip)",
    re.I,
)
_LIST_RE = re.compile(
    r"(?:son\s+indir|indirilen\s+videolar|video\s+listesi|son\s+videolar)",
    re.I,
)

_REGISTERED = False


def _enabled() -> bool:
    return os.environ.get("RUZGAR_VIDEO_FAZ71", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz71_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_classifier("video", classify_video_intent)
    _REGISTERED = True


def extract_urls(message: str) -> list[str]:
    return [u.rstrip(".,);]") for u in _URL_RE.findall(message or "")]


def classify_video_intent(
    message: str,
    *,
    mode_norm: str = "video",
    **kwargs: Any,
) -> dict[str, Any]:
    _ = kwargs
    if mode_norm != "video":
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}
    raw = (message or "").strip()
    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}
    if _LIST_RE.search(_ascii_fold(raw)):
        return {"intent": INTENT_COMMAND, "reason": "list_downloads"}
    if _QUESTION_RE.search(raw) and not _ACTION_RE.search(raw):
        return {"intent": INTENT_CHAT, "reason": "question"}
    urls = extract_urls(raw)
    if urls and (_ACTION_RE.search(raw) or "youtube" in raw.lower() or "youtu.be" in raw.lower()):
        return {"intent": INTENT_DO, "reason": "download_url", "urls": urls}
    if urls and len(raw) < 200:
        return {"intent": INTENT_DO, "reason": "bare_url", "urls": urls}
    if _ACTION_RE.search(raw) and not urls:
        return {
            "intent": INTENT_DO,
            "reason": "action_no_url",
            "start_task": False,
            "hint": "YouTube veya video bağlantısını mesaja yapıştırın.",
        }
    return {"intent": INTENT_CHAT, "reason": "conversation"}


def format_download_report(result: Any) -> str:
    if getattr(result, "ok", False):
        return (
            f"Ümit abi, video indirildi.\n\n"
            f"**{getattr(result, 'title', '') or 'video'}**\n"
            f"Yol: `{getattr(result, 'file_path', '')}`\n"
            f"Boyut: {int(getattr(result, 'file_size_bytes', 0) or 0)} bayt\n"
            f"({FAZ71_VERSION})"
        )
    err = getattr(result, "error", None) or "indirme başarısız"
    return f"Ümit abi, video indirilemedi: {err}\n({FAZ71_VERSION})"


def run_download_url(url: str) -> str:
    from ilim_assistant.motorlar.video_motoru import download_video_with_yt_dlp

    res = download_video_with_yt_dlp(url.strip())
    return format_download_report(res)


def format_recent_list() -> str:
    from ilim_assistant.motorlar.video_motoru import list_recent_downloads

    rows = list_recent_downloads(8)
    if not rows:
        return f"Ümit abi, henüz kayıtlı video indirmesi yok.\n({FAZ71_VERSION})"
    lines = ["Ümit abi, **son video indirmeleri:**", ""]
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"· {row.get('title', '?')} — `{row.get('file_path', '')}`"
        )
    lines.append(f"\n({FAZ71_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz71(message: str) -> str | None:
    if not _enabled():
        return None
    ensure_kernel_registered()
    raw = (message or "").strip()
    if not raw:
        return None

    if _LIST_RE.search(_ascii_fold(raw)):
        return format_recent_list()

    intent = classify_video_intent(raw, mode_norm="video")
    if intent.get("intent") == INTENT_DO:
        urls = intent.get("urls") or extract_urls(raw)
        if urls:
            return run_download_url(urls[0])
        hint = intent.get("hint") or "Video linki ekleyin."
        return f"Ümit abi, {hint}\n({FAZ71_VERSION})"

    low = _ascii_fold(raw)
    if low.startswith("video indir:") or low.startswith("indir:"):
        rest = raw.split(":", 1)[-1].strip()
        u = extract_urls(rest)
        if u:
            return run_download_url(u[0])

    return None


def augment_video_context(base: str) -> str:
    if not _enabled():
        return base
    ensure_kernel_registered()
    extra = (
        f"\n[VIDEO ROK — Faz 71]\n"
        "Konuşarak: «şu videoyu indir» + URL · «son indirmeler»\n"
        "Kapat: RUZGAR_VIDEO_FAZ71=0\n"
    )
    return (base or "").rstrip() + extra


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["video_faz71"] = faz71_enabled()
    return out


def faz71_directive() -> str:
    return (
        "[VİDEO — Konuşarak yap Faz 71]\n"
        "Örnek: `şu videoyu indir https://www.youtube.com/watch?v=...`\n"
        "Liste: `son indirmeler` · Kapat: RUZGAR_VIDEO_FAZ71=0\n"
    )


ensure_kernel_registered()
