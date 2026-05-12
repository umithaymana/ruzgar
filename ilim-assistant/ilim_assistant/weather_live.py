"""Canlı hava: ücretsiz Open-Meteo; isteğe bağlı OpenWeatherMap anahtarı."""

from __future__ import annotations

import os
import unicodedata
from typing import Any

import requests

from ilim_assistant.persona import OWNER_ADDRESS

_SESSION = requests.Session()
_TIMEOUT = float(os.environ.get("WEATHER_HTTP_TIMEOUT", "6"))

# Büyükşehir ve sık geçen adlar — alt dize eşleşmesi (ör. "istanbulda"); uzun iğne önce.
_CITY_NEEDLES: list[tuple[str, str]] = [
    ("kahramanmaras", "Kahramanmaras"),
    ("maraş", "Kahramanmaras"),
    ("maras", "Kahramanmaras"),
    ("sanliurfa", "Sanliurfa"),
    ("şanlıurfa", "Sanliurfa"),
    ("urfa", "Sanliurfa"),
    ("gaziantep", "Gaziantep"),
    ("antalya", "Antalya"),
    ("kocaeli", "Kocaeli"),
    ("izmir", "Izmir"),
    ("istanbul", "Istanbul"),
    ("ankara", "Ankara"),
    ("bursa", "Bursa"),
    ("adana", "Adana"),
    ("konya", "Konya"),
    ("mersin", "Mersin"),
    ("diyarbakir", "Diyarbakir"),
    ("diyarbakır", "Diyarbakir"),
    ("kayseri", "Kayseri"),
    ("eskisehir", "Eskisehir"),
    ("eskişehir", "Eskisehir"),
    ("trabzon", "Trabzon"),
    ("malatya", "Malatya"),
    ("erzurum", "Erzurum"),
    ("samsun", "Samsun"),
    ("denizli", "Denizli"),
    ("bodrum", "Bodrum"),
    ("edirne", "Edirne"),
    ("çanakkale", "Canakkale"),
    ("canakkale", "Canakkale"),
]
_CITY_NEEDLES.sort(key=lambda x: len(x[0]), reverse=True)

_CITY_DISPLAY_TR: dict[str, str] = {
    "Istanbul": "İstanbul",
    "Izmir": "İzmir",
    "Gaziantep": "Gaziantep",
    "Kahramanmaras": "Kahramanmaraş",
    "Sanliurfa": "Şanlıurfa",
    "Eskisehir": "Eskişehir",
    "Diyarbakir": "Diyarbakır",
    "Canakkale": "Çanakkale",
}

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


def _norm_match(text: str) -> str:
    """Türkçe İ/ı vb. için karşılaştırma tamponu (alt dize araması)."""
    d = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in d if unicodedata.category(c) != "Mn")
    for a, b in (
        ("ğ", "g"),
        ("ü", "u"),
        ("ş", "s"),
        ("ı", "i"),
        ("ö", "o"),
        ("ç", "c"),
        ("Ğ", "g"),
        ("Ü", "u"),
        ("Ş", "s"),
        ("İ", "i"),
        ("Ö", "o"),
        ("Ç", "c"),
    ):
        s = s.replace(a, b)
    return s.lower()


def _extract_city_from_message(message: str) -> str | None:
    nm = _norm_match(message)
    for needle, geo in _CITY_NEEDLES:
        if needle in nm:
            return geo
    return None


def _wants_tomorrow(message: str) -> bool:
    nm = _norm_match(message)
    return "yarin" in nm


def _wants_today_focus(message: str) -> bool:
    nm = _norm_match(message)
    return any(
        k in nm
        for k in (
            "bugun",
            "bu gun",
            "simdi",
            "şimdi",
            "bu aksam",
            "bu akşam",
            "bu gece",
        )
    )


def _open_meteo_forecast_json(lat: float, lon: float) -> dict[str, Any] | None:
    tz = os.environ.get("OPEN_METEO_TIMEZONE", "Europe/Istanbul")
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,relative_humidity_2m"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone={requests.utils.quote(tz)}"
        "&forecast_days=4"
    )
    try:
        r = _SESSION.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        j = r.json()
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _daily_line(
    j: dict[str, Any],
    idx: int,
    label: str,
) -> str | None:
    daily = j.get("daily") or {}
    times = daily.get("time") or []
    codes = daily.get("weather_code") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    probs = daily.get("precipitation_probability_max") or []
    if idx >= len(times) or idx >= len(codes):
        return None
    date = str(times[idx])
    try:
        code = int(codes[idx])
    except (TypeError, ValueError):
        code = 0
    desc = _WMO_TR.get(code, "hava durumu")
    parts = [f"{label} ({date}): {desc}"]
    try:
        if idx < len(tmax) and idx < len(tmin) and tmax[idx] is not None and tmin[idx] is not None:
            parts.append(f"gündüz en yüksek ~{float(tmax[idx]):.0f}°C, gece en düşük ~{float(tmin[idx]):.0f}°C")
    except (TypeError, ValueError, IndexError):
        pass
    try:
        if idx < len(probs) and probs[idx] is not None:
            parts.append(f"yağış olasılığı (tahmini en yüksek): %{int(probs[idx])}")
    except (TypeError, ValueError, IndexError):
        pass
    return "; ".join(parts)


