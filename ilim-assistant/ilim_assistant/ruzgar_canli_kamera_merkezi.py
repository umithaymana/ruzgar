# -*- coding: utf-8 -*-
"""
Rüzgar Canlı Kamera Merkezi — açık lisans / açık yayın (scrape yok).

Dünya: Fintraffic + env JSON.
Uzay: NASA TV HLS (hesap yok) + GIBS/NOAA katalog (katman/yayın).
"""
from __future__ import annotations

import math
import re
from typing import Any

from ilim_assistant.ruzgar_canli_kamera import (
    fetch_open_json_cameras,
    nearby_open_cameras,
)
from ilim_assistant.ruzgar_kamera_rig import CANLI_KAYNAK_ENVANTER

# Son liste — «aç / tam ekran / dört kamera» için (tek masa oturumu)
_LAST: dict[str, Any] = {
    "kameralar": [],
    "uzay": [],
    "place": "",
    "lat": None,
    "lon": None,
    "kategori": "",
}

# Hesap/API istemeyen uzay yayınları (resmi Akamai NASA TV)
UZAY_KAMERALAR: list[dict[str, Any]] = [
    {
        "id": "nasa-tv-public",
        "ad": "NASA TV Public",
        "tur": "uzay/yayin",
        "canli": True,
        "media": "video",
        "hls": "https://ntv1.akamaiized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8",
        "page": "https://www.nasa.gov/nasatv/",
        "source": "NASA",
        "license": "NASA public",
        "attribution": "NASA TV",
        "hesap": False,
        "api": False,
    },
    {
        "id": "nasa-tv-media",
        "ad": "NASA TV Media",
        "tur": "uzay/yayin",
        "canli": True,
        "media": "video",
        "hls": "https://ntv2.akamaiized.net/hls/live/2013923/NASA-NTV2-HLS/master.m3u8",
        "page": "https://www.nasa.gov/nasatv/",
        "source": "NASA",
        "license": "NASA public",
        "attribution": "NASA TV Media",
        "hesap": False,
        "api": False,
    },
    {
        "id": "nasa-gibs-dunya",
        "ad": "NASA GIBS · Dünya uydu katmanı",
        "tur": "uzay/dunya",
        "canli": False,
        "media": "katman",
        "hls": "",
        "page": "https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs",
        "action": "mode_4d",
        "source": "NASA GIBS",
        "license": "ücretsiz (NASA)",
        "attribution": "NASA GIBS",
        "hesap": False,
        "api": False,
        "note": "Canlı kamera değil — 4D uydu katmanı (harita)",
    },
    {
        "id": "noaa-goes",
        "ad": "NOAA GOES Dünya görüntüleri",
        "tur": "uzay/dunya",
        "canli": True,
        "media": "foto",
        "hls": "",
        "image": "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/FD/GEOCOLOR/latest.jpg",
        "page": "https://www.star.nesdis.noaa.gov/goes/",
        "source": "NOAA",
        "license": "ABD kamu (NOAA)",
        "attribution": "NOAA NESDIS STAR",
        "hesap": False,
        "api": False,
    },
]

UZAY_BEKLEYEN: list[dict[str, Any]] = [
    {
        "ad": "ISS sürekli Dünya kamerası (HDEV)",
        "durum": "HDEV kapandı (2019); yerine sürekli resmi HLS sabit değil",
        "hesap": False,
        "api": False,
    },
    {
        "ad": "NASA Trek / Ion Moon-Mars",
        "durum": "WMTS/Ion — kamera mozaiği değil, tiles",
        "hesap": "Ion için evet",
        "api": "kısmen",
    },
]

_KAT_ALIASES: dict[str, tuple[str, ...]] = {
    "trafik": ("trafik", "traffic", "yol"),
    "hava": ("hava", "weather", "meteor"),
    "turizm": ("turizm", "tourism", "sehir"),
    "dag": ("dag", "mountain", "alpin"),
    "liman": ("liman", "port", "harbour", "harbor"),
    "deniz": ("deniz", "sea", "marine", "kiyi"),
    "kayak": ("kayak", "ski", "piste"),
}


