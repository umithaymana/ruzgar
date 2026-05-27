from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _path() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / "ruzgar_kullanici_baglami.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load() -> dict[str, Any]:
    p = _path()
    if not p.is_file():
        return {"active_user": "", "profiles": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"active_user": "", "profiles": {}}
        if not isinstance(data.get("profiles"), dict):
            data["profiles"] = {}
        if not isinstance(data.get("active_user"), str):
            data["active_user"] = ""
        return data
    except Exception:
        return {"active_user": "", "profiles": {}}


def _save(data: dict[str, Any]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _norm_name(name: str) -> str:
    n = re.sub(r"\s+", " ", (name or "").strip())
    n = n.strip(" \t\r\n.,:;!?")
    if not n:
        return ""
    bits = []
    for b in n.split(" "):
        if b.lower() in ("abi", "abla"):
            bits.append(b.lower())
        else:
            bits.append(b[:1].upper() + b[1:])
    return " ".join(bits)[:60]


def _slug(name: str) -> str:
    s = (name or "").strip().lower()
    s = s.replace("ı", "i").replace("ğ", "g").replace("ş", "s").replace("ö", "o").replace(
        "ü", "u"
    ).replace("ç", "c")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", "_", s).strip("_")[:80]


def _detect_user_intro(message: str) -> str:
    msg = (message or "").strip()
    patterns = (
        r"(?i)\bbenim\s+ad[ıi]m\s+(?P<name>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,48})",
        r"(?i)\bad[ıi]m\s+(?P<name>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,48})",
        r"(?i)\bben\s+(?P<name>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,48})",
    )
    for pat in patterns:
        m = re.search(pat, msg)
        if not m:
            continue
        raw = _norm_name(m.group("name"))
        if not raw:
            continue
        low = raw.lower()
        if low in ("var", "yok", "burada", "geldim", "hazirim"):
            continue
        return raw
    return ""


def _ensure_profile(data: dict[str, Any], user_name: str) -> dict[str, Any]:
    uid = _slug(user_name)
    if not uid:
        uid = "kullanici"
    profiles = data.setdefault("profiles", {})
    if uid not in profiles:
        profiles[uid] = {
            "display_name": user_name,
            "aliases": [user_name],
            "relations": [],
            "topic_notes": [],
            "last_seen": _now_iso(),
        }
    prof = profiles[uid]
    if user_name and user_name not in prof.get("aliases", []):
        prof.setdefault("aliases", []).append(user_name)
    prof["display_name"] = user_name or prof.get("display_name") or "kullanici"
    prof["last_seen"] = _now_iso()
    return prof


def _add_topic_note(profile: dict[str, Any], message: str) -> None:
    msg = re.sub(r"\s+", " ", (message or "").strip())
    if len(msg) < 18:
        return
    if any(x in msg.lower() for x in ("hatırla:", "unut:", "görev", "hatırlat")):
        return
    note = msg[:160]
    arr = profile.setdefault("topic_notes", [])
    if note in arr:
        return
    arr.append(note)
    if len(arr) > 12:
        del arr[:-12]


def _add_style_pref(profile: dict[str, Any], pref: str) -> None:
    pref = re.sub(r"\s+", " ", (pref or "").strip())
    if not pref:
        return
    arr = profile.setdefault("style_prefs", [])
    if pref in arr:
        return
    arr.append(pref)
    if len(arr) > 10:
        del arr[:-10]


def _extract_style_prefs(profile: dict[str, Any], message: str) -> None:
    low = (message or "").lower()
    if "kısa ve net" in low or "kisa ve net" in low:
        _add_style_pref(profile, "Yanıtları kısa ve net ver.")
    if "adım adım" in low or "adim adim" in low:
        _add_style_pref(profile, "Gerektiğinde adım adım anlat.")
    if "teknik detaya girme" in low or "teknik detay verme" in low:
        _add_style_pref(profile, "Gereksiz teknik detaya girme.")
    if "örnek ver" in low or "ornek ver" in low:
        _add_style_pref(profile, "Uygun yerde kısa örnek ver.")


def _add_relation(profile: dict[str, Any], subject: str, predicate: str, obj: str, source: str) -> None:
    s = _norm_name(subject)
    o = _norm_name(obj)
    if not s or not o:
        return
    rels = profile.setdefault("relations", [])
    key = (s.lower(), predicate.strip().lower(), o.lower())
    for r in rels:
        if (
            str(r.get("subject", "")).lower(),
            str(r.get("predicate", "")).lower(),
            str(r.get("object", "")).lower(),
        ) == key:
            return
    rels.append(
        {
            "subject": s,
            "predicate": predicate.strip().lower(),
            "object": o,
            "source": source[:180],
            "ts": _now_iso(),
        }
    )
    if len(rels) > 80:
        del rels[:-80]


def _child_of_parent(profile: dict[str, Any], person: str) -> str:
    p = _norm_name(person).lower()
    for r in reversed(profile.get("relations", [])):
        if str(r.get("predicate")) == "child_of" and str(r.get("subject", "")).lower() == p:
            return str(r.get("object") or "")
    return ""


def _extract_relations(profile: dict[str, Any], message: str) -> None:
    msg = (message or "").strip()
    if not msg:
        return
    child = re.search(
        r"(?i)(?P<sub>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,60})\s+benim\s+(?P<obj>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,60})\s+(?:oğlu|oglu|kızı|kizi|çocuğu|cocugu)\s*(?:dur|dir)?",
        msg,
    )
    if child:
        _add_relation(profile, child.group("sub"), "child_of", child.group("obj"), msg)

    low = msg.lower().replace("'", " ").replace("’", " ")
    if "kardeş" in low and any(x in low for x in (" nın ", " nin ", " nun ", " nün ")):
        cut = low.split("kardeş", 1)[0].strip()
        marker_idx = max(cut.rfind(" nın "), cut.rfind(" nin "), cut.rfind(" nun "), cut.rfind(" nün "))
        if marker_idx > 0:
            duo = msg[:marker_idx].replace("'", " ").replace("’", " ").strip()
            tokens = [t for t in duo.split() if t]
            if len(tokens) >= 4:
                sub = " ".join(tokens[:2])
                obj = " ".join(tokens[2:])
                _add_relation(profile, sub, "sibling_of", obj, msg)
                parent = _child_of_parent(profile, obj)
                if parent:
                    _add_relation(profile, sub, "child_of", parent, "sibling inference")


def ingest_message(message: str) -> None:
    raw = (message or "").strip()
    if not raw:
        return
    data = _load()
    low = raw.lower()
    if any(x in low for x in ("yeni kullanıcı", "demo modu", "misafir modu", "kullanıcı sıfırla")):
        data["active_user"] = ""
        _save(data)
        return

    intro_name = _detect_user_intro(raw)
    active = str(data.get("active_user") or "")
    if intro_name:
        active = _slug(intro_name)
        data["active_user"] = active
        profile = _ensure_profile(data, intro_name)
    elif active and active in data.get("profiles", {}):
        profile = data["profiles"][active]
    else:
        # Varsayılanı bozmadan yeni anonim profil aç.
        profile = _ensure_profile(data, "Ümit abi")
        data["active_user"] = _slug(profile.get("display_name") or "umit abi")

    _extract_relations(profile, raw)
    _add_topic_note(profile, raw)
    _extract_style_prefs(profile, raw)
    _save(data)


def active_user_display(default_name: str = "Ümit abi") -> str:
    data = _load()
    active = str(data.get("active_user") or "")
    prof = data.get("profiles", {}).get(active or "", {})
    name = _norm_name(str(prof.get("display_name") or ""))
    return name or default_name


def build_context_block() -> str:
    data = _load()
    active = str(data.get("active_user") or "")
    prof = data.get("profiles", {}).get(active or "", {})
    if not prof:
        return ""
    name = _norm_name(str(prof.get("display_name") or "")) or "Ümit abi"
    topics = list(prof.get("topic_notes") or [])[-4:]
    rels = list(prof.get("relations") or [])[-8:]
    prefs = list(prof.get("style_prefs") or [])[-4:]

    lines = [
        "[KULLANICI BAĞLAMI — KISA HAFIZA]",
        f"- Aktif konuştuğun kişi: {name}",
        f"- Hitap: {name}",
    ]
    if topics:
        lines.append("- Son konuşma notları:")
        lines.extend(f"  - {t}" for t in topics)
    if rels:
        lines.append("- Bilinen kişi ilişkileri:")
        for r in rels:
            s = str(r.get("subject") or "")
            p = str(r.get("predicate") or "")
            o = str(r.get("object") or "")
            if s and p and o:
                lines.append(f"  - {s} {p} {o}")
    if prefs:
        lines.append("- Cevap stili tercihleri:")
        lines.extend(f"  - {p}" for p in prefs)
    lines.append(
        f"- Talimat: Bu blok dahili bağlamdır; cevapta kullanıcıya '{name}' diye hitap et, "
        "kullanıcıya 'hafızamda' demeden doğal konuş."
    )
    lines.append("[/KULLANICI BAĞLAMI]")
    return "\n".join(lines)

