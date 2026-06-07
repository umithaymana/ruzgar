# Created by Ümit & Gökçenur
"""Ses klon kütüphanesi — kolonlanmış referans sesler + motor eşlemesi (sohbet/tilavet/okuma)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.ses_klon_motoru import (
    _REPO_ROOT,
    kaydet_referans_upload,
    referans_klasoru,
)

MIMAR = "Ümit & Gökçenur"
KOLON_VERSION = "ses-kolon-v1-2026-06-07"
_MOTORLAR = ("sohbet", "tilavet", "okuma")
_STORE = Path(__file__).resolve().parents[2] / ".ruzgar_ses_kolonlari.json"

_DEFAULT_SEED = (
    ("kuran", "Kuran tilavet", "kuran.wav"),
    ("gazel", "Gazel okuma", "gazel.wav"),
    ("ilahi", "Ilahi / tasavvuf", "ilahi.wav"),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(raw: str) -> str:
    s = (raw or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:48] or f"ses-{uuid.uuid4().hex[:8]}"


def _empty_store() -> dict[str, Any]:
    return {
        "version": KOLON_VERSION,
        "mimarlar": MIMAR,
        "kolonlar": [],
        "aktif": {m: None for m in _MOTORLAR},
    }


def load_kutuphane() -> dict[str, Any]:
    if not _STORE.is_file():
        data = _empty_store()
        seed_from_referans_klasoru(data)
        save_kutuphane(data)
        return data
    try:
        data = json.loads(_STORE.read_text(encoding="utf-8"))
    except Exception:
        data = _empty_store()
    if not isinstance(data.get("kolonlar"), list):
        data["kolonlar"] = []
    aktif = data.get("aktif") if isinstance(data.get("aktif"), dict) else {}
    data["aktif"] = {m: aktif.get(m) for m in _MOTORLAR}
    data["version"] = KOLON_VERSION
    return data


def save_kutuphane(data: dict[str, Any]) -> Path:
    out = dict(data)
    out["version"] = KOLON_VERSION
    out["mimarlar"] = MIMAR
    kolonlar = out.get("kolonlar")
    if not isinstance(kolonlar, list):
        kolonlar = []
    out["kolonlar"] = kolonlar
    aktif = out.get("aktif") if isinstance(out.get("aktif"), dict) else {}
    out["aktif"] = {m: aktif.get(m) for m in _MOTORLAR}
    _STORE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return _STORE


def seed_from_referans_klasoru(data: dict[str, Any] | None = None) -> list[str]:
    """arsiv/ses-referans/*.wav → kütüphane (eksikse)."""
    store = data if data is not None else load_kutuphane()
    kolonlar: list[dict[str, Any]] = list(store.get("kolonlar") or [])
    ids = {str(k.get("id")) for k in kolonlar}
    added: list[str] = []
    ref_dir = referans_klasoru()
    for slug, ad, fname in _DEFAULT_SEED:
        if slug in ids:
            continue
        p = ref_dir / fname
        if not p.is_file() or p.stat().st_size < 4096:
            continue
        try:
            rel = p.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
        except ValueError:
            rel = p.as_posix()
        motors = {"sohbet": False, "tilavet": slug == "kuran", "okuma": False}
        if slug == "gazel":
            motors = {"sohbet": False, "tilavet": True, "okuma": True}
        if slug == "ilahi":
            motors = {"sohbet": True, "tilavet": True, "okuma": False}
        kolonlar.append(
            {
                "id": slug,
                "ad": ad,
                "wav_rel": rel,
                "motors": motors,
                "created_at": _now_iso(),
            }
        )
        ids.add(slug)
        added.append(slug)
    store["kolonlar"] = kolonlar
    aktif = store.get("aktif") or {}
    if not aktif.get("tilavet") and "kuran" in ids:
        aktif["tilavet"] = "kuran"
    store["aktif"] = {m: aktif.get(m) for m in _MOTORLAR}
    if data is None:
        save_kutuphane(store)
    return added


def find_kolon(kolon_id: str, store: dict[str, Any] | None = None) -> dict[str, Any] | None:
    kid = (kolon_id or "").strip()
    if not kid:
        return None
    for k in store.get("kolonlar") or [] if store else load_kutuphane().get("kolonlar") or []:
        if str(k.get("id")) == kid:
            return k
    return None


def kolon_wav_path(kolon: dict[str, Any]) -> Path | None:
    rel = str(kolon.get("wav_rel") or "").strip()
    if not rel:
        return None
    p = Path(rel)
    if p.is_absolute():
        target = p
    else:
        target = (_REPO_ROOT / rel).resolve()
    if target.is_file() and target.stat().st_size > 4096:
        return target
    return None


def coz_aktif_kolon_wav(motor: str, ayar: dict[str, Any] | None = None) -> Path | None:
    """Aktif kolon → wav (sohbet / tilavet / okuma)."""
    from ilim_assistant.tts_service import read_ses_ayarlari

    m = (motor or "").strip().lower()
    if m not in _MOTORLAR:
        return None
    ay = ayar or read_ses_ayarlari()
    kid = (ay.get("kolon_aktif") or {}).get(m) or (load_kutuphane().get("aktif") or {}).get(m)
    if not kid:
        return None
    kolon = find_kolon(str(kid))
    if not kolon:
        return None
    return kolon_wav_path(kolon)


def coz_aktif_kolon_rel(motor: str, ayar: dict[str, Any] | None = None) -> str | None:
    p = coz_aktif_kolon_wav(motor, ayar=ayar)
    if not p:
        return None
    try:
        return p.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def list_kolonlar_snapshot() -> dict[str, Any]:
    store = load_kutuphane()
    seed_from_referans_klasoru(store)
    save_kutuphane(store)
    rows: list[dict[str, Any]] = []
    for k in store.get("kolonlar") or []:
        wav = kolon_wav_path(k)
        rows.append(
            {
                "id": k.get("id"),
                "ad": k.get("ad"),
                "wav_rel": k.get("wav_rel"),
                "wav_ok": bool(wav),
                "size_kb": (wav.stat().st_size // 1024) if wav else 0,
                "motors": dict(k.get("motors") or {}),
                "created_at": k.get("created_at"),
            }
        )
    return {
        "ok": True,
        "version": KOLON_VERSION,
        "kolonlar": rows,
        "aktif": dict(store.get("aktif") or {}),
        "motors": list(_MOTORLAR),
    }


def add_kolon_from_upload(
    ad: str,
    src_path: Path,
    *,
    kolon_id: str | None = None,
    motors: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Yeni kolon — wav arsiv/ses-referans/kolon-{id}.wav."""
    store = load_kutuphane()
    kid = _slugify(kolon_id or ad)
    existing = {str(k.get("id")) for k in store.get("kolonlar") or []}
    base = kid
    n = 2
    while kid in existing:
        kid = f"{base}-{n}"
        n += 1
    ref_dir = referans_klasoru()
    ref_dir.mkdir(parents=True, exist_ok=True)
    out = ref_dir / f"kolon-{kid}.wav"
    from ilim_assistant.motorlar.ses_klon_motoru import normalize_reference_to_wav

    normalize_reference_to_wav(src_path.resolve(), out)
    try:
        rel = out.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        rel = out.as_posix()
    mot = {m: False for m in _MOTORLAR}
    if motors:
        for m in _MOTORLAR:
            mot[m] = bool(motors.get(m))
    entry = {
        "id": kid,
        "ad": (ad or kid).strip()[:120],
        "wav_rel": rel,
        "motors": mot,
        "created_at": _now_iso(),
    }
    store.setdefault("kolonlar", []).append(entry)
    save_kutuphane(store)
    return entry


def delete_kolon(kolon_id: str) -> bool:
    store = load_kutuphane()
    kid = (kolon_id or "").strip()
    before = len(store.get("kolonlar") or [])
    store["kolonlar"] = [k for k in store.get("kolonlar") or [] if str(k.get("id")) != kid]
    if len(store["kolonlar"]) == before:
        return False
    aktif = store.get("aktif") or {}
    for m in _MOTORLAR:
        if aktif.get(m) == kid:
            aktif[m] = None
    store["aktif"] = aktif
    save_kutuphane(store)
    return True


def uygula_motor_eslemesi(aktif: dict[str, str | None]) -> dict[str, Any]:
    """Seçilen kolonları kaydet + ses ayarlarına referans yollarını yaz."""
    from ilim_assistant.tts_service import read_ses_ayarlari, write_ses_ayarlari

    store = load_kutuphane()
    clean: dict[str, str | None] = {}
    for m in _MOTORLAR:
        v = aktif.get(m)
        clean[m] = str(v).strip() if v else None
        if clean[m]:
            if not find_kolon(clean[m], store):
                raise ValueError(f"Kolon bulunamadı: {clean[m]} ({m})")
            if not kolon_wav_path(find_kolon(clean[m], store) or {}):
                raise ValueError(f"Kolon ses dosyası yok: {clean[m]}")

    store["aktif"] = clean
    save_kutuphane(store)

    ayar = read_ses_ayarlari()
    refs = dict(ayar.get("referans") or {})
    for m in _MOTORLAR:
        kid = clean.get(m)
        if not kid:
            continue
        kolon = find_kolon(kid, store)
        if kolon and kolon_wav_path(kolon):
            refs[f"kolon_{m}"] = kolon.get("wav_rel")
            if m == "tilavet" and kid in ("kuran", "gazel", "ilahi"):
                refs[kid] = kolon.get("wav_rel")
    write_ses_ayarlari({"referans": refs, "kolon_aktif": clean})
    return list_kolonlar_snapshot()