def _norm(s: str) -> str:
    t = (s or "").lower()
    rep = str.maketrans(
        {
            "ı": "i",
            "İ": "i",
            "ş": "s",
            "Ş": "s",
            "ğ": "g",
            "Ğ": "g",
            "ü": "u",
            "Ü": "u",
            "ö": "o",
            "Ö": "o",
            "ç": "c",
            "Ç": "c",
        }
    )
    t = t.translate(rep)
    t = re.sub(r"[^\w\s\-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _place_query(raw: str) -> str:
    """«istanbulda» → «istanbul» — locative ek geocode’u bozmasın."""
    p = _norm(raw)
    if not p:
        return ""
    # tek kelime veya son kelime: -da/-de/-ta/-te/-daki/-deki …
    p = re.sub(
        r"(daki|deki|daki|teki|dan|den|tan|ten|da|de|ta|te)$",
        "",
        p,
    ).strip()
    p = re.sub(r"\b(icin|icin|bul|getir|goster|listele)\b", " ", p)
    return re.sub(r"\s+", " ", p).strip()


def _haversine_km(a: float, b: float, c: float, d: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a)
    dl = math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(x)))


def _enrich(cam: dict[str, Any]) -> dict[str, Any]:
    c = dict(cam)
    img = str(c.get("image") or "")
    hls = str(c.get("hls") or "")
    media = str(c.get("media") or "")
    if not media:
        if hls:
            media = "video"
        elif img:
            media = "foto"
        else:
            media = "bilinmiyor"
    c["media"] = media
    c["canli"] = bool(c.get("canli")) if "canli" in c else bool(hls) or bool(img)
    c["tur"] = str(c.get("tur") or "genel")
    c["ad"] = str(c.get("ad") or c.get("id") or "kamera")
    c["source"] = str(c.get("source") or c.get("attribution") or "?")
    if c.get("distance_km") is not None:
        try:
            c["distance_km"] = round(float(c["distance_km"]), 2)
        except (TypeError, ValueError):
            pass
    return c


def _match_tur(cam: dict[str, Any], kategori: str | None) -> bool:
    if not kategori:
        return True
    keys = _KAT_ALIASES.get(kategori, (kategori,))
    blob = _norm(
        " ".join(
            str(x)
            for x in (cam.get("tur"), cam.get("ad"), cam.get("source"), cam.get("id"))
            if x
        )
    )
    return any(k in blob for k in keys)


def format_camera_list_reply(pack: dict[str, Any]) -> str:
    """Sohbet için kısa, okunaklı özet (duvar metin yok)."""
    cams = [_enrich(c) for c in (pack.get("kameralar") or [])]
    title = pack.get("title") or "Canlı kameralar"
    if not cams:
        wait = pack.get("bekleyen") or []
        note = str(pack.get("note") or "").strip()
        lines = [title, note or "Bu konumda bağlı açık lisanslı kamera yok."]
        if wait:
            lines.append("Gerekli: " + ", ".join(str(x) for x in wait[:3]))
        lines.append("Not: Fintraffic yalnız Finlandiya — başka şehre karıştırılmaz.")
        return "\n".join(lines)
    lines = [f"{title} · {len(cams)} sonuç"]
    for i, c in enumerate(cams[:6], 1):
        dist = c.get("distance_km")
        dist_s = f" · {dist} km" if dist is not None else ""
        lines.append(f"{i}. {c.get('ad')}{dist_s} · {c.get('tur')} · {c.get('source')}")
    if len(cams) > 6:
        lines.append(f"… +{len(cams) - 6} daha (sahnede)")
    lines.append("Komut: aç · tam ekran aç · dört kamera aç")
    return "\n".join(lines)


