# -*- coding: utf-8 -*-
"""Sahne harita — evrensel yer adı → lat/lon/zoom/tip (Anayasa FROZEN).

Üretim yolu sabit lokasyon tablosuna BAĞLI DEĞİLDİR.
Geocode: öğrenilmiş disk önbellek + Photon (birincil) + Open-Meteo + Nominatim (yedek).
Kamera: tip (sınıf) profili. Örnek koordinatlar yalnız test dosyalarında.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Tip → zoom (sınıf; yer adı değil)
TIP_ZOOM: dict[str, int] = {
    "ulke": 7,
    "il": 11,
    "ilce": 13,
    "mahalle": 15,
    "dag": 14,
    "gecit": 16,
    "vadi": 13,
    "kanyon": 14,
    "gol": 12,
    "nehir": 11,
    "bogaz": 14,
    "volkan": 14,
    "selale": 15,
    "delta": 10,
    "col": 9,
    "ada": 12,
    "sirt": 13,
    "kopru": 17,
    "bina": 18,
    "nokta": 18,
    "sehir": 12,
}

# Sınıf kamera başlangıcı — yer adına bağlı değil (Anayasa §2/§6)
CAMERA_BY_TIP: dict[str, dict[str, float]] = {
    "ulke": {"heading": 0, "pitch": -40, "range_m": 800000},
    "il": {"heading": 35, "pitch": -30, "range_m": 2500},
    "sehir": {"heading": 40, "pitch": -22, "range_m": 90},
    "ilce": {"heading": 40, "pitch": -24, "range_m": 200},
    "mahalle": {"heading": 50, "pitch": -22, "range_m": 120},
    "nehir": {"heading": 8, "pitch": -20, "range_m": 60},
    "bogaz": {"heading": 18, "pitch": -20, "range_m": 90},
    "gol": {"heading": 20, "pitch": -24, "range_m": 200},
    "dag": {"heading": 200, "pitch": -22, "range_m": 220},
    "volkan": {"heading": 210, "pitch": -22, "range_m": 180},
    "kanyon": {"heading": 250, "pitch": -20, "range_m": 100},
    "vadi": {"heading": 140, "pitch": -22, "range_m": 120},
    "ada": {"heading": 90, "pitch": -22, "range_m": 150},
    "gecit": {"heading": 120, "pitch": -20, "range_m": 140},
    "sirt": {"heading": 180, "pitch": -22, "range_m": 180},
    "selale": {"heading": 160, "pitch": -20, "range_m": 80},
    "delta": {"heading": 30, "pitch": -24, "range_m": 160},
    "col": {"heading": 0, "pitch": -28, "range_m": 300},
    "kopru": {"heading": 90, "pitch": -20, "range_m": 80},
    "bina": {"heading": 180, "pitch": -22, "range_m": 80},
    "nokta": {"heading": 0, "pitch": -22, "range_m": 100},
}

# Biçimsel ekler (yer listesi değil)
_INFLECT_SUFFIX: frozenset[str] = frozenset(
    {
        "dagi",
        "dag",
        "daglari",
        "daglar",
        "nehri",
        "nehir",
        "river",
        "adasi",
        "ada",
        "yanardagi",
        "yanardag",
        "volcano",
        "kulesi",
        "kule",
        "tower",
        "koprusu",
        "kopru",
        "bridge",
        "gecidi",
        "gecit",
        "mountain",
        "peak",
        "strait",
        "bogazi",
        "bogaz",
        "canyon",
        "kanyonu",
        "golu",
        "lake",
        "island",
    }
)

# Üretimde boş — sabit dünya noktası yok (Anayasa §2)
# İsteğe bağlı acil önbellek: RUZGAR_GEO_LOCAL_CACHE=1 + dışarıdan doldurma
_YEREL: dict[str, dict[str, Any]] = {}

# Öğrenilmiş önbellek (Nominatim/Photon başarısından yazılır — sabit tablo değil)
_GEO_DISK_PATH = Path(__file__).resolve().parents[1] / "hafiza" / "geo_learned_cache.json"
_GEO_DISK: dict[str, dict[str, Any]] = {}
_GEO_DISK_LOADED = False
_NETWORK_BUDGET = max(1, int(os.environ.get("RUZGAR_GEO_NET_BUDGET", "3") or "3"))
_PHOTON_LAST_TS = 0.0
_NOMINATIM_BLOCKED_UNTIL = 0.0

# Biçimsel onarım (yer adı değil)
_REPAIR: dict[str, str] = {
    "koprus": "kopru",
    "gecid": "gecit",
}


def _norm_key(s: str) -> str:
    from ilim_assistant.sahne_super_el import _norm

    t = _norm(s)
    t = t.replace("'", "").replace("'", "").replace("-", " ")
    t = " ".join(t.split())
    return t.replace(" ", "")


def zoom_for_tip(tip: str | None, fallback: int = 11) -> int:
    if not tip:
        return fallback
    return int(TIP_ZOOM.get(str(tip).lower(), fallback))


def camera_for_tip(tip: str | None, lat: float | None = None, lon: float | None = None) -> dict[str, Any]:
    """Sınıf tabanlı kamera başlangıcı — herhangi bir dünya noktası için."""
    t = str(tip or "nokta").lower()
    base = dict(CAMERA_BY_TIP.get(t) or CAMERA_BY_TIP["nokta"])
    out: dict[str, Any] = {
        "heading": float(base.get("heading", 0)),
        "pitch": float(base.get("pitch", -28)),
        "range_m": float(base.get("range_m", 200)),
    }
    if lat is not None:
        out["lat"] = float(lat)
    if lon is not None:
        out["lon"] = float(lon)
    return out


def infer_tip_from_text(hedef: str) -> str | None:
    """Metin ipuçlarından tip — doğal sınıflar; yer listesi yok."""
    if not hedef:
        return None
    from ilim_assistant.sahne_super_el import _norm

    n = _norm(hedef)
    compact = n.replace(" ", "")
    if re.search(r"\b(ulke|country|nation)\b", n):
        return "ulke"
    try:
        from ilim_assistant.sahne_dunya_gezgini import classify_nature_tip

        nat = classify_nature_tip(hedef, n)
        if nat:
            return nat
    except Exception:
        pass
    if re.search(r"\b(gecit|gecidi|gecid|pass)\b", n) or "gecit" in compact:
        return "gecit"
    if re.search(r"\b(kopru|koprusu|bridge)\b", n) or "kopru" in compact:
        return "kopru"
    if (
        re.search(r"\b(bogaz|bogazi|bosphorus|bosporus|strait)\b", n)
        or "bogaz" in compact
        or "strait" in compact
    ) and "kopru" not in compact:
        return "bogaz"
    if (
        re.search(r"\b(dag|dagi|daglar|mountain|peak)\b", n)
        or compact.endswith("dag")
        or compact.endswith("dagi")
    ):
        return "dag"
    if re.search(
        r"\b(cami|camii|kilise|katedral|saray|kule|muze|bina|tower)\b",
        n,
    ) or "kulesi" in compact:
        return "bina"
    if re.search(r"\b(mahalle|mah|semt|quarter|neighbourhood|neighborhood)\b", n):
        return "mahalle"
    if re.search(r"\b(ilce|ilcesi|district|county)\b", n):
        return "ilce"
    if re.search(r"\b(il|ili|sehir|city|province|town)\b", n):
        return "il"
    return None


def tip_from_osm(osm_class: str, osm_type: str, hedef: str) -> str:
    text_tip = infer_tip_from_text(hedef)
    if text_tip:
        return text_tip
    kind = (osm_type or "").lower()
    cls = (osm_class or "").lower()
    if kind in ("country", "nation"):
        return "ulke"
    if kind in ("state", "province", "region"):
        return "il"
    if kind in ("city", "town"):
        return "il"
    if kind in ("county", "district", "municipality", "borough"):
        return "ilce"
    if kind in ("suburb", "neighbourhood", "neighborhood", "quarter", "city_block", "residential"):
        return "mahalle"
    if kind in ("village", "hamlet", "locality"):
        return "ilce"
    if kind in ("volcano",) or (cls == "natural" and kind == "volcano"):
        return "volkan"
    if kind in ("peak", "mountain") or (cls == "natural" and kind in ("peak", "mountain")):
        return "dag"
    if kind in ("ridge",) or (cls == "natural" and kind == "ridge"):
        return "sirt"
    if kind in ("pass", "saddle") or "saddle" in kind:
        return "gecit"
    if kind in ("valley",) or (cls == "natural" and kind == "valley"):
        return "vadi"
    if kind in ("canyon", "gorge", "ravine") or (cls == "natural" and kind in ("canyon", "gorge")):
        return "kanyon"
    if kind in ("strait", "channel", "sound") or (cls == "natural" and kind in ("strait", "bay")):
        return "bogaz"
    if kind in ("river", "stream", "canal") or cls == "waterway":
        return "nehir"
    if kind in ("lake", "reservoir", "lagoon", "pond") or (
        cls == "natural" and kind in ("water", "lake")
    ):
        return "gol"
    if kind in ("waterfall", "falls") or (cls == "waterway" and kind == "waterfall"):
        return "selale"
    if kind in ("island", "islet", "archipelago") or (cls == "place" and kind == "island"):
        return "ada"
    if kind in ("desert", "dune", "sand") or (cls == "natural" and kind in ("desert", "dune", "sand")):
        return "col"
    if kind in ("bridge",) or (cls == "man_made" and kind == "bridge"):
        return "kopru"
    if cls in ("building", "tourism", "historic", "amenity") or kind in (
        "attraction",
        "museum",
        "yes",
        "cathedral",
        "mosque",
        "church",
        "palace",
        "tower",
    ):
        return "bina"
    if cls == "place" and kind in ("city", "town"):
        return "il"
    try:
        from ilim_assistant.sahne_dunya_gezgini import classify_nature_tip

        nat = classify_nature_tip(hedef, kind, tip_hint=kind)
        if nat:
            return nat
    except Exception:
        pass
    return "nokta"


def bbox_from_center(lat: float, lon: float, zoom: int) -> list[float]:
    z = max(2, min(18, int(zoom)))
    span = 360.0 / (2**z)
    span_lat = span * 0.55
    span_lon = span * 0.75
    return [
        round(lon - span_lon / 2, 5),
        round(lat - span_lat / 2, 5),
        round(lon + span_lon / 2, 5),
        round(lat + span_lat / 2, 5),
    ]


def _attach_camera(out: dict[str, Any], query: str = "") -> dict[str, Any]:
    tip = str(out.get("tip") or infer_tip_from_text(query) or "nokta")
    out["camera"] = camera_for_tip(tip, out.get("lat"), out.get("lon"))
    return out


def _finalize(hit: dict[str, Any], *, query: str = "") -> dict[str, Any]:
    out = dict(hit)
    tip = out.get("tip") or infer_tip_from_text(query) or infer_tip_from_text(str(out.get("label") or ""))
    if not tip:
        tip = "nokta"
    out["tip"] = tip
    out["zoom"] = zoom_for_tip(tip, int(out.get("zoom") or TIP_ZOOM.get(tip, 11)))
    if not out.get("bbox"):
        out["bbox"] = bbox_from_center(float(out["lat"]), float(out["lon"]), int(out["zoom"]))
    return _attach_camera(out, query)


_GEO_VERB_TAIL = re.compile(
    r"\s+(goster|ac|odaklan|odakla|yaklastir|uzaklastir|git|getir|yansit|"
    r"gezdir|gezgini|gezisi|gezi|turu|tur|haritasini|haritasi)\s*$",
    re.I,
)


def _strip_geo_verbs(hedef: str) -> str:
    from ilim_assistant.sahne_super_el import _norm

    t = (hedef or "").strip()
    if not t:
        return ""
    n = _norm(t)
    prev = None
    while prev != n:
        prev = n
        n = _GEO_VERB_TAIL.sub("", n).strip()
    return n or t


def _query_variants(hedef: str) -> list[str]:
    raw = (hedef or "").strip()
    if not raw:
        return []
    from ilim_assistant.sahne_super_el import _norm, _strip_case_suffix

    variants: list[str] = []

    def add(x: str | None) -> None:
        t = (x or "").strip()
        if t and t not in variants:
            variants.append(t)

    stripped = _strip_geo_verbs(raw)
    add(raw)
    add(stripped)
    add(_norm(raw))
    add(_norm(stripped))
    for base in (stripped, raw):
        parts = _norm(base).split()
        if not parts:
            continue
        stemmed = " ".join(_strip_case_suffix(p) for p in parts)
        add(stemmed)
        add(_norm_key(stemmed))
    compact = _norm_key(stripped or raw)
    add(compact)
    if compact in _REPAIR:
        add(_REPAIR[compact])
    for a, b in (
        ("gecidi", " gecidi"),
        ("gecit", " gecit"),
        ("koprusu", " koprusu"),
        ("kopru", " kopru"),
        ("dagi", " dagi"),
        ("dag", " dag"),
        ("nehri", " nehri"),
        ("bogazi", " bogazi"),
        ("kanyonu", " kanyonu"),
        ("adasi", " adasi"),
        ("golu", " golu"),
        ("kulesi", " kulesi"),
    ):
        if compact.endswith(a) and len(compact) > len(a) + 2:
            add(compact[: -len(a)] + b)
    if compact.endswith("gecid"):
        add(compact + "i")
        add(compact[:-5] + " gecidi" if len(compact) > 5 else compact)
    return variants


def _ensure_disk_cache() -> None:
    global _GEO_DISK_LOADED, _GEO_DISK
    if _GEO_DISK_LOADED:
        return
    _GEO_DISK_LOADED = True
    try:
        if _GEO_DISK_PATH.is_file():
            raw = json.loads(_GEO_DISK_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                _GEO_DISK = {str(k): v for k, v in raw.items() if isinstance(v, dict)}
    except Exception:
        _GEO_DISK = {}


def _remember_geo(hedef: str, geo: dict[str, Any]) -> None:
    """Başarılı ağ sonucunu öğren — sabit şehir listesi değil."""
    if not geo or geo.get("lat") is None or geo.get("lon") is None:
        return
    _ensure_disk_cache()
    keys = {_norm_key(v) for v in _query_variants(hedef) if _norm_key(v)}
    label = str(geo.get("label") or "")
    if label:
        keys.add(_norm_key(label.split(",")[0]))
    payload = {
        "lat": float(geo["lat"]),
        "lon": float(geo["lon"]),
        "zoom": int(geo.get("zoom") or zoom_for_tip(geo.get("tip"))),
        "tip": geo.get("tip") or "nokta",
        "label": geo.get("label") or hedef,
        "source": "learned",
    }
    if geo.get("bbox"):
        payload["bbox"] = geo["bbox"]
    changed = False
    for k in keys:
        if not k or len(k) < 2:
            continue
        prev = _GEO_DISK.get(k)
        if prev and abs(float(prev.get("lat", 0)) - payload["lat"]) < 1e-5:
            continue
        _GEO_DISK[k] = payload
        changed = True
    if not changed:
        return
    try:
        _GEO_DISK_PATH.parent.mkdir(parents=True, exist_ok=True)
        _GEO_DISK_PATH.write_text(
            json.dumps(_GEO_DISK, ensure_ascii=False, indent=0),
            encoding="utf-8",
        )
    except Exception:
        pass


def geocode_disk(hedef: str) -> dict[str, Any] | None:
    """Öğrenilmiş disk önbelleği — Anayasa: sabit üretim tablosu değil."""
    if os.environ.get("RUZGAR_GEO_DISK_CACHE", "1").strip() in ("0", "false", "no"):
        return None
    _ensure_disk_cache()
    if not _GEO_DISK or not hedef:
        return None
    for cand in _query_variants(hedef):
        key = _norm_key(cand)
        hit = _GEO_DISK.get(key)
        if hit and hit.get("lat") is not None:
            out = _finalize(hit, query=hedef)
            out["source"] = "learned"
            return out
    return None


def geocode_local(hedef: str) -> dict[str, Any] | None:
    """Opsiyonel boş önbellek — varsayılan kapalı (Anayasa: sabit tablo yok)."""
    if os.environ.get("RUZGAR_GEO_LOCAL_CACHE", "0").strip() not in ("1", "true", "yes"):
        return None
    if not hedef or not _YEREL:
        return None
    for cand in _query_variants(hedef):
        key = _norm_key(cand)
        if not key:
            continue
        hit = _YEREL.get(key)
        if hit:
            out = _finalize(hit, query=hedef)
            out["source"] = "local"
            return out
        best = None
        best_score = -1
        for k, v in _YEREL.items():
            score = -1
            if key == k:
                score = 100000 + len(k)
            elif key.startswith(k) and len(k) >= 4:
                rest = key[len(k) :]
                if not rest or rest in _INFLECT_SUFFIX:
                    score = 10000 + len(k)
            elif k.startswith(key) and len(key) >= 5:
                score = 100 + len(key)
            if score > best_score:
                best_score = score
                best = v
        if best is not None and best_score >= 0:
            out = _finalize(best, query=hedef)
            out["source"] = "local"
            return out
    return None


def _class_query_suffixes(tip: str | None) -> list[str]:
    """Sınıfa göre evrensel sorgu ekleri — ülke/şehir listesi yok."""
    t = (tip or "").lower()
    if t in ("dag",):
        return ["mountain", "peak", "dağ", "dagi"]
    if t in ("volkan",):
        return ["volcano", "yanardağ", "yanardagi"]
    if t in ("nehir",):
        return ["river", "nehri"]
    if t in ("gol",):
        return ["lake", "gölü", "golu"]
    if t in ("kanyon",):
        return ["canyon", "kanyonu"]
    if t in ("bogaz",):
        return ["strait", "boğazı", "bogazi"]
    if t in ("ada",):
        return ["island", "adası", "adasi"]
    if t in ("gecit",):
        return ["pass", "geçidi", "gecidi"]
    if t in ("selale",):
        return ["waterfall", "falls"]
    if t in ("col",):
        return ["desert"]
    if t in ("vadi",):
        return ["valley", "vadisi"]
    if t in ("kopru",):
        return ["bridge", "köprüsü"]
    if t in ("bina",):
        return ["tower", "monument"]
    return []


def _nominatim_queries(hedef: str) -> list[str]:
    """Sınıf-bilinçli evrensel sorgular — sabit yer özel yolu yok."""
    from ilim_assistant.sahne_super_el import _norm

    raw = _strip_geo_verbs((hedef or "").strip())
    if not raw:
        return []
    n = _norm(raw)
    out: list[str] = []

    def add(x: str) -> None:
        t = (x or "").strip()
        if t and t not in out:
            out.append(t)

    text_tip = infer_tip_from_text(raw)
    for v in _query_variants(raw):
        add(v)
    add(raw)
    add(n)
    for suf in _class_query_suffixes(text_tip):
        add(f"{raw} {suf}")
        add(f"{n} {suf}")
    # Çıplak ad (tip yok): az sayıda evrensel sınıf eki (rate-limit dostu)
    tokens = [t for t in n.split() if t]
    if not text_tip and 1 <= len(tokens) <= 3:
        for suf in ("mountain", "peak", "river", "volcano", "canyon", "strait", "island"):
            add(f"{raw} {suf}")
    # Türkiye'ye zorlama YOK — en fazla 8 sorgu
    return out[:8]


_PREFERRED_OSM: dict[str, tuple[tuple[str, str], ...]] = {
    "dag": (("natural", "peak"), ("natural", "mountain"), ("place", "locality")),
    "volkan": (("natural", "volcano"), ("natural", "peak")),
    "nehir": (("waterway", "river"), ("waterway", "stream"), ("natural", "water")),
    "gol": (("natural", "water"), ("natural", "lake")),
    "kanyon": (("natural", "gorge"), ("natural", "valley"), ("tourism", "yes")),
    "bogaz": (("natural", "strait"), ("natural", "bay"), ("waterway", "river")),
    "ada": (("place", "island"), ("natural", "coastline")),
    "gecit": (("mountain_pass", "yes"), ("natural", "saddle")),
    "bina": (("tourism", "attraction"), ("historic", "yes"), ("building", "yes"), ("man_made", "tower")),
    "kopru": (("man_made", "bridge"),),
    "ulke": (("boundary", "administrative"), ("place", "country")),
    "il": (("place", "city"), ("place", "town"), ("place", "state")),
    "sehir": (("place", "city"), ("place", "town"), ("place", "municipality")),
}


def _score_osm_row(row: dict[str, Any], want_tip: str | None) -> float:
    cls = str(row.get("class") or "").lower()
    kind = str(row.get("type") or "").lower()
    try:
        importance = float(row.get("importance") or 0.0)
    except (TypeError, ValueError):
        importance = 0.0
    score = importance * 100.0
    naturalish = cls == "natural" and kind in (
        "peak",
        "mountain",
        "volcano",
        "ridge",
        "gorge",
        "valley",
        "strait",
        "bay",
        "desert",
        "water",
    )
    waterish = cls == "waterway" and kind in ("river", "stream", "canal", "waterfall")
    # Tip yokken doğal sınıf öne; şehir aramasında doğal ceza
    if want_tip in ("il", "sehir", "ulke", "ilce", "mahalle"):
        if naturalish or waterish:
            score -= 70.0
        if kind in ("city", "town", "country", "state", "province", "municipality"):
            score += 55.0
    else:
        if naturalish:
            score += 40.0
        if waterish:
            score += 35.0
        if kind in ("island",) or (cls == "place" and kind == "island"):
            score += 30.0
    if want_tip and want_tip in _PREFERRED_OSM:
        prefs = _PREFERRED_OSM[want_tip]
        for i, (pc, pt) in enumerate(prefs):
            if cls == pc and (pt == "yes" or kind == pt or pt in kind):
                score += 80.0 - i * 5.0
                break
        if want_tip in ("dag", "volkan", "nehir", "kanyon", "bogaz", "gecit", "ada") and kind in (
            "city",
            "town",
            "village",
            "suburb",
            "neighbourhood",
            "hamlet",
            "residential",
        ):
            score -= 60.0
        if want_tip == "gecit" and kind in ("mosque", "place_of_worship", "fuel"):
            score -= 80.0
        if want_tip == "dag" and kind in ("peak", "mountain", "volcano"):
            score += 50.0
        if want_tip == "nehir" and kind in ("river", "stream"):
            score += 50.0
    elif kind in ("village", "hamlet", "suburb", "neighbourhood"):
        # küçük yer — zirve/nehir keşfinde geride; şehir/ülke cezalanmaz
        score -= 15.0
    return score


_NOMINATIM_CACHE: dict[str, list[dict[str, Any]]] = {}
_NOMINATIM_LAST_TS = 0.0
_PHOTON_CACHE: dict[str, list[dict[str, Any]]] = {}


def _photon_tags_for_tip(tip: str | None) -> list[str]:
    t = (tip or "").lower()
    if t in ("dag",):
        return ["natural:peak", "natural:volcano"]
    if t in ("volkan",):
        return ["natural:volcano", "natural:peak"]
    if t in ("nehir",):
        return ["waterway:river", "waterway:stream"]
    if t in ("gol",):
        return ["natural:water"]
    if t in ("kanyon",):
        return ["natural:gorge", "natural:valley"]
    if t in ("bogaz",):
        return ["natural:strait", "natural:bay"]
    if t in ("ada",):
        return ["place:island"]
    if t in ("gecit",):
        return ["natural:saddle"]
    if t in ("col",):
        return ["natural:desert"]
    if t in ("vadi",):
        return ["natural:valley"]
    if t in ("selale",):
        return ["waterway:waterfall"]
    if t in ("il", "sehir"):
        return ["place:city", "place:town"]
    if t in ("ulke",):
        return ["place:country"]
    return []


_NAME_STOP = frozenset(
    {
        "nehri",
        "nehir",
        "river",
        "dagi",
        "dag",
        "daglari",
        "mountain",
        "peak",
        "volcano",
        "yanardagi",
        "yanardag",
        "adasi",
        "ada",
        "island",
        "kanyonu",
        "canyon",
        "bogazi",
        "bogaz",
        "strait",
        "golu",
        "gol",
        "lake",
        "gecidi",
        "gecit",
        "pass",
        "mount",
        "mt",
    }
)


def _name_match_score(query: str, name: str) -> float:
    from ilim_assistant.sahne_super_el import _norm

    q = _norm_key(query)
    n = _norm_key(name)
    if not q or not n:
        return 0.0
    if q == n:
        return 90.0
    # Tam ad eşleşmesi (Boğaz/ Cadde uzantılı sonuçları ezmesin)
    n_first = _norm_key((name or "").split(",")[0].split(" ")[0] if name else "")
    q_tokens = [t for t in _norm(query).split() if t and t not in _NAME_STOP]
    n_tokens = [t for t in _norm(name).split() if t and t not in _NAME_STOP]
    if q_tokens and n_tokens and q_tokens == n_tokens[: len(q_tokens)]:
        return 85.0
    if q_tokens and set(q_tokens) <= set(n_tokens):
        return 70.0
    if n.startswith(q) and len(q) >= 4:
        # istanbul → istanbulbogazi zayıf; yalnız sınırlı
        if len(n) <= len(q) + 2:
            return 60.0
        return 25.0
    if q.startswith(n) and len(n) >= 4:
        return 45.0
    if q_tokens and n_tokens and (set(q_tokens) & set(n_tokens)):
        return 40.0
    if n_first and q_tokens and n_first == _norm_key(q_tokens[0]):
        return 55.0
    return 0.0


def _photon_search(
    q_try: str,
    *,
    osm_tags: list[str] | None = None,
    timeout: float = 4.0,
) -> list[dict[str, Any]]:
    """Photon (Komoot) — hızlı evrensel geocode; sabit yer listesi yok."""
    global _PHOTON_LAST_TS
    tag_key = ",".join(osm_tags or ())
    cache_key = f"{q_try.strip().lower()}|{tag_key}"
    if cache_key in _PHOTON_CACHE:
        return _PHOTON_CACHE[cache_key]
    wait = 0.35 - (time.monotonic() - _PHOTON_LAST_TS)
    if wait > 0:
        time.sleep(wait)
    params: list[tuple[str, str]] = [("q", q_try), ("limit", "8")]
    for tag in osm_tags or ():
        params.append(("osm_tag", tag))
    url = "https://photon.komoot.io/api/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RuzgarSahne/1.0 (local desktop; umit-gokcenur)",
            "Accept": "application/json",
        },
    )
    rows: list[dict[str, Any]] = []
    try:
        _PHOTON_LAST_TS = time.monotonic()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        for feat in data.get("features") or []:
            props = feat.get("properties") or {}
            geom = feat.get("geometry") or {}
            coords = geom.get("coordinates") or []
            if len(coords) < 2:
                continue
            rows.append(
                {
                    "lat": float(coords[1]),
                    "lon": float(coords[0]),
                    "class": str(props.get("osm_key") or ""),
                    "type": str(props.get("osm_value") or props.get("type") or ""),
                    "display_name": str(
                        props.get("name")
                        or props.get("street")
                        or q_try
                    ),
                    "importance": 0.55,
                    "country": str(props.get("country") or ""),
                }
            )
    except Exception:
        rows = []
    # Boş cevap önbelleğe yazılmaz — geçici rate-limit kalıcı "yok" olmasın
    if rows:
        _PHOTON_CACHE[cache_key] = rows
    return rows


def _open_meteo_search(q_try: str, *, timeout: float = 4.0) -> list[dict[str, Any]]:
    """Open-Meteo geocoding — şehir/yer yedek (API anahtarı yok)."""
    params = urllib.parse.urlencode(
        {
            "name": q_try,
            "count": "5",
            "language": "tr",
            "format": "json",
        }
    )
    url = f"https://geocoding-api.open-meteo.com/v1/search?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "RuzgarSahne/1.0 (local desktop; umit-gokcenur)"},
    )
    rows: list[dict[str, Any]] = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        for item in data.get("results") or []:
            code = str(item.get("feature_code") or "")
            kind = "city"
            cls = "place"
            if code.startswith("PCLI") or code == "PCLC":
                kind = "country"
            elif code.startswith("ADM"):
                kind = "state"
            elif code.startswith("MT") or code == "MTS":
                kind, cls = "peak", "natural"
            elif code.startswith("VOL"):
                kind, cls = "volcano", "natural"
            elif code.startswith("STM"):
                kind, cls = "river", "waterway"
            elif code.startswith("LK"):
                kind, cls = "lake", "natural"
            elif code.startswith("ISL"):
                kind = "island"
            rows.append(
                {
                    "lat": float(item["latitude"]),
                    "lon": float(item["longitude"]),
                    "class": cls,
                    "type": kind,
                    "display_name": str(item.get("name") or q_try),
                    "importance": min(0.9, float(item.get("population") or 0) / 5_000_000.0 + 0.3),
                }
            )
    except Exception:
        rows = []
    return rows


def _nominatim_search(q_try: str, *, timeout: float = 3.0) -> list[dict[str, Any]]:
    """Nominatim GET — önbellek + rate limit; 429'da devre kesici."""
    global _NOMINATIM_LAST_TS, _NOMINATIM_BLOCKED_UNTIL
    if time.monotonic() < _NOMINATIM_BLOCKED_UNTIL:
        return []
    key = q_try.strip().lower()
    if key in _NOMINATIM_CACHE:
        return _NOMINATIM_CACHE[key]
    wait = 1.05 - (time.monotonic() - _NOMINATIM_LAST_TS)
    if wait > 0:
        time.sleep(wait)
    params = urllib.parse.urlencode(
        {
            "q": q_try,
            "format": "json",
            "limit": "5",
            "addressdetails": "1",
        }
    )
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RuzgarSahne/1.0 (local desktop; umit-gokcenur)",
            "Accept": "application/json",
        },
    )
    rows: list[dict[str, Any]] = []
    try:
        _NOMINATIM_LAST_TS = time.monotonic()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        rows = data if isinstance(data, list) else []
    except urllib.error.HTTPError as exc:
        if int(getattr(exc, "code", 0) or 0) == 429:
            _NOMINATIM_BLOCKED_UNTIL = time.monotonic() + 120.0
        rows = []
    except Exception:
        rows = []
    if rows:
        _NOMINATIM_CACHE[key] = rows
    return rows


