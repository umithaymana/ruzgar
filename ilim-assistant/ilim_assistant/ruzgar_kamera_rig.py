# -*- coding: utf-8 -*-
"""
Rüzgar CameraRig — evrensel kamera çekirdeği (Anayasa: hardcode yer yok).

Dünya + Uzay aynı preset sözlüğü; domain ayrımı ile.
"""
from __future__ import annotations

import re
from typing import Any

# --- Dünya modları (C0–C5 ile uyumlu isimler) ---
EARTH_PRESETS: dict[str, dict[str, Any]] = {
    "yuruyus": {
        "id": "yuruyus",
        "label": "Yürüyüş",
        "domain": "earth",
        "kind": "ground",
        "eye_m": 1.7,
        "speed_mps": 1.4,
        "turn_dps": 40.0,
        "pitch_deg": -8.0,
        "collision": True,
        "pano_auto": True,
        "tour_auto": False,
    },
    "bisiklet": {
        "id": "bisiklet",
        "label": "Bisiklet",
        "domain": "earth",
        "kind": "ground",
        "eye_m": 1.55,
        "speed_mps": 6.5,
        "turn_dps": 55.0,
        "pitch_deg": -6.0,
        "collision": True,
        "pano_auto": False,
        "tour_auto": False,
    },
    "arac": {
        "id": "arac",
        "label": "Araç",
        "domain": "earth",
        "kind": "ground",
        "eye_m": 1.35,
        "speed_mps": 14.0,
        "turn_dps": 32.0,
        "pitch_deg": -4.0,
        "collision": True,
        "pano_auto": False,
        "tour_auto": False,
    },
    "drone": {
        "id": "drone",
        "label": "Drone",
        "domain": "earth",
        "kind": "air",
        "eye_m": 48.0,
        "speed_mps": 12.0,
        "turn_dps": 50.0,
        "pitch_deg": -28.0,
        "collision": False,
        "pano_auto": False,
        "tour_auto": False,
    },
    "serbest": {
        "id": "serbest",
        "label": "Serbest Pilot",
        "domain": "earth",
        "kind": "free",
        "eye_m": 12.0,
        "speed_mps": 22.0,
        "turn_dps": 70.0,
        "pitch_deg": -12.0,
        "collision": False,
        "pano_auto": False,
        "tour_auto": False,
    },
    "sinematik": {
        "id": "sinematik",
        "label": "Sinematik Tur",
        "domain": "earth",
        "kind": "cinema",
        "eye_m": None,
        "speed_mps": None,
        "turn_dps": 18.0,
        "pitch_deg": None,
        "collision": False,
        "pano_auto": False,
        "tour_auto": True,
    },
}

# --- Uzay modları (uygulama: domain + preset; tiles ayrı) ---
SPACE_PRESETS: dict[str, dict[str, Any]] = {
    "yorunge": {
        "id": "yorunge",
        "label": "Yörünge",
        "domain": "space",
        "kind": "orbit",
        "eye_m": 2.5e6,
        "speed_mps": 800.0,
        "turn_dps": 12.0,
        "pitch_deg": -35.0,
        "collision": False,
        "body": "earth",
    },
    "rover": {
        "id": "rover",
        "label": "Rover",
        "domain": "space",
        "kind": "ground",
        "eye_m": 1.8,
        "speed_mps": 0.55,
        "turn_dps": 25.0,
        "pitch_deg": -10.0,
        "collision": True,
        "body": "mars",
    },
    "inis": {
        "id": "inis",
        "label": "İniş",
        "domain": "space",
        "kind": "cinema",
        "eye_m": 80000.0,
        "speed_mps": None,
        "turn_dps": 8.0,
        "pitch_deg": -55.0,
        "collision": False,
        "body": "mars",
    },
    "kokpit": {
        "id": "kokpit",
        "label": "Kokpit",
        "domain": "space",
        "kind": "cockpit",
        "eye_m": 2.0,
        "speed_mps": 0.0,
        "turn_dps": 40.0,
        "pitch_deg": 0.0,
        "collision": False,
        "body": "craft",
    },
    "uydu": {
        "id": "uydu",
        "label": "Uydu",
        "domain": "space",
        "kind": "orbit",
        "eye_m": 8.0e5,
        "speed_mps": 0.0,
        "turn_dps": 6.0,
        "pitch_deg": -90.0,
        "collision": False,
        "body": "earth",
    },
    "serbest_uzay": {
        "id": "serbest_uzay",
        "label": "Serbest Uzay",
        "domain": "space",
        "kind": "free",
        "eye_m": 5.0e5,
        "speed_mps": 2000.0,
        "turn_dps": 45.0,
        "pitch_deg": 0.0,
        "collision": False,
        "body": "space",
    },
}