def format_camera_speak(pack: dict[str, Any]) -> str:
    """TTS — tek kısa cümle (uzun liste okutma = yavaşlık)."""
    cams = pack.get("kameralar") or []
    title = pack.get("title") or "Canlı kameralar"
    n = len(cams)
    if not n:
        return f"{title}. Açık kamera yok."
    first = str((cams[0] or {}).get("ad") or "kamera")
    return f"{title}. {n} kamera. İlk: {first}. Aç diyerek sahneye al."


def format_uzay_list_reply() -> str:
    _LAST["uzay"] = list(UZAY_KAMERALAR)
    lines = [f"Uzay kameraları · {len(UZAY_KAMERALAR)} açık kaynak"]
    for i, c in enumerate(UZAY_KAMERALAR, 1):
        e = _enrich(c)
        lines.append(f"{i}. {e['ad']} · {e['media']} · {e['source']}")
    lines.append("Komut: NASA canlı yayınlarını aç · dünya kamerasını aç")
    return "\n".join(lines)


def format_uzay_speak() -> str:
    return (
        f"Uzayda {len(UZAY_KAMERALAR)} açık yayın var. "
        "NASA televizyonu veya dünya kamerası diyebilirsin."
    )


def list_world_cameras(
    *,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float = 120.0,
    limit: int = 12,
    kategori: str | None = None,
    place_label: str = "",
) -> dict[str, Any]:
    if lat is None or lon is None:
        pack = fetch_open_json_cameras(limit=max(limit * 3, 40))
        cams = [_enrich(c) for c in (pack.get("kameralar") or [])]
        # merkez yoksa Fintraffic örneklerini sıralı ver
        for c in cams:
            c["distance_km"] = None
    else:
        pack = nearby_open_cameras(
            lat=float(lat), lon=float(lon), radius_km=float(radius_km), limit=200
        )
        cams = [_enrich(c) for c in (pack.get("kameralar") or [])]

    if kategori:
        cams = [c for c in cams if _match_tur(c, kategori)]

    # kategori daraldıysa ve boşsa: bağlı kaynak dürüst not
    bekleyen = []
    if kategori and not cams:
        bekleyen = [
            e.get("kurum") or e.get("id")
            for e in CANLI_KAYNAK_ENVANTER
            if kategori in _norm(str(e.get("tur") or ""))
            or kategori in _norm(str(e.get("id") or ""))
        ]

    cams = cams[:limit]
    _LAST["kameralar"] = cams
    _LAST["place"] = place_label
    _LAST["lat"] = lat
    _LAST["lon"] = lon
    _LAST["kategori"] = kategori or ""

    title = "Canlı kameralar"
    if place_label:
        title += f" · {place_label}"
    if kategori:
        title += f" · {kategori}"
    if lat is not None and lon is not None:
        title += " · yakındakiler"

    note = pack.get("note") or ""
    if kategori in ("turizm", "dag", "liman", "deniz", "kayak") and not cams:
        note = (
            (note + " ")
            + f"«{kategori}» için açık API bağlı değil (Windy/belediye hesap veya sözleşme)."
        ).strip()

    return {
        "ok": True,
        "title": title,
        "kameralar": cams,
        "count": len(cams),
        "lat": lat,
        "lon": lon,
        "kategori": kategori,
        "place": place_label,
        "note": note,
        "bekleyen": bekleyen,
        "envanter": CANLI_KAYNAK_ENVANTER,
        "reply": "",  # doldurulacak
    }


def last_listed() -> dict[str, Any]:
    return dict(_LAST)


def pick_cameras_for_layout(n: int) -> list[dict[str, Any]]:
    n = max(1, min(16, int(n)))
    world = list(_LAST.get("kameralar") or [])
    uzay = list(_LAST.get("uzay") or UZAY_KAMERALAR)
    # Önce dünya, yetmezse uzay
    out = [_enrich(c) for c in world[:n]]
    if len(out) < n:
        for u in uzay:
            if len(out) >= n:
                break
            out.append(_enrich(u))
    if not out:
        out = [_enrich(c) for c in UZAY_KAMERALAR[:n]]
    return out[:n]


