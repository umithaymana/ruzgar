# -*- coding: utf-8 -*-
"""Rüzgar — Arapça lügat / kök-müştak / nahiv-sarf anlık cevap."""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "03_arapca_lugat"
_KOK = _DIR / "kuran_kok_lugat.jsonl"
_KLASIK = _DIR / "klasik_kok_lugat.jsonl"
_NAHIV = _DIR / "nahiv_sarf_temel.jsonl"
_LOOKUP = _DIR / "lookup_index.json"

# Latin / TR yazım → kök (sık Kur'an kelimeleri; sohbet dili)
_LATIN_TO_ROOT: dict[str, str] = {
    "rahman": "رحم",
    "rahmaan": "رحم",
    "rahmanin": "رحم",
    "rahim": "رحم",
    "rahîm": "رحم",
    "raheem": "رحم",
    "rahmet": "رحم",
    "kitab": "كتب",
    "kitap": "كتب",
    "kuran": "قرأ",
    "kur'an": "قرأ",
    "quran": "قرأ",
    "allah": "أله",
    "rabb": "ربب",
    "rab": "ربب",
    "iman": "أمن",
    "islam": "سلم",
    "salam": "سلم",
    "selam": "سلم",
    "sabr": "صبر",
    "sabir": "صبر",
    "ilm": "علم",
    "ilim": "علم",
    "alim": "علم",
    "nuzul": "نزل",
    "nüzul": "نزل",
    "hidayet": "هدي",
    "huda": "هدي",
    "tekbir": "كبر",
    "hamd": "حمد",
    "tesbih": "سبح",
    "zikr": "ذكر",
    "zikir": "ذكر",
    "dua": "دعو",
    "tawba": "توب",
    "tövbe": "توب",
    "tevbe": "توب",
    "gafur": "غفر",
    "magfiret": "غفر",
    "rizk": "رزق",
    "rızık": "رزق",
    "halq": "خلق",
    "halk": "خلق",
    "nur": "نور",
    "zulm": "ظلم",
    "zulüm": "ظلم",
    "haqq": "حقق",
    "hak": "حقق",
    "batil": "بطل",
    "bâtıl": "بطل",
    "shirk": "شرك",
    "şirk": "شرك",
    "kufr": "كفر",
    "küfür": "كفر",
    "salat": "صلو",
    "salât": "صلو",
    "namaz": "صلو",
    "zakat": "زكو",
    "zekat": "زكو",
    "zekât": "زكو",
    "sawm": "صوم",
    "oruç": "صوم",
    "hajj": "حجج",
    "hac": "حجج",
    "nabi": "نبأ",
    "nebi": "نبأ",
    "rasul": "رسل",
    "resul": "رسل",
    "malak": "ملك",
    "melek": "ملك",
    "shaytan": "شيط",
    "şeytan": "شيط",
    "jannah": "جنن",
    "cennet": "جنن",
    "insan": "أنس",
    "insanlar": "أنس",
    "nafs": "نفس",
    "nefis": "نفس",
    "ruh": "روح",
    "qalb": "قلب",
    "kalp": "قلب",
    "ayat": "أيي",
    "ayet": "أيي",
    "surah": "سور",
    "sure": "سور",
    "ayah": "أيي",
    "amin": "أمن",
    "mu'min": "أمن",
    "mümin": "أمن",
    "kafir": "كفر",
    "kâfir": "كفر",
    "taqwa": "وقي",
    "takva": "وقي",
    "sabır": "صبر",
    "şükür": "شكر",
    "shukr": "شكر",
    "amr": "أمر",
    "emir": "أمر",
    "yawm": "يوم",
    "yevm": "يوم",
    "ard": "أرض",
    "arz": "أرض",
    "sama": "سمو",
    "sema": "سمو",
    "gök": "سمو",
}

