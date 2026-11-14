# -*- coding: utf-8 -*-
"""
Sahne süper-el (plan sıra 21) + harita komutları.
Söz → niyet → sahne eylemi. Organ sürücüleri istemcide uygular.
Boot / yüz kilidine dokunmaz.
"""
from __future__ import annotations

import re
from typing import Any

# Sekiz fiil (plan)
FILLER = (
    "goster",
    "odakla",
    "karsilastir",
    "zaman_kaydir",
    "pin",
    "degistir",
    "disari_ver",
    "temizle",
)

ORGANLAR = (
    "harita",
    "cam",
    "uzay",
    "belge",
    "tablo",
    "sunum",
    "cizim",
    "foto",
    "video",
    "ses",
    "eser",
    "yuz",
)

_TR = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "c",
        "Ğ": "g",
        "İ": "i",
        "Ö": "o",
        "Ş": "s",
        "Ü": "u",
    }
)

_STOP = {
    "bir",
    "bu",
    "su",
    "o",
    "ve",
    "ile",
    "icin",
    "lutfen",
    "bana",
    "beni",
    "simdi",
    "hemen",
    "daha",
    "cok",
    "az",
    "biraz",
    "sahne",
    "sahnede",
    "ekran",
    "ekranda",
    "harita",
    "haritayi",
    "haritaya",
    "haritanin",
    "haritam",
    "earth",
    "map",
    "atlas",
    "cografya",
    "goster",
    "gosterir",
    "gosterelim",
    "ac",
    "acik",
    "kapat",
    "yaklastir",
    "yaklas",
    "uzaklastir",
    "uzaklas",
    "zoom",
    "odak",
    "odaklan",
    "odakla",
    "git",
    "getir",
    "yansit",
    "koy",
    "bak",
    "bakayim",
    "gor",
    "goreyim",
    "ulke",
    "sehir",
    "kasaba",
    "ilce",
    "bolge",
    "yer",
    "konum",
    "koordinat",
    "merkez",
    "merkezine",
    "uzerine",
    "icine",
    "dogru",
    "kadar",
    "2d",
    "3d",
    "4d",
    "uc",
    "dort",
    "iki",
    "boyut",
    "boyuta",
    "boyutu",
    "boyutlu",
    "ucboyut",
    "ucboyutlu",
    "tarihi",
    "tarih",
    "historical",
    "katman",
    "moda",
    "modu",
    "moduna",
    "mod",
    "don",
    "gec",
    "yap",
    "uydu",
    "uyduya",
    "satellite",
    "panorama",
    "panoramik",
    "tur",
    "tura",
    "dunya",
    "glob",
    "globe",
}


