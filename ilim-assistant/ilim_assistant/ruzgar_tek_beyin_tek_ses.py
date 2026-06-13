# Created by Ümit & Gökçenur
"""Tek beyin Faz K — dost, hafıza ve bilgi yollarında tek Rüzgar sesi."""

from __future__ import annotations

import os
import re
from typing import Any

TEK_BEYIN_TEK_SES_VERSION = "tek-beyin-tek-ses-v1-2026-06-12-faz-k"

_ROBOT_OPENERS = re.compile(
    r"^(?:"
    r"tabii ki[,!]?\s*(?:size\s+)?yardımcı olmaktan.*|"
    r"elbette[,!]?\s*.*yardımcı.*|"
    r"işte\s+(?:bilgiler|özet|cevap)|"
    r"özetle(?:me)?\s*:|"
    r"aşağıdaki\s+bilgiler"
    r")\s*\n*",
    re.I | re.MULTILINE,
)
_BULLET_LINE = re.compile(r"^[\s]*(?:[-*•]|\d+[.)])\s+", re.MULTILINE)
_META_HAFIZA = re.compile(
    r"(?:hafızamda|hafizamda|kayıtlarımda|kayitlarimda|kayıtlara\s+baktım|"
    r"buldum\s+ki|hafızaya\s+baktım)\b",
    re.I,
)


def tek_beyin_tek_ses_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_TEK_SES", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _voice_core_block() -> str:
    return (
        "### TEK BEYİN — TEK SES (Faz K)\n"
        "Ümit abi ile **aynı sıcak Rüzgar** konuşuyorsun; dost sohbet, hafıza veya bilgi fark etmez.\n"
        "- Samimi «Ümit abi» tonu; soğuk resmi dil veya sürekli «nasıl yardımcı olabilirim» yok.\n"
        "- Akıcı paragraf tercih et; zorunlu madde listesi yok.\n"
        "- Kullanıcının cümlesini kopyalama; mekanik «evet seni anlıyorum» echo yok.\n"
        "- «Hafızamda buldum», «kayıtlarımda» gibi meta ifadeler kullanma.\n"
        "- Bilmediğini uydurma; emin değilsen kısa ve dürüstçe söyle.\n"
    )


def build_tek_beyin_voice_system_addon(path: str = "genel") -> str:
    """LLM sistem promptuna eklenecek tek ses bloğu."""
    if not tek_beyin_tek_ses_enabled():
        return ""
    p = (path or "genel").strip().lower()
    tail = _voice_core_block()
    if p == "dost":
        tail += (
            "- Bu tur **yakın dost sohbeti**; dinle, hisset, 2–6 akıcı cümle.\n"
            "- Ders anlatımı veya numaralı liste zorunlu değil.\n"
        )
    elif p == "hafiza":
        tail += (
            "- Bu tur **kişisel hafıza**; kayıtlı bilgiyi kendi cümlelerinle anlat.\n"
            "- Madde madde dökme; 2–6 cümle doğal anlatım.\n"
        )
    elif p == "bilgi":
        tail += (
            "- Bu tur **bilgi/ansiklopedi**; önce tek cümlede net cevap, sonra isteğe bağlı 2–3 kısa cümle bağlam.\n"
            "- Uzun madde listesi ve ders kitabı üslubu yok; konuşur gibi yaz.\n"
            "- Güven satırı varsa sonda kalsın; gövdeyi madde listesine çevirme.\n"
        )
    else:
        tail += "- Kısa ve doğal; robot şablonu yok.\n"
    return "\n\n" + tail.strip() + "\n"


def build_bilgi_voice_instruction() -> str:
    """Hızlı bilgi yolları için eski «2–5 madde» talimatının yerine."""
    if not tek_beyin_tek_ses_enabled():
        return (
            "\n\n[TALİMAT — HIZLI BILGI]\n"
            "Tek paragraf veya 2–4 madde; Türkçe, net, kaynak uydurma.\n"
        )
    return (
        "\n\n[TALİMAT — BILGI — TEK SES]\n"
        "Ümit abi'ye doğal anlat: önce net cevap, sonra kısa bağlam (akıcı paragraf). "
        "Zorunlu madde listesi yok. Kaynak uydurma; emin değilsen belirt.\n"
    )


def build_bilgi_cloud_voice_instruction(*, topic: str = "bilgi") -> str:
    if not tek_beyin_tek_ses_enabled():
        return (
            f"\n\n[TALİMAT — {topic.upper()} — BULUT HIZLI]\n"
            "Türkçe, yapılandırılmış yanıt (2–5 madde veya kısa paragraflar). "
            "Kaynak uydurma; emin değilsen kısaca belirt. Ümit abi'ye hitap et.\n"
        )
    return (
        f"\n\n[TALİMAT — {topic.upper()} — TEK SES]\n"
        "Ümit abi'ye sıcak ve akıcı Türkçe: önce doğrudan cevap, ardından 1–3 kısa cümle detay. "
        "Liste zorunlu değil. Kaynak uydurma.\n"
    )


def _bullet_ratio(text: str) -> float:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return 0.0
    bullets = sum(1 for ln in lines if _BULLET_LINE.match(ln))
    return bullets / len(lines)


def polish_tek_beyin_voice(text: str, *, path: str = "") -> str:
    """Kullanıcıya giden metin — tek beyin ses cilası (Faz B üstü)."""
    if not tek_beyin_tek_ses_enabled():
        return (text or "").strip()
    t = (text or "").strip()
    if not t:
        return t
    t = _ROBOT_OPENERS.sub("", t).strip()
    t = _META_HAFIZA.sub("bildiğim kadarıyla", t)
    try:
        ratio_cap = max(0.45, min(float(os.environ.get("RUZGAR_TEK_BEYIN_BULLET_RATIO_MAX", "0.72")), 0.95))
    except ValueError:
        ratio_cap = 0.72
    if _bullet_ratio(t) > ratio_cap and len(t) > 40:
        lines = t.splitlines()
        prose: list[str] = []
        buf: list[str] = []
        for ln in lines:
            if _BULLET_LINE.match(ln):
                item = _BULLET_LINE.sub("", ln).strip()
                if item:
                    buf.append(item)
            else:
                if buf:
                    prose.append(" ".join(buf))
                    buf = []
                prose.append(ln.strip())
        if buf:
            prose.append(" ".join(buf))
        merged = "\n\n".join(p for p in prose if p)
        guven = ""
        m = re.search(r"(\n\n\*\*Güven:[^\n]+\*\*[^\n]*)", t, re.I)
        if m:
            guven = m.group(1)
            merged = re.sub(r"\n\n\*\*Güven:[^\n]+\*\*[^\n]*", "", merged, flags=re.I).strip()
        t = merged.strip()
        if guven and guven not in t:
            t = t.rstrip() + guven
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def append_voice_addon_to_system(system: str, path: str = "genel") -> str:
    addon = build_tek_beyin_voice_system_addon(path)
    if not addon:
        return system
    return (system or "").rstrip() + addon


def tek_beyin_tek_ses_status() -> dict[str, Any]:
    try:
        ratio = float(os.environ.get("RUZGAR_TEK_BEYIN_BULLET_RATIO_MAX", "0.72"))
    except ValueError:
        ratio = 0.72
    return {
        "enabled": tek_beyin_tek_ses_enabled(),
        "version": TEK_BEYIN_TEK_SES_VERSION,
        "bullet_ratio_max": ratio,
    }
