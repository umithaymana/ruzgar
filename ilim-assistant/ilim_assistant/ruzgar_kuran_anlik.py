# -*- coding: utf-8 -*-
"""Rüzgar — Kur'an anlık doğru cevap (sure/ayet/meal + temel kavramlar).

Yanlış hafıza/web/echo yerine yerel `01_kuran` verisini kullanır.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_KURAN_DIR = _ROOT / "knowledge" / "ilim" / "din" / "01_kuran"
_SURELER = _KURAN_DIR / "metadata" / "sureler.json"
_CUZ = _KURAN_DIR / "metadata" / "cuz_hizb.json"
_NUZUL = _KURAN_DIR / "metadata" / "nuzul_sirasi.json"
_AYETLER = _KURAN_DIR / "ayetler.jsonl"
_KAVRAMLAR = _KURAN_DIR / "temel_kavramlar.jsonl"
_TECVID = _KURAN_DIR / "tecvid_giris.jsonl"

# Sıra = sure numarası (1..114) — yedek
_SURE_ADLARI_TR = [
    "Fâtiha", "Bakara", "Âl-i İmrân", "Nisâ", "Mâide", "En'âm", "A'râf", "Enfâl",
    "Tevbe", "Yûnus", "Hûd", "Yûsuf", "Ra'd", "İbrâhîm", "Hicr", "Nahl", "İsrâ",
    "Kehf", "Meryem", "Tâhâ", "Enbiyâ", "Hac", "Mü'minûn", "Nûr", "Furkân",
    "Şuarâ", "Neml", "Kasas", "Ankebût", "Rûm", "Lokmân", "Secde", "Ahzâb",
    "Sebe'", "Fâtır", "Yâsîn", "Sâffât", "Sâd", "Zümer", "Mü'min", "Fussilet",
    "Şûrâ", "Zuhruf", "Duhân", "Câsiye", "Ahkâf", "Muhammed", "Fetih", "Hucurât",
    "Kâf", "Zâriyât", "Tûr", "Necm", "Kamer", "Rahmân", "Vâkıa", "Hadîd",
    "Mücâdele", "Haşr", "Mümtehine", "Saff", "Cuma", "Münâfikûn", "Teğâbün",
    "Talâk", "Tahrîm", "Mülk", "Kalem", "Hâkka", "Meâric", "Nûh", "Cin",
    "Müzzemmil", "Müddessir", "Kıyâme", "İnsan", "Mürselât", "Nebe'", "Nâziât",
    "Abese", "Tekvîr", "İnfitâr", "Mutaffifîn", "İnşikâk", "Bürûc", "Târık",
    "A'lâ", "Gâşiye", "Fecr", "Beled", "Şems", "Leyl", "Duhâ", "İnşirâh",
    "Tîn", "Alak", "Kadr", "Beyyine", "Zilzâl", "Âdiyât", "Kâria", "Tekâsür",
    "Asr", "Hümeze", "Fîl", "Kureyş", "Mâûn", "Kevser", "Kâfirûn", "Nasr",
    "Tebbet", "İhlâs", "Felak", "Nâs",
]


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def looks_like_kuran_question(msg: str) -> bool:
    low = _fold(msg)
    if not low:
        return False
    cues = (
        "kuran", "kur'an", "sure", "sûre", "ayet", "âyet", "meal", "meâl",
        "tefsir", "mushaf", "tecvid", "tecvit", "kiraat", "kıraat",
        "cuz", "cüz", "hizb", "hizip", "nuzul", "nüzul", "nüzûl", "kronoloji",
        "mekki", "mekkî", "medeni", "medenî", "tilavet", "besmele",
        "mahreç", "mahrec", "idgam", "ihfa", "iklab", "izhar", "gunne",
        "hatim", "vahiy", "kelamullah", "müfessir", "mufessir", "tertib",
        "tertîb", "iniş sırası", "siralam", "sıralama", "fatiha", "bakara",
        "cin suresi", "ihlas", "ayetel kursi", "ayatul kursi",
    )
    return any(c in low for c in cues)


@lru_cache(maxsize=1)
def _load_sureler() -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    if _SURELER.is_file():
        try:
            rows = json.loads(_SURELER.read_text(encoding="utf-8"))
            for r in rows:
                n = int(r.get("sure_no") or 0)
                if 1 <= n <= 114:
                    out[n] = r
        except Exception:
            pass
    if len(out) < 114:
        for i, name in enumerate(_SURE_ADLARI_TR, start=1):
            out.setdefault(i, {"sure_no": i, "sure_adi_tr": name})
    return out


@lru_cache(maxsize=1)
def _load_ayet_index() -> dict[tuple[int, int], dict[str, Any]]:
    idx: dict[tuple[int, int], dict[str, Any]] = {}
    if not _AYETLER.is_file():
        return idx
    try:
        for line in _AYETLER.open(encoding="utf-8"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            s, a = r.get("sure_no"), r.get("ayet_no")
            if isinstance(s, int) and isinstance(a, int):
                idx[(s, a)] = r
    except Exception:
        pass
    return idx


@lru_cache(maxsize=1)
def _load_kavramlar() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in (_KAVRAMLAR, _TECVID):
        if not path.is_file():
            continue
        try:
            for line in path.open(encoding="utf-8"):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
    return rows


@lru_cache(maxsize=1)
def _load_cuz() -> dict[str, Any]:
    if not _CUZ.is_file():
        return {}
    try:
        return json.loads(_CUZ.read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _load_nuzul() -> dict[str, Any]:
    if not _NUZUL.is_file():
        return {}
    try:
        return json.loads(_NUZUL.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sure_name(sure_no: int) -> str:
    if not (1 <= sure_no <= 114):
        return ""
    row = _load_sureler().get(sure_no) or {}
    name = str(row.get("sure_adi_tr") or "").strip()
    if name:
        return name
    return _SURE_ADLARI_TR[sure_no - 1]


def lookup_ayah_text(sure_no: int, ayet_no: int) -> Optional[dict[str, str]]:
    r = _load_ayet_index().get((sure_no, ayet_no))
    if not r:
        return None
    meal = (
        (r.get("meal_tr_diyanet") or "").strip()
        or (r.get("meal_tr") or "").strip()
        or (r.get("meal_tr_kuran_yolu") or "").strip()
    )
    return {
        "sure_adi": str(r.get("sure_adi_tr") or sure_name(sure_no)),
        "text_ar": str(r.get("text_ar") or "").strip(),
        "meal_tr": meal,
    }


def parse_sure_number_question(msg: str) -> Optional[int]:
    """«5. sure hangisi», «kuranı kerimde 15. sure nedir»."""
    low = _fold(msg)
    if "sure" not in low and "sûre" not in low:
        return None
    if re.search(r"\b\d{1,3}\s*\.?\s*ayet\b", low) or re.search(
        r"\b\d{1,3}\s*[:/]\s*\d{1,3}\b", msg or ""
    ):
        return None
    if not re.search(r"(hangisi|nedir|adi|adı|ismi|ne\s+sure|hangi\s+sure)", low):
        if not re.search(r"\b\d{1,3}\s*\.?\s*sure\b", low):
            return None
    m = re.search(r"\b(\d{1,3})\s*\.?\s*sure\b", low)
    if not m:
        m = re.search(r"sure\s*(?:no|numara[sş][ıi]?)?\s*[:\-]?\s*(\d{1,3})\b", low)
    if not m:
        return None
    n = int(m.group(1))
    if 1 <= n <= 114:
        return n
    return None


def parse_ayah_read_request(msg: str) -> Optional[tuple[int, int]]:
    """«cin suresi 12. ayet» veya «7. sure 15. ayet»."""
    from ilim_assistant.ruzgar_tefsir_kutuphane import AYET_SAYILARI, detect_sure_no, parse_sure_ayet

    refs = parse_sure_ayet(msg)
    if refs:
        if len(refs) == 1:
            return refs[0]
        sures = {s for s, _ in refs}
        if len(sures) == 1:
            return refs[0]

    low = _fold(msg)
    m_num = re.search(
        r"\b(\d{1,3})\s*\.?\s*sure(?:si)?\s*(?:nin)?\s*(\d{1,3})\s*\.?\s*ayet",
        low,
    )
    if m_num:
        s, a = int(m_num.group(1)), int(m_num.group(2))
        if 1 <= s <= 114 and 1 <= a <= AYET_SAYILARI[s - 1]:
            return (s, a)

    sno = detect_sure_no(msg)
    if not sno:
        return None
    m = re.search(r"\b(\d{1,3})\s*\.?\s*ayet", low)
    if not m:
        m = re.search(rf"\b{sno}\s*[:/]\s*(\d{{1,3}})\b", msg or "")
        if m:
            return (sno, int(m.group(1)))
        return None
    a = int(m.group(1))
    n_max = AYET_SAYILARI[sno - 1]
    if 1 <= a <= n_max:
        return (sno, a)
    return None


def format_sure_identity_reply(sure_no: int) -> str:
    row = _load_sureler().get(sure_no) or {}
    name = str(row.get("sure_adi_tr") or sure_name(sure_no))
    ar = str(row.get("sure_adi_ar") or "").strip()
    ayet_n = row.get("ayet_sayisi")
    iniş = str(row.get("iniş") or "").strip()
    nuzul = row.get("nuzul_sirasi")
    parts = [
        f"Ümit abi, Kur'an-ı Kerim'in **{sure_no}. sûresi** **{name}**"
        + (f" ({ar})" if ar else "")
        + " sûresidir."
    ]
    det: list[str] = []
    if ayet_n:
        det.append(f"{ayet_n} ayet")
    if iniş:
        note = " — sınıflandırma ihtilaflı olabilir" if row.get("inis_ihtilafli") else ""
        det.append(f"{iniş}{note}")
    if nuzul:
        det.append(f"nüzûl sırası {nuzul}")
    if det:
        parts.append(" · ".join(det) + ".")
    parts.append("(Kaynak: yerel `01_kuran` metadata)")
    return "\n".join(parts)


def format_ayah_read_reply(sure_no: int, ayet_no: int) -> Optional[str]:
    hit = lookup_ayah_text(sure_no, ayet_no)
    if not hit:
        return None
    name = hit["sure_adi"] or sure_name(sure_no)
    parts = [f"Ümit abi, **{name}** sûresi **{ayet_no}. âyet**:"]
    if hit["text_ar"]:
        parts.append("")
        parts.append(hit["text_ar"])
    if hit["meal_tr"]:
        parts.append("")
        parts.append(f"**Meal:** {hit['meal_tr']}")
    parts.append("")
    parts.append("(Kaynak: yerel Diyanet mushaf / meal — `01_kuran`)")
    return "\n".join(parts)


def _score_kavram(msg_fold: str, row: dict[str, Any]) -> float:
    score = 0.0
    kid = _fold(str(row.get("id") or ""))
    baslik = _fold(str(row.get("baslik") or ""))
    aliases = [_fold(a) for a in (row.get("aliases") or [])]
    keys = [kid, baslik] + aliases
    for k in keys:
        if not k:
            continue
        if msg_fold == k or msg_fold == f"{k} nedir" or msg_fold == f"{k} ne demek":
            score = max(score, 10.0)
        elif k in msg_fold:
            score = max(score, 4.0 + min(len(k), 20) * 0.05)
    # ek ipuçları
    blob = _fold(str(row.get("metin") or ""))[:200]
    tokens = [t for t in re.split(r"\W+", msg_fold) if len(t) >= 4]
    if tokens:
        hit = sum(1 for t in tokens if t in kid or t in baslik or any(t in a for a in aliases))
        score += hit * 0.8
        if hit and blob:
            score += 0.2
    return score


def try_kavram_reply(message: str) -> Optional[str]:
    """Sûre/âyet/tecvid/kronoloji tanım soruları."""
    low = _fold(message)
    if not low:
        return None

    # Özel yapısal sorular
    if re.search(r"(kac|kaç)\s*(sure|sûre)", low):
        return (
            "Ümit abi, Kur'an-ı Kerim'de **114 sûre** vardır. "
            "Mushaf sırası 1 Fâtiha → 114 Nâs; nüzûl sırası bundan farklıdır."
        )
    if re.search(r"(kac|kaç)\s*ayet", low):
        return (
            "Ümit abi, standart Diyanet / yaygın sayımla Kur'an'da **6236 âyet** vardır. "
            "Bazı geleneklerde besmele sayımı nedeniyle rakam biraz değişebilir."
        )
    if re.search(r"(kac|kaç)\s*c[uü]z", low) or "30 cuz" in low or "30 cüz" in low:
        return (
            "Ümit abi, Kur'an **30 cüz**e ayrılır; her cüz kabaca **2 hizb** (toplam 60 hizb)dir. "
            "1. cüz Fâtiha ile, 30. cüz Nebe' ile başlar."
        )
    if re.search(r"(ilk\s+inen|ilk\s+n[uü]z[uü]l|en\s+once\s+inen|ilk\s+vahiy)", low):
        return (
            "Ümit abi, rivayete göre ilk inen ayetler **Alak** sûresinin başıdır "
            "(nüzûl sırası 1 → mushaf no **96**). Fâtiha mushafta 1. olsa da nüzûlde daha sonradır."
        )
    if re.search(r"(son\s+inen|en\s+son\s+inen)", low):
        return (
            "Ümit abi, yaygın rivayette son inen sûre **Nasr**'dır (mushaf 110; nüzûl sırası sonda). "
            "Bazı rivayetlerde son ayetler hakkında farklı nakiller de vardır."
        )
    if re.search(r"n[uü]z[uü]l\s*s[ıi]ras|ini[sş]\s*s[ıi]ras|kronoloj", low):
        nuz = _load_nuzul()
        sira = nuz.get("sira_mushaf_no") or []
        if sira:
            first = [f"{sure_name(n)} ({n})" for n in sira[:5]]
            return (
                "Ümit abi, **nüzûl (iniş) sırası** mushaf sırasından ayrıdır. "
                f"İlk beşi: {', '.join(first)}… "
                "Tam liste yerel `metadata/nuzul_sirasi.json` içinde. "
                "Bazı sûrelerde kronoloji ihtilaflı olabilir."
            )

    # «X suresi mekki mi» / «bakara medeni mi»
    if any(x in low for x in ("mekki", "medeni", "mekkî", "medenî")):
        sno = None
        try:
            from ilim_assistant.ruzgar_tefsir_kutuphane import detect_sure_no

            sno = detect_sure_no(message)
        except Exception:
            sno = None
        if not sno:
            sno = parse_sure_number_question(message)
        if sno:
            row = _load_sureler().get(sno) or {}
            iniş = row.get("iniş") or "?"
            note = (
                " (Bu sûrede sınıflandırma ihtilaflı olabilir.)"
                if row.get("inis_ihtilafli")
                else ""
            )
            return (
                f"Ümit abi, **{sure_name(sno)}** sûresi kayıtlarda **{iniş}** olarak geçer"
                f"{note}."
            )

    # «N. cüz nerede başlar»
    m_cuz = re.search(r"\b(\d{1,2})\s*\.?\s*c[uü]z", low)
    if m_cuz and any(x in low for x in ("nerede", "baslar", "başlar", "hangi", "nedir")):
        n = int(m_cuz.group(1))
        items = (_load_cuz().get("items") or [])
        row = next((x for x in items if int(x.get("cuz_no") or 0) == n), None)
        if row:
            return (
                f"Ümit abi, **{n}. cüz** "
                f"**{row.get('baslangic_sure_adi')}** "
                f"{row.get('baslangic_sure')}:{row.get('baslangic_ayet')} ile başlar."
            )

    best: Optional[dict[str, Any]] = None
    best_sc = 0.0
    for row in _load_kavramlar():
        sc = _score_kavram(low, row)
        if sc > best_sc:
            best_sc = sc
            best = row
    if best and best_sc >= 3.5:
        metin = str(best.get("metin") or "").strip()
        if metin:
            return f"Ümit abi, {metin}"
    return None


def build_kuran_kavram_context(msg: str, *, max_chars: int = 3500) -> str:
    """LLM turuna eklenecek kısa kavram bağlamı."""
    if not looks_like_kuran_question(msg):
        return ""
    low = _fold(msg)
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in _load_kavramlar():
        sc = _score_kavram(low, row)
        if sc >= 2.5:
            scored.append((sc, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return ""
    lines = [
        "【Kur'an temel kavramları — yerel; uydurma】",
        "Kullanıcıya robot listesi okuma; dostça doğru tanım ver.",
        "",
    ]
    for _, row in scored[:6]:
        lines.append(f"### {row.get('baslik') or row.get('id')}")
        lines.append(str(row.get("metin") or "").strip())
        lines.append("")
    text = "\n".join(lines).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0] + "\n…"
    return text


def try_kuran_instant_reply(message: str) -> Optional[str]:
    """Anında doğru Kur'an cevabı — LLM/hafıza/web atlanır."""
    msg = (message or "").strip()
    if not msg or not looks_like_kuran_question(msg):
        return None

    try:
        from ilim_assistant.ruzgar_tefsir_kutuphane import looks_like_tefsir_followup

        if looks_like_tefsir_followup(msg):
            return (
                "Ümit abi, az önce okuduğum tefsiri **yerel kütüphanemdeki** şu eserlerden "
                "alıyorum: **Kur'an Yolu (Diyanet)**, **İbn Kesîr**, **Taberî**, "
                "**Kurtubî**, **Beyzâvî** ve **Fahreddin er-Râzî**. "
                "Web'den uydurmuyorum; hangisini daha derinlemesine istersen söyle."
            )
    except Exception:
        pass

    # Tanım / kronoloji / tecvid — ayet okumadan önce
    kav = try_kavram_reply(msg)
    if kav:
        # Sure kimliği daha spesifikse onu tercih et
        sno = parse_sure_number_question(msg)
        if sno and re.search(r"\b\d{1,3}\s*\.?\s*sure\b", _fold(msg)):
            return format_sure_identity_reply(sno)
        # Ayet okuma isteği tanımı ezmesin
        if not parse_ayah_read_request(msg):
            return kav

    sno = parse_sure_number_question(msg)
    if sno:
        return format_sure_identity_reply(sno)

    low = _fold(msg)
    ref = parse_ayah_read_request(msg)
    if ref:
        if "tefsir" in low:
            return None
        return format_ayah_read_reply(ref[0], ref[1])

    return kav