def _row_to_geo(row: dict[str, Any], *, hedef: str, q_try: str, want_tip: str | None) -> dict[str, Any]:
    lat = float(row["lat"])
    lon = float(row["lon"])
    tip = tip_from_osm(str(row.get("class") or ""), str(row.get("type") or ""), hedef or q_try)
    if want_tip in (
        "dag",
        "gecit",
        "kopru",
        "bina",
        "nehir",
        "bogaz",
        "gol",
        "vadi",
        "kanyon",
        "volkan",
        "selale",
        "delta",
        "col",
        "ada",
        "sirt",
    ):
        tip = want_tip
    elif tip in ("nokta", ""):
        osm_tip = tip_from_osm(
            str(row.get("class") or ""),
            str(row.get("type") or ""),
            hedef or q_try,
        )
        if osm_tip != "nokta":
            tip = osm_tip
    # place=city/town her zaman il
    kind = str(row.get("type") or "").lower()
    cls = str(row.get("class") or "").lower()
    if kind in ("city", "town", "municipality") or (cls == "place" and kind in ("city", "town")):
        tip = "il"
    if kind in ("country",) or (cls == "place" and kind == "country"):
        tip = "ulke"
    zoom = zoom_for_tip(tip)
    bb = row.get("boundingbox")
    if bb and len(bb) == 4 and tip in ("ulke", "il", "ilce", "mahalle", "dag"):
        bbox = [float(bb[2]), float(bb[0]), float(bb[3]), float(bb[1])]
    else:
        bbox = bbox_from_center(lat, lon, zoom)
    return {
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "tip": tip,
        "label": row.get("display_name") or q_try,
        "bbox": bbox,
        "source": "nominatim",
    }


