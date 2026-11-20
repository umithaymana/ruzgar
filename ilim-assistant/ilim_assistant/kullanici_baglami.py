from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _path() -> Path:
    try:
        from ilim_assistant.ruzgar_public_mode import current_user_id, kullanici_baglami_path

        return kullanici_baglami_path(current_user_id())
    except Exception:
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


_OWNER_DISPLAY = "Ümit abi"
_OWNER_SLUGS = frozenset({"umit_abi", "umit", "gokcenur", "gokcenur_abi"})

# Cümle kırıntısı / selam — kişi adı değil
_NAME_BLOCK_TOKENS = frozenset(
    {
        "var",
        "yok",
        "burada",
        "geldim",
        "hazirim",
        "hazırım",
        "nasilsin",
        "nasılsın",
        "iyi",
        "gunaydin",
        "günaydın",
        "merhaba",
        "selam",
        "tesekkur",
        "teşekkür",
        "soracagim",
        "soracağım",
        "soyleyeyim",
        "söyleyeyim",
        "diyeyim",
        "yasindayim",
        "yaşındayım",
        "kac",
        "kaç",
        "diyorum",
        "usudum",
        "üşüdüm",
        "kactim",
        "kaçtım",
        "uzuluyorum",
        "üzülüyorum",
        "seviyorum",
        "kullaniyorum",
        "kullanıyorum",
        "kesfettim",
        "keşfettim",
        "iyiyim",
        "degilim",
        "değilim",
        "miyim",
        "misin",
        "mısın",
        "musun",
        "müsün",
        "hangi",
        "ne",
        "nedir",
        "kim",
        "kimim",
        "benim",
        "senin",
        "sana",
        "seni",
        "bana",
        "beni",
        "cok",
        "çok",
        "daha",
        "bir",
        "sey",
        "şey",
        "de",
        "da",
        "ki",
        "ve",
        "ile",
        "icin",
        "için",
        "ruzgar",
        "rüzgar",
        "bak",
        "ama",
        "yoksa",
        "ol",
        "olma",
        "yolunda",
        "ugrasan",
        "uğraşan",
    }
)

_VERB_TAIL = re.compile(
    r"(?i)(?:"
    r"yorum|iyorum|uyoruz|ece[gğ]im|aca[gğ]im|eceksin|acaksın|"
    r"yeyim|yay[ıi]m|yayim|"
    r"day[ıi]m|deyim|dayim|"
    r"dim|d[ıi]m|duk|dük|dik|dık|di[gk]|dı[gk]|"
    r"misin|m[ıi]s[ıi]n|musun|müsün|miyim|mıyım|"
    r"sin|sın|sun|sün"
    r")$"
)


def _norm_name(name: str) -> str:
    n = re.sub(r"\s+", " ", (name or "").strip())
    n = n.strip(" \t\r\n.,:;!?\"'`")
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


def is_plausible_person_name(name: str) -> bool:
    """Cümle kırıntısı ≠ kişi adı. Sahte profil kapısı."""
    raw = (name or "").strip()
    if not raw or "?" in raw or "!" in raw:
        return False
    n = _norm_name(raw)
    if not n or len(n) < 2 or len(n) > 40:
        return False
    if _slug(n) in _OWNER_SLUGS:
        return True
    tokens = [t for t in n.split(" ") if t]
    if not tokens or len(tokens) > 4:
        return False
    # En az bir «özad» benzeri parça (abi/abla tek başına yetmez)
    core = [t for t in tokens if t.lower() not in ("abi", "abla", "bey", "hanim", "hanım")]
    if not core:
        return False
    for t in tokens:
        low = t.lower()
        if low in _NAME_BLOCK_TOKENS:
            return False
        if _VERB_TAIL.search(low) and low not in ("abi", "abla"):
            # Kısa özel adlar (Can, Ali) fiil eki gibi görünmesin diye len>=4
            if len(low) >= 4:
                return False
    if not re.match(
        r"^[A-Za-zÇĞİÖŞÜçğıöşü][A-Za-zÇĞİÖŞÜçğıöşü\-]*"
        r"(?:\s+[A-Za-zÇĞİÖŞÜçğıöşü][A-Za-zÇĞİÖŞÜçğıöşü\-]*){0,3}$",
        n,
    ):
        return False
    # 3+ kelime ve unvan yoksa cümle şüphesi
    if len(tokens) >= 3 and not any(
        t.lower() in ("abi", "abla", "bey", "hanım", "hanim") for t in tokens
    ):
        return False
    return True


def _detect_user_intro(message: str) -> str:
    """Yalnız açık ad tanıtımı. «Ben …» cümlesi kişi adı sayılmaz."""
    msg = (message or "").strip()
    patterns = (
        r"(?i)\bbenim\s+ad[ıi]m\s+(?P<name>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,40})",
        r"(?i)\bad[ıi]m\s+(?P<name>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,40})",
        r"(?i)\bbeni\s+(?P<name>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,32})\s+"
        r"diye\s+(?:[cç]a[gğ][ıi]r|hitap|seslen)",
        r"(?i)\bbana\s+(?P<name>[a-zA-ZçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\- ]{1,32})\s+de\b",
    )
    for pat in patterns:
        m = re.search(pat, msg)
        if not m:
            continue
        raw = _norm_name(m.group("name"))
        # Trailing cümle artığını kes (ilk 1–3 token)
        parts = raw.split()
        if len(parts) > 3:
            raw = _norm_name(" ".join(parts[:3]))
        if is_plausible_person_name(raw):
            return raw
    return ""


