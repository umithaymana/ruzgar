# Created by Ümit & Gökçenur
"""
Ümit abi kesin emri — «rüzgar ben ümit» sahip kilidi.

Yalnızca bu ifadeyle (yazım varyantları) tam yönetici oturumu onaylanır.
Başkalarının aynı cümleyi söylemesi güvenlik sağlamaz; kilidi yerel masaüstü
ve Ümit abi'nin makinesi için kimlik hatırlatıcısı olarak kullanın.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

OWNER_LOCK_VERSION = "owner-lock-v1-2026-05-20"

_OWNER_PATTERNS = (
    r"ruzgar\s+ben\s+umit",
    r"rüzgar\s+ben\s+ümit",
    r"ruzgar\s+benim\s+adim\s+umit",
    r"rüzgar\s+benim\s+adım\s+ümit",
)


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


_IDENTITY_PATTERNS = (
    r"^ben\s+kimim$",
    r"^kimim\s+ben$",
    r"^ben\s+kim$",
    r"^ben\s+kimdir$",
    r"^kimdir\s+ben$",
    r"^sen\s+beni\s+taniyor",
    r"^beni\s+taniyor",
    r"^benim\s+adim\s+ne",
    r"^adim\s+ne$",
    r"^ismim\s+ne$",
    r"^ben\s+kimim\s+ben$",
)


def is_owner_identity_question(message: str) -> bool:
    """«ben kimim?» — öğretim onayı değil; sahip kimliği sorusu."""
    n = _norm(message)
    if not n or len(n) > 80:
        return False
    return any(re.search(p, n) for p in _IDENTITY_PATTERNS)


def owner_identity_reply() -> str:
    return (
        "Sen Ümit'sin — Rüzgar'ın mimarı ve sahibisin. "
        "Sana «Ümit abi» diye hitap ediyorum; kişisel asistanın ve geliştirme arkadaşın benim."
    )


def is_owner_phrase(message: str) -> bool:
    """Kullanıcı açıkça «rüzgar ben ümit» (veya yakın varyant) dedi mi?"""
    n = _norm(message)
    if not n:
        return False
    if any(re.search(p, n) for p in _OWNER_PATTERNS):
        return True
    # Sıra / ek kelime toleransı: «rüzgar benim ümit», «rüzgar ben ümit abi»
    if "ruzgar" in n and "umit" in n and ("ben" in n or "benim" in n):
        return True
    return False


def owner_ack_reply(*, context: Literal["genel", "programlama"] = "genel") -> str:
    base = (
        "Evet Ümit abi, seni tanıdım — tam yönetici oturumu açık. "
        "Emirlerin önceliklidir; hafıza dosyaları yalnızca bu makinede kalır."
    )
    if context == "programlama":
        return (
            base
            + " Programlama atölyesinde: dosya okuma/yazma (@@write), pytest/ruff "
            "ve «otomatik debug» / «kendin düzelt» ile otonom düzeltme döngüsü hazır. "
            "«kendini tara» dersen öz-denetim raporu üretirim — onayından sonra düzeltirim."
        )
    return base + " Programlama işleri için Programlama motoruna geçmen yeterli."


def startup_owner_banner() -> str:
    return (
        "[Rüzgar] Sahip kilidi etkin ("
        + OWNER_LOCK_VERSION
        + "). «rüzgar ben ümit» ile yönetici oturumu onaylanır."
    )


def maybe_owner_instant_reply(message: str, mode_norm: str) -> str | None:
    if is_owner_identity_question(message):
        try:
            from ilim_assistant.ruzgar_egitim import clear_pending

            clear_pending()
        except Exception:
            pass
        return owner_identity_reply()
    if not is_owner_phrase(message):
        return None
    ctx: Literal["genel", "programlama"] = (
        "programlama" if mode_norm == "programlama" else "genel"
    )
    return owner_ack_reply(context=ctx)
