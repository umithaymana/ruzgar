# -*- coding: utf-8 -*-
"""Rüzgar — tüm tefsir kütüphanesi tarama (modern + klasik, karıştırmadan).

Kur'an Yolu ve klasik eserler ayrı dosyalarda; sorgu anında birleştirilir.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_TEFSIR_ROOT = _ROOT / "knowledge" / "ilim" / "din" / "02_tefsir"

SURE_ALIASES: dict[str, int] = {
    "fatiha": 1, "fâtiha": 1, "bakara": 2, "bakarah": 2,
    "ali imran": 3, "al-i imran": 3, "âli imrân": 3, "ali İmran": 3,
    "nisa": 4, "nisâ": 4, "maide": 5, "mâide": 5, "enam": 6, "en'am": 6,
    "araf": 7, "a'raf": 7, "enfal": 8, "tevbe": 9, "tövbe": 9,
    "yunus": 10, "hud": 11, "yusuf": 12, "rad": 13, "ibrahim": 14,
    "hicr": 15, "nahl": 16, "isra": 17, "isrâ": 17, "kehf": 18,
    "meryem": 19, "taha": 20, "tâhâ": 20, "enbiya": 21, "hac": 22,
    "muminun": 23, "müminun": 23, "nur": 24, "furkan": 25, "suara": 26,
    "neml": 27, "kasas": 28, "ankebut": 29, "rum": 30, "lokman": 31,
    "secde": 32, "ahzab": 33, "sebe": 34, "fatir": 35, "yasin": 36,
    "yâsin": 36, "saffat": 37, "sad": 38, "zumer": 39, "zümer": 39,
    "mumin": 40, "mümin": 40, "fussilet": 41, "sura": 42, "şura": 42,
    "zuhruf": 43, "duhan": 44, "casiye": 45, "ahkaf": 46, "muhammed": 47,
    "fetih": 48, "hucurat": 49, "kaf": 50, "zariyat": 51, "tur": 52,
    "necm": 53, "kamer": 54, "rahman": 55, "vakia": 56,
    "hadid": 57, "mucadele": 58, "hasr": 59, "mumtehine": 60, "saff": 61,
    "cuma": 62, "munafikun": 63, "tegabun": 64, "talak": 65, "tahrim": 66,
    "mulk": 67, "kalem": 68, "hakka": 69, "mearic": 70, "nuh": 71,
    "cin": 72, "muzzemmil": 73, "muddessir": 74, "kiyame": 75, "insan": 76,
    "murselat": 77, "nebe": 78, "naziat": 79, "abese": 80, "tekvir": 81,
    "infitar": 82, "mutaffifin": 83, "insikak": 84, "buruc": 85, "tarik": 86,
    "ala": 87, "gasiye": 88, "fecr": 89, "beled": 90, "sems": 91, "leyl": 92,
    "duha": 93, "insirah": 94, "tin": 95, "alak": 96, "kadr": 97, "beyyine": 98,
    "zilzal": 99, "adiyat": 100, "karia": 101, "tekasur": 102, "asr": 103,
    "humaze": 104, "fil": 105, "kureys": 106, "maun": 107, "kevser": 108,
    "kafirun": 109, "nasr": 110, "tebbet": 111, "ihlas": 112, "felak": 113,
    "nas": 114, "ayatel kursi": 2, "ayetel kursi": 2, "ayetul kursi": 2,
}

AYET_SAYILARI = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111,
    110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45,
    83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55,
    78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20,
    56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21,
    11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
]

_ESER_LABEL = {
    "kuran_yolu": "Kur'an Yolu (Diyanet)",
    "ibn_kesir": "İbn Kesîr",
    "taberi": "Taberî",
    "kurtubi": "Kurtubî",
    "beyzavi": "Beyzâvî",
    "razi": "Fahreddin er-Râzî",
}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_tefsir_question(msg: str) -> bool:
    low = _fold(msg)
    cues = (
        "tefsir", "mufessir", "ibn kesir", "ibni kesir", "ibn kathir",
        "taberi", "kurtubi", "beyzavi", "razi", "fahreddin",
        "kuran yolu", "kur'an yolu", "bu ayet", "ayetinin tefsiri",
        "ne demek istiyor", "ne kastediliyor", "meal ve tefsir",
        "suresinin tefsiri", "suresinin meali", "suresi tefsiri",
        "hangi kitaba", "kimden aldin", "hangi eser", "hangi tefsir",
    )
    if any(c in low for c in cues):
        return True
    if re.search(r"\b\d{1,3}\s*[:/]\s*\d{1,3}\b", msg or ""):
        if any(k in low for k in ("ayet", "sure", "meal", "tefsir", "anlam")):
            return True
    return False


def looks_like_tefsir_followup(msg: str) -> bool:
    low = _fold(msg)
    return any(
        p in low
        for p in (
            "bu tefsir",
            "hangi kitap",
            "hangi eser",
            "kimden aldin",
            "kimden aldın",
            "kaynagin ne",
            "kaynağın ne",
            "hangi kaynaktan",
            "hangi mufessir",
            "hangi tefsirden",
            "nereden okudun",
            "nereden biliyorsun",
            "bu meal",
            "az onceki",
            "az önceki",
            "devam et",
            "sonraki ayet",
            "bir sonraki",
        )
    )


def detect_sure_no(msg: str) -> int | None:
    low = _fold(msg)
    for name, sno in sorted(SURE_ALIASES.items(), key=lambda x: -len(x[0])):
        if name in low:
            return sno
    return None


def parse_sure_ayet(msg: str) -> list[tuple[int, int]]:
    """Mesajdan (sure, ayet) adayları. Sure adı + tefsir isteğinde ayetleri açar."""
    out: list[tuple[int, int]] = []
    raw = msg or ""
    low = _fold(raw)
    for m in re.finditer(r"\b(\d{1,3})\s*[:/]\s*(\d{1,3})\b", raw):
        s, a = int(m.group(1)), int(m.group(2))
        if 1 <= s <= 114 and a >= 1:
            out.append((s, a))
    if "ayatel kursi" in low or "ayetel kursi" in low or "ayetul kursi" in low:
        out.append((2, 255))

    sure_only: list[int] = []
    for name, sno in sorted(SURE_ALIASES.items(), key=lambda x: -len(x[0])):
        if name not in low:
            continue
        m = re.search(
            rf"{re.escape(name)}\s*(?:suresi|sure|suresinin)?\s*(\d{{1,3}})(?!\s*[:/])",
            low,
        )
        if m:
            out.append((sno, int(m.group(1))))
        elif sno == 2 and "kursi" in low:
            out.append((2, 255))
        else:
            # «cin suresi 12. ayet» — sure adı + N. ayet
            m2 = re.search(
                rf"{re.escape(name)}\s*(?:suresi|sure|suresinin)?\s*(\d{{1,3}})\s*\.?\s*ayet",
                low,
            )
            if m2:
                out.append((sno, int(m2.group(1))))
            else:
                sure_only.append(sno)

    if not out and sure_only:
        wants_whole = any(
            k in low for k in ("tefsir", "meal", "oku", "acikla", "anlat", "nedir", "ne demek")
        )
        if wants_whole or looks_like_tefsir_question(msg):
            sno = sure_only[0]
            n = AYET_SAYILARI[sno - 1]
            if n <= 12:
                out.extend((sno, a) for a in range(1, n + 1))
            else:
                out.extend((sno, a) for a in (1, 2, 3, max(1, n // 2), n))

    seen: set[tuple[int, int]] = set()
    uniq: list[tuple[int, int]] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq[:20]


def _index_paths() -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    ky = _TEFSIR_ROOT / "kuran_yolu" / "tefsir_ayet_indeks.jsonl"
    if ky.is_file():
        paths.append(("kuran_yolu", ky))
    klasik = _TEFSIR_ROOT / "klasik"
    if klasik.is_dir():
        for d in sorted(klasik.iterdir()):
            if not d.is_dir():
                continue
            p = d / "tefsir_ayet_indeks.jsonl"
            if p.is_file():
                paths.append((d.name, p))
    return paths


@lru_cache(maxsize=8)
def _load_work_index(work_id: str, path_str: str) -> dict[tuple[int, int], dict]:
    path = Path(path_str)
    out: dict[tuple[int, int], dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        s, a = r.get("sure_no"), r.get("ayet_no")
        if not isinstance(s, int) or not isinstance(a, int):
            continue
        t = (r.get("tefsir_blok") or r.get("tefsir") or "").strip()
        if not t:
            continue
        out[(s, a)] = r
    return out


def _all_indexes() -> dict[str, dict[tuple[int, int], dict]]:
    loaded: dict[str, dict[tuple[int, int], dict]] = {}
    for wid, path in _index_paths():
        loaded[wid] = _load_work_index(wid, str(path))
    return loaded


def _excerpt(text: str, limit: int = 900) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if len(t) <= limit:
        return t
    return t[:limit].rsplit(" ", 1)[0] + "…"


def lookup_ayah(sure_no: int, ayet_no: int, *, per_work_limit: int = 900) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for wid, idx in _all_indexes().items():
        r = idx.get((sure_no, ayet_no))
        if not r:
            continue
        tefsir = (r.get("tefsir_blok") or r.get("tefsir") or "").strip()
        meal = (r.get("meal_blok") or r.get("meal") or "").strip()
        eser = r.get("eser") or wid
        hits.append(
            {
                "eser_id": wid,
                "eser": eser,
                "yazar": r.get("yazar") or "",
                "dil": r.get("dil") or ("tr" if wid == "kuran_yolu" else "ar"),
                "sure_no": sure_no,
                "ayet_no": ayet_no,
                "sure_adi_tr": r.get("sure_adi_tr") or "",
                "meal": _excerpt(meal, 400) if meal else "",
                "tefsir": _excerpt(tefsir, per_work_limit),
                "kaynak": r.get("kaynak") or "",
            }
        )
    # sıra: modern TR önce, sonra klasik
    order = {"kuran_yolu": 0, "ibn_kesir": 1, "taberi": 2, "kurtubi": 3, "beyzavi": 4, "razi": 5}
    hits.sort(key=lambda h: order.get(h["eser_id"], 99))
    return hits


def keyword_scan(query: str, *, top_per_work: int = 2, max_total: int = 10) -> list[dict[str, Any]]:
    """Basit kelime tarama — tüm eserlerde."""
    tokens = [t for t in re.split(r"\W+", _fold(query)) if len(t) >= 4]
    if not tokens:
        return []
    scored: list[tuple[float, dict[str, Any]]] = []
    for wid, idx in _all_indexes().items():
        local: list[tuple[float, dict[str, Any]]] = []
        for (s, a), r in idx.items():
            blob = _fold((r.get("tefsir_blok") or "")[:2000] + " " + (r.get("meal_blok") or "")[:400])
            if not blob:
                continue
            score = sum(1.0 for t in tokens if t in blob)
            if score <= 0:
                continue
            local.append(
                (
                    score,
                    {
                        "eser_id": wid,
                        "eser": r.get("eser") or wid,
                        "yazar": r.get("yazar") or "",
                        "dil": r.get("dil") or ("tr" if wid == "kuran_yolu" else "ar"),
                        "sure_no": s,
                        "ayet_no": a,
                        "sure_adi_tr": r.get("sure_adi_tr") or "",
                        "meal": _excerpt(r.get("meal_blok") or "", 300),
                        "tefsir": _excerpt(r.get("tefsir_blok") or "", 700),
                        "kaynak": r.get("kaynak") or "",
                        "score": score,
                    },
                )
            )
        local.sort(key=lambda x: x[0], reverse=True)
        scored.extend(local[:top_per_work])
    scored.sort(key=lambda x: x[0], reverse=True)
    return [h for _, h in scored[:max_total]]


def search_tefsir_library(msg: str) -> list[dict[str, Any]]:
    refs = parse_sure_ayet(msg)
    # Takip sorusu: son sohbetten sure/ayet çıkar (önce kullanıcı cümlesi)
    if looks_like_tefsir_followup(msg) or (not refs and looks_like_tefsir_question(msg)):
        try:
            from ilim_assistant.ana_motor_sohbet_gecmis import search_chat_history

            prev = search_chat_history("tefsir", limit=8)
            for it in prev.get("items") or []:
                user_b = it.get("user_snippet") or ""
                if not looks_like_tefsir_question(user_b):
                    continue
                # «hangi kitap» gibi takip cümlelerini atla
                if looks_like_tefsir_followup(user_b):
                    continue
                pref = parse_sure_ayet(user_b)
                if pref:
                    refs = pref
                    break
                sno = detect_sure_no(user_b)
                if sno:
                    n = AYET_SAYILARI[sno - 1]
                    refs = [(sno, a) for a in range(1, min(n, 7) + 1)]
                    break
        except Exception:
            pass

    hits: list[dict[str, Any]] = []
    for s, a in refs:
        hits.extend(lookup_ayah(s, a, per_work_limit=500))
    # Kaynak/kitap sorusunda rastgele keyword tarama yapma
    if not hits and not looks_like_tefsir_followup(msg):
        hits = keyword_scan(msg)
    return hits


def build_tefsir_context(msg: str, *, max_chars: int = 9000) -> str:
    """Sohbet promptuna eklenecek çok-eser tefsir bağlamı + zorunlu atıf emri."""
    if not (looks_like_tefsir_question(msg) or looks_like_tefsir_followup(msg)):
        return ""
    hits = search_tefsir_library(msg)

    if looks_like_tefsir_followup(msg) and not hits:
        lines = [
            "【Tefsir kaynakları — doğal anlat】",
            "Kullanıcı az önceki tefsirin kaynağını soruyor. Madde madde robot gibi okuma;",
            "samimi asistan gibi söyle: «Bunu kütüphanemdeki şu eserlerden okudum…»",
            "Kur'an Yolu (Diyanet, Türkçe), İbn Kesîr, Taberî, Kurtubî, Beyzâvî, Râzî.",
            "Web uydurma. Son konuştuğunuz sureyi hatırlat (örn. Fatiha).",
        ]
        return "\n".join(lines)

    if not hits:
        return (
            "【Tefsir】 Bu turda net sure/ayet bulamadım. Uydurma yazma; "
            "dostça sure veya ayet sor."
        )

    by_eser: dict[str, list[dict[str, Any]]] = {}
    for h in hits:
        by_eser.setdefault(h.get("eser_id") or "?", []).append(h)

    lines = [
        "【Yerel tefsir notları — kullanıcıya şablon gibi okuma】",
        "Sen Ümit'in kişisel asistanı Rüzgar'sın. Karşında bir insan varmış gibi konuş:",
        "sıcak, akıcı, yönlendirici. Kaynakları doğal cümleyle an (Kur'an Yolu, İbn Kesîr…).",
        "Arapça klasikleri Türkçe özetle; meal varsa önce onu söyle. Web'den uydurma ekleme.",
        "İstersen ardından «İstersen bir sonraki ayete geçelim» diye yönlendir.",
        "",
    ]
    for wid, items in by_eser.items():
        label = _ESER_LABEL.get(wid) or (items[0].get("eser") or wid)
        yazar = items[0].get("yazar") or ""
        lines.append(f"### {label}" + (f" — {yazar}" if yazar else ""))
        shown = 0
        for h in items:
            if shown >= 4:
                break
            sure = h.get("sure_adi_tr") or h.get("sure_no")
            bit = f"{sure} {h.get('sure_no')}:{h.get('ayet_no')}"
            if h.get("meal"):
                lines.append(f"- [{bit}] Meal: {h['meal']}")
            if h.get("tefsir"):
                lines.append(f"- [{bit}] Tefsir: {h['tefsir']}")
            shown += 1
        lines.append("")

    text = "\n".join(lines).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0] + "\n…"
    return text


def hits_as_rag_tuples(hits: list[dict[str, Any]]) -> list[tuple[str, str, float]]:
    """main_engine RAG hit formatı: (text, source, score)."""
    out: list[tuple[str, str, float]] = []
    for i, h in enumerate(hits):
        sure = h.get("sure_adi_tr") or h.get("sure_no")
        label = _ESER_LABEL.get(h.get("eser_id") or "", h.get("eser") or "")
        title = f"Tefsir · {label} · {sure} {h.get('sure_no')}:{h.get('ayet_no')}"
        parts = [title]
        if h.get("meal"):
            parts.append(f"Meal: {h['meal']}")
        if h.get("tefsir"):
            parts.append(f"Tefsir: {h['tefsir']}")
        text = "\n".join(parts)
        src = f"ilim/din/02_tefsir/{h.get('eser_id')}"
        score = float(h.get("score") or (2.0 - i * 0.02))
        out.append((text, src, score))
    return out


def library_status() -> dict[str, Any]:
    cat = _TEFSIR_ROOT / "klasik" / "catalog.json"
    status: dict[str, Any] = {"works": {}}
    for wid, path in _index_paths():
        n = sum(1 for _ in path.open(encoding="utf-8"))
        status["works"][wid] = {"path": str(path), "lines": n}
    if cat.is_file():
        status["catalog"] = json.loads(cat.read_text(encoding="utf-8"))
    return status