def list_suspect_profiles(*, data: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """Silme yok — sahte kişi adayı listesi (Mimar onayı için)."""
    blob = data if isinstance(data, dict) else _load()
    out: list[dict[str, str]] = []
    for uid, prof in (blob.get("profiles") or {}).items():
        if not isinstance(prof, dict):
            continue
        dn = str(prof.get("display_name") or "")
        if uid in _OWNER_SLUGS or is_plausible_person_name(dn):
            continue
        out.append(
            {
                "slug": str(uid),
                "display_name": dn,
                "reason": "cumle_kirintisi_veya_sahte_kisi",
            }
        )
    out.sort(key=lambda x: x.get("slug") or "")
    return out


def heal_active_user_if_poisoned(data: dict[str, Any]) -> bool:
    """Aktif kullanıcı sahteyse Ümit abi'ye çek — profil silmez."""
    active = str(data.get("active_user") or "")
    profiles = data.setdefault("profiles", {})
    changed = False
    if active and active in profiles:
        dn = str(profiles[active].get("display_name") or "")
        if active not in _OWNER_SLUGS and not is_plausible_person_name(dn):
            changed = True
            active = ""
    if not active or active not in profiles:
        _ensure_profile(data, _OWNER_DISPLAY)
        data["active_user"] = _slug(_OWNER_DISPLAY)
        return True
    return changed


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
    if "önce test" in low or "once test" in low:
        _add_style_pref(profile, "Değişiklikten önce/sonra test doğrulaması yap.")
    if "uzun yazma" in low or "kısa yaz" in low or "kisa yaz" in low:
        _add_style_pref(profile, "Uzun anlatım yerine kısa çıktı ver.")


def _add_relation(profile: dict[str, Any], subject: str, predicate: str, obj: str, source: str) -> None:
    s = _norm_name(subject)
    o = _norm_name(obj)
    if not s or not o:
        return
    if not is_plausible_person_name(s) or not is_plausible_person_name(o):
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

    # Sahte aktif kişi varsa önce iyileştir (silmeden).
    heal_active_user_if_poisoned(data)

    intro_name = _detect_user_intro(raw)
    active = str(data.get("active_user") or "")
    if intro_name:
        active = _slug(intro_name)
        data["active_user"] = active
        profile = _ensure_profile(data, intro_name)
    elif active and active in data.get("profiles", {}):
        profile = data["profiles"][active]
        dn = str(profile.get("display_name") or "")
        if active not in _OWNER_SLUGS and not is_plausible_person_name(dn):
            profile = _ensure_profile(data, _OWNER_DISPLAY)
            data["active_user"] = _slug(_OWNER_DISPLAY)
    else:
        profile = _ensure_profile(data, _OWNER_DISPLAY)
        data["active_user"] = _slug(_OWNER_DISPLAY)

    _extract_relations(profile, raw)
    _add_topic_note(profile, raw)
    _extract_style_prefs(profile, raw)
    _save(data)


def active_user_display(default_name: str = "Ümit abi") -> str:
    data = _load()
    if heal_active_user_if_poisoned(data):
        _save(data)
    active = str(data.get("active_user") or "")
    prof = data.get("profiles", {}).get(active or "", {})
    name = _norm_name(str(prof.get("display_name") or ""))
    if name and (active in _OWNER_SLUGS or is_plausible_person_name(name)):
        return name
    return default_name


def active_style_prefs(limit: int = 6) -> list[str]:
    data = _load()
    active = str(data.get("active_user") or "")
    prof = data.get("profiles", {}).get(active or "", {})
    prefs = [str(x).strip() for x in (prof.get("style_prefs") or []) if str(x).strip()]
    lim = max(1, min(int(limit), 12))
    return prefs[-lim:]


def build_programming_style_directive() -> str:
    prefs = active_style_prefs(limit=6)
    if not prefs:
        return ""
    lines = ["[PROGRAMLAMA KULLANICI TERCIHI]"]
    lines.extend(f"- {p}" for p in prefs)
    lines.append(
        "Talimat: Programlama yanıtında bu tercihleri öncelikli uygula; çelişirse kullanıcıdan netleştirme iste."
    )
    lines.append("[/PROGRAMLAMA KULLANICI TERCIHI]")
    return "\n".join(lines)


def build_context_block() -> str:
    data = _load()
    if heal_active_user_if_poisoned(data):
        _save(data)
    active = str(data.get("active_user") or "")
    prof = data.get("profiles", {}).get(active or "", {})
    if not prof:
        return ""
    name = _norm_name(str(prof.get("display_name") or ""))
    if not name or (
        active not in _OWNER_SLUGS and not is_plausible_person_name(name)
    ):
        name = _OWNER_DISPLAY
    topics = list(prof.get("topic_notes") or [])[-4:]
    rels = [
        r
        for r in list(prof.get("relations") or [])[-12:]
        if isinstance(r, dict)
        and is_plausible_person_name(str(r.get("subject") or ""))
        and is_plausible_person_name(str(r.get("object") or ""))
    ][-8:]
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