def _format_open_meteo_bundle(
    j: dict[str, Any],
    city_label: str,
    *,
    emit_current: bool,
    tomorrow_detail: bool,
    today_daily: bool,
    tomorrow_one_liner: bool,
) -> str:
    lines: list[str] = [f"=== Güncel hava (Open-Meteo) — {city_label} ==="]

    if emit_current:
        cur = j.get("current") or {}
        temp = cur.get("temperature_2m")
        if temp is not None:
            try:
                code = int(cur.get("weather_code") or 0)
            except (TypeError, ValueError):
                code = 0
            desc = _WMO_TR.get(code, "hava durumu")
            lines.append(f"Şu an (tahmin): {desc}, sıcaklık ~{float(temp):.0f}°C")
            hum = cur.get("relative_humidity_2m")
            if hum is not None:
                lines.append(f"Nem: %{int(hum)}")

    if today_daily:
        dl = _daily_line(j, 0, "Bugün gün içi özeti")
        if dl:
            lines.append(dl)

    if tomorrow_detail:
        dl = _daily_line(j, 1, "Yarın")
        if dl:
            lines.append(dl)
    elif tomorrow_one_liner:
        dl = _daily_line(j, 1, "Yarın kabaca")
        if dl:
            lines.append(dl)

    if len(lines) <= 1:
        return ""
    return "\n".join(lines) + "\n"


def _open_meteo_block(city: str) -> str:
    """Geriye dönük uyumluluk: yalnızca şu an + yarın tek satır (tek istek)."""
    geo = _geocode_city(city)
    if not geo:
        return ""
    j = _open_meteo_forecast_json(*geo)
    if not j:
        return ""
    return _format_open_meteo_bundle(
        j,
        city.strip(),
        emit_current=True,
        tomorrow_detail=False,
        today_daily=False,
        tomorrow_one_liner=True,
    )


def fetch_live_weather_context(city: str | None = None) -> str:
    """
    API anahtarı yoksa Open-Meteo kullanır (ücretsiz).
    OPENWEATHER_API_KEY varsa önce OpenWeatherMap denenir.
    """
    city = (city or os.environ.get("OPENWEATHER_DEFAULT_CITY", "Istanbul")).strip()
    if not city:
        return ""
    ow = _openweather_block(city)
    geo = _geocode_city(city)
    if not geo:
        return ow
    j = _open_meteo_forecast_json(*geo)
    if not j:
        return ow
    om = _format_open_meteo_bundle(
        j,
        city,
        emit_current=not bool(ow),
        tomorrow_detail=False,
        today_daily=False,
        tomorrow_one_liner=True,
    )
    if ow and om:
        return ow.rstrip() + "\n\n" + om
    return om or ow


def _display_city_tr(geo_name: str) -> str:
    g = (geo_name or "").strip()
    return _CITY_DISPLAY_TR.get(g, g)


def _ow_user_line(ow_block: str) -> str:
    for ln in (ow_block or "").splitlines():
        t = ln.strip()
        if t and not t.startswith("==="):
            return t.rstrip(".")
    return ""


def _precip_prob(j: dict[str, Any], idx: int) -> int | None:
    daily = j.get("daily") or {}
    probs = daily.get("precipitation_probability_max") or []
    if idx >= len(probs) or probs[idx] is None:
        return None
    try:
        return int(probs[idx])
    except (TypeError, ValueError):
        return None


def _umbrella_hint(prob: int | None) -> str:
    if prob is None:
        return ""
    if prob >= 60:
        return " Yanına şemsiye alman iyi olur."
    if prob >= 35:
        return " Kısa süreli yağmur ihtimali var; ince bir kat veya şemsiye düşünebilirsin."
    return ""


def _human_daily_sentence(j: dict[str, Any], idx: int, lead: str) -> str:
    """Anlık kullanıcı yanıtı için kısa, doğal Türkçe (LLM bağlam bloğundan ayrı)."""
    daily = j.get("daily") or {}
    times = daily.get("time") or []
    codes = daily.get("weather_code") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    if idx >= len(times) or idx >= len(codes):
        return ""
    date = str(times[idx])
    try:
        code = int(codes[idx])
    except (TypeError, ValueError):
        code = 0
    desc = _WMO_TR.get(code, "hava durumu")
    bits = [f"{lead} ({date}) genel olarak {desc} görünüyor."]
    try:
        if idx < len(tmax) and idx < len(tmin) and tmax[idx] is not None and tmin[idx] is not None:
            hi = float(tmax[idx])
            lo = float(tmin[idx])
            bits.append(f"Gündüz en sıcak ~{hi:.0f}, gece en serin ~{lo:.0f} derece.")
    except (TypeError, ValueError, IndexError):
        pass
    prob = _precip_prob(j, idx)
    if prob is not None:
        bits.append(f"Yağmur ihtimali kabaca yüzde {prob}.")
    return " ".join(bits).strip()