# Yumuşak geçiş sırası (Faz 5)
EARTH_BLEND_EDGES: tuple[tuple[str, str], ...] = (
    ("yuruyus", "bisiklet"),
    ("bisiklet", "arac"),
    ("arac", "drone"),
    ("drone", "sinematik"),
    ("drone", "serbest"),
    ("yuruyus", "drone"),
    ("serbest", "sinematik"),
)

SPACE_BLEND_EDGES: tuple[tuple[str, str], ...] = (
    ("yorunge", "uydu"),
    ("uydu", "inis"),
    ("inis", "rover"),
    ("rover", "kokpit"),
    ("yorunge", "serbest_uzay"),
    ("kokpit", "serbest_uzay"),
)

# Domain geçişleri (cisim) — tiles/hesap ayrı
BODY_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("earth", "moon"),
    ("moon", "mars"),
    ("mars", "space"),
    ("earth", "mars"),
    ("earth", "space"),
)

BLEND_MS_DEFAULT = 750

_MODE_ALIASES: dict[str, str] = {
    "yuruyus": "yuruyus",
    "yuru": "yuruyus",
    "walk": "yuruyus",
    "bisiklet": "bisiklet",
    "bike": "bisiklet",
    "bicycle": "bisiklet",
    "arac": "arac",
    "araba": "arac",
    "car": "arac",
    "vehicle": "arac",
    "drone": "drone",
    "iha": "drone",
    "serbest": "serbest",
    "serbest_pilot": "serbest",
    "free": "serbest",
    "pilot": "serbest",
    "sinematik": "sinematik",
    "sinema": "sinematik",
    "cinema": "sinematik",
    "cinematic": "sinematik",
    "yorunge": "yorunge",
    "orbit": "yorunge",
    "rover": "rover",
    "inis": "inis",
    "landing": "inis",
    "kokpit": "kokpit",
    "cockpit": "kokpit",
    "uydu_mod": "uydu",
    "satellite_cam": "uydu",
    "serbest_uzay": "serbest_uzay",
    "free_space": "serbest_uzay",
}


def all_presets() -> dict[str, dict[str, Any]]:
    out = dict(EARTH_PRESETS)
    out.update(SPACE_PRESETS)
    return out


def get_preset(mode_id: str) -> dict[str, Any] | None:
    mid = _MODE_ALIASES.get((mode_id or "").strip().lower(), (mode_id or "").strip().lower())
    return all_presets().get(mid)


def normalize_mode_id(raw: str) -> str | None:
    t = (raw or "").strip().lower()
    if not t:
        return None
    if t in all_presets():
        return t
    return _MODE_ALIASES.get(t)


def looks_like_camera_mode(n: str) -> str | None:
    """
    Sesli/metin → tour_camera_<mode> aksiyonu.
    Yer adı yok; yalnız mod.
    """
    if not n:
        return None
    # Dünya
    if re.search(
        r"\b(yuruyus\s*mod(una|u)?(\s*gec)?|yuru(yus)?\s*mod|"
        r"walk(\s*mode)?|goz\s*hiza\w*\s*mod)\b",
        n,
    ):
        return "tour_camera_yuruyus"
    if re.search(r"\b(bisiklet\s*mod(una|u)?(\s*gec)?|bike(\s*mode)?)\b", n):
        return "tour_camera_bisiklet"
    if re.search(
        r"\b(arac\s*mod(una|u)?(\s*gec)?|araba\s*mod|surus\s*mod|"
        r"car(\s*mode)?|driving\s*mode)\b",
        n,
    ):
        return "tour_camera_arac"
    if re.search(r"\b(drone\s*mod(una|u)?(\s*gec)?|iha\s*mod|drone\s*ol)\b", n):
        return "tour_camera_drone"
    if re.search(
        r"\b(serbest\s*pilot(\s*ol)?|serbest\s*mod(una|u)?(\s*gec)?|"
        r"free\s*pilot|free\s*cam)\b",
        n,
    ):
        return "tour_camera_serbest"
    if re.search(
        r"\b(sinematik\s*mod(una|u)?(\s*gec)?|sinema\s*mod|"
        r"cinematic(\s*mode)?|belgesel\s*mod)\b",
        n,
    ):
        return "tour_camera_sinematik"
    # Uzay
    if re.search(r"\b(yorunge\s*mod(una|u)?|orbit(\s*mode)?)\b", n):
        return "tour_camera_yorunge"
    if re.search(r"\b(rover\s*mod(una|u)?|mars\s*rover)\b", n):
        return "tour_camera_rover"
    if re.search(r"\b(inis\s*mod(una|u)?|landing(\s*mode)?)\b", n):
        return "tour_camera_inis"
    if re.search(r"\b(kokpit\s*mod(una|u)?|cockpit(\s*mode)?)\b", n):
        return "tour_camera_kokpit"
    if re.search(r"\b(uydu\s*kamera|uydu\s*mod(una|u)?\s*kamera|satellite\s*cam)\b", n):
        return "tour_camera_uydu"
    if re.search(r"\b(serbest\s*uzay|free\s*space(\s*mode)?)\b", n):
        return "tour_camera_serbest_uzay"
    # Cisim geçişi (Faz 5) — tiles yoksa istemci dürüst mesaj
    if re.search(r"\b(dunya(ya)?\s*(don|gec)|earth(\s*mode)?)\b", n) and re.search(
        r"\b(ay|mars|uzay|moon)\b", n
    ):
        return "tour_body_earth"
    if re.search(r"\b((dunya|earth)\s*(dan\s*)?(aya|ay[aı])|ay[aı]\s*gec|moon)\b", n):
        return "tour_body_moon"
    if re.search(r"\b((ay|moon)\s*(dan\s*)?mars[aı]?|mars[aı]?\s*gec)\b", n):
        return "tour_body_mars"
    if re.search(
        r"\b(mars[aı]?(tan|dan)?\s*uzay[aı]?|uzay[aı]?\s*(mod(una|u)?\s*)?gec|"
        r"deep\s*space|serbest\s*uzay\s*gec)\b",
        n,
    ):
        return "tour_body_space"
    return None