def looks_like_canli_kamera(n: str) -> dict[str, Any] | None:
    """norm metin → süper-el action paketi."""
    if not n:
        return None

    # --- aç / yerleşim ---
    if re.search(r"\b(tam\s*ekran\s*ac|fullscreen)\b", n):
        return {
            "action": "cam_layout_full",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.95,
            "layout": "full",
            "count": 1,
            "canli_kamera": True,
        }
    if re.search(r"\b(yarim\s*ekran\s*ac|half\s*screen)\b", n):
        return {
            "action": "cam_layout_half",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.95,
            "layout": "half",
            "count": 1,
            "canli_kamera": True,
        }
    if re.search(r"\b(dort\s*kamera\s*ac|4\s*kamera|2\s*[x×]\s*2)\b", n):
        return {
            "action": "cam_layout_4",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.95,
            "layout": "grid4",
            "count": 4,
            "canli_kamera": True,
        }
    if re.search(r"\b(sekiz\s*kamera\s*ac|8\s*kamera)\b", n):
        return {
            "action": "cam_layout_8",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.95,
            "layout": "grid8",
            "count": 8,
            "canli_kamera": True,
        }
    mcount = re.search(r"\b(\d{1,2})\s*kamera\s*ac\b", n)
    if mcount:
        return {
            "action": "cam_layout_n",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.94,
            "layout": "grid",
            "count": int(mcount.group(1)),
            "canli_kamera": True,
        }
    # yalnız «aç» — önceki liste bağlamı
    if re.search(r"^(ac|ac\s*kamera|kamerayi\s*ac|canli\s*kamerayi\s*ac)$", n):
        return {
            "action": "cam_open",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.9,
            "layout": "full",
            "count": 1,
            "canli_kamera": True,
        }

    # --- uzay ---
    if re.search(r"\b(uzay\s*kameralar[iı]?|space\s*cameras?)\b", n):
        return {
            "action": "cam_list_space",
            "fiil": "listele",
            "organ": "cam",
            "guven": 0.95,
            "canli_kamera": True,
            "space": True,
        }
    if re.search(r"\b(iss\s*kamera\w*|iss\s*(yayin|canli)\w*|iss\s*ac)\b", n):
        return {
            "action": "cam_open_iss",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.93,
            "canli_kamera": True,
            "space": True,
        }
    if re.search(
        r"\b(nasa\s*(canli\s*)?(yayin\w*|tv)|nasa\s*canli|nasa\s*yayinlarini\s*ac)\b",
        n,
    ):
        return {
            "action": "cam_open_nasa",
            "fiil": "goster",
            "organ": "cam",
            "guven": 0.94,
            "canli_kamera": True,
            "space": True,
            "layout": "full",
            "count": 1,
        }
    if re.search(
        r"\b(dunya\s*kamera\w*|dunya\s*kamerasini\s*ac|gibs\s*ac)\b", n
    ):
        return {
            "action": "cam_open_earth_view",
            "fiil": "goster",
            "organ": "harita",
            "guven": 0.93,
            "canli_kamera": True,
            "space": True,
            "map_action": "mode_4d",
        }

    # --- dünya liste ---
    kat = None
    for k, keys in _KAT_ALIASES.items():
        if any(re.search(rf"\b{re.escape(x)}\b", n) for x in keys):
            if re.search(r"kamera", n) or re.search(r"canli", n):
                kat = k
                break
    if re.search(r"\b(trafik\s*kameralar)", n):
        kat = "trafik"
    if re.search(r"\b(hava\s*durumu\s*kameralar|hava\s*kameralar)", n):
        kat = "hava"

    near = bool(
        re.search(
            r"\b(yakinimdaki|en\s*yakin|yakindaki|nearby|closest)\b", n
        )
        and re.search(r"\b(canli\s*)?kamera", n)
    )
    place_list = bool(
        re.search(r"\b(canli\s*kameralar|canli\s*kamera|live\s*cameras?)\b", n)
    )
    if not (near or place_list or kat):
        return None

    # yer çıkar: «paris canli kameralar»
    place = None
    m = re.search(
        r"^(.+?)\s+(canli\s*kameralar|canli\s*kamera|live\s*cameras?)\b", n
    )
    if m:
        place = m.group(1).strip()
        place = re.sub(
            r"\b(yakinimdaki|en\s*yakin|yakindaki|listele|goster)\b", "", place
        ).strip()
        place = _place_query(place) or place
    if near and not place:
        place = None  # konum masa/haritadan

    return {
        "action": "cam_list",
        "fiil": "listele",
        "organ": "cam",
        "guven": 0.94,
        "canli_kamera": True,
        "kategori": kat,
        "nearby": near,
        "hedef": place or None,
        "place": place or None,
    }


