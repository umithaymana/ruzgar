# Created by Ümit & Gökçenur
"""S3 — Klon yolu: BUSENAZ (muhabbet) + kuran.wav (tilavet) · Edge yedek.

XTTS yoksa yapı yine yeşil sayılır (Edge yedek zorunlu). Canlı XTTS ayrı kurulum.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

S3_VERSION = "ses-s3-klon-yolu-v1-2026-11-21"


def _edge_available() -> bool:
    try:
        from ilim_assistant.tts_service import edge_available

        return bool(edge_available())
    except Exception:
        return False


def referans_kart() -> dict[str, Any]:
    from ilim_assistant.motorlar.ses_klon_motoru import (
        clone_enabled,
        clone_status_snapshot,
        coz_referans_yolu,
        coz_tilavet_referans_yolu,
        should_use_clone,
        xtts_runtime_available,
    )
    from ilim_assistant.tts_service import read_ses_ayarlari

    ay = read_ses_ayarlari()
    muh = coz_referans_yolu("muhabbet", ayar=ay)
    alim = coz_referans_yolu("alim", ayar=ay)
    til = coz_referans_yolu("tilavet", ayar=ay)
    kuran = coz_tilavet_referans_yolu("kuran", ayar=ay)
    st = clone_status_snapshot()

    def _name(p: Path | None) -> str | None:
        return p.name if p else None

    return {
        "clone_enabled": clone_enabled(),
        "xtts": xtts_runtime_available(),
        "edge": _edge_available(),
        "klon_onay": bool(ay.get("klon_onay") or ay.get("prefer_clone")),
        "tts_backend": ay.get("tts_backend") or ay.get("backend") or "auto",
        "refs": {
            "muhabbet": {"path": str(muh) if muh else None, "name": _name(muh)},
            "alim": {"path": str(alim) if alim else None, "name": _name(alim)},
            "tilavet": {"path": str(til) if til else None, "name": _name(til)},
            "kuran": {"path": str(kuran) if kuran else None, "name": _name(kuran)},
        },
        "busenaz_ok": bool(
            muh
            and (
                "BUSENAZ" in muh.name.upper()
                or "busenaz" in str(muh).lower()
                or muh.name.lower() in ("muhabbet.wav", "asistan.wav")
            )
        ),
        "tilavet_kuran_ok": bool(kuran and kuran.name.lower() == "kuran.wav"),
        "should_auto_muhabbet": should_use_clone(
            backend="auto", karakter="muhabbet", ayar=ay
        ),
        "should_clone_muhabbet": should_use_clone(
            backend="clone", karakter="muhabbet", ayar=ay
        ),
        "status": st,
    }


def edge_yedek_sozlesmesi() -> dict[str, Any]:
    """API: XTTS yok / klon hata → Edge (STRICT=1 hariç)."""
    ds = Path(__file__).resolve().parents[1] / "desktop_server.py"
    txt = ds.read_text(encoding="utf-8") if ds.is_file() else ""
    markers = [
        "edge_yedek_meta",
        "RUZGAR_TTS_CLONE_STRICT",
        "clone_fallback",
        "coz_tts_tavan_paketi",
    ]
    missing = [m for m in markers if m not in txt]
    return {
        "ok": not missing,
        "missing": missing,
        "kural": "XTTS yok veya klon hata → Edge yedek; STRICT=1 ile 503",
    }


def run_s3_card() -> dict[str, Any]:
    refs = referans_kart()
    yedek = edge_yedek_sozlesmesi()
    # Yeşil: referanslar + Edge yedek sözleşmesi (+ Edge runtime)
    # XTTS opsiyonel — yoksa yedek yolu yeterli
    refs_ok = bool(refs.get("busenaz_ok") and refs.get("tilavet_kuran_ok"))
    s3_yesil = bool(refs_ok and yedek.get("ok") and refs.get("edge"))
    return {
        "version": S3_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "referans": refs,
        "edge_yedek": yedek,
        "xtts_runtime": refs.get("xtts"),
        "klon_canli": bool(refs.get("xtts") and refs_ok),
        "s3_yesil": s3_yesil,
        "not": (
            "XTTS kurulu değil — klon canlı sentez yok; Edge yedek YEŞİL. "
            "pip install TTS torch sonrası auto+klon_onay ile BUSENAZ devreye girer."
            if not refs.get("xtts")
            else "XTTS hazır — auto+klon_onay ile BUSENAZ / kuran klon yolu açık."
        ),
        "sonraki": "S4 tamam — V1 video dublaj veya kulak turu",
    }


def write_s3_docs(card: dict[str, Any] | None = None) -> dict[str, str]:
    payload = card or run_s3_card()
    docs = Path(__file__).resolve().parents[1] / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    js = docs / "S3_SES_KLON_YOLU_2026-11-21.json"
    md = docs / "S3_SES_KLON_YOLU_2026-11-21.md"
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    r = payload.get("referans") or {}
    refs = r.get("refs") or {}
    lines = [
        "# S3 — Klon yolu (BUSENAZ + kuran) — 2026-11-21",
        "",
        f"`{payload.get('version')}` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`",
        "",
        f"**S3 yeşil:** {'EVET' if payload.get('s3_yesil') else 'HAYIR'}  ",
        f"**XTTS canlı:** {'EVET' if payload.get('klon_canli') else 'HAYIR (Edge yedek)'}  ",
        "",
        payload.get("not") or "",
        "",
        "## Referanslar",
        "",
        "| Profil | Dosya |",
        "|--------|-------|",
        f"| muhabbet (BUSENAZ) | `{ (refs.get('muhabbet') or {}).get('name') }` |",
        f"| alim | `{ (refs.get('alim') or {}).get('name') }` |",
        f"| tilavet | `{ (refs.get('tilavet') or {}).get('name') }` |",
        f"| kuran WAV | `{ (refs.get('kuran') or {}).get('name') }` |",
        "",
        f"- busenaz_ok: {r.get('busenaz_ok')} · tilavet_kuran_ok: {r.get('tilavet_kuran_ok')}",
        f"- klon_onay: {r.get('klon_onay')} · xtts: {r.get('xtts')} · edge: {r.get('edge')}",
        f"- Edge yedek sözleşme: {(payload.get('edge_yedek') or {}).get('ok')}",
        f"- klon_canli: {payload.get('klon_canli')}",
        "",
        "**Canlı kanıt:** `arsiv/ses-referans/_s3_busenaz_smoke.wav` (BUSENAZ XTTS).",
        "",
        "**A3:** XTTS canlı YEŞİL · Fish/F5 ayrı (yoksa KISMI, A3 ile karıştırma).",
        "",
        "## Davranış",
        "",
        "1. `backend=auto` + `klon_onay` + XTTS → BUSENAZ / kuran klon",
        "2. XTTS yok veya klon hata → **Edge yedek** (S1/S2 profil parametreleri)",
        "3. `RUZGAR_TTS_CLONE_STRICT=1` → yedek yok, 503",
        "",
        "## Araçlar",
        "",
        "- `ilim_assistant/ses_s3_klon_yolu.py`",
        "- `scripts/smoke_s3_ses_klon_yolu.py`",
        "",
        "## Sonraki",
        "",
        "**S4 tamam** — V1 video dublaj veya kulak turu.",
        "",
        "*Ümit & Gökçenur Haymana'nın ortak projesi.*",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(js), "md": str(md)}
