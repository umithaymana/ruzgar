# Created by Ümit & Gökçenur
"""Rüzgar Harita — H10.5 Dünya Gezgini (sınıf bazlı profil; isim özel listesi yok)."""

from __future__ import annotations

import re
from typing import Any

H9_VERSION = "ruzgar-dunya-gezgini-h9-v1-2026-11-14"
H10_VERSION = "ruzgar-dunya-gezgini-h10.5-v1-2026-11-14"
VERSION = H10_VERSION

# Doğal coğrafi sınıflar (Şehir Gezgini / NASA / kamera değil)
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

PHASES = (
    ("baslangic", "Başlangıç"),
    ("kesif", "Keşif"),
    ("onemli", "Önemli Noktalar"),
    ("genel", "Genel Bakış"),
)

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
}

# Her sınıf için gezgin profili (kamera / durak geometrisi) — isim bağımsız
_CLASS_PROFILES: dict[str, dict[str, Any]] = {
    "dag": {
        "offsets": [(0.055, 0.03), (0.02, -0.04), (0.0, 0.0), (-0.045, 0.025)],
        "cams": [
            (200, -32, 26000, 4.2),
            (150, -26, 16000, 4.5),
            (185, -28, 12000, 5.2),
            (320, -34, 30000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — ufukta kütle.",
            "{name}: keşif — yamaç ve etek (World Terrain).",
            "{name}: önemli nokta — zirve / ana sırt.",
            "{name}: genel bakış — coğrafi çerçeve.",
        ),
        "card": {
            "yukseklik": "zirve / sırt kotu",
            "bolge": "Dağ kütlesi",
            "ozet": "{name}: dağ sınıfı — rölyef ve zirve hattı keşfi.",
        },
    },
    "gecit": {
        "offsets": [(0.035, -0.02), (0.01, 0.015), (0.0, 0.0), (-0.03, 0.02)],
        "cams": [
            (130, -24, 9000, 4.2),
            (100, -18, 5500, 4.5),
            (85, -20, 4200, 5.0),
            (250, -28, 11000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — geçide yaklaşım.",
            "{name}: keşif — yan koridor ve vadi ekseni.",
            "{name}: önemli nokta — en dar sırt.",
            "{name}: genel bakış — geçit geride.",
        ),
        "card": {
            "yukseklik": "geçit kotu",
            "bolge": "Dağ geçidi",
            "ozet": "{name}: geçit sınıfı — koridor ve sırt hattı.",
        },
    },
    "vadi": {
        "offsets": [(0.05, 0.02), (0.02, -0.015), (0.0, 0.0), (-0.04, -0.02)],
        "cams": [
            (200, -26, 16000, 4.2),
            (150, -18, 10000, 4.5),
            (110, -16, 7000, 5.0),
            (320, -30, 20000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — vadi ağzı.",
            "{name}: keşif — yan yarma.",
            "{name}: önemli nokta — taban ve yamaçlar.",
            "{name}: genel bakış — havza ölçeği.",
        ),
        "card": {
            "yukseklik": "vadi tabanı",
            "bolge": "Vadi sistemi",
            "ozet": "{name}: vadi sınıfı — yarma ve yamaçlar.",
        },
    },
    "kanyon": {
        "offsets": [(0.05, 0.02), (0.02, -0.015), (0.0, 0.0), (-0.04, -0.02)],
        "cams": [
            (200, -28, 18000, 4.2),
            (150, -18, 11000, 4.5),
            (100, -14, 6500, 5.0),
            (320, -32, 22000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — kanyon ağzı, derinlik hissi.",
            "{name}: keşif — duvar hattı.",
            "{name}: önemli nokta — taban koridoru.",
            "{name}: genel bakış — kanyon sistemi.",
        ),
        "card": {
            "yukseklik": "kanyon derinliği",
            "bolge": "Kanyon",
            "ozet": "{name}: kanyon sınıfı — duvar ve taban.",
        },
    },
    "gol": {
        "offsets": [(0.08, 0.0), (0.0, 0.06), (0.0, 0.0), (-0.06, -0.04)],
        "cams": [
            (180, -35, 28000, 4.0),
            (270, -30, 22000, 4.2),
            (40, -28, 18000, 4.5),
            (90, -40, 36000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — kıyıdan göl aynası.",
            "{name}: keşif — kıyı kıvrımları.",
            "{name}: önemli nokta — göl merkezi.",
            "{name}: genel bakış — havza ölçeği.",
        ),
        "card": {
            "yukseklik": "göl yüzeyi",
            "bolge": "Göl havzası",
            "ozet": "{name}: göl sınıfı — ayna ve kıyı hattı.",
        },
    },
    "nehir": {
        "offsets": [(0.06, -0.04), (0.02, 0.02), (0.0, 0.0), (-0.05, 0.04)],
        "cams": [
            (120, -30, 32000, 4.2),
            (100, -24, 18000, 4.5),
            (90, -22, 12000, 5.0),
            (40, -34, 42000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — yukarı akışa giriş.",
            "{name}: keşif — nehir koridoru ve yamaçlar.",
            "{name}: önemli nokta — ana yatak.",
            "{name}: genel bakış — akış yönünde geniş çerçeve.",
        ),
        "card": {
            "yukseklik": "akarsu yatağı",
            "bolge": "Nehir koridoru",
            "ozet": "{name}: nehir sınıfı — akış ve vadi tabanı.",
        },
    },
    "volkan": {
        "offsets": [(0.06, 0.04), (0.025, -0.02), (0.0, 0.0), (-0.05, -0.03)],
        "cams": [
            (210, -28, 22000, 4.5),
            (180, -24, 15000, 4.5),
            (160, -22, 11000, 5.0),
            (40, -34, 28000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — konik siluet.",
            "{name}: keşif — yamaç ve lav alanları.",
            "{name}: önemli nokta — zirve/krater.",
            "{name}: genel bakış — geniş açı.",
        ),
        "card": {
            "yukseklik": "koni yüksekliği",
            "bolge": "Volkanik yapı",
            "ozet": "{name}: volkan sınıfı — koni ve krater.",
        },
    },
    "selale": {
        "offsets": [(0.03, 0.02), (0.012, -0.01), (0.0, 0.0), (-0.025, 0.015)],
        "cams": [
            (200, -26, 12000, 4.2),
            (160, -20, 7000, 4.5),
            (140, -18, 4500, 5.0),
            (320, -30, 16000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — şelaleye yaklaşım.",
            "{name}: keşif — düşüş hattı ve yamaç.",
            "{name}: önemli nokta — su perdesi / kanyon ağzı.",
            "{name}: genel bakış — havza çerçevesi.",
        ),
        "card": {
            "yukseklik": "düşüş yüksekliği",
            "bolge": "Şelale",
            "ozet": "{name}: şelale sınıfı — düşüş ve vadi bağlantısı.",
        },
    },
    "delta": {
        "offsets": [(0.09, 0.04), (0.03, -0.05), (0.0, 0.0), (-0.07, 0.05)],
        "cams": [
            (180, -38, 48000, 4.2),
            (120, -32, 28000, 4.5),
            (90, -30, 20000, 5.0),
            (40, -40, 56000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — delta ovasına uzak bakış.",
            "{name}: keşif — kollar ve tortu yelpazesi.",
            "{name}: önemli nokta — ana ağız / kıyı.",
            "{name}: genel bakış — delta sistemi.",
        ),
        "card": {
            "yukseklik": "delta ovası",
            "bolge": "Nehir deltası",
            "ozet": "{name}: delta sınıfı — kollar ve kıyı yayılımı.",
        },
    },
    "col": {
        "offsets": [(0.12, 0.05), (0.04, -0.08), (0.0, 0.0), (-0.1, 0.06)],
        "cams": [
            (200, -28, 52000, 4.2),
            (150, -24, 32000, 4.5),
            (180, -22, 22000, 5.0),
            (40, -32, 60000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — çöl ufku.",
            "{name}: keşif — kum / kaya dokusu.",
            "{name}: önemli nokta — karakteristik yüzey.",
            "{name}: genel bakış — geniş çöl çerçevesi.",
        ),
        "card": {
            "yukseklik": "çöl yüzeyi",
            "bolge": "Çöl",
            "ozet": "{name}: çöl sınıfı — kurak arazi ve ufuk.",
        },
    },
    "ada": {
        "offsets": [(0.08, 0.05), (0.03, -0.04), (0.0, 0.0), (-0.06, 0.04)],
        "cams": [
            (200, -32, 36000, 4.2),
            (140, -26, 20000, 4.5),
            (180, -24, 14000, 5.0),
            (40, -36, 42000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — ada silueti denizin ortasında.",
            "{name}: keşif — kıyı hattı.",
            "{name}: önemli nokta — iç / yüksek arazi.",
            "{name}: genel bakış — ada ve çevre suları.",
        ),
        "card": {
            "yukseklik": "ada rölyefi",
            "bolge": "Ada",
            "ozet": "{name}: ada sınıfı — kıyı ve iç arazi.",
        },
    },
    "sirt": {
        "offsets": [(0.05, 0.03), (0.02, -0.03), (0.0, 0.0), (-0.04, 0.02)],
        "cams": [
            (200, -30, 22000, 4.2),
            (150, -24, 14000, 4.5),
            (180, -22, 10000, 5.0),
            (320, -32, 26000, 4.0),
        ],
        "infos": (
            "{name}: başlangıç — sırt hattı uzak bakış.",
            "{name}: keşif — sırt boyunca.",
            "{name}: önemli nokta — ana sırt.",
            "{name}: genel bakış — silsile çerçevesi.",
        ),
        "card": {
            "yukseklik": "sırt kotu",
            "bolge": "Sırt",
            "ozet": "{name}: sırt sınıfı — hat ve etek.",
        },
    },
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
    """
    Metin / OSM ipucundan doğal sınıf.
    Önce açık sınıf sözcükleri; sonra tip_hint (yalnız NATURE_TIPS ise).
    İsim listesi yok — «Nil» özel değil; «nehir/nehri/river» sınıfı bağlar.
    """
    blob = _norm(" ".join(str(t or "") for t in texts if t))
    if not blob and not tip_hint:
        return None

    # Sıra: özgül → genel (dağ en sonda)
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
        (r"\b(volkan|volkani|volcano|crater)\b", "volkan"),
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
    # OSM / geo eşlemeleri
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


def _stop(
    lat: float,
    lon: float,
    *,
    heading: float,
    pitch: float,
    range_m: float,
    info: str,
    dwell: float = 4.0,
    title: str = "",
    phase: str = "",
    phase_label: str = "",
) -> dict[str, Any]:
    return {
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "heading": heading,
        "pitch": pitch,
        "range": range_m,
        "info": info,
        "title": title or phase_label or "",
        "dwell_sec": dwell,
        "phase": phase or "",
        "phase_label": phase_label or "",
    }


def _offset(lat: float, lon: float, dlat: float, dlon: float) -> tuple[float, float]:
    return lat + dlat, lon + dlon


def _card_for_class(tip: str, label: str, *, bolge_hint: str | None = None) -> dict[str, Any]:
    tip_l = (tip or "dag").lower()
    if tip_l not in _CLASS_PROFILES:
        tip_l = "dag"
    tmpl = _CLASS_PROFILES[tip_l]["card"]
    name = label or "Hedef"
    return {
        "title": name,
        "yukseklik": tmpl["yukseklik"],
        "bolge": (bolge_hint or tmpl["bolge"]),
        "tur": TIP_LABELS.get(tip_l, tip_l),
        "tip": tip_l,
        "ozet": str(tmpl["ozet"]).format(name=name),
    }


def build_stops_for_tip(
    tip: str,
    lat: float,
    lon: float,
    label: str,
) -> list[dict[str, Any]]:
    """Sınıf profilinden 4 aşamalı durak."""
    tip_l = (tip or "").lower()
    if tip_l not in _CLASS_PROFILES:
        tip_l = "dag"
    prof = _CLASS_PROFILES[tip_l]
    name = label or "Hedef"
    stops: list[dict[str, Any]] = []
    for i, ((pkey, plabel), off, cam, info_t) in enumerate(
        zip(PHASES, prof["offsets"], prof["cams"], prof["infos"])
    ):
        pt = _offset(lat, lon, off[0], off[1]) if (off[0] or off[1]) else (lat, lon)
        h, p, r, d = cam
        stops.append(
            _stop(
                pt[0],
                pt[1],
                heading=h,
                pitch=p,
                range_m=r,
                info=str(info_t).format(name=name),
                dwell=d,
                title=plabel,
                phase=pkey,
                phase_label=plabel,
            )
        )
    return stops


def _strip_tour_words(n: str) -> str:
    t = n
    t = re.sub(
        r"\b(gezdir|gezdirelim|turu|turunu|tur|tura|gezgini|gezgin|baslat|basla|baslatin)\b",
        " ",
        t,
    )
    t = re.sub(r"\b(dunya\s+gezgini|harita\s+turu)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def looks_like_tour_control(n: str) -> str | None:
    if re.search(
        r"\b(turu?\s*(durdur|duraklat|beklet)|gezgini?\s*(durdur|duraklat)|tour\s*pause|pause\s*tour)\b",
        n,
    ):
        return "tour_pause"
    if re.search(
        r"\b(tura?\s*devam|turu?\s*devam|gezgini?\s*devam|tour\s*resume|resume\s*tour|devam\s*et)\b",
        n,
    ):
        return "tour_resume"
    if re.search(
        r"\b(turu?\s*(bitir|iptal|kapat|sonlandir)|gezgini?\s*(bitir|kapat)|tour\s*stop|stop\s*tour)\b",
        n,
    ):
        return "tour_stop"
    if re.search(
        r"\b(onceki\s*durak|geri\s*(git|don|durak)|tur\s*geri|tour\s*prev|prev\s*(stop|tour))\b",
        n,
    ):
        return "tour_prev"
    if re.search(
        r"\b(durak\s*atla|atl[aı]|skip\s*(stop|tour)|tour\s*skip)\b",
        n,
    ):
        return "tour_skip"
    if re.search(
        r"\b(sonraki\s*durak|ileri\s*(git|durak)?|tur\s*ileri|next\s*(stop|tour)|tour\s*next)\b",
        n,
    ):
        return "tour_next"
    return None


def looks_like_tour_start(n: str) -> bool:
    if looks_like_tour_control(n):
        return False
    if re.search(r"\b(dunya\s*turu|panoramik|kure\s*tur|globe\s*tour|tur\s*mod)\b", n):
        if not re.search(r"\b(gezdir|gezgin)\b", n):
            return False
    if re.search(r"\b(gezdir|gezdirelim|dunya\s+gezgini|gezgin\s+modu)\b", n):
        return True
    if re.search(r"\b\w+\s+turu\b", n) and not re.search(
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
    """Sınıf profili + koordinat. İsim özel tur listesi yok."""
    label = ""
    lat = lon = None
    tip_hint = None
    bolge_hint = None

    if geo and geo.get("lat") is not None and geo.get("lon") is not None:
        lat = float(geo["lat"])
        lon = float(geo["lon"])
        label = str(geo.get("label") or place or "Tur")
        tip_hint = str(geo.get("tip") or "").lower() or None
        bolge_hint = geo.get("bolge") or geo.get("region") or geo.get("country")
        if isinstance(bolge_hint, str) and not bolge_hint.strip():
            bolge_hint = None
    elif place:
        # Yalnız yer adı: sınıf metinden; koordinat yoksa tur kurulamaz
        label = place
        tip_hint = None

    tip = classify_nature_tip(
        place or "",
        label,
        tip_hint=tip_hint,
    )
    if not tip:
        # Doğal sınıf yok → dağa zorlama (Nil/şehir hatası); tur yok
        return None

    if lat is None or lon is None:
        return None

    stops = build_stops_for_tip(tip, lat, lon, label)
    card = _card_for_class(tip, label, bolge_hint=str(bolge_hint) if bolge_hint else None)
    return {
        "ok": True,
        "version": H10_VERSION,
        "h9_compat": H9_VERSION,
        "id": "class:" + tip + ":" + re.sub(r"[^a-z0-9]+", "", _norm(label))[:20],
        "label": label,
        "tip": tip,
        "lat": lat,
        "lon": lon,
        "stops": stops,
        "stop_count": len(stops),
        "phases": [{"id": a, "label": b} for a, b in PHASES],
        "card": card,
        "nature": True,
        "smart": True,
        "class_based": True,
    }


def try_resolve_tour_intent(norm_text: str) -> dict[str, Any] | None:
    n = norm_text
    ctrl = looks_like_tour_control(n)
    if ctrl:
        return {
            "action": ctrl,
            "fiil": "gezgin",
            "organ": "harita",
            "guven": 0.94,
            "hedef": None,
            "tour_ctrl": ctrl,
        }
    if not looks_like_tour_start(n):
        return None
    place = extract_tour_place(n)
    return {
        "action": "tour_start",
        "fiil": "gezgin",
        "organ": "harita",
        "guven": 0.93,
        "hedef": place,
        "tour_start": True,
    }