def execute_canli_intent(
    intent: dict[str, Any],
    *,
    lat: float | None = None,
    lon: float | None = None,
    place_hint: str = "",
) -> dict[str, Any]:
    """Liste / aç paketini üret (istemci mozaiği + sohbet metni)."""
    act = str(intent.get("action") or "")

    if act == "cam_list_space":
        reply = format_uzay_list_reply()
        return {
            "ok": True,
            "action": act,
            "organ": "cam",
            "layout": "browse",
            "reply": reply,
            "speak": format_uzay_speak(),
            "kameralar": list(UZAY_KAMERALAR),
            "space": True,
        }

    if act == "cam_open_iss":
        reply = (
            "ISS sürekli Dünya kamerası (HDEV) 2019’da kapandı. "
            "Şimdilik NASA TV açık yayınını açıyorum; ISS özel HLS yok."
        )
        cams = pick_cameras_for_layout(1)
        # NASA public tercih
        cams = [_enrich(UZAY_KAMERALAR[0])]
        _LAST["uzay"] = list(UZAY_KAMERALAR)
        return {
            "ok": True,
            "action": "cam_layout_full",
            "organ": "cam",
            "layout": "full",
            "reply": reply,
            "kameralar": cams,
            "space": True,
            "honest": True,
        }

    if act == "cam_open_nasa":
        cams = [_enrich(UZAY_KAMERALAR[0])]
        return {
            "ok": True,
            "action": "cam_layout_full",
            "organ": "cam",
            "layout": "full",
            "reply": "NASA TV Public yayını · sahne",
            "kameralar": cams,
            "space": True,
        }

    if act == "cam_open_earth_view":
        return {
            "ok": True,
            "action": "mode_4d",
            "organ": "harita",
            "map_action": "mode_4d",
            "reply": "Dünya kamerası → NASA GIBS 4D uydu katmanı (canlı kamera değil).",
            "space": True,
        }

    if act in (
        "cam_open",
        "cam_layout_full",
        "cam_layout_half",
        "cam_layout_4",
        "cam_layout_8",
        "cam_layout_n",
    ):
        layout = str(intent.get("layout") or "full")
        count = int(intent.get("count") or (4 if layout == "grid4" else 1))
        if act == "cam_layout_4":
            count, layout = 4, "grid4"
        if act == "cam_layout_8":
            count, layout = 8, "grid8"
        if act == "cam_layout_half":
            count, layout = 1, "half"
        if act in ("cam_open", "cam_layout_full"):
            count, layout = 1, "full" if act != "cam_layout_half" else layout
        cams = pick_cameras_for_layout(count)
        return {
            "ok": True,
            "action": act,
            "organ": "cam",
            "layout": layout,
            "count": count,
            "kameralar": cams,
            "reply": f"Sahne · {layout} · {len(cams)} kamera",
        }

    # cam_list
    kategori = intent.get("kategori")
    place_raw = str(intent.get("place") or intent.get("hedef") or place_hint or "").strip()
    place = _place_query(place_raw) if place_raw else ""
    use_lat, use_lon = lat, lon
    label = place or place_raw
    geo_ok = False

    if place:
        try:
            from ilim_assistant.sahne_harita_geo import geocode

            geo = geocode(place, allow_network=True)
            if geo and geo.get("lat") is not None:
                use_lat = float(geo["lat"])
                use_lon = float(geo["lon"])
                label = str(geo.get("label") or place)
                geo_ok = True
        except Exception:
            geo_ok = False

    # Yer sorulduysa: yalnızca o konum civarı. Başka ülkenin kamerasını «İstanbul» diye gösterme.
    if place and not geo_ok:
        pack = {
            "ok": True,
            "title": f"Canlı kameralar · {label}",
            "kameralar": [],
            "count": 0,
            "lat": None,
            "lon": None,
            "kategori": kategori,
            "place": label,
            "note": "Konum çözülemedi.",
            "bekleyen": [],
            "envanter": CANLI_KAYNAK_ENVANTER,
        }
        _LAST["kameralar"] = []
        pack["reply"] = (
            f"«{label}» için konum bulunamadı. "
            "«İstanbul canlı kameralar» gibi yazmayı dene."
        )
        pack["speak"] = f"{label} konumu bulunamadı."
        pack["action"] = "cam_list"
        pack["organ"] = "cam"
        pack["layout"] = "browse"
        pack["geo"] = None
        return pack

    if place and geo_ok:
        radius = 80.0
        pack = list_world_cameras(
            lat=use_lat,
            lon=use_lon,
            radius_km=radius,
            kategori=kategori,
            place_label=label,
            limit=8,
        )
        if not pack.get("kameralar"):
            pack["note"] = (
                f"«{label}» civarında bağlı açık lisanslı kamera yok. "
                "Şu an dünya feed’i Fintraffic (Finlandiya). "
                "İstanbul için Windy/belediye açık API veya hesap gerekir."
            )
            pack["bekleyen"] = [
                "Windy Webcams (hesap)",
                "Belediye / turizm open-data",
                "NSW/NYC dışı yerel açık JSON",
            ]
            _LAST["kameralar"] = []
    elif intent.get("nearby") and (use_lat is None or use_lon is None):
        pack = {
            "ok": True,
            "title": "Canlı kameralar · yakınımda",
            "kameralar": [],
            "count": 0,
            "note": "Önce bir yer seç (ör. İstanbul gezi) veya «İstanbul canlı kameralar».",
            "bekleyen": [],
            "envanter": CANLI_KAYNAK_ENVANTER,
        }
        _LAST["kameralar"] = []
    elif use_lat is not None and use_lon is not None:
        pack = list_world_cameras(
            lat=use_lat,
            lon=use_lon,
            radius_km=80.0,
            kategori=kategori,
            place_label=label or "konum",
            limit=8,
        )
    else:
        # Yer yok, kategori var (trafik/hava) → bağlı açık feed (Fintraffic)
        pack = list_world_cameras(
            lat=None,
            lon=None,
            kategori=kategori,
            place_label=kategori or "genel",
            limit=8,
        )
        if not place and not kategori:
            pack["note"] = (
                (pack.get("note") or "")
                + " Genel liste (Fintraffic). Şehir için «İstanbul canlı kameralar» de."
            ).strip()

    pack["reply"] = format_camera_list_reply(pack)
    pack["speak"] = format_camera_speak(pack)
    pack["action"] = "cam_list"
    pack["organ"] = "cam"
    pack["layout"] = "browse"
    pack["geo"] = (
        {"lat": use_lat, "lon": use_lon, "label": label}
        if use_lat is not None and use_lon is not None
        else None
    )
    return pack


def api_gerekenler_rapor() -> dict[str, Any]:
    return {
        "api_gerekenler": [
            "NSW Live Traffic (API key)",
            "NYC DOT (sözleşme)",
            "Fintraffic dışı belediye open-data URL’leri (kaynağa bağlı)",
        ],
        "hesap_gerekenler": [
            "Windy Webcams (turizm/dağ/kayak)",
            "Cesium Ion (Ay/Mars sahne)",
        ],
        "ucretli_olanlar": [
            "Windy ticari kota / redistrib kısıt",
            "NYC DOT abone",
            "Cesium Ion kota",
        ],
    }