# Yüksek frekans / sık sorulan kökler — kısa TR (meal dili, uydurma değil)
_TR_ROOT_HINTS: dict[str, str] = {
    "أله": "Allah (özel isim / ilâh)",
    "ربب": "Rab, sahip, terbiye eden",
    "أيي": "âyet, işaret, delil",
    "أتي": "gelmek, getirmek",
    "بين": "açıklamak, ayırt etmek",
    "شيأ": "şey, bir şey",
    "كلل": "bütün, her; (bağlama göre) yorulmak",
    "عذب": "azap; (bağlama göre) tatlı su",
    "أنس": "insan, ünsiyet",
    "عمل": "amel, iş yapmak",
    "رأي": "görmek, görüş",
    "قبل": "ön, kabul etmek, yönelmek",
    "هدي": "hidayet, yol göstermek",
    "ذكر": "zikir, anmak, hatırlamak",
    "حقق": "hak, gerçek, sabit olmak",
    "جيأ": "gelmek",
    "نزل": "inmek, indirmek (nüzûl)",
    "أخر": "sonra, âhiret",
    "وقي": "korumak, takvâ",
    "أمر": "emretmek, iş",
    "علم": "bilmek, ilim",
    "كتب": "yazmak, kitap",
    "قرأ": "okumak",
    "رحم": "merhamet, rahmet",
    "أمن": "güven, iman",
    "كفر": "örtmek, inkâr",
    "صلو": "namaz, salât, dua",
    "صلى": "namaz, salât, dua",
    "زكو": "temizlenmek, zekât",
    "صبر": "sabretmek",
    "شكر": "şükretmek",
    "هدى": "hidayet, yol göstermek",
    "ضل": "sapmak",
    "خلق": "yaratmak",
    "رزق": "rızık vermek",
    "ملك": "mülk / melek (bağlama göre)",
    "عبد": "kulluk etmek",
    "سبح": "tesbih etmek",
    "حمد": "hamd etmek",
    "غفر": "bağışlamak",
    "توب": "tövbe etmek",
    "شهد": "şahit olmak",
    "رسل": "göndermek, elçi",
    "نبأ": "haber, nebî",
    "نبي": "haber vermek, nebî",
    "يوم": "gün",
    "أرض": "yer, arz",
    "سما": "gök",
    "سمو": "isim / gök (bağlama göre)",
    "نور": "ışık, nur",
    "ظلم": "zulmetmek, karanlık",
    "حق": "hak, gerçek",
    "بطل": "bâtıl olmak",
    "باطل": "bâtıl",
    "خير": "hayır, iyi",
    "شرر": "şer, kötülük",
    "شرك": "ortak koşmak, şirk",
    "حبب": "sevmek",
    "كره": "hoşlanmamak",
    "موت": "ölüm",
    "حيي": "hayat, diriltmek",
    "أكل": "yemek",
    "شرب": "içmek",
    "سمع": "işitmek",
    "بصر": "görmek",
    "قول": "söylemek",
    "فعل": "yapmak",
    "جعل": "kılmak, etmek",
    "كون": "olmak",
    "وجد": "bulmak",
    "أخذ": "almak",
    "ترك": "bırakmak",
    "دخل": "girmek",
    "خرج": "çıkmak",
    "رجع": "dönmek",
    "قام": "ayakta durmak, ikame",
    "قعد": "oturmak",
    "مشي": "yürümek",
    "جرى": "akmak, cereyan",
    "فتح": "açmak",
    "غلق": "kapamak",
    "درس": "öğrenmek, ders",
    "فقه": "anlamak, fıkıh",
    "حكم": "hükmetmek",
    "عدل": "adalet",
    "صدق": "doğru olmak",
    "كذب": "yalan söylemek",
    "صوم": "oruç tutmak",
    "حجج": "hac, delil",
    "قتل": "öldürmek",
    "ولد": "doğmak, çocuk",
    "زوج": "eş",
    "أخو": "kardeş",
    "أب": "baba",
    "أمم": "ümmet, anne",
    "قوم": "kavim, ayağa kalkmak",
    "ناس": "insanlar",
    "رجل": "adam, yürümek",
    "مرأ": "kadın, kişi",
    "يد": "el",
    "وجه": "yüz, yönelmek",
    "قلب": "kalp, çevirmek",
    "نفس": "nefis, can",
    "روح": "ruh",
    "جنن": "cin / cennet (bağlama göre)",
    "شيط": "şeytan",
    "إبليس": "İblis",
    "جن": "cin",
    "الله": "Allah (özel isim)",
    "دعو": "dua, çağrı",
    "كبر": "büyük olmak, tekbir",
    "سلم": "selâm, teslim olmak, İslâm",
    "سور": "sûre / sur",
}

_STOP_LATIN = {
    "nedir", "ne", "demek", "anlam", "anlami", "anlamı", "kok", "kök", "koku",
    "kökü", "kokü", "lugat", "lügat", "sozluk", "sözlük", "arapca", "arapça",
    "arabic", "root", "mushtaq", "mustak", "müştak", "mushtak", "nahiv", "sarf",
    "lane", "abi", "ümit", "umit", "rüzgar", "ruzgar", "bir", "bu", "şu", "ve",
    "ile", "icin", "için", "hakkinda", "hakkında", "kelime", "kelimesi",
    "kelimenin", "kelimesinin", "form", "formlar", "turev", "türev",
}


