# Created by Ümit & Gökçenur
"""
Ses motoru — Faz 72: ROK pilot (U3) — konuşarak yap.

Doğal cümle → profil seçimi / ayar özeti / içerik hattı önerisi;
«oku: …» → seslendirme yönergesi (uzun metin panelden).
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
)

FAZ72_VERSION = "ses-faz72-v1-2026-05-26"

_QUESTION_RE = re.compile(
    r"(?:\b(?:nedir|nasıl|nasil|ne\s+demek)\b|^(?:açıkla|acikla|anlat)\b)",
    re.I,
)
_PROFILE_RE = re.compile(r"\b(alim|edip|asistan)\b", re.I)
_PROFILE_SWITCH_RE = re.compile(
    r"(?:geç|gec|seç|sec|kullan|yap|mod|profil|karakter|aktif)",
    re.I,
)
_SETTINGS_RE = re.compile(
    r"(?:ses\s+ayar|profil\s+durum|hangi\s+karakter|ses\s+profil|ses\s+ayarları|ses ayarlari)",
    re.I,
)
_STT_RE = re.compile(
    r"(?:stt\s+durum|whisper|transkript\s+durum|ses\s+tanıma|ses tanima|döküm\s+durum)",
    re.I,
)
_READ_RE = re.compile(
    r"(?:\boku\b|seslendir|söyle|soyle|okut|dinlet)",
    re.I,
)
_CONTENT_HINT_RE = re.compile(
    r"(?:hangi\s+profil|hangi\s+karakter|içerik\s+hattı|icerik\s+hatti|"
    r"tilavet\s+profil|gazel\s+profil)",
    re.I,
)

_READ_TEXT_RE = re.compile(
    r"(?:oku|seslendir|söyle|soyle|okut)\s*[:：]\s*(.+)$",
    re.I | re.DOTALL,
)
_QUOTED_RE = re.compile(r"[«\"'](.+?)[»\"']", re.DOTALL)

_REGISTERED = False


def _enabled() -> bool:
    return os.environ.get("RUZGAR_SES_FAZ72", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz72_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_classifier("ses", classify_ses_intent)
    _REGISTERED = True


def extract_read_text(message: str) -> str:
    raw = (message or "").strip()
    m = _READ_TEXT_RE.search(raw)
    if m:
        return m.group(1).strip()
    q = _QUOTED_RE.search(raw)
    if q:
        return q.group(1).strip()
    if _READ_RE.search(raw):
        for sep in ("—", "–", "-", ":"):
            if sep in raw:
                tail = raw.split(sep, 1)[-1].strip()
                if len(tail) > 8:
                    return tail
    return ""


def classify_ses_intent(
    message: str,
    *,
    mode_norm: str = "ses",
    **kwargs: Any,
) -> dict[str, Any]:
    _ = kwargs
    if mode_norm != "ses":
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}
    raw = (message or "").strip()
    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}
    low = _ascii_fold(raw)

    if _SETTINGS_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "show_settings"}
    if _STT_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "stt_status"}

    prof = _PROFILE_RE.search(raw)
    if prof and _PROFILE_SWITCH_RE.search(low):
        return {
            "intent": INTENT_DO,
            "reason": "set_profile",
            "profile": prof.group(1).lower(),
        }

    if _CONTENT_HINT_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "content_profile_hint"}

    read_txt = extract_read_text(raw)
    if read_txt or (_READ_RE.search(raw) and len(raw) > 12):
        return {
            "intent": INTENT_DO,
            "reason": "read_text",
            "text": read_txt or raw,
        }

    if _QUESTION_RE.search(raw) and not _READ_RE.search(raw):
        return {"intent": INTENT_CHAT, "reason": "question"}

    if prof and not _PROFILE_SWITCH_RE.search(low):
        return {
            "intent": INTENT_DO,
            "reason": "set_profile",
            "profile": prof.group(1).lower(),
        }

    return {"intent": INTENT_CHAT, "reason": "conversation"}


def format_ses_settings() -> str:
    from ilim_assistant.motorlar.ses_motoru import normalize_ses_karakteri, profil_aciklamasi
    from ilim_assistant.tts_service import read_ses_ayarlari

    ayar = read_ses_ayarlari()
    kar = normalize_ses_karakteri(str(ayar.get("karakter", "asistan")))
    hiz = ayar.get("hiz", 0.92)
    huzur = ayar.get("huzur", 0.88)
    lines = [
        "Ümit abi, **ses motoru ayarları:**",
        "",
        f"· Aktif profil: **{kar.value}**",
        f"· Hız çarpanı: {hiz}",
        f"· Huzur çarpanı: {huzur}",
        "",
        profil_aciklamasi(kar),
        "",
        "Profil değiştir: «alim moduna geç» · «edip profili» · «asistan sesi»",
        f"({FAZ72_VERSION})",
    ]
    return "\n".join(lines)


def format_stt_status() -> str:
    try:
        from ilim_assistant.stt_whisper import stt_runtime_available
    except Exception:
        stt_runtime_available = lambda: False  # type: ignore

    ok = bool(stt_runtime_available())
    if ok:
        return (
            "Ümit abi, yerel **STT (Whisper)** hazır.\n"
            "Sağ panelden ses dosyası seçip «Metne dök» kullanabilirsiniz.\n"
            f"({FAZ72_VERSION})"
        )
    return (
        "Ümit abi, yerel STT şu an **kapalı** veya kurulu değil.\n"
        "Kurulum: `pip install faster-whisper` · Kapat: `RUZGAR_STT=0`\n"
        f"({FAZ72_VERSION})"
    )


def run_set_profile(profile: str) -> str:
    from ilim_assistant.motorlar.ses_motoru import (
        normalize_ses_karakteri,
        profil_aciklamasi,
    )
    from ilim_assistant.tts_service import read_ses_ayarlari, write_ses_ayarlari

    kar = normalize_ses_karakteri(profile)
    write_ses_ayarlari({"karakter": kar.value})
    ayar = read_ses_ayarlari()
    return (
        f"Ümit abi, ses profili **{kar.value}** olarak kaydedildi.\n\n"
        f"{profil_aciklamasi(kar)}\n\n"
        f"Hız: {ayar.get('hiz', 0.92)} · Huzur: {ayar.get('huzur', 0.88)}\n"
        f"({FAZ72_VERSION})"
    )


def format_content_profile_hint(message: str) -> str:
    from ilim_assistant.motorlar.ses_motoru import (
        analiz_icerik_yolu,
        profil_aciklamasi,
        varsayilan_karakter_icerige,
    )

    yol = analiz_icerik_yolu(message)
    oneri = varsayilan_karakter_icerige(yol)
    return (
        f"Ümit abi, metin hattı: **{yol.value}**.\n"
        f"Önerilen profil: **{oneri.value}**.\n\n"
        f"{profil_aciklamasi(oneri)}\n"
        f"({FAZ72_VERSION})"
    )


def format_read_guidance(text: str) -> str:
    from ilim_assistant.motorlar.ses_motoru import (
        analiz_icerik_yolu,
        varsayilan_karakter_icerige,
    )
    from ilim_assistant.tts_service import read_ses_ayarlari
    from ilim_assistant.motorlar.ses_motoru import normalize_ses_karakteri

    body = (text or "").strip()
    if not body:
        return (
            f"Ümit abi, okunacak metni yazın.\n"
            f"Örnek: `oku: Bismillahirrahmanirrahim` veya metni tırnak içinde verin.\n"
            f"({FAZ72_VERSION})"
        )

    ayar = read_ses_ayarlari()
    kar = normalize_ses_karakteri(str(ayar.get("karakter", "asistan")))
    yol = analiz_icerik_yolu(body)
    oneri = varsayilan_karakter_icerige(yol)
    n = len(body)
    preview = body if n <= 220 else f"{body[:220]}…"

    if n > 1200:
        return (
            f"Ümit abi, metin **{n}** karakter — sohbetten seslendirme zaman aşımına girebilir.\n"
            f"Metni sağ paneldeki **döküm kutusuna** yapıştırıp **«Seslendir»** kullanın.\n\n"
            f"Önerilen profil: **{oneri.value}** (aktif: {kar.value})\n"
            f"({FAZ72_VERSION})"
        )

    return (
        f"Ümit abi, **{kar.value}** profiliyle okunacak metin hazır ({n} karakter).\n"
        f"İçerik hattı: {yol.value} · öneri: {oneri.value}.\n\n"
        f"Önizleme: {preview}\n\n"
        "Seslendirme: sağ panel **«Seslendir»** veya sohbette **Sesli yanıt** kutusu.\n"
        f"({FAZ72_VERSION})"
    )


def maybe_instant_faz72(message: str) -> str | None:
    if not _enabled():
        return None
    ensure_kernel_registered()
    raw = (message or "").strip()
    if not raw:
        return None

    intent = classify_ses_intent(raw, mode_norm="ses")
    reason = intent.get("reason") or ""

    if intent.get("intent") == INTENT_COMMAND:
        if reason == "show_settings":
            return format_ses_settings()
        if reason == "stt_status":
            return format_stt_status()
        if reason == "content_profile_hint":
            return format_content_profile_hint(raw)

    if intent.get("intent") == INTENT_DO:
        if reason == "set_profile":
            prof = intent.get("profile") or "asistan"
            return run_set_profile(str(prof))
        if reason == "read_text":
            txt = intent.get("text") or extract_read_text(raw) or raw
            return format_read_guidance(txt)

    low = _ascii_fold(raw)
    if low.startswith("ses profil:") or low.startswith("profil:"):
        rest = raw.split(":", 1)[-1].strip()
        if rest:
            return run_set_profile(rest.split()[0])

    return None


def augment_ses_context(base: str) -> str:
    if not _enabled():
        return base
    ensure_kernel_registered()
    extra = (
        "\n[SES ROK — Faz 72]\n"
        "Konuşarak: «alim moduna geç» · «ses ayarları» · «oku: …» · «stt durumu»\n"
        "Kapat: RUZGAR_SES_FAZ72=0\n"
    )
    return (base or "").rstrip() + extra


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["ses_faz72"] = faz72_enabled()
    return out


def faz72_directive() -> str:
    return (
        "[SES — Konuşarak yap Faz 72]\n"
        "Örnek: `alim moduna geç` · `ses ayarları` · `oku: …` · `stt durumu`\n"
        "Kapat: RUZGAR_SES_FAZ72=0\n"
    )


ensure_kernel_registered()
