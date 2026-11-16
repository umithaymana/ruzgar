# Created by Ümit & Gökçenur
"""Rüzgar Harita — H10.7 Sürekli Dünya Gezgini (sonsuz keşif, dur diyene kadar)."""

from __future__ import annotations

import math
import re
from typing import Any

H9_VERSION = "ruzgar-dunya-gezgini-h9-v1-2026-11-14"
H10_VERSION = "ruzgar-dunya-gezgini-h10.7-v1-2026-11-15"
VERSION = H10_VERSION

# Geriye uyum: smoke / eski çağrılar
PHASES = (
    ("baslangic", "Başlangıç"),
    ("kesif", "Keşif"),
    ("onemli", "Önemli Noktalar"),
    ("genel", "Genel Bakış"),
)

NATURE_TIPS = frozenset(
    {
        "dag",
        "gecit",
        "vadi",
        "kanyon",
        "gol",
        "nehir",
        "volkan",
        "selale",
        "delta",
        "col",
        "ada",
        "sirt",
    }
)

GEZGIN_TIPS = NATURE_TIPS | frozenset({"sehir", "bogaz"})

TIP_LABELS = {
    "dag": "Dağ",
    "gecit": "Geçit",
    "vadi": "Vadi",
    "kanyon": "Kanyon",
    "gol": "Göl",
    "nehir": "Nehir",
    "volkan": "Volkan",
    "selale": "Şelale",
    "delta": "Delta",
    "col": "Çöl",
    "ada": "Ada",
    "sirt": "Sırt",
    "sehir": "Şehir",
    "bogaz": "Boğaz",
}

# Gezi irtifası — çevre görülsün (uydu değil). Metre.
ALT_BANDS: dict[str, tuple[float, float]] = {
    "sehir": (35.0, 110.0),
    "bogaz": (40.0, 130.0),
    "nehir": (25.0, 85.0),
    "delta": (30.0, 100.0),
    "dag": (70.0, 260.0),
    "sirt": (70.0, 240.0),
    "gecit": (45.0, 160.0),
    "vadi": (40.0, 140.0),
    "kanyon": (40.0, 130.0),
    "ada": (50.0, 180.0),
    "gol": (45.0, 160.0),
    "volkan": (55.0, 220.0),
    "selale": (30.0, 100.0),
    "col": (60.0, 220.0),
}

FLIGHT_STYLES: dict[str, str] = {
    "sehir": "city_cruise",
    "bogaz": "city_cruise",
    "dag": "ridge_wander",
    "gecit": "corridor",
    "vadi": "corridor",
    "kanyon": "corridor",
    "gol": "coast_cruise",
    "nehir": "river_follow",
    "volkan": "volcano_wander",
    "selale": "river_follow",
    "delta": "river_follow",
    "col": "sweep",
    "ada": "coast_cruise",
    "sirt": "ridge_wander",
}

_CARD_TMPL: dict[str, dict[str, str]] = {
    tip: {
        "yukseklik": f"{ALT_BANDS.get(tip, (50, 250))[0]:.0f}–{ALT_BANDS.get(tip, (50, 250))[1]:.0f} m",
        "bolge": TIP_LABELS.get(tip, tip),
        "ozet": "{name}: sürekli Dünya Gezgini — dur diyene kadar keşif.",
    }
    for tip in GEZGIN_TIPS
}