def _is_strong_place_hit(row: dict[str, Any]) -> bool:
    kind = str(row.get("type") or "").lower()
    cls = str(row.get("class") or "").lower()
    try:
        imp = float(row.get("importance") or 0)
    except (TypeError, ValueError):
        imp = 0.0
    if kind in ("city", "town", "country", "state", "province", "municipality") and imp >= 0.4:
        return True
    if cls == "boundary" and kind == "administrative" and imp >= 0.5:
        return True
    return False


def _pick_best_row(
    rows: list[dict[str, Any]],
    *,
    hedef: str,
    q_try: str,
    want_tip: str | None,
) -> tuple[dict[str, Any] | None, float, dict[str, Any] | None]:
    best: dict[str, Any] | None = None
    best_score = -1e18
    best_row: dict[str, Any] | None = None
    q_low = (q_try or "").lower()
    mount_query = q_low.startswith("mount ") or want_tip in ("dag", "volkan")
    # Mount Everest: OSM sırasındaki ilk peak (Chomolungma) — Latin isimdeş Florida'yı ezmesin
    if mount_query:
        for i, row in enumerate(rows):
            kind = str(row.get("type") or "").lower()
            cls = str(row.get("class") or "").lower()
            if kind in ("peak", "volcano", "mountain") or (
                cls == "natural" and kind in ("peak", "volcano", "ridge")
            ):
                geo = _row_to_geo(row, hedef=hedef, q_try=q_try, want_tip=want_tip or "dag")
                return geo, 200.0 - float(i), row
    for i, row in enumerate(rows):
        sc = _score_osm_row(row, want_tip)
        sc += _name_match_score(q_try, str(row.get("display_name") or ""))
        sc += _name_match_score(hedef, str(row.get("display_name") or ""))
        # Photon/Nominatim sırası kalite sinyali
        sc += max(0.0, 24.0 - float(i) * 4.0)
        if sc <= best_score:
            continue
        best_score = sc
        best_row = row
        best = _row_to_geo(row, hedef=hedef, q_try=q_try, want_tip=want_tip)
    return best, best_score, best_row


