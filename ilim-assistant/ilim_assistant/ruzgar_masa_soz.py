"""Dört masanın düz cümlesi. Bilinen kalıp eylem döner; çözülemeyen iş masa değiştirmez."""

from __future__ import annotations

import re

_YANIT = "Masa cümlesi alındı. Açık çalışma sayfası uygular. Model dosya yazmadı."
_RED = (
    "Bunu yapmadım. Masa değişmedi. Şöyle söyle: belgeye selam yaz, "
    "tabloda A1 e 10 yaz, çizime kutu çiz, sunuma Hoş geldin slaytı ekle: bugün."
)


def _bak_masa(raw: str) -> str:
    m = re.match(
        r"^(belgeye|tabloya|çizime|cizime|sunuma)\s+bak\s+ve\s+s[öo]yle$",
        raw,
        re.I,
    )
    if not m:
        return ""
    ad = m.group(1).lower()
    if ad == "belgeye":
        return "belge"
    if ad == "tabloya":
        return "tablo"
    if ad == "sunuma":
        return "sunum"
    return "cizim"


def _yer_ciz(yer: str, tur: str, renk: str) -> dict | None:
    yer_ad = (yer or "").lower()
    sekil = (tur or "").lower()
    eylem = None
    if yer_ad == "ortaya" and sekil == "kutu":
        eylem = {"eylem": "cizim.kutu", "x": 680, "y": 430, "w": 240, "h": 140}
    elif yer_ad == "ortaya" and sekil == "daire":
        eylem = {"eylem": "cizim.daire", "x": 800, "y": 500, "rx": 80, "ry": 60}
    elif yer_ad == "ortaya":
        eylem = {"eylem": "cizim.cizgi", "x1": 200, "y1": 500, "x2": 1400, "y2": 500}
    elif yer_ad in {"üste", "uste"}:
        if sekil == "kutu":
            eylem = {"eylem": "cizim.kutu", "x": 80, "y": 40, "w": 240, "h": 140}
        elif sekil == "daire":
            eylem = {"eylem": "cizim.daire", "x": 300, "y": 120, "rx": 80, "ry": 60}
        else:
            eylem = {"eylem": "cizim.cizgi", "x1": 80, "y1": 60, "x2": 1520, "y2": 60}
    elif yer_ad == "alta":
        if sekil == "kutu":
            eylem = {"eylem": "cizim.kutu", "x": 80, "y": 780, "w": 240, "h": 140}
        elif sekil in {"çizgi", "cizgi"}:
            eylem = {"eylem": "cizim.cizgi", "x1": 80, "y1": 920, "x2": 1520, "y2": 920}
        else:
            eylem = {"eylem": "cizim.daire", "x": 800, "y": 860, "rx": 80, "ry": 60}
    if not eylem:
        return None
    if renk:
        eylem["renk"] = renk
    return eylem


