# Created by Ümit & Gökçenur
"""S4 — Okuma bağ: raftan kısa pasaj → sesle oku (masa + mobil aynı API).

Üzerine ekler: ruzgar_kutuphane + /api/tts (+ S1–S3 profil/prosodi/klon).
Boot / ana yüz / hub dokunulmaz.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

S4_VERSION = "ses-s4-okuma-bag-v1-2026-11-21"

# Kısa pasaj tavanı (kulak + mobil paket)
_DEFAULT_MAX_CHARS = 420
_HARD_MAX_CHARS = 900
_READ_WINDOW = 6000

# Oturum içi devam offset (process-local; istemci offset de gönderebilir)
_OTURUM: dict[str, dict[str, Any]] = {}


def s4_enabled() -> bool:
    return os.environ.get("RUZGAR_SES_S4", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    t = t.replace("ı", "i").replace("İ", "i")
    return re.sub(r"\s+", " ", t)


def _temiz_tts(text: str) -> str:
    """Markdown gürültüsünü azalt; TTS için düz metin."""
    t = text or ""
    t = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[*`_]+", "", t)
    t = re.sub(r"(?m)^\s*[-*•]\s+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _cumle_kes(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    window = t[: max_chars + 1]
    for sep in (". ", "! ", "? ", "۔ ", "؛ ", "; ", ", ", " "):
        idx = window.rfind(sep)
        if idx >= max(40, max_chars // 3):
            return window[: idx + len(sep)].strip()
    return window[:max_chars].rstrip() + "…"


def coz_okuma_karakter(
    query: str,
    *,
    pasaj: str = "",
    raf_ad: str = "",
    eser_id: str = "",
    action: str = "oku",
    override: str | None = None,
) -> str:
    """Kitap okuma → âlim; Kur’an izi → tilavet; husulu → tilavet; yavas → alim."""
    from ilim_assistant.ses_s1_tavan_profil import coz_tavan_profil

    if override:
        return coz_tavan_profil(override)
    act = _fold(action)
    if act in ("husulu", "husu", "huşûlu", "husulu", "daha husulu", "daha huşûlu"):
        return "tilavet"
    blob = _fold(" ".join([query, pasaj[:200], raf_ad, eser_id]))
    if re.search(
        r"\b(kuran|quran|ayet|sure|sûre|tilavet|tecvid|fatiha|bakara)\b",
        blob,
    ):
        return "tilavet"
    try:
        from ilim_assistant.okuma_motoru import kategorize_metin_parcastipi

        kod, _ = kategorize_metin_parcastipi(pasaj or query)
        if kod == "hadis":
            return "alim"
    except Exception:
        pass
    return "alim"


def _normalize_action(raw: str | None) -> str:
    a = _fold(raw or "oku")
    if a in ("devam", "devam et", "sonraki", "ileri"):
        return "devam"
    if a in ("tekrar", "yeniden", "bir daha", "tekrar oku"):
        return "tekrar"
    if a in ("yavas", "yavaş", "daha yavas", "daha yavaş"):
        return "yavas"
    if a in ("husulu", "husu", "huşûlu", "daha husulu", "daha huşûlu", "husulu oku"):
        return "husulu"
    return "oku"


def _coz_eser(query: str, *, yol: str | None = None, eser_id: str | None = None) -> dict[str, Any] | None:
    from ilim_assistant.ruzgar_kutuphane import load_katalog, search_kutuphane

    if yol:
        return {
            "id": eser_id or Path_stem(yol),
            "yol": yol,
            "raf_ad": "",
            "basliklar": [],
            "skor": 1.0,
        }
    if eser_id:
        kat = load_katalog()
        for eser in kat.get("eserler") or []:
            if str(eser.get("id") or "") == eser_id:
                return dict(eser)
    q = (query or "").strip()
    if not q:
        return None
    hits = search_kutuphane(q, limit=5)
    return dict(hits[0]) if hits else None


def Path_stem(yol: str) -> str:
    name = (yol or "").replace("\\", "/").rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[0] if name else "eser"


def prepare_okuma_ses(
    query: str = "",
    *,
    action: str = "oku",
    yol: str | None = None,
    eser_id: str | None = None,
    offset: int | None = None,
    max_chars: int | None = None,
    karakter: str | None = None,
    session_id: str = "default",
) -> dict[str, Any]:
    """Raftan kısa pasaj hazırla (TTS çağırmaz)."""
    if not s4_enabled():
        return {"ok": False, "error": "S4 kapalı (RUZGAR_SES_S4=0)", "version": S4_VERSION}

    from ilim_assistant.ruzgar_kutuphane import kutuphane_enabled, read_eser_excerpt

    if not kutuphane_enabled():
        return {"ok": False, "error": "Kütüphane kapalı (RUZGAR_KUTUPHANE=0)", "version": S4_VERSION}

    act = _normalize_action(action)
    lim = max(120, min(int(max_chars or _DEFAULT_MAX_CHARS), _HARD_MAX_CHARS))
    sid = (session_id or "default").strip()[:80] or "default"
    prev = _OTURUM.get(sid) or {}

    # tekrar / yavas / husulu: aynı pasajı profil bayrağıyla yeniden
    if act in ("tekrar", "yavas", "husulu") and prev.get("pasaj"):
        pasaj = str(prev.get("pasaj") or "")
        eser = {
            "id": prev.get("eser_id"),
            "yol": prev.get("yol"),
            "raf_ad": prev.get("raf_ad"),
            "basliklar": prev.get("basliklar") or [],
        }
        off = int(prev.get("offset") or 0)
        next_off = int(prev.get("next_offset") or off)
        q_used = str(prev.get("query") or query)
    else:
        q_used = (query or "").strip() or str(prev.get("query") or "")
        if act == "devam" and not q_used and not yol and not eser_id:
            q_used = str(prev.get("query") or "")
            yol = yol or prev.get("yol")
            eser_id = eser_id or prev.get("eser_id")

        eser = _coz_eser(q_used, yol=yol, eser_id=eser_id)
        if not eser or not eser.get("yol"):
            return {
                "ok": False,
                "error": f"«{q_used or '(boş)'}» için rafta eser bulunamadı.",
                "version": S4_VERSION,
                "action": act,
            }

        raw = read_eser_excerpt(str(eser.get("yol") or ""), max_chars=_READ_WINDOW)
        clean = _temiz_tts(raw)
        if len(clean) < 20:
            return {
                "ok": False,
                "error": "Eser metni okunamadı veya çok kısa.",
                "version": S4_VERSION,
                "eser_id": eser.get("id"),
                "yol": eser.get("yol"),
            }

        if offset is not None:
            off = max(0, int(offset))
        elif act == "devam":
            off = int(prev.get("next_offset") or 0)
            # aynı eser devamı
            if prev.get("yol") and prev.get("yol") != eser.get("yol"):
                off = 0
        else:
            off = 0

        if off >= len(clean):
            return {
                "ok": False,
                "error": "Pasaj bitti — başa dönmek için tekrar / oku.",
                "version": S4_VERSION,
                "eser_id": eser.get("id"),
                "yol": eser.get("yol"),
                "offset": off,
                "bitti": True,
            }

        slice_txt = clean[off:]
        pasaj = _cumle_kes(slice_txt, lim)
        next_off = off + len(pasaj)
        # cümle kesmesi … ile bitince ilerlemeyi garanti et
        if next_off <= off:
            next_off = min(len(clean), off + lim)

    kar = coz_okuma_karakter(
        q_used,
        pasaj=pasaj,
        raf_ad=str(eser.get("raf_ad") or ""),
        eser_id=str(eser.get("id") or ""),
        action=act,
        override=karakter,
    )
    if act == "yavas" and kar == "alim":
        # yavaş = âlim profili + istemci/API'ye yavas bayrağı (S2 huzur)
        pass

    baslik = ""
    bl = eser.get("basliklar") or []
    if isinstance(bl, list) and bl:
        baslik = str(bl[0])

    out: dict[str, Any] = {
        "ok": True,
        "version": S4_VERSION,
        "action": act,
        "query": q_used,
        "pasaj": pasaj,
        "chars": len(pasaj),
        "karakter": kar,
        "eser_id": eser.get("id"),
        "yol": eser.get("yol"),
        "raf_ad": eser.get("raf_ad") or "",
        "baslik": baslik,
        "offset": off if act != "tekrar" else int(prev.get("offset") or 0),
        "next_offset": next_off if act != "tekrar" else int(prev.get("next_offset") or 0),
        "yavas": act == "yavas",
        "husulu": act == "husulu" or kar == "tilavet",
        "tts_hint": {
            "endpoint": "/api/tts",
            "karakter": kar,
            "prosody": kar in ("alim", "tilavet"),
            "backend": "auto",
        },
        "mobil_ayni_api": True,
    }

    _OTURUM[sid] = {
        "query": q_used,
        "pasaj": pasaj,
        "eser_id": out["eser_id"],
        "yol": out["yol"],
        "raf_ad": out["raf_ad"],
        "basliklar": eser.get("basliklar") or [],
        "offset": out["offset"],
        "next_offset": out["next_offset"],
        "karakter": kar,
        "action": act,
    }
    return out


def parse_okuma_ses_komut(message: str) -> dict[str, Any] | None:
    """Sohbet / mobil: «raftan oku fotosentez» · «sesle oku raftan: osmanlı»."""
    raw = (message or "").strip()
    if not raw or len(raw) > 400:
        return None
    m = re.match(
        r"(?is)^\s*(?:"
        r"raftan\s+(?:sesle\s+)?oku|"
        r"kitaptan\s+(?:sesle\s+)?oku|"
        r"kütüphaneden\s+(?:sesle\s+)?oku|"
        r"kutuphaneden\s+(?:sesle\s+)?oku|"
        r"sesle\s+oku\s+raftan|"
        r"raf(?:tan)?\s+oku"
        r")\s*[:\-]?\s*(.+?)\s*$",
        raw,
    )
    if not m:
        # devam / tekrar / yavaş / huşûlu (kısa komut)
        low = _fold(raw)
        if low in (
            "devam oku",
            "okumaya devam",
            "raftan devam",
            "devam et oku",
            "tekrar oku",
            "daha yavas oku",
            "daha yavaş oku",
            "daha husulu oku",
            "daha huşûlu oku",
        ):
            act = "oku"
            if "devam" in low:
                act = "devam"
            elif "tekrar" in low:
                act = "tekrar"
            elif "yavas" in low or "yavaş" in low:
                act = "yavas"
            elif "husu" in low or "huşû" in low:
                act = "husulu"
            return {"query": "", "action": act, "kind": "okuma_ses"}
        return None
    q = (m.group(1) or "").strip()
    if len(q) < 2:
        return None
    return {"query": q[:200], "action": "oku", "kind": "okuma_ses"}


def run_s4_card() -> dict[str, Any]:
    from ilim_assistant.ruzgar_kutuphane import kutuphane_enabled, kutuphane_status

    st = kutuphane_status() if kutuphane_enabled() else {"enabled": False, "eser_sayisi": 0}
    demo_q = "fotosentez"
    prep = prepare_okuma_ses(demo_q, action="oku", session_id="_s4_smoke") if st.get("enabled") else {
        "ok": False,
        "error": "kutuphane kapali",
    }
    # devam smoke (aynı oturum)
    devam = (
        prepare_okuma_ses(demo_q, action="devam", session_id="_s4_smoke")
        if prep.get("ok")
        else {"ok": False}
    )
    tekrar = (
        prepare_okuma_ses(action="tekrar", session_id="_s4_smoke")
        if prep.get("ok")
        else {"ok": False}
    )

    ds = Path_read_ds()
    api_ok = all(
        m in ds
        for m in (
            "/api/okuma/pasaj",
            "/api/okuma/sesle",
            "prepare_okuma_ses",
            "ses_s4_okuma_bag",
        )
    )
    desk = Path_read_desk()
    mob = Path_read_mobil()
    masa_ok = "speakRaftanPasaj" in desk or "okuma/sesle" in desk
    mobil_ok = "speakRaftanPasaj" in mob or "okuma/pasaj" in mob or "okuma/sesle" in mob

    yesil = bool(
        st.get("enabled")
        and prep.get("ok")
        and len(str(prep.get("pasaj") or "")) >= 40
        and prep.get("karakter") in ("alim", "tilavet", "muhabbet")
        and api_ok
        and masa_ok
        and mobil_ok
    )
    return {
        "version": S4_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "kutuphane": {
            "enabled": bool(st.get("enabled")),
            "eser_sayisi": st.get("eser_sayisi"),
        },
        "demo": {
            "query": demo_q,
            "ok": bool(prep.get("ok")),
            "chars": prep.get("chars"),
            "karakter": prep.get("karakter"),
            "eser_id": prep.get("eser_id"),
            "baslik": prep.get("baslik"),
            "pasaj_onizleme": (str(prep.get("pasaj") or ""))[:160],
        },
        "devam_ok": bool(devam.get("ok") and devam.get("offset", 0) > 0),
        "tekrar_ok": bool(
            tekrar.get("ok") and tekrar.get("pasaj") == devam.get("pasaj")
        ),
        "api_hooks": api_ok,
        "masa_hook": masa_ok,
        "mobil_hook": mobil_ok,
        "s4_yesil": yesil,
        "kulak_liste": [
            "Raftan kısa pasaj — âlim edası doğal mı?",
            "Devam / tekrar aynı yerden mi?",
            "Mobil + masa aynı pasaj / profil?",
        ],
        "sonraki": "V1 — video dublaj omurga profili · veya kulak turu S0–S4",
    }


def Path_read_ds() -> str:
    from pathlib import Path

    p = Path(__file__).resolve().parents[1] / "desktop_server.py"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def Path_read_desk() -> str:
    from pathlib import Path

    # repo kökü: YAPAY ZEKA / ruzgar-desktop
    root = Path(__file__).resolve().parents[2]
    p = root / "ruzgar-desktop" / "app.js"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def Path_read_mobil() -> str:
    from pathlib import Path

    p = Path(__file__).resolve().parents[1] / "static" / "mobil-pwa" / "app.js"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def write_s4_docs(card: dict[str, Any] | None = None) -> dict[str, str]:
    from pathlib import Path

    payload = card or run_s4_card()
    docs = Path(__file__).resolve().parents[1] / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    js = docs / "S4_OKUMA_SES_BAG_2026-11-21.json"
    md = docs / "S4_OKUMA_SES_BAG_2026-11-21.md"
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    d = payload.get("demo") or {}
    lines = [
        "# S4 — Okuma bağ (raftan kısa pasaj sesle oku) — 2026-11-21",
        "",
        f"`{payload.get('version')}` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`",
        "",
        f"**S4 yeşil:** {'EVET' if payload.get('s4_yesil') else 'HAYIR'}  ",
        "",
        "Raftan eser → kısa pasaj → S1–S3 profil/prosodi/klon omurgası (`/api/tts`).",
        "",
        "## Davranış",
        "",
        "1. `POST /api/okuma/pasaj` — pasaj + karakter (TTS yok)",
        "2. `POST /api/okuma/sesle` — pasaj + Edge/klon MP3 (FileResponse)",
        "3. Aksiyonlar: `oku` · `devam` · `tekrar` · `yavas` · `husulu`",
        "4. Masa + mobil aynı API (`mobil_ayni_api`)",
        "",
        "## Demo",
        "",
        f"- Sorgu: `{d.get('query')}` → eser `{d.get('eser_id')}` · karakter **{d.get('karakter')}**",
        f"- Başlık: {d.get('baslik')}",
        f"- Pasaj önizleme: {(d.get('pasaj_onizleme') or '')[:120]}…",
        f"- devam_ok: {payload.get('devam_ok')} · tekrar_ok: {payload.get('tekrar_ok')}",
        "",
        "## Kulak checklist (Mimar)",
        "",
    ]
    for i, item in enumerate(payload.get("kulak_liste") or [], 1):
        lines.append(f"{i}. {item}")
    lines.extend(
        [
            "",
            "## Araçlar",
            "",
            "- `ilim_assistant/ses_s4_okuma_bag.py`",
            "- `scripts/smoke_s4_okuma_ses_bag.py`",
            "",
            "## Sonraki",
            "",
            str(payload.get("sonraki") or "V1 / kulak"),
            "",
            "*Ümit & Gökçenur Haymana'nın ortak projesi.*",
            "",
        ]
    )
    md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(js), "md": str(md)}
