"""
Mimar motoru — Faz 5: doğal dil → atölye niyeti (ROK + API köprüsü).
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

FAZ5_VERSION = "mimar-faz5-v1-2026-06-01"

_HELP_RE = re.compile(
    r"(?:mimar\s+(?:yardim|komut|help)|atolye\s+(?:yardim|komut))",
    re.I,
)
_FOTO_RE = re.compile(
    r"(?:\bfoto(?:graf)?\b|restorasyon|eski\s+foto|soluk|cizik|gurultu)",
    re.I,
)
_SANAT_RE = re.compile(
    r"(?:\b(?:sanat|galeri|eser|tablo)\b|eseri\s+tani|detayli\s+rapor)",
    re.I,
)
_TASARIM_RE = re.compile(
    r"(?:\b(?:ciz|cizim|tuval|mimari|plan|tasarim|tasarla|kroki)\b|sohbetten\s+ciz)",
    re.I,
)
_CIZ_PROMPT_RE = re.compile(
    r"(?:ciz|cizim|tasarla)\s*[:：]?\s*(.+)$",
    re.I | re.DOTALL,
)

_REGISTERED = False


def _enabled() -> bool:
    return os.environ.get("RUZGAR_MIMAR_FAZ5", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz5_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = (
        t.replace("ı", "i")
        .replace("İ", "i")
        .replace("ş", "s")
        .replace("Ş", "s")
        .replace("ğ", "g")
        .replace("Ğ", "g")
        .replace("ü", "u")
        .replace("Ü", "u")
        .replace("ö", "o")
        .replace("Ö", "o")
        .replace("ç", "c")
        .replace("Ç", "c")
    )
    return t.lower()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    from ilim_assistant.motorlar.okuma_faz73 import (
        classify_okuma_intent,
        ensure_kernel_registered as _okuma_reg,
    )

    _okuma_reg()
    register_classifier("mimar", classify_mimar_intent)
    _REGISTERED = True


def _copy_mode(low: str) -> str:
    if "poster" in low:
        return "poster"
    if "kalem" in low or "pencil" in low:
        return "pencil"
    return "trace"


def parse_atolye_action(message: str) -> dict[str, Any] | None:
    """Doğal dil → { tab, action, ... } veya None."""
    if not _enabled():
        return None
    raw = (message or "").strip()
    low = _ascii_fold(raw)
    if not low:
        return None

    if _HELP_RE.search(low):
        return {
            "tab": None,
            "action": "help",
            "label_tr": "Mimar atölye komutları",
        }

    if re.search(
        r"kopya\s+cikar|kopyala(?!.*proje)|trace\s+kopya|poster\s+stil|kalem\s+kopya",
        low,
    ) or (re.search(r"\b(?:poster|trace|pencil)\b", low) and "kopya" in low):
        return {
            "tab": "resim-sanat",
            "action": "copy",
            "mode": _copy_mode(low),
            "label_tr": "Kopya çıkar",
        }

    if re.search(r"png\s+indir|disa\s+aktar|export\s+png", low):
        return {"tab": "tasarim", "action": "export_png", "label_tr": "PNG dışa aktar"}
    if re.search(r"proje\s+kopya|plan\s+kopya", low):
        return {"tab": "tasarim", "action": "duplicate_project", "label_tr": "Proje kopyala"}
    if re.search(r"yeniden\s+uret|regenerate", low):
        return {"tab": "tasarim", "action": "regenerate", "label_tr": "Yeniden üret"}

    if re.search(r"eser\w*\s+tani|tani\w*\s+eser|bu\s+eser\s+nedir", low):
        return {
            "tab": "resim-sanat",
            "action": "identify",
            "label_tr": "Eseri tanı",
        }

    if _SANAT_RE.search(low):
        if re.search(r"detayli\s+rapor|eser\s+rapor|derin\s+analiz", low):
            return {
                "tab": "resim-sanat",
                "action": "analyze",
                "depth": "deep",
                "label_tr": "Detaylı eser raporu",
            }
        if re.search(r"eser\w*\s+tani", low):
            return {
                "tab": "resim-sanat",
                "action": "identify",
                "label_tr": "Eseri tanı",
            }
        if re.search(r"eskiz|üzerine\s+ciz|uzerine\s+ciz", low):
            return {
                "tab": "resim-sanat",
                "action": "sketch",
                "label_tr": "Eser eskizi",
            }
        if re.search(r"kopya\s+cikar|kopyala|trace|poster|kalem\s+kopya", low):
            return {
                "tab": "resim-sanat",
                "action": "copy",
                "mode": _copy_mode(low),
                "label_tr": "Kopya çıkar",
            }
        return {"tab": "resim-sanat", "action": "open_tab", "label_tr": "Sanat galerisi"}

    if _FOTO_RE.search(low):
        if re.search(r"\bocr\b|metin\s+oku|yaziyi\s+oku", low):
            return {"tab": "fotograf", "action": "ocr", "label_tr": "Fotoğraf OCR"}
        if re.search(r"restorasyon|yenile|soluk|cizik", low):
            return {
                "tab": "fotograf",
                "action": "restore",
                "label_tr": "Restorasyon paneli",
            }
        if re.search(r"sesli\s+oku|konustur|tts", low):
            return {
                "tab": "fotograf",
                "action": "voice_speak",
                "label_tr": "Sesli okuma",
            }
        return {"tab": "fotograf", "action": "open_tab", "label_tr": "Fotoğraf stüdyosu"}

    if _TASARIM_RE.search(low):
        if re.search(r"sohbetten|son\s+mesaj|az\s+once", low):
            return {
                "tab": "tasarim",
                "action": "sketch_from_chat",
                "label_tr": "Sohbetten çiz",
            }
        m = _CIZ_PROMPT_RE.search(raw)
        if m and len(m.group(1).strip()) >= 3:
            return {
                "tab": "tasarim",
                "action": "sketch_from_text",
                "prompt": m.group(1).strip()[:4000],
                "label_tr": "Betimlemeden çiz",
            }
        if len(raw) >= 6:
            return {
                "tab": "tasarim",
                "action": "sketch_from_chat",
                "user_hint": raw[:4000],
                "label_tr": "Tuval çizimi",
            }
        return {"tab": "tasarim", "action": "open_tab", "label_tr": "Tasarım tuvali"}

    if re.search(r"\bfotograf\b", low):
        return {"tab": "fotograf", "action": "open_tab", "label_tr": "Fotoğraf"}
    if re.search(r"\bsanat\b|\bgaleri\b", low):
        return {"tab": "resim-sanat", "action": "open_tab", "label_tr": "Sanat"}
    if re.search(r"\btasarim\b|\btuval\b", low):
        return {"tab": "tasarim", "action": "open_tab", "label_tr": "Tasarım"}

    return None


def format_atolye_help() -> str:
    return (
        "Ümit abi, **Mimar atölye (Faz 5)** — örnek komutlar:\n\n"
        "· «fotoğraf restorasyon» · «foto ocr»\n"
        "· «eseri tanı» · «detaylı rapor» · «kopya çıkar poster»\n"
        "· «ev planı çiz» · «sohbetten çiz» · «png indir»\n"
        "· «sanat galerisi» · «tasarım tuvali»\n\n"
        "Arşiv: «arsiv durumu» (eski Okuma komutu).\n"
        f"({FAZ5_VERSION})"
    )


def maybe_instant_faz5(message: str) -> str | None:
    if not _enabled():
        return None
    act = parse_atolye_action(message)
    if not act:
        return None
    action = act.get("action")
    if action == "help":
        return format_atolye_help()
    if action == "open_tab":
        tab = act.get("tab") or "fotograf"
        labels = {
            "fotograf": "Fotoğraf",
            "resim-sanat": "Resim · Sanat",
            "tasarim": "Tasarım",
        }
        return (
            f"Ümit abi, **{labels.get(tab, tab)}** sekmesine geçtim. "
            "Dosya ekleyip araç çubuğundan işlemi seçebilirsiniz."
        )
    return None


def classify_mimar_intent(
    message: str,
    *,
    mode_norm: str = "mimar",
    **kwargs: Any,
) -> dict[str, Any]:
    _ = kwargs
    if mode_norm not in ("mimar", "okuma"):
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}
    raw = (message or "").strip()
    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}

    act = parse_atolye_action(raw) if _enabled() else None
    if act:
        action = str(act.get("action") or "")
        if action == "help":
            return {
                "intent": INTENT_COMMAND,
                "reason": "atolye_help",
                "atolye": act,
            }
        if action == "open_tab":
            return {
                "intent": INTENT_COMMAND,
                "reason": "atolye_tab",
                "atolye": act,
            }
        if action:
            return {
                "intent": INTENT_DO,
                "reason": f"atolye_{action}",
                "atolye": act,
            }

    from ilim_assistant.motorlar.okuma_faz73 import classify_okuma_intent

    return classify_okuma_intent(raw, mode_norm="mimar", **kwargs)


def atolye_parse_payload(message: str) -> dict[str, Any]:
    """API / UI köprüsü."""
    raw = (message or "").strip()
    spec = classify_mimar_intent(raw, mode_norm="mimar")
    act = spec.get("atolye") or parse_atolye_action(raw)
    instant = maybe_instant_faz5(raw)
    run = bool(
        act
        and spec.get("intent") == INTENT_DO
        and act.get("action") not in ("help", "open_tab")
    )
    return {
        "ok": True,
        "version": FAZ5_VERSION,
        "intent": spec.get("intent"),
        "reason": spec.get("reason"),
        "atolye": act,
        "instant_reply": instant,
        "run": run,
    }


ensure_kernel_registered()