def _parca(raw: str) -> dict | None:
    m = re.match(r"^belgede\s+(.+?)\s+yerine\s+(.+?)\s+yaz$", raw, re.I)
    if m and m.group(1).strip() and m.group(2).strip():
        return {"eylem": "belge.yerine", "eski": m.group(1).strip(), "yeni": m.group(2).strip()}
    m = re.match(r"^belgeye\s+(.+?)\s+yaz$", raw, re.I)
    if m and m.group(1).strip():
        return {"eylem": "belge.yaz", "metin": m.group(1).strip()}
    m = re.match(r"^belgeye\s+(.+?)\s+ekle$", raw, re.I)
    if m and m.group(1).strip():
        return {"eylem": "belge.ekle", "metin": m.group(1).strip()}
    m = re.match(r"^(?:tabloda\s+)?([A-La-l])(\d{1,2})\s+h[üu]cresini\s+sil$", raw, re.I)
    if m:
        return {"eylem": "tablo.sil", "hucre": (m.group(1) + m.group(2)).upper()}
    m = re.match(r"^([A-La-l])\s+s[üu]tununu\s+topla$", raw, re.I)
    if m:
        return {"eylem": "tablo.topla", "sutun": m.group(1).upper()}
    m = re.match(
        r"^(?:tabloda|tabloya)\s+([A-La-l])(\d{1,2})\s*(?:e|ye|hücresine|hucresine)?\s*(.+?)\s+yaz$",
        raw,
        re.I,
    )
    if m and m.group(3).strip():
        return {
            "eylem": "tablo.hucre",
            "hucre": (m.group(1) + m.group(2)).upper(),
            "deger": m.group(3).strip(),
        }
    if re.match(r"^(?:belgeyi temizle|belge temizle)$", raw, re.I):
        return {"eylem": "belge.temizle"}
    if re.match(r"^(?:tabloyu temizle|tablo temizle)$", raw, re.I):
        return {"eylem": "tablo.temizle"}
    if re.match(r"^(?:çizimi temizle|cizimi temizle|çizim temizle)$", raw, re.I):
        return {"eylem": "cizim.temizle"}
    if re.match(r"^(?:sunumu temizle|sunum temizle)$", raw, re.I):
        return {"eylem": "sunum.temizle"}
    m = re.match(r"^slayt[ıi]n\s+metnini\s+(.+?)\s+yap$", raw, re.I)
    if m and m.group(1).strip():
        return {"eylem": "sunum.metin", "metin": m.group(1).strip()}
    m = re.match(
        r"^(?:çizime|cizime)\s+(ortaya|üste|uste|alta)\s+"
        r"(?:(siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+)?"
        r"(kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)$",
        raw,
        re.I,
    )
    if m:
        return _yer_ciz(m.group(1), m.group(3), m.group(2) or "")
    m = re.match(
        r"^(?:çizime|cizime)\s+(siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+"
        r"(kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)$",
        raw,
        re.I,
    )
    if m:
        renk = m.group(1)
        tur = m.group(2).lower()
        if tur == "kutu":
            return {"eylem": "cizim.kutu", "x": 80, "y": 80, "w": 240, "h": 140, "renk": renk}
        if tur == "daire":
            return {"eylem": "cizim.daire", "x": 300, "y": 220, "rx": 80, "ry": 60, "renk": renk}
        return {"eylem": "cizim.cizgi", "x1": 40, "y1": 40, "x2": 400, "y2": 200, "renk": renk}
    m = re.match(r"^(?:çizime|cizime)\s+(kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)$", raw, re.I)
    if m:
        tur = m.group(1).lower()
        if tur == "kutu":
            return {"eylem": "cizim.kutu", "x": 80, "y": 80, "w": 240, "h": 140}
        if tur == "daire":
            return {"eylem": "cizim.daire", "x": 300, "y": 220, "rx": 80, "ry": 60}
        return {"eylem": "cizim.cizgi", "x1": 40, "y1": 40, "x2": 400, "y2": 200}
    m = re.match(r"^slayt[ıi]n\s+ba[sş]l[ıi][gğ][ıi]n[ıi]\s+(.+?)\s+yap$", raw, re.I)
    if m and m.group(1).strip():
        return {"eylem": "sunum.baslik", "baslik": m.group(1).strip()}
    m = re.match(r"^sunuma\s+slayt\s+ekle\s*[:\-]\s*(.+?)\s*\|\s*(.+)$", raw, re.I)
    if m and (m.group(1).strip() or m.group(2).strip()):
        return {"eylem": "sunum.ekle", "baslik": m.group(1).strip(), "metin": m.group(2).strip()}
    m = re.match(r"^sunuma\s+(.+?)\s+slayt[ıi]\s+ekle\s*[:\-]\s*(.+)$", raw, re.I)
    if m and (m.group(1).strip() or m.group(2).strip()):
        return {"eylem": "sunum.ekle", "baslik": m.group(1).strip(), "metin": m.group(2).strip()}
    return None


def coz(text: str) -> dict | None:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw or len(raw) > 9000:
        return None
    bak = _bak_masa(raw)
    if bak:
        return {"bak": bak}
    if re.match(r"^masay[ıi]\s+ba[sş]tan\s+tasarla$", raw, re.I):
        return {"red": True}
    parcalar = [p.strip() for p in re.split(r"\s*,\s*|\s+sonra\s+", raw) if p.strip()]
    if len(parcalar) >= 2:
        liste = []
        for parca in parcalar:
            if _bak_masa(parca):
                return {"red": True}
            hit = _parca(parca)
            if not hit:
                return {"red": True} if liste else None
            liste.append(hit)
        return {"liste": liste}
    return _parca(raw)


def masa_sohbet_yaniti(msg: str) -> str | None:
    """Modelden önce. Masa dosyası sunucuda yoktur; açık sayfa uygular."""
    hit = coz(msg)
    if not hit:
        return None
    if hit.get("red"):
        return _RED
    return _YANIT
