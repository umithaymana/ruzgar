# Created by Ümit & Gökçenur
"""S0 — Ses tavanı ölçüm kartı: şimdi robot / ilk-byte / mobil eşitlik tabanı.

Boot / yüz / hub dokunulmaz. Canlı Edge ölçümü opsiyonel (RUZGAR_S0_LIVE=1).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

S0_VERSION = "ses-s0-tavan-olcum-v1-2026-11-21"

# Mühürlü referanslar (ezilmez)
V0_TTS_FIRST_BYTE_REF_MS = 1686.0
V0_STT_WARM_REF_MS = 10288.0
V3_MEASURED_FIRST_BYTE_MS = 820.0  # V3 mühür notu (bu makine, kısa cümle)
V3_TARGET_FIRST_BYTE_MS = 900.0
ASAMA_D_KEEP_MS = 886.0

# Tavan hedef (S1+); S0 yalnız ölçer
TAVAN_PROFILLER_HEDEF = ("muhabbet", "alim", "tilavet")
TAVAN_PROFIL_OPSIYON = "anlatici"

_LAST: dict[str, Any] = {}


def s0_enabled() -> bool:
    return os.environ.get("RUZGAR_SES_S0", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def last_s0_report() -> dict[str, Any]:
    return dict(_LAST)


def _docs_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "docs"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sealed_refs() -> dict[str, Any]:
    return {
        "v0_tts_first_byte_ms": V0_TTS_FIRST_BYTE_REF_MS,
        "v0_stt_warm_ms": V0_STT_WARM_REF_MS,
        "v3_measured_first_byte_ms": V3_MEASURED_FIRST_BYTE_MS,
        "v3_target_first_byte_ms": V3_TARGET_FIRST_BYTE_MS,
        "asama_d_keep_ms": ASAMA_D_KEEP_MS,
        "docs": {
            "v0": "docs/V0_STT_TTS_BASELINE_2026-10-23.md",
            "v3": "docs/V3_TTS_ILK_BYTE_2026-11-03.md",
            "v5": "docs/V5_FAZ_V_MUHUR_2026-11-03.md",
        },
    }


def profile_gap_snapshot() -> dict[str, Any]:
    """Şimdiki Edge profiller vs tavan hedef (muhabbet/âlim/tilavet)."""
    from ilim_assistant.ses_f7_kalite import profile_ton_snapshot

    snap = profile_ton_snapshot()
    mevcut = sorted(snap.get("profiller") or {})
    # Kabaca eşleme notu (S1 işi; S0 yalnız kart)
    esleme = {
        "muhabbet": "asistan (şimdi)",
        "alim": "alim (şimdi; hadis/tefsir vakur — tilavet ayrı değil)",
        "tilavet": "yok ayrı profil — ses_tilavet + /api/tts/tilavet iskelet",
        "anlatici": "edip yakın / S1+ opsiyon",
    }
    return {
        "aktif": snap.get("aktif"),
        "mevcut_edge_profiller": mevcut,
        "tavan_hedef": list(TAVAN_PROFILLER_HEDEF),
        "tavan_opsiyon": TAVAN_PROFIL_OPSIYON,
        "esleme_not": esleme,
        "gap": [p for p in TAVAN_PROFILLER_HEDEF if p not in mevcut],
        "detail": snap,
    }


def robot_checklist() -> dict[str, Any]:
    """Objektif «robot hissi» yapı kontrolü — kulak skoru Mimar’a kalır."""
    root = Path(__file__).resolve().parents[1] / "ilim_assistant"
    motor = root / "motorlar"
    checks = {
        "ses_prosody": (motor / "ses_prosody.py").is_file(),
        "ses_tilavet": (motor / "ses_tilavet.py").is_file(),
        "ses_klon_motoru": (motor / "ses_klon_motoru.py").is_file(),
        "ses_v3_ilk_byte": (root / "ses_v3_tts_ilk_byte.py").is_file(),
        "ses_v4_barge_in": (root / "ses_v4_barge_in.py").is_file(),
        "ses_f7_kalite": (root / "ses_f7_kalite.py").is_file(),
    }
    n_ok = sum(1 for v in checks.values() if v)
    # 0–5 yapı skoru (kulak ayrı)
    yapi = round(5.0 * n_ok / max(1, len(checks)), 2)
    return {
        "yapi_skoru_0_5": yapi,
        "checks": checks,
        "kulak_skoru_0_5": None,
        "kulak_not": "Mimar kulak onayı S1+ mühür için zorunlu; S0 skor bırakmaz.",
        "robot_hissi_ozet": (
            "Edge neural + prosody/tilavet iskelet var; tavan profil ayrımı (S1) ve "
            "klon referansı (S3) gelmeden robot hissi yüksek kalabilir."
        ),
    }


def mobil_esitlik_snapshot() -> dict[str, Any]:
    """Masaüstü ↔ mobil aynı TTS API / barge sözleşmesi."""
    from ilim_assistant.ses_v4_barge_in import (
        verify_mobil_barge_markers,
        verify_ui_barge_in_markers,
    )

    desk = verify_ui_barge_in_markers()
    mob = verify_mobil_barge_markers()
    mobil_js = (
        Path(__file__).resolve().parents[1] / "static" / "mobil-pwa" / "app.js"
    )
    desk_js = _repo_root() / "ruzgar-desktop" / "app.js"
    mobil_txt = mobil_js.read_text(encoding="utf-8") if mobil_js.is_file() else ""
    desk_txt = desk_js.read_text(encoding="utf-8") if desk_js.is_file() else ""
    ayni_api = ("/api/tts" in mobil_txt) and ("/api/tts" in desk_txt)
    return {
        "ayni_api_tts": ayni_api,
        "desktop_barge_ok": bool(desk.get("ok")),
        "mobil_barge_ok": bool(mob.get("ok")),
        "esitlik_ok": bool(ayni_api and desk.get("ok") and mob.get("ok")),
        "desktop": {
            "ok": desk.get("ok"),
            "missing": desk.get("missing") or [],
        },
        "mobil": {
            "ok": mob.get("ok"),
            "missing": mob.get("missing") or [],
        },
        "not": "Canlı kulak mobil=PC ölçümü S1+; S0 sözleşme/marker tabanı.",
    }


def clone_tilavet_snapshot() -> dict[str, Any]:
    from ilim_assistant.ses_f7_kalite import clone_policy_snapshot

    clone = clone_policy_snapshot()
    tilavet_wav: str | None = None
    try:
        from ilim_assistant.motorlar.ses_klon_motoru import coz_tilavet_referans_yolu

        p = coz_tilavet_referans_yolu("kuran", ayar={})
        tilavet_wav = str(p) if p is not None else None
    except Exception as exc:
        tilavet_wav = f"err:{exc}"[:120]
    return {
        "clone": clone,
        "tilavet_referans_wav": tilavet_wav,
        "mimar_kilit": {
            "klon": "kız sesi — WhatsApp’tan PC’ye Mimar aktarır; usta WA’ya bağlanmaz",
            "tilavet_wav": "arsiv/ses-referans/kuran.wav kullan (Mimar 2026-11-21)",
        },
    }


def measure_live_tts(*, force: bool | None = None) -> dict[str, Any]:
    """Edge first-byte canlı ölçüm. Varsayılan: RUZGAR_S0_LIVE=1 iken."""
    live = force
    if live is None:
        live = os.environ.get("RUZGAR_S0_LIVE", "0").strip().lower() not in (
            "0",
            "false",
            "no",
            "off",
            "",
        )
    out: dict[str, Any] = {
        "ran": False,
        "ok": False,
        "first_byte_ms": None,
        "total_ms": None,
        "vs_v0": None,
        "vs_v3_target": None,
        "note": "skip (RUZGAR_S0_LIVE=0)",
    }
    if not live:
        return out
    try:
        import asyncio

        from ilim_assistant.ses_f7_kalite import measure_tts_first_byte_f7

        res = asyncio.run(measure_tts_first_byte_f7())
        out["ran"] = True
        out["ok"] = bool(res.get("ok"))
        out["first_byte_ms"] = res.get("first_byte_ms")
        out["total_ms"] = res.get("total_ms")
        out["attempts"] = res.get("attempts")
        out["note"] = res.get("note") or ""
        out["vs_v0"] = res.get("vs_v0")
        fb = out["first_byte_ms"]
        if fb is not None:
            out["vs_v3_target"] = {
                "under_target": float(fb) <= V3_TARGET_FIRST_BYTE_MS,
                "delta_to_target_ms": round(V3_TARGET_FIRST_BYTE_MS - float(fb), 1),
            }
    except Exception as exc:
        out["ran"] = True
        out["note"] = str(exc)[:200]
    return out


def run_s0_card(*, live_tts: bool | None = None) -> dict[str, Any]:
    global _LAST
    report: dict[str, Any] = {
        "version": S0_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "enabled": s0_enabled(),
        "basari_cumlesi": (
            "Kur’an’da huşû; hadis/tefsirde vakur; sohbette doğal; "
            "video aynı ses omurgası — mobil = PC."
        ),
        "sealed_refs": sealed_refs(),
        "robot": robot_checklist(),
        "profiller": profile_gap_snapshot(),
        "mobil_esitlik": mobil_esitlik_snapshot(),
        "klon_tilavet": clone_tilavet_snapshot(),
        "tts_live": measure_live_tts(force=live_tts),
        "sonraki": "S1 — üç profil seçici (muhabbet / âlim / tilavet) Edge üzerinde",
    }
    # Özet skor kartı
    mob = report["mobil_esitlik"]
    live = report["tts_live"]
    report["ozet"] = {
        "yapi_robot_0_5": report["robot"]["yapi_skoru_0_5"],
        "mobil_esitlik_ok": mob.get("esitlik_ok"),
        "profil_gap": report["profiller"].get("gap"),
        "tts_first_byte_ms": live.get("first_byte_ms"),
        "tts_live_ran": live.get("ran"),
        "s0_yesil": bool(
            s0_enabled()
            and mob.get("esitlik_ok")
            and report["robot"]["yapi_skoru_0_5"] >= 4.0
        ),
    }
    _LAST = report
    return report


def write_s0_docs(report: dict[str, Any] | None = None) -> dict[str, str]:
    """Ölçüm kartını docs’a yazar (S0 mühür kartı — yeniden ölçüm aynı dosyaya)."""
    payload = report or run_s0_card()
    docs = _docs_dir()
    docs.mkdir(parents=True, exist_ok=True)
    js_path = docs / "S0_SES_TAVAN_OLCUM_2026-11-21.json"
    md_path = docs / "S0_SES_TAVAN_OLCUM_2026-11-21.md"
    js_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    o = payload.get("ozet") or {}
    refs = payload.get("sealed_refs") or {}
    robot = payload.get("robot") or {}
    prof = payload.get("profiller") or {}
    mob = payload.get("mobil_esitlik") or {}
    live = payload.get("tts_live") or {}
    klon = payload.get("klon_tilavet") or {}

    lines = [
        "# S0 — Ses tavanı ölçüm kartı — 2026-11-21",
        "",
        f"`{payload.get('version')}` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`",
        "",
        "## Başarı cümlesi",
        "",
        payload.get("basari_cumlesi") or "",
        "",
        "## Özet",
        "",
        "| Alan | Değer |",
        "|------|-------|",
        f"| Yapı robot skoru (0–5) | **{o.get('yapi_robot_0_5')}** |",
        f"| Kulak skoru | _(Mimar — S1+)_ |",
        f"| Mobil eşitlik (sözleşme) | **{'YEŞİL' if o.get('mobil_esitlik_ok') else 'KIRMIZI'}** |",
        f"| Profil gap (tavan) | `{', '.join(o.get('profil_gap') or [])}` |",
        f"| TTS live first-byte | {live.get('first_byte_ms') if live.get('ran') else 'ölçülmedi (LIVE=0)'} |",
        f"| S0 yeşil | **{'EVET' if o.get('s0_yesil') else 'HAYIR'}** |",
        "",
        "## Mühürlü referanslar (ezilmez)",
        "",
        "| Ref | ms |",
        "|-----|-----|",
        f"| V0 TTS first-byte | {refs.get('v0_tts_first_byte_ms')} |",
        f"| V0 STT warm | {refs.get('v0_stt_warm_ms')} |",
        f"| V3 ölçülen first-byte | {refs.get('v3_measured_first_byte_ms')} |",
        f"| V3 hedef üstü | {refs.get('v3_target_first_byte_ms')} |",
        f"| Aşama D keep | {refs.get('asama_d_keep_ms')} |",
        "",
        "## Robot / yapı",
        "",
        robot.get("robot_hissi_ozet") or "",
        "",
        "```",
        json.dumps(robot.get("checks") or {}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Profiller (şimdi → tavan)",
        "",
        f"- Mevcut Edge: `{', '.join(prof.get('mevcut_edge_profiller') or [])}`",
        f"- Tavan hedef: `{', '.join(prof.get('tavan_hedef') or [])}`",
        f"- Gap: `{', '.join(prof.get('gap') or [])}` → **S1**",
        "",
        "## Mobil = PC",
        "",
        f"- Aynı `/api/tts`: {mob.get('ayni_api_tts')}",
        f"- Desktop barge: {mob.get('desktop_barge_ok')}",
        f"- Mobil barge: {mob.get('mobil_barge_ok')}",
        "",
        "## Klon / tilavet WAV",
        "",
        f"- Tilavet referans: `{klon.get('tilavet_referans_wav')}`",
        f"- Mimar kilit: {json.dumps(klon.get('mimar_kilit') or {}, ensure_ascii=False)}",
        "",
        "## Canlı TTS",
        "",
        f"- ran={live.get('ran')} ok={live.get('ok')} first_byte_ms={live.get('first_byte_ms')}",
        f"- note: {live.get('note')}",
        "",
        "## Araçlar",
        "",
        "- `ilim_assistant/ses_s0_olcum.py`",
        "- `scripts/smoke_s0_ses_tavan.py`",
        "- Canlı ölçüm: `RUZGAR_S0_LIVE=1`",
        "",
        "## Sonraki",
        "",
        "**S1** — üç profil seçici (muhabbet / âlim / tilavet) Edge üzerinde.",
        "",
        "*Ümit & Gökçenur Haymana'nın ortak projesi.*",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(js_path), "md": str(md_path)}
