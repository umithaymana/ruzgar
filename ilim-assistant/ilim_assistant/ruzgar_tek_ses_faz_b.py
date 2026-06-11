# Created by Ümit & Gökçenur
"""
Ana Motor — Faz B «Tek Ses» (2026-06-11).

Tüm kanallardan (LLM, çeviri, hafıza, hava) çıkan yanıtları tek Rüzgar sesine yaklaştırır:
- Dahili köşeli etiket / backend dipnotu temizliği
- Ham API / HTTP hata metni sızdırmama
- Çift karşılama ve robot kalıbı kırpma
"""

from __future__ import annotations

import os
import re

TEK_SES_VERSION = "tek-ses-faz-b-v1-2026-06-11"

_BACKEND_FOOTER = re.compile(
    r"\n*_\([^)]*(?:backend|sohbet\s+içi|karakter)[^)]*\)_\s*",
    re.I,
)
_HTTP_ERR = re.compile(r"\[HTTP\s+\d+\][\s\S]*", re.I)
_JSON_ERR = re.compile(r'^\s*\{\s*"error"\s*:', re.I)
_DUP_UMIT = re.compile(
    r"^(Ümit abi[,!]?\s*){2,}",
    re.I | re.MULTILINE,
)
_CHANNEL_TAG = re.compile(
    r"\n*\[(?:TALİMAT|TALIMAT|ARAŞTIRMA\s+ÖZETİ|HIZLI\s+BILGI)[^\]]*\]\s*",
    re.I,
)


def tek_ses_enabled() -> bool:
    return os.environ.get("RUZGAR_TEK_SES_FAZ_B", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def polish_tek_ses(text: str, *, channel: str = "") -> str:
    """Kullanıcıya giden son metin — tek ses cilası."""
    if not tek_ses_enabled():
        return (text or "").strip()
    t = (text or "").strip()
    if not t:
        return t
    if _JSON_ERR.match(t) or _HTTP_ERR.search(t):
        return (
            "Ümit abi, bulut kotası veya bağlantı nedeniyle yanıt tamamlanamadı — "
            "biraz sonra tekrar dene; yerel Ollama açıksa otomatik ona düşer."
        )
    t = _HTTP_ERR.sub("", t).strip()
    t = _BACKEND_FOOTER.sub("", t).strip()
    t = _CHANNEL_TAG.sub("\n", t)
    t = _DUP_UMIT.sub("Ümit abi, ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def tek_ses_status() -> dict[str, object]:
    return {
        "enabled": tek_ses_enabled(),
        "version": TEK_SES_VERSION,
    }