def geocode_photon(hedef: str, timeout: float = 2.5) -> dict[str, Any] | None:
    """Photon birincil — tek istek (UI donmasın)."""
    want_tip = infer_tip_from_text(hedef)
    try:
        from ilim_assistant.sahne_dunya_gezgini import classify_gezgin_tip

        if not want_tip:
            want_tip = classify_gezgin_tip(hedef)
    except Exception:
        pass
    raw = _strip_geo_verbs(hedef) or (hedef or "").strip()
    from ilim_assistant.sahne_super_el import _norm, _strip_case_suffix

    variants: list[str] = []

    def _add_var(x: str | None) -> None:
        t = (x or "").strip()
        if t and len(t) >= 2 and t not in variants:
            variants.append(t)

    _add_var(raw)
    stemmed_parts = [_strip_case_suffix(p) for p in _norm(raw).split()]
    stemmed = " ".join(stemmed_parts)
    _add_var(stemmed)
    core_parts = [p for p in stemmed_parts if p not in _NAME_STOP]
    core = " ".join(core_parts) if core_parts else stemmed
    _add_var(core)
    for suf in _class_query_suffixes(want_tip):
        if core:
            _add_var(f"{core} {suf}")
    if not want_tip and core:
        for suf in ("mountain", "peak", "river", "volcano", "canyon", "island"):
            _add_var(f"{core} {suf}")
    if not variants:
        return None

    q_tagged = None
    for cand in variants:
        low = cand.lower()
        if any(
            s in low
            for s in ("river", "mountain", "peak", "volcano", "canyon", "island", "strait")
        ):
            q_tagged = cand
            break
    if want_tip in ("il", "sehir", "ulke"):
        q0 = core or raw
        tags = _photon_tags_for_tip(want_tip)
    else:
        q0 = q_tagged or (core if core else variants[0])
        tags = _photon_tags_for_tip(want_tip) or (
            None
            if want_tip
            else [
                "natural:peak",
                "natural:volcano",
                "waterway:river",
                "natural:gorge",
                "place:island",
            ]
        )

    rows = _photon_search(q0, osm_tags=tags, timeout=timeout)
    # Volkan/dağ: etiket boşsa etiketsiz tek deneme
    if not rows and want_tip in ("volkan", "dag", "ada") and tags:
        rows = _photon_search(core or raw, osm_tags=None, timeout=timeout)
    best, _sc, _row = _pick_best_row(rows, hedef=hedef, q_try=q0, want_tip=want_tip)
    if not best:
        return None
    best["source"] = "photon"
    return _finalize(best, query=hedef)