def camera_mode_from_action(action: str) -> str | None:
    a = (action or "").strip().lower()
    if a.startswith("tour_camera_"):
        return normalize_mode_id(a.replace("tour_camera_", "", 1))
    return None


def catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "kamera-rig-v1",
        "blend_ms": BLEND_MS_DEFAULT,
        "earth": EARTH_PRESETS,
        "space": SPACE_PRESETS,
        "earth_blend_edges": [list(x) for x in EARTH_BLEND_EDGES],
        "space_blend_edges": [list(x) for x in SPACE_BLEND_EDGES],
        "body_transitions": [list(x) for x in BODY_TRANSITIONS],
        "anayasa": "evrensel — sabit şehir/dağ/nehir yok",
    }


# --- Canlı kamera kaynak envanteri (scrape yok) ---
CANLI_KAYNAK_ENVANTER: list[dict[str, Any]] = [
    {
        "id": "fintraffic",
        "kurum": "Fintraffic Digitraffic (Finlandiya)",
        "tur": "trafik/hava",
        "baglanti": "https://tie.digitraffic.fi/api/weathercam/v1/stations",
        "api": True,
        "hesap": False,
        "ucret": "ücretsiz (CC BY 4.0)",
        "uygula": "BAĞLI — RUZGAR_WEBCAM_FINTRAFFIC=1 (varsayılan)",
        "lisans_not": "CC BY 4.0 + Digitraffic-User önerilir",
    },
    {
        "id": "nsw_livetraffic",
        "kurum": "Transport for NSW (Avustralya)",
        "tur": "trafik",
        "baglanti": "https://opendata.transport.nsw.gov.au/ (Live Traffic Cameras)",
        "api": True,
        "hesap": True,
        "ucret": "ücretsiz kota (API key)",
        "uygula": "HESAP BEKLIYOR — key sonrası OPEN_JSON_URLS",
        "lisans_not": "CC-BY attribution zorunlu",
    },
    {
        "id": "windy_webcams",
        "kurum": "Windy Webcams API",
        "tur": "turizm/dağ/hava/kayak",
        "baglanti": "https://api.windy.com/webcams/",
        "api": True,
        "hesap": True,
        "ucret": "ücretsiz kotası / ticari kısıt",
        "uygula": "HESAP BEKLIYOR — redistrib TOS kısıtlı",
        "lisans_not": "yeniden yayınlama kısıtlı",
    },
    {
        "id": "nyc_dot",
        "kurum": "NYC DOT Traffic Cameras",
        "tur": "trafik",
        "baglanti": "https://webcams.nyctmc.org/",
        "api": True,
        "hesap": True,
        "ucret": "sözleşme / abone",
        "uygula": "HESAP+SÖZLEŞME BEKLIYOR",
        "lisans_not": "subscriber agreement",
    },
    {
        "id": "belediye",
        "kurum": "Belediye kameraları (dünya geneli)",
        "tur": "belediye",
        "baglanti": "kurum open-data / CCTV portal",
        "api": "nadiren açık",
        "hesap": "çoğu evet",
        "ucret": "görüntüleme ücretsiz; API nadir/ücretli",
        "uygula": "scrape YOK — açık JSON gelince OPEN_JSON_URLS",
        "lisans_not": "çoğu embed yasak",
    },
    {
        "id": "turizm",
        "kurum": "Turizm / şehir tanıtım kameraları",
        "tur": "turizm",
        "baglanti": "Windy / EarthCam / yerel turizm ofisi",
        "api": "kaynağa bağlı",
        "hesap": True,
        "ucret": "çoğu ücretsiz görüntüleme",
        "uygula": "HESAP / TOS — scrape yok",
        "lisans_not": "yeniden yayın kısıtlı",
    },
    {
        "id": "deniz_liman",
        "kurum": "Deniz / liman kameraları",
        "tur": "deniz/liman",
        "baglanti": "liman otoritesi / AIS+cam portalları",
        "api": "nadiren açık",
        "hesap": "çoğu evet",
        "ucret": "kaynağa bağlı",
        "uygula": "açık API yoksa bağlanmaz",
        "lisans_not": "güvenlik/operasyon kısıtı sık",
    },
    {
        "id": "dag_kayak",
        "kurum": "Dağ / kayak merkezi kameraları",
        "tur": "dağ/kayak",
        "baglanti": "tesis webcam / Windy",
        "api": "çoğu yok (embed)",
        "hesap": "kaynağa bağlı",
        "ucret": "görüntüleme ücretsiz",
        "uygula": "scrape YOK — Windy hesabı veya tesis açık feed",
        "lisans_not": "embed şartlarına bağlı",
    },
    {
        "id": "hava",
        "kurum": "Hava durumu kameraları",
        "tur": "hava",
        "baglanti": "Fintraffic / NOAA / meteoroloji open-data",
        "api": True,
        "hesap": "kaynağa bağlı",
        "ucret": "Fintraffic ücretsiz; diğerleri değişken",
        "uygula": "Fintraffic BAĞLI; NOAA sonraki",
        "lisans_not": "attribution",
    },
    {
        "id": "generic_open_json",
        "kurum": "Yerel / kurumsal açık JSON",
        "tur": "hepsi",
        "baglanti": "RUZGAR_WEBCAM_OPEN_JSON_URLS",
        "api": True,
        "hesap": False,
        "ucret": "kaynağa bağlı",
        "uygula": "şimdi: lat/lon/hls|image + license",
        "lisans_not": "yalnız açık lisanslı URL",
    },
]