def _norm(s: str) -> str:
    t = (s or "").strip().lower()
    for a, b in (
        ("ı", "i"),
        ("ğ", "g"),
        ("ü", "u"),
        ("ş", "s"),
        ("ö", "o"),
        ("ç", "c"),
        ("â", "a"),
        ("î", "i"),
        ("û", "u"),
    ):
        t = t.replace(a, b)
    t = re.sub(r"[^\w\s]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def classify_nature_tip(*texts: str, tip_hint: str | None = None) -> str | None:
    blob = _norm(" ".join(str(t or "") for t in texts if t))
    if not blob and not tip_hint:
        return None

    rules: list[tuple[str, str]] = [
        (r"\b(selale|selalesi|waterfall|falls)\b", "selale"),
        (r"\b(delta|deltasi)\b", "delta"),
        (r"\b(col|colu|desert|sahra|erg\b|dune)\b", "col"),
        (r"\b(ada|adasi|island|isle)\b", "ada"),
        (
            r"\b(nehir|nehri|irmak|irmagi|akarsu|river|stream|creek)\b|\b\w+cayi\b|\bcayi\b",
            "nehir",
        ),
        (r"\b(gol|golu|lake|lagoon|reservoir)\b", "gol"),
        (r"\b(volkan|volkani|volcano|crater|yanardag|yanardagi)\b", "volkan"),
        (r"\b(kanyon|kanyonu|canyon|gorge|ravine)\b", "kanyon"),
        (r"\b(vadi|vadisi|valley|vale)\b", "vadi"),
        (r"\b(gecit|gecidi|gecid|pass|saddle)\b", "gecit"),
        (r"\b(sirt|sirti|ridge)\b", "sirt"),
        (r"\b(dag|dagi|daglar|daglari|mountain|peak|mount)\b", "dag"),
    ]
    for pat, tip in rules:
        if blob and re.search(pat, blob):
            return tip

    hint = (tip_hint or "").strip().lower()
    if hint in NATURE_TIPS:
        return hint
    osm_map = {
        "peak": "dag",
        "mountain": "dag",
        "ridge": "sirt",
        "volcano": "volkan",
        "pass": "gecit",
        "saddle": "gecit",
        "valley": "vadi",
        "canyon": "kanyon",
        "gorge": "kanyon",
        "river": "nehir",
        "stream": "nehir",
        "waterway": "nehir",
        "lake": "gol",
        "water": "gol",
        "waterfall": "selale",
        "island": "ada",
        "islet": "ada",
        "desert": "col",
        "dune": "col",
    }
    if hint in osm_map:
        return osm_map[hint]
    return None


def classify_gezgin_tip(*texts: str, tip_hint: str | None = None) -> str | None:
    """Doğal sınıf veya şehir — H10.7."""
    nat = classify_nature_tip(*texts, tip_hint=tip_hint)
    if nat:
        return nat
    hint = (tip_hint or "").strip().lower()
    if hint in ("sehir", "il", "ilce", "mahalle", "city", "town"):
        return "sehir"
    blob = _norm(" ".join(str(t or "") for t in texts if t))
    if re.search(r"\b(bogaz|bogazi|bosphorus|bosporus)\b", blob):
        return "bogaz" if "kopru" not in blob else "sehir"
    if re.search(
        r"\b(sehir|sehrini|kent|metropol|istanbul|ankara|izmir|bursa|antalya|"
        r"london|paris|tokyo|roma|new\s*york)\b",
        blob,
    ):
        return "sehir"
    return None


def _bearing_offset(
    lat: float, lon: float, bearing_deg: float, dist_deg: float
) -> tuple[float, float]:
    rad = math.radians(bearing_deg)
    return lat + dist_deg * math.cos(rad), lon + dist_deg * math.sin(rad) / max(
        0.2, math.cos(math.radians(lat))
    )


def _alt(tip: str, t: float, *, low_bias: float = 0.35) -> float:
    lo, hi = ALT_BANDS.get(tip, (60.0, 250.0))
    # t 0..1 — low_bias ile daha çok alt banda yakın
    u = max(0.0, min(1.0, t))
    mix = low_bias + (1.0 - low_bias) * (0.5 - 0.5 * math.cos(u * math.pi * 2))
    return lo + (hi - lo) * mix


def _wp(
    lat: float,
    lon: float,
    *,
    heading: float,
    pitch: float,
    range_m: float,
    seg_sec: float,
    look_lat: float | None = None,
    look_lon: float | None = None,
    info: str = "",
    section: str = "kesif",
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "heading": round(heading % 360, 1),
        "pitch": round(pitch, 1),
        "range": round(max(20.0, range_m), 1),
        "seg_sec": round(max(0.8, seg_sec), 2),
        "info": info,
        "section": section,
        # H10.7: faz yok; eski alanlar boş/uyum
        "phase": "",
        "phase_label": section,
    }
    if look_lat is not None and look_lon is not None:
        out["look_lat"] = round(look_lat, 5)
        out["look_lon"] = round(look_lon, 5)
    else:
        out["look_lat"] = out["lat"]
        out["look_lon"] = out["lon"]
    return out


def _seed_count(tip: str) -> int:
    return {
        "nehir": 36,
        "delta": 32,
        "kanyon": 32,
        "vadi": 28,
        "sehir": 40,
        "ada": 36,
        "gol": 32,
        "dag": 36,
        "volkan": 36,
        "sirt": 32,
    }.get(tip, 28)


def build_endless_seed(
    tip: str,
    lat: float,
    lon: float,
    label: str,
    *,
    bearing0: float | None = None,
    n: int | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Sonsuz keşif için başlangıç tohum yolu (bitiş yok; istemci uzatır)."""
    tip_l = tip if tip in GEZGIN_TIPS else "dag"
    style = FLIGHT_STYLES.get(tip_l, "ridge_wander")
    name = label or "Keşif"
    steps = n or _seed_count(tip_l)
    bearing = 18.0 if bearing0 is None else float(bearing0)
    wps: list[dict[str, Any]] = []

    if style == "river_follow":
        bearing = 18.0 if bearing0 is None else bearing
        half = 0.9
        for i in range(steps):
            t = i / max(1, steps - 1)
            along = -half * 0.15 + half * t  # ileri akış
            meander = 0.035 * math.sin(t * math.pi * 3.1 + i * 0.2)
            pt = _bearing_offset(lat, lon, bearing, along)
            look = _bearing_offset(pt[0], pt[1], bearing + 90.0, meander)
            cam = _bearing_offset(look[0], look[1], bearing + 105.0, 0.012)
            rng = _alt("nehir" if tip_l != "delta" else "delta", t, low_bias=0.55)
            wps.append(
                _wp(
                    cam[0],
                    cam[1],
                    heading=(bearing + 6) % 360,
                    pitch=-22 + 4 * math.sin(t * math.pi),
                    range_m=rng,
                    seg_sec=10.0,
                    look_lat=look[0],
                    look_lon=look[1],
                    info=f"{name}",
                    section="nehir",
                )
            )

    elif style == "corridor":
        axis = 115.0 if tip_l == "kanyon" else 95.0
        if bearing0 is not None:
            axis = bearing
        for i in range(steps):
            t = i / max(1, steps - 1)
            along = 0.02 + 0.85 * t
            base = _bearing_offset(lat, lon, axis, along)
            cam = _bearing_offset(base[0], base[1], axis - 90.0, 0.012)
            depth = abs(math.sin(t * math.pi * 1.4))
            rng = _alt("kanyon" if tip_l == "kanyon" else tip_l, depth, low_bias=0.5)
            wps.append(
                _wp(
                    cam[0],
                    cam[1],
                    heading=axis % 360,
                    pitch=-16 - 4 * depth,
                    range_m=rng,
                    seg_sec=9.5,
                    look_lat=base[0],
                    look_lon=base[1],
                    info=f"{name}",
                    section="koridor",
                )
            )

    elif style == "city_cruise":
        # Sınıf şablonu — herhangi şehir; isim özel yolu yok
        # along derece cinsinden: eski 0.42° (~45 km) kıyı şehirlerinde denize kaçıyordu
        bearing = 55.0 if bearing0 is None else bearing
        tip_alt = "bogaz" if tip_l == "bogaz" else "sehir"
        max_along = 0.028 if tip_l == "bogaz" else 0.022
        for i in range(steps):
            t = i / max(1, steps - 1)
            along = 0.003 + max_along * t
            coast = 0.004 * math.sin(t * math.pi * 2.2)
            pt = _bearing_offset(lat, lon, bearing, along)
            look = _bearing_offset(pt[0], pt[1], bearing + 90.0, coast)
            rng = _alt(tip_alt, t, low_bias=0.72)
            if int(i / 5) % 2 == 1:
                rng = max(35.0, rng * 0.78)
            wps.append(
                _wp(
                    look[0],
                    look[1],
                    heading=(bearing + 6 + 8 * math.sin(t * 3)) % 360,
                    pitch=-18,
                    range_m=rng,
                    seg_sec=11.0,
                    look_lat=look[0],
                    look_lon=look[1],
                    info=f"{name}",
                    section="sehir",
                )
            )

    elif style == "coast_cruise":
        bearing = 200.0 if bearing0 is None else bearing
        radius = 0.05 if tip_l == "ada" else 0.04
        for i in range(steps):
            t = i / max(1, steps - 1)
            ang = bearing + 360.0 * t
            r = radius * (0.85 + 0.3 * t)
            cam = _bearing_offset(lat, lon, ang, r)
            rng = _alt(tip_l, t, low_bias=0.55)
            wps.append(
                _wp(
                    cam[0],
                    cam[1],
                    heading=(ang + 180) % 360,
                    pitch=-18,
                    range_m=rng,
                    seg_sec=10.0,
                    look_lat=lat,
                    look_lon=lon,
                    info=f"{name}",
                    section="kiyi",
                )
            )

    elif style == "volcano_wander":
        for i in range(steps):
            t = i / max(1, steps - 1)
            ang = 200.0 + 400.0 * t
            dist = 0.06 * (1.0 - 0.5 * math.sin(t * math.pi)) + 0.012
            cam = _bearing_offset(lat, lon, ang, dist)
            rng = _alt("volkan", t, low_bias=0.55)
            if 0.35 < t < 0.55:
                rng = max(55.0, rng * 0.7)
            wps.append(
                _wp(
                    cam[0],
                    cam[1],
                    heading=(ang + 180) % 360,
                    pitch=-18,
                    range_m=rng,
                    seg_sec=10.0,
                    look_lat=lat,
                    look_lon=lon,
                    info=f"{name}",
                    section="volkan",
                )
            )

    elif style == "sweep":
        for i in range(steps):
            t = i / max(1, steps - 1)
            ang = 40.0 + 220.0 * t
            cam = _bearing_offset(lat, lon, ang, 0.06 + 0.03 * t)
            rng = _alt("col", t, low_bias=0.5)
            wps.append(
                _wp(
                    cam[0],
                    cam[1],
                    heading=(ang + 160) % 360,
                    pitch=-18,
                    range_m=rng,
                    seg_sec=10.0,
                    look_lat=lat,
                    look_lon=lon,
                    info=f"{name}",
                    section="kesif",
                )
            )

    else:  # ridge_wander
        approach = 200.0 if bearing0 is None else bearing
        for i in range(steps):
            t = i / max(1, steps - 1)
            ang = approach + 50.0 * math.sin(t * math.pi * 2) + 180.0 * t
            dist = 0.07 * (1.0 - 0.65 * t) + 0.018 + 0.025 * abs(math.sin(t * math.pi * 3))
            cam = _bearing_offset(lat, lon, ang, dist)
            rng = _alt("dag", t, low_bias=0.5)
            wps.append(
                _wp(
                    cam[0],
                    cam[1],
                    heading=(ang + 180) % 360,
                    pitch=-18 + 3 * math.sin(t * math.pi),
                    range_m=rng,
                    seg_sec=10.5,
                    look_lat=lat,
                    look_lon=lon,
                    info=f"{name}",
                    section="dag",
                )
            )

    return wps, style


def extend_endless_path(
    tip: str,
    last_wp: dict[str, Any],
    *,
    label: str = "",
    count: int = 24,
    bearing_bias: float = 0.0,
    mode: str | None = None,
) -> list[dict[str, Any]]:
    """Mevcut uçuştan devam — yeni araştırma değil, yol uzatma."""
    tip_l = tip if tip in GEZGIN_TIPS else "dag"
    if mode == "nehir" or mode == "river":
        tip_l = "nehir"
    elif mode == "sehir" or mode == "city":
        tip_l = "sehir"
    elif mode == "kiyi" or mode == "coast":
        tip_l = "ada"
    elif mode == "kanyon" or mode == "corridor":
        tip_l = "kanyon"
    elif mode == "volkan" or mode == "crater":
        tip_l = "volkan"
    lat = float(last_wp.get("look_lat") or last_wp.get("lat") or 0)
    lon = float(last_wp.get("look_lon") or last_wp.get("lon") or 0)
    heading = float(last_wp.get("heading") or 0) + float(bearing_bias or 0)
    seed, _style = build_endless_seed(
        tip_l, lat, lon, label or "Keşif", bearing0=heading, n=count
    )
    return seed


def build_waypoints_for_tip(
    tip: str,
    lat: float,
    lon: float,
    label: str,
) -> tuple[list[dict[str, Any]], str]:
    return build_endless_seed(tip, lat, lon, label)


def build_stops_for_tip(
    tip: str,
    lat: float,
    lon: float,
    label: str,
) -> list[dict[str, Any]]:
    """Geriye uyum: faz özeti yok — ilk 4 waypoint hafif özet."""
    wps, _s = build_endless_seed(tip, lat, lon, label)
    out = []
    for i, w in enumerate(wps[:4]):
        out.append(
            {
                "lat": w["lat"],
                "lon": w["lon"],
                "heading": w["heading"],
                "pitch": w["pitch"],
                "range": w["range"],
                "info": w.get("info") or "",
                "title": w.get("section") or f"kesif-{i+1}",
                "dwell_sec": 0.0,
                "phase": "",
                "phase_label": w.get("section") or "",
            }
        )
    return out


def _card_for_class(tip: str, label: str, *, bolge_hint: str | None = None) -> dict[str, Any]:
    tip_l = tip if tip in _CARD_TMPL else "dag"
    tmpl = _CARD_TMPL[tip_l]
    name = label or "Hedef"
    return {
        "title": name,
        "yukseklik": tmpl["yukseklik"],
        "bolge": bolge_hint or tmpl["bolge"],
        "tur": TIP_LABELS.get(tip_l, tip_l),
        "tip": tip_l,
        "ozet": str(tmpl["ozet"]).format(name=name),
    }


def _strip_tour_words(n: str) -> str:
    t = n
    t = re.sub(
        r"\b(gezdir|gezdirelim|gezelim|gezisi|geziyi|gezi|turu|turunu|tur|tura|gezgini|gezgin|baslat|basla|baslatin)\b",
        " ",
        t,
    )
    t = re.sub(r"\b(dunya\s+gezgini|harita\s+turu)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


_WORD_METERS = {
    "bir": 1.0,
    "iki": 2.0,
    "uc": 3.0,
    "dort": 4.0,
    "bes": 5.0,
    "alti": 6.0,
    "yedi": 7.0,
    "sekiz": 8.0,
    "dokuz": 9.0,
    "on": 10.0,
}


def parse_tour_altitude_meters(n: str) -> float | None:
    if not n:
        return None
    m = re.search(
        r"\b(\d+(?:[.,]\d+)?)\s*(?:metre|meter|metrey[ei]|metreye|m\b)",
        n,
    )
    if m:
        try:
            return max(1.0, min(80000.0, float(m.group(1).replace(",", "."))))
        except ValueError:
            return None
    m = re.search(
        r"\b(bir|iki|uc|dort|bes|alti|yedi|sekiz|dokuz|on)\s*"
        r"(?:metre|meter|metrey[ei]|metreye)\b",
        n,
    )
    if m:
        return _WORD_METERS.get(m.group(1))
    m = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:kilometre|km)\b", n)
    if m:
        try:
            return max(1.0, min(80000.0, float(m.group(1).replace(",", ".")) * 1000.0))
        except ValueError:
            return None
    if re.search(r"\b(yer\s*seviyesi|yer\s*seviyesine|topraga\s*in|sifir\s*metre)\b", n):
        return 1.0
    return None


def looks_like_tour_control(n: str) -> str | None:
    """Pilot komutları — yeni araştırma değil, kamerayı değiştir."""
    if not n:
        return None
    # CameraRig mod / cisim geçişi (evrensel — yer hardcode yok)
    try:
        from ilim_assistant.ruzgar_kamera_rig import looks_like_camera_mode

        cam = looks_like_camera_mode(n)
        if cam:
            return cam
    except Exception:
        pass
    # Dur = hareketi duraklat (geziyi öldürme). Bitir = stop.
    if re.search(
        r"\b(turu?\s*(bitir|iptal|kapat|sonlandir)|gezgini?\s*(bitir|kapat)|"
        r"geziyi?\s*(bitir|kapat)|tour\s*stop|stop\s*tour|bitir)\b",
        n,
    ):
        return "tour_stop"
    if re.search(
        r"\b(turu?\s*(durdur|duraklat|beklet)|gezgini?\s*(durdur|duraklat)|"
        r"tour\s*pause|pause\s*tour|\bdur\b)\b",
        n,
    ):
        return "tour_pause"
    if re.search(
        r"\b(tura?\s*devam|turu?\s*devam|gezgini?\s*devam|geziye?\s*devam|"
        r"tour\s*resume|resume\s*tour|devam\s*et|devam)\b",
        n,
    ):
        return "tour_resume"
    if re.search(
        r"\b(hiz\s*(azalt|dusur|yavaslat)|yavaslat|daha\s*yavas|slow\s*down|tour\s*slower)\b",
        n,
    ):
        return "tour_slower"
    if re.search(
        r"\b(hiz\s*(arttir|artir|hizlandir)|hizlandir|daha\s*hizli|hizlan|speed\s*up|tour\s*faster)\b",
        n,
    ):
        return "tour_faster"
    if parse_tour_altitude_meters(n) is not None:
        return "tour_altitude"
    if re.search(
        r"\b(kus\s*ucus(u)?|normal\s*mesafe|varsayilan\s*(mesafe|yukseklik)|"
        r"mesafeyi\s*sifirla|irtifayi\s*sifirla)\b",
        n,
    ):
        return "tour_altitude_reset"
    if re.search(
        r"\b(yere\s*(yaklas|in|alcal)|alcal|daha\s*alcak|mesafeyi\s*(azalt|kisalt)|"
        r"kamerayi\s*(indir|alcalt)|irtifayi\s*(azalt|dusur)|asagi\s*in|asagi|"
        r"fly\s*lower|come\s*closer)\b",
        n,
    ):
        return "tour_closer"
    if re.search(
        r"\b(yuksel|daha\s*yuksek|mesafeyi\s*(arttir|artir|ac)|kamerayi\s*yukselt|"
        r"irtifayi\s*(arttir|artir)|yukaridan\s*bak|yukari\s*cik|yukari|"
        r"fly\s*higher|pull\s*up)\b",
        n,
    ):
        return "tour_farther"
    if re.search(
        r"\b(goz\s*hiza\w*|goze\s*in|yuru(me)?(\s*modu)?\b|yuruyerek|"
        r"walk(\s*mode)?|first\s*person|gozle\s*gez)\b",
        n,
    ):
        return "tour_walk"
    if re.search(
        r"\b(ucus\s*modu|kus\s*bakisi|bird(\s*view)?|yurumeden\s*cik|walk\s*(off|exit))\b",
        n,
    ):
        return "tour_fly"
    if re.search(r"\b(sola\s*(git|kay)|sol(a)?\s*yan|strafe\s*left)\b", n):
        return "tour_strafe_left"
    if re.search(r"\b(saga\s*(git|kay)|sag(a)?\s*yan|strafe\s*right)\b", n):
        return "tour_strafe_right"
    if re.search(r"\b(sola\s*don|sol(a)?\s*cevir|turn\s*left|left\s*turn)\b", n):
        return "tour_turn_left"
    if re.search(r"\b(saga\s*don|sag(a)?\s*cevir|turn\s*right|right\s*turn)\b", n):
        return "tour_turn_right"
    if re.search(r"\b(geri\s*(don|git)|back\s*up|turn\s*around|geriye)\b", n):
        return "tour_back"
    if re.search(r"\b(ileri\s*git|duz\s*git|ileri|go\s*forward|straight)\b", n):
        return "tour_forward"
    if re.search(
        r"\b(sokak\s*(ismi|isimleri|adlari|yazilari)|"
        r"mahalle\s*(ismi|isimleri|adlari)|etiket(leri)?\s*ac)\b",
        n,
    ):
        return "tour_labels_on"
    if re.search(r"\b(trafik|arabalar?|gemiler?|kayiklar?|sim(?:ulasyon)?\s*trafik)\b", n):
        return "tour_traffic"
    if re.search(r"\b(gercek\s*goruntu|son\s*cekil|mapillary|sokak\s*pano|pano\s*ac)\b", n):
        return "tour_pano_near"
    if re.search(r"\b(nehri?\s*takip|nehir\s*boyu|irmagi?\s*takip|follow\s*river)\b", n):
        return "tour_follow_river"
    if re.search(r"\b(sehre\s*gir|sehir\s*ici|kente\s*gir|enter\s*city)\b", n):
        return "tour_enter_city"
    if re.search(
        r"\b(uzerine\s*cik|üstüne\s*çık|kus\s*bakisi|kuşbakışı|overhead|top\s*down)\b",
        n,
    ):
        return "tour_uzerine_cik"
    if re.search(r"\b(odak\s*takibi|focus\s*mode|odak\s*modu)\b", n):
        return "tour_odak_takibi"
    if re.search(r"\b(serbest\s*bakis|serbest\s*bakış|free\s*look|free\s*mode)\b", n):
        return "tour_serbest_bakis"
    if re.search(r"\b(kiyi(yi)?\s*takip|sahili?\s*takip|follow\s*coast)\b", n):
        return "tour_follow_coast"
    if re.search(
        r"\b(krater(in)?\s*icine|krater(e)?\s*(gir|yaklas)|icine\s*gir|enter\s*crater)\b",
        n,
    ):
        return "tour_enter_crater"
    if re.search(r"\b(onceki\s*bolum|tur\s*geri|tour\s*prev)\b", n):
        return "tour_prev"
    if re.search(r"\b(durak\s*atla|atl[aı]|skip\s*(stop|tour)|tour\s*skip)\b", n):
        return "tour_skip"
    if re.search(r"\b(sonraki\s*bolum|tur\s*ileri|next\s*(stop|tour)|tour\s*next)\b", n):
        return "tour_next"
    return None


def looks_like_tour_start(n: str) -> bool:
    """Herhangi yer + gezi/tur/gezdir — sabit bölge yok (anayasa)."""
    if looks_like_tour_control(n):
        return False
    if re.search(r"\b(dunya\s*turu|panoramik|kure\s*tur|globe\s*tour|tur\s*mod)\b", n):
        if not re.search(r"\b(gezdir|gezgin|gezi)\b", n):
            return False
    if re.search(
        r"\b(gezdir|gezdirelim|gezelim|dunya\s+gezgini|gezgin\s+modu|gezgini)\b",
        n,
    ):
        return True
    # «X gezi / gezisi / turu» — yer geocode ile çözülür, listeden değil
    if re.search(r"\b\w+\s+(turu|gezgini|gezisi|gezi)\b", n) and not re.search(
        r"\b(dunya\s*turu|panorama)\b", n
    ):
        return True
    return False


def extract_tour_place(n: str) -> str | None:
    t = _strip_tour_words(n)
    t = re.sub(
        r"\b(lutfen|bana|bir|su|o|beni|haritada|haritada|3d|de|da|yi|yı|yu|yü|i|ı)\b",
        " ",
        t,
    )
    t = re.sub(r"\s+", " ", t).strip()
    return t or None


def build_tour_payload(
    *,
    place: str | None = None,
    geo: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """H10.7: sürekli keşif tohumu — bitiş/faz yok."""
    label = ""
    lat = lon = None
    tip_hint = None
    bolge_hint = None

    if geo and geo.get("lat") is not None and geo.get("lon") is not None:
        lat = float(geo["lat"])
        lon = float(geo["lon"])
        label = str(geo.get("label") or place or "Keşif")
        tip_hint = str(geo.get("tip") or "").lower() or None
        bolge_hint = geo.get("bolge") or geo.get("region") or geo.get("country")
        if isinstance(bolge_hint, str) and not bolge_hint.strip():
            bolge_hint = None
    elif place:
        label = place
        tip_hint = None

    # place var, lat/lon yok → geocode et (API yalnız place ile gelince tur_yok olmasın)
    if (lat is None or lon is None) and (place or label):
        try:
            from ilim_assistant.sahne_harita_geo import geocode

            hit = geocode(str(place or label), allow_network=True)
            if hit and hit.get("lat") is not None and hit.get("lon") is not None:
                lat = float(hit["lat"])
                lon = float(hit["lon"])
                label = str(hit.get("label") or place or label or "Keşif")
                tip_hint = tip_hint or str(hit.get("tip") or "").lower() or None
                bolge_hint = bolge_hint or hit.get("bolge") or hit.get("country")
        except Exception:
            pass

    tip = classify_gezgin_tip(place or "", label, tip_hint=tip_hint)
    # Geocode şehir/ülke döndüyse tipsiz bırakma (Halkalı vb.)
    if not tip and tip_hint in ("sehir", "il", "ilce", "mahalle", "nokta", "city", "town"):
        tip = "sehir"
    if not tip and lat is not None and lon is not None:
        # Türkiye kara kutusu içindeyse şehir turu varsay
        if 35.8 <= float(lat) <= 42.3 and 25.5 <= float(lon) <= 45.0:
            tip = "sehir"
    if not tip:
        return None
    if lat is None or lon is None:
        return None

    waypoints, style = build_endless_seed(tip, lat, lon, label)
    lo, hi = ALT_BANDS.get(tip, (50.0, 250.0))
    card = _card_for_class(tip, label, bolge_hint=str(bolge_hint) if bolge_hint else None)
    return {
        "ok": True,
        "version": H10_VERSION,
        "h9_compat": H9_VERSION,
        "id": "endless:" + tip + ":" + re.sub(r"[^a-z0-9]+", "", _norm(label))[:20],
        "label": label,
        "tip": tip,
        "lat": lat,
        "lon": lon,
        "waypoints": waypoints,
        "waypoint_count": len(waypoints),
        # H10.7: durak/faz yok — uyum için boş/özet
        "stops": [],
        "stop_count": 0,
        "phases": [],
        "card": card,
        "nature": tip in NATURE_TIPS,
        "smart": True,
        "class_based": True,
        "continuous": True,
        "endless": True,
        "cinematic": True,
        "flight": {
            "mode": "endless",
            "style": style,
            "spline": "catmull",
            "dwell": False,
            "bird_default": True,
            "min_range_m": lo,
            "max_range_m": hi,
            "altitude_voice": True,
            "extendable": True,
            "until_stop": True,
        },
    }


def try_resolve_tour_intent(norm_text: str) -> dict[str, Any] | None:
    n = norm_text
    ctrl = looks_like_tour_control(n)
    if ctrl:
        out: dict[str, Any] = {
            "action": ctrl,
            "fiil": "gezgin",
            "organ": "harita",
            "guven": 0.94,
            "hedef": None,
            "tour_ctrl": ctrl,
        }
        if ctrl == "tour_altitude":
            meters = parse_tour_altitude_meters(n)
            if meters is not None:
                out["tour_meters"] = meters
                out["meters"] = meters
        return out
    if not looks_like_tour_start(n):
        return None
    place = extract_tour_place(n)
    # soru kalıntısı / boş hedef → gezi değil (sabit yer listesi yok)
    if not place or re.search(
        r"^(nedir|nasil|neden|niye|kim|ne|hangi|nerede|ne\s*zaman)$",
        place,
    ):
        return None
    return {
        "action": "tour_start",
        "fiil": "gezgin",
        "organ": "harita",
        "guven": 0.93,
        "hedef": place,
        "tour_start": True,
    }