def geocode_open_meteo(hedef: str, timeout: float = 2.5) -> dict[str, Any] | None:
    """Open-Meteo — hızlı evrensel yedek/birincil (anahtar yok)."""
    want_tip = infer_tip_from_text(hedef)
    try:
        from ilim_assistant.sahne_dunya_gezgini import classify_gezgin_tip

        if not want_tip:
            want_tip = classify_gezgin_tip(hedef)
    except Exception:
        pass
    raw = _strip_geo_verbs(hedef) or (hedef or "").strip()
    from ilim_assistant.sahne_super_el import _norm, _strip_case_suffix

    stemmed_parts = [_strip_case_suffix(p) for p in _norm(raw).split()]
    core_parts = [p for p in stemmed_parts if p not in _NAME_STOP]
    core = " ".join(core_parts) if core_parts else " ".join(stemmed_parts)
    queries: list[str] = []

    def _addq(x: str | None) -> None:
        t = (x or "").strip()
        if t and len(t) >= 2 and t not in queries:
            queries.append(t)

    # Sınıf-bilinçli EN ad (Everest → Mount Everest; Nil → Nile River)
    if want_tip == "dag" and core:
        _addq(f"Mount {core.title()}")
        _addq(f"{core.title()} Mountain")
    if want_tip == "volkan" and core:
        _addq(f"Mount {core.title()}")
        _addq(f"{core.title()} Volcano")
    if want_tip == "nehir" and core:
        _addq(raw)
        _addq(f"{core.title()} River")
    if want_tip == "kanyon" and core:
        _addq(raw)
        _addq(f"{core.title()} Canyon")
    if want_tip == "ada" and core:
        _addq(core.title())
        _addq(f"{core.title()} Island")
    if not want_tip and core:
        # Tip yok: zirve adları için Mount dene (Everest kasaba tuzağı)
        _addq(f"Mount {core.title()}")
    _addq(raw)
    _addq(core)
    if not queries:
        return None

    best: dict[str, Any] | None = None
    best_score = -1e18
    best_row: dict[str, Any] | None = None
    for q in queries[:3]:
        rows = _open_meteo_search(q, timeout=timeout)
        geo, sc, row = _pick_best_row(rows, hedef=hedef, q_try=q, want_tip=want_tip)
        if geo and sc > best_score:
            best, best_score, best_row = geo, sc, row
        if best_row and best_score >= 80:
            break
    if not best or best_score < 25:
        return None
    # Dağ/nehir: feature_code MT/STM tercih; şehir PPL ceza zaten skorda
    if want_tip in ("dag", "volkan") and best_row:
        kind = str(best_row.get("type") or "")
        if kind not in ("peak", "volcano", "mountain") and best_score < 100:
            # Mount Everest MT gelir; düz Everest kasabasını ele
            return None
    best["source"] = "open-meteo"
    return _finalize(best, query=hedef)


