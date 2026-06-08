# Created by Ümit & Gökçenur
"""Ses klon kütüphanesi — halka açık + Ümit özel depolar, motor eşlemesi, ince ayar."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from ilim_assistant.motorlar.ses_klon_motoru import (
    _REPO_ROOT,
    referans_klasoru,
)

MIMAR = "Ümit & Gökçenur"
KOLON_VERSION = "ses-kolon-v2-2026-06-08"
_MOTORLAR = ("sohbet", "tilavet", "okuma")
Scope = Literal["halka", "ozel"]

_ILIM_ROOT = Path(__file__).resolve().parents[2]
HALKA_DIR = _ILIM_ROOT / "arsiv" / "klon-sesler"
OZEL_DIR = _ILIM_ROOT / "arsiv" / "klon-sesler-umit-ozel"
_STORE_HALKA = _ILIM_ROOT / ".ruzgar_ses_kolonlari.json"
_STORE_OZEL = _ILIM_ROOT / ".ruzgar_ses_kolonlari_ozel.json"

_DEFAULT_TUNING: dict[str, Any] = {
    "hiz": 0.92,
    "huzur": 0.88,
    "durak": 1.0,
    "lang": "tr",
    "tilavet_mod": False,
    "prosody": True,
}

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


def _normalize_scope(scope: str | None) -> Scope:
    s = (scope or "halka").strip().lower()
    return "ozel" if s in ("ozel", "özel", "private", "umit") else "halka"


def _store_path(scope: Scope) -> Path:
    return _STORE_OZEL if scope == "ozel" else _STORE_HALKA


def _wav_dir(scope: Scope) -> Path:
    d = OZEL_DIR if scope == "ozel" else HALKA_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _empty_store() -> dict[str, Any]:
    return {
        "version": KOLON_VERSION,
        "mimarlar": MIMAR,
        "scope": "halka",
        "kolonlar": [],
        "aktif": {m: None for m in _MOTORLAR},
    }


def load_kutuphane(scope: Scope | None = None) -> dict[str, Any]:
    sc = _normalize_scope(scope)
    store_file = _store_path(sc)
    if not store_file.is_file():
        data = _empty_store()
        data["scope"] = sc
        if sc == "halka":
            seed_from_referans_klasoru(data)
        save_kutuphane(data, scope=sc)
        return data
    try:
        data = json.loads(store_file.read_text(encoding="utf-8"))
    except Exception:
        data = _empty_store()
    if not isinstance(data.get("kolonlar"), list):
        data["kolonlar"] = []
    aktif = data.get("aktif") if isinstance(data.get("aktif"), dict) else {}
    data["aktif"] = {m: aktif.get(m) for m in _MOTORLAR}
    data["version"] = KOLON_VERSION
    data["scope"] = sc
    return data


def save_kutuphane(data: dict[str, Any], *, scope: Scope | None = None) -> Path:
    sc = _normalize_scope(scope or data.get("scope"))
    out = dict(data)
    out["version"] = KOLON_VERSION
    out["mimarlar"] = MIMAR
    out["scope"] = sc
    kolonlar = out.get("kolonlar")
    if not isinstance(kolonlar, list):
        kolonlar = []
    out["kolonlar"] = kolonlar
    if sc == "halka":
        aktif = out.get("aktif") if isinstance(out.get("aktif"), dict) else {}
        out["aktif"] = {m: aktif.get(m) for m in _MOTORLAR}
    else:
        out.pop("aktif", None)
    path = _store_path(sc)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def seed_from_referans_klasoru(data: dict[str, Any] | None = None) -> list[str]:
    """arsiv/ses-referans/*.wav → halka kütüphane (eksikse)."""
    store = data if data is not None else load_kutuphane("halka")
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
                "scope": "halka",
                "motors": motors,
                "tuning": dict(_DEFAULT_TUNING),
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
        save_kutuphane(store, scope="halka")
    return added


def _kolon_row(k: dict[str, Any], scope: Scope) -> dict[str, Any]:
    wav = kolon_wav_path(k)
    tuning = dict(_DEFAULT_TUNING)
    if isinstance(k.get("tuning"), dict):
        tuning.update(k["tuning"])
    return {
        "id": k.get("id"),
        "ad": k.get("ad"),
        "scope": scope,
        "wav_rel": k.get("wav_rel"),
        "wav_ok": bool(wav),
        "size_kb": (wav.stat().st_size // 1024) if wav else 0,
        "motors": dict(k.get("motors") or {}),
        "tuning": tuning,
        "created_at": k.get("created_at"),
    }


def find_kolon(
    kolon_id: str,
    store: dict[str, Any] | None = None,
    *,
    scope: Scope | None = None,
) -> dict[str, Any] | None:
    kid = (kolon_id or "").strip()
    if not kid:
        return None
    if store is not None:
        for k in store.get("kolonlar") or []:
            if str(k.get("id")) == kid:
                return {**k, "scope": _normalize_scope(store.get("scope") or scope)}
    if scope:
        sc = _normalize_scope(scope)
        st = load_kutuphane(sc)
        for k in st.get("kolonlar") or []:
            if str(k.get("id")) == kid:
                return {**k, "scope": sc}
        return None
    for sc in ("halka", "ozel"):
        st = load_kutuphane(sc)
        for k in st.get("kolonlar") or []:
            if str(k.get("id")) == kid:
                return {**k, "scope": sc}
    return None


def kolon_wav_path(kolon: dict[str, Any]) -> Path | None:
    rel = str(kolon.get("wav_rel") or "").strip()
    if not rel:
        return None
    p = Path(rel)
    target = p.resolve() if p.is_absolute() else (_REPO_ROOT / rel).resolve()
    if target.is_file() and target.stat().st_size > 4096:
        return target
    return None


def kolon_tuning(kolon: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(_DEFAULT_TUNING)
    if kolon and isinstance(kolon.get("tuning"), dict):
        out.update(kolon["tuning"])
    return out


def save_kolon_tuning(kolon_id: str, tuning: dict[str, Any], *, scope: Scope) -> dict[str, Any]:
    sc = _normalize_scope(scope)
    store = load_kutuphane(sc)
    kid = (kolon_id or "").strip()
    found = False
    for k in store.get("kolonlar") or []:
        if str(k.get("id")) != kid:
            continue
        cur = kolon_tuning(k)
        for key in ("hiz", "huzur", "durak", "lang", "tilavet_mod", "prosody"):
            if key in tuning and tuning[key] is not None:
                if key in ("hiz", "huzur"):
                    cur[key] = max(0.45, min(1.0, float(tuning[key])))
                elif key == "durak":
                    cur[key] = max(0.55, min(1.6, float(tuning[key])))
                elif key == "lang":
                    cur[key] = str(tuning[key]).strip().lower()[:2] or "tr"
                else:
                    cur[key] = bool(tuning[key])
        k["tuning"] = cur
        found = True
        break
    if not found:
        raise ValueError(f"Kolon bulunamadı: {kid} ({sc})")
    save_kutuphane(store, scope=sc)
    return kolon_tuning(find_kolon(kid, store, scope=sc))


def coz_aktif_kolon_wav(motor: str, ayar: dict[str, Any] | None = None) -> Path | None:
    from ilim_assistant.tts_service import read_ses_ayarlari

    m = (motor or "").strip().lower()
    if m not in _MOTORLAR:
        return None
    ay = ayar or read_ses_ayarlari()
    kid = (ay.get("kolon_aktif") or {}).get(m) or (load_kutuphane("halka").get("aktif") or {}).get(m)
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


def list_kolonlar_snapshot(*, include_ozel: bool = True) -> dict[str, Any]:
    store_h = load_kutuphane("halka")
    seed_from_referans_klasoru(store_h)
    save_kutuphane(store_h, scope="halka")
    rows: list[dict[str, Any]] = []
    for k in store_h.get("kolonlar") or []:
        rows.append(_kolon_row(k, "halka"))
    if include_ozel:
        store_o = load_kutuphane("ozel")
        for k in store_o.get("kolonlar") or []:
            rows.append(_kolon_row(k, "ozel"))
    return {
        "ok": True,
        "version": KOLON_VERSION,
        "kolonlar": rows,
        "aktif": dict(store_h.get("aktif") or {}),
        "motors": list(_MOTORLAR),
        "depolar": {
            "halka": {
                "label": "Klon sesler (halka açık)",
                "dir": HALKA_DIR.relative_to(_ILIM_ROOT).as_posix(),
                "commit": True,
            },
            "ozel": {
                "label": "Klon sesler — Ümit özel",
                "dir": OZEL_DIR.relative_to(_ILIM_ROOT).as_posix(),
                "commit": False,
            },
        },
    }


def add_kolon_from_upload(
    ad: str,
    src_path: Path,
    *,
    kolon_id: str | None = None,
    motors: dict[str, bool] | None = None,
    scope: Scope | str = "halka",
) -> dict[str, Any]:
    sc = _normalize_scope(str(scope))
    store = load_kutuphane(sc)
    kid = _slugify(kolon_id or ad)
    existing = {str(k.get("id")) for k in store.get("kolonlar") or []}
    base = kid
    n = 2
    while kid in existing:
        kid = f"{base}-{n}"
        n += 1
    out_dir = _wav_dir(sc)
    out = out_dir / f"{kid}.wav"
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
        "scope": sc,
        "motors": mot,
        "tuning": dict(_DEFAULT_TUNING),
        "created_at": _now_iso(),
    }
    store.setdefault("kolonlar", []).append(entry)
    save_kutuphane(store, scope=sc)
    return entry


def delete_kolon(kolon_id: str, *, scope: Scope | None = None) -> bool:
    kid = (kolon_id or "").strip()
    if scope:
        sc = _normalize_scope(scope)
        store = load_kutuphane(sc)
        before = len(store.get("kolonlar") or [])
        store["kolonlar"] = [k for k in store.get("kolonlar") or [] if str(k.get("id")) != kid]
        if len(store["kolonlar"]) == before:
            return False
        if sc == "halka":
            aktif = store.get("aktif") or {}
            for m in _MOTORLAR:
                if aktif.get(m) == kid:
                    aktif[m] = None
            store["aktif"] = aktif
        save_kutuphane(store, scope=sc)
        return True
    deleted = delete_kolon(kid, scope="halka") or delete_kolon(kid, scope="ozel")
    return deleted


def uygula_motor_eslemesi(aktif: dict[str, str | None]) -> dict[str, Any]:
    from ilim_assistant.tts_service import read_ses_ayarlari, write_ses_ayarlari

    store = load_kutuphane("halka")
    clean: dict[str, str | None] = {}
    for m in _MOTORLAR:
        v = aktif.get(m)
        clean[m] = str(v).strip() if v else None
        if clean[m]:
            kolon = find_kolon(clean[m])
            if not kolon:
                raise ValueError(f"Kolon bulunamadı: {clean[m]} ({m})")
            if not kolon_wav_path(kolon):
                raise ValueError(f"Kolon ses dosyası yok: {clean[m]}")

    store["aktif"] = clean
    save_kutuphane(store, scope="halka")

    ayar = read_ses_ayarlari()
    refs = dict(ayar.get("referans") or {})
    for m in _MOTORLAR:
        kid = clean.get(m)
        if not kid:
            continue
        kolon = find_kolon(kid)
        if kolon and kolon_wav_path(kolon):
            refs[f"kolon_{m}"] = kolon.get("wav_rel")
            if m == "tilavet" and kid in ("kuran", "gazel", "ilahi"):
                refs[kid] = kolon.get("wav_rel")
    write_ses_ayarlari({"referans": refs, "kolon_aktif": clean})
    return list_kolonlar_snapshot()
