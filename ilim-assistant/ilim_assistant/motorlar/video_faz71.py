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
    r"göm|gom|ffmpeg|video\s+yap|klip|oynat|sinema|dönüştür|donustur|transcode|"
    r"medya\s+bilgi|panel|montaj|mux)",
    re.I,
)
_LIST_RE = re.compile(
    r"(?:son\s+indir|indirilen\s+videolar|video\s+listesi|son\s+videolar)",
    re.I,
)
_PROBE_RE = re.compile(
    r"(?:medya\s+bilgi|teknik\s+özet|teknik\s+ozet|ffprobe\b|probe\b)",
    re.I,
)
_EXPORT_RE = re.compile(
    r"(?:çıktı\s+klasör|cikti\s+klasor|export\s+klasör|export\s+klasor|dışa\s+aktar\s+klasör)",
    re.I,
)
_PANEL_RE = re.compile(
    r"(?:panel(?:i|ini)?\s+aç|panel(?:i|ini)?\s+ac|aç\s+.*panel|ac\s+.*panel)",
    re.I,
)
_TRIM_RANGE_RE = re.compile(
    r"(?:kes|trim)\s+(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*[-–]\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)",
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


def _parse_time_sec(raw: str) -> float | None:
    s = (raw or "").strip().replace(",", ".")
    if not s:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = s.split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    return None


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
    fold = _ascii_fold(raw)
    if _EXPORT_RE.search(fold):
        return {"intent": INTENT_COMMAND, "reason": "export_folder"}
    if _PROBE_RE.search(raw):
        return {"intent": INTENT_COMMAND, "reason": "media_probe"}
    if _PANEL_RE.search(fold):
        return {"intent": INTENT_COMMAND, "reason": "open_panel"}
    if _TRIM_RANGE_RE.search(raw):
        m = _TRIM_RANGE_RE.search(raw)
        if m:
            a = _parse_time_sec(m.group(1))
            b = _parse_time_sec(m.group(2))
            if a is not None and b is not None and b > a:
                return {
                    "intent": INTENT_DO,
                    "reason": "trim_range",
                    "start_sec": a,
                    "end_sec": b,
                }
    # Soru niyeti, mode=video olsa da açıklama talebi ise sohbete düşmeli.
    if _QUESTION_RE.search(raw):
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

    if _EXPORT_RE.search(_ascii_fold(raw)):
        return (
            "Ümit abi, video çıktıları `.ruzgar-video-export/` klasöründe.\n"
            "Masaüstü Rüzgar'da «Çıktı klasörü» veya sohbette aynı komut klasörü açar.\n"
            f"({FAZ71_VERSION})"
        )

    if _PROBE_RE.search(raw):
        return (
            "Ümit abi, **Medya bilgisi** için Kes panelinde göreli yol veya dosya seçin; "
            "sinema araç çubuğundaki «Medya bilgisi» düğmesine basın.\n"
            "Sohbette aynı ifade masaüstünde otomatik çalışır.\n"
            f"({FAZ71_VERSION})"
        )

    if _PANEL_RE.search(_ascii_fold(raw)):
        return (
            "Ümit abi, panel açma masaüstü sohbetinde anında çalışır "
            "(ör. «kesim panelini aç», «indirme paneli aç»).\n"
            "Üst hızlı düğmeler veya Düzen menüsünden de açabilirsiniz.\n"
            f"({FAZ71_VERSION})"
        )

    trim_m = _TRIM_RANGE_RE.search(raw)
    if trim_m:
        a = _parse_time_sec(trim_m.group(1))
        b = _parse_time_sec(trim_m.group(2))
        if a is not None and b is not None and b > a:
            return (
                f"Ümit abi, kesim aralığı **{a:.1f}–{b:.1f} sn** olarak anlaşıldı.\n"
                "Masaüstü Video motorunda göreli yol doluysa sohbet kesimi otomatik başlatır; "
                "yoksa Kes panelinde yolu yazın.\n"
                f"({FAZ71_VERSION})"
            )

    try:
        from ilim_assistant.motorlar.video_faz84 import maybe_instant_faz84

        v84 = maybe_instant_faz84(raw)
        if v84:
            return v84
    except Exception:
        pass

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
        f"\n[VIDEO ROK — Faz 71 + Sohbet süper beyin]\n"
        "Konuşarak sinema paneli: link indir/oynat · arama · kes · kurgu · medya bilgisi\n"
        "«yardım» — tüm komutlar · Düğmeler yedek\n"
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
        "Örnek: `son indirmeler` · `medya bilgisi` · `çıktı klasörü` · `kes 0:30-1:00`\n"
        "Örnek: `kesim panelini aç`\n"
        "Liste: `son indirmeler` · Kapat: RUZGAR_VIDEO_FAZ71=0\n"
    )


ensure_kernel_registered()