def geocode_nominatim(hedef: str, timeout: float = 2.5) -> dict[str, Any] | None:
    """Nominatim yedek — tek sorgu; 429'da hemen çık (donma yok)."""
    if time.monotonic() < _NOMINATIM_BLOCKED_UNTIL:
        return None
    want_tip = infer_tip_from_text(hedef)
    try:
        from ilim_assistant.sahne_dunya_gezgini import classify_gezgin_tip

        if not want_tip:
            want_tip = classify_gezgin_tip(hedef)
    except Exception:
        pass
    raw = _strip_geo_verbs(hedef) or (hedef or "").strip()
    from ilim_assistant.sahne_super_el import _norm, _strip_case_suffix

    stemmed_parts = [_strip_case_suffix(p) for p in _norm(raw).split()]
    core_parts = [p for p in stemmed_parts if p not in _NAME_STOP]
    core = " ".join(core_parts) if core_parts else " ".join(stemmed_parts)
    # Tek en iyi sorgu — rate-limit dostu
    if want_tip == "dag" and core:
        q_try = f"Mount {core.title()}"
    elif want_tip == "volkan" and core:
        q_try = f"Mount {core.title()}"
    elif want_tip == "nehir" and core:
        # Amazon River / Nile River OSM'de daha isabetli; TR ham ad ikinci
        q_try = f"{core.title()} River"
    elif want_tip == "kanyon" and core:
        q_try = raw if ("canyon" in _norm(raw) or "kanyon" in _norm(raw)) else f"{core.title()} Canyon"
    elif want_tip == "ada" and core:
        q_try = core.title()
    elif not want_tip and core and " " not in core.strip():
        # Tipsiz tek sözcük: önce Mount (Everest); kasaba tuzağını skor ezer
        q_try = f"Mount {core.title()}"
    else:
        q_try = core or raw
    if len(q_try) < 2:
        return None
    try:
        data = _nominatim_search(q_try, timeout=timeout)
    except Exception:
        data = []
    if not data and q_try != raw:
        try:
            data = _nominatim_search(raw, timeout=timeout)
        except Exception:
            data = []
    # Tipsiz Mount sonucu zayıfsa çıplak adı dene
    best, sc, row = _pick_best_row(data, hedef=hedef, q_try=q_try, want_tip=want_tip)
    if (not want_tip) and core and (
        not best
        or (
            row
            and str(row.get("type") or "") in ("census", "administrative", "hamlet", "suburb")
        )
    ):
        try:
            data2 = _nominatim_search(core, timeout=timeout)
        except Exception:
            data2 = []
        best2, sc2, row2 = _pick_best_row(data2, hedef=hedef, q_try=core, want_tip=want_tip)
        if best2 and sc2 > sc:
            best, sc, row = best2, sc2, row2
    if not best:
        return None
    return _finalize(best, query=hedef)


