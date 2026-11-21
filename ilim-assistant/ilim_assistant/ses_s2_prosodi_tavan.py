# Created by Ümit & Gökçenur
"""S2 — Prosodi + tilavet/âlim parametre tavanı.

S1 üç profil üzerine: muhabbet akıcı kalır; âlim vakur; tilavet huşûlu durak.
Kulak onayı Mimar’da — smoke yapı/ayrım yeşili verir.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

S2_VERSION = "ses-s2-prosodi-tavan-v1-2026-11-21"

# Tavan parametreleri (Edge + prosody durak çarpanı)
# hiz/huzur: ayar üst sınırı (düşük = daha yavaş / daha ağır)
TAVAN_PARAM: dict[str, dict[str, Any]] = {
    "muhabbet": {
        "hiz_ust": 1.0,
        "huzur_ust": 0.96,
        "durak_carpani": 0.88,
        "rate_extra_pct": 0.0,
        "pitch_override": None,
        "prosody_tercih": False,
        "tilavet_durak": False,
        "aciklama": "Günlük muhabbet — kısa durak, doğal tempo",
    },
    "alim": {
        "hiz_ust": 0.86,
        "huzur_ust": 0.80,
        "durak_carpani": 1.22,
        "rate_extra_pct": -3.0,
        "pitch_override": None,
        "prosody_tercih": True,
        "tilavet_durak": False,
        "aciklama": "Âlim — hadis/tefsir vakur; orta-uzun durak",
    },
    "tilavet": {
        "hiz_ust": 0.74,
        "huzur_ust": 0.70,
        "durak_carpani": 1.42,
        "rate_extra_pct": -8.0,
        "pitch_override": "-5Hz",
        "prosody_tercih": True,
        "tilavet_durak": True,
        "aciklama": "Tilavet — huşû; ayet/vakıf uzun nefes",
    },
}


def s2_enabled() -> bool:
    return os.environ.get("RUZGAR_SES_S2", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def coz_tavan(raw: str | None) -> str:
    from ilim_assistant.ses_s1_tavan_profil import coz_tavan_profil

    return coz_tavan_profil(raw)


def tavan_param(tavan: str | None) -> dict[str, Any]:
    t = coz_tavan(tavan)
    return dict(TAVAN_PARAM.get(t) or TAVAN_PARAM["muhabbet"])


def ayarla_hiz_huzur(
    tavan: str | None,
    *,
    hiz: float,
    huzur: float,
) -> tuple[float, float]:
    """Ayar değerlerini tavan üst sınırına sıkıştırır."""
    if not s2_enabled():
        return float(hiz), float(huzur)
    p = tavan_param(tavan)
    hiz_out = min(float(hiz), float(p["hiz_ust"]))
    huzur_out = min(float(huzur), float(p["huzur_ust"]))
    return max(0.55, hiz_out), max(0.45, huzur_out)


def ayarla_durak_carpani(tavan: str | None, base: float = 1.0) -> float:
    if not s2_enabled():
        return max(0.55, min(1.6, float(base)))
    p = tavan_param(tavan)
    out = float(base) * float(p["durak_carpani"])
    return max(0.55, min(2.0, out))


def ayarla_rate_string(rate: str, tavan: str | None) -> str:
    if not s2_enabled():
        return rate
    p = tavan_param(tavan)
    extra = float(p.get("rate_extra_pct") or 0.0)
    if abs(extra) < 0.01:
        return rate
    try:
        pct = float(str(rate).rstrip("%"))
        pct = max(-48.0, min(8.0, pct + extra))
        return f"{pct:.0f}%"
    except ValueError:
        return rate


def ayarla_pitch_string(pitch: str, tavan: str | None) -> str:
    if not s2_enabled():
        return pitch
    p = tavan_param(tavan)
    ov = p.get("pitch_override")
    return str(ov) if ov else pitch


def wants_prosody(tavan: str | None, *, metin_gerekli: bool, ayar_prosody: bool) -> bool:
    """Âlim/tilavet: metin uygunsa prosody tercih; muhabbet: mevcut kural."""
    if not s2_enabled():
        return bool(ayar_prosody and metin_gerekli)
    p = tavan_param(tavan)
    if p.get("prosody_tercih") and metin_gerekli:
        return True
    return bool(ayar_prosody and metin_gerekli)


def wants_tilavet_pause(tavan: str | None) -> bool:
    return bool(s2_enabled() and tavan_param(tavan).get("tilavet_durak"))


def coz_tts_tavan_paketi(
    karakter: str | None,
    *,
    ayar: dict[str, Any] | None = None,
    rate: str | None = None,
    pitch: str | None = None,
    durak_carpani: float | None = None,
) -> dict[str, Any]:
    """API/TTS için S2 sıkıştırılmış paket."""
    from ilim_assistant.tts_service import read_ses_ayarlari

    ay = ayar or read_ses_ayarlari()
    t = coz_tavan(karakter or ay.get("karakter"))
    hiz0 = float(ay.get("hiz", 0.92))
    huzur0 = float(ay.get("huzur", 0.88))
    hiz, huzur = ayarla_hiz_huzur(t, hiz=hiz0, huzur=huzur0)
    base_durak = float(
        durak_carpani if durak_carpani is not None else ay.get("durak", 1.0)
    )
    paket = {
        "tavan": t,
        "hiz": hiz,
        "huzur": huzur,
        "durak_carpani": ayarla_durak_carpani(t, base_durak),
        "tilavet_durak": wants_tilavet_pause(t),
        "param": tavan_param(t),
        "s2": s2_enabled(),
        "version": S2_VERSION,
    }
    if rate is not None:
        paket["rate"] = ayarla_rate_string(rate, t)
    if pitch is not None:
        paket["pitch"] = ayarla_pitch_string(pitch, t)
    return paket


def kulak_kontrol_listesi() -> list[dict[str, str]]:
    """Mimar kulak testi — S2 mühür için yapısal checklist (skor Mimar)."""
    return [
        {
            "id": "muhabbet",
            "metin": "Merhaba Ümit abi, nasılsın? Kısa bir muhabbet cümlesi.",
            "beklenen": "Doğal, robot değil, kısa durak",
        },
        {
            "id": "alim",
            "metin": "Hadis-i şerifte buyurulur ki: Ameller niyetlere göredir.",
            "beklenen": "Vakur, tane tane, acele yok",
        },
        {
            "id": "tilavet",
            "metin": "Rahmân ve Rahîm olan Allah'ın adıyla. Elhamdülillâhi rabbil âlemîn.",
            "beklenen": "Huşû, uzun nefes / vakıf hissi",
        },
    ]


def run_s2_card() -> dict[str, Any]:
    from ilim_assistant.motorlar.ses_motoru import (
        IcerikYolu,
        SesKarakteri,
        edge_pitch_string,
        edge_rate_yuzdesi,
    )
    from ilim_assistant.motorlar.ses_prosody import DurakTuru, durak_suresi_ms
    from ilim_assistant.motorlar.ses_tilavet import (
        TilavetMod,
        tilavet_durak_ms,
        tilavet_rate_pitch,
    )

    profiller: dict[str, Any] = {}
    for t in ("muhabbet", "alim", "tilavet"):
        kar = SesKarakteri(t) if t != "muhabbet" else SesKarakteri.muhabbet
        icerik = (
            IcerikYolu.kuran
            if t == "tilavet"
            else (IcerikYolu.tasavvuf_hadis if t == "alim" else IcerikYolu.genel)
        )
        hiz, huzur = ayarla_hiz_huzur(t, hiz=0.92, huzur=0.88)
        rate = edge_rate_yuzdesi(
            karakter=kar, icerik=icerik, hiz_carpani=hiz, huzur_carpani=huzur
        )
        pitch = edge_pitch_string(kar, icerik)
        paket = coz_tts_tavan_paketi(t, rate=rate, pitch=pitch, durak_carpani=1.0)
        pause_cumle = durak_suresi_ms(
            DurakTuru.cumle,
            icerik=icerik,
            durak_carpani=paket["durak_carpani"],
            huzur_carpani=huzur,
            tilavet=bool(paket["tilavet_durak"]),
        )
        profiller[t] = {
            **paket,
            "rate_base": rate,
            "pause_cumle_ms": pause_cumle,
        }

    # Tilavet hattı ekstra
    tr_rate, tr_pitch = tilavet_rate_pitch(
        "Bismillahirrahmanirrahim. Elhamdülillah.",
        karakter="tilavet",
        hiz_carpani=0.74,
        huzur_carpani=0.70,
    )
    ayet_ms = tilavet_durak_ms(
        DurakTuru.ayet,
        mod=TilavetMod.kuran_meal,
        durak_carpani=ayarla_durak_carpani("tilavet", 1.0),
        huzur_carpani=0.70,
    )

    # Ayrım: tilavet durak > alim > muhabbet; tilavet rate daha yavaş
    p_m = int(profiller["muhabbet"]["pause_cumle_ms"])
    p_a = int(profiller["alim"]["pause_cumle_ms"])
    p_t = int(profiller["tilavet"]["pause_cumle_ms"])
    distinct_pause = p_t > p_a > p_m > 0

    def _pct(r: str) -> float:
        try:
            return float(str(r).rstrip("%"))
        except ValueError:
            return 0.0

    r_m = _pct(profiller["muhabbet"]["rate"])
    r_t = _pct(profiller["tilavet"]["rate"])
    distinct_rate = r_t < r_m - 5

    return {
        "version": S2_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "enabled": s2_enabled(),
        "profiller": profiller,
        "tilavet_ornek": {
            "rate": tr_rate,
            "pitch": tr_pitch,
            "ayet_durak_ms": ayet_ms,
        },
        "distinct_pause_ok": distinct_pause,
        "distinct_rate_ok": distinct_rate,
        "kulak_liste": kulak_kontrol_listesi(),
        "kulak_skoru_0_5": None,
        "kulak_not": "Mimar kulak onayı — yapı yeşili kulak mühürü değildir.",
        "s2_yesil": bool(
            s2_enabled() and distinct_pause and distinct_rate and ayet_ms >= 1500
        ),
        "sonraki": "S3 — klon yolu (BUSENAZ ses + kuran.wav) / Edge yedek",
    }


def write_s2_docs(card: dict[str, Any] | None = None) -> dict[str, str]:
    payload = card or run_s2_card()
    docs = Path(__file__).resolve().parents[1] / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    js = docs / "S2_SES_PROSODI_TAVAN_2026-11-21.json"
    md = docs / "S2_SES_PROSODI_TAVAN_2026-11-21.md"
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    prof = payload.get("profiller") or {}
    lines = [
        "# S2 — Prosodi + tilavet/âlim parametre tavanı — 2026-11-21",
        "",
        f"`{payload.get('version')}` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`",
        "",
        f"**S2 yapı yeşili:** {'EVET' if payload.get('s2_yesil') else 'HAYIR'}  ",
        f"**Kulak skoru:** _(Mimar — checklist aşağıda)_",
        "",
        "## Parametre özeti",
        "",
        "| Tavan | Rate | Durak çarpanı | Cümle durak ms | Hız üst | Huzur üst |",
        "|-------|------|---------------|----------------|---------|-----------|",
    ]
    for t in ("muhabbet", "alim", "tilavet"):
        d = prof.get(t) or {}
        p = d.get("param") or {}
        lines.append(
            f"| {t} | {d.get('rate')} | {d.get('durak_carpani')} | "
            f"{d.get('pause_cumle_ms')} | {p.get('hiz_ust')} | {p.get('huzur_ust')} |"
        )
    til = payload.get("tilavet_ornek") or {}
    lines += [
        "",
        f"- Tilavet örnek rate/pitch: `{til.get('rate')}` / `{til.get('pitch')}`",
        f"- Ayet durak ms: **{til.get('ayet_durak_ms')}**",
        f"- Pause ayrımı: {payload.get('distinct_pause_ok')} · Rate ayrımı: {payload.get('distinct_rate_ok')}",
        "",
        "## Kulak checklist (Mimar)",
        "",
    ]
    for item in payload.get("kulak_liste") or []:
        lines.append(
            f"- [ ] **{item.get('id')}** — «{item.get('metin')}» → {item.get('beklenen')}"
        )
    lines += [
        "",
        "## Araçlar",
        "",
        "- `ilim_assistant/ses_s2_prosodi_tavan.py`",
        "- `scripts/smoke_s2_ses_prosodi_tavan.py`",
        "- Kapat: `RUZGAR_SES_S2=0`",
        "",
        "## Sonraki",
        "",
        "**S3** — klon: `BUSENAZ ses` + tilavet `kuran.wav` / Edge yedek.",
        "",
        "*Ümit & Gökçenur Haymana'nın ortak projesi.*",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(js), "md": str(md)}
