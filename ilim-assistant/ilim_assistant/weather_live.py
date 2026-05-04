"""Canlı hava: ücretsiz Open-Meteo; isteğe bağlı OpenWeatherMap anahtarı."""

from __future__ import annotations

import os
from typing import Any

import requests

_SESSION = requests.Session()
_TIMEOUT = float(os.environ.get("WEATHER_HTTP_TIMEOUT", "12"))

# WMO kodları → kısa Türkçe (Open-Meteo current.weather_code)
_WMO_TR: dict[int, str] = {
    0: "açık",
    1: "çoğunlukla açık",
    2: "parçalı bulutlu",
    3: "bulutlu",
    45: "sisli",
    48: "sisli",
    51: "çiseleyen yağmur",
    53: "hafif yağmur",
    55: "yağmurlu",
    61: "hafif yağmur",
    63: "yağmurlu",
    65: "şiddetli yağmur",
    71: "hafif kar",
    73: "kar",
    75: "yoğun kar",
    77: "kar taneleri",
    80: "sağanak",
    81: "sağanak",
    82: "şiddetli sağanak",
    85: "karla karışık yağmur",
    86: "karla karışık yağmur",
    95: "gök gürültülü sağanak",
    96: "dolu fırtınası",
    99: "şiddetli dolu",
}


def _openweather_block(city: str) -> str:
    key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not key:
        return ""
    q = city.strip()
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={requests.utils.quote(q)}&appid={key}&lang=tr&units=metric"
    )
    try:
        r = _SESSION.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return ""
    try:
        temp = data["main"]["temp"]
        desc = (data["weather"][0].get("description") or "").strip()
        name = data.get("name") or q
        return (
            f"=== Güncel hava (OpenWeatherMap) — {name} ===\n"
            f"{desc or 'Durum'}, sıcaklık: {temp:.0f}°C\n"
        )
    except (KeyError, TypeError, IndexError):
        return ""


def _geocode_city(name: str) -> tuple[float, float] | None:
    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={requests.utils.quote(name)}&count=1&language=tr&format=json"
    )
    try:
        r = _SESSION.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        j: dict[str, Any] = r.json()
        res = j.get("results") or []
        if not res:
            return None
        lat = float(res[0]["latitude"])
        lon = float(res[0]["longitude"])
        return lat, lon
    except Exception:
        return None


def _open_meteo_block(city: str) -> str:
    geo = _geocode_city(city)
    if not geo:
        return ""
    lat, lon = geo
    tz = os.environ.get("OPEN_METEO_TIMEZONE", "Europe/Istanbul")
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,relative_humidity_2m"
        f"&timezone={requests.utils.quote(tz)}"
    )
    try:
        r = _SESSION.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        j = r.json()
        cur = j.get("current") or {}
        temp = cur.get("temperature_2m")
        code = int(cur.get("weather_code") or 0)
        hum = cur.get("relative_humidity_2m")
    except Exception:
        return ""
    if temp is None:
        return ""
    desc = _WMO_TR.get(code, "hava durumu")
    lines = [
        f"=== Güncel hava (Open-Meteo) — {city.strip()} ===",
        f"Özet: {desc}, sıcaklık: {float(temp):.0f}°C",
    ]
    if hum is not None:
        lines.append(f"Nem: %{int(hum)}")
    return "\n".join(lines) + "\n"


def fetch_live_weather_context(city: str | None = None) -> str:
    """
    API anahtarı yoksa Open-Meteo kullanır (ücretsiz).
    OPENWEATHER_API_KEY varsa önce OpenWeatherMap denenir.
    """
    city = (city or os.environ.get("OPENWEATHER_DEFAULT_CITY", "Istanbul")).strip()
    if not city:
        return ""
    ow = _openweather_block(city)
    if ow:
        return ow
    return _open_meteo_block(city)