def log_hedef(geo: dict[str, Any] | None, query: str = "") -> dict[str, Any] | None:
    if not geo:
        return None
    out = dict(geo)
    entry = {
        "ad": out.get("label") or query,
        "tip": out.get("tip"),
        "lat": out.get("lat"),
        "lon": out.get("lon"),
        "zoom": out.get("zoom"),
        "source": out.get("source"),
        "query": query,
    }
    out["hedef_log"] = entry
    try:
        import logging

        logging.getLogger("ruzgar.harita").info(
            "H4 hedef ad=%s tip=%s lat=%s lon=%s zoom=%s src=%s q=%s",
            entry["ad"],
            entry["tip"],
            entry["lat"],
            entry["lon"],
            entry["zoom"],
            entry["source"],
            query,
        )
    except Exception:
        pass
    print(
        "[Rüzgar Harita H4]",
        f"ad={entry['ad']}",
        f"tip={entry['tip']}",
        f"lat={entry['lat']}",
        f"lon={entry['lon']}",
        flush=True,
    )
    return out


def geocode(hedef: str, *, allow_network: bool = True) -> dict[str, Any] | None:
    """Evrensel geocode: öğrenilmiş önbellek → Photon → Open-Meteo → (opsiyonel) Nominatim.

    Sabit şehir/dağ tablosuna bağlı değil (Anayasa §2).
    Üst süre varsayılan ~2.8s — UI donmasını keser.
    """
    q = _strip_geo_verbs(hedef) or (hedef or "").strip()
    if not q:
        return None
    learned = geocode_disk(q)
    if learned:
        return log_hedef(learned, hedef)
    local = geocode_local(q)
    if local:
        return log_hedef(local, hedef)
    # Türkiye OSM bölgesel paket (C0) — ağdan önce; Anayasa: sabit tablo değil
    try:
        from ilim_assistant.sahne_osm_tr import lookup_place, osm_tr_enabled

        if osm_tr_enabled():
            osm_hit = lookup_place(q)
            if osm_hit and osm_hit.get("lat") is not None:
                _remember_geo(q, osm_hit)
                return log_hedef(osm_hit, hedef)
    except Exception:
        pass
    if not allow_network:
        return None

    deadline = time.monotonic() + float(os.environ.get("RUZGAR_GEO_DEADLINE_SEC", "2.8") or "2.8")
    # Photon varsayılan kapalı (sık timeout)
    use_photon = os.environ.get("RUZGAR_GEO_PHOTON", "0").strip() in ("1", "true", "yes")
    use_nominatim = os.environ.get("RUZGAR_GEO_NOMINATIM", "1").strip() not in ("0", "false", "no")
    tip_now = infer_tip_from_text(q)
    try:
        if not tip_now:
            from ilim_assistant.sahne_dunya_gezgini import classify_gezgin_tip

            tip_now = classify_gezgin_tip(q)
    except Exception:
        pass
    # Open-Meteo şehir/ülkede iyi; dağ/nehir/kanyon + tipsiz ad → Nominatim
    nature = tip_now in (
        "dag",
        "volkan",
        "nehir",
        "kanyon",
        "bogaz",
        "gecit",
        "ada",
        "selale",
        "col",
        "vadi",
        "gol",
        "sirt",
    )
    providers: list[str] = []
    if nature or not tip_now:
        if use_nominatim:
            providers.append("nominatim")
        providers.append("open-meteo")
    else:
        providers.append("open-meteo")
        if use_nominatim:
            providers.append("nominatim")
    if use_photon:
        providers.append("photon")

    for name in providers:
        if time.monotonic() >= deadline:
            break
        if name == "nominatim" and time.monotonic() < _NOMINATIM_BLOCKED_UNTIL:
            continue
        remain = max(0.35, deadline - time.monotonic())
        try:
            if name == "open-meteo":
                hit = geocode_open_meteo(q, timeout=min(2.0, remain))
            elif name == "photon":
                hit = geocode_photon(q, timeout=min(1.8, remain))
            else:
                hit = geocode_nominatim(q, timeout=min(1.8, remain))
        except Exception:
            hit = None
        if hit and hit.get("lat") is not None:
            _remember_geo(q, hit)
            return log_hedef(hit, hedef)
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(min(1.0, sqrt(a)))


