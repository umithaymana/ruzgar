# Created by Ümit & Gökçenur
"""
Ekran görüntüsü / yapıştırılan görsel → OCR + medya niyeti + motor önerisi.
Ana Motor sohbetinden video, ses, görsel, tercüme vb. yönlendirme.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any
from urllib.parse import urlparse

from ilim_assistant.motorlar.video_faz71 import extract_urls

FAZ_VERSION = "ruzgar-gorsel-niyet-v1-2026-06-06"

_URL_RE = re.compile(r"https?://[^\s<>\"{}|\\^`\[\]]+", re.I)
_PARTIAL_HOST_RE = re.compile(
    r"(?:www\.)?(?:youtube\.com|youtu\.be|dailymotion\.com|dai\.ly|vimeo\.com|"
    r"tiktok\.com|twitch\.tv|soundcloud\.com|open\.spotify\.com)[^\s\]\)\"']*",
    re.I,
)
_VIDEO_HOST_RE = re.compile(
    r"youtube|youtu\.be|dailymotion|dai\.ly|vimeo|tiktok|twitch|facebook\.com/watch|fb\.watch",
    re.I,
)
_AUDIO_HINT_RE = re.compile(
    r"\.(?:mp3|wav|flac|m4a|aac|ogg|opus)\b|soundcloud|spotify|podcast|"
    r"m[üu]zik|ses\s+dosy|whisper|transkript|metne\s+d[öo]k",
    re.I,
)
_IMAGE_HINT_RE = re.compile(
    r"foto[ğg]raf|galeri|sanat|tablo|resim|g[öo]rsel|ill[üu]strasyon|poster|kapak",
    re.I,
)
_TERCUME_HINT_RE = re.compile(
    r"meal|ayet|sure|kuran|kur'?an|osmanl[ıi]|arap[çc]a|terc[üu]me|"
    r"[\u0600-\u06FF]{4,}",
    re.I,
)
_CODE_HINT_RE = re.compile(
    r"\b(?:def|class|import|function|const|let|var|public\s+static|#include)\b|"
    r"\.(?:py|js|ts|tsx|java|cpp|c|go|rs)\b|pytest|git\s+durum",
    re.I,
)
_HIZIR_HINT_RE = re.compile(
    r"trendyol|amazon|hepsiburada|n11|indirim|fiyat|₺|\btl\b|pazar\s+tara|ürün",
    re.I,
)
_VIDEO_UI_RE = re.compile(
    r"\bizle\b|\boynat\b|play\b|shorts|abone|subscriber|views|g[öo]r[üu]nt[üu]lenme|"
    r"video\s+oynat|sinema",
    re.I,
)

_MOTOR_LABEL = {
    "video": "Video",
    "ses": "Ses",
    "mimar": "Mimar",
    "tercume": "Tercüme",
    "programlama": "Programlama",
    "hizir": "Hızır",
    "genel": "Ana Motor",
}


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ocr_image_bytes(raw: bytes, lang: str = "tur+eng") -> tuple[str, str]:
    """OCR metni; ikinci değer kaynak (tesseract|none)."""
    if not raw or len(raw) < 16:
        return "", "none"
    try:
        import io

        from PIL import Image
        import pytesseract

        tess_cmd = os.environ.get("TESSERACT_CMD", "").strip()
        if tess_cmd:
            pytesseract.pytesseract.tesseract_cmd = tess_cmd
    except Exception:
        return "", "none"
    try:
        img = Image.open(io.BytesIO(raw))
        txt = pytesseract.image_to_string(img, lang=(lang or "tur+eng").strip())
        text = (txt or "").strip()
        if text:
            return text, "tesseract"
    except Exception:
        pass
    return "", "none"


def _normalize_ocr_url(u: str) -> str:
    s = (u or "").strip().replace("\n", "").replace(" ", "")
    s = s.replace("hxxp", "http").replace("hXXp", "http")
    if s and not s.lower().startswith("http"):
        s = "https://" + s.lstrip("/")
    return s.rstrip(".,);]")


def collect_urls_from_text(*parts: str) -> list[str]:
    blob = " ".join(p for p in parts if p)
    found: list[str] = []
    seen: set[str] = set()
    for u in extract_urls(blob):
        nu = _normalize_ocr_url(u)
        if nu and nu not in seen:
            seen.add(nu)
            found.append(nu)
    for m in _URL_RE.findall(blob):
        nu = _normalize_ocr_url(m)
        if nu and nu not in seen:
            seen.add(nu)
            found.append(nu)
    for m in _PARTIAL_HOST_RE.findall(blob):
        nu = _normalize_ocr_url(m)
        if nu and nu not in seen:
            seen.add(nu)
            found.append(nu)
    return found


def _url_kind(url: str) -> str:
    low = _ascii_fold(url)
    path = ""
    try:
        path = urlparse(url).path or ""
    except Exception:
        pass
    if _VIDEO_HOST_RE.search(low) or re.search(r"\.(?:mp4|mkv|webm|mov|m4v|m3u8)\b", low):
        return "video"
    if _AUDIO_HINT_RE.search(low + " " + path):
        return "audio"
    if re.search(r"\.(?:png|jpe?g|webp|gif|bmp|svg)\b", low):
        return "image"
    return "link"


def classify_media_intent(ocr_text: str, urls: list[str], user_hint: str = "") -> dict[str, Any]:
    blob = _ascii_fold((ocr_text or "") + " " + (user_hint or "") + " " + " ".join(urls))
    scores: dict[str, int] = {
        "video": 0,
        "ses": 0,
        "mimar": 0,
        "tercume": 0,
        "programlama": 0,
        "hizir": 0,
    }
    media_kinds: set[str] = set()

    for u in urls:
        kind = _url_kind(u)
        media_kinds.add(kind)
        if kind == "video":
            scores["video"] += 8
        elif kind == "audio":
            scores["ses"] += 8
        elif kind == "image":
            scores["mimar"] += 6

    if _VIDEO_HOST_RE.search(blob) or _VIDEO_UI_RE.search(blob):
        scores["video"] += 5
        media_kinds.add("video")
    if _AUDIO_HINT_RE.search(blob):
        scores["ses"] += 5
        media_kinds.add("audio")
    if _IMAGE_HINT_RE.search(blob):
        scores["mimar"] += 4
        media_kinds.add("image")
    if _TERCUME_HINT_RE.search(blob) or _TERCUME_HINT_RE.search(ocr_text or ""):
        scores["tercume"] += 5
        media_kinds.add("text")
    if _CODE_HINT_RE.search(blob):
        scores["programlama"] += 5
        media_kinds.add("code")
    if _HIZIR_HINT_RE.search(blob):
        scores["hizir"] += 4
        media_kinds.add("product")

    ranked = sorted(
        ((m, s) for m, s in scores.items() if s > 0),
        key=lambda x: (-x[1], x[0]),
    )
    primary = ranked[0][0] if ranked else "genel"
    motors = [m for m, _ in ranked[:3]] or (["genel"] if not urls else [primary])

    if urls and primary == "genel":
        primary = "video" if _url_kind(urls[0]) == "video" else motors[0]
        if primary not in motors:
            motors.insert(0, primary)

    media_kind = "unknown"
    if len(media_kinds) == 1:
        media_kind = next(iter(media_kinds))
    elif media_kinds:
        media_kind = "mixed"

    confidence = min(0.95, 0.35 + (ranked[0][1] / 20.0 if ranked else 0.1))

    return {
        "primary_motor": primary,
        "motors": motors,
        "media_kind": media_kind,
        "confidence": round(confidence, 2),
        "scores": scores,
    }


def build_action_text(
    urls: list[str],
    classification: dict[str, Any],
    user_hint: str = "",
) -> str:
    hint = (user_hint or "").strip()
    motor = str(classification.get("primary_motor") or "genel")
    if urls:
        u0 = urls[0]
        kind = _url_kind(u0)
        if kind == "video":
            if re.search(r"\bindir\b", _ascii_fold(hint)):
                return f"indir {u0}"
            return u0
        if kind == "audio":
            if re.search(r"metne|transkript|whisper|stt", _ascii_fold(hint)):
                return f"metne dök {u0}"
            return f"ses dosyası {u0}"
    low = _ascii_fold(hint)
    if motor == "ses" and re.search(r"metne|transkript|whisper", low):
        return "metne dök"
    if motor == "tercume" and hint:
        return hint
    if motor == "mimar" and hint:
        return hint
    if hint:
        return hint
    if urls:
        return urls[0]
    return ""


def build_summary(
    ocr_text: str,
    urls: list[str],
    classification: dict[str, Any],
    ocr_source: str,
) -> str:
    motor = str(classification.get("primary_motor") or "genel")
    label = _MOTOR_LABEL.get(motor, motor)
    kind = str(classification.get("media_kind") or "unknown")
    lines = [
        f"Ümit abi, ekran görüntüsünü okudum — **{label}** motoru öne çıkıyor.",
        "",
    ]
    if urls:
        lines.append("**Bulunan bağlantılar:**")
        for u in urls[:4]:
            lines.append(f"· `{u}`")
        lines.append("")
    if ocr_text:
        preview = ocr_text.replace("\n", " ").strip()
        if len(preview) > 220:
            preview = preview[:220] + "…"
        src = "OCR" if ocr_source == "tesseract" else "yapısal"
        lines.append(f"**Ekrandaki metin ({src}):** {preview}")
        lines.append("")
    kind_tr = {
        "video": "video",
        "audio": "ses",
        "image": "görsel",
        "text": "metin/kitap",
        "code": "kod",
        "product": "ürün/fiyat",
        "mixed": "karışık içerik",
        "unknown": "belirsiz",
    }.get(kind, kind)
    lines.append(f"Tür: **{kind_tr}** · Güven: {classification.get('confidence', 0)}")
    if motor == "video" and urls:
        lines.append("Sinema açılıyor…")
    elif not urls:
        lines.append(
            "Tam link OCR ile çıkmadıysa adres çubuğunu net gösteren bir görüntü dene "
            "veya linki metin olarak yaz."
        )
    lines.append(f"({FAZ_VERSION})")
    return "\n".join(lines)


def build_activations(classification: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in classification.get("motors") or []:
        if m == "genel":
            continue
        out.append(
            {
                "motor": m,
                "label": _MOTOR_LABEL.get(m, m),
                "reason": str(classification.get("media_kind") or "screenshot"),
            }
        )
    return out


def analyze_screenshot_bytes(
    raw: bytes,
    *,
    user_hint: str = "",
    lang: str = "tur+eng",
) -> dict[str, Any]:
    ocr_text, ocr_source = ocr_image_bytes(raw, lang=lang)
    if not ocr_text:
        try:
            from ilim_assistant.dinamit_vision import analyze_image_bytes

            lite = analyze_image_bytes(raw)
            if lite.get("ok"):
                ocr_source = "structural"
        except Exception:
            lite = {}
    else:
        lite = {}
    urls = collect_urls_from_text(ocr_text, user_hint, str(lite.get("summary") or ""))
    classification = classify_media_intent(
        ocr_text,
        urls,
        user_hint + " " + str(lite.get("summary") or ""),
    )
    action_text = build_action_text(urls, classification, user_hint)
    summary = build_summary(ocr_text, urls, classification, ocr_source)
    activations = build_activations(classification)

    return {
        "ok": True,
        "version": FAZ_VERSION,
        "ocr_text": ocr_text,
        "ocr_source": ocr_source,
        "urls": urls,
        "media_kind": classification.get("media_kind"),
        "motor": classification.get("primary_motor"),
        "motors": classification.get("motors"),
        "confidence": classification.get("confidence"),
        "activations": activations,
        "action_text": action_text,
        "summary": summary,
    }