UZAY_KAYNAK_ENVANTER: list[dict[str, Any]] = [
    {
        "id": "nasa_gibs",
        "ad": "NASA GIBS",
        "api": False,
        "hesap": False,
        "ucret": "ücretsiz",
        "kullanim": "Dünya 4D / uydu kamera",
        "durum": "BAĞLI (mode_4d)",
    },
    {
        "id": "nasa_trek",
        "ad": "NASA Solar System Treks WMTS",
        "api": False,
        "hesap": False,
        "ucret": "ücretsiz",
        "kullanim": "Ay/Mars yörünge+rover görüntü",
        "durum": "HAZIR — WMTS katmanı eklenebilir",
    },
    {
        "id": "nasa_open",
        "ad": "NASA Open Data",
        "api": True,
        "hesap": "opsiyonel API key",
        "ucret": "ücretsiz",
        "kullanim": "meta / görüntü arşivi",
        "durum": "HESAP OPSİYONEL",
    },
    {
        "id": "cesium_moon",
        "ad": "Cesium Ion Moon",
        "api": True,
        "hesap": True,
        "ucret": "Ion hesabı (kotaya bağlı)",
        "kullanim": "yorunge/rover/inis (Ay)",
        "durum": "HESAP BEKLIYOR — RUZGAR_CESIUM_ION_TOKEN + Moon asset",
    },
    {
        "id": "cesium_mars",
        "ad": "Cesium Ion Mars",
        "api": True,
        "hesap": True,
        "ucret": "Ion hesabı",
        "kullanim": "yorunge/rover/inis (Mars)",
        "durum": "HESAP BEKLIYOR",
    },
    {
        "id": "esa",
        "ad": "ESA (HRSC vb.)",
        "api": "karışık",
        "hesap": "kaynağa bağlı",
        "ucret": "çoğu ücretsiz arşiv",
        "kullanim": "Mars detay",
        "durum": "sonraki — Trek/Ion üstü",
    },
    {
        "id": "jaxa",
        "ad": "JAXA",
        "api": "karışık",
        "hesap": "kaynağa bağlı",
        "ucret": "çoğu ücretsiz",
        "kullanim": "Ay / Dünya",
        "durum": "liste — bağ yok",
    },
    {
        "id": "isro",
        "ad": "ISRO",
        "api": "karışık",
        "hesap": "kaynağa bağlı",
        "ucret": "çoğu ücretsiz",
        "kullanim": "Ay / Dünya",
        "durum": "liste — bağ yok",
    },
    {
        "id": "noaa",
        "ad": "NOAA",
        "api": True,
        "hesap": "opsiyonel",
        "ucret": "ücretsiz",
        "kullanim": "Dünya hava / uydu",
        "durum": "sonraki katman",
    },
]