def reverse_local(lat: float, lon: float, max_km: float = 80.0) -> dict[str, Any] | None:
    """Yerel tablo boşsa None (Anayasa)."""
    if not _YEREL:
        return None
    best: dict[str, Any] | None = None
    best_d = 1e18
    seen_labels: set[str] = set()
    for _k, v in _YEREL.items():
        lab = str(v.get("label") or "")
        if lab in seen_labels:
            continue
        seen_labels.add(lab)
        d = _haversine_km(lat, lon, float(v["lat"]), float(v["lon"]))
        if d < best_d:
            best_d = d
            best = v
    if not best or best_d > max_km:
        return None
    tip = str(best.get("tip") or "nokta")
    short = str(best.get("label") or "")
    return {
        "ok": True,
        "lat": lat,
        "lon": lon,
        "label": short,
        "short": short,
        "tip": tip,
        "distance_km": round(best_d, 2),
        "source": "local",
    }


def reverse_nominatim(lat: float, lon: float, timeout: float = 3.5) -> dict[str, Any] | None:
    params = urllib.parse.urlencode(
        {
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "format": "json",
            "zoom": "16",
            "addressdetails": "1",
        }
    )
    url = f"https://nominatim.openstreetmap.org/reverse?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RuzgarSahne/1.0 (local desktop; umit-gokcenur)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        row = json.loads(raw)
        if not row or row.get("error"):
            return None
        addr = row.get("address") or {}
        short = (
            addr.get("neighbourhood")
            or addr.get("suburb")
            or addr.get("quarter")
            or addr.get("city_district")
            or addr.get("district")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
            or addr.get("city")
            or addr.get("province")
            or addr.get("state")
            or ""
        )
        city = addr.get("city") or addr.get("town") or addr.get("province") or addr.get("state") or ""
        display_short = short or city or (row.get("display_name") or "").split(",")[0]
        tip = tip_from_osm(str(row.get("class") or ""), str(row.get("type") or ""), display_short)
        return {
            "ok": True,
            "lat": lat,
            "lon": lon,
            "label": row.get("display_name") or display_short,
            "short": display_short,
            "city": city,
            "tip": tip,
            "source": "nominatim",
            "camera": camera_for_tip(tip, lat, lon),
        }
    except Exception:
        return None


def reverse_geocode(lat: float, lon: float, *, allow_network: bool = True) -> dict[str, Any]:
    local = reverse_local(lat, lon)
    if allow_network:
        nom = reverse_nominatim(lat, lon)
        if nom:
            if local and not nom.get("short"):
                nom["short"] = local.get("short")
            return nom
    if local:
        return local
    return {
        "ok": True,
        "lat": lat,
        "lon": lon,
        "label": f"{lat:.4f}, {lon:.4f}",
        "short": f"{lat:.3f}, {lon:.3f}",
        "tip": "nokta",
        "source": "coord",
        "camera": camera_for_tip("nokta", lat, lon),
    }