def _fold_ar(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in t if not unicodedata.combining(c))


def _fold_tr(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def looks_like_arapca_lugat_question(msg: str) -> bool:
    low = _fold_tr(msg)
    if not low:
        return False
    cues = (
        "lugat", "lügat", "sozluk", "sözlük", "kok", "kök", "mushtaq", "mushtak",
        "mustak", "nahiv", "sarf", "irab", "i'rab", "vezin", "masdar", "ism-i fail",
        "ism-i meful", "arapca ne demek", "arapça ne demek", "kelimesinin koku",
        "kelimenin koku", "lane", "morpholog", "morfoloji", "bab nedir",
        "harf-i cer", "mubteda", "mübteda", "fail nedir", "turev", "türev",
        "ne demek", "anlami", "anlamı",
    )
    if any(_fold_tr(c) in low for c in cues):
        return True
    if re.search(r"[\u0600-\u06FF]{2,}", msg or "") and any(
        x in low for x in ("nedir", "ne demek", "anlam", "kok", "kök", "mana")
    ):
        return True
    # Latin/TR kök kelimesi tek başına (rahman, kitab…)
    for tok in re.findall(r"[A-Za-zİıŞşĞğÜüÖöÇçÂâÎîÛû']{3,}", msg or ""):
        if _fold_tr(tok) in _LATIN_TO_ROOT:
            return True
    return False


@lru_cache(maxsize=1)
def _load_roots() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not _KOK.is_file():
        return out
    try:
        for line in _KOK.open(encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            root = (r.get("root") or "").strip()
            if root:
                out[root] = r
    except Exception:
        pass
    return out


@lru_cache(maxsize=1)
def _load_klasik() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    if not _KLASIK.is_file():
        return out
    try:
        for line in _KLASIK.open(encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            root = (r.get("root") or "").strip()
            if root:
                out.setdefault(root, []).append(r)
    except Exception:
        pass
    return out


@lru_cache(maxsize=1)
def _load_lookup() -> dict[str, str]:
    if not _LOOKUP.is_file():
        return {}
    try:
        return json.loads(_LOOKUP.read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _load_nahiv() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not _NAHIV.is_file():
        return rows
    try:
        for line in _NAHIV.open(encoding="utf-8"):
            if not line.strip():
                continue
            rows.append(json.loads(line))
    except Exception:
        pass
    return rows


@lru_cache(maxsize=1)
def _buckwalter_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for root, row in _load_roots().items():
        bw = (row.get("root_buckwalter") or "").strip().lower()
        if bw:
            idx[bw] = root
            idx[bw.replace("'", "")] = root
    return idx


def _extract_arabic_token(msg: str) -> Optional[str]:
    m = re.search(r"([\u0600-\u06FF]{2,}(?:\s+[\u0600-\u06FF]{2,}){0,2})", msg or "")
    if not m:
        return None
    return m.group(1).strip()


def _extract_latin_lemma(msg: str) -> Optional[str]:
    tokens = re.findall(r"[A-Za-zİıŞşĞğÜüÖöÇçÂâÎîÛû']{2,}", msg or "")
    for raw in tokens:
        key = _fold_tr(raw).replace("'", "")
        if key in _STOP_LATIN:
            continue
        if key in _LATIN_TO_ROOT:
            return key
        # kısmi: rahmanin → rahman
        for stem, _root in _LATIN_TO_ROOT.items():
            if key.startswith(stem) and len(stem) >= 4:
                return stem
    return None


def lookup_root(token: str) -> Optional[dict[str, Any]]:
    if not token:
        return None
    roots = _load_roots()
    lookup = _load_lookup()
    klasik = _load_klasik()
    bare = _fold_ar(token).replace(" ", "")
    low = _fold_tr(token).replace("'", "")

    def _pack_klasik(root: str) -> dict[str, Any]:
        k0 = (klasik.get(root) or [{}])[0]
        return {
            "root": root,
            "meaning_en": k0.get("definition") if k0.get("lang") == "en" else "",
            "meaning_tr": _TR_ROOT_HINTS.get(root, ""),
            "forms": [],
            "verse_keys": [],
            "frequency": 0,
        }

    # Latin/TR lemma
    mapped = _LATIN_TO_ROOT.get(low)
    if mapped and mapped in roots:
        return roots[mapped]
    if mapped and mapped in klasik:
        return _pack_klasik(mapped)

    bw = _buckwalter_index().get(low)
    if bw and bw in roots:
        return roots[bw]

    if token in roots:
        return roots[token]
    if bare in roots:
        return roots[bare]
    root = lookup.get(token) or lookup.get(bare)
    if root and root in roots:
        return roots[root]
    if root and root in klasik:
        return _pack_klasik(root)
    if bare in klasik:
        return _pack_klasik(bare)
    for k, r in roots.items():
        if k in bare or bare in k:
            return r
    return None


def format_root_reply(row: dict[str, Any]) -> str:
    root = row.get("root") or ""
    en = (row.get("meaning_en") or "").strip()
    tr = (row.get("meaning_tr") or "").strip() or _TR_ROOT_HINTS.get(root, "")
    forms = row.get("forms") or []
    verses = row.get("verse_keys") or []
    parts = [f"Ümit abi, kök **{root}**:"]
    if tr:
        parts.append(f"**TR (kısa):** {tr}")
    if en:
        parts.append(f"**EN (Lane / Kur'an kök):** {en}")
    for k in (_load_klasik().get(root) or [])[:2]:
        book = (k.get("book_name") or "")[:60]
        definition = (k.get("definition") or "").strip()
        if not definition:
            continue
        label = "EN (klasik sözlük)" if k.get("lang") == "en" else "AR (klasik lügat)"
        parts.append(f"**{label} — {book}:** {definition[:500]}")
    if forms:
        parts.append("**Müştak / formlar:** " + ", ".join(forms[:12]))
    if verses:
        parts.append("**Kur'an örnekleri:** " + ", ".join(verses[:8]))
    parts.append("(Kaynak: yerel Kur'an kök lügati + klasik Arapça sözlükler)")
    return "\n".join(parts)


def _score_nahiv(low: str, row: dict[str, Any]) -> float:
    sc = 0.0
    rid = str(row.get("id") or "")
    keys = [_fold_tr(rid), _fold_tr(str(row.get("baslik") or ""))]
    keys += [_fold_tr(a) for a in (row.get("aliases") or [])]
    for k in keys:
        if not k:
            continue
        if k in low:
            # Kısa alias (kök/kok) tek başına soru değilse düşük skor — kelime kökü sorgusunu çalmasın
            if rid in ("judhur", "mushtaq") and len(k) <= 4:
                # "kök nedir" / "müştak nedir" gibi net sorulara izin
                if re.search(rf"(^|\s){re.escape(k)}(\s+nedir)?(\s|$)", low):
                    other = re.sub(
                        rf"\b({k}|nedir|ne|demek|anlam|anlami|anlamı)\b",
                        " ",
                        low,
                    )
                    other = re.sub(r"\s+", " ", other).strip()
                    if other and len(other) >= 3:
                        sc = max(sc, 2.0)  # düşük — kök lookup önce gelsin
                    else:
                        sc = max(sc, 5.5)
                else:
                    sc = max(sc, 2.0)
            else:
                sc = max(sc, 5.0 + min(len(k), 12) * 0.1)
    return sc


def try_nahiv_reply(msg: str) -> Optional[str]:
    low = _fold_tr(msg)
    best = None
    best_sc = 0.0
    for row in _load_nahiv():
        sc = _score_nahiv(low, row)
        if sc > best_sc:
            best_sc = sc
            best = row
    if best and best_sc >= 4.0:
        return f"Ümit abi, {best.get('metin')}"
    return None


def try_arapca_lugat_reply(message: str) -> Optional[str]:
    msg = (message or "").strip()
    if not msg or not looks_like_arapca_lugat_question(msg):
        return None

    tok = _extract_arabic_token(msg)
    if tok:
        row = lookup_root(tok)
        if row:
            return format_root_reply(row)

    lemma = _extract_latin_lemma(msg)
    if lemma:
        row = lookup_root(lemma)
        if row:
            return format_root_reply(row)

    nah = try_nahiv_reply(msg)
    if nah:
        return nah
    return None


def build_arapca_lugat_context(msg: str, *, max_chars: int = 4000) -> str:
    if not looks_like_arapca_lugat_question(msg):
        return ""
    parts = ["【Arapça lügat / nahiv — yerel】", ""]
    tok = _extract_arabic_token(msg)
    if tok:
        row = lookup_root(tok)
        if row:
            parts.append(format_root_reply(row))
            parts.append("")
    else:
        lemma = _extract_latin_lemma(msg)
        if lemma:
            row = lookup_root(lemma)
            if row:
                parts.append(format_root_reply(row))
                parts.append("")
    nah = try_nahiv_reply(msg)
    if nah:
        parts.append(nah)
    text = "\n".join(parts).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "…"
    return text if len(parts) > 2 else ""
