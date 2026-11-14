# -*- coding: utf-8 -*-
"""Sahne harita — yer adı → lat/lon/zoom/tip (yerel sözlük + Nominatim yedek)."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any

# Tip → zoom (Mimar 2026-11-14)
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
    "volkan": 14,
    "selale": 15,
    "delta": 10,
    "col": 9,
    "ada": 12,
    "sirt": 13,
    "kopru": 17,
    "bina": 18,
    "nokta": 18,
}

# zoom alanları tip ile hizalı; tip her kayıtta tutulur
_YEREL: dict[str, dict[str, Any]] = {
    "turkiye": {"lat": 39.0, "lon": 35.2, "zoom": 7, "tip": "ulke", "label": "Türkiye"},
    "turkey": {"lat": 39.0, "lon": 35.2, "zoom": 7, "tip": "ulke", "label": "Türkiye"},
    "anadolu": {"lat": 39.2, "lon": 35.5, "zoom": 7, "tip": "ulke", "label": "Anadolu"},
    "istanbul": {"lat": 41.0082, "lon": 28.9784, "zoom": 11, "tip": "il", "label": "İstanbul"},
    "ankara": {"lat": 39.9334, "lon": 32.8597, "zoom": 11, "tip": "il", "label": "Ankara"},
    "izmir": {"lat": 38.4192, "lon": 27.1287, "zoom": 11, "tip": "il", "label": "İzmir"},
    "bursa": {"lat": 40.1885, "lon": 29.0610, "zoom": 11, "tip": "il", "label": "Bursa"},
    "antalya": {"lat": 36.8969, "lon": 30.7133, "zoom": 11, "tip": "il", "label": "Antalya"},
    "adana": {"lat": 37.0, "lon": 35.3213, "zoom": 11, "tip": "il", "label": "Adana"},
    "konya": {"lat": 37.8746, "lon": 32.4932, "zoom": 11, "tip": "il", "label": "Konya"},
    "gaziantep": {"lat": 37.0662, "lon": 37.3833, "zoom": 11, "tip": "il", "label": "Gaziantep"},
    "kayseri": {"lat": 38.7312, "lon": 35.4787, "zoom": 11, "tip": "il", "label": "Kayseri"},
    "mersin": {"lat": 36.8121, "lon": 34.6415, "zoom": 11, "tip": "il", "label": "Mersin"},
    "diyarbakir": {"lat": 37.9144, "lon": 40.2306, "zoom": 11, "tip": "il", "label": "Diyarbakır"},
    "samsun": {"lat": 41.2867, "lon": 36.33, "zoom": 11, "tip": "il", "label": "Samsun"},
    "trabzon": {"lat": 41.0027, "lon": 39.7168, "zoom": 11, "tip": "il", "label": "Trabzon"},
    "erzurum": {"lat": 39.9043, "lon": 41.2679, "zoom": 11, "tip": "il", "label": "Erzurum"},
    "van": {"lat": 38.4891, "lon": 43.4089, "zoom": 11, "tip": "il", "label": "Van"},
    "eskisehir": {"lat": 39.7767, "lon": 30.5206, "zoom": 11, "tip": "il", "label": "Eskişehir"},
    "malatya": {"lat": 38.3552, "lon": 38.3095, "zoom": 11, "tip": "il", "label": "Malatya"},
    "denizli": {"lat": 37.7765, "lon": 29.0864, "zoom": 11, "tip": "il", "label": "Denizli"},
    "sivas": {"lat": 39.7477, "lon": 37.0179, "zoom": 11, "tip": "il", "label": "Sivas"},
    "balikesir": {"lat": 39.6484, "lon": 27.8826, "zoom": 11, "tip": "il", "label": "Balıkesir"},
    "kahramanmaras": {"lat": 37.5858, "lon": 36.9371, "zoom": 11, "tip": "il", "label": "Kahramanmaraş"},
    "hatay": {"lat": 36.4018, "lon": 36.3498, "zoom": 11, "tip": "il", "label": "Hatay"},
    "manisa": {"lat": 38.6191, "lon": 27.4289, "zoom": 11, "tip": "il", "label": "Manisa"},
    "aydin": {"lat": 37.8560, "lon": 27.8416, "zoom": 11, "tip": "il", "label": "Aydın"},
    "tekirdag": {"lat": 40.9833, "lon": 27.5167, "zoom": 11, "tip": "il", "label": "Tekirdağ"},
    "sakarya": {"lat": 40.7569, "lon": 30.3781, "zoom": 11, "tip": "il", "label": "Sakarya"},
    "kocaeli": {"lat": 40.8533, "lon": 29.8815, "zoom": 11, "tip": "il", "label": "Kocaeli"},
    "mugla": {"lat": 37.2153, "lon": 28.3636, "zoom": 11, "tip": "il", "label": "Muğla"},
    "canakkale": {"lat": 40.1553, "lon": 26.4142, "zoom": 11, "tip": "il", "label": "Çanakkale"},
    "ordu": {"lat": 40.9862, "lon": 37.8797, "zoom": 11, "tip": "il", "label": "Ordu"},
    "rize": {"lat": 41.0201, "lon": 40.5234, "zoom": 11, "tip": "il", "label": "Rize"},
    "artvin": {"lat": 41.1828, "lon": 41.8183, "zoom": 11, "tip": "il", "label": "Artvin"},
    "palandoken": {"lat": 39.8700, "lon": 41.3000, "zoom": 14, "tip": "dag", "label": "Palandöken"},
    "tortum": {"lat": 40.3000, "lon": 41.5500, "zoom": 13, "tip": "ilce", "label": "Tortum"},
    "oltu": {"lat": 40.5500, "lon": 41.9900, "zoom": 13, "tip": "ilce", "label": "Oltu"},
    "uludag": {"lat": 40.0705, "lon": 29.2213, "zoom": 14, "tip": "dag", "label": "Uludağ"},
    "uludagi": {"lat": 40.0705, "lon": 29.2213, "zoom": 14, "tip": "dag", "label": "Uludağ"},
    # Everest — İstanbul'daki yanlış OSM eşleşmesini engelle (tek merkez)
    "everest": {"lat": 27.9881, "lon": 86.9250, "zoom": 14, "tip": "dag", "label": "Everest"},
    "mounteverest": {"lat": 27.9881, "lon": 86.9250, "zoom": 14, "tip": "dag", "label": "Mount Everest"},
    "everestdagi": {"lat": 27.9881, "lon": 86.9250, "zoom": 14, "tip": "dag", "label": "Everest Dağı"},
    "everestdag": {"lat": 27.9881, "lon": 86.9250, "zoom": 14, "tip": "dag", "label": "Everest Dağı"},
    "chomolungma": {"lat": 27.9881, "lon": 86.9250, "zoom": 14, "tip": "dag", "label": "Everest"},
    "agridagi": {"lat": 39.7019, "lon": 44.2984, "zoom": 14, "tip": "dag", "label": "Ağrı Dağı"},
    "agrida": {"lat": 39.7019, "lon": 44.2984, "zoom": 14, "tip": "dag", "label": "Ağrı Dağı"},
    "ararat": {"lat": 39.7019, "lon": 44.2984, "zoom": 14, "tip": "dag", "label": "Ağrı Dağı"},
    "kackar": {"lat": 40.8330, "lon": 41.1610, "zoom": 13, "tip": "dag", "label": "Kaçkar Dağları"},
    "kackardaglari": {"lat": 40.8330, "lon": 41.1610, "zoom": 13, "tip": "dag", "label": "Kaçkar Dağları"},
    "kackardagi": {"lat": 40.8330, "lon": 41.1610, "zoom": 13, "tip": "dag", "label": "Kaçkar Dağı"},
    "mescitgecidi": {
        "lat": 40.1230,
        "lon": 41.4800,
        "zoom": 16,
        "tip": "gecit",
        "label": "Mescit Geçidi",
    },
    "mescitgecit": {
        "lat": 40.1230,
        "lon": 41.4800,
        "zoom": 16,
        "tip": "gecit",
        "label": "Mescit Geçidi",
    },
    "ziganagecidi": {
        "lat": 40.6450,
        "lon": 39.5050,
        "zoom": 15,
        "tip": "gecit",
        "label": "Zigana Geçidi",
    },
    "zigana": {
        "lat": 40.6450,
        "lon": 39.5050,
        "zoom": 15,
        "tip": "gecit",
        "label": "Zigana Geçidi",
    },
    "kopgecidi": {
        "lat": 40.0350,
        "lon": 40.5150,
        "zoom": 15,
        "tip": "gecit",
        "label": "Kop Geçidi",
    },
    "kopgecit": {
        "lat": 40.0350,
        "lon": 40.5150,
        "zoom": 15,
        "tip": "gecit",
        "label": "Kop Geçidi",
    },
    "bogazkoprusu": {
        "lat": 41.0450,
        "lon": 29.0336,
        "zoom": 17,
        "tip": "kopru",
        "label": "Boğaziçi Köprüsü",
    },
    "bogazkopru": {
        "lat": 41.0450,
        "lon": 29.0336,
        "zoom": 17,
        "tip": "kopru",
        "label": "Boğaziçi Köprüsü",
    },
    "bogazicikoprusu": {
        "lat": 41.0450,
        "lon": 29.0336,
        "zoom": 17,
        "tip": "kopru",
        "label": "Boğaziçi Köprüsü",
    },
    "fsmkoprusu": {
        "lat": 41.0915,
        "lon": 29.0615,
        "zoom": 17,
        "tip": "kopru",
        "label": "Fatih Sultan Mehmet Köprüsü",
    },
    "ayasofya": {
        "lat": 41.0086,
        "lon": 28.9802,
        "zoom": 18,
        "tip": "bina",
        "label": "Ayasofya",
    },
    "ayasof": {
        "lat": 41.0086,
        "lon": 28.9802,
        "zoom": 18,
        "tip": "bina",
        "label": "Ayasofya",
    },
    "almanya": {"lat": 51.1657, "lon": 10.4515, "zoom": 7, "tip": "ulke", "label": "Almanya"},
    "germany": {"lat": 51.1657, "lon": 10.4515, "zoom": 7, "tip": "ulke", "label": "Almanya"},
    "fransa": {"lat": 46.2276, "lon": 2.2137, "zoom": 7, "tip": "ulke", "label": "Fransa"},
    "france": {"lat": 46.2276, "lon": 2.2137, "zoom": 7, "tip": "ulke", "label": "Fransa"},
    "italya": {"lat": 41.8719, "lon": 12.5674, "zoom": 7, "tip": "ulke", "label": "İtalya"},
    "ispanya": {"lat": 40.4637, "lon": -3.7492, "zoom": 7, "tip": "ulke", "label": "İspanya"},
    "yunanistan": {"lat": 39.0742, "lon": 21.8243, "zoom": 7, "tip": "ulke", "label": "Yunanistan"},
    "suriye": {"lat": 34.8021, "lon": 38.9968, "zoom": 7, "tip": "ulke", "label": "Suriye"},
    "irak": {"lat": 33.2232, "lon": 43.6793, "zoom": 7, "tip": "ulke", "label": "Irak"},
    "iran": {"lat": 32.4279, "lon": 53.6880, "zoom": 7, "tip": "ulke", "label": "İran"},
    "azerbaycan": {"lat": 40.1431, "lon": 47.5769, "zoom": 7, "tip": "ulke", "label": "Azerbaycan"},
    "gurcistan": {"lat": 42.3154, "lon": 43.3569, "zoom": 7, "tip": "ulke", "label": "Gürcistan"},
    "rusya": {"lat": 61.5240, "lon": 105.3188, "zoom": 4, "tip": "ulke", "label": "Rusya"},
    "amerika": {"lat": 37.0902, "lon": -95.7129, "zoom": 4, "tip": "ulke", "label": "ABD"},
    "abd": {"lat": 37.0902, "lon": -95.7129, "zoom": 4, "tip": "ulke", "label": "ABD"},
    "japonya": {"lat": 36.2048, "lon": 138.2529, "zoom": 7, "tip": "ulke", "label": "Japonya"},
    "cin": {"lat": 35.8617, "lon": 104.1954, "zoom": 4, "tip": "ulke", "label": "Çin"},
    "misir": {"lat": 26.8206, "lon": 30.8025, "zoom": 7, "tip": "ulke", "label": "Mısır"},
    "mekke": {"lat": 21.3891, "lon": 39.8579, "zoom": 13, "tip": "ilce", "label": "Mekke"},
    "medine": {"lat": 24.5247, "lon": 39.5692, "zoom": 13, "tip": "ilce", "label": "Medine"},
    "kudus": {"lat": 31.7683, "lon": 35.2137, "zoom": 15, "tip": "mahalle", "label": "Kudüs"},
}

# Son ek kırpımından bozulan gövdeler → doğru sorgu
_REPAIR: dict[str, str] = {
    "ayasof": "ayasofya",
    "koprus": "kopru",
    "bogazkoprus": "bogaz koprusu",
    "bogazicikoprus": "bogazici koprusu",
    "mescitgecid": "mescit gecidi",
    "uludag": "uludag",
    "gecid": "gecit",
    "everestdag": "everest dagi",
    "agridag": "agri dagi",
    "kackardaglar": "kackar daglari",
    "kackardag": "kackar dagi",
    "ziganagecid": "zigana gecidi",
    "kopgecid": "kop gecidi",
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


def infer_tip_from_text(hedef: str) -> str | None:
    """Metin ipuçlarından tip — doğal sınıflar önce (H10.5)."""
    if not hedef:
        return None
    from ilim_assistant.sahne_super_el import _norm

    n = _norm(hedef)
    compact = n.replace(" ", "")
    if re.search(r"\b(ulke|country|nation)\b", n) or compact in ("turkiye", "turkey", "anadolu"):
        return "ulke"
    # Doğal sınıf (nehir/göl/… dağdan önce) — isim listesi değil
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
        re.search(r"\b(dag|dagi|daglar|mountain|peak)\b", n)
        or compact.endswith("dag")
        or "uludag" in compact
        or "palandoken" in compact
    ):
        return "dag"
    if re.search(
        r"\b(cami|camii|kilise|katedral|saray|kule|muze|bina|ayasofya|ayasof)\b",
        n,
    ) or "ayasof" in compact:
        return "bina"
    if re.search(r"\b(mahalle|mah|semt|quarter|neighbourhood|neighborhood)\b", n):
        return "mahalle"
    if re.search(r"\b(ilce|ilcesi|district|county)\b", n):
        return "ilce"
    if re.search(r"\b(il|ili|sehir|city|province)\b", n):
        return "il"
    return None


def tip_from_osm(osm_class: str, osm_type: str, hedef: str) -> str:
    text_tip = infer_tip_from_text(hedef)
    if text_tip:
        return text_tip
    kind = (osm_type or "").lower()
    cls = (osm_class or "").lower()
    if kind in ("country", "nation") or cls == "boundary" and kind == "administrative":
        pass
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
    # Doğal / su sınıfları (H10.5)
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
    if kind in ("bridge",) or cls == "man_made" and kind == "bridge":
        return "kopru"
    if cls in ("building", "tourism", "historic", "amenity") or kind in (
        "attraction",
        "museum",
        "yes",
        "cathedral",
        "mosque",
        "church",
        "palace",
    ):
        return "bina"
    if cls == "place" and kind in ("city", "town"):
        return "il"
    # OSM tipi doğal sınıf ipucu olabilir
    try:
        from ilim_assistant.sahne_dunya_gezgini import classify_nature_tip

        nat = classify_nature_tip(hedef, kind, tip_hint=kind)
        if nat:
            return nat
    except Exception:
        pass
    return "nokta"


def bbox_from_center(lat: float, lon: float, zoom: int) -> list[float]:
    """OSM embed bbox: minLon,minLat,maxLon,maxLat."""
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


def _finalize(hit: dict[str, Any], *, query: str = "") -> dict[str, Any]:
    out = dict(hit)
    tip = out.get("tip") or infer_tip_from_text(query) or infer_tip_from_text(str(out.get("label") or ""))
    if not tip:
        tip = "nokta"
    out["tip"] = tip
    out["zoom"] = zoom_for_tip(tip, int(out.get("zoom") or TIP_ZOOM.get(tip, 11)))
    if not out.get("bbox"):
        out["bbox"] = bbox_from_center(float(out["lat"]), float(out["lon"]), int(out["zoom"]))
    return out


def _query_variants(hedef: str) -> list[str]:
    raw = (hedef or "").strip()
    if not raw:
        return []
    from ilim_assistant.sahne_super_el import _norm

    variants: list[str] = []

    def add(x: str | None) -> None:
        t = (x or "").strip()
        if t and t not in variants:
            variants.append(t)

    add(raw)
    add(_norm(raw))
    compact = _norm_key(raw)
    add(compact)
    # onarım
    if compact in _REPAIR:
        add(_REPAIR[compact])
    # boşluklu: mescitgecidi → mescit gecidi
    for a, b in (
        ("gecidi", " gecidi"),
        ("gecit", " gecit"),
        ("koprusu", " koprusu"),
        ("kopru", " kopru"),
        ("dagi", " dagi"),
        ("dag", " dag"),
    ):
        if compact.endswith(a) and len(compact) > len(a) + 2:
            add(compact[: -len(a)] + b)
    # agresif kırpım onarımı: ayasof → ayasofya
    if compact.endswith("sof") or compact == "ayasof":
        add("ayasofya")
    if "koprus" in compact and "kopru" not in variants:
        add(compact.replace("koprus", "koprusu"))
        add("bogaz koprusu")
    if compact.endswith("gecid"):
        add(compact + "i")
        add(compact[:-5] + " gecidi" if len(compact) > 5 else "mescit gecidi")
    return variants


def geocode_local(hedef: str) -> dict[str, Any] | None:
    if not hedef:
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
        for k, v in _YEREL.items():
            if key.startswith(k) or k.startswith(key):
                out = _finalize(v, query=hedef)
                out["source"] = "local"
                return out
    return None


def _nominatim_queries(hedef: str) -> list[str]:
    """Dağ/zirve/geçit için yanlış şehir eşleşmesini azalt."""
    from ilim_assistant.sahne_super_el import _norm

    raw = (hedef or "").strip()
    n = _norm(raw)
    compact = _norm_key(raw)
    out: list[str] = []

    def add(x: str) -> None:
        t = (x or "").strip()
        if t and t not in out:
            out.append(t)

    text_tip = infer_tip_from_text(raw)
    if "everest" in compact or "chomolungma" in compact:
        add("Mount Everest, Nepal")
        add("Everest")
        return out
    if text_tip in ("dag", "gecit") or re.search(r"\b(dag|dagi|daglar|peak|mountain|gecit)\b", n):
        add(f"{raw}")
        add(f"{raw}, Türkiye")
        if text_tip == "dag" or "dag" in n:
            add(f"{raw} peak")
            add(f"{raw} mountain")
        if text_tip == "gecit" or "gecit" in n:
            add(f"{raw} pass")
        for v in _query_variants(hedef):
            add(v)
        return out
    for v in _query_variants(hedef):
        add(v)
        if not re.search(r"turkey|turkiye|nepal|china|tibet", v, re.I):
            add(f"{v}, Türkiye")
    return out


def geocode_nominatim(hedef: str, timeout: float = 4.0) -> dict[str, Any] | None:
    for q_try in _nominatim_queries(hedef):
        if len(q_try) < 2:
            continue
        params = urllib.parse.urlencode(
            {
                "q": q_try,
                "format": "json",
                "limit": "1",
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
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            if not data:
                continue
            row = data[0]
            lat = float(row["lat"])
            lon = float(row["lon"])
            tip = tip_from_osm(str(row.get("class") or ""), str(row.get("type") or ""), hedef or q_try)
            # Metin dağ/geçit diyorsa OSM şehir tipini ez
            text_tip = infer_tip_from_text(hedef)
            if text_tip in (
                "dag",
                "gecit",
                "kopru",
                "bina",
                "nehir",
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
                tip = text_tip
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
        except Exception:
            continue
    return None


def log_hedef(geo: dict[str, Any] | None, query: str = "") -> dict[str, Any] | None:
    """Hedef adı / tip / koordinat — tek merkez log."""
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
    local = geocode_local(hedef)
    if local:
        return log_hedef(local, hedef)
    if allow_network:
        return log_hedef(geocode_nominatim(hedef), hedef)
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(min(1.0, sqrt(a)))


def reverse_local(lat: float, lon: float, max_km: float = 80.0) -> dict[str, Any] | None:
    """En yakın yerel nokta (hızlı merkez adı)."""
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
        if short and city and short.lower() != str(city).lower():
            display_short = f"{short}"
        else:
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
        }
    except Exception:
        return None


def reverse_geocode(lat: float, lon: float, *, allow_network: bool = True) -> dict[str, Any]:
    """Harita merkezi → yer adı (yerel hızlı + Nominatim ince)."""
    local = reverse_local(lat, lon)
    if allow_network:
        nom = reverse_nominatim(lat, lon)
        if nom:
            # Yerel il adı yedek; nominatim mahalle/ilçe öncelikli
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
    }