def _compose_instant_weather_reply(
    city_geo: str,
    ow_block: str,
    j: dict[str, Any] | None,
    *,
    want_tomorrow: bool,
    want_today: bool,
    tomorrow_one_liner: bool,
) -> str | None:
    """
    LLM kullanmadan kısa Türkçe yanıt (masaüstü anında cevap / tutarlı üslup).
    """
    cd = _display_city_tr(city_geo)
    addr = OWNER_ADDRESS
    parts: list[str] = []

    if ow_block:
        fact = _ow_user_line(ow_block)
        if fact:
            parts.append(f"{addr}, {cd} için şu an: {fact}.")
    if not parts and j:
        cur = j.get("current") or {}
        temp = cur.get("temperature_2m")
        if temp is not None:
            try:
                code = int(cur.get("weather_code") or 0)
            except (TypeError, ValueError):
                code = 0
            desc = _WMO_TR.get(code, "hava durumu")
            t = float(temp)
            bit = f"{addr}, {cd} için şu an hava {desc}; sıcaklık yaklaşık {t:.0f} derece."
            hum = cur.get("relative_humidity_2m")
            if hum is not None:
                bit += f" Nem yüzde {int(hum)} civarında."
            parts.append(bit)

    if not parts:
        return None

    if j and want_today:
        dl = _daily_line(j, 0, "Bugün")
        if dl:
            tail = dl.split(":", 1)[-1].strip() if ":" in dl else dl
            parts.append(f"Bugün gün boyu kabaca şöyle: {tail}.")

    if j and want_tomorrow:
        sent = _human_daily_sentence(j, 1, "Yarın")
        if sent:
            prob = _precip_prob(j, 1)
            parts.append(f"{sent}{_umbrella_hint(prob)}")
    elif j and tomorrow_one_liner:
        sent = _human_daily_sentence(j, 1, "Yarın")
        if sent:
            prob = _precip_prob(j, 1)
            parts.append(f"{sent}{_umbrella_hint(prob)}")

    return " ".join(parts).strip()


def compute_live_weather_outcome(message: str) -> tuple[str, str | None]:
    """
    (LLM bağlam bloğu, anında Türkçe yanıt veya None).
    Tek tahmin isteği; OPENWEATHER_API_KEY varsa anlık satır OW'dan gelir.
    """
    msg = (message or "").strip()
    if not msg:
        return "", None
    default = (os.environ.get("OPENWEATHER_DEFAULT_CITY") or "Istanbul").strip() or "Istanbul"
    city = _extract_city_from_message(msg) or default
    want_tom = _wants_tomorrow(msg)
    want_td = _wants_today_focus(msg)
    tomorrow_one = not want_tom and not want_td

    ow = _openweather_block(city)
    geo = _geocode_city(city)
    j: dict[str, Any] | None = None
    if geo:
        j = _open_meteo_forecast_json(*geo)

    instant: str | None = None
    if os.environ.get("RUZGAR_WEATHER_INSTANT_REPLY", "1").strip() not in ("0", "false", "no"):
        if j is not None:
            instant = _compose_instant_weather_reply(
                city,
                ow,
                j,
                want_tomorrow=want_tom,
                want_today=want_td,
                tomorrow_one_liner=tomorrow_one,
            )
        elif ow:
            instant = _compose_instant_weather_reply(
                city,
                ow,
                None,
                want_tomorrow=False,
                want_today=False,
                tomorrow_one_liner=False,
            )

    if not geo:
        return (ow, instant)

    if not j:
        return (ow, instant)

    om = _format_open_meteo_bundle(
        j,
        city,
        emit_current=not bool(ow),
        tomorrow_detail=want_tom,
        today_daily=want_td,
        tomorrow_one_liner=tomorrow_one,
    )
    if ow and om:
        ctx = ow.rstrip() + "\n\n" + om
    else:
        ctx = om or ow
    return (ctx, instant)


def fetch_live_weather_for_message(message: str) -> str:
    """
    Mesajdan şehir ve 'yarın' niyetini çıkarır; tek Open-Meteo isteğiyle özet üretir.
    OPENWEATHER_API_KEY varsa anlık özet önce OW'dan gelir, OM günlük satırları eklenir.
    """
    return compute_live_weather_outcome(message)[0]