def _norm(s: str) -> str:
    t = (s or "").strip().lower().translate(_TR)
    t = re.sub(r"[\"'`]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


def _strip_case_suffix(word: str) -> str:
    """istanbulu/erzuruma/turkiyeye → kök (kaba)."""
    w = (word or "").strip()
    if len(w) < 4:
        return w
    for suf in (
        "sini",
        "sina",
        "sini",
        "ye",
        "ya",
        "yu",
        "yi",
        "na",
        "ne",
        "nu",
        "ni",
        "nda",
        "nde",
        "dan",
        "den",
        "u",
        "ü",
        "i",
        "ı",
        "a",
        "e",
    ):
        # ascii norm already; keep simple
        pass
    for suf in ("sina", "sini", "suna", "sunu", "ye", "ya", "yu", "yi", "na", "ne", "nu", "ni", "nda", "nde"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    for suf in ("u", "i", "a", "e"):
        if w.endswith(suf) and len(w) >= 5:
            return w[:-1]
    return w


def _clean_hedef_cand(cand: str) -> str | None:
    cand = (cand or "").strip(" .,!;:")
    cand = re.sub(
        r"\b(harita|haritayi|haritaya|haritanin|goster|ac|odaklan|odakla|yaklastir|yaklas|uzaklastir|lutfen|daha|cok|biraz|2d|3d|4d|uc\s*boyut(?:lu)?|dort\s*boyut(?:lu)?|iki\s*boyut(?:lu)?|tarihi|historical|katman|moda|modu|moduna|gec|yap|don|uydu|uyduya|satellite|panorama|panoramik|tur|tura|dunya\s*turu|glob(?:e)?)\b",
        " ",
        cand,
    )
    cand = re.sub(r"\s+", " ", cand).strip()
    if not cand or len(cand) < 2:
        return None
    if cand in _STOP:
        return None
    # tek token ise ek kırp
    parts = cand.split()
    parts = [_strip_case_suffix(p) for p in parts if p not in _STOP]
    cand2 = " ".join(p for p in parts if p)
    if not cand2 or cand2 in _STOP or len(cand2) < 2:
        return None
    return cand2


def _extract_hedef(n: str) -> str | None:
    """Yer adı çıkar — ülke/şehir/kasaba."""
    if not n:
        return None

    # Bilinen yer sözlüğü önce (çoklu kelime); mod kelimelerini at
    try:
        from ilim_assistant.sahne_harita_geo import _YEREL, _norm_key

        tokens = [
            t
            for t in n.replace(",", " ").split()
            if t
            not in _STOP
            and t
            not in (
                "2d",
                "3d",
                "4d",
                "uydu",
                "tur",
                "panorama",
                "panoramik",
                "goster",
                "ac",
            )
        ]
        for i in range(len(tokens)):
            for j in range(len(tokens), i, -1):
                chunk = " ".join(tokens[i:j])
                key = _norm_key(chunk)
                key2 = _norm_key(_strip_case_suffix(chunk))
                if key in _YEREL:
                    return chunk
                if key2 in _YEREL:
                    return key2
    except Exception:
        pass

    patterns = [
        # fiil + yer
        r"(?:odaklan|odakla|yaklastir|uzaklastir|git|goster|ac|getir|yansit)\s+(?:harita(?:yi|ya|nin)?\s+)?(.+)$",
        # yer + haritasını göster
        r"(.+?)\s+(?:haritasini|haritasina|haritasi|haritayi)\s+(?:goster|ac|yaklastir|odakla|getir)",
        # yer + uydu/3d/4d/tur
        r"(.+?)\s+(?:uydu|uyduya|3d|4d|2d|tur|panorama|panoramik)\s*$",
        # yer + göster/aç/odaklan (sonda fiil)
        r"(.+?)\s+(?:goster|ac|odaklan|odakla|yaklastir)\s*$",
        # yer'e odaklan
        r"(.+?)(?:ye|ya|yu|yi|na|ne|nu|ni)\s+(?:odaklan|odakla|git)\b",
        r"(?:ulke|sehir|kasaba|ilce|bolge)\s+(.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, n)
        if m:
            cleaned = _clean_hedef_cand(m.group(1))
            if cleaned:
                return cleaned

    if "turkiye" in n or "turkey" in n:
        return "turkiye"
    return None


def resolve_super_el(text: str, *, geocode: bool = True) -> dict[str, Any]:
    """
    Doğal cümleden süper-el niyeti.
    Harita için ek alanlar: zoom_delta, geo {lat,lon,zoom,bbox,label}.
    """
    raw = (text or "").strip()
    n = _norm(raw)
    if not n or len(n) < 2:
        return {
            "ok": False,
            "fiil": None,
            "organ": None,
            "hedef": None,
            "guven": 0.0,
            "not": "bos",
            "zoom_delta": 0,
            "action": None,
        }

    fiil = None
    guven = 0.55
    zoom_delta = 0
    action = None  # organ sürücüsü için: show|focus|zoom_in|zoom_out|clear|...

    # --- fiil ---
    if re.search(r"\b(temizle|kapat|kaldir|sil sahne|yuzu getir|yuzune don)\b", n):
        fiil = "temizle"
        action = "clear"
        guven = 0.85
    elif re.search(r"\b(pin|sabitle|hatirla|pinle)\b", n):
        fiil = "pin"
        action = "pin"
        guven = 0.8
    elif re.search(r"\b(disari|export|indir|kaydet|pdf ver)\b", n):
        fiil = "disari_ver"
        action = "export"
        guven = 0.75
    elif re.search(r"\b(karsilastir|yan yana|vs\.?|versus)\b", n):
        fiil = "karsilastir"
        action = "compare"
        guven = 0.8
    elif re.search(
        r"\b(uydu|satellite|goruntu\s*uydu|uydu\s*goruntu|uyduya\s*gec)\b", n
    ):
        fiil = "degistir"
        action = "mode_uydu"
        guven = 0.92
    elif re.search(
        r"\b(dunya\s*turu|panorama|panoramik|kure\s*tur|globe\s*tour|tur\s*mod)\b",
        n,
    ) or re.search(r"\b(panoramik\s+dunya|dunya\s+turu)\b", n):
        fiil = "degistir"
        action = "mode_tur"
        guven = 0.92
    elif re.search(r"\b(4d|dort\s*boyut|tarih[iî]|zaman\s*katman|zamanli\s*uydu|historical|gibs)\b", n):
        fiil = "degistir"
        action = "mode_4d"
        guven = 0.9
    elif re.search(r"\b(gecmis|eski\s*sehir|tarihte|onceki\s*yil)\b", n) and re.search(
        r"\b(sehir|harita|bina|gost|gor)\b", n
    ):
        fiil = "zaman_kaydir"
        action = "era_gecmis"
        guven = 0.88
    elif re.search(r"\b(gelecek|yenileme|kentsel\s*donus|projeksiyon)\b", n) and re.search(
        r"\b(sehir|harita|bina|gost|gor)\b", n
    ):
        fiil = "zaman_kaydir"
        action = "era_gelecek"
        guven = 0.88
    elif re.search(r"\b(bina|ayakizi|binalari|yapi\s*stok)\b", n) and re.search(
        r"\b(goster|ac|yukle|sahne)\b", n
    ):
        fiil = "goster"
        action = "show_buildings"
        guven = 0.9
    elif re.search(
        r"\b(sentinel|stac|uydu\s*analiz|copernicus\s*sentinel|sentinel\s*2)\b", n
    ) or (
        re.search(r"\b(tarim|orman|yangin)\b", n)
        and re.search(r"\b(uydu|goruntu|goster|analiz)\b", n)
    ):
        fiil = "goster"
        action = "mode_sentinel"
        guven = 0.9
    elif re.search(
        r"\b(mapillary|kartaview|sokak\s*goruntu|panorama|pano|sokak\s*seviye)\b", n
    ):
        fiil = "goster"
        action = "mode_pano"
        guven = 0.9
    elif re.search(r"\b(f4map|f4\s*yedek|yedek\s*3d|f4\s*mod)\b", n):
        fiil = "degistir"
        action = "mode_f4"
        guven = 0.9
    elif re.search(r"\b(3d|uc\s*boyut|ucboyut|cesium)\b", n) or re.search(
        r"\b(uc|3)\s*boyut", n
    ):
        fiil = "degistir"
        action = "mode_3d"
        guven = 0.9
    elif re.search(r"\b(2d|iki\s*boyut|duz\s*harita)\b", n):
        fiil = "degistir"
        action = "mode_2d"
        guven = 0.88
    elif re.search(
        r"\b(uzaklastir|uzaklas|geri cekil|zoom out|kucult|genislet)\b", n
    ) or re.search(r"\bdaha\s+(uzak|genis|kucuk)\b", n):
        fiil = "odakla"
        action = "zoom_out"
        zoom_delta = -1
        if re.search(r"\b(iki|2|cok|biraz fazla)\b", n):
            zoom_delta = -2
        guven = 0.88
    elif re.search(
        r"\b(yaklastir|yaklas|yakinlas|zoom in|buyut|detay|yakindan)\b", n
    ) or re.search(r"\bdaha\s+(yakin|buyuk|detay)\b", n):
        fiil = "odakla"
        action = "zoom_in"
        zoom_delta = 1
        if re.search(r"\b(iki|2|cok|biraz fazla|daha da)\b", n):
            zoom_delta = 2
        guven = 0.88
    elif re.search(r"(odak|fokus|merkez|git\b)", n):
        fiil = "odakla"
        action = "focus"
        guven = 0.84
    elif re.search(r"\b(zaman|faz|4d|timeline|yil)\b", n) and re.search(
        r"\b(kaydir|goster|ac)\b", n
    ):
        fiil = "zaman_kaydir"
        action = "timeline"
        guven = 0.7
    elif re.search(r"\b(degistir|degis|yerine koy|guncelle)\b", n):
        fiil = "degistir"
        action = "replace"
        guven = 0.65
    elif re.search(r"\b(goster|ac|sahneye koy|yansit|getir|bak)\b", n):
        fiil = "goster"
        action = "show"
        guven = 0.78

    # --- organ ---
    organ = "yuz"
    if re.search(r"(harita|earth|cograf|atlas|osm|maplibre|\bmap\b)", n):
        organ = "harita"
    elif re.search(r"(kamera|\bcam\b|rtsp|yayin|iss|\btv\b)", n):
        organ = "cam"
    elif re.search(r"(uzay|nasa|hubble|astro|gezegen|teleskop)", n):
        organ = "uzay"
    elif re.search(r"(belge|pdf|metin|\byaz\b)", n):
        organ = "belge"
    elif re.search(r"(tablo|excel|metraj)", n):
        organ = "tablo"
    elif re.search(r"(sunum|slayt)", n):
        organ = "sunum"
    elif re.search(r"(cizim|kroki|\bplan\b)", n):
        organ = "cizim"
    elif re.search(r"(foto|resim|goruntu)", n):
        organ = "foto"
    elif re.search(r"(video|klip|montaj)", n):
        organ = "video"
    elif re.search(r"(\bses\b|muzik|dalga)", n):
        organ = "ses"
    elif re.search(r"(eser|kitap|ayet|hadis|pasaj|tefsir|meal)", n):
        organ = "eser"

    # Yer adı varsa ve zoom/odak/göster → harita varsay
    hedef = _extract_hedef(n)
    # 2D/3D/4D komutlarında «3d» yer adı sanılmasın
    if action in ("mode_2d", "mode_3d", "mode_4d", "mode_uydu", "mode_tur", "mode_f4") and hedef:
        hn = _norm(str(hedef))
        if re.fullmatch(
            r"(2d|3d|4d|uydu|tur|panorama|uc|dort|iki|boyut|ucboyut|tarihi|historical|katman|dunya|glob|globe)",
            hn,
        ) or re.fullmatch(r"(uc|dort|iki)\s*boyut(lu)?|dunya\s*turu", hn):
            hedef = None
    if organ == "yuz" and hedef and action in (
        "show",
        "focus",
        "zoom_in",
        "zoom_out",
        None,
    ):
        # «Erzurum'a odaklan» harita demeden
        if action in ("focus", "zoom_in", "zoom_out", "show") or re.search(
            r"(odak|yaklas|sehir|ulke|kasaba|harita)", n
        ):
            organ = "harita"

    # Salt zoom / görüntü modları (hedef yok) → harita
    if organ == "yuz" and action in (
        "zoom_in",
        "zoom_out",
        "mode_2d",
        "mode_3d",
        "mode_4d",
        "mode_uydu",
        "mode_tur",
        "mode_f4",
        "era_gecmis",
        "era_gelecek",
        "show_buildings",
        "mode_sentinel",
        "mode_pano",
    ):
        organ = "harita"

    if fiil is None and organ != "yuz":
        fiil = "goster"
        action = action or "show"
        guven = min(guven, 0.6)

    if fiil == "odakla" and action == "focus" and zoom_delta == 0 and hedef:
        # yer + odak → hafif yakınlaştır
        pass

    if action is None and fiil == "goster":
        action = "show"
    if action is None and fiil == "odakla":
        action = "focus"
    if action is None and fiil == "temizle":
        action = "clear"

    ok = fiil is not None
    out: dict[str, Any] = {
        "ok": ok,
        "fiil": fiil,
        "organ": organ if ok else None,
        "hedef": hedef,
        "guven": round(guven if ok else 0.0, 2),
        "not": "super_el_v2",
        "zoom_delta": zoom_delta,
        "action": action,
        "fiiller": list(FILLER),
        "organlar": list(ORGANLAR),
        "geo": None,
    }

    # Zoom'da yer arama yok; mod+şehir («istanbul uydu») ve show/focus geocode
    if (
        ok
        and organ == "harita"
        and geocode
        and action not in ("zoom_in", "zoom_out")
        and (
            hedef
            or action in ("show", "focus")
        )
    ):
        try:
            from ilim_assistant.sahne_harita_geo import geocode

            place = hedef or ("turkiye" if action == "show" and not hedef else None)
            if place:
                geo = geocode(place, allow_network=True)
                if geo:
                    out["geo"] = geo
                    if not out["hedef"]:
                        out["hedef"] = geo.get("label") or place
                    out["guven"] = min(0.95, out["guven"] + 0.08)
        except Exception as exc:
            out["geo_error"] = str(exc)[:120]

    return out


def smoke_super_el() -> list[str]:
    fails: list[str] = []
    cases = [
        ("haritayi ac turkiyeye odaklan", "odakla", "harita"),
        ("iss yayinini goster", "goster", "cam"),
        ("nasa uzaydan bak", "goster", "uzay"),
        ("sahneyi temizle", "temizle", None),
        ("bunu pinle", "pin", None),
        ("iki tefsiri karsilastir", "karsilastir", "eser"),
        ("erzuruma odaklan", "odakla", "harita"),
        ("haritayi yaklastir", "odakla", "harita"),
        ("uzaklastir", "odakla", "harita"),
    ]
    for text, fiil, organ in cases:
        r = resolve_super_el(text, geocode=False)
        if not r.get("ok"):
            fails.append(f"ok yok: {text}")
            continue
        if r.get("fiil") != fiil:
            fails.append(f"fiil {text}: {r.get('fiil')} != {fiil}")
        if organ and r.get("organ") != organ:
            fails.append(f"organ {text}: {r.get('organ')} != {organ}")
    # hedef + zoom
    r2 = resolve_super_el("istanbulu goster", geocode=False)
    if r2.get("hedef") is None or "istanbul" not in _norm(str(r2.get("hedef"))):
        fails.append("istanbul hedef yok")
    r3 = resolve_super_el("daha yaklastir", geocode=False)
    if r3.get("zoom_delta", 0) <= 0:
        fails.append("yaklastir zoom_delta")
    r4 = resolve_super_el("uzaklastir", geocode=False)
    if r4.get("zoom_delta", 0) >= 0:
        fails.append("uzaklastir zoom_delta")
    return fails
