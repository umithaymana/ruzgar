# Created by Ümit & Gökçenur
"""S1 — Ses tavanı üç profil seçici (muhabbet / âlim / tilavet) Edge üzerinde.

Boot / yüz / hub dokunulmaz. Eski asistan/edip alias olarak kalır.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

S1_VERSION = "ses-s1-tavan-profil-v1-2026-11-21"

# Tavan omurga (plan §3.2 / §5)
TAVAN_PROFILLER = ("muhabbet", "alim", "tilavet")

# Eski menü adları → tavan
_ALIAS_TO_TAVAN: dict[str, str] = {
    "asistan": "muhabbet",
    "sohbet": "muhabbet",
    "gunluk": "muhabbet",
    "günlük": "muhabbet",
    "muhabbet": "muhabbet",
    "alim": "alim",
    "âlim": "alim",
    "bilge": "alim",
    "kari": "alim",
    "tilavet": "tilavet",
    "kuran": "tilavet",
    "tecvid": "tilavet",
    "edip": "muhabbet",  # edebiyat yumuşak → muhabbet omurgası (edip enum ayrı kalır)
    "sair": "muhabbet",
}


def tavan_profil_mi(raw: str | None) -> bool:
    s = (raw or "").strip().lower()
    return s in TAVAN_PROFILLER or s in _ALIAS_TO_TAVAN


def coz_tavan_profil(raw: str | None) -> str:
    """API/menü metnini tavan profil adına çevirir; bilinmeyen → muhabbet."""
    s = (raw or "").strip().lower()
    if s in TAVAN_PROFILLER:
        return s
    if s in _ALIAS_TO_TAVAN:
        return _ALIAS_TO_TAVAN[s]
    return "muhabbet"


def tavan_to_ses_karakteri(tavan: str):
    """Tavan adı → SesKarakteri (Edge parametreleri için)."""
    from ilim_assistant.motorlar.ses_motoru import SesKarakteri, normalize_ses_karakteri

    t = coz_tavan_profil(tavan)
    return normalize_ses_karakteri(t)


def edge_snapshot_for_tavan(tavan: str, *, ayar: dict[str, Any] | None = None) -> dict[str, Any]:
    from ilim_assistant.motorlar.ses_motoru import (
        EDGE_VOICES,
        IcerikYolu,
        edge_pitch_string,
        edge_rate_yuzdesi,
        profil_aciklamasi,
    )
    from ilim_assistant.tts_service import read_ses_ayarlari

    ay = ayar or read_ses_ayarlari()
    kar = tavan_to_ses_karakteri(tavan)
    t = coz_tavan_profil(tavan)
    icerik = IcerikYolu.kuran if t == "tilavet" else (
        IcerikYolu.tasavvuf_hadis if t == "alim" else IcerikYolu.genel
    )
    return {
        "tavan": t,
        "karakter": kar.value,
        "voice": EDGE_VOICES.get(kar),
        "rate": edge_rate_yuzdesi(
            karakter=kar,
            icerik=icerik,
            hiz_carpani=float(ay.get("hiz", 0.92)),
            huzur_carpani=float(ay.get("huzur", 0.88)),
        ),
        "pitch": edge_pitch_string(kar, icerik),
        "icerik_yolu": icerik.value,
        "aciklama": (profil_aciklamasi(kar) or "")[:200],
    }


def tavan_profiller_snapshot(*, ayar: dict[str, Any] | None = None) -> dict[str, Any]:
    from ilim_assistant.tts_service import read_ses_ayarlari

    ay = ayar or read_ses_ayarlari()
    aktif_raw = str(ay.get("karakter") or "muhabbet")
    aktif = coz_tavan_profil(aktif_raw)
    return {
        "version": S1_VERSION,
        "aktif_tavan": aktif,
        "aktif_kayit": aktif_raw,
        "profiller": {p: edge_snapshot_for_tavan(p, ayar=ay) for p in TAVAN_PROFILLER},
        "alias": dict(_ALIAS_TO_TAVAN),
        "kural": "sohbet/API karakter=muhabbet|alim|tilavet (asistan→muhabbet)",
    }


def sohbet_profil_dogru_mu(istenilen: str, ayar_veya_karakter: str | dict[str, Any]) -> bool:
    """Smoke: istenen tavan ile kayıtlı karakter aynı omurgada mı?"""
    want = coz_tavan_profil(istenilen)
    if isinstance(ayar_veya_karakter, dict):
        got = coz_tavan_profil(str(ayar_veya_karakter.get("karakter") or ""))
    else:
        got = coz_tavan_profil(str(ayar_veya_karakter or ""))
    return want == got


def set_tavan_profil(tavan: str) -> dict[str, Any]:
    """Aktif karakteri tavan profiline yazar (Edge yolu)."""
    from ilim_assistant.motorlar.ses_motoru import normalize_ses_karakteri
    from ilim_assistant.tts_service import read_ses_ayarlari, write_ses_ayarlari

    t = coz_tavan_profil(tavan)
    kar = normalize_ses_karakteri(t)
    write_ses_ayarlari({"karakter": kar.value})
    ay = read_ses_ayarlari()
    return {
        "ok": True,
        "tavan": t,
        "karakter": kar.value,
        "snapshot": edge_snapshot_for_tavan(t, ayar=ay),
    }


def run_s1_card() -> dict[str, Any]:
    snap = tavan_profiller_snapshot()
    # Üç profilin voice/rate/pitch ayırt edilebilir olması
    rates = {p: snap["profiller"][p]["rate"] for p in TAVAN_PROFILLER}
    pitches = {p: snap["profiller"][p]["pitch"] for p in TAVAN_PROFILLER}
    distinct = len(set(rates.values())) >= 2 and (
        rates["tilavet"] != rates["muhabbet"] or pitches["tilavet"] != pitches["muhabbet"]
    )
    # Alias smoke
    alias_ok = (
        coz_tavan_profil("asistan") == "muhabbet"
        and coz_tavan_profil("kuran") == "tilavet"
        and coz_tavan_profil("alim") == "alim"
    )
    return {
        "version": S1_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "snapshot": snap,
        "rates": rates,
        "pitches": pitches,
        "distinct_ok": distinct,
        "alias_ok": alias_ok,
        "s1_yesil": bool(distinct and alias_ok and len(snap["profiller"]) == 3),
        "sonraki": "S2 — prosodi + tilavet/âlim parametre tavanı (kulak)",
    }


def write_s1_docs(card: dict[str, Any] | None = None) -> dict[str, str]:
    payload = card or run_s1_card()
    docs = Path(__file__).resolve().parents[1] / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    js = docs / "S1_SES_TAVAN_PROFIL_2026-11-21.json"
    md = docs / "S1_SES_TAVAN_PROFIL_2026-11-21.md"
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    snap = payload.get("snapshot") or {}
    lines = [
        "# S1 — Ses tavanı üç profil (Edge) — 2026-11-21",
        "",
        f"`{payload.get('version')}` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`",
        "",
        "## Yeşil koşul",
        "",
        "Sohbette / API’de `karakter` = **muhabbet | alim | tilavet** (asistan→muhabbet).",
        "",
        f"**S1 yeşil:** {'EVET' if payload.get('s1_yesil') else 'HAYIR'}",
        "",
        "## Profiller",
        "",
        "| Tavan | Edge karakter | Voice | Rate | Pitch |",
        "|-------|---------------|-------|------|-------|",
    ]
    for p in TAVAN_PROFILLER:
        d = (snap.get("profiller") or {}).get(p) or {}
        lines.append(
            f"| {p} | {d.get('karakter')} | {d.get('voice')} | {d.get('rate')} | {d.get('pitch')} |"
        )
    lines += [
        "",
        f"- Alias OK: {payload.get('alias_ok')}",
        f"- Rate/pitch ayrımı: {payload.get('distinct_ok')}",
        f"- Aktif tavan: {snap.get('aktif_tavan')} (kayıt: {snap.get('aktif_kayit')})",
        "",
        "## Araçlar",
        "",
        "- `ilim_assistant/ses_s1_tavan_profil.py`",
        "- `scripts/smoke_s1_ses_tavan_profil.py`",
        "",
        "## Sonraki",
        "",
        "**S2** — prosodi + tilavet/âlim parametre tavanı (kulak onayı).",
        "",
        "*Ümit & Gökçenur Haymana'nın ortak projesi.*",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(js), "md": str(md)}
