# Created by Ümit & Gökçenur
"""Metin içi köşeli etiketler → temiz metin + ses/prosodi parametreleri.

Örnek: [korku] [vurgulu] [fısıltı] [duraksama] [duraksama:0.8s]
Ham etiketler seslendirilmez.

§2 sınır (2026-11-21): yığın etiket soft-clamp + duraksama tek-hedef.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

ETIKET_VERSION = "ses-etiket-prosodi-v2-2026-11-21"

# Soft tavanlar — yığın etiket abartısını keser
HIZ_MIN, HIZ_MAX = 0.82, 1.12
HUZUR_MIN, HUZUR_MAX = 0.80, 1.05
RATE_EXTRA_MIN, RATE_EXTRA_MAX = -12.0, 6.0
PITCH_EXTRA_MIN, PITCH_EXTRA_MAX = -8, 6
DURAK_CARPAN_MAX = 1.45
DURAK_EK_MS_MAX = 1200
PARAGRAF_TABAN_MS = 520.0

# [etiket] veya [etiket:0.8s] / [etiket:800ms]
_TAG_RE = re.compile(
    r"\[\s*"
    r"(?P<name>korku|vurgulu|vurgu|fisilti|fısıltı|fisildi|duraksama|durak|nefes|huzun|hüzün|neseli|neşeli|ciddi|sakin)"
    r"(?:\s*:\s*(?P<val>\d+(?:[.,]\d+)?)\s*(?P<unit>s|sec|ms)?)?"
    r"\s*\]",
    re.I,
)


@dataclass
class EtiketSonuc:
    temiz_metin: str
    etiketler: list[str] = field(default_factory=list)
    rate_extra_pct: float = 0.0
    pitch_extra_hz: int = 0
    hiz_carpani: float = 1.0
    huzur_carpani: float = 1.0
    durak_carpani: float = 1.0
    durak_ek_ms: int = 0
    force_prosody: bool = False
    emotion_hint: str | None = None
    # Prosody lean'i atla — etiket durak hedefi korunur
    koru_etiket_durak: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": ETIKET_VERSION,
            "temiz_metin": self.temiz_metin,
            "etiketler": list(self.etiketler),
            "rate_extra_pct": self.rate_extra_pct,
            "pitch_extra_hz": self.pitch_extra_hz,
            "hiz_carpani": self.hiz_carpani,
            "huzur_carpani": self.huzur_carpani,
            "durak_carpani": self.durak_carpani,
            "durak_ek_ms": self.durak_ek_ms,
            "force_prosody": self.force_prosody,
            "emotion_hint": self.emotion_hint,
            "koru_etiket_durak": self.koru_etiket_durak,
        }


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def _norm_name(raw: str) -> str:
    s = (raw or "").strip().lower()
    s = (
        s.replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    aliases = {
        "vurgu": "vurgulu",
        "fisilti": "fisilti",
        "fisildi": "fisilti",
        "durak": "duraksama",
        "nefes": "duraksama",
        "huzun": "korku",
        "neseli": "neseli",
    }
    return aliases.get(s, s)


def _parse_durak_ms(val: str | None, unit: str | None) -> int:
    if not val:
        return 800
    try:
        n = float(val.replace(",", "."))
    except ValueError:
        return 800
    u = (unit or "s").lower()
    if u == "ms":
        return max(80, min(DURAK_EK_MS_MAX, int(n)))
    return max(80, min(DURAK_EK_MS_MAX, int(n * 1000)))


def _apply_soft_clamps(
    *,
    rate_x: float,
    pitch_x: int,
    hiz: float,
    huzur: float,
    durak_ms: int,
) -> tuple[float, int, float, float, float, int, bool]:
    """Yığın sonrası tavanlar + duraksama tek-hedef çarpanı."""
    rate_x = _clamp(rate_x, RATE_EXTRA_MIN, RATE_EXTRA_MAX)
    pitch_x = int(_clamp(pitch_x, PITCH_EXTRA_MIN, PITCH_EXTRA_MAX))
    hiz = _clamp(hiz, HIZ_MIN, HIZ_MAX)
    huzur = _clamp(huzur, HUZUR_MIN, HUZUR_MAX)
    durak_ms = max(0, min(DURAK_EK_MS_MAX, int(durak_ms)))
    koru = durak_ms > 0
    if koru:
        # Tek atış: 800ms → ~1.54 ham; tavan 1.45 → ~754ms taban×çarpan (huzur ayrı)
        durak_c = _clamp(float(durak_ms) / PARAGRAF_TABAN_MS, 1.0, DURAK_CARPAN_MAX)
    else:
        durak_c = 1.0
    return rate_x, pitch_x, hiz, huzur, durak_c, durak_ms, koru


def parse_ses_etiketleri(metin: str) -> EtiketSonuc:
    """Köşeli etiketleri çıkar; temiz metin + birikmiş (clamp'li) ayarlar döner."""
    raw = metin or ""
    found: list[str] = []
    rate_x = 0.0
    pitch_x = 0
    hiz = 1.0
    huzur = 1.0
    durak_ms = 0
    force_p = False
    emo: str | None = None
    # Aynı aile 2.+ etiket → yarı etki (yığın abartısı)
    family_n: dict[str, int] = {}

    def _w(name: str) -> float:
        n = family_n.get(name, 0)
        family_n[name] = n + 1
        return 1.0 if n == 0 else 0.5

    def _repl(m: re.Match[str]) -> str:
        nonlocal rate_x, pitch_x, hiz, huzur, durak_ms, force_p, emo
        name = _norm_name(m.group("name"))
        found.append(
            name if not m.group("val") else f"{name}:{m.group('val')}{m.group('unit') or 's'}"
        )
        w = _w(name)
        if name == "korku":
            rate_x -= 6.0 * w
            pitch_x -= int(round(4 * w))
            hiz *= 1.0 - (1.0 - 0.9) * w
            huzur *= 1.0 - (1.0 - 0.88) * w
            emo = emo or "ciddi"
        elif name == "vurgulu":
            rate_x -= 2.0 * w
            pitch_x += int(round(2 * w))
            hiz *= 1.0 - (1.0 - 0.96) * w
            force_p = True
        elif name == "fisilti":
            rate_x -= 4.0 * w
            pitch_x -= int(round(5 * w))
            hiz *= 1.0 - (1.0 - 0.88) * w
            huzur *= 1.0 - (1.0 - 0.85) * w
        elif name == "duraksama":
            pause = _parse_durak_ms(m.group("val"), m.group("unit"))
            # Tek hedef: max (çarpmalı yığılma yok)
            durak_ms = max(durak_ms, pause)
            force_p = True
            return "\n\n"
        elif name == "neseli":
            rate_x += 3.0 * w
            pitch_x += int(round(3 * w))
            hiz *= 1.0 + (1.06 - 1.0) * w
            emo = emo or "mutlu"
        elif name == "ciddi":
            rate_x -= 4.0 * w
            pitch_x -= int(round(3 * w))
            hiz *= 1.0 - (1.0 - 0.94) * w
            emo = emo or "ciddi"
        elif name == "sakin":
            rate_x -= 3.0 * w
            pitch_x -= int(round(1 * w))
            hiz *= 1.0 - (1.0 - 0.95) * w
            huzur *= 1.0 - (1.0 - 0.9) * w
            emo = emo or "yorgun"
        return " "

    temiz = _TAG_RE.sub(_repl, raw)
    temiz = re.sub(r"[ \t]{2,}", " ", temiz)
    temiz = re.sub(r" *\n\n *", "\n\n", temiz)
    temiz = re.sub(r"\n{3,}", "\n\n", temiz).strip()
    if not temiz and found:
        temiz = "…"
        force_p = True

    rate_x, pitch_x, hiz, huzur, durak_c, durak_ms, koru = _apply_soft_clamps(
        rate_x=rate_x,
        pitch_x=pitch_x,
        hiz=hiz,
        huzur=huzur,
        durak_ms=durak_ms,
    )
    if koru:
        force_p = True

    return EtiketSonuc(
        temiz_metin=temiz,
        etiketler=found,
        rate_extra_pct=rate_x,
        pitch_extra_hz=pitch_x,
        hiz_carpani=hiz,
        huzur_carpani=huzur,
        durak_carpani=durak_c,
        durak_ek_ms=durak_ms,
        force_prosody=force_p,
        emotion_hint=emo,
        koru_etiket_durak=koru,
    )


def apply_rate_pitch_extras(rate: str, pitch: str, et: EtiketSonuc) -> tuple[str, str]:
    """Edge rate/pitch dizelerine etiket eklerini uygula (zaten clamp'li extras)."""
    try:
        pct = float(str(rate).rstrip("%"))
        pct = max(-48.0, min(8.0, pct + float(et.rate_extra_pct)))
        rate_out = f"{pct:.0f}%"
    except ValueError:
        rate_out = rate
    try:
        from ilim_assistant.dinamit_gelisme import merge_pitch

        extra = f"{'+' if et.pitch_extra_hz >= 0 else ''}{et.pitch_extra_hz}Hz"
        pitch_out = merge_pitch(pitch, extra)
    except Exception:
        pitch_out = pitch
    return rate_out, pitch_out


def strip_etiket_smoke_cases() -> list[tuple[str, str, list[str]]]:
    """(girdi, beklenen_temiz_özet, beklenen_etiket_adları)"""
    return [
        ("Merhaba [korku] dünya", "Merhaba dünya", ["korku"]),
        ("[vurgulu] Önemli nokta.", "Önemli nokta.", ["vurgulu"]),
        ("Ses [fısıltı] alçak", "Ses alçak", ["fisilti"]),
        ("Bekle [duraksama:0.8s] devam", "Bekle\n\ndevam", ["duraksama:0.8s"]),
        ("Düz metin", "Düz metin", []),
    ]